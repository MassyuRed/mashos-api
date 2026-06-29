# -*- coding: utf-8 -*-
"""R54-AHR-CS08/CS09 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "raw_body",
    "returned_emlis_body",
    "history_surface",
    "comment_text",
    "comment_text_body",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "raw_question_answer",
    "body_full_packet_content",
    "packet_content",
    "local_absolute_path",
    "local_file_path",
    "body_hash",
    "terminal_output_body",
    "stdout_body",
    "stderr_body",
    "traceback_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _assert_bodyfree_no_touch_allowing_cs09_receipt(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key in cs.P7_R54_AHR_CS09_ALLOWED_TRUE_FALSE_FLAG_REFS:
            continue
        assert material[key] is False, key
    assert material["actual_human_review_operation_run"] is True
    assert material["actual_human_review_executed_by_person"] is True
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _build_ready_cs08() -> dict[str, Any]:
    cs07 = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan()
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(cs07) is True
    cs08 = cs.build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility(
        packet_completeness_export_denylist_scan=cs07
    )
    assert cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(cs08) is True
    return cs08


def _build_ready_cs09() -> dict[str, Any]:
    cs08 = _build_ready_cs08()
    material = cs.build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
        reviewer_selection_form_current_compatibility=cs08,
        operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_operation_run=True,
        actual_human_review_executed_by_person=True,
        review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
        review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
        reviewed_case_count=cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        selection_row_count=cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    )
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(material) is True
    return material


def test_cs00_to_cs07_are_present_before_cs08_cs09() -> None:
    cs00 = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()
    cs01 = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=cs00)
    cs02 = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=cs01)
    cs03 = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment(
        historical_helper_refs_reconcile=cs02
    )
    cs04 = cs.build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze(
        manifest_packet_evidence_impact_assessment=cs03
    )
    cs05 = cs.build_p7_r54_ahr_cs05_local_only_preflight(current_24_case_manifest_refreeze=cs04)
    cs06 = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(local_only_preflight=cs05)
    cs07 = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
        packet_generation_request_receipt_bridge=cs06
    )

    assert cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(cs00) is True
    assert cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(cs01) is True
    assert cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(cs02) is True
    assert cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(cs03) is True
    assert cs.assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(cs04) is True
    assert cs.assert_p7_r54_ahr_cs05_local_only_preflight_contract(cs05) is True
    assert cs.assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(cs06) is True
    assert cs.assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(cs07) is True
    assert tuple(cs07["implemented_steps"]) == cs.P7_R54_AHR_CS07_IMPLEMENTED_STEPS
    assert tuple(cs07["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS
    assert cs07["next_required_step"] == cs.P7_R54_AHR_CS08_STEP_REF
    assert cs07["reviewer_selection_form_freeze_allowed_next"] is True
    assert cs07["actual_review_execution_allowed_next"] is False


def test_cs08_reviewer_selection_form_current_compatibility_ready_bodyfree() -> None:
    cs07 = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan()
    material = cs.build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility(
        packet_completeness_export_denylist_scan=cs07
    )

    assert set(material) == set(cs.P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS08_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS08_STEP_REF
    assert material["cs07_schema_version"] == cs.P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert material["cs07_next_required_step"] == cs.P7_R54_AHR_CS08_STEP_REF
    assert material["cs07_scan_status_ref"] == cs.P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF
    assert material["cs07_packet_completeness_passed"] is True
    assert material["cs07_export_denylist_scan_passed"] is True
    assert material["cs07_forbidden_key_scan_passed"] is True
    assert material["cs07_reviewer_selection_form_freeze_allowed_next"] is True

    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["existing_ahr_can_be_used_as_current_actual_review_evidence"] is False

    assert material["selection_form_status_ref"] == cs.P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
    assert material["selection_form_status"] == cs.P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
    assert material["selection_form_reason_refs"] == [cs.P7_R54_AHR_CS08_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["packet_scan_ready_for_form_freeze"] is True
    assert material["selection_only"] is True
    assert material["selection_only_form"] is True
    assert material["selection_form_current_compatibility_checked"] is True
    assert material["selection_form_structure_frozen"] is True
    assert material["selection_form_bodyfree_only"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["body_full_packet_content_available_to_local_reviewer_only"] is True
    assert material["actual_human_review_operation_receipt_intake_allowed_next"] is True
    assert material["actual_review_execution_allowed_next"] is False
    assert material["actual_review_execution_allowed_here"] is False
    assert material["actual_review_execution_blocked_until_operation_receipt"] is True
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS09_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(material) is True


def test_cs08_selection_form_options_match_current_axis_contract() -> None:
    material = _build_ready_cs08()

    assert tuple(material["rating_axis_refs"]) == cs.P7_R54_AHR_CS04_RATING_AXIS_REFS
    assert material["rating_axis_count"] == 6
    assert material["rating_axis_profile_ref"] == cs.P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF
    assert material["rating_axis_target_thresholds"] == cs.P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS
    assert tuple(material["score_option_refs"]) == (0.0, 0.25, 0.5, 0.75, 1.0)
    assert tuple(material["verdict_option_refs"]) == (
        "PASS",
        "YELLOW",
        "REPAIR_REQUIRED",
        "RED",
        "BLOCKED",
        "NOT_REVIEWABLE",
    )
    assert tuple(material["sanitized_reason_id_option_refs"]) == cs.P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS
    assert tuple(material["readfeel_blocker_id_option_refs"]) == cs.P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS
    assert tuple(material["execution_blocker_id_option_refs"]) == cs.P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS
    assert tuple(material["question_need_primary_class_options"]) == cs.P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(material["ambiguity_kind_option_refs"]) == cs.P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS
    assert tuple(material["one_question_fit_option_refs"]) == cs.P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS
    assert tuple(material["repair_required_option_refs"]) == cs.P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS
    assert tuple(material["plan_candidate_flag_refs"]) == cs.P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS
    assert material["score_option_count"] == len(cs.P7_R54_AHR_CS08_SCORE_OPTION_REFS)
    assert material["question_need_primary_class_option_count"] == len(
        cs.P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS
    )
    assert material["p8_implementation_spec_finalized_here"] is False


@pytest.mark.parametrize("false_field", cs.P7_R54_AHR_CS08_PROHIBITED_FORM_FALSE_FLAG_REFS)
def test_cs08_reviewer_selection_form_prohibited_fields_remain_false(false_field: str) -> None:
    material = _build_ready_cs08()
    assert material[false_field] is False

    mutated = deepcopy(material)
    mutated[false_field] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(mutated)


def test_cs08_blocks_when_packet_scan_is_blocked() -> None:
    cs06 = cs.build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge()
    blocked_scan = cs.build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
        packet_generation_request_receipt_bridge=cs06,
        scanned_packet_count=23,
    )
    assert blocked_scan["scan_status_ref"] == cs.P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF

    material = cs.build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility(
        packet_completeness_export_denylist_scan=blocked_scan
    )
    assert material["selection_form_status_ref"] == cs.P7_R54_AHR_CS08_FORM_BLOCKED_STATUS_REF
    assert "cs07_packet_scan_not_ready" in material["execution_blocker_ids"]
    assert material["selection_form_structure_frozen"] is False
    assert material["actual_human_review_operation_receipt_intake_allowed_next"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(material) is True


def test_cs08_rejects_body_question_path_hash_key_injected_after_build() -> None:
    material = _build_ready_cs08()
    mutated = deepcopy(material)
    mutated["question_text"] = "should-not-exist"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(mutated)


def test_cs08_compatibility_aliases() -> None:
    material = cs.build_p7_r54_ahr_cs08_reviewer_selection_form_freeze()
    assert material["schema_version"] == cs.P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION
    assert cs.assert_p7_r54_ahr_cs08_reviewer_selection_form_freeze_contract(material) is True
    alias_material = (
        cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_reviewer_selection_form_current_compatibility_bodyfree()
    )
    assert alias_material["selection_form_status_ref"] == cs.P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_reviewer_selection_form_current_compatibility_bodyfree_contract(
            alias_material
        )
        is True
    )


def test_cs09_default_operation_receipt_is_blocked_fail_closed() -> None:
    cs08 = _build_ready_cs08()
    material = cs.build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
        reviewer_selection_form_current_compatibility=cs08
    )

    assert set(material) == set(cs.P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS09_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS09_STEP_REF
    assert material["operation_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF
    assert material["operation_receipt_ref"] == ""
    assert material["operation_receipt_ref_present"] is False
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_human_review_operation_receipt_intaken_here"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert "operation_receipt_ref_missing_or_unexpected" in material["execution_blocker_ids"]
    assert "actual_human_review_operation_run_not_confirmed" in material["execution_blocker_ids"]
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(material) is True


def test_cs09_actual_operation_receipt_intake_ready_bodyfree() -> None:
    material = _build_ready_cs09()

    assert set(material) == set(cs.P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS09_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS09_STEP_REF
    assert material["cs08_schema_version"] == cs.P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION
    assert material["cs08_next_required_step"] == cs.P7_R54_AHR_CS09_STEP_REF
    assert material["cs08_selection_form_status_ref"] == cs.P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
    assert material["cs08_actual_human_review_operation_receipt_intake_allowed_next"] is True

    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["existing_ahr_used_as_current_actual_review_evidence"] is False

    assert material["operation_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    assert material["operation_receipt_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    assert material["operation_receipt_reason_refs"] == [cs.P7_R54_AHR_CS09_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["selection_form_ready_for_operation_receipt_intake"] is True
    assert material["operation_receipt_ref"] == cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF
    assert material["operation_receipt_ref_present"] is True
    assert material["operation_receipt_bodyfree_only"] is True
    assert material["reviewer_person_ref"] == cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT
    assert material["reviewer_person_ref_present"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["review_started_at_bucket_ref"] == cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT
    assert material["review_completed_at_bucket_ref"] == cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT
    assert material["review_time_bucket_refs_present"] is True
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["reviewed_case_count_complete"] is True
    assert material["selection_row_count_complete"] is True
    assert material["selection_form_used"] is True
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["selection_only"] is True
    assert material["body_full_packet_read_local_only"] is True
    assert material["body_full_packet_content_available_to_local_reviewer_only"] is True

    assert material["actual_human_review_operation_run"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_operation_receipt_intaken_here"] is True
    assert material["actual_human_review_operation_receipt_bodyfree_only"] is True
    assert material["actual_human_review_operation_complete"] is True
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is True
    assert material["sanitized_review_result_rows_materialized_here"] is False
    assert material["rating_rows_materialized_here"] is False
    assert material["question_need_observation_rows_materialized_here"] is False
    assert material["disposal_receipt_materialized_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS10_STEP_REF
    _assert_bodyfree_no_touch_allowing_cs09_receipt(material)


@pytest.mark.parametrize("false_field", cs.P7_R54_AHR_CS09_BODYFREE_RECEIPT_FALSE_FLAG_REFS)
def test_cs09_receipt_bodyfree_flags_remain_false(false_field: str) -> None:
    material = _build_ready_cs09()
    assert material[false_field] is False

    mutated = deepcopy(material)
    mutated[false_field] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(mutated)


def test_cs09_blocks_when_reviewed_case_count_is_incomplete() -> None:
    cs08 = _build_ready_cs08()
    material = cs.build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
        reviewer_selection_form_current_compatibility=cs08,
        operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_operation_run=True,
        actual_human_review_executed_by_person=True,
        review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
        review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
        reviewed_case_count=23,
        selection_row_count=24,
    )

    assert material["operation_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF
    assert "reviewed_case_count_not_24" in material["execution_blocker_ids"]
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_human_review_operation_receipt_intaken_here"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(material) is True


def test_cs09_blocks_when_body_content_flag_is_supplied() -> None:
    cs08 = _build_ready_cs08()
    material = cs.build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
        reviewer_selection_form_current_compatibility=cs08,
        operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_operation_run=True,
        actual_human_review_executed_by_person=True,
        review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
        review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
        reviewed_case_count=24,
        selection_row_count=24,
        body_full_packet_content_included=True,
    )

    assert material["operation_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF
    assert "body_full_packet_content_included" in material["execution_blocker_ids"]
    assert material["body_full_packet_content_included"] is False
    assert material["actual_human_review_operation_run"] is False
    assert material["actual_human_review_executed_by_person"] is False
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(material) is True


def test_cs09_rejects_body_question_path_hash_key_injected_after_build() -> None:
    material = _build_ready_cs09()
    mutated = deepcopy(material)
    mutated["reviewer_free_text"] = "should-not-exist"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(mutated)


def test_cs09_rejects_release_or_p8_promotion_even_with_ready_receipt() -> None:
    material = _build_ready_cs09()
    for field in ("p5_confirmed_final", "p6_start_allowed", "p8_start_allowed", "release_allowed"):
        mutated = deepcopy(material)
        mutated[field] = True
        with pytest.raises(ValueError):
            cs.assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(mutated)


def test_cs09_compatibility_aliases() -> None:
    cs08 = _build_ready_cs08()
    material = cs.build_p7_r54_ahr_cs09_actual_human_review_local_only_operation_receipt_intake(
        reviewer_selection_form_current_compatibility=cs08,
        operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_operation_run=True,
        actual_human_review_executed_by_person=True,
        review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
        review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
        reviewed_case_count=24,
        selection_row_count=24,
    )
    assert material["operation_status_ref"] == cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    assert cs.assert_p7_r54_ahr_cs09_actual_human_review_local_only_operation_receipt_intake_contract(material) is True
    alias_material = (
        cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_actual_human_review_operation_receipt_intake_bodyfree(
            reviewer_selection_form_current_compatibility=cs08,
            operation_receipt_ref=cs.P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
            reviewer_person_ref=cs.P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT,
            reviewer_is_person=True,
            reviewer_person_confirmed=True,
            reviewer_local_only_read_receipt_present=True,
            actual_human_review_operation_run=True,
            actual_human_review_executed_by_person=True,
            review_started_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT,
            review_completed_at_bucket_ref=cs.P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT,
            reviewed_case_count=24,
            selection_row_count=24,
        )
    )
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_actual_human_review_operation_receipt_intake_bodyfree_contract(
            alias_material
        )
        is True
    )


def test_cs00_to_cs09_chain_preserves_no_touch_and_current_basis() -> None:
    cs08 = _build_ready_cs08()
    cs09 = _build_ready_cs09()

    assert cs08["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert cs09["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert cs09["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert cs09["existing_ahr_can_be_used_as_current_actual_review_evidence"] is False
    assert cs09["actual_human_review_operation_run"] is True
    assert cs09["actual_human_review_run_here"] is False
    assert cs09["actual_human_review_complete"] is False
    assert cs09["actual_review_evidence_complete"] is False
    assert cs09["sanitized_review_result_row_intake_allowed_next"] is True
    assert cs09["actual_rating_rows_materialized_here"] is False
    assert cs09["actual_question_need_observation_rows_materialized_here"] is False
    assert cs09["actual_disposal_receipt_materialized_here"] is False
    assert cs09["actual_r52_reintake_execution_confirmed"] is False
    assert cs09["p5_confirmed_final"] is False
    assert cs09["p6_start_allowed"] is False
    assert cs09["p8_start_allowed"] is False
    assert tuple(cs09["implemented_steps"]) == cs.P7_R54_AHR_CS09_IMPLEMENTED_STEPS
    assert cs09["next_required_step"] == cs.P7_R54_AHR_CS10_STEP_REF
