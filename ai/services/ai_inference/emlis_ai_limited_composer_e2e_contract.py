# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 10 E2E display-contract meta for EmlisAI limited Composer extension.

This module is meta-only. It does not relax any gate, does not create user-facing
text, does not read raw user input, and does not rename DB/API/response keys.
"""

from typing import Any, Dict, Mapping

_E2E_DISPLAY_CONTRACT_VERSION = "emlis.limited_composer_e2e_display_contract.v1"
_E2E_DISPLAY_CONTRACT_STEP = "10_E2E_test_fixed"
_DISPLAY_CONTRACT_NAME = "input_feedback.comment_text_passed_only"
_ALLOWED_STATUSES = {"passed", "rejected", "unavailable", "safety_blocked"}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any) -> bool:
    return bool(value)


def _dedupe(values: Any) -> list[str]:
    out: list[str] = []
    for value in list(values or []):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def build_limited_composer_e2e_display_contract(
    *,
    observation_status: Any = "",
    comment_text: Any = "",
    diagnostic_summary: Mapping[str, Any] | None = None,
    gate_trace: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return the Step 10 passed-only E2E contract meta.

    The contract is intentionally narrow: user-visible comment_text may be
    non-empty only when observation_status is ``passed`` and the Display Gate
    has allowed the text. Non-passed statuses must preserve fail-closed empty
    comment_text.
    """

    summary = _as_mapping(diagnostic_summary)
    trace = _as_mapping(gate_trace)
    display_trace = _as_mapping(trace.get("display_gate") or trace.get("display") or {})
    gate_results = _as_mapping(summary.get("gate_results"))
    display_gate_result = _as_mapping(gate_results.get("display"))
    display_gate_diagnostics = _as_mapping(display_gate_result.get("diagnostics"))

    status = _clean(observation_status or summary.get("observation_status"))
    if status not in _ALLOWED_STATUSES:
        status = "unavailable"

    text_present = bool(_clean(comment_text))
    display_allowed = bool(
        summary.get("comment_text_allowed")
        or display_trace.get("comment_text_allowed")
        or display_gate_diagnostics.get("comment_text_allowed")
    )
    display_gate_passed = bool(
        display_trace.get("passed")
        or display_gate_result.get("passed")
        or (status == "passed" and display_allowed and text_present)
    )

    passed_status = status == "passed"
    passed_text_visible = bool(passed_status and display_allowed and display_gate_passed and text_present)
    non_passed_suppressed = bool((not passed_status) and (not text_present) and (not display_allowed))

    blockers: list[str] = []
    if passed_status:
        if not display_gate_passed:
            blockers.append("passed_without_display_gate_pass")
        if not display_allowed:
            blockers.append("passed_without_comment_text_allowed")
        if not text_present:
            blockers.append("passed_without_comment_text")
    else:
        if text_present:
            blockers.append("non_passed_comment_text_exposed")
        if display_allowed:
            blockers.append("non_passed_comment_text_allowed")
    if not isinstance(summary, Mapping) or not summary:
        blockers.append("diagnostic_summary_missing")
    if not gate_results:
        blockers.append("gate_results_missing")

    scorecard = _as_mapping(
        summary.get("step9_scorecard_harness")
        or summary.get("limited_composer_scorecard_harness")
        or summary.get("scorecard_harness")
    )
    binding_diagnostic = _as_mapping(summary.get("binding_diagnostic"))
    relation_taxonomy = _as_mapping(
        binding_diagnostic.get("relation_taxonomy")
        or summary.get("relation_taxonomy")
        or _as_mapping(summary.get("composer_diagnostic")).get("relation_taxonomy")
    )

    return {
        "version": _E2E_DISPLAY_CONTRACT_VERSION,
        "step": _E2E_DISPLAY_CONTRACT_STEP,
        "target_step": _E2E_DISPLAY_CONTRACT_STEP,
        "contract_name": _DISPLAY_CONTRACT_NAME,
        "display_contract": "input_feedback.comment_text is visible only when observation_status=passed and text exists",
        "observation_status": status,
        "comment_text_present": text_present,
        "comment_text_allowed": display_allowed,
        "comment_text_exposed": text_present,
        "display_gate_passed": display_gate_passed,
        "passed_status": passed_status,
        "passed_comment_text_visible": passed_text_visible,
        "non_passed_comment_text_suppressed": non_passed_suppressed,
        "passed_only_contract_passed": not blockers,
        "contract_passed": not blockers,
        "release_blockers": blockers,
        "limited_extension_exit_gate_step10_passed": bool(not blockers),
        "eligible_for_limited_extension_exit": False,
        "diagnostic_summary_present": bool(summary),
        "gate_results_present": bool(gate_results),
        "scorecard_harness_present": bool(scorecard),
        "scorecard_ready": bool(scorecard.get("ready") or scorecard.get("scorecard_ready")),
        "binding_present": bool(summary.get("binding_present") or binding_diagnostic.get("binding_present")),
        "binding_missing": bool(summary.get("binding_missing") or binding_diagnostic.get("binding_missing")),
        "binding_count": int(summary.get("binding_count") or binding_diagnostic.get("binding_count") or 0),
        "expected_binding_count": int(summary.get("expected_binding_count") or binding_diagnostic.get("expected_binding_count") or 0),
        "relation_taxonomy_present": bool(relation_taxonomy or binding_diagnostic.get("relation_types") or summary.get("relation_types")),
        "raw_input_included": False,
        "raw_input_required_for_debug": False,
        "input_specific_template_added": False,
        "fixed_completion_template_added": False,
        "display_gate_relaxed": False,
        "reader_grounding_template_relaxed": False,
        "db_api_rename_performed": False,
        "response_key_rename_performed": False,
        "frontend_contract_mutated": False,
        "safe_to_attach_to_meta": True,
    }


build_step10_e2e_display_contract = build_limited_composer_e2e_display_contract


__all__ = [
    "build_limited_composer_e2e_display_contract",
    "build_step10_e2e_display_contract",
]
