# -*- coding: utf-8 -*-
"""R54-AHR Post-PCM DHR-OP05 manual handoff boundary DHB OP02/OP03 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb


_DHB_OP02_FALSE_CLAIM_KEYS = (
    "dhr_op05_lane_confirmed_here",
    "dhr_op05_handoff_envelope_materialized_here",
    "selected_pcm_next_boundary_executed_here",
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

_DHB_OP03_FALSE_CLAIM_KEYS = (
    "dhr_op05_manual_handoff_envelope_materialized",
    "dhr_op05_handoff_envelope_ready",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "existing_dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "actual_review_started_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
)


def _explicit_pcm_op08_material(**overrides: object) -> dict[str, object]:
    material: dict[str, object] = {
        "schema_version": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "operation_step_ref": dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "material_id": "explicit_pcm_op08_dhr_op05_lane_bodyfree_closure_material_for_dhb_op02_op03_test",
        "review_session_id": "dhb_op02_op03_test_session",
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


def test_dhb_op02_validates_pcm_op08_required_field_set_without_confirming_dhr_lane() -> None:
    op02 = _op02()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_contract(op02) is True
    assert op02["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF
    assert op02["dhb_op02_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[0]
    assert op02["pcm_op08_contract_valid"] is True
    assert op02["pcm_op08_contract_missing_field_refs"] == []
    assert tuple(op02["pcm_op08_contract_required_field_refs"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_PCM_CONTRACT_REQUIRED_FIELD_REFS
    assert op02["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF
    assert op02["dhb_op02_does_not_confirm_dhr_op05_lane"] is True
    assert op02["dhr_op05_lane_confirmed_here"] is False
    assert op02["dhr_op05_handoff_envelope_materialized_here"] is False
    assert tuple(op02["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_IMPLEMENTED_STEPS
    assert tuple(op02["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_NOT_YET_IMPLEMENTED_STEPS


@pytest.mark.parametrize(
    "override",
    [
        {"selected_pnt_lane_ref": ""},
        {"selected_pnt_lane_ref": "unknown_pcm_op08_lane"},
        {"selected_pcm_next_boundary_not_executed": False},
        {"schema_version": "wrong_pcm_op08_schema"},
    ],
)
def test_dhb_op02_repairs_invalid_or_ambiguous_pcm_material(override: dict[str, object]) -> None:
    op02 = _op2_from_override = _op02(**override)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_contract(op02) is True
    assert _op2_from_override["dhb_op02_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[1]
    assert _op2_from_override["dhb_op02_repair_required"] is True
    assert _op2_from_override["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_CONTRACT_REF
    assert _op2_from_override["pcm_op08_contract_valid"] is False
    assert _op2_from_override["dhb_op02_does_not_confirm_dhr_op05_lane"] is True


@pytest.mark.parametrize(
    ("mutation_key", "expected_path_fragment"),
    [
        ("dhr_op05_called_here", "dhr_op05_called_here"),
        ("release_allowed", "release_allowed"),
        ("api_changed", "api_changed"),
    ],
)
def test_dhb_op02_blocks_dhr_call_release_or_no_touch_claim_from_input(
    mutation_key: str,
    expected_path_fragment: str,
) -> None:
    op01 = _op01()
    mutated = deepcopy(op01)
    mutated[mutation_key] = True
    op02 = dhb.build_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_contract(op02) is True
    assert op02["dhb_op02_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[2]
    assert op02["dhb_op02_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert op02["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_CONTRACT_REF
    combined_paths = (
        tuple(op02["op02_input_forbidden_payload_key_path_refs"])
        + tuple(op02["op02_input_body_like_value_path_refs"])
        + tuple(op02["op02_input_promotion_claim_refs"])
        + tuple(op02["op02_input_no_touch_mutation_path_refs"])
    )
    assert any(expected_path_fragment in path for path in combined_paths)


def test_dhb_op03_confirms_dhr_op05_lane_exactly_and_stops_before_handoff_envelope() -> None:
    op03 = _op03()

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(op03) is True
    assert op03["operation_step_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF
    assert op03["dhb_op03_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[0]
    assert op03["dhr_op05_lane_confirmed"] is True
    assert op03["dhr_op05_lane_selected"] is True
    assert op03["selected_pnt_lane_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
    assert op03["selected_pcm_next_work_class_ref_matches_dhr_op05_lane"] is True
    assert op03["selected_pcm_next_boundary_ref_matches_dhr_op05_lane"] is True
    assert op03["selected_pcm_next_boundary_kind_ref_matches_dhr_op05_lane"] is True
    assert op03["next_design_document_candidate_ref_matches_dhr_op05_lane"] is True
    assert op03["next_design_document_allowed_matches_dhr_op05_lane"] is True
    assert op03["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF
    assert op03["dhr_op05_manual_handoff_envelope_materialized"] is False
    assert op03["dhr_op05_handoff_envelope_ready"] is False
    assert op03["dhr_op05_call_allowed_here"] is False
    assert tuple(op03["implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_IMPLEMENTED_STEPS
    assert tuple(op03["not_yet_implemented_steps"]) == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_NOT_YET_IMPLEMENTED_STEPS


@pytest.mark.parametrize("lane_ref", dhb.P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS)
def test_dhb_op03_preserves_non_dhr_lanes_without_handoff_envelope(lane_ref: str) -> None:
    op03 = _op03(selected_pnt_lane_ref=lane_ref, next_design_document_allowed=False)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(op03) is True
    assert op03["dhb_op03_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[1]
    assert op03["dhr_op05_lane_confirmed"] is False
    assert op03["dhr_op05_lane_selected"] is False
    assert op03["non_dhr_lane_route_preserved"] is True
    assert op03["preserved_non_dhr_lane_ref"] == lane_ref
    assert op03["preserved_pcm_route_without_execution"] is True
    assert op03["dhr_op05_manual_handoff_envelope_materialized"] is False
    assert op03["dhr_op05_handoff_envelope_ready"] is False
    assert op03["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF


def test_dhb_op03_repairs_dhr_lane_when_expected_boundary_ref_is_inconsistent() -> None:
    op03 = _op03(selected_pcm_next_boundary_ref="unexpected_downstream_boundary_ref")

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(op03) is True
    assert op03["dhb_op03_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2]
    assert op03["dhb_op03_repair_required"] is True
    assert op03["dhr_op05_lane_selected"] is True
    assert op03["dhr_op05_lane_confirmed"] is False
    assert op03["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_LANE_CONFIRMATION_REF
    assert any("selected_pcm_next_boundary_ref" in blocker for blocker in op03["dhb_op03_blocker_refs"])


@pytest.mark.parametrize(
    ("mutation_key", "expected_path_fragment"),
    [
        ("dhr_op05_called_here", "dhr_op05_called_here"),
        ("release_allowed", "release_allowed"),
        ("api_changed", "api_changed"),
    ],
)
def test_dhb_op03_blocks_dhr_call_release_or_no_touch_claim_from_input(
    mutation_key: str,
    expected_path_fragment: str,
) -> None:
    op02 = _op02()
    mutated = deepcopy(op02)
    mutated[mutation_key] = True
    op03 = dhb.build_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation(mutated)

    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(op03) is True
    assert op03["dhb_op03_status_ref"] == dhb.P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[3]
    assert op03["dhb_op03_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert op03["next_required_step"] == dhb.P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_LANE_CONFIRMATION_REF
    combined_paths = (
        tuple(op03["op03_input_forbidden_payload_key_path_refs"])
        + tuple(op03["op03_input_body_like_value_path_refs"])
        + tuple(op03["op03_input_promotion_claim_refs"])
        + tuple(op03["op03_input_no_touch_mutation_path_refs"])
    )
    assert any(expected_path_fragment in path for path in combined_paths)


@pytest.mark.parametrize("key", _DHB_OP02_FALSE_CLAIM_KEYS)
def test_dhb_op02_keeps_forbidden_claims_false_in_output(key: str) -> None:
    op02 = _op02()

    assert op02[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_contract(op02) is True


@pytest.mark.parametrize("key", _DHB_OP03_FALSE_CLAIM_KEYS)
def test_dhb_op03_keeps_forbidden_claims_false_in_output(key: str) -> None:
    op03 = _op03()

    assert op03[key] is False, key
    assert dhb.assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(op03) is True


def test_dhb_op03_assert_rejects_output_promotion_mutation() -> None:
    op03 = _op03()
    mutated = deepcopy(op03)
    mutated["dhr_op05_call_allowed_here"] = True

    with pytest.raises(ValueError):
        dhb.assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(mutated)
