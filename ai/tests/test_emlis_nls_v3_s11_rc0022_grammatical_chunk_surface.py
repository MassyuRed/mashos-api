# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

import emlis_ai_step11_natural_surface_matcher_v3 as matcher
import emlis_ai_step11_natural_surface_v3 as surface
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3
from emlis_ai_step11_surface_catalog_v3 import (
    STEP11_SURFACE_CATALOG,
    validate_step11_surface_catalog,
)


def _unit(
    index: int,
    phase: str,
    *,
    introduced: tuple[int, ...] = (),
    used: tuple[int, ...] = (),
) -> surface.Step11SurfaceRealizationUnit:
    required = tuple(
        ordinal for ordinal in used if ordinal not in set(introduced)
    )
    return surface.Step11SurfaceRealizationUnit(
        semantic_unit_id=f"unit-{index}",
        section_role="observation",
        phase=phase,
        owner_obligation_ids=(f"obligation-{index}",),
        owner_anchor_ids=(),
        owner_nucleus_ids=(),
        owner_relation_ids=(),
        owner_mixed_emotion_requirement_ids=(),
        introduced_reference_ordinals=introduced,
        used_reference_ordinals=used,
        required_reference_ordinals=required,
        visible_reference_count=len(used),
        body_free_complexity_weight=max(1, len(used)),
        parent_sentence_group_ids=("group-1", "group-2"),
        assigned_sentence_group_id="",
        assigned_grammatical_chunk_ordinal=0,
        source_order=index,
    )


def _dense_units() -> tuple[surface.Step11SurfaceRealizationUnit, ...]:
    return (
        _unit(0, "source_introduction", introduced=(1,), used=(1,)),
        _unit(1, "source_introduction", introduced=(2,), used=(2,)),
        _unit(2, "source_introduction", introduced=(3,), used=(3,)),
        _unit(
            3,
            "source_introduction",
            introduced=(4, 5),
            used=(4, 5),
        ),
        _unit(4, "relation", used=(1, 2)),
        _unit(5, "unknown_boundary", used=(1,)),
        _unit(6, "unknown_boundary", used=(2,)),
    )


def test_rc0027_retains_chunk_and_historical_typed_reception_grammar() -> None:
    grammar = STEP11_SURFACE_CATALOG["group_grammar"]
    reception = STEP11_SURFACE_CATALOG["reception_forms"][
        "typed_reference_grammar"
    ]

    assert validate_step11_surface_catalog() == ()
    assert surface.STEP11_CANDIDATE_VERSION_ID == "nls_v3_rc_0027"
    assert surface.STEP11_SURFACE_AST_SCHEMA.endswith(".v8")
    assert grammar["maximum_visible_clauses_per_grammatical_sentence"] == 2
    assert grammar["maximum_repeated_joiner_per_group"] == 2
    assert grammar["grammatical_chunk_separator"] == "。"
    assert reception["generic_relation_only_forbidden"] is True
    assert reception["literal_quotes_forbidden"] is True
    assert reception["parser_visible_delimiters"] == {
        "open": "〔",
        "close": "〕",
    }
    assert all(
        "{from_ref}" in row and "{to_ref}" in row
        for rows in reception["content_forms"]["relation"].values()
        for row in rows
    )
    assert all(
        all(token in row for token in ("{from_ref}", "{to_ref}", "{action_ref}"))
        for rows in reception["content_forms"]["relation_action"].values()
        for row in rows
    )


def test_dense_units_are_committed_to_bounded_grammatical_chunks() -> None:
    plan = surface.build_step11_surface_realization_plan(
        _dense_units(),
        observation_group_ids=("group-1", "group-2"),
        reception_group_ids=(),
    )

    assert plan.schema_version.endswith(".rc0027.v1")
    assert plan.peak_observation_clause_count == 4
    assert plan.peak_grammatical_clause_count <= 2
    assert plan.peak_grammatical_complexity_load <= 4
    assert plan.peak_group_repeated_joiner_count <= 2
    for group_id in plan.observation_sentence_group_ids:
        rows = tuple(
            row
            for row in plan.units
            if row.assigned_sentence_group_id == group_id
        )
        assert rows
        assert tuple(row.assigned_grammatical_chunk_ordinal for row in rows)
        for chunk_ordinal in {
            row.assigned_grammatical_chunk_ordinal for row in rows
        }:
            chunk = tuple(
                row
                for row in rows
                if row.assigned_grammatical_chunk_ordinal == chunk_ordinal
            )
            assert len(chunk) <= 2
            assert sum(row.body_free_complexity_weight for row in chunk) <= 4

    second_unknown = next(
        row for row in plan.units if row.semantic_unit_id == "unit-6"
    )
    assert second_unknown.used_reference_ordinals == (2,)
    assert second_unknown.required_reference_ordinals == (2,)
    assert second_unknown.visible_reference_count == 1


