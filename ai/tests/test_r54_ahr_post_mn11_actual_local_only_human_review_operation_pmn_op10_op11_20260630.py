# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP10/OP11 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op08_op09_20260630 as prev


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in pmn.P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_mn11_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    if "not_claimed_boundary" in material:
        assert all(value is False for value in material["not_claimed_boundary"].values())


def _ready_op09() -> dict[str, object]:
    return prev._ready_op09()


def _contract_fixture_state_capture(op09: dict[str, object]) -> dict[str, object]:
    return {
        "review_state_capture_ref": "postmn11_actual_review_state_capture_contract_fixture_001",
        "review_session_id": op09["review_session_id"],
        "actual_review_basis_ref": pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_source_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_ACTUAL_SOURCE_REF,
        "reviewer_person_ref": op09["reviewer_person_ref"],
        "reviewer_is_person": True,
        "reviewer_person_confirmed": True,
        "reviewer_local_only_read_receipt_present": True,
        "review_state_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP10_REVIEW_STATE_COMPLETED_SELECTION_ROWS_READY_REF,
        "review_started_at_bucket_ref": "review_started_bucket_20260630_local_only_contract_fixture",
        "review_completed_at_bucket_ref": "review_completed_bucket_20260630_local_only_contract_fixture",
        "reviewed_case_count": 24,
        "selection_row_count": 24,
        "local_only": True,
        "must_not_export": True,
        "selection_only": True,
        "actual_human_review_executed_by_person": True,
        "reviewer_free_text_exported": False,
        "reviewer_notes_body_exported": False,
        "body_quotation_exported": False,
        "question_text_materialized_in_review": False,
        "draft_question_text_materialized_in_review": False,
        "packet_content_exported": False,
        "body_full_packet_content_exported": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_body_included": False,
        "comment_text_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
        "body_free": True,
    }


def _ready_op10() -> dict[str, object]:
    op09 = _ready_op09()
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=op09,
        actual_review_execution_state_capture_bodyfree=_contract_fixture_state_capture(op09),
    )


def _contract_fixture_operation_receipt(op10: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "cocolon.emlis.p7_r54.ahr.post_mn11.actual_operation_receipt.bodyfree.v1",
        "operation_receipt_ref": "postmn11_actual_operation_receipt_contract_fixture_001",
        "review_session_id": op10["review_session_id"],
        "actual_review_basis_ref": pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "reviewer_person_ref": op10["reviewer_person_ref"],
        "reviewer_is_person": True,
        "reviewer_person_confirmed": True,
        "reviewer_local_only_read_receipt_present": True,
        "review_started_at_bucket_ref": op10["review_started_at_bucket_ref"],
        "review_completed_at_bucket_ref": op10["review_completed_at_bucket_ref"],
        "reviewed_case_count": 24,
        "selection_row_count": 24,
        "local_only": True,
        "must_not_export": True,
        "selection_only": True,
        "actual_source_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_body_included": False,
        "history_surface_included": False,
        "comment_text_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
        "body_free": True,
    }


def _ready_op11() -> dict[str, object]:
    op10 = _ready_op10()
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
        actual_24_case_human_review_execution_protocol_state_capture=op10,
        actual_operation_receipt_bodyfree=_contract_fixture_operation_receipt(op10),
    )


