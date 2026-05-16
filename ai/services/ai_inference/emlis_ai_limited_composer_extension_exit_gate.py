# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 11 E2E exit-gate meta for the EmlisAI limited Composer extension.

This module is diagnostic / release meta only.  It does not generate text, does
not read raw user input, does not relax Reader / Grounding / Template / Display
Gate, and does not rename any DB / API / response-key contract.
"""

from typing import Any, Dict, Iterable, Mapping

_STEP11_EXIT_GATE_VERSION = "emlis.limited_composer_extension_e2e_exit_gate.v1"
_STEP11_EXIT_GATE_STEP = "11_E2E_test_fixed"
_EXIT_GATE_NAME = "limited_composer_extension_exit_gate"
_ALLOWED_STATUSES = {"passed", "rejected", "unavailable", "safety_blocked"}
_REQUIRED_GATES = ("reader", "grounding", "template_echo", "display")
_PREVIOUS_STEP_KEYS = {
    "step0_baseline": ("step0_baseline", "limited_composer_extension_baseline"),
    "step1_connection_visibility": ("step1_connection_visibility", "connection_visibility", "limited_composer_connection_visibility"),
    "step2_diagnostic_summary_extension": ("step2_diagnostic_summary_extension", "diagnostic_summary_v2", "limited_composer_diagnostic_summary_extension"),
    "step3_sentence_binding": ("binding_diagnostic",),
    "step4_phrase_unit_material_quality": ("phrase_unit_material_quality", "step4_phrase_unit_material_quality"),
    "step5_relation_taxonomy": ("relation_taxonomy", "step5_relation_taxonomy"),
    "step6_binding_aware_grounding": ("binding_aware_grounding",),
    "step7_gate_binding_reflection": ("gate_binding_reflection", "step7_gate_binding_reflection"),
    "step8_limited_surface_realizer": ("limited_surface_realizer", "limited_surface_realizer_stabilization", "step8_limited_surface_realizer_stabilization"),
    "step9_scorecard_harness": ("step9_scorecard_harness", "limited_composer_scorecard_harness", "scorecard_harness"),
    "step10_e2e_display_contract": ("step10_e2e_display_contract", "limited_composer_e2e_display_contract", "e2e_display_contract"),
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any) -> bool:
    return bool(value)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _first_mapping(source: Mapping[str, Any], keys: Iterable[str]) -> Mapping[str, Any]:
    for key in keys:
        value = source.get(key)
        if isinstance(value, Mapping) and value:
            return value
    return {}


def _previous_step_presence(summary: Mapping[str, Any], gate_results: Mapping[str, Any]) -> tuple[Dict[str, bool], list[str]]:
    presence: Dict[str, bool] = {}
    missing: list[str] = []
    binding_diag = _as_mapping(summary.get("binding_diagnostic"))
    composer_diag = _as_mapping(summary.get("composer_diagnostic"))
    for step_name, keys in _PREVIOUS_STEP_KEYS.items():
        present = bool(_first_mapping(summary, keys) or _first_mapping(composer_diag, keys) or _first_mapping(binding_diag, keys))
        if step_name == "step4_phrase_unit_material_quality" and not present:
            # Step 4 is surfaced in composer meta on generated responses.  For
            # unavailable pre-connection responses there is no material yet, so
            # the presence check is satisfied by the Step 2 binding diagnostic
            # saying no candidate body exists.
            present = bool(binding_diag and not _bool(binding_diag.get("candidate_comment_text_present")))
        if step_name == "step5_relation_taxonomy" and not present:
            relation_meta = _as_mapping(binding_diag.get("relation_taxonomy") or binding_diag.get("step5_relation_taxonomy"))
            present = bool(relation_meta) or (binding_diag and not _bool(binding_diag.get("candidate_comment_text_present")))
        if step_name == "step6_binding_aware_grounding" and not present:
            grounding_gate = _as_mapping(gate_results.get("grounding"))
            present = bool(
                grounding_gate.get("step6_binding_aware_grounding")
                or grounding_gate.get("binding_aware_grounding")
                or grounding_gate.get("binding_present") is not None
            )
        if step_name == "step7_gate_binding_reflection" and not present:
            present = any(
                _as_mapping(gate_results.get(gate)).get("step7_gate_binding_reflection")
                or _as_mapping(gate_results.get(gate)).get("binding_present") is not None
                for gate in _REQUIRED_GATES
            )
        if step_name == "step8_limited_surface_realizer" and not present:
            # Same as Step 4: unavailable pre-connection has no realizer pass.
            present = bool(binding_diag and not _bool(binding_diag.get("candidate_comment_text_present")))
        presence[step_name] = bool(present)
        if not present:
            missing.append(step_name)
    return presence, missing


def _gate_contract(summary: Mapping[str, Any]) -> tuple[Dict[str, Dict[str, Any]], list[str], bool]:
    gate_results = _as_mapping(summary.get("gate_results"))
    rows: Dict[str, Dict[str, Any]] = {}
    missing: list[str] = []
    trace_has_binding = False
    for gate in _REQUIRED_GATES:
        row = _as_mapping(gate_results.get(gate))
        if not row:
            missing.append(gate)
            rows[gate] = {"present": False, "passed": False, "binding_trace_present": False}
            continue
        binding_trace_present = any(key in row for key in ("binding_used", "binding_present", "binding_missing", "binding_count"))
        trace_has_binding = bool(trace_has_binding or binding_trace_present)
        rows[gate] = {
            "present": True,
            "passed": bool(row.get("passed")),
            "primary_reason": _clean(row.get("primary_reason") or row.get("first_failed_reason")),
            "rejection_reasons": list(row.get("rejection_reasons") or []),
            "binding_trace_present": binding_trace_present,
            "binding_present": bool(row.get("binding_present")),
            "binding_used": bool(row.get("binding_used")),
            "binding_missing": bool(row.get("binding_missing")),
            "binding_count": _safe_int(row.get("binding_count")),
            "expected_binding_count": _safe_int(row.get("expected_binding_count")),
            "raw_input_included": False,
        }
    return rows, missing, trace_has_binding


def build_limited_composer_extension_e2e_exit_gate(
    *,
    diagnostic_summary: Mapping[str, Any] | None = None,
    step10_display_contract: Mapping[str, Any] | None = None,
    gate_trace: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build Step 11 meta that fixes the limited-extension E2E Exit Gate.

    This is intentionally stricter than the Step 10 passed-only display contract:
    Step 10 proves non-passed text is suppressed.  Step 11 proves the limited
    Composer extension has enough end-to-end metadata to decide whether a
    passed eligible fixture is ready to become the entrance to the complete
    Composer initial version.
    """

    summary = _as_mapping(diagnostic_summary)
    step10 = _as_mapping(
        step10_display_contract
        or summary.get("step10_e2e_display_contract")
        or summary.get("limited_composer_e2e_display_contract")
        or summary.get("e2e_display_contract")
    )
    gate_results = _as_mapping(summary.get("gate_results"))
    binding = _as_mapping(summary.get("binding_diagnostic"))
    scorecard = _as_mapping(
        summary.get("step9_scorecard_harness")
        or summary.get("limited_composer_scorecard_harness")
        or summary.get("scorecard_harness")
    )

    status = _clean(summary.get("observation_status") or step10.get("observation_status"))
    if status not in _ALLOWED_STATUSES:
        status = "unavailable"
    passed_status = status == "passed"

    primary_reason = _clean(summary.get("primary_reason"))
    failed_stage = _clean(summary.get("failed_stage") or summary.get("stage"))
    coverage_group = _clean(summary.get("coverage_group"))
    binding_count = _safe_int(summary.get("binding_count") or binding.get("binding_count"))
    expected_binding_count = _safe_int(summary.get("expected_binding_count") or binding.get("expected_binding_count"))
    binding_present = bool(summary.get("binding_present") or binding.get("binding_present") or binding_count > 0)
    binding_missing = bool(summary.get("binding_missing") or binding.get("binding_missing") or (expected_binding_count and binding_count < expected_binding_count))
    all_body_sentences_bound = bool(expected_binding_count > 0 and binding_count == expected_binding_count and not binding_missing)

    relation_meta = _as_mapping(
        summary.get("relation_taxonomy")
        or summary.get("step5_relation_taxonomy")
        or binding.get("relation_taxonomy")
        or binding.get("step5_relation_taxonomy")
        or _as_mapping(summary.get("composer_diagnostic")).get("relation_taxonomy")
    )
    relation_types = _dedupe(
        binding.get("relation_types")
        or summary.get("relation_types")
        or relation_meta.get("canonical_relation_types")
        or relation_meta.get("relation_types")
        or []
    )
    relation_taxonomy_present = bool(relation_meta or relation_types)
    relation_not_expressed_traceable = bool(
        relation_taxonomy_present
        or binding.get("relation_not_expressed_traceable")
        or _as_mapping(relation_meta).get("relation_not_expressed_traceable")
    )

    gate_rows, missing_gates, gate_binding_trace_present = _gate_contract(summary)
    previous_step_presence, previous_steps_missing = _previous_step_presence(summary, gate_results)

    step10_contract_passed = bool(step10.get("contract_passed") or step10.get("passed_only_contract_passed"))
    step10_blockers = _dedupe(step10.get("release_blockers") or [])
    scorecard_ready = bool(scorecard.get("ready") or scorecard.get("scorecard_ready"))
    next_tasks_visible = bool(scorecard.get("next_tasks_visible") or scorecard.get("groups_needing_attention") is not None)
    binding_sentence_coverage_rate = _safe_float(
        _as_mapping(scorecard.get("binding_coverage")).get("binding_sentence_coverage_rate")
        or _as_mapping(scorecard.get("aggregate")).get("totals", {}).get("binding_sentence_coverage_rate")
        or 0.0
    )

    blockers: list[str] = []
    if not summary:
        blockers.append("diagnostic_summary_missing")
    if not primary_reason:
        blockers.append("primary_reason_missing")
    if not failed_stage:
        blockers.append("failed_stage_missing")
    if not coverage_group:
        blockers.append("coverage_group_missing")
    if missing_gates:
        blockers.append("gate_results_missing")
    if previous_steps_missing:
        blockers.append("previous_step_meta_missing")
    if not step10_contract_passed:
        blockers.append("step10_display_contract_not_passed")
    blockers.extend(step10_blockers)

    # Passed eligible output must have the full limited-extension evidence chain.
    if passed_status:
        if not binding_present:
            blockers.append("sentence_binding_missing")
        if binding_missing:
            blockers.append("sentence_binding_incomplete")
        if not all_body_sentences_bound:
            blockers.append("body_sentence_binding_count_mismatch")
        if not relation_taxonomy_present:
            blockers.append("relation_taxonomy_missing")
        if not relation_not_expressed_traceable:
            blockers.append("relation_not_expressed_not_traceable")
        if not gate_binding_trace_present:
            blockers.append("gate_binding_trace_missing")
        if not scorecard_ready:
            blockers.append("scorecard_not_ready")
        if not next_tasks_visible:
            blockers.append("scorecard_next_tasks_not_visible")

    non_blocking_reasons: list[str] = []
    if not passed_status:
        non_blocking_reasons.append("not_a_passed_exit_candidate")
    if status in {"rejected", "unavailable", "safety_blocked"} and step10_contract_passed:
        non_blocking_reasons.append("fail_closed_contract_preserved")

    release_blockers = _dedupe(blockers)
    e2e_contract_passed = bool(not release_blockers or (not passed_status and step10_contract_passed and not step10_blockers))
    limited_extension_exit_gate_ready = bool(passed_status and not release_blockers)

    return {
        "version": _STEP11_EXIT_GATE_VERSION,
        "step": _STEP11_EXIT_GATE_STEP,
        "target_step": _STEP11_EXIT_GATE_STEP,
        "exit_gate_name": _EXIT_GATE_NAME,
        "phase": "limited_composer_extension",
        "purpose": "fix_limited_composer_extension_e2e_exit_gate_before_complete_composer_initial",
        "observation_status": status,
        "primary_reason": primary_reason,
        "failed_stage": failed_stage,
        "coverage_group": coverage_group,
        "previous_step_presence": previous_step_presence,
        "previous_steps_missing": previous_steps_missing,
        "all_previous_step_meta_present": not previous_steps_missing,
        "gate_contract_rows": gate_rows,
        "required_gate_results_present": not missing_gates,
        "missing_gate_results": missing_gates,
        "gate_binding_trace_present": gate_binding_trace_present,
        "step10_display_contract_passed": step10_contract_passed,
        "step10_release_blockers": step10_blockers,
        "passed_only_display_contract_preserved": step10_contract_passed and not step10_blockers,
        "binding_present": binding_present,
        "binding_missing": binding_missing,
        "binding_count": binding_count,
        "expected_binding_count": expected_binding_count,
        "all_body_sentences_bound": all_body_sentences_bound,
        "binding_sentence_coverage_rate": binding_sentence_coverage_rate,
        "relation_taxonomy_present": relation_taxonomy_present,
        "relation_not_expressed_traceable": relation_not_expressed_traceable,
        "relation_types": relation_types,
        "scorecard_ready": scorecard_ready,
        "scorecard_present": bool(scorecard),
        "scorecard_next_tasks_visible": next_tasks_visible,
        "e2e_contract_passed": e2e_contract_passed,
        "contract_passed": e2e_contract_passed,
        "limited_extension_exit_gate_ready": limited_extension_exit_gate_ready,
        "limited_composer_extension_complete": limited_extension_exit_gate_ready,
        "ready_for_complete_composer_initial": limited_extension_exit_gate_ready,
        "release_blockers": release_blockers,
        "non_blocking_reasons": _dedupe(non_blocking_reasons),
        "raw_input_included": False,
        "raw_input_required_for_debug": False,
        "input_specific_template_added": False,
        "fixed_completion_template_added": False,
        "role_completion_template_added": False,
        "display_gate_relaxed": False,
        "reader_grounding_template_relaxed": False,
        "db_api_rename_performed": False,
        "response_key_rename_performed": False,
        "frontend_contract_mutated": False,
        "safe_to_attach_to_meta": True,
    }


build_step11_e2e_exit_gate = build_limited_composer_extension_e2e_exit_gate


__all__ = [
    "build_limited_composer_extension_e2e_exit_gate",
    "build_step11_e2e_exit_gate",
]
