from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_connection import (
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION,
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP,
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP,
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP,
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP,
    ProductQualityMeasurementConnectionError,
    assert_product_quality_measurement_connection_meta_only,
    build_complete_product_quality_blind_qa_input_candidates,
    build_complete_product_quality_measurement_connection,
    build_complete_product_quality_measurement_next_action_routing_summary,
    build_product_quality_scorecard_events_from_joined_rows,
    dump_complete_product_quality_measurement_connection,
    dump_product_quality_measurement_connection_payload,
    normalize_observation_row_to_product_quality_event,
    normalize_observation_rows_to_product_quality_events,
)
from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER
from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard

_SECRET_COMMENT = "これはscorecard eventへ出してはいけない観測本文です"
_SECRET_RAW_INPUT = "これはscorecard eventへ出してはいけない入力本文です"


def _joined_row(
    *,
    trace_id: str = "emlisobs-step3",
    emotion_log_id: str = "emotion-step3",
    backend_status: str = "passed",
    backend_len: int = 120,
    frontend_joined: bool = True,
    modal_opened: bool | None = True,
    display_confirmed: bool = True,
    classification: str = "passed_displayed",
    measurement_classification: str = "passed_displayed",
    primary_reason: str = "passed",
    display_blockers: list[str] | None = None,
    coverage_group: str = "short_daily",
) -> dict:
    return {
        "trace_id": trace_id,
        "emotion_log_id": emotion_log_id,
        "coverage_group": coverage_group,
        "backend_status": backend_status,
        "backend_len": backend_len,
        "backend_comment_text_present": backend_len > 0,
        "backend_public_passed": backend_status == "passed" and backend_len > 0,
        "rn_status": "passed" if frontend_joined and backend_status == "passed" else backend_status,
        "rn_len": backend_len if frontend_joined else None,
        "frontend_joined": frontend_joined,
        "frontend_join_status": "joined" if frontend_joined else "missing",
        "modal_opened": modal_opened,
        "display_confirmed": display_confirmed,
        "product_gate_display_counted": display_confirmed,
        "scorecard_passed_display_count": 1 if display_confirmed else 0,
        "diagnostic_capture_status": "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured",
        "classification": classification,
        "measurement_classification": measurement_classification,
        "primary_reason": primary_reason,
        "stage": "display",
        "candidate_generated": True,
        "reader": "pass",
        "grounding": "pass",
        "template": "pass",
        "display": "pass" if backend_status == "passed" else "fail",
        "reader_reason": "passed",
        "grounding_reason": "passed",
        "template_reason": "passed",
        "display_reason": primary_reason,
        "display_count_blockers": list(display_blockers or []),
        "binding_supported_sentence_count": 1 if backend_status == "passed" and display_confirmed else 0,
        "expected_binding_count": 1 if backend_status == "passed" else 0,
        "join_semantics": {
            "measurement_classification": measurement_classification,
            "display_count_blockers": list(display_blockers or []),
        "binding_supported_sentence_count": 1 if backend_status == "passed" and display_confirmed else 0,
        "expected_binding_count": 1 if backend_status == "passed" else 0,
            "display_confirmed": display_confirmed,
            "scorecard_passed_display_count": 1 if display_confirmed else 0,
            "raw_input_included": False,
            "comment_text_included": False,
        },
        "raw_input_included": False,
        "comment_text_included": False,
    }


