# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from fixtures.emlis_ai_two_stage_reception_cases import two_stage_reception_case_by_id
from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_state_answer_composer_contract import attach_state_answer_composer_meta
from emlis_ai_two_stage_section_surface_plan import (
    EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID,
    EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION,
    assert_two_stage_section_surface_plan,
    build_two_stage_section_surface_plan,
)


def _daily_a_payload() -> dict:
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
    current_input = dict(case["current_input"])
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    material = build_observation_structure_material(current_input=current_input, evidence_ledger=evidence)
    return build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="phase16-2-two-stage-section-surface-plan",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )


def test_phase16_2_builds_two_stage_section_surface_plan_from_role_plan() -> None:
    payload = _daily_a_payload()
    plan = build_two_stage_section_surface_plan(
        payload["state_answer_composer_role_plan"],
        state_answer_surface_contract=payload["state_answer_surface_contract"],
        composition_contract=payload["composition_contract"],
    )

    assert_two_stage_section_surface_plan(plan)
    assert plan["schema_version"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION
    assert plan["material_id"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID
    assert plan["enabled"] is True
    assert plan["required"] is True
    assert plan["expected_comment_text_shape"] == "labelled_two_stage_text"
    assert plan["display_labels"] == {"observation": "見えたこと", "reception": "Emlisから"}
    assert plan["comment_text_section_labels"] == {"observation": "見えたこと：", "reception": "Emlisから："}
    assert plan["section_order"] == ["observation", "reception"]
    assert plan["reception_mode_id"] == "daily_unpleasant_reception"
    assert plan["ratio_reason"] == "daily_unpleasant_reception_light"
    assert plan["comment_text_generated"] is False
    assert plan["completed_reply_template_used"] is False
    assert plan["public_response_key_added"] is False
    assert plan["public_contract"]["rn_visible_contract_changed"] is False

    observation, reception = plan["sections"]
    assert observation["section_id"] == "observation"
    assert observation["section_role"] == "state_answer_observation"
    assert observation["display_label"] == "見えたこと"
    assert observation["comment_text_section_label"] == "見えたこと："
    assert observation["sentence_plan_unit_count"] == 1
    assert observation["must_not_include_human_follow"] is True
    assert observation["comment_text_generated"] is False

    assert reception["section_id"] == "reception"
    assert reception["section_role"] == "emlis_reception"
    assert reception["source_role_plan_section_role"] == "human_follow"
    assert reception["display_label"] == "Emlisから"
    assert reception["comment_text_section_label"] == "Emlisから："
    assert reception["sentence_plan_unit_count"] == 3
    assert reception["follow_mode"] == "emlis_impression_not_fact"
    assert reception["must_not_include_new_observation_claim"] is True
    assert reception["target_judgement_agreement_allowed"] is False
    assert reception["action_instruction_allowed"] is False


def test_phase16_2_conversation_payload_exposes_plan_without_response_key_change() -> None:
    payload = _daily_a_payload()
    plan = payload["two_stage_section_surface_plan"]
    contract = payload["composition_contract"]

    assert payload["two_stage_section_surface_plan_connected"] is True
    assert payload["two_stage_section_surface_plan_material_id"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID
    assert plan["section_ids"] == ["observation", "reception"]
    assert plan["sentence_plan_unit_count_by_section"] == {"observation": 1, "reception": 3}
    assert plan["public_contract"]["public_response_key_added"] is False

    assert contract["two_stage_section_surface_plan_connected"] is True
    assert contract["two_stage_section_surface_plan_required"] is True
    assert contract["two_stage_section_surface_plan_material_id"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID
    assert contract["two_stage_section_surface_plan_section_order"] == ["observation", "reception"]
    assert contract["two_stage_section_surface_plan_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert contract["public_response_key_added"] is False
    assert contract["observation_text_public_response_key_added"] is False
    assert contract["reception_text_public_response_key_added"] is False
    assert payload["expected_response_schema"]["required"] == ["comment_text", "used_evidence_span_ids", "confidence"]


def test_phase16_2_plan_is_material_only_and_does_not_copy_raw_input_text() -> None:
    payload = _daily_a_payload()
    plan = payload["two_stage_section_surface_plan"]
    encoded = json.dumps(plan, ensure_ascii=False, sort_keys=True)

    assert plan["raw_input_included"] is False
    assert plan["raw_text_included"] is False
    assert plan["comment_text_generated"] is False
    assert plan["completed_reply_template_used"] is False
    assert plan["fixed_sentence_template_used"] is False
    assert "立ちションのおじさん" not in encoded
    assert "この世で1番気持ち悪い" not in encoded
    assert "うわ、それは嫌でしたね" not in encoded
    assert "不快で怖さもある出来事" not in encoded


def test_phase16_2_attaches_section_surface_plan_to_internal_composer_meta_only() -> None:
    payload = _daily_a_payload()
    meta = attach_state_answer_composer_meta({}, payload)

    assert meta["two_stage_section_surface_plan_connected"] is True
    assert meta["two_stage_section_surface_plan_material_id"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID
    assert meta["two_stage_section_surface_plan_schema_version"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION
    assert meta["two_stage_section_surface_plan_section_order"] == ["observation", "reception"]
    assert meta["two_stage_section_surface_plan_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert meta["state_answer_public_response_key_added"] is False
    assert meta["state_answer_observation_text_public_response_key_added"] is False
    assert meta["state_answer_reception_text_public_response_key_added"] is False
