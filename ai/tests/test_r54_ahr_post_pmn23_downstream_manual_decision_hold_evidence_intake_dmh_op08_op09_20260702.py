# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP08/OP09 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op06_op07_20260702 as dmh_op06_op07_prev

_READY_OP07_CACHE: dict[str, object] | None = None
_READY_OP08_CACHE: dict[str, object] | None = None
_READY_OP09_CACHE: dict[str, object] | None = None


def _ready_op07() -> dict[str, object]:
    global _READY_OP07_CACHE
    if _READY_OP07_CACHE is None:
        material = dmh_op06_op07_prev._ready_op07()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(material) is True
        _READY_OP07_CACHE = material
    return deepcopy(_READY_OP07_CACHE)


def _ready_state_capture(op07: dict[str, object] | None = None) -> dict[str, object]:
    if op07 is None:
        op07 = _ready_op07()
    capture = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_review_lifecycle_state_capture_bodyfree(
        review_session_id=str(op07["review_session_id"]),
        reviewer_person_ref=str(op07["reviewer_person_ref"]),
    )
    assert capture["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_LIFECYCLE_STATE_CAPTURE_SCHEMA_VERSION
    assert capture["body_free"] is True
    return capture


def _ready_op08() -> dict[str, object]:
    global _READY_OP08_CACHE
    if _READY_OP08_CACHE is None:
        op07 = _ready_op07()
        capture = _ready_state_capture(op07)
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
            reviewer_person_confirmation_selection_only_form_finalization=op07,
            review_lifecycle_state_capture_bodyfree=capture,
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(material) is True
        _READY_OP08_CACHE = material
    return deepcopy(_READY_OP08_CACHE)


def _ready_operation_receipt(op08: dict[str, object] | None = None) -> dict[str, object]:
    if op08 is None:
        op08 = _ready_op08()
    receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_bodyfree(
        review_session_id=str(op08["review_session_id"]),
        review_state_capture_ref=str(op08["review_state_capture_ref"]),
        reviewer_person_ref=str(op08["reviewer_person_ref"]),
        review_started_bucket_ref=str(op08["review_started_bucket_ref"]),
        review_completed_bucket_ref=str(op08["review_completed_bucket_ref"]),
    )
    assert receipt["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION
    assert receipt["body_free"] is True
    return receipt


def _ready_op09() -> dict[str, object]:
    global _READY_OP09_CACHE
    if _READY_OP09_CACHE is None:
        op08 = _ready_op08()
        receipt = _ready_operation_receipt(op08)
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
            actual_review_operation_state_machine_pause_abort_lifecycle=op08,
            actual_operation_receipt_bodyfree=receipt,
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True
        _READY_OP09_CACHE = material
    return deepcopy(_READY_OP09_CACHE)


def _assert_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def test_dmh_op08_state_capture_shape_is_bodyfree_completed_lifecycle() -> None:
    op07 = _ready_op07()
    capture = _ready_state_capture(op07)

    assert set(capture) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_STATE_CAPTURE_FIELD_REFS)
    assert capture["review_state_capture_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_CAPTURE_REF
    assert capture["review_session_id"] == op07["review_session_id"]
    assert capture["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert capture["actual_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_ACTUAL_SOURCE_REF
    assert capture["reviewer_person_ref"] == op07["reviewer_person_ref"]
    assert capture["reviewer_is_person"] is True
    assert capture["reviewer_person_confirmed"] is True
    assert capture["reviewer_local_only_read_receipt_present"] is True
    assert capture["review_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF
    assert capture["reviewed_case_count"] == 24
    assert capture["selection_row_count"] == 24
    assert capture["pause_abort_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF
    assert capture["body_purge_required_on_abort"] is False
    assert capture["body_purged_on_abort"] is False
    assert capture["local_only"] is True
    assert capture["must_not_export"] is True
    assert capture["selection_only"] is True
    assert capture["actual_human_review_executed_by_person"] is True
    for key in (
        "reviewer_free_text_exported",
        "reviewer_notes_body_exported",
        "body_quotation_exported",
        "question_text_materialized_in_review",
        "draft_question_text_materialized_in_review",
        "packet_content_exported",
        "body_full_packet_content_exported",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
    ):
        assert capture[key] is False, key


def test_dmh_op08_accepts_completed_state_capture_and_allows_operation_receipt_intake_next() -> None:
    material = _ready_op08()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_ACTUAL_REVIEW_OPERATION_STATE_MACHINE_PAUSE_ABORT_LIFECYCLE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF
    assert material["dmh_op08_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF
    assert material["dmh_op08_ready"] is True
    assert material["dmh_op08_blocker_refs"] == []
    assert tuple(material["dmh_op08_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_READY_REASON_REFS
    assert material["op07_dmh_ready"] is True
    assert material["op07_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF
    assert material["review_state_capture_received_here"] is True
    assert material["review_state_capture_intaked_here"] is True
    assert material["review_state_capture_source_ref_allowed"] is True
    assert material["review_state_capture_bodyfree_only"] is True
    assert material["review_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF
    assert material["review_state_is_completed_selection_rows_ready"] is True
    assert material["review_state_is_paused_local_only"] is False
    assert material["review_state_is_aborted_body_purged"] is False
    assert material["pause_abort_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF
    assert material["review_started_bucket_ref_present"] is True
    assert material["review_completed_bucket_ref_present"] is True
    assert material["reviewer_person_ref_matches_op07"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["operation_receipt_intake_allowed_next"] is True
    assert material["actual_operation_receipt_still_not_received"] is True
    assert material["actual_review_rows_still_not_created"] is True
    assert material["actual_disposal_purge_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert material["dmh_op08_does_not_create_actual_operation_receipt_or_rows_or_disposal"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op08_blocks_without_state_capture_and_keeps_operation_receipt_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=_ready_op07()
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_FIELD_REFS)
    assert material["dmh_op08_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_STATUS_REF
    assert material["dmh_op08_ready"] is False
    assert "dmh_op08_review_lifecycle_state_capture_not_received" in material["dmh_op08_blocker_refs"]
    assert material["review_state_capture_received_here"] is False
    assert material["review_state_capture_intaked_here"] is False
    assert material["operation_receipt_intake_allowed_next"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op08_paused_lifecycle_is_accepted_as_pause_state_but_not_operation_receipt_ready() -> None:
    op07 = _ready_op07()
    capture = _ready_state_capture(op07)
    capture["review_state_ref"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF
    capture["pause_abort_status_ref"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_PAUSED_REF

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=capture,
    )

    assert material["dmh_op08_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF
    assert material["dmh_op08_ready"] is False
    assert "dmh_op08_state_capture_review_state_paused_operation_receipt_not_allowed_yet" in material["dmh_op08_blocker_refs"]
    assert material["review_state_is_paused_local_only"] is True
    assert material["operation_receipt_intake_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op08_aborted_lifecycle_requires_body_purged_and_does_not_allow_operation_receipt() -> None:
    op07 = _ready_op07()
    capture = _ready_state_capture(op07)
    capture["review_state_ref"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF
    capture["pause_abort_status_ref"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_ABORTED_PURGED_REF
    capture["body_purge_required_on_abort"] = True
    capture["body_purged_on_abort"] = True

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=capture,
    )

    assert material["dmh_op08_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF
    assert material["dmh_op08_ready"] is False
    assert "dmh_op08_state_capture_review_state_aborted_operation_receipt_not_allowed_yet" in material["dmh_op08_blocker_refs"]
    assert material["review_state_is_aborted_body_purged"] is True
    assert material["body_purge_required_on_abort"] is True
    assert material["body_purged_on_abort"] is True
    assert material["operation_receipt_intake_allowed_next"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op08_blocks_state_capture_with_forbidden_body_question_path_hash_key() -> None:
    op07 = _ready_op07()
    capture = _ready_state_capture(op07)
    capture["reviewer_notes"] = "must never be accepted"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=capture,
    )

    assert material["dmh_op08_ready"] is False
    assert material["dmh_op08_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_BY_LEAK_STATUS_REF
    assert "dmh_op08_state_capture_forbidden_body_question_path_hash_key_detected" in material["dmh_op08_blocker_refs"]
    assert material["review_state_capture_forbidden_payload_key_paths"] == ["review_lifecycle_state_capture.reviewer_notes"]
    assert material["operation_receipt_intake_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("actual_source_ref", "wrong_source", "dmh_op08_state_capture_actual_source_ref_not_allowed"),
        ("review_session_id", "wrong_session", "dmh_op08_state_capture_review_session_id_mismatch"),
        ("actual_review_basis_ref", "wrong_basis", "dmh_op08_state_capture_actual_review_basis_ref_mismatch"),
        ("reviewer_person_ref", "other_reviewer", "dmh_op08_state_capture_reviewer_person_ref_mismatch"),
        ("reviewer_person_ref", "local/path/reviewer", "dmh_op08_state_capture_reviewer_person_ref_path_shape"),
        ("reviewer_is_person", False, "dmh_op08_state_capture_reviewer_is_person_not_true"),
        ("reviewer_person_confirmed", False, "dmh_op08_state_capture_reviewer_person_confirmed_not_true"),
        ("reviewer_local_only_read_receipt_present", False, "dmh_op08_state_capture_reviewer_local_only_read_receipt_missing"),
        ("actual_human_review_executed_by_person", False, "dmh_op08_state_capture_actual_human_review_executed_by_person_not_true"),
        ("review_state_ref", "UNKNOWN_REVIEW_STATE", "dmh_op08_state_capture_review_state_ref_not_allowed"),
        ("pause_abort_status_ref", "UNKNOWN_PAUSE_ABORT", "dmh_op08_state_capture_pause_abort_status_ref_not_allowed"),
        ("review_started_bucket_ref", "local/path/start", "dmh_op08_state_capture_review_started_bucket_ref_path_shape"),
        ("review_completed_bucket_ref", "local/path/complete", "dmh_op08_state_capture_review_completed_bucket_ref_path_shape"),
        ("reviewed_case_count", 23, "dmh_op08_state_capture_reviewed_case_count_not_24"),
        ("selection_row_count", 23, "dmh_op08_state_capture_selection_row_count_not_24"),
        ("local_only", False, "dmh_op08_state_capture_local_only_not_true"),
        ("must_not_export", False, "dmh_op08_state_capture_must_not_export_not_true"),
        ("selection_only", False, "dmh_op08_state_capture_selection_only_not_true"),
        ("question_text_materialized_in_review", True, "dmh_op08_state_capture_question_text_materialized_in_review_not_false"),
        ("packet_content_exported", True, "dmh_op08_state_capture_packet_content_exported_not_false"),
        ("body_hash_included", True, "dmh_op08_state_capture_body_hash_included_not_false"),
        ("row_created_by_helper", True, "dmh_op08_state_capture_row_created_by_helper_cannot_be_actual"),
    ],
)
def test_dmh_op08_blocks_invalid_state_capture_boundaries(field: str, bad_value: object, expected_blocker: str) -> None:
    op07 = _ready_op07()
    capture = _ready_state_capture(op07)
    capture[field] = bad_value

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=capture,
    )

    assert material["dmh_op08_ready"] is False
    assert expected_blocker in material["dmh_op08_blocker_refs"]
    assert material["operation_receipt_intake_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op08_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_STATUS_REF),
        ("dmh_op08_ready", False),
        ("review_state_capture_intaked_here", False),
        ("review_state_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF),
        ("reviewed_case_count", 23),
        ("selection_row_count", 23),
        ("operation_receipt_intake_allowed_next", False),
        ("actual_human_review_executed_by_person", False),
        ("raw_input_included", True),
        ("question_text_included", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op08_contract_rejects_ready_mutations_leaks_or_promotion(field: str, bad_value: object) -> None:
    material = _ready_op08()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(mutated)


def test_dmh_op09_operation_receipt_shape_is_bodyfree_and_matches_op08_refs() -> None:
    op08 = _ready_op08()
    receipt = _ready_operation_receipt(op08)

    assert set(receipt) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_OPERATION_RECEIPT_FIELD_REFS)
    assert receipt["operation_receipt_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_REF
    assert receipt["review_session_id"] == op08["review_session_id"]
    assert receipt["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert receipt["review_state_capture_ref"] == op08["review_state_capture_ref"]
    assert receipt["reviewer_person_ref"] == op08["reviewer_person_ref"]
    assert receipt["review_started_bucket_ref"] == op08["review_started_bucket_ref"]
    assert receipt["review_completed_bucket_ref"] == op08["review_completed_bucket_ref"]
    assert receipt["reviewed_case_count"] == 24
    assert receipt["selection_row_count"] == 24
    assert receipt["actual_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF
    assert receipt["local_only"] is True
    assert receipt["must_not_export"] is True
    assert receipt["selection_only"] is True
    for key in (
        "raw_input_included",
        "returned_emlis_body_included",
        "history_body_included",
        "comment_text_body_included",
        "reviewer_free_text_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "packet_content_included",
        "body_full_packet_content_included",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
    ):
        assert receipt[key] is False, key


def test_dmh_op09_accepts_actual_operation_receipt_without_creating_rows_or_promotion() -> None:
    material = _ready_op09()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF
    assert material["dmh_op09_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_READY_STATUS_REF
    assert material["dmh_op09_ready"] is True
    assert material["dmh_op09_blocker_refs"] == []
    assert tuple(material["dmh_op09_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_READY_REASON_REFS
    assert material["op08_dmh_ready"] is True
    assert material["op08_next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF
    assert material["operation_receipt_received_here"] is True
    assert material["operation_receipt_intaked_here"] is True
    assert material["operation_receipt_ref_present"] is True
    assert material["operation_receipt_ref_is_bodyfree_ref"] is True
    assert material["review_state_capture_ref_matches_op08"] is True
    assert material["reviewer_person_ref_matches_op08"] is True
    assert material["review_started_bucket_ref_matches_op08"] is True
    assert material["review_completed_bucket_ref_matches_op08"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["actual_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF
    assert material["actual_source_guard_passed"] is True
    assert material["operation_receipt_confirms_actual_person_local_only_review"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["sanitized_review_result_rows_intake_required_next"] is True
    assert material["sanitized_review_result_rows_created_here"] is False
    assert material["rating_rows_created_here"] is False
    assert material["question_need_observation_rows_created_here"] is False
    assert material["disposal_receipt_created_here"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert material["dmh_op09_does_not_create_sanitized_rows_or_rating_rows_or_question_rows"] is True
    assert material["dmh_op09_does_not_create_disposal_receipt"] is True
    assert material["dmh_op09_does_not_start_p8_p6_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op09_blocks_without_operation_receipt() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
        actual_review_operation_state_machine_pause_abort_lifecycle=_ready_op08()
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_FIELD_REFS)
    assert material["dmh_op09_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_STATUS_REF
    assert material["dmh_op09_ready"] is False
    assert "dmh_op09_actual_operation_receipt_not_received" in material["dmh_op09_blocker_refs"]
    assert material["operation_receipt_received_here"] is False
    assert material["operation_receipt_intaked_here"] is False
    assert material["sanitized_review_result_rows_intake_required_next"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op09_blocks_when_op08_is_paused_not_completed() -> None:
    op07 = _ready_op07()
    capture = _ready_state_capture(op07)
    capture["review_state_ref"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF
    capture["pause_abort_status_ref"] = dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_PAUSED_REF
    op08 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=capture,
    )
    receipt = _ready_operation_receipt(_ready_op08())

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
        actual_review_operation_state_machine_pause_abort_lifecycle=op08,
        actual_operation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op09_ready"] is False
    assert "dmh_op09_op08_actual_review_operation_state_machine_not_ready" in material["dmh_op09_blocker_refs"]
    assert "dmh_op09_op08_next_step_not_actual_operation_receipt_intake" in material["dmh_op09_blocker_refs"]
    assert material["operation_receipt_intaked_here"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True


def test_dmh_op09_blocks_operation_receipt_with_forbidden_body_question_path_hash_key() -> None:
    op08 = _ready_op08()
    receipt = _ready_operation_receipt(op08)
    receipt["raw_input"] = "must never be accepted"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
        actual_review_operation_state_machine_pause_abort_lifecycle=op08,
        actual_operation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op09_ready"] is False
    assert material["dmh_op09_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_BY_LEAK_STATUS_REF
    assert "dmh_op09_operation_receipt_forbidden_body_question_path_hash_key_detected" in material["dmh_op09_blocker_refs"]
    assert material["operation_receipt_forbidden_payload_key_paths"] == ["actual_operation_receipt.raw_input"]
    assert material["operation_receipt_intaked_here"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("actual_source_ref", "wrong_source", "dmh_op09_operation_receipt_actual_source_ref_not_allowed"),
        ("review_session_id", "wrong_session", "dmh_op09_operation_receipt_review_session_id_mismatch"),
        ("actual_review_basis_ref", "wrong_basis", "dmh_op09_operation_receipt_actual_review_basis_ref_mismatch"),
        ("operation_receipt_ref", "", "dmh_op09_operation_receipt_ref_missing"),
        ("operation_receipt_ref", "local/path/receipt", "dmh_op09_operation_receipt_ref_path_shape"),
        ("review_state_capture_ref", "wrong_state_capture", "dmh_op09_operation_receipt_review_state_capture_ref_mismatch"),
        ("reviewer_person_ref", "other_reviewer", "dmh_op09_operation_receipt_reviewer_person_ref_mismatch"),
        ("reviewer_person_ref", "local/path/reviewer", "dmh_op09_operation_receipt_reviewer_person_ref_path_shape"),
        ("reviewer_is_person", False, "dmh_op09_operation_receipt_reviewer_is_person_not_true"),
        ("reviewer_person_confirmed", False, "dmh_op09_operation_receipt_reviewer_person_confirmed_not_true"),
        ("reviewer_local_only_read_receipt_present", False, "dmh_op09_operation_receipt_reviewer_local_only_read_receipt_present_not_true"),
        ("review_started_bucket_ref", "other_started", "dmh_op09_operation_receipt_review_started_bucket_ref_mismatch"),
        ("review_started_bucket_ref", "local/path/start", "dmh_op09_operation_receipt_review_started_bucket_ref_path_shape"),
        ("review_completed_bucket_ref", "other_completed", "dmh_op09_operation_receipt_review_completed_bucket_ref_mismatch"),
        ("review_completed_bucket_ref", "local/path/complete", "dmh_op09_operation_receipt_review_completed_bucket_ref_path_shape"),
        ("reviewed_case_count", 23, "dmh_op09_operation_receipt_reviewed_case_count_not_24"),
        ("selection_row_count", 23, "dmh_op09_operation_receipt_selection_row_count_not_24"),
        ("local_only", False, "dmh_op09_operation_receipt_local_only_not_true"),
        ("must_not_export", False, "dmh_op09_operation_receipt_must_not_export_not_true"),
        ("selection_only", False, "dmh_op09_operation_receipt_selection_only_not_true"),
        ("question_text_included", True, "dmh_op09_operation_receipt_question_text_included_not_false"),
        ("packet_content_included", True, "dmh_op09_operation_receipt_packet_content_included_not_false"),
        ("body_hash_included", True, "dmh_op09_operation_receipt_body_hash_included_not_false"),
    ],
)
def test_dmh_op09_blocks_invalid_operation_receipt_boundaries(field: str, bad_value: object, expected_blocker: str) -> None:
    op08 = _ready_op08()
    receipt = _ready_operation_receipt(op08)
    receipt[field] = bad_value

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
        actual_review_operation_state_machine_pause_abort_lifecycle=op08,
        actual_operation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op09_ready"] is False
    assert expected_blocker in material["dmh_op09_blocker_refs"]
    assert material["operation_receipt_intaked_here"] is False
    assert material["sanitized_review_result_rows_intake_required_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op09_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_STATUS_REF),
        ("dmh_op09_ready", False),
        ("operation_receipt_intaked_here", False),
        ("operation_receipt_ref_present", False),
        ("review_state_capture_ref_matches_op08", False),
        ("reviewer_person_ref_matches_op08", False),
        ("review_started_bucket_ref_matches_op08", False),
        ("review_completed_bucket_ref_matches_op08", False),
        ("reviewed_case_count", 23),
        ("selection_row_count", 23),
        ("actual_source_guard_passed", False),
        ("operation_receipt_confirms_actual_person_local_only_review", False),
        ("actual_human_review_executed_by_person", False),
        ("sanitized_review_result_rows_intake_required_next", False),
        ("sanitized_review_result_rows_created_here", True),
        ("question_text_included", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF),
    ],
)
def test_dmh_op09_contract_rejects_ready_mutations_rows_leaks_or_promotion(field: str, bad_value: object) -> None:
    material = _ready_op09()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(mutated)


def test_dmh_op08_op09_aliases_match_primary_builders_and_contracts() -> None:
    op07 = _ready_op07()
    primary_capture = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_review_lifecycle_state_capture_bodyfree(
        review_session_id=str(op07["review_session_id"]),
        reviewer_person_ref=str(op07["reviewer_person_ref"]),
    )
    alias_capture = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_review_lifecycle_state_capture_bodyfree(
        review_session_id=str(op07["review_session_id"]),
        reviewer_person_ref=str(op07["reviewer_person_ref"]),
    )
    assert alias_capture == primary_capture

    primary_op08 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=primary_capture,
    )
    alias_op08 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_operation_state_machine_pause_abort_lifecycle_bodyfree(
        reviewer_person_confirmation_selection_only_form_finalization=op07,
        review_lifecycle_state_capture_bodyfree=primary_capture,
    )
    assert alias_op08 == primary_op08
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_operation_state_machine_pause_abort_lifecycle_bodyfree_contract(alias_op08) is True

    primary_receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_bodyfree(
        review_session_id=str(primary_op08["review_session_id"]),
        review_state_capture_ref=str(primary_op08["review_state_capture_ref"]),
        reviewer_person_ref=str(primary_op08["reviewer_person_ref"]),
        review_started_bucket_ref=str(primary_op08["review_started_bucket_ref"]),
        review_completed_bucket_ref=str(primary_op08["review_completed_bucket_ref"]),
    )
    alias_receipt = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_operation_receipt_bodyfree(
        review_session_id=str(primary_op08["review_session_id"]),
        review_state_capture_ref=str(primary_op08["review_state_capture_ref"]),
        reviewer_person_ref=str(primary_op08["reviewer_person_ref"]),
        review_started_bucket_ref=str(primary_op08["review_started_bucket_ref"]),
        review_completed_bucket_ref=str(primary_op08["review_completed_bucket_ref"]),
    )
    assert alias_receipt == primary_receipt

    primary_op09 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
        actual_review_operation_state_machine_pause_abort_lifecycle=primary_op08,
        actual_operation_receipt_bodyfree=primary_receipt,
    )
    alias_op09 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_operation_receipt_intake_bodyfree(
        actual_review_operation_state_machine_pause_abort_lifecycle=primary_op08,
        actual_operation_receipt_bodyfree=primary_receipt,
    )
    assert alias_op09 == primary_op09
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_operation_receipt_intake_bodyfree_contract(alias_op09) is True
