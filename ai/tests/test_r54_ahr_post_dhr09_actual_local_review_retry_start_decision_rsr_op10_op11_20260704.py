# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP10/OP11 receipt/rows-intake boundary tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_op03_20260704 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_op07_20260704 import (
    _rsr_op06_ready,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op08_op09_20260704 import (
    _rsr_op08_ready,
)


def _rsr_op09_completed_receipt_required() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(
        selection_only_reviewer_form_contract=_rsr_op08_ready(),
        lifecycle_status_ref=rsr.P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF,
        lifecycle_state_material={"body_free": True},
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(material) is True
    assert material["rsr_op09_ready_for_actual_operation_receipt_intake"] is True
    assert material["actual_operation_receipt_required"] is True
    return material


def _valid_actual_operation_receipt(op09: dict[str, object] | None = None) -> dict[str, object]:
    op09 = op09 or _rsr_op09_completed_receipt_required()
    op06 = _rsr_op06_ready()
    return {
        "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": "operation_receipt_bodyfree_ref_001",
        "review_session_id": op09["review_session_id"],
        "packet_request_ref": op06["packet_request_ref"],
        "source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "created_from_real_operation": True,
        "actual_human_review_executed_by_person": True,
        "reviewer_person_ref": op06["reviewer_person_ref"],
        "reviewed_case_count": rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "selection_row_count": rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "local_only_operation_confirmed": True,
        "selection_only_form_used": True,
        "external_export_performed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "answer_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _rsr_op10_accepted() -> dict[str, object]:
    op09 = _rsr_op09_completed_receipt_required()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake(
        actual_local_only_review_lifecycle_state_capture=op09,
        actual_operation_receipt=_valid_actual_operation_receipt(op09),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(material) is True
    assert material["rsr_op10_actual_operation_receipt_accepted"] is True
    assert material["ready_for_sanitized_review_result_rows_rating_rows_intake"] is True
    return material


def _valid_sanitized_and_rating_rows(op10: dict[str, object] | None = None) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    op10 = op10 or _rsr_op10_accepted()
    op06 = _rsr_op06_ready()
    axis_scores = {axis: 1.0 for axis in rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS}
    axis_pass_flags = {axis: True for axis in rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS}
    sanitized_rows: list[dict[str, object]] = []
    rating_rows: list[dict[str, object]] = []
    case_refs = list(op06["case_ref_values"])
    for index, case_ref in enumerate(case_refs, start=1):
        review_result_row_ref = f"review_result_row_ref_{index:03d}"
        sanitized_rows.append({
            "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
            "review_session_id": op10["review_session_id"],
            "operation_receipt_ref": op10["operation_receipt_ref"],
            "review_result_row_ref": review_result_row_ref,
            "case_ref": case_ref,
            "reviewer_person_ref": op10["reviewer_person_ref"],
            "source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
            "verdict_ref": "PASS",
            "axis_score_refs": dict(axis_scores),
            "axis_score_count": len(rsr.P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS),
            "axis_pass_flags": dict(axis_pass_flags),
            "sanitized_reason_id_refs": ["rsr_review_pass_selection_only"],
            "readfeel_blocker_id_refs": [],
            "execution_blocker_id_refs": [],
            "question_need_primary_class_ref": "no_question_needed_emlis_can_observe",
            "ambiguity_kind_refs": [],
            "one_question_fit_ref": "not_needed",
            "repair_required_refs": [],
            "selection_only": True,
            "row_created_by_helper": False,
            "row_created_for_unit_test": False,
            "row_is_synthetic_contract_fixture": False,
            "historical_row_reused": False,
            "body_free": True,
        })
        rating_rows.append({
            "schema_version": rsr.P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_SCHEMA_VERSION,
            "rating_row_ref": f"rating_row_ref_{index:03d}",
            "source_sanitized_review_result_row_ref": review_result_row_ref,
            "review_session_id": op10["review_session_id"],
            "operation_receipt_ref": op10["operation_receipt_ref"],
            "case_ref": case_ref,
            "verdict_ref": "PASS",
            "axis_score_refs": dict(axis_scores),
            "axis_pass_flags": dict(axis_pass_flags),
            "below_target_axis_refs": [],
            "readfeel_blocker_id_refs": [],
            "execution_blocker_id_refs": [],
            "repair_required_refs": [],
            "actual_rating_row_from_real_operation": True,
            "rating_decision_material_only": True,
            "body_free": True,
        })
    return sanitized_rows, rating_rows, case_refs


def _assert_op10_no_rows_or_promotion(material: dict[str, object]) -> None:
    assert material["helper_executes_actual_review"] is False
    assert material["actual_operation_receipt_created_here_by_helper"] is False
    assert material["actual_rows_created_here_by_helper"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["rsr_op10_does_not_run_actual_local_human_review"] is True
    assert material["rsr_op10_does_not_create_actual_operation_receipt"] is True
    assert material["rsr_op10_does_not_create_rows_question_rows_or_disposal"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def _assert_op11_no_question_or_promotion(material: dict[str, object]) -> None:
    assert material["rsr_op11_does_not_create_sanitized_rows_or_rating_rows"] is True
    assert material["rsr_op11_does_not_create_question_rows_or_disposal"] is True
    assert material["rsr_op11_does_not_materialize_question_text_or_p8_spec"] is True
    assert material["question_text_materialized"] is False
    assert material["draft_question_text_materialized"] is False
    assert material["p8_question_spec_created"] is False
    assert material["p8_question_design_started_here"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["actual_sanitized_review_result_rows_materialized_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_local_human_review_executed_here"] is False
    assert material["actual_operation_receipt_created_here"] is False
    assert material["actual_rows_created_here"] is False
    assert material["actual_disposal_purge_executed_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def test_rsr_op10_waits_for_receipt_after_completed_lifecycle_without_creating_any_receipt() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake(
        actual_local_only_review_lifecycle_state_capture=_rsr_op09_completed_receipt_required(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF
    assert material["op09_ready_for_actual_operation_receipt_intake"] is True
    assert material["actual_operation_receipt_present"] is False
    assert material["rsr_op10_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF
    assert material["rsr_op10_actual_operation_receipt_missing_waiting"] is True
    assert material["rsr_op10_actual_operation_receipt_accepted"] is False
    assert material["actual_operation_receipt_accepted_by_rsr_op10"] is False
    assert material["ready_for_sanitized_review_result_rows_rating_rows_intake"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_ACTUAL_OPERATION_RECEIPT_BODYFREE_REF
    _assert_op10_no_rows_or_promotion(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op10_accepts_bodyfree_actual_operation_receipt_without_rows_or_evidence_completion() -> None:
    material = _rsr_op10_accepted()

    assert material["rsr_op10_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF
    assert material["actual_operation_receipt_present"] is True
    assert material["operation_receipt_ref_present"] is True
    assert material["operation_receipt_review_session_id_matches"] is True
    assert material["source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["created_from_real_operation"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["local_only_operation_confirmed"] is True
    assert material["selection_only_form_used"] is True
    assert material["reviewed_case_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["selection_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["actual_operation_receipt_forbidden_payload_key_path_count"] == 0
    assert material["actual_operation_receipt_body_like_value_path_count"] == 0
    assert material["actual_operation_receipt_source_claim_blocker_ref_count"] == 0
    assert material["actual_operation_receipt_intake_bodyfree_accepted_without_rows"] is True
    assert material["sanitized_review_result_rows_and_rating_rows_required_next"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF
    _assert_op10_no_rows_or_promotion(material)
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("mutation", "expected_status", "expected_blocker", "leaked_text"),
    [
        ({"schema_version": "wrong_schema"}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF, "actual_operation_receipt_schema_version_mismatch", None),
        ({"raw_input": "body must not leak", "body_free": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "actual_operation_receipt_forbidden_payload_key_detected", "body must not leak"),
        ({"source_kind_ref": "helper_generated_candidate"}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "source_kind_not_actual_local_only_human_review_by_person", None),
        ({"reviewed_case_count": 23}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "reviewed_case_count_not_24", None),
        ({"actual_operation_receipt_created_here": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "actual_operation_receipt_promotion_claim_detected", None),
    ],
)
def test_rsr_op10_repairs_or_blocks_invalid_actual_operation_receipt(mutation: dict[str, object], expected_status: str, expected_blocker: str, leaked_text: str | None) -> None:
    op09 = _rsr_op09_completed_receipt_required()
    receipt = _valid_actual_operation_receipt(op09)
    receipt.update(mutation)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake(
        actual_local_only_review_lifecycle_state_capture=op09,
        actual_operation_receipt=receipt,
    )

    assert material["rsr_op10_status_ref"] == expected_status
    assert expected_blocker in material["op10_blocker_refs"]
    assert material["rsr_op10_actual_operation_receipt_accepted"] is False
    assert material["ready_for_sanitized_review_result_rows_rating_rows_intake"] is False
    assert material["next_required_step"] in (
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_BEFORE_ROWS_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF,
    )
    if leaked_text:
        assert leaked_text not in repr(material)
    _assert_op10_no_rows_or_promotion(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("helper_executes_actual_review", True),
        ("actual_operation_receipt_created_here_by_helper", True),
        ("actual_rows_created_here_by_helper", True),
        ("actual_review_evidence_complete_here", True),
        ("actual_operation_receipt_created_here", True),
        ("actual_rows_created_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF),
    ],
)
def test_rsr_op10_contract_rejects_receipt_creation_rows_completion_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op10_accepted()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(material)


def test_rsr_op11_waits_when_rows_missing_after_op10_receipt_accepted() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=_rsr_op10_accepted(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF
    assert material["op10_actual_operation_receipt_accepted"] is True
    assert material["sanitized_review_result_rows_present"] is False
    assert material["rating_rows_present"] is False
    assert material["rsr_op11_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF
    assert material["rsr_op11_rows_missing_waiting"] is True
    assert material["rsr_op11_sanitized_review_result_rows_accepted"] is False
    assert material["rsr_op11_rating_rows_accepted"] is False
    assert material["question_need_observation_rows_required_next"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_BODYFREE_REF
    _assert_op11_no_question_or_promotion(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rsr_op11_accepts_bodyfree_sanitized_review_result_rows_and_rating_rows_without_creating_next_rows_or_p8() -> None:
    op10 = _rsr_op10_accepted()
    sanitized_rows, rating_rows, case_refs = _valid_sanitized_and_rating_rows(op10)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=op10,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )

    assert material["rsr_op11_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF
    assert material["sanitized_review_result_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["rating_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["case_ref_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["case_refs_match_between_sanitized_and_rating_rows"] is True
    assert material["sanitized_rows_bodyfree_only"] is True
    assert material["sanitized_rows_selection_only"] is True
    assert material["sanitized_rows_have_actual_person_selection_only_provenance"] is True
    assert material["sanitized_rows_have_required_axis_scores"] is True
    assert material["sanitized_rows_have_allowed_question_observation_refs"] is True
    assert material["sanitized_rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["rating_rows_bodyfree_only"] is True
    assert material["rating_rows_from_sanitized_rows"] is True
    assert material["rating_rows_have_required_axis_scores"] is True
    assert material["rating_rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["rows_source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["review_rows_forbidden_payload_key_path_count"] == 0
    assert material["rating_rows_forbidden_payload_key_path_count"] == 0
    assert material["actual_review_rows_and_rating_rows_intaken_bodyfree"] is True
    assert material["question_need_observation_rows_required_next"] is True
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF
    _assert_op11_no_question_or_promotion(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("target", "mutation", "expected_status", "expected_blocker", "leaked_text"),
    [
        ("sanitized", {"raw_input": "row body must not leak"}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "sanitized_review_result_row_required_fields_mismatch", "row body must not leak"),
        ("sanitized", {"source_kind_ref": "helper_generated_candidate"}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "sanitized_review_result_row_source_kind_not_actual_local_only_human_review_by_person", None),
        ("sanitized", {"row_created_by_helper": True}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF, "sanitized_review_result_row_row_created_by_helper_not_false", None),
        ("rating", {"source_sanitized_review_result_row_ref": "mismatched_ref"}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF, "rating_row_source_sanitized_review_result_row_ref_mismatch", None),
        ("rating", {"question_text": "do not materialize a question"}, rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, "rating_row_required_fields_mismatch", "do not materialize a question"),
    ],
)
def test_rsr_op11_repairs_or_blocks_invalid_rows(target: str, mutation: dict[str, object], expected_status: str, expected_blocker: str, leaked_text: str | None) -> None:
    op10 = _rsr_op10_accepted()
    sanitized_rows, rating_rows, case_refs = _valid_sanitized_and_rating_rows(op10)
    if target == "sanitized":
        sanitized_rows = deepcopy(sanitized_rows)
        sanitized_rows[0].update(mutation)
    else:
        rating_rows = deepcopy(rating_rows)
        rating_rows[0].update(mutation)

    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=op10,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )

    assert material["rsr_op11_status_ref"] == expected_status
    assert expected_blocker in material["op11_blocker_refs"]
    assert material["rsr_op11_sanitized_review_result_rows_accepted"] is False
    assert material["rsr_op11_rating_rows_accepted"] is False
    assert material["actual_review_rows_and_rating_rows_intaken_bodyfree"] is False
    assert material["question_need_observation_rows_required_next"] is False
    assert material["next_required_step"] in (
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_ROWS_RATING_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF,
    )
    if leaked_text:
        assert leaked_text not in repr(material)
    _assert_op11_no_question_or_promotion(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rsr_op11_does_not_create_sanitized_rows_or_rating_rows", False),
        ("rsr_op11_does_not_create_question_rows_or_disposal", False),
        ("rsr_op11_does_not_materialize_question_text_or_p8_spec", False),
        ("question_text_materialized", True),
        ("draft_question_text_materialized", True),
        ("p8_question_spec_created", True),
        ("actual_review_evidence_complete_here", True),
        ("actual_sanitized_review_result_rows_materialized_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF),
    ],
)
def test_rsr_op11_contract_rejects_row_creation_question_materialization_or_promotion_mutations(field: str, bad_value: object) -> None:
    op10 = _rsr_op10_accepted()
    sanitized_rows, rating_rows, case_refs = _valid_sanitized_and_rating_rows(op10)
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=op10,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material) is True
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(material)


def test_rsr_op10_op11_full_title_aliases_match_canonical_builders() -> None:
    op09 = _rsr_op09_completed_receipt_required()
    receipt = _valid_actual_operation_receipt(op09)
    op10_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_actual_operation_receipt_intake(
        actual_local_only_review_lifecycle_state_capture=op09,
        actual_operation_receipt=receipt,
    )
    op10_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake(
        actual_local_only_review_lifecycle_state_capture=op09,
        actual_operation_receipt=receipt,
    )
    assert op10_alias == op10_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_actual_operation_receipt_intake_contract(op10_alias) is True

    sanitized_rows, rating_rows, case_refs = _valid_sanitized_and_rating_rows(op10_canonical)
    op11_alias = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=op10_canonical,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )
    op11_canonical = rsr.build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
        actual_operation_receipt_intake=op10_canonical,
        sanitized_review_result_rows=sanitized_rows,
        rating_rows=rating_rows,
        expected_case_refs=case_refs,
    )
    assert op11_alias == op11_canonical
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(op11_alias) is True
