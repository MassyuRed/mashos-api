# -*- coding: utf-8 -*-
from __future__ import annotations

import re

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
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)


_CASES = {
    case.case_id: case
    for case in (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
}


def _artifacts(case_id: str, *, recovery_stage: str = "full"):
    normalized = normalize_emlis_current_input(_CASES[case_id].as_current_input())
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(
        plan,
        resolver,
        recovery_stage=recovery_stage,
    )
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return plan, spans, resolver, sentence_plan, surface


@pytest.mark.parametrize("recovery_stage", GROUND_RECOVERY_STAGES)
def test_rr3_a_groups_homogeneous_state_and_integrates_follow_once(
    recovery_stage: str,
) -> None:
    plan, _spans, _resolver, sentence_plan, surface = _artifacts(
        "A",
        recovery_stage=recovery_stage,
    )
    assert len(sentence_plan.lines) == 1
    line = sentence_plan.lines[0]
    assert set(plan.coverage_requirements.required_nucleus_ids) <= set(
        line.binding.nucleus_ids
    )
    assert "human_follow:burden_expression" in line.binding.functional_atom_ids
    assert "human_follow_delivery:integrated" in line.binding.functional_atom_ids
    assert sentence_plan.human_follow_covered is True
    assert surface.required_coverage_preserved is True


def test_rr5_b_dependent_clause_is_complete_source_bound_and_deterministic() -> None:
    plan, _spans, _resolver, sentence_plan, first = _artifacts("B")
    second = _artifacts("B")[-1]
    atoms = {
        atom
        for line in sentence_plan.lines
        for atom in line.binding.functional_atom_ids
    }
    assert "surface_unit:complete_clause" in atoms
    assert "dependency:quotative_continuation" in atoms
    assert set(plan.coverage_requirements.required_nucleus_ids) <= set(
        sentence_plan.covered_required_nucleus_ids
    )
    assert first.text == second.text
    assert not re.search(r"(?:何故|なぜ|どうして)と考えて", first.text)
    assert "「と考えて" not in first.text


def test_rr4_l03_complete_clause_predicate_is_not_appended_twice() -> None:
    plan, _spans, resolver, sentence_plan, surface = _artifacts("I6-L03")
    relation = next(
        item
        for item in plan.relations
        if item.type == "preserves_despite" and item.retention == "required"
    )
    right = next(
        item for item in plan.nuclei if item.nucleus_id == relation.to_nucleus_id
    )
    source_predicate_count = sum(
        resolver.resolve(span_id).raw_text.count("見えた")
        for span_id in right.source_span_ids
    )
    relation_sentence_ids = {
        line.binding.sentence_id
        for line in sentence_plan.lines
        if relation.relation_id in line.binding.relation_ids
    }
    relation_text = " ".join(
        line.text for line in surface.lines if line.sentence_id in relation_sentence_ids
    )
    assert source_predicate_count == 1
    assert relation_text.count("見えた") == source_predicate_count


@pytest.mark.parametrize(
    "case_id",
    ("C", "I6-L01", "I6-L03", "I6-C01", "I6-C02", "I6-C03"),
)
def test_rr5_intention_follow_is_integrated_without_generic_change_tail(
    case_id: str,
) -> None:
    plan, _spans, _resolver, sentence_plan, surface = _artifacts(case_id)
    target_ids = set(plan.response_plan.human_follow_target_ids)
    target_lines = tuple(
        line
        for line in sentence_plan.lines
        if target_ids.intersection(line.binding.nucleus_ids)
    )
    assert len(target_lines) == 1
    assert target_lines[0].binding.line_role != "human_follow"
    assert "human_follow:retained_intention" in target_lines[0].binding.functional_atom_ids
    assert "human_follow_delivery:integrated" in target_lines[0].binding.functional_atom_ids
    assert "という変化を、今の記録にある大切な手がかり" not in surface.text


@pytest.mark.parametrize(
    ("case_id", "expected_role", "expected_delivery"),
    (
        ("D", "protective_counterdirection", "integrated"),
        ("I6-D01", "protective_counterdirection", "integrated"),
        ("I6-D02", "help_seeking_preserved", "separate"),
        ("I6-D03", "help_seeking_preserved", "separate"),
    ),
)
def test_rr3_self_denial_follow_uses_distinct_contribution_delivery(
    case_id: str,
    expected_role: str,
    expected_delivery: str,
) -> None:
    _plan, _spans, _resolver, sentence_plan, _surface = _artifacts(case_id)
    follow = next(
        line
        for line in sentence_plan.lines
        if f"human_follow:{expected_role}" in line.binding.functional_atom_ids
    )
    assert f"human_follow:{expected_role}" in follow.binding.functional_atom_ids
    assert f"human_follow_delivery:{expected_delivery}" in follow.binding.functional_atom_ids
    if expected_delivery == "integrated":
        assert follow.binding.line_role == "limited_opposition"
    else:
        assert follow.binding.line_role == "human_follow"
