# -*- coding: utf-8 -*-
"""R54-AHR Post-PCM DHR-OP05 manual handoff boundary DHB OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


_DHB_OP00_FALSE_ALLOWANCE_KEYS = (
    "pcm_op08_material_synthesis_allowed_here",
    "pcm_builder_call_allowed_here",
    "pcm_r11_memo_as_current_lane_allowed_here",
    "pcm_target_green_as_current_lane_allowed_here",
    "pcm_decision_table_as_single_lane_allowed_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "repair_execution_allowed_here",
    "raw_evidence_request_allowed_here",
    "p8_question_design_allowed_here",
    "p8_question_implementation_allowed_here",
    "question_text_materialization_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "p7_complete_allowed_here",
    "release_decision_allowed_here",
    "full_backend_suite_green_claim_allowed_here",
    "rn_contract_green_claim_allowed_here",
    "rn_real_device_modal_verification_claim_allowed_here",
    "github_connection_check_performed",
)

_DHB_OP01_FALSE_CLAIM_KEYS = (
    "pcm_op08_material_synthesis_allowed_here",
    "pcm_builder_call_allowed_here",
    "pcm_r11_memo_as_current_lane_allowed_here",
    "pcm_target_green_as_current_lane_allowed_here",
    "pcm_decision_table_as_single_lane_allowed_here",
    "pcm_op08_material_synthesized_here",
    "pcm_builder_called_here",
    "pcm_r11_memo_used_as_current_lane_here",
    "pcm_target_green_used_as_current_lane_here",
    "pcm_decision_table_used_as_single_lane_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "existing_dhr_op05_builder_called_here",
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


def _explicit_pcm_op08_material(**overrides: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "material_id": "explicit_pcm_op08_dhr_op05_lane_bodyfree_closure_material_for_dhb_op01_test",
        "review_session_id": "dhb_op01_test_session",
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


def test_dhb_op00_freezes_scope_and_stops_before_pcm_op08_intake() -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11_contract(op00) is True
    assert op00["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF
    assert op00["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF
    assert op00["dhb_op00_implemented"] is True
    assert tuple(op00["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP00_IMPLEMENTED_STEPS
    assert tuple(op00["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert op00["dhb_scope_refrozen"] is True
    assert op00["explicit_pcm_op08_closed_material_required"] is True
    assert op00["body_free"] is True


@pytest.mark.parametrize("key", _DHB_OP00_FALSE_ALLOWANCE_KEYS)
def test_dhb_op00_keeps_execution_p8_release_and_contract_allowances_false(key: str) -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()

    assert op00[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11_contract(op00) is True


def test_dhb_op00_assert_rejects_dhr_or_release_promotion_mutation() -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    mutated = deepcopy(op00)
    mutated["dhr_op05_call_allowed_here"] = True

    with pytest.raises(ValueError):
        dhb.assert_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11_contract(mutated)


def test_dhb_op01_waits_when_explicit_pcm_op08_material_is_missing() -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=None,
        op00_scope_refreeze=op00,
    )

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True
    assert op01["dhb_op01_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[1]
    assert op01["dhb_op01_waiting_for_explicit_pcm_op08_closed_material"] is True
    assert op01["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_CLOSED_MATERIAL_REF
    assert op01["pcm_op08_material_present"] is False
    assert op01["dhb_op00_implemented"] is True
    assert op01["dhb_op01_implemented"] is True


def test_dhb_op01_accepts_explicit_pcm_op08_shaped_material_only_for_contract_validation() -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(),
        op00_scope_refreeze=op00,
    )

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True
    assert op01["dhb_op01_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[0]
    assert op01["dhb_op01_ready_for_contract_validation"] is True
    assert op01["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF
    assert op01["pcm_op08_shaped_material_valid"] is True
    assert op01["selected_pnt_lane_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
    assert op01["dhb_op01_does_not_confirm_dhr_op05_lane"] is True
    assert op01["dhb_op01_does_not_materialize_dhr_op05_handoff_envelope"] is True


def test_dhb_op01_accepts_non_dhr_pcm_op08_material_without_lane_confirmation() -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    non_dhr_lane = dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS[0]
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(selected_pnt_lane_ref=non_dhr_lane),
        op00_scope_refreeze=op00,
    )

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True
    assert op01["dhb_op01_ready_for_contract_validation"] is True
    assert op01["selected_pnt_lane_ref"] == non_dhr_lane
    assert op01["dhb_op01_does_not_confirm_dhr_op05_lane"] is True


@pytest.mark.parametrize(
    "material",
    [
        {"decision_table": [{"lane": "dhr"}], "schema_version": "pcm_r11_result_memo_not_pcm_op08"},
        {"all_lane_summary": {"green": True}, "schema_version": "pcm_r11_result_memo_not_pcm_op08"},
        {"target_test_result_status_ref": "140_passed", "compileall_result_status_ref": "passed"},
    ],
)
def test_dhb_op01_rejects_decision_table_or_target_green_as_selected_material(material: dict[str, object]) -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=material,
        op00_scope_refreeze=op00,
    )

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True
    assert op01["dhb_op01_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[2]
    assert op01["dhb_op01_repair_required"] is True
    assert op01["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_MATERIAL_INTAKE_REF
    assert op01["pcm_r11_memo_used_as_current_lane_here"] is False
    assert op01["pcm_target_green_used_as_current_lane_here"] is False
    assert op01["pcm_decision_table_used_as_single_lane_here"] is False


@pytest.mark.parametrize(
    ("bad_key", "bad_value", "expected_path_fragment"),
    [
        ("raw_input", "raw body must not enter DHB", "raw_input"),
        ("question_text", "question text must not enter DHB", "question_text"),
        ("dhr_op05_called_here", True, "dhr_op05_called_here"),
        ("release_allowed", True, "release_allowed"),
        ("api_changed", True, "api_changed"),
    ],
)
def test_dhb_op01_blocks_body_like_payload_promotion_or_no_touch_mutation(
    bad_key: str,
    bad_value: object,
    expected_path_fragment: str,
) -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    material = _explicit_pcm_op08_material(**{bad_key: bad_value})
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=material,
        op00_scope_refreeze=op00,
    )

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True
    assert op01["dhb_op01_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[3]
    assert op01["dhb_op01_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert op01["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_MATERIAL_INTAKE_REF
    combined_paths = (
        tuple(op01["pcm_op08_input_forbidden_payload_key_path_refs"])
        + tuple(op01["pcm_op08_input_body_like_value_path_refs"])
        + tuple(op01["pcm_op08_input_promotion_claim_refs"])
        + tuple(op01["pcm_op08_input_no_touch_mutation_path_refs"])
    )
    assert any(expected_path_fragment in path for path in combined_paths)


@pytest.mark.parametrize("key", _DHB_OP01_FALSE_CLAIM_KEYS)
def test_dhb_op01_keeps_forbidden_claims_false_in_output(key: str) -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(),
        op00_scope_refreeze=op00,
    )

    assert op01[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True


def test_dhb_op01_assert_rejects_output_promotion_mutation() -> None:
    op00 = dhb.build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11()
    op01 = dhb.build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
        explicit_pcm_op08_closed_material=_explicit_pcm_op08_material(),
        op00_scope_refreeze=op00,
    )
    mutated = deepcopy(op01)
    mutated["release_allowed"] = True

    with pytest.raises(ValueError):
        dhb.assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(mutated)