def test_canonical_chunk_joiner_keeps_one_discourse_group_line() -> None:
    rendered = surface._join_group_clauses(
        ("alpha", "beta", "gamma", "delta"),
        grammatical_chunk_ordinals=(1, 1, 2, 2),
    )

    assert rendered == "alpha、また、beta。gamma、また、delta。"
    assert "\n" not in rendered
    assert rendered.count("、また、") == 2
    assert all(
        grammatical_sentence.count("、また、") <= 1
        for grammatical_sentence in rendered.rstrip("。").split("。")
    )


@pytest.mark.parametrize(
    "tamper",
    ("missing_used_ref", "false_visible_count", "preassigned_chunk"),
)
def test_used_reference_and_chunk_tampering_fail_closed(tamper: str) -> None:
    units = list(_dense_units())
    target = units[-1]
    if tamper == "missing_used_ref":
        units[-1] = replace(target, used_reference_ordinals=())
    elif tamper == "false_visible_count":
        units[-1] = replace(target, visible_reference_count=0)
    else:
        units[-1] = replace(target, assigned_grammatical_chunk_ordinal=1)

    with pytest.raises(surface.Step11NaturalSurfaceError) as exc_info:
        surface.build_step11_surface_realization_plan(
            tuple(units),
            observation_group_ids=("group-1", "group-2"),
            reception_group_ids=(),
        )
    assert exc_info.value.code in {
        "STEP11_SURFACE_PLAN_REFERENCE_ORDER_INVALID",
        "STEP11_SURFACE_PLAN_UNIT_INVALID",
    }


def test_chunk_assignment_is_part_of_plan_identity() -> None:
    plan = surface.build_step11_surface_realization_plan(
        _dense_units(),
        observation_group_ids=("group-1", "group-2"),
        reception_group_ids=(),
    )
    first = plan.units[0]
    forged = replace(
        plan,
        units=(
            replace(
                first,
                assigned_grammatical_chunk_ordinal=(
                    first.assigned_grammatical_chunk_ordinal + 1
                ),
            ),
            *plan.units[1:],
        ),
    )

    assert artifact_sha256(
        surface.step11_surface_realization_plan_material(
            forged, include_id=False
        )
    ) != artifact_sha256(
        surface.step11_surface_realization_plan_material(
            plan, include_id=False
        )
    )


@pytest.fixture(scope="module")
def dense_generic_execution():
    return execute_step11_offline_v3(
        {
            "thought_text": (
                "企画を続けるか決められない。"
                "それとは別に、引っ越しを考える時期も決められない。"
            ),
            "action_text": (
                "二つを混同しないよう、判断材料を別々のメモに書いている。"
            ),
            "emotions": [
                {"type": "喜び", "strength": "weak"},
                {"type": "不安", "strength": "strong"},
            ],
            "categories": ["生活", "仕事"],
        },
        candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="9" * 64,
    )


def test_dense_generic_forward_surface_preserves_depth_with_chunking(
    dense_generic_execution,
) -> None:
    assert dense_generic_execution.status == "selected"
    candidate = dense_generic_execution.selected_candidate
    assert candidate is not None
    plan = candidate.surface_ast.surface_realization_plan
    assert plan is not None
    text = candidate.final_utf8_bytes.decode("utf-8")
    observation = text.split("見えたこと：\n", 1)[1].split(
        "\n\nEmlisから：\n", 1
    )[0]
    lines = observation.split("\n")

    assert len(lines) == len(plan.observation_sentence_group_ids)
    assert all(line.count("、また、") <= 2 for line in lines)
    assert all(
        grammatical_sentence.count("、また、") <= 1
        for line in lines
        for grammatical_sentence in line.rstrip("。").split("。")
    )
    assert all(
        set(row.introduced_reference_ordinals)
        <= set(row.used_reference_ordinals)
        and set(row.required_reference_ordinals)
        == set(row.used_reference_ordinals)
        - set(row.introduced_reference_ordinals)
        for row in plan.units
    )


