# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_complete_composer_client import CocolonCompleteComposerClient
from emlis_ai_p7_hold004_path_matrix import (
    P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION,
    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract,
    build_p7_hold004_phase16_adjacent_public_fixture_row,
    build_p7_hold004_phase16_decision_rule,
    build_p7_hold004_phase16_path_matrix,
    build_p7_hold004_phase16_r4b_stale_contract_replacement_design,
)
from emlis_ai_p7_hold004_phase16_composer_classification import (
    build_p7_hold004_phase16_composer_observation,
)
from test_emlis_ai_complete_composer_two_stage_surface_connection import _daily_a_payload


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


def _observation(path_id: str, *, public: bool = False) -> dict:
    if public:
        return build_p7_hold004_phase16_composer_observation(
            path_id=path_id,
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
    return build_p7_hold004_phase16_composer_observation(
        path_id=path_id,
        test_ref="tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py",
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _matrix() -> dict:
    return build_p7_hold004_phase16_path_matrix(
        observations=[
            _observation("complete_composer_direct_daily_unpleasant_A"),
            _observation("conversation_composer_daily_unpleasant_A"),
            _observation("emotion_submit_public_daily_unpleasant_A", public=True),
        ],
        extra_rows=[build_p7_hold004_phase16_adjacent_public_fixture_row()],
        include_default_adjacent_public_red=False,
    )


def test_r4a_complete_composer_generates_candidate_but_keeps_display_gate_closed_for_tone_blocker() -> None:
    result = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True).generate(_daily_a_payload())

    assert result["status"] == "generated"
    assert result["composer_source"] == "ai_generated"
    assert result["comment_text"].startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in result["comment_text"]

    meta = result["composer_meta"]
    boundary = meta["complete_surface_candidate_readiness"]
    assert boundary["candidate_generation_allowed_before_display_gate"] is True
    assert boundary["surface_structural_ready_before_display_gate"] is True
    assert boundary["surface_display_quality_blocked_before_display_gate"] is True
    assert boundary["display_quality_reason_codes"] == ["tone_guard:ending_family_repetition"]
    assert boundary["comment_text_body_included"] is False
    assert boundary["raw_input_included"] is False

    assert meta["candidate_generated_before_display_gate"] is True
    assert meta["candidate_status_before_display_gate"] == "generated"
    assert meta["candidate_status_after_internal_gate"] == "rejected"
    assert meta["surface_structural_ready_before_display_gate"] is True
    assert meta["surface_display_quality_blocked_before_display_gate"] is True
    assert meta["complete_initial_internal_tone_guard_failed_before_display_gate"] is True
    assert meta["public_comment_text_assigned"] is False
    assert meta["comment_text_publicly_assigned"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["grounding_gate_relaxed"] is False
    assert meta["fixed_string_renderer_used"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["two_stage_surface_realization"]["applied"] is True
    assert meta["two_stage_surface_realization"]["comment_text_body_included"] is False
    assert "comment_text" not in meta["complete_composer_candidate"]


def test_r4b_replacement_design_is_body_free_and_not_applied_when_r4a_is_current_branch() -> None:
    decision = build_p7_hold004_phase16_decision_rule(path_matrix=_matrix())
    design = build_p7_hold004_phase16_r4b_stale_contract_replacement_design(decision_rule=decision)

    assert design["schema_version"] == P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION
    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design)
    assert design["status"] == "DESIGNED_NOT_APPLIED"
    assert design["r4a_selected_by_decision_rule"] is True
    assert design["r4b_selected_by_decision_rule"] is False
    assert design["stale_contract_evidence_confirmed"] is False
    assert design["legacy_direct_generated_expectation_replacement_allowed"] is False
    assert design["target_test_replacement_required"] is False
    assert design["target_test_rewrite_applied"] is False
    assert design["replacement_contract_shape"]["direct_generated_expectation_replaced"] is False
    assert design["replacement_contract_shape"]["unavailable_not_safe_success"] is True
    assert design["replacement_contract_shape"]["public_daily_labelled_two_stage_path_required"] is True
    assert design["prohibited_changes"]["display_gate_relaxed"] is False
    assert design["prohibited_changes"]["public_response_key_added"] is False
    assert design["hold004_close_allowed"] is False
    assert design["p8_start_allowed"] is False
    assert design["release_allowed"] is False
    assert design["body_free"] is True


def test_r4b_replacement_design_becomes_ready_only_for_explicit_stale_contract_branch() -> None:
    stale_decision = build_p7_hold004_phase16_decision_rule(
        path_matrix=_matrix(),
        candidate_display_separation_required=False,
        stale_direct_contract_evidence_confirmed=True,
    )
    design = build_p7_hold004_phase16_r4b_stale_contract_replacement_design(decision_rule=stale_decision)

    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design)
    assert stale_decision["repair_branch"] == "R4-B"
    assert design["status"] == "REPLACEMENT_READY_PENDING_IMPLEMENTATION"
    assert design["r4b_selected_by_decision_rule"] is True
    assert design["stale_contract_evidence_confirmed"] is True
    assert design["legacy_direct_generated_expectation_replacement_allowed"] is True
    assert design["target_test_replacement_required"] is True
    assert design["target_test_rewrite_applied"] is False
    assert design["replacement_contract_shape"]["direct_generated_expectation_replaced"] is True
    assert design["replacement_contract_shape"]["direct_path_unavailable_reason_body_free_required"] is True
    assert design["replacement_contract_shape"]["generated_not_public_display_permission"] is True
    assert design["replacement_contract_shape"]["unavailable_not_safe_success"] is True
    assert design["release_allowed"] is False