def test_step3_display_confirmed_row_becomes_scorecard_display_event() -> None:
    event = normalize_observation_row_to_product_quality_event(_joined_row())

    assert event["version"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION
    assert event["measurement_connection_version"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_CONNECTION_VERSION
    assert event["scorecard_event_adapter_ready"] is True
    assert event["eligible_for_scorecard"] is True
    assert event["eligible_count"] == 1
    assert event["observation_status"] == "passed"
    assert event["backend_observation_status"] == "passed"
    assert event["display_confirmed"] is True
    assert event["passed_display_count"] == 1
    assert event["scorecard_passed_display_count"] == 1
    assert event["top_rejection_reasons"] == []
    assert event["raw_input_included"] is False
    assert event["comment_text_included"] is False

    scorecard = build_complete_product_quality_scorecard(scorecard_events=[event])
    assert scorecard["eligible_count"] == 1
    assert scorecard["passed_display_count"] == 1
    assert scorecard["display_reach_rate"] == 1.0


def test_step3_backend_passed_without_frontend_stays_eligible_but_not_display_counted() -> None:
    row = _joined_row(
        trace_id="emlisobs-step3-backend-only",
        emotion_log_id="emotion-step3-backend-only",
        frontend_joined=False,
        modal_opened=None,
        display_confirmed=False,
        classification="passed_displayed",
        measurement_classification="backend_public_passed_frontend_unconfirmed",
        display_blockers=["frontend_diagnostic_missing_or_not_captured"],
    )

    event = normalize_observation_row_to_product_quality_event(row)

    assert event["observation_status"] == "passed"
    assert event["backend_observation_status"] == "passed"
    assert event["eligible_count"] == 1
    assert event["display_confirmed"] is False
    assert event["passed_display_count"] == 0
    assert event["scorecard_passed_display_count"] == 0
    assert event["display_count_blockers"] == ["frontend_diagnostic_missing_or_not_captured"]
    assert "backend_public_passed_frontend_unconfirmed" in event["top_rejection_reasons"]
    assert "frontend_diagnostic_missing_or_not_captured" in event["top_rejection_reasons"]

    scorecard = build_complete_product_quality_scorecard(scorecard_events=[event])
    assert scorecard["eligible_count"] == 1
    assert scorecard["passed_display_count"] == 0
    assert scorecard["display_reach_rate"] == 0.0
    assert "frontend_diagnostic_missing_or_not_captured" in scorecard["top_rejection_reasons"]


def test_step3_backend_passed_frontend_hidden_keeps_rn_reason_without_gate_relaxation() -> None:
    row = _joined_row(
        trace_id="emlisobs-step3-hidden",
        emotion_log_id="emotion-step3-hidden",
        frontend_joined=True,
        modal_opened=False,
        display_confirmed=False,
        classification="passed_backend_frontend_hidden",
        measurement_classification="passed_backend_frontend_hidden",
        primary_reason="frontend_modal_not_opened",
        display_blockers=["frontend_modal_not_opened"],
    )

    event = normalize_observation_row_to_product_quality_event(row)

    assert event["observation_status"] == "passed"
    assert event["backend_observation_status"] == "passed"
    assert event["display_confirmed"] is False
    assert event["passed_display_count"] == 0
    assert event["display_gate_relaxed"] is False
    assert event["reader_gate_relaxed"] is False
    assert "passed_backend_frontend_hidden" in event["top_rejection_reasons"]
    assert "frontend_modal_not_opened" in event["top_rejection_reasons"]


def test_step3_backend_rejected_row_collects_classification_primary_and_gate_reasons() -> None:
    row = _joined_row(
        trace_id="emlisobs-step3-grounding",
        emotion_log_id="emotion-step3-grounding",
        backend_status="rejected",
        backend_len=0,
        frontend_joined=True,
        modal_opened=False,
        display_confirmed=False,
        classification="candidate_generated_but_grounding_rejected",
        measurement_classification="candidate_generated_but_grounding_rejected",
        primary_reason="unsupported_sentence",
        coverage_group="conflict",
    )
    row["stage"] = "grounding"
    row["grounding"] = "fail"
    row["grounding_reason"] = "unsupported_sentence"
    row["gate_results"] = {
        "grounding": {
            "passed": False,
            "primary_reason": "unsupported_sentence",
            "rejection_reasons": ["unsupported_sentence"],
        }
    }

    event = normalize_observation_row_to_product_quality_event(row)

    assert event["coverage_group"] == "conflict"
    assert event["observation_status"] == "rejected"
    assert event["eligible_count"] == 1
    assert event["passed_display_count"] == 0
    assert event["rejected_count"] == 1
    assert "candidate_generated_but_grounding_rejected" in event["top_rejection_reasons"]
    assert "unsupported_sentence" in event["top_rejection_reasons"]
    assert "grounding:unsupported_sentence" in event["top_rejection_reasons"]

    scorecard = build_complete_product_quality_scorecard(scorecard_events=[event])
    assert scorecard["eligible_count"] == 1
    assert scorecard["rejected_count"] == 1
    assert scorecard["reason_required_count"] == 1
    assert scorecard["reason_covered_count"] == 1
    assert scorecard["reason_coverage_rate"] == 1.0


def test_step3_diagnostic_missing_row_is_not_mixed_into_eligible_count() -> None:
    row = {
        "trace_id": "missing-diagnostic",
        "classification": "unknown_diagnostic_missing",
        "measurement_classification": "unknown_diagnostic_missing",
        "diagnostic_capture_status": "diagnostic_log_missing_or_not_captured",
        "backend_diagnostic_capture_status": "backend_diagnostic_missing_or_not_captured",
        "frontend_diagnostic_capture_status": "frontend_diagnostic_missing_or_not_captured",
        "raw_input_included": False,
        "comment_text_included": False,
    }

    event = normalize_observation_row_to_product_quality_event(row)

    assert event["eligible_for_scorecard"] is False
    assert event["eligible_count"] == 0
    assert event["passed_display_count"] == 0
    assert event["observation_status"] == ""
    assert "unknown_diagnostic_missing" in event["top_rejection_reasons"]
    assert "backend_diagnostic_missing_or_not_captured" in event["top_rejection_reasons"]

    scorecard = build_complete_product_quality_scorecard(scorecard_events=[event])
    assert scorecard["eligible_count"] == 0
    assert scorecard["passed_display_count"] == 0
    assert scorecard["display_reach_rate"] == 0.0


def test_step3_rows_can_be_normalized_as_scorecard_event_list() -> None:
    rows = [
        _joined_row(trace_id="emlisobs-step3-list-1", emotion_log_id="emotion-step3-list-1"),
        _joined_row(
            trace_id="emlisobs-step3-list-2",
            emotion_log_id="emotion-step3-list-2",
            frontend_joined=False,
            modal_opened=None,
            display_confirmed=False,
            measurement_classification="backend_public_passed_frontend_unconfirmed",
            display_blockers=["frontend_diagnostic_missing_or_not_captured"],
        ),
    ]
    events = normalize_observation_rows_to_product_quality_events(rows)
    alias_events = build_product_quality_scorecard_events_from_joined_rows(rows)
    scorecard = build_complete_product_quality_scorecard(scorecard_events=events)

    assert len(events) == 2
    assert len(alias_events) == 2
    assert scorecard["eligible_count"] == 2
    assert scorecard["passed_display_count"] == 1
    assert scorecard["display_reach_rate"] == 0.5


def test_step3_rejects_forbidden_text_payload_keys_and_dump_stays_meta_only() -> None:
    unsafe = _joined_row()
    unsafe["comment_text"] = _SECRET_COMMENT
    with pytest.raises(ProductQualityMeasurementConnectionError):
        normalize_observation_row_to_product_quality_event(unsafe)

    unsafe = _joined_row()
    unsafe["frontend"] = {"raw_input": _SECRET_RAW_INPUT}
    with pytest.raises(ProductQualityMeasurementConnectionError):
        assert_product_quality_measurement_connection_meta_only(unsafe)

    events = normalize_observation_rows_to_product_quality_events([_joined_row()])
    payload = {
        "scorecard_events": events,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }
    dumped = dump_product_quality_measurement_connection_payload(payload)
    parsed = json.loads(dumped)
    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_included"] is False
    assert _SECRET_COMMENT not in dumped
    assert _SECRET_RAW_INPUT not in dumped


def _blind_qa_green_review(*, coverage_group: str = "short_daily") -> dict:
    return {
        "review_id": "blind-qa-step4-green",
        "coverage_group": coverage_group,
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def test_step4_measurement_run_builder_connects_scorecard_and_release_ladder() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_joined_row(trace_id="emlisobs-step4-display", emotion_log_id="emotion-step4-display")],
        blind_qa_reviews=[_blind_qa_green_review()],
        run_id="step4-run-display",
    )

    assert report["source_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP
    assert report["measurement_run_builder_ready"] is True
    assert report["scorecard_ready"] is True
    assert report["release_ladder_connected"] is True
    assert report["capture_summary"]["diagnostic_capture_status"] == "captured"
    assert report["scorecard"]["eligible_count"] == 1
    assert report["scorecard"]["passed_display_count"] == 1
    assert report["display_confirmed_count"] == 1
    assert report["release_ladder"]["release_ladder_connected"] is True
    assert report["next_action_branch"]["classification"] == "passed_displayed"
    assert report["next_action_branch"]["target_layer"] == "scorecard"
    assert report["public_release_applied"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["release_ladder"]["product_gate_public_release_applied"] is False
    assert report["raw_input_included"] is False
    assert report["comment_text_included"] is False


def test_step4_blind_qa_missing_remains_release_blocker_without_public_release() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_joined_row(trace_id="emlisobs-step4-no-blind", emotion_log_id="emotion-step4-no-blind")],
        run_id="step4-run-no-blind",
    )

    assert report["scorecard_ready"] is True
    assert report["release_ladder_connected"] is True
    assert report["scorecard"]["blind_qa_ready"] is False
    assert "blind_qa_missing" in report["release_blockers"]
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False
    assert report["release_judgment"]["release_allowed"] is False


def test_step4_backend_passed_without_frontend_routes_to_diagnostic_gap_and_not_display_counted() -> None:
    row = _joined_row(
        trace_id="emlisobs-step4-backend-only",
        emotion_log_id="emotion-step4-backend-only",
        frontend_joined=False,
        modal_opened=None,
        display_confirmed=False,
        classification="passed_displayed",
        measurement_classification="backend_public_passed_frontend_unconfirmed",
        display_blockers=["frontend_diagnostic_missing_or_not_captured"],
    )
    report = build_complete_product_quality_measurement_connection(rows=[row], run_id="step4-run-backend-only")

    assert report["scorecard"]["eligible_count"] == 1
    assert report["scorecard"]["passed_display_count"] == 0
    assert report["capture_summary"]["diagnostic_capture_status"] == "diagnostic_log_missing_or_not_captured"
    assert "frontend_diagnostic_missing_or_not_captured" in report["capture_summary"]["capture_blockers"]
    assert "frontend_diagnostic_missing_or_not_captured" in report["release_blockers"]
    assert report["next_action_branch"]["classification"] == "unknown_diagnostic_missing"
    assert report["next_action_branch"]["target_layer"] == "diagnostic"
    assert report["next_action_branch"]["repair_allowed"] is False


def test_step4_measurement_report_dump_stays_meta_only_and_rejects_forbidden_row_payload() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_joined_row(trace_id="emlisobs-step4-dump", emotion_log_id="emotion-step4-dump")],
        run_id="step4-run-dump",
    )
    dumped = dump_complete_product_quality_measurement_connection(report)
    parsed = json.loads(dumped)
    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_included"] is False
    assert _SECRET_COMMENT not in dumped
    assert _SECRET_RAW_INPUT not in dumped

    unsafe = _joined_row(trace_id="emlisobs-step4-unsafe", emotion_log_id="emotion-step4-unsafe")
    unsafe["comment_text"] = _SECRET_COMMENT
    with pytest.raises(ProductQualityMeasurementConnectionError):
        build_complete_product_quality_measurement_connection(rows=[unsafe], run_id="step4-run-unsafe")




