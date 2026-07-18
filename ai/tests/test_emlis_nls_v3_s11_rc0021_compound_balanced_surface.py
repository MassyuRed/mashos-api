# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace

import pytest

import emlis_ai_step11_hard_gate_v3 as gate
import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
from emlis_ai_step11_cycle_evidence_v3 import (
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_planning_frontier_v3 import (
    STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_SCHEMA,
    STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_VERSION,
    STEP11_PLANNING_FRONTIER_SCHEMA,
    STEP11_PLANNING_FRONTIER_VERSION,
)
from emlis_ai_step11_runtime_adapter_v3 import (
    STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION,
    STEP11_RUNTIME_ADAPTER_VERSION,
    execute_step11_offline_v3,
)
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG


def _compound_body(*, positive: str = "喜び", negative: str = "不安") -> bytes:
    template = STEP11_SURFACE_CATALOG["mixed_emotion_compound_grammar"][
        "forms"
    ][0]
    observation = template.format(
        positive_ref="1つ目の感情",
        positive_literal=f"『{positive}』",
        negative_ref="2つ目の感情",
        negative_literal=f"『{negative}』",
    )
    return (
        "見えたこと：\n"
        + observation
        + "。\n\nEmlisから：\nEmlisは、その思いを、気に留めています。"
    ).encode("utf-8")


@pytest.fixture(scope="module")
def dense_generic_execution():
    execution = execute_step11_offline_v3(
        {
            "thought_text": (
                "少し安心した気持ちと、まだ心配な気持ちが同時にある。"
            ),
            "action_text": "予定をノートに書き出している。",
            "emotions": [
                {"type": "喜び", "strength": "medium"},
                {"type": "不安", "strength": "medium"},
            ],
            "categories": ["生活"],
        },
        candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="7" * 64,
    )
    assert execution.status == "selected"
    assert execution.selected_candidate is not None
    return execution


def test_rc0023_contract_retains_rc0021_balance_regression() -> None:
    assert STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID == (
        "nls_v3_rc_0021"
    )
    assert surface.STEP11_CANDIDATE_VERSION_ID == (
        STEP11_CURRENT_CANDIDATE_VERSION_ID
    )
    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0023"
    assert surface.STEP11_SURFACE_REALIZATION_PLAN_SCHEMA.endswith(
        ".rc0023.v1"
    )
    assert STEP11_SURFACE_CATALOG["candidate_version_id"] == (
        STEP11_CURRENT_CANDIDATE_VERSION_ID
    )
    assert STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_VERSION == (
        "nls_v3_rc_0021"
    )
    assert STEP11_HISTORICAL_RC0021_PLANNING_FRONTIER_SCHEMA.endswith(
        ".rc0021.v1"
    )
    assert STEP11_PLANNING_FRONTIER_VERSION == "nls_v3_rc_0023"
    assert STEP11_PLANNING_FRONTIER_SCHEMA.endswith(".rc0023.v1")
    assert STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION.endswith(
        ".rc0021.v1"
    )
    assert STEP11_RUNTIME_ADAPTER_VERSION.endswith(".rc0023.v1")
    assert STEP11_SURFACE_CATALOG["group_grammar"][
        "maximum_observation_clauses_per_sentence"
    ] == 4
    assert STEP11_SURFACE_CATALOG["group_grammar"][
        "maximum_repeated_joiner_per_sentence"
    ] == 2


def test_typed_mixed_emotion_compound_is_one_independent_atom() -> None:
    witness = matcher.parse_step11_natural_surface(_compound_body())
    compound = witness.atoms[0]

    assert compound.form_id.startswith("mixed_emotion_compound:")
    assert compound.claim_kinds == (
        "nucleus_notice",
        "mixed_emotion_relation",
    )
    assert compound.source_fragments == ("喜び", "不安")
    assert compound.compound_label_references == (
        matcher.Step11EndpointReference(1, "affect"),
        matcher.Step11EndpointReference(2, "affect"),
    )
    assert compound.relation_endpoint_references == (
        matcher.Step11EndpointReference(1, "affect"),
        matcher.Step11EndpointReference(2, "affect"),
    )
    assert len(witness.sentences[0].clause_atom_ids) == 1


@pytest.mark.parametrize(
    ("mutation", "issue"),
    (
        ("delete", "S11_MATCH_MIXED_EMOTION_COMPOUND_COVERAGE_MISMATCH"),
        ("swap", "S11_MATCH_MIXED_EMOTION_COMPOUND_ORDER_MISMATCH"),
        ("duplicate", "S11_MATCH_MIXED_EMOTION_COMPOUND_DUPLICATE"),
    ),
)
def test_compound_deletion_swap_and_duplicate_fail_closed(
    mutation: str,
    issue: str,
) -> None:
    atom = matcher.parse_step11_natural_surface(_compound_body()).atoms[0]
    expected = (
        matcher.Step11EndpointReference(1, "affect"),
        matcher.Step11EndpointReference(2, "affect"),
    )
    if mutation == "delete":
        atoms = ()
    elif mutation == "swap":
        atoms = (
            replace(
                atom,
                source_fragments=tuple(reversed(atom.source_fragments)),
                compound_label_references=tuple(
                    reversed(atom.compound_label_references)
                ),
            ),
        )
    else:
        atoms = (atom, replace(atom, atom_id=atom.atom_id + "x"))

    issues = matcher._independent_mixed_emotion_compound_issues(
        atoms,
        expected_positive_label="喜び",
        expected_negative_label="不安",
        expected_references=expected,
    )

    assert issue in issues


def test_density_and_reference_order_are_fail_closed() -> None:
    units = tuple(
        surface.Step11SurfaceRealizationUnit(
            semantic_unit_id=f"unit-{index}",
            section_role="observation",
            phase="source_introduction" if index < 2 else "unknown_boundary",
            owner_obligation_ids=(f"obligation-{index}",),
            owner_anchor_ids=(),
            owner_nucleus_ids=(),
            owner_relation_ids=(),
            owner_mixed_emotion_requirement_ids=(),
            introduced_reference_ordinals=(index + 1,) if index < 2 else (),
            used_reference_ordinals=(
                (index + 1,) if index < 2 else (1,)
            ),
            required_reference_ordinals=(1,) if index >= 2 else (),
            visible_reference_count=1,
            body_free_complexity_weight=1,
            parent_sentence_group_ids=("group-1",),
            assigned_sentence_group_id="",
            assigned_grammatical_chunk_ordinal=0,
            source_order=index,
        )
        for index in range(5)
    )

    plan = surface.build_step11_surface_realization_plan(
        units,
        observation_group_ids=("group-1", "group-2"),
        reception_group_ids=(),
    )

    assert tuple(row.assigned_sentence_group_id for row in plan.units) == (
        "group-1",
        "group-1",
        "group-1",
        "group-2",
        "group-2",
    )
    assert plan.peak_observation_clause_count == 3
    with pytest.raises(surface.Step11NaturalSurfaceError) as exc_info:
        surface.build_step11_surface_realization_plan(
            units,
            observation_group_ids=("group-1",),
            reception_group_ids=(),
        )
    assert exc_info.value.code == "STEP11_SURFACE_PLAN_DENSITY_UNSATISFIABLE"

    bad_order = (
        replace(
            units[2],
            source_order=0,
        ),
        replace(units[0], source_order=1),
    )
    with pytest.raises(surface.Step11NaturalSurfaceError) as exc_info:
        surface.build_step11_surface_realization_plan(
            bad_order,
            observation_group_ids=("group-1",),
            reception_group_ids=(),
        )
    assert exc_info.value.code == "STEP11_SURFACE_PLAN_REFERENCE_ORDER_INVALID"


def test_dense_generic_runtime_commits_balanced_plan(
    dense_generic_execution,
) -> None:
    candidate = dense_generic_execution.selected_candidate
    witness = matcher.parse_step11_natural_surface(
        candidate.final_utf8_bytes
    )

    assert max(len(row.clause_atom_ids) for row in witness.sentences) <= 4
    assert sum(
        row.form_id.startswith("mixed_emotion_compound:")
        for row in witness.atoms
    ) == 1
    assert candidate.surface_ast.surface_realization_plan is not None
    assert candidate.surface_ast.surface_realization_plan.body_free is True


@pytest.mark.parametrize("tamper", ("missing", "assignment"))
def test_ast_realization_plan_missing_or_tampered_fails_recompute(
    dense_generic_execution,
    tamper: str,
) -> None:
    candidate = dense_generic_execution.selected_candidate
    ast = candidate.surface_ast
    if tamper == "missing":
        forged = replace(ast, surface_realization_plan=None)
    else:
        plan = ast.surface_realization_plan
        assert plan is not None
        first = plan.units[0]
        other_group = next(
            group_id
            for group_id in plan.observation_sentence_group_ids
            if group_id != first.assigned_sentence_group_id
        )
        forged_plan = replace(
            plan,
            units=(
                replace(first, assigned_sentence_group_id=other_group),
                *plan.units[1:],
            ),
        )
        forged = replace(ast, surface_realization_plan=forged_plan)

    issues = surface.validate_step11_surface_ast(
        forged,
        discourse_plan=candidate.discourse_plan,
        inventory_result=dense_generic_execution.inventory_result,
        content_plan=dense_generic_execution.content_plan,
        current_input=dense_generic_execution.projected_current_input,
    )

    assert "STEP11_SURFACE_REALIZATION_PLAN_INVALID" in issues


def test_selector_quality_prefers_lower_peak_then_lower_repetition() -> None:
    assert gate._surface_quality_key((3, 3, 9, 2)) < gate._surface_quality_key(
        (4, 1, 2, 1)
    )
    assert gate._surface_quality_key((3, 2, 9, 2)) < gate._surface_quality_key(
        (3, 3, 2, 1)
    )


def test_hard_gate_density_rejects_more_than_four_clauses() -> None:
    body = (
        "見えたこと：\n"
        "aがあり、bがあり、cがあり、dがあり、eがあります。\n\n"
        "Emlisから：\nEmlisは、その思いを、気に留めています。"
    ).encode("utf-8")
    witness = matcher.Step11ParsedSurfaceWitness(
        schema_version=matcher.STEP11_PARSED_WITNESS_SCHEMA,
        surface_catalog_sha256="0" * 64,
        body_sha256="0" * 64,
        atoms=(),
        observation_atom_count=5,
        reception_atom_count=1,
        body_free_export_allowed=False,
        sentences=(
            matcher.Step11ParsedSentence(
                sentence_ordinal=1,
                section_role="observation",
                clause_atom_ids=("a", "b", "c", "d", "e"),
                byte_start=0,
                byte_end=len(body),
            ),
        ),
    )

    assert gate._surface_density_green(body, witness) is False
