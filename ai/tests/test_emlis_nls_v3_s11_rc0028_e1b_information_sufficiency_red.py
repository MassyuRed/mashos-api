# -*- coding: utf-8 -*-
from __future__ import annotations

"""E1b RED: prove rc0028 upstream information-sufficiency boundaries.

These tests are intentionally RED against baseline ``50f80a4f``.  They do
not authorize a renderer, Matcher, Gate, frozen-owner, or production change.
Failure messages contain only closed diagnostic codes; source bodies stay in
the request-local resolver and are not copied into receipts.
"""

from dataclasses import replace
import json

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_lexical_role_experiment_snapshot_v3 import (
    build_grounded_lexical_role_experiment_snapshot,
    grounded_lexical_role_experiment_snapshot_material,
    validate_grounded_lexical_role_experiment_snapshot,
)
from emlis_ai_grounded_lexical_role_witness_v3 import (
    GroundedLexicalRoleError,
    build_grounded_lexical_role_witness,
    grounded_lexical_role_witness_material,
    validate_grounded_lexical_role_witness,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    build_grounded_semantic_restatement_witness,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_observation_stage_context_v3 import (
    build_observation_stage_context,
)
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import build_emlis_safety_triage_decision


def _input(thought_text: str) -> dict[str, object]:
    return {
        "thought_text": thought_text,
        "action_text": "",
        "emotions": [],
        "categories": [],
    }


def _plan_and_resolver(current_input: dict[str, object]):
    normalized = normalize_emlis_current_input(dict(current_input))
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(
        spans,
        current_input=normalized,
    )
    reports = tuple(run_perspective_observers(spans))
    board = build_perspective_board(
        evidence_spans=spans,
        reports=reports,
    )
    graph = integrate_perspective_board(board=board)
    safety = build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=graph,
        evidence_spans=spans,
    )
    plan = build_grounded_observation_plan(
        normalized,
        evidence_spans=spans,
        reports=reports,
        board=board,
        graph=graph,
        safety_decision=safety,
    )
    return normalized, plan, resolver


def test_rc0028_e1b_cross_span_relation_owner_closure_is_lossless() -> None:
    samples = (
        (
            "準備は進んだ。でも、結論はまだ決められない。",
            "contrast",
        ),
        (
            "昨日は記録を読み返した。今日は次の手順を決めた。",
            "shift_from_to",
        ),
        (
            "余裕は残っている。同時に、慎重さも残っている。",
            "coexistence",
        ),
    )
    issues: list[str] = []
    for current_text, expected_type in samples:
        _normalized, plan, resolver = _plan_and_resolver(
            _input(current_text)
        )
        required = frozenset(
            plan.coverage_requirements.required_relation_ids
        )
        matching = tuple(
            row
            for row in plan.relations
            if row.relation_id in required
            and row.type == expected_type
            and row.grounding_kind == "user_stated_relation"
            and len(row.source_span_ids) > 1
        )
        if len(matching) != 1:
            issues.append(
                "E1B_CROSS_SPAN_"
                + expected_type.upper()
                + "_AUTHORITY_MISSING"
            )
            continue

        relation = matching[0]
        witness = build_grounded_lexical_role_witness(plan, resolver)
        bindings = tuple(
            row
            for row in getattr(
                witness,
                "relation_endpoint_bindings",
                (),
            )
            if getattr(row, "relation_id", "") == relation.relation_id
        )
        direction = (
            "bidirectional"
            if relation.type == "coexistence"
            else "source_to_target"
        )
        expected = {
            ("from", relation.from_nucleus_id, direction),
            ("to", relation.to_nucleus_id, direction),
        }
        actual = {
            (
                getattr(row, "relation_endpoint_role", ""),
                getattr(row, "source_owner_id", ""),
                getattr(row, "relation_direction", ""),
            )
            for row in bindings
        }
        if actual != expected:
            issues.append(
                "E1B_CROSS_SPAN_"
                + expected_type.upper()
                + "_BINDING_MISSING"
            )

    assert tuple(issues) == ()


