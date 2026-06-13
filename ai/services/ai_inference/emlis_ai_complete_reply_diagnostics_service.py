# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 11 Reply service / diagnostics integration for Complete Composer.

This module is deliberately meta-only. It reads the Complete Composer initial
candidate produced by Step 10 and creates sanitized diagnostics for the reply
service, diagnostic_summary, repair trace handoff, and future scorecard input.
It does not assign ``input_feedback.comment_text``, does not change
``observation_status``, and does not add or rename public response keys.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

from emlis_ai_complete_composer_initial_meta import (
    COMPLETE_COMPOSER_INITIAL_MODEL,
    build_complete_composer_initial_term_meta,
)
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_relation_surface_contract import (
    RELATION_SURFACE_CONTRACT_VERSION,
    relation_surface_status_for_reader,
)
from emlis_ai_complete_surface_quality_signature import (
    SURFACE_QUALITY_SIGNATURE_VERSION,
    assert_surface_quality_signature_meta_only,
    build_surface_quality_signature,
    normalize_surface_signature_to_scorecard_event,
)
from emlis_ai_runtime_surface_source_lock import (
    RUNTIME_SURFACE_SOURCE_LOCK_VERSION,
    build_runtime_surface_source_lock,
)
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW as RUNTIME_SURFACE_ACTION_ALLOW,
    ACTION_BLOCK as RUNTIME_SURFACE_ACTION_BLOCK,
    ACTION_FAIL_CLOSED as RUNTIME_SURFACE_ACTION_FAIL_CLOSED,
    RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
    assert_runtime_surface_pre_return_gate_meta_only,
)
from emlis_ai_runtime_surface_tone_engine_2_1 import (
    RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
    normalize_tone_engine_2_1_to_scorecard_event,
)

COMPLETE_REPLY_DIAGNOSTICS_VERSION = "emlis.complete_reply_service_diagnostics.v1"
COMPLETE_SCORECARD_EVENT_VERSION = "emlis.complete_scorecard_event.v1"
COMPLETE_REPLY_DIAGNOSTICS_STAGE = "Step11_Reply_service_diagnostics_integration"
COMPLETE_REPLY_DIAGNOSTICS_STEP = COMPLETE_REPLY_DIAGNOSTICS_STAGE
COMPLETE_REPLY_DIAGNOSTICS_IMPLEMENTATION_UNIT = "Commit 11"
RUNTIME_SURFACE_STEP8_DIAGNOSTICS_VERSION = "emlis.runtime_surface_diagnostics_scorecard.v1"
RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP = "Step8_diagnostics_scorecard_update"

_TEXT_PAYLOAD_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
    "material_text",
    "surface_text",
    "realized_text",
    "comment_text",
    "text",
    "phrase",
    "sentence",
    "sentences",
    "line_text",
    "body",
    "reply_text",
    "summary_of_output",
    "matched_raw_quote_fragments",
    "relation_marker_phrase",
    "marker_phrase",
}

_SAFE_META_KEYS = (
    "version",
    "schema_version",
    "service_version",
    "target_step",
    "step",
    "source_step",
    "stage",
    "implementation_unit",
    "status",
    "ready",
    "display_ready",
    "primary_reason",
    "rejection_reasons",
    "blocking_reasons",
    "coverage_group",
    "coverage_scope",
    "composer_model",
    "generation_method",
    "generation_scope",
    "material_service",
    "coverage_plan",
    "relation_graph",
    "sentence_plan",
    "sentence_binding_bundle",
    "surface_realizer",
    "surface_signature",
    "surface_quality_signature",
    "step2_surface_quality_signature",
    "surface_quality_signature_version",
    "step2_surface_quality_signature_ready",
    "surface_signature_id",
    "surface_signature_family_key",
    "surface_template_major",
    "surface_grammar_warning_codes",
    "surface_grammar_warning_count",
    "relation_surface_contract_version",
    "relation_surface_report",
    "strict_relation_trace",
    "relation_signal_source_records",
    "relation_signal_source_priority",
    "selected_relation_signal_source",
    "gate_recovery_synthesized_reader_report",
    "strict_relation_signal_required",
    "required_relation_signal_keys",
    "matched_relation_signal_keys",
    "broad_relation_type_only",
    "broad_relation_type_only_keys",
    "relation_surface_status",
    "relation_surface_missing",
    "relation_surface_missing_after_repair",
    "strict_relation_surface_present_anywhere",
    "reader_relation_signal_detected",
    "reader_relation_signal_count",
    "reader_relation_signal_keys",
    "reader_relation_signal_relation_types",
    "expected_relation_types",
    "surface_recovery_relation_line_aligned",
    "surface_relation_marker_key",
    "surface_relation_marker_keys",
    "relation_marker_key",
    "self_repair_relation_marker_applied",
    "self_repair_relation_marker_key",
    "self_repair_relation_marker_keys",
    "self_repair_relation_marker_count",
    "self_repair_relation_marker_relation_type",
    "self_repair_relation_marker_signal_detected",
    "self_repair_relation_marker_signal_count",
    "self_repair_relation_marker_signal_keys",
    "self_repair_relation_marker_signal_relation_types",
    "self_repair_relation_signal_detected",
    "self_repair_relation_signal_count",
    "self_repair_relation_signal_keys",
    "self_repair_relation_signal_relation_types",
    "self_repair_relation_marker_meaning_added",
    "self_repair_relation_marker_gate_relaxed",
    "tone_engine_version",
    "product_quality_tone_engine_version",
    "tone_policy",
    "tone_policy_contract",
    "tone_policy_applied",
    "tone_guard_report",
    "tone_guard_major_count",
    "tone_guard_passed",
    "tone_guard_reasons",
    "tone_meaning_added",
    "initial_grounding_report",
    "final_grounding_report",
    "grounding_input",
    "complete_grounding_binding",
    "binding_meta",
    "sentence_bindings",
    "self_repair",
    "self_repair_report_v2",
    "product_quality_self_repair",
    "limited_reader_repair",
    "limited_reader_repair_step3",
    "limited_reader_repair_step4",
    "limited_reader_repair_step5",
    "limited_reader_repair_diagnostic",
    "limited_reader_repair_attempted",
    "limited_reader_repair_applied",
    "limited_reader_repair_relation_marker_key",
    "limited_reader_repair_relation_marker_signal_keys",
    "limited_reader_repair_relation_type",
    "repair_trace",
    "repair_trace_v2",
    "complete_composer_candidate",
    "used_evidence_span_ids",
    "used_phrase_unit_ids",
    "used_relation_ids",
    "relation_types",
    "comment_text_present",
    "comment_text_contract",
    "fallback_observation_sentence_added",
    "fixed_string_renderer_used",
    "external_ai_used",
    "local_llm_used",
    "fixed_sentence_template_used",
    "completion_sentence_templates_added",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_title_changed",
    "runtime_surface_source_lock",
    "step1_runtime_surface_source_lock",
    "runtime_surface_source_lock_version",
    "runtime_surface_source_lock_ready",
    "runtime_surface_source_locked",
    "runtime_composer_source",
    "composer_requested",
    "composer_resolved",
    "runtime_composer_model",
    "runtime_surface_source_complete_initial_client_used",
    "runtime_surface_source_limited_reader_repair_applied",
    "sentence_plan_version",
    "surface_realizer_version",
    "tone_policy_version",
    "self_repair_version",
    "surface_quality_signature",
    "step2_surface_quality_signature",
    "surface_quality_signature_version",
    "step2_surface_quality_signature_ready",
    "surface_signature_id",
    "surface_signature_family_key",
    "surface_template_major",
    "surface_grammar_warning_codes",
    "surface_grammar_warning_count",
    "runtime_surface_pre_return_gate",
    "runtime_surface_pre_return_gate_evaluated",
    "runtime_surface_pre_return_gate_passed",
    "runtime_surface_pre_return_gate_action",
    "runtime_surface_pre_return_gate_rejection_reasons",
    "surface_template_major_blocked",
    "malformed_phrase_unit_blocked_count",
    "shallow_surface_realizer_v2",
    "step5_shallow_surface_realizer_v2",
    "shallow_realizer_version",
    "shallow_v2_used",
    "shallow_phrase_unit_guard",
    "step4_shallow_phrase_unit_guard",
    "shallow_phrase_unit_creation_guard",
    "step4_shallow_phrase_unit_creation_guard",
    "low_information_specificity_plan",
    "low_information_specificity_used",
    "safe_anchor_count",
    "uses_safe_anchor",
    "safe_anchor_role",
    "safe_anchor_surface_kind",
    "safe_anchor_evidence_ids",
    "user_fact_promotion_attempt",
    "unsupported_event_assertion_present",
    "step6_low_information_specificity_ready",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
    "raw_input_included",
)

