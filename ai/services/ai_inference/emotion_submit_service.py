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
from emlis_ai_observation_diagnostic_lockdown import (
    build_observation_diagnostic_lockdown,
    dump_observation_diagnostic,
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

    current_input = {
        "id": inserted.get("id"),
        "created_at": inserted.get("created_at", effective_created_at),
        "emotions": normalized["emotions_tags"],
        "emotion_details": normalized["emotion_details"],
        "memo": memo,
        "memo_action": memo_action,
        "category": normalized["category"],
        "is_secret": bool(is_secret),
        "selection_seed": input_feedback_seed,
    }

    input_feedback_comment = ""
    input_feedback_meta: Dict[str, Any] = {}
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
        input_feedback_meta = reply.meta if isinstance(reply.meta, dict) else {}

        _log_emlis_ai_observation_result(
            input_feedback_comment=input_feedback_comment,
            input_feedback_meta=input_feedback_meta,
        )
    except Exception as exc:
        _log_emlis_ai_reply_failure(exc)
        # Fail-closed: do not fall back to a fixed Emlis observation sentence.
        # The saved emotion remains successful, but Emlisの観測 is not shown.
        input_feedback_comment = ""
        input_feedback_meta = {
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

    _log_emlis_ai_observation_diagnostic_lockdown(
        input_feedback_comment=input_feedback_comment,
        input_feedback_meta=input_feedback_meta,
        emotion_log_id=str(inserted.get("id") or ""),
        created_at=str(
            inserted.get("created_at", effective_created_at) or effective_created_at
        ),
    )

    return {
        "inserted": inserted,
        "created_at": inserted.get("created_at", effective_created_at),
        "global_summary_activity_date": activity_date,
        "input_feedback_comment": input_feedback_comment,
        "input_feedback_meta": input_feedback_meta,
        "normalized": normalized,
    }


__all__ = [
    "normalize_submission_payload",
    "persist_emotion_submission",
    "resolve_authenticated_user_id",
]
