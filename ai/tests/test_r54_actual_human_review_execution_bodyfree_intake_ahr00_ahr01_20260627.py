# -*- coding: utf-8 -*-
"""R54-AHR-00/01 body-free intake contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as r54clr
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


def _assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in ahr.P7_R54_AHR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in (
        "raw_input",
        "returned_emlis_body",
        "history_surface",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "body_hash",
        "packet_content",
        "terminal_output_body",
    ):
        assert forbidden_key not in material


def test_r54_ahr00_freezes_scope_and_no_touch_boundary_for_actual_review_intake() -> None:
    material = ahr.build_p7_r54_ahr00_scope_no_touch_boundary_freeze()

    assert set(material) == set(ahr.P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR00_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR00_STEP_REF
    assert material["review_session_id"] == ahr.P7_R54_AHR_DEFAULT_REVIEW_SESSION_ID
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["scope_boundary_confirmed"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_touch_boundary_frozen"] is True
    assert material["ahr_line_selected"] is True
    assert material["r54_ahr_prefix_used"] is True

    assert material["current_execution_basis_refs"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["current_execution_basis_refs"]["premise_zip_ref"] == "Cocolon_前提資料(260).zip"
    assert material["current_execution_basis_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(83).zip"
    assert material["current_execution_basis_refs"]["rn_zip_ref"] == "Cocolon(256).zip"
    assert material["current_execution_basis_refs"]["backend_zip_ref"] == "mashos-api(169).zip"
    assert tuple(material["current_execution_basis_ref_keys"]) == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS
    assert tuple(material["required_current_execution_basis_ref_keys"]) == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS
    assert material["all_required_current_execution_basis_refs_present"] is True
    assert material["current_execution_basis_refs_are_current_received_snapshot_candidate"] is True
    assert material["current_execution_basis_refs_are_actual_execution_basis"] is False
    assert material["current_execution_basis_refs_used_as_actual_execution_basis"] is False
    assert material["current_execution_basis_refreeze_required_next"] is True

    assert tuple(material["historical_helper_ref_groups"]) == ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUPS
    assert "r54_clr_20260627" in material["historical_helper_ref_groups"]
    assert material["historical_helper_refs_must_be_separated"] is True
    assert material["historical_helper_refs_used_as_actual_execution_basis"] is False
    assert material["r54_clr_historical_refs_used_as_actual_execution_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_execution_basis"] is False

    assert material["p8_p6_release_api_db_rn_runtime_out_of_scope"] is True
    assert material["p8_question_design_not_started_here"] is True
    assert material["api_db_rn_runtime_no_touch_boundary_frozen"] is True
    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR01_STEP_REF
    assert "p8_question_design_or_implementation" in material["out_of_scope_refs"]
    assert "api_route_or_request_response_key_change" in material["out_of_scope_refs"]
    assert "actual_human_review_execution_or_completion_claim" in material["out_of_scope_refs"]
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract(material) is True


def test_r54_ahr01_refreezes_current_execution_basis_without_rewriting_historical_helpers() -> None:
    ahr00 = ahr.build_p7_r54_ahr00_scope_no_touch_boundary_freeze()
    material = ahr.build_p7_r54_ahr01_current_execution_basis_refreeze(scope_no_touch_boundary_freeze=ahr00)

    assert set(material) == set(ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_SCHEMA_VERSION
    assert material["policy_section"] == ahr.P7_R54_AHR01_STEP_REF
    assert material["operation_step_ref"] == ahr.P7_R54_AHR01_STEP_REF
    assert material["ahr00_schema_version"] == ahr.P7_R54_AHR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["ahr00_next_required_step"] == ahr.P7_R54_AHR01_STEP_REF
    assert material["current_execution_basis_refreeze_status_ref"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFREEZE_STATUS_REF
    assert material["current_execution_basis_refrozen"] is True
    assert material["current_execution_basis_source_mode"] == material["source_mode"]
    assert material["current_execution_basis_refs"] == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
    assert material["current_execution_basis_refs"]["premise_zip_ref"] == "Cocolon_前提資料(260).zip"
    assert material["current_execution_basis_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(83).zip"
    assert material["current_execution_basis_refs"]["rn_zip_ref"] == "Cocolon(256).zip"
    assert material["current_execution_basis_refs"]["backend_zip_ref"] == "mashos-api(169).zip"
    assert tuple(material["current_execution_basis_ref_keys"]) == ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REF_KEYS
    assert material["current_execution_basis_refs_match_received_snapshot_260_83_256_169"] is True
    assert material["current_execution_basis_refs_match_260_83_256_169_snapshot"] is True
    assert material["current_execution_basis_refs_are_actual_execution_basis"] is True
    assert material["current_execution_basis_refs_used_as_actual_execution_basis"] is True

    assert tuple(material["historical_helper_ref_groups"]) == ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUPS
    assert material["historical_helper_refs"] == ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS
    assert material["historical_helper_refs"]["r54_op_20260625"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["historical_helper_refs"]["r54_ev_20260626"] == r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r54_clr_20260627"] == r54clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r55_20260623"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r52_20260621"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs_are_historical_here"] is True
    assert material["historical_helper_refs_are_structural_refs_only"] is True
    assert material["historical_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_actual_execution_basis"] is False
    assert material["historical_helper_refs_used_as_actual_execution_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_execution_basis"] is False
    assert material["r54_clr_current_refs_are_historical_here"] is True
    assert material["r54_clr_refs_used_as_actual_execution_basis"] is False
    assert material["r54_clr_current_refs_match_current_execution_basis_260_83_256_169"] is False

    differing = material["historical_helper_differing_execution_basis_ref_keys"]
    assert set(differing) == set(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUPS)
    for group_ref, differing_keys in differing.items():
        assert "premise_zip_ref" in differing_keys, group_ref
        assert "backend_zip_ref" in differing_keys, group_ref
        assert differing_keys, group_ref
    assert material["differing_execution_basis_ref_group_count"] == len(ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUPS)
    assert material["current_execution_basis_refreeze_does_not_rewrite_historical_helpers"] is True
    assert material["existing_helper_constants_not_rewritten"] is True
    assert material["existing_helper_constants_rewritten"] is False
    assert material["existing_helper_refs_preserved_as_received"] is True
    assert material["new_thin_boundary_helper_only"] is True
    assert material["new_full_operation_helper_required_here"] is False

    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["actual_rating_or_question_rows_claim_blocked_here"] is True
    assert material["disposal_receipt_claim_blocked_here"] is True
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ahr.P7_R54_AHR02_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert ahr.assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_implementation_started_here", True),
        ("question_text_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_executed_by_person", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("actual_r52_reintake_execution_confirmed", True),
        ("disposal_verified", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("raw_body_included", True),
        ("question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("packet_content_included", True),
    ],
)
def test_r54_ahr00_rejects_touch_promotion_or_body_flags(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr00_scope_no_touch_boundary_freeze())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("current_execution_basis_refs_match_received_snapshot_260_83_256_169", False),
        ("current_execution_basis_refs_match_260_83_256_169_snapshot", False),
        ("current_execution_basis_refs_used_as_actual_execution_basis", False),
        ("historical_helper_refs_used_as_actual_execution_basis", True),
        ("old_helper_refs_allowed_as_actual_execution_basis", True),
        ("historical_helper_refs_can_be_used_for_actual_execution_basis", True),
        ("r54_clr_refs_used_as_actual_execution_basis", True),
        ("r54_clr_current_refs_match_current_execution_basis_260_83_256_169", True),
        ("current_execution_basis_refreeze_does_not_rewrite_historical_helpers", False),
        ("existing_helper_constants_not_rewritten", False),
        ("existing_helper_constants_rewritten", True),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("actual_rating_or_question_rows_claim_blocked_here", False),
        ("disposal_receipt_claim_blocked_here", False),
        ("r52_reintake_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("new_full_operation_helper_required_here", True),
        ("p5_final_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr01_rejects_basis_or_boundary_mutations(key: str, value: object) -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr01_current_execution_basis_refreeze())
    mutated[key] = value
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(mutated)


def test_r54_ahr01_rejects_r54_clr_snapshot_as_current_execution_basis() -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr01_current_execution_basis_refreeze())
    mutated["current_execution_basis_refs"] = dict(r54clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS)
    mutated["current_execution_basis_refs_match_received_snapshot_260_83_256_169"] = False
    mutated["current_execution_basis_refs_match_260_83_256_169_snapshot"] = False
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(mutated)


def test_r54_ahr01_rejects_historical_helper_refs_as_actual_execution_basis() -> None:
    mutated = deepcopy(ahr.build_p7_r54_ahr01_current_execution_basis_refreeze())
    mutated["historical_helper_refs_used_as_actual_execution_basis"] = True
    mutated["r54_clr_refs_used_as_actual_execution_basis"] = True
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(mutated)


def test_r54_ahr_rejects_forbidden_body_or_question_keys() -> None:
    mutated00 = deepcopy(ahr.build_p7_r54_ahr00_scope_no_touch_boundary_freeze())
    mutated00["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr00_scope_no_touch_boundary_freeze_contract(mutated00)

    mutated01 = deepcopy(ahr.build_p7_r54_ahr01_current_execution_basis_refreeze())
    mutated01["packet_content"] = "forbidden"
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr01_current_execution_basis_refreeze_contract(mutated01)


def test_r54_ahr01_aliases_preserve_contract() -> None:
    ahr00 = ahr.build_p7_r54_actual_human_review_execution_scope_no_touch_boundary_freeze_bodyfree()
    assert ahr.assert_p7_r54_actual_human_review_execution_scope_no_touch_boundary_freeze_bodyfree_contract(ahr00) is True

    ahr01 = ahr.build_p7_r54_actual_human_review_execution_current_execution_basis_refreeze_bodyfree(
        scope_no_touch_boundary_freeze=ahr00
    )
    assert ahr.assert_p7_r54_actual_human_review_execution_current_execution_basis_refreeze_bodyfree_contract(ahr01) is True
