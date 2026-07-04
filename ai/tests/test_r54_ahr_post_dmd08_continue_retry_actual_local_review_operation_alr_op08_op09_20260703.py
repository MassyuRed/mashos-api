# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP08/OP09 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_op03_20260703 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op06_op07_20260703 import (
    _op05_complete,
    _op05_retry,
    _op06,
    _op07,
)


def _ready_op07() -> dict[str, object]:
    return _op07(_op06(_op05_retry()))


def _downstream_manual_decision_op07() -> dict[str, object]:
    return _op07(_op06(_op05_complete()))


def _complete_receipt(**overrides: object) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": "actual_receipt_bodyfree_alr_op08_complete_candidate",
        "review_session_id": alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        "source_kind_ref": alr.P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF,
        "created_from_real_operation": True,
        "actual_source_guard_passed": True,
        "actual_human_review_executed_by_person": True,
        "reviewed_case_count": alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "selection_row_count": alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "sanitized_review_result_row_count": alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "question_need_observation_row_count": alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "disposal_purge_receipt_accepted": True,
        "no_body_leak_validation_passed": True,
        "no_question_text_validation_passed": True,
        "no_path_hash_validation_passed": True,
        "no_terminal_output_body_validation_passed": True,
        "no_touch_validation_passed": True,
        "body_free": True,
    }
    receipt.update(overrides)
    return receipt


def _op08(receipt: dict[str, object] | None = None, *, op07: dict[str, object] | None = None) -> dict[str, object]:
    return alr.build_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard(
        alr_op07_bodyfull_packet_request_bodyfree_envelope=op07 or _ready_op07(),
        actual_operation_receipt_bodyfree=receipt,
    )


def _sanitized_row(index: int, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": alr.P7_R54_AHR_POST_DMD08_ALR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
        "review_session_id": alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        "case_ref": f"case_{index:02d}",
        "verdict_ref": "VERDICT_PASS_BODYFREE",
        "sanitized_reason_ids": ["REASON_ID_READ_AS_WRITTEN_WEAK"],
        "blocker_refs": [],
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "body_free": True,
    }
    row.update(overrides)
    return row


def _rating_row(index: int, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": alr.P7_R54_AHR_POST_DMD08_ALR_RATING_ROW_SCHEMA_VERSION,
        "review_session_id": alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        "case_ref": f"case_{index:02d}",
        "rating_axis_scores": {axis: 2 for axis in alr.P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS},
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "body_free": True,
    }
    row.update(overrides)
    return row


def _question_need_row(index: int, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": alr.P7_R54_AHR_POST_DMD08_ALR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "review_session_id": alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        "case_ref": f"case_{index:02d}",
        "question_need_primary_class_ref": "QUESTION_NEED_NONE",
        "ambiguity_kind_refs": ["AMBIGUITY_NONE"],
        "one_question_fit_ref": "ONE_QUESTION_NOT_NEEDED",
        "repair_required_refs": [],
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "p8_question_spec_created": False,
        "body_free": True,
    }
    row.update(overrides)
    return row


def _complete_row_sets() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    size = alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT
    return (
        [_sanitized_row(index) for index in range(1, size + 1)],
        [_rating_row(index) for index in range(1, size + 1)],
        [_question_need_row(index) for index in range(1, size + 1)],
    )


def _op09(
    op08: dict[str, object] | None = None,
    *,
    rows: tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]] | None = None,
) -> dict[str, object]:
    sanitized_rows, rating_rows, question_need_rows = rows or ([], [], [])
    return alr.build_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard(
        alr_op08_actual_operation_receipt_expected_schema_completeness_guard=op08 or _op08(),
        sanitized_review_result_rows_bodyfree=sanitized_rows,
        rating_rows_bodyfree=rating_rows,
        question_need_observation_rows_bodyfree=question_need_rows,
    )


