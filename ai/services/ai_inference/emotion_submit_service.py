# -*- coding: utf-8 -*-
"""emotion_submit_service.py

Shared helpers for emotion persistence flows.

Purpose
-------
- Keep `/emotion/submit` semantics unchanged.
- Allow new routes such as `/emotion/reflection/publish` to reuse the same
  normalization / insert / cache invalidation / background task pipeline
  without HTTP self-calls.

Notes
-----
- This module intentionally reuses the existing private helpers from
  `api_emotion_submit.py` to minimize blast radius for the current release.
- The public API here is small and additive.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence, Union

from fastapi import HTTPException

from api_emotion_submit import (
    ALLOW_LEGACY_USER_ID,
    EmotionItem,
    _extract_bearer_token,
    _global_summary_activity_date_from_created_at,
    _insert_emotion_row,
    _normalize_categories,
    _normalize_emotions,
    _resolve_user_id_from_token,
    _start_post_submit_background_tasks,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_observation_diagnostic_lockdown import (
    build_observation_diagnostic_lockdown,
    dump_observation_diagnostic,
)
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_reply_service import render_emlis_ai_reply
from response_microcache import invalidate_prefix
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user


logger = logging.getLogger(__name__)


def _emlis_ai_reply_timeout_seconds() -> float:
    """Return the synchronous EmlisAI reply budget for /emotion/submit.

    Emotion saving must not be held hostage by optional context reads.
    If the reply path exceeds this budget, Emlisの観測 is fail-closed and the
    saved input itself remains successful.
    """
    try:
        raw = float(os.getenv("EMLIS_AI_REPLY_TIMEOUT_SECONDS", "3.0") or "3.0")
    except Exception:
        raw = 3.0
    return max(0.5, min(10.0, raw))


def _emlis_ai_observation_result_log_enabled() -> bool:
    """Return whether temporary Emlis observation result logging is enabled.

    Step7 keeps normal logs quiet by default. The log is diagnostic-only,
    contains no raw input or public comment text, and can be enabled locally
    while checking display reach regressions.
    """
    truthy = {"1", "true", "yes", "y", "on", "debug"}
    for name in (
        "EMLIS_AI_OBSERVATION_RESULT_LOG_ENABLED",
        "COCOLON_EMLIS_OBSERVATION_RESULT_LOG_ENABLED",
        "EMLIS_AI_OBSERVATION_DEBUG_LOG",
        "EMLIS_AI_OBSERVATION_DEBUG_LOGS",
    ):
        raw = os.getenv(name)
        if raw is not None and str(raw).strip().lower() in truthy:
            return True
    return False


def _emlis_ai_observation_debug_logging_enabled() -> bool:
    """Backward-compatible alias for Step7 debug log gating tests."""
    return _emlis_ai_observation_result_log_enabled()


def _emlis_ai_observation_diagnostic_lockdown_log_enabled() -> bool:
    """Return whether submit-level structured observation diagnostics are enabled.

    The lockdown log is opt-in, meta-only, and additive.  The legacy Step7
    debug flags also enable it so local diagnosis can use one switch, while the
    new explicit flags allow this structured log without the old free-form
    ``emlis_observation_result`` line.
    """
    truthy = {"1", "true", "yes", "y", "on", "debug"}
    for name in (
        "EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED",
        "COCOLON_EMLIS_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED",
    ):
        raw = os.getenv(name)
        if raw is not None and str(raw).strip().lower() in truthy:
            return True
    return _emlis_ai_observation_result_log_enabled()


def _extract_emlis_ai_diagnostic_summary(input_feedback_meta: Any) -> Dict[str, Any]:
    """Extract diagnostic_summary from reply meta without reading raw input."""
    if not isinstance(input_feedback_meta, dict):
        return {}

    raw_diagnostic_summary = input_feedback_meta.get("diagnostic_summary")
    if isinstance(raw_diagnostic_summary, dict):
        return raw_diagnostic_summary

    multi_perspective_meta = input_feedback_meta.get("multi_perspective")
    if isinstance(multi_perspective_meta, dict):
        raw_diagnostic_summary = multi_perspective_meta.get("diagnostic_summary")
        if isinstance(raw_diagnostic_summary, dict):
            return raw_diagnostic_summary

    return {}


def _safe_reason_codes(values: Any, *, limit: int = 20) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        source = [values]
    elif isinstance(values, (list, tuple, set)):
        source = list(values)
    else:
        source = [values]
    out: list[str] = []
    for raw in source:
        text = str(raw or "").strip()
        if not text or text in out:
            continue
        out.append(text[:96])
        if len(out) >= limit:
            break
    return out


def _public_visible_surface_gate_blocks(public_meta: Dict[str, Any]) -> bool:
    gate = public_meta.get("visible_surface_acceptance_gate") if isinstance(public_meta, dict) else None
    if not isinstance(gate, dict):
        return False
    if gate.get("passed") is False:
        return True
    if str(gate.get("classification") or "").strip() in {"repair_required", "red"}:
        return True
    if str(gate.get("action") or "").strip() in {"rerender_surface", "reroute_low_information", "block", "fail_closed"}:
        return True
    return False


def _public_input_feedback_comment(
    input_feedback_comment: str,
    public_input_feedback_meta: Dict[str, Any],
) -> str:
    """Return comment_text only when the public RN display contract can include it."""

    comment_text = str(input_feedback_comment or "").strip()
    if should_include_public_input_feedback(comment_text, public_input_feedback_meta):
        return comment_text
    return ""


def _existing_step7_public_feedback_summary(internal_meta: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(internal_meta, dict):
        return {}
    for key in (
        "step7_public_feedback_diagnostic_summary",
        "public_feedback_diagnostic_summary",
        "display_absence_summary",
    ):
        value = internal_meta.get(key)
        if isinstance(value, dict):
            return dict(value)
    diagnostic_summary = internal_meta.get("diagnostic_summary")
    if isinstance(diagnostic_summary, dict):
        for key in (
            "step7_public_feedback_diagnostic_summary",
            "public_feedback_diagnostic_summary",
            "display_absence_summary",
        ):
            value = diagnostic_summary.get(key)
            if isinstance(value, dict):
                return dict(value)
    return {}


def _build_public_feedback_inclusion_summary(
    *,
    input_feedback_comment: str,
    internal_input_feedback_meta: Dict[str, Any],
    public_input_feedback_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Build Step7 public-safe inclusion diagnostics for submit logs.

    The summary is code/boolean/count-only. It never copies raw input or the
    public comment body.
    """

    public_meta = public_input_feedback_meta if isinstance(public_input_feedback_meta, dict) else {}
    internal_meta = internal_input_feedback_meta if isinstance(internal_input_feedback_meta, dict) else {}
    existing = _existing_step7_public_feedback_summary(internal_meta)
    comment_present = bool(str(input_feedback_comment or "").strip())
    observation_status = str(public_meta.get("observation_status") or internal_meta.get("observation_status") or "").strip()
    public_feedback_included = should_include_public_input_feedback(input_feedback_comment, public_meta)
    visible_gate_blocks = _public_visible_surface_gate_blocks(public_meta)
    visible_gate = public_meta.get("visible_surface_acceptance_gate") if isinstance(public_meta.get("visible_surface_acceptance_gate"), dict) else {}
    runtime_gate = public_meta.get("runtime_surface_pre_return_gate") if isinstance(public_meta.get("runtime_surface_pre_return_gate"), dict) else {}
    reason_codes = _safe_reason_codes(
        [
            *(public_meta.get("rejection_reasons") or [] if isinstance(public_meta.get("rejection_reasons"), list) else []),
            *(visible_gate.get("rejection_reasons") or [] if isinstance(visible_gate.get("rejection_reasons"), list) else []),
            *(runtime_gate.get("rejection_reasons") or [] if isinstance(runtime_gate.get("rejection_reasons"), list) else []),
            *(existing.get("reason_codes") or [] if isinstance(existing.get("reason_codes"), list) else []),
        ]
    )
    candidate_blocked_koto_splice = bool(
        existing.get("candidate_blocked_koto_splice") is True
        or visible_gate.get("koto_splice_detected") is True
        or any("koto" in reason or reason.startswith("malformed_nominalization_") for reason in reason_codes)
    )
    candidate_blocked_relation_skeleton = bool(
        existing.get("candidate_blocked_relation_skeleton") is True
        or visible_gate.get("relation_skeleton_major") is True
        or visible_gate.get("analytic_register_leak") is True
        or any(reason.startswith("surface_relation_skeleton") or reason == "analytic_register_leak" for reason in reason_codes)
    )
    candidate_blocked_surface_grammar = bool(
        existing.get("candidate_blocked_surface_grammar") is True
        or candidate_blocked_koto_splice
        or runtime_gate.get("passed") is False
        or any(reason in {"runtime_surface_pre_return_gate_failed", "surface_grammar_warning", "malformed_phrase_unit", "surface_template_major"} for reason in reason_codes)
    )
    candidate_repair_attempted = bool(existing.get("candidate_repair_attempted") is True)
    candidate_repair_succeeded = bool(existing.get("candidate_repair_succeeded") is True or (candidate_repair_attempted and public_feedback_included))
    candidate_repair_failed = bool(existing.get("candidate_repair_failed") is True or (candidate_repair_attempted and not candidate_repair_succeeded))
    public_feedback_not_included_non_passed = bool(not public_feedback_included and observation_status != "passed")
    public_feedback_not_included_empty_comment_text = bool(not public_feedback_included and not comment_present)
    public_feedback_not_included_visible_surface_gate = bool(not public_feedback_included and visible_gate_blocks)
    rn_payload_absent = bool(not public_feedback_included)
    candidate_fail_closed_display_absent = bool(
        existing.get("candidate_fail_closed_display_absent") is True
        or rn_payload_absent
        or public_feedback_not_included_non_passed
        or public_feedback_not_included_empty_comment_text
        or public_feedback_not_included_visible_surface_gate
    )
    if candidate_blocked_koto_splice:
        reason_family = "koto_splice"
    elif candidate_blocked_relation_skeleton:
        reason_family = "relation_skeleton"
    elif candidate_blocked_surface_grammar:
        reason_family = "surface_grammar"
    elif public_feedback_not_included_empty_comment_text:
        reason_family = "empty_comment_text"
    elif public_feedback_not_included_non_passed:
        reason_family = "non_passed"
    elif public_feedback_not_included_visible_surface_gate:
        reason_family = "visible_surface_gate"
    elif public_feedback_included:
        reason_family = "included"
    else:
        reason_family = "display_absent"

    return {
        "version": "emlis.step7.public_feedback_inclusion_summary.v1",
        "public_feedback_included": public_feedback_included,
        "public_feedback_not_included_non_passed": public_feedback_not_included_non_passed,
        "public_feedback_not_included_empty_comment_text": public_feedback_not_included_empty_comment_text,
        "public_feedback_not_included_visible_surface_gate": public_feedback_not_included_visible_surface_gate,
        "rn_payload_absent": rn_payload_absent,
        "candidate_blocked_surface_grammar": candidate_blocked_surface_grammar,
        "candidate_blocked_koto_splice": candidate_blocked_koto_splice,
        "candidate_blocked_relation_skeleton": candidate_blocked_relation_skeleton,
        "candidate_repair_attempted": candidate_repair_attempted,
        "candidate_repair_succeeded": candidate_repair_succeeded,
        "candidate_repair_failed": candidate_repair_failed,
        "candidate_fail_closed_display_absent": candidate_fail_closed_display_absent,
        "reason_family": reason_family,
        "reason_codes": reason_codes,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
    }


