# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR00-CLR01 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr


NO_TOUCH_FALSE_FLAG_REFS = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "response_shape_changed",
    "db_schema_changed",
    "db_migration_added",
    "db_physical_schema_changed",
    "rn_ui_changed",
    "rn_visible_contract_changed",
    "public_response_key_changed",
    "public_response_top_level_key_added",
    "runtime_gate_threshold_changed",
    "user_label_connection_runtime_changed",
    "emlis_visible_output_generation_changed",
    "subscription_or_plan_access_policy_changed",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_answer_persistence_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "body_full_packet_generation_started_here",
    "body_full_packet_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "real_device_modal_verified",
)

BODY_FREE_FALSE_FLAG_REFS = (
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
)


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
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
)


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in NO_TOUCH_FALSE_FLAG_REFS + BODY_FREE_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_clr_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def test_r54_clr00_freezes_scope_and_no_touch_boundary() -> None:
    material = clr.build_p7_r54_clr00_scope_no_touch_boundary_freeze()

    assert set(material) == set(clr.P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR00_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR00_STEP_REF
    assert material["review_session_id"] == clr.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["scope_boundary_confirmed"] is True
    assert material["no_touch_boundary_confirmed"] is True
    assert material["no_touch_boundary_frozen"] is True

    assert material["operation_current_refs"] == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert tuple(material["operation_current_ref_keys"]) == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert tuple(material["required_current_snapshot_ref_keys"]) == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert material["operation_current_ref_count"] == len(clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert material["required_current_snapshot_ref_key_count"] == len(clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS)
    assert material["actual_review_basis_ref"] == clr.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF
    assert material["actual_review_basis_allowed"] == clr.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF
    assert material["operation_current_refs_are_current_snapshot_candidate"] is True
    assert material["operation_current_refs_are_actual_review_basis"] is False
    assert material["operation_current_refs_used_as_actual_review_basis"] is False
    assert material["current_snapshot_basis_refreeze_required_next"] is True

    assert material["existing_r54_op00_contract_available"] is True
    assert material["existing_r54_ev00_contract_available"] is True
    assert tuple(material["historical_helper_ref_groups"]) == clr.P7_R54_CLR_HISTORICAL_HELPER_REF_GROUPS
    assert material["historical_helper_refs_must_be_separated"] is True
    assert material["historical_helper_refs_used_as_actual_review_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_review_basis"] is False
    assert material["existing_helper_refs_can_be_used_for_actual_review_basis"] is False
    assert material["existing_helper_refs_can_be_used_for_helper_regression_only"] is True

    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_blocked_until_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR01_STEP_REF
    assert "p8_question_design_or_implementation" in material["out_of_scope_refs"]
    assert "api_route_or_response_key_change" in material["out_of_scope_refs"]
    assert "actual_human_review_execution" in material["out_of_scope_refs"]
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(material) is True


def test_r54_clr01_refreezes_current_snapshot_basis_without_rewriting_historical_helpers() -> None:
    clr00 = clr.build_p7_r54_clr00_scope_no_touch_boundary_freeze()
    material = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze(scope_no_touch_boundary_freeze=clr00)

    assert set(material) == set(clr.P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR01_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR01_STEP_REF
    assert material["clr00_schema_version"] == clr.P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert material["clr00_next_required_step"] == clr.P7_R54_CLR01_STEP_REF
    assert material["clr00_scope_boundary_confirmed"] is True
    assert material["clr00_no_touch_boundary_confirmed"] is True

    assert material["current_snapshot_basis_refreeze_status_ref"] == clr.P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_STATUS_REF
    assert material["current_snapshot_source_mode"] == material["source_mode"]
    assert material["operation_current_refs"] == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert tuple(material["operation_current_ref_keys"]) == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert tuple(material["required_current_snapshot_ref_keys"]) == clr.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    assert material["all_required_current_refs_present"] is True
    assert material["operation_current_refs_match_current_snapshot_20260627"] is True
    assert material["operation_current_refs_match_20260627_snapshot"] is True
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["operation_current_refs_used_as_actual_review_basis"] is True

    assert tuple(material["historical_helper_ref_groups"]) == clr.P7_R54_CLR_HISTORICAL_HELPER_REF_GROUPS
    assert material["historical_helper_refs"] == clr.P7_R54_CLR_HISTORICAL_HELPER_REFS
    assert material["historical_helper_refs"]["r54_op_20260625"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["historical_helper_refs"]["r54_ev_20260626"] == r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs"]["r55_20260623"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["historical_helper_refs_separated"] is True
    assert material["historical_helper_refs_are_historical_here"] is True
    assert material["historical_helper_refs_used_as_actual_review_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_review_basis"] is False
    assert material["old_helper_refs_match_current_snapshot_20260627"] is False
    assert material["existing_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_actual_review_basis"] is False

    assert material["r54_op_current_refs_are_historical_here"] is True
    assert material["r54_ev_current_refs_are_historical_here"] is True
    assert material["r55_current_refs_are_historical_here"] is True
    assert material["r54_op_refs_used_as_actual_review_basis"] is False
    assert material["r54_ev_refs_used_as_actual_review_basis"] is False
    assert material["r55_refs_used_as_actual_review_basis"] is False
    assert material["r54_op_current_refs_match_current_snapshot_20260627"] is False
    assert material["r54_ev_current_refs_match_current_snapshot_20260627"] is False
    assert material["r55_current_refs_match_current_snapshot_20260627"] is False
    differing = material["differing_operation_current_ref_keys_by_historical_group"]
    assert set(differing) == set(clr.P7_R54_CLR_HISTORICAL_HELPER_REF_GROUPS)
    for group_ref, differing_keys in differing.items():
        assert "premise_zip_ref" in differing_keys, group_ref
        assert "backend_zip_ref" in differing_keys, group_ref
        assert differing_keys, group_ref
    assert material["differing_operation_current_ref_group_count"] == len(clr.P7_R54_CLR_HISTORICAL_HELPER_REF_GROUPS)
    assert material["current_refs_refreeze_does_not_rewrite_historical_helpers"] is True
    assert material["existing_helper_constants_not_rewritten"] is True
    assert material["current_refs_override_uses_thin_20260627_boundary_layer"] is True

    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_blocked_until_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["p5_finalization_blocked_here"] is True
    assert material["new_full_operation_helper_required"] is False
    assert material["new_full_operation_helper_required_here"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR02_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(material) is True


@pytest.mark.parametrize(
    "key,value",
    [
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("public_response_key_changed", True),
        ("question_implementation_started_here", True),
        ("question_text_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("raw_body_included", True),
        ("returned_emlis_body_included", True),
        ("history_surface_included", True),
        ("question_text_included", True),
        ("local_path_included", True),
        ("body_hash_included", True),
        ("packet_content_included", True),
        ("terminal_output_body_included", True),
    ],
)
def test_r54_clr00_rejects_touch_promotion_or_body_flags(key: str, value: object) -> None:
    material = clr.build_p7_r54_clr00_scope_no_touch_boundary_freeze()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(mutated)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_match_current_snapshot_20260627", False),
        ("operation_current_refs_match_20260627_snapshot", False),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("historical_helper_refs_used_as_actual_review_basis", True),
        ("old_helper_refs_allowed_as_actual_review_basis", True),
        ("historical_helper_refs_can_be_used_for_actual_review_basis", True),
        ("old_helper_refs_match_current_snapshot_20260627", True),
        ("r54_op_refs_used_as_actual_review_basis", True),
        ("r54_ev_refs_used_as_actual_review_basis", True),
        ("r55_refs_used_as_actual_review_basis", True),
        ("r54_op_current_refs_match_current_snapshot_20260627", True),
        ("r54_ev_current_refs_match_current_snapshot_20260627", True),
        ("r55_current_refs_match_current_snapshot_20260627", True),
        ("current_refs_refreeze_does_not_rewrite_historical_helpers", False),
        ("existing_helper_constants_not_rewritten", False),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("new_full_operation_helper_required", True),
        ("new_full_operation_helper_required_here", True),
        ("release_allowed", True),
    ],
)
def test_r54_clr01_rejects_basis_or_boundary_mutations(key: str, value: object) -> None:
    material = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze()
    mutated = deepcopy(material)
    mutated[key] = value
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(mutated)


def test_r54_clr01_rejects_old_snapshot_as_current_basis() -> None:
    material = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze()
    mutated = deepcopy(material)
    mutated["operation_current_refs"] = dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS)
    mutated["operation_current_refs_match_current_snapshot_20260627"] = False
    mutated["operation_current_refs_match_20260627_snapshot"] = False
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(mutated)


def test_r54_clr01_rejects_historical_helper_refs_as_actual_review_basis() -> None:
    material = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze()
    mutated = deepcopy(material)
    mutated["historical_helper_refs_used_as_actual_review_basis"] = True
    mutated["r54_op_refs_used_as_actual_review_basis"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(mutated)


def test_r54_clr_rejects_forbidden_body_or_question_keys() -> None:
    clr00 = clr.build_p7_r54_clr00_scope_no_touch_boundary_freeze()
    mutated00 = deepcopy(clr00)
    mutated00["question_text"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(mutated00)

    clr01 = clr.build_p7_r54_clr01_current_snapshot_basis_refreeze()
    mutated01 = deepcopy(clr01)
    mutated01["packet_content"] = "forbidden"
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(mutated01)


def test_r54_clr01_aliases_preserve_contract() -> None:
    clr00 = clr.build_p7_r54_current_snapshot_scope_no_touch_boundary_freeze_bodyfree()
    assert clr.assert_p7_r54_current_snapshot_scope_no_touch_boundary_freeze_bodyfree_contract(clr00) is True
    assert clr.build_p7_r54_current_snapshot_local_run_clr00_scope_no_touch_boundary_freeze() == clr00
    assert clr.assert_p7_r54_current_snapshot_local_run_clr00_scope_no_touch_boundary_freeze_contract(clr00) is True

    clr01 = clr.build_p7_r54_current_snapshot_basis_refreeze_bodyfree(scope_no_touch_boundary_freeze=clr00)
    assert clr.assert_p7_r54_current_snapshot_basis_refreeze_bodyfree_contract(clr01) is True
    assert clr.assert_p7_r54_current_snapshot_local_run_clr01_current_snapshot_basis_refreeze_contract(clr01) is True
