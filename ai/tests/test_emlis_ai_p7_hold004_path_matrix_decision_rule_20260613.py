# -*- coding: utf-8 -*-
from __future__ import annotations

import copy

import pytest

from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION,
    assert_p7_hold004_phase16_decision_rule_contract,
    assert_p7_hold004_phase16_path_matrix_contract,
    build_p7_hold004_phase16_adjacent_public_fixture_row,
    build_p7_hold004_phase16_decision_rule,
    build_p7_hold004_phase16_path_matrix,
)
from emlis_ai_p7_hold004_phase16_composer_classification import (
    build_p7_hold004_phase16_composer_observation,
)


DAILY_A_CASE_ID = "daily_unpleasant_encounter_A"


def _phase16_boundary_meta() -> dict:
    return {
        "primary_reason": "complete_initial_surface_unavailable",
        "phase17_7_unavailable_reason_codes": [
            "phase17_surface_mode_policy_missing",
            "phase17_product_visible_fixture_not_reached",
        ],
        "phase17_7_self_repair_handoff_reason_codes": [
            "phase17_surface_mode_policy_missing",
            "template_like",
        ],
        "surface_realizer": {
            "status": "ready",
            "ready": False,
            "validation_errors": ["tone_guard:ending_family_repetition"],
            "two_stage_surface_realization": {
                "required": True,
                "applied": True,
                "labels_present": True,
                "section_order_valid": True,
                "observation_section_non_empty": True,
                "reception_section_non_empty": True,
                "section_line_counts": {"observation": 1, "reception": 2},
                "validation_errors": [],
                "daily_unpleasant_surface_quality_applied": True,
                "two_stage_mode_specific_surface_applied": True,
            },
        },
    }