def test_rc0028_e1b_overlap_retains_all_nested_constructions() -> None:
    _normalized, plan, resolver = _plan_and_resolver(
        _input("安心したのに、後で迷いが残ったのはなぜだろう。")
    )
    restatement = build_grounded_semantic_restatement_witness(
        plan,
        resolver,
    )
    assert len(restatement.semantic_units) == 2
    assert len(restatement.semantic_links) == 1
    assert restatement.explicit_unknowns

    witness = build_grounded_lexical_role_witness(plan, resolver)
    issues: list[str] = []
    if "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP" in {
        reason for _owner_id, reason in witness.unresolved_owner_reasons
    }:
        issues.append("E1B_OVERLAP_STILL_UNRESOLVED")

    construction_codes = {
        row.construction_code for row in witness.facets
    }
    if not {
        "explicit_contrast",
        "ordered_sequence",
    } <= construction_codes:
        issues.append("E1B_OVERLAP_CONSTRUCTION_LOSS")

    adapted_owner_ids = frozenset(
        getattr(witness, "adapted_source_owner_ids", ())
    )
    if not {
        row.unit_id for row in restatement.semantic_units
    } <= adapted_owner_ids:
        issues.append("E1B_OVERLAP_OWNER_ALIAS_MISSING")

    semantic_link_ids = {
        getattr(row, "source_semantic_link_id", "")
        for row in getattr(witness, "semantic_link_bindings", ())
    }
    if not {
        row.link_id for row in restatement.semantic_links
    } <= semantic_link_ids:
        issues.append("E1B_OVERLAP_LINK_BINDING_MISSING")

    explicit_unknown_ids = {
        getattr(row, "source_unknown_id", "")
        for row in getattr(witness, "explicit_unknown_bindings", ())
    }
    if not {
        row.unknown_id for row in restatement.explicit_unknowns
    } <= explicit_unknown_ids:
        issues.append("E1B_OVERLAP_UNKNOWN_BINDING_MISSING")

    role_owner_pairs = [
        (
            getattr(row, "source_owner_id", row.owner_nucleus_id),
            row.lexical_role_kind,
        )
        for row in witness.facets
    ]
    if len(role_owner_pairs) != len(set(role_owner_pairs)):
        issues.append("E1B_OVERLAP_DUPLICATE_ROLE_FOR_OWNER")
    if len(witness.facets) > witness.resource_bound:
        issues.append("E1B_OVERLAP_RESOURCE_BOUND_EXCEEDED")

    assert tuple(issues) == ()


def test_rc0028_e1b_relation_endpoint_direction_mutation_fails_closed() -> None:
    _normalized, plan, resolver = _plan_and_resolver(
        _input("準備は進んだ。でも、結論はまだ決められない。")
    )
    relation = next(
        row
        for row in plan.relations
        if row.type == "contrast" and row.retention == "required"
    )
    witness = build_grounded_lexical_role_witness(plan, resolver)
    rows = tuple(
        row
        for row in getattr(witness, "relation_endpoint_bindings", ())
        if getattr(row, "relation_id", "") == relation.relation_id
    )
    assert len(rows) == 2, "E1B_RELATION_ENDPOINT_BINDINGS_MISSING"

    original = rows[0]
    forged_row = replace(
        original,
        source_owner_id=(
            relation.to_nucleus_id
            if original.source_owner_id == relation.from_nucleus_id
            else relation.from_nucleus_id
        ),
        relation_direction=(
            "bidirectional"
            if original.relation_direction == "source_to_target"
            else "source_to_target"
        ),
    )
    all_rows = tuple(
        forged_row if row is original else row
        for row in witness.relation_endpoint_bindings
    )
    forged = replace(witness, relation_endpoint_bindings=all_rows)
    assert "LEXICAL_ROLE_RELATION_ENDPOINT_BINDINGS_MISMATCH" in (
        validate_grounded_lexical_role_witness(
            forged,
            plan=plan,
            resolver=resolver,
        )
    )
    with pytest.raises(
        GroundedLexicalRoleError,
        match="LEXICAL_ROLE_RELATION_ENDPOINT_BINDINGS_MISMATCH",
    ):
        grounded_lexical_role_witness_material(
            forged,
            plan=plan,
            resolver=resolver,
        )


