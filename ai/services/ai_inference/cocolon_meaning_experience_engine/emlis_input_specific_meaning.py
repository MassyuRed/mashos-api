# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed, Reception-free Foreground Scope derivation.

This module is the sole local meaning owner between the validated pre-meaning
projection and later input-specific meaning work.  It consumes only grounded
semantic objects, source relations, qualifiers, retention duties, and material
unknowns.  Reception acts, affect, style, temperature, surface text, fixture
identity, and candidate ordering are intentionally absent from its input
types and decision procedure.

Object and basis identifiers are retained for provenance only.  They never
rank, select, truncate, or break a tie.  Compatible rows are combined by
canonical set union; an actual typed conflict remains competing, and missing
typed structure remains structure-insufficient.
"""

from dataclasses import dataclass, replace
from enum import Enum
from itertools import combinations, product
from typing import Iterable, Mapping, Sequence, Tuple

from .contracts import (
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEEStage1ContractError,
    EpistemicState,
    ForegroundScope,
    ForegroundScopeBasisKind,
    ForegroundScopeBasisRow,
    ForegroundScopeCompatibilityAxis,
    ForegroundScopeDerivation,
    ForegroundScopeDerivationState,
    ForegroundScopeObjectCompatibilityRow,
    ForegroundScopeRelationKind,
    GroundedMeaningGraph,
    GroundedSourceRelationRow,
    MeaningEdge,
    MeaningNode,
    OwnerClass,
    PreMeaningGroundedInputs,
    SourceOwnerDisposition,
    VisibleAuthority,
    foreground_scope_basis_row_ref,
    foreground_scope_id,
    validate_version_qualified_ref,
)


_SCHEMA_VERSION = "1.0"
_FOREGROUND_SCOPE_BASIS_REF_VERSION = (
    "cocolon.cmee.emlis.foreground_scope_basis.v1"
)

_BASIS_KINDS_EXACT5 = frozenset(ForegroundScopeBasisKind)
_RELATION_KINDS_EXACT4 = frozenset(ForegroundScopeRelationKind)
_COMPATIBILITY_AXES_EXACT10 = tuple(ForegroundScopeCompatibilityAxis)

_COMPATIBILITY_FIELD_BY_AXIS = {
    ForegroundScopeCompatibilityAxis.OWNER: "owner_refs",
    ForegroundScopeCompatibilityAxis.WORLD: "world_refs",
    ForegroundScopeCompatibilityAxis.EPISTEMIC: "epistemic_state_refs",
    ForegroundScopeCompatibilityAxis.TIME: "time_refs",
    ForegroundScopeCompatibilityAxis.ASPECT: "aspect_refs",
    ForegroundScopeCompatibilityAxis.MODALITY: "modality_refs",
    ForegroundScopeCompatibilityAxis.POLARITY: "polarity_refs",
    ForegroundScopeCompatibilityAxis.SCOPE: "scope_refs",
    ForegroundScopeCompatibilityAxis.REQUIRED_QUALIFIER: (
        "required_qualifier_refs"
    ),
    ForegroundScopeCompatibilityAxis.UNKNOWN: "material_unknown_refs",
}
_COMPATIBILITY_PREFIXES_BY_FIELD = {
    "owner_refs": ("owner:",),
    "world_refs": ("world:",),
    "epistemic_state_refs": ("epistemic:", "epistemic-state:"),
    "time_refs": ("time:", "time_scope:"),
    "aspect_refs": ("aspect:",),
    "modality_refs": ("modality:",),
    "polarity_refs": ("polarity:",),
    "scope_refs": ("scope:",),
    "required_qualifier_refs": (
        "actor:",
        "aspect:",
        "epistemic:",
        "modality:",
        "polarity:",
        "qualifier:",
        "scope:",
        "time:",
        "time_scope:",
        "world:",
    ),
    "material_unknown_refs": ("unknown:",),
}

if set(_COMPATIBILITY_FIELD_BY_AXIS) != set(_COMPATIBILITY_AXES_EXACT10):
    raise RuntimeError("foreground_scope_compatibility_axis_mapping_not_exact10")
if set(_COMPATIBILITY_PREFIXES_BY_FIELD) != set(
    _COMPATIBILITY_FIELD_BY_AXIS.values()
):
    raise RuntimeError("foreground_scope_compatibility_prefix_mapping_not_exact10")


class ForegroundScopeDispositionCode(str, Enum):
    """The only IM01 disposition reachable from a scope derivation state."""

    AVAILABLE = "FOREGROUND_SCOPE_AVAILABLE"
    LIMITED_COMPETING_MATERIAL_READINGS = (
        "LIMITED_COMPETING_MATERIAL_READINGS"
    )
    LIMITED_STRUCTURE_INSUFFICIENT = "LIMITED_STRUCTURE_INSUFFICIENT"
    STRUCTURE_INSUFFICIENT_STOP = "STRUCTURE_INSUFFICIENT_STOP"


@dataclass(frozen=True, slots=True)
class SourceConnectedScopeRelation:
    """One exact4 source relation that connects the stated object pair."""

    schema_version: str
    relation_ref: str
    relation_kind: ForegroundScopeRelationKind
    source_object_ref: str
    target_object_ref: str
    source_evidence_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GroundedSituationView:
    """Reception-unreachable input to closed Foreground Scope derivation."""

    schema_version: str
    basis_rows: Tuple[ForegroundScopeBasisRow, ...]
    compatibility_rows: Tuple[ForegroundScopeObjectCompatibilityRow, ...]
    source_connected_relations: Tuple[SourceConnectedScopeRelation, ...]
    missing_structure_refs: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ForegroundScopeDisposition:
    """Exhaustive delivery disposition for one closed scope derivation."""

    schema_version: str
    code: ForegroundScopeDispositionCode
    derivation_state: ForegroundScopeDerivationState
    retained_foreground_source_object_refs: Tuple[str, ...]
    unresolved_scope_refs: Tuple[str, ...]
    missing_structure_refs: Tuple[str, ...]


def _canonical(values: Iterable[str]) -> Tuple[str, ...]:
    materialized = tuple(values)
    if any(type(value) is not str or not value for value in materialized):
        raise CMEEStage1ContractError(
            "foreground_scope_internal_ref_invalid"
        )
    return tuple(sorted(set(materialized)))


def _is_canonical(values: Sequence[str]) -> bool:
    if type(values) is not tuple:
        return False
    materialized = tuple(values)
    return (
        all(type(value) is str and bool(value) for value in materialized)
        and materialized == tuple(sorted(set(materialized)))
    )


def _node_ref(node: MeaningNode) -> str:
    return f"node:{node.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _edge_ref(edge: MeaningEdge) -> str:
    return f"edge:{edge.edge_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _evidence_refs(
    values: Iterable[MeaningNode | MeaningEdge],
    *,
    source_version: str,
) -> Tuple[str, ...]:
    return _canonical(
        f"evidence:{evidence_id}@{source_version}"
        for value in values
        for evidence_id in value.evidence_ids
    )


def _missing_ref(kind: str, *refs: str) -> str:
    return ":".join(("foreground-scope-missing", kind, *refs))


def _qualifiers_by_node_ref(
    premeaning_inputs: PreMeaningGroundedInputs,
) -> Mapping[str, Tuple[str, ...]]:
    result: dict[str, Tuple[str, ...]] = {}
    for row in premeaning_inputs.source_qualifier_rows:
        if row.node_ref in result:
            raise CMEEStage1ContractError(
                "grounded_situation_view_source_qualifier_duplicate"
            )
        if (
            not row.qualifier_refs
            or any(
                type(value) is not str or not value
                for value in row.qualifier_refs
            )
            or len(row.qualifier_refs) != len(set(row.qualifier_refs))
        ):
            raise CMEEStage1ContractError(
                "grounded_situation_view_source_qualifier_invalid"
            )
        result[row.node_ref] = _canonical(row.qualifier_refs)
    return result


def _unknowns_by_node_ref(
    premeaning_inputs: PreMeaningGroundedInputs,
    nodes_by_ref: Mapping[str, MeaningNode],
) -> tuple[Mapping[str, Tuple[str, ...]], Tuple[str, ...]]:
    graph = premeaning_inputs.grounded_graph
    unknown_to_nodes: dict[str, set[str]] = {}
    for disposition in graph.owner_dispositions:
        if disposition.target_unknown_ref is None:
            continue
        unknown_ref = (
            f"unknown:{disposition.target_unknown_ref}"
            f"@{graph.obligation_version}"
        )
        object_ref = (
            f"node:{disposition.target_unknown_ref}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        )
        if object_ref in nodes_by_ref:
            unknown_to_nodes.setdefault(unknown_ref, set()).add(object_ref)

    material_unknowns = _canonical(premeaning_inputs.material_unknown_refs)
    missing = tuple(
        _missing_ref("material-unknown-object", unknown_ref)
        for unknown_ref in material_unknowns
        if not unknown_to_nodes.get(unknown_ref)
    )
    by_node: dict[str, list[str]] = {}
    for unknown_ref in material_unknowns:
        for object_ref in unknown_to_nodes.get(unknown_ref, ()):
            by_node.setdefault(object_ref, []).append(unknown_ref)
    return (
        {
            object_ref: _canonical(unknown_refs)
            for object_ref, unknown_refs in by_node.items()
        },
        _canonical(missing),
    )


def _compatibility_row(
    *,
    object_ref: str,
    node: MeaningNode,
    graph: GroundedMeaningGraph,
    qualifier_refs: Sequence[str],
    material_unknown_refs: Sequence[str],
) -> ForegroundScopeObjectCompatibilityRow:
    qualifiers = _canonical(qualifier_refs)
    explicit_scope = tuple(
        value for value in qualifiers if value.startswith("scope:")
    )
    return ForegroundScopeObjectCompatibilityRow(
        schema_version=_SCHEMA_VERSION,
        scope_object_ref=object_ref,
        owner_refs=(f"owner:{node.owner_id}@{graph.obligation_version}",),
        world_refs=tuple(
            value for value in qualifiers if value.startswith("world:")
        ),
        epistemic_state_refs=(
            f"epistemic-state:{node.epistemic_state.value.lower()}"
            f"@{_FOREGROUND_SCOPE_BASIS_REF_VERSION}",
        ),
        time_refs=tuple(
            value
            for value in qualifiers
            if value.startswith(("time:", "time_scope:"))
        ),
        aspect_refs=tuple(
            value for value in qualifiers if value.startswith("aspect:")
        ),
        modality_refs=tuple(
            value for value in qualifiers if value.startswith("modality:")
        ),
        polarity_refs=tuple(
            value for value in qualifiers if value.startswith("polarity:")
        ),
        scope_refs=_canonical(
            (
                *explicit_scope,
                *(("scope:source_bounded",) if qualifiers else ()),
            )
        ),
        required_qualifier_refs=tuple(
            value
            for value in qualifiers
            if not value.startswith(("world:", "aspect:"))
        ),
        material_unknown_refs=_canonical(material_unknown_refs),
    )


def _basis_row(
    *,
    basis_kind: ForegroundScopeBasisKind,
    object_refs: Sequence[str],
    evidence_refs: Sequence[str],
    compatibility_by_object: Mapping[
        str, ForegroundScopeObjectCompatibilityRow
    ],
    layer1_required_object_refs: Sequence[str] = (),
    required_retention_duty_refs: Sequence[str] = (),
    source_connected_relation_refs: Sequence[str] = (),
    material_unknown_refs: Sequence[str] = (),
    required_qualifier_refs: Sequence[str] = (),
) -> ForegroundScopeBasisRow:
    if basis_kind not in _BASIS_KINDS_EXACT5:
        raise CMEEStage1ContractError(
            "grounded_situation_view_basis_kind_not_allowlisted"
        )
    objects = _canonical(object_refs)
    evidence = _canonical(evidence_refs)
    if not objects or not evidence:
        raise CMEEStage1ContractError(
            "grounded_situation_view_basis_provenance_empty"
        )
    profiles = tuple(compatibility_by_object[ref] for ref in objects)

    def union(field_name: str) -> Tuple[str, ...]:
        return _canonical(
            value
            for profile in profiles
            for value in getattr(profile, field_name)
        )

    return ForegroundScopeBasisRow(
        schema_version=_SCHEMA_VERSION,
        basis_kind=basis_kind,
        scope_object_refs=objects,
        source_object_refs=objects,
        source_evidence_refs=evidence,
        layer1_required_object_refs=_canonical(
            layer1_required_object_refs
        ),
        required_retention_duty_refs=_canonical(
            required_retention_duty_refs
        ),
        source_connected_relation_refs=_canonical(
            source_connected_relation_refs
        ),
        material_unknown_refs=_canonical(material_unknown_refs),
        required_qualifier_refs=_canonical(required_qualifier_refs),
        owner_refs=union("owner_refs"),
        world_refs=union("world_refs"),
        epistemic_state_refs=union("epistemic_state_refs"),
        time_refs=union("time_refs"),
        aspect_refs=union("aspect_refs"),
        modality_refs=union("modality_refs"),
        polarity_refs=union("polarity_refs"),
        scope_refs=union("scope_refs"),
    )


def _basis_sort_key(row: ForegroundScopeBasisRow) -> tuple[object, ...]:
    """Canonical serialization order; never a selection or priority key."""

    return (
        row.basis_kind.value,
        row.scope_object_refs,
        row.source_object_refs,
        row.source_evidence_refs,
        row.layer1_required_object_refs,
        row.required_retention_duty_refs,
        row.source_connected_relation_refs,
        row.material_unknown_refs,
        row.required_qualifier_refs,
        row.owner_refs,
        row.world_refs,
        row.epistemic_state_refs,
        row.time_refs,
        row.aspect_refs,
        row.modality_refs,
        row.polarity_refs,
        row.scope_refs,
    )


def _relation_is_source_explicit(
    edge: MeaningEdge,
    graph: GroundedMeaningGraph,
) -> bool:
    return (
        edge.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        and edge.grounding_kind == "user_stated_relation"
        and bool(edge.evidence_ids)
        and any(
            disposition.meaning_owner_id == edge.owner_id
            and disposition.visible_authority
            is VisibleAuthority.SOURCE_EXPLICIT
            and disposition.source_owner_disposition
            is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
            and edge.edge_id in disposition.visible_claim_refs
            for disposition in graph.owner_dispositions
        )
    )


def derive_grounded_situation_view(
    premeaning_inputs: PreMeaningGroundedInputs,
) -> GroundedSituationView:
    """Build exact5-allowlisted bases and per-object exact10 profiles.

    ``premeaning_inputs`` is expected to have passed
    ``validate_premeaning_grounded_inputs`` at the actual source boundary.
    This function deliberately accepts no Reception-side argument.
    """

    if type(premeaning_inputs) is not PreMeaningGroundedInputs:
        raise CMEEStage1ContractError(
            "grounded_situation_view_premeaning_inputs_invalid"
        )
    if premeaning_inputs.schema_version != _SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "grounded_situation_view_schema_version_invalid"
        )
    graph = premeaning_inputs.grounded_graph
    if type(graph) is not GroundedMeaningGraph:
        raise CMEEStage1ContractError(
            "grounded_situation_view_graph_invalid"
        )

    nodes_by_ref = {_node_ref(node): node for node in graph.nodes}
    edges_by_ref = {_edge_ref(edge): edge for edge in graph.edges}
    if len(nodes_by_ref) != len(graph.nodes) or len(edges_by_ref) != len(
        graph.edges
    ):
        raise CMEEStage1ContractError(
            "grounded_situation_view_graph_identity_duplicate"
        )

    qualifiers_by_node = _qualifiers_by_node_ref(premeaning_inputs)
    unknowns_by_node, unknown_missing = _unknowns_by_node_ref(
        premeaning_inputs, nodes_by_ref
    )
    compatibility_by_object = {
        object_ref: _compatibility_row(
            object_ref=object_ref,
            node=node,
            graph=graph,
            qualifier_refs=qualifiers_by_node.get(object_ref, ()),
            material_unknown_refs=unknowns_by_node.get(object_ref, ()),
        )
        for object_ref, node in nodes_by_ref.items()
    }

    candidates_by_ref = {
        row.candidate_id: row
        for row in premeaning_inputs.interpretation_candidate_rows
    }
    source_relation_kind_by_ref: dict[str, ForegroundScopeRelationKind] = {}
    for row in premeaning_inputs.source_relation_rows:
        if (
            type(row) is not GroundedSourceRelationRow
            or type(row.relation_kind) is not ForegroundScopeRelationKind
            or row.relation_kind not in _RELATION_KINDS_EXACT4
            or type(row.relation_ref) is not str
            or not row.relation_ref
        ):
            raise CMEEStage1ContractError(
                "grounded_situation_view_source_relation_invalid"
            )
        validate_version_qualified_ref(
            row.relation_ref,
            expected_types=("edge",),
        )
        if row.relation_ref in source_relation_kind_by_ref:
            raise CMEEStage1ContractError(
                "grounded_situation_view_source_relation_duplicate"
            )
        source_relation_kind_by_ref[row.relation_ref] = row.relation_kind
    if not set(source_relation_kind_by_ref).issubset(edges_by_ref):
        raise CMEEStage1ContractError(
            "grounded_situation_view_source_relation_unbound"
        )
    contributions_by_ref = {
        row.contribution_id: row
        for row in premeaning_inputs.observation_contribution_rows
    }
    if len(candidates_by_ref) != len(
        premeaning_inputs.interpretation_candidate_rows
    ) or len(contributions_by_ref) != len(
        premeaning_inputs.observation_contribution_rows
    ):
        raise CMEEStage1ContractError(
            "grounded_situation_view_layer1_identity_duplicate"
        )

    required_contributions = tuple(
        row
        for row in premeaning_inputs.observation_contribution_rows
        if row.retention == "REQUIRED"
    )
    missing: list[str] = list(unknown_missing)
    basis_rows: list[ForegroundScopeBasisRow] = []

    def admitted_objects(
        refs: Sequence[str], *, missing_kind: str
    ) -> Tuple[str, ...]:
        values = _canonical(refs)
        absent = tuple(ref for ref in values if ref not in nodes_by_ref)
        missing.extend(_missing_ref(missing_kind, ref) for ref in absent)
        return tuple(ref for ref in values if ref in nodes_by_ref)

    def append_basis(row: ForegroundScopeBasisRow) -> None:
        # The trace ref helper validates the closed row shape without needing
        # any raw source, Reception plan, or downstream projection.
        foreground_scope_basis_row_ref(row)
        basis_rows.append(row)

    required_owner_ids = set(graph.required_owner_refs)
    required_visible_claim_ids = {
        claim_id
        for disposition in graph.owner_dispositions
        if disposition.meaning_owner_id in required_owner_ids
        and disposition.owner_class is OwnerClass.REQUIRED
        and disposition.visible_authority is VisibleAuthority.SOURCE_EXPLICIT
        and disposition.source_owner_disposition
        is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
        for claim_id in disposition.visible_claim_refs
    }
    source_explicit_objects = _canonical(
        object_ref
        for object_ref, node in nodes_by_ref.items()
        if node.owner_id in required_owner_ids
        and node.node_id in required_visible_claim_ids
        and node.epistemic_state is EpistemicState.SOURCE_EXPLICIT
    )
    if source_explicit_objects:
        append_basis(
            _basis_row(
                basis_kind=(
                    ForegroundScopeBasisKind.SOURCE_EXPLICIT_TARGET_TOPIC_OR_SCOPE
                ),
                object_refs=source_explicit_objects,
                evidence_refs=_evidence_refs(
                    (nodes_by_ref[ref] for ref in source_explicit_objects),
                    source_version=graph.source_version,
                ),
                compatibility_by_object=compatibility_by_object,
            )
        )

    for contribution in required_contributions:
        object_refs = admitted_objects(
            contribution.semantic_refs,
            missing_kind="layer1-object",
        )
        if not object_refs or not contribution.evidence_refs:
            missing.append(
                _missing_ref(
                    "layer1-basis", contribution.contribution_id
                )
            )
            continue
        append_basis(
            _basis_row(
                basis_kind=(
                    ForegroundScopeBasisKind.LAYER1_REQUIRED_OBSERVATION_OBJECT
                ),
                object_refs=object_refs,
                evidence_refs=contribution.evidence_refs,
                compatibility_by_object=compatibility_by_object,
                layer1_required_object_refs=(
                    contribution.contribution_id,
                ),
            )
        )

    required_by_duty: dict[str, list[object]] = {}
    for contribution in required_contributions:
        required_by_duty.setdefault(
            contribution.parent_duty_ref, []
        ).append(contribution)
    for duty_ref, contributions in required_by_duty.items():
        object_refs = admitted_objects(
            tuple(
                ref
                for contribution in contributions
                for ref in contribution.semantic_refs
            ),
            missing_kind="retention-object",
        )
        evidence_refs = _canonical(
            ref
            for contribution in contributions
            for ref in contribution.evidence_refs
        )
        if not object_refs or not evidence_refs:
            missing.append(_missing_ref("retention-duty", duty_ref))
            continue
        append_basis(
            _basis_row(
                basis_kind=(
                    ForegroundScopeBasisKind.EXISTING_REQUIRED_RETENTION_DUTY
                ),
                object_refs=object_refs,
                evidence_refs=evidence_refs,
                compatibility_by_object=compatibility_by_object,
                required_retention_duty_refs=(duty_ref,),
            )
        )

    used_relation_refs = set(
        _canonical(
            ref
            for contribution in required_contributions
            for ref in contribution.relation_basis_refs
        )
    )
    missing.extend(
        _missing_ref("relation-object", relation_ref)
        for relation_ref in sorted(used_relation_refs)
        if relation_ref not in edges_by_ref
    )
    source_relations: list[SourceConnectedScopeRelation] = []
    # SOURCE_CONNECTED_RELATION is an independent exact5 basis arm.  Discover
    # every visible source-explicit graph edge that the shared closed projector
    # can normalize into exact4; Layer-1 use is neither required nor ranking.
    for relation_ref in sorted(edges_by_ref):
        edge = edges_by_ref[relation_ref]
        relation_kind = source_relation_kind_by_ref.get(relation_ref)
        if relation_kind is None:
            continue
        if not _relation_is_source_explicit(edge, graph):
            if relation_ref in used_relation_refs:
                missing.append(
                    _missing_ref("source-relation", relation_ref)
                )
            continue
        endpoint_refs = (
            f"node:{edge.source_node_id}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
            f"node:{edge.target_node_id}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
        )
        object_refs = admitted_objects(
            endpoint_refs,
            missing_kind="relation-endpoint",
        )
        if len(set(object_refs)) != 2:
            missing.append(_missing_ref("relation-endpoint", relation_ref))
            continue
        evidence_refs = _evidence_refs(
            (
                edge,
                *(nodes_by_ref[ref] for ref in object_refs),
            ),
            source_version=graph.source_version,
        )
        relation = SourceConnectedScopeRelation(
            schema_version=_SCHEMA_VERSION,
            relation_ref=relation_ref,
            relation_kind=relation_kind,
            source_object_ref=endpoint_refs[0],
            target_object_ref=endpoint_refs[1],
            source_evidence_refs=evidence_refs,
        )
        source_relations.append(relation)
        append_basis(
            _basis_row(
                basis_kind=ForegroundScopeBasisKind.SOURCE_CONNECTED_RELATION,
                object_refs=object_refs,
                evidence_refs=evidence_refs,
                compatibility_by_object=compatibility_by_object,
                source_connected_relation_refs=(relation_ref,),
            )
        )

    required_candidate_refs = set(
        premeaning_inputs.meaning_field.required_candidate_refs
    )
    required_candidate_refs.update(
        ref
        for contribution in required_contributions
        for ref in contribution.interpretation_candidate_refs
    )
    for candidate_ref in _canonical(required_candidate_refs):
        candidate = candidates_by_ref.get(candidate_ref)
        if candidate is None:
            missing.append(_missing_ref("required-candidate", candidate_ref))
            continue
        if not candidate.required_qualifiers:
            continue
        object_refs = admitted_objects(
            candidate.semantic_refs,
            missing_kind="required-qualifier-object",
        )
        if not object_refs:
            missing.append(
                _missing_ref("required-qualifier", candidate_ref)
            )
            continue
        evidence_refs = _evidence_refs(
            (nodes_by_ref[ref] for ref in object_refs),
            source_version=graph.source_version,
        )
        if not evidence_refs:
            missing.append(
                _missing_ref("required-qualifier-evidence", candidate_ref)
            )
            continue
        append_basis(
            _basis_row(
                basis_kind=(
                    ForegroundScopeBasisKind.MATERIAL_UNKNOWN_OR_REQUIRED_QUALIFIER
                ),
                object_refs=object_refs,
                evidence_refs=evidence_refs,
                compatibility_by_object=compatibility_by_object,
                required_qualifier_refs=candidate.required_qualifiers,
            )
        )

    for unknown_ref in _canonical(premeaning_inputs.material_unknown_refs):
        object_refs = tuple(
            object_ref
            for object_ref, unknown_refs in unknowns_by_node.items()
            if unknown_ref in unknown_refs
        )
        if not object_refs:
            continue
        evidence_refs = _evidence_refs(
            (nodes_by_ref[ref] for ref in object_refs),
            source_version=graph.source_version,
        )
        if not evidence_refs:
            missing.append(_missing_ref("material-unknown-evidence", unknown_ref))
            continue
        append_basis(
            _basis_row(
                basis_kind=(
                    ForegroundScopeBasisKind.MATERIAL_UNKNOWN_OR_REQUIRED_QUALIFIER
                ),
                object_refs=object_refs,
                evidence_refs=evidence_refs,
                compatibility_by_object=compatibility_by_object,
                material_unknown_refs=(unknown_ref,),
            )
        )

    sorted_basis_rows = tuple(sorted(basis_rows, key=_basis_sort_key))
    deduplicated_basis_rows: list[ForegroundScopeBasisRow] = []
    for row in sorted_basis_rows:
        if deduplicated_basis_rows and row == deduplicated_basis_rows[-1]:
            continue
        deduplicated_basis_rows.append(row)
    ordered_basis_rows = tuple(deduplicated_basis_rows)
    observed_basis_refs: list[str] = []
    for row in ordered_basis_rows:
        trace_ref = foreground_scope_basis_row_ref(row)
        if trace_ref in observed_basis_refs:
            raise CMEEStage1ContractError(
                "foreground_scope_basis_ref_collision"
            )
        observed_basis_refs.append(trace_ref)
    admitted_object_refs = {
        ref for row in ordered_basis_rows for ref in row.scope_object_refs
    }
    compatibility_rows = tuple(
        compatibility_by_object[ref] for ref in sorted(admitted_object_refs)
    )
    ordered_relations = tuple(
        sorted(
            source_relations,
            key=lambda row: (
                row.relation_kind.value,
                row.source_object_ref,
                row.target_object_ref,
                row.relation_ref,
                row.source_evidence_refs,
            ),
        )
    )
    return GroundedSituationView(
        schema_version=_SCHEMA_VERSION,
        basis_rows=ordered_basis_rows,
        compatibility_rows=compatibility_rows,
        source_connected_relations=ordered_relations,
        missing_structure_refs=_canonical(missing),
    )


def _validate_compatibility_row(
    row: ForegroundScopeObjectCompatibilityRow,
) -> None:
    if type(row) is not ForegroundScopeObjectCompatibilityRow:
        raise CMEEStage1ContractError(
            "foreground_scope_compatibility_row_invalid"
        )
    if row.schema_version != _SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "foreground_scope_compatibility_schema_version_invalid"
        )
    if type(row.scope_object_ref) is not str or not row.scope_object_ref:
        raise CMEEStage1ContractError(
            "foreground_scope_compatibility_object_ref_invalid"
        )
    validate_version_qualified_ref(
        row.scope_object_ref,
        expected_types=("node",),
    )
    for field_name in _COMPATIBILITY_FIELD_BY_AXIS.values():
        values = getattr(row, field_name)
        if not _is_canonical(values):
            raise CMEEStage1ContractError(
                f"foreground_scope_compatibility_{field_name}_noncanonical"
            )
        if any(
            not value.startswith(
                _COMPATIBILITY_PREFIXES_BY_FIELD[field_name]
            )
            for value in values
        ):
            raise CMEEStage1ContractError(
                f"foreground_scope_compatibility_{field_name}_namespace_invalid"
            )


def _validate_source_relation(row: SourceConnectedScopeRelation) -> None:
    if type(row) is not SourceConnectedScopeRelation:
        raise CMEEStage1ContractError(
            "foreground_scope_source_relation_invalid"
        )
    if (
        row.schema_version != _SCHEMA_VERSION
        or type(row.relation_kind) is not ForegroundScopeRelationKind
        or row.relation_kind not in _RELATION_KINDS_EXACT4
        or type(row.relation_ref) is not str
        or not row.relation_ref
        or type(row.source_object_ref) is not str
        or not row.source_object_ref
        or type(row.target_object_ref) is not str
        or not row.target_object_ref
        or row.source_object_ref == row.target_object_ref
        or not _is_canonical(row.source_evidence_refs)
        or not row.source_evidence_refs
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_source_relation_shape_invalid"
        )
    validate_version_qualified_ref(row.relation_ref, expected_types=("edge",))
    validate_version_qualified_ref(
        row.source_object_ref,
        expected_types=("node",),
    )
    validate_version_qualified_ref(
        row.target_object_ref,
        expected_types=("node",),
    )
    for ref in row.source_evidence_refs:
        validate_version_qualified_ref(ref, expected_types=("evidence",))


def _base_required_qualifier_ref(value: str) -> str:
    """Remove only a typed argument-role wrapper used by relation candidates."""

    qualifier_prefixes = (
        "actor:",
        "aspect:",
        "epistemic:",
        "modality:",
        "polarity:",
        "qualifier:",
        "scope:",
        "time:",
        "time_scope:",
        "world:",
    )
    if value.startswith(qualifier_prefixes):
        return value
    _separator, _present, suffix = value.partition("_")
    return suffix if suffix.startswith(qualifier_prefixes) else value


def _relation_connects(
    relations: Sequence[SourceConnectedScopeRelation],
    left_object_ref: str,
    right_object_ref: str,
) -> bool:
    if left_object_ref == right_object_ref:
        return False
    endpoints = {left_object_ref, right_object_ref}
    return any(
        {row.source_object_ref, row.target_object_ref} == endpoints
        for row in relations
    )


def _material_object_pairs(
    basis_rows: Sequence[ForegroundScopeBasisRow],
) -> Tuple[Tuple[str, str], ...]:
    """Return cross-row and intra-row pairs without using row order to rank."""

    pairs: set[Tuple[str, str]] = set()
    for row in basis_rows:
        for left, right in combinations(row.scope_object_refs, 2):
            pairs.add(tuple(sorted((left, right))))
    for left_row, right_row in combinations(basis_rows, 2):
        for left, right in product(
            left_row.scope_object_refs, right_row.scope_object_refs
        ):
            pairs.add(tuple(sorted((left, right))))
    return tuple(sorted(pairs))


def _canonical_scope(
    basis_rows: Sequence[ForegroundScopeBasisRow],
) -> ForegroundScope:
    scope = ForegroundScope(
        schema_version=_SCHEMA_VERSION,
        scope_id=(
            "foreground-scope:pending"
            "@cocolon.cmee.emlis.foreground_scope.v1"
        ),
        integrated_scope_object_refs=_canonical(
            ref for row in basis_rows for ref in row.scope_object_refs
        ),
        basis_row_refs=_canonical(
            foreground_scope_basis_row_ref(row) for row in basis_rows
        ),
        source_connected_relation_refs=_canonical(
            ref
            for row in basis_rows
            for ref in row.source_connected_relation_refs
        ),
        required_retention_duty_refs=_canonical(
            ref
            for row in basis_rows
            for ref in row.required_retention_duty_refs
        ),
        material_unknown_refs=_canonical(
            ref for row in basis_rows for ref in row.material_unknown_refs
        ),
        required_qualifier_refs=_canonical(
            ref for row in basis_rows for ref in row.required_qualifier_refs
        ),
        source_evidence_refs=_canonical(
            ref for row in basis_rows for ref in row.source_evidence_refs
        ),
    )
    return replace(scope, scope_id=foreground_scope_id(scope))


def derive_foreground_scope_closed(
    grounded_view: GroundedSituationView,
) -> ForegroundScopeDerivation:
    """Derive one canonical union, a named LIMITED state, or zero-only STOP."""

    if type(grounded_view) is not GroundedSituationView:
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_view_invalid"
        )
    if grounded_view.schema_version != _SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_view_schema_version_invalid"
        )
    for field_name in (
        "basis_rows",
        "compatibility_rows",
        "source_connected_relations",
    ):
        if type(getattr(grounded_view, field_name)) is not tuple:
            raise CMEEStage1ContractError(
                f"foreground_scope_view_{field_name}_tuple_required"
            )
    if not _is_canonical(grounded_view.missing_structure_refs):
        raise CMEEStage1ContractError(
            "foreground_scope_view_missing_structure_noncanonical"
        )

    basis_rows = grounded_view.basis_rows
    basis_refs = tuple(foreground_scope_basis_row_ref(row) for row in basis_rows)
    if len(basis_refs) != len(set(basis_refs)):
        raise CMEEStage1ContractError(
            "foreground_scope_view_basis_rows_duplicate"
        )
    retained = _canonical(
        ref for row in basis_rows for ref in row.scope_object_refs
    )
    evidence = _canonical(
        ref for row in basis_rows for ref in row.source_evidence_refs
    )
    profiles_by_object: dict[
        str, list[ForegroundScopeObjectCompatibilityRow]
    ] = {}
    for row in grounded_view.compatibility_rows:
        _validate_compatibility_row(row)
        if row.scope_object_ref not in retained:
            raise CMEEStage1ContractError(
                "foreground_scope_compatibility_object_unbound"
            )
        profiles = profiles_by_object.setdefault(row.scope_object_ref, [])
        if profiles:
            raise CMEEStage1ContractError(
                "foreground_scope_compatibility_object_identity_conflict"
            )
        profiles.append(row)

    compatibility_basis_fields = tuple(
        field_name
        for axis, field_name in _COMPATIBILITY_FIELD_BY_AXIS.items()
        if axis
        not in {
            ForegroundScopeCompatibilityAxis.REQUIRED_QUALIFIER,
            ForegroundScopeCompatibilityAxis.UNKNOWN,
        }
    )
    for basis_row in basis_rows:
        profiles = tuple(
            profile
            for object_ref in basis_row.scope_object_refs
            for profile in profiles_by_object.get(object_ref, ())
        )
        if not profiles:
            continue
        for field_name in compatibility_basis_fields:
            expected = _canonical(
                value
                for profile in profiles
                for value in getattr(profile, field_name)
            )
            if getattr(basis_row, field_name) != expected:
                raise CMEEStage1ContractError(
                    "foreground_scope_basis_compatibility_mismatch"
                )
        profile_unknowns = {
            value
            for profile in profiles
            for value in profile.material_unknown_refs
        }
        if not set(basis_row.material_unknown_refs).issubset(
            profile_unknowns
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_unknown_compatibility_mismatch"
            )
        profile_qualifiers = {
            value
            for profile in profiles
            for value in profile.required_qualifier_refs
        }
        if not {
            _base_required_qualifier_ref(value)
            for value in basis_row.required_qualifier_refs
        }.issubset(profile_qualifiers):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_qualifier_compatibility_mismatch"
            )

    relation_basis_by_ref: dict[str, ForegroundScopeBasisRow] = {}
    for basis_row in basis_rows:
        relation_refs = basis_row.source_connected_relation_refs
        if basis_row.basis_kind is ForegroundScopeBasisKind.SOURCE_CONNECTED_RELATION:
            if len(relation_refs) != 1:
                raise CMEEStage1ContractError(
                    "foreground_scope_relation_basis_cardinality_invalid"
                )
            relation_ref = relation_refs[0]
            if relation_ref in relation_basis_by_ref:
                raise CMEEStage1ContractError(
                    "foreground_scope_relation_basis_identity_conflict"
                )
            relation_basis_by_ref[relation_ref] = basis_row
        elif relation_refs:
            raise CMEEStage1ContractError(
                "foreground_scope_relation_basis_kind_mismatch"
            )
    relation_by_ref: dict[str, SourceConnectedScopeRelation] = {}
    for relation in grounded_view.source_connected_relations:
        _validate_source_relation(relation)
        relation_basis = relation_basis_by_ref.get(relation.relation_ref)
        if relation_basis is None:
            raise CMEEStage1ContractError(
                "foreground_scope_source_relation_unbound"
            )
        relation_endpoints = {
            relation.source_object_ref,
            relation.target_object_ref,
        }
        if (
            set(relation_basis.scope_object_refs) != relation_endpoints
            or set(relation_basis.source_object_refs) != relation_endpoints
            or relation_basis.source_evidence_refs
            != relation.source_evidence_refs
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_source_relation_basis_mismatch"
            )
        previous = relation_by_ref.get(relation.relation_ref)
        if previous is not None:
            raise CMEEStage1ContractError(
                "foreground_scope_source_relation_identity_conflict"
            )
        relation_by_ref[relation.relation_ref] = relation
    if set(relation_by_ref) != set(relation_basis_by_ref):
        raise CMEEStage1ContractError(
            "foreground_scope_relation_basis_proof_missing"
        )
    relations = tuple(relation_by_ref.values())

    if not retained:
        return ForegroundScopeDerivation(
            schema_version=_SCHEMA_VERSION,
            state=ForegroundScopeDerivationState.NO_SAFE_FOREGROUND_OBJECT,
            foreground_scope=None,
            retained_foreground_source_object_refs=(),
            unresolved_scope_refs=(),
            missing_structure_refs=(),
            derivation_evidence_refs=(),
        )

    missing = set(grounded_view.missing_structure_refs)
    missing_required_qualifiers = {
        (object_ref, value)
        for object_ref in retained
        for profile in profiles_by_object.get(object_ref, ())
        for value in profile.required_qualifier_refs
        if value
        not in {
            _base_required_qualifier_ref(candidate)
            for basis_row in basis_rows
            if object_ref in basis_row.scope_object_refs
            for candidate in basis_row.required_qualifier_refs
        }
    }
    missing.update(
        _missing_ref(
            ForegroundScopeCompatibilityAxis.REQUIRED_QUALIFIER.value,
            object_ref,
            value,
        )
        for object_ref, value in missing_required_qualifiers
    )
    missing_material_unknowns = {
        (object_ref, value)
        for object_ref in retained
        for profile in profiles_by_object.get(object_ref, ())
        for value in profile.material_unknown_refs
        if value
        not in {
            candidate
            for basis_row in basis_rows
            if object_ref in basis_row.scope_object_refs
            for candidate in basis_row.material_unknown_refs
        }
    }
    missing.update(
        _missing_ref(
            ForegroundScopeCompatibilityAxis.UNKNOWN.value,
            object_ref,
            value,
        )
        for object_ref, value in missing_material_unknowns
    )
    conflicts: set[str] = set()
    for object_ref in retained:
        profiles = tuple(profiles_by_object.get(object_ref, ()))
        if not profiles:
            missing.add(_missing_ref("compatibility-row", object_ref))
            continue
        for profile in profiles:
            for axis in (
                ForegroundScopeCompatibilityAxis.OWNER,
                ForegroundScopeCompatibilityAxis.WORLD,
                ForegroundScopeCompatibilityAxis.EPISTEMIC,
                ForegroundScopeCompatibilityAxis.TIME,
                ForegroundScopeCompatibilityAxis.ASPECT,
                ForegroundScopeCompatibilityAxis.MODALITY,
                ForegroundScopeCompatibilityAxis.POLARITY,
                ForegroundScopeCompatibilityAxis.SCOPE,
            ):
                field_name = _COMPATIBILITY_FIELD_BY_AXIS[axis]
                if not getattr(profile, field_name):
                    missing.add(
                        _missing_ref(axis.value, object_ref)
                    )
        for left, right in combinations(profiles, 2):
            for axis in _COMPATIBILITY_AXES_EXACT10:
                field_name = _COMPATIBILITY_FIELD_BY_AXIS[axis]
                left_values = getattr(left, field_name)
                right_values = getattr(right, field_name)
                if left_values == right_values:
                    continue
                if not left_values or not right_values:
                    missing.add(_missing_ref(axis.value, object_ref))
                else:
                    conflicts.add(object_ref)

    def basis_axis_values(
        basis_row: ForegroundScopeBasisRow,
        field_name: str,
    ) -> Tuple[str, ...]:
        explicit = getattr(basis_row, field_name)
        if field_name == "required_qualifier_refs":
            if explicit:
                return _canonical(
                    _base_required_qualifier_ref(value)
                    for value in explicit
                )
            return _canonical(
                value
                for object_ref in basis_row.scope_object_refs
                for profile in profiles_by_object.get(object_ref, ())
                for value in profile.required_qualifier_refs
            )
        if field_name == "material_unknown_refs" and not explicit:
            return _canonical(
                value
                for object_ref in basis_row.scope_object_refs
                for profile in profiles_by_object.get(object_ref, ())
                for value in profile.material_unknown_refs
            )
        return explicit

    # Compare the admitted basis rows themselves.  Object-level profiles are
    # provenance, but collapsing rows to one profile must not erase a typed
    # qualifier or unknown difference on the same scope object.
    for left_row, right_row in combinations(basis_rows, 2):
        left_objects = set(left_row.scope_object_refs)
        right_objects = set(right_row.scope_object_refs)
        distinct_pairs = tuple(
            (left_ref, right_ref)
            for left_ref, right_ref in product(
                left_row.scope_object_refs,
                right_row.scope_object_refs,
            )
            if left_ref != right_ref
        )
        relation_bridges_rows = (
            left_objects != right_objects
            and bool(distinct_pairs)
            and all(
                _relation_connects(relations, left_ref, right_ref)
                for left_ref, right_ref in distinct_pairs
            )
        )
        for axis in _COMPATIBILITY_AXES_EXACT10:
            field_name = _COMPATIBILITY_FIELD_BY_AXIS[axis]
            left_values = basis_axis_values(left_row, field_name)
            right_values = basis_axis_values(right_row, field_name)
            if left_values == right_values:
                continue
            pair_objects = _canonical((*left_objects, *right_objects))
            if not left_values or not right_values:
                missing.add(_missing_ref(axis.value, *pair_objects))
            elif (
                (
                    axis
                    is ForegroundScopeCompatibilityAxis.REQUIRED_QUALIFIER
                    and bool(missing_required_qualifiers)
                )
                or (
                    axis is ForegroundScopeCompatibilityAxis.UNKNOWN
                    and bool(missing_material_unknowns)
                )
            ) and (
                set(left_values) < set(right_values)
                or set(right_values) < set(left_values)
            ):
                missing.add(_missing_ref(axis.value, *pair_objects))
            elif not relation_bridges_rows:
                conflicts.update(pair_objects)

    for left_ref, right_ref in _material_object_pairs(basis_rows):
        left_profiles = tuple(profiles_by_object.get(left_ref, ()))
        right_profiles = tuple(profiles_by_object.get(right_ref, ()))
        same_object = left_ref == right_ref
        connected = _relation_connects(relations, left_ref, right_ref)
        if not same_object and not connected:
            missing.add(
                _missing_ref(
                    "source-connected-relation", left_ref, right_ref
                )
            )
        for left, right in product(left_profiles, right_profiles):
            for axis in _COMPATIBILITY_AXES_EXACT10:
                field_name = _COMPATIBILITY_FIELD_BY_AXIS[axis]
                left_values = getattr(left, field_name)
                right_values = getattr(right, field_name)
                if left_values == right_values:
                    continue
                if not left_values or not right_values:
                    missing.add(
                        _missing_ref(axis.value, left_ref, right_ref)
                    )
                elif same_object or not connected:
                    conflicts.update((left_ref, right_ref))

    if conflicts:
        return ForegroundScopeDerivation(
            schema_version=_SCHEMA_VERSION,
            state=(
                ForegroundScopeDerivationState.COMPETING_MATERIAL_SCOPES
            ),
            foreground_scope=None,
            retained_foreground_source_object_refs=retained,
            unresolved_scope_refs=_canonical(conflicts),
            missing_structure_refs=(),
            derivation_evidence_refs=evidence,
        )
    if missing:
        return ForegroundScopeDerivation(
            schema_version=_SCHEMA_VERSION,
            state=(
                ForegroundScopeDerivationState.FOREGROUND_SCOPE_STRUCTURE_INSUFFICIENT
            ),
            foreground_scope=None,
            retained_foreground_source_object_refs=retained,
            unresolved_scope_refs=(),
            missing_structure_refs=_canonical(missing),
            derivation_evidence_refs=evidence,
        )
    scope = _canonical_scope(basis_rows)
    return ForegroundScopeDerivation(
        schema_version=_SCHEMA_VERSION,
        state=ForegroundScopeDerivationState.FOREGROUND_SCOPE_AVAILABLE,
        foreground_scope=scope,
        retained_foreground_source_object_refs=retained,
        unresolved_scope_refs=(),
        missing_structure_refs=(),
        derivation_evidence_refs=evidence,
    )


_DISPOSITION_BY_DERIVATION_STATE = {
    ForegroundScopeDerivationState.FOREGROUND_SCOPE_AVAILABLE: (
        ForegroundScopeDispositionCode.AVAILABLE
    ),
    ForegroundScopeDerivationState.COMPETING_MATERIAL_SCOPES: (
        ForegroundScopeDispositionCode.LIMITED_COMPETING_MATERIAL_READINGS
    ),
    ForegroundScopeDerivationState.FOREGROUND_SCOPE_STRUCTURE_INSUFFICIENT: (
        ForegroundScopeDispositionCode.LIMITED_STRUCTURE_INSUFFICIENT
    ),
    ForegroundScopeDerivationState.NO_SAFE_FOREGROUND_OBJECT: (
        ForegroundScopeDispositionCode.STRUCTURE_INSUFFICIENT_STOP
    ),
}

if set(_DISPOSITION_BY_DERIVATION_STATE) != set(
    ForegroundScopeDerivationState
):
    raise RuntimeError("foreground_scope_disposition_mapping_not_exhaustive")


def foreground_scope_disposition(
    derivation: ForegroundScopeDerivation,
) -> ForegroundScopeDisposition:
    """Map all exact4 derivation states to the closed IM01 disposition."""

    if type(derivation) is not ForegroundScopeDerivation:
        raise CMEEStage1ContractError(
            "foreground_scope_disposition_derivation_invalid"
        )
    if (
        derivation.schema_version != _SCHEMA_VERSION
        or type(derivation.state) is not ForegroundScopeDerivationState
        or any(
            not _is_canonical(values)
            for values in (
                derivation.retained_foreground_source_object_refs,
                derivation.unresolved_scope_refs,
                derivation.missing_structure_refs,
                derivation.derivation_evidence_refs,
            )
        )
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_disposition_derivation_invalid"
        )
    try:
        code = _DISPOSITION_BY_DERIVATION_STATE[derivation.state]
    except (KeyError, TypeError):
        raise CMEEStage1ContractError(
            "foreground_scope_disposition_state_invalid"
        ) from None
    if code is ForegroundScopeDispositionCode.AVAILABLE:
        valid = (
            type(derivation.foreground_scope) is ForegroundScope
            and bool(derivation.retained_foreground_source_object_refs)
            and derivation.retained_foreground_source_object_refs
            == derivation.foreground_scope.integrated_scope_object_refs
            and derivation.foreground_scope.scope_id
            == foreground_scope_id(derivation.foreground_scope)
            and not derivation.unresolved_scope_refs
            and not derivation.missing_structure_refs
            and bool(derivation.derivation_evidence_refs)
            and derivation.derivation_evidence_refs
            == derivation.foreground_scope.source_evidence_refs
        )
    elif code is ForegroundScopeDispositionCode.LIMITED_COMPETING_MATERIAL_READINGS:
        valid = (
            derivation.foreground_scope is None
            and bool(derivation.retained_foreground_source_object_refs)
            and bool(derivation.unresolved_scope_refs)
            and not derivation.missing_structure_refs
            and bool(derivation.derivation_evidence_refs)
        )
    elif code is ForegroundScopeDispositionCode.LIMITED_STRUCTURE_INSUFFICIENT:
        valid = (
            derivation.foreground_scope is None
            and bool(derivation.retained_foreground_source_object_refs)
            and not derivation.unresolved_scope_refs
            and bool(derivation.missing_structure_refs)
            and bool(derivation.derivation_evidence_refs)
        )
    else:
        valid = (
            derivation.foreground_scope is None
            and not derivation.retained_foreground_source_object_refs
            and not derivation.unresolved_scope_refs
            and not derivation.missing_structure_refs
            and not derivation.derivation_evidence_refs
        )
    if not valid:
        raise CMEEStage1ContractError(
            "foreground_scope_disposition_cardinality_invalid"
        )
    return ForegroundScopeDisposition(
        schema_version=_SCHEMA_VERSION,
        code=code,
        derivation_state=derivation.state,
        retained_foreground_source_object_refs=(
            derivation.retained_foreground_source_object_refs
        ),
        unresolved_scope_refs=derivation.unresolved_scope_refs,
        missing_structure_refs=derivation.missing_structure_refs,
    )


__all__ = (
    "ForegroundScopeDisposition",
    "ForegroundScopeDispositionCode",
    "GroundedSituationView",
    "SourceConnectedScopeRelation",
    "derive_foreground_scope_closed",
    "derive_grounded_situation_view",
    "foreground_scope_disposition",
)
