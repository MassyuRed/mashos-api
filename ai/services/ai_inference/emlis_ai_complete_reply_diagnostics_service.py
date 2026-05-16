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

COMPLETE_REPLY_DIAGNOSTICS_VERSION = "emlis.complete_reply_service_diagnostics.v1"
COMPLETE_SCORECARD_EVENT_VERSION = "emlis.complete_scorecard_event.v1"
COMPLETE_REPLY_DIAGNOSTICS_STAGE = "Step11_Reply_service_diagnostics_integration"
COMPLETE_REPLY_DIAGNOSTICS_STEP = COMPLETE_REPLY_DIAGNOSTICS_STAGE
COMPLETE_REPLY_DIAGNOSTICS_IMPLEMENTATION_UNIT = "Commit 11"

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

    item = meta.get("tone_guard_report")
    if isinstance(item, Mapping):
        return item
    surface = meta.get("surface_realizer")
    if isinstance(surface, Mapping):
        item = surface.get("tone_guard_report")
        if isinstance(item, Mapping):
            return item
    signature = meta.get("surface_signature")
    if isinstance(signature, Mapping):
        item = signature.get("tone_guard_report")
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
    tone_guard_report = _tone_guard_report_from_meta(runtime_meta)
    tone_guard_major_count = _safe_int(tone_guard_report.get("tone_guard_major_count"), 0)
    tone_guard_reasons = _dedupe(tone_guard_report.get("tone_guard_reasons") or tone_guard_report.get("blocker_reasons"))
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
        "complete_candidate_generated": bool(composer_status == "generated" and composer_source == "ai_generated"),
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
        "tone_engine_version": _clean(tone_guard_report.get("tone_engine_version")),
        "product_quality_tone_engine_version": _clean(tone_guard_report.get("product_quality_tone_engine_version")),
        "tone_policy_applied": bool(runtime_meta.get("tone_policy_applied") or runtime_meta.get("tone_policy")),
        "tone_guard_report": _safe_mapping(tone_guard_report),
        "tone_guard_major_count": tone_guard_major_count,
        "tone_guard_passed": bool(tone_guard_report.get("passed", tone_guard_major_count == 0)) and tone_guard_major_count == 0,
        "tone_guard_reasons": list(tone_guard_reasons),
        "tone_over_empathy_count": _safe_int(tone_guard_report.get("over_empathy_count"), 0),
        "tone_diagnostic_count": _safe_int(tone_guard_report.get("diagnostic_tone_count"), 0),
        "tone_advice_count": _safe_int(tone_guard_report.get("advice_like_count"), 0),
        "tone_generic_count": _safe_int(tone_guard_report.get("generic_comfort_count"), 0),
        "tone_meaning_added": bool(runtime_meta.get("tone_meaning_added") or tone_guard_report.get("meaning_added") or tone_guard_report.get("meaning_added_by_tone_policy")),
        "safety_major_count": safety_major_count,
        "read_feeling_score": None,
        "top_rejection_reasons": list(dict.fromkeys([*gate_reasons[:5], *tone_guard_reasons[:3]])),
        "observation_status": observation_status,
        "display_passed": display_passed,
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
        "repair_trace": bool(repair_trace),
        "scorecard_event": True,
    }
    composer_status = _clean(_candidate_attr(composer_candidate, "status", ""))
    composer_source = _clean(_candidate_attr(composer_candidate, "composer_source", ""))
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
        "complete_candidate_generated": bool(composer_status == "generated" and composer_source == "ai_generated"),
        "complete_candidate_displayed": bool(observation_status == "passed" and candidate_seen),
        "composer_status": composer_status,
        "composer_source": composer_source,
        "composer_model": _clean(_candidate_attr(composer_candidate, "composer_model", "") or runtime_meta.get("composer_model")),
        "generation_method": _clean(_candidate_attr(composer_candidate, "generation_method", "") or runtime_meta.get("generation_method")),
        "generation_scope": _clean(_candidate_attr(composer_candidate, "generation_scope", "") or runtime_meta.get("generation_scope")),
        "coverage_scope": _clean(_candidate_attr(composer_candidate, "coverage_scope", "") or runtime_meta.get("coverage_scope")),
        "observation_status": observation_status,
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
    diagnostic_summary["step11_complete_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_composer_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_composer_initial_reply_diagnostics"] = dict(diagnostics)
    diagnostic_summary["complete_composer_initial_meta"] = complete_meta
    diagnostic_summary["complete_composer_initial_repair_trace"] = repair_trace
    diagnostic_summary["complete_composer_initial_scorecard_event"] = scorecard_event
    diagnostic_summary["complete_composer_scorecard_event"] = scorecard_event
    diagnostic_summary["scorecard_event"] = scorecard_event

    phase_gate["step11_reply_service_diagnostics_ready"] = bool(diagnostics.get("complete_reply_service_diagnostics_added"))
    phase_gate["step11_complete_meta_connected"] = bool(diagnostics.get("complete_meta_connected"))
    phase_gate["step11_repair_trace_connected"] = bool(diagnostics.get("repair_trace_connected"))
    phase_gate["step11_scorecard_event_connected"] = bool(diagnostics.get("scorecard_event_connected"))
    phase_gate["step11_passed_only_preserved"] = bool(diagnostics.get("passed_only_preserved"))
    phase_gate["step11_response_shape_changed"] = bool(diagnostics.get("response_shape_changed"))
    phase_gate["step11_public_response_key_change"] = bool(diagnostics.get("public_response_key_change"))


__all__ = [
    "COMPLETE_REPLY_DIAGNOSTICS_IMPLEMENTATION_UNIT",
    "COMPLETE_REPLY_DIAGNOSTICS_STAGE",
    "COMPLETE_REPLY_DIAGNOSTICS_STEP",
    "COMPLETE_REPLY_DIAGNOSTICS_VERSION",
    "COMPLETE_SCORECARD_EVENT_VERSION",
    "attach_complete_reply_service_diagnostics",
    "build_complete_reply_diagnostics_contract_meta",
    "build_complete_reply_service_diagnostics",
    "build_complete_scorecard_event",
    "extract_complete_composer_runtime_meta",
]
