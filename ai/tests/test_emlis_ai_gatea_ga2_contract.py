# -*- coding: utf-8 -*-
from __future__ import annotations

"""GA2 Plan/SentencePlan/Surface/Gate and regression contracts."""

import ast
from dataclasses import replace
from pathlib import Path

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
    GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION,
    build_grounded_observation_plan,
    classify_grounded_human_follow_delivery,
)
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    GroundedSurfaceLine,
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
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    return plan, resolver, sentence_plan, surface, report


def _follow_line(plan, sentence_plan):
    target_ids = set(plan.response_plan.human_follow_target_ids)
    return next(
        line
        for line in sentence_plan.lines
        if target_ids.intersection(line.binding.nucleus_ids)
        and any(
            atom.startswith("human_follow:")
            for atom in line.binding.functional_atom_ids
        )
    )


def _delivery(plan) -> str:
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    return classify_grounded_human_follow_delivery(
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
        required_nucleus_count=len(plan.coverage_requirements.required_nucleus_ids),
        target_nuclei=tuple(
            nucleus_index[item]
            for item in plan.response_plan.human_follow_target_ids
            if item in nucleus_index
        ),
        relations=plan.relations,
        required_relation_ids=plan.coverage_requirements.required_relation_ids,
        fact_boundary_nucleus_ids=plan.response_plan.fact_boundary_nucleus_ids,
    )


@pytest.mark.parametrize(
    ("case_id", "expected"),
    (
        ("D", "integrated_into_relation"),
        ("I6-D01", "integrated_into_relation"),
        ("I6-D02", "separate_distinct_contribution"),
        ("I6-D03", "separate_distinct_contribution"),
        ("I6-C01", "integrated_into_relation"),
        ("I6-S01", "integrated_into_observation"),
    ),
)
def test_ga2_a_plan_owns_body_free_follow_delivery(case_id: str, expected: str) -> None:
    plan = _artifacts(case_id)[0]
    assert _delivery(plan) == expected
    assert GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION == "cocolon.emlis.grounded_semantics.i2.v3"


@pytest.mark.parametrize("case_id", ("D", "I6-D01"))
def test_ga2_b_protective_counterdirection_is_integrated_once(case_id: str) -> None:
    plan, _resolver, sentence_plan, _surface, report = _artifacts(case_id)
    follow = _follow_line(plan, sentence_plan)
    assert follow.binding.line_role == "limited_opposition"
    assert "human_follow:protective_counterdirection" in follow.binding.functional_atom_ids
    assert "human_follow_delivery:integrated" in follow.binding.functional_atom_ids
    assert not any(
        line.binding.line_role == "human_follow" for line in sentence_plan.lines
    )
    assert report.public_observation_status == "passed"


@pytest.mark.parametrize("case_id", ("I6-D02", "I6-D03"))
def test_ga2_b_help_seeking_keeps_distinct_value_without_requoting_target(
    case_id: str,
) -> None:
    plan, resolver, sentence_plan, surface, report = _artifacts(case_id)
    follow = _follow_line(plan, sentence_plan)
    assert follow.binding.line_role == "human_follow"
    assert "human_follow:help_seeking_preserved" in follow.binding.functional_atom_ids
    assert "human_follow_target_already_delivered" in follow.binding.functional_atom_ids
    target_text = " ".join(
        resolver.resolve(span_id).raw_text.strip(" 、。")
        for nucleus in plan.nuclei
        if nucleus.nucleus_id in plan.response_plan.human_follow_target_ids
        for span_id in nucleus.source_span_ids
    )
    assert target_text
    target_anchor = target_text.split("、")[-1]
    assert surface.text.count(target_anchor) == 1
    assert report.public_observation_status == "passed"


@pytest.mark.parametrize(
    "case_id",
    ("B", "C", "I6-L01", "I6-L02", "I6-L03", "I6-C01", "I6-C02", "I6-C03"),
)
def test_ga2_b_c_retained_intention_has_scoped_modality_without_generic_tail(
    case_id: str,
) -> None:
    plan, _resolver, sentence_plan, surface, report = _artifacts(case_id)
    follow = _follow_line(plan, sentence_plan)
    assert {
        "human_follow:retained_intention",
        "human_follow_contribution:retained_intention",
        "human_follow_delivery:integrated",
        "closure_role:human_follow",
        "closure_modality:intention",
        "closure_scope:selected_target",
    } <= set(follow.binding.functional_atom_ids)
    target_surface_line = next(
        line for line in surface.lines if line.sentence_id == follow.binding.sentence_id
    )
    assert target_surface_line.text.count("。") <= 2
    assert report.public_observation_status == "passed"


def test_ga2_c_action_relation_distinguishes_current_change_from_intention() -> None:
    _plan, _resolver, sentence_plan, _surface, report = _artifacts("B")
    action_line = next(
        line
        for line in sentence_plan.lines
        if "relation:action_supports_change" in line.binding.functional_atom_ids
    )
    atoms = set(action_line.binding.functional_atom_ids)
    assert "relation_surface_role:change_evidenced_by_action" in atoms
    assert "relation_surface_role:intention_evidenced_by_action" not in atoms
    assert report.public_observation_status == "passed"


@pytest.mark.parametrize("case_id", tuple(_CASES))
def test_ga2_d_same16_current_gate_passes_without_question_or_body_free_leak(
    case_id: str,
) -> None:
    plan, _resolver, sentence_plan, surface, report = _artifacts(case_id)
    assert report.public_observation_status == "passed"
    assert report.rejection_reasons == ()
    assert plan.response_plan.question_policy.allowed is False
    assert all(not line.binding.contains_question for line in sentence_plan.lines)
    assert surface.as_body_free_meta()["surface_text_included"] is False