def test_pmn_op00_to_op09_implementation_is_present_before_op10_op11() -> None:
    op09 = _ready_op09()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(op09) is True
    assert op09["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF
    assert op09["reviewer_form_ready"] is True
    assert tuple(op09["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS
    assert tuple(op09["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch_no_promotion(op09)


def test_pmn_op10_blocks_without_actual_review_state_capture_and_does_not_promote_review() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_ready_op09()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_FIELD_REFS)
    assert material["review_execution_state_capture_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_STATUS_REF
    assert material["review_execution_state_capture_ready"] is False
    assert "pmn_op10_actual_human_review_execution_state_capture_not_received" in material["review_execution_state_capture_blocker_refs"]
    assert material["actual_review_state_capture_received_here"] is False
    assert material["actual_review_state_capture_intaked_here"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_operation_receipt_intake_allowed_next"] is False
    assert material["actual_operation_receipt_intaked_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op10_accepts_bodyfree_actual_review_state_capture_contract_fixture_without_body_or_question() -> None:
    material = _ready_op10()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_PROTOCOL_STATE_CAPTURE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF
    assert material["review_execution_state_capture_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_READY_STATUS_REF
    assert material["review_execution_state_capture_ready"] is True
    assert material["review_execution_state_capture_blocker_refs"] == []
    assert tuple(material["review_execution_state_capture_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_READY_REASON_REFS
    assert material["review_execution_protocol_bodyfree_only"] is True
    assert tuple(material["review_execution_protocol_step_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_PROTOCOL_STEP_REFS
    assert tuple(material["actual_review_state_capture_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_STATE_CAPTURE_FIELD_REFS
    assert material["actual_review_state_capture_received_here"] is True
    assert material["actual_review_state_capture_intaked_here"] is True
    assert material["actual_review_state_capture_source_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_ACTUAL_SOURCE_REF
    assert material["actual_review_state_capture_source_allowed"] is True
    assert material["review_state_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_REVIEW_STATE_COMPLETED_SELECTION_ROWS_READY_REF
    assert material["reviewer_person_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_matches_op09"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["review_started_at_bucket_ref_present"] is True
    assert material["review_completed_at_bucket_ref_present"] is True
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["selection_only"] is True
    assert material["reviewer_free_text_exported"] is False
    assert material["reviewer_notes_body_exported"] is False
    assert material["question_text_materialized_in_review"] is False
    assert material["draft_question_text_materialized_in_review"] is False
    assert material["packet_content_exported"] is False
    assert material["body_full_packet_content_exported"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["actual_operation_receipt_required_next"] is True
    assert material["operation_receipt_required_actual_source_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF
    assert material["actual_operation_receipt_intaked_here"] is False
    assert material["actual_sanitized_review_result_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("review_execution_state_capture_ready", False),
        ("actual_review_state_capture_source_allowed", False),
        ("reviewer_person_ref_matches_op09", False),
        ("reviewer_is_person", False),
        ("reviewer_person_confirmed", False),
        ("reviewer_local_only_read_receipt_present", False),
        ("actual_human_review_executed_by_person", False),
        ("reviewed_case_count", 23),
        ("selection_row_count", 23),
        ("local_only", False),
        ("must_not_export", False),
        ("selection_only", False),
        ("reviewer_free_text_exported", True),
        ("reviewer_notes_body_exported", True),
        ("question_text_materialized_in_review", True),
        ("draft_question_text_materialized_in_review", True),
        ("packet_content_exported", True),
        ("body_full_packet_content_exported", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("actual_operation_receipt_intaked_here", True),
        ("actual_sanitized_review_result_rows_materialized_here", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op10_contract_rejects_leak_count_review_receipt_rows_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op10()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(mutated)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("actual_source_ref", "unit_test_rows", "pmn_op10_state_capture_actual_source_ref_not_allowed"),
        ("reviewer_person_ref", "different_reviewer_ref", "pmn_op10_state_capture_reviewer_person_ref_mismatch"),
        ("reviewed_case_count", 23, "pmn_op10_state_capture_reviewed_case_count_not_24"),
        ("selection_row_count", 23, "pmn_op10_state_capture_selection_row_count_not_24"),
        ("local_only", False, "pmn_op10_state_capture_local_only_not_true"),
        ("question_text_included", True, "pmn_op10_state_capture_question_text_included_not_false"),
        ("body_hash_included", True, "pmn_op10_state_capture_body_hash_included_not_false"),
        ("row_created_for_unit_test", True, "pmn_op10_state_capture_row_created_for_unit_test_cannot_be_actual"),
    ],
)
def test_pmn_op10_blocks_state_capture_with_invalid_source_counts_leak_or_fixture_source(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    op09 = _ready_op09()
    capture = _contract_fixture_state_capture(op09)
    capture[field] = bad_value

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=op09,
        actual_review_execution_state_capture_bodyfree=capture,
    )

    assert material["review_execution_state_capture_ready"] is False
    assert expected_blocker in material["review_execution_state_capture_blocker_refs"]
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op11_blocks_without_actual_operation_receipt_and_does_not_create_rows_or_disposal() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
        actual_24_case_human_review_execution_protocol_state_capture=_ready_op10()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_FIELD_REFS)
    assert material["operation_receipt_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_STATUS_REF
    assert material["operation_receipt_accepted"] is False
    assert "pmn_op11_actual_operation_receipt_not_received" in material["operation_receipt_blocker_refs"]
    assert material["operation_receipt_received_here"] is False
    assert material["operation_receipt_intaked_here"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["sanitized_review_result_rows_intake_required_next"] is False
    assert material["sanitized_review_result_rows_created_here"] is False
    assert material["rating_rows_created_here"] is False
    assert material["question_need_observation_rows_created_here"] is False
    assert material["disposal_receipt_created_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op11_accepts_bodyfree_actual_operation_receipt_contract_fixture_without_rows_or_promotion() -> None:
    material = _ready_op11()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF
    assert material["operation_receipt_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_READY_STATUS_REF
    assert material["operation_receipt_accepted"] is True
    assert material["operation_receipt_blocker_refs"] == []
    assert tuple(material["operation_receipt_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_READY_REASON_REFS
    assert tuple(material["operation_receipt_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_OPERATION_RECEIPT_FIELD_REFS
    assert material["operation_receipt_received_here"] is True
    assert material["operation_receipt_intaked_here"] is True
    assert material["operation_receipt_confirms_actual_person_local_only_review"] is True
    assert material["actual_source_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF
    assert material["actual_source_guard_passed"] is True
    assert material["operation_receipt_ref_present"] is True
    assert material["operation_receipt_ref_is_bodyfree_ref"] is True
    assert material["operation_receipt_ref_has_local_path_shape"] is False
    assert material["reviewer_person_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_matches_op10"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["review_started_at_bucket_ref_matches_op10"] is True
    assert material["review_completed_at_bucket_ref_matches_op10"] is True
    assert material["reviewed_case_count"] == 24
    assert material["reviewed_case_count_matches_op10"] is True
    assert material["selection_row_count"] == 24
    assert material["selection_row_count_matches_op10"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["selection_only"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["sanitized_review_result_rows_intake_required_next"] is True
    assert material["sanitized_review_result_rows_created_here"] is False
    assert material["rating_rows_created_here"] is False
    assert material["question_need_observation_rows_created_here"] is False
    assert material["disposal_receipt_created_here"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("operation_receipt_accepted", False),
        ("operation_receipt_received_here", False),
        ("operation_receipt_intaked_here", False),
        ("operation_receipt_confirms_actual_person_local_only_review", False),
        ("actual_source_guard_passed", False),
        ("operation_receipt_ref_present", False),
        ("reviewer_person_ref_matches_op10", False),
        ("reviewer_is_person", False),
        ("reviewer_person_confirmed", False),
        ("reviewer_local_only_read_receipt_present", False),
        ("review_started_at_bucket_ref_matches_op10", False),
        ("review_completed_at_bucket_ref_matches_op10", False),
        ("reviewed_case_count", 23),
        ("selection_row_count", 23),
        ("local_only", False),
        ("must_not_export", False),
        ("selection_only", False),
        ("actual_human_review_executed_by_person", False),
        ("actual_human_review_run_here", True),
        ("sanitized_review_result_rows_intake_required_next", False),
        ("sanitized_review_result_rows_created_here", True),
        ("rating_rows_created_here", True),
        ("question_need_observation_rows_created_here", True),
        ("disposal_receipt_created_here", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("terminal_output_body_included", True),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op11_contract_rejects_receipt_leak_rows_disposal_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op11()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(mutated)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("actual_source_ref", "unit_test_rows", "pmn_op11_operation_receipt_actual_source_ref_not_allowed"),
        ("reviewer_person_ref", "different_reviewer_ref", "pmn_op11_operation_receipt_reviewer_person_ref_mismatch"),
        ("review_started_at_bucket_ref", "different_started_bucket", "pmn_op11_operation_receipt_review_started_bucket_ref_mismatch"),
        ("review_completed_at_bucket_ref", "different_completed_bucket", "pmn_op11_operation_receipt_review_completed_bucket_ref_mismatch"),
        ("reviewed_case_count", 23, "pmn_op11_operation_receipt_reviewed_case_count_not_24"),
        ("selection_row_count", 23, "pmn_op11_operation_receipt_selection_row_count_not_24"),
        ("local_only", False, "pmn_op11_operation_receipt_local_only_not_true"),
        ("question_text_included", True, "pmn_op11_operation_receipt_question_text_included_not_false"),
        ("body_hash_included", True, "pmn_op11_operation_receipt_body_hash_included_not_false"),
        ("row_created_for_unit_test", True, "pmn_op11_operation_receipt_row_created_for_unit_test_cannot_be_actual"),
    ],
)
def test_pmn_op11_blocks_receipt_with_invalid_source_count_leak_or_fixture_source(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    op10 = _ready_op10()
    receipt = _contract_fixture_operation_receipt(op10)
    receipt[field] = bad_value

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
        actual_24_case_human_review_execution_protocol_state_capture=op10,
        actual_operation_receipt_bodyfree=receipt,
    )

    assert material["operation_receipt_accepted"] is False
    assert expected_blocker in material["operation_receipt_blocker_refs"]
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op10_op11_aliases_match_primary_builders_and_contracts() -> None:
    op09 = _ready_op09()
    capture = _contract_fixture_state_capture(op09)
    primary_op10 = pmn.build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=op09,
        actual_review_execution_state_capture_bodyfree=capture,
    )
    alias_op10 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_actual_24_case_human_review_execution_protocol_state_capture_bodyfree(
        reviewer_person_boundary_selection_only_form_freeze=op09,
        actual_review_execution_state_capture_bodyfree=capture,
    )
    assert alias_op10 == primary_op10
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_actual_24_case_human_review_execution_protocol_state_capture_bodyfree_contract(alias_op10) is True

    receipt = _contract_fixture_operation_receipt(primary_op10)
    primary_op11 = pmn.build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
        actual_24_case_human_review_execution_protocol_state_capture=primary_op10,
        actual_operation_receipt_bodyfree=receipt,
    )
    alias_op11 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_actual_operation_receipt_intake_bodyfree(
        actual_24_case_human_review_execution_protocol_state_capture=primary_op10,
        actual_operation_receipt_bodyfree=receipt,
    )
    assert alias_op11 == primary_op11
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_actual_operation_receipt_intake_bodyfree_contract(alias_op11) is True
