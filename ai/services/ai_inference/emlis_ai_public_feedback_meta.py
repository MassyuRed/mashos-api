# -*- coding: utf-8 -*-
"""Public EmlisAI input-feedback meta boundary.

This module keeps the internal EmlisAI reply meta out of the public
``/emotion/submit`` response.  It exposes only a small additive metadata subset
needed by RN display/debug contracts and never returns raw input, evidence text,
comment text, graph payloads, scorecards, or complete diagnostics.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from enum import Enum
from typing import Any, Dict, Iterable, Optional

from emlis_ai_response_contract import (
    internal_response_contract_from_meta,
    public_status_from_internal_response_contract,
)
from emlis_ai_state_answer_gate_boundary import state_answer_gate_boundary_public_summary
from emlis_ai_two_stage_reception_gate import two_stage_reception_gate_public_summary
from emlis_ai_user_label_connection_public_meta import (
    USER_LABEL_CONNECTION_META_ONLY_META_KEY,
    USER_LABEL_CONNECTION_PUBLIC_META_KEY,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY,
    user_label_connection_public_summary,
)


PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION = "emlis.public_input_feedback_meta.v1"
PUBLIC_EMLIS_FEEDBACK_META_BOUNDARY_VERSION = "emlis.public_feedback_meta_boundary.v1"
PUBLIC_EMLIS_FEEDBACK_META_TARGET_BYTES = 8 * 1024
PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES = 12 * 1024
PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS = 20
PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH = 96
PUBLIC_EMLIS_FEEDBACK_META_MAX_GATE_RESULTS = 20
PUBLIC_EMLIS_FEEDBACK_META_MAX_SURFACE_CODE_COUNT = 16
PUBLIC_EMLIS_FEEDBACK_META_MAX_SURFACE_COUNT = 32

_DEFAULT_VERSION = "emlis_ai_v3"
_DEFAULT_KERNEL_VERSION = "multi_perspective_observation.v1"
_DEFAULT_TIER = "free"
_ALLOWED_OBSERVATION_STATUSES = {"passed", "rejected", "unavailable", "safety_blocked"}
_ALLOWED_OBSERVATION_REPLY_KINDS = {
    "eligible_observation",
    "low_information_observation",
}
_ALLOWED_VISIBLE_SURFACE_ACCEPTANCE_CLASSIFICATIONS = {"pass", "yellow", "repair_required", "red"}
_ALLOWED_VISIBLE_SURFACE_ACCEPTANCE_ACTIONS = {
    "allow",
    "warn",
    "rerender_surface",
    "reroute_low_information",
    "block",
    "fail_closed",
}
_BLOCKING_VISIBLE_SURFACE_ACCEPTANCE_CLASSIFICATIONS = {"repair_required", "red"}
_BLOCKING_VISIBLE_SURFACE_ACCEPTANCE_ACTIONS = {
    "rerender_surface",
    "reroute_low_information",
    "block",
    "fail_closed",
}
_BLOCKING_RUNTIME_SURFACE_ACTIONS = {
    "rerender_shallow_v2",
    "rerender_surface",
    "reroute_low_information",
    "block",
    "fail_closed",
}
_TWO_STAGE_RECEPTION_GATE_SOURCE_KEYS = (
    "two_stage_reception_gate",
    "two_stage_reception_cross_gate",
    "emlis_ai_two_stage_reception_gate",
    "emlis_two_stage_reception_gate",
)
_TWO_STAGE_RECEPTION_GATE_CONTAINER_KEYS = (
    "state_answer_gate_boundary",
    "state_answer_gate_public_meta_boundary",
    "visible_surface_acceptance_gate",
    "visible_surface_acceptance",
    "runtime_surface_pre_return_gate",
    "gate_trace",
    "phase_gate",
    "diagnostic_summary",
    "composer_meta",
    "multi_perspective",
)
_ENVIRONMENT_STATE_OUTPUT_TERMINAL_SURFACE_REASONS = {
    "environment_state_output_scope_marker_missing",
    "environment_state_output_empty_body",
    "environment_state_output_body_line_missing",
    "period_tendency_from_single_record_surface",
    "personality_tendency_surface",
    "diagnosis_surface",
    "cause_from_category_surface",
    "cause_from_emotion_strength_surface",
    "recovery_prescription_surface",
}
_VISIBLE_SURFACE_ACCEPTANCE_UNSAFE_CONTRACT_FLAGS = (
    "api_route_changed",
    "comment_text_body_included",
    "comment_text_included",
    "db_physical_name_changed",
    "display_gate_relaxed",
    "external_ai_used",
    "fixed_sentence_template_added",
    "gate_relaxed",
    "grounding_gate_relaxed",
    "input_specific_template_used",
    "input_text_included",
    "local_llm_used",
    "public_response_key_change",
    "raw_input_included",
    "raw_text_included",
    "reader_gate_relaxed",
    "response_shape_changed",
    "rn_visible_contract_changed",
    "template_gate_relaxed",
)
_INTERNAL_RESPONSE_CONTRACT_PUBLIC_FORBIDDEN_KEYS = frozenset(
    {
        "internal_response_contract",
        "internal_response_contract_schema_version",
        "response_kind",
        "public_input_feedback_allowed",
        "comment_text_required",
        "safety_triage_kind",
        "grounding_scope",
        "repair_attempts",
        "visible_material_slots",
        "unknown_slots",
        "material_quality",
        "generic_relation_material_ids",
        "reception_mode_id",
        "selected_reception_mode_id",
        "two_stage_reception_mode_id",
        "reception_mode_family",
        "mode_id",
        "mode",
        "mode_specific_rejection_reasons",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "evidence_text",
        "evidenceText",
    }
)
_INTERNAL_RUNTIME_MODE_PUBLIC_FORBIDDEN_VALUES = frozenset(
    {
        "normal_observation",
        "low_information_observation",
        "limited_grounding_observation",
        "self_denial_safe_state_answer",
        "safety_support_required",
        "safety_blocked_emergency",
        "infrastructure_error",
        "generic_sentence_plan_surface",
    }
)
_INTERNAL_RUNTIME_IDENTIFIER_FORBIDDEN_MARKERS = (
    "_runtime_mode",
    "_case_route",
    "_case_specific_route",
    "_learning_shift",
    "_gratitude_recovery",
)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


def _compact_json_bytes(value: Mapping[str, Any]) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _boundary_marker(*, trimmed: bool) -> Dict[str, Any]:
    return {
        "version": PUBLIC_EMLIS_FEEDBACK_META_BOUNDARY_VERSION,
        "sanitized": True,
        "max_bytes": PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES,
        "trimmed": bool(trimmed),
        "internal_meta_returned": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _minimal_unavailable_meta(
    *,
    subscription_tier: Any = None,
    reason: str = "public_feedback_meta_sanitizer_failed",
) -> Dict[str, Any]:
    return {
        "schema_version": PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION,
        "version": _DEFAULT_VERSION,
        "kernel_version": _DEFAULT_KERNEL_VERSION,
        "tier": _coerce_tier(subscription_tier),
        "observation_status": "unavailable",
        "rejection_reasons": [_safe_reason(reason) or "public_feedback_meta_sanitizer_failed"],
        "public_feedback_meta_boundary": _boundary_marker(trimmed=True),
    }


def _coerce_tier(value: Any) -> str:
    if isinstance(value, Enum):
        raw = value.value
    else:
        raw = getattr(value, "value", value)
    text = str(raw or "").strip() or _DEFAULT_TIER
    return _safe_identifier(text, max_length=40, default=_DEFAULT_TIER)


def _safe_identifier(value: Any, *, max_length: int, default: Optional[str] = None) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return default
    text = text[:max_length]
    if not _IDENTIFIER_RE.match(text):
        return default
    return text


def _safe_public_identifier(value: Any, *, max_length: int, default: Optional[str] = None) -> Optional[str]:
    """Return a public-safe identifier without leaking internal routing names.

    Phase20-7 keeps RN display owned by ``input_feedback.comment_text`` plus
    public ``observation_status``.  Internal response contracts, response_kind
    and backend runtime mode names are useful inside diagnostics, but they must
    not become public response fields or RN-visible display sources.
    """

    text = _safe_identifier(value, max_length=max_length, default=default)
    if text is None:
        return default
    if text in _INTERNAL_RESPONSE_CONTRACT_PUBLIC_FORBIDDEN_KEYS:
        return default
    if text in _INTERNAL_RUNTIME_MODE_PUBLIC_FORBIDDEN_VALUES:
        return default
    if any(marker in text for marker in _INTERNAL_RUNTIME_IDENTIFIER_FORBIDDEN_MARKERS):
        return default
    return text


def _safe_trace(value: Any) -> Optional[str]:
    return _safe_identifier(value, max_length=120, default=None)


def _safe_status(value: Any) -> Optional[str]:
    text = _safe_identifier(value, max_length=40, default=None)
    if text in _ALLOWED_OBSERVATION_STATUSES:
        return text
    return None


def _safe_reply_kind(value: Any) -> Optional[str]:
    text = _safe_identifier(value, max_length=80, default=None)
    if text in _ALLOWED_OBSERVATION_REPLY_KINDS:
        return text
    return None


def _safe_visible_surface_acceptance_classification(value: Any) -> Optional[str]:
    text = _safe_identifier(value, max_length=40, default=None)
    if text in _ALLOWED_VISIBLE_SURFACE_ACCEPTANCE_CLASSIFICATIONS:
        return text
    return None


def _safe_visible_surface_acceptance_action(value: Any) -> Optional[str]:
    text = _safe_identifier(value, max_length=80, default=None)
    if text in _ALLOWED_VISIBLE_SURFACE_ACCEPTANCE_ACTIONS:
        return text
    return None


def _safe_reason(value: Any) -> Optional[str]:
    return _safe_public_identifier(
        value,
        max_length=PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH,
        default=None,
    )


def _safe_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    return None


def _safe_int(value: Any, *, minimum: int = 0, maximum: int = PUBLIC_EMLIS_FEEDBACK_META_MAX_SURFACE_COUNT) -> Optional[int]:
    if isinstance(value, bool):
        return None
    try:
        integer = int(value)
    except Exception:
        return None
    return max(minimum, min(maximum, integer))


def _safe_mapping(value: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return value
    return None


def _safe_get(meta: Mapping[str, Any], key: str, default: Any = None) -> Any:
    return meta.get(key, default)


def _internal_response_contract_or_none(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    # Phase20-1: the internal response contract may guide the public status
    # bridge, but it is never copied into public RN-facing meta.
    return internal_response_contract_from_meta(internal_meta)


def _contract_comment_required(contract: Mapping[str, Any] | None) -> Optional[bool]:
    if contract is None or not isinstance(contract.get("comment_text_required"), bool):
        return None
    return bool(contract.get("comment_text_required"))


def _safe_rejection_reasons(values: Any) -> list[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes, bytearray)):
        return []
    reasons: list[str] = []
    for raw in values:
        reason = _safe_reason(raw)
        if not reason or reason in reasons:
            continue
        reasons.append(reason)
        if len(reasons) >= PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS:
            break
    return reasons


def _prepend_public_rejection_reason(reasons: list[str], reason: str) -> list[str]:
    safe = _safe_reason(reason)
    if not safe:
        return reasons
    return [safe, *[item for item in reasons if item != safe]][:PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS]


def _safe_surface_codes(values: Any) -> list[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes, bytearray)):
        return []
    codes: list[str] = []
    for raw in values:
        code = _safe_reason(raw)
        if not code or code in codes:
            continue
        codes.append(code)
        if len(codes) >= PUBLIC_EMLIS_FEEDBACK_META_MAX_SURFACE_CODE_COUNT:
            break
    return codes


def _pick_diagnostic_summary(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    summary = _safe_mapping(_safe_get(internal_meta, "diagnostic_summary"))
    if summary is not None:
        return summary

    multi_perspective = _safe_mapping(_safe_get(internal_meta, "multi_perspective"))
    if multi_perspective is None:
        return None
    return _safe_mapping(_safe_get(multi_perspective, "diagnostic_summary"))


def _build_gate_results(raw_gate_results: Any) -> Dict[str, Dict[str, Any]]:
    gate_results = _safe_mapping(raw_gate_results)
    if gate_results is None:
        return {}

    public_gate_results: Dict[str, Dict[str, Any]] = {}
    for raw_gate_name, raw_gate_payload in gate_results.items():
        if len(public_gate_results) >= PUBLIC_EMLIS_FEEDBACK_META_MAX_GATE_RESULTS:
            break
        gate_name = _safe_identifier(raw_gate_name, max_length=80, default=None)
        gate_payload = _safe_mapping(raw_gate_payload)
        if not gate_name or gate_payload is None:
            continue

        gate_summary: Dict[str, Any] = {}
        passed = _safe_bool(_safe_get(gate_payload, "passed"))
        if passed is not None:
            gate_summary["passed"] = passed
        primary_reason = _safe_reason(_safe_get(gate_payload, "primary_reason"))
        if primary_reason:
            gate_summary["primary_reason"] = primary_reason
        if gate_summary:
            public_gate_results[gate_name] = gate_summary
    return public_gate_results


def _pick_display_absence_summary(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    for key in (
        "step7_public_feedback_diagnostic_summary",
        "public_feedback_diagnostic_summary",
        "display_absence_summary",
    ):
        direct = _safe_mapping(_safe_get(internal_meta, key))
        if direct is not None:
            return direct

    summary = _pick_diagnostic_summary(internal_meta)
    if summary is None:
        return None
    for key in (
        "step7_public_feedback_diagnostic_summary",
        "public_feedback_diagnostic_summary",
        "display_absence_summary",
    ):
        nested = _safe_mapping(_safe_get(summary, key))
        if nested is not None:
            return nested
    return None


def _build_display_absence_summary(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_display_absence_summary(internal_meta)
    if source is None:
        return {}

    public_summary: Dict[str, Any] = {}
    for key in (
        "candidate_blocked_surface_grammar",
        "candidate_blocked_koto_splice",
        "candidate_blocked_relation_skeleton",
        "candidate_repair_attempted",
        "candidate_repair_succeeded",
        "candidate_repair_failed",
        "candidate_fail_closed_display_absent",
        "public_feedback_not_included_non_passed",
        "public_feedback_not_included_empty_comment_text",
        "public_feedback_not_included_visible_surface_gate",
        "public_feedback_not_included_two_stage_gate",
        "public_feedback_not_included_two_stage_reception_gate",
        "public_feedback_not_included_state_answer_gate",
        "public_feedback_not_included_reply_timeout_or_error",
        "rn_payload_absent",
    ):
        value = _safe_bool(_safe_get(source, key))
        if value is not None:
            public_summary[key] = value

    reason_family = _safe_identifier(_safe_get(source, "reason_family"), max_length=80, default=None)
    if reason_family:
        public_summary["reason_family"] = reason_family
    reason_codes = _safe_surface_codes(_safe_get(source, "reason_codes"))
    if reason_codes:
        public_summary["reason_codes"] = reason_codes
    return public_summary


def _build_diagnostic_summary(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_diagnostic_summary(internal_meta)
    if source is None:
        return {}

    public_summary: Dict[str, Any] = {}
    for key, max_length in (
        ("stage", 80),
        ("primary_reason", 120),
        ("coverage_group", 80),
        ("composer_status", 80),
        ("composer_source", 80),
    ):
        value = _safe_public_identifier(_safe_get(source, key), max_length=max_length, default=None)
        if value:
            public_summary[key] = value

    gate_results = _build_gate_results(_safe_get(source, "gate_results"))
    if gate_results:
        public_summary["gate_results"] = gate_results

    display_absence_summary = _build_display_absence_summary(internal_meta)
    if display_absence_summary:
        public_summary["display_absence_summary"] = display_absence_summary

    return public_summary


def _runtime_surface_source_has_unsafe_contract_flags(source: Mapping[str, Any]) -> bool:
    for flag in _VISIBLE_SURFACE_ACCEPTANCE_UNSAFE_CONTRACT_FLAGS:
        if _safe_bool(_safe_get(source, flag)) is True:
            return True
        if _safe_bool(_safe_get(source, f"runtime_surface_pre_return_gate_{flag}")) is True:
            return True
    return False


def _pick_state_answer_gate_boundary_source(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    for key in ("state_answer_gate_boundary", "state_answer_gate_public_meta_boundary"):
        direct = _safe_mapping(_safe_get(internal_meta, key))
        if direct is not None:
            return direct

    for container_key in (
        "runtime_surface_pre_return_gate",
        "visible_surface_acceptance_gate",
        "runtime_surface_tone_engine_2_1",
        "tone_engine_2_1",
        "gate_trace",
        "phase_gate",
        "diagnostic_summary",
        "composer_meta",
        "multi_perspective",
    ):
        container = _safe_mapping(_safe_get(internal_meta, container_key))
        if container is None:
            continue
        direct = _safe_mapping(_safe_get(container, "state_answer_gate_boundary"))
        if direct is not None:
            return direct
        gate_trace = _safe_mapping(_safe_get(container, "gate_trace"))
        if gate_trace is not None:
            nested = _safe_mapping(_safe_get(gate_trace, "state_answer_gate_boundary"))
            if nested is not None:
                return nested
            for gate_key in ("runtime_surface_pre_return_gate", "visible_surface_acceptance_gate"):
                gate = _safe_mapping(_safe_get(gate_trace, gate_key))
                nested = _safe_mapping(_safe_get(gate or {}, "state_answer_gate_boundary"))
                if nested is not None:
                    return nested
    return None


def _build_state_answer_gate_boundary_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_state_answer_gate_boundary_source(internal_meta)
    if source is None:
        return {}
    return _sanitize_gate_summary_reason_lists(state_answer_gate_boundary_public_summary(source))


def _sanitize_gate_summary_reason_lists(summary: Dict[str, Any]) -> Dict[str, Any]:
    for key in (
        "rejection_reasons",
        "surface_blocker_reasons",
        "forbidden_claim_reasons",
        "allowed_exception_ids",
        "two_stage_reception_gate_rejection_reasons",
        "section_shape_rejection_reasons",
        "section_boundary_rejection_reasons",
        "consistency_rejection_reasons",
        "mode_specific_rejection_reasons",
        "surface_quality_rejection_reasons",
        "koto_splice_codes",
    ):
        if key in summary:
            values = _safe_rejection_reasons(summary.get(key))
            if values:
                summary[key] = values
            else:
                summary.pop(key, None)

    # Phase20-7: public gate meta may describe pass/block status, but runtime
    # mode names and internal routing identifiers remain backend-only.
    for key in (
        "reception_mode_id",
        "selected_reception_mode_id",
        "two_stage_reception_mode_id",
        "reception_mode_family",
        "mode_id",
        "mode",
        "mode_specific_rejection_reasons",
    ):
        summary.pop(key, None)

    nested = _safe_mapping(summary.get("two_stage_reception_gate"))
    if nested is not None:
        summary["two_stage_reception_gate"] = _sanitize_gate_summary_reason_lists(dict(nested))
    return summary


def _pick_two_stage_reception_gate_source(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    """Pick the Phase 10 two-stage cross-gate report without copying text."""
    for key in _TWO_STAGE_RECEPTION_GATE_SOURCE_KEYS:
        direct = _safe_mapping(_safe_get(internal_meta, key))
        if direct is not None:
            return direct

    visible_gate = _pick_visible_surface_acceptance_gate_source(internal_meta)
    if visible_gate is not None:
        nested = _safe_mapping(_safe_get(visible_gate, "two_stage_reception_gate"))
        if nested is not None:
            return nested

    state_answer_gate = _pick_state_answer_gate_boundary_source(internal_meta)
    if state_answer_gate is not None:
        nested = _safe_mapping(_safe_get(state_answer_gate, "two_stage_reception_gate"))
        if nested is not None:
            return nested

    for container_key in _TWO_STAGE_RECEPTION_GATE_CONTAINER_KEYS:
        container = _safe_mapping(_safe_get(internal_meta, container_key))
        if container is None:
            continue

        for key in _TWO_STAGE_RECEPTION_GATE_SOURCE_KEYS:
            direct = _safe_mapping(_safe_get(container, key))
            if direct is not None:
                return direct

        nested_state_answer_gate = _safe_mapping(_safe_get(container, "state_answer_gate_boundary"))
        if nested_state_answer_gate is not None:
            nested = _safe_mapping(_safe_get(nested_state_answer_gate, "two_stage_reception_gate"))
            if nested is not None:
                return nested

        nested_visible_gate = _safe_mapping(_safe_get(container, "visible_surface_acceptance_gate"))
        if nested_visible_gate is not None:
            nested = _safe_mapping(_safe_get(nested_visible_gate, "two_stage_reception_gate"))
            if nested is not None:
                return nested

        gate_trace = _safe_mapping(_safe_get(container, "gate_trace"))
        if gate_trace is not None:
            nested = _pick_two_stage_reception_gate_source(gate_trace)
            if nested is not None:
                return nested
    return None


def _build_two_stage_reception_gate_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_two_stage_reception_gate_source(internal_meta)
    if source is None:
        return {}
    try:
        return _sanitize_gate_summary_reason_lists(two_stage_reception_gate_public_summary(source))
    except Exception:
        return {
            "evaluated": True,
            "passed": False,
            "blocked": True,
            "terminal_surface_block": True,
            "rejection_reasons": ["two_stage_reception_gate_public_meta_unsafe"],
            "public_meta_summary_only": True,
        }


def _build_runtime_surface_gate(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _safe_mapping(_safe_get(internal_meta, "runtime_surface_pre_return_gate"))
    if source is None:
        return {}

    if _runtime_surface_source_has_unsafe_contract_flags(source):
        return {
            "passed": False,
            "action": "fail_closed",
            "rejection_reasons": ["runtime_surface_pre_return_gate_public_meta_unsafe"],
        }

    public_gate: Dict[str, Any] = {}
    passed = _safe_bool(_safe_get(source, "passed"))
    if passed is not None:
        public_gate["passed"] = passed

    action = _safe_identifier(_safe_get(source, "action"), max_length=80, default=None)
    if action:
        public_gate["action"] = action

    rerender_attempted = _safe_bool(_safe_get(source, "rerender_attempted"))
    if rerender_attempted is not None:
        public_gate["rerender_attempted"] = rerender_attempted

    reasons = _safe_rejection_reasons(_safe_get(source, "rejection_reasons"))
    if reasons:
        public_gate["rejection_reasons"] = reasons

    koto_splice_detected = _safe_bool(_safe_get(source, "koto_splice_detected"))
    if koto_splice_detected is not None:
        public_gate["koto_splice_detected"] = koto_splice_detected

    malformed_phrase_unit_count = _safe_int(_safe_get(source, "malformed_phrase_unit_count"))
    if malformed_phrase_unit_count is not None:
        public_gate["malformed_phrase_unit_count"] = malformed_phrase_unit_count

    for key in (
        "koto_splice_codes",
        "surface_malformed_nominalization_codes",
    ):
        codes = _safe_surface_codes(_safe_get(source, key))
        if codes:
            public_gate[key] = codes

    for key in (
        "environment_state_output_frame_surface_limited_use",
        "environment_state_output_single_record_only",
        "environment_state_output_scope_marker_required",
        "environment_state_output_scope_marker_present",
        "environment_state_output_runtime_marker_check_performed",
        "environment_state_output_runtime_double_check_active",
        "environment_state_output_runtime_gate_repair_applied",
        "environment_state_output_terminal_surface_block",
        "period_tendency_from_single_record_surface_blocked",
        "personality_tendency_surface_blocked",
        "cause_from_category_surface_blocked",
        "cause_from_emotion_strength_surface_blocked",
        "diagnosis_surface_blocked",
        "recovery_prescription_surface_blocked",
    ):
        value = _safe_bool(_safe_get(source, key))
        if value is not None:
            public_gate[key] = value

    return public_gate


def _visible_surface_acceptance_value(source: Mapping[str, Any], key: str) -> Any:
    if key in source:
        return _safe_get(source, key)
    return _safe_get(source, f"visible_surface_acceptance_gate_{key}")


def _flat_visible_surface_acceptance_gate_source(source: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    flat: Dict[str, Any] = {}
    for suffix in (
        "evaluated",
        "passed",
        "classification",
        "action",
        "rejection_reasons",
        "koto_splice_detected",
        "koto_splice_codes",
        "relation_skeleton_marker_count",
        "relation_skeleton_marker_codes",
        "relation_skeleton_major",
        "analytic_register_leak_count",
        "analytic_register_leak_codes",
        "analytic_register_leak",
        "surface_repair_requested",
        "repair_reason_family",
    ):
        prefixed_key = f"visible_surface_acceptance_gate_{suffix}"
        if prefixed_key in source:
            flat[suffix] = _safe_get(source, prefixed_key)
    for flag in _VISIBLE_SURFACE_ACCEPTANCE_UNSAFE_CONTRACT_FLAGS:
        prefixed_key = f"visible_surface_acceptance_gate_{flag}"
        if prefixed_key in source:
            flat[flag] = _safe_get(source, prefixed_key)
    return flat or None


def _pick_visible_surface_acceptance_gate_source(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    for key in ("visible_surface_acceptance_gate", "visible_surface_acceptance"):
        direct = _safe_mapping(_safe_get(internal_meta, key))
        if direct is not None:
            return direct

    for container_key in ("gate_trace", "phase_gate", "diagnostic_summary", "multi_perspective"):
        container = _safe_mapping(_safe_get(internal_meta, container_key))
        if container is None:
            continue

        gate_trace = container if container_key == "gate_trace" else _safe_mapping(_safe_get(container, "gate_trace"))
        if gate_trace is not None:
            nested = _safe_mapping(_safe_get(gate_trace, "visible_surface_acceptance_gate"))
            if nested is not None:
                return nested

        direct = _safe_mapping(_safe_get(container, "visible_surface_acceptance_gate"))
        if direct is not None:
            return direct

        flat = _flat_visible_surface_acceptance_gate_source(container)
        if flat is not None:
            return flat

    picked_summary = _pick_diagnostic_summary(internal_meta)
    if picked_summary is not None:
        gate_trace = _safe_mapping(_safe_get(picked_summary, "gate_trace"))
        if gate_trace is not None:
            nested = _safe_mapping(_safe_get(gate_trace, "visible_surface_acceptance_gate"))
            if nested is not None:
                return nested
        direct = _safe_mapping(_safe_get(picked_summary, "visible_surface_acceptance_gate"))
        if direct is not None:
            return direct
        flat = _flat_visible_surface_acceptance_gate_source(picked_summary)
        if flat is not None:
            return flat

    return None


def _visible_surface_acceptance_source_has_unsafe_contract_flags(source: Mapping[str, Any]) -> bool:
    for flag in _VISIBLE_SURFACE_ACCEPTANCE_UNSAFE_CONTRACT_FLAGS:
        if _safe_bool(_safe_get(source, flag)) is True:
            return True
        if _safe_bool(_safe_get(source, f"visible_surface_acceptance_gate_{flag}")) is True:
            return True
    return False


def _build_visible_surface_acceptance_gate_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_visible_surface_acceptance_gate_source(internal_meta)
    if source is None:
        return {}

    if _visible_surface_acceptance_source_has_unsafe_contract_flags(source):
        return {
            "passed": False,
            "classification": "red",
            "action": "fail_closed",
            "rejection_reasons": ["visible_surface_acceptance_gate_public_meta_unsafe"],
        }

    public_gate: Dict[str, Any] = {}
    evaluated = _safe_bool(_visible_surface_acceptance_value(source, "evaluated"))
    if evaluated is not None:
        public_gate["evaluated"] = evaluated

    passed = _safe_bool(_visible_surface_acceptance_value(source, "passed"))
    if passed is not None:
        public_gate["passed"] = passed

    classification = _safe_visible_surface_acceptance_classification(
        _visible_surface_acceptance_value(source, "classification")
    )
    if classification:
        public_gate["classification"] = classification

    action = _safe_visible_surface_acceptance_action(
        _visible_surface_acceptance_value(source, "action")
    )
    if action:
        public_gate["action"] = action

    reasons = _safe_rejection_reasons(_visible_surface_acceptance_value(source, "rejection_reasons"))
    if reasons:
        public_gate["rejection_reasons"] = reasons

    for key in (
        "koto_splice_detected",
        "relation_skeleton_major",
        "analytic_register_leak",
        "surface_repair_requested",
    ):
        value = _safe_bool(_visible_surface_acceptance_value(source, key))
        if value is not None:
            public_gate[key] = value

    for key in ("relation_skeleton_marker_count", "analytic_register_leak_count"):
        value = _safe_int(_visible_surface_acceptance_value(source, key))
        if value is not None:
            public_gate[key] = value

    for key in (
        "koto_splice_codes",
        "relation_skeleton_marker_codes",
        "analytic_register_leak_codes",
    ):
        codes = _safe_surface_codes(_visible_surface_acceptance_value(source, key))
        if codes:
            public_gate[key] = codes

    repair_reason_family = _safe_identifier(
        _visible_surface_acceptance_value(source, "repair_reason_family"),
        max_length=80,
        default=None,
    )
    if repair_reason_family:
        public_gate["repair_reason_family"] = repair_reason_family

    return public_gate


def _build_observation_reply_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _safe_mapping(_safe_get(internal_meta, "observation_reply_meta"))
    if source is None:
        return {}

    public_meta: Dict[str, Any] = {}
    reply_kind = _safe_reply_kind(_safe_get(source, "observation_reply_kind"))
    if reply_kind:
        public_meta["observation_reply_kind"] = reply_kind

    for key in (
        "eligible_for_full_observation",
        "question_required",
        "user_fact_may_promote_to_eligible",
    ):
        value = _safe_bool(_safe_get(source, key))
        if value is not None:
            public_meta[key] = value

    return public_meta


def _build_step10_repair_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _safe_mapping(_safe_get(internal_meta, "step10_observation_display_repair_integration"))
    if source is None:
        return {}

    public_meta: Dict[str, Any] = {}
    applied = _safe_bool(_safe_get(source, "applied"))
    if applied is not None:
        public_meta["applied"] = applied

    final_status = _safe_status(_safe_get(source, "final_observation_status"))
    if final_status:
        public_meta["final_observation_status"] = final_status

    reply_kind = _safe_reply_kind(_safe_get(source, "observation_reply_kind"))
    if reply_kind:
        public_meta["observation_reply_kind"] = reply_kind

    for key in (
        "public_status_extended",
        "observation_status_enum_extended",
        "rn_visible_contract_changed",
        "response_shape_changed",
        "display_gate_relaxed",
        "fixed_fallback_used",
        "external_ai_used",
    ):
        value = _safe_bool(_safe_get(source, key))
        if value is not None:
            public_meta[key] = value

    return public_meta


def _pick_user_label_connection_source(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    direct_meta_only = _safe_mapping(_safe_get(internal_meta, USER_LABEL_CONNECTION_META_ONLY_META_KEY))
    direct_visible = _safe_mapping(_safe_get(internal_meta, USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY))
    if direct_meta_only is not None:
        if direct_visible is not None:
            merged = dict(direct_meta_only)
            merged[USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY] = dict(direct_visible)
            return merged
        return direct_meta_only
    if direct_visible is not None:
        return direct_visible

    for container_key in ("diagnostic_summary", "phase_gate", "multi_perspective"):
        container = _safe_mapping(_safe_get(internal_meta, container_key))
        if container is None:
            continue
        nested_meta_only = _safe_mapping(_safe_get(container, USER_LABEL_CONNECTION_META_ONLY_META_KEY))
        nested_visible = _safe_mapping(_safe_get(container, USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY))
        if nested_meta_only is not None:
            if nested_visible is not None:
                merged = dict(nested_meta_only)
                merged[USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY] = dict(nested_visible)
                return merged
            return nested_meta_only
        if nested_visible is not None:
            return nested_visible
    return None


def _build_user_label_connection_public_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_user_label_connection_source(internal_meta)
    if source is None:
        return {}
    try:
        summary = user_label_connection_public_summary(source)
    except Exception:
        return {
            "schema_version": "cocolon.emlis.user_label_connection_meta_only_public_summary.v1",
            "phase": "phase7_meta_only_integration",
            "meta_only_connected": False,
            "history_connection_applied": False,
            "history_connection_blocked": True,
            "history_connection_edge_family_count": 0,
            "history_connection_evidence_record_count": 0,
            "scope_marker_required": True,
            "soft_marker_required": True,
            "public_response_key_added": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "history_raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "comment_text_generated": False,
            "comment_text_connected": False,
            "visible_text_generated": False,
            "visible_surface_connected": False,
            "runtime_surface_connected": False,
            "public_release_applied": False,
            "rejection_reasons": ["meta_only_integration_exception"],
        }
    return dict(summary)


def _strip_internal_public_boundary_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        stripped: Dict[str, Any] = {}
        for raw_key, raw_child in value.items():
            key = str(raw_key)
            if key in _INTERNAL_RESPONSE_CONTRACT_PUBLIC_FORBIDDEN_KEYS:
                continue
            stripped[key] = _strip_internal_public_boundary_keys(raw_child)
        return stripped
    if isinstance(value, list):
        return [_strip_internal_public_boundary_keys(item) for item in value]
    return value


def _mark_trimmed(meta: Dict[str, Any]) -> Dict[str, Any]:
    boundary = meta.get("public_feedback_meta_boundary")
    if isinstance(boundary, dict):
        boundary["trimmed"] = True
    return meta


def _fit_hard_byte_limit(meta: Dict[str, Any], *, subscription_tier: Any = None) -> Dict[str, Any]:
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    _mark_trimmed(meta)

    runtime_gate = meta.get("runtime_surface_pre_return_gate")
    if isinstance(runtime_gate, dict):
        runtime_gate.pop("rejection_reasons", None)
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    visible_surface_gate = meta.get("visible_surface_acceptance_gate")
    if isinstance(visible_surface_gate, dict):
        visible_surface_gate.pop("rejection_reasons", None)
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    diagnostic_summary = meta.get("diagnostic_summary")
    if isinstance(diagnostic_summary, dict):
        diagnostic_summary.pop("gate_results", None)
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    meta.pop("diagnostic_summary", None)
    meta.pop("runtime_surface_pre_return_gate", None)
    meta.pop("visible_surface_acceptance_gate", None)
    meta.pop("state_answer_gate_boundary", None)
    meta.pop("two_stage_reception_gate", None)
    meta.pop("observation_reply_meta", None)
    meta.pop("step10_observation_display_repair_integration", None)
    meta["rejection_reasons"] = meta.get("rejection_reasons", [])[:5]
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    return _minimal_unavailable_meta(
        subscription_tier=subscription_tier,
        reason="public_feedback_meta_hard_limit_exceeded",
    )


def build_public_emlis_input_feedback_meta(
    internal_meta: Mapping[str, Any] | None,
    *,
    comment_text_present: bool,
    subscription_tier: Any = None,
) -> Dict[str, Any]:
    """Build the public-safe ``input_feedback.emlis_ai`` metadata subset.

    ``comment_text_present`` is intentionally accepted at this boundary so
    callers can keep the public display contract close to the sanitizer.  The
    sanitizer never copies the actual comment text; response inclusion remains
    controlled by the caller in the next integration step.
    """
    # The body is never copied into public meta.  The boolean is only used to
    # keep the public status contract from reporting passed without a body.

    try:
        if not isinstance(internal_meta, Mapping):
            return _minimal_unavailable_meta(subscription_tier=subscription_tier)

        version = _safe_identifier(
            _safe_get(internal_meta, "version"),
            max_length=80,
            default=_DEFAULT_VERSION,
        )
        kernel_version = _safe_identifier(
            _safe_get(internal_meta, "kernel_version"),
            max_length=120,
            default=_DEFAULT_KERNEL_VERSION,
        )
        tier_source = subscription_tier
        if tier_source is None:
            tier_source = _safe_get(internal_meta, "tier", _DEFAULT_TIER)

        step10_meta = _safe_mapping(
            _safe_get(internal_meta, "step10_observation_display_repair_integration")
        )
        comment_body_present = bool(comment_text_present)
        try:
            internal_response_contract = _internal_response_contract_or_none(internal_meta)
        except Exception:
            return _minimal_unavailable_meta(
                subscription_tier=tier_source,
                reason="public_feedback_response_contract_invalid",
            )
        contract_status = _safe_status(
            public_status_from_internal_response_contract(internal_response_contract)
            if internal_response_contract is not None
            else None
        )
        # Phase20-7: once an internal response contract is present, the
        # response_kind -> public observation_status mapping is the public
        # boundary source of truth.  Legacy status fields remain as fallback for
        # older meta that has not been bridged yet, but they may not keep
        # normal / low-information / limited-grounding observations rejected
        # after Phase20 recovery has produced a displayable comment_text.
        if internal_response_contract is not None and contract_status:
            observation_status = contract_status
        else:
            observation_status = _safe_status(_safe_get(internal_meta, "observation_status"))
            if observation_status is None and step10_meta is not None:
                observation_status = _safe_status(_safe_get(step10_meta, "final_observation_status"))
            if observation_status is None and contract_status:
                observation_status = contract_status
        observation_status = observation_status or "unavailable"

        rejection_reasons = _safe_rejection_reasons(_safe_get(internal_meta, "rejection_reasons"))
        comment_required = _contract_comment_required(internal_response_contract)
        if comment_required is None:
            comment_required = True
        if observation_status == "passed" and comment_required and not comment_body_present:
            observation_status = "unavailable"
            rejection_reasons = _prepend_public_rejection_reason(
                rejection_reasons,
                "public_feedback_comment_text_missing",
            )

        public_meta: Dict[str, Any] = {
            "schema_version": PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION,
            "version": version or _DEFAULT_VERSION,
            "kernel_version": kernel_version or _DEFAULT_KERNEL_VERSION,
            "tier": _coerce_tier(tier_source),
            "observation_status": observation_status,
        }

        observation_trace_id = _safe_trace(_safe_get(internal_meta, "observation_trace_id"))
        if observation_trace_id:
            public_meta["observation_trace_id"] = observation_trace_id

        trace_id = _safe_trace(_safe_get(internal_meta, "trace_id"))
        if trace_id:
            public_meta["trace_id"] = trace_id

        reply_kind = _safe_reply_kind(_safe_get(internal_meta, "observation_reply_kind"))
        if reply_kind:
            public_meta["observation_reply_kind"] = reply_kind

        if rejection_reasons:
            public_meta["rejection_reasons"] = rejection_reasons

        diagnostic_summary = _build_diagnostic_summary(internal_meta)
        if diagnostic_summary:
            public_meta["diagnostic_summary"] = diagnostic_summary

        runtime_gate = _build_runtime_surface_gate(internal_meta)
        if runtime_gate:
            public_meta["runtime_surface_pre_return_gate"] = runtime_gate

        observation_reply_meta = _build_observation_reply_meta(internal_meta)
        if observation_reply_meta:
            public_meta["observation_reply_meta"] = observation_reply_meta

        step10_public_meta = _build_step10_repair_meta(internal_meta)
        if step10_public_meta:
            public_meta["step10_observation_display_repair_integration"] = step10_public_meta

        user_label_connection_meta = _build_user_label_connection_public_meta(internal_meta)
        if user_label_connection_meta:
            public_meta[USER_LABEL_CONNECTION_PUBLIC_META_KEY] = user_label_connection_meta

        visible_surface_gate = _build_visible_surface_acceptance_gate_meta(internal_meta)
        if visible_surface_gate:
            public_meta["visible_surface_acceptance_gate"] = visible_surface_gate

        two_stage_reception_gate = _build_two_stage_reception_gate_meta(internal_meta)
        if two_stage_reception_gate:
            public_meta["two_stage_reception_gate"] = two_stage_reception_gate

        state_answer_gate_boundary = _build_state_answer_gate_boundary_meta(internal_meta)
        if state_answer_gate_boundary:
            public_meta["state_answer_gate_boundary"] = state_answer_gate_boundary

        if public_meta.get("observation_status") == "passed" and _two_stage_reception_gate_blocks_public_feedback(public_meta):
            public_meta["observation_status"] = "rejected"
            reasons = _safe_rejection_reasons(public_meta.get("rejection_reasons"))
            public_meta["rejection_reasons"] = _prepend_public_rejection_reason(
                reasons,
                "public_feedback_two_stage_reception_gate_blocked",
            )

        if public_meta.get("observation_status") == "passed" and _state_answer_gate_boundary_blocks_public_feedback(public_meta):
            public_meta["observation_status"] = "rejected"
            reasons = _safe_rejection_reasons(public_meta.get("rejection_reasons"))
            public_meta["rejection_reasons"] = _prepend_public_rejection_reason(
                reasons,
                "public_feedback_state_answer_gate_blocked",
            )

        public_meta["public_feedback_meta_boundary"] = _boundary_marker(trimmed=False)
        public_meta = _strip_internal_public_boundary_keys(public_meta)
        return _fit_hard_byte_limit(public_meta, subscription_tier=tier_source)
    except Exception:
        return _minimal_unavailable_meta(subscription_tier=subscription_tier)


def _visible_surface_acceptance_gate_blocks_public_feedback(public_meta: Mapping[str, Any]) -> bool:
    gate = _safe_mapping(_safe_get(public_meta, "visible_surface_acceptance_gate"))
    if gate is None:
        return False

    passed = _safe_bool(_safe_get(gate, "passed"))
    if passed is False:
        return True

    classification = _safe_visible_surface_acceptance_classification(_safe_get(gate, "classification"))
    if classification in _BLOCKING_VISIBLE_SURFACE_ACCEPTANCE_CLASSIFICATIONS:
        return True

    action = _safe_visible_surface_acceptance_action(_safe_get(gate, "action"))
    if action in _BLOCKING_VISIBLE_SURFACE_ACCEPTANCE_ACTIONS:
        return True

    return False


def _state_answer_gate_boundary_blocks_public_feedback(public_meta: Mapping[str, Any]) -> bool:
    gate = _safe_mapping(_safe_get(public_meta, "state_answer_gate_boundary"))
    if gate is None:
        return False
    passed = _safe_bool(_safe_get(gate, "passed"))
    if passed is False:
        return True
    if _safe_bool(_safe_get(gate, "blocked")) is True:
        return True
    if _safe_bool(_safe_get(gate, "terminal_surface_block")) is True:
        return True
    reasons = _safe_rejection_reasons(_safe_get(gate, "rejection_reasons"))
    if reasons:
        return True
    return False


def _runtime_surface_gate_blocks_public_feedback(public_meta: Mapping[str, Any]) -> bool:
    gate = _safe_mapping(_safe_get(public_meta, "runtime_surface_pre_return_gate"))
    if gate is None:
        return False

    passed = _safe_bool(_safe_get(gate, "passed"))
    if passed is False:
        return True

    action = _safe_identifier(_safe_get(gate, "action"), max_length=80, default=None)
    if action in _BLOCKING_RUNTIME_SURFACE_ACTIONS:
        return True

    if _safe_bool(_safe_get(gate, "environment_state_output_terminal_surface_block")) is True:
        return True

    if _safe_bool(_safe_get(gate, "environment_state_output_runtime_gate_repair_applied")) is True:
        return True

    marker_check_required = bool(
        _safe_bool(_safe_get(gate, "environment_state_output_runtime_marker_check_performed")) is True
        and _safe_bool(_safe_get(gate, "environment_state_output_scope_marker_required")) is True
    )
    if marker_check_required and _safe_bool(_safe_get(gate, "environment_state_output_scope_marker_present")) is False:
        return True

    reasons = _safe_rejection_reasons(_safe_get(gate, "rejection_reasons"))
    if any(reason in _ENVIRONMENT_STATE_OUTPUT_TERMINAL_SURFACE_REASONS for reason in reasons):
        return True

    return False


def _two_stage_gate_summary_blocks_public_feedback(gate: Mapping[str, Any] | None) -> bool:
    if gate is None:
        return False
    passed = _safe_bool(_safe_get(gate, "passed"))
    if passed is False:
        return True
    if _safe_bool(_safe_get(gate, "blocked")) is True:
        return True
    if _safe_bool(_safe_get(gate, "terminal_surface_block")) is True:
        return True
    reasons = _safe_rejection_reasons(
        _safe_get(gate, "rejection_reasons")
        or _safe_get(gate, "surface_blocker_reasons")
    )
    if reasons:
        return True
    return False


def _two_stage_reception_gate_blocks_public_feedback(public_meta: Mapping[str, Any]) -> bool:
    if _two_stage_gate_summary_blocks_public_feedback(
        _safe_mapping(_safe_get(public_meta, "two_stage_reception_gate"))
    ):
        return True

    state_gate = _safe_mapping(_safe_get(public_meta, "state_answer_gate_boundary"))
    if state_gate is not None:
        if _safe_bool(_safe_get(state_gate, "two_stage_reception_gate_terminal_surface_block")) is True:
            return True
        if _safe_bool(_safe_get(state_gate, "two_stage_reception_cross_gate_active")) is True and _safe_bool(
            _safe_get(state_gate, "two_stage_reception_gate_connected")
        ) is True and _safe_bool(_safe_get(state_gate, "two_stage_reception_gate_passed")) is False:
            return True
        if _safe_rejection_reasons(_safe_get(state_gate, "two_stage_reception_gate_rejection_reasons")):
            return True
        if _two_stage_gate_summary_blocks_public_feedback(
            _safe_mapping(_safe_get(state_gate, "two_stage_reception_gate"))
        ):
            return True

    visible_gate = _safe_mapping(_safe_get(public_meta, "visible_surface_acceptance_gate"))
    if visible_gate is not None:
        if _safe_bool(_safe_get(visible_gate, "two_stage_reception_gate_terminal_surface_block")) is True:
            return True
        if _safe_rejection_reasons(_safe_get(visible_gate, "two_stage_reception_gate_rejection_reasons")):
            return True
        if _two_stage_gate_summary_blocks_public_feedback(
            _safe_mapping(_safe_get(visible_gate, "two_stage_reception_gate"))
        ):
            return True

    return False

def should_include_public_input_feedback(
    comment_text: Any,
    public_meta: Mapping[str, Any] | None,
) -> bool:
    """Return whether ``input_feedback`` should be present in a public response.

    RN shows Emlis observations only for ``passed`` public meta plus a non-empty
    ``comment_text``.  Keeping this condition in the public meta boundary avoids
    returning meta-only unavailable/rejected payloads that cannot be displayed and
    can bloat ``/emotion/submit`` responses.
    """
    if not str(comment_text or "").strip():
        return False
    if not isinstance(public_meta, Mapping):
        return False
    if str(public_meta.get("observation_status") or "").strip() != "passed":
        return False
    if _runtime_surface_gate_blocks_public_feedback(public_meta):
        return False
    if _visible_surface_acceptance_gate_blocks_public_feedback(public_meta):
        return False
    if _two_stage_reception_gate_blocks_public_feedback(public_meta):
        return False
    if _state_answer_gate_boundary_blocks_public_feedback(public_meta):
        return False
    return True


__all__ = [
    "PUBLIC_EMLIS_FEEDBACK_META_BOUNDARY_VERSION",
    "PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_GATE_RESULTS",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_SURFACE_CODE_COUNT",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_SURFACE_COUNT",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS",
    "PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION",
    "PUBLIC_EMLIS_FEEDBACK_META_TARGET_BYTES",
    "build_public_emlis_input_feedback_meta",
    "should_include_public_input_feedback",
]
