# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"existing_helper_refs_can_be_used_for_actual_review_basis": true',
    '"helper_op01_override_build_accepted": true',
    '"current_refs_override_possible_with_existing_helper_only": true',
    '"existing_helper_only_sufficient_for_20260626_actual_review_basis": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_ev00() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev00_scope_no_touch_boundary_confirmation()
    assert ev.assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material) is True
    return (material,)


def _ev00() -> dict[str, object]:
    return deepcopy(_cached_ev00()[0])


@lru_cache(maxsize=1)
def _cached_ev01() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev01_existing_helper_capability_inspection(
        scope_no_touch_boundary_confirmation=_ev00(),
    )
    assert ev.assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material) is True
    return (material,)


def _ev01() -> dict[str, object]:
    return deepcopy(_cached_ev01()[0])


def test_r54_ev00_freezes_20260626_scope_no_touch_boundary_without_starting_review_p8_or_release() -> None:
    material = _ev00()

    assert material["schema_version"] == ev.P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["step"] == ev.P7_R54_EV_STEP
    assert material["scope"] == ev.P7_R54_EV_SCOPE
    assert material["policy_section"] == ev.P7_R54_EV00_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV00_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs"]["premise_zip_ref"] == "Cocolon_前提資料(256).zip"
    assert material["operation_current_refs"]["implemented_materials_zip_ref"] == "EmlisAIの実装済み資料(81).zip"
    assert material["operation_current_refs"]["rn_zip_ref"] == "Cocolon(254).zip"
    assert material["operation_current_refs"]["backend_zip_ref"] == "mashos-api(167).zip"
    assert material["actual_review_basis_ref"] == ev.P7_R54_EV_ACTUAL_REVIEW_BASIS_REF
    assert material["actual_review_basis_allowed"] == ev.P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF
    assert material["operation_current_refs_are_actual_review_basis"] is True

    assert material["allowed_operation_step_refs"] == [ev.P7_R54_EV00_STEP_REF, ev.P7_R54_EV01_STEP_REF]
    assert "p8_question_design" in material["out_of_scope_refs"]
    assert "api_route_change" in material["out_of_scope_refs"]
    assert "db_schema_or_migration_change" in material["out_of_scope_refs"]
    assert "rn_ui_or_visible_contract_change" in material["out_of_scope_refs"]
    assert "body_full_packet_generation" in material["out_of_scope_refs"]
    assert material["existing_op00_contract_available"] is True
    assert material["existing_helper_refs_can_be_used_for_actual_review_basis"] is False
    assert material["body_full_generation_blocked_until_later_preflight"] is True
    assert material["body_full_generation_requested_here"] is False
    assert material["actual_human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["no_touch_boundary_frozen"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV01_STEP_REF

    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False

    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("existing_helper_refs_can_be_used_for_actual_review_basis", True),
        ("body_full_generation_blocked_until_later_preflight", False),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("no_touch_boundary_frozen", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_implementation_started_here", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev00_rejects_no_touch_actual_review_p8_release_or_body_boundary_mutation(key: str, value: object) -> None:
    material = _ev00()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material)


def test_r54_ev00_rejects_old_helper_or_unknown_current_refs_as_actual_review_basis() -> None:
    material = _ev00()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material)

    material = _ev00()
    material["operation_current_refs"] = dict(ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS)
    material["operation_current_refs"]["backend_zip_ref"] = "mashos-api(999).zip"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material)