def _with_public_feedback_inclusion_summary(
    *,
    internal_input_feedback_meta: Dict[str, Any],
    inclusion_summary: Dict[str, Any],
) -> Dict[str, Any]:
    meta = dict(internal_input_feedback_meta or {})
    summary = dict(inclusion_summary or {})
    if not summary:
        return meta
    diagnostic_summary = dict(meta.get("diagnostic_summary") or {}) if isinstance(meta.get("diagnostic_summary"), dict) else {}
    diagnostic_summary["step7_public_feedback_diagnostic_summary"] = summary
    diagnostic_summary["public_feedback_diagnostic_summary"] = summary
    diagnostic_summary["display_absence_summary"] = summary
    meta["diagnostic_summary"] = diagnostic_summary
    meta["step7_public_feedback_diagnostic_summary"] = summary
    meta["public_feedback_diagnostic_summary"] = summary
    meta["display_absence_summary"] = summary
    return meta


def _log_emlis_ai_observation_result(
    *,
    input_feedback_comment: str,
    input_feedback_meta: Dict[str, Any],
) -> None:
    """Emit the temporary observation-result log only when explicitly enabled."""
    if not _emlis_ai_observation_result_log_enabled():
        return

    diagnostic_summary = _extract_emlis_ai_diagnostic_summary(input_feedback_meta)
    logger.info(
        "emlis_observation_result comment_text_present=%s observation_status=%s "
        "stage=%s primary_reason=%s coverage_group=%s",
        bool(str(input_feedback_comment or "").strip()),
        input_feedback_meta.get("observation_status")
        if isinstance(input_feedback_meta, dict)
        else "",
        diagnostic_summary.get("stage") if isinstance(diagnostic_summary, dict) else "",
        diagnostic_summary.get("primary_reason")
        if isinstance(diagnostic_summary, dict)
        else "",
        diagnostic_summary.get("coverage_group")
        if isinstance(diagnostic_summary, dict)
        else "",
    )


