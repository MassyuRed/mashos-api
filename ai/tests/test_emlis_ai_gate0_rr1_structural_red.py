# -*- coding: utf-8 -*-
from __future__ import annotations

"""Gate 0 RR1 structural REDs for the read-feel repair cycle.

Assertions intentionally describe roles, targets, delivery units, and
validation inputs.  No completed public body is used as an expected value.
RR2 is expected to turn only the Plan role/target subset green; the remaining
REDs belong to RR3/RR4/RR5/RR6.
"""

import ast
from dataclasses import replace
import inspect
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
import emlis_ai_grounded_observation_plan as plan_module
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import build_grounded_sentence_plan
import helpers.emlis_ai_gate0_r9_r10_boundary as gate0_boundary


_CASES = {
    case.case_id: case
    for case in (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
}


def _artifacts(case_id: str):
    current_input = _CASES[case_id].as_current_input()
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    return plan, spans, resolver, sentence_plan


def _classifier():
    classifier = getattr(plan_module, "classify_grounded_human_follow_role", None)
    assert callable(classifier), "RR2 shared Plan classifier is not implemented"
    return classifier


def _nucleus_ids_containing(plan, spans, anchor: str) -> set[str]:
    span_ids = {span.span_id for span in spans if anchor in span.raw_text}
    return {
        nucleus.nucleus_id
        for nucleus in plan.nuclei
        if span_ids.intersection(nucleus.source_span_ids)
    }


def _classify(plan, nuclei) -> str:
    return _classifier()(
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
        required_nucleus_count=len(plan.coverage_requirements.required_nucleus_ids),
        nuclei=tuple(nuclei),
    )


@pytest.mark.parametrize(
    "case_id",
    ("C", "I6-L01", "I6-L03", "I6-C01", "I6-C02", "I6-C03"),
)
def test_rr1_intention_nucleus_has_retained_intention_follow_role(case_id: str) -> None:
    plan, _spans, _resolver, _sentence_plan = _artifacts(case_id)
    candidates = tuple(
        nucleus
        for nucleus in plan.nuclei
        if "semantic_role:retained_intention" in nucleus.semantic_frame.attribute_codes
    )
    assert candidates
    assert _classify(plan, candidates) == "retained_intention"


@pytest.mark.parametrize(
    "case_id",
    ("C", "I6-L01", "I6-L03", "I6-C01", "I6-C02", "I6-C03"),
)
def test_rr1_intention_case_selects_a_resolvable_retained_intention_target(
    case_id: str,
) -> None:
    plan, _spans, resolver, _sentence_plan = _artifacts(case_id)
    selected = tuple(
        item
        for item in plan.nuclei
        if item.nucleus_id in plan.response_plan.human_follow_target_ids
    )
    assert selected
    assert _classify(plan, selected) == "retained_intention"
    assert all(
        item.semantic_frame.modality in {"wish", "intention"}
        or "semantic_role:retained_intention"
        in item.semantic_frame.attribute_codes
        for item in selected
    )
    assert resolver.unresolved_ids(
        span_id
        for item in selected
        for span_id in item.source_span_ids
    ) == ()


def test_rr1_l02_follow_target_is_the_explicit_next_intention_and_resolves() -> None:
    plan, spans, resolver, _sentence_plan = _artifacts("I6-L02")
    expected_ids = _nucleus_ids_containing(plan, spans, "境界だけ短く伝えるつもり")
    selected_ids = set(plan.response_plan.human_follow_target_ids)
    assert selected_ids
    assert selected_ids <= expected_ids
    assert all(
        "semantic_role:retained_intention"
        in next(item for item in plan.nuclei if item.nucleus_id == nucleus_id).semantic_frame.attribute_codes
        for nucleus_id in selected_ids
    )
    selected_nuclei = tuple(item for item in plan.nuclei if item.nucleus_id in selected_ids)
    assert _classify(plan, selected_nuclei) == "retained_intention"
    assert resolver.unresolved_ids(
        span_id
        for item in selected_nuclei
        for span_id in item.source_span_ids
    ) == ()


def test_rr1_role_classifier_is_semantic_under_anchor_change_and_fact_control() -> None:
    plan, _spans, _resolver, _sentence_plan = _artifacts("C")
    intention = next(
        item
        for item in plan.nuclei
        if "semantic_role:retained_intention" in item.semantic_frame.attribute_codes
    )
    renamed_anchor = replace(intention, surface_anchor_ids=("surface_anchor:metamorphic_target",))
    assert _classify(plan, (renamed_anchor,)) == "retained_intention"

    fact_frame = replace(
        intention.semantic_frame,
        modality="fact",
        polarity="neutral",
        attribute_codes=tuple(
            code
            for code in intention.semantic_frame.attribute_codes
            if code
            not in {
                "operator:wish",
                "operator:positive_change",
                "operator:change",
                "semantic_role:retained_intention",
                "semantic_role:current_change",
            }
        ),
    )
    fact_control = replace(intention, kind="event", semantic_frame=fact_frame)
    assert _classify(plan, (fact_control,)) != "retained_intention"


def test_rr1_role_classifier_keeps_action_and_genuine_change_controls_distinct() -> None:
    plan, _spans, _resolver, _sentence_plan = _artifacts("I6-L02")
    action = next(item for item in plan.nuclei if item.kind == "action")
    assert _classify(plan, (action,)) == "concrete_effort"

    change_frame = replace(
        action.semantic_frame,
        modality="fact",
        polarity="positive",
        attribute_codes=("semantic_role:current_change",),
    )
    change = replace(action, kind="change", semantic_frame=change_frame)
    assert _classify(plan, (change,)) == "valued_change"


@pytest.mark.parametrize(
    ("case_id", "expected_role"),
    (
        ("D", "protective_counterdirection"),
        ("I6-D01", "protective_counterdirection"),
        ("I6-D02", "help_seeking_preserved"),
        ("I6-D03", "help_seeking_preserved"),
    ),
)
def test_rr1_self_denial_priority_remains_protective(case_id: str, expected_role: str) -> None:
    plan, _spans, _resolver, _sentence_plan = _artifacts(case_id)
    selected = tuple(
        item
        for item in plan.nuclei
        if item.nucleus_id in plan.response_plan.human_follow_target_ids
    )
    assert selected
    assert _classify(plan, selected) == expected_role


def test_rr1_help_seeking_removed_control_does_not_keep_help_role() -> None:
    plan, _spans, _resolver, _sentence_plan = _artifacts("I6-D02")
    target = next(
        item
        for item in plan.nuclei
        if item.nucleus_id in plan.response_plan.human_follow_target_ids
    )
    without_help = replace(
        target,
        semantic_frame=replace(
            target.semantic_frame,
            attribute_codes=tuple(
                code
                for code in target.semantic_frame.attribute_codes
                if code != "operator:help_seeking"
            ),
        ),
    )
    assert _classify(plan, (without_help,)) != "help_seeking_preserved"


@pytest.mark.parametrize(
    ("case_id", "relation_type", "expected_surface_role"),
    (
        ("I6-L01", "preserves_despite", "burden_or_constraint_with_progress"),
        ("I6-L03", "preserves_despite", "provisional_evaluation_to_counterevidence"),
        ("I6-C01", "preserves_despite", "comparison_to_counterevidence"),
        ("I6-C03", "preserves_despite", "comparison_to_counterevidence"),
        ("I6-C02", "contrast", "coexisting_comparison_and_evidence"),
    ),
)
def test_rr1_relation_lines_expose_endpoint_semantic_surface_role(
    case_id: str,
    relation_type: str,
    expected_surface_role: str,
) -> None:
    plan, _spans, _resolver, sentence_plan = _artifacts(case_id)
    relation_ids = {
        item.relation_id
        for item in plan.relations
        if item.type == relation_type and item.retention in {"required", "should"}
    }
    assert relation_ids
    relation_lines = tuple(
        line
        for line in sentence_plan.lines
        if relation_ids.intersection(line.binding.relation_ids)
    )
    assert relation_lines
    assert any(
        f"relation_surface_role:{expected_surface_role}"
        in line.binding.functional_atom_ids
        for line in relation_lines
    )


def test_rr1_a_anchor_is_one_delivery_unit_without_repeated_observation_opening() -> None:
    _plan, _spans, _resolver, sentence_plan = _artifacts("A")
    occurrences: dict[str, list[object]] = {}
    for line in sentence_plan.lines:
        for nucleus_id in line.binding.nucleus_ids:
            occurrences.setdefault(nucleus_id, []).append(line)
    duplicated = {
        nucleus_id: lines
        for nucleus_id, lines in occurrences.items()
        if len(lines) > 1
        and not any(
            line.binding.line_role == "fact_boundary"
            or "safety_support_owner" in line.binding.functional_atom_ids
            for line in lines
        )
    }
    assert duplicated == {}

    observation_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role in {"primary_observation", "supporting_observation"}
    )
    assert all(
        left.surface_function != right.surface_function
        for left, right in zip(observation_lines, observation_lines[1:])
    )


def test_rr1_b_dependent_fragments_are_planned_as_one_complete_clause_unit() -> None:
    _plan, _spans, _resolver, sentence_plan = _artifacts("B")
    atoms = {
        atom
        for line in sentence_plan.lines
        for atom in line.binding.functional_atom_ids
    }
    assert "surface_unit:complete_clause" in atoms
    assert "dependency:quotative_continuation" in atoms


def test_rr1_gate0_decision_requires_explicit_validation_evidence_contract() -> None:
    evidence_type = getattr(gate0_boundary, "Gate0ValidationEvidence", None)
    assert evidence_type is not None
    fields = set(getattr(evidence_type, "__dataclass_fields__", {}))
    assert {
        "source_snapshot_fingerprint",
        "targeted_suites_green",
        "safety_public_contract_green",
        "rn_contract_green",
        "full_collect_success",
        "collected_test_count",
        "collection_error_refs",
        "full_backend_green",
        "unclassified_failure_refs",
    } <= fields
    parameters = set(inspect.signature(gate0_boundary.build_gate0_local_decision).parameters)
    assert "validation_evidence" in parameters


def test_rr1_file_contains_no_exact_completed_body_assertion() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(isinstance(op, ast.Eq) for op in node.ops):
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