def test_step5_coverage_group_aggregation_exposes_all_required_groups_and_group_reasons() -> None:
    rows = []
    for group in COMPLETE_COVERAGE_GROUP_ORDER:
        row = _joined_row(
            trace_id=f"emlisobs-step5-{group}",
            emotion_log_id=f"emotion-step5-{group}",
            coverage_group=group,
        )
        rows.append(row)
    rows[2] = _joined_row(
        trace_id="emlisobs-step5-conflict-reject",
        emotion_log_id="emotion-step5-conflict-reject",
        backend_status="rejected",
        backend_len=0,
        frontend_joined=True,
        modal_opened=False,
        display_confirmed=False,
        classification="candidate_generated_but_reader_rejected",
        measurement_classification="candidate_generated_but_reader_rejected",
        primary_reason="relation_not_expressed",
        coverage_group="conflict",
    )

    report = build_complete_product_quality_measurement_connection(
        rows=rows,
        blind_qa_reviews=[_blind_qa_green_review(coverage_group=group) for group in COMPLETE_COVERAGE_GROUP_ORDER],
        run_id="step5-run-all-groups",
    )

    by_group = report["by_coverage_group"]
    assert set(COMPLETE_COVERAGE_GROUP_ORDER).issubset(set(by_group))
    assert report["coverage_group_aggregation_ready"] is True
    assert report["coverage_group_summary"]["missing_coverage_groups"] == []
    assert report["coverage_group_summary"]["coverage_group_missing_count"] == 0
    assert report["coverage_group_summary"]["required_coverage_groups_complete"] is True
    assert by_group["conflict"]["eligible_count"] == 1
    assert by_group["conflict"]["passed_display_count"] == 0
    assert by_group["conflict"]["reason_counter"]["relation_not_expressed"] >= 1
    assert report["scorecard"]["by_coverage_group"]["relationship"]["eligible_count"] == 1
    assert report["raw_input_included"] is False
    assert report["comment_text_included"] is False


