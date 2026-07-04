# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP08/OP09 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op06_op07_20260703 import (  # noqa: E501
    _assert_common_bodyfree_no_touch_no_promotion,
    _op06_passed,
)

_OP07_READY_CACHE: dict[str, object] | None = None
_OP08_COMPLETED_CACHE: dict[str, object] | None = None


def _op07_ready() -> dict[str, object]:
    global _OP07_READY_CACHE
    if _OP07_READY_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze(
            packet_completeness_export_denylist_scan_receipt=_op06_passed(),
            reviewer_person_ref="reviewer_person_bodyfree_ref_20260703",
            reviewer_is_person_confirmed=True,
            local_only_operation_confirmed=True,
        )
        assert material["reviewer_form_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP07_STATUS_READY_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op07_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True
        _OP07_READY_CACHE = material
    return deepcopy(_OP07_READY_CACHE)


def _valid_lifecycle_material(*, state_ref: str | None = None, reviewer_person_ref: str | None = None) -> dict[str, object]:
    op07 = _op07_ready()
    return {
        "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_OPERATION_LIFECYCLE_MATERIAL_SCHEMA_VERSION,
        "operation_lifecycle_ref": "elr_op08_operation_lifecycle_state_bodyfree_ref_20260703_v1",
        "review_session_id": elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_REVIEW_SESSION_ID,
        "reviewer_person_ref": reviewer_person_ref or str(op07["reviewer_person_ref"]),
        "operation_lifecycle_state_ref": state_ref or elr.P7_R54_AHR_POST_ALR12_ELR_OPERATION_STATE_COMPLETED_RECEIPT_WAITING_REF,
        "reviewer_is_person_confirmed": True,
        "local_only_operation_confirmed": True,
        "selection_only_form_used": True,
        "external_export_performed": False,
        "helper_executes_actual_review": False,
        "actual_review_execution_started_by_helper": False,
        "actual_review_execution_completed_by_helper": False,
        "operation_receipt_created_here": False,
        "reviewer_free_text_recorded": False,
        "reviewer_note_body_included": False,
        "question_text_created": False,
        "draft_question_text_created": False,
        "answer_text_included": False,
        "body_full_packet_exported": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "body_free": True,
    }


def _op08_completed() -> dict[str, object]:
    global _OP08_COMPLETED_CACHE
    if _OP08_COMPLETED_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
            reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
            operation_lifecycle_material_optional=_valid_lifecycle_material(),
        )
        assert material["operation_lifecycle_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_COMPLETED_RECEIPT_WAITING_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material) is True
        _OP08_COMPLETED_CACHE = material
    return deepcopy(_OP08_COMPLETED_CACHE)


def _valid_actual_operation_receipt(*, reviewer_person_ref: str | None = None) -> dict[str, object]:
    op08 = _op08_completed()
    return {
        "schema_version": elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": "elr_op09_actual_operation_receipt_bodyfree_ref_20260703_v1",
        "review_session_id": elr.P7_R54_AHR_POST_ALR12_ELR_DEFAULT_REVIEW_SESSION_ID,
        "source_kind_ref": elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "created_from_real_operation": True,
        "actual_human_review_executed_by_person": True,
        "reviewer_person_ref": reviewer_person_ref or str(op08["op07_reviewer_person_ref"]),
        "reviewed_case_count": elr.P7_R54_AHR_POST_ALR12_ELR_EXPECTED_REVIEW_CASE_COUNT,
        "selection_row_count": elr.P7_R54_AHR_POST_ALR12_ELR_EXPECTED_REVIEW_CASE_COUNT,
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


def test_elr_op08_missing_lifecycle_material_waits_without_executing_actual_review() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_SCHEMA_VERSION
    assert material["op07_reviewer_selection_form_ready"] is True
    assert material["operation_lifecycle_material_present"] is False
    assert material["operation_lifecycle_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_NOT_STARTED_OR_WAITING_REF
    assert material["operation_not_started_or_waiting"] is True
    assert material["actual_review_execution_allowed_here"] is False
    assert material["actual_review_operation_lifecycle_started_here"] is False
    assert material["helper_executes_actual_review"] is False
    assert material["actual_operation_receipt_required_next"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_CAPTURE_OPERATION_LIFECYCLE_STATE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("state_ref", "expected_status", "expected_next"),
    [
        (
            elr.P7_R54_AHR_POST_ALR12_ELR_OPERATION_STATE_IN_PROGRESS_REF,
            elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_IN_PROGRESS_BODYFREE_TRACKED_REF,
            elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_CONTINUE_OPERATION_UNTIL_RECEIPT_WAITING_REF,
        ),
        (
            elr.P7_R54_AHR_POST_ALR12_ELR_OPERATION_STATE_PAUSED_REF,
            elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_PAUSED_BODYFREE_TRACKED_REF,
            elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_RESUME_OPERATION_OR_CAPTURE_UPDATED_STATE_REF,
        ),
        (
            elr.P7_R54_AHR_POST_ALR12_ELR_OPERATION_STATE_COMPLETED_RECEIPT_WAITING_REF,
            elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_COMPLETED_RECEIPT_WAITING_REF,
            elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STEP_REF,
        ),
    ],
)
def test_elr_op08_tracks_lifecycle_state_bodyfree_without_receipt_or_rows_claim(
    state_ref: str, expected_status: str, expected_next: str
) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
        operation_lifecycle_material_optional=_valid_lifecycle_material(state_ref=state_ref),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP08_REQUIRED_FIELD_REFS)
    assert material["operation_lifecycle_status_ref"] == expected_status
    assert material["operation_lifecycle_state_ref"] == state_ref
    assert material["helper_executes_actual_review"] is False
    assert material["operation_receipt_created_here"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == expected_next
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op08_completed_receipt_waiting_requires_operation_receipt_next_but_does_not_accept_it_here() -> None:
    material = _op08_completed()

    assert material["operation_completed_receipt_waiting"] is True
    assert material["actual_operation_receipt_required_next"] is True
    assert material["actual_operation_receipt_intake_required_next"] is True
    assert material["operation_receipt_required_for_completed_claim"] is True
    assert material["operation_receipt_created_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("helper_executes_actual_review", True, "elr_op08_helper_executes_actual_review"),
        ("actual_review_execution_started_by_helper", True, "elr_op08_actual_review_started_by_helper"),
        ("external_export_performed", True, "elr_op08_external_export_performed"),
        ("question_text_created", True, "elr_op08_question_text_created"),
        ("body_free", False, "elr_op08_operation_lifecycle_not_bodyfree"),
    ],
)
def test_elr_op08_invalid_lifecycle_material_goes_to_repair(field: str, bad_value: object, expected_blocker: str) -> None:
    lifecycle = _valid_lifecycle_material()
    lifecycle[field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
        operation_lifecycle_material_optional=lifecycle,
    )

    assert material["operation_lifecycle_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_ABORTED_OR_REPAIR_REQUIRED_REF
    assert expected_blocker in material["elr_op08_blocker_refs"]
    assert material["actual_operation_receipt_required_next"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material) is True


def test_elr_op08_forbidden_payload_in_lifecycle_is_repair_without_body_value() -> None:
    lifecycle = _valid_lifecycle_material()
    lifecycle["reviewer_note_body"] = "body-full reviewer note must never leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
        operation_lifecycle_material_optional=lifecycle,
    )

    assert material["operation_lifecycle_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_ABORTED_OR_REPAIR_REQUIRED_REF
    assert material["operation_lifecycle_forbidden_payload_key_paths"] == ["operation_lifecycle.reviewer_note_body"]
    assert "must never leak" not in repr(material)
    assert "elr_op08_operation_lifecycle_forbidden_payload_key_detected" in material["elr_op08_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material) is True


def test_elr_op08_invalid_op07_goes_to_repair() -> None:
    op07 = _op07_ready()
    op07["p8_start_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=op07,
        operation_lifecycle_material_optional=_valid_lifecycle_material(),
    )

    assert material["operation_lifecycle_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP08_STATUS_ABORTED_OR_REPAIR_REQUIRED_REF
    assert "elr_op08_op07_reviewer_form_contract_invalid_or_missing" in material["elr_op08_blocker_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("operation_completed_receipt_waiting", False),
        ("actual_operation_receipt_required_next", False),
        ("operation_receipt_created_here", True),
        ("helper_executes_actual_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op08_contract_rejects_completed_lifecycle_mutations(field: str, bad_value: object) -> None:
    material = _op08_completed()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture_contract(material)


def test_elr_op09_missing_actual_operation_receipt_waits_without_rows_or_complete_claim() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=_op08_completed(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_SCHEMA_VERSION
    assert material["op08_operation_completed_receipt_waiting"] is True
    assert material["actual_operation_receipt_present"] is False
    assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_MISSING_WAITING_REF
    assert material["actual_operation_receipt_accepted"] is False
    assert material["ready_for_sanitized_review_result_rows_intake"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_PROVIDE_ACTUAL_OPERATION_RECEIPT_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_elr_op09_accepts_bodyfree_actual_operation_receipt_without_rows_or_downstream_promotion() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=_op08_completed(),
        actual_operation_receipt_optional=_valid_actual_operation_receipt(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP09_REQUIRED_FIELD_REFS)
    assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_ACCEPTED_BODYFREE_REF
    assert material["actual_operation_receipt_accepted"] is True
    assert material["source_kind_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_REVIEW_SOURCE_KIND_REF
    assert material["source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["created_from_real_operation"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["local_only_operation_confirmed"] is True
    assert material["selection_only_form_used"] is True
    assert material["actual_operation_receipt_intake_bodyfree_accepted_without_rows"] is True
    assert material["sanitized_rows_intake_required_next"] is True
    assert material["actual_rows_created_here_by_helper"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP10_STEP_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("source_kind_ref", "synthetic_rows", "elr_op09_source_kind_not_actual_local_only_human_review_by_person"),
        ("created_from_real_operation", False, "elr_op09_created_from_real_operation_mismatch"),
        ("reviewed_case_count", 23, "elr_op09_reviewed_case_count_mismatch"),
        ("selection_row_count", 23, "elr_op09_selection_row_count_mismatch"),
        ("external_export_performed", True, "elr_op09_external_export_performed_mismatch"),
        ("question_text_included", True, "elr_op09_question_text_included_mismatch"),
        ("body_free", False, "elr_op09_body_free_mismatch"),
    ],
)
def test_elr_op09_invalid_receipt_goes_to_invalid_or_incomplete(field: str, bad_value: object, expected_blocker: str) -> None:
    receipt = _valid_actual_operation_receipt()
    receipt[field] = bad_value
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=_op08_completed(),
        actual_operation_receipt_optional=receipt,
    )

    assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_INVALID_OR_INCOMPLETE_REF
    assert expected_blocker in material["elr_op09_blocker_refs"]
    assert material["actual_operation_receipt_accepted"] is False
    assert material["ready_for_sanitized_review_result_rows_intake"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True


def test_elr_op09_forbidden_payload_in_actual_operation_receipt_is_invalid_without_body_value() -> None:
    receipt = _valid_actual_operation_receipt()
    receipt["raw_input"] = "body-full actual operation receipt content must never leak"
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=_op08_completed(),
        actual_operation_receipt_optional=receipt,
    )

    assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_INVALID_OR_INCOMPLETE_REF
    assert material["actual_operation_receipt_forbidden_payload_key_paths"] == ["actual_operation_receipt.raw_input"]
    assert "must never leak" not in repr(material)
    assert "elr_op09_actual_operation_receipt_forbidden_payload_key_detected" in material["elr_op09_blocker_refs"]
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True


def test_elr_op09_rejects_receipt_before_completed_lifecycle_state() -> None:
    op08 = elr.build_p7_r54_ahr_post_alr12_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
        operation_lifecycle_material_optional=_valid_lifecycle_material(
            state_ref=elr.P7_R54_AHR_POST_ALR12_ELR_OPERATION_STATE_IN_PROGRESS_REF
        ),
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=op08,
        actual_operation_receipt_optional=_valid_actual_operation_receipt(),
    )

    assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op09_actual_operation_receipt_provided_before_completed_receipt_waiting_lifecycle" in material["elr_op09_blocker_refs"]
    assert material["actual_operation_receipt_accepted"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True


def test_elr_op09_invalid_op08_goes_to_repair() -> None:
    op08 = _op08_completed()
    op08["release_allowed"] = True
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=op08,
        actual_operation_receipt_optional=_valid_actual_operation_receipt(),
    )

    assert material["actual_operation_receipt_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP09_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op09_op08_lifecycle_contract_invalid_or_missing" in material["elr_op09_blocker_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_ELR_OPERATION_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("actual_operation_receipt_accepted", False),
        ("reviewed_case_count", 23),
        ("selection_row_count", 23),
        ("actual_rows_created_here_by_helper", True),
        ("actual_review_evidence_complete_here", True),
        ("p8_start_allowed", True),
    ],
)
def test_elr_op09_contract_rejects_accepted_receipt_mutations(field: str, bad_value: object) -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=_op08_completed(),
        actual_operation_receipt_optional=_valid_actual_operation_receipt(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op09_actual_operation_receipt_intake_contract(material)


def test_elr_op08_op09_alias_builders_and_contracts_match_canonical_functions() -> None:
    op08 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op08_actual_review_operation_lifecycle_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=_op07_ready(),
        operation_lifecycle_material_optional=_valid_lifecycle_material(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op08_actual_review_operation_lifecycle_state_capture_contract(op08) is True

    op09 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op09_actual_operation_receipt_intake(
        actual_review_operation_lifecycle_state_capture=op08,
        actual_operation_receipt_optional=_valid_actual_operation_receipt(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op09_actual_operation_receipt_intake_contract(op09) is True


def test_elr_op08_op09_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP09_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. Prior implementation confirmation",
        "## 4. ELR-OP08",
        "## 5. ELR-OP09",
        "## 6. Test results",
        "## 7. Not claimed",
        "## 8. Next required step",
    ):
        assert heading in text
    assert "ELR-OP10" in text
    assert "actual_local_human_review_execution_by_helper: false" in text
    assert "actual_operation_receipt_created_here: false" in text
    assert "actual_rows_created_here: false" in text
    assert "actual_review_evidence_complete: false" in text
    forbidden_literals = (
        "raw_input:",
        "comment_text:",
        "question_text:",
        "draft_question_text:",
        "terminal output body",
        "body-full actual operation receipt content must never leak",
    )
    for literal in forbidden_literals:
        assert literal not in text
