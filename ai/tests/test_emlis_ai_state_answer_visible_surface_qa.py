# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pytest

from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_state_answer_composer_contract import build_state_answer_composer_role_plan
from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report
from fixtures.emlis_ai_state_answer_cases import (
    COMMON_FORBIDDEN_SURFACE_PROBES,
    STATE_ANSWER_FORBIDDEN_SURFACE_FRAGMENTS,
    STATE_ANSWER_REQUIRED_CASE_IDS,
    STATE_ANSWER_VISIBLE_SURFACE_QA_CASES,
    STATE_ANSWER_VISIBLE_SURFACE_QA_VERSION,
    current_input_for_state_answer_case,
)

_GENERATED_QA_CASE_IDS = {
    "anxiety_standard",
    "exhaustion_balanced",
    "ambivalence_standard",
    "joy_or_relief_standard",
    "structure_question_observation_thickened",
}

_FORBIDDEN_PUBLIC_PAYLOAD_KEYS = {
    "memo",
    "memo_action",
    "raw_input",
    "raw_text",
    "input_text",
    "source_text",
    "comment_text",
    "candidate_comment_text",
    "public_comment_text",
    "reply_text",
    "surface_text",
    "evidence_text",
    "raw_quote",
    "raw_quotes",
    "body",
    "text",
    "sentence",
    "sentences",
}


def _state_answer_contract(case: dict) -> dict:
    return build_emlis_state_answer_surface_contract(current_input_for_state_answer_case(case)).as_meta()


def _composer_candidate(case: dict):
    current_input = current_input_for_state_answer_case(case)
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    material = build_observation_structure_material(
        current_input=current_input,
        evidence_ledger=evidence,
    )
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id=f"phase9-{case['case_id']}",
        observation_structure_material=material,
    )
    return CocolonLimitedComposerClient().generate(payload), evidence, scope, current_input, payload


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _compact(value: str) -> str:
    for ch in "\n\r\t 　、,。.!！?？『』\"'「」（）()[]【】":
        value = value.replace(ch, "")
    return value


def _assert_no_forbidden_public_payload_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key) not in _FORBIDDEN_PUBLIC_PAYLOAD_KEYS
            _assert_no_forbidden_public_payload_keys(child)
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            _assert_no_forbidden_public_payload_keys(child)


def _assert_public_meta_does_not_contain_raw_text(public_meta: dict, case: dict, surface: str = "") -> None:
    dumped = _json(public_meta)
    _assert_no_forbidden_public_payload_keys(public_meta)
    for raw_fragment in (
        str(case.get("memo") or "")[:24],
        str(case.get("memo_action") or "")[:24],
        str(surface or "")[:24],
    ):
        if raw_fragment:
            assert raw_fragment not in dumped
    assert '"state_answer_surface_contract":' not in dumped
    assert '"emlis_state_answer_surface_contract":' not in dumped


def _case(case_id: str) -> dict:
    return next(case for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case["case_id"] == case_id)


def test_phase9_fixture_set_covers_required_acceptance_cases():
    assert STATE_ANSWER_VISIBLE_SURFACE_QA_VERSION == "cocolon.emlis_state_answer.visible_surface_qa.v1"
    assert {case["case_id"] for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES} == STATE_ANSWER_REQUIRED_CASE_IDS


