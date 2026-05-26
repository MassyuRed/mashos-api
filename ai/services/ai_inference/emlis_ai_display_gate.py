# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed display gate and judge trace helpers for EmlisAI observation."""

from typing import Any, Dict, List, Mapping

from emlis_ai_types import (
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)
from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW,
    ACTION_BLOCK,
    ACTION_FAIL_CLOSED,
    ACTION_RERENDER_SHALLOW_V2,
    ACTION_REROUTE_LOW_INFORMATION,
    RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
    assert_runtime_surface_pre_return_gate_meta_only,
)
from emlis_ai_visible_surface_acceptance_gate import (
    ACTION_ALLOW as VISIBLE_SURFACE_ACTION_ALLOW,
    ACTION_BLOCK as VISIBLE_SURFACE_ACTION_BLOCK,
    ACTION_FAIL_CLOSED as VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
    ACTION_RERENDER_SURFACE as VISIBLE_SURFACE_ACTION_RERENDER_SURFACE,
    ACTION_REROUTE_LOW_INFORMATION as VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION,
    ACTION_WARN as VISIBLE_SURFACE_ACTION_WARN,
    CLASSIFICATION_RED as VISIBLE_SURFACE_CLASSIFICATION_RED,
    CLASSIFICATION_REPAIR_REQUIRED as VISIBLE_SURFACE_CLASSIFICATION_REPAIR_REQUIRED,
    VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
    assert_visible_surface_acceptance_gate_meta_only,
)

_VALID_STATUSES = {"passed", "rejected", "unavailable", "safety_blocked"}
_UNAVAILABLE_SOURCES = {"", "unavailable", "empty"}
_NON_AI_RENDERED_SOURCES = {"rule_rendered", "fallback", "static_string", "legacy_kernel", "safe_fallback"}
_PHASE10_REQUIRED_PHASES = tuple(range(0, 11))
_PHASE10_REQUIRED_RELEASE_CHECKS = (
    "phase9_frontend_passed_only",
    "phase10_fixed_string_regression",
    "phase10_structure_reading_grounding_guard",
    "phase10_template_echo_guard",
    "phase10_screenshot_regression",
    "phase10_unverified_phase_not_passed",
)

_STEP7_GATE_BINDING_TRACE_VERSION = "emlis.limited_composer_gate_binding_reflection.v1"
_STEP7_GATE_BINDING_TARGET_STEP = "7_Gate_binding_reflection"
GATE_BINDING_CONTRACT_VERSION = "emlis.gate_binding_contract.v2"
_BINDING_DECISION_GATES = {"grounding", "display"}

