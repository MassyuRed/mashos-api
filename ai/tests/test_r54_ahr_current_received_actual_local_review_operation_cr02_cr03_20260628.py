# -*- coding: utf-8 -*-
"""R54-AHR-CR02/CR03 current received actual local review operation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as historical_ahr
import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr
import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as historical_cs


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in cr.P7_R54_AHR_CR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in (
        "raw_input",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "history_surface",
        "comment_text",
        "reviewer_free_text",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "packet_content",
        "body_full_packet_content",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
    ):
        assert forbidden_key not in material


def test_cr02_separates_historical_helper_refs_without_rewriting_existing_helpers() -> None:
    cr01 = cr.build_p7_r54_ahr_cr01_current_received_basis_envelope()
    material = cr.build_p7_r54_ahr_cr02_historical_helper_refs_separation(current_received_basis_envelope=cr01)

    assert set(material) == set(cr.P7_R54_AHR_CR02_HISTORICAL_HELPER_REFS_SEPARATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR02_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR02_STEP_REF
    assert material["cr01_schema_version"] == cr.P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION
    assert material["cr01_next_required_step"] == cr.P7_R54_AHR_CR02_STEP_REF
    assert material["cr01_current_basis_refrozen_here"] is True
    assert material["cr01_current_basis_status_ref"] == cr.P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["actual_review_basis_allowed_ref"] == "current_received_snapshot_264_85_258_171_only"
    assert material["outer_received_zip_refs"] == {
        "premise_zip_ref": "Cocolon_前提資料(264).zip",
        "implemented_materials_zip_ref": "EmlisAIの実装済み資料(85).zip",
        "roadmap_zip_ref": (
            "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(4).zip"
        ),
        "rn_zip_ref": "Cocolon(258).zip",
        "backend_zip_ref": "mashos-api(171).zip",
    }
    assert material["outer_received_zip_refs_used_as_actual_review_basis"] is True
    assert material["current_received_snapshot_refs_used_as_actual_review_basis"] is True
    assert material["internal_source_lineage_refs_separated"] is True

    assert material["historical_ahr_basis_ref"] == historical_ahr.P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF
    assert material["historical_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["historical_cs_basis_ref"] == historical_cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_cs_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["historical_basis_refs_used_as_current_actual_review_basis"] is False
    assert material["historical_basis_refs_used_as_current_actual_review_evidence"] is False

    assert material["historical_helper_separation_status_ref"] == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_SEPARATION_STATUS_REF
    assert material["historical_helper_refs_separated"] is True
    assert tuple(material["historical_helper_ref_groups"]) == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS
    assert material["historical_helper_ref_group_count"] == len(cr.P7_R54_AHR_CR_HISTORICAL_HELPER_REF_GROUP_REFS)
    assert material["historical_helper_refs"] == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_REFS
    assert material["historical_helper_ref_count"] == len(cr.P7_R54_AHR_CR_HISTORICAL_HELPER_REFS)
    assert material["historical_helper_role_refs"] == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_ROLE_REFS
    assert material["historical_helper_classification_refs"] == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_CLASSIFICATION_REFS
    assert tuple(material["historical_helper_allowed_usage_refs"]) == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_ALLOWED_USAGE_REFS
    assert tuple(material["historical_helper_prohibited_usage_refs"]) == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_PROHIBITED_USAGE_REFS
    assert set(material["historical_helper_ref_groups"]) == {
        "r54_ahr_20260627_basis",
        "r54_ahr_cs_20260628_basis",
        "r54_clr_refs",
        "r54_op_refs",
        "r54_ev_refs",
        "r55_refs",
        "r52_refs",
    }
    assert material["historical_helper_refs"]["r54_ahr_20260627_basis"]["backend_zip_ref"] == "mashos-api(169).zip"
    assert material["historical_helper_refs"]["r54_ahr_cs_20260628_basis"]["backend_zip_ref"] == "mashos-api(170).zip"
    assert all(
        value == "historical_structural_regression_ref_only"
        for value in material["historical_helper_classification_refs"].values()
    )

    assert material["historical_helper_refs_are_historical_here"] is True
    assert material["historical_helper_refs_are_structural_refs_only"] is True
    assert material["historical_helper_refs_are_regression_refs_only"] is True
    assert material["historical_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_current_actual_review_basis"] is False
    assert material["historical_helper_refs_used_as_current_actual_review_basis"] is False
    assert material["historical_helper_refs_can_be_used_for_current_actual_review_evidence"] is False
    assert material["historical_helper_refs_used_as_current_actual_review_evidence"] is False
    assert material["existing_ahr_used_as_current_actual_review_evidence"] is False
    assert material["existing_cs_used_as_current_actual_review_evidence"] is False
    assert material["helper_green_not_actual_human_review_complete"] is True
    assert material["synthetic_contract_rows_not_actual_review_rows"] is True
    assert material["separation_does_not_modify_helper_modules"] is True
    assert material["existing_helper_constants_rewritten"] is False
    assert material["existing_helper_refs_preserved_as_received"] is True
    assert material["current_264_85_258_171_remains_only_actual_review_basis"] is True
    assert material["cr02_does_not_execute_direct_diff"] is True
    assert material["cr02_does_not_assess_impact_as_no_impact"] is True
    assert material["cr02_does_not_create_manifest_packet_review_rows_or_disposal"] is True

    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR03_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr02_historical_helper_refs_separation_contract(material) is True


def test_cr03_records_basis_impact_without_converting_diff_unavailable_to_no_impact() -> None:
    cr02 = cr.build_p7_r54_ahr_cr02_historical_helper_refs_separation()
    material = cr.build_p7_r54_ahr_cr03_basis_impact_assessment(historical_helper_refs_separation=cr02)

    assert set(material) == set(cr.P7_R54_AHR_CR03_BASIS_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR03_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR03_STEP_REF
    assert material["cr02_schema_version"] == cr.P7_R54_AHR_CR_HISTORICAL_HELPER_REFS_SEPARATION_SCHEMA_VERSION
    assert material["cr02_next_required_step"] == cr.P7_R54_AHR_CR03_STEP_REF
    assert material["cr02_historical_helper_refs_separated"] is True
    assert material["cr02_historical_helper_refs_used_as_current_actual_review_evidence"] is False

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["basis_impact_assessment_status_ref"] == cr.P7_R54_AHR_CR_BASIS_IMPACT_ASSESSMENT_STATUS_REF
    assert material["basis_impact_assessment_from_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["basis_impact_assessment_to_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["historical_helper_refs_separated_before_impact_assessment"] is True
    assert material["basis_impact_assessed_here"] is True
    assert tuple(material["impact_target_refs"]) == cr.P7_R54_AHR_CR03_IMPACT_TARGET_REFS
    assert material["impact_target_ref_count"] == len(cr.P7_R54_AHR_CR03_IMPACT_TARGET_REFS)

    assert material["direct_file_diff_available"] is False
    assert material["direct_file_diff_executed"] is False
    assert material["direct_file_diff_not_available_reason_ref"] == cr.P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_REASON_REF_DEFAULT
    assert material["diff_impact_status_ref"] == cr.P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_RESULT_REF
    assert tuple(material["diff_impact_status_allowed_refs"]) == cr.P7_R54_AHR_CR03_DIFF_IMPACT_STATUS_REFS
    assert material["direct_diff_cannot_claim_no_impact"] is True
    assert material["diff_unavailable_does_not_equal_no_impact"] is True
    assert material["diff_unavailable_no_impact_claimed"] is False
    assert material["impact_summary_refs_bodyfree_only"] is True
    assert material["raw_diff_body_included"] is False
    assert material["body_full_diff_content_included"] is False
    assert material["local_file_path_included"] is False

    assert material["review_manifest_impact_unknown_until_current_manifest_refreeze"] is True
    assert material["current_manifest_refreeze_required"] is True
    assert material["current_manifest_refreeze_required_reason_ref"] == cr.P7_R54_AHR_CR03_DIRECT_DIFF_UNAVAILABLE_RESULT_REF
    assert material["old_manifest_allowed_as_current_manifest"] is False
    assert material["old_manifest_allowed_as_structural_ref"] is True
    assert material["old_manifest_unconditional_adoption_blocked"] is True
    assert material["old_packet_boundary_allowed_as_current_packet_boundary"] is False
    assert material["old_packet_boundary_unconditional_adoption_blocked"] is True
    assert material["old_evidence_rows_allowed_as_current_actual_review_rows"] is False
    assert material["old_evidence_rows_current_adoption_blocked"] is True
    assert material["current_24_case_manifest_must_be_refrozen_next"] is True
    assert material["current_manifest_refreeze_is_next_step"] is True
    assert material["cr03_does_not_create_manifest_packet_review_rows_or_disposal"] is True

    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR04_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(material) is True


def test_cr03_records_bodyfree_executed_diff_without_storing_diff_body() -> None:
    material = cr.build_p7_r54_ahr_cr03_basis_impact_assessment(
        direct_diff_available=True,
        direct_diff_executed=True,
    )

    assert material["direct_file_diff_available"] is True
    assert material["direct_file_diff_executed"] is True
    assert material["direct_file_diff_not_available_reason_ref"] == ""
    assert material["diff_impact_status_ref"] == cr.P7_R54_AHR_CR03_DIRECT_DIFF_EXECUTED_RESULT_REF
    assert material["direct_diff_cannot_claim_no_impact"] is False
    assert material["diff_unavailable_does_not_equal_no_impact"] is False
    assert material["diff_unavailable_no_impact_claimed"] is False
    assert material["raw_diff_body_included"] is False
    assert material["body_full_diff_content_included"] is False
    assert material["local_file_path_included"] is False
    assert material["current_manifest_refreeze_required"] is True
    assert material["current_manifest_refreeze_required_reason_ref"] == cr.P7_R54_AHR_CR03_DIRECT_DIFF_EXECUTED_RESULT_REF
    assert cr.assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("historical_helper_refs_can_be_used_for_current_actual_review_basis", True),
        ("historical_helper_refs_used_as_current_actual_review_basis", True),
        ("historical_helper_refs_can_be_used_for_current_actual_review_evidence", True),
        ("historical_helper_refs_used_as_current_actual_review_evidence", True),
        ("existing_ahr_used_as_current_actual_review_evidence", True),
        ("existing_cs_used_as_current_actual_review_evidence", True),
        ("helper_green_not_actual_human_review_complete", False),
        ("synthetic_contract_rows_not_actual_review_rows", False),
        ("separation_does_not_modify_helper_modules", False),
        ("existing_helper_constants_rewritten", True),
        ("existing_helper_refs_preserved_as_received", False),
        ("current_264_85_258_171_remains_only_actual_review_basis", False),
        ("cr02_does_not_execute_direct_diff", False),
        ("cr02_does_not_assess_impact_as_no_impact", False),
        ("cr02_does_not_create_manifest_packet_review_rows_or_disposal", False),
        ("historical_helper_green_claimed_as_actual_review_complete", True),
        ("synthetic_contract_rows_used_as_actual_review_rows", True),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cr02_rejects_historical_ref_evidence_relabeling_or_promotion(key: str, value: object) -> None:
    mutated = deepcopy(cr.build_p7_r54_ahr_cr02_historical_helper_refs_separation())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr02_historical_helper_refs_separation_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("direct_file_diff_executed", True),
        ("direct_file_diff_not_available_reason_ref", ""),
        ("diff_impact_status_ref", "NO_REVIEW_MANIFEST_IMPACT"),
        ("direct_diff_cannot_claim_no_impact", False),
        ("diff_unavailable_does_not_equal_no_impact", False),
        ("diff_unavailable_no_impact_claimed", True),
        ("impact_summary_refs_bodyfree_only", False),
        ("raw_diff_body_included", True),
        ("body_full_diff_content_included", True),
        ("local_file_path_included", True),
        ("review_manifest_impact_unknown_until_current_manifest_refreeze", False),
        ("current_manifest_refreeze_required", False),
        ("old_manifest_allowed_as_current_manifest", True),
        ("old_manifest_allowed_as_structural_ref", False),
        ("old_manifest_unconditional_adoption_blocked", False),
        ("old_packet_boundary_allowed_as_current_packet_boundary", True),
        ("old_packet_boundary_unconditional_adoption_blocked", False),
        ("old_evidence_rows_allowed_as_current_actual_review_rows", True),
        ("old_evidence_rows_current_adoption_blocked", False),
        ("current_24_case_manifest_must_be_refrozen_next", False),
        ("current_manifest_refreeze_is_next_step", False),
        ("cr03_does_not_create_manifest_packet_review_rows_or_disposal", False),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cr03_rejects_no_impact_claims_body_leak_old_adoption_or_promotion(key: str, value: object) -> None:
    mutated = deepcopy(cr.build_p7_r54_ahr_cr03_basis_impact_assessment())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(mutated)


def test_cr02_cr03_reject_forbidden_body_question_path_or_hash_keys() -> None:
    mutated02 = deepcopy(cr.build_p7_r54_ahr_cr02_historical_helper_refs_separation())
    mutated02["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr02_historical_helper_refs_separation_contract(mutated02)

    mutated03 = deepcopy(cr.build_p7_r54_ahr_cr03_basis_impact_assessment())
    mutated03["local_absolute_path"] = "/tmp/forbidden"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr03_basis_impact_assessment_contract(mutated03)


def test_cr02_cr03_aliases_preserve_contract() -> None:
    cr01 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_current_received_basis_envelope_bodyfree()
    cr02 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_historical_helper_refs_separation_bodyfree(
        current_received_basis_envelope=cr01
    )
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_historical_helper_refs_separation_bodyfree_contract(
            cr02
        )
        is True
    )

    cr03 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_basis_impact_assessment_bodyfree(
        historical_helper_refs_separation=cr02
    )
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_basis_impact_assessment_bodyfree_contract(
            cr03
        )
        is True
    )
