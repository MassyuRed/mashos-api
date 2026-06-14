# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from fixtures.emlis_ai_two_stage_reception_cases import two_stage_reception_case_by_id
from emlis_ai_complete_composer_client import (
    CocolonCompleteComposerClient,
    classify_complete_surface_readiness_for_candidate_path,
)
from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_p7_hold004_path_matrix import (
    build_p7_hold004_phase16_adjacent_public_fixture_row,
    build_p7_hold004_phase16_decision_rule,
    build_p7_hold004_phase16_path_matrix,
)
from emlis_ai_p7_hold004_phase16_composer_classification import (
    build_p7_hold004_phase16_composer_observation,
)
from emlis_ai_p7_hold004_r4_contract_material import (
    P7_HOLD004_PHASE16_R4A_REPAIR_SCHEMA_VERSION,
    P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION,
    assert_p7_hold004_phase16_r4a_runtime_repair_summary_contract,
    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract,
    build_p7_hold004_phase16_r4a_runtime_repair_summary,
    build_p7_hold004_phase16_r4b_stale_contract_replacement_design,
)
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers


DAILY_A_CASE_ID = "daily_unpleasant_encounter_A"


def _daily_a_materials():
    case = two_stage_reception_case_by_id(DAILY_A_CASE_ID)
    current_input = dict(case["current_input"])
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    material = build_observation_structure_material(current_input=current_input, evidence_ledger=evidence)
    return evidence, scope, material


def _daily_a_payload():
    evidence, scope, material = _daily_a_materials()
    return build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="p7-hold004-r4a-candidate-boundary",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )


def _conversation_candidate():
    evidence, scope, material = _daily_a_materials()
    return compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True),
        trace_id="p7-hold004-r4a-conversation-boundary",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )


def _assert_labelled_two_stage(comment_text: str) -> None:
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert comment_text.count("見えたこと：") == 1
    assert comment_text.count("Emlisから：") == 1


def _frozen_phase16_boundary_meta() -> dict:
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
                "comment_text_body_included": False,
                "raw_input_included": False,
            },
        },
    }


def _observation(path_id: str, test_name: str) -> dict:
    return build_p7_hold004_phase16_composer_observation(
        path_id=path_id,
        test_ref=f"tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::{test_name}",
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_frozen_phase16_boundary_meta(),
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
        observations=[
            _observation(
                "complete_composer_direct_daily_unpleasant_A",
                "test_phase16_6_complete_composer_direct_output_reaches_labelled_two_stage_text",
            ),
            _observation(
                "conversation_composer_daily_unpleasant_A",
                "test_phase16_6_conversation_composer_path_reaches_labelled_two_stage_text",
            ),
            _public_daily_observation(),
        ],
        extra_rows=[build_p7_hold004_phase16_adjacent_public_fixture_row()],
        include_default_adjacent_public_red=False,
    )


def test_r4a_direct_and_conversation_paths_generate_candidate_without_public_gate_relaxation() -> None:
    direct_result = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True).generate(_daily_a_payload())
    conversation_candidate = _conversation_candidate()

    assert direct_result["status"] == "generated"
    assert conversation_candidate.status == "generated"
    _assert_labelled_two_stage(str(direct_result["comment_text"]))
    _assert_labelled_two_stage(conversation_candidate.comment_text)

    direct_meta = direct_result["composer_meta"]
    conversation_meta = conversation_candidate.composer_meta
    assert direct_meta["candidate_generated_before_display_gate"] is True
    assert conversation_meta["candidate_generated_before_display_gate"] is True
    assert direct_meta["complete_initial_candidate_generation_display_gate_separated"] is True
    assert conversation_meta["complete_initial_candidate_generation_display_gate_separated"] is True
    assert direct_meta["surface_structural_ready_before_display_gate"] is True
    assert conversation_meta["surface_structural_ready_before_display_gate"] is True
    assert direct_meta["surface_display_quality_blocked_before_display_gate"] is True
    assert conversation_meta["surface_display_quality_blocked_before_display_gate"] is True
    assert "tone_guard:ending_family_repetition" in direct_meta["surface_display_quality_reason_codes_before_display_gate"]
    assert direct_meta["candidate_status_after_internal_gate"] == "rejected"
    assert conversation_meta["candidate_status_after_internal_gate"] == "rejected"
    assert direct_meta["public_comment_text_assigned"] is False
    assert direct_meta["comment_text_publicly_assigned"] is False
    assert direct_meta["display_gate_relaxed"] is False
    assert direct_meta["grounding_gate_relaxed"] is False
    assert direct_meta["fixed_string_renderer_used"] is False
    assert direct_meta["external_ai_used"] is False
    assert direct_meta["local_llm_used"] is False
    assert direct_meta["complete_composer_candidate"]["comment_text_in_meta"] is False
    assert "comment_text" not in direct_meta["complete_composer_candidate"]


