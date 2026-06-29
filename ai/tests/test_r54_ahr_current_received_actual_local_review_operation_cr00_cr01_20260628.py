# -*- coding: utf-8 -*-
"""R54-AHR-CR00/CR01 current received actual local review operation tests."""

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


def test_cr00_freezes_scope_and_no_touch_boundary_for_current_received_operation() -> None:
    material = cr.build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze()

    assert set(material) == set(cr.P7_R54_AHR_CR00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert material["current_phase"] == cr.P7_R54_AHR_CR_CURRENT_PHASE
    assert material["step"] == cr.P7_R54_AHR_CR_STEP
    assert material["scope"] == cr.P7_R54_AHR_CR_SCOPE
    assert material["policy_kind"] == cr.P7_R54_AHR_CR_POLICY_KIND
    assert material["policy_section"] == cr.P7_R54_AHR_CR00_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR00_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False

    assert material["scope_boundary_confirmed"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_touch_boundary_frozen"] is True
    assert material["current_received_actual_local_review_operation_selected"] is True
    assert material["r54_ahr_cr_prefix_used"] is True
    assert material["p7_r54_ahr_line_preserved"] is True
    assert material["cr00_does_not_claim_current_basis_complete"] is True
    assert material["current_basis_refreeze_required_next"] is True
    assert material["current_basis_refrozen_here"] is False
    assert material["current_received_basis_refrozen_for_actual_review_operation"] is False

    refs = material["current_received_snapshot_refs"]
    assert refs == cr.P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert refs["premise_zip_ref"] == "Cocolon_前提資料(264).zip"
    assert refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(85).zip"
    assert refs["roadmap_zip_ref"] == (
        "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(4).zip"
    )
    assert refs["rn_zip_ref"] == "Cocolon(258).zip"
    assert refs["backend_zip_ref"] == "mashos-api(171).zip"
    assert tuple(material["current_received_snapshot_ref_keys"]) == cr.P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert tuple(material["required_current_received_snapshot_ref_keys"]) == (
        cr.P7_R54_AHR_CR_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    )
    assert material["all_required_current_received_snapshot_refs_present"] is True
    assert material["outer_received_zip_refs_present"] is True
    assert material["outer_received_zip_refs_are_actual_review_basis"] is False
    assert material["outer_received_zip_refs_used_as_actual_review_basis"] is False
    assert material["current_received_snapshot_refs_are_actual_review_basis"] is False
    assert material["current_received_snapshot_refs_used_as_actual_review_basis"] is False
    assert material["internal_source_lineage_refs_separated"] is True
    assert material["outer_received_zip_refs_internal_lineage_same_object"] is False

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["actual_review_basis_allowed_ref"] == "current_received_snapshot_264_85_258_171_only"

    assert material["historical_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["historical_ahr_basis_allowed_ref"] == "current_received_snapshot_260_83_256_169_only"
    assert material["historical_ahr_basis_refs"] == historical_ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["historical_cs_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["historical_cs_basis_allowed_ref"] == "current_received_snapshot_262_84_257_170_only"
    assert material["historical_cs_basis_refs"] == historical_cs.P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_basis_refs_are_structural_or_regression_refs_only"] is True
    assert material["historical_basis_refs_used_as_current_actual_review_basis"] is False
    assert material["historical_basis_refs_used_as_current_actual_review_evidence"] is False
    assert material["historical_helper_green_claimed_as_actual_review_complete"] is False
    assert material["synthetic_contract_rows_used_as_actual_review_rows"] is False
    assert material["existing_ahr_helper_rewritten"] is False
    assert material["existing_cs_helper_rewritten"] is False
    assert material["old_260_83_256_169_not_relabelled_as_current"] is True
    assert material["old_262_84_257_170_not_relabelled_as_current"] is True

    assert material["p8_question_design_out_of_scope"] is True
    assert material["p8_question_implementation_out_of_scope"] is True
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
    assert "actual_human_review_execution" in material["out_of_scope_refs"]
    assert "body_full_packet_generation_or_export" in material["out_of_scope_refs"]
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR01_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_contract(material) is True


def test_cr01_refreezes_current_received_264_85_258_171_basis_envelope_only() -> None:
    cr00 = cr.build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze()
    material = cr.build_p7_r54_ahr_cr01_current_received_basis_envelope(scope_no_touch_boundary_freeze=cr00)

    assert set(material) == set(cr.P7_R54_AHR_CR01_CURRENT_RECEIVED_BASIS_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cr.P7_R54_AHR_CR_CURRENT_RECEIVED_BASIS_ENVELOPE_SCHEMA_VERSION
    assert material["policy_section"] == cr.P7_R54_AHR_CR01_STEP_REF
    assert material["operation_step_ref"] == cr.P7_R54_AHR_CR01_STEP_REF
    assert material["cr00_schema_version"] == cr.P7_R54_AHR_CR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["cr00_next_required_step"] == cr.P7_R54_AHR_CR01_STEP_REF
    assert material["cr00_scope_boundary_confirmed"] is True
    assert material["cr00_no_touch_boundary_confirmed"] is True
    assert material["current_basis_status_ref"] == cr.P7_R54_AHR_CR_CURRENT_BASIS_STATUS_REF

    refs = material["current_received_snapshot_refs"]
    assert refs == cr.P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert refs["premise_zip_ref"] == "Cocolon_前提資料(264).zip"
    assert refs["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(85).zip"
    assert refs["rn_zip_ref"] == "Cocolon(258).zip"
    assert refs["backend_zip_ref"] == "mashos-api(171).zip"
    assert refs["pre_design_memo_ref"] == (
        "Cocolon_EmlisAI_P7_R54AHR_CurrentReceivedSnapshotActualReview_PreDesignMemo_20260628.md"
    )
    assert refs["detailed_design_ref"] == (
        "Cocolon_EmlisAI_P7_R54AHR_CurrentReceivedSnapshotActualLocalReviewOperation_"
        "DetailedDesign_ImplementationOrder_20260628.md"
    )
    assert tuple(material["current_received_snapshot_ref_keys"]) == cr.P7_R54_AHR_CR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert tuple(material["required_current_received_snapshot_ref_keys"]) == (
        cr.P7_R54_AHR_CR_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    )
    assert material["all_required_current_received_snapshot_refs_present"] is True
    assert material["outer_received_zip_refs"] == {
        "premise_zip_ref": "Cocolon_前提資料(264).zip",
        "implemented_materials_zip_ref": "EmlisAIの実装済み資料(85).zip",
        "roadmap_zip_ref": (
            "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(4).zip"
        ),
        "rn_zip_ref": "Cocolon(258).zip",
        "backend_zip_ref": "mashos-api(171).zip",
    }
    assert material["outer_received_zip_refs_present"] is True
    assert material["current_received_snapshot_refs_match_264_85_258_171"] is True
    assert material["outer_received_zip_refs_are_actual_review_basis"] is True
    assert material["outer_received_zip_refs_used_as_actual_review_basis"] is True
    assert material["current_received_snapshot_refs_are_actual_review_basis"] is True
    assert material["current_received_snapshot_refs_used_as_actual_review_basis"] is True
    assert material["internal_source_lineage_refs_separated"] is True
    assert material["outer_received_zip_refs_internal_lineage_same_object"] is False

    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["actual_review_basis_allowed_ref"] == "current_received_snapshot_264_85_258_171_only"
    assert material["historical_ahr_basis_ref"] == historical_ahr.P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF
    assert material["historical_ahr_basis_ref"] == "current_received_snapshot_260_83_256_169"
    assert material["historical_ahr_basis_refs"]["premise_zip_ref"] == "Cocolon_前提資料(260).zip"
    assert material["historical_ahr_basis_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(83).zip"
    assert material["historical_ahr_basis_refs"]["rn_zip_ref"] == "Cocolon(256).zip"
    assert material["historical_ahr_basis_refs"]["backend_zip_ref"] == "mashos-api(169).zip"
    assert material["historical_cs_basis_ref"] == historical_cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_cs_basis_ref"] == "current_received_snapshot_262_84_257_170"
    assert material["historical_cs_basis_refs"]["premise_zip_ref"] == "Cocolon_前提資料(262).zip"
    assert material["historical_cs_basis_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(84).zip"
    assert material["historical_cs_basis_refs"]["rn_zip_ref"] == "Cocolon(257).zip"
    assert material["historical_cs_basis_refs"]["backend_zip_ref"] == "mashos-api(170).zip"
    assert material["historical_basis_refs_are_structural_or_regression_refs_only"] is True
    assert material["historical_basis_refs_used_as_current_actual_review_basis"] is False
    assert material["historical_basis_refs_used_as_current_actual_review_evidence"] is False
    assert material["existing_ahr_helper_rewritten"] is False
    assert material["existing_cs_helper_rewritten"] is False
    assert material["current_basis_does_not_rewrite_existing_ahr_or_cs_helpers"] is True

    assert material["current_basis_refrozen_here"] is True
    assert material["current_received_basis_refrozen_for_actual_review_operation"] is True
    assert material["current_264_85_258_171_does_not_claim_actual_review_complete"] is True
    assert material["current_basis_envelope_only"] is True
    assert material["cr01_does_not_create_manifest_packet_review_rows_or_disposal"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_complete"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["p5_confirmed_final"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cr.P7_R54_AHR_CR01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cr.P7_R54_AHR_CR01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cr.P7_R54_AHR_CR02_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert cr.assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("api_changed", True),
        ("api_route_changed", True),
        ("request_key_changed", True),
        ("response_key_changed", True),
        ("db_schema_changed", True),
        ("db_physical_schema_changed", True),
        ("rn_ui_changed", True),
        ("rn_visible_contract_changed", True),
        ("runtime_changed", True),
        ("user_label_connection_runtime_changed", True),
        ("public_response_key_changed", True),
        ("question_api_implemented", True),
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
def test_cr00_rejects_touch_promotion_or_body_flags(key: str, value: object) -> None:
    mutated = deepcopy(cr.build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("actual_review_basis_ref", "current_received_snapshot_262_84_257_170"),
        ("actual_review_basis_allowed_ref", "current_received_snapshot_262_84_257_170_only"),
        ("current_received_snapshot_refs_match_264_85_258_171", False),
        ("all_required_current_received_snapshot_refs_present", False),
        ("outer_received_zip_refs_present", False),
        ("outer_received_zip_refs_are_actual_review_basis", False),
        ("outer_received_zip_refs_used_as_actual_review_basis", False),
        ("current_received_snapshot_refs_are_actual_review_basis", False),
        ("current_received_snapshot_refs_used_as_actual_review_basis", False),
        ("internal_source_lineage_refs_separated", False),
        ("outer_received_zip_refs_internal_lineage_same_object", True),
        ("historical_basis_refs_used_as_current_actual_review_basis", True),
        ("historical_basis_refs_used_as_current_actual_review_evidence", True),
        ("historical_helper_green_claimed_as_actual_review_complete", True),
        ("synthetic_contract_rows_used_as_actual_review_rows", True),
        ("existing_ahr_helper_rewritten", True),
        ("existing_cs_helper_rewritten", True),
        ("current_basis_refrozen_here", False),
        ("current_received_basis_refrozen_for_actual_review_operation", False),
        ("current_basis_envelope_only", False),
        ("cr01_does_not_create_manifest_packet_review_rows_or_disposal", False),
        ("actual_human_review_run_here", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("p5_confirmed_final", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
    ],
)
def test_cr01_rejects_basis_historical_or_boundary_mutations(key: str, value: object) -> None:
    mutated = deepcopy(cr.build_p7_r54_ahr_cr01_current_received_basis_envelope())
    mutated[key] = value
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(mutated)


def test_cr01_rejects_missing_or_old_current_received_snapshot_ref() -> None:
    old_backend = deepcopy(cr.build_p7_r54_ahr_cr01_current_received_basis_envelope())
    old_backend["current_received_snapshot_refs"]["backend_zip_ref"] = "mashos-api(170).zip"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(old_backend)

    missing_backend = deepcopy(cr.build_p7_r54_ahr_cr01_current_received_basis_envelope())
    del missing_backend["current_received_snapshot_refs"]["backend_zip_ref"]
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(missing_backend)

    old_outer = deepcopy(cr.build_p7_r54_ahr_cr01_current_received_basis_envelope())
    old_outer["outer_received_zip_refs"]["backend_zip_ref"] = "mashos-api(170).zip"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(old_outer)


def test_cr_rejects_forbidden_body_question_path_or_hash_keys() -> None:
    mutated00 = deepcopy(cr.build_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze())
    mutated00["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr00_scope_no_touch_boundary_freeze_contract(mutated00)

    mutated01 = deepcopy(cr.build_p7_r54_ahr_cr01_current_received_basis_envelope())
    mutated01["local_absolute_path"] = "/tmp/forbidden"
    with pytest.raises(ValueError):
        cr.assert_p7_r54_ahr_cr01_current_received_basis_envelope_contract(mutated01)


def test_cr_aliases_preserve_contract() -> None:
    cr00 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_scope_no_touch_boundary_freeze_bodyfree()
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_scope_no_touch_boundary_freeze_bodyfree_contract(cr00)
        is True
    )

    cr01 = cr.build_p7_r54_ahr_current_received_actual_local_review_operation_current_received_basis_envelope_bodyfree(
        scope_no_touch_boundary_freeze=cr00
    )
    assert (
        cr.assert_p7_r54_ahr_current_received_actual_local_review_operation_current_received_basis_envelope_bodyfree_contract(cr01)
        is True
    )