@pytest.mark.parametrize(
    "case",
    STATE_ANSWER_VISIBLE_SURFACE_QA_CASES,
    ids=[case["case_id"] for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES],
)
def test_phase9_state_answer_material_acceptance_matrix(case):
    contract = _state_answer_contract(case)
    human_follow = contract["human_follow_layer"]
    ratio = contract["ratio_policy"]["resolved_ratio"]

    assert [step["step_id"] for step in contract["observation_layer"]["steps"]] == [
        "intent_pickup",
        "surface_state_observation",
        "unconfirmed_area",
        "deeper_state_observation",
        "fact_boundary",
    ]
    assert human_follow["input_type"] == case["expected_input_type"]
    assert human_follow["primary_follow_key"] == case["expected_primary_follow_key"]
    assert len(human_follow["secondary_follow_keys"]) == 2
    assert human_follow["afterglow_follow_key"]
    assert human_follow["follow_mode"] == "emlis_impression_not_fact"
    assert human_follow["personality_claim_allowed"] is False
    assert human_follow["emotion_label_only_selection"] is False

    assert ratio["observation"] == pytest.approx(case["expected_ratio"]["observation"])
    assert ratio["human_follow"] == pytest.approx(case["expected_ratio"]["human_follow"])
    assert ratio["reason"] == case["expected_ratio"]["reason"]
    assert ratio["observation"] > 0
    assert ratio["human_follow"] > 0
    assert contract["ratio_policy"]["ratio_basis"]["character_count_exact"] is False
    assert contract["ratio_policy"]["ratio_basis"]["section_role_unit_plan"]["observation_units"] >= 1
    assert contract["ratio_policy"]["ratio_basis"]["section_role_unit_plan"]["human_follow_units"] >= 1
    if case.get("expect_follow_thickened"):
        assert ratio["human_follow"] >= ratio["observation"]

    if case.get("expected_special_case") == "self_denial":
        self_denial = contract["special_handling"]["self_denial"]
        assert self_denial["enabled"] is True
        assert self_denial["felt_state_is_real"] is True
        assert self_denial["identity_claim_is_not_accepted"] is True
        assert self_denial["emlis_impression_has_evidence"] is True
        assert self_denial["identity_claim_as_fact_allowed"] is False
    if case.get("expected_special_case") == "anger":
        anger = contract["special_handling"]["anger"]
        assert anger["enabled"] is True
        assert anger["inner_value_line_receiving_allowed"] is True
        assert anger["target_judgement_agreement_allowed"] is False
        assert anger["target_attack_amplification_allowed"] is False

    assert contract["metaphor_policy"]["free_metaphor_generation_allowed"] is False
    assert contract["metaphor_policy"]["completed_metaphor_sentence_generated"] is False
    if case.get("expected_metaphor_mode"):
        assert contract["metaphor_policy"]["mode"] == case["expected_metaphor_mode"]
        assert contract["metaphor_policy"]["selected_analogy_family"] == case["expected_analogy_family"]
    else:
        assert contract["metaphor_policy"]["mode"] == "none"
    assert contract["comment_text_generated"] is False
    assert contract["raw_input_included"] is False
    assert contract["raw_text_included"] is False
    assert contract["public_response_key_added"] is False
    assert contract["rn_visible_contract_changed"] is False

    role_plan = build_state_answer_composer_role_plan(contract)
    assert role_plan["section_role_order"] == ["state_answer_observation", "human_follow"]
    assert role_plan["observation_zero_allowed"] is False
    assert role_plan["human_follow_zero_allowed"] is False
    assert role_plan["comfort_only_allowed"] is False
    assert role_plan["completed_reply_generated"] is False
    assert role_plan["fixed_sentence_template_used"] is False
    assert role_plan["runtime_renderer_marker_used"] is False

    material_payload = {"contract": contract, "role_plan": role_plan}
    material_dump = _json(material_payload)
    assert case["memo"] not in material_dump
    if case.get("memo_action"):
        assert str(case["memo_action"]) not in material_dump
    _assert_no_forbidden_public_payload_keys(material_payload)


@pytest.mark.parametrize(
    "case",
    [case for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case.get("allowed_surface_probe")],
    ids=[case["case_id"] for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case.get("allowed_surface_probe")],
)
def test_phase9_allowed_special_surfaces_pass_gate_and_public_meta(case):
    current_input = current_input_for_state_answer_case(case)
    contract = _state_answer_contract(case)
    surface = case["allowed_surface_probe"]

    gate = build_state_answer_gate_boundary_report(
        visible_surface=surface,
        state_answer_surface_contract=contract,
        current_input=current_input,
    )
    assert gate["passed"] is True, gate["rejection_reasons"]
    assert gate["blocked"] is False
    assert case["expected_allowed_exception"] in gate["allowed_exception_ids"]
    assert gate["public_meta_summary_only"] is True

    visible = build_visible_surface_acceptance_gate_report(
        comment_text=surface,
        current_input=current_input,
        state_answer_surface_contract=contract,
    )
    assert visible["passed"] is True, visible["rejection_reasons"]
    assert visible["state_answer_public_meta_summary_only"] is True
    assert visible["state_answer_contract_body_returned"] is False
    assert visible["state_answer_raw_evidence_included"] is False

    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            "state_answer_gate_boundary": gate,
            "visible_surface_acceptance_gate": visible,
        },
        comment_text_present=True,
        subscription_tier="free",
    )
    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback(surface, public_meta) is True
    _assert_public_meta_does_not_contain_raw_text(public_meta, case, surface=surface)


@pytest.mark.parametrize(
    "case",
    [case for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case.get("blocked_surface_probe")],
    ids=[case["case_id"] for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case.get("blocked_surface_probe")],
)
def test_phase9_blocked_special_surfaces_never_become_passed_comment_text(case):
    current_input = current_input_for_state_answer_case(case)
    contract = _state_answer_contract(case)
    surface = case["blocked_surface_probe"]

    gate = build_state_answer_gate_boundary_report(
        visible_surface=surface,
        state_answer_surface_contract=contract,
        current_input=current_input,
    )
    assert gate["passed"] is False
    assert gate["blocked"] is True
    assert set(case["expected_block_reasons"]).intersection(gate["rejection_reasons"])

    visible = build_visible_surface_acceptance_gate_report(
        comment_text=surface,
        current_input=current_input,
        state_answer_surface_contract=contract,
    )
    assert visible["passed"] is False
    assert visible["classification"] == "red"
    assert set(case["expected_block_reasons"]).intersection(visible["rejection_reasons"])

    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            "state_answer_gate_boundary": gate,
            "visible_surface_acceptance_gate": visible,
        },
        comment_text_present=True,
        subscription_tier="free",
    )
    assert public_meta["observation_status"] == "rejected"
    assert "public_feedback_state_answer_gate_blocked" in public_meta["rejection_reasons"]
    assert should_include_public_input_feedback(surface, public_meta) is False
    _assert_public_meta_does_not_contain_raw_text(public_meta, case, surface=surface)


