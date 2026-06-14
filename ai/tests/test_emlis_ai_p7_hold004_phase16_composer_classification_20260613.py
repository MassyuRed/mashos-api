# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

import emotion_submit_service as submit_service
import emlis_ai_reply_service as reply_service
from emlis_ai_complete_composer_client import CocolonCompleteComposerClient
from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_p7_hold004_phase16_composer_classification import (
    assert_p7_hold004_phase16_baseline_freeze_contract,
    assert_p7_hold004_phase16_composer_classification_contract,
    assert_p7_hold004_phase16_composer_observation_contract,
    build_p7_hold004_phase16_baseline_freeze,
    build_p7_hold004_phase16_composer_classification,
    build_p7_hold004_phase16_composer_observation,
)
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_types import GreetingDecision, SourceBundle
from fixtures.emlis_ai_two_stage_reception_cases import two_stage_reception_case_by_id


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
    return current_input, evidence, scope, material


def _daily_a_payload():
    _current_input, evidence, scope, material = _daily_a_materials()
    return build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="p7-hold004-r0-baseline-freeze",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )


def _phase16_frozen_boundary_meta() -> dict:
    # R0/R1 is historical baseline material.  Later R4-A repairs may change
    # live runtime status to generated, so these tests keep the body-free red
    # observation frozen as explicit classification input.
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


def _build_direct_observation() -> dict:
    return build_p7_hold004_phase16_composer_observation(
        path_id="complete_composer_direct_daily_unpleasant_A",
        test_ref=(
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
            "test_phase16_6_complete_composer_direct_output_reaches_labelled_two_stage_text"
        ),
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_frozen_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _build_conversation_observation() -> dict:
    return build_p7_hold004_phase16_composer_observation(
        path_id="conversation_composer_daily_unpleasant_A",
        test_ref=(
            "tests/test_emlis_ai_complete_composer_two_stage_surface_connection.py::"
            "test_phase16_6_conversation_composer_path_reaches_labelled_two_stage_text"
        ),
        fixture_family=DAILY_A_CASE_ID,
        composer_meta=_phase16_frozen_boundary_meta(),
        observed_status="unavailable",
        expected_status_kind="generated_candidate_before_display_gate",
    )


def _patch_submit_persistence(monkeypatch, current_input: dict) -> None:
    def fake_normalize_submission_payload(**_kwargs):
        return {
            "emotions_tags": list(current_input.get("emotions") or ["怒り"]),
            "emotion_details": list(current_input.get("emotion_details") or []),
            "emotion_strength_avg": 2.0,
            "category": list(current_input.get("category") or []),
            "has_memo_input": bool(str(current_input.get("memo") or "").strip() or str(current_input.get("memo_action") or "").strip()),
        }

    async def fake_insert_emotion_row(**_kwargs):
        return {
            "id": str(current_input.get("id") or "phase16-emotion-log-1"),
            "created_at": str(current_input.get("created_at") or "2026-05-28T00:00:00.000000+00:00"),
        }

    async def fake_subscription_tier_for_user(*_args, **_kwargs):
        return "free"

    monkeypatch.setattr(submit_service, "normalize_submission_payload", fake_normalize_submission_payload)
    monkeypatch.setattr(submit_service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(submit_service, "invalidate_prefix", lambda _prefix: None)
    monkeypatch.setattr(submit_service, "_global_summary_activity_date_from_created_at", lambda _created_at: "2026-05-28")
    monkeypatch.setattr(submit_service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(submit_service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)


def _patch_reply_rendering(monkeypatch) -> None:
    async def fake_source_bundle(**kwargs):
        return SourceBundle(
            user_id=kwargs["user_id"],
            display_name="Mash",
            current_input=dict(kwargs["current_input"]),
            greeting=GreetingDecision(
                slot_name="phase16-hold004-test",
                slot_key="phase16-hold004-test",
                greeting_text="Emlisです。",
                first_in_slot=False,
            ),
            side_state={},
            input_effort={},
            memory_richness={},
            debug={"tier": "free"},
        )

    async def actual_render_with_complete_client(**kwargs):
        return await reply_service.render_emlis_ai_reply(
            **kwargs,
            composer_client=CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True),
        )

    monkeypatch.setattr(reply_service, "build_emlis_ai_source_bundle", fake_source_bundle)
    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", actual_render_with_complete_client)


async def _build_public_daily_observation(monkeypatch) -> dict:
    current_input = dict(two_stage_reception_case_by_id(DAILY_A_CASE_ID)["current_input"])
    _patch_submit_persistence(monkeypatch, current_input)
    _patch_reply_rendering(monkeypatch)

    result = await submit_service.persist_emotion_submission(
        user_id="p7-hold004-phase16-public-user",
        emotions=current_input["emotions"],
        memo=current_input["memo"],
        memo_action=current_input["memo_action"],
        category=current_input["category"],
    )

    feedback = str(result.get("input_feedback_comment") or "")
    meta = dict(result.get("input_feedback_meta") or {})
    assert meta.get("observation_status") == "passed"
    assert feedback.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in feedback
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


def test_r0_phase16_baseline_freeze_records_direct_red_body_free() -> None:
    observation = _build_direct_observation()

    assert_p7_hold004_phase16_composer_observation_contract(observation)
    assert observation["observed_status"] == "unavailable"
    assert observation["two_stage_surface_summary"]["applied"] is True
    assert observation["two_stage_surface_summary"]["labels_present"] is True
    assert observation["surface_quality_summary"]["surface_structural_ready"] is True
    assert observation["surface_quality_summary"]["surface_display_quality_blocked"] is True
    assert "tone_guard:ending_family_repetition" in observation["validation_error_codes"]

    freeze = build_p7_hold004_phase16_baseline_freeze(observations=[observation])
    assert_p7_hold004_phase16_baseline_freeze_contract(freeze)
    assert freeze["status"] == "RED_REPRODUCED"
    assert freeze["full_backend_suite_green_confirmed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p8_start_allowed"] is False


@pytest.mark.asyncio
async def test_r1_phase16_classification_material_separates_paths_without_closing_hold(monkeypatch) -> None:
    direct_observation = _build_direct_observation()
    conversation_observation = _build_conversation_observation()
    public_observation = await _build_public_daily_observation(monkeypatch)

    classification = build_p7_hold004_phase16_composer_classification(
        observations=[direct_observation, conversation_observation, public_observation]
    )

    assert_p7_hold004_phase16_composer_classification_contract(classification)
    assert classification["status"] == "CLASSIFIED_UNRESOLVED"
    assert classification["classification"] == "candidate_readiness_display_gate_boundary_mixed"
    assert "complete_surface_realizer_tone_boundary" in classification["owner_layers"]
    assert "complete_composer_candidate_boundary" in classification["owner_layers"]
    assert classification["public_daily_path_labelled"] is True
    assert classification["direct_or_conversation_unavailable"] is True
    assert classification["full_backend_suite_green_confirmed"] is False
    assert classification["hold004_close_allowed"] is False
    assert classification["release_allowed"] is False
    assert classification["p8_start_allowed"] is False
    assert {row["path_id"]: row["observed_status"] for row in classification["path_statuses"]} == {
        "complete_composer_direct_daily_unpleasant_A": "unavailable",
        "conversation_composer_daily_unpleasant_A": "unavailable",
        "emotion_submit_public_daily_unpleasant_A": "public_feedback_labelled",
    }
