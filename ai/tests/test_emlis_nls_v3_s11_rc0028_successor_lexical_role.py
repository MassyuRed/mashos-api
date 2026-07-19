# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED/GREEN contract for the rc0028 lexical-role successor.

The successor is experiment-only.  It must preserve the frozen Plan and
semantic-restatement owners, expose no semantic-coverage self-claim, and
project the relation/construction authority without raw source material.
"""

from dataclasses import replace
import importlib
import json

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_observation_semantic_restatement_v3 import (
    build_grounded_semantic_restatement_witness,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import build_emlis_safety_triage_decision


def _owner():
    try:
        return importlib.import_module(
            "emlis_ai_grounded_lexical_role_witness_successor_v3"
        )
    except ModuleNotFoundError:
        pytest.fail(
            "rc0028 lexical-role successor is not implemented",
            pytrace=False,
        )


def _input(thought_text: str) -> dict[str, object]:
    return {
        "thought_text": thought_text,
        "action_text": "",
        "emotions": [],
        "categories": [],
    }


def _sources(current_input: dict[str, object]):
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


def test_rc0028_successor_exports_closed_v2_contract() -> None:
    owner = _owner()
    assert owner.GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_SCHEMA.endswith(
        ".rc0028.experiment.v2"
    )
    assert owner.GROUNDED_LEXICAL_ROLE_WITNESS_SUCCESSOR_ADAPTER_VERSION.endswith(
        ".20260719.v2"
    )
    assert owner.MAX_LEXICAL_ROLES_PER_REQUIRED_TEXT_NUCLEUS == 6
    assert owner.GroundedLexicalRoleFacetSuccessor.__module__ == owner.__name__
    assert owner.GroundedLexicalRoleWitnessSuccessor.__module__ == owner.__name__
    assert callable(owner.build_grounded_lexical_role_witness_successor)
    assert callable(owner.validate_grounded_lexical_role_witness_successor)
    assert callable(owner.grounded_lexical_role_witness_successor_material)


def test_rc0028_successor_overlap_is_lossless_by_construction_instance() -> None:
    owner = _owner()
    _normalized, plan, resolver = _sources(
        _input("安心したのに、後で迷いが残ったのはなぜだろう。")
    )
    restatement = build_grounded_semantic_restatement_witness(plan, resolver)
    witness = owner.build_grounded_lexical_role_witness_successor(
        plan,
        resolver,
    )

    assert owner.validate_grounded_lexical_role_witness_successor(
        witness,
        plan=plan,
        resolver=resolver,
    ) == ()
    assert {
        "explicit_contrast",
        "ordered_sequence",
    } <= {row.construction_code for row in witness.facets}
    assert {row.unit_id for row in restatement.semantic_units} <= set(
        witness.adapted_source_owner_ids
    )
    assert {row.link_id for row in restatement.semantic_links} == {
        row.source_semantic_link_id for row in witness.semantic_link_bindings
    }
    assert {row.unknown_id for row in restatement.explicit_unknowns} == {
        row.source_unknown_id for row in witness.explicit_unknown_bindings
    }
    pairs = [
        (row.source_owner_id, row.lexical_role_kind)
        for row in witness.facets
    ]
    assert len(pairs) == len(set(pairs))
    assert len(witness.facets) <= 6 * witness.required_text_parent_count
    assert "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP" not in {
        reason for _owner_id, reason in witness.unresolved_owner_reasons
    }


def test_rc0028_successor_relation_endpoint_mutations_fail_closed() -> None:
    owner = _owner()
    _normalized, plan, resolver = _sources(
        _input("準備は進んだ。でも、結論はまだ決められない。")
    )
    witness = owner.build_grounded_lexical_role_witness_successor(
        plan,
        resolver,
    )
    relation = next(
        row
        for row in witness.relation_authorities
        if row.effective_relation_type == "contrast"
        and row.source_retention == "required"
    )
    bindings = tuple(
        row
        for row in witness.relation_endpoint_bindings
        if row.relation_id == relation.experiment_relation_id
    )
    assert len(bindings) == 2
    assert {row.relation_endpoint_role for row in bindings} == {"from", "to"}

    first = bindings[0]
    other_owner = (
        relation.to_source_owner_id
        if first.source_owner_id == relation.from_source_owner_id
        else relation.from_source_owner_id
    )
    mutations = (
        replace(first, source_owner_id=other_owner),
        replace(
            first,
            relation_direction=(
                "bidirectional"
                if first.relation_direction == "source_to_target"
                else "source_to_target"
            ),
        ),
        replace(
            first,
            relation_endpoint_role=(
                "to" if first.relation_endpoint_role == "from" else "from"
            ),
        ),
    )
    for mutation in mutations:
        forged_rows = tuple(
            mutation if row is first else row
            for row in witness.relation_endpoint_bindings
        )
        forged = replace(witness, relation_endpoint_bindings=forged_rows)
        assert "LEXICAL_ROLE_RELATION_ENDPOINT_BINDINGS_MISMATCH" in (
            owner.validate_grounded_lexical_role_witness_successor(
                forged,
                plan=plan,
                resolver=resolver,
            )
        )


def test_rc0028_successor_explicit_unknown_is_exact_and_tamper_closed() -> None:
    owner = _owner()
    _normalized, plan, resolver = _sources(_input("結果はまだ分からない。"))
    restatement = build_grounded_semantic_restatement_witness(plan, resolver)
    witness = owner.build_grounded_lexical_role_witness_successor(
        plan,
        resolver,
    )
    assert len(restatement.explicit_unknowns) == 1
    source = restatement.explicit_unknowns[0]
    binding = next(
        row
        for row in witness.explicit_unknown_bindings
        if row.source_unknown_id == source.unknown_id
    )
    assert binding.dimension == source.dimension
    assert binding.source_span_id == source.source_span_id
    assert tuple(row.owner_id for row in binding.affected_source_owners) == (
        source.affected_unit_ids
    )
    assert binding.lexical_role_kind == "unknown_or_limit"

    forged_binding = replace(binding, dimension="explicit_invented_unknown")
    forged = replace(
        witness,
        explicit_unknown_bindings=tuple(
            forged_binding if row is binding else row
            for row in witness.explicit_unknown_bindings
        ),
    )
    assert "LEXICAL_ROLE_EXPLICIT_UNKNOWN_BINDINGS_MISMATCH" in (
        owner.validate_grounded_lexical_role_witness_successor(
            forged,
            plan=plan,
            resolver=resolver,
        )
    )


def test_rc0028_successor_facet_presence_is_not_semantic_coverage() -> None:
    owner = _owner()
    normalized, plan, resolver = _sources(_input("続けるか迷っている。"))
    witness = owner.build_grounded_lexical_role_witness_successor(
        plan,
        resolver,
    )
    required = {
        row.nucleus_id
        for row in plan.nuclei
        if row.nucleus_id in plan.coverage_requirements.required_nucleus_ids
        and set(row.source_fields) <= {"memo", "memo_action"}
    }
    assert set(witness.facet_present_required_nucleus_ids).isdisjoint(
        witness.facet_absent_required_nucleus_ids
    )
    assert set(witness.facet_present_required_nucleus_ids) | set(
        witness.facet_absent_required_nucleus_ids
    ) == required
    assert witness.semantic_coverage_authority == "none"
    assert not hasattr(witness, "covered_required_nucleus_ids")

    material = owner.grounded_lexical_role_witness_successor_material(
        witness,
        plan=plan,
        resolver=resolver,
    )
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert material["body_free"] is True
    assert "covered_required_nucleus_ids" not in encoded
    assert normalized["memo"] not in encoded
    assert "start_index" not in encoded
    assert "end_index" not in encoded


def test_rc0028_successor_witness_hash_and_partition_tamper_fail_closed() -> None:
    owner = _owner()
    _normalized, plan, resolver = _sources(_input("続けるか迷っている。"))
    witness = owner.build_grounded_lexical_role_witness_successor(
        plan,
        resolver,
    )
    mutations = (
        replace(witness, witness_sha256="0" * 64),
        replace(
            witness,
            facet_absent_required_nucleus_ids=(
                *witness.facet_absent_required_nucleus_ids,
                "nucleus:forged",
            ),
        ),
        replace(witness, semantic_coverage_authority="self_claimed"),
    )
    for forged in mutations:
        assert owner.validate_grounded_lexical_role_witness_successor(
            forged,
            plan=plan,
            resolver=resolver,
        )

