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
import time
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


_PHASE14_SPEED_REGRESSION_SCHEMA_VERSION = "cocolon.emlis.submit_speed_regression.v1"
_PHASE14_SPEED_REGRESSION_PHASE = "Phase14_speed_regression"
_DAILY_RECEPTION_MODE_IDS = {"daily_unpleasant_reception", "daily_positive_reception"}
_PHASE19_PUBLIC_SAFE_MODE_ID_ALIASES = {
    "self_understanding_learning_shift": "self_understanding_follow",
    "relationship_gratitude_recovery": "relationship_reception",
}
_SUBMIT_SPEED_REGRESSION_MAX_REASON_CODES = 20
_SUBMIT_SPEED_REGRESSION_MAX_REASON_LENGTH = 96




def _phase14_public_safe_reception_mode_id(value: Any) -> str:
    mode_id = _phase14_clean_identifier(value, limit=80)
    if not mode_id:
        return ""
    return _PHASE19_PUBLIC_SAFE_MODE_ID_ALIASES.get(mode_id, mode_id)

def _phase14_perf_counter() -> float:
    return time.perf_counter()


def _phase14_elapsed_ms(started_at: float | None) -> int:
    if started_at is None:
        return 0
    try:
        return max(0, int(round((time.perf_counter() - float(started_at)) * 1000.0)))
    except Exception:
        return 0


def _phase14_safe_int(value: Any, *, maximum: int = 600_000) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(round(float(value)))
    except Exception:
        return None
    return max(0, min(maximum, number))


def _phase14_clean_identifier(value: Any, *, limit: int = 120) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    allowed = []
    for char in text[:limit]:
        if char.isalnum() or char in {"_", "-", ".", ":", "/"}:
            allowed.append(char)
    return "".join(allowed)


def _phase14_reason_codes(values: Any, *, limit: int = _SUBMIT_SPEED_REGRESSION_MAX_REASON_CODES) -> list[str]:
    if values is None:
        source: list[Any] = []
    elif isinstance(values, (str, bytes, bytearray)):
        source = [values]
    elif isinstance(values, (list, tuple, set)):
        source = list(values)
    else:
        source = [values]
    out: list[str] = []
    for raw in source:
        code = _phase14_clean_identifier(raw, limit=_SUBMIT_SPEED_REGRESSION_MAX_REASON_LENGTH)
        if not code or code in out:
            continue
        out.append(code)
        if len(out) >= limit:
            break
    return out


def _phase14_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _phase14_nested_mappings(meta: Dict[str, Any]) -> list[Dict[str, Any]]:
    diagnostic_summary = _phase14_mapping(meta.get("diagnostic_summary"))
    multi_perspective = _phase14_mapping(meta.get("multi_perspective"))
    composer_meta = _phase14_mapping(meta.get("composer_meta"))
    phase_gate = _phase14_mapping(meta.get("phase_gate"))
    gate_trace = _phase14_mapping(meta.get("gate_trace"))
    out = [meta, diagnostic_summary, multi_perspective, composer_meta, phase_gate, gate_trace]
    for source in (diagnostic_summary, multi_perspective, composer_meta, phase_gate, gate_trace):
        nested_gate_trace = _phase14_mapping(source.get("gate_trace"))
        if nested_gate_trace:
            out.append(nested_gate_trace)
        nested_composer_meta = _phase14_mapping(source.get("composer_meta"))
        if nested_composer_meta:
            out.append(nested_composer_meta)
    return [item for item in out if item]


def _phase14_find_elapsed_ms(meta: Dict[str, Any], *keys: str) -> int | None:
    for source in _phase14_nested_mappings(meta):
        for key in keys:
            value = _phase14_safe_int(source.get(key))
            if value is not None:
                return value
    return None


