from __future__ import annotations

import json

from fixtures.emlis_ai_two_stage_reception_cases import (
    current_input_for_two_stage_reception_case,
    two_stage_reception_case_by_id,
)
from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_state_answer_composer_contract import (
    EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID,
    build_state_answer_composer_role_plan,
    state_answer_composer_payload_fragment,
)


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _current_input():
    return {
        "id": "phase7-state-answer-composer",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": SAMPLE_MEMO,
        "memo_action": "家で過ごしながら生活の不便さを考えていた",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _payload_with_state_answer_material():
    current_input = _current_input()
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    material = build_observation_structure_material(
        current_input=current_input,
        evidence_ledger=evidence,
    )
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="phase7-state-answer-composer",
        observation_structure_material=material,
    )
    return payload, evidence, scope, material


def test_phase7_composer_payload_contains_state_answer_role_plan_without_public_contract_change():
    payload, _evidence, _scope, _material = _payload_with_state_answer_material()

    assert payload["state_answer_surface_contract"]["material_id"] == "emlis_state_answer_surface_contract"
    assert payload["state_answer_composer_role_plan_connected"] is True
    role_plan = payload["state_answer_composer_role_plan"]
    assert role_plan["material_id"] == EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID
    assert role_plan["state_answer_surface_contract_connected"] is True
    assert role_plan["section_boundary_required"] is True
    assert role_plan["section_role_order"] == ["state_answer_observation", "human_follow"]
    assert role_plan["sections"][0]["source_layer"] == "observation_layer"
    assert role_plan["sections"][1]["source_layer"] == "human_follow_layer"
    assert role_plan["completed_reply_generated"] is False
    assert role_plan["fixed_sentence_template_used"] is False
    assert role_plan["runtime_renderer_marker_used"] is False

    contract = payload["composition_contract"]
    assert contract["state_answer_surface_contract_connected"] is True
    assert contract["state_answer_section_boundary_required"] is True
    assert contract["state_answer_input_feedback_comment_text_contract_unchanged"] is True
    assert contract["state_answer_passed_only_display_condition_unchanged"] is True
    assert contract["state_answer_dictionary_must_not_generate_completed_sentence"] is True
    assert contract["state_answer_material_is_not_fixed_template"] is True
    assert "state_answer" not in payload["expected_response_schema"]["required"]


def test_phase7_role_plan_is_material_only_and_does_not_copy_raw_input_text():
    payload, _evidence, _scope, _material = _payload_with_state_answer_material()
    fragment = state_answer_composer_payload_fragment(payload)
    role_plan = build_state_answer_composer_role_plan(fragment["state_answer_surface_contract"])
    encoded = json.dumps(role_plan, ensure_ascii=False, sort_keys=True)

    assert role_plan["material_is_completed_reply_template"] is False
    assert role_plan["comment_text_generated"] is False
    assert role_plan["raw_input_included"] is False
    assert role_plan["raw_text_included"] is False
    assert role_plan["public_payload_changed"] is False
    assert "ずっと家にいて" not in encoded
    assert "家で過ごしながら" not in encoded
    assert "comment_text body" not in encoded


def test_phase7_limited_composer_keeps_section_boundary_in_sentence_plan_meta():
    payload, evidence, _scope, _material = _payload_with_state_answer_material()
    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert result["fixed_string_renderer_used"] is False
    assert set(result["used_evidence_span_ids"]).issubset({span.span_id for span in evidence})
    meta = result["composer_meta"]
    assert meta["state_answer_surface_contract_connected"] is True
    assert meta["state_answer_composer_role_plan_connected"] is True
    assert meta["state_answer_section_boundary_required"] is True
    assert meta["state_answer_section_role_order"] == ["state_answer_observation", "human_follow"]
    assert meta["state_answer_completed_reply_generated_from_contract"] is False
    assert meta["state_answer_fixed_sentence_template_used"] is False
    assert meta["state_answer_runtime_renderer_marker_used"] is False
    assert meta["state_answer_public_response_key_added"] is False

    plan_meta = meta["profile_sentence_plan"]
    assert plan_meta["state_answer_section_boundary_on_sentence_plan"] is True
    assert plan_meta["state_answer_observation_section_present"] is True
    assert plan_meta["state_answer_human_follow_section_present"] is True
    assert plan_meta["state_answer_planned_section_roles"] == ["state_answer_observation", "human_follow"]