def test_step5_missing_coverage_group_is_not_folded_into_short_daily_and_blocks_broader_or_product_gate() -> None:
    row = _joined_row(
        trace_id="emlisobs-step5-missing-group",
        emotion_log_id="emotion-step5-missing-group",
        coverage_group="",
    )

    report = build_complete_product_quality_measurement_connection(
        rows=[row],
        blind_qa_reviews=[_blind_qa_green_review()],
        run_id="step5-run-missing-group",
    )

    by_group = report["by_coverage_group"]
    assert set(COMPLETE_COVERAGE_GROUP_ORDER).issubset(set(by_group))
    assert by_group["short_daily"]["eligible_count"] == 0
    assert by_group["coverage_group_missing"]["eligible_count"] == 1
    assert report["coverage_group_summary"]["coverage_group_missing_count"] == 1
    assert report["coverage_group_summary"]["required_coverage_groups_complete"] is False
    assert "coverage_group_missing" in report["release_blockers"]
    assert "coverage_group_missing" in report["release_ladder"]["stage_evaluations"]["broader_beta"]["blockers"]
    assert "product_gate_coverage_groups_incomplete" in report["release_ladder"]["stage_evaluations"]["product_gate"]["blockers"]
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False



def test_step6_blind_qa_input_candidates_are_meta_only_and_separate_from_machine_metrics() -> None:
    row = _joined_row(
        trace_id="emlisobs-step6-blind-candidate",
        emotion_log_id="emotion-step6-blind-candidate",
        coverage_group="pressure",
    )
    row["read_feeling_score"] = 1.0  # must not be trusted as machine-derived read-feeling

    event = normalize_observation_row_to_product_quality_event(row)
    assert event["read_feeling_score"] is None
    assert event["read_feeling_source"] == "blind_qa_required_not_in_event"

    candidates = build_complete_product_quality_blind_qa_input_candidates([event])
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["source_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP
    assert candidate["row_id"] == "emlisobs-step6-blind-candidate"
    assert candidate["coverage_group"] == "pressure"
    assert candidate["classification"] == "passed_displayed"
    assert candidate["public_passed"] is True
    assert candidate["public_passed_for_blind_qa"] is True
    assert candidate["blind_qa_review_required"] is True
    assert candidate["read_feeling_score"] is None
    assert candidate["machine_read_feeling_score"] is None
    assert candidate["raw_input_included"] is False
    assert candidate["comment_text_included"] is False
    dumped_candidate = json.dumps(candidate, ensure_ascii=False)
    assert _SECRET_COMMENT not in dumped_candidate
    assert _SECRET_RAW_INPUT not in dumped_candidate
    assert "comment_text" not in candidate
    assert "raw_input" not in candidate


def test_step6_measurement_report_requires_blind_qa_for_read_feeling_and_product_gate() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_joined_row(trace_id="emlisobs-step6-no-blind", emotion_log_id="emotion-step6-no-blind")],
        run_id="step6-run-no-blind",
    )

    assert report["source_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_RUN_BUILDER_STEP
    assert report["blind_qa_separation_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_BLIND_QA_STEP
    assert report["blind_qa_separation_ready"] is True
    assert report["blind_qa_required"] is True
    assert report["read_feeling_requires_blind_qa"] is True
    assert report["read_feeling_auto_estimation_allowed"] is False
    assert report["machine_metrics_separated_from_blind_qa"] is True
    assert report["machine_metrics_and_blind_qa_separated"] is True
    assert report["blind_qa_candidate_count"] == 1
    assert report["blind_qa_public_passed_candidate_count"] == 1
    assert report["blind_qa_ready"] is False
    assert report["blind_qa_missing"] is True
    assert report["blind_qa_missing_count"] == 1
    assert report["read_feeling_score"] is None
    assert report["machine_read_feeling_score"] is None
    assert report["scorecard"]["machine_metrics"]["read_feeling_score"] is None
    assert report["scorecard"]["read_feeling_score"] is None
    assert "blind_qa_missing" in report["release_blockers"]
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False


def test_step6_blind_qa_reviews_fill_read_feeling_only_from_rating_results() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_joined_row(trace_id="emlisobs-step6-blind", emotion_log_id="emotion-step6-blind")],
        blind_qa_reviews=[_blind_qa_green_review()],
        run_id="step6-run-with-blind",
    )

    assert report["blind_qa_ready"] is True
    assert report["blind_qa_missing"] is False
    assert report["blind_qa_missing_count"] == 0
    assert report["machine_read_feeling_score"] is None
    assert report["read_feeling_score"] == 1.0
    assert report["read_feeling_source"] == "blind_qa"
    assert report["scorecard"]["blind_qa_metrics"]["read_feeling_score"] == 1.0
    assert report["scorecard"]["machine_metrics"]["read_feeling_score"] is None
    assert report["blind_qa_input_candidates"][0]["read_feeling_score"] is None
    assert report["raw_input_included"] is False
    assert report["comment_text_included"] is False


