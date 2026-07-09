# -*- coding: utf-8 -*-
"""R54-AHR Post-PCM DHR-OP05 manual handoff boundary DHB OP06/OP07 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


_DHB_OP06_FALSE_CLAIM_KEYS = (
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "raw_evidence_request_allowed_here",
    "repair_execution_allowed_here",
    "p8_question_design_allowed_here",
    "p8_question_implementation_allowed_here",
    "question_text_materialization_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "p7_complete_allowed_here",
    "release_decision_allowed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)

_DHB_OP07_FALSE_GREEN_KEYS = (
    "validation_commands_executed_here",
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
)


def _explicit_pcm_op08_material(**overrides: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "material_id": "explicit_pcm_op08_dhr_op05_lane_bodyfree_closure_material_for_dhb_op06_op07_test",
        "review_session_id": "dhb_op06_op07_test_session",
        "body_free": True,
        "pcm_op08_status_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "bodyfree_post_pnt_closed_material_confirmation_closure_status_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "pcm_op08_closed_stopped": True,
        "selected_pnt_lane_ref": dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF,
        "selected_pcm_next_work_class_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_WORK_CLASS_REF,
        "selected_pcm_next_boundary_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_REF,
        "selected_pcm_next_boundary_kind_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF,
        "selected_pcm_next_boundary_not_executed": True,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "next_design_document_candidate_ref": dhb.P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF,
        "next_design_document_allowed": True,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "pnt_op08_builder_not_called": True,
        "pnt_op08_material_not_synthesized": True,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "actual_review_not_started": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "api_db_rn_runtime_response_key_not_changed": True,
    }
    material.update(overrides)
    return material


def _op00() -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()


def _op01(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(**material_overrides),
        op00_scope_refreeze=_op00(),
    )


def _op02(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation(_op01(**material_overrides))


def _op03(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation(_op02(**material_overrides))


def _op04(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(_op03(**material_overrides))


def _op05(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(_op04(**material_overrides))


def _op06(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(_op05(**material_overrides))


def _op07(**material_overrides: object) -> dict[str, object]:
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material(_op06(**material_overrides))


def test_dhb_op06_passes_clean_bodyfree_materials_without_touch_or_promotion() -> None:
    op06 = _op06()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    assert op06["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF
    assert op06["dhb_op06_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[0]
    assert op06["dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed"] is True
    assert op06["dhb_op06_repair_required"] is False
    assert op06["dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked"] is False
    assert op06["op05_contract_valid"] is True
    assert op06["op05_crosswalk_recorded"] is True
    assert op06["op06_input_forbidden_payload_key_path_refs"] == []
    assert op06["op06_input_body_like_value_path_refs"] == []
    assert op06["op06_input_promotion_claim_refs"] == []
    assert op06["op06_input_no_touch_mutation_path_refs"] == []
    assert op06["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF
    assert tuple(op06["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_IMPLEMENTED_STEPS
    assert tuple(op06["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_NOT_YET_IMPLEMENTED_STEPS
    for key in _DHB_OP06_FALSE_CLAIM_KEYS:
        assert op06[key] is False
    assert op06["op06_does_not_claim_validation_green"] is True


@pytest.mark.parametrize(
    "payload_key",
    ["raw_input", "comment_text", "question_text", "stdout", "hash"],
)
def test_dhb_op06_blocks_body_like_or_terminal_payload_keys(payload_key: str) -> None:
    op05 = _op05()
    mutated = deepcopy(op05)
    mutated[payload_key] = "must not enter DHB body-free guard"

    op06 = dhb.build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    assert op06["dhb_op06_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[2]
    assert op06["dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked"] is True
    assert any(payload_key in ref for ref in op06["dhb_op06_blocker_refs"])
    assert op06["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_GUARD_REF


@pytest.mark.parametrize(
    "promotion_key",
    [
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dmd_execution_started_here",
        "p8_question_design_started",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "api_changed",
    ],
)
def test_dhb_op06_blocks_execution_release_green_or_no_touch_promotion_claims(promotion_key: str) -> None:
    op05 = _op05()
    mutated = deepcopy(op05)
    mutated[promotion_key] = True

    op06 = dhb.build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    assert op06["dhb_op06_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[2]
    assert op06["dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked"] is True
    assert any(promotion_key in ref for ref in op06["dhb_op06_blocker_refs"])
    assert op06["dhr_op05_called_here"] is False
    assert op06["dhr_op06_called_here"] is False
    assert op06["release_allowed"] is False


def test_dhb_op06_repairs_missing_op05_material_without_calling_downstream() -> None:
    op06 = dhb.build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(None)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    assert op06["dhb_op06_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[1]
    assert op06["dhb_op06_repair_required"] is True
    assert "op05_material_present_false" in op06["dhb_op06_blocker_refs"]
    assert op06["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_GUARD_INPUTS_REF
    assert op06["dhr_op05_call_allowed_here"] is False


def test_dhb_op07_records_validation_plan_without_claiming_green() -> None:
    op07 = _op07()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    assert op07["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF
    assert op07["dhb_op07_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[0]
    assert op07["dhb_op07_validation_plan_result_memo_draft_materialized_stopped"] is True
    assert op07["target_validation_test_ref_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R5_TARGET_TEST_REF_REFS)
    assert op07["selected_regression_test_ref_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R5_SELECTED_REGRESSION_TEST_REF_REFS)
    assert op07["compileall_target_ref_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R5_COMPILEALL_TARGET_REF_REFS)
    assert op07["result_memo_expected_file_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R5_RESULT_MEMO_EXPECTED_FILE_REFS)
    assert op07["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF
    for key in _DHB_OP07_FALSE_GREEN_KEYS:
        assert op07[key] is False
    assert op07["op07_does_not_execute_validation_commands"] is True
    assert op07["op07_does_not_claim_target_green"] is True
    assert op07["op07_does_not_claim_selected_regression_green"] is True
    assert op07["op07_does_not_claim_compileall_green"] is True
    assert tuple(op07["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_IMPLEMENTED_STEPS
    assert tuple(op07["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_NOT_YET_IMPLEMENTED_STEPS


def test_dhb_op07_keeps_full_backend_rn_and_real_device_unconfirmed() -> None:
    op07 = _op07()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    assert op07["full_backend_suite_green_confirmed"] is False
    assert op07["rn_contract_green_confirmed"] is False
    assert op07["rn_real_device_modal_verified_claimed_here"] is False
    assert op07["op07_keeps_full_backend_suite_unconfirmed"] is True
    assert op07["op07_keeps_rn_contract_unconfirmed"] is True
    assert op07["op07_keeps_rn_real_device_unconfirmed"] is True
    assert op07["dhr_op05_not_called"] is True
    assert op07["dhr_op05_builder_not_called"] is True
    assert op07["dhr_op06_not_called"] is True
    assert op07["actual_review_not_started"] is True
    assert op07["release_decision_not_made"] is True


@pytest.mark.parametrize(
    "claim_key",
    [
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ],
)
def test_dhb_op07_blocks_validation_or_device_green_promotion_claims(claim_key: str) -> None:
    op06 = _op06()
    mutated = deepcopy(op06)
    mutated[claim_key] = True

    op07 = dhb.build_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    assert op07["dhb_op07_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[3]
    assert op07["dhb_op07_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert any(claim_key in ref for ref in op07["dhb_op07_blocker_refs"])
    assert op07["target_validation_green_confirmed_here"] is False
    assert op07["full_backend_suite_green_confirmed"] is False
    assert op07["rn_contract_green_confirmed"] is False


@pytest.mark.parametrize("lane_ref", dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS[:2])
def test_dhb_op07_preserves_clean_non_dhr_bodyfree_route_as_wait_or_stop(lane_ref: str) -> None:
    op07 = _op07(selected_pnt_lane_ref=lane_ref, next_design_document_allowed=False)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    assert op07["op06_guard_passed"] is True
    assert op07["op06_op05_crosswalk_recorded"] is False
    assert op07["dhb_op07_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[1]
    assert op07["dhb_op07_wait_or_stop_result_memo_draft_materialized_stopped"] is True
    assert op07["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_OR_STOP_AFTER_RESULT_MEMO_DRAFT_REF
    assert op07["dhr_op05_not_called"] is True
    assert op07["release_decision_not_made"] is True