def _payload_for_current_input(current_input: dict):
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    material = build_observation_structure_material(
        current_input=current_input,
        evidence_ledger=evidence,
    )
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="phase8-two-stage-composer",
        observation_structure_material=material,
    )
    return payload, evidence, scope, material


class _TwoStageCommentTextComposer:
    def generate(self, payload):
        assert payload["composition_contract"]["two_stage_reception_surface_required"] is True
        assert payload["composition_contract"]["section_labels_required"] is True
        assert payload["composition_contract"]["expected_comment_text_shape"] == "labelled_two_stage_text"
        assert payload["expected_response_schema"]["required"] == [
            "comment_text",
            "used_evidence_span_ids",
            "confidence",
        ]
        assert "observation_text" not in payload["expected_response_schema"]["required"]
        assert "reception_text" not in payload["expected_response_schema"]["required"]
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": "phase8-test-composer",
            "generation_method": "test_ai_boundary",
            "generation_scope": "two_stage_comment_text",
            "coverage_scope": "current_input_only",
            "fixed_string_renderer_used": False,
            "comment_text": (
                "見えたこと：\n"
                "不快で怖さもある出来事に出くわして、怒りが残っているように見えます。\n\n"
                "Emlisから：\n"
                "うわ、それは嫌でしたね。\n"
                "怖さも怒りも残るのは自然です。"
            ),
            "used_evidence_span_ids": [payload["evidence_spans"][0]["span_id"]],
            "confidence": 0.83,
            "composer_meta": {},
        }


def test_phase8_composer_payload_contains_two_stage_role_plan_and_contract_without_response_key_change():
    payload, _evidence, _scope, _material = _payload_with_state_answer_material()

    role_plan = payload["state_answer_composer_role_plan"]
    assert role_plan["two_stage_display_required"] is True
    assert role_plan["two_stage_reception_surface_required"] is True
    assert role_plan["section_labels_required"] is True
    assert role_plan["display_labels"] == {
        "observation": "見えたこと",
        "reception": "Emlisから",
    }
    assert role_plan["two_stage_reception_labels"] == ["見えたこと", "Emlisから"]
    assert role_plan["section_id_order"] == ["observation", "reception"]
    assert role_plan["display_label_order"] == ["見えたこと", "Emlisから"]
    assert role_plan["joined_comment_text_required"] is True
    assert role_plan["expected_comment_text_shape"] == "labelled_two_stage_text"
    assert role_plan["observation_section_must_precede_reception_section"] is True
    assert role_plan["observation_section_must_not_include_human_follow"] is True
    assert role_plan["reception_section_must_not_include_new_observation_claim"] is True
    assert role_plan["daily_reception_may_use_natural_short_comment"] is True
    assert role_plan["must_not_prompt_for_event_when_event_fact_present"] is True
    assert role_plan["material_is_completed_reply_template"] is False
    assert role_plan["comment_text_generated"] is False
    assert role_plan["public_response_key_added"] is False
    assert role_plan["observation_text_public_response_key_added"] is False
    assert role_plan["reception_text_public_response_key_added"] is False
    assert role_plan["section_text_public_response_keys_added"] is False

    assert role_plan["sections"][0]["display_label"] == "見えたこと"
    assert role_plan["sections"][0]["section_id"] == "observation"
    assert role_plan["sections"][0]["must_not_include_human_follow"] is True
    assert role_plan["sections"][1]["display_label"] == "Emlisから"
    assert role_plan["sections"][1]["section_id"] == "reception"
    assert role_plan["sections"][1]["reception_section_role"] == "emlis_reception"
    assert role_plan["sections"][1]["must_not_include_new_observation_claim"] is True

    contract = payload["composition_contract"]
    assert contract["two_stage_reception_surface_required"] is True
    assert contract["two_stage_display_required"] is True
    assert contract["section_labels_required"] is True
    assert contract["two_stage_reception_labels"] == ["見えたこと", "Emlisから"]
    assert contract["two_stage_section_order"] == ["observation", "reception"]
    assert contract["observation_display_label"] == "見えたこと"
    assert contract["reception_display_label"] == "Emlisから"
    assert contract["joined_comment_text_required"] is True
    assert contract["expected_comment_text_shape"] == "labelled_two_stage_text"
    assert contract["observation_section_must_precede_reception_section"] is True
    assert contract["observation_section_must_not_include_human_follow"] is True
    assert contract["reception_section_must_not_include_new_observation_claim"] is True
    assert contract["daily_reception_may_use_natural_short_comment"] is True
    assert contract["must_not_prompt_for_event_when_event_fact_present"] is True
    assert contract["public_response_key_added"] is False
    assert contract["observation_text_public_response_key_added"] is False
    assert contract["reception_text_public_response_key_added"] is False
    assert payload["expected_response_schema"]["required"] == [
        "comment_text",
        "used_evidence_span_ids",
        "confidence",
    ]