def test_step7_next_action_routes_to_most_frequent_classification_before_cause_repair() -> None:
    rows = [
        _joined_row(
            trace_id="emlisobs-step7-reader-1",
            emotion_log_id="emotion-step7-reader-1",
            backend_status="rejected",
            backend_len=0,
            frontend_joined=True,
            modal_opened=False,
            display_confirmed=False,
            classification="candidate_generated_but_reader_rejected",
            measurement_classification="candidate_generated_but_reader_rejected",
            primary_reason="relation_not_expressed",
            coverage_group="conflict",
        ),
        _joined_row(
            trace_id="emlisobs-step7-reader-2",
            emotion_log_id="emotion-step7-reader-2",
            backend_status="rejected",
            backend_len=0,
            frontend_joined=True,
            modal_opened=False,
            display_confirmed=False,
            classification="candidate_generated_but_reader_rejected",
            measurement_classification="candidate_generated_but_reader_rejected",
            primary_reason="reader_relation_surface_missing",
            coverage_group="relationship",
        ),
        _joined_row(
            trace_id="emlisobs-step7-grounding",
            emotion_log_id="emotion-step7-grounding",
            backend_status="rejected",
            backend_len=0,
            frontend_joined=True,
            modal_opened=False,
            display_confirmed=False,
            classification="candidate_generated_but_grounding_rejected",
            measurement_classification="candidate_generated_but_grounding_rejected",
            primary_reason="unsupported_sentence",
            coverage_group="pressure",
        ),
    ]

    report = build_complete_product_quality_measurement_connection(rows=rows, run_id="step7-run-reader-dominant")

    assert report["measurement_latest_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP
    assert report["next_action_routing_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_NEXT_ACTION_ROUTING_STEP
    assert report["next_action_routing_ready"] is True
    assert report["next_action_routing_basis"] == "most_frequent_classification"
    assert report["next_action_branch"]["classification"] == "candidate_generated_but_reader_rejected"
    assert report["next_action_branch"]["target_layer"] == "reader"
    assert report["next_action_branch"]["classification_decided_before_cause_repair"] is True
    assert report["next_action_branch"]["repair_allowed"] is True
    assert report["next_action_classification_counter"]["candidate_generated_but_reader_rejected"] == 2
    assert "RN表示条件" in report["next_action_branch"]["do_not_touch"]


def test_step7_displayed_only_routes_to_scorecard_coverage_or_blind_qa_not_non_display_repair() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_joined_row(trace_id="emlisobs-step7-display-only", emotion_log_id="emotion-step7-display-only")],
        run_id="step7-run-display-only",
    )

    assert report["next_action_branch"]["classification"] == "passed_displayed"
    assert report["next_action_branch"]["target_layer"] == "scorecard"
    assert report["next_action_branch"]["passed_displayed_only"] is True
    assert report["next_action_branch"]["repair_allowed"] is False
    assert report["next_action_branch"]["measurement_next_action_routing_ready"] is True
    assert report["next_action_routing_summary"]["passed_displayed_only"] is True
    assert report["public_release_applied"] is False


