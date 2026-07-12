# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import (
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    OBSERVATION_SECTION_LABEL,
    RECEPTION_SECTION_LABEL,
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
    validate_grounded_sentence_plan,
)
from emlis_ai_reply_service import render_emlis_ai_reply


_CASES = {
    case.case_id: case
    for case in (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
}
_FORBIDDEN_LEDGER_PHRASES = (
    "記されています",
    "記録されています",
    "同じ記録にあります",
    "この記録には",
)


def _artifacts(case_id: str):
    current_input = _CASES[case_id].as_current_input()
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    return current_input, resolver, plan, sentence_plan, surface, report


@pytest.mark.parametrize("case_id", tuple(_CASES))
def test_all_current_observations_are_visible_labelled_two_stage_and_non_ledger(
    case_id: str,
) -> None:
    current_input, _resolver, _plan, _sentence_plan, _surface, _report = _artifacts(case_id)
    reply = asyncio.run(
        render_emlis_ai_reply(
            user_id="mandatory-two-stage-runtime-contract",
            subscription_tier="free",
            current_input=current_input,
        )
    )
    observation, reception, issues = split_two_stage_surface(reply.comment_text)
    grounded = reply.meta["grounded_observation"]

    assert issues == ()
    assert reply.comment_text.startswith(OBSERVATION_SECTION_LABEL)
    assert reply.comment_text.count(OBSERVATION_SECTION_LABEL) == 1
    assert reply.comment_text.count(RECEPTION_SECTION_LABEL) == 1
    assert observation
    assert reception
    assert observation != reception
    assert grounded["two_stage_contract_gate"] == "passed"
    assert grounded["mechanical_restatement_gate"] == "passed"
    assert grounded["runtime_visible_contract_guard"] == "passed"
    assert grounded["two_stage_observation_section_present"] is True
    assert grounded["two_stage_reception_section_present"] is True
    assert not any(phrase in reply.comment_text for phrase in _FORBIDDEN_LEDGER_PHRASES)


@pytest.mark.parametrize("case_id", ("A", "I6-S01", "I6-S03"))
def test_short_state_never_downgrades_to_plain_surface(case_id: str) -> None:
    _input, _resolver, plan, sentence_plan, surface, report = _artifacts(case_id)
    assert plan.response_plan.surface_shape == "two_stage"
    assert plan.coverage_requirements.human_follow_required is True
    assert [line.binding.line_role for line in sentence_plan.lines][-1] == "human_follow"
    assert report.two_stage_contract_gate == "passed"
    assert surface.text.startswith(f"{OBSERVATION_SECTION_LABEL}\n")
    assert f"\n\n{RECEPTION_SECTION_LABEL}\n" in surface.text


def test_plan_validator_rejects_unilateral_plain_surface_downgrade() -> None:
    _input, resolver, plan, _sentence_plan, _surface, _report = _artifacts("A")
    downgraded = replace(
        plan,
        response_plan=replace(plan.response_plan, surface_shape="plain"),
    )
    issues = validate_grounded_observation_plan(downgraded, resolver)
    assert "mandatory_two_stage_surface_shape_missing" in issues


def test_sentence_plan_validator_rejects_integrated_follow_as_second_section_substitute() -> None:
    _input, resolver, plan, sentence_plan, _surface, _report = _artifacts("A")
    follow = sentence_plan.lines[-1]
    mutated_atoms = tuple(
        atom
        for atom in follow.binding.functional_atom_ids
        if atom != "human_follow_delivery:separate"
    ) + ("human_follow_delivery:integrated",)
    mutated_follow = replace(
        follow,
        binding=replace(follow.binding, functional_atom_ids=mutated_atoms),
    )
    mutated = replace(
        sentence_plan,
        lines=(*sentence_plan.lines[:-1], mutated_follow),
    )
    issues = validate_grounded_sentence_plan(mutated, plan, resolver)
    assert any(issue.startswith("human_follow_integrated_delivery_forbidden:") for issue in issues)
    assert "two_stage_reception_line_missing" in issues


def test_gate_rejects_missing_reception_label_even_when_internal_follow_exists() -> None:
    _input, resolver, plan, sentence_plan, surface, _report = _artifacts("A")
    missing_label = replace(
        surface,
        text=surface.text.replace(RECEPTION_SECTION_LABEL, "受け取り：", 1),
    )
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=missing_label,
        resolver=resolver,
    )
    assert report.public_observation_status == "rejected"
    assert report.two_stage_contract_gate == "failed"
    assert "two_stage_labels_missing_or_duplicated" in report.rejection_reasons


def test_gate_rejects_mechanical_ledger_restatement_under_correct_labels() -> None:
    _input, resolver, plan, sentence_plan, surface, _report = _artifacts("A")
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    mechanical = replace(
        surface,
        text=(
            f"{OBSERVATION_SECTION_LABEL}\n{observation}が記されています。\n\n"
            f"{RECEPTION_SECTION_LABEL}\n{reception}"
        ),
    )
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=mechanical,
        resolver=resolver,
    )
    assert report.public_observation_status == "rejected"
    assert report.mechanical_restatement_gate == "failed"
    assert report.mechanical_restatement_detected is True
    assert "grounded_mechanical_restatement_surface" in report.rejection_reasons
