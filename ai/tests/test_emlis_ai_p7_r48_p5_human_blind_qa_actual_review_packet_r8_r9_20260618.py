# -*- coding: utf-8 -*-
"""R48 R8/R9 body-free rating and blocker row contracts."""

from __future__ import annotations

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48


def _r6_r7_freeze() -> dict:
    freeze = r48.build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    assert r48.assert_p7_r48_r6_r7_materialization_notes_policy_freeze_contract(freeze)
    return freeze


def _case_row() -> dict:
    combined = _r6_r7_freeze()
    matrix = combined["r4_r5_reviewer_packet_schema_freeze"]["r2_r3_local_storage_case_matrix_freeze"]["p5_case_matrix"]
    row = dict(matrix["case_rows"][0])
    row["review_session_id"] = matrix["review_session_id"]
    return row


def _passing_result() -> dict:
    return {
        "axis_scores": {axis: 1.0 for axis in r48.P5_HUMAN_BLIND_QA_RATING_AXES},
        "verdict": "PASS",
        "sanitized_reason_ids": [],
        "blocker_ids": [],
        "reviewer_free_text_included": False,
    }


def test_r8_rating_row_normalizer_policy_is_bodyfree_and_points_to_r9() -> None:
    policy = r48.build_p7_r48_rating_row_normalizer_policy(r6_r7_freeze=_r6_r7_freeze())

    assert r48.assert_p7_r48_rating_row_normalizer_policy_contract(policy)
    assert policy["normalizer_ready"] is True
    assert policy["body_free_rating_row_normalizer_ready"] is True
    assert policy["next_required_step"] == r48.P7_R48_R8_NEXT_REQUIRED_STEP_REF
    assert policy["next_required_step"] == "R9_blocker_execution_blocker_row_builder"
    assert policy["actual_rating_rows_materialized_here"] is False
    assert policy["actual_human_review_run_here"] is False
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["hold004_close_allowed"] is False


def test_rating_row_normalizer_accepts_only_sanitized_human_axis_scores() -> None:
    row = r48.normalize_p7_r48_p5_rating_row_bodyfree(
        review_result=_passing_result(),
        case_row=_case_row(),
        reviewer_ref="local_reviewer_a",
        reviewed_at="2026-06-19T00-00-00Z",
        body_removed=False,
    )

    assert r48.assert_p7_r48_p5_rating_row_bodyfree_contract(row)
    assert set(row) == set(r48.P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS)
    assert row["schema_version"] == r48.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert row["reviewer_free_text_included"] is False
    assert row["body_free"] is True
    assert row["verdict"] == "PASS"
    assert row["blocker_ids"] == []
    assert set(row["axis_scores"]) == set(r48.P5_HUMAN_BLIND_QA_RATING_AXES)


def test_rating_row_rejects_missing_axis_machine_metric_and_reviewer_text_payload() -> None:
    missing_axis = _passing_result()
    missing_axis["axis_scores"] = dict(missing_axis["axis_scores"])
    missing_axis["axis_scores"].pop(r48.P5_HUMAN_BLIND_QA_RATING_AXES[0])
    with pytest.raises(ValueError, match="requires every P5 axis"):
        r48.normalize_p7_r48_p5_rating_row_bodyfree(review_result=missing_axis, case_row=_case_row())

    machine_metric = _passing_result()
    machine_metric["machine_metrics_used_for_readfeel"] = True
    with pytest.raises(ValueError, match="machine metric|machine metrics|body payload"):
        r48.normalize_p7_r48_p5_rating_row_bodyfree(review_result=machine_metric, case_row=_case_row())

    reviewer_text = _passing_result()
    reviewer_text["reviewer_free_text"] = "local reviewer note must not survive into body-free rows"
    with pytest.raises(ValueError, match="reviewer text|body payload|body-free"):
        r48.normalize_p7_r48_p5_rating_row_bodyfree(review_result=reviewer_text, case_row=_case_row())