def test_step7_unknown_and_unclassified_stay_in_diagnostic_enrichment() -> None:
    row = _joined_row(
        trace_id="emlisobs-step7-unclassified",
        emotion_log_id="emotion-step7-unclassified",
        backend_status="rejected",
        backend_len=0,
        frontend_joined=True,
        modal_opened=False,
        display_confirmed=False,
        classification="unclassified_non_display",
        measurement_classification="unclassified_non_display",
        primary_reason="reason_missing",
        coverage_group="desire_fear",
    )

    report = build_complete_product_quality_measurement_connection(rows=[row], run_id="step7-run-unclassified")

    branch = report["next_action_branch"]
    assert branch["classification"] == "unclassified_non_display"
    assert branch["target_layer"] == "diagnostic"
    assert branch["repair_allowed"] is False
    assert branch["requires_diagnostic_enrichment"] is True
    assert branch["classification_decided_before_cause_repair"] is True
    assert "SelfRepair" in branch["do_not_touch"]


def test_step7_template_major_release_blocker_routes_to_template_only_after_measured_issue() -> None:
    rows = []
    reviews = []
    for group in COMPLETE_COVERAGE_GROUP_ORDER:
        row = _joined_row(
            trace_id=f"emlisobs-step7-template-{group}",
            emotion_log_id=f"emotion-step7-template-{group}",
            coverage_group=group,
        )
        if group == "short_daily":
            row["template_major_count"] = 1
        rows.append(row)
        reviews.append(_blind_qa_green_review(coverage_group=group))

    report = build_complete_product_quality_measurement_connection(
        rows=rows,
        blind_qa_reviews=reviews,
        run_id="step7-run-template-major",
    )

    branch = report["next_action_branch"]
    assert "template_major_detected" in report["release_blockers"]
    assert branch["classification"] == "candidate_generated_but_template_rejected"
    assert branch["target_layer"] == "template"
    assert branch["routing_basis"] == "first_release_blocker"
    assert branch["selected_release_blocker"] == "template_major_detected"
    assert branch["measured_surface_or_tone_issue"] is True
    assert branch["tone_or_surface_routing_requires_measured_issue"] is True
    assert "Template/Echo Gate を緩める" in branch["forbidden_actions"]


def test_step7_routing_summary_rejects_forbidden_text_payload_keys() -> None:
    event = normalize_observation_row_to_product_quality_event(_joined_row())
    unsafe = dict(event)
    unsafe["commentText"] = _SECRET_COMMENT

    with pytest.raises(ProductQualityMeasurementConnectionError):
        build_complete_product_quality_measurement_next_action_routing_summary(
            capture_summary={"capture_blockers": [], "raw_input_included": False, "comment_text_included": False},
            events=[unsafe],
            scorecard={},
            release_blockers=[],
            run_id="step7-run-unsafe",
        )
