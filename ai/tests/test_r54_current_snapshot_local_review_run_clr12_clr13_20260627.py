# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR12-CLR13 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "local_path",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any], *, allowed_true_false_flags: set[str] | None = None) -> None:
    allowed = allowed_true_false_flags or set()
    assert material["body_free"] is True
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] is True, key
        else:
            assert material[key] is False, key
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_clr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _ready_clr09() -> dict[str, Any]:
    form = clr09.build_p7_r54_clr09_reviewer_selection_form_freeze()
    assert clr09.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form) is True
    assert form["reviewer_selection_form_status"] == clr09.P7_R54_CLR09_FORM_READY_STATUS_REF
    assert form["next_required_step"] == clr11.P7_R54_CLR10_STEP_REF
    return form


def _completed_clr10() -> dict[str, Any]:
    form = _ready_clr09()
    receipt = clr11.build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form(
        reviewer_selection_form_freeze=form,
        reviewer_ref_ids=["r54-local-reviewer-bodyfree-ref-001"],
    )
    material = clr11.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=form,
        local_human_review_operation_receipt=receipt,
    )
    assert clr11.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True
    return material


def _ready_rows(op10: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return clr11.build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion(op10 or _completed_clr10())


def _ready_clr11(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    op10 = _completed_clr10()
    material = clr11.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=rows or _ready_rows(op10),
    )
    assert clr11.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True
    assert material["rating_row_normalization_allowed_next"] is True
    return material


def _ready_clr12(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr.build_p7_r54_clr12_rating_row_normalization(
        sanitized_review_result_row_intake=_ready_clr11(rows),
    )
    assert clr.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True
    return material


def test_r54_clr00_to_clr11_are_present_before_clr12_clr13() -> None:
    intake = _ready_clr11()

    assert tuple(intake["implemented_steps"]) == clr11.P7_R54_CLR11_IMPLEMENTED_STEPS
    assert intake["sanitized_review_result_row_count"] == 24
    assert intake["rating_row_count"] == 0
    assert intake["question_observation_row_count"] == 0
    assert intake["rating_row_normalization_allowed_next"] is True
    assert intake["actual_rating_rows_materialized_here"] is False
    assert intake["disposal_verified"] is False
    assert intake["next_required_step"] == clr.P7_R54_CLR12_STEP_REF


def test_r54_clr12_default_blocks_without_ready_clr11() -> None:
    material = clr.build_p7_r54_clr12_rating_row_normalization()

    assert set(material) == set(clr.P7_R54_CLR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR12_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR12_STEP_REF
    assert material["rating_row_normalization_status"] == clr.P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    assert "clr11_sanitized_review_result_row_intake_not_ready_for_rating_normalization" in material["execution_blocker_ids"]
    assert material["rating_rows"] == []
    assert material["rating_row_count"] == 0
    assert material["rating_rows_normalized_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR12_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True


def test_r54_clr12_rating_row_normalization_ready_bodyfree() -> None:
    material = _ready_clr12()

    assert set(material) == set(clr.P7_R54_CLR12_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["rating_row_normalization_status"] == clr.P7_R54_CLR12_RATING_NORMALIZATION_READY_STATUS_REF
    assert material["rating_row_normalization_ref"] == clr.P7_R54_CLR12_RATING_ROW_NORMALIZATION_REF
    assert material["rating_row_normalization_reason_refs"] == [clr.P7_R54_CLR12_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_ref_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["case_ref_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["selection_row_ref_count"] == 24
    assert material["all_axes_present"] is True
    assert material["axis_score_range_valid"] is True
    assert material["verdict_allowed"] is True
    assert material["below_target_axis_refs_calculated"] is True
    assert material["rating_rows_are_bodyfree"] is True
    assert material["all_required_rating_rows_present"] is True
    assert material["rating_case_ref_sets_match_sanitized_intake"] is True
    assert material["verdict_counts"] == {"PASS": 24}
    assert material["overall_read_feeling_counts"] == {"felt_record_returned_as_line": 24}
    assert material["readfeel_blocker_row_candidate_count"] == 0
    assert material["execution_blocker_row_candidate_count"] == 0
    assert material["rating_rows_normalized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR13_STEP_REF

    for row in material["rating_rows"]:
        assert set(row) == set(clr.P7_R54_CLR12_RATING_ROW_REQUIRED_FIELD_REFS)
        assert tuple(row["axis_scores"].keys()) == clr.P7_R54_CLR12_RATING_AXIS_REFS
        assert row["axis_score_count"] == 6
        assert row["axis_score_average"] == 1.0
        assert row["average_score"] == 1.0
        assert row["below_target_axis_refs"] == []
        assert row["overall_read_feeling_ref"] == "felt_record_returned_as_line"
        assert row["rating_row_is_bodyfree"] is True
        assert row["selection_only_source_row"] is True
        assert row["machine_auto_score_used"] is False
        assert row["machine_metrics_used_for_readfeel"] is False
        assert row["body_free"] is True
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row
    _assert_bodyfree_no_touch(material, allowed_true_false_flags={"actual_rating_rows_materialized_here"})
    assert clr.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True


def test_r54_clr12_calculates_below_target_axis_refs_without_using_machine_metrics() -> None:
    rows = _ready_rows()
    rows[0]["verdict"] = "YELLOW"
    rows[0]["overall_read_feeling_ref"] = "felt_generic_or_shallow"
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["axis_scores"] = dict(rows[0]["axis_scores"])
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.75

    material = _ready_clr12(rows)
    row = material["rating_rows"][0]

    assert row["below_target_axis_refs"] == ["history_connection_naturalness"]
    assert row["below_target_axis_count"] == 1
    assert row["machine_auto_score_used"] is False
    assert row["machine_metrics_used_for_readfeel"] is False
    assert material["below_target_axis_refs"] == ["history_connection_naturalness"]
    assert material["below_target_rating_row_count"] == 1
    assert material["verdict_counts"]["YELLOW"] == 1
    assert material["readfeel_blocker_row_candidate_count"] == 1
    assert clr.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True


def test_r54_clr12_blocks_pass_with_blocker_instead_of_confirming_p5() -> None:
    rows = _ready_rows()
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]

    material = clr.build_p7_r54_clr12_rating_row_normalization(
        sanitized_review_result_row_intake=_ready_clr11(rows),
    )

    assert material["rating_row_normalization_status"] == clr.P7_R54_CLR12_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    assert "rating_row_verdict_blocker_consistency_failed" in material["execution_blocker_ids"]
    assert material["pass_with_any_blocker_detected"] is True
    assert material["rating_rows"] == []
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["release_allowed"] is False
    assert clr.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True


def test_r54_clr12_rejects_forbidden_payload_key_from_clr11_material() -> None:
    intake = _ready_clr11()
    mutated = deepcopy(intake)
    mutated["sanitized_review_result_rows"][0]["question_text"] = "forbidden"

    with pytest.raises(ValueError):
        clr.build_p7_r54_clr12_rating_row_normalization(sanitized_review_result_row_intake=mutated)


def test_r54_clr13_default_blocks_without_ready_clr12() -> None:
    material = clr.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion()

    assert set(material) == set(clr.P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR13_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR13_STEP_REF
    assert material["blocker_ingestion_status"] == clr.P7_R54_CLR13_BLOCKER_INGESTION_BLOCKED_STATUS_REF
    assert "rating_row_normalization_not_ready_for_blocker_ingestion" in material["execution_blocker_ids"]
    assert material["readfeel_blocker_rows_normalized"] is False
    assert material["execution_blocker_rows_normalized"] is False
    assert material["actual_blocker_rows_materialized_here"] is False
    assert material["question_need_observation_normalization_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR13_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True


def test_r54_clr13_ingestion_ready_empty_blockers_bodyfree() -> None:
    material = clr.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=_ready_clr12(),
    )

    assert set(material) == set(clr.P7_R54_CLR13_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert material["blocker_ingestion_status"] == clr.P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["blocker_ingestion_ref"] == clr.P7_R54_CLR13_BLOCKER_INGESTION_REF
    assert material["blocker_ingestion_reason_refs"] == [clr.P7_R54_CLR13_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["readfeel_blocker_row_count"] == 0
    assert material["execution_blocker_row_count"] == 0
    assert material["open_readfeel_blocker_count"] == 0
    assert material["open_execution_blocker_count"] == 0
    assert material["readfeel_blocker_counts"] == {}
    assert material["execution_blocker_counts"] == {}
    assert material["readfeel_blocker_rows_normalized"] is True
    assert material["execution_blocker_rows_normalized"] is True
    assert material["readfeel_and_execution_blockers_separated"] is True
    assert material["execution_blocker_not_mixed_into_readfeel_verdict"] is True
    assert material["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert material["rating_rows_preserved_from_clr12"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["question_need_observation_normalization_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR14_STEP_REF
    _assert_bodyfree_no_touch(material, allowed_true_false_flags={"actual_rating_rows_materialized_here"})
    assert clr.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True


def test_r54_clr13_separates_readfeel_and_execution_blockers() -> None:
    rows = _ready_rows()
    rows[0]["verdict"] = "YELLOW"
    rows[0]["overall_read_feeling_ref"] = "felt_generic_or_shallow"
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[1]["verdict"] = "NOT_REVIEWABLE"
    rows[1]["overall_read_feeling_ref"] = "felt_not_reviewable"
    rows[1]["execution_blocker_ids"] = ["rating_row_incomplete"]

    material = clr.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=_ready_clr12(rows),
    )

    assert material["blocker_ingestion_status"] == clr.P7_R54_CLR13_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["readfeel_blocker_row_count"] == 1
    assert material["execution_blocker_row_count"] == 1
    assert material["open_readfeel_blocker_count"] == 1
    assert material["open_execution_blocker_count"] == 1
    assert material["readfeel_blocker_counts"] == {"p5_history_connection_too_generic": 1}
    assert material["execution_blocker_counts"] == {"rating_row_incomplete": 1}
    assert material["p5_confirmed_candidate_blocked_by_open_execution_blockers"] is True

    readfeel_row = material["readfeel_blocker_rows"][0]
    execution_row = material["execution_blocker_rows"][0]
    assert set(readfeel_row) == set(clr.P7_R54_CLR13_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert set(execution_row) == set(clr.P7_R54_CLR13_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert readfeel_row["blocker_kind_ref"] == clr.P7_R54_CLR13_READFEEL_BLOCKER_KIND_REF
    assert execution_row["execution_blocker_kind_ref"] == clr.P7_R54_CLR13_EXECUTION_BLOCKER_KIND_REF
    assert execution_row["execution_blocker_does_not_assign_readfeel_verdict"] is True
    assert execution_row["execution_blocker_id"] == "rating_row_incomplete"
    assert readfeel_row["readfeel_blocker_id"] == "p5_history_connection_too_generic"
    for row in (readfeel_row, execution_row):
        assert row["body_free"] is True
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row
    assert clr.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True


def test_r54_clr13_contract_rejects_mutations() -> None:
    clr12 = _ready_clr12()
    mutated_clr12 = deepcopy(clr12)
    mutated_clr12["actual_review_evidence_complete"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr12_rating_row_normalization_contract(mutated_clr12)

    material = clr.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=clr12)
    mutated = deepcopy(material)
    mutated["release_allowed"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(mutated)

    mutated_execution = deepcopy(material)
    rows = _ready_rows()
    rows[1]["verdict"] = "NOT_REVIEWABLE"
    rows[1]["execution_blocker_ids"] = ["rating_row_incomplete"]
    with_execution = clr.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=_ready_clr12(rows),
    )
    mutated_execution = deepcopy(with_execution)
    mutated_execution["execution_blocker_rows"][0]["execution_blocker_does_not_assign_readfeel_verdict"] = False
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(mutated_execution)


def test_r54_clr12_clr13_aliases_remain_available() -> None:
    clr11_material = _ready_clr11()
    clr12 = clr.build_p7_r54_current_snapshot_local_run_clr12_rating_row_normalization(
        sanitized_review_result_row_intake=clr11_material,
    )
    assert clr.assert_p7_r54_current_snapshot_local_run_clr12_rating_row_normalization_contract(clr12) is True
    assert clr.assert_p7_r54_current_snapshot_rating_row_normalization_bodyfree_contract(clr12) is True
    assert clr.assert_clr12_rating_row_normalization_contract(clr12) is True

    clr13 = clr.build_p7_r54_current_snapshot_local_run_clr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=clr12,
    )
    assert clr.assert_p7_r54_current_snapshot_local_run_clr13_readfeel_blocker_execution_blocker_ingestion_contract(clr13) is True
    assert clr.assert_p7_r54_current_snapshot_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(clr13) is True
    assert clr.assert_clr13_readfeel_blocker_execution_blocker_ingestion_contract(clr13) is True