def test_rating_row_verdict_boundary_does_not_hide_below_target_or_blocked_cases() -> None:
    below_target_pass = _passing_result()
    first_axis = r48.P5_HUMAN_BLIND_QA_RATING_AXES[0]
    below_target_pass["axis_scores"] = dict(below_target_pass["axis_scores"])
    below_target_pass["axis_scores"][first_axis] = 0.0
    with pytest.raises(ValueError, match="PASS cannot"):
        r48.normalize_p7_r48_p5_rating_row_bodyfree(review_result=below_target_pass, case_row=_case_row())

    red_without_blocker = _passing_result()
    red_without_blocker["verdict"] = "RED"
    with pytest.raises(ValueError, match="RED/REPAIR_REQUIRED"):
        r48.normalize_p7_r48_p5_rating_row_bodyfree(review_result=red_without_blocker, case_row=_case_row())

    blocked_result = _passing_result()
    blocked_result["verdict"] = "BLOCKED"
    with pytest.raises(ValueError, match="execution-blocked"):
        r48.normalize_p7_r48_p5_rating_row_bodyfree(review_result=blocked_result, case_row=_case_row())


def test_r9_blocker_execution_blocker_policy_separates_readfeel_and_execution() -> None:
    policy = r48.build_p7_r48_blocker_execution_blocker_row_builder_policy()

    assert r48.assert_p7_r48_blocker_execution_blocker_row_builder_policy_contract(policy)
    assert policy["blocker_row_builder_ready"] is True
    assert policy["execution_blocker_row_builder_ready"] is True
    assert policy["readfeel_and_execution_blockers_separated"] is True
    assert policy["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert policy["timeout_maps_to_execution_blocker_not_red"] is True
    assert policy["missing_local_root_maps_to_execution_blocker_not_red"] is True
    assert policy["material_missing_maps_to_execution_blocker_not_red"] is True
    assert policy["actual_blocker_rows_materialized_here"] is False
    assert policy["actual_execution_blocker_rows_materialized_here"] is False
    assert policy["next_required_step"] == r48.P7_R48_R8_R9_NEXT_REQUIRED_STEP_REF
    assert policy["next_required_step"] == "R10_disposal_receipt_builder"


def test_readfeel_blocker_row_is_bodyfree_and_cannot_use_execution_kind() -> None:
    row = r48.build_p7_r48_p5_blocker_row_bodyfree(
        case_row=_case_row(),
        blocker_id="p5_history_connection_too_generic",
        blocker_kind="REPAIR_REQUIRED",
        blocker_status="OPEN",
        body_removed=False,
    )

    assert r48.assert_p7_r48_p5_blocker_row_bodyfree_contract(row)
    assert set(row) == set(r48.P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert row["schema_version"] == r48.P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert row["blocker_id"] == "p5_history_connection_too_generic"
    assert row["reviewer_free_text_included"] is False
    assert row["body_free"] is True

    with pytest.raises(ValueError, match="EXECUTION_BLOCKER"):
        r48.build_p7_r48_p5_blocker_row_bodyfree(
            case_row=_case_row(),
            blocker_id="p5_history_connection_too_generic",
            blocker_kind="EXECUTION_BLOCKER",
        )


def test_execution_blocker_rows_do_not_assign_readfeel_verdict() -> None:
    row = r48.build_p7_r48_p5_execution_blocker_row_bodyfree(
        case_row=_case_row(),
        execution_blocker_id="review_packet_generation_blocked_missing_local_root",
    )

    assert r48.assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(row)
    assert set(row) == set(r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert row["schema_version"] == r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert row["execution_blocker_kind"] == "GENERATION"
    assert row["execution_blocker_status"] == "OPEN"
    assert row["readfeel_verdict_not_assigned"] is True
    assert "verdict" not in row
    assert row["body_free"] is True


def test_r8_r9_combined_freeze_keeps_review_closed_and_points_to_r10() -> None:
    freeze = r48.build_p7_r48_r8_r9_rating_blocker_rows_freeze(r6_r7_freeze=_r6_r7_freeze())

    assert r48.assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(freeze)
    assert freeze["rating_row_normalizer_ready"] is True
    assert freeze["blocker_row_builder_ready"] is True
    assert freeze["execution_blocker_row_builder_ready"] is True
    assert freeze["readfeel_and_execution_blockers_separated"] is True
    assert freeze["next_required_step"] == "R10_disposal_receipt_builder"
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["actual_blocker_rows_materialized_here"] is False
    assert freeze["actual_execution_blocker_rows_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
