# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED contract for the rc0022 grouped, reference-typed surface.

The cases in this file intentionally exercise only common structure.  They do
not name a Cycle 001 case, read a sample oracle, or introduce a case-specific
rendering branch.
"""

from collections import Counter
from dataclasses import replace
from typing import Any

import pytest

from emlis_ai_step11_cycle_evidence_v3 import (
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
)
import emlis_ai_step11_natural_surface_matcher_v3 as matcher_module
from emlis_ai_step11_natural_surface_matcher_v3 import (
    match_step11_natural_surface,
    parse_step11_natural_surface,
)
from emlis_ai_step11_natural_surface_v3 import (
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_runtime_adapter_v3 import (
    STEP11_RUNTIME_ADAPTER_VERSION,
    execute_step11_offline_v3,
)
from emlis_ai_step11_semantic_overlay_v3 import (
    build_step11_semantic_overlay,
)
from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG


_RELATION_RICH_INPUT: dict[str, Any] = {
    "thought_text": (
        "協力して仕上げたものを褒められてうれしかった。"
        "でも、助けてもらった部分も大きく、自分だけの成果として"
        "受け取ってよいのか迷っている。"
    ),
    "action_text": (
        "自分が担った部分と、助けてもらった部分を分けてメモした。"
    ),
    "emotions": [
        {"type": "喜び", "strength": "medium"},
        {"type": "不安", "strength": "medium"},
    ],
    "categories": ["仕事", "人間関係"],
}


@pytest.fixture(scope="module")
def relation_rich_execution():
    execution = execute_step11_offline_v3(
        _RELATION_RICH_INPUT,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256="a" * 64,
    )
    assert execution.natural_candidates
    return execution


@pytest.fixture(scope="module")
def grouped_candidate(relation_rich_execution):
    candidates = tuple(
        candidate
        for candidate in relation_rich_execution.natural_candidates
        if any(
            group["section_role"] == "observation"
            and len(group["node_ids"]) > 1
            for group in candidate.discourse_plan["sentence_groups"]
        )
    )
    assert candidates, "relation-rich input must exercise clause integration"
    return candidates[0]


def _active_obligation_ids(content_plan: dict[str, Any]) -> frozenset[str]:
    return frozenset(
        row["obligation_id"]
        for row in content_plan["decisions"]
        if row["status"] in {"selected", "integrated_into"}
    )


def _physical_section_lines(body: bytes) -> dict[str, tuple[str, ...]]:
    text = body.decode("utf-8", errors="strict")
    labels = STEP11_SURFACE_CATALOG["labels"]
    observation_prefix = f"{labels['observation']}\n"
    reception_separator = f"\n\n{labels['reception']}\n"
    assert text.startswith(observation_prefix)
    assert text.count(reception_separator) == 1
    observation, reception = text[len(observation_prefix) :].split(
        reception_separator
    )
    return {
        "observation": tuple(observation.split("\n")),
        "reception": tuple(reception.split("\n")),
    }


def _match(relation_rich_execution, candidate, witness):
    return match_step11_natural_surface(
        witness,
        inventory_result=relation_rich_execution.inventory_result,
        content_plan=relation_rich_execution.content_plan,
        discourse_plan=candidate.discourse_plan,
        current_input=relation_rich_execution.projected_current_input,
    )


def _relation_atom(witness):
    rows = tuple(
        row
        for row in witness.atoms
        if row.section_role == "observation"
        and row.relation_type is not None
        and row.form_id.startswith("relation:")
    )
    assert rows
    return rows[0]


def test_rc0023_version_boundary_is_explicit_everywhere() -> None:
    assert STEP11_CANDIDATE_VERSION_ID == (
        STEP11_CURRENT_CANDIDATE_VERSION_ID
    )
    assert STEP11_SURFACE_CATALOG["candidate_version_id"] == (
        STEP11_CANDIDATE_VERSION_ID
    )
    assert matcher_module.STEP11_CANDIDATE_VERSION_ID == (
        STEP11_CANDIDATE_VERSION_ID
    )
    assert matcher_module.STEP11_SOURCE_UNKNOWN_ORACLE_SCHEMA.endswith(
        ".rc0023.v1"
    )
    assert STEP11_RUNTIME_ADAPTER_VERSION.endswith(".rc0023.v1")


def test_surface_frontier_is_limited_to_selected_or_integrated_obligations(
    relation_rich_execution,
) -> None:
    ledger_by_id = {
        row["obligation_id"]: row
        for row in relation_rich_execution.inventory_result.ledger[
            "obligations"
        ]
    }
    for candidate in relation_rich_execution.natural_candidates:
        overlay = build_step11_semantic_overlay(
            relation_rich_execution.projected_current_input,
            inventory_result=relation_rich_execution.inventory_result,
            content_plan=relation_rich_execution.content_plan,
            discourse_plan=candidate.discourse_plan,
        )
        active = frozenset(
            overlay.planning_frontier.participating_obligation_ids
        )
        assert frozenset(
            overlay.planning_frontier.base_active_obligation_ids
        ) == _active_obligation_ids(relation_rich_execution.content_plan)
        assert set(overlay.planning_frontier.integrated_obligation_ids) <= active
        allowed_nuclei = {
            nucleus_id
            for obligation_id in active
            for nucleus_id in ledger_by_id[obligation_id].get("nucleus_ids", [])
        }
        allowed_relations = {
            relation_id
            for obligation_id in active
            for relation_id in ledger_by_id[obligation_id].get("relation_ids", [])
        }
        allowed_unknowns = {
            unknown_id
            for obligation_id in active
            for unknown_id in ledger_by_id[obligation_id].get(
                "unknown_boundary_ids", []
            )
        }
        ast = candidate.surface_ast
        clause_ids = {
            clause.obligation_id
            for sentence in ast.sentences
            for clause in sentence.clauses
        }
        assert clause_ids <= active
        assert all(
            set(row.source_nucleus_ids) <= allowed_nuclei
            for row in ast.source_fragments
        )
        assert all(
            set(row.nucleus_ids) <= allowed_nuclei
            for row in ast.nucleus_surface_references
        )
        assert all(
            set(row.owner_obligation_ids) <= active
            and set(row.source_relation_ids) <= allowed_relations
            for row in ast.integrated_relations
        )
        assert all(
            set(row.owner_obligation_ids) <= active
            and set(row.source_unknown_ids) <= allowed_unknowns
            for row in ast.integrated_unknowns
        )


def test_final_physical_sentence_counts_equal_discourse_groups(
    relation_rich_execution,
) -> None:
    for candidate in relation_rich_execution.natural_candidates:
        physical = _physical_section_lines(
            candidate.rendered_surface.utf8_bytes
        )
        groups = Counter(
            row["section_role"]
            for row in candidate.discourse_plan["sentence_groups"]
        )
        assert len(physical["observation"]) == groups["observation"]
        assert len(physical["reception"]) == groups["reception"]


def test_one_discourse_group_can_round_trip_multiple_clause_atoms(
    grouped_candidate,
) -> None:
    witness = parse_step11_natural_surface(
        grouped_candidate.rendered_surface.utf8_bytes
    )
    grouped_sentences = tuple(
        row for row in witness.sentences if len(row.clause_atom_ids) > 1
    )

    assert len(witness.sentences) == len(
        grouped_candidate.discourse_plan["sentence_groups"]
    )
    assert grouped_sentences
    atom_ids = {row.atom_id for row in witness.atoms}
    assert all(
        set(row.clause_atom_ids) <= atom_ids for row in witness.sentences
    )


def test_relations_are_quote_free_typed_backward_references(
    grouped_candidate,
) -> None:
    body = grouped_candidate.rendered_surface.utf8_bytes
    witness = parse_step11_natural_surface(body)
    introduced = {
        row.introduced_reference.reference_ordinal: row
        for row in witness.atoms
        if row.introduced_reference is not None
    }
    relation_atoms = tuple(
        row
        for row in witness.atoms
        if row.relation_type is not None
        and row.form_id.startswith("relation:")
    )

    assert relation_atoms
    for atom in relation_atoms:
        assert atom.source_fragments == ()
        assert len(atom.relation_endpoint_references) == 2
        assert tuple(
            row.endpoint_role for row in atom.relation_endpoint_references
        ) == atom.relation_endpoint_roles
        for reference in atom.relation_endpoint_references:
            antecedent = introduced[reference.reference_ordinal]
            assert antecedent.byte_end <= atom.byte_start
        visible = body[atom.byte_start : atom.byte_end].decode("utf-8")
        assert not {"『", "』", "「", "」"} & set(visible)


def test_exact_source_range_is_introduced_only_once(grouped_candidate) -> None:
    ast = grouped_candidate.surface_ast
    source_ranges = tuple(
        (
            row.source_slot,
            row.source_field,
            row.source_ordinal,
            row.source_start,
            row.source_end,
            row.source_identity_key,
        )
        for row in ast.nucleus_surface_references
    )
    assert len(source_ranges) == len(set(source_ranges))

    witness = parse_step11_natural_surface(
        grouped_candidate.rendered_surface.utf8_bytes
    )
    introduced_ordinals = tuple(
        row.introduced_reference.reference_ordinal
        for row in witness.atoms
        if row.introduced_reference is not None
    )
    assert len(introduced_ordinals) == len(set(introduced_ordinals))


@pytest.mark.parametrize("mutation", ("swap", "missing", "late"))
def test_matcher_rejects_malformed_relation_reference_graph(
    relation_rich_execution,
    grouped_candidate,
    mutation: str,
) -> None:
    witness = parse_step11_natural_surface(
        grouped_candidate.rendered_surface.utf8_bytes
    )
    relation = _relation_atom(witness)
    references = relation.relation_endpoint_references
    assert len(references) == 2
    atoms = list(witness.atoms)

    if mutation == "swap":
        forged_relation = replace(
            relation,
            relation_endpoint_references=tuple(reversed(references)),
        )
    elif mutation == "missing":
        missing = replace(
            references[0],
            reference_ordinal=max(
                row.reference_ordinal
                for atom in witness.atoms
                for row in (
                    (atom.introduced_reference,)
                    if atom.introduced_reference is not None
                    else ()
                )
            )
            + 100,
        )
        forged_relation = replace(
            relation,
            relation_endpoint_references=(missing, references[1]),
        )
    else:
        antecedent = next(
            row
            for row in witness.atoms
            if row.introduced_reference is not None
            and row.introduced_reference.reference_ordinal
            == references[0].reference_ordinal
        )
        late_antecedent = replace(
            antecedent,
            sentence_ordinal=relation.sentence_ordinal + 1,
            clause_ordinal=0,
            byte_start=relation.byte_end,
            byte_end=relation.byte_end,
        )
        atoms[atoms.index(antecedent)] = late_antecedent
        forged_relation = relation

    atoms[atoms.index(relation)] = forged_relation
    forged_witness = replace(witness, atoms=tuple(atoms))
    binding = _match(
        relation_rich_execution,
        grouped_candidate,
        forged_witness,
    )

    assert binding.verified is False
    assert (
        "S11_MATCH_RELATION_ENDPOINT_REFERENCE_MISMATCH"
        in binding.issue_codes
    )


def test_literal_range_replay_is_rejected_without_relation_owner_exception(
    relation_rich_execution,
    grouped_candidate,
) -> None:
    witness = parse_step11_natural_surface(
        grouped_candidate.rendered_surface.utf8_bytes
    )
    first = next(
        row
        for row in witness.atoms
        if row.section_role == "observation"
        and row.introduced_reference is not None
        and row.source_fragments
    )
    replay = replace(
        first,
        atom_id="s11atom_rc0019_literal_replay",
        sentence_ordinal=first.sentence_ordinal + 100,
        clause_ordinal=0,
        byte_start=first.byte_end,
        byte_end=first.byte_end,
    )
    forged_witness = replace(
        witness,
        atoms=(*witness.atoms, replay),
        observation_atom_count=witness.observation_atom_count + 1,
    )

    binding = _match(
        relation_rich_execution,
        grouped_candidate,
        forged_witness,
    )

    assert binding.verified is False
    assert "S11_MATCH_LITERAL_OWNER_BUDGET_EXCEEDED" in binding.issue_codes