def test_r4a_runtime_repair_summary_is_body_free_release_closed_and_not_hold_closure() -> None:
    direct_result = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True).generate(_daily_a_payload())
    conversation_candidate = _conversation_candidate()

    summary = build_p7_hold004_phase16_r4a_runtime_repair_summary(
        direct_result=direct_result,
        conversation_result=conversation_candidate,
        public_daily_path_labelled=True,
        adjacent_public_red_registered=True,
    )

    assert summary["schema_version"] == P7_HOLD004_PHASE16_R4A_REPAIR_SCHEMA_VERSION
    assert_p7_hold004_phase16_r4a_runtime_repair_summary_contract(summary)
    assert summary["status"] == "REPAIRED_PENDING_REGRESSION"
    assert summary["repair_branch"] == "R4-A"
    assert summary["target_paths_repaired"] is True
    assert summary["candidate_generated_before_display_gate"] is True
    assert summary["surface_structural_ready_before_display_gate"] is True
    assert summary["surface_display_quality_blocked_before_display_gate"] is True
    assert "tone_guard:ending_family_repetition" in summary["surface_display_quality_reason_codes_before_display_gate"]
    assert summary["generated_not_public_display_permission"] is True
    assert summary["public_comment_text_assigned"] is False
    assert summary["r4b_replacement_applied"] is False
    assert summary["full_backend_suite_green_confirmed"] is False
    assert summary["hold004_close_allowed"] is False
    assert summary["release_allowed"] is False
    assert summary["p8_start_allowed"] is False


def test_r4b_stale_contract_replacement_design_is_available_only_for_stale_r3_decision() -> None:
    implementation_decision = build_p7_hold004_phase16_decision_rule(path_matrix=_matrix())
    with pytest.raises(ValueError):
        build_p7_hold004_phase16_r4b_stale_contract_replacement_design(decision_rule=implementation_decision)

    stale_decision = build_p7_hold004_phase16_decision_rule(
        path_matrix=_matrix(),
        stale_direct_contract_evidence_confirmed=True,
        candidate_display_separation_required=False,
    )
    design = build_p7_hold004_phase16_r4b_stale_contract_replacement_design(decision_rule=stale_decision)

    assert design["schema_version"] == P7_HOLD004_PHASE16_R4B_REPLACEMENT_DESIGN_SCHEMA_VERSION
    assert_p7_hold004_phase16_r4b_stale_contract_replacement_design_contract(design)
    assert design["status"] == "STALE_CONTRACT_REPLACEMENT_DESIGNED"
    assert design["repair_branch"] == "R4-B"
    assert design["replacement_kind"] == "replace_stale_direct_generated_expectation"
    assert design["old_direct_expected_status_kind"] == "generated_candidate_before_display_gate"
    assert design["new_direct_expected_status_kind"] == "unavailable_with_body_free_reason_and_public_recovery_required"
    assert design["public_daily_path_contract_required"] is True
    assert design["direct_unavailable_reason_summary_required"] is True
    assert design["two_stage_surface_summary_required"] is True
    assert design["tone_or_display_blocker_summary_required"] is True
    assert design["unavailable_not_safe_success"] is True
    assert design["generated_not_public_display_permission"] is True
    assert design["replacement_applied_to_test_file"] is False
    assert design["release_allowed"] is False
    assert design["p8_start_allowed"] is False


def test_r4a_surface_readiness_classifier_does_not_treat_tone_blocker_as_structural_failure() -> None:
    meta = _frozen_phase16_boundary_meta()["surface_realizer"]
    readiness = classify_complete_surface_readiness_for_candidate_path(meta)

    assert readiness["surface_structural_ready"] is True
    assert readiness["surface_display_quality_blocked"] is True
    assert readiness["candidate_generation_allowed_before_display_gate"] is True
    assert readiness["display_ready_before_public_gate"] is False
    assert readiness["structural_error_codes"] == []
    assert "tone_guard:ending_family_repetition" in readiness["display_quality_reason_codes"]
    assert readiness["display_gate_relaxed"] is False
    assert readiness["grounding_gate_relaxed"] is False
