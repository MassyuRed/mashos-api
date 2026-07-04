# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op04_op05_20260702 as dmh_op04_op05_prev

_READY_OP05_CACHE: dict[str, object] | None = None
_READY_OP06_CACHE: dict[str, object] | None = None
_READY_OP07_CACHE: dict[str, object] | None = None


def _ready_op05() -> dict[str, object]:
    global _READY_OP05_CACHE
    if _READY_OP05_CACHE is None:
        material = dmh_op04_op05_prev._ready_op05()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(material) is True
        _READY_OP05_CACHE = material
    return deepcopy(_READY_OP05_CACHE)


def _ready_scan_receipt(review_session_id: str | None = None, packet_generation_receipt_ref: str | None = None) -> dict[str, object]:
    receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_bodyfree(
        review_session_id=review_session_id,
        packet_generation_receipt_ref=packet_generation_receipt_ref,
    )
    assert receipt["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_SCHEMA_VERSION
    assert receipt["body_free"] is True
    return receipt


def _ready_op06() -> dict[str, object]:
    global _READY_OP06_CACHE
    if _READY_OP06_CACHE is None:
        op05 = _ready_op05()
        receipt = _ready_scan_receipt(str(op05["review_session_id"]), str(op05["packet_generation_receipt_ref"]))
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary(
            body_full_packet_generation_receipt_intake_boundary=op05,
            packet_scan_receipt_bodyfree=receipt,
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(material) is True
        _READY_OP06_CACHE = material
    return deepcopy(_READY_OP06_CACHE)


def _ready_reviewer_confirmation_receipt(review_session_id: str | None = None) -> dict[str, object]:
    receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_receipt_bodyfree(
        review_session_id=review_session_id,
    )
    assert receipt["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_SCHEMA_VERSION
    assert receipt["body_free"] is True
    return receipt


def _ready_op07() -> dict[str, object]:
    global _READY_OP07_CACHE
    if _READY_OP07_CACHE is None:
        op06 = _ready_op06()
        receipt = _ready_reviewer_confirmation_receipt(str(op06["review_session_id"]))
        material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
            packet_completeness_export_denylist_scan_receipt_boundary=op06,
            reviewer_person_confirmation_receipt_bodyfree=receipt,
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(material) is True
        _READY_OP07_CACHE = material
    return deepcopy(_READY_OP07_CACHE)


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


def test_dmh_op06_scan_receipt_shape_is_bodyfree_and_contract_fixture_not_real_folder_scan() -> None:
    op05 = _ready_op05()
    receipt = _ready_scan_receipt(str(op05["review_session_id"]), str(op05["packet_generation_receipt_ref"]))

    assert set(receipt) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_SCAN_RECEIPT_FIELD_REFS)
    assert receipt["packet_scan_receipt_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_SCAN_RECEIPT_REF
    assert receipt["review_session_id"] == op05["review_session_id"]
    assert receipt["packet_generation_receipt_ref"] == op05["packet_generation_receipt_ref"]
    assert receipt["actual_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_EXPECTED_SOURCE_REF
    assert receipt["scan_source_kind_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_CONTRACT_FIXTURE_SOURCE_KIND_REF
    assert receipt["scan_executed_against_real_local_folder_claimed_here"] is False
    assert receipt["packet_count"] == 24
    assert receipt["packet_ref_id_count"] == 24
    assert receipt["packet_ref_ids"] == op05["packet_ref_ids"]
    assert receipt["packet_completeness_scan_required"] is True
    assert receipt["packet_completeness_scan_passed"] is True
    assert receipt["export_denylist_scan_required"] is True
    assert receipt["export_denylist_scan_passed"] is True
    assert receipt["export_denylist_violation_refs"] == []
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS:
        assert receipt[key] is False, key


def test_dmh_op06_accepts_packet_completeness_export_denylist_scan_receipt_boundary_without_actual_review() -> None:
    material = _ready_op06()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_BOUNDARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF
    assert material["dmh_op06_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_READY_STATUS_REF
    assert material["dmh_op06_ready"] is True
    assert material["dmh_op06_blocker_refs"] == []
    assert tuple(material["dmh_op06_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_READY_REASON_REFS
    assert material["op05_dmh_ready"] is True
    assert material["op05_packet_generation_receipt_intaked_here"] is True
    assert material["op05_packet_completeness_export_denylist_scan_required_next"] is True
    assert material["packet_scan_receipt_present"] is True
    assert material["packet_scan_receipt_source_ref_allowed"] is True
    assert material["packet_scan_receipt_source_kind_is_contract_fixture_not_real_scan_evidence"] is True
    assert material["packet_generation_receipt_ref_confirmed"] is True
    assert material["packet_generation_request_ref_confirmed"] is True
    assert material["actual_review_basis_ref_confirmed"] is True
    assert material["packet_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["packet_count_matches_expected"] is True
    assert material["packet_ref_id_count_matches_expected"] is True
    assert material["packet_completeness_scan_required"] is True
    assert material["packet_completeness_scan_passed"] is True
    assert material["export_denylist_policy_ref_confirmed"] is True
    assert material["export_denylist_scan_required"] is True
    assert material["export_denylist_scan_passed"] is True
    assert material["export_denylist_violation_refs"] == []
    assert material["body_full_packet_export_candidate_refs"] == []
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS:
        assert material[key] is False, key
    assert material["packet_scan_receipt_intaked_here"] is True
    assert material["packet_scan_receipt_from_real_operation_claimed_here"] is False
    assert material["packet_scan_executed_against_real_local_folder_claimed_here"] is False
    assert material["reviewer_person_selection_only_form_allowed_next"] is True
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_operation_receipt_still_not_received"] is True
    assert material["actual_review_rows_still_not_created"] is True
    assert material["actual_disposal_purge_still_not_run"] is True
    assert material["dmh_op06_does_not_scan_real_local_folder_here"] is True
    assert material["dmh_op06_does_not_run_actual_human_review"] is True
    assert material["dmh_op06_does_not_start_p8_p6_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op06_blocks_without_scan_receipt_and_keeps_next_step_closed() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary(
        body_full_packet_generation_receipt_intake_boundary=_ready_op05(),
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_FIELD_REFS)
    assert material["dmh_op06_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_STATUS_REF
    assert material["dmh_op06_ready"] is False
    assert "dmh_op06_packet_scan_receipt_missing" in material["dmh_op06_blocker_refs"]
    assert material["packet_scan_receipt_present"] is False
    assert material["packet_scan_receipt_intaked_here"] is False
    assert material["reviewer_person_selection_only_form_allowed_next"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op06_blocks_scan_receipt_with_forbidden_body_question_path_hash_keys() -> None:
    op05 = _ready_op05()
    receipt = _ready_scan_receipt(str(op05["review_session_id"]), str(op05["packet_generation_receipt_ref"]))
    receipt["raw_input"] = "forbidden packet body must never be accepted"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary(
        body_full_packet_generation_receipt_intake_boundary=op05,
        packet_scan_receipt_bodyfree=receipt,
    )

    assert material["dmh_op06_ready"] is False
    assert "dmh_op06_packet_scan_receipt_forbidden_body_question_path_hash_key_detected" in material["dmh_op06_blocker_refs"]
    assert material["packet_scan_receipt_forbidden_payload_key_paths"] == ["packet_scan_receipt.raw_input"]
    assert material["packet_scan_receipt_intaked_here"] is False
    assert material["reviewer_person_selection_only_form_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("receipt_field", "bad_value", "expected_blocker"),
    [
        ("packet_count", 23, "dmh_op06_packet_scan_receipt_packet_count_not_24"),
        ("packet_ref_id_count", 23, "dmh_op06_packet_scan_receipt_packet_ref_id_count_not_24"),
        ("packet_completeness_scan_required", False, "dmh_op06_packet_completeness_scan_required_not_true"),
        ("packet_completeness_scan_passed", False, "dmh_op06_packet_completeness_scan_not_passed"),
        ("export_denylist_policy_ref", "wrong_policy", "dmh_op06_export_denylist_policy_ref_mismatch"),
        ("export_denylist_scan_required", False, "dmh_op06_export_denylist_scan_required_not_true"),
        ("export_denylist_scan_passed", False, "dmh_op06_export_denylist_scan_not_passed"),
        ("raw_input_detected_in_export", True, "dmh_op06_packet_scan_receipt_raw_input_detected_in_export_not_false"),
        ("comment_text_detected_in_export", True, "dmh_op06_packet_scan_receipt_comment_text_detected_in_export_not_false"),
        ("packet_content_detected_in_export", True, "dmh_op06_packet_scan_receipt_packet_content_detected_in_export_not_false"),
        ("question_text_detected_in_export", True, "dmh_op06_packet_scan_receipt_question_text_detected_in_export_not_false"),
        ("local_path_detected_in_export", True, "dmh_op06_packet_scan_receipt_local_path_detected_in_export_not_false"),
        ("body_hash_detected_in_export", True, "dmh_op06_packet_scan_receipt_body_hash_detected_in_export_not_false"),
        ("terminal_output_body_detected_in_export", True, "dmh_op06_packet_scan_receipt_terminal_output_body_detected_in_export_not_false"),
        ("scan_executed_against_real_local_folder_claimed_here", True, "dmh_op06_packet_scan_receipt_claims_real_folder_scan_here"),
    ],
)
def test_dmh_op06_blocks_invalid_scan_receipt_bodyfree_boundaries(
    receipt_field: str, bad_value: object, expected_blocker: str
) -> None:
    op05 = _ready_op05()
    receipt = _ready_scan_receipt(str(op05["review_session_id"]), str(op05["packet_generation_receipt_ref"]))
    receipt[receipt_field] = bad_value

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary(
        body_full_packet_generation_receipt_intake_boundary=op05,
        packet_scan_receipt_bodyfree=receipt,
    )

    assert material["dmh_op06_ready"] is False
    assert expected_blocker in material["dmh_op06_blocker_refs"]
    assert material["packet_scan_receipt_intaked_here"] is False
    assert material["reviewer_person_selection_only_form_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_count", 23),
        ("packet_ref_id_count", 23),
        ("packet_ref_ids_unique", False),
        ("packet_completeness_scan_passed", False),
        ("export_denylist_scan_passed", False),
        ("raw_input_detected_in_export", True),
        ("comment_text_detected_in_export", True),
        ("question_text_detected_in_export", True),
        ("local_path_detected_in_export", True),
        ("body_hash_detected_in_export", True),
        ("terminal_output_body_detected_in_export", True),
        ("packet_scan_receipt_from_real_operation_claimed_here", True),
        ("packet_scan_executed_against_real_local_folder_claimed_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op06_contract_rejects_scan_leak_real_scan_actual_review_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op06()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(mutated)


def test_dmh_op07_reviewer_person_confirmation_receipt_shape_is_bodyfree_not_review_execution() -> None:
    op06 = _ready_op06()
    receipt = _ready_reviewer_confirmation_receipt(str(op06["review_session_id"]))

    assert set(receipt) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_REVIEWER_CONFIRMATION_RECEIPT_FIELD_REFS)
    assert receipt["review_session_id"] == op06["review_session_id"]
    assert receipt["actual_review_basis_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF
    assert receipt["reviewer_person_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF
    assert receipt["reviewer_is_person"] is True
    assert receipt["reviewer_person_confirmed"] is True
    assert receipt["reviewer_person_confirmation_source_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_REF
    assert receipt["reviewer_confirmation_source_kind_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_KIND_REF
    assert receipt["reviewer_identity_public_export_allowed"] is False
    assert receipt["reviewer_free_text_export_allowed"] is False
    assert receipt["reviewer_notes_body_export_allowed"] is False
    assert receipt["reviewer_local_only_read_receipt_present"] is False
    assert receipt["actual_human_review_executed_by_person"] is False
    assert receipt["ai_or_helper_substitution_allowed"] is False
    assert receipt["body_free"] is True


def test_dmh_op07_finalizes_reviewer_person_and_selection_only_form_without_running_review() -> None:
    material = _ready_op07()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SELECTION_ONLY_FORM_FINALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF
    assert material["dmh_op07_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_READY_STATUS_REF
    assert material["dmh_op07_ready"] is True
    assert material["dmh_op07_blocker_refs"] == []
    assert tuple(material["dmh_op07_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_READY_REASON_REFS
    assert material["op06_dmh_ready"] is True
    assert material["op06_packet_count"] == 24
    assert material["op06_packet_ref_id_count"] == 24
    assert material["op06_packet_completeness_scan_passed"] is True
    assert material["op06_export_denylist_scan_passed"] is True
    assert material["reviewer_person_confirmation_receipt_present"] is True
    assert material["reviewer_person_confirmation_source_ref_allowed"] is True
    assert material["reviewer_confirmation_source_kind_is_boundary_not_actual_review_execution"] is True
    assert material["reviewer_person_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_present"] is True
    assert material["reviewer_person_ref_is_bodyfree_ref"] is True
    assert material["reviewer_person_ref_has_local_path_shape"] is False
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["ai_or_helper_substitution_allowed"] is False
    assert material["selection_only_form_ready"] is True
    assert material["selection_only"] is True
    assert material["selection_only_form_bodyfree_only"] is True
    assert material["selection_only_form_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_SELECTION_ONLY_FORM_REF
    assert material["reviewer_instruction_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_INSTRUCTION_REF
    for forbidden_form_key in (
        "free_text_field_present",
        "free_text_field_export_allowed",
        "reviewer_note_field_present",
        "reviewer_notes_body_field_present",
        "raw_body_copy_field_present",
        "question_text_field_present",
        "draft_question_text_field_present",
        "local_path_field_present",
        "body_hash_field_present",
        "packet_content_field_present",
    ):
        assert material[forbidden_form_key] is False, forbidden_form_key
    assert material["required_axis_count"] == 6
    assert tuple(material["rating_axis_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS
    assert material["rating_axis_target_thresholds"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS
    assert material["required_case_count"] == 24
    assert material["selection_row_count_required"] == 24
    assert material["sanitized_review_result_row_count_required"] == 24
    assert material["rating_row_count_required"] == 24
    assert material["question_need_observation_row_count_required"] == 24
    assert material["reviewer_receives_blind_case_id_only"] is True
    assert material["actual_review_operation_state_machine_allowed_next"] is True
    assert material["actual_human_review_started_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["dmh_op07_does_not_run_actual_human_review"] is True
    assert material["dmh_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal"] is True
    assert material["dmh_op07_does_not_start_p8_p6_r52_or_release"] is True
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op07_blocks_without_reviewer_person_confirmation_receipt() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
        packet_completeness_export_denylist_scan_receipt_boundary=_ready_op06(),
    )

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_FIELD_REFS)
    assert material["dmh_op07_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_STATUS_REF
    assert material["dmh_op07_ready"] is False
    assert "dmh_op07_reviewer_person_confirmation_receipt_missing" in material["dmh_op07_blocker_refs"]
    assert material["reviewer_person_confirmation_receipt_present"] is False
    assert material["selection_only_form_ready"] is False
    assert material["actual_review_operation_state_machine_allowed_next"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_dmh_op07_blocks_reviewer_confirmation_with_forbidden_body_question_path_hash_keys() -> None:
    op06 = _ready_op06()
    receipt = _ready_reviewer_confirmation_receipt(str(op06["review_session_id"]))
    receipt["reviewer_notes"] = "free text note must never be accepted"

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
        packet_completeness_export_denylist_scan_receipt_boundary=op06,
        reviewer_person_confirmation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op07_ready"] is False
    assert "dmh_op07_reviewer_person_confirmation_receipt_forbidden_body_question_path_hash_key_detected" in material["dmh_op07_blocker_refs"]
    assert material["reviewer_person_confirmation_receipt_forbidden_payload_key_paths"] == ["reviewer_person_confirmation_receipt.reviewer_notes"]
    assert material["selection_only_form_ready"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(material) is True


@pytest.mark.parametrize(
    ("receipt_field", "bad_value", "expected_blocker"),
    [
        ("reviewer_person_ref", "", "dmh_op07_reviewer_person_ref_missing"),
        ("reviewer_person_ref", "redacted_local_path_shape/person", "dmh_op07_reviewer_person_ref_has_local_path_shape"),
        ("reviewer_is_person", False, "dmh_op07_reviewer_is_person_not_true"),
        ("reviewer_person_confirmed", False, "dmh_op07_reviewer_person_confirmed_not_true"),
        ("reviewer_person_confirmation_source_ref", "wrong_source", "dmh_op07_reviewer_person_confirmation_source_ref_not_allowed"),
        ("reviewer_confirmation_source_kind_ref", "actual_review_execution", "dmh_op07_reviewer_confirmation_source_kind_not_boundary"),
        ("reviewer_identity_public_export_allowed", True, "dmh_op07_reviewer_person_confirmation_receipt_reviewer_identity_public_export_allowed_not_false"),
        ("reviewer_free_text_export_allowed", True, "dmh_op07_reviewer_person_confirmation_receipt_reviewer_free_text_export_allowed_not_false"),
        ("reviewer_notes_body_export_allowed", True, "dmh_op07_reviewer_person_confirmation_receipt_reviewer_notes_body_export_allowed_not_false"),
        ("reviewer_local_only_read_receipt_present", True, "dmh_op07_reviewer_person_confirmation_receipt_reviewer_local_only_read_receipt_present_not_false"),
        ("actual_human_review_executed_by_person", True, "dmh_op07_reviewer_person_confirmation_receipt_actual_human_review_executed_by_person_not_false"),
        ("ai_or_helper_substitution_allowed", True, "dmh_op07_reviewer_person_confirmation_receipt_ai_or_helper_substitution_allowed_not_false"),
        ("packet_content_included", True, "dmh_op07_reviewer_person_confirmation_receipt_packet_content_included_not_false"),
        ("question_text_included", True, "dmh_op07_reviewer_person_confirmation_receipt_question_text_included_not_false"),
    ],
)
def test_dmh_op07_blocks_invalid_reviewer_confirmation_receipt_boundaries(
    receipt_field: str, bad_value: object, expected_blocker: str
) -> None:
    op06 = _ready_op06()
    receipt = _ready_reviewer_confirmation_receipt(str(op06["review_session_id"]))
    receipt[receipt_field] = bad_value

    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
        packet_completeness_export_denylist_scan_receipt_boundary=op06,
        reviewer_person_confirmation_receipt_bodyfree=receipt,
    )

    assert material["dmh_op07_ready"] is False
    assert expected_blocker in material["dmh_op07_blocker_refs"]
    assert material["selection_only_form_ready"] is False
    assert material["actual_review_operation_state_machine_allowed_next"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("reviewer_person_ref", "other_person_ref"),
        ("reviewer_person_ref_present", False),
        ("reviewer_person_ref_has_local_path_shape", True),
        ("reviewer_is_person", False),
        ("reviewer_person_confirmed", False),
        ("reviewer_local_only_read_receipt_present", True),
        ("actual_human_review_executed_by_person", True),
        ("ai_or_helper_substitution_allowed", True),
        ("selection_only_form_ready", False),
        ("selection_only", False),
        ("free_text_field_present", True),
        ("reviewer_note_field_present", True),
        ("question_text_field_present", True),
        ("draft_question_text_field_present", True),
        ("packet_content_field_present", True),
        ("required_axis_count", 5),
        ("required_case_count", 23),
        ("actual_human_review_started_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_dmh_op07_contract_rejects_form_mutations_actual_review_or_promotion(field: str, bad_value: object) -> None:
    material = _ready_op07()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(mutated)


def test_dmh_op06_op07_aliases_match_primary_builders_and_contracts() -> None:
    op05 = _ready_op05()
    primary_scan_receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_bodyfree(
        review_session_id=str(op05["review_session_id"]),
        packet_generation_receipt_ref=str(op05["packet_generation_receipt_ref"]),
    )
    alias_scan_receipt = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_completeness_export_denylist_scan_receipt_bodyfree(
        review_session_id=str(op05["review_session_id"]),
        packet_generation_receipt_ref=str(op05["packet_generation_receipt_ref"]),
    )
    assert alias_scan_receipt == primary_scan_receipt

    primary_op06 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary(
        body_full_packet_generation_receipt_intake_boundary=op05,
        packet_scan_receipt_bodyfree=primary_scan_receipt,
    )
    alias_op06 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_completeness_export_denylist_scan_receipt_boundary_bodyfree(
        body_full_packet_generation_receipt_intake_boundary=op05,
        packet_scan_receipt_bodyfree=primary_scan_receipt,
    )
    assert alias_op06 == primary_op06
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_completeness_export_denylist_scan_receipt_boundary_bodyfree_contract(alias_op06) is True

    primary_reviewer_receipt = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_receipt_bodyfree(
        review_session_id=str(primary_op06["review_session_id"]),
    )
    alias_reviewer_receipt = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_reviewer_person_confirmation_receipt_bodyfree(
        review_session_id=str(primary_op06["review_session_id"]),
    )
    assert alias_reviewer_receipt == primary_reviewer_receipt

    primary_op07 = dmh.build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
        packet_completeness_export_denylist_scan_receipt_boundary=primary_op06,
        reviewer_person_confirmation_receipt_bodyfree=primary_reviewer_receipt,
    )
    alias_op07 = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_reviewer_person_confirmation_selection_only_form_finalization_bodyfree(
        packet_completeness_export_denylist_scan_receipt_boundary=primary_op06,
        reviewer_person_confirmation_receipt_bodyfree=primary_reviewer_receipt,
    )
    assert alias_op07 == primary_op07
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_reviewer_person_confirmation_selection_only_form_finalization_bodyfree_contract(alias_op07) is True