def _direct_observation() -> dict:
    return build_p7_hold004_phase16_composer_observation(
        path_id="complete_composer_direct_daily_unpleasant_A",
        test_ref=(
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
            "test_phase16_6_complete_composer_direct_output_reaches_labelled_two_stage_text"
        ),
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _conversation_observation() -> dict:
    return build_p7_hold004_phase16_composer_observation(
        path_id="conversation_composer_daily_unpleasant_A",
        test_ref=(
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
            "test_phase16_6_conversation_composer_path_reaches_labelled_two_stage_text"
        ),
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _public_daily_observation() -> dict:
    return build_p7_hold004_phase16_composer_observation(
        path_id="emotion_submit_public_daily_unpleasant_A",
        test_ref=(
            "tests/test_emotion_submit_two_stage_reception_e2e.py::"
            "test_phase16_8_emotion_submit_path_returns_public_two_stage_input_feedback"
        ),
        fixture_family=DAILY_A_CASE_ID,
        observed_status="public_feedback_labelled",
        expected_status_kind="public_labelled_two_stage_input_feedback",
        public_reached=True,
        labelled_two_stage_reached=True,
        candidate_generated_before_display_gate=False,
    )


def _matrix() -> dict:
    return build_p7_hold004_phase16_path_matrix(
        observations=[_direct_observation(), _conversation_observation(), _public_daily_observation()],
        extra_rows=[build_p7_hold004_phase16_adjacent_public_fixture_row()],
        include_default_adjacent_public_red=False,
    )


def test_r2_path_matrix_separates_direct_conversation_public_and_adjacent_red_body_free() -> None:
    matrix = _matrix()

    assert matrix["schema_version"] == P7_HOLD004_PHASE16_PATH_MATRIX_SCHEMA_VERSION
    assert_p7_hold004_phase16_path_matrix_contract(matrix)
    assert matrix["path_statuses"]["complete_composer_direct_daily_unpleasant_A"] == "unavailable"
    assert matrix["path_statuses"]["conversation_composer_daily_unpleasant_A"] == "unavailable"
    assert matrix["path_statuses"]["emotion_submit_public_daily_unpleasant_A"] == "public_feedback_labelled"
    assert matrix["path_statuses"]["emotion_submit_public_product_visible_fixture_suite"] == "public_feedback_unlabelled"
    assert matrix["direct_and_conversation_are_separate"] is True
    assert matrix["public_daily_pass_not_merged_with_direct_red"] is True
    assert matrix["adjacent_public_red_not_merged_with_daily_A"] is True
    assert matrix["direct_or_conversation_unavailable"] is True
    assert matrix["public_daily_path_labelled"] is True
    assert matrix["adjacent_public_red_registered"] is True
    assert matrix["full_backend_suite_green_confirmed"] is False
    assert matrix["full_backend_suite_green_claim_allowed"] is False
    assert matrix["hold004_close_allowed"] is False
    assert matrix["p8_start_allowed"] is False
    assert matrix["release_allowed"] is False
    assert "positive_public_fixture_shape_boundary" in matrix["required_followup_fixes"]


def test_r3_decision_rule_routes_current_phase16_red_to_r4a_without_closing_hold() -> None:
    decision = build_p7_hold004_phase16_decision_rule(path_matrix=_matrix())

    assert decision["schema_version"] == P7_HOLD004_PHASE16_DECISION_RULE_SCHEMA_VERSION
    assert_p7_hold004_phase16_decision_rule_contract(decision)
    assert decision["decision_rule_fixed"] is True
    assert decision["status"] == "IMPLEMENTATION_REPAIR_REQUIRED"
    assert decision["classification"] == "candidate_readiness_display_gate_boundary_mixed"
    assert decision["decision_kind"] == "repair_candidate_display_boundary"
    assert decision["repair_branch"] == "R4-A"
    assert decision["next_branch"] == "R4-A"
    assert decision["implementation_rule_matched"] is True
    assert decision["stale_contract_rule_matched"] is False
    assert decision["structural_failure_rule_matched"] is False
    assert decision["implementation_rule_evaluations"] == {
        "two_stage_surface_applied": True,
        "labels_present": True,
        "section_validation_clear": True,
        "candidate_shape_material_available": True,
        "display_quality_reason_present": True,
        "candidate_display_separation_required": True,
    }
    assert decision["safety_boundaries"]["generated_not_public_display_permission"] is True
    assert decision["safety_boundaries"]["unavailable_not_safe_success"] is True
    assert decision["safety_boundaries"]["display_gate_relaxed"] is False
    assert decision["safety_boundaries"]["grounding_gate_relaxed"] is False
    assert decision["full_backend_suite_green_confirmed"] is False
    assert decision["hold004_close_allowed"] is False
    assert decision["p8_start_allowed"] is False
    assert decision["release_allowed"] is False
    assert "phase16_complete_composer_candidate_boundary" in decision["required_followup_fixes"]


def test_r3_stale_contract_branch_requires_explicit_evidence_and_no_candidate_display_rule() -> None:
    default_decision = build_p7_hold004_phase16_decision_rule(path_matrix=_matrix())
    stale_decision = build_p7_hold004_phase16_decision_rule(
        path_matrix=_matrix(),
        stale_direct_contract_evidence_confirmed=True,
        candidate_display_separation_required=False,
    )

    assert default_decision["repair_branch"] == "R4-A"
    assert stale_decision["status"] == "STALE_CONTRACT_REPLACEMENT_REQUIRED"
    assert stale_decision["classification"] == "public_recovery_expected_direct_contract_stale"
    assert stale_decision["decision_kind"] == "replace_stale_direct_contract"
    assert stale_decision["repair_branch"] == "R4-B"
    assert stale_decision["stale_contract_rule_matched"] is True
    assert stale_decision["implementation_rule_matched"] is False
    assert stale_decision["release_allowed"] is False
    assert stale_decision["p8_start_allowed"] is False
    assert_p7_hold004_phase16_decision_rule_contract(stale_decision)


def test_r2_r3_contracts_reject_release_full_suite_green_and_body_payload() -> None:
    matrix = _matrix()
    decision = build_p7_hold004_phase16_decision_rule(path_matrix=matrix)

    matrix_release = copy.deepcopy(matrix)
    matrix_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_phase16_path_matrix_contract(matrix_release)

    matrix_full_suite = copy.deepcopy(matrix)
    matrix_full_suite["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_phase16_path_matrix_contract(matrix_full_suite)

    decision_release = copy.deepcopy(decision)
    decision_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_phase16_decision_rule_contract(decision_release)

    decision_payload = copy.deepcopy(decision)
    decision_payload["comment_text"] = "forbidden body payload"
    with pytest.raises(ValueError):
        assert_p7_hold004_phase16_decision_rule_contract(decision_payload)