def test_dense_generic_chunk_assignment_tamper_fails_ast_recompute(
    dense_generic_execution,
) -> None:
    candidate = dense_generic_execution.selected_candidate
    assert candidate is not None
    ast = candidate.surface_ast
    plan = ast.surface_realization_plan
    assert plan is not None
    target = next(row for row in plan.units if row.section_role == "observation")
    forged_ast = replace(
        ast,
        surface_realization_plan=replace(
            plan,
            units=tuple(
                replace(
                    row,
                    assigned_grammatical_chunk_ordinal=(
                        row.assigned_grammatical_chunk_ordinal + 1
                    ),
                )
                if row.semantic_unit_id == target.semantic_unit_id
                else row
                for row in plan.units
            ),
        ),
    )

    issues = surface.validate_step11_surface_ast(
        forged_ast,
        discourse_plan=candidate.discourse_plan,
        inventory_result=dense_generic_execution.inventory_result,
        content_plan=dense_generic_execution.content_plan,
        current_input=dense_generic_execution.projected_current_input,
    )
    assert "STEP11_SURFACE_REALIZATION_PLAN_INVALID" in issues


def _cycle001_input(case_id: str) -> dict[str, object]:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "emlis_nls_v3"
        / "generated"
        / "batch_001.jsonl"
    )
    for line in fixture.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("case_id") == case_id:
            return dict(row["input"])
    raise AssertionError(f"missing fixture: {case_id}")


@pytest.fixture(scope="module")
def rc0022_case0035_execution():
    return execute_step11_offline_v3(
        _cycle001_input("nls3s_b001_0035"),
        candidate_version_id=surface.STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="8" * 64,
    )


def _match(execution, body: bytes):
    candidate = execution.selected_candidate
    assert candidate is not None
    witness = matcher.parse_step11_natural_surface(body)
    return witness, matcher.match_step11_natural_surface(
        witness,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=execution.projected_current_input,
    )


def test_rc0022_case0035_uses_visible_exact_owner_and_action_support(
    rc0022_case0035_execution,
) -> None:
    execution = rc0022_case0035_execution
    assert execution.status == "selected"
    body = execution.final_utf8_bytes
    assert body is not None
    text = body.decode("utf-8")
    assert "〔〔" not in text and "〕〕" not in text
    assert "〔1つ目の記述内容〕" in text
    assert "〔3つ目の行動〕" in text

    witness, binding = _match(execution, body)
    reception = tuple(
        row for row in witness.atoms if row.section_role == "reception"
    )
    assert binding.verified is True
    assert len(reception) == 1
    assert reception[0].form_id.startswith("reception:typed:")
    assert tuple(
        (row.reference_ordinal, row.endpoint_role)
        for row in reception[0].reception_antecedent_references
    ) == ((1, "proposition"), (3, "action"))
    reception_binding = next(
        row
        for row in binding.binding_rows
        if row.obligation_kind == "bound_emlis_reception"
    )
    assert (
        reception_binding.match_basis
        == "bound_reception_typed_referent_exact_source_owner"
    )


def test_rc0022_reception_owner_substitution_fails_closed(
    rc0022_case0035_execution,
) -> None:
    execution = rc0022_case0035_execution
    body = execution.final_utf8_bytes
    assert body is not None
    tampered = body.replace(
        "〔1つ目の記述内容〕".encode("utf-8"),
        "〔2つ目の記述内容〕".encode("utf-8"),
    )
    assert tampered != body

    _, binding = _match(execution, tampered)
    assert binding.verified is False
    assert {
        "S11_MATCH_RECEPTION_BINDING_UNRESOLVED",
        "S11_MATCH_RECEPTION_TARGET_SCOPE_STATUS_MISMATCH",
    } <= set(binding.issue_codes)
