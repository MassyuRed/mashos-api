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


def _dedupe(values: List[str]) -> List[str]:
    return list(dict.fromkeys(str(v) for v in values if str(v)))



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
    return all(_gate_passed(gate_trace, key) for key in _required_gate_trace_keys())


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


def _with_display_gate_trace(
    gate_trace: Dict[str, Any],
    *,
    observation_status: str,
    rejection_reasons: List[str],
    comment_text: str,
    binding_meta: Mapping[str, Any] | None = None,
    binding_used_override: bool | None = None,
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
    out["display_gate"] = {
        "passed": observation_status == "passed",
        "observation_status": observation_status,
        "comment_text_allowed": bool(observation_status == "passed" and str(comment_text or "").strip()),
        "comment_text_present": bool(str(comment_text or "").strip()),
        "rejection_reasons": list(rejection_reasons or []),
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
    return {
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
) -> DisplayDecision:
    """Final fail-closed decision for displaying Emlis observation text."""

    safety = safety_report or SafetyBoundaryReport()
    source = str(composer_source or "").strip()
    text = str(comment_text or "").strip()
    gate_trace = build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        safety_report=safety,
        composer_source=source,
        phase_completion_ready=phase_completion_ready,
        binding_meta=binding_meta,
    )
    display_binding_used = _display_binding_used_from_trace(gate_trace, binding_meta)
    reasons: List[str] = []

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
    if not text:
        reasons.append("empty_comment_text")
        if source in _UNAVAILABLE_SOURCES:
            reasons.append("empty_comment_text_without_candidate")

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