def _assert_op08_does_not_create_or_execute(material: dict[str, object]) -> None:
    for key in (
        "alr_op08_does_not_create_actual_operation_receipt",
        "alr_op08_does_not_generate_body_full_packet",
        "alr_op08_does_not_run_actual_local_human_review",
        "alr_op08_does_not_create_rows_or_disposal",
        "alr_op08_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op08_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op08_does_not_change_api_db_rn_runtime_response_key",
    ):
        assert material[key] is True, key


def _assert_op09_does_not_create_or_execute(material: dict[str, object]) -> None:
    for key in (
        "alr_op09_does_not_create_actual_rows",
        "alr_op09_does_not_create_question_text_or_p8_spec",
        "alr_op09_does_not_generate_body_full_packet",
        "alr_op09_does_not_run_actual_local_human_review",
        "alr_op09_does_not_create_disposal_or_purge_receipt",
        "alr_op09_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op09_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op09_does_not_change_api_db_rn_runtime_response_key",
    ):
        assert material[key] is True, key


def test_alr_op08_defines_expected_dmd_compatible_receipt_schema_without_creating_receipt() -> None:
    material = _op08()

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_SCHEMA_VERSION
    assert material["actual_operation_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF
    assert material["actual_operation_receipt_expected_schema_version_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
    assert tuple(material["actual_operation_receipt_required_count_field_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS
    assert tuple(material["actual_operation_receipt_required_true_guard_field_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS
    assert material["actual_operation_receipt_present"] is False
    assert material["actual_operation_receipt_complete_candidate"] is False
    assert material["actual_operation_receipt_missing_or_incomplete"] is True
    assert material["actual_operation_receipt_expected_schema_guard_ready"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF
    _assert_op08_does_not_create_or_execute(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op08_accepts_complete_candidate_only_by_schema_counts_and_true_guards() -> None:
    material = _op08(_complete_receipt())

    assert material["actual_operation_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF
    assert material["actual_operation_receipt_complete_candidate"] is True
    assert material["receipt_count_complete"] is True
    assert material["receipt_guard_complete"] is True
    assert all(value is True for value in material["receipt_count_pass_refs"].values())
    assert all(value is True for value in material["receipt_guard_true_field_pass_refs"].values())
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF
    _assert_op08_does_not_create_or_execute(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op08_marks_present_but_incomplete_receipt_without_promoting_complete() -> None:
    material = _op08(_complete_receipt(selection_row_count=23))

    assert material["actual_operation_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF
    assert material["actual_operation_receipt_complete_candidate"] is False
    assert material["receipt_count_complete"] is False
    assert material["receipt_count_pass_refs"]["selection_row_count"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op08_forbidden_body_payload_in_receipt_becomes_repair_path_without_body_value() -> None:
    material = _op08(_complete_receipt(raw_input="body-value-must-not-survive"))

    assert material["actual_operation_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["actual_operation_receipt_forbidden_payload_key_paths"] == ["actual_operation_receipt_bodyfree.raw_input"]
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert "body-value-must-not-survive" not in repr(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op08_contract_rejects_manual_complete_candidate_count_tampering() -> None:
    material = _op08(_complete_receipt())
    material["reviewed_case_count"] = 23

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material)


def test_alr_op08_not_applicable_downstream_manual_decision_path_does_not_open_receipt_guard() -> None:
    material = _op08(op07=_downstream_manual_decision_op07())

    assert material["actual_operation_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF
    assert material["actual_operation_receipt_expected_schema_guard_ready"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    assert material["next_implementation_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op09_defines_selection_only_rows_expected_schema_without_creating_rows() -> None:
    material = _op09(_op08())

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_SCHEMA_VERSION
    assert material["row_schema_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF
    assert material["sanitized_review_result_row_schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
    assert material["rating_row_schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_RATING_ROW_SCHEMA_VERSION
    assert material["question_need_observation_row_schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
    assert tuple(material["allowed_verdict_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_ALLOWED_VERDICT_REFS
    assert tuple(material["rating_axis_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS
    assert tuple(material["allowed_question_need_primary_class_refs"]) == alr.P7_R54_AHR_POST_DMD08_ALR_ALLOWED_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert material["row_bodyfree_schema_guard_ready"] is True
    assert material["rows_complete_candidate"] is False
    assert material["rows_missing_or_incomplete"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF
    _assert_op09_does_not_create_or_execute(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op09_accepts_complete_candidate_rows_only_as_bodyfree_selection_rows() -> None:
    material = _op09(_op08(_complete_receipt()), rows=_complete_row_sets())

    assert material["row_schema_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF
    assert material["rows_complete_candidate"] is True
    assert material["row_count_complete"] is True
    assert material["sanitized_review_result_rows_bodyfree_valid"] is True
    assert material["rating_rows_bodyfree_valid"] is True
    assert material["question_need_observation_rows_bodyfree_valid"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["reviewer_free_text_included"] is False
    assert material["p8_question_spec_created"] is False
    assert material["p8_question_trigger_created"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF
    _assert_op09_does_not_create_or_execute(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op09_marks_incomplete_rows_without_claiming_actual_rows_complete() -> None:
    rows = _complete_row_sets()
    rows[0].pop()
    material = _op09(_op08(_complete_receipt()), rows=rows)

    assert material["row_schema_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF
    assert material["sanitized_review_result_row_count"] == alr.P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT - 1
    assert material["rows_complete_candidate"] is False
    assert material["rows_missing_or_incomplete"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op09_rejects_question_text_payload_without_preserving_body_value() -> None:
    rows = _complete_row_sets()
    bad_question_rows = deepcopy(rows[2])
    bad_question_rows[0]["question_text"] = "body-value-must-not-survive"
    material = _op09(_op08(_complete_receipt()), rows=(rows[0], rows[1], bad_question_rows))

    assert material["row_schema_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF
    assert material["rows_repair_required"] is True
    assert material["row_forbidden_payload_key_paths"] == ["row_group[2][0].question_text"]
    assert "body-value-must-not-survive" not in repr(material)
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op09_contract_rejects_question_text_included_flag_opened() -> None:
    material = _op09(_op08())
    material["question_text_included"] = True

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(material)


def test_alr_op08_op09_aliases_match_full_design_title_names() -> None:
    op08 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op08_actual_operation_receipt_expected_schema_completeness_guard(
        alr_op07_bodyfull_packet_request_bodyfree_envelope=_ready_op07(),
    )
    op09 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard(
        alr_op08_actual_operation_receipt_expected_schema_completeness_guard=op08,
    )

    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(op08) is True
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(op09) is True
    assert op08["actual_operation_receipt_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF
    assert op09["row_schema_guard_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF


def test_alr_op00_to_op09_retry_path_stays_bodyfree_without_receipt_rows_or_review_execution() -> None:
    op08 = _op08()
    op09 = _op09(op08)

    assert tuple(op08["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_IMPLEMENTED_STEPS
    assert tuple(op09["implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_IMPLEMENTED_STEPS
    assert tuple(op08["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP08_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(op09["not_yet_implemented_steps"]) == alr.P7_R54_AHR_POST_DMD08_ALR_OP09_NOT_YET_IMPLEMENTED_STEPS
    for material in (op08, op09):
        assert material["not_claimed_boundary"]["actual_body_full_packet_generation"] is False
        assert material["not_claimed_boundary"]["actual_local_human_review_execution"] is False
        assert material["not_claimed_boundary"]["actual_rows_creation"] is False
        assert material["not_claimed_boundary"]["actual_disposal_purge_execution"] is False
        assert material["p8_start_allowed"] is False
        assert material["release_allowed"] is False


def test_alr_op08_op09_result_memo_exists_and_remains_bodyfree() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP09_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    assert "ALR-OP08: actual operation receipt expected schema / completeness guard" in text
    assert "ALR-OP09: selection-only rows / rating / question need expected schema guard" in text
    assert "actual_operation_receipt_created_here: false" in text
    assert "actual_rows_created_here: false" in text
    assert "actual_local_human_review_execution: false" in text
    assert "p8_question_design: false" in text
    assert "release_decision: false" in text
    assert "raw_input:" not in text
    assert "question_text:" not in text