def test_r54_ev01_inspects_existing_helper_and_routes_to_thin_20260626_boundary_layer() -> None:
    material = _ev01()

    assert material["schema_version"] == ev.P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_REQUIRED_FIELD_REFS)
    assert material["phase"].startswith("P7_")
    assert material["step"] == ev.P7_R54_EV_STEP
    assert material["scope"] == ev.P7_R54_EV_SCOPE
    assert material["policy_section"] == ev.P7_R54_EV01_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV01_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["ev00_schema_version"] == ev.P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION
    assert material["ev00_next_required_step"] == ev.P7_R54_EV01_STEP_REF
    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["actual_review_basis_ref"] == ev.P7_R54_EV_ACTUAL_REVIEW_BASIS_REF
    assert material["operation_current_refs_are_actual_review_basis"] is True

    assert material["existing_helper_module_ref"] == r54op.__name__
    assert material["existing_helper_schema_step_ref"] == r54op.P7_R54_OPERATION_REENTRY_STEP
    assert material["existing_helper_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_helper_current_refs"]["premise_zip_ref"] == "Cocolon_前提資料(254).zip"
    assert material["existing_helper_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_helper_current_refs_match_20260626_snapshot"] is False
    assert material["existing_helper_current_refs_are_historical_here"] is True
    assert material["existing_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["existing_helper_refs_can_be_used_for_actual_review_basis"] is False

    assert tuple(material["required_helper_function_refs"]) == ev.P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS
    assert material["required_helper_function_count"] == len(ev.P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS)
    assert tuple(material["found_helper_function_refs"]) == ev.P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS
    assert material["found_helper_function_count"] == len(ev.P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS)
    assert material["missing_helper_function_refs"] == []
    assert material["missing_helper_function_count"] == 0
    assert material["required_helper_functions_all_present"] is True
    assert material["helper_function_capability_row_count"] == len(ev.P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS)
    assert material["selection_row_intake_helper_count"] == len(ev.P7_R54_EV_SELECTION_ROW_INTAKE_HELPER_REFS)
    assert material["selection_row_intake_helpers_present"] is True

    op01_row = next(
        row
        for row in material["helper_function_capability_rows"]
        if row["helper_function_ref"] == "build_p7_r54_op01_operation_current_snapshot_refs_refreeze"
    )
    assert op01_row["present"] is True
    assert op01_row["accepts_operation_current_refs"] is True
    op11_row = next(
        row
        for row in material["helper_function_capability_rows"]
        if row["helper_function_ref"] == "build_p7_r54_op11_sanitized_review_result_capture"
    )
    assert op11_row["present"] is True
    assert op11_row["accepts_reviewer_selection_rows"] is True

    assert material["helper_op01_accepts_operation_current_refs_parameter"] is True
    assert material["helper_op01_override_build_attempted_bodyfree"] is True
    assert material["helper_op01_override_build_accepted"] is False
    assert material["helper_op01_override_rejected"] is True
    assert material["helper_op01_override_rejection_ref"] == ev.P7_R54_EV01_CURRENT_REF_OVERRIDE_REJECTION_REF
    assert material["current_refs_override_possible_with_existing_helper_only"] is False
    assert material["bodyfree_handoff_possible_with_existing_helper_functions"] is True
    assert material["actual_selection_rows_intake_possible_with_existing_helper_functions"] is True
    assert material["existing_helper_only_sufficient_for_20260626_actual_review_basis"] is False
    assert material["thin_20260626_boundary_layer_required_next"] is True
    assert material["new_full_operation_helper_required"] is False
    assert material["helper_capability_status_ref"] == ev.P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF
    assert material["helper_reuse_verdict_ref"] == ev.P7_R54_EV01_HELPER_REUSE_VERDICT_THIN_LAYER_REQUIRED_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV01_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV01_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV02_NEXT_REQUIRED_STEP_REF

    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False

    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("existing_helper_current_refs_match_20260626_snapshot", True),
        ("existing_helper_current_refs_are_historical_here", False),
        ("existing_helper_refs_can_be_used_for_actual_review_basis", True),
        ("required_helper_functions_all_present", False),
        ("selection_row_intake_helpers_present", False),
        ("helper_op01_accepts_operation_current_refs_parameter", False),
        ("helper_op01_override_build_attempted_bodyfree", False),
        ("helper_op01_override_build_accepted", True),
        ("helper_op01_override_rejected", False),
        ("current_refs_override_possible_with_existing_helper_only", True),
        ("bodyfree_handoff_possible_with_existing_helper_functions", False),
        ("actual_selection_rows_intake_possible_with_existing_helper_functions", False),
        ("existing_helper_only_sufficient_for_20260626_actual_review_basis", True),
        ("thin_20260626_boundary_layer_required_next", False),
        ("new_full_operation_helper_required", True),
        ("body_full_generation_blocked_until_later_preflight", False),
        ("body_full_generation_requested_here", True),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("disposal_verified", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev01_rejects_helper_basis_no_touch_actual_review_p8_release_or_body_boundary_mutation(key: str, value: object) -> None:
    material = _ev01()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material)


def test_r54_ev01_rejects_missing_required_helper_or_helper_refs_as_actual_review_basis() -> None:
    material = _ev01()
    material["missing_helper_function_refs"] = ["build_p7_r54_op23_r52_reintake_handoff"]
    material["missing_helper_function_count"] = 1
    material["required_helper_functions_all_present"] = False
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material)

    material = _ev01()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material)

    material = _ev01()
    material["existing_helper_current_refs"] = dict(ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material)
