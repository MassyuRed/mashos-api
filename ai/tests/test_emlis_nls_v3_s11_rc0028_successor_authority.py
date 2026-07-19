# -*- coding: utf-8 -*-
from __future__ import annotations

"""A1 RED/GREEN contract for the rc0028 experiment-only authority successor.

The authority is upstream-only.  These tests bind relation projection,
coexistence refinement, nested construction topology, semantic-restatement
lineage, strict origin, resources and body-free material without importing a
Surface, Parser, Matcher, Gate or runtime owner.
"""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

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
from emlis_ai_grounded_relation_construction_authority_successor_v3 import (
    GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_ADAPTER_VERSION,
    GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_SCHEMA,
    MAX_CONSTRUCTION_INSTANCES_PER_PARENT_SPAN,
    MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT,
    GroundedRelationConstructionAuthoritySuccessorError,
    build_grounded_relation_construction_authority_successor,
    grounded_relation_construction_authority_successor_material,
    validate_grounded_relation_construction_authority_successor,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import build_emlis_safety_triage_decision


_HERE = Path(__file__).resolve().parent
_OWNER = (
    _HERE.parent
    / "services"
    / "ai_inference"
    / "emlis_ai_grounded_relation_construction_authority_successor_v3.py"
)


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


def _build(text: str):
    normalized, plan, resolver = _plan_and_resolver(_input(text))
    value = build_grounded_relation_construction_authority_successor(
        plan,
        resolver,
    )
    return normalized, plan, resolver, value


def test_successor_exports_closed_experiment_only_contract() -> None:
    assert GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_SCHEMA.endswith(
        ".rc0028.experiment.v2"
    )
    assert (
        GROUNDED_RELATION_CONSTRUCTION_AUTHORITY_SUCCESSOR_ADAPTER_VERSION
        .endswith(".20260719.v2")
    )
    assert MAX_CONSTRUCTION_SLOTS_PER_REQUIRED_TEXT_PARENT == 6
    assert MAX_CONSTRUCTION_INSTANCES_PER_PARENT_SPAN == 6
    _normalized, _plan, _resolver, value = _build(
        "準備は進んだ。でも、結論はまだ決められない。"
    )
    assert value.experimental_only is True
    assert value.body_free is True
    assert value.runtime_connected is False


@pytest.mark.parametrize(
    ("text", "source_type", "effective_type", "basis", "direction"),
    (
        (
            "準備は進んだ。でも、結論はまだ決められない。",
            "contrast",
            "contrast",
            "grounded_plan_projection",
            "source_to_target",
        ),
        (
            "昨日は記録を読み返した。今日は次の手順を決めた。",
            "shift_from_to",
            "shift_from_to",
            "grounded_plan_projection",
            "source_to_target",
        ),
        (
            "余裕は残っている。同時に、慎重さも残っている。",
            "uncertain_connection",
            "coexistence",
            "source_explicit_refinement",
            "bidirectional",
        ),
    ),
)
def test_all_plan_relations_are_exactly_one_effective_projection_or_refinement(
    text: str,
    source_type: str,
    effective_type: str,
    basis: str,
    direction: str,
) -> None:
    _normalized, plan, resolver, value = _build(text)
    assert validate_grounded_relation_construction_authority_successor(
        value,
        plan=plan,
        resolver=resolver,
    ) == ()
    assert len(value.relation_authorities) == len(plan.relations) == 1
    source = plan.relations[0]
    row = value.relation_authorities[0]
    assert row.source_relation_id == source.relation_id
    assert row.source_relation_type == source_type
    assert row.effective_relation_type == effective_type
    assert row.authority_basis == basis
    assert row.direction == direction
    assert row.source_grounding_kind == source.grounding_kind
    assert row.source_certainty == source.certainty
    assert row.source_retention == source.retention
    assert row.source_from_nucleus_id == source.from_nucleus_id
    assert row.source_to_nucleus_id == source.to_nucleus_id
    assert row.from_source_owner_id == source.from_nucleus_id
    assert row.to_source_owner_id == source.to_nucleus_id
    assert row.source_relation_ids == source.source_relation_ids
    assert row.source_meaning_arc_keys == source.source_meaning_arc_keys
    assert row.evidence_alias_ids == source.source_span_ids
    if basis == "source_explicit_refinement":
        assert row.refines_source_relation_id == source.relation_id
        assert row.experiment_retention == "experiment_required_refinement"
        assert row.marker_code == "explicit_simultaneous_connector"
        assert row.marker_source_span_id in source.source_span_ids
        assert type(row.marker_start_index) is int
        assert type(row.marker_end_index) is int
        assert row.marker_start_index < row.marker_end_index
    else:
        assert row.refines_source_relation_id is None
        assert row.experiment_retention == "source_projection"
        assert row.marker_code is None
        assert row.marker_source_span_id is None
        assert row.marker_start_index is None
        assert row.marker_end_index is None


def test_nested_constructions_slots_topology_and_participation_are_lossless() -> None:
    _normalized, plan, resolver, value = _build(
        "安心したのに、後で迷いが残ったのはなぜだろう。"
    )
    restatement = build_grounded_semantic_restatement_witness(plan, resolver)
    assert {row.construction_code for row in value.construction_instances} == {
        "explicit_contrast",
        "ordered_sequence",
    }
    assert len(value.construction_slots) == 6
    assert len(value.interval_edges) == 1
    assert value.interval_edges[0].range_relation == "coextensive"
    for instance in value.construction_instances:
        rows = tuple(
            row
            for row in value.construction_slots
            if row.construction_instance_id == instance.construction_instance_id
        )
        assert tuple(row.construction_slot_id for row in rows) == instance.slot_ids
        assert len(rows) == len({row.lexical_role_kind for row in rows})
        expected_participation_ids = tuple(
            sorted(
                {
                    item
                    for row in rows
                    for item in row.participation_ids
                }
            )
        )
        assert instance.participation_ids == expected_participation_ids
    source_unit_ids = {row.unit_id for row in restatement.semantic_units}
    assert source_unit_ids <= {
        row.target_owner_id
        for row in value.source_owner_participations
        if row.target_owner_kind == "semantic_unit"
    }
    assert all(
        row.semantic_equivalence_authorized is False
        for row in value.source_owner_participations
    )
    assert tuple(
        row.source_semantic_link_id for row in value.semantic_link_bindings
    ) == tuple(row.link_id for row in restatement.semantic_links)
    assert tuple(
        row.source_unknown_id for row in value.explicit_unknown_authorities
    ) == tuple(row.unknown_id for row in restatement.explicit_unknowns)


def test_relation_topology_semantic_link_and_unknown_mutations_fail_closed() -> None:
    _normalized, plan, resolver, value = _build(
        "安心したのに、後で迷いが残ったのはなぜだろう。"
    )
    edge = value.interval_edges[0]
    forged_edge = replace(edge, range_relation="contains")
    forged = replace(value, interval_edges=(forged_edge,))
    issues = validate_grounded_relation_construction_authority_successor(
        forged,
        plan=plan,
        resolver=resolver,
    )
    assert "SUCCESSOR_AUTHORITY_INTERVAL_EDGES_MISMATCH" in issues

    link = value.semantic_link_bindings[0]
    forged_link = replace(link, direction="source_to_target")
    forged = replace(value, semantic_link_bindings=(forged_link,))
    issues = validate_grounded_relation_construction_authority_successor(
        forged,
        plan=plan,
        resolver=resolver,
    )
    assert "SUCCESSOR_AUTHORITY_SEMANTIC_LINKS_MISMATCH" in issues

    unknown = value.explicit_unknown_authorities[0]
    forged_unknown = replace(
        unknown,
        dimension="explicit_invented_unknown",
    )
    forged = replace(
        value,
        explicit_unknown_authorities=(
            forged_unknown,
            *value.explicit_unknown_authorities[1:],
        ),
    )
    issues = validate_grounded_relation_construction_authority_successor(
        forged,
        plan=plan,
        resolver=resolver,
    )
    assert "SUCCESSOR_AUTHORITY_EXPLICIT_UNKNOWNS_MISMATCH" in issues


def test_relation_direction_mutation_and_originless_clone_fail_closed() -> None:
    _normalized, plan, resolver, value = _build(
        "準備は進んだ。でも、結論はまだ決められない。"
    )
    row = value.relation_authorities[0]
    forged_row = replace(row, direction="bidirectional")
    forged = replace(value, relation_authorities=(forged_row,))
    assert "SUCCESSOR_AUTHORITY_RELATIONS_MISMATCH" in (
        validate_grounded_relation_construction_authority_successor(
            forged,
            plan=plan,
            resolver=resolver,
        )
    )
    with pytest.raises(
        GroundedRelationConstructionAuthoritySuccessorError,
        match="SUCCESSOR_AUTHORITY_RELATIONS_MISMATCH",
    ):
        grounded_relation_construction_authority_successor_material(
            forged,
            plan=plan,
            resolver=resolver,
        )

    originless = replace(value)
    assert "SUCCESSOR_AUTHORITY_ORIGIN_CAPABILITY_MISSING" in (
        validate_grounded_relation_construction_authority_successor(
            originless,
            plan=plan,
            resolver=resolver,
        )
    )
    assert deepcopy(value) is value


def test_resource_denominators_are_frozen_upstream_and_material_is_body_free() -> None:
    normalized, plan, resolver, value = _build(
        "安心したのに、後で迷いが残ったのはなぜだろう。"
    )
    required = frozenset(plan.coverage_requirements.required_nucleus_ids)
    n = sum(
        1
        for row in plan.nuclei
        if row.nucleus_id in required
        and set(row.source_fields) <= {"memo", "memo_action"}
    )
    assert value.resource_counts.required_text_parent_nucleus_count == n
    assert value.resource_bounds.max_lexical_construction_slots == 6 * n
    assert value.resource_bounds.max_construction_instances == 6 * n
    assert value.resource_counts.lexical_construction_slot_count == len(
        value.construction_slots
    )
    assert value.resource_counts.effective_relation_count == len(
        plan.relations
    )
    assert value.resource_counts.source_owner_participation_count <= (
        value.resource_bounds.max_source_owner_participations
    )

    material = grounded_relation_construction_authority_successor_material(
        value,
        plan=plan,
        resolver=resolver,
    )
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert material["experimental_only"] is True
    assert material["body_free"] is True
    assert material["runtime_connected"] is False
    assert "raw_text" not in encoded
    assert "source_fragment" not in encoded
    for field in ("memo", "memo_action"):
        source = str(normalized.get(field, ""))
        assert not source or source not in encoded


def test_owner_has_no_case_fixture_or_downstream_import() -> None:
    source = _OWNER.read_text(encoding="utf-8")
    forbidden = (
        "case_id",
        "batch_001",
        "semantic_contract",
        "nls3s_b",
        "emlis_ai_step11_natural_surface_v3",
        "emlis_ai_step11_natural_surface_matcher_v3",
        "emlis_ai_independent_semantic_matcher_v3",
        "emlis_ai_semantic_hard_gate_v3",
    )
    assert all(token not in source for token in forbidden)
