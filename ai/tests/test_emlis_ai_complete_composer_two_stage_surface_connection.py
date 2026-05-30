# -*- coding: utf-8 -*-
from __future__ import annotations

from fixtures.emlis_ai_two_stage_reception_cases import two_stage_reception_case_by_id
from emlis_ai_complete_composer_client import CocolonCompleteComposerClient
from emlis_ai_conversation_composer_service import (
    build_conversation_composer_payload,
    compose_emlis_conversation_candidate,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers


FORBIDDEN_COMPLETE_SKELETONS = (
    "先を考え続ける流れ",
    "pressure or limit",
)


def _daily_a_materials():
    case = two_stage_reception_case_by_id("daily_unpleasant_encounter_A")
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
        trace_id="phase16-complete-composer-two-stage-red",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )


def _assert_labelled_two_stage_comment_text(comment_text: str) -> None:
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert comment_text.count("見えたこと：") == 1
    assert comment_text.count("Emlisから：") == 1
    for forbidden in FORBIDDEN_COMPLETE_SKELETONS:
        assert forbidden not in comment_text


def test_phase16_6_complete_composer_direct_output_reaches_labelled_two_stage_text() -> None:
    payload = _daily_a_payload()
    result = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True).generate(payload)

    assert result["status"] == "generated"
    assert result["composer_source"] == "ai_generated"
    meta = result["composer_meta"]
    assert meta["state_answer_two_stage_display_required"] is True
    assert meta["state_answer_section_labels_required"] is True
    assert meta["state_answer_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert meta["two_stage_section_surface_plan_connected"] is True
    assert meta["two_stage_surface_realization"]["applied"] is True
    assert meta["two_stage_surface_realization"]["comment_text_body_included"] is False
    assert meta["two_stage_surface_realization"]["raw_input_included"] is False
    assert meta["complete_composer_candidate"]["comment_text_in_meta"] is False
    assert "comment_text" not in meta["complete_composer_candidate"]
    assert meta["fixed_string_renderer_used"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    _assert_labelled_two_stage_comment_text(str(result["comment_text"]))


def test_phase16_6_conversation_composer_path_reaches_labelled_two_stage_text() -> None:
    _current_input, evidence, scope, material = _daily_a_materials()
    candidate = compose_emlis_conversation_candidate(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        composer_client=CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True),
        trace_id="phase16-conversation-composer-two-stage-red",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )

    assert candidate.status == "generated"
    assert candidate.composer_source == "ai_generated"
    assert candidate.composer_meta["state_answer_two_stage_display_required"] is True
    assert candidate.composer_meta["state_answer_section_labels_required"] is True
    assert candidate.composer_meta["state_answer_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert candidate.composer_meta["two_stage_section_surface_plan_connected"] is True
    assert candidate.composer_meta["two_stage_surface_realization"]["applied"] is True
    assert candidate.composer_meta["two_stage_surface_realization"]["comment_text_body_included"] is False
    assert candidate.composer_meta["complete_composer_candidate"]["comment_text_in_meta"] is False
    _assert_labelled_two_stage_comment_text(candidate.comment_text)