def _log_emlis_ai_observation_diagnostic_lockdown(
    *,
    input_feedback_comment: str,
    input_feedback_meta: Dict[str, Any],
    emotion_log_id: str,
    created_at: str,
) -> None:
    """Emit the Step2 submit-level structured diagnostic line.

    This is a diagnostic-only side effect.  It must never block emotion submit
    persistence and must never expose raw input or public comment text.
    """
    if not _emlis_ai_observation_diagnostic_lockdown_log_enabled():
        return

    try:
        lockdown = build_observation_diagnostic_lockdown(
            input_feedback_comment=input_feedback_comment,
            input_feedback_meta=(
                input_feedback_meta if isinstance(input_feedback_meta, dict) else {}
            ),
            emotion_log_id=str(emotion_log_id or ""),
            created_at=str(created_at or ""),
        )
        logger.info(
            "emlis_observation_diagnostic_lockdown %s",
            dump_observation_diagnostic(lockdown),
        )
    except Exception as exc:
        logger.warning(
            "emlis_observation_diagnostic_lockdown_failed error_type=%s",
            type(exc).__name__,
        )


def _log_emlis_ai_reply_failure(exc: Exception) -> None:
    """Log fail-closed EmlisAI reply failures without exposing raw input.

    The stack trace is kept behind the same opt-in debug flag because
    timeout/error paths can be noisy during normal emotion submission traffic.
    """
    if _emlis_ai_observation_result_log_enabled():
        logger.exception("emlis_ai_reply_failed")
    else:
        logger.warning(
            "emlis_ai_reply_failed fail_closed=True reason=timeout_or_error error_type=%s",
            type(exc).__name__,
        )