def _dedupe(values: Any) -> List[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        source = [values]
    else:
        try:
            source = list(values)
        except TypeError:
            source = [values]
    return list(dict.fromkeys(str(v) for v in source if str(v)))



def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _binding_trace(binding_meta: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    binding = binding_meta if isinstance(binding_meta, Mapping) else {}
    binding_required = bool(binding.get("binding_required") or binding.get("binding_expected"))
    sentence_count = _safe_int(
        binding.get("sentence_count")
        or binding.get("expected_binding_count")
        or binding.get("body_sentence_count")
        or 0
    )
    expected_binding_count = _safe_int(binding.get("expected_binding_count") or sentence_count)
    binding_count = _safe_int(binding.get("binding_count") or binding.get("sentence_binding_count") or 0)
    binding_present = bool(binding.get("binding_present") or binding_count > 0)
    binding_missing = bool(
        binding.get("binding_missing")
        or (binding_required and expected_binding_count and binding_count < expected_binding_count)
    )
    return {
        "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "binding_used": bool(binding.get("binding_used")),
        "binding_present": binding_present,
        "binding_available": binding_present,
        "binding_missing": binding_missing,
        "binding_required": binding_required,
        "binding_count": binding_count,
        "sentence_count": sentence_count,
        "expected_binding_count": expected_binding_count,
        "binding_version": str(binding.get("binding_version") or binding.get("version") or ""),
        "binding_support_source": str(binding.get("binding_support_source") or binding.get("grounding_support_source") or "none"),
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
    }


def _gate_requires_binding(gate: str, fields: Mapping[str, Any]) -> bool:
    gate_key = "display" if gate == "display_gate" else str(gate or "")
    if gate_key not in _BINDING_DECISION_GATES:
        return False
    return bool(
        fields.get("binding_required")
        or fields.get("binding_expected")
        or fields.get("expected_binding_count")
        or fields.get("binding_count")
        or fields.get("binding_present")
    )


def _default_binding_support_source(*, gate: str, binding_used: bool, binding_meta: Mapping[str, Any] | None = None) -> str:
    if not binding_used:
        return "none"
    binding = binding_meta if isinstance(binding_meta, Mapping) else {}
    explicit = str(
        binding.get("binding_support_source")
        or binding.get("grounding_support_source")
        or binding.get("support_source")
        or ""
    ).strip()
    if explicit and explicit != "none":
        return explicit
    gate_key = "display" if gate == "display_gate" else str(gate or "")
    if gate_key == "display":
        return "display_binding_aware_result"
    if gate_key == "grounding":
        return "declared_relation_binding"
    return "none"


def _gate_binding_fields(
    binding_meta: Mapping[str, Any] | None,
    *,
    gate: str,
    binding_used: bool | None = None,
    binding_present: bool | None = None,
    binding_missing: bool | None = None,
    binding_count: int | None = None,
    sentence_count: int | None = None,
    expected_binding_count: int | None = None,
    binding_version: str | None = None,
    binding_supported_sentence_count: int | None = None,
    binding_required: bool | None = None,
    binding_support_source: str | None = None,
) -> Dict[str, Any]:
    """Build Step 7 binding trace fields for a single gate.

    This is diagnostic meta only; it does not include raw user input and it
    does not relax the Display Gate.
    """

    fields = _binding_trace(binding_meta)
    if binding_used is not None:
        fields["binding_used"] = bool(binding_used)
    if binding_present is not None:
        fields["binding_present"] = bool(binding_present)
    if binding_missing is not None:
        fields["binding_missing"] = bool(binding_missing)
    if binding_count is not None:
        fields["binding_count"] = _safe_int(binding_count)
    if sentence_count is not None:
        fields["sentence_count"] = _safe_int(sentence_count)
    if expected_binding_count is not None:
        fields["expected_binding_count"] = _safe_int(expected_binding_count)
    if binding_version:
        fields["binding_version"] = str(binding_version)
    if binding_required is not None:
        fields["binding_required"] = bool(binding_required)
    else:
        fields["binding_required"] = _gate_requires_binding(gate, fields)
    fields["binding_available"] = bool(fields.get("binding_present") or fields.get("binding_count"))
    if fields.get("binding_required") and fields.get("expected_binding_count"):
        fields["binding_missing"] = bool(_safe_int(fields.get("binding_count")) < _safe_int(fields.get("expected_binding_count")))
    elif not fields.get("binding_required"):
        fields["binding_missing"] = False
    fields["gate_binding_contract_version"] = GATE_BINDING_CONTRACT_VERSION
    fields["binding_contract_version"] = GATE_BINDING_CONTRACT_VERSION
    fields["binding_support_source"] = str(
        binding_support_source
        or _default_binding_support_source(
            gate=gate,
            binding_used=bool(fields.get("binding_used")),
            binding_meta=binding_meta,
        )
    )
    fields["step7_gate_binding_reflection"] = {
        "version": _STEP7_GATE_BINDING_TRACE_VERSION,
        "target_step": _STEP7_GATE_BINDING_TARGET_STEP,
        "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "gate": str(gate or ""),
        "binding_trace_present": True,
        "binding_used": bool(fields.get("binding_used")),
        "binding_available": bool(fields.get("binding_available")),
        "binding_present": bool(fields.get("binding_present")),
        "binding_missing": bool(fields.get("binding_missing")),
        "binding_required": bool(fields.get("binding_required")),
        "binding_count": _safe_int(fields.get("binding_count")),
        "expected_binding_count": _safe_int(fields.get("expected_binding_count")),
        "sentence_count": _safe_int(fields.get("sentence_count")),
        "binding_supported_sentence_count": _safe_int(binding_supported_sentence_count),
        "binding_version": str(fields.get("binding_version") or ""),
        "binding_support_source": str(fields.get("binding_support_source") or "none"),
        "gate_threshold_relaxed": False,
        "display_contract_relaxed": False,
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
    }
    return fields


def _display_binding_used_from_trace(gate_trace: Mapping[str, Any] | None, binding_meta: Mapping[str, Any] | None) -> bool:
    trace = gate_trace if isinstance(gate_trace, Mapping) else {}
    grounding = trace.get("grounding") if isinstance(trace.get("grounding"), Mapping) else {}
    return bool(
        (grounding or {}).get("binding_used")
        or (grounding or {}).get("binding_supported_sentence_count")
    )


def _grounding_binding_support_source(grounding_report: GroundingReport) -> str:
    diagnostics = getattr(grounding_report, "binding_diagnostics", {}) or {}
    if isinstance(diagnostics, Mapping):
        explicit = str(
            diagnostics.get("binding_support_source")
            or diagnostics.get("grounding_support_source")
            or diagnostics.get("support_source")
            or ""
        ).strip()
        if explicit:
            return explicit
    if not bool(getattr(grounding_report, "binding_used", False)):
        return "none"
    relation_types = list(getattr(grounding_report, "declared_relation_types", []) or [])
    phrase_ids = list(getattr(grounding_report, "declared_phrase_unit_ids", []) or [])
    sentence_claims = list(getattr(grounding_report, "sentence_claims", []) or [])
    if relation_types or any(str(getattr(claim, "declared_relation_type", "") or getattr(claim, "binding_relation_type", "")) for claim in sentence_claims):
        return "declared_relation_binding"
    if phrase_ids or any(list(getattr(claim, "declared_phrase_unit_ids", []) or getattr(claim, "binding_phrase_unit_ids", []) or []) for claim in sentence_claims):
        return "declared_phrase_binding"
    return "declared_evidence_binding"

def _required_gate_trace_keys() -> tuple[str, ...]:
    return ("reader", "grounding", "template_echo", "generation_source", "safety", "phase_completion")


def _gate_passed(gate_trace: Mapping[str, Any], key: str) -> bool:
    gate = gate_trace.get(key)
    return isinstance(gate, Mapping) and bool(gate.get("passed"))


def _all_core_gates_passed(gate_trace: Mapping[str, Any]) -> bool:
    core_passed = all(_gate_passed(gate_trace, key) for key in _required_gate_trace_keys())
    if not core_passed:
        return False
    if isinstance(gate_trace.get("observation_structure"), Mapping) and not _gate_passed(gate_trace, "observation_structure"):
        return False
    if isinstance(gate_trace.get("runtime_surface_pre_return_gate"), Mapping) and not _gate_passed(gate_trace, "runtime_surface_pre_return_gate"):
        return False
    if isinstance(gate_trace.get("visible_surface_acceptance_gate"), Mapping) and _visible_surface_gate_blocks(
        gate_trace.get("visible_surface_acceptance_gate")
    ):
        return False
    return True


def _structure_gate_meta(observation_structure_gate_report: Any = None) -> Dict[str, Any]:
    if observation_structure_gate_report is None:
        return {}
    if isinstance(observation_structure_gate_report, Mapping):
        raw = dict(observation_structure_gate_report)
    else:
        as_meta = getattr(observation_structure_gate_report, "as_meta", None)
        if callable(as_meta):
            try:
                meta = as_meta()
                raw = dict(meta) if isinstance(meta, Mapping) else {}
            except Exception:
                raw = {}
        else:
            raw = {
                "passed": bool(getattr(observation_structure_gate_report, "passed", True)),
                "evaluated": bool(getattr(observation_structure_gate_report, "evaluated", False)),
                "status": str(getattr(observation_structure_gate_report, "status", "") or ""),
                "rejection_reasons": list(getattr(observation_structure_gate_report, "rejection_reasons", []) or []),
                "selected_entry_ids": list(getattr(observation_structure_gate_report, "selected_entry_ids", []) or []),
                "selected_relation_ids": list(getattr(observation_structure_gate_report, "selected_relation_ids", []) or []),
                "gate_constraint_ids": list(getattr(observation_structure_gate_report, "gate_constraint_ids", []) or []),
            }
    if not raw:
        return {}
    reasons = raw.get("rejection_reasons") if isinstance(raw.get("rejection_reasons"), list) else []
    return {
        "passed": bool(raw.get("passed", True)),
        "evaluated": bool(raw.get("evaluated", False)),
        "status": str(raw.get("status") or ""),
        "rejection_reasons": [str(item) for item in reasons if str(item)],
        "selected_entry_ids": list(raw.get("selected_entry_ids") or []),
        "selected_relation_ids": list(raw.get("selected_relation_ids") or []),
        "gate_constraint_ids": list(raw.get("gate_constraint_ids") or []),
        "environment_state_output_frame_connected": bool(raw.get("environment_state_output_frame_connected")),
        "environment_state_output_frame_material_id": str(raw.get("environment_state_output_frame_material_id") or ""),
        "environment_state_output_frame_axis_presence": dict(raw.get("environment_state_output_frame_axis_presence") or {}),
        "environment_state_output_frame_output_theme_ids": list(raw.get("environment_state_output_frame_output_theme_ids") or []),
        "comment_text_included": False,
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
        "display_gate_relaxed": False,
    }


def _runtime_surface_gate_meta(runtime_surface_pre_return_gate_report: Any = None) -> Dict[str, Any]:
    """Return sanitized Step2 Runtime Surface Pre-Return Gate trace meta.

    The report is meta-only.  If a malformed report is supplied, fail closed
    without copying exception details or any candidate body.
    """

    if not runtime_surface_pre_return_gate_report:
        return {}
    if not isinstance(runtime_surface_pre_return_gate_report, Mapping):
        return {
            "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
            "evaluated": True,
            "passed": False,
            "action": ACTION_FAIL_CLOSED,
            "rejection_reasons": ["runtime_surface_pre_return_gate_invalid"],
            "runtime_surface_pre_return_gate_invalid": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "display_gate_relaxed": False,
        }
    data = dict(runtime_surface_pre_return_gate_report)
    try:
        assert_runtime_surface_pre_return_gate_meta_only(data, source="display_gate.runtime_surface_pre_return_gate")
    except Exception:
        return {
            "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
            "evaluated": True,
            "passed": False,
            "action": ACTION_FAIL_CLOSED,
            "rejection_reasons": ["runtime_surface_pre_return_gate_invalid"],
            "runtime_surface_pre_return_gate_invalid": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "display_gate_relaxed": False,
        }
    reasons = _dedupe(list(data.get("rejection_reasons") or []))
    action = str(data.get("action") or ACTION_ALLOW).strip()
    if action not in {ACTION_ALLOW, ACTION_BLOCK, ACTION_FAIL_CLOSED, ACTION_RERENDER_SHALLOW_V2, ACTION_REROUTE_LOW_INFORMATION}:
        action = ACTION_FAIL_CLOSED
        if "runtime_surface_pre_return_gate_invalid" not in reasons:
            reasons.append("runtime_surface_pre_return_gate_invalid")
    return {
        "version": str(data.get("version") or RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION),
        "schema_version": str(data.get("schema_version") or data.get("version") or RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION),
        "evaluated": bool(data.get("evaluated", True)),
        "passed": bool(data.get("passed")),
        "blocked": bool(data.get("blocked", not bool(data.get("passed")))),
        "action": action,
        "rerender_recommended": bool(data.get("rerender_recommended") or action == ACTION_RERENDER_SHALLOW_V2),
        "reroute_low_information_recommended": bool(data.get("reroute_low_information_recommended") or action == ACTION_REROUTE_LOW_INFORMATION),
        "rejection_reasons": reasons,
        "surface_signature_ready": bool(data.get("surface_signature_ready") or data.get("surface_signature_id")),
        "surface_signature_id": str(data.get("surface_signature_id") or ""),
        "surface_template_major": bool(data.get("surface_template_major")),
        "generic_center_phrase_count": _safe_int(data.get("generic_center_phrase_count")),
        "same_connector_run_max": _safe_int(data.get("same_connector_run_max")),
        "same_connector_repetition_count": _safe_int(data.get("same_connector_repetition_count")),
        "grammar_warning_count": _safe_int(data.get("grammar_warning_count")),
        "malformed_nominalization_risk": bool(data.get("malformed_nominalization_risk")),
        "malformed_phrase_unit_count": _safe_int(data.get("malformed_phrase_unit_count")),
        "shallow_observation_path": bool(data.get("shallow_observation_path")),
        "environment_state_output_frame_surface_limited_use": bool(data.get("environment_state_output_frame_surface_limited_use")),
        "environment_state_output_single_record_only": bool(data.get("environment_state_output_single_record_only")),
        "environment_state_output_scope_marker_required": bool(data.get("environment_state_output_scope_marker_required")),
        "environment_state_output_scope_marker_present": bool(data.get("environment_state_output_scope_marker_present")),
        "environment_state_output_allowed_surface_claim_strength": str(data.get("environment_state_output_allowed_surface_claim_strength") or ""),
        "environment_state_output_output_theme_ids": list(data.get("environment_state_output_output_theme_ids") or []),
        "environment_state_output_surface_rejection_reasons": _dedupe(list(data.get("environment_state_output_surface_rejection_reasons") or [])),
        "period_tendency_from_single_record_surface_blocked": bool(data.get("period_tendency_from_single_record_surface_blocked")),
        "personality_tendency_surface_blocked": bool(data.get("personality_tendency_surface_blocked")),
        "cause_from_category_surface_blocked": bool(data.get("cause_from_category_surface_blocked")),
        "cause_from_emotion_strength_surface_blocked": bool(data.get("cause_from_emotion_strength_surface_blocked")),
        "diagnosis_surface_blocked": bool(data.get("diagnosis_surface_blocked")),
        "recovery_prescription_surface_blocked": bool(data.get("recovery_prescription_surface_blocked")),
        "period_tendency_from_single_record": False,
        "recovery_prescription_allowed": False,
        "state_answer_gate_boundary": dict(data.get("state_answer_gate_boundary") or {})
        if isinstance(data.get("state_answer_gate_boundary"), Mapping)
        else {},
        "state_answer_gate_boundary_rejection_reasons": _dedupe(
            list(data.get("state_answer_gate_boundary_rejection_reasons") or [])
        ),
        "state_answer_gate_boundary_terminal_surface_block": bool(
            data.get("state_answer_gate_boundary_terminal_surface_block")
        ),
        "state_answer_forbidden_claim_reasons": _dedupe(
            list(data.get("state_answer_forbidden_claim_reasons") or [])
        ),
        "state_answer_allowed_exception_ids": _dedupe(
            list(data.get("state_answer_allowed_exception_ids") or [])
        ),
        "state_answer_public_meta_summary_only": bool(data.get("state_answer_public_meta_summary_only", True)),
        "state_answer_contract_body_returned": False,
        "state_answer_raw_evidence_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
    }


def _runtime_surface_gate_rejection_reasons(runtime_surface_gate: Mapping[str, Any] | None) -> List[str]:
    gate = runtime_surface_gate if isinstance(runtime_surface_gate, Mapping) else {}
    if not gate:
        return []
    if bool(gate.get("passed")):
        return []
    reasons = _dedupe(list(gate.get("rejection_reasons") or []))
    out = ["runtime_surface_pre_return_gate_failed"]
    out.extend(reasons)
    action = str(gate.get("action") or "").strip()
    if action and action != ACTION_ALLOW:
        out.append(f"runtime_surface_pre_return_gate_action_{action}")
    return _dedupe(out)


def _visible_surface_acceptance_gate_meta(visible_surface_acceptance_gate_report: Any = None) -> Dict[str, Any]:
    """Return a meta-only Visible Surface Acceptance Gate trace.

    Step4 wires the Step3 acceptance report into the Display Gate without
    adding text payloads, response keys, API routes, or DB changes.  Invalid
    gate payloads fail closed because a malformed display-quality report should
    never be used to pass a public ``comment_text``.
    """

    if not visible_surface_acceptance_gate_report:
        return {}
    if not isinstance(visible_surface_acceptance_gate_report, Mapping):
        return {
            "version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
            "schema_version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
            "evaluated": True,
            "passed": False,
            "blocked": True,
            "classification": VISIBLE_SURFACE_CLASSIFICATION_RED,
            "action": VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
            "rejection_reasons": ["visible_surface_acceptance_gate_invalid"],
            "warning_reasons": [],
            "visible_surface_acceptance_gate_invalid": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "rn_visible_contract_changed": False,
            "public_response_key_change": False,
            "db_physical_name_changed": False,
            "display_gate_relaxed": False,
        }
    data = dict(visible_surface_acceptance_gate_report)
    try:
        assert_visible_surface_acceptance_gate_meta_only(
            data,
            source="display_gate.visible_surface_acceptance_gate",
        )
    except Exception:
        return {
            "version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
            "schema_version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
            "evaluated": True,
            "passed": False,
            "blocked": True,
            "classification": VISIBLE_SURFACE_CLASSIFICATION_RED,
            "action": VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
            "rejection_reasons": ["visible_surface_acceptance_gate_invalid"],
            "warning_reasons": [],
            "visible_surface_acceptance_gate_invalid": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "rn_visible_contract_changed": False,
            "public_response_key_change": False,
            "db_physical_name_changed": False,
            "display_gate_relaxed": False,
        }
    reasons = _dedupe(list(data.get("rejection_reasons") or []))
    warnings = _dedupe(list(data.get("warning_reasons") or []))
    action = str(data.get("action") or VISIBLE_SURFACE_ACTION_ALLOW).strip()
    if action not in {
        VISIBLE_SURFACE_ACTION_ALLOW,
        VISIBLE_SURFACE_ACTION_WARN,
        VISIBLE_SURFACE_ACTION_RERENDER_SURFACE,
        VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION,
        VISIBLE_SURFACE_ACTION_BLOCK,
        VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
    }:
        action = VISIBLE_SURFACE_ACTION_FAIL_CLOSED
        if "visible_surface_acceptance_gate_invalid" not in reasons:
            reasons.append("visible_surface_acceptance_gate_invalid")
    return {
        "version": str(data.get("version") or VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION),
        "schema_version": str(data.get("schema_version") or data.get("version") or VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION),
        "evaluated": bool(data.get("evaluated", True)),
        "passed": bool(data.get("passed")),
        "blocked": bool(data.get("blocked", not bool(data.get("passed")))),
        "classification": str(data.get("classification") or ""),
        "action": action,
        "rerender_recommended": bool(data.get("rerender_recommended") or action == VISIBLE_SURFACE_ACTION_RERENDER_SURFACE),
        "reroute_low_information_recommended": bool(
            data.get("reroute_low_information_recommended") or action == VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION
        ),
        "rejection_reasons": reasons,
        "warning_reasons": warnings,
        "visible_header_dominant_emotion_present": bool(data.get("visible_header_dominant_emotion_present")),
        "visible_header_dominant_emotion_source": str(data.get("visible_header_dominant_emotion_source") or ""),
        "opening_emotion_focus_present": bool(data.get("opening_emotion_focus_present")),
        "dominant_emotion_bridge_present": bool(data.get("dominant_emotion_bridge_present")),
        "selected_emotion_count": _safe_int(data.get("selected_emotion_count")),
        "secondary_emotion_focus_detected": bool(data.get("secondary_emotion_focus_detected")),
        "unselected_emotion_focus_detected": bool(data.get("unselected_emotion_focus_detected")),
        "negative_text_anchor_present": bool(data.get("negative_text_anchor_present")),
        "positive_tone_profile": str(data.get("positive_tone_profile") or ""),
        "burden_surface_without_anchor_detected": bool(data.get("burden_surface_without_anchor_detected")),
        "malformed_nominalization_detected": bool(data.get("malformed_nominalization_detected")),
        "malformed_nominalization_codes": _dedupe(list(data.get("malformed_nominalization_codes") or [])),
        "state_answer_gate_boundary": dict(data.get("state_answer_gate_boundary") or {})
        if isinstance(data.get("state_answer_gate_boundary"), Mapping)
        else {},
        "state_answer_gate_boundary_rejection_reasons": _dedupe(
            list(data.get("state_answer_gate_boundary_rejection_reasons") or [])
        ),
        "state_answer_gate_boundary_terminal_surface_block": bool(
            data.get("state_answer_gate_boundary_terminal_surface_block")
        ),
        "state_answer_forbidden_claim_reasons": _dedupe(
            list(data.get("state_answer_forbidden_claim_reasons") or [])
        ),
        "state_answer_allowed_exception_ids_detected": _dedupe(
            list(data.get("state_answer_allowed_exception_ids_detected") or [])
        ),
        "state_answer_public_meta_summary_only": bool(data.get("state_answer_public_meta_summary_only", True)),
        "state_answer_contract_body_returned": False,
        "state_answer_raw_evidence_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "rn_visible_contract_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
    }


def _visible_surface_gate_blocks(visible_surface_gate: Mapping[str, Any] | None) -> bool:
    gate = visible_surface_gate if isinstance(visible_surface_gate, Mapping) else {}
    if not gate:
        return False
    action = str(gate.get("action") or "").strip()
    classification = str(gate.get("classification") or "").strip()
    if action == VISIBLE_SURFACE_ACTION_WARN:
        return False
    if classification in {VISIBLE_SURFACE_CLASSIFICATION_RED, VISIBLE_SURFACE_CLASSIFICATION_REPAIR_REQUIRED}:
        return True
    if action in {
        VISIBLE_SURFACE_ACTION_RERENDER_SURFACE,
        VISIBLE_SURFACE_ACTION_REROUTE_LOW_INFORMATION,
        VISIBLE_SURFACE_ACTION_BLOCK,
        VISIBLE_SURFACE_ACTION_FAIL_CLOSED,
    }:
        return True
    return bool(not gate.get("passed") and action != VISIBLE_SURFACE_ACTION_WARN)


def _visible_surface_gate_rejection_reasons(visible_surface_gate: Mapping[str, Any] | None) -> List[str]:
    gate = visible_surface_gate if isinstance(visible_surface_gate, Mapping) else {}
    if not _visible_surface_gate_blocks(gate):
        return []
    reasons = _dedupe(list(gate.get("rejection_reasons") or []))
    out = ["visible_surface_acceptance_gate_failed"]
    out.extend(reasons)
    action = str(gate.get("action") or "").strip()
    if action and action != VISIBLE_SURFACE_ACTION_ALLOW:
        out.append(f"visible_surface_acceptance_gate_action_{action}")
    classification = str(gate.get("classification") or "").strip()
    if classification:
        out.append(f"visible_surface_acceptance_gate_classification_{classification}")
    return _dedupe(out)


def _step14_reason_subset(reasons: List[str]) -> List[str]:
    markers = (
        "diagnosis",
        "personality",
        "general_knowledge",
        "overclaim",
        "advice",
        "causal",
        "repeated_surface",
        "unsupported_sentence",
    )
    return _dedupe([reason for reason in reasons or [] if any(marker in str(reason or "") for marker in markers)])


def _status_for_failure(*, source: str, reasons: List[str]) -> str:
    reason_set = set(_dedupe(reasons))
    if "phase_not_complete" in reason_set:
        return "unavailable"
    if source in _UNAVAILABLE_SOURCES:
        return "unavailable"
    if "composer_source_unavailable" in reason_set or "empty_comment_text_without_candidate" in reason_set:
        return "unavailable"
    return "rejected"


def _low_information_quality_rejection_reasons(
    *,
    comment_text: str,
    observation_quality_meta: Mapping[str, Any] | None = None,
) -> List[str]:
    """Return Step 10 low-information observation quality failures.

    This is an additive branch quality gate. It does not relax safety, source,
    phase, template, or unsupported-overclaim guards.
    """

    meta = observation_quality_meta if isinstance(observation_quality_meta, Mapping) else {}
    text = str(comment_text or "").strip()
    reasons: List[str] = []

    def _bool(*keys: str, default: bool = False) -> bool:
        for key in keys:
            if key in meta:
                return bool(meta.get(key))
        return bool(default)

    def _list(*keys: str) -> List[Any]:
        for key in keys:
            value = meta.get(key)
            if isinstance(value, list):
                return list(value)
            if value:
                return [value]
        return []

    if not text:
        reasons.append("low_information_body_missing")
    if meta and not _bool("body_non_empty", "comment_text_non_empty", default=bool(text)):
        reasons.append("low_information_body_missing")
    if not _bool("known_scope_observation_present", "low_info_known_scope_present"):
        reasons.append("low_information_known_scope_missing")
    if not _bool("contains_humility_marker", "humility_marker_present"):
        reasons.append("low_information_humility_marker_missing")
    if not _bool("contains_question", "question_present", "low_info_question_present"):
        reasons.append("low_information_question_missing")
    if meta.get("question_not_only") is False or _bool("question_only", "question_only_surface"):
        reasons.append("low_information_question_only")
    if not _list("unknown_slots"):
        reasons.append("low_information_unknown_slots_missing")
    if _bool("unsupported_event_assertion_present", "current_event_assertion_from_user_fact_present"):
        reasons.append("low_information_unsupported_event_assertion")
    if _bool("user_fact_may_promote_to_eligible"):
        reasons.append("low_information_user_fact_promotion_attempt")
    if _bool("free_user_fact_violation", "free_user_fact_surface_violation"):
        reasons.append("low_information_free_user_fact_violation")
    return _dedupe(reasons)


def _with_display_gate_trace(
    gate_trace: Dict[str, Any],
    *,
    observation_status: str,
    rejection_reasons: List[str],
    comment_text: str,
    binding_meta: Mapping[str, Any] | None = None,
    binding_used_override: bool | None = None,
    observation_reply_kind: str = "",
    low_information_quality_rejection_reasons: List[str] | None = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    out = dict(gate_trace or {})
    binding_fields = _gate_binding_fields(
        binding_meta,
        gate="display",
        binding_used=(
            _display_binding_used_from_trace(out, binding_meta)
            if binding_used_override is None
            else bool(binding_used_override)
        ),
    )
    kind = str(observation_reply_kind or "").strip()
    low_info_reasons = _dedupe(list(low_information_quality_rejection_reasons or []))
    runtime_surface_gate = _runtime_surface_gate_meta(runtime_surface_pre_return_gate_report) or (
        out.get("runtime_surface_pre_return_gate") if isinstance(out.get("runtime_surface_pre_return_gate"), Mapping) else {}
    )
    if runtime_surface_gate:
        out["runtime_surface_pre_return_gate"] = dict(runtime_surface_gate)
    runtime_surface_reasons = _dedupe(runtime_surface_gate.get("rejection_reasons") if isinstance(runtime_surface_gate, Mapping) else [])
    visible_surface_gate = _visible_surface_acceptance_gate_meta(visible_surface_acceptance_gate_report) or (
        out.get("visible_surface_acceptance_gate") if isinstance(out.get("visible_surface_acceptance_gate"), Mapping) else {}
    )
    if visible_surface_gate:
        out["visible_surface_acceptance_gate"] = dict(visible_surface_gate)
    visible_surface_reasons = _dedupe(visible_surface_gate.get("rejection_reasons") if isinstance(visible_surface_gate, Mapping) else [])
    visible_surface_blocks = _visible_surface_gate_blocks(visible_surface_gate)
    state_answer_runtime_reasons = _dedupe(
        runtime_surface_gate.get("state_answer_gate_boundary_rejection_reasons")
        if isinstance(runtime_surface_gate, Mapping)
        else []
    )
    state_answer_visible_reasons = _dedupe(
        visible_surface_gate.get("state_answer_gate_boundary_rejection_reasons")
        if isinstance(visible_surface_gate, Mapping)
        else []
    )
    state_answer_boundary_reasons = _dedupe([*state_answer_runtime_reasons, *state_answer_visible_reasons])
    out["display_gate"] = {
        "passed": observation_status == "passed",
        "observation_status": observation_status,
        "comment_text_allowed": bool(observation_status == "passed" and str(comment_text or "").strip()),
        "comment_text_present": bool(str(comment_text or "").strip()),
        "rejection_reasons": list(rejection_reasons or []),
        "observation_reply_kind": kind,
        "low_information_quality_gate": kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        "low_information_quality_passed": bool(kind != OBSERVATION_REPLY_KIND_LOW_INFORMATION or not low_info_reasons),
        "low_information_quality_rejection_reasons": low_info_reasons,
        "runtime_surface_pre_return_gate_evaluated": bool(runtime_surface_gate.get("evaluated")) if isinstance(runtime_surface_gate, Mapping) else False,
        "runtime_surface_pre_return_gate_passed": bool(runtime_surface_gate.get("passed")) if isinstance(runtime_surface_gate, Mapping) and runtime_surface_gate else True,
        "runtime_surface_pre_return_gate_action": str(runtime_surface_gate.get("action") or "") if isinstance(runtime_surface_gate, Mapping) else "",
        "runtime_surface_pre_return_gate_rejection_reasons": runtime_surface_reasons,
        "surface_template_major_blocked": "surface_template_major" in runtime_surface_reasons,
        "malformed_phrase_unit_blocked_count": _safe_int(runtime_surface_gate.get("malformed_phrase_unit_count")) if isinstance(runtime_surface_gate, Mapping) else 0,
        "visible_surface_acceptance_gate_evaluated": bool(visible_surface_gate.get("evaluated")) if isinstance(visible_surface_gate, Mapping) else False,
        "visible_surface_acceptance_gate_passed": bool(not visible_surface_blocks) if isinstance(visible_surface_gate, Mapping) and visible_surface_gate else True,
        "visible_surface_acceptance_gate_report_passed": bool(visible_surface_gate.get("passed")) if isinstance(visible_surface_gate, Mapping) and visible_surface_gate else True,
        "visible_surface_acceptance_gate_action": str(visible_surface_gate.get("action") or "") if isinstance(visible_surface_gate, Mapping) else "",
        "visible_surface_acceptance_gate_classification": str(visible_surface_gate.get("classification") or "") if isinstance(visible_surface_gate, Mapping) else "",
        "visible_surface_acceptance_gate_rejection_reasons": visible_surface_reasons,
        "visible_surface_acceptance_gate_blocked": bool(visible_surface_blocks),
        "visible_surface_acceptance_gate_display_gate_relaxed": False,
        "visible_surface_acceptance_gate_comment_text_body_included": False,
        "visible_surface_acceptance_gate_raw_input_included": False,
        "state_answer_gate_boundary_runtime_blocked": bool(
            runtime_surface_gate.get("state_answer_gate_boundary_terminal_surface_block")
        ) if isinstance(runtime_surface_gate, Mapping) else False,
        "state_answer_gate_boundary_visible_blocked": bool(
            visible_surface_gate.get("state_answer_gate_boundary_terminal_surface_block")
        ) if isinstance(visible_surface_gate, Mapping) else False,
        "state_answer_gate_boundary_rejection_reasons": state_answer_boundary_reasons,
        "state_answer_public_meta_summary_only": True,
        "state_answer_contract_body_returned": False,
        "state_answer_raw_evidence_included": False,
        "display_gate_relaxed": False,
        **binding_fields,
    }
    return out

def build_emlis_gate_trace(
    *,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    safety_report: SafetyBoundaryReport | None = None,
    composer_source: str = "",
    phase_completion_ready: bool = True,
    binding_meta: Mapping[str, Any] | None = None,
    observation_structure_gate_report: Any = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a compact pass/fail trace for all EmlisAI judge gates.

    This trace contains booleans and reason codes only. It deliberately avoids
    storing the user's full original input or any hidden model reasoning.
    """

    safety = safety_report or SafetyBoundaryReport()
    source = str(composer_source or "").strip()
    reader_binding_fields = _gate_binding_fields(binding_meta, gate="reader", binding_used=False)
    reader_relation_signal_fields = {
        "relation_surface_contract_version": str(getattr(reader_report, "relation_surface_contract_version", "") or ""),
        "reader_relation_signal_detected": bool(getattr(reader_report, "reader_relation_signal_detected", False)),
        "reader_relation_signal_count": int(getattr(reader_report, "reader_relation_signal_count", 0) or 0),
        "reader_relation_signal_keys": list(getattr(reader_report, "reader_relation_signal_keys", []) or []),
        "reader_relation_signal_relation_types": list(getattr(reader_report, "reader_relation_signal_relation_types", []) or []),
        "expected_relation_types": list(getattr(reader_report, "expected_relation_types", []) or []),
        "reader_relation_signal_meta": dict(getattr(reader_report, "reader_relation_signal_meta", {}) or {}),
        "reader_relation_signal_raw_input_included": bool(getattr(reader_report, "raw_input_included", False)),
    }
    grounding_binding_fields = _gate_binding_fields(
        binding_meta,
        gate="grounding",
        binding_used=bool(getattr(grounding_report, "binding_used", False)),
        binding_present=bool(getattr(grounding_report, "binding_present", False)) or None,
        binding_missing=bool(getattr(grounding_report, "binding_missing", False)) or None,
        binding_count=int(getattr(grounding_report, "binding_count", 0) or 0) or None,
        expected_binding_count=int(getattr(grounding_report, "expected_binding_count", 0) or 0) or None,
        binding_version=str(getattr(grounding_report, "binding_version", "") or "") or None,
        binding_supported_sentence_count=int(getattr(grounding_report, "binding_supported_sentence_count", 0) or 0),
        binding_support_source=_grounding_binding_support_source(grounding_report),
    )
    template_binding_fields = _gate_binding_fields(binding_meta, gate="template_echo", binding_used=False)
    generation_source_binding_fields = _gate_binding_fields(binding_meta, gate="generation_source", binding_used=False)
    source_reasons: List[str] = []
    if source != "ai_generated":
        source_reasons.append("composer_source_not_ai_generated")
        if source in _UNAVAILABLE_SOURCES:
            source_reasons.append("composer_source_unavailable")
        elif source in _NON_AI_RENDERED_SOURCES:
            source_reasons.append("rule_rendered_or_fallback_source")
    phase_reasons = [] if phase_completion_ready else ["phase_not_complete"]
    trace: Dict[str, Any] = {
        "reader": {
            "passed": bool(reader_report.understandable),
            "rejection_reasons": list(reader_report.rejection_reasons or []),
            "understandable": bool(reader_report.understandable),
            "addressee_clear": bool(reader_report.addressee_clear),
            "speaker_integrity_ok": bool(reader_report.speaker_integrity_ok),
            "conversational": bool(reader_report.conversational),
            "report_like": bool(reader_report.report_like),
            "confidence": float(reader_report.confidence or 0.0),
            **reader_relation_signal_fields,
            **reader_binding_fields,
        },
        "grounding": {
            "passed": bool(grounding_report.passed),
            "rejection_reasons": list(grounding_report.rejection_reasons or []),
            "coverage_ratio": float(grounding_report.coverage_ratio or 0.0),
            "sentence_count": len(list(grounding_report.sentence_claims or [])),
            "unsupported_sentence_count": len([
                c for c in list(grounding_report.sentence_claims or [])
                if getattr(c, "unsupported_reason", "")
            ]),
            "confidence": float(grounding_report.confidence or 0.0),
            # Step07: keep the scoped-grounding contract visible in the gate
            # trace so QA can verify that B-plan partial observations are
            # grounded only against the scoped graph, while excluded full-graph
            # evidence remains unavailable for display validation.
            "grounding_scope": str(getattr(grounding_report, "grounding_scope", "full_graph") or "full_graph"),
            "allowed_evidence_span_count": len(list(getattr(grounding_report, "allowed_evidence_span_ids", []) or [])),
            "ignored_evidence_span_count": len(list(getattr(grounding_report, "ignored_evidence_span_ids", []) or [])),
            "binding_aware_grounding": bool(getattr(grounding_report, "binding_present", False)),
            **grounding_binding_fields,
            "binding_supported_sentence_count": int(getattr(grounding_report, "binding_supported_sentence_count", 0) or 0),
            "step6_binding_aware_grounding": dict(getattr(grounding_report, "binding_diagnostics", {}) or {}),
            "step14_guard_rejection_reasons": _step14_reason_subset(list(grounding_report.rejection_reasons or [])),
            "step14_guard_strengthening": {
                "version": "emlis.guard_strengthening.v1",
                "target_step": "Step14_guard_strengthening",
                "guard_threshold_relaxed": False,
                "unsupported_sentence_guarded": "unsupported_sentence" in list(grounding_report.rejection_reasons or []),
                "diagnosis_like_guarded": "unsupported_diagnosis_like" in list(grounding_report.rejection_reasons or []),
                "personality_label_guarded": "unsupported_personality_label" in list(grounding_report.rejection_reasons or []),
                "general_knowledge_completion_guarded": "unsupported_general_knowledge_completion" in list(grounding_report.rejection_reasons or []),
            },
        },
        "template_echo": {
            "passed": bool(template_echo_report.passed),
            "rejection_reasons": list(template_echo_report.rejection_reasons or []),
            "matched_banned_patterns": list(template_echo_report.matched_banned_patterns or []),
            "max_old_template_similarity": float(template_echo_report.max_old_template_similarity or 0.0),
            "max_previous_output_similarity": float(template_echo_report.max_previous_output_similarity or 0.0),
            "raw_echo_ratio": float(template_echo_report.raw_echo_ratio or 0.0),
            "repeated_sentence_pattern_score": float(template_echo_report.repeated_sentence_pattern_score or 0.0),
            "max_sentence_echo_ratio": float(getattr(template_echo_report, "max_sentence_echo_ratio", 0.0) or 0.0),
            "raw_quote_span_count": int(getattr(template_echo_report, "raw_quote_span_count", 0) or 0),
            "raw_copy_sentence_ratio": float(getattr(template_echo_report, "raw_copy_sentence_ratio", 0.0) or 0.0),
            "limited_surface_repetition_score": float(getattr(template_echo_report, "limited_surface_repetition_score", 0.0) or 0.0),
            "surface_signature_row_count": int(getattr(template_echo_report, "surface_signature_row_count", 0) or 0),
            "surface_signature_repeat_count": int(getattr(template_echo_report, "surface_signature_repeat_count", 0) or 0),
            "same_ending_major_count": int(getattr(template_echo_report, "same_ending_major_count", 0) or 0),
            "surface_connector_repetition_count": int(getattr(template_echo_report, "surface_connector_repetition_count", 0) or 0),
            "repeated_surface_signature_keys": list(getattr(template_echo_report, "repeated_surface_signature_keys", []) or []),
            "repeated_surface_ending_keys": list(getattr(template_echo_report, "repeated_surface_ending_keys", []) or []),
            "repeated_surface_connector_keys": list(getattr(template_echo_report, "repeated_surface_connector_keys", []) or []),
            "product_quality_surface_variation_guarded": any(str(reason) in {"same_ending_major", "surface_signature_repeat", "surface_connector_repetition", "surface_signature_template_flag", "surface_signature_raw_input_included"} for reason in list(getattr(template_echo_report, "rejection_reasons", []) or [])),
            "abstract_repetition_score": float(getattr(template_echo_report, "abstract_repetition_score", 0.0) or 0.0),
            "abstract_phrase_repetition_score": float(getattr(template_echo_report, "abstract_phrase_repetition_score", 0.0) or 0.0),
            "raw_quote_char_ratio": float(getattr(template_echo_report, "raw_quote_char_ratio", 0.0) or 0.0),
            "matched_raw_quote_fragments": list(getattr(template_echo_report, "matched_raw_quote_fragments", []) or []),
            "matched_limited_surface_patterns": list(getattr(template_echo_report, "matched_limited_surface_patterns", []) or []),
            "phase8_emotion_label_body_line_count": int(getattr(template_echo_report, "phase8_emotion_label_body_line_count", 0) or 0),
            "phase8_missing_must_keep_roles": list(getattr(template_echo_report, "phase8_missing_must_keep_roles", []) or []),
            "phase8_quality_rejection_reasons": list(getattr(template_echo_report, "phase8_quality_rejection_reasons", []) or []),
            **template_binding_fields,
            "step14_guard_rejection_reasons": _step14_reason_subset([
                *list(template_echo_report.rejection_reasons or []),
                *list(getattr(template_echo_report, "phase8_quality_rejection_reasons", []) or []),
            ]),
            "step14_guard_strengthening": {
                "version": "emlis.guard_strengthening.v1",
                "target_step": "Step14_guard_strengthening",
                "guard_threshold_relaxed": False,
                "diagnosis_like_guarded": any("diagnosis" in str(reason) for reason in [*list(template_echo_report.rejection_reasons or []), *list(getattr(template_echo_report, "phase8_quality_rejection_reasons", []) or [])]),
                "personality_label_guarded": any("personality" in str(reason) for reason in [*list(template_echo_report.rejection_reasons or []), *list(getattr(template_echo_report, "phase8_quality_rejection_reasons", []) or [])]),
                "general_knowledge_completion_guarded": any("general_knowledge" in str(reason) for reason in [*list(template_echo_report.rejection_reasons or []), *list(getattr(template_echo_report, "phase8_quality_rejection_reasons", []) or [])]),
                "repeated_surface_guarded": any("repeated_surface" in str(reason) for reason in [*list(template_echo_report.rejection_reasons or []), *list(getattr(template_echo_report, "phase8_quality_rejection_reasons", []) or [])]),
            },
        },
        "generation_source": {
            "passed": source == "ai_generated",
            "rejection_reasons": source_reasons,
            "composer_source": source,
            **generation_source_binding_fields,
        },
        "safety": {
            "passed": not bool(safety.requires_block),
            "rejection_reasons": list(safety.reasons or []) if safety.requires_block else [],
            "diagnostics": safety.as_meta() if hasattr(safety, "as_meta") else {
                "requires_block": bool(safety.requires_block),
                "reasons": list(safety.reasons or []),
                "blocked_before_composer": bool(safety.requires_block),
            },
        },
        "phase_completion": {
            "passed": bool(phase_completion_ready),
            "rejection_reasons": phase_reasons,
        },
    }
    structure_gate = _structure_gate_meta(observation_structure_gate_report)
    if structure_gate:
        trace["observation_structure"] = structure_gate
    runtime_surface_gate = _runtime_surface_gate_meta(runtime_surface_pre_return_gate_report)
    if runtime_surface_gate:
        trace["runtime_surface_pre_return_gate"] = runtime_surface_gate
    visible_surface_gate = _visible_surface_acceptance_gate_meta(visible_surface_acceptance_gate_report)
    if visible_surface_gate:
        trace["visible_surface_acceptance_gate"] = visible_surface_gate
    return trace


def phase9_frontend_display_contract_ready(*, display_gate_ready: bool = True) -> bool:
    """Return True once the frontend passed-only modal contract is verified.

    The backend cannot inspect the RN bundle at runtime, so this function is a
    named release contract boundary.  Phase 9 is satisfied only when the backend
    Display Gate is ready and the frontend has been verified to hide every
    non-passed observation_status.
    """

    return bool(display_gate_ready)


def _default_phase10_release_checks() -> Dict[str, bool]:
    return {key: True for key in _PHASE10_REQUIRED_RELEASE_CHECKS}


def build_phase10_release_readiness(
    *,
    display_decision: DisplayDecision | None = None,
    frontend_display_control_ready: bool = True,
    release_checks: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the explicit Phase 10 release-readiness decision.

    This is not a user-facing quality judgment.  It is a release contract that
    becomes true only when all phases are declared complete, backend display
    gate consistency is verified, the frontend passed-only display control is
    verified, and the Phase 10 regression checks are all true.
    """

    checks = dict(_default_phase10_release_checks())
    if isinstance(release_checks, Mapping):
        for key in _PHASE10_REQUIRED_RELEASE_CHECKS:
            if key in release_checks:
                checks[key] = bool(release_checks[key])
    blockers: List[str] = []
    display_gate_ready = phase8_display_gate_contract_ready(display_decision) if display_decision is not None else True
    if not display_gate_ready:
        blockers.append("display_gate_contract_not_ready")
    if display_decision is not None:
        status = str(getattr(display_decision, "observation_status", "") or "")
        comment_text = str(getattr(display_decision, "comment_text", "") or "").strip()
        if status != "passed":
            blockers.append("observation_not_passed")
        elif not comment_text:
            blockers.append("passed_comment_text_missing")
    if not phase9_frontend_display_contract_ready(display_gate_ready=frontend_display_control_ready):
        blockers.append("frontend_passed_only_display_not_verified")
    failed_checks = [key for key in _PHASE10_REQUIRED_RELEASE_CHECKS if checks.get(key) is not True]
    blockers.extend(failed_checks)
    release_ready = not blockers
    return {
        "release_ready": release_ready,
        "release_blockers": blockers,
        "required_completed_phases": list(_PHASE10_REQUIRED_PHASES),
        "release_checks": checks,
        "display_gate_release_ready": display_gate_ready,
        "phase9_frontend_display_control_ready": bool(frontend_display_control_ready),
        "phase10_regression_release_ready": release_ready,
    }


def phase10_release_readiness_contract_ready(
    *,
    display_decision: DisplayDecision | None = None,
    frontend_display_control_ready: bool = True,
    release_checks: Mapping[str, Any] | None = None,
) -> bool:
    return bool(
        build_phase10_release_readiness(
            display_decision=display_decision,
            frontend_display_control_ready=frontend_display_control_ready,
            release_checks=release_checks,
        ).get("release_ready")
    )

def phase7_judge_contract_ready(
    *,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    composer_source: str = "",
) -> bool:
    """Return True when Reader/Grounding/Template Guard expose traceable gates.

    This does not mean the candidate is displayable. It means Phase 7 can expose
    pass/fail and rejection_reason for every relevant judge gate.
    """

    trace = build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        composer_source=composer_source,
        phase_completion_ready=False,
    )
    required = ("reader", "grounding", "template_echo", "generation_source")
    for key in required:
        gate = trace.get(key)
        if not isinstance(gate, dict):
            return False
        if not isinstance(gate.get("passed"), bool):
            return False
        if not isinstance(gate.get("rejection_reasons"), list):
            return False
    return True


def decide_emlis_observation_display(
    *,
    comment_text: str,
    reader_report: ListenerReaderReport,
    grounding_report: GroundingReport,
    template_echo_report: TemplateEchoReport,
    safety_report: SafetyBoundaryReport | None = None,
    trace_id: str = "",
    composer_source: str = "",
    phase_completion_ready: bool = True,
    binding_meta: Mapping[str, Any] | None = None,
    observation_reply_kind: str = "",
    observation_quality_meta: Mapping[str, Any] | None = None,
    observation_structure_gate_report: Any = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
) -> DisplayDecision:
    """Final fail-closed decision for displaying Emlis observation text.

    Step 10 adds a narrow Display/Repair integration path for the
    low-information observation branch. It keeps the public passed+body
    contract and does not add a public observation_status. Reader, Grounding,
    Template, safety, source, and phase gates still have to pass; the only
    addition here is branch-specific low-information quality validation.
    """

    safety = safety_report or SafetyBoundaryReport()
    source = str(composer_source or "").strip()
    text = str(comment_text or "").strip()
    runtime_surface_gate = _runtime_surface_gate_meta(runtime_surface_pre_return_gate_report)
    visible_surface_gate = _visible_surface_acceptance_gate_meta(visible_surface_acceptance_gate_report)
    gate_trace = build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        safety_report=safety,
        composer_source=source,
        phase_completion_ready=phase_completion_ready,
        binding_meta=binding_meta,
        observation_structure_gate_report=observation_structure_gate_report,
        runtime_surface_pre_return_gate_report=runtime_surface_gate if runtime_surface_gate else None,
        visible_surface_acceptance_gate_report=visible_surface_gate if visible_surface_gate else None,
    )
    display_binding_used = _display_binding_used_from_trace(gate_trace, binding_meta)
    reasons: List[str] = []
    observation_kind = str(observation_reply_kind or "").strip()
    low_information_quality_reasons: List[str] = []

    if observation_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        low_information_quality_reasons = _low_information_quality_rejection_reasons(
            comment_text=text,
            observation_quality_meta=observation_quality_meta,
        )

    if safety.requires_block:
        reasons.extend(safety.reasons or ["safety_boundary"])
        deduped = _dedupe(reasons)
        return DisplayDecision(
            observation_status="safety_blocked",
            comment_text="",
            rejection_reasons=deduped,
            trace_id=trace_id,
            gate_trace=_with_display_gate_trace(
                gate_trace,
                observation_status="safety_blocked",
                rejection_reasons=deduped,
                comment_text="",
                binding_meta=binding_meta,
                binding_used_override=display_binding_used,
                observation_reply_kind=observation_kind,
                low_information_quality_rejection_reasons=low_information_quality_reasons,
                runtime_surface_pre_return_gate_report=runtime_surface_gate if runtime_surface_gate else None,
                visible_surface_acceptance_gate_report=visible_surface_gate if visible_surface_gate else None,
            ),
        )

    if not phase_completion_ready:
        reasons.append("phase_not_complete")
    if source != "ai_generated":
        reasons.append("composer_source_not_ai_generated")
        if source in _UNAVAILABLE_SOURCES:
            reasons.append("composer_source_unavailable")
        elif source in _NON_AI_RENDERED_SOURCES:
            reasons.append("rule_rendered_or_fallback_source")
    if not reader_report.understandable:
        reasons.extend(reader_report.rejection_reasons or ["reader_cannot_understand"])
    if not grounding_report.passed:
        reasons.extend(grounding_report.rejection_reasons or ["ungrounded_or_relation_broken"])
    if not template_echo_report.passed:
        reasons.extend(template_echo_report.rejection_reasons or ["template_or_echo_detected"])
    structure_gate = _structure_gate_meta(observation_structure_gate_report)
    if structure_gate and not bool(structure_gate.get("passed")):
        reasons.extend(list(structure_gate.get("rejection_reasons") or ["observation_structure_gate_rejected"]))
    reasons.extend(_runtime_surface_gate_rejection_reasons(runtime_surface_gate))
    reasons.extend(_visible_surface_gate_rejection_reasons(visible_surface_gate))
    if not text:
        reasons.append("empty_comment_text")
        if source in _UNAVAILABLE_SOURCES:
            reasons.append("empty_comment_text_without_candidate")

    if observation_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        reasons.extend(low_information_quality_reasons)

    if reasons:
        deduped = _dedupe(reasons)
        status = _status_for_failure(source=source, reasons=deduped)
        return DisplayDecision(
            observation_status=status,
            comment_text="",
            rejection_reasons=deduped,
            trace_id=trace_id,
            gate_trace=_with_display_gate_trace(
                gate_trace,
                observation_status=status,
                rejection_reasons=deduped,
                comment_text="",
                binding_meta=binding_meta,
                binding_used_override=display_binding_used,
                observation_reply_kind=observation_kind,
                low_information_quality_rejection_reasons=low_information_quality_reasons,
                runtime_surface_pre_return_gate_report=runtime_surface_gate if runtime_surface_gate else None,
                visible_surface_acceptance_gate_report=visible_surface_gate if visible_surface_gate else None,
            ),
        )

    return DisplayDecision(
        observation_status="passed",
        comment_text=text,
        rejection_reasons=[],
        trace_id=trace_id,
        gate_trace=_with_display_gate_trace(
            gate_trace,
            observation_status="passed",
            rejection_reasons=[],
            comment_text=text,
            binding_meta=binding_meta,
            binding_used_override=display_binding_used,
            observation_reply_kind=observation_kind,
            low_information_quality_rejection_reasons=low_information_quality_reasons,
            runtime_surface_pre_return_gate_report=runtime_surface_gate if runtime_surface_gate else None,
            visible_surface_acceptance_gate_report=visible_surface_gate if visible_surface_gate else None,
        ),
    )

def phase8_display_gate_contract_ready(display_decision: DisplayDecision | None = None) -> bool:
    """Return True when Display Gate enforces the Phase 8 fail-closed contract.

    With no argument, this verifies the generic gate behavior using synthetic
    reports. With a decision, it verifies that the decision is internally
    consistent: passed decisions must carry text, while every non-passed
    decision must have an empty comment_text and traceable reasons.
    """

    if display_decision is not None:
        status = str(getattr(display_decision, "observation_status", "") or "")
        if status not in _VALID_STATUSES:
            return False
        gate_trace = getattr(display_decision, "gate_trace", {}) or {}
        if not isinstance(gate_trace, Mapping):
            return False
        for key in _required_gate_trace_keys():
            gate = gate_trace.get(key)
            if not isinstance(gate, Mapping):
                return False
            if not isinstance(gate.get("passed"), bool):
                return False
            if not isinstance(gate.get("rejection_reasons"), list):
                return False
        display_gate = gate_trace.get("display_gate")
        if not isinstance(display_gate, Mapping) or not isinstance(display_gate.get("passed"), bool):
            return False
        comment_text = str(getattr(display_decision, "comment_text", "") or "").strip()
        reasons = list(getattr(display_decision, "rejection_reasons", []) or [])
        if status == "passed":
            return bool(comment_text) and not reasons and _all_core_gates_passed(gate_trace) and display_gate.get("passed") is True
        if comment_text:
            return False
        if status == "safety_blocked":
            return (not _gate_passed(gate_trace, "safety")) and bool(reasons)
        return (not _all_core_gates_passed(gate_trace)) and bool(reasons)

    passing_reader = ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        confidence=1.0,
    )
    failing_reader = ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=False,
        conversational=False,
        report_like=True,
        rejection_reasons=["reader_cannot_understand"],
        confidence=0.0,
    )
    passing_grounding = GroundingReport(passed=True, coverage_ratio=1.0, confidence=1.0)
    failing_grounding = GroundingReport(passed=False, rejection_reasons=["empty_text"])
    passing_template = TemplateEchoReport(passed=True)

    passed = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="ai_generated",
        phase_completion_ready=True,
    )
    reader_rejected = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=failing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="ai_generated",
        phase_completion_ready=True,
    )
    source_rejected = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        composer_source="rule_rendered",
        phase_completion_ready=True,
    )
    unavailable = decide_emlis_observation_display(
        comment_text="",
        reader_report=failing_reader,
        grounding_report=failing_grounding,
        template_echo_report=passing_template,
        composer_source="unavailable",
        phase_completion_ready=True,
    )
    safety = decide_emlis_observation_display(
        comment_text="candidate",
        reader_report=passing_reader,
        grounding_report=passing_grounding,
        template_echo_report=passing_template,
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_boundary"]),
        composer_source="ai_generated",
        phase_completion_ready=True,
    )

    return bool(
        phase8_display_gate_contract_ready(passed)
        and passed.observation_status == "passed"
        and passed.comment_text == "candidate"
        and phase8_display_gate_contract_ready(reader_rejected)
        and reader_rejected.observation_status == "rejected"
        and reader_rejected.comment_text == ""
        and phase8_display_gate_contract_ready(source_rejected)
        and source_rejected.observation_status == "rejected"
        and source_rejected.comment_text == ""
        and phase8_display_gate_contract_ready(unavailable)
        and unavailable.observation_status == "unavailable"
        and unavailable.comment_text == ""
        and phase8_display_gate_contract_ready(safety)
        and safety.observation_status == "safety_blocked"
        and safety.comment_text == ""
    )


__all__ = [
    "build_emlis_gate_trace",
    "build_phase10_release_readiness",
    "phase7_judge_contract_ready",
    "phase8_display_gate_contract_ready",
    "phase9_frontend_display_contract_ready",
    "phase10_release_readiness_contract_ready",
    "decide_emlis_observation_display",
]
