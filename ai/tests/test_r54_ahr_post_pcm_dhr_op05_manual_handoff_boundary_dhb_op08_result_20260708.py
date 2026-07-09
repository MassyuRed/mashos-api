# -*- coding: utf-8 -*-
"""R54-AHR Post-PCM DHR-OP05 manual handoff boundary DHB OP08 closure tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


_DHB_OP08_FALSE_EXECUTION_KEYS = (
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
    "dmd_r52_executed_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "api_db_rn_runtime_response_key_changed",
    "p7_complete",
    "release_allowed",
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
)

_DHB_OP08_TRUE_NON_EXECUTION_KEYS = (
    "dhr_op05_not_called",
    "dhr_op05_builder_not_called",
    "dhr_op06_not_called",
    "dmd_r52_not_executed",
    "actual_review_not_started",
    "actual_rows_not_created",
    "question_need_observation_rows_not_created",
    "p8_question_design_not_started",
    "question_text_not_materialized",
    "api_db_rn_runtime_response_key_not_changed",
    "release_decision_not_made",
    "op08_does_not_execute_validation_commands",
    "op08_does_not_claim_target_green",
    "op08_does_not_claim_selected_regression_green",
    "op08_does_not_claim_compileall_green",
    "op08_keeps_full_backend_suite_unconfirmed",
    "op08_keeps_rn_contract_unconfirmed",
    "op08_keeps_rn_real_device_unconfirmed",
    "op08_does_not_call_dhr_op05",
    "op08_does_not_call_existing_dhr_op05_builder",
    "op08_does_not_call_dhr_op06",
    "op08_does_not_execute_dmd_r52",
    "op08_does_not_start_actual_review",
    "op08_does_not_create_actual_rows",
    "op08_does_not_create_question_need_observation_rows",
    "op08_does_not_start_p8_question_design",
    "op08_does_not_materialize_question_text",
    "op08_does_not_change_api_db_rn_runtime_response_key",
    "op08_does_not_make_release_decision",
    "op08_does_not_create_json_schema_file",
)


def _explicit_pcm_op08_material(**overrides: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "material_id": "explicit_pcm_op08_bodyfree_closure_material_for_dhb_op08_test",
        "review_session_id": "dhb_op08_test_session",
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


def _chain(**material_overrides: object) -> tuple[dict[str, object], ...]:
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(**material_overrides),
        op00_scope_refreeze=_op00(),
    )
    op02 = dhb.build_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation(op01)
    op03 = dhb.build_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation(op02)
    op04 = dhb.build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(op03)
    op05 = dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(op04)
    op06 = dhb.build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)
    op07 = dhb.build_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material(op06)
    return op01, op02, op03, op04, op05, op06, op07


def _missing_chain() -> tuple[dict[str, object], ...]:
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=None,
        op00_scope_refreeze=_op00(),
    )
    op02 = dhb.build_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation(op01)
    op03 = dhb.build_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation(op02)
    op04 = dhb.build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(op03)
    op05 = dhb.build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(op04)
    op06 = dhb.build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(op05)
    op07 = dhb.build_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material(op06)
    return op01, op02, op03, op04, op05, op06, op07


def _op08_from_chain(chain: tuple[dict[str, object], ...]) -> dict[str, object]:
    *upstream, op07 = chain
    return dhb.build_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure(
        op07,
        upstream_dhb_materials=upstream,
    )


def _assert_common_op08_contract(op08: dict[str, object]) -> None:
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure_contract(op08) is True
    assert op08["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF
    assert op08["body_free"] is True
    assert op08["execution_allowance_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_EXECUTION_ALLOWANCE_REF
    assert tuple(op08["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_IMPLEMENTED_STEPS
    assert tuple(op08["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_NOT_YET_IMPLEMENTED_STEPS
    assert op08["target_validation_test_ref_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R6_TARGET_TEST_REF_REFS)
    assert op08["selected_regression_test_ref_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R6_SELECTED_REGRESSION_TEST_REF_REFS)
    assert op08["compileall_target_ref_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R6_COMPILEALL_TARGET_REF_REFS)
    assert op08["result_memo_expected_file_refs"] == list(dhb.P7_R54_AHR_POST_PCM_DHB_R6_RESULT_MEMO_EXPECTED_FILE_REFS)
    for key in _DHB_OP08_FALSE_EXECUTION_KEYS:
        assert op08[key] is False
    for key in _DHB_OP08_TRUE_NON_EXECUTION_KEYS:
        assert op08[key] is True


def test_dhb_op08_closes_dhr_lane_as_stopped_not_executed() -> None:
    op08 = _op08_from_chain(_chain())

    _assert_common_op08_contract(op08)
    assert op08["dhb_op08_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]
    assert op08["dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped"] is True
    assert op08["explicit_pcm_op08_dhr_lane_confirmed"] is True
    assert op08["dhr_op05_manual_handoff_envelope_materialized"] is True
    assert op08["dhr_op05_call_still_requires_separate_explicit_instruction"] is True
    assert op08["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_STOP_BEFORE_DHR_OP05_CALL_REF
    assert op08["next_work_candidate_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_NEXT_WORK_CANDIDATE_WHEN_DHR_CLOSED_REF


@pytest.mark.parametrize("lane_ref", dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS[:3])
def test_dhb_op08_closes_non_dhr_lanes_as_route_preserved_not_executed(lane_ref: str) -> None:
    op08 = _op08_from_chain(_chain(selected_pnt_lane_ref=lane_ref, next_design_document_allowed=False))

    _assert_common_op08_contract(op08)
    assert op08["dhb_op08_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[1]
    assert op08["dhb_op08_not_dhr_op05_lane_route_preserved_stopped"] is True
    assert op08["non_dhr_lane_route_preserved"] is True
    assert op08["explicit_pcm_op08_dhr_lane_confirmed"] is False
    assert op08["dhr_op05_manual_handoff_envelope_materialized"] is False
    assert op08["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF


def test_dhb_op08_waits_without_explicit_pcm_op08_material() -> None:
    op08 = _op08_from_chain(_missing_chain())

    _assert_common_op08_contract(op08)
    assert op08["dhb_op08_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[2]
    assert op08["dhb_op08_waiting_for_explicit_pcm_op08_dhr_lane"] is True
    assert op08["op08_waiting_status_ref_detected"] is True
    assert op08["explicit_pcm_op08_dhr_lane_confirmed"] is False
    assert op08["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_DHR_LANE_REF


def test_dhb_op08_repairs_invalid_pcm_or_dhb_bodyfree_handoff_inputs() -> None:
    op08 = _op08_from_chain(_chain(selected_pcm_next_boundary_not_executed=False))

    _assert_common_op08_contract(op08)
    assert op08["dhb_op08_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3]
    assert op08["dhb_op08_repair_required"] is True
    assert op08["op08_repair_status_ref_detected"] is True
    assert any("REPAIR" in ref for ref in op08["dhb_op08_blocker_refs"])
    assert op08["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS_REF


@pytest.mark.parametrize(
    "claim_key",
    [
        "question_text",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dmd_r52_executed_here",
        "p8_question_design_started",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
        "api_changed",
    ],
)
def test_dhb_op08_blocks_body_leak_promotion_green_or_autorun_claims(claim_key: str) -> None:
    chain = _chain()
    *upstream, op07 = chain
    mutated = deepcopy(op07)
    mutated[claim_key] = "body-like leak" if claim_key == "question_text" else True

    op08 = dhb.build_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure(
        mutated,
        upstream_dhb_materials=upstream,
    )

    _assert_common_op08_contract(op08)
    assert op08["dhb_op08_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[4]
    assert op08["dhb_op08_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert any(claim_key in ref for ref in op08["dhb_op08_blocker_refs"])
    assert op08["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF


def test_dhb_op08_repairs_when_op07_closure_input_is_missing() -> None:
    op08 = dhb.build_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure(None)

    _assert_common_op08_contract(op08)
    assert op08["dhb_op08_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3]
    assert op08["dhb_op08_repair_required"] is True
    assert "op07_material_present_false" in op08["dhb_op08_blocker_refs"]
    assert op08["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS_REF