async def resolve_authenticated_user_id(
    *,
    authorization: Optional[str],
    legacy_user_id: Optional[str] = None,
) -> str:
    """Resolve authenticated user id with the same policy as `/emotion/submit`."""
    access_token = _extract_bearer_token(authorization)
    if access_token:
        return await _resolve_user_id_from_token(access_token)

    if ALLOW_LEGACY_USER_ID and legacy_user_id:
        return str(legacy_user_id)

    raise HTTPException(
        status_code=401,
        detail="Authorization header with Bearer token is required",
    )


def normalize_submission_payload(
    *,
    emotions: Sequence[Union[EmotionItem, str]],
    memo: Optional[str],
    memo_action: Optional[str],
    category: Optional[Sequence[str]],
) -> Dict[str, Any]:
    """Normalize emotion submit payload into storage-ready values."""
    emotions_tags, emotion_details, avg_strength = _normalize_emotions(emotions)
    if not emotions_tags:
        raise HTTPException(status_code=400, detail="At least one emotion is required")

    normalized_categories = _normalize_categories(category)
    has_memo_input = bool(str(memo or "").strip() or str(memo_action or "").strip())
    if not has_memo_input:
        normalized_categories = []

    return {
        "emotions_tags": emotions_tags,
        "emotion_details": emotion_details,
        "emotion_strength_avg": avg_strength,
        "category": normalized_categories,
        "has_memo_input": has_memo_input,
    }