_TEMPLATE_REASON_MARKERS = (
    "template",
    "fixed",
    "raw_echo",
    "over_echo",
    "repeated_sentence_pattern",
    "same_ending",
)
_SAFETY_REASON_MARKERS = (
    "safety",
    "diagnosis",
    "overclaim",
    "personality",
    "advice",
    "action_instruction",
    "medical",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        source: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        source = values
    else:
        source = [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in source:
        item = _clean(value)
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _candidate_attr(candidate: Any, key: str, default: Any = None) -> Any:
    if isinstance(candidate, Mapping) and key in candidate:
        return candidate.get(key, default)
    return getattr(candidate, key, default)


def _candidate_meta(candidate: Any) -> dict[str, Any]:
    meta = _candidate_attr(candidate, "composer_meta", {})
    return dict(meta) if isinstance(meta, Mapping) else {}


def _json_safe(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return None
    if is_dataclass(value):
        return _json_safe(asdict(value), depth=depth + 1)
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _clean(key)
            if not key_text or key_text in _TEXT_PAYLOAD_KEYS:
                continue
            safe_item = _json_safe(item, depth=depth + 1)
            if safe_item is not None:
                out[key_text] = safe_item
        return out
    if isinstance(value, (list, tuple, set)):
        return [item for item in (_json_safe(v, depth=depth + 1) for v in value) if item is not None]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    safe = _json_safe(value)
    return safe if isinstance(safe, dict) else {}


def _safe_subset(meta: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in _SAFE_META_KEYS:
        if key not in meta:
            continue
        safe_item = _json_safe(meta.get(key))
        if safe_item is not None:
            out[key] = safe_item
    return out


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _runtime_surface_invalid_gate_report(reason: str) -> dict[str, Any]:
    """Return a fail-closed Step8-safe gate report for invalid Step1 meta."""

    report = {
        "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "schema_version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "source": "step8.runtime_surface_diagnostics_scorecard",
        "source_step": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP,
        "step": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP,
        "runtime_surface_pre_return_gate_ready": True,
        "runtime_surface_pre_return_gate_contract_ready": True,
        "evaluated": True,
        "passed": False,
        "blocked": True,
        "action": RUNTIME_SURFACE_ACTION_FAIL_CLOSED,
        "rejection_reasons": _dedupe(["runtime_surface_pre_return_gate_invalid", reason]),
        "runtime_surface_pre_return_gate_invalid": True,
        "surface_template_major": False,
        "generic_center_phrase_count": 0,
        "same_connector_run_max": 0,
        "same_connector_repetition_count": 0,
        "grammar_warning_count": 0,
        "malformed_phrase_unit_count": 0,
        "rerender_allowed": False,
        "rerender_attempted": False,
        "rerender_attempt_limit": 1,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    assert_runtime_surface_pre_return_gate_meta_only(report, source="step8.runtime_surface_invalid_gate_report")
    return report


def _validated_runtime_surface_gate_report(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    report = dict(value)
    try:
        assert_runtime_surface_pre_return_gate_meta_only(report, source="step8.runtime_surface_pre_return_gate")
    except Exception as exc:
        return _runtime_surface_invalid_gate_report(str(exc).splitlines()[0][:160])
    return _safe_mapping(report)


def _display_decision_gate_trace(display_decision: Any) -> dict[str, Any]:
    trace = _candidate_attr(display_decision, "gate_trace", {})
    if isinstance(trace, Mapping):
        return dict(trace)
    return {}


def _display_decision_meta(display_decision: Any) -> dict[str, Any]:
    meta = _candidate_attr(display_decision, "meta", {}) or _candidate_attr(display_decision, "display_meta", {})
    if isinstance(meta, Mapping):
        return dict(meta)
    return {}


def _runtime_surface_gate_report_from_sources(
    *,
    gate_trace: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    display_decision: Any = None,
) -> dict[str, Any]:
    trace = dict(gate_trace or {}) if isinstance(gate_trace, Mapping) else {}
    summary = dict(diagnostic_summary or {}) if isinstance(diagnostic_summary, Mapping) else {}
    display_trace = _display_decision_gate_trace(display_decision)
    display_meta = _display_decision_meta(display_decision)
    report = _first_mapping(
        summary.get("runtime_surface_pre_return_gate"),
        trace.get("runtime_surface_pre_return_gate"),
        display_trace.get("runtime_surface_pre_return_gate"),
        display_meta.get("runtime_surface_pre_return_gate"),
    )
    if report:
        return _validated_runtime_surface_gate_report(report)

    display_gate = trace.get("display_gate") if isinstance(trace.get("display_gate"), Mapping) else {}
    if not isinstance(display_gate, Mapping):
        display_gate = {}
    display_trace_gate = display_trace.get("display_gate") if isinstance(display_trace.get("display_gate"), Mapping) else {}
    if isinstance(display_trace_gate, Mapping):
        display_gate = {**dict(display_trace_gate), **dict(display_gate)}

    evaluated = bool(
        summary.get("runtime_surface_pre_return_gate_evaluated")
        or display_gate.get("runtime_surface_pre_return_gate_evaluated")
        or display_meta.get("runtime_surface_pre_return_gate_evaluated")
    )
    if not evaluated:
        return {}

    reasons = _dedupe(
        summary.get("runtime_surface_pre_return_gate_rejection_reasons")
        or display_gate.get("runtime_surface_pre_return_gate_rejection_reasons")
        or display_meta.get("runtime_surface_pre_return_gate_rejection_reasons")
    )
    passed_value = (
        summary.get("runtime_surface_pre_return_gate_passed")
        if "runtime_surface_pre_return_gate_passed" in summary
        else display_gate.get("runtime_surface_pre_return_gate_passed")
        if "runtime_surface_pre_return_gate_passed" in display_gate
        else display_meta.get("runtime_surface_pre_return_gate_passed")
    )
    passed = bool(passed_value)
    action = _clean(
        summary.get("runtime_surface_pre_return_gate_action")
        or display_gate.get("runtime_surface_pre_return_gate_action")
        or display_meta.get("runtime_surface_pre_return_gate_action")
        or (RUNTIME_SURFACE_ACTION_ALLOW if passed and not reasons else RUNTIME_SURFACE_ACTION_BLOCK)
    )
    if action not in {RUNTIME_SURFACE_ACTION_ALLOW, RUNTIME_SURFACE_ACTION_BLOCK, RUNTIME_SURFACE_ACTION_FAIL_CLOSED, "rerender_shallow_v2", "reroute_low_information"}:
        action = RUNTIME_SURFACE_ACTION_FAIL_CLOSED
        reasons = _dedupe([*reasons, "runtime_surface_pre_return_gate_invalid_action"])
        passed = False
    synthetic_report = {
        "version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "schema_version": RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
        "source": "step8.runtime_surface_diagnostics_scorecard",
        "source_step": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP,
        "step": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP,
        "runtime_surface_pre_return_gate_ready": True,
        "runtime_surface_pre_return_gate_contract_ready": True,
        "evaluated": True,
        "passed": passed,
        "blocked": not passed,
        "action": action,
        "rejection_reasons": reasons,
        "surface_template_major": bool(
            summary.get("surface_template_major_blocked")
            or display_gate.get("surface_template_major_blocked")
            or display_meta.get("surface_template_major_blocked")
            or "surface_template_major" in reasons
        ),
        "generic_center_phrase_count": _safe_int(summary.get("generic_center_phrase_count") or display_gate.get("generic_center_phrase_count")),
        "same_connector_run_max": _safe_int(summary.get("same_connector_run_max") or display_gate.get("same_connector_run_max")),
        "same_connector_repetition_count": _safe_int(summary.get("same_connector_repetition_count") or display_gate.get("same_connector_repetition_count")),
        "grammar_warning_count": _safe_int(summary.get("surface_grammar_warning_count") or display_gate.get("surface_grammar_warning_count")),
        "malformed_phrase_unit_count": max(
            _safe_int(summary.get("malformed_phrase_unit_blocked_count")),
            _safe_int(display_gate.get("malformed_phrase_unit_blocked_count")),
            _safe_int(display_meta.get("malformed_phrase_unit_blocked_count")),
        ),
        "rerender_allowed": False,
        "rerender_attempted": False,
        "rerender_attempt_limit": 1,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    return _validated_runtime_surface_gate_report(synthetic_report)

def _shallow_v2_meta_from_runtime(runtime_meta: Mapping[str, Any]) -> dict[str, Any]:
    surface_realizer = runtime_meta.get("surface_realizer") if isinstance(runtime_meta.get("surface_realizer"), Mapping) else {}
    composer_diagnostic = runtime_meta.get("composer_diagnostic") if isinstance(runtime_meta.get("composer_diagnostic"), Mapping) else {}
    return _first_mapping(
        runtime_meta.get("shallow_surface_realizer_v2"),
        runtime_meta.get("step5_shallow_surface_realizer_v2"),
        surface_realizer.get("shallow_surface_realizer_v2") if isinstance(surface_realizer, Mapping) else {},
        surface_realizer.get("step5_shallow_surface_realizer_v2") if isinstance(surface_realizer, Mapping) else {},
        composer_diagnostic.get("shallow_surface_realizer_v2") if isinstance(composer_diagnostic, Mapping) else {},
        composer_diagnostic.get("step5_shallow_surface_realizer_v2") if isinstance(composer_diagnostic, Mapping) else {},
    )


def _low_information_plan_from_runtime(runtime_meta: Mapping[str, Any]) -> dict[str, Any]:
    composer_diagnostic = runtime_meta.get("composer_diagnostic") if isinstance(runtime_meta.get("composer_diagnostic"), Mapping) else {}
    return _first_mapping(
        runtime_meta.get("low_information_specificity_plan"),
        runtime_meta.get("step6_low_information_specificity_plan"),
        composer_diagnostic.get("low_information_specificity_plan") if isinstance(composer_diagnostic, Mapping) else {},
    )


def _bounded_bool(value: Any) -> bool:
    return bool(value) if value is not None else False


def build_runtime_surface_step8_diagnostics_meta(
    *,
    runtime_meta: Mapping[str, Any] | None = None,
    gate_trace: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    surface_quality_signature: Mapping[str, Any] | None = None,
    display_decision: Any = None,
) -> dict[str, Any]:
    """Build Step8 diagnostics/scorecard meta without storing raw input or body text."""

    runtime = dict(runtime_meta or {}) if isinstance(runtime_meta, Mapping) else {}
    summary = dict(diagnostic_summary or {}) if isinstance(diagnostic_summary, Mapping) else {}
    gate_report = _runtime_surface_gate_report_from_sources(
        gate_trace=gate_trace,
        diagnostic_summary=diagnostic_summary,
        display_decision=display_decision,
    )
    gate_reasons = _dedupe(gate_report.get("rejection_reasons")) if gate_report else _dedupe(
        summary.get("runtime_surface_pre_return_gate_rejection_reasons")
    )
    shallow_v2_meta = _safe_mapping(_shallow_v2_meta_from_runtime(runtime))
    shallow_guard_meta = _safe_mapping(_first_mapping(
        runtime.get("shallow_phrase_unit_guard"),
        runtime.get("step4_shallow_phrase_unit_guard"),
        runtime.get("shallow_phrase_unit_creation_guard"),
        runtime.get("step4_shallow_phrase_unit_creation_guard"),
    ))
    low_information_plan = _safe_mapping(_low_information_plan_from_runtime(runtime))
    surface_signature = dict(surface_quality_signature or {}) if isinstance(surface_quality_signature, Mapping) else {}
    if surface_signature:
        assert_surface_quality_signature_meta_only(surface_signature, source="step8.surface_quality_signature")
    if gate_report:
        assert_runtime_surface_pre_return_gate_meta_only(gate_report, source="step8.runtime_surface_gate_report")

    gate_evaluated = bool(gate_report.get("evaluated")) if gate_report else bool(summary.get("runtime_surface_pre_return_gate_evaluated"))
    gate_passed = bool(gate_report.get("passed")) if gate_report else bool(summary.get("runtime_surface_pre_return_gate_passed", True))
    gate_action = _clean(gate_report.get("action") if gate_report else summary.get("runtime_surface_pre_return_gate_action"))
    malformed_blocked_count = max(
        _safe_int(gate_report.get("malformed_phrase_unit_count") if gate_report else 0),
        _safe_int(runtime.get("malformed_phrase_unit_blocked_count")),
        _safe_int(runtime.get("malformed_nominalization_blocked_count")),
        _safe_int(shallow_guard_meta.get("malformed_phrase_unit_blocked_count")),
        _safe_int(shallow_guard_meta.get("malformed_nominalization_blocked_count")),
        _safe_int(shallow_guard_meta.get("blocked_count")),
    )
    shallow_version = _clean(
        runtime.get("shallow_realizer_version")
        or runtime.get("surface_realizer_version")
        or shallow_v2_meta.get("realizer_version")
        or shallow_v2_meta.get("shallow_realizer_version")
        or summary.get("shallow_realizer_version")
    )
    shallow_v2_used = bool(
        runtime.get("shallow_v2_used")
        or runtime.get("step5_shallow_v2_used")
        or shallow_v2_meta.get("shallow_v2_used")
        or shallow_v2_meta.get("eligible")
        or shallow_v2_meta.get("realizer_version") == "shallow_surface_realizer.v2"
        or shallow_version == "shallow_surface_realizer.v2"
    )
    low_information_specificity_used = bool(
        runtime.get("low_information_specificity_used")
        or runtime.get("step6_low_information_specificity_used")
        or low_information_plan.get("uses_safe_anchor")
        or low_information_plan.get("safe_anchor_count")
        or summary.get("low_information_specificity_used")
    )
    safe_anchor_count = max(
        _safe_int(runtime.get("safe_anchor_count")),
        _safe_int(summary.get("safe_anchor_count")),
        _safe_int(low_information_plan.get("safe_anchor_count")),
    )
    uses_safe_anchor = bool(runtime.get("uses_safe_anchor") or summary.get("uses_safe_anchor") or low_information_plan.get("uses_safe_anchor") or safe_anchor_count > 0)
    safe_anchor_role = _clean(runtime.get("safe_anchor_role") or summary.get("safe_anchor_role") or low_information_plan.get("safe_anchor_role"))
    safe_anchor_surface_kind = _clean(runtime.get("safe_anchor_surface_kind") or summary.get("safe_anchor_surface_kind") or low_information_plan.get("safe_anchor_surface_kind"))
    safe_anchor_evidence_ids = _dedupe(runtime.get("safe_anchor_evidence_ids") or summary.get("safe_anchor_evidence_ids") or low_information_plan.get("safe_anchor_evidence_ids") or [])

    gate_surface_template_major = bool(gate_report.get("surface_template_major")) if gate_report else bool(summary.get("surface_template_major_blocked"))
    signature_template_major = bool(surface_signature.get("surface_template_major") or surface_signature.get("template_major"))
    surface_template_major_blocked = bool(
        (gate_evaluated and not gate_passed and (gate_surface_template_major or signature_template_major))
        or "surface_template_major" in gate_reasons
        or "generic_center_phrase" in gate_reasons
        or "same_connector_run" in gate_reasons
        or "surface_template_skeleton" in gate_reasons
    )
    step6_ready = bool(
        runtime.get("step6_low_information_specificity_ready")
        or runtime.get("low_information_specificity_ready")
        or low_information_plan.get("version")
        or low_information_specificity_used
        or summary.get("step6_low_information_specificity_ready")
    )
    result = {
        "version": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_VERSION,
        "target_step": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP,
        "step": RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP,
        "ready": True,
        "step8_runtime_surface_diagnostics_ready": True,
        "runtime_surface_step8_diagnostics_ready": True,
        "diagnostics_scorecard_update_ready": True,
        "runtime_surface_diagnostics_scorecard_updated": True,
        "runtime_surface_pre_return_gate_scorecard_connected": bool(gate_report or gate_evaluated),
        "runtime_surface_pre_return_gate": dict(gate_report) if gate_report else {},
        "runtime_surface_pre_return_gate_evaluated": gate_evaluated,
        "runtime_surface_pre_return_gate_passed": gate_passed,
        "runtime_surface_pre_return_gate_final_passed": gate_passed,
        "runtime_surface_pre_return_gate_action": gate_action,
        "runtime_surface_pre_return_gate_rejection_reasons": gate_reasons,
        "surface_template_major_blocked": surface_template_major_blocked,
        "surface_template_major": signature_template_major or gate_surface_template_major,
        "surface_grammar_warning_count": _safe_int(
            surface_signature.get("surface_grammar_warning_count")
            or surface_signature.get("grammar_warning_count")
            or (gate_report.get("grammar_warning_count") if gate_report else 0)
        ),
        "malformed_phrase_unit_blocked_count": malformed_blocked_count,
        "shallow_surface_realizer_v2": shallow_v2_meta,
        "step5_shallow_surface_realizer_v2": shallow_v2_meta,
        "shallow_realizer_version": shallow_version,
        "shallow_v2_used": shallow_v2_used,
        "shallow_phrase_unit_guard": shallow_guard_meta,
        "step4_shallow_phrase_unit_guard": shallow_guard_meta,
        "low_information_specificity_plan": low_information_plan,
        "low_information_specificity_used": low_information_specificity_used,
        "step6_low_information_specificity_ready": step6_ready,
        "low_information_safe_anchor_count": safe_anchor_count,
        "safe_anchor_count": safe_anchor_count,
        "uses_safe_anchor": uses_safe_anchor,
        "safe_anchor_role": safe_anchor_role,
        "safe_anchor_surface_kind": safe_anchor_surface_kind,
        "safe_anchor_evidence_ids": safe_anchor_evidence_ids,
        "unsupported_event_assertion_present": bool(
            runtime.get("unsupported_event_assertion_present")
            or low_information_plan.get("unsupported_event_assertion_present")
            or summary.get("unsupported_event_assertion_present")
        ),
        "user_fact_promotion_attempt": bool(
            runtime.get("user_fact_promotion_attempt")
            or low_information_plan.get("user_fact_promotion_attempt")
            or summary.get("user_fact_promotion_attempt")
        ),
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
    }
    # Contract check the nested Step1 report if present, then return a whitelisted,
    # JSON-safe object.  This keeps Step8 diagnostics meta-only even when upstream
    # sources carry accidental text fields.
    if result["runtime_surface_pre_return_gate"]:
        assert_runtime_surface_pre_return_gate_meta_only(
            result["runtime_surface_pre_return_gate"],
            source="step8.runtime_surface_pre_return_gate_nested",
        )
    return _safe_mapping(result)

def _is_complete_candidate(candidate: Any) -> bool:
    if candidate is None:
        return False
    meta = _candidate_meta(candidate)
    model = _clean(_candidate_attr(candidate, "composer_model", "") or meta.get("composer_model"))
    method = _clean(_candidate_attr(candidate, "generation_method", "") or meta.get("generation_method"))
    return bool(
        model == COMPLETE_COMPOSER_INITIAL_MODEL
        or method == COMPLETE_COMPOSER_GENERATION_METHOD
        or meta.get("complete_composer_client_added") is True
    )


def extract_complete_composer_runtime_meta(candidate: Any) -> dict[str, Any]:
    """Return sanitized Complete Composer meta without raw user text."""

    meta = _candidate_meta(candidate)
    if not _is_complete_candidate(candidate) and not meta:
        return {}
    subset = _safe_subset(meta)
    subset.setdefault("version", "emlis.complete_runtime_meta.v1")
    subset.setdefault("target_step", COMPLETE_REPLY_DIAGNOSTICS_STAGE)
    subset.setdefault("composer_model", _clean(_candidate_attr(candidate, "composer_model", "") or meta.get("composer_model")))
    subset.setdefault("generation_method", _clean(_candidate_attr(candidate, "generation_method", "") or meta.get("generation_method")))
    subset.setdefault("generation_scope", _clean(_candidate_attr(candidate, "generation_scope", "") or meta.get("generation_scope")))
    subset.setdefault("coverage_scope", _clean(_candidate_attr(candidate, "coverage_scope", "") or meta.get("coverage_scope") or meta.get("coverage_group")))
    subset["raw_input_included"] = False
    subset["comment_text_included"] = False
    return subset


def _binding_count_from_meta(meta: Mapping[str, Any]) -> int:
    for key in ("grounding_input", "complete_grounding_binding", "binding_meta", "sentence_binding_bundle"):
        item = meta.get(key)
        if isinstance(item, Mapping):
            count = _safe_int(item.get("binding_count") or item.get("sentence_binding_count"), 0)
            if count:
                return count
            rows = item.get("sentence_bindings") or item.get("bindings") or item.get("items") or item.get("surface_lines")
            if isinstance(rows, (list, tuple, set)):
                return len(rows)
    rows = meta.get("sentence_bindings")
    if isinstance(rows, (list, tuple, set)):
        return len(rows)
    return 0


def _final_grounding_report_from_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    item = meta.get("final_grounding_report")
    if isinstance(item, Mapping):
        return item
    for key in ("grounding_report", "initial_grounding_report"):
        item = meta.get(key)
        if isinstance(item, Mapping):
            return item
    return {}


def _product_quality_grounding_report_from_meta(report: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("product_quality_grounding_report", "grounding_report_v2"):
        item = report.get(key)
        if isinstance(item, Mapping):
            return item
    diagnostics = report.get("binding_diagnostics")
    if isinstance(diagnostics, Mapping):
        item = diagnostics.get("grounding_report_v2") or diagnostics.get("product_quality_grounding_report")
        if isinstance(item, Mapping):
            return item
    return {}


def _surface_variation_report_from_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    """Read Step3 surface-variation diagnostics from sanitized Complete meta."""

    for key in ("surface_variation_report", "surface_variation_profile"):
        item = meta.get(key)
        if isinstance(item, Mapping):
            return item
    surface = meta.get("surface_realizer")
    if isinstance(surface, Mapping):
        for key in ("surface_variation_report", "surface_variation_profile"):
            item = surface.get(key)
            if isinstance(item, Mapping):
                return item
    signature = meta.get("surface_signature")
    if isinstance(signature, Mapping):
        for key in ("surface_variation_report", "surface_variation_profile"):
            item = signature.get(key)
            if isinstance(item, Mapping):
                return item
        return signature
    return {}



def _tone_guard_report_from_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    """Read Step5 Tone Engine diagnostics from sanitized Complete meta."""

    for key in ("tone_engine_2_1_report", "step9_tone_engine_2_1_report", "tone_guard_report"):
        item = meta.get(key)
        if isinstance(item, Mapping):
            return item
    surface = meta.get("surface_realizer")
    if isinstance(surface, Mapping):
        for key in ("tone_engine_2_1_report", "step9_tone_engine_2_1_report", "tone_guard_report"):
            item = surface.get(key)
            if isinstance(item, Mapping):
                return item
    signature = meta.get("surface_signature")
    if isinstance(signature, Mapping):
        for key in ("tone_engine_2_1_report", "step9_tone_engine_2_1_report", "tone_guard_report"):
            item = signature.get(key)
            if isinstance(item, Mapping):
                return item
    tone_policy = meta.get("tone_policy")
    if isinstance(tone_policy, Mapping):
        return {
            "tone_policy_version": tone_policy.get("version"),
            "tone_guard_major_count": 0,
            "tone_guard_reasons": [],
            "passed": True,
            "release_blocker": False,
            "raw_input_included": False,
        }
    return {}

def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _gate_primary_reason(gate_trace: Mapping[str, Any] | None, display_decision: Any) -> str:
    display = gate_trace.get("display_gate") if isinstance(gate_trace, Mapping) else {}
    if isinstance(display, Mapping):
        reason = _clean(display.get("primary_reason") or "")
        if reason:
            return reason
        reasons = _dedupe(display.get("rejection_reasons") or [])
        if reasons:
            return reasons[0]
    reasons = _dedupe(_candidate_attr(display_decision, "rejection_reasons", []))
    return reasons[0] if reasons else ("passed" if _clean(_candidate_attr(display_decision, "observation_status", "")) == "passed" else "")


def _count_reason_markers(reasons: Iterable[str], markers: tuple[str, ...]) -> int:
    count = 0
    for reason in reasons:
        lowered = reason.lower()
        if any(marker in lowered for marker in markers):
            count += 1
    return count


def _repair_succeeded(self_repair: Mapping[str, Any], repair_trace: list[Any], display_passed: bool) -> bool:
    if not repair_trace and not self_repair:
        return False
    if display_passed:
        return True
    result = _clean(self_repair.get("result") or self_repair.get("status") or self_repair.get("final_status"))
    return result in {"passed", "repaired", "generated"} or bool(self_repair.get("repaired"))


def _trace_meta_row(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return _safe_mapping(value)
    if hasattr(value, "as_meta"):
        try:
            meta = value.as_meta()
            if isinstance(meta, Mapping):
                return _safe_mapping(meta)
        except Exception:
            return {}
    return {}


def _repair_trace_v2_summary(repair_trace: list[Any], self_repair: Mapping[str, Any]) -> dict[str, Any]:
    rows = [_trace_meta_row(row) for row in repair_trace]
    if not rows and isinstance(self_repair, Mapping):
        rows = [_trace_meta_row(row) for row in _as_list(self_repair.get("repair_trace_v2") or self_repair.get("repair_trace"))]
    rows = [row for row in rows if row]
    operation_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    result_counts: dict[str, int] = {}
    abort_reasons: list[str] = []
    source_gates: list[str] = []
    meaning_added_count = 0
    policy_violation_count = 0
    for row in rows:
        operation = _clean(row.get("operation") or row.get("applied_operation"))
        reason = _clean(row.get("reason_code"))
        result = _clean(row.get("result"))
        if operation:
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
        if reason:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if result:
            result_counts[result] = result_counts.get(result, 0) + 1
        if row.get("abort_reason"):
            abort_reasons.append(str(row.get("abort_reason")))
        if row.get("source_gate"):
            source_gates.append(str(row.get("source_gate")))
        meaning_added = bool(row.get("meaning_added") or row.get("new_meaning_added"))
        meaning_added_count += 1 if meaning_added else 0
        evidence_ok = bool(row.get("evidence_ids_preserved", row.get("evidence_ids_unchanged", True)))
        relation_ok = bool(row.get("relation_ids_preserved", row.get("relation_ids_unchanged", True)))
        if meaning_added or not evidence_ok or not relation_ok or bool(row.get("gate_relaxed")):
            policy_violation_count += 1
    return {
        "repair_trace_contract_version": "emlis.complete_repair_trace.v2",
        "repair_trace_v2_count": len(rows),
        "repair_passed_count": result_counts.get("passed", 0),
        "repair_failed_count": result_counts.get("failed", 0),
        "repair_aborted_count": result_counts.get("aborted", 0),
        "repair_meaning_added_count": meaning_added_count,
        "repair_policy_violation_count": policy_violation_count,
        "repair_operation_counts": operation_counts,
        "repair_reason_counts": reason_counts,
        "repair_result_counts": result_counts,
        "repair_abort_reasons": _dedupe(abort_reasons),
        "repair_source_gates": _dedupe(source_gates),
        "repair_trace_v2_ready": bool(rows),
        "meaning_added": meaning_added_count > 0,
        "raw_input_included": False,
    }



RELATION_DIAGNOSTIC_VERSION = "emlis.positive_recovery_relation_diagnostic.v1"
RELATION_DIAGNOSTIC_STEP = "Step5_diagnostic_connection"
LIMITED_READER_REPAIR_DIAGNOSTIC_VERSION = "emlis.limited_reader_repair_diagnostic.v1"


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _bool_from_sources(sources: Iterable[Mapping[str, Any]], *keys: str) -> bool:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in keys:
            if key in source:
                return bool(source.get(key))
    return False


def _int_from_sources(sources: Iterable[Mapping[str, Any]], *keys: str) -> int:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in keys:
            if key in source and source.get(key) is not None:
                return _safe_int(source.get(key), 0)
    return 0


def _list_from_sources(sources: Iterable[Mapping[str, Any]], *keys: str) -> list[str]:
    values: list[Any] = []
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in keys:
            if key not in source:
                continue
            item = source.get(key)
            if isinstance(item, Mapping):
                continue
            if isinstance(item, (list, tuple, set)):
                values.extend(item)
            elif item is not None and not isinstance(item, bool):
                values.append(item)
    return _dedupe(values)


def _first_from_sources(sources: Iterable[Mapping[str, Any]], *keys: str) -> str:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in keys:
            item = _clean(source.get(key))
            if item:
                return item
    return ""


RELATION_SIGNAL_SOURCE_PRIORITY = (
    "reader_gate",
    "runtime_surface_report",
    "self_repair_report",
    "limited_reader_repair_report",
    "gate_recovery_synthesized_report",
)


def _relation_signal_keys_from_sources(sources: Iterable[Mapping[str, Any]]) -> list[str]:
    return _list_from_sources(
        sources,
        "reader_relation_signal_keys",
        "self_repair_relation_marker_signal_keys",
        "self_repair_relation_signal_keys",
        "relation_marker_signal_keys",
        "keys",
    )


def _relation_source_record(
    *,
    source: str,
    sources: Iterable[Mapping[str, Any]],
    expected_relation_types: Iterable[Any] | Any,
) -> dict[str, Any]:
    source_list = [item for item in sources if isinstance(item, Mapping)]
    signal_keys = _relation_signal_keys_from_sources(source_list)
    relation_types = _list_from_sources(
        source_list,
        "reader_relation_signal_relation_types",
        "self_repair_relation_marker_signal_relation_types",
        "self_repair_relation_signal_relation_types",
        "relation_marker_signal_relation_types",
        "relation_types",
    )
    marker_keys = _list_from_sources(
        source_list,
        "self_repair_relation_marker_keys",
        "self_repair_relation_marker_key",
        "surface_relation_marker_keys",
        "surface_relation_marker_key",
        "relation_marker_key",
    )
    status = relation_surface_status_for_reader(
        expected_relation_types=expected_relation_types,
        detected_signal_keys=signal_keys,
    )
    return {
        "source": source,
        "signal_keys": list(signal_keys),
        "relation_types": list(relation_types),
        "marker_keys": list(marker_keys),
        "strict_relation_signal_required": bool(status.get("strict_relation_signal_required")),
        "matched_relation_signal_keys": list(status.get("matched_relation_signal_keys") or []),
        "broad_relation_type_only": bool(status.get("broad_relation_type_only")),
        "relation_surface_status": _clean(status.get("relation_surface_status")),
        "relation_surface_missing": bool(status.get("relation_surface_missing")),
        "raw_input_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _relation_source_records(
    *,
    reader_sources: Iterable[Mapping[str, Any]],
    runtime_sources: Iterable[Mapping[str, Any]],
    limited_reader_repair_diagnostic: Mapping[str, Any],
    expected_relation_types: Iterable[Any] | Any,
) -> list[dict[str, Any]]:
    self_repair_sources = [
        source
        for source in runtime_sources
        if isinstance(source, Mapping)
        and (
            source.get("self_repair_relation_marker_signal_keys") is not None
            or source.get("self_repair_relation_signal_keys") is not None
            or source.get("self_repair_relation_marker_applied") is not None
        )
    ]
    limited_sources = [limited_reader_repair_diagnostic] if isinstance(limited_reader_repair_diagnostic, Mapping) else []
    return [
        _relation_source_record(
            source="reader_gate",
            sources=reader_sources,
            expected_relation_types=expected_relation_types,
        ),
        _relation_source_record(
            source="runtime_surface_report",
            sources=runtime_sources,
            expected_relation_types=expected_relation_types,
        ),
        _relation_source_record(
            source="self_repair_report",
            sources=self_repair_sources,
            expected_relation_types=expected_relation_types,
        ),
        _relation_source_record(
            source="limited_reader_repair_report",
            sources=limited_sources,
            expected_relation_types=expected_relation_types,
        ),
    ]


def _gate_recovery_synthesized_reader_report(
    *,
    reader_gate: Mapping[str, Any],
    relation_surface_contract_version: str,
) -> bool:
    meta = reader_gate.get("reader_relation_signal_meta") if isinstance(reader_gate, Mapping) else {}
    source_phase = _clean(meta.get("source_phase")) if isinstance(meta, Mapping) else ""
    contract_version = _clean(relation_surface_contract_version)
    return bool(
        "gate_recovery" in source_phase
        or "public_observation_recovery" in contract_version
        or "phase20_5" in contract_version
        or "phase20_6" in contract_version
        or "phase20_7" in contract_version
        or "phase20_8" in contract_version
    )


def _selected_relation_signal_source(records: Iterable[Mapping[str, Any]]) -> str:
    by_source = {str(record.get("source") or ""): record for record in records if isinstance(record, Mapping)}
    for source in RELATION_SIGNAL_SOURCE_PRIORITY:
        record = by_source.get(source)
        if record and record.get("signal_keys"):
            return source
    return "none"


def _build_strict_relation_trace(
    *,
    expected_relation_types: Iterable[Any] | Any,
    reader_signal_keys: Iterable[Any] | Any,
    reader_signal_relation_types: Iterable[Any] | Any,
    marker_signal_keys: Iterable[Any] | Any,
    marker_keys: Iterable[Any] | Any,
    source_records: Iterable[Mapping[str, Any]],
    selected_relation_signal_source: str,
    gate_recovery_synthesized_reader_report: bool,
) -> dict[str, Any]:
    reader_status = relation_surface_status_for_reader(
        expected_relation_types=expected_relation_types,
        detected_signal_keys=reader_signal_keys,
    )
    marker_status = relation_surface_status_for_reader(
        expected_relation_types=expected_relation_types,
        detected_signal_keys=marker_signal_keys,
    )
    records = [dict(record) for record in source_records if isinstance(record, Mapping)]
    strict_present_anywhere = any(record.get("matched_relation_signal_keys") for record in records)
    relation_surface_missing_after_repair = bool(
        reader_status.get("strict_relation_signal_required")
        and not strict_present_anywhere
    )
    return {
        "schema_version": "cocolon.emlis.positive_recovery.strict_relation_trace.v1",
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "relation_signal_source_priority": list(RELATION_SIGNAL_SOURCE_PRIORITY),
        "selected_relation_signal_source": selected_relation_signal_source,
        "gate_recovery_synthesized_reader_report": bool(gate_recovery_synthesized_reader_report),
        "strict_relation_signal_required": bool(reader_status.get("strict_relation_signal_required")),
        "expected_relation_types": list(reader_status.get("expected_relation_types") or []),
        "required_relation_signal_keys": list(reader_status.get("required_relation_signal_keys") or []),
        "reader_relation_signal_keys": list(_dedupe(reader_signal_keys)),
        "reader_relation_signal_relation_types": list(_dedupe(reader_signal_relation_types)),
        "matched_relation_signal_keys": list(reader_status.get("matched_relation_signal_keys") or []),
        "broad_relation_type_only_keys": list(reader_status.get("broad_relation_type_only_keys") or []),
        "broad_relation_type_only": bool(reader_status.get("broad_relation_type_only")),
        "relation_surface_status": _clean(reader_status.get("relation_surface_status")),
        "relation_surface_missing": bool(reader_status.get("relation_surface_missing")),
        "self_repair_relation_marker_signal_keys": list(_dedupe(marker_signal_keys)),
        "self_repair_relation_marker_keys": list(_dedupe(marker_keys)),
        "self_repair_matched_relation_signal_keys": list(marker_status.get("matched_relation_signal_keys") or []),
        "strict_relation_surface_present_anywhere": bool(strict_present_anywhere),
        "relation_surface_missing_after_repair": relation_surface_missing_after_repair,
        "relation_signal_source_records": records,
        "raw_input_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


def _strict_relation_fail_closed_diagnostic(
    *,
    strict_relation_trace: Mapping[str, Any],
    gate_trace: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build R4 Positive Recovery fail-closed diagnostic without text bodies.

    The diagnostic mirrors the runtime fail-closed boundary used by Gate
    Recovery, but remains diagnostic-only.  It keeps relation type
    (``recovery``) separate from concrete relation signal keys
    (``recovery_load_bridge`` family), and it never carries raw input,
    candidate text, or public comment bodies.
    """

    trace = dict(strict_relation_trace or {})
    display_gate = {}
    if isinstance(gate_trace, Mapping) and isinstance(gate_trace.get("display_gate"), Mapping):
        display_gate = dict(gate_trace.get("display_gate") or {})
    display_reasons = _dedupe(display_gate.get("rejection_reasons") or [])
    expected_relation_types = _dedupe(trace.get("expected_relation_types") or [])
    strict_required = bool(trace.get("strict_relation_signal_required"))
    missing_after_repair = bool(
        trace.get("relation_surface_missing_after_repair")
        or (strict_required and trace.get("relation_surface_missing"))
    )
    triggered = bool(strict_required and missing_after_repair)
    strict_relation_type = (
        "recovery"
        if "recovery" in expected_relation_types
        else (expected_relation_types[0] if expected_relation_types else "")
    )
    final_observation_status = _clean(display_gate.get("observation_status"))
    if not final_observation_status:
        if triggered:
            final_observation_status = "rejected"
        elif display_gate.get("passed") is True:
            final_observation_status = "passed"
    final_primary_reason = (
        "relation_not_expressed"
        if triggered
        else (
            "passed"
            if final_observation_status == "passed"
            else (_dedupe(display_reasons) or [final_observation_status or ""])[0]
        )
    )
    blocked_reasons = (
        ["strict_relation_surface_missing_after_repair", "relation_not_expressed"]
        if triggered
        else []
    )
    relation_not_expressed_retained = bool(
        triggered
        or "relation_not_expressed" in display_reasons
        or final_primary_reason == "relation_not_expressed"
    )
    return {
        "schema_version": "cocolon.emlis.strict_relation_fail_closed.v1",
        "source_phase": "Step5_positive_recovery_strict_relation_fail_closed",
        "strict_relation_fail_closed_evaluated": bool(strict_required),
        "strict_relation_fail_closed_triggered": bool(triggered),
        "strict_relation_fail_closed_applied": bool(triggered),
        "strict_relation_type": strict_relation_type,
        "expected_relation_types": list(expected_relation_types),
        "repair_attempt_count": 1 if strict_required else 0,
        "strict_relation_surface_present_after_repair": bool(
            strict_required and not missing_after_repair and trace.get("strict_relation_surface_present_anywhere")
        ),
        "strict_relation_surface_missing_after_repair": bool(missing_after_repair),
        "fallback_public_recovery_attempted": bool(trace.get("gate_recovery_synthesized_reader_report")),
        "fallback_public_recovery_allowed_for_this_candidate": bool(strict_required and not missing_after_repair),
        "final_observation_status": final_observation_status,
        "final_primary_reason": final_primary_reason,
        "comment_text_allowed": bool(display_gate.get("comment_text_allowed")) if display_gate else False,
        "display_gate_passed": bool(display_gate.get("passed")) if display_gate else False,
        "display_gate_rejection_reasons": list(display_reasons),
        "relation_not_expressed_preserved": bool(relation_not_expressed_retained),
        "relation_not_expressed_retained": bool(relation_not_expressed_retained),
        "blocked_reasons": list(blocked_reasons),
        "raw_input_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


_LIMITED_READER_REPAIR_SOURCE_KEYS = (
    "limited_reader_repair",
    "limited_reader_repair_step3",
    "limited_reader_repair_step4",
    "limited_reader_repair_step5",
)

_LIMITED_READER_REPAIR_SAFE_KEYS = (
    "version",
    "target_step",
    "attempted",
    "applied",
    "previous_rejection_reasons",
    "reader_rejection_reasons",
    "repair_required_reasons",
    "requires_limited_reader_repair",
    "addressee_repair_required",
    "relation_surface_repair_required",
    "addressee_repaired",
    "relation_surface_repaired",
    "addressee_repair_step",
    "relation_surface_repair_step",
    "relation_type",
    "relation_marker_key",
    "relation_marker_signal_detected",
    "relation_marker_signal_keys",
    "relation_marker_signal_relation_types",
    "relation_surface_contract_version",
    "operations",
    "pending_operations",
    "reason_source",
    "comment_text_changed",
    "meaning_added",
    "gate_relaxed",
    "raw_input_included",
    "complete_client_self_repair_touched",
    "coverage_scope",
    "profile_key",
)


def _limited_reader_repair_sources(runtime_meta: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return limited/A1 reader-repair meta sources without raw text."""

    sources: list[Mapping[str, Any]] = []
    if not isinstance(runtime_meta, Mapping):
        return sources
    for key in _LIMITED_READER_REPAIR_SOURCE_KEYS:
        item = runtime_meta.get(key)
        if isinstance(item, Mapping):
            sources.append(item)
    diagnostic = runtime_meta.get("composer_diagnostic")
    if isinstance(diagnostic, Mapping):
        item = diagnostic.get("limited_reader_repair")
        if isinstance(item, Mapping):
            sources.append(item)
    return sources


def _safe_limited_reader_repair_meta(runtime_meta: Mapping[str, Any]) -> dict[str, Any]:
    """Extract whitelisted limited repair meta for diagnostics only.

    The adapter meta is useful for diagnosing Reader repair, but the structured
    diagnostic must never include comment text, raw input, or marker phrases.
    """

    merged: dict[str, Any] = {}
    for source in _limited_reader_repair_sources(runtime_meta):
        merged.update(dict(source))
    if not merged:
        return {}

    safe: dict[str, Any] = {}
    for key in _LIMITED_READER_REPAIR_SAFE_KEYS:
        if key not in merged:
            continue
        safe_item = _json_safe(merged.get(key))
        if safe_item is not None:
            safe[key] = safe_item
    safe.setdefault("version", "limited_reader_repair.v1")
    safe["attempted"] = bool(safe.get("attempted"))
    safe["applied"] = bool(safe.get("applied"))
    safe["meaning_added"] = bool(safe.get("meaning_added"))
    safe["gate_relaxed"] = bool(safe.get("gate_relaxed"))
    safe["raw_input_included"] = False
    safe["comment_text_included"] = False
    return safe


def _build_limited_reader_repair_diagnostic(runtime_meta: Mapping[str, Any]) -> dict[str, Any]:
    repair_meta = _safe_limited_reader_repair_meta(runtime_meta)
    if not repair_meta:
        return {}

    relation_marker_key = _clean(repair_meta.get("relation_marker_key"))
    relation_marker_signal_keys = _dedupe(repair_meta.get("relation_marker_signal_keys"))
    relation_marker_signal_relation_types = _dedupe(
        repair_meta.get("relation_marker_signal_relation_types") or repair_meta.get("relation_type")
    )
    relation_type = _clean(repair_meta.get("relation_type"))
    if relation_type and relation_type not in relation_marker_signal_relation_types:
        relation_marker_signal_relation_types.insert(0, relation_type)

    return {
        "version": LIMITED_READER_REPAIR_DIAGNOSTIC_VERSION,
        "target_step": "Step7_limited_reader_repair_diagnostic_meta",
        "diagnostic_connected": True,
        "attempted": bool(repair_meta.get("attempted")),
        "applied": bool(repair_meta.get("applied")),
        "requires_limited_reader_repair": bool(repair_meta.get("requires_limited_reader_repair")),
        "previous_rejection_reasons": _dedupe(repair_meta.get("previous_rejection_reasons")),
        "reader_rejection_reasons": _dedupe(repair_meta.get("reader_rejection_reasons")),
        "operations": _dedupe(repair_meta.get("operations")),
        "pending_operations": _dedupe(repair_meta.get("pending_operations")),
        "addressee_repaired": bool(repair_meta.get("addressee_repaired")),
        "relation_surface_repaired": bool(repair_meta.get("relation_surface_repaired")),
        "relation_marker_key": relation_marker_key,
        "relation_marker_signal_detected": bool(repair_meta.get("relation_marker_signal_detected")) or bool(relation_marker_signal_keys),
        "relation_marker_signal_keys": list(relation_marker_signal_keys),
        "relation_marker_signal_relation_types": list(relation_marker_signal_relation_types),
        "relation_type": relation_type,
        "relation_surface_contract_version": _clean(repair_meta.get("relation_surface_contract_version")),
        "comment_text_changed": bool(repair_meta.get("comment_text_changed")),
        "meaning_added": bool(repair_meta.get("meaning_added")),
        "gate_relaxed": bool(repair_meta.get("gate_relaxed")),
        "complete_client_self_repair_touched": bool(repair_meta.get("complete_client_self_repair_touched")),
        "limited_reader_repair": repair_meta,
        "raw_input_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


def _relation_report_sources(runtime_meta: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    sources: list[Mapping[str, Any]] = [_mapping_or_empty(runtime_meta)]
    sources.extend(_limited_reader_repair_sources(runtime_meta))
    for key in ("surface_realizer", "surface_signature", "grounding_input", "complete_grounding_binding", "binding_meta"):
        item = runtime_meta.get(key)
        if isinstance(item, Mapping):
            sources.append(item)
            nested = item.get("relation_surface_report")
            if isinstance(nested, Mapping):
                sources.append(nested)
    for key in ("self_repair", "self_repair_report_v2", "product_quality_self_repair"):
        item = runtime_meta.get(key)
        if isinstance(item, Mapping):
            sources.append(item)
            for nested_key in (
                "self_repair_relation_signal",
                "self_repair_relation_marker_signal",
                "relation_marker_signal",
                "relation_surface_report",
            ):
                nested = item.get(nested_key)
                if isinstance(nested, Mapping):
                    sources.append(nested)
    for key in ("repair_trace_v2", "repair_trace", "complete_repair_trace"):
        rows = runtime_meta.get(key)
        if isinstance(rows, (list, tuple, set)):
            for row in rows:
                if isinstance(row, Mapping):
                    sources.append(row)
                    for nested_key in (
                        "self_repair_relation_signal",
                        "self_repair_relation_marker_signal",
                        "relation_marker_signal",
                    ):
                        nested = row.get(nested_key)
                        if isinstance(nested, Mapping):
                            sources.append(nested)
    return sources


def _reader_gate_sources(gate_trace: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    reader_gate = gate_trace.get("reader") if isinstance(gate_trace, Mapping) else {}
    sources: list[Mapping[str, Any]] = []
    if isinstance(reader_gate, Mapping):
        sources.append(reader_gate)
        for key in ("diagnostics", "reader_relation_signal_meta"):
            nested = reader_gate.get(key)
            if isinstance(nested, Mapping):
                sources.append(nested)
    return sources


def build_positive_recovery_relation_diagnostic(
    *,
    composer_candidate: Any = None,
    gate_trace: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Step5 relation-surface diagnostic meta without raw input text.

    The output is additive and diagnostic-only. It does not change Reader,
    Display, or public ``input_feedback.comment_text`` behavior.
    """

    runtime_meta = extract_complete_composer_runtime_meta(composer_candidate)
    limited_reader_repair_diagnostic = _build_limited_reader_repair_diagnostic(runtime_meta)
    reader_sources = _reader_gate_sources(gate_trace)
    runtime_sources = _relation_report_sources(runtime_meta)
    all_sources = [*reader_sources, *runtime_sources]
    reader_signal_detected = _bool_from_sources(
        reader_sources,
        "reader_relation_signal_detected",
        "detected",
    )
    reader_signal_count = _int_from_sources(
        reader_sources,
        "reader_relation_signal_count",
        "count",
    )
    reader_signal_keys = _list_from_sources(
        reader_sources,
        "reader_relation_signal_keys",
        "keys",
        "recovery_relation_signal_keys",
        "generic_relation_signal_keys",
    )
    reader_signal_relation_types = _list_from_sources(
        reader_sources,
        "reader_relation_signal_relation_types",
        "relation_types",
    )
    if not reader_signal_detected:
        # In some service-only tests the Reader gate is not built; fall back to
        # generated surface/self-repair meta while keeping the source visible.
        reader_signal_detected = _bool_from_sources(runtime_sources, "reader_relation_signal_detected", "detected")
        reader_signal_count = _int_from_sources(runtime_sources, "reader_relation_signal_count", "count")
        reader_signal_keys = _list_from_sources(runtime_sources, "reader_relation_signal_keys", "keys")
        reader_signal_relation_types = _list_from_sources(runtime_sources, "reader_relation_signal_relation_types", "relation_types")

    marker_keys = _list_from_sources(
        runtime_sources,
        "self_repair_relation_marker_keys",
        "self_repair_relation_marker_key",
        "surface_relation_marker_keys",
        "surface_relation_marker_key",
        "relation_marker_key",
    )
    marker_signal_keys = _list_from_sources(
        runtime_sources,
        "self_repair_relation_marker_signal_keys",
        "self_repair_relation_signal_keys",
        "reader_relation_signal_keys",
        "keys",
    )
    marker_relation_types = _list_from_sources(
        runtime_sources,
        "self_repair_relation_marker_signal_relation_types",
        "self_repair_relation_signal_relation_types",
        "reader_relation_signal_relation_types",
        "relation_types",
    )
    marker_applied = bool(
        _bool_from_sources(runtime_sources, "self_repair_relation_marker_applied")
        or bool(marker_keys)
    )
    marker_count = _int_from_sources(runtime_sources, "self_repair_relation_marker_count")
    if marker_applied and marker_count <= 0:
        marker_count = len(marker_keys) or 1

    reader_gate = gate_trace.get("reader") if isinstance(gate_trace, Mapping) else {}
    reader_rejection_reasons = _dedupe(reader_gate.get("rejection_reasons") if isinstance(reader_gate, Mapping) else [])
    expected_relation_types = _list_from_sources(
        all_sources,
        "expected_relation_types",
        "reader_relation_signal_relation_types",
        "relation_types",
    )
    if not expected_relation_types:
        expected_relation_types = _dedupe(runtime_meta.get("relation_types") or runtime_meta.get("used_relation_ids") or [])

    relation_surface_contract_version = (
        _first_from_sources(all_sources, "relation_surface_contract_version", "contract_version")
        or RELATION_SURFACE_CONTRACT_VERSION
    )
    surface_marker_keys = _list_from_sources(
        runtime_sources,
        "surface_relation_marker_keys",
        "surface_relation_marker_key",
        "relation_marker_key",
    )
    surface_recovery_aligned = _bool_from_sources(runtime_sources, "surface_recovery_relation_line_aligned")
    source_records = _relation_source_records(
        reader_sources=reader_sources,
        runtime_sources=runtime_sources,
        limited_reader_repair_diagnostic=limited_reader_repair_diagnostic,
        expected_relation_types=expected_relation_types,
    )
    selected_relation_signal_source = _selected_relation_signal_source(source_records)
    gate_recovery_synthesized_reader = _gate_recovery_synthesized_reader_report(
        reader_gate=reader_gate if isinstance(reader_gate, Mapping) else {},
        relation_surface_contract_version=relation_surface_contract_version,
    )
    strict_relation_trace = _build_strict_relation_trace(
        expected_relation_types=expected_relation_types,
        reader_signal_keys=reader_signal_keys,
        reader_signal_relation_types=reader_signal_relation_types,
        marker_signal_keys=marker_signal_keys,
        marker_keys=marker_keys,
        source_records=source_records,
        selected_relation_signal_source=selected_relation_signal_source,
        gate_recovery_synthesized_reader_report=gate_recovery_synthesized_reader,
    )
    strict_relation_fail_closed = _strict_relation_fail_closed_diagnostic(
        strict_relation_trace=strict_relation_trace,
        gate_trace=gate_trace,
    )
    diagnostic = {
        "version": RELATION_DIAGNOSTIC_VERSION,
        "target_step": RELATION_DIAGNOSTIC_STEP,
        "step": RELATION_DIAGNOSTIC_STEP,
        "diagnostic_connected": True,
        "relation_surface_contract_version": relation_surface_contract_version,
        "reader_relation_signal_detected": bool(reader_signal_detected),
        "reader_relation_signal_count": int(reader_signal_count or 0),
        "reader_relation_signal_keys": list(reader_signal_keys),
        "reader_relation_signal_relation_types": list(reader_signal_relation_types),
        "expected_relation_types": list(expected_relation_types),
        "strict_relation_trace": strict_relation_trace,
        "strict_relation_fail_closed": strict_relation_fail_closed,
        "strict_relation_fail_closed_evaluated": bool(strict_relation_fail_closed.get("strict_relation_fail_closed_evaluated")),
        "strict_relation_fail_closed_triggered": bool(strict_relation_fail_closed.get("strict_relation_fail_closed_triggered")),
        "strict_relation_fail_closed_applied": bool(strict_relation_fail_closed.get("strict_relation_fail_closed_applied")),
        "strict_relation_type": _clean(strict_relation_fail_closed.get("strict_relation_type")),
        "strict_relation_surface_present_after_repair": bool(strict_relation_fail_closed.get("strict_relation_surface_present_after_repair")),
        "strict_relation_surface_missing_after_repair": bool(strict_relation_fail_closed.get("strict_relation_surface_missing_after_repair")),
        "fallback_public_recovery_attempted": bool(strict_relation_fail_closed.get("fallback_public_recovery_attempted")),
        "fallback_public_recovery_allowed_for_this_candidate": bool(strict_relation_fail_closed.get("fallback_public_recovery_allowed_for_this_candidate")),
        "relation_not_expressed_preserved": bool(strict_relation_fail_closed.get("relation_not_expressed_preserved")),
        "relation_not_expressed_retained": bool(strict_relation_fail_closed.get("relation_not_expressed_retained")),
        "strict_relation_fail_closed_blocked_reasons": list(strict_relation_fail_closed.get("blocked_reasons") or []),
        "relation_signal_source_records": list(source_records),
        "relation_signal_source_priority": list(RELATION_SIGNAL_SOURCE_PRIORITY),
        "selected_relation_signal_source": selected_relation_signal_source,
        "gate_recovery_synthesized_reader_report": bool(gate_recovery_synthesized_reader),
        "strict_relation_signal_required": bool(strict_relation_trace.get("strict_relation_signal_required")),
        "required_relation_signal_keys": list(strict_relation_trace.get("required_relation_signal_keys") or []),
        "matched_relation_signal_keys": list(strict_relation_trace.get("matched_relation_signal_keys") or []),
        "broad_relation_type_only_keys": list(strict_relation_trace.get("broad_relation_type_only_keys") or []),
        "broad_relation_type_only": bool(strict_relation_trace.get("broad_relation_type_only")),
        "relation_surface_status": _clean(strict_relation_trace.get("relation_surface_status")),
        "relation_surface_missing": bool(strict_relation_trace.get("relation_surface_missing")),
        "relation_surface_missing_after_repair": bool(strict_relation_trace.get("relation_surface_missing_after_repair")),
        "strict_relation_surface_present_anywhere": bool(strict_relation_trace.get("strict_relation_surface_present_anywhere")),
        "reader_gate_relation_not_expressed": "relation_not_expressed" in reader_rejection_reasons,
        "reader_rejection_reasons": list(reader_rejection_reasons),
        "limited_reader_repair_diagnostic": limited_reader_repair_diagnostic,
        "limited_reader_repair": dict(limited_reader_repair_diagnostic.get("limited_reader_repair") or {}),
        "limited_reader_repair_attempted": bool(limited_reader_repair_diagnostic.get("attempted")),
        "limited_reader_repair_applied": bool(limited_reader_repair_diagnostic.get("applied")),
        "limited_reader_repair_requires_repair": bool(limited_reader_repair_diagnostic.get("requires_limited_reader_repair")),
        "limited_reader_repair_operations": list(limited_reader_repair_diagnostic.get("operations") or []),
        "limited_reader_repair_relation_marker_key": _clean(limited_reader_repair_diagnostic.get("relation_marker_key")),
        "limited_reader_repair_relation_marker_signal_detected": bool(limited_reader_repair_diagnostic.get("relation_marker_signal_detected")),
        "limited_reader_repair_relation_marker_signal_keys": list(limited_reader_repair_diagnostic.get("relation_marker_signal_keys") or []),
        "limited_reader_repair_relation_type": _clean(limited_reader_repair_diagnostic.get("relation_type")),
        "limited_reader_repair_meaning_added": bool(limited_reader_repair_diagnostic.get("meaning_added")),
        "limited_reader_repair_gate_relaxed": bool(limited_reader_repair_diagnostic.get("gate_relaxed")),
        "limited_reader_repair_raw_input_included": False,
        "surface_recovery_relation_line_aligned": bool(surface_recovery_aligned),
        "surface_relation_marker_key": surface_marker_keys[0] if surface_marker_keys else "",
        "surface_relation_marker_keys": list(surface_marker_keys),
        "self_repair_relation_marker_applied": bool(marker_applied),
        "self_repair_relation_marker_key": marker_keys[0] if marker_keys else "",
        "self_repair_relation_marker_keys": list(marker_keys),
        "self_repair_relation_marker_count": int(marker_count or 0),
        "self_repair_relation_marker_signal_detected": bool(
            _bool_from_sources(runtime_sources, "self_repair_relation_marker_signal_detected", "self_repair_relation_signal_detected", "reader_relation_signal_detected", "detected")
            or bool(marker_signal_keys)
        ),
        "self_repair_relation_marker_signal_count": int(
            _int_from_sources(runtime_sources, "self_repair_relation_marker_signal_count", "self_repair_relation_signal_count", "reader_relation_signal_count", "count")
            or len(marker_signal_keys)
        ),
        "self_repair_relation_marker_signal_keys": list(marker_signal_keys),
        "self_repair_relation_marker_signal_relation_types": list(marker_relation_types),
        "self_repair_relation_marker_meaning_added": bool(_bool_from_sources(runtime_sources, "self_repair_relation_marker_meaning_added", "meaning_added", "new_meaning_added")),
        "self_repair_relation_marker_gate_relaxed": bool(_bool_from_sources(runtime_sources, "self_repair_relation_marker_gate_relaxed", "gate_relaxed")),
        "raw_input_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "reader_gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }
    return diagnostic


def build_complete_reply_diagnostics_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_REPLY_DIAGNOSTICS_VERSION,
        "target_step": COMPLETE_REPLY_DIAGNOSTICS_STAGE,
        "step": COMPLETE_REPLY_DIAGNOSTICS_STAGE,
        "implementation_unit": COMPLETE_REPLY_DIAGNOSTICS_IMPLEMENTATION_UNIT,
        "stage": "complete_composer_initial",
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "reply_service_integration_added": True,
        "diagnostic_summary_integration_added": True,
        "repair_trace_connection_added": True,
        "scorecard_event_connection_added": True,
        "comment_text_contract": "passed_only",
        "comment_text_written_by_step11": False,
        "comment_text_key_written": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "external_ai_allowed": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_allowed": False,
        "raw_input_included": False,
        "comment_text_included": False,
        "raw_input_required_for_improvement": False,
    }


def build_complete_scorecard_event(
    *,
    composer_candidate: Any = None,
    display_decision: Any = None,
    gate_trace: Mapping[str, Any] | None = None,
    resolution_meta: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a one-row event that Step 12 scorecard can aggregate later."""

    runtime_meta = extract_complete_composer_runtime_meta(composer_candidate)
    candidate_seen = bool(_is_complete_candidate(composer_candidate))
    composer_status = _clean(_candidate_attr(composer_candidate, "status", ""))
    composer_source = _clean(_candidate_attr(composer_candidate, "composer_source", ""))
    candidate_generated = bool(composer_status == "generated" and composer_source == "ai_generated")
    used_evidence = _dedupe(_candidate_attr(composer_candidate, "used_evidence_span_ids", []) or runtime_meta.get("used_evidence_span_ids") or [])
    used_phrase = _dedupe(runtime_meta.get("used_phrase_unit_ids") or [])
    used_relations = _dedupe(_candidate_attr(composer_candidate, "used_relation_ids", []) or runtime_meta.get("used_relation_ids") or runtime_meta.get("relation_types") or [])
    repair_trace_source = runtime_meta.get("repair_trace_v2") or runtime_meta.get("repair_trace")
    repair_trace = _as_list(repair_trace_source) if isinstance(repair_trace_source, (list, tuple, set)) else []
    self_repair = runtime_meta.get("self_repair_report_v2") if isinstance(runtime_meta.get("self_repair_report_v2"), Mapping) else runtime_meta.get("self_repair") if isinstance(runtime_meta.get("self_repair"), Mapping) else {}
    binding_count = _binding_count_from_meta(runtime_meta)
    grounding_report = _final_grounding_report_from_meta(runtime_meta)
    product_grounding = _product_quality_grounding_report_from_meta(grounding_report)
    surface_variation = _surface_variation_report_from_meta(runtime_meta)
    display_comment_text = _candidate_attr(display_decision, "comment_text", "")
    surface_quality_signature = build_surface_quality_signature(
        comment_text=display_comment_text,
        sentence_bindings=(
            runtime_meta.get("sentence_bindings")
            or runtime_meta.get("sentence_binding_bundle")
            or runtime_meta.get("grounding_input")
        ),
        relation_meta=(
            runtime_meta.get("relation_surface_report")
            if isinstance(runtime_meta.get("relation_surface_report"), Mapping)
            else runtime_meta.get("relation_graph")
            if isinstance(runtime_meta.get("relation_graph"), Mapping)
            else {}
        ),
        phrase_unit_grammar_meta=(
            runtime_meta.get("phrase_unit_grammar_normalizer")
            if isinstance(runtime_meta.get("phrase_unit_grammar_normalizer"), Mapping)
            else runtime_meta.get("complete_material_service")
            if isinstance(runtime_meta.get("complete_material_service"), Mapping)
            else runtime_meta.get("material_service")
            if isinstance(runtime_meta.get("material_service"), Mapping)
            else {}
        ),
    )
    assert_surface_quality_signature_meta_only(surface_quality_signature)
    surface_signature_event = normalize_surface_signature_to_scorecard_event(surface_quality_signature)
    tone_guard_report = _tone_guard_report_from_meta(runtime_meta)
    nested_tone_report = tone_guard_report.get("tone_engine_2_1_report") or tone_guard_report.get("step9_tone_engine_2_1_report")
    if isinstance(nested_tone_report, Mapping):
        tone_engine_2_1_report = nested_tone_report
    else:
        tone_engine_2_1_report = tone_guard_report
    tone_engine_2_1_event = normalize_tone_engine_2_1_to_scorecard_event(tone_engine_2_1_report)
    tone_guard_major_count = max(_safe_int(tone_guard_report.get("tone_guard_major_count"), 0), _safe_int(tone_engine_2_1_event.get("tone_guard_major_count"), 0))
    tone_guard_reasons = _dedupe([
        *list(tone_guard_report.get("tone_guard_reasons") or tone_guard_report.get("blocker_reasons") or []),
        *list(tone_engine_2_1_event.get("tone_guard_reasons") or []),
    ])
    surface_same_ending_major_count = _safe_int(surface_variation.get("same_ending_major_count"), 0)
    surface_signature_repeat_count = _safe_int(surface_variation.get("surface_signature_repeat_count"), 0)
    surface_connector_repetition_count = _safe_int(surface_variation.get("connector_repetition_major_count") or surface_variation.get("surface_connector_repetition_count"), 0)
    surface_template_flag_count = len(_as_list(surface_variation.get("flagged_template_sentence_ids")))
    surface_raw_input_signature_count = len(_as_list(surface_variation.get("raw_input_sentence_ids")))
    surface_variation_major_count = (
        surface_same_ending_major_count
        + surface_signature_repeat_count
        + surface_connector_repetition_count
        + surface_template_flag_count
        + surface_raw_input_signature_count
    )
    binding_supported_sentence_count = _safe_int(
        product_grounding.get("binding_supported_sentence_count")
        or grounding_report.get("binding_supported_sentence_count"),
        0,
    )
    expected_binding_count = _safe_int(
        product_grounding.get("expected_binding_count")
        or grounding_report.get("expected_binding_count")
        or binding_count,
        binding_count,
    )
    if binding_supported_sentence_count == 0 and grounding_report.get("binding_used") and expected_binding_count:
        binding_supported_sentence_count = expected_binding_count
    binding_pass_rate = (
        round(binding_supported_sentence_count / max(1, expected_binding_count), 3)
        if expected_binding_count
        else (1.0 if binding_count and used_evidence and (used_phrase or used_relations) else 0.0 if candidate_seen else None)
    )
    observation_status = _clean(_candidate_attr(display_decision, "observation_status", ""))
    display_passed = observation_status == "passed"
    gate_reasons = _dedupe(_candidate_attr(display_decision, "rejection_reasons", []))
    summary = dict(diagnostic_summary or {}) if isinstance(diagnostic_summary, Mapping) else {}
    runtime_surface_step8 = build_runtime_surface_step8_diagnostics_meta(
        runtime_meta=runtime_meta,
        gate_trace=gate_trace,
        diagnostic_summary=summary,
        surface_quality_signature=surface_quality_signature,
        display_decision=display_decision,
    )
    repair_attempted = bool(repair_trace or self_repair.get("attempt_count") or self_repair.get("repair_attempted"))
    repair_success = _repair_succeeded(self_repair, repair_trace, display_passed)
    repair_trace_v2 = _repair_trace_v2_summary(repair_trace, self_repair)
    if repair_trace_v2["repair_meaning_added_count"] or repair_trace_v2["repair_policy_violation_count"]:
        repair_success = False
    binding_pass = bool(
        (expected_binding_count and binding_supported_sentence_count >= expected_binding_count)
        or (binding_count and used_evidence and (used_phrase or used_relations))
    )
    template_major_count = _count_reason_markers(gate_reasons, _TEMPLATE_REASON_MARKERS) + surface_variation_major_count
    safety_major_count = _count_reason_markers(gate_reasons, _SAFETY_REASON_MARKERS) + (1 if observation_status == "safety_blocked" else 0) + tone_guard_major_count
    runtime_surface_source_lock = build_runtime_surface_source_lock(
        trace_id=summary.get("trace_id") or _candidate_attr(display_decision, "trace_id", ""),
        emotion_log_id=summary.get("emotion_log_id") or _candidate_attr(display_decision, "emotion_log_id", ""),
        observation_status=observation_status,
        backend_comment_text_present=display_passed,
        backend_comment_text_length=len(_clean(display_comment_text)),
        comment_text=display_comment_text,
        display_confirmed=display_passed,
        display_confirmed_source="backend_display_gate",
        coverage_group=runtime_meta.get("coverage_group") or runtime_meta.get("coverage_scope") or summary.get("coverage_group"),
        composer_candidate=composer_candidate,
        resolution_meta=resolution_meta,
        runtime_meta=runtime_meta,
        diagnostic_meta=summary,
        display_meta={"observation_status": observation_status, "display_confirmed": display_passed},
        surface_signature_id=surface_quality_signature.get("surface_signature_id"),
    )
    return {
        "version": COMPLETE_SCORECARD_EVENT_VERSION,
        "target_step": "Step12_Scorecard_fixture_extension",
        "source_step": COMPLETE_REPLY_DIAGNOSTICS_STAGE,
        "implementation_unit": COMPLETE_REPLY_DIAGNOSTICS_IMPLEMENTATION_UNIT,
        "event_kind": "complete_composer_initial_reply_attempt",
        "scorecard_event_added": True,
        "scorecard_event_connected": True,
        "scorecard_event_only": True,
        "complete_candidate_seen": candidate_seen,
        "complete_candidate_generated": candidate_generated,
        "candidate_generated_before_display_gate": candidate_generated,
        "complete_candidate_generated_before_display_gate": candidate_generated,
        "candidate_seen_before_display_gate": candidate_seen,
        "complete_candidate_seen_before_display_gate": candidate_seen,
        "complete_candidate_displayed": bool(display_passed and candidate_seen),
        "eligible_count": 1 if candidate_seen else 0,
        "passed_display_count": 1 if display_passed and candidate_seen else 0,
        "candidate_generated_count": 1 if composer_status == "generated" and composer_source == "ai_generated" and candidate_seen else 0,
        "binding_pass": binding_pass,
        "binding_pass_rate": binding_pass_rate,
        "binding_supported_sentence_count": binding_supported_sentence_count,
        "expected_binding_count": expected_binding_count,
        "unsupported_sentence_ids": list(product_grounding.get("unsupported_sentence_ids") or grounding_report.get("unsupported_sentence_ids") or []),
        "relation_not_expressed_sentence_ids": list(product_grounding.get("relation_not_expressed_sentence_ids") or grounding_report.get("relation_not_expressed_sentence_ids") or []),
        "phrase_unit_missing_sentence_ids": list(product_grounding.get("phrase_unit_missing_sentence_ids") or grounding_report.get("phrase_unit_missing_sentence_ids") or []),
        "weak_material_sentence_ids": list(product_grounding.get("weak_material_sentence_ids") or grounding_report.get("weak_material_sentence_ids") or []),
        "binding_support_source": _clean(product_grounding.get("binding_support_source") or grounding_report.get("binding_support_source")),
        "repair_success": repair_success,
        "repair_success_rate": 1.0 if repair_success else 0.0 if repair_attempted else None,
        "repair_trace_contract_version": repair_trace_v2["repair_trace_contract_version"],
        "repair_trace_v2_count": repair_trace_v2["repair_trace_v2_count"],
        "repair_passed_count": repair_trace_v2["repair_passed_count"],
        "repair_failed_count": repair_trace_v2["repair_failed_count"],
        "repair_aborted_count": repair_trace_v2["repair_aborted_count"],
        "repair_meaning_added_count": repair_trace_v2["repair_meaning_added_count"],
        "repair_policy_violation_count": repair_trace_v2["repair_policy_violation_count"],
        "repair_operation_counts": repair_trace_v2["repair_operation_counts"],
        "repair_reason_counts": repair_trace_v2["repair_reason_counts"],
        "repair_result_counts": repair_trace_v2["repair_result_counts"],
        "repair_abort_reasons": repair_trace_v2["repair_abort_reasons"],
        "repair_source_gates": repair_trace_v2["repair_source_gates"],
        "repair_trace_v2_ready": repair_trace_v2["repair_trace_v2_ready"],
        "repair_meaning_added": repair_trace_v2["meaning_added"],
        "template_major_count": template_major_count,
        "surface_same_ending_major_count": surface_same_ending_major_count,
        "surface_signature_repeat_count": surface_signature_repeat_count,
        "surface_connector_repetition_count": surface_connector_repetition_count,
        "surface_template_flag_count": surface_template_flag_count,
        "surface_raw_input_signature_count": surface_raw_input_signature_count,
        "surface_variation_major_count": surface_variation_major_count,
        "surface_variation_passed": bool(surface_variation.get("passed", True)) and surface_variation_major_count == 0,
        "surface_variation_report": _safe_mapping(surface_variation),
        "surface_quality_signature_version": SURFACE_QUALITY_SIGNATURE_VERSION,
        "surface_quality_signature_ready": True,
        "step2_surface_quality_signature_ready": True,
        "step2_surface_signature_measured": True,
        "surface_quality_signature": surface_quality_signature,
        "step2_surface_quality_signature": surface_quality_signature,
        **surface_signature_event,
        "surface_signature_template_major_count": 1 if surface_quality_signature.get("template_major") else 0,
        "surface_signature_grammar_warning_count": int(surface_quality_signature.get("grammar_warning_count") or 0),
        "tone_engine_version": _clean(tone_guard_report.get("tone_engine_version") or tone_engine_2_1_event.get("tone_engine_2_1_version")),
        "tone_engine_2_1_version": _clean(tone_engine_2_1_event.get("tone_engine_2_1_version") or RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION),
        "product_quality_tone_engine_version": _clean(tone_guard_report.get("product_quality_tone_engine_version")),
        "tone_policy_applied": bool(runtime_meta.get("tone_policy_applied") or runtime_meta.get("tone_policy")),
        "tone_guard_report": _safe_mapping(tone_guard_report),
        "tone_engine_2_1_report": _safe_mapping(tone_engine_2_1_report),
        "step9_tone_engine_2_1_report": _safe_mapping(tone_engine_2_1_report),
        **tone_engine_2_1_event,
        "tone_guard_major_count": tone_guard_major_count,
        "tone_guard_passed": bool(tone_guard_report.get("passed", tone_guard_major_count == 0)) and tone_guard_major_count == 0,
        "tone_guard_reasons": list(tone_guard_reasons),
        "tone_over_empathy_count": max(_safe_int(tone_guard_report.get("over_empathy_count"), 0), _safe_int(tone_engine_2_1_event.get("tone_over_empathy_count"), 0)),
        "tone_diagnostic_count": max(_safe_int(tone_guard_report.get("diagnostic_tone_count"), 0), _safe_int(tone_engine_2_1_event.get("tone_diagnostic_count"), 0)),
        "tone_advice_count": max(_safe_int(tone_guard_report.get("advice_like_count"), 0), _safe_int(tone_engine_2_1_event.get("tone_advice_count"), 0)),
        "tone_generic_count": max(_safe_int(tone_guard_report.get("generic_comfort_count"), 0), _safe_int(tone_engine_2_1_event.get("tone_generic_count"), 0)),
        "tone_meaning_added": bool(runtime_meta.get("tone_meaning_added") or tone_guard_report.get("meaning_added") or tone_guard_report.get("meaning_added_by_tone_policy") or tone_engine_2_1_event.get("tone_meaning_added")),
        "safety_major_count": safety_major_count,
        "read_feeling_score": None,
        "top_rejection_reasons": list(dict.fromkeys([*gate_reasons[:5], *tone_guard_reasons[:3], *runtime_surface_step8.get("runtime_surface_pre_return_gate_rejection_reasons", [])[:3]])),
        "runtime_surface_step8_diagnostics": runtime_surface_step8,
        "runtime_surface_diagnostics_scorecard": runtime_surface_step8,
        "runtime_surface_pre_return_gate_evaluated": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_evaluated")),
        "runtime_surface_pre_return_gate_passed": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_passed")),
        "runtime_surface_pre_return_gate_action": str(runtime_surface_step8.get("runtime_surface_pre_return_gate_action") or ""),
        "runtime_surface_pre_return_gate_rejection_reasons": list(runtime_surface_step8.get("runtime_surface_pre_return_gate_rejection_reasons") or []),
        "runtime_surface_pre_return_gate_final_passed": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_final_passed")),
        "runtime_surface_pre_return_gate_scorecard_connected": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_scorecard_connected")),
        "runtime_surface_diagnostics_scorecard_updated": bool(runtime_surface_step8.get("runtime_surface_diagnostics_scorecard_updated")),
        "step8_runtime_surface_diagnostics_ready": bool(runtime_surface_step8.get("step8_runtime_surface_diagnostics_ready")),
        "surface_template_major_blocked": bool(runtime_surface_step8.get("surface_template_major_blocked")),
        "malformed_phrase_unit_blocked_count": int(runtime_surface_step8.get("malformed_phrase_unit_blocked_count") or 0),
        "shallow_realizer_version": str(runtime_surface_step8.get("shallow_realizer_version") or ""),
        "shallow_v2_used": bool(runtime_surface_step8.get("shallow_v2_used")),
        "low_information_specificity_used": bool(runtime_surface_step8.get("low_information_specificity_used")),
        "step6_low_information_specificity_ready": bool(runtime_surface_step8.get("step6_low_information_specificity_ready")),
        "safe_anchor_count": int(runtime_surface_step8.get("safe_anchor_count") or 0),
        "uses_safe_anchor": bool(runtime_surface_step8.get("uses_safe_anchor")),
        "safe_anchor_role": str(runtime_surface_step8.get("safe_anchor_role") or ""),
        "safe_anchor_surface_kind": str(runtime_surface_step8.get("safe_anchor_surface_kind") or ""),
        "safe_anchor_evidence_ids": list(runtime_surface_step8.get("safe_anchor_evidence_ids") or []),
        "unsupported_event_assertion_present": bool(runtime_surface_step8.get("unsupported_event_assertion_present")),
        "user_fact_promotion_attempt": bool(runtime_surface_step8.get("user_fact_promotion_attempt")),
        "observation_status": observation_status,
        "display_passed": display_passed,
        "runtime_surface_source_lock_version": RUNTIME_SURFACE_SOURCE_LOCK_VERSION,
        "runtime_surface_source_lock_ready": True,
        "runtime_surface_source_locked": True,
        "runtime_surface_source_lock": runtime_surface_source_lock,
        "step1_runtime_surface_source_lock": runtime_surface_source_lock,
        "runtime_composer_source": runtime_surface_source_lock.get("composer_source"),
        "composer_requested": runtime_surface_source_lock.get("composer_requested"),
        "composer_resolved": runtime_surface_source_lock.get("composer_resolved"),
        "runtime_composer_model": runtime_surface_source_lock.get("composer_model"),
        "runtime_surface_source_complete_initial_client_used": bool(runtime_surface_source_lock.get("complete_initial_client_used")),
        "runtime_surface_source_limited_reader_repair_applied": bool(runtime_surface_source_lock.get("limited_reader_repair_applied")),
        "sentence_plan_version": runtime_surface_source_lock.get("sentence_plan_version"),
        "surface_realizer_version": runtime_surface_source_lock.get("surface_realizer_version"),
        "tone_policy_version": runtime_surface_source_lock.get("tone_policy_version"),
        "self_repair_version": runtime_surface_source_lock.get("self_repair_version"),
        "comment_text_body_included": False,
        "composer_source": composer_source,
        "composer_status": composer_status,
        "composer_model": _clean(_candidate_attr(composer_candidate, "composer_model", "") or runtime_meta.get("composer_model")),
        "generation_method": _clean(_candidate_attr(composer_candidate, "generation_method", "") or runtime_meta.get("generation_method")),
        "coverage_group": _clean(runtime_meta.get("coverage_group") or runtime_meta.get("coverage_scope") or summary.get("coverage_group")),
        "coverage_scope": _clean(_candidate_attr(composer_candidate, "coverage_scope", "") or runtime_meta.get("coverage_scope")),
        "binding_count": binding_count,
        "binding_present": bool(binding_count),
        "used_evidence_span_count": len(used_evidence),
        "used_phrase_unit_count": len(used_phrase),
        "used_relation_count": len(used_relations),
        "relation_types": used_relations,
        "repair_attempted": repair_attempted,
        "repair_trace_count": len(repair_trace),
        "self_repair_ready": bool(self_repair.get("ready")) if self_repair else False,
        "gate_primary_reason": _gate_primary_reason(gate_trace, display_decision),
        "gate_rejection_reasons": gate_reasons,
        "registry_source": _clean((resolution_meta or {}).get("source") or (resolution_meta or {}).get("resolution_source")) if isinstance(resolution_meta, Mapping) else "",
        "complete_initial_client_used": bool((resolution_meta or {}).get("complete_initial_client_used")) if isinstance(resolution_meta, Mapping) else False,
        "explicit_client_used": bool((resolution_meta or {}).get("explicit_client_used")) if isinstance(resolution_meta, Mapping) else False,
        "product_gate_evaluation": "not_evaluated_step11_only",
        "raw_input_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "comment_text_contract": "passed_only",
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }


def build_complete_reply_service_diagnostics(
    *,
    composer_candidate: Any = None,
    display_decision: Any = None,
    gate_trace: Mapping[str, Any] | None = None,
    resolution_meta: Mapping[str, Any] | None = None,
    release_meta: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    phase_gate: Mapping[str, Any] | None = None,
    scorecard_harness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Connect Complete Composer meta to reply diagnostics without output changes."""

    contract = build_complete_reply_diagnostics_contract_meta()
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    runtime_meta = extract_complete_composer_runtime_meta(composer_candidate)
    candidate_seen = bool(_is_complete_candidate(composer_candidate))
    scorecard_event = build_complete_scorecard_event(
        composer_candidate=composer_candidate,
        display_decision=display_decision,
        gate_trace=gate_trace,
        resolution_meta=resolution_meta,
        diagnostic_summary=diagnostic_summary,
    )
    runtime_surface_source_lock = dict(scorecard_event.get("runtime_surface_source_lock") or {})
    surface_quality_signature = dict(
        scorecard_event.get("surface_quality_signature")
        or scorecard_event.get("step2_surface_quality_signature")
        or {}
    )
    if surface_quality_signature:
        assert_surface_quality_signature_meta_only(surface_quality_signature)
    runtime_surface_step8 = build_runtime_surface_step8_diagnostics_meta(
        runtime_meta=runtime_meta,
        gate_trace=gate_trace,
        diagnostic_summary=diagnostic_summary,
        surface_quality_signature=surface_quality_signature,
        display_decision=display_decision,
    )
    relation_diagnostic = build_positive_recovery_relation_diagnostic(
        composer_candidate=composer_candidate,
        gate_trace=gate_trace,
    )
    limited_reader_repair_diagnostic = dict(relation_diagnostic.get("limited_reader_repair_diagnostic") or {})
    limited_reader_repair = dict(limited_reader_repair_diagnostic.get("limited_reader_repair") or {})
    repair_trace_source = runtime_meta.get("repair_trace_v2") or runtime_meta.get("repair_trace")
    repair_trace = _as_list(repair_trace_source) if isinstance(repair_trace_source, (list, tuple, set)) else []
    self_repair = runtime_meta.get("self_repair_report_v2") if isinstance(runtime_meta.get("self_repair_report_v2"), Mapping) else runtime_meta.get("self_repair") if isinstance(runtime_meta.get("self_repair"), Mapping) else {}
    repair_trace_v2 = _repair_trace_v2_summary(repair_trace, self_repair)
    grounding_input = runtime_meta.get("grounding_input") if isinstance(runtime_meta.get("grounding_input"), Mapping) else {}
    if not grounding_input and isinstance(runtime_meta.get("complete_grounding_binding"), Mapping):
        grounding_input = runtime_meta.get("complete_grounding_binding")
    binding_count = _binding_count_from_meta(runtime_meta)
    connected_parts = {
        "material_service": isinstance(runtime_meta.get("material_service"), Mapping),
        "coverage_plan": isinstance(runtime_meta.get("coverage_plan"), Mapping),
        "relation_graph": isinstance(runtime_meta.get("relation_graph"), Mapping),
        "sentence_plan": isinstance(runtime_meta.get("sentence_plan"), Mapping),
        "sentence_binding_bundle": isinstance(runtime_meta.get("sentence_binding_bundle"), Mapping),
        "surface_realizer": isinstance(runtime_meta.get("surface_realizer"), Mapping),
        "grounding_input": bool(grounding_input),
        "self_repair": isinstance(self_repair, Mapping) and bool(self_repair),
        "limited_reader_repair": bool(limited_reader_repair),
        "repair_trace": bool(repair_trace),
        "runtime_surface_source_lock": bool(runtime_surface_source_lock),
        "surface_quality_signature": bool(surface_quality_signature),
        "scorecard_event": True,
    }
    composer_status = _clean(_candidate_attr(composer_candidate, "status", ""))
    composer_source = _clean(_candidate_attr(composer_candidate, "composer_source", ""))
    candidate_generated = bool(composer_status == "generated" and composer_source == "ai_generated")
    observation_status = _clean(_candidate_attr(display_decision, "observation_status", ""))
    return {
        **contract,
        "stage": "complete_composer_initial",
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "complete_reply_service_diagnostics_added": True,
        "complete_reply_service_integrated": True,
        "complete_meta_connected": bool(runtime_meta),
        "complete_candidate_seen": candidate_seen,
        "complete_candidate_generated": candidate_generated,
        "candidate_generated_before_display_gate": candidate_generated,
        "complete_candidate_generated_before_display_gate": candidate_generated,
        "candidate_seen_before_display_gate": candidate_seen,
        "complete_candidate_seen_before_display_gate": candidate_seen,
        "complete_candidate_displayed": bool(observation_status == "passed" and candidate_seen),
        "composer_status": composer_status,
        "composer_source": composer_source,
        "composer_model": _clean(_candidate_attr(composer_candidate, "composer_model", "") or runtime_meta.get("composer_model")),
        "generation_method": _clean(_candidate_attr(composer_candidate, "generation_method", "") or runtime_meta.get("generation_method")),
        "generation_scope": _clean(_candidate_attr(composer_candidate, "generation_scope", "") or runtime_meta.get("generation_scope")),
        "coverage_scope": _clean(_candidate_attr(composer_candidate, "coverage_scope", "") or runtime_meta.get("coverage_scope")),
        "observation_status": observation_status,
        "runtime_surface_source_lock_version": RUNTIME_SURFACE_SOURCE_LOCK_VERSION,
        "runtime_surface_source_lock_ready": bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready")),
        "runtime_surface_source_locked": bool(runtime_surface_source_lock.get("runtime_surface_source_locked")),
        "runtime_surface_source_lock": runtime_surface_source_lock,
        "step1_runtime_surface_source_lock": runtime_surface_source_lock,
        "runtime_composer_source": runtime_surface_source_lock.get("composer_source"),
        "composer_requested": runtime_surface_source_lock.get("composer_requested"),
        "composer_resolved": runtime_surface_source_lock.get("composer_resolved"),
        "runtime_composer_model": runtime_surface_source_lock.get("composer_model"),
        "runtime_surface_source_complete_initial_client_used": bool(runtime_surface_source_lock.get("complete_initial_client_used")),
        "runtime_surface_source_limited_reader_repair_applied": bool(runtime_surface_source_lock.get("limited_reader_repair_applied")),
        "sentence_plan_version": runtime_surface_source_lock.get("sentence_plan_version"),
        "surface_realizer_version": runtime_surface_source_lock.get("surface_realizer_version"),
        "tone_policy_version": runtime_surface_source_lock.get("tone_policy_version"),
        "self_repair_version": runtime_surface_source_lock.get("self_repair_version"),
        "surface_quality_signature_version": SURFACE_QUALITY_SIGNATURE_VERSION,
        "step2_surface_quality_signature_ready": bool(scorecard_event.get("step2_surface_quality_signature_ready")),
        "surface_quality_signature": surface_quality_signature,
        "step2_surface_quality_signature": surface_quality_signature,
        "surface_signature_id": scorecard_event.get("surface_signature_id"),
        "surface_signature_family_key": scorecard_event.get("surface_signature_family_key"),
        "surface_template_major": bool(scorecard_event.get("surface_template_major")),
        "surface_grammar_warning_codes": list(scorecard_event.get("surface_grammar_warning_codes") or []),
        "surface_grammar_warning_count": int(scorecard_event.get("surface_grammar_warning_count") or 0),
        "runtime_surface_step8_diagnostics": runtime_surface_step8,
        "runtime_surface_diagnostics_scorecard": runtime_surface_step8,
        "runtime_surface_pre_return_gate_evaluated": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_evaluated")),
        "runtime_surface_pre_return_gate_passed": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_passed")),
        "runtime_surface_pre_return_gate_action": str(runtime_surface_step8.get("runtime_surface_pre_return_gate_action") or ""),
        "runtime_surface_pre_return_gate_rejection_reasons": list(runtime_surface_step8.get("runtime_surface_pre_return_gate_rejection_reasons") or []),
        "runtime_surface_pre_return_gate_final_passed": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_final_passed")),
        "runtime_surface_pre_return_gate_scorecard_connected": bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_scorecard_connected")),
        "runtime_surface_diagnostics_scorecard_updated": bool(runtime_surface_step8.get("runtime_surface_diagnostics_scorecard_updated")),
        "step8_runtime_surface_diagnostics_ready": bool(runtime_surface_step8.get("step8_runtime_surface_diagnostics_ready")),
        "surface_template_major_blocked": bool(runtime_surface_step8.get("surface_template_major_blocked")),
        "malformed_phrase_unit_blocked_count": int(runtime_surface_step8.get("malformed_phrase_unit_blocked_count") or 0),
        "shallow_realizer_version": str(runtime_surface_step8.get("shallow_realizer_version") or ""),
        "shallow_v2_used": bool(runtime_surface_step8.get("shallow_v2_used")),
        "low_information_specificity_used": bool(runtime_surface_step8.get("low_information_specificity_used")),
        "step6_low_information_specificity_ready": bool(runtime_surface_step8.get("step6_low_information_specificity_ready")),
        "safe_anchor_count": int(runtime_surface_step8.get("safe_anchor_count") or 0),
        "uses_safe_anchor": bool(runtime_surface_step8.get("uses_safe_anchor")),
        "safe_anchor_role": str(runtime_surface_step8.get("safe_anchor_role") or ""),
        "safe_anchor_surface_kind": str(runtime_surface_step8.get("safe_anchor_surface_kind") or ""),
        "safe_anchor_evidence_ids": list(runtime_surface_step8.get("safe_anchor_evidence_ids") or []),
        "unsupported_event_assertion_present": bool(runtime_surface_step8.get("unsupported_event_assertion_present")),
        "user_fact_promotion_attempt": bool(runtime_surface_step8.get("user_fact_promotion_attempt")),
        "connected_parts": connected_parts,
        "binding_count": binding_count,
        "binding_present": bool(binding_count),
        "grounding_binding_connected": bool(grounding_input),
        "grounding_binding": _safe_mapping(grounding_input),
        "complete_runtime_meta": runtime_meta,
        "complete_composer_meta": runtime_meta,
        "complete_composer_initial_meta": runtime_meta,
        "complete_repair_trace": repair_trace,
        "repair_trace": repair_trace,
        "positive_recovery_relation_diagnostic": relation_diagnostic,
        "relation_surface_diagnostic": relation_diagnostic,
        "step5_relation_diagnostic": relation_diagnostic,
        "limited_reader_repair_diagnostic": limited_reader_repair_diagnostic,
        "limited_reader_repair": limited_reader_repair,
        "limited_reader_repair_attempted": bool(limited_reader_repair_diagnostic.get("attempted")),
        "limited_reader_repair_applied": bool(limited_reader_repair_diagnostic.get("applied")),
        "limited_reader_repair_requires_repair": bool(limited_reader_repair_diagnostic.get("requires_limited_reader_repair")),
        "limited_reader_repair_operations": list(limited_reader_repair_diagnostic.get("operations") or []),
        "limited_reader_repair_relation_marker_key": _clean(limited_reader_repair_diagnostic.get("relation_marker_key")),
        "limited_reader_repair_relation_marker_signal_detected": bool(limited_reader_repair_diagnostic.get("relation_marker_signal_detected")),
        "limited_reader_repair_relation_marker_signal_keys": list(limited_reader_repair_diagnostic.get("relation_marker_signal_keys") or []),
        "limited_reader_repair_relation_type": _clean(limited_reader_repair_diagnostic.get("relation_type")),
        "limited_reader_repair_meaning_added": bool(limited_reader_repair_diagnostic.get("meaning_added")),
        "limited_reader_repair_gate_relaxed": bool(limited_reader_repair_diagnostic.get("gate_relaxed")),
        "limited_reader_repair_raw_input_included": False,
        "relation_surface_contract_version": relation_diagnostic["relation_surface_contract_version"],
        "reader_relation_signal_detected": relation_diagnostic["reader_relation_signal_detected"],
        "reader_relation_signal_count": relation_diagnostic["reader_relation_signal_count"],
        "reader_relation_signal_keys": relation_diagnostic["reader_relation_signal_keys"],
        "reader_relation_signal_relation_types": relation_diagnostic["reader_relation_signal_relation_types"],
        "expected_relation_types": relation_diagnostic["expected_relation_types"],
        "self_repair_relation_marker_applied": relation_diagnostic["self_repair_relation_marker_applied"],
        "self_repair_relation_marker_key": relation_diagnostic["self_repair_relation_marker_key"],
        "self_repair_relation_marker_keys": relation_diagnostic["self_repair_relation_marker_keys"],
        "self_repair_relation_marker_count": relation_diagnostic["self_repair_relation_marker_count"],
        "self_repair_relation_marker_signal_detected": relation_diagnostic["self_repair_relation_marker_signal_detected"],
        "self_repair_relation_marker_signal_keys": relation_diagnostic["self_repair_relation_marker_signal_keys"],
        "self_repair_relation_marker_meaning_added": relation_diagnostic["self_repair_relation_marker_meaning_added"],
        "self_repair_relation_marker_gate_relaxed": relation_diagnostic["self_repair_relation_marker_gate_relaxed"],
        "repair_trace_v2_summary": repair_trace_v2,
        "repair_trace_v2_count": repair_trace_v2["repair_trace_v2_count"],
        "repair_meaning_added_count": repair_trace_v2["repair_meaning_added_count"],
        "repair_policy_violation_count": repair_trace_v2["repair_policy_violation_count"],
        "repair_aborted_count": repair_trace_v2["repair_aborted_count"],
        "repair_abort_reasons": repair_trace_v2["repair_abort_reasons"],
        "repair_source_gates": repair_trace_v2["repair_source_gates"],
        "repair_trace_connected": bool(repair_trace),
        "repair_trace_count": len(repair_trace),
        "self_repair": _safe_mapping(self_repair),
        "scorecard_event": scorecard_event,
        "complete_scorecard_event": scorecard_event,
        "scorecard_event_connected": True,
        "scorecard_harness_seen": bool(scorecard_harness),
        "phase_gate_seen": bool(phase_gate),
        "release_meta_seen": bool(release_meta),
        "display_contract_preserved": True,
        "passed_only_preserved": True,
        "comment_text_contract": "passed_only",
        "comment_text_publicly_assigned": False,
        "comment_text_key_written": False,
        "comment_text_body_included": False,
        "input_feedback_comment_text_contract_preserved": True,
        "input_feedback_emlis_ai_contract_preserved": True,
        "observation_status_contract_preserved": True,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
        "fixed_fallback_used": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
    }


def attach_complete_reply_service_diagnostics(
    *,
    diagnostic_summary: dict[str, Any],
    phase_gate: dict[str, Any],
    diagnostics: Mapping[str, Any],
) -> None:
    """Attach Step 11 meta into existing reply diagnostics dictionaries."""

    scorecard_event = dict(diagnostics.get("scorecard_event") or {})
    repair_trace = list(diagnostics.get("repair_trace") or [])
    complete_meta = dict(diagnostics.get("complete_composer_initial_meta") or diagnostics.get("complete_runtime_meta") or {})
    runtime_surface_source_lock = dict(
        diagnostics.get("runtime_surface_source_lock")
        or diagnostics.get("step1_runtime_surface_source_lock")
        or scorecard_event.get("runtime_surface_source_lock")
        or {}
    )
    surface_quality_signature = dict(
        diagnostics.get("surface_quality_signature")
        or diagnostics.get("step2_surface_quality_signature")
        or scorecard_event.get("surface_quality_signature")
        or scorecard_event.get("step2_surface_quality_signature")
        or {}
    )
    if surface_quality_signature:
        assert_surface_quality_signature_meta_only(surface_quality_signature)
    diagnostic_summary["step11_complete_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_composer_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_composer_initial_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_composer_initial_meta"] = complete_meta
    diagnostic_summary["complete_composer_initial_repair_trace"] = repair_trace
    diagnostic_summary["complete_composer_initial_scorecard_event"] = scorecard_event
    diagnostic_summary["complete_composer_scorecard_event"] = scorecard_event
    diagnostic_summary["scorecard_event"] = scorecard_event
    runtime_surface_step8 = dict(
        diagnostics.get("runtime_surface_step8_diagnostics")
        or diagnostics.get("runtime_surface_diagnostics_scorecard")
        or scorecard_event.get("runtime_surface_step8_diagnostics")
        or scorecard_event.get("runtime_surface_diagnostics_scorecard")
        or {}
    )
    if runtime_surface_step8:
        diagnostic_summary["runtime_surface_step8_diagnostics"] = runtime_surface_step8
        diagnostic_summary["runtime_surface_diagnostics_scorecard"] = runtime_surface_step8
        for key in (
            "runtime_surface_pre_return_gate_evaluated",
            "runtime_surface_pre_return_gate_passed",
            "runtime_surface_pre_return_gate_action",
            "runtime_surface_pre_return_gate_rejection_reasons",
            "runtime_surface_pre_return_gate_final_passed",
            "runtime_surface_pre_return_gate_scorecard_connected",
            "runtime_surface_diagnostics_scorecard_updated",
            "step8_runtime_surface_diagnostics_ready",
            "surface_template_major_blocked",
            "malformed_phrase_unit_blocked_count",
            "shallow_realizer_version",
            "shallow_v2_used",
            "low_information_specificity_used",
            "step6_low_information_specificity_ready",
            "safe_anchor_count",
            "uses_safe_anchor",
            "safe_anchor_role",
            "safe_anchor_surface_kind",
            "safe_anchor_evidence_ids",
            "unsupported_event_assertion_present",
            "user_fact_promotion_attempt",
        ):
            if key in runtime_surface_step8:
                diagnostic_summary[key] = runtime_surface_step8[key]
    if runtime_surface_source_lock:
        diagnostic_summary["runtime_surface_source_lock"] = runtime_surface_source_lock
        diagnostic_summary["step1_runtime_surface_source_lock"] = runtime_surface_source_lock
        diagnostic_summary["runtime_surface_source_lock_ready"] = bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready"))
        diagnostic_summary["runtime_surface_source_locked"] = bool(runtime_surface_source_lock.get("runtime_surface_source_locked"))
        diagnostic_summary["runtime_composer_source"] = runtime_surface_source_lock.get("composer_source")
        diagnostic_summary["composer_requested"] = runtime_surface_source_lock.get("composer_requested")
        diagnostic_summary["composer_resolved"] = runtime_surface_source_lock.get("composer_resolved")
        diagnostic_summary["runtime_composer_model"] = runtime_surface_source_lock.get("composer_model")
        diagnostic_summary["runtime_surface_source_complete_initial_client_used"] = bool(runtime_surface_source_lock.get("complete_initial_client_used"))
        diagnostic_summary["runtime_surface_source_limited_reader_repair_applied"] = bool(runtime_surface_source_lock.get("limited_reader_repair_applied"))
        diagnostic_summary["sentence_plan_version"] = runtime_surface_source_lock.get("sentence_plan_version")
        diagnostic_summary["surface_realizer_version"] = runtime_surface_source_lock.get("surface_realizer_version")
        diagnostic_summary["tone_policy_version"] = runtime_surface_source_lock.get("tone_policy_version")
        diagnostic_summary["self_repair_version"] = runtime_surface_source_lock.get("self_repair_version")
        diagnostic_summary["comment_text_body_included"] = False
    if surface_quality_signature:
        diagnostic_summary["surface_quality_signature_version"] = SURFACE_QUALITY_SIGNATURE_VERSION
        diagnostic_summary["step2_surface_quality_signature_ready"] = bool(
            scorecard_event.get("step2_surface_quality_signature_ready", True)
        )
        diagnostic_summary["surface_quality_signature"] = surface_quality_signature
        diagnostic_summary["step2_surface_quality_signature"] = surface_quality_signature
        diagnostic_summary["surface_signature_id"] = surface_quality_signature.get("surface_signature_id")
        diagnostic_summary["surface_signature_family_key"] = surface_quality_signature.get("surface_signature_family_key")
        diagnostic_summary["surface_template_major"] = bool(surface_quality_signature.get("template_major"))
        diagnostic_summary["surface_grammar_warning_codes"] = list(surface_quality_signature.get("grammar_warning_codes") or [])
        diagnostic_summary["surface_grammar_warning_count"] = int(surface_quality_signature.get("grammar_warning_count") or 0)

    relation_diagnostic = dict(
        diagnostics.get("positive_recovery_relation_diagnostic")
        or diagnostics.get("relation_surface_diagnostic")
        or {}
    )
    if relation_diagnostic:
        diagnostic_summary["step5_relation_diagnostic"] = relation_diagnostic
        diagnostic_summary["positive_recovery_relation_diagnostic"] = relation_diagnostic
        diagnostic_summary["relation_surface_diagnostic"] = relation_diagnostic
        for key in (
            "relation_surface_contract_version",
            "strict_relation_trace",
            "relation_signal_source_records",
            "relation_signal_source_priority",
            "selected_relation_signal_source",
            "gate_recovery_synthesized_reader_report",
            "strict_relation_signal_required",
            "required_relation_signal_keys",
            "matched_relation_signal_keys",
            "broad_relation_type_only",
            "broad_relation_type_only_keys",
            "relation_surface_status",
            "relation_surface_missing",
            "relation_surface_missing_after_repair",
            "strict_relation_surface_present_anywhere",
            "reader_relation_signal_detected",
            "reader_relation_signal_count",
            "reader_relation_signal_keys",
            "reader_relation_signal_relation_types",
            "expected_relation_types",
            "self_repair_relation_marker_applied",
            "self_repair_relation_marker_key",
            "self_repair_relation_marker_keys",
            "self_repair_relation_marker_count",
            "self_repair_relation_marker_signal_detected",
            "self_repair_relation_marker_signal_keys",
            "self_repair_relation_marker_meaning_added",
            "self_repair_relation_marker_gate_relaxed",
            "limited_reader_repair_attempted",
            "limited_reader_repair_applied",
            "limited_reader_repair_requires_repair",
            "limited_reader_repair_operations",
            "limited_reader_repair_relation_marker_key",
            "limited_reader_repair_relation_marker_signal_detected",
            "limited_reader_repair_relation_marker_signal_keys",
            "limited_reader_repair_relation_type",
            "limited_reader_repair_meaning_added",
            "limited_reader_repair_gate_relaxed",
            "limited_reader_repair_raw_input_included",
            "strict_relation_trace",
            "relation_signal_source_records",
            "relation_signal_source_priority",
            "selected_relation_signal_source",
            "gate_recovery_synthesized_reader_report",
            "strict_relation_signal_required",
            "required_relation_signal_keys",
            "matched_relation_signal_keys",
            "broad_relation_type_only",
            "broad_relation_type_only_keys",
            "relation_surface_status",
            "relation_surface_missing",
            "relation_surface_missing_after_repair",
            "strict_relation_surface_present_anywhere",
        ):
            if key in relation_diagnostic:
                diagnostic_summary[key] = relation_diagnostic[key]

    phase_gate["step11_reply_service_diagnostics_ready"] = bool(diagnostics.get("complete_reply_service_diagnostics_added"))
    phase_gate["step11_complete_meta_connected"] = bool(diagnostics.get("complete_meta_connected"))
    phase_gate["step11_repair_trace_connected"] = bool(diagnostics.get("repair_trace_connected"))
    phase_gate["step11_scorecard_event_connected"] = bool(diagnostics.get("scorecard_event_connected"))
    phase_gate["step1_runtime_surface_source_lock_ready"] = bool(
        runtime_surface_source_lock.get("runtime_surface_source_lock_ready")
    )
    phase_gate["runtime_surface_source_lock_ready"] = bool(
        runtime_surface_source_lock.get("runtime_surface_source_lock_ready")
    )
    phase_gate["runtime_composer_source"] = runtime_surface_source_lock.get("composer_source", "")
    phase_gate["step2_surface_quality_signature_ready"] = bool(surface_quality_signature)
    phase_gate["surface_quality_signature_ready"] = bool(surface_quality_signature)
    phase_gate["surface_template_major"] = bool(surface_quality_signature.get("template_major")) if surface_quality_signature else False
    if runtime_surface_step8:
        phase_gate["runtime_surface_step8_diagnostics_ready"] = bool(runtime_surface_step8.get("ready", True))
        phase_gate["runtime_surface_pre_return_gate_evaluated"] = bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_evaluated"))
        phase_gate["runtime_surface_pre_return_gate_passed"] = bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_passed"))
        phase_gate["runtime_surface_pre_return_gate_action"] = str(runtime_surface_step8.get("runtime_surface_pre_return_gate_action") or "")
        phase_gate["runtime_surface_pre_return_gate_rejection_reasons"] = list(runtime_surface_step8.get("runtime_surface_pre_return_gate_rejection_reasons") or [])
        phase_gate["runtime_surface_pre_return_gate_final_passed"] = bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_final_passed"))
        phase_gate["runtime_surface_pre_return_gate_scorecard_connected"] = bool(runtime_surface_step8.get("runtime_surface_pre_return_gate_scorecard_connected"))
        phase_gate["runtime_surface_diagnostics_scorecard_updated"] = bool(runtime_surface_step8.get("runtime_surface_diagnostics_scorecard_updated"))
        phase_gate["step8_runtime_surface_diagnostics_ready"] = bool(runtime_surface_step8.get("step8_runtime_surface_diagnostics_ready"))
        phase_gate["surface_template_major_blocked"] = bool(runtime_surface_step8.get("surface_template_major_blocked"))
        phase_gate["malformed_phrase_unit_blocked_count"] = int(runtime_surface_step8.get("malformed_phrase_unit_blocked_count") or 0)
        phase_gate["shallow_realizer_version"] = str(runtime_surface_step8.get("shallow_realizer_version") or "")
        phase_gate["shallow_v2_used"] = bool(runtime_surface_step8.get("shallow_v2_used"))
        phase_gate["low_information_specificity_used"] = bool(runtime_surface_step8.get("low_information_specificity_used"))
        phase_gate["step6_low_information_specificity_ready"] = bool(runtime_surface_step8.get("step6_low_information_specificity_ready"))
        phase_gate["safe_anchor_count"] = int(runtime_surface_step8.get("safe_anchor_count") or 0)
        phase_gate["uses_safe_anchor"] = bool(runtime_surface_step8.get("uses_safe_anchor"))
        phase_gate["safe_anchor_role"] = str(runtime_surface_step8.get("safe_anchor_role") or "")
        phase_gate["safe_anchor_surface_kind"] = str(runtime_surface_step8.get("safe_anchor_surface_kind") or "")
        phase_gate["safe_anchor_evidence_ids"] = list(runtime_surface_step8.get("safe_anchor_evidence_ids") or [])
        phase_gate["unsupported_event_assertion_present"] = bool(runtime_surface_step8.get("unsupported_event_assertion_present"))
        phase_gate["user_fact_promotion_attempt"] = bool(runtime_surface_step8.get("user_fact_promotion_attempt"))
        phase_gate["runtime_surface_step8_raw_input_included"] = False
        phase_gate["runtime_surface_step8_comment_text_body_included"] = False
    phase_gate["step11_passed_only_preserved"] = bool(diagnostics.get("passed_only_preserved"))
    phase_gate["step11_response_shape_changed"] = bool(diagnostics.get("response_shape_changed"))
    phase_gate["step11_public_response_key_change"] = bool(diagnostics.get("public_response_key_change"))
    if relation_diagnostic:
        phase_gate["step5_relation_diagnostic_connected"] = bool(relation_diagnostic.get("diagnostic_connected"))
        phase_gate["step5_reader_relation_signal_detected"] = bool(relation_diagnostic.get("reader_relation_signal_detected"))
        phase_gate["step5_self_repair_relation_marker_applied"] = bool(relation_diagnostic.get("self_repair_relation_marker_applied"))
        phase_gate["step5_relation_diagnostic_raw_input_included"] = bool(relation_diagnostic.get("raw_input_included"))
        phase_gate["step7_limited_reader_repair_attempted"] = bool(relation_diagnostic.get("limited_reader_repair_attempted"))
        phase_gate["step7_limited_reader_repair_applied"] = bool(relation_diagnostic.get("limited_reader_repair_applied"))
        phase_gate["step7_limited_reader_repair_raw_input_included"] = bool(relation_diagnostic.get("limited_reader_repair_raw_input_included"))


__all__ = [
    "COMPLETE_REPLY_DIAGNOSTICS_IMPLEMENTATION_UNIT",
    "COMPLETE_REPLY_DIAGNOSTICS_STAGE",
    "COMPLETE_REPLY_DIAGNOSTICS_STEP",
    "COMPLETE_REPLY_DIAGNOSTICS_VERSION",
    "COMPLETE_SCORECARD_EVENT_VERSION",
    "RUNTIME_SURFACE_STEP8_DIAGNOSTICS_VERSION",
    "RUNTIME_SURFACE_STEP8_DIAGNOSTICS_STEP",
    "RUNTIME_SURFACE_SOURCE_LOCK_VERSION",
    "LIMITED_READER_REPAIR_DIAGNOSTIC_VERSION",
    "attach_complete_reply_service_diagnostics",
    "build_complete_reply_diagnostics_contract_meta",
    "build_complete_reply_service_diagnostics",
    "build_complete_scorecard_event",
    "build_runtime_surface_step8_diagnostics_meta",
    "build_positive_recovery_relation_diagnostic",
    "extract_complete_composer_runtime_meta",
]
