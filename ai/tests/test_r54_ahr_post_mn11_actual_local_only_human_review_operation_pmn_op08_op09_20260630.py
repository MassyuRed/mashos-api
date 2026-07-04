# -*- coding: utf-8 -*-
"""R54-AHR Post-MN11 actual local-only human review operation PMN-OP08/OP09 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn
import test_r54_ahr_post_mn11_actual_local_only_human_review_operation_pmn_op06_op07_20260630 as prev


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


def _ready_op07() -> dict[str, object]:
    return prev._ready_op07()


def _contract_fixture_packet_generation_receipt(op07: dict[str, object]) -> dict[str, object]:
    packet_ref_ids = [f"cral_packet_ref_{index:03d}" for index in range(1, 25)]
    return {
        "packet_generation_receipt_ref": "postmn11_packet_generation_receipt_contract_fixture_001",
        "review_session_id": op07["review_session_id"],
        "packet_generation_request_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF,
        "actual_review_basis_ref": pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_source_ref": pmn.P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF,
        "packet_materialized_local_only": True,
        "packet_count": 24,
        "packet_ref_id_count": 24,
        "packet_ref_ids": packet_ref_ids,
        "body_full_exported": False,
        "body_full_packet_exported_to_artifact": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "body_free": True,
    }


def _ready_op08() -> dict[str, object]:
    op07 = _ready_op07()
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation_receipt_boundary=op07,
        packet_generation_receipt_bodyfree=_contract_fixture_packet_generation_receipt(op07),
    )


def _ready_op09() -> dict[str, object]:
    return pmn.build_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan=_ready_op08()
    )


def test_pmn_op00_to_op07_implementation_is_present_before_op08_op09() -> None:
    op01 = prev._ready_op01()
    op02 = prev._ready_op02()
    op03 = prev._ready_op03()
    op04 = prev._ready_op04()
    op05 = prev._ready_op05()
    op06 = prev._ready_op06()
    op07 = _ready_op07()

    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(op01) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(op02) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(op03) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(op04) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(op05) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(op06) is True
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(op07) is True
    assert op07["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF
    assert op07["packet_generation_receipt_boundary_ready"] is True
    assert op07["packet_generation_receipt_received_here"] is False
    assert op07["packet_generation_receipt_intaked_here"] is False
    assert op07["actual_human_review_still_not_run"] is True
    assert op07["actual_review_evidence_complete_from_real_review"] is False
    _assert_bodyfree_no_touch_no_promotion(op07)


def test_pmn_op08_blocks_without_actual_packet_generation_receipt_and_does_not_claim_scan_pass() -> None:
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation_receipt_boundary=_ready_op07()
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_FIELD_REFS)
    assert material["packet_scan_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_STATUS_REF
    assert material["packet_scan_ready"] is False
    assert "pmn_op08_actual_local_packet_generation_receipt_not_received" in material["packet_scan_blocker_refs"]
    assert material["actual_packet_generation_receipt_received_here"] is False
    assert material["actual_packet_generation_receipt_intaked_here"] is False
    assert material["actual_packet_generation_receipt_ref"] == ""
    assert material["packet_count"] == 0
    assert material["packet_ref_id_count"] == 0
    assert material["packet_ref_ids"] == []
    assert material["packet_completeness_scan_passed"] is False
    assert material["export_denylist_scan_passed"] is False
    assert material["reviewer_packet_required_fields_present"] is False
    assert material["reviewer_packet_required_field_ref_count"] == 0
    assert material["body_full_packet_exported_to_artifact"] is False
    assert material["packet_content_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op08_accepts_bodyfree_packet_generation_receipt_contract_fixture_without_body_path_hash_or_question() -> None:
    material = _ready_op08()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF
    assert material["packet_scan_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_READY_STATUS_REF
    assert material["packet_scan_ready"] is True
    assert material["packet_scan_blocker_refs"] == []
    assert tuple(material["packet_scan_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_READY_REASON_REFS
    assert material["packet_scan_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_SCAN_REF
    assert material["packet_scan_depends_on_actual_packet_generation_receipt"] is True
    assert material["actual_packet_generation_receipt_received_here"] is True
    assert material["actual_packet_generation_receipt_intaked_here"] is True
    assert material["actual_packet_generation_receipt_source_allowed"] is True
    assert material["packet_generation_request_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF
    assert material["packet_count"] == 24
    assert material["packet_ref_id_count"] == 24
    assert len(material["packet_ref_ids"]) == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["packet_count_matches_expected"] is True
    assert material["packet_ref_id_count_matches_expected"] is True
    assert material["packet_completeness_scan_passed"] is True
    assert material["reviewer_packet_required_fields_present"] is True
    assert tuple(material["reviewer_packet_required_field_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_REVIEWER_PACKET_FIELD_REFS
    assert material["export_denylist_scan_passed"] is True
    assert material["export_denylist_violation_refs"] == []
    assert material["body_full_packet_content_detected_in_export"] is False
    assert material["question_text_detected_in_export"] is False
    assert material["draft_question_text_detected_in_export"] is False
    assert material["local_path_detected_in_export"] is False
    assert material["body_hash_detected_in_export"] is False
    assert material["terminal_output_body_detected_in_export"] is False
    assert material["body_full_packet_exported"] is False
    assert material["body_full_packet_exported_to_artifact"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_stored"] is False
    assert material["terminal_output_body_included"] is False
    assert material["packet_content_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["reviewer_person_selection_only_form_freeze_allowed_next"] is True
    assert material["pmn_op08_does_not_generate_body_full_packet"] is True
    assert material["pmn_op08_does_not_run_actual_human_review"] is True
    assert material["pmn_op08_does_not_create_actual_operation_receipt_or_review_rows_or_disposal"] is True
    assert material["actual_human_review_still_not_run"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("packet_scan_bodyfree_only", False),
        ("packet_count", 23),
        ("packet_ref_id_count", 23),
        ("packet_completeness_scan_passed", False),
        ("export_denylist_scan_passed", False),
        ("body_full_packet_content_detected_in_export", True),
        ("question_text_detected_in_export", True),
        ("draft_question_text_detected_in_export", True),
        ("local_path_detected_in_export", True),
        ("body_hash_detected_in_export", True),
        ("terminal_output_body_detected_in_export", True),
        ("body_full_packet_exported", True),
        ("body_full_packet_exported_to_artifact", True),
        ("local_absolute_path_included", True),
        ("body_hash_stored", True),
        ("terminal_output_body_included", True),
        ("packet_content_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("pmn_op08_does_not_generate_body_full_packet", False),
        ("pmn_op08_does_not_run_actual_human_review", False),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op08_contract_rejects_receipt_leak_or_promotion_mutation(field: str, bad_value: object) -> None:
    material = _ready_op08()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(mutated)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("actual_source_ref", "unit_test_rows", "pmn_op08_packet_generation_receipt_actual_source_ref_not_allowed"),
        ("packet_count", 23, "pmn_op08_packet_generation_receipt_packet_count_not_24"),
        ("packet_ref_id_count", 23, "pmn_op08_packet_generation_receipt_packet_ref_id_count_not_24"),
        ("packet_ref_ids", ["cral_packet_ref_001"] * 24, "pmn_op08_packet_generation_receipt_packet_ref_ids_not_24_unique"),
        ("body_full_packet_exported_to_artifact", True, "pmn_op08_packet_generation_receipt_body_full_packet_exported_to_artifact_not_false"),
        ("question_text_included", True, "pmn_op08_packet_generation_receipt_question_text_included_not_false"),
        ("body_hash_stored", True, "pmn_op08_packet_generation_receipt_body_hash_stored_not_false"),
    ],
)
def test_pmn_op08_blocks_receipt_with_invalid_source_count_or_denylist_violation(
    field: str, bad_value: object, expected_blocker: str
) -> None:
    op07 = _ready_op07()
    receipt = _contract_fixture_packet_generation_receipt(op07)
    receipt[field] = bad_value

    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation_receipt_boundary=op07,
        packet_generation_receipt_bodyfree=receipt,
    )

    assert material["packet_scan_ready"] is False
    assert expected_blocker in material["packet_scan_blocker_refs"]
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op09_blocks_until_op08_ready_and_does_not_start_review() -> None:
    blocked_op08 = pmn.build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation_receipt_boundary=_ready_op07()
    )
    material = pmn.build_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan=blocked_op08
    )

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REQUIRED_FIELD_REFS)
    assert material["reviewer_form_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_STATUS_REF
    assert material["reviewer_form_ready"] is False
    assert "pmn_op09_packet_scan_not_ready" in material["reviewer_form_blocker_refs"]
    assert material["selection_only_form_ready"] is False
    assert material["reviewer_person_ref_present"] is False
    assert material["reviewer_is_person"] is False
    assert material["actual_human_review_started_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


def test_pmn_op09_freezes_reviewer_person_selection_only_form_without_running_actual_review() -> None:
    material = _ready_op09()

    assert set(material) == set(pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION
    assert material["operation_step_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF
    assert material["reviewer_form_status_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_READY_STATUS_REF
    assert material["reviewer_form_ready"] is True
    assert material["reviewer_form_blocker_refs"] == []
    assert tuple(material["reviewer_form_reason_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_READY_REASON_REFS
    assert material["op08_packet_scan_ready"] is True
    assert material["op08_packet_count"] == 24
    assert material["op08_packet_ref_id_count"] == 24
    assert material["op08_packet_completeness_scan_passed"] is True
    assert material["op08_export_denylist_scan_passed"] is True
    assert material["reviewer_person_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF
    assert material["reviewer_person_ref_present"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["reviewer_identity_public_export_allowed"] is False
    assert material["reviewer_free_text_export_allowed"] is False
    assert material["reviewer_notes_body_export_allowed"] is False
    assert material["selection_only_form_ready"] is True
    assert material["selection_only_form_ref"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_SELECTION_ONLY_FORM_REF
    assert material["selection_only"] is True
    assert material["selection_only_form_bodyfree_only"] is True
    assert material["free_text_field_present"] is False
    assert material["free_text_field_export_allowed"] is False
    assert material["reviewer_notes_body_field_present"] is False
    assert material["raw_body_copy_field_present"] is False
    assert material["question_text_field_present"] is False
    assert material["draft_question_text_field_present"] is False
    assert material["local_path_field_present"] is False
    assert material["body_hash_field_present"] is False
    assert material["packet_content_field_present"] is False
    assert material["required_axis_count"] == 6
    assert material["required_case_count"] == 24
    assert tuple(material["rating_axis_refs"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS
    assert material["reviewer_receives_blind_case_id_only"] is True
    assert material["reviewer_facing_family_exposed"] is False
    assert material["reviewer_facing_tier_exposed"] is False
    assert material["reviewer_facing_case_ref_exposed"] is False
    assert material["reviewer_facing_packet_ref_exposed"] is False
    assert material["reviewer_facing_expected_result_exposed"] is False
    assert material["actual_human_review_state_capture_allowed_next"] is True
    assert material["actual_human_review_started_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["pmn_op09_does_not_run_actual_human_review"] is True
    assert material["pmn_op09_does_not_create_actual_operation_receipt_or_rows_or_disposal"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert material["actual_review_evidence_complete_from_real_review_still_false"] is True
    assert tuple(material["implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == pmn.P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == pmn.P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF
    assert pmn.assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(material) is True
    _assert_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("reviewer_form_ready", False),
        ("reviewer_person_ref", ""),
        ("reviewer_person_ref_present", False),
        ("reviewer_is_person", False),
        ("reviewer_person_confirmed", False),
        ("reviewer_local_only_read_receipt_present", True),
        ("actual_human_review_executed_by_person", True),
        ("reviewer_identity_public_export_allowed", True),
        ("reviewer_free_text_export_allowed", True),
        ("reviewer_notes_body_export_allowed", True),
        ("selection_only_form_ready", False),
        ("selection_only", False),
        ("selection_only_form_bodyfree_only", False),
        ("free_text_field_present", True),
        ("free_text_field_export_allowed", True),
        ("reviewer_notes_body_field_present", True),
        ("raw_body_copy_field_present", True),
        ("question_text_field_present", True),
        ("draft_question_text_field_present", True),
        ("local_path_field_present", True),
        ("body_hash_field_present", True),
        ("packet_content_field_present", True),
        ("required_axis_count", 5),
        ("required_case_count", 23),
        ("reviewer_receives_blind_case_id_only", False),
        ("reviewer_facing_family_exposed", True),
        ("reviewer_facing_tier_exposed", True),
        ("reviewer_facing_case_ref_exposed", True),
        ("reviewer_facing_packet_ref_exposed", True),
        ("reviewer_facing_expected_result_exposed", True),
        ("actual_human_review_started_here", True),
        ("actual_human_review_run_here", True),
        ("pmn_op09_does_not_run_actual_human_review", False),
        ("pmn_op09_does_not_create_actual_operation_receipt_or_rows_or_disposal", False),
        ("actual_review_evidence_complete_from_real_review", True),
        ("p8_start_allowed", True),
    ],
)
def test_pmn_op09_contract_rejects_free_text_question_body_path_hash_review_or_promotion_mutation(
    field: str, bad_value: object
) -> None:
    material = _ready_op09()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        pmn.assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(mutated)


def test_pmn_op08_op09_aliases_match_primary_builders_and_contracts() -> None:
    op07 = _ready_op07()
    receipt = _contract_fixture_packet_generation_receipt(op07)
    primary_op08 = pmn.build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation_receipt_boundary=op07,
        packet_generation_receipt_bodyfree=receipt,
    )
    alias_op08 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_local_operation_receipt_boundary=op07,
        packet_generation_receipt_bodyfree=receipt,
    )
    assert alias_op08 == primary_op08
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_packet_completeness_export_denylist_scan_bodyfree_contract(alias_op08) is True

    primary_op09 = pmn.build_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan=primary_op08
    )
    alias_op09 = pmn.build_p7_r54_ahr_post_mn11_actual_operation_reviewer_person_boundary_selection_only_form_freeze_bodyfree(
        packet_completeness_export_denylist_scan=primary_op08
    )
    assert alias_op09 == primary_op09
    assert pmn.assert_p7_r54_ahr_post_mn11_actual_operation_reviewer_person_boundary_selection_only_form_freeze_bodyfree_contract(alias_op09) is True
