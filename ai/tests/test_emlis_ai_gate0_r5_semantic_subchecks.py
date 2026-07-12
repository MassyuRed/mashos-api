# -*- coding: utf-8 -*-
from __future__ import annotations

"""Gate 0 R5 semantic subcheck and repetition-guard tests."""

from dataclasses import replace
from typing import Any

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
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
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


def _artifacts(case_id: str) -> tuple[Any, Any, Any, Any]:
    normalized = normalize_emlis_current_input(_CASES[case_id].as_current_input())
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return plan, resolver, sentence_plan, surface


def _report(case_id: str, *, mutate: Any = None) -> Any:
    plan, resolver, sentence_plan, surface = _artifacts(case_id)
    if mutate is not None:
        plan, sentence_plan, surface = mutate(plan, sentence_plan, surface)
    return evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )


def test_major_arc_role_removed_from_required_set_is_rejected() -> None:
    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        required = plan.coverage_requirements.required_nucleus_ids
        coverage = replace(plan.coverage_requirements, required_nucleus_ids=required[1:])
        return replace(plan, coverage_requirements=coverage), sentence_plan, surface

    report = _report("I6-L01", mutate=mutate)
    assert report.text_semantic_retention_gate == "failed"
    assert "major_arc_role_missing" in report.rejection_reasons


@pytest.mark.parametrize(
    ("case_id", "relation_type", "reason"),
    (
        ("I6-L02", "action_supports_change", "required_relation_direction_mismatch"),
        ("I6-L03", "preserves_despite", "required_reversal_missing"),
    ),
)
def test_required_relation_endpoint_or_reversal_loss_is_rejected(
    case_id: str,
    relation_type: str,
    reason: str,
) -> None:
    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        relation = next(
            item
            for item in plan.relations
            if item.type == relation_type
            and item.relation_id in plan.coverage_requirements.required_relation_ids
        )
        lines = []
        for line in sentence_plan.lines:
            if relation.relation_id in line.binding.relation_ids:
                binding = replace(
                    line.binding,
                    nucleus_ids=(
                        relation.to_nucleus_id,
                        relation.from_nucleus_id,
                        *tuple(
                            item
                            for item in line.binding.nucleus_ids
                            if item not in {relation.from_nucleus_id, relation.to_nucleus_id}
                        ),
                    ),
                )
                line = replace(line, binding=binding)
            lines.append(line)
        return plan, replace(sentence_plan, lines=tuple(lines)), surface

    report = _report(case_id, mutate=mutate)
    assert report.text_semantic_retention_gate == "failed"
    assert reason in report.rejection_reasons


@pytest.mark.parametrize(
    ("replacement", "reason"),
    (
        ("今は、その状態なのですね。", "lexical_anchor_missing"),
        ("今は、胸の内側が苦しい感じという重さがある状態なのですね。", "ungrounded_sensation_family_added"),
    ),
)
def test_short_state_lexical_drift_is_rejected(replacement: str, reason: str) -> None:
    anchor = "胸の内側が苦しい感じ"

    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        lines = tuple(
            replace(line, text=line.text.replace(anchor, replacement))
            for line in surface.lines
        )
        return plan, sentence_plan, replace(
            surface,
            text=surface.text.replace(anchor, replacement),
            lines=lines,
        )

    report = _report("I6-S03", mutate=mutate)
    assert report.text_semantic_retention_gate == "failed"
    assert reason in report.rejection_reasons


def test_required_unknown_cannot_be_promoted_to_a_certain_result() -> None:
    source = "焼成条件はまだ不明"
    promoted = "焼成条件は確定した"

    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        lines = tuple(
            replace(line, text=line.text.replace(source, promoted))
            for line in surface.lines
        )
        return plan, sentence_plan, replace(
            surface,
            text=surface.text.replace(source, promoted),
            lines=lines,
        )

    report = _report("I6-L03", mutate=mutate)
    assert report.text_semantic_retention_gate == "failed"
    assert "required_relation_direction_mismatch" in report.rejection_reasons


def test_self_denial_protective_direction_misclassified_as_burden_is_rejected() -> None:
    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        lines = []
        for line in sentence_plan.lines:
            atoms = tuple(
                "human_follow:burden_expression"
                if atom == "human_follow:protective_counterdirection"
                else atom
                for atom in line.binding.functional_atom_ids
            )
            lines.append(replace(line, binding=replace(line.binding, functional_atom_ids=atoms)))
        return plan, replace(sentence_plan, lines=tuple(lines)), surface

    report = _report("I6-D01", mutate=mutate)
    assert report.depth_adequacy_gate == "failed"
    assert "human_follow_role_target_mismatch" in report.rejection_reasons
    assert "protective_counterdirection_misclassified_as_burden" in report.rejection_reasons


@pytest.mark.parametrize(
    ("case_id", "expected_atom"),
    (
        ("D", "human_follow:protective_counterdirection"),
        ("I6-D01", "human_follow:protective_counterdirection"),
        ("I6-D02", "human_follow:help_seeking_preserved"),
        ("I6-D03", "human_follow:help_seeking_preserved"),
    ),
)
def test_self_denial_follow_roles_keep_protection_and_help_seeking_distinct(
    case_id: str,
    expected_atom: str,
) -> None:
    _plan, _resolver, sentence_plan, _surface = _artifacts(case_id)
    follow = next(
        line
        for line in sentence_plan.lines
        if expected_atom in line.binding.functional_atom_ids
    )
    assert expected_atom in follow.binding.functional_atom_ids
    assert "human_follow:burden_expression" not in follow.binding.functional_atom_ids
    if expected_atom == "human_follow:protective_counterdirection":
        assert follow.binding.line_role == "limited_opposition"
        assert "human_follow_delivery:integrated" in follow.binding.functional_atom_ids
    else:
        assert follow.binding.line_role == "human_follow"
        assert "human_follow_delivery:separate" in follow.binding.functional_atom_ids


def test_short_state_separate_duplicate_line_is_rejected() -> None:
    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        duplicate = replace(
            sentence_plan.lines[0],
            binding=replace(sentence_plan.lines[0].binding, sentence_id="sentence:2"),
        )
        return plan, replace(sentence_plan, lines=(*sentence_plan.lines, duplicate)), surface

    report = _report("I6-S03", mutate=mutate)
    assert report.anti_template_gate == "failed"
    assert "short_state_duplicate_anchor_loop" in report.rejection_reasons


def test_same_nucleus_repeated_without_new_role_is_rejected() -> None:
    def mutate(plan: Any, sentence_plan: Any, surface: Any) -> tuple[Any, Any, Any]:
        first = sentence_plan.lines[0]
        duplicate = replace(first, binding=replace(first.binding, sentence_id="sentence:99"))
        return plan, replace(sentence_plan, lines=(first, duplicate, *sentence_plan.lines[1:])), surface

    report = _report("B", mutate=mutate)
    assert report.anti_template_gate == "failed"
    assert "surface_semantic_repetition_without_new_role" in report.rejection_reasons


@pytest.mark.parametrize("case_id", tuple(_CASES))
def test_canonical_sixteen_are_not_over_rejected(case_id: str) -> None:
    report = _report(case_id)
    assert report.semantic_quality_gate == "passed", report.rejection_reasons
    assert report.product_readfeel_status == "not_evaluated"
    meta = report.as_body_free_meta()
    assert meta["surface_text_included"] is False
    assert meta["candidate_body_included"] is False