def test_ga2_d_gate_rejects_reintroduced_self_denial_duplicate() -> None:
    plan, resolver, sentence_plan, surface, _report = _artifacts("D")
    source = _follow_line(plan, sentence_plan)
    duplicate_atoms = tuple(
        atom
        for atom in source.binding.functional_atom_ids
        if not atom.startswith(("relation:", "relation_surface", "relation_endpoint"))
        and atom not in {
            "human_follow_delivery:integrated",
            "human_follow_target_already_delivered",
            "line_role:limited_opposition",
            "surface_function:render_limited_opposition",
        }
    ) + (
        "line_role:human_follow",
        "surface_function:render_human_follow",
        "human_follow_delivery:separate",
    )
    duplicate_binding = replace(
        source.binding,
        sentence_id="sentence:3",
        line_role="human_follow",
        relation_ids=(),
        functional_atom_ids=duplicate_atoms,
    )
    duplicate_line = replace(
        source,
        binding=duplicate_binding,
        surface_function="render_human_follow",
    )
    duplicate_surface = GroundedSurfaceLine(
        sentence_id="sentence:3",
        text=surface.lines[-1].text,
        binding=duplicate_binding,
    )
    mutated_plan = replace(sentence_plan, lines=(*sentence_plan.lines, duplicate_line))
    mutated_surface = replace(surface, lines=(*surface.lines, duplicate_surface))
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=mutated_plan,
        surface_result=mutated_surface,
        resolver=resolver,
    )
    assert "human_follow_no_distinct_contribution" in report.rejection_reasons
    assert "human_follow_repeats_relation_target" in report.rejection_reasons
    assert "self_denial_counterdirection_duplicated" in report.rejection_reasons


def test_ga2_d_gate_rejects_retained_intention_closure_mismatch() -> None:
    plan, resolver, sentence_plan, surface, _report = _artifacts("I6-C01")
    source = _follow_line(plan, sentence_plan)
    stripped_binding = replace(
        source.binding,
        functional_atom_ids=tuple(
            atom
            for atom in source.binding.functional_atom_ids
            if not atom.startswith("closure_")
        ),
    )
    stripped_line = replace(source, binding=stripped_binding)
    mutated_plan = replace(
        sentence_plan,
        lines=tuple(
            stripped_line if line is source else line for line in sentence_plan.lines
        ),
    )
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=mutated_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert "generic_follow_suffix_role_mismatch" in report.rejection_reasons


def test_ga2_d_gate_rejects_repeated_stem_without_expressed_role() -> None:
    plan, resolver, sentence_plan, surface, _report = _artifacts("B")
    first, second = sentence_plan.lines[:2]
    stripped_binding = replace(
        second.binding,
        functional_atom_ids=tuple(
            atom
            for atom in second.binding.functional_atom_ids
            if not atom.startswith(("observation_surface_role:", "semantic_arc:"))
        ),
    )
    stripped_second = replace(second, binding=stripped_binding)
    mutated_plan = replace(
        sentence_plan,
        lines=(first, stripped_second, *sentence_plan.lines[2:]),
    )
    mutated_surface_lines = list(surface.lines)
    mutated_surface_lines[1] = replace(
        mutated_surface_lines[1],
        text=surface.lines[0].text,
        binding=stripped_binding,
    )
    mutated_surface = replace(surface, lines=tuple(mutated_surface_lines))
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=mutated_plan,
        surface_result=mutated_surface,
        resolver=resolver,
    )
    assert (
        "relation_surface_stem_repetition_without_new_role"
        in report.rejection_reasons
    )


@pytest.mark.parametrize(
    "case_id",
    ("A", "I6-S01", "I6-S02", "I6-S03", "D", "I6-D02", "B", "I6-L03"),
)
@pytest.mark.parametrize("recovery_stage", GROUND_RECOVERY_STAGES)
def test_ga2_e_recovery_preserves_required_meaning_and_safety(
    case_id: str,
    recovery_stage: str,
) -> None:
    plan, _resolver, sentence_plan, surface, report = _artifacts(
        case_id,
        recovery_stage=recovery_stage,
    )
    assert set(plan.coverage_requirements.required_nucleus_ids) <= set(
        sentence_plan.covered_required_nucleus_ids
    )
    assert set(plan.coverage_requirements.required_relation_ids) <= set(
        sentence_plan.covered_required_relation_ids
    )
    assert surface.required_coverage_preserved is True
    assert report.public_observation_status == "passed"


def test_ga2_e_surface_is_deterministic_and_has_no_case_specific_source_branch() -> None:
    for case_id in _CASES:
        first = _artifacts(case_id)[3]
        second = _artifacts(case_id)[3]
        assert first.text == second.text
    production_paths = (
        Path(__file__).parents[1]
        / "services"
        / "ai_inference"
        / "emlis_ai_grounded_observation_plan.py",
        Path(__file__).parents[1]
        / "services"
        / "ai_inference"
        / "emlis_ai_grounded_sentence_surface.py",
        Path(__file__).parents[1]
        / "services"
        / "ai_inference"
        / "emlis_ai_grounded_observation_gate.py",
    )
    string_literals = {
        node.value
        for path in production_paths
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    fixture_case_ids = {case_id for case_id in _CASES if case_id.startswith("I6-")}
    assert not fixture_case_ids.intersection(string_literals)


def test_ga2_contract_contains_no_exact_completed_body_assertion() -> None:
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
