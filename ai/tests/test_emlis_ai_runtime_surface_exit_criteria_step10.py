# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_observation_diagnostic_lockdown import (
    build_observation_diagnostic_lockdown,
    dump_observation_diagnostic,
)
from emlis_ai_runtime_surface_exit_criteria import (
    CASE_KIND_BROKEN_SURFACE,
    CASE_KIND_LOW_INFORMATION,
    CASE_KIND_NORMAL_INPUT,
    RUNTIME_SURFACE_EXIT_CRITERIA_VERSION,
    build_runtime_surface_exit_criteria_report,
    build_runtime_surface_exit_criteria_report_from_log_lines,
    build_runtime_surface_exit_criteria_summary,
    dump_runtime_surface_exit_criteria_report,
    extract_observation_diagnostic_lockdown_records_from_log_lines,
)

_BAD_DISPLAYED_TEXT = (
    "Emlisです。\n"
    "今までことが中心にあります。\n"
    "その中でも、大丈夫ことも見えています。\n"
    "その中でも、何かが重なっています。"
)
_SECRET_RAW_INPUT = "このraw inputはStep10 reportへ出してはいけない"


def _surface_step8_meta(*, passed: bool, action: str = "allow", grammar_count: int = 0, malformed_count: int = 0) -> dict:
    return {
        "version": "emlis.runtime_surface_diagnostics_scorecard.v1",
        "step8_runtime_surface_diagnostics_ready": True,
        "runtime_surface_diagnostics_scorecard_updated": True,
        "runtime_surface_pre_return_gate_evaluated": True,
        "runtime_surface_pre_return_gate_passed": passed,
        "runtime_surface_pre_return_gate_final_passed": passed,
        "runtime_surface_pre_return_gate_action": action,
        "runtime_surface_pre_return_gate_rejection_reasons": [] if passed else ["surface_template_major", "same_connector_run"],
        "runtime_surface_pre_return_gate_scorecard_connected": True,
        "surface_template_major": not passed,
        "surface_template_major_blocked": not passed,
        "surface_grammar_warning_count": grammar_count,
        "malformed_phrase_unit_blocked_count": malformed_count,
        "shallow_realizer_version": "shallow_surface_realizer.v2",
        "shallow_v2_used": True,
        "low_information_specificity_used": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _record(*, passed: bool, low_information: bool = False) -> dict:
    meta = {
        "observation_status": "passed" if passed else "rejected",
        "observation_trace_id": "step10-trace-low" if low_information else "step10-trace-passed" if passed else "step10-trace-blocked",
        "rejection_reasons": [] if passed else ["runtime_surface_pre_return_gate_failed"],
        "diagnostic_summary": {
            "observation_status": "passed" if passed else "rejected",
            "stage": "display",
            "primary_reason": "passed" if passed else "runtime_surface_pre_return_gate_failed",
            "display_rejection_reasons": [] if passed else ["runtime_surface_pre_return_gate_failed", "surface_template_major"],
            "complete_candidate_seen": True,
            "complete_candidate_generated": True,
            "complete_candidate_status": "generated",
            "complete_candidate_source": "ai_generated",
            "composer_status": "generated",
            "composer_source": "ai_generated",
            "coverage_scope": "low_information" if low_information else "current_input_core",
            "registry_resolution": {"connection_status": "connected"},
            "runtime_surface_step8_diagnostics": _surface_step8_meta(passed=passed, action="allow" if passed else "rerender_shallow_v2"),
            "gate_results": {
                "reader": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
                "grounding": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
                "template_echo": {"passed": True, "primary_reason": "passed", "rejection_reasons": []},
                "display": {
                    "passed": passed,
                    "primary_reason": "passed" if passed else "runtime_surface_pre_return_gate_failed",
                    "rejection_reasons": [] if passed else ["runtime_surface_pre_return_gate_failed"],
                },
            },
            "low_information_specificity_used": bool(low_information),
            "step6_low_information_specificity_ready": bool(low_information),
            "safe_anchor_count": 1 if low_information else 0,
            "uses_safe_anchor": bool(low_information),
        },
        # Hostile accidental raw payloads must not cross into the diagnostic row.
        "current_input": {"memo": _SECRET_RAW_INPUT},
    }
    return build_observation_diagnostic_lockdown(
        input_feedback_comment="Emlisです。\n今は、仕事で疲れたことが先に出ています。" if passed else "",
        input_feedback_meta=meta,
        emotion_log_id="emotion-step10-low" if low_information else "emotion-step10",
        created_at="2026-05-23T00:00:00Z",
    )


def test_step10_lockdown_exposes_exit_log_fields_for_displayed_clean_record() -> None:
    clean = _record(passed=True)

    assert clean["surface_template_major"] is False
    assert clean["surface_grammar_warning_count"] == 0
    assert clean["malformed_phrase_unit_blocked_count"] == 0
    assert clean["step10_runtime_surface_exit_criteria_ready"] is True
    assert clean["runtime_surface_exit_criteria_passed"] is True
    assert clean["runtime_surface_exit_criteria_outcome"] == "passed"

    dumped = dump_observation_diagnostic(clean)
    assert _SECRET_RAW_INPUT not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped


def test_step10_exit_criteria_summary_passes_for_normal_low_info_and_broken_surface_cases_meta_only() -> None:
    normal = _record(passed=True)
    low = _record(passed=True, low_information=True)
    broken = _record(passed=False)

    normal_case = build_runtime_surface_exit_criteria_report(
        diagnostic_record=normal,
        displayed_comment_text="Emlisです。\n今は、仕事で疲れたことが先に出ています。",
        case_kind=CASE_KIND_NORMAL_INPUT,
    )
    low_case = build_runtime_surface_exit_criteria_report(
        diagnostic_record=low,
        displayed_comment_text="Emlisです。\n今は、『大丈夫かどうか』を確かめたい感じが先に出ています。",
        case_kind=CASE_KIND_LOW_INFORMATION,
    )
    broken_case = build_runtime_surface_exit_criteria_report(
        diagnostic_record=broken,
        case_kind=CASE_KIND_BROKEN_SURFACE,
    )
    summary = build_runtime_surface_exit_criteria_summary([normal_case, low_case, broken_case])

    assert normal_case["passed"] is True
    assert low_case["passed"] is True
    assert broken_case["passed"] is True
    assert summary["version"] == RUNTIME_SURFACE_EXIT_CRITERIA_VERSION
    assert summary["passed"] is True
    assert summary["normal_input_display_confirmed"] is True
    assert summary["low_information_branch_confirmed"] is True
    assert summary["broken_surface_blocked_confirmed"] is True
    assert summary["public_contract_unchanged"] is True

    dumped = dump_runtime_surface_exit_criteria_report(summary)
    assert _SECRET_RAW_INPUT not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped


def test_step10_exit_criteria_blocks_displayed_template_major_grammar_or_malformed_counts() -> None:
    clean = _record(passed=True)
    clean["surface_template_major"] = True
    clean["surface_grammar_warning_count"] = 1
    clean["malformed_phrase_unit_blocked_count"] = 1

    report = build_runtime_surface_exit_criteria_report(diagnostic_record=clean, case_kind=CASE_KIND_NORMAL_INPUT)

    assert report["passed"] is False
    assert "displayed_surface_template_major" in report["blockers"]
    assert "displayed_surface_grammar_warning" in report["blockers"]
    assert "displayed_malformed_phrase_unit_blocked_count" in report["blockers"]


def test_step10_exit_criteria_scans_displayed_text_without_returning_public_body() -> None:
    clean = _record(passed=True)
    report = build_runtime_surface_exit_criteria_report(
        diagnostic_record=clean,
        displayed_comment_text=_BAD_DISPLAYED_TEXT,
        case_kind=CASE_KIND_NORMAL_INPUT,
    )

    assert report["passed"] is False
    assert "displayed_forbidden_surface_pattern" in report["blockers"]
    assert len(report["forbidden_surface_pattern_ids"]) >= 3
    dumped = dump_runtime_surface_exit_criteria_report(report)
    assert "malformed_nominalization_imamade_koto" in dumped
    assert _BAD_DISPLAYED_TEXT not in dumped
    assert "今までこと" not in dumped
    assert "大丈夫こと" not in dumped
    assert "その中でも" not in dumped


def test_step10_exit_criteria_from_render_log_lines_uses_lockdown_json_rows() -> None:
    normal = _record(passed=True)
    low = _record(passed=True, low_information=True)
    broken = _record(passed=False)
    lines = [
        "INFO healthcheck ok",
        "INFO emlis_observation_diagnostic_lockdown " + dump_observation_diagnostic(normal),
        "INFO emlis_observation_diagnostic_lockdown " + dump_observation_diagnostic(low),
        "WARN emlis_observation_diagnostic_lockdown " + dump_observation_diagnostic(broken),
    ]

    parsed = extract_observation_diagnostic_lockdown_records_from_log_lines(lines)
    summary = build_runtime_surface_exit_criteria_report_from_log_lines(
        log_lines=lines,
        displayed_comment_text_by_trace_id={
            normal["trace_id"]: "Emlisです。\n今は、仕事で疲れたことが先に出ています。",
            low["trace_id"]: "Emlisです。\n今は、『大丈夫かどうか』を確かめたい感じが先に出ています。",
        },
    )

    assert len(parsed) == 3
    assert summary["passed"] is True
    assert summary["record_count"] == 3
    assert summary["normal_input_display_confirmed"] is True
    assert summary["low_information_branch_confirmed"] is True
    assert summary["broken_surface_blocked_confirmed"] is True

    dumped = json.dumps(summary, ensure_ascii=False)
    assert _SECRET_RAW_INPUT not in dumped
    assert '"displayed_comment_text"' not in dumped
