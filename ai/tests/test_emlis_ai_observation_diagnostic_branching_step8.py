from __future__ import annotations

import json

import pytest

from emlis_ai_observation_diagnostic_branching import (
    BRANCHING_VERSION,
    attach_observation_diagnostic_next_branch,
    known_observation_branch_classifications,
    resolve_observation_diagnostic_next_branch,
)
from emlis_ai_observation_diagnostic_compare import (
    BACKEND_LOG_PREFIX,
    FRONTEND_LOG_PREFIX,
    build_comparison_from_log_lines,
    dump_observation_diagnostic_comparison,
    format_observation_diagnostic_comparison_markdown,
)

_SECRET_COMMENT = "これは Step8 分岐ログへ出してはいけない観測本文です"


def _gate(passed: bool, reason: str = "") -> dict:
    return {
        "passed": passed,
        "primary_reason": "passed" if passed else reason,
        "rejection_reasons": [] if passed else [reason],
    }


def _backend_record(
    *,
    trace_id: str = "emlisobs-step8-left",
    emotion_log_id: str = "emotion-step8-left",
    status: str = "rejected",
    comment_len: int = 0,
    stage: str = "grounding",
    reason: str = "unsupported_sentence",
    failed_gate: str = "grounding",
    candidate_generated: bool = True,
) -> dict:
    gates = {
        "reader": _gate(True),
        "grounding": _gate(True),
        "template_echo": _gate(True),
        "display": _gate(status == "passed", "" if status == "passed" else reason),
    }
    if status != "passed" and failed_gate in gates:
        gates[failed_gate] = _gate(False, reason)
        gates["display"] = _gate(False, reason)
    return {
        "version": "emlis.observation_diagnostic_lockdown.v1",
        "source": "backend_emotion_submit",
        "emotion_log_id": emotion_log_id,
        "created_at": "2026-05-17T02:35:05Z",
        "trace_id": trace_id,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "stage": stage,
        "primary_reason": reason,
        "secondary_reasons": [] if status == "passed" else [reason],
        "rejection_reasons": [] if status == "passed" else [reason],
        "coverage_group": "step8_branch_fixture",
        "composer_status": "generated" if candidate_generated else "unavailable",
        "composer_source": "ai_generated" if candidate_generated else "unavailable",
        "composer_client_resolution": {"connection_status": "connected"},
        "candidate": {
            "seen": candidate_generated,
            "generated": candidate_generated,
            "generated_before_display_gate": candidate_generated,
            "status": "generated" if candidate_generated else "unavailable",
            "source": "ai_generated" if candidate_generated else "unavailable",
        },
        "evidence_counts": {
            "evidence_span_count": 2,
            "used_evidence_span_count": 1 if candidate_generated else 0,
            "used_phrase_unit_count": 1 if candidate_generated else 0,
            "used_relation_count": 1 if candidate_generated else 0,
        },
        "gate_results": gates,
        "display_rejection_reasons": [] if status == "passed" else [reason],
        "self_repair": {
            "attempted": failed_gate == "grounding",
            "status": "attempted" if failed_gate == "grounding" else "not_attempted",
            "repair_trace_count": 1 if failed_gate == "grounding" else 0,
            "aborted_count": 0,
            "abort_reasons": [],
        },
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _frontend_record(*, trace_id: str, emotion_log_id: str, status: str, comment_len: int, modal_opened: bool) -> dict:
    return {
        "version": "emlis.frontend_observation_diagnostic.v1",
        "source": "rn_input_screen",
        "emotion_log_id": emotion_log_id,
        "trace_id": trace_id,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "modal_opened": modal_opened,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _line(prefix: str, record: dict) -> str:
    return f"2026-05-17 INFO {prefix}{json.dumps(record, ensure_ascii=False, sort_keys=True)}"


def test_step8_branch_table_covers_all_expected_classifications() -> None:
    expected = {
        "backend_exception_or_timeout",
        "pre_connection_stop",
        "candidate_missing",
        "candidate_generated_but_reader_rejected",
        "candidate_generated_but_grounding_rejected",
        "candidate_generated_but_template_rejected",
        "candidate_generated_but_display_rejected",
        "passed_backend_frontend_hidden",
        "passed_displayed",
        "unclassified_non_display",
    }

    assert expected.issubset(set(known_observation_branch_classifications()))
    for classification in expected:
        branch = resolve_observation_diagnostic_next_branch(classification)
        assert branch["version"] == BRANCHING_VERSION
        assert branch["classification"] == classification
        assert branch["target_area"]
        assert branch["touch_files"]
        assert branch["do_not_touch"]
        assert branch["raw_input_included"] is False
        assert branch["comment_text_included"] is False


def test_step8_grounding_branch_locks_sentence_binding_without_template_or_gate_relaxation() -> None:
    branch = resolve_observation_diagnostic_next_branch(
        {"next_action_classification": "candidate_generated_but_grounding_rejected", "first_divergence_layer": "grounding"}
    )

    assert branch["target_layer"] == "grounding"
    assert branch["target_area"] == "sentence binding / evidence binding / unsupported_sentence"
    assert branch["ready_for_cause_repair"] is True
    assert branch["branch_locked"] is True
    assert "complete_grounding_binding" in branch["touch_files"]
    assert "テンプレ文追加" in branch["do_not_touch"]
    assert any("unsupported_sentence" in item for item in branch["forbidden_actions"])


def test_step8_unclassified_requires_diagnostic_enrichment_before_repair() -> None:
    branch = resolve_observation_diagnostic_next_branch({"classification": "unclassified_non_display"})

    assert branch["target_layer"] == "diagnostic"
    assert branch["ready_for_cause_repair"] is False
    assert branch["requires_diagnostic_enrichment"] is True
    assert "SelfRepair" in branch["do_not_touch"]
    assert any("原因未分類" in item for item in branch["forbidden_actions"])


def test_step8_passed_displayed_routes_to_scorecard_not_non_display_repair() -> None:
    branch = resolve_observation_diagnostic_next_branch({"classification": "passed_displayed", "first_divergence_layer": "passed"})

    assert branch["terminal"] is True
    assert branch["ready_for_cause_repair"] is False
    assert branch["target_area"] == "scorecard / coverage suite / blind QA"
    assert "非表示修正扱いにしない" in branch["do_not_touch"]


def test_step8_attach_branch_to_1135_1136_comparison_report() -> None:
    left_backend = _backend_record(
        trace_id="emlisobs-step8-1135",
        emotion_log_id="emotion-step8-1135",
        status="rejected",
        comment_len=0,
        stage="grounding",
        reason="unsupported_sentence",
        failed_gate="grounding",
    )
    left_frontend = _frontend_record(
        trace_id="emlisobs-step8-1135",
        emotion_log_id="emotion-step8-1135",
        status="rejected",
        comment_len=0,
        modal_opened=False,
    )
    right_backend = _backend_record(
        trace_id="emlisobs-step8-1136",
        emotion_log_id="emotion-step8-1136",
        status="passed",
        comment_len=120,
        stage="display",
        reason="passed",
    )
    right_frontend = _frontend_record(
        trace_id="emlisobs-step8-1136",
        emotion_log_id="emotion-step8-1136",
        status="passed",
        comment_len=120,
        modal_opened=True,
    )

    report = build_comparison_from_log_lines(
        [
            _line(BACKEND_LOG_PREFIX, left_backend),
            _line(FRONTEND_LOG_PREFIX, left_frontend),
            _line(BACKEND_LOG_PREFIX, right_backend),
            _line(FRONTEND_LOG_PREFIX, right_frontend),
        ]
    )

    assert report["first_divergence_layer"] == "grounding"
    assert report["next_action_classification"] == "candidate_generated_but_grounding_rejected"
    assert report["next_action_branch"]["target_layer"] == "grounding"
    assert report["next_action_branch"]["branch_locked"] is True
    assert report["ready_for_cause_repair"] is True
    assert report["next_action_target"] == "sentence binding / evidence binding / unsupported_sentence"

    markdown = format_observation_diagnostic_comparison_markdown(report)
    assert "branch_locked: True" in markdown
    assert "ready_for_cause_repair: True" in markdown
    assert "touch_files: complete_grounding_binding" in markdown

    dumped = dump_observation_diagnostic_comparison(report)
    assert _SECRET_COMMENT not in dumped
    assert json.loads(dumped)["next_action_branch"]["comment_text_included"] is False


def test_step8_attach_rejects_forbidden_payload_keys() -> None:
    with pytest.raises(ValueError):
        attach_observation_diagnostic_next_branch(
            {
                "version": "emlis.observation_diagnostic_comparison.v1",
                "next_action_classification": "candidate_generated_but_grounding_rejected",
                "commentText": _SECRET_COMMENT,
            }
        )
