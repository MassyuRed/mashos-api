# -*- coding: utf-8 -*-
"""R54-AHR-CS00/CS01 current snapshot actual review re-entry tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as historical_ahr
import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
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
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
    ):
        assert forbidden_key not in material


def test_cs00_freezes_scope_and_no_touch_boundary_for_current_snapshot_reentry() -> None:
    material = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()

    assert set(material) == set(cs.P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["current_phase"] == cs.P7_R54_AHR_CS_CURRENT_PHASE
    assert material["step"] == cs.P7_R54_AHR_CS_STEP
    assert material["scope"] == cs.P7_R54_AHR_CS_SCOPE
    assert material["policy_kind"] == cs.P7_R54_AHR_CS_POLICY_KIND
    assert material["policy_section"] == cs.P7_R54_AHR_CS00_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS00_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False

    assert material["scope_boundary_confirmed"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_touch_boundary_frozen"] is True
    assert material["current_snapshot_actual_review_reentry_selected"] is True
    assert material["r54_ahr_cs_prefix_used"] is True
    assert material["p7_r54_ahr_line_preserved"] is True
    assert material["existing_ahr_helper_direct_rewrite_out_of_scope"] is True
    assert material["current_basis_refreeze_required_next"] is True
    assert material["current_basis_refrozen_here"] is False
    assert material["cs00_does_not_claim_current_basis_complete"] is True

    assert material["current_received_snapshot_refs"] == cs.P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["current_received_snapshot_refs"]["premise_zip_ref"] == "Cocolon_前提資料(262).zip"
    assert material["current_received_snapshot_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(84).zip"
    assert material["current_received_snapshot_refs"]["rn_zip_ref"] == "Cocolon(257).zip"
    assert material["current_received_snapshot_refs"]["backend_zip_ref"] == "mashos-api(170).zip"
    assert tuple(material["required_current_received_snapshot_ref_keys"]) == (
        cs.P7_R54_AHR_CS_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    )
    assert material["all_required_current_received_snapshot_refs_present"] is True
    assert material["current_received_snapshot_refs_are_actual_review_basis"] is False
    assert material["current_received_snapshot_refs_used_as_actual_review_basis"] is False

    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["existing_ahr_basis_allowed"] == "current_received_snapshot_260_83_256_169_only"
    assert material["existing_ahr_basis_refs"] == historical_ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["existing_ahr_basis_matches_current"] is False
    assert material["existing_ahr_can_be_used_as_current_actual_review_evidence"] is False
    assert material["existing_ahr_used_as_current_actual_review_evidence"] is False
    assert material["existing_ahr_helper_rewritten"] is False
    assert material["existing_ahr_helper_preserved_as_historical_structural_regression_ref"] is True
    assert material["current_basis_does_not_rewrite_existing_ahr_helper"] is True
    assert material["old_260_83_256_169_not_relabelled_as_current"] is True

    assert material["p8_p6_r52_p5_release_out_of_scope"] is True
    assert material["api_db_rn_runtime_public_contract_no_touch_boundary_frozen"] is True
    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert "p8_question_api_db_rn_trigger_storage_or_text_generation" in material["out_of_scope_refs"]
    assert "api_route_or_request_response_key_change" in material["out_of_scope_refs"]
    assert "body_full_packet_generation_or_export" in material["out_of_scope_refs"]
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS01_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(material) is True


def test_cs01_refreezes_current_262_84_257_170_basis_without_rewriting_existing_ahr() -> None:
    cs00 = cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze()
    material = cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=cs00)

    assert set(material) == set(cs.P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS_CURRENT_SNAPSHOT_BASIS_ENVELOPE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS01_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS01_STEP_REF
    assert material["cs00_schema_version"] == cs.P7_R54_AHR_CS_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["cs00_next_required_step"] == cs.P7_R54_AHR_CS01_STEP_REF
    assert material["cs00_scope_boundary_confirmed"] is True
    assert material["cs00_no_touch_boundary_confirmed"] is True
    assert material["current_basis_status_ref"] == cs.P7_R54_AHR_CS_CURRENT_BASIS_STATUS_REF

    refs = material["current_received_snapshot_refs"]
    assert refs == cs.P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert refs["premise_zip_ref"] == "Cocolon_前提資料(262).zip"
    assert refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(84).zip"
    assert refs["rn_zip_ref"] == "Cocolon(257).zip"
    assert refs["backend_zip_ref"] == "mashos-api(170).zip"
    assert refs["roadmap_ref"] == "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md"
    assert refs["pre_design_memo_ref"] == "Cocolon_EmlisAI_P7_R54AHR_CurrentSnapshotActualReview_PreDesignMemo_20260628.md"
    assert (
        refs["detailed_design_ref"]
        == "Cocolon_EmlisAI_P7_R54AHR_CurrentSnapshotActualReview_Reentry_DetailedDesign_ImplementationOrder_20260628.md"
    )
    assert tuple(material["current_received_snapshot_ref_keys"]) == cs.P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert tuple(material["required_current_received_snapshot_ref_keys"]) == (
        cs.P7_R54_AHR_CS_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    )
    assert material["all_required_current_received_snapshot_refs_present"] is True
    assert material["current_received_snapshot_refs_match_262_84_257_170"] is True
    assert material["current_received_snapshot_refs_are_actual_review_basis"] is True
    assert material["current_received_snapshot_refs_used_as_actual_review_basis"] is True

    assert material["actual_review_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["actual_review_basis_allowed"] == "current_received_snapshot_262_84_257_170_only"
    assert material["existing_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["existing_ahr_basis_allowed"] == "current_received_snapshot_260_83_256_169_only"
    assert material["existing_ahr_basis_refs"] == historical_ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["existing_ahr_basis_refs"]["premise_zip_ref"] == "Cocolon_前提資料(260).zip"
    assert material["existing_ahr_basis_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(83).zip"
    assert material["existing_ahr_basis_refs"]["rn_zip_ref"] == "Cocolon(256).zip"
    assert material["existing_ahr_basis_refs"]["backend_zip_ref"] == "mashos-api(169).zip"
    assert material["existing_ahr_basis_matches_current"] is False
    assert material["existing_ahr_can_be_used_as_current_actual_review_evidence"] is False
    assert material["existing_ahr_used_as_current_actual_review_evidence"] is False
    assert material["existing_ahr_helper_rewritten"] is False
    assert material["existing_ahr_helper_preserved_as_historical_structural_regression_ref"] is True
    assert material["current_basis_does_not_rewrite_existing_ahr_helper"] is True
    assert material["old_260_83_256_169_not_relabelled_as_current"] is True

    assert material["current_basis_refrozen_here"] is True
    assert material["current_basis_refrozen_for_actual_review_reentry"] is True
    assert material["current_262_84_257_170_does_not_claim_actual_review_complete"] is True
    assert material["current_basis_wrapper_only"] is True
    assert material["new_full_operation_helper_required_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS02_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("api_route_changed", True),
        ("request_response_key_changed", True),
        ("db_schema_changed", True),
        ("db_physical_schema_changed", True),
        ("rn_ui_changed", True),
        ("rn_display_condition_changed", True),
        ("runtime_generation_changed", True),
        ("public_response_key_changed", True),
        ("p8_question_api_created", True),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_executed_by_person", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("raw_input_included", True),
        ("returned_emlis_body_included", True),
        ("question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("packet_content_included", True),
    ],
)
def test_cs00_rejects_touch_promotion_or_body_flags(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("actual_review_basis_ref", "current_received_snapshot_260_83_256_169"),
        ("actual_review_basis_allowed", "current_received_snapshot_260_83_256_169_only"),
        ("current_received_snapshot_refs_match_262_84_257_170", False),
        ("all_required_current_received_snapshot_refs_present", False),
        ("current_received_snapshot_refs_are_actual_review_basis", False),
        ("current_received_snapshot_refs_used_as_actual_review_basis", False),
        ("existing_ahr_basis_matches_current", True),
        ("existing_ahr_can_be_used_as_current_actual_review_evidence", True),
        ("existing_ahr_used_as_current_actual_review_evidence", True),
        ("existing_ahr_helper_rewritten", True),
        ("existing_ahr_helper_preserved_as_historical_structural_regression_ref", False),
        ("current_basis_refrozen_here", False),
        ("current_basis_refrozen_for_actual_review_reentry", False),
        ("current_basis_wrapper_only", False),
        ("new_full_operation_helper_required_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_cs01_rejects_basis_or_boundary_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze())
    mutated[key] = value
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(mutated)


def test_cs01_rejects_missing_or_old_current_snapshot_ref() -> None:
    mutated = deepcopy(cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze())
    mutated["current_received_snapshot_refs"]["backend_zip_ref"] = "mashos-api(169).zip"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(mutated)

    missing = deepcopy(cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze())
    del missing["current_received_snapshot_refs"]["backend_zip_ref"]
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(missing)


def test_cs_rejects_forbidden_body_question_path_or_hash_keys() -> None:
    mutated00 = deepcopy(cs.build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze())
    mutated00["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(mutated00)

    mutated01 = deepcopy(cs.build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze())
    mutated01["local_absolute_path"] = "/tmp/forbidden"
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(mutated01)


def test_cs_aliases_preserve_contract() -> None:
    cs00 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_scope_no_touch_boundary_freeze_bodyfree()
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_scope_no_touch_boundary_freeze_bodyfree_contract(cs00)
        is True
    )

    cs01 = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_current_basis_envelope_bodyfree(
        scope_no_touch_boundary_freeze=cs00
    )
    assert (
        cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_current_basis_envelope_bodyfree_contract(cs01)
        is True
    )
