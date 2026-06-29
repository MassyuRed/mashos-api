# -*- coding: utf-8 -*-
"""R54-AHR-CS02/CS03 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as historical_ahr
import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "raw_body",
    "returned_emlis_body",
    "history_surface",
    "comment_text",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "raw_diff_body",
    "body_full_diff_content",
    "local_absolute_path",
    "local_file_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
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


def test_cs00_cs01_are_present_before_cs02_cs03() -> None:
    cs00 = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()
    cs01 = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=cs00)

    assert cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(cs00) is True
    assert cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(cs01) is True
    assert tuple(cs01["implemented_steps"]) == cs.P7_R54_AHR_CS01_IMPLEMENTED_STEPS
    assert cs01["next_required_step"] == cs.P7_R54_AHR_CS02_STEP_REF
    assert cs01["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert cs01["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert cs01["existing_ahr_used_as_current_actual_review_evidence"] is False


def test_cs02_reconciles_historical_helper_refs_without_using_them_as_current_evidence() -> None:
    cs01 = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze()
    material = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile(current_snapshot_basis_refreeze=cs01)

    assert set(material) == set(cs.P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS02_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS02_STEP_REF
    assert material["cs01_schema_version"] == cs.P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION
    assert material["cs01_next_required_step"] == cs.P7_R54_AHR_CS02_STEP_REF
    assert material["cs01_current_basis_refrozen_here"] is True

    assert material["historical_helper_refs_reconcile_status_ref"] == (
        cs.P7_R54_AHR_CS_HISTORICAL_HELPER_RECONCILE_STATUS_REF
    )
    assert tuple(material["historical_helper_ref_groups"]) == cs.P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS
    assert material["historical_helper_ref_group_count"] == 7
    assert set(material["historical_helper_ref_groups"]) == {
        "r52_20260621",
        "r54_bodyfree_handoff_20260622",
        "r55_20260623",
        "r54_op_20260625",
        "r54_ev_20260626",
        "r54_clr_20260627",
        "r54_ahr_20260627",
    }
    assert material["historical_helper_refs"]["r54_ahr_20260627"] == (
        historical_ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    )
    assert material["historical_helper_refs"]["r54_ahr_20260627"]["premise_zip_ref"] == "Cocolon_前提資料(260).zip"
    assert material["historical_helper_refs"]["r54_ahr_20260627"]["backend_zip_ref"] == "mashos-api(169).zip"
    assert material["historical_helper_basis_refs"]["r54_ahr_20260627"] == (
        "current_received_snapshot_260_83_256_169"
    )

    assert material["historical_helper_ref_row_count"] == 7
    assert len(material["historical_helper_ref_rows"]) == 7
    for row in material["historical_helper_ref_rows"]:
        assert row["body_free"] is True
        assert row["matches_current_basis"] is False
        assert row["allowed_as_structural_ref"] is True
        assert row["allowed_as_regression_ref"] is True
        assert row["allowed_as_current_actual_review_evidence"] is False
        assert row["used_as_current_actual_review_evidence"] is False
        assert row["helper_green_can_claim_actual_review_complete"] is False
        assert row["rewritten_here"] is False
        assert row["differing_current_basis_ref_key_count"] >= 4

    assert all(value is False for value in material["historical_helper_refs_match_current_basis_262_84_257_170"].values())
    assert set(material["historical_helper_differing_current_basis_ref_keys"]) == set(
        cs.P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS
    )
    assert material["differing_current_basis_ref_group_count"] == 7
    assert tuple(material["historical_helper_green_claim_boundary_refs"]) == (
        cs.P7_R54_AHR_CS_HISTORICAL_HELPER_GREEN_CLAIM_BOUNDARY_REFS
    )

    assert material["historical_helper_refs_are_historical_here"] is True
    assert material["historical_helper_refs_are_structural_refs_only"] is True
    assert material["historical_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_actual_review_basis"] is False
    assert material["historical_helper_refs_used_as_actual_review_basis"] is False
    assert material["historical_helper_refs_can_be_used_for_current_actual_review_evidence"] is False
    assert material["historical_helper_refs_used_as_current_actual_review_evidence"] is False
    assert material["historical_helper_output_used_as_current_actual_evidence"] is False
    assert material["helper_green_not_actual_human_review_complete"] is True
    assert material["synthetic_contract_rows_not_actual_review_rows"] is True
    assert material["r52_handoff_ready_contract_not_actual_r52_reintake_execution"] is True
    assert material["reconcile_does_not_modify_helper_modules"] is True
    assert material["existing_helper_constants_not_rewritten"] is True
    assert material["existing_helper_constants_rewritten"] is False
    assert material["current_refs_override_uses_thin_current_reentry_boundary_layer"] is True
    assert material["new_thin_boundary_helper_only"] is True
    assert material["new_full_operation_helper_required_here"] is False

    assert material["actual_review_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["existing_ahr_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["existing_ahr_used_as_current_actual_review_evidence"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS03_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(material) is True


def test_cs03_marks_direct_diff_unavailable_and_requires_current_manifest_refreeze() -> None:
    cs02 = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile()
    material = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment(
        historical_helper_refs_reconcile=cs02
    )

    assert set(material) == set(
        cs.P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS
    )
    assert material["schema_version"] == (
        cs.P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION
    )
    assert material["policy_section"] == cs.P7_R54_AHR_CS03_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS03_STEP_REF
    assert material["cs02_schema_version"] == cs.P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
    assert material["cs02_next_required_step"] == cs.P7_R54_AHR_CS03_STEP_REF
    assert material["cs02_historical_helper_refs_separated"] is True
    assert material["cs02_historical_helper_refs_used_as_current_actual_review_evidence"] is False

    assert material["current_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["historical_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert tuple(material["impact_target_refs"]) == cs.P7_R54_AHR_CS03_IMPACT_TARGET_REFS
    assert material["impact_target_ref_count"] == len(cs.P7_R54_AHR_CS03_IMPACT_TARGET_REFS)
    assert set(material["impact_target_refs"]) == {
        "current_24_case_manifest",
        "local_only_packet_boundary",
        "bodyfree_evidence_rows",
        "actual_review_receipt_chain",
        "r52_reintake_handoff_candidate_envelope",
    }

    assert material["direct_file_diff_available"] is False
    assert material["direct_file_diff_executed"] is False
    assert material["direct_file_diff_not_available_reason_ref"] == (
        cs.P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_REASON_REF
    )
    assert material["diff_impact_status_ref"] == cs.P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF
    assert tuple(material["diff_impact_status_allowed_refs"]) == cs.P7_R54_AHR_CS03_DIFF_IMPACT_STATUS_REFS
    assert material["direct_diff_cannot_claim_no_impact"] is True
    assert material["diff_unavailable_does_not_equal_no_impact"] is True
    assert material["review_manifest_impact_unknown_until_current_manifest_refreeze"] is True

    assert material["current_manifest_refreeze_required"] is True
    assert material["current_manifest_refreeze_required_reason_ref"] == (
        cs.P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF
    )
    assert material["old_manifest_allowed_as_current_manifest"] is False
    assert material["old_manifest_allowed_as_structural_ref"] is True
    assert material["old_manifest_unconditional_adoption_blocked"] is True
    assert material["old_packet_boundary_allowed_as_current_packet_boundary"] is False
    assert material["old_evidence_rows_allowed_as_current_actual_review_rows"] is False
    assert material["current_24_case_manifest_must_be_refrozen_next"] is True

    assert material["body_full_diff_content_included"] is False
    assert material["raw_diff_body_included"] is False
    assert material["local_file_path_included"] is False
    assert material["terminal_output_body_included"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False

    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS04_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("historical_helper_refs_separated", False),
        ("historical_helper_refs_are_historical_here", False),
        ("historical_helper_refs_are_structural_refs_only", False),
        ("historical_helper_refs_can_be_used_for_helper_regression_only", False),
        ("historical_helper_refs_can_be_used_for_actual_review_basis", True),
        ("historical_helper_refs_used_as_actual_review_basis", True),
        ("historical_helper_refs_can_be_used_for_current_actual_review_evidence", True),
        ("historical_helper_refs_used_as_current_actual_review_evidence", True),
        ("historical_helper_output_used_as_current_actual_evidence", True),
        ("helper_green_not_actual_human_review_complete", False),
        ("synthetic_contract_rows_not_actual_review_rows", False),
        ("r52_handoff_ready_contract_not_actual_r52_reintake_execution", False),
        ("reconcile_does_not_modify_helper_modules", False),
        ("existing_helper_constants_not_rewritten", False),
        ("existing_helper_constants_rewritten", True),
        ("new_full_operation_helper_required_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cs02_rejects_historical_basis_mixing_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("direct_file_diff_available", True),
        ("direct_file_diff_executed", True),
        ("diff_impact_status_ref", "NO_REVIEW_MANIFEST_IMPACT"),
        ("direct_diff_cannot_claim_no_impact", False),
        ("diff_unavailable_does_not_equal_no_impact", False),
        ("review_manifest_impact_unknown_until_current_manifest_refreeze", False),
        ("current_manifest_refreeze_required", False),
        ("old_manifest_allowed_as_current_manifest", True),
        ("old_manifest_allowed_as_structural_ref", False),
        ("old_manifest_unconditional_adoption_blocked", False),
        ("old_packet_boundary_allowed_as_current_packet_boundary", True),
        ("old_evidence_rows_allowed_as_current_actual_review_rows", True),
        ("current_24_case_manifest_must_be_refrozen_next", False),
        ("body_full_diff_content_included", True),
        ("raw_diff_body_included", True),
        ("local_file_path_included", True),
        ("terminal_output_body_included", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_cs03_rejects_diff_noimpact_claim_or_promotion_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(mutated)


def test_cs02_cs03_reject_body_or_question_payload_keys() -> None:
    cs02 = cs.build_p7_r54_ahr_cs02_historical_helper_refs_reconcile()
    mutated02 = deepcopy(cs02)
    mutated02["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(mutated02)

    cs03 = cs.build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment()
    mutated03 = deepcopy(cs03)
    mutated03["raw_diff_body"] = "forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(mutated03)


def test_cs02_cs03_aliases_preserve_contract() -> None:
    cs02 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_historical_helper_refs_reconcile_bodyfree()
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_historical_helper_refs_reconcile_bodyfree_contract(
            cs02
        )
        is True
    )

    cs03 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_manifest_packet_evidence_impact_assessment_bodyfree(
        historical_helper_refs_reconcile=cs02
    )
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_manifest_packet_evidence_impact_assessment_bodyfree_contract(
            cs03
        )
        is True
    )