def _phase14_find_mapping(meta: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    for source in _phase14_nested_mappings(meta):
        for key in keys:
            value = source.get(key)
            if isinstance(value, dict):
                return dict(value)
    return {}


def _build_phase14_reception_mode_timing_probe(current_input: Any) -> Dict[str, Any]:
    """Build a tiny meta-only timing probe for the daily-reception branch.

    Phase 14 needs submit-time visibility into whether the two-stage daily
    reception branch stayed light.  This probe only resolves shared evidence and
    reception mode; it never generates surface text and it never returns raw
    input or comment bodies.
    """

    probe_started = _phase14_perf_counter()
    shared_elapsed_ms = 0
    resolver_elapsed_ms = 0
    try:
        from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence
        from emlis_ai_reception_mode_resolver import resolve_emlis_reception_mode

        shared_started = _phase14_perf_counter()
        shared_evidence = build_emlis_shared_reception_evidence(current_input)
        shared_elapsed_ms = _phase14_elapsed_ms(shared_started)

        resolver_started = _phase14_perf_counter()
        resolution = resolve_emlis_reception_mode(
            current_input,
            shared_evidence=shared_evidence,
        )
        resolver_elapsed_ms = _phase14_elapsed_ms(resolver_started)
        resolution_meta = resolution.as_meta() if hasattr(resolution, "as_meta") else {}
        reception_mode_id = _phase14_public_safe_reception_mode_id(
            resolution_meta.get("reception_mode_id")
            or resolution_meta.get("reception_mode")
            or resolution_meta.get("selected_reception_mode_id")
        )
        return {
            "probe_succeeded": True,
            "probe_elapsed_ms": _phase14_elapsed_ms(probe_started),
            "shared_evidence_elapsed_ms": shared_elapsed_ms,
            "reception_mode_elapsed_ms": resolver_elapsed_ms,
            "reception_mode_id": reception_mode_id,
            "reception_mode_family": "daily_reception" if reception_mode_id in _DAILY_RECEPTION_MODE_IDS else _phase14_clean_identifier(resolution_meta.get("reception_mode_family"), limit=80),
            "daily_reception_branch": reception_mode_id in _DAILY_RECEPTION_MODE_IDS,
            "low_information_question_allowed": bool(resolution_meta.get("low_information_question_allowed")),
            "question_required": bool(resolution_meta.get("question_required")),
            "event_fact_present": bool(resolution_meta.get("event_fact_present")),
            "reaction_present": bool(resolution_meta.get("reaction_present")),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
        }
    except Exception as exc:
        return {
            "probe_succeeded": False,
            "probe_elapsed_ms": _phase14_elapsed_ms(probe_started),
            "shared_evidence_elapsed_ms": shared_elapsed_ms,
            "reception_mode_elapsed_ms": resolver_elapsed_ms,
            "reception_mode_id": "",
            "reception_mode_family": "",
            "daily_reception_branch": False,
            "probe_error_type": _phase14_clean_identifier(type(exc).__name__, limit=80),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
        }


def _build_submit_speed_regression_summary(
    *,
    trace_id: str,
    reply_elapsed_ms: int,
    reply_timeout_budget_ms: int,
    public_meta_elapsed_ms: int,
    submit_elapsed_ms: int,
    internal_input_feedback_meta: Dict[str, Any],
    public_input_feedback_meta: Dict[str, Any],
    reception_probe: Dict[str, Any],
    comment_text_present: bool,
    public_feedback_included: bool,
    saved_emotion_success: bool,
    reply_timeout: bool,
    reply_error_type: str = "",
) -> Dict[str, Any]:
    internal_meta = internal_input_feedback_meta if isinstance(internal_input_feedback_meta, dict) else {}
    public_meta = public_input_feedback_meta if isinstance(public_input_feedback_meta, dict) else {}
    probe = reception_probe if isinstance(reception_probe, dict) else {}

    observation_status = _phase14_clean_identifier(
        public_meta.get("observation_status") or internal_meta.get("observation_status") or "unavailable",
        limit=40,
    ) or "unavailable"
    reason_codes = _phase14_reason_codes(
        [
            *(internal_meta.get("rejection_reasons") or [] if isinstance(internal_meta.get("rejection_reasons"), list) else []),
            *(public_meta.get("rejection_reasons") or [] if isinstance(public_meta.get("rejection_reasons"), list) else []),
        ]
    )
    if reply_timeout and "emlis_ai_reply_timeout" not in reason_codes:
        reason_codes = ["emlis_ai_reply_timeout", *reason_codes]
    elif reply_error_type and not reply_timeout and "emlis_ai_reply_error" not in reason_codes:
        reason_codes = ["emlis_ai_reply_error", *reason_codes]
    reason_codes = _phase14_reason_codes(reason_codes)

    visible_gate = _phase14_find_mapping(public_meta, "visible_surface_acceptance_gate")
    runtime_gate = _phase14_find_mapping(public_meta, "runtime_surface_pre_return_gate")
    state_gate = _phase14_find_mapping(public_meta, "state_answer_gate_boundary")
    two_stage_gate = _phase14_find_mapping(public_meta, "two_stage_reception_gate")

    fail_closed_reason_code = ""
    if public_feedback_included:
        fail_closed_reason_code = ""
    elif reply_timeout:
        fail_closed_reason_code = "emlis_ai_reply_timeout"
    elif reply_error_type:
        fail_closed_reason_code = "emlis_ai_reply_error"
    elif two_stage_gate.get("passed") is False or two_stage_gate.get("blocked") is True:
        fail_closed_reason_code = "two_stage_reception_gate_blocked"
    elif state_gate.get("passed") is False or state_gate.get("blocked") is True:
        fail_closed_reason_code = "state_answer_gate_blocked"
    elif visible_gate.get("passed") is False:
        fail_closed_reason_code = "visible_surface_gate_blocked"
    elif runtime_gate.get("passed") is False:
        fail_closed_reason_code = "runtime_surface_gate_blocked"
    elif not comment_text_present:
        fail_closed_reason_code = "comment_text_missing"
    elif observation_status != "passed":
        fail_closed_reason_code = "non_passed_observation_status"
    else:
        fail_closed_reason_code = "public_feedback_not_included"

    reply_completed_within_budget = bool(
        not reply_timeout and reply_elapsed_ms <= max(0, int(reply_timeout_budget_ms))
    )
    reception_mode_id = _phase14_public_safe_reception_mode_id(
        probe.get("reception_mode_id")
        or internal_meta.get("reception_mode_id")
        or _phase14_find_mapping(internal_meta, "reception_mode_resolution").get("reception_mode_id")
    )
    reception_mode_family = _phase14_clean_identifier(
        probe.get("reception_mode_family")
        or ("daily_reception" if reception_mode_id in _DAILY_RECEPTION_MODE_IDS else ""),
        limit=80,
    )

    summary: Dict[str, Any] = {
        "schema_version": _PHASE14_SPEED_REGRESSION_SCHEMA_VERSION,
        "source_phase": _PHASE14_SPEED_REGRESSION_PHASE,
        "trace_id": _phase14_clean_identifier(trace_id, limit=120),
        "reply_elapsed_ms": max(0, int(reply_elapsed_ms)),
        "reply_timeout_budget_ms": max(0, int(reply_timeout_budget_ms)),
        "reply_completed_within_budget": reply_completed_within_budget,
        "reply_timeout": bool(reply_timeout),
        "reply_error_type": _phase14_clean_identifier(reply_error_type, limit=80),
        "eligibility_elapsed_ms": _phase14_find_elapsed_ms(internal_meta, "eligibility_elapsed_ms", "observation_eligibility_elapsed_ms") or 0,
        "shared_evidence_elapsed_ms": _phase14_safe_int(probe.get("shared_evidence_elapsed_ms")) or _phase14_find_elapsed_ms(internal_meta, "shared_evidence_elapsed_ms", "reception_shared_evidence_elapsed_ms") or 0,
        "reception_mode_elapsed_ms": _phase14_safe_int(probe.get("reception_mode_elapsed_ms")) or _phase14_find_elapsed_ms(internal_meta, "reception_mode_elapsed_ms", "reception_mode_resolver_elapsed_ms") or 0,
        "composer_elapsed_ms": _phase14_find_elapsed_ms(internal_meta, "composer_elapsed_ms", "conversation_composer_elapsed_ms", "complete_composer_elapsed_ms") or 0,
        "runtime_gate_elapsed_ms": _phase14_find_elapsed_ms(internal_meta, "runtime_gate_elapsed_ms", "runtime_surface_gate_elapsed_ms", "runtime_surface_pre_return_gate_elapsed_ms") or 0,
        "visible_gate_elapsed_ms": _phase14_find_elapsed_ms(internal_meta, "visible_gate_elapsed_ms", "visible_surface_gate_elapsed_ms", "visible_surface_acceptance_gate_elapsed_ms") or 0,
        "public_meta_elapsed_ms": max(0, int(public_meta_elapsed_ms)),
        "submit_elapsed_ms": max(0, int(submit_elapsed_ms)),
        "observation_status": observation_status,
        "comment_text_present": bool(comment_text_present),
        "public_feedback_included": bool(public_feedback_included),
        "saved_emotion_success": bool(saved_emotion_success),
        "emlis_display_fail_closed": bool(saved_emotion_success and not public_feedback_included),
        "fail_closed_reason_code": _phase14_clean_identifier(fail_closed_reason_code, limit=96),
        "reason_codes": reason_codes,
        "reception_mode_id": reception_mode_id,
        "reception_mode_family": reception_mode_family,
        "daily_reception_branch": bool(probe.get("daily_reception_branch") or reception_mode_id in _DAILY_RECEPTION_MODE_IDS),
        "reception_probe_succeeded": bool(probe.get("probe_succeeded")),
        "reception_probe_elapsed_ms": _phase14_safe_int(probe.get("probe_elapsed_ms")) or 0,
        "heavy_diagnostics_added_before_display": False,
        "general_dictionary_lookup_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
    }
    if not summary["reply_error_type"]:
        summary.pop("reply_error_type", None)
    if not summary["fail_closed_reason_code"]:
        summary.pop("fail_closed_reason_code", None)
    if not summary["reception_mode_id"]:
        summary.pop("reception_mode_id", None)
    if not summary["reception_mode_family"]:
        summary.pop("reception_mode_family", None)
    if not summary["reason_codes"]:
        summary.pop("reason_codes", None)
    return summary


def _attach_submit_speed_regression_summary(
    meta: Dict[str, Any],
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(meta, dict) or not isinstance(summary, dict) or not summary:
        return meta if isinstance(meta, dict) else {}
    meta["submit_speed_regression"] = dict(summary)
    diagnostic_summary = dict(meta.get("diagnostic_summary") or {}) if isinstance(meta.get("diagnostic_summary"), dict) else {}
    diagnostic_summary["submit_speed_regression"] = dict(summary)
    meta["diagnostic_summary"] = diagnostic_summary
    return meta


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


def _public_state_answer_gate_blocks(public_meta: Dict[str, Any]) -> bool:
    gate = public_meta.get("state_answer_gate_boundary") if isinstance(public_meta, dict) else None
    if not isinstance(gate, dict):
        return False
    if gate.get("passed") is False:
        return True
    if gate.get("blocked") is True or gate.get("terminal_surface_block") is True:
        return True
    reasons = gate.get("rejection_reasons")
    if isinstance(reasons, list) and reasons:
        return True
    return False


def _public_two_stage_gate_blocks(public_meta: Dict[str, Any]) -> bool:
    if not isinstance(public_meta, dict):
        return False

    def _gate_blocks(gate: Any) -> bool:
        if not isinstance(gate, dict):
            return False
        if gate.get("passed") is False:
            return True
        if gate.get("blocked") is True:
            return True
        if gate.get("terminal_surface_block") is True:
            return True
        for key in ("rejection_reasons", "surface_blocker_reasons"):
            values = gate.get(key)
            if isinstance(values, list) and values:
                return True
        return False

    if _gate_blocks(public_meta.get("two_stage_reception_gate")):
        return True

    state_gate = public_meta.get("state_answer_gate_boundary")
    if isinstance(state_gate, dict):
        if state_gate.get("two_stage_reception_gate_terminal_surface_block") is True:
            return True
        if (
            state_gate.get("two_stage_reception_cross_gate_active") is True
            and state_gate.get("two_stage_reception_gate_connected") is True
            and state_gate.get("two_stage_reception_gate_passed") is False
        ):
            return True
        values = state_gate.get("two_stage_reception_gate_rejection_reasons")
        if isinstance(values, list) and values:
            return True
        if _gate_blocks(state_gate.get("two_stage_reception_gate")):
            return True

    visible_gate = public_meta.get("visible_surface_acceptance_gate")
    if isinstance(visible_gate, dict):
        if visible_gate.get("two_stage_reception_gate_terminal_surface_block") is True:
            return True
        values = visible_gate.get("two_stage_reception_gate_rejection_reasons")
        if isinstance(values, list) and values:
            return True
        if _gate_blocks(visible_gate.get("two_stage_reception_gate")):
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
    state_answer_gate_blocks = _public_state_answer_gate_blocks(public_meta)
    two_stage_gate_blocks = _public_two_stage_gate_blocks(public_meta)
    visible_gate = public_meta.get("visible_surface_acceptance_gate") if isinstance(public_meta.get("visible_surface_acceptance_gate"), dict) else {}
    runtime_gate = public_meta.get("runtime_surface_pre_return_gate") if isinstance(public_meta.get("runtime_surface_pre_return_gate"), dict) else {}
    state_answer_gate = public_meta.get("state_answer_gate_boundary") if isinstance(public_meta.get("state_answer_gate_boundary"), dict) else {}
    two_stage_gate = public_meta.get("two_stage_reception_gate") if isinstance(public_meta.get("two_stage_reception_gate"), dict) else {}
    nested_two_stage_gate = state_answer_gate.get("two_stage_reception_gate") if isinstance(state_answer_gate.get("two_stage_reception_gate"), dict) else {}
    reason_codes = _safe_reason_codes(
        [
            *(public_meta.get("rejection_reasons") or [] if isinstance(public_meta.get("rejection_reasons"), list) else []),
            *(visible_gate.get("rejection_reasons") or [] if isinstance(visible_gate.get("rejection_reasons"), list) else []),
            *(runtime_gate.get("rejection_reasons") or [] if isinstance(runtime_gate.get("rejection_reasons"), list) else []),
            *(state_answer_gate.get("rejection_reasons") or [] if isinstance(state_answer_gate.get("rejection_reasons"), list) else []),
            *(state_answer_gate.get("two_stage_reception_gate_rejection_reasons") or [] if isinstance(state_answer_gate.get("two_stage_reception_gate_rejection_reasons"), list) else []),
            *(two_stage_gate.get("rejection_reasons") or [] if isinstance(two_stage_gate.get("rejection_reasons"), list) else []),
            *(two_stage_gate.get("surface_blocker_reasons") or [] if isinstance(two_stage_gate.get("surface_blocker_reasons"), list) else []),
            *(nested_two_stage_gate.get("rejection_reasons") or [] if isinstance(nested_two_stage_gate.get("rejection_reasons"), list) else []),
            *(nested_two_stage_gate.get("surface_blocker_reasons") or [] if isinstance(nested_two_stage_gate.get("surface_blocker_reasons"), list) else []),
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
    public_feedback_not_included_state_answer_gate = bool(not public_feedback_included and state_answer_gate_blocks)
    public_feedback_not_included_two_stage_reception_gate = bool(not public_feedback_included and two_stage_gate_blocks)
    public_feedback_not_included_reply_timeout_or_error = bool(
        not public_feedback_included
        and any(
            reason in {"emlis_ai_timeout_or_error", "emlis_ai_reply_timeout", "emlis_ai_reply_error"}
            for reason in reason_codes
        )
    )
    rn_payload_absent = bool(not public_feedback_included)
    candidate_fail_closed_display_absent = bool(
        existing.get("candidate_fail_closed_display_absent") is True
        or rn_payload_absent
        or public_feedback_not_included_non_passed
        or public_feedback_not_included_empty_comment_text
        or public_feedback_not_included_visible_surface_gate
        or public_feedback_not_included_state_answer_gate
        or public_feedback_not_included_two_stage_reception_gate
        or public_feedback_not_included_reply_timeout_or_error
    )
    if public_feedback_not_included_reply_timeout_or_error:
        reason_family = "reply_timeout_or_error"
    elif public_feedback_not_included_two_stage_reception_gate:
        reason_family = "two_stage_reception_gate"
    elif public_feedback_not_included_state_answer_gate:
        reason_family = "state_answer_gate"
    elif public_feedback_not_included_visible_surface_gate:
        reason_family = "visible_surface_gate"
    elif candidate_blocked_koto_splice:
        reason_family = "koto_splice"
    elif candidate_blocked_relation_skeleton:
        reason_family = "relation_skeleton"
    elif candidate_blocked_surface_grammar:
        reason_family = "surface_grammar"
    elif public_feedback_not_included_empty_comment_text:
        reason_family = "empty_comment_text"
    elif public_feedback_not_included_non_passed:
        reason_family = "non_passed"
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
        "public_feedback_not_included_state_answer_gate": public_feedback_not_included_state_answer_gate,
        "public_feedback_not_included_two_stage_reception_gate": public_feedback_not_included_two_stage_reception_gate,
        "public_feedback_not_included_reply_timeout_or_error": public_feedback_not_included_reply_timeout_or_error,
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
    submit_started_at = _phase14_perf_counter()
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

    phase14_reception_probe = _build_phase14_reception_mode_timing_probe(current_input)

    input_feedback_comment = ""
    internal_input_feedback_meta: Dict[str, Any] = {}
    try:
        subscription_tier = await get_subscription_tier_for_user(
            str(user_id or "").strip(),
            default=SubscriptionTier.FREE,
        )
    except Exception:
        subscription_tier = SubscriptionTier.FREE

    reply_timeout_budget_seconds = _emlis_ai_reply_timeout_seconds()
    reply_timeout_budget_ms = max(0, int(round(reply_timeout_budget_seconds * 1000.0)))
    reply_started_at = _phase14_perf_counter()
    reply_elapsed_ms = 0
    reply_timeout = False
    reply_error_type = ""

    try:
        reply = await asyncio.wait_for(
            render_emlis_ai_reply(
                user_id=str(user_id or "").strip(),
                subscription_tier=subscription_tier,
                current_input=current_input,
            ),
            timeout=reply_timeout_budget_seconds,
        )
        reply_elapsed_ms = _phase14_elapsed_ms(reply_started_at)
        input_feedback_comment = str(reply.comment_text or "").strip()
        internal_input_feedback_meta = reply.meta if isinstance(reply.meta, dict) else {}

        _log_emlis_ai_observation_result(
            input_feedback_comment=input_feedback_comment,
            input_feedback_meta=internal_input_feedback_meta,
        )
    except asyncio.TimeoutError as exc:
        reply_elapsed_ms = _phase14_elapsed_ms(reply_started_at)
        reply_timeout = True
        reply_error_type = type(exc).__name__
        _log_emlis_ai_reply_failure(exc)
        # Fail-closed: the saved emotion remains successful, but Emlisの観測
        # is not shown and the reason is explicit for Phase 14 diagnosis.
        input_feedback_comment = ""
        internal_input_feedback_meta = {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": str(getattr(subscription_tier, "value", subscription_tier) or "free"),
            "observation_status": "unavailable",
            "rejection_reasons": ["emlis_ai_timeout_or_error", "emlis_ai_reply_timeout"],
            "multi_perspective": {
                "fail_closed": True,
                "fail_closed_reason_code": "emlis_ai_reply_timeout",
                "legacy_input_feedback_template_used": False,
                "legacy_safe_fallback_used": False,
            },
            "used_sources": ["current_input"],
            "used_memory_layers": ["canonical_history"],
            "fallback_used": False,
        }
    except Exception as exc:
        reply_elapsed_ms = _phase14_elapsed_ms(reply_started_at)
        reply_error_type = type(exc).__name__
        _log_emlis_ai_reply_failure(exc)
        # Fail-closed: do not fall back to a fixed Emlis observation sentence.
        # The saved emotion remains successful, but Emlisの観測 is not shown.
        input_feedback_comment = ""
        internal_input_feedback_meta = {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": str(getattr(subscription_tier, "value", subscription_tier) or "free"),
            "observation_status": "unavailable",
            "rejection_reasons": ["emlis_ai_timeout_or_error", "emlis_ai_reply_error"],
            "multi_perspective": {
                "fail_closed": True,
                "fail_closed_reason_code": "emlis_ai_reply_error",
                "legacy_input_feedback_template_used": False,
                "legacy_safe_fallback_used": False,
            },
            "used_sources": ["current_input"],
            "used_memory_layers": ["canonical_history"],
            "fallback_used": False,
        }

    public_meta_started_at = _phase14_perf_counter()
    public_input_feedback_meta = build_public_emlis_input_feedback_meta(
        internal_input_feedback_meta,
        comment_text_present=bool(input_feedback_comment),
        subscription_tier=subscription_tier,
    )
    public_meta_elapsed_ms = _phase14_elapsed_ms(public_meta_started_at)
    public_input_feedback_comment = _public_input_feedback_comment(
        input_feedback_comment,
        public_input_feedback_meta,
    )
    public_feedback_included = bool(public_input_feedback_comment)
    public_feedback_inclusion_summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=input_feedback_comment,
        internal_input_feedback_meta=internal_input_feedback_meta,
        public_input_feedback_meta=public_input_feedback_meta,
    )
    phase14_trace_id = (
        str(internal_input_feedback_meta.get("observation_trace_id") or "").strip()
        or str(internal_input_feedback_meta.get("trace_id") or "").strip()
        or f"emotion-log:{inserted.get('id') or ''}"
    )
    submit_speed_regression_summary = _build_submit_speed_regression_summary(
        trace_id=phase14_trace_id,
        reply_elapsed_ms=reply_elapsed_ms,
        reply_timeout_budget_ms=reply_timeout_budget_ms,
        public_meta_elapsed_ms=public_meta_elapsed_ms,
        submit_elapsed_ms=_phase14_elapsed_ms(submit_started_at),
        internal_input_feedback_meta=internal_input_feedback_meta,
        public_input_feedback_meta=public_input_feedback_meta,
        reception_probe=phase14_reception_probe,
        comment_text_present=bool(input_feedback_comment),
        public_feedback_included=public_feedback_included,
        saved_emotion_success=True,
        reply_timeout=reply_timeout,
        reply_error_type=reply_error_type,
    )
    public_input_feedback_meta = _attach_submit_speed_regression_summary(
        public_input_feedback_meta,
        submit_speed_regression_summary,
    )
    internal_input_feedback_meta = _attach_submit_speed_regression_summary(
        internal_input_feedback_meta,
        submit_speed_regression_summary,
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