async def persist_emotion_submission(
    *,
    user_id: str,
    emotions: Sequence[Union[EmotionItem, str]],
    memo: Optional[str],
    memo_action: Optional[str],
    category: Optional[Sequence[str]],
    created_at: Optional[str] = None,
    is_secret: bool = False,
    notify_friends: bool = True,
) -> Dict[str, Any]:
    """Persist one emotion submission and trigger the existing post-submit flow."""
    normalized = normalize_submission_payload(
        emotions=emotions,
        memo=memo,
        memo_action=memo_action,
        category=category,
    )

    effective_created_at = str(created_at or "").strip() or datetime.now(timezone.utc).isoformat()
    inserted = await _insert_emotion_row(
        user_id=str(user_id or "").strip(),
        emotions=normalized["emotions_tags"],
        emotion_details=normalized["emotion_details"],
        emotion_strength_avg=normalized["emotion_strength_avg"],
        memo=memo,
        memo_action=memo_action,
        category=normalized["category"],
        created_at=effective_created_at,
        is_secret=bool(is_secret),
    )

    try:
        await invalidate_prefix(f"input_summary:{user_id}")
    except Exception:
        pass

    try:
        await invalidate_prefix(f"myweb_home_summary:{user_id}")
    except Exception:
        pass

    activity_date = _global_summary_activity_date_from_created_at(
        inserted.get("created_at", effective_created_at)
    )
    try:
        await invalidate_prefix(f"global_summary:{activity_date}:")
    except Exception:
        pass

    _start_post_submit_background_tasks(
        user_id=str(user_id or "").strip(),
        emotion_details=normalized["emotion_details"],
        created_at=effective_created_at,
        avg_strength=normalized["emotion_strength_avg"],
        memo=memo,
        is_secret=bool(is_secret),
        notify_friends=bool(notify_friends),
    )

    input_feedback_seed = (
        f"{inserted.get('id') or ''}|{inserted.get('created_at', effective_created_at) or effective_created_at}"
    )

    # Phase 1: keep the legacy current_input keys stable while normalizing them
    # into EmlisAI's internal input-bundle shape (memo/thought, memo_action/action,
    # selected emotions, categories, selected_at/source id).  This is an internal
    # boundary only; /emotion/submit request/response and DB write paths stay the same.
    current_input = normalize_emlis_current_input({
        "id": inserted.get("id"),
        "created_at": inserted.get("created_at", effective_created_at),
        "emotions": normalized["emotions_tags"],
        "emotion_details": normalized["emotion_details"],
        "memo": memo,
        "memo_action": memo_action,
        "category": normalized["category"],
        "is_secret": bool(is_secret),
        "selection_seed": input_feedback_seed,
    })

    input_feedback_comment = ""
    internal_input_feedback_meta: Dict[str, Any] = {}
    try:
        subscription_tier = await get_subscription_tier_for_user(
            str(user_id or "").strip(),
            default=SubscriptionTier.FREE,
        )
    except Exception:
        subscription_tier = SubscriptionTier.FREE

    try:
        reply = await asyncio.wait_for(
            render_emlis_ai_reply(
                user_id=str(user_id or "").strip(),
                subscription_tier=subscription_tier,
                current_input=current_input,
            ),
            timeout=_emlis_ai_reply_timeout_seconds(),
        )
        input_feedback_comment = str(reply.comment_text or "").strip()
        internal_input_feedback_meta = reply.meta if isinstance(reply.meta, dict) else {}

        _log_emlis_ai_observation_result(
            input_feedback_comment=input_feedback_comment,
            input_feedback_meta=internal_input_feedback_meta,
        )
    except Exception as exc:
        _log_emlis_ai_reply_failure(exc)
        # Fail-closed: do not fall back to a fixed Emlis observation sentence.
        # The saved emotion remains successful, but Emlisの観測 is not shown.
        input_feedback_comment = ""
        internal_input_feedback_meta = {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": str(getattr(subscription_tier, "value", subscription_tier) or "free"),
            "observation_status": "unavailable",
            "rejection_reasons": ["emlis_ai_timeout_or_error"],
            "multi_perspective": {
                "fail_closed": True,
                "legacy_input_feedback_template_used": False,
                "legacy_safe_fallback_used": False,
            },
            "used_sources": ["current_input"],
            "used_memory_layers": ["canonical_history"],
            "fallback_used": False,
        }

    public_input_feedback_meta = build_public_emlis_input_feedback_meta(
        internal_input_feedback_meta,
        comment_text_present=bool(input_feedback_comment),
        subscription_tier=subscription_tier,
    )
    public_input_feedback_comment = _public_input_feedback_comment(
        input_feedback_comment,
        public_input_feedback_meta,
    )
    public_feedback_inclusion_summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=input_feedback_comment,
        internal_input_feedback_meta=internal_input_feedback_meta,
        public_input_feedback_meta=public_input_feedback_meta,
    )
    diagnostic_input_feedback_meta = _with_public_feedback_inclusion_summary(
        internal_input_feedback_meta=internal_input_feedback_meta,
        inclusion_summary=public_feedback_inclusion_summary,
    )

    _log_emlis_ai_observation_diagnostic_lockdown(
        input_feedback_comment=input_feedback_comment,
        input_feedback_meta=diagnostic_input_feedback_meta,
        emotion_log_id=str(inserted.get("id") or ""),
        created_at=str(
            inserted.get("created_at", effective_created_at) or effective_created_at
        ),
    )

    return {
        "inserted": inserted,
        "created_at": inserted.get("created_at", effective_created_at),
        "global_summary_activity_date": activity_date,
        "input_feedback_comment": public_input_feedback_comment,
        "input_feedback_meta": public_input_feedback_meta,
        "normalized": normalized,
    }


__all__ = [
    "normalize_submission_payload",
    "persist_emotion_submission",
    "resolve_authenticated_user_id",
]