def test_rc0028_e1b_explicit_unknown_has_exact_owner_binding() -> None:
    _normalized, plan, resolver = _plan_and_resolver(
        _input("結果はまだ分からない。")
    )
    restatement = build_grounded_semantic_restatement_witness(
        plan,
        resolver,
    )
    assert len(restatement.explicit_unknowns) == 1
    source_unknown = restatement.explicit_unknowns[0]
    assert source_unknown.dimension == "explicit_unverbalized_unknown"

    witness = build_grounded_lexical_role_witness(plan, resolver)
    bindings = tuple(
        row
        for row in getattr(witness, "explicit_unknown_bindings", ())
        if getattr(row, "source_unknown_id", "")
        == source_unknown.unknown_id
    )
    assert len(bindings) == 1, "E1B_EXPLICIT_UNKNOWN_BINDING_MISSING"
    binding = bindings[0]
    assert binding.dimension == source_unknown.dimension
    assert binding.source_span_id == source_unknown.source_span_id
    assert tuple(binding.affected_source_owner_ids) == (
        source_unknown.affected_unit_ids
    )
    assert binding.lexical_role_kind == "unknown_or_limit"

    forged_binding = replace(
        binding,
        dimension="explicit_invented_unknown",
    )
    all_rows = tuple(
        forged_binding if row is binding else row
        for row in witness.explicit_unknown_bindings
    )
    forged = replace(witness, explicit_unknown_bindings=all_rows)
    assert "LEXICAL_ROLE_EXPLICIT_UNKNOWN_BINDINGS_MISMATCH" in (
        validate_grounded_lexical_role_witness(
            forged,
            plan=plan,
            resolver=resolver,
        )
    )


def test_rc0028_e1b_facet_presence_cannot_self_certify_coverage() -> None:
    normalized, plan, resolver = _plan_and_resolver(
        _input("続けるか迷っている。")
    )
    restatement = build_grounded_semantic_restatement_witness(
        plan,
        resolver,
    )
    assert restatement.explicit_unknowns

    witness = build_grounded_lexical_role_witness(plan, resolver)
    facet_present = tuple(
        getattr(
            witness,
            "facet_present_required_nucleus_ids",
            getattr(witness, "covered_required_nucleus_ids", ()),
        )
    )
    assert facet_present
    issues: list[str] = []
    if hasattr(witness, "covered_required_nucleus_ids"):
        issues.append("E1B_COVERED_NAME_OVERSTATES_FACET_PRESENCE")
    if not getattr(witness, "facet_present_required_nucleus_ids", ()):
        issues.append("E1B_FACET_PRESENCE_PARTITION_MISSING")
    if getattr(witness, "semantic_coverage_authority", None) != "none":
        issues.append("E1B_SEMANTIC_COVERAGE_AUTHORITY_NOT_DENIED")

    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=normalized,
    )
    experiment = build_grounded_lexical_role_experiment_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    if getattr(experiment, "semantic_coverage_authorized", None) is not False:
        issues.append("E1B_SNAPSHOT_COVERAGE_AUTHORITY_NOT_DENIED")
    material = grounded_lexical_role_experiment_snapshot_material(
        experiment
    )
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)
    if "covered_required_nucleus_ids" in encoded:
        issues.append("E1B_COVERED_NAME_PROPAGATED_TO_SNAPSHOT")

    if hasattr(experiment, "semantic_coverage_authorized"):
        forged = replace(
            experiment,
            semantic_coverage_authorized=True,
        )
        if "LEXICAL_ROLE_SEMANTIC_COVERAGE_SELF_CLAIM_FORBIDDEN" not in (
            validate_grounded_lexical_role_experiment_snapshot(forged)
        ):
            issues.append("E1B_COVERAGE_SELF_CLAIM_NOT_REJECTED")
    else:
        issues.append("E1B_COVERAGE_SELF_CLAIM_GUARD_MISSING")

    assert tuple(issues) == ()
