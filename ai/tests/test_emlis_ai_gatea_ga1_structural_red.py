# -*- coding: utf-8 -*-
from __future__ import annotations

"""Gate A GA1 structural REDs for post-FB172 current-input closure.

The assertions describe contribution ownership, relation surface signatures,
closure modality, clause integrity, and short-state controls.  They do not use
a completed reply body as an expected value.
"""

import ast
from dataclasses import replace
from pathlib import Path
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
_QUOTE_RE = re.compile(r"「[^」]*」")


def _artifacts_for_input(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return plan, sentence_plan, surface


def _artifacts(case_id: str):
    return _artifacts_for_input(_CASES[case_id].as_current_input())


def _atoms(line) -> set[str]:
    return set(line.binding.functional_atom_ids)


def _human_follow_role(line) -> str:
    return next(
        (atom.split(":", 1)[1] for atom in _atoms(line) if atom.startswith("human_follow:")),
        "",
    )


def _semantic_contribution(line, follow_target_ids: set[str]) -> str:
    role = _human_follow_role(line)
    if role:
        return role
    if line.binding.line_role == "limited_opposition" and follow_target_ids.intersection(
        line.binding.nucleus_ids
    ):
        return "protective_counterdirection"
    return line.binding.line_role


def _terminal_surface_stem(text: str) -> str:
    skeleton = _QUOTE_RE.sub("<ANCHOR>", text)
    return re.sub(r"\s+", "", skeleton.rsplit("<ANCHOR>", 1)[-1])


@pytest.mark.parametrize("case_id", ("D", "I6-D01"))
def test_ga1_r1_r2_same_target_lines_have_distinct_semantic_contributions(
    case_id: str,
) -> None:
    plan, sentence_plan, _surface = _artifacts(case_id)
    target_ids = set(plan.response_plan.human_follow_target_ids)
    target_lines = tuple(
        line
        for line in sentence_plan.lines
        if target_ids.intersection(line.binding.nucleus_ids)
    )
    contributions = tuple(
        _semantic_contribution(line, target_ids) for line in target_lines
    )
    assert len(contributions) == len(set(contributions))


@pytest.mark.parametrize("case_id", ("D", "I6-D01"))
def test_ga1_r3_self_denial_has_no_counterdirection_triple_delivery(
    case_id: str,
) -> None:
    plan, sentence_plan, _surface = _artifacts(case_id)
    roles = {line.binding.line_role for line in sentence_plan.lines}
    target_ids = set(plan.response_plan.human_follow_target_ids)
    duplicate_counterdirection = any(
        line.binding.line_role == "human_follow"
        and _human_follow_role(line) == "protective_counterdirection"
        and target_ids.intersection(line.binding.nucleus_ids)
        for line in sentence_plan.lines
    )
    assert not (
        {"fact_boundary", "limited_opposition", "human_follow"} <= roles
        and duplicate_counterdirection
    )


@pytest.mark.parametrize("case_id", ("I6-D02", "I6-D03"))
def test_ga1_r3_help_seeking_is_a_distinct_self_denial_control(case_id: str) -> None:
    _plan, sentence_plan, _surface = _artifacts(case_id)
    follow = next(
        line for line in sentence_plan.lines if line.binding.line_role == "human_follow"
    )
    assert _human_follow_role(follow) == "help_seeking_preserved"


@pytest.mark.parametrize("case_id", ("B", "C"))
def test_ga1_r4_repeated_surface_stem_requires_distinct_role_expression(
    case_id: str,
) -> None:
    _plan, sentence_plan, surface = _artifacts(case_id)
    plan_by_id = {line.binding.sentence_id: line for line in sentence_plan.lines}
    observed: dict[str, list[tuple[str, tuple[str, ...]]]] = {}
    for line in surface.lines:
        planned = plan_by_id[line.sentence_id]
        if planned.binding.line_role not in {
            "primary_observation",
            "supporting_observation",
        }:
            continue
        signature = _terminal_surface_stem(line.text)
        surface_roles = tuple(
            sorted(
                atom
                for atom in _atoms(planned)
                if atom.startswith("relation_surface_role:")
            )
        )
        observed.setdefault(signature, []).append((line.sentence_id, surface_roles))
    invalid = {
        signature: occurrences
        for signature, occurrences in observed.items()
        if len(occurrences) > 1
        and (
            any(not roles for _sentence_id, roles in occurrences)
            or len({roles for _sentence_id, roles in occurrences}) != len(occurrences)
        )
    }
    assert invalid == {}


@pytest.mark.parametrize(
    "case_id",
    ("B", "C", "I6-L01", "I6-L02", "I6-L03", "I6-C01", "I6-C02", "I6-C03"),
)
def test_ga1_r5_retained_intention_closure_declares_role_modality_and_scope(
    case_id: str,
) -> None:
    plan, sentence_plan, _surface = _artifacts(case_id)
    target_ids = set(plan.response_plan.human_follow_target_ids)
    target_line = next(
        line
        for line in sentence_plan.lines
        if target_ids.intersection(line.binding.nucleus_ids)
        and "human_follow:retained_intention" in _atoms(line)
    )
    assert {
        "closure_role:human_follow",
        "closure_modality:intention",
        "closure_scope:selected_target",
    } <= _atoms(target_line)


def test_ga1_r6_dependent_clause_control_remains_a_complete_bound_unit() -> None:
    _plan, sentence_plan, _surface = _artifacts("B")
    atoms = {atom for line in sentence_plan.lines for atom in _atoms(line)}
    assert "surface_unit:complete_clause" in atoms
    assert "dependency:quotative_continuation" in atoms


@pytest.mark.parametrize("case_id", ("I6-S01", "I6-S02", "I6-S03"))
def test_ga1_r7_short_state_stays_one_line_without_duplicate_follow(
    case_id: str,
) -> None:
    plan, sentence_plan, _surface = _artifacts(case_id)
    assert len(plan.coverage_requirements.required_nucleus_ids) == 1
    assert len(sentence_plan.lines) == 1
    assert sentence_plan.lines[0].binding.line_role != "human_follow"


def test_ga1_r8_case_id_and_case_order_do_not_change_structural_decisions() -> None:
    case = _CASES["I6-C01"]
    renamed = replace(case, case_id="metamorphic-unseen-case")
    original = _artifacts_for_input(case.as_current_input())
    metamorphic = _artifacts_for_input(renamed.as_current_input())
    assert original[0].as_body_free_meta() == metamorphic[0].as_body_free_meta()
    assert original[1].as_body_free_meta() == metamorphic[1].as_body_free_meta()
    reversed_results = [_artifacts(case_id)[1].as_body_free_meta() for case_id in ("I6-C02", "I6-C01")]
    forward_results = [_artifacts(case_id)[1].as_body_free_meta() for case_id in ("I6-C01", "I6-C02")]
    assert reversed_results == list(reversed(forward_results))


def test_ga1_file_contains_no_exact_completed_body_assertion() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(
            isinstance(operator, ast.Eq) for operator in node.ops
        ):
            continue
        values = (node.left, *node.comparators)
        has_completed_body_field = any(
            isinstance(value, ast.Attribute)
            and value.attr in {"text", "comment_text", "current_body"}
            for value in values
        )
        has_literal_sentence = any(
            isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and len(value.value) >= 20
            for value in values
        )
        assert not (has_completed_body_field and has_literal_sentence)