@pytest.mark.parametrize(
    "probe",
    COMMON_FORBIDDEN_SURFACE_PROBES,
    ids=[probe["surface"] for probe in COMMON_FORBIDDEN_SURFACE_PROBES],
)
def test_phase9_common_forbidden_surfaces_are_blocked_by_state_answer_gate(probe):
    case = _case("anxiety_standard")
    current_input = current_input_for_state_answer_case(case)
    contract = _state_answer_contract(case)

    gate = build_state_answer_gate_boundary_report(
        visible_surface=probe["surface"],
        state_answer_surface_contract=contract,
        current_input=current_input,
    )
    assert gate["passed"] is False
    assert gate["blocked"] is True
    assert set(probe["expected_block_reasons"]).intersection(gate["rejection_reasons"])


@pytest.mark.parametrize(
    "case",
    [case for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case["case_id"] in _GENERATED_QA_CASE_IDS],
    ids=[case["case_id"] for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES if case["case_id"] in _GENERATED_QA_CASE_IDS],
)
def test_phase9_generated_visible_surfaces_pass_structure_not_exact_text(case):
    candidate, evidence, scope, current_input, _payload = _composer_candidate(case)
    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "ai_generated"
    assert candidate["comment_text"]

    text = candidate["comment_text"]
    compact = _compact(text)
    for forbidden in STATE_ANSWER_FORBIDDEN_SURFACE_FRAGMENTS:
        assert _compact(forbidden) not in compact

    contract = _state_answer_contract(case)
    visible = build_visible_surface_acceptance_gate_report(
        comment_text=text,
        current_input=current_input,
        state_answer_surface_contract=contract,
        composer_meta=candidate.get("composer_meta") or {},
    )
    assert visible["passed"] is True, visible["rejection_reasons"]

    gate = build_state_answer_gate_boundary_report(
        visible_surface=text,
        state_answer_surface_contract=contract,
        composer_meta=candidate.get("composer_meta") or {},
        current_input=current_input,
    )
    assert gate["passed"] is True, gate["rejection_reasons"]

    guard = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert guard.passed is True, guard.rejection_reasons

    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            "state_answer_gate_boundary": gate,
            "visible_surface_acceptance_gate": visible,
        },
        comment_text_present=True,
        subscription_tier="free",
    )
    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback(text, public_meta) is True
    _assert_public_meta_does_not_contain_raw_text(public_meta, case, surface=text)


def test_phase9_low_information_case_does_not_become_passed_comment_text():
    case = _case("low_information")
    candidate, _evidence, scope, _current_input, _payload = _composer_candidate(case)

    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "unavailable"
    assert candidate["comment_text"] == ""
    assert set(candidate["rejection_reasons"]).intersection(
        {
            "limited_composer_shallow_insufficient_evidence",
            "limited_composer_missing_information",
            "limited_composer_short_ambiguous_low_evidence",
        }
    )

    public_meta = build_public_emlis_input_feedback_meta(
        {"observation_status": "passed", "rejection_reasons": candidate["rejection_reasons"]},
        comment_text_present=False,
        subscription_tier="free",
    )
    assert public_meta["observation_status"] == "unavailable"
    assert "public_feedback_comment_text_missing" in public_meta["rejection_reasons"]
    assert should_include_public_input_feedback(candidate["comment_text"], public_meta) is False
    _assert_public_meta_does_not_contain_raw_text(public_meta, case)


def test_phase9_qa_probe_surfaces_are_not_runtime_templates():
    service_dir = Path(__file__).resolve().parents[1] / "services" / "ai_inference"
    service_sources = "\n".join(path.read_text(encoding="utf-8") for path in service_dir.glob("emlis_ai_*.py"))

    probes = []
    for case in STATE_ANSWER_VISIBLE_SURFACE_QA_CASES:
        probes.extend(str(case.get(key) or "") for key in ("allowed_surface_probe", "blocked_surface_probe"))
    probes.extend(probe["surface"] for probe in COMMON_FORBIDDEN_SURFACE_PROBES)

    for surface in probes:
        surface = surface.strip()
        if not surface:
            continue
        first_sentence = surface.split("。")[0]
        assert first_sentence not in service_sources