def test_phase8_daily_reception_role_plan_allows_short_natural_reception_without_prompt_escape():
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    current_input = current_input_for_two_stage_reception_case(case)
    payload, _evidence, _scope, _material = _payload_for_current_input(current_input)

    reception_mode = payload["state_answer_surface_contract"]["reception_mode"]
    role_plan = payload["state_answer_composer_role_plan"]
    contract = payload["composition_contract"]

    assert reception_mode["reception_mode_id"] == "daily_unpleasant_reception"
    assert role_plan["current_reception_mode_may_use_natural_short_comment"] is True
    assert role_plan["daily_reception_may_use_natural_short_comment"] is True
    assert role_plan["must_not_prompt_for_event_when_event_fact_present"] is True
    assert contract["current_reception_mode_may_use_natural_short_comment"] is True
    assert contract["daily_reception_may_use_natural_short_comment"] is True
    assert contract["must_not_prompt_for_event_when_event_fact_present"] is True
    assert contract["expected_comment_text_shape"] == "labelled_two_stage_text"


def test_phase8_conversation_composer_accepts_two_stage_comment_text_inside_existing_comment_text_key():
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    current_input = current_input_for_two_stage_reception_case(case)
    payload, evidence, scope, material = _payload_for_current_input(current_input)

    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=_TwoStageCommentTextComposer(),
        trace_id="phase8-two-stage-comment-text",
        observation_structure_material=material,
    )

    assert candidate.status == "generated"
    assert candidate.composer_source == "ai_generated"
    assert candidate.fixed_string_renderer_used is False
    assert candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in candidate.comment_text
    assert candidate.comment_text.count("見えたこと：") == 1
    assert candidate.comment_text.count("Emlisから：") == 1
    assert candidate.used_evidence_span_ids

    meta = candidate.composer_meta
    assert meta["state_answer_two_stage_display_required"] is True
    assert meta["state_answer_section_labels_required"] is True
    assert meta["state_answer_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert meta["state_answer_public_response_key_added"] is False
    assert meta["state_answer_observation_text_public_response_key_added"] is False
    assert meta["state_answer_reception_text_public_response_key_added"] is False
    scope_completion = meta["environment_state_output_scope_marker_completion"]
    assert scope_completion["skip_reason"] == "two_stage_labels_provide_scope_boundary"
    assert scope_completion["two_stage_labels_present"] is True
    assert scope_completion["section_order_valid"] is True
    assert scope_completion["action"] == "continue"
