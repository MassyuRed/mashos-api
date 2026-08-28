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
    CounterfactualMutationKind,
    CounterfactualMutationRow,
    DifferenceAxis,
    DifferenceConfiguration,
    DifferenceConfigurationDerivation,
    DifferenceConfigurationDerivationState,
    DifferenceConfigurationSet,
    DifferenceInvariantCode,
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
    InputSpecificMeaningStructure,
    MeaningComponentSemanticKey,
    MeaningSemanticSignature,
    MeaningEdge,
    MeaningNode,
    ObservedDistinctionDerivationKind,
    ObservedDistinctionRow,
    OwnerClass,
    PreMeaningGroundedInputs,
    QualifiedEventStateConfiguration,
    RelationDirectionRow,
    RelationalConfiguration,
    RequiredDifferenceRow,
    RequirementBundle,
    RequirementBundleDerivation,
    RequirementBundleDerivationState,
    RequirementBundleSet,
    SourceOwnerDisposition,
    VisibleAuthority,
    WholeReadingConsequenceCode,
    WholeReadingConsequenceRow,
    counterfactual_mutation_id,
    difference_configuration_id,
    foreground_scope_basis_row_ref,
    foreground_scope_id,
    observed_distinction_id,
    required_difference_id,
    requirement_bundle_id,
    stage1_canonical_json_bytes,
    validate_counterfactual_mutation_local_shape,
    validate_meaning_semantic_signature_local_shape,
    validate_version_qualified_ref,
    whole_reading_consequence_id,
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


_DIFFERENCE_CONFIGURATION_REF_VERSION = (
    "cocolon.cmee.emlis.difference_configuration.v1"
)
_OBSERVED_DISTINCTION_REF_VERSION = (
    "cocolon.cmee.emlis.observed_distinction.v1"
)
_COUNTERFACTUAL_MUTATION_REF_VERSION = (
    "cocolon.cmee.emlis.counterfactual_mutation.v1"
)
_REQUIRED_DIFFERENCE_REF_VERSION = (
    "cocolon.cmee.emlis.required_difference.v1"
)
_REQUIREMENT_BUNDLE_REF_VERSION = (
    "cocolon.cmee.emlis.requirement_bundle.v1"
)
_WHOLE_READING_CONSEQUENCE_REF_VERSION = (
    "cocolon.cmee.emlis.whole_reading_consequence.v1"
)

_OBSERVED_ORIGINS_EXACT5 = frozenset(ObservedDistinctionDerivationKind)
_DIFFERENCE_AXES_EXACT10 = frozenset(DifferenceAxis)
_DIFFERENCE_INVARIANTS_EXACT10 = frozenset(DifferenceInvariantCode)
_COUNTERFACTUAL_MUTATIONS_EXACT12 = frozenset(CounterfactualMutationKind)
_CONFIGURATION_STATES_EXACT4 = frozenset(
    DifferenceConfigurationDerivationState
)
_BUNDLE_STATES_EXACT3 = frozenset(RequirementBundleDerivationState)
_WHOLE_READING_CODES_EXACT7 = frozenset(WholeReadingConsequenceCode)


def _configuration_object_refs(
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    if type(configuration) is RelationalConfiguration:
        return configuration.endpoint_component_refs
    if type(configuration) is QualifiedEventStateConfiguration:
        return (configuration.predicate_ref,)
    raise CMEEStage1ContractError(
        "difference_configuration_type_invalid"
    )


def _configuration_qualifier_refs(
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    if type(configuration) is RelationalConfiguration:
        return configuration.source_qualifier_refs
    if type(configuration) is QualifiedEventStateConfiguration:
        return _canonical(
            (
                *configuration.modality_refs,
                *configuration.time_refs,
                *configuration.aspect_refs,
                *configuration.scope_refs,
                *configuration.qualifier_refs,
            )
        )
    raise CMEEStage1ContractError(
        "difference_configuration_type_invalid"
    )


def _configuration_evidence_refs(
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    if type(configuration) not in {
        RelationalConfiguration,
        QualifiedEventStateConfiguration,
    }:
        raise CMEEStage1ContractError(
            "difference_configuration_type_invalid"
        )
    return configuration.source_evidence_refs


def _configuration_sort_key(
    configuration: DifferenceConfiguration,
) -> tuple[object, ...]:
    """Canonical serialization key; never a selection or priority key."""

    if type(configuration) is RelationalConfiguration:
        return (
            "relational",
            configuration.endpoint_component_refs,
            configuration.relation_path_refs,
            tuple(
                (
                    row.relation_kind.value,
                    row.source_endpoint_ref,
                    row.target_endpoint_ref,
                    row.relation_ref,
                )
                for row in configuration.direction_rows
            ),
            configuration.source_qualifier_refs,
            configuration.source_evidence_refs,
        )
    if type(configuration) is QualifiedEventStateConfiguration:
        return (
            "qualified-event-state",
            configuration.predicate_ref,
            configuration.owner_ref,
            configuration.modality_refs,
            configuration.time_refs,
            configuration.aspect_refs,
            configuration.scope_refs,
            configuration.qualifier_refs,
            configuration.source_evidence_refs,
        )
    raise CMEEStage1ContractError(
        "difference_configuration_type_invalid"
    )


def _profile_source_qualifiers(
    profile: ForegroundScopeObjectCompatibilityRow,
) -> Tuple[str, ...]:
    # ``world`` and material unknown are deliberately included.  They are
    # source-bound modifiers, not a free materiality judgement.
    return _canonical(
        (
            *profile.world_refs,
            *(
                "epistemic:"
                f"{value.split(':', 1)[1].split('@', 1)[0]}"
                for value in profile.epistemic_state_refs
            ),
            *profile.time_refs,
            *profile.aspect_refs,
            *profile.modality_refs,
            *profile.polarity_refs,
            *profile.scope_refs,
            *profile.required_qualifier_refs,
            *profile.material_unknown_refs,
        )
    )


def _object_evidence_refs(
    grounded_view: GroundedSituationView,
    *,
    object_ref: str,
    foreground_scope: ForegroundScope,
) -> Tuple[str, ...]:
    return _canonical(
        evidence_ref
        for row in grounded_view.basis_rows
        if object_ref in row.scope_object_refs
        for evidence_ref in row.source_evidence_refs
        if evidence_ref in foreground_scope.source_evidence_refs
    )


def _relation_components(
    relations: Sequence[SourceConnectedScopeRelation],
) -> Tuple[Tuple[SourceConnectedScopeRelation, ...], ...]:
    """Return connected source-relation components without path invention."""

    remaining = set(range(len(relations)))
    components: list[Tuple[SourceConnectedScopeRelation, ...]] = []
    while remaining:
        seed = min(
            remaining,
            key=lambda index: (
                relations[index].relation_kind.value,
                relations[index].source_object_ref,
                relations[index].target_object_ref,
                relations[index].relation_ref,
            ),
        )
        selected = {seed}
        endpoints = {
            relations[seed].source_object_ref,
            relations[seed].target_object_ref,
        }
        changed = True
        while changed:
            changed = False
            for index in tuple(remaining - selected):
                relation = relations[index]
                if endpoints.intersection(
                    {
                        relation.source_object_ref,
                        relation.target_object_ref,
                    }
                ):
                    selected.add(index)
                    endpoints.update(
                        {
                            relation.source_object_ref,
                            relation.target_object_ref,
                        }
                    )
                    changed = True
        remaining.difference_update(selected)
        components.append(
            tuple(
                sorted(
                    (relations[index] for index in selected),
                    key=lambda row: (
                        row.relation_kind.value,
                        row.source_object_ref,
                        row.target_object_ref,
                        row.relation_ref,
                    ),
                )
            )
        )
    return tuple(components)


def derive_difference_configuration_set(
    grounded_view: GroundedSituationView,
    foreground_scope_derivation: ForegroundScopeDerivation,
) -> tuple[
    DifferenceConfigurationDerivation,
    Tuple[DifferenceConfiguration, ...],
]:
    """Derive the closed 1..5 relational/qualified IM02 configuration set."""

    if type(grounded_view) is not GroundedSituationView:
        raise CMEEStage1ContractError(
            "difference_configuration_grounded_view_invalid"
        )
    if type(foreground_scope_derivation) is not ForegroundScopeDerivation:
        raise CMEEStage1ContractError(
            "difference_configuration_foreground_derivation_invalid"
        )
    if (
        grounded_view.schema_version != _SCHEMA_VERSION
        or foreground_scope_derivation.schema_version != _SCHEMA_VERSION
        or type(foreground_scope_derivation.state)
        is not ForegroundScopeDerivationState
    ):
        raise CMEEStage1ContractError(
            "difference_configuration_input_schema_invalid"
        )

    retained = foreground_scope_derivation.retained_foreground_source_object_refs
    evidence = foreground_scope_derivation.derivation_evidence_refs
    if (
        foreground_scope_derivation.state
        is ForegroundScopeDerivationState.NO_SAFE_FOREGROUND_OBJECT
    ):
        return (
            DifferenceConfigurationDerivation(
                schema_version=_SCHEMA_VERSION,
                state=(
                    DifferenceConfigurationDerivationState.NO_FOREGROUND_OBJECT
                ),
                configuration_set=None,
                foreground_source_object_refs=(),
                missing_structure_refs=(),
                derivation_evidence_refs=(),
            ),
            (),
        )
    if (
        foreground_scope_derivation.state
        is not ForegroundScopeDerivationState.FOREGROUND_SCOPE_AVAILABLE
        or type(foreground_scope_derivation.foreground_scope)
        is not ForegroundScope
    ):
        missing = foreground_scope_derivation.missing_structure_refs
        if not missing:
            missing = _canonical(
                (
                    *(
                        f"difference-configuration:unresolved:{value}"
                        for value in foreground_scope_derivation.unresolved_scope_refs
                    ),
                    "difference-configuration:foreground-scope-unavailable",
                )
            )
        return (
            DifferenceConfigurationDerivation(
                schema_version=_SCHEMA_VERSION,
                state=(
                    DifferenceConfigurationDerivationState.UPSTREAM_STRUCTURE_INSUFFICIENT
                ),
                configuration_set=None,
                foreground_source_object_refs=_canonical(retained),
                missing_structure_refs=_canonical(missing),
                derivation_evidence_refs=_canonical(evidence),
            ),
            (),
        )

    scope = foreground_scope_derivation.foreground_scope
    scope_objects = set(scope.integrated_scope_object_refs)
    profiles_by_object = {
        row.scope_object_ref: row
        for row in grounded_view.compatibility_rows
        if row.scope_object_ref in scope_objects
    }
    missing: list[str] = []
    if set(profiles_by_object) != scope_objects:
        missing.extend(
            _missing_ref("difference-compatibility", ref)
            for ref in sorted(scope_objects - set(profiles_by_object))
        )

    admitted_relations = tuple(
        relation
        for relation in grounded_view.source_connected_relations
        if {
            relation.source_object_ref,
            relation.target_object_ref,
        }.issubset(scope_objects)
    )
    configurations: list[DifferenceConfiguration] = []
    relationally_covered: set[str] = set()
    for relation_component in _relation_components(admitted_relations):
        endpoints = _canonical(
            ref
            for relation in relation_component
            for ref in (
                relation.source_object_ref,
                relation.target_object_ref,
            )
        )
        if not 2 <= len(endpoints) <= 5:
            missing.append(
                _missing_ref("relation-endpoint-cardinality", *endpoints)
            )
            continue
        direction_rows = tuple(
            RelationDirectionRow(
                schema_version=_SCHEMA_VERSION,
                relation_ref=relation.relation_ref,
                relation_kind=relation.relation_kind,
                source_endpoint_ref=relation.source_object_ref,
                target_endpoint_ref=relation.target_object_ref,
            )
            for relation in relation_component
        )
        relation_evidence = _canonical(
            ref
            for relation in relation_component
            for ref in relation.source_evidence_refs
            if ref in scope.source_evidence_refs
        )
        if not relation_evidence:
            missing.append(
                _missing_ref(
                    "relation-evidence",
                    *(relation.relation_ref for relation in relation_component),
                )
            )
            continue
        qualifiers = _canonical(
            qualifier
            for endpoint in endpoints
            for profile in (profiles_by_object.get(endpoint),)
            if profile is not None
            for qualifier in _profile_source_qualifiers(profile)
        )
        configuration = RelationalConfiguration(
            schema_version=_SCHEMA_VERSION,
            configuration_id=(
                "difference-configuration:pending"
                f"@{_DIFFERENCE_CONFIGURATION_REF_VERSION}"
            ),
            endpoint_component_refs=endpoints,
            relation_path_refs=_canonical(
                relation.relation_ref for relation in relation_component
            ),
            direction_rows=direction_rows,
            source_qualifier_refs=qualifiers,
            source_evidence_refs=relation_evidence,
        )
        configuration = replace(
            configuration,
            configuration_id=difference_configuration_id(configuration),
        )
        configurations.append(configuration)
        relationally_covered.update(endpoints)

    # A source object already represented by a relational configuration is
    # not duplicated as a qualified configuration.  This keeps the set a
    # semantic partition rather than an optional-feature counter.
    for object_ref in sorted(scope_objects - relationally_covered):
        profile = profiles_by_object.get(object_ref)
        if profile is None:
            continue
        if len(profile.owner_refs) != 1:
            missing.append(_missing_ref("qualified-owner", object_ref))
            continue
        qualifiers = _profile_source_qualifiers(profile)
        modifier_refs = _canonical(
            (
                *profile.modality_refs,
                *profile.time_refs,
                *profile.aspect_refs,
                *profile.scope_refs,
                *qualifiers,
            )
        )
        if not modifier_refs:
            continue
        object_evidence = _object_evidence_refs(
            grounded_view,
            object_ref=object_ref,
            foreground_scope=scope,
        )
        if not object_evidence:
            missing.append(_missing_ref("qualified-evidence", object_ref))
            continue
        configuration = QualifiedEventStateConfiguration(
            schema_version=_SCHEMA_VERSION,
            configuration_id=(
                "difference-configuration:pending"
                f"@{_DIFFERENCE_CONFIGURATION_REF_VERSION}"
            ),
            predicate_ref=object_ref,
            owner_ref=profile.owner_refs[0],
            modality_refs=profile.modality_refs,
            time_refs=profile.time_refs,
            aspect_refs=profile.aspect_refs,
            scope_refs=profile.scope_refs,
            qualifier_refs=qualifiers,
            source_evidence_refs=object_evidence,
        )
        configuration = replace(
            configuration,
            configuration_id=difference_configuration_id(configuration),
        )
        configurations.append(configuration)

    ordered_configurations = tuple(
        sorted(configurations, key=_configuration_sort_key)
    )
    if len(ordered_configurations) > 5:
        missing.append(
            _missing_ref(
                "configuration-cardinality-overflow",
                str(len(ordered_configurations)),
            )
        )
    if missing:
        return (
            DifferenceConfigurationDerivation(
                schema_version=_SCHEMA_VERSION,
                state=(
                    DifferenceConfigurationDerivationState.UPSTREAM_STRUCTURE_INSUFFICIENT
                ),
                configuration_set=None,
                foreground_source_object_refs=_canonical(scope_objects),
                missing_structure_refs=_canonical(missing),
                derivation_evidence_refs=scope.source_evidence_refs,
            ),
            (),
        )
    if not ordered_configurations:
        return (
            DifferenceConfigurationDerivation(
                schema_version=_SCHEMA_VERSION,
                state=(
                    DifferenceConfigurationDerivationState.THIN_NO_SAFE_CONFIGURATION
                ),
                configuration_set=None,
                foreground_source_object_refs=_canonical(scope_objects),
                missing_structure_refs=(),
                derivation_evidence_refs=(),
            ),
            (),
        )

    configuration_set = DifferenceConfigurationSet(
        schema_version=_SCHEMA_VERSION,
        foreground_scope_ref=scope.scope_id,
        configuration_refs=tuple(
            configuration.configuration_id
            for configuration in ordered_configurations
        ),
        source_evidence_refs=_canonical(
            ref
            for configuration in ordered_configurations
            for ref in _configuration_evidence_refs(configuration)
        ),
    )
    return (
        DifferenceConfigurationDerivation(
            schema_version=_SCHEMA_VERSION,
            state=(
                DifferenceConfigurationDerivationState.CONFIGURATION_SET_AVAILABLE
            ),
            configuration_set=configuration_set,
            foreground_source_object_refs=_canonical(scope_objects),
            missing_structure_refs=(),
            derivation_evidence_refs=configuration_set.source_evidence_refs,
        ),
        ordered_configurations,
    )


def _new_observed_distinction(
    *,
    configuration_ref: str,
    derivation_kind: ObservedDistinctionDerivationKind,
    axis: DifferenceAxis,
    contrasted_component_refs: Sequence[str],
    source_qualifier_refs: Sequence[str],
    source_evidence_refs: Sequence[str],
) -> ObservedDistinctionRow:
    row = ObservedDistinctionRow(
        schema_version=_SCHEMA_VERSION,
        distinction_id=(
            "observed-distinction:pending"
            f"@{_OBSERVED_DISTINCTION_REF_VERSION}"
        ),
        configuration_ref=configuration_ref,
        derivation_kind=derivation_kind,
        axis=axis,
        contrasted_component_refs=_canonical(contrasted_component_refs),
        source_qualifier_refs=_canonical(source_qualifier_refs),
        source_evidence_refs=_canonical(source_evidence_refs),
    )
    return replace(row, distinction_id=observed_distinction_id(row))


def _qualifier_axis(values: Sequence[str]) -> DifferenceAxis:
    prefixes = {value.split(":", 1)[0] for value in values if ":" in value}
    if "world" in prefixes:
        return DifferenceAxis.INTERNAL_VS_EXTERNAL
    if prefixes.intersection({"time", "time_scope"}):
        return DifferenceAxis.BEFORE_VS_AFTER
    if "modality" in prefixes:
        return DifferenceAxis.HISTORY_VS_PATTERN_VS_POSSIBILITY
    if "unknown" in prefixes:
        return DifferenceAxis.RESOLVED_VS_UNRESOLVED
    if prefixes.intersection({"scope", "aspect", "qualifier"}):
        return DifferenceAxis.CHANGE_VS_GENERALIZATION
    if "polarity" in prefixes:
        return DifferenceAxis.FACT_VS_INTERPRETATION
    if prefixes.intersection({"epistemic", "epistemic-state"}):
        return DifferenceAxis.FACT_VS_INTERPRETATION
    return DifferenceAxis.INTENTION_VS_OUTPUT


def _derive_observed_distinctions(
    grounded_view: GroundedSituationView,
    configurations: Sequence[DifferenceConfiguration],
) -> Tuple[ObservedDistinctionRow, ...]:
    profiles_by_object = {
        row.scope_object_ref: row for row in grounded_view.compatibility_rows
    }
    rows: list[ObservedDistinctionRow] = []
    typed_axes = (
        ("world_refs", DifferenceAxis.INTERNAL_VS_EXTERNAL),
        ("time_refs", DifferenceAxis.BEFORE_VS_AFTER),
        (
            "epistemic_state_refs",
            DifferenceAxis.FACT_VS_INTERPRETATION,
        ),
        (
            "modality_refs",
            DifferenceAxis.HISTORY_VS_PATTERN_VS_POSSIBILITY,
        ),
        ("polarity_refs", DifferenceAxis.CHANGE_VS_GENERALIZATION),
    )
    for configuration in configurations:
        objects = _configuration_object_refs(configuration)
        qualifiers = _configuration_qualifier_refs(configuration)
        evidence = _configuration_evidence_refs(configuration)
        if type(configuration) is RelationalConfiguration:
            for direction in configuration.direction_rows:
                rows.append(
                    _new_observed_distinction(
                        configuration_ref=configuration.configuration_id,
                        derivation_kind=(
                            ObservedDistinctionDerivationKind.BINARY_ENDPOINT_AND_DIRECTION
                        ),
                        axis=DifferenceAxis.ENDPOINT_A_VS_ENDPOINT_B,
                        contrasted_component_refs=(
                            direction.source_endpoint_ref,
                            direction.target_endpoint_ref,
                        ),
                        source_qualifier_refs=qualifiers,
                        source_evidence_refs=evidence,
                    )
                )
            for left_ref, right_ref in combinations(objects, 2):
                left = profiles_by_object.get(left_ref)
                right = profiles_by_object.get(right_ref)
                if left is None or right is None:
                    continue
                for field_name, axis in typed_axes:
                    left_values = getattr(left, field_name)
                    right_values = getattr(right, field_name)
                    if (
                        not left_values
                        or not right_values
                        or left_values == right_values
                    ):
                        continue
                    typed_qualifiers = (
                        tuple(
                            "epistemic:"
                            f"{value.split(':', 1)[1].split('@', 1)[0]}"
                            for value in (*left_values, *right_values)
                        )
                        if field_name == "epistemic_state_refs"
                        else (*left_values, *right_values)
                    )
                    rows.append(
                        _new_observed_distinction(
                            configuration_ref=configuration.configuration_id,
                            derivation_kind=(
                                ObservedDistinctionDerivationKind.TYPED_AXIS_CONTRAST
                            ),
                            axis=axis,
                            contrasted_component_refs=(left_ref, right_ref),
                            source_qualifier_refs=typed_qualifiers,
                            source_evidence_refs=evidence,
                        )
                    )
        elif type(configuration) is QualifiedEventStateConfiguration:
            rows.append(
                _new_observed_distinction(
                    configuration_ref=configuration.configuration_id,
                    derivation_kind=(
                        ObservedDistinctionDerivationKind.QUALIFIED_PREDICATE_OWNER_MODIFIER
                    ),
                    axis=_qualifier_axis(qualifiers),
                    contrasted_component_refs=(
                        configuration.predicate_ref,
                        configuration.owner_ref,
                    ),
                    source_qualifier_refs=qualifiers,
                    source_evidence_refs=evidence,
                )
            )
        else:
            raise CMEEStage1ContractError(
                "difference_configuration_type_invalid"
            )

        bound_qualifiers = tuple(
            value for value in qualifiers if not value.startswith("unknown:")
        )
        if bound_qualifiers:
            rows.append(
                _new_observed_distinction(
                    configuration_ref=configuration.configuration_id,
                    derivation_kind=(
                        ObservedDistinctionDerivationKind.BOUND_QUALIFIER
                    ),
                    axis=_qualifier_axis(bound_qualifiers),
                    contrasted_component_refs=objects,
                    source_qualifier_refs=bound_qualifiers,
                    source_evidence_refs=evidence,
                )
            )
        material_unknowns = tuple(
            value for value in qualifiers if value.startswith("unknown:")
        )
        if material_unknowns:
            rows.append(
                _new_observed_distinction(
                    configuration_ref=configuration.configuration_id,
                    derivation_kind=(
                        ObservedDistinctionDerivationKind.BOUND_MATERIAL_UNKNOWN
                    ),
                    axis=DifferenceAxis.RESOLVED_VS_UNRESOLVED,
                    contrasted_component_refs=objects,
                    source_qualifier_refs=material_unknowns,
                    source_evidence_refs=evidence,
                )
            )

    by_ref: dict[str, ObservedDistinctionRow] = {}
    for row in rows:
        previous = by_ref.get(row.distinction_id)
        if previous is not None and previous != row:
            raise CMEEStage1ContractError(
                "observed_distinction_identity_collision"
            )
        by_ref[row.distinction_id] = row
    origin_order = {
        value: index
        for index, value in enumerate(ObservedDistinctionDerivationKind)
    }
    axis_order = {value: index for index, value in enumerate(DifferenceAxis)}
    configuration_order = {
        row.configuration_id: index
        for index, row in enumerate(configurations)
    }
    return tuple(
        sorted(
            by_ref.values(),
            key=lambda row: (
                configuration_order[row.configuration_ref],
                origin_order[row.derivation_kind],
                axis_order[row.axis],
                row.contrasted_component_refs,
                row.source_qualifier_refs,
                row.source_evidence_refs,
            ),
        )
    )


def _closed_replacement(value: str, *, axis: str) -> str:
    if axis == "world":
        replacements = {
            "world:internal": "world:external",
            "world:external": "world:internal",
            "world:relationship": "world:unknown",
            "world:unknown": "world:external",
        }
        return replacements.get(value, "world:unknown")
    if axis == "time":
        prefix = "time_scope:" if value.startswith("time_scope:") else "time:"
        body = value.split(":", 1)[-1]
        replacements = {
            "past": "future",
            "present": "future",
            "future": "past",
            "past_to_present": "present_to_future",
            "present_to_future": "past_to_present",
            "continuing": "future",
            "current_input": "future",
        }
        replacement = replacements.get(body)
        if replacement is None:
            raise CMEEStage1ContractError(
                "counterfactual_time_replacement_source_not_closed"
            )
        return f"{prefix}{replacement}"
    raise CMEEStage1ContractError(
        "counterfactual_replacement_axis_invalid"
    )


def _mutation_spec(
    row: ObservedDistinctionRow,
    configuration: DifferenceConfiguration,
) -> tuple[
    CounterfactualMutationKind,
    Tuple[str, ...],
    Tuple[str, ...],
    Tuple[DifferenceInvariantCode, ...],
]:
    objects = _configuration_object_refs(configuration)
    qualifiers = row.source_qualifier_refs
    if (
        row.derivation_kind
        is ObservedDistinctionDerivationKind.BINARY_ENDPOINT_AND_DIRECTION
    ):
        matching_directions = tuple(
            value
            for value in configuration.direction_rows
            if {
                value.source_endpoint_ref,
                value.target_endpoint_ref,
            }
            == set(row.contrasted_component_refs)
        )
        if len(matching_directions) != 1:
            raise CMEEStage1ContractError(
                "binary_observed_direction_unbound"
            )
        direction = matching_directions[0]
        if direction.relation_kind in {
            ForegroundScopeRelationKind.CONTINUATION,
            ForegroundScopeRelationKind.CORRECTION,
        }:
            directional_endpoints = (
                direction.source_endpoint_ref,
                direction.target_endpoint_ref,
            )
            return (
                CounterfactualMutationKind.SWAP_ENDPOINTS,
                directional_endpoints,
                tuple(reversed(directional_endpoints)),
                (DifferenceInvariantCode.DIRECTION_REVERSAL,),
            )
        return (
            CounterfactualMutationKind.DELETE_ENDPOINT,
            (direction.target_endpoint_ref,),
            (),
            (DifferenceInvariantCode.ENDPOINT_COLLAPSE,),
        )
    if (
        row.derivation_kind
        is ObservedDistinctionDerivationKind.QUALIFIED_PREDICATE_OWNER_MODIFIER
    ):
        return (
            CounterfactualMutationKind.DELETE_PREDICATE,
            (objects[0],),
            (),
            (DifferenceInvariantCode.ENDPOINT_COLLAPSE,),
        )
    if (
        row.derivation_kind
        is ObservedDistinctionDerivationKind.BOUND_MATERIAL_UNKNOWN
    ):
        return (
            CounterfactualMutationKind.PROMOTE_UNKNOWN,
            (qualifiers[0],),
            ("resolution:resolved",),
            (DifferenceInvariantCode.UNKNOWN_ERASURE,),
        )

    if row.axis is DifferenceAxis.INTERNAL_VS_EXTERNAL:
        target = next(
            (value for value in qualifiers if value.startswith("world:")),
            None,
        )
        if target is not None:
            return (
                CounterfactualMutationKind.REPLACE_WORLD,
                (target,),
                (_closed_replacement(target, axis="world"),),
                (DifferenceInvariantCode.WORLD_COLLAPSE,),
            )
    if row.axis is DifferenceAxis.BEFORE_VS_AFTER:
        target = next(
            (
                value
                for value in qualifiers
                if value.startswith(("time:", "time_scope:"))
            ),
            None,
        )
        if target is not None:
            return (
                CounterfactualMutationKind.REPLACE_TIME,
                (target,),
                (_closed_replacement(target, axis="time"),),
                (DifferenceInvariantCode.TEMPORAL_COLLAPSE,),
            )
    if row.axis is DifferenceAxis.WISH_VS_CONSTRAINT and len(objects) >= 2:
        return (
            CounterfactualMutationKind.REPLACE_ROLE,
            ("role:right",),
            ("role:left",),
            (DifferenceInvariantCode.ROLE_COLLAPSE,),
        )

    target = qualifiers[0] if qualifiers else objects[0]
    if target.startswith("modality:"):
        return (
            CounterfactualMutationKind.DELETE_MODALITY,
            (target,),
            (),
            (DifferenceInvariantCode.MODALITY_PROMOTION,),
        )
    if target.startswith("aspect:"):
        return (
            CounterfactualMutationKind.DELETE_ASPECT,
            (target,),
            (),
            (DifferenceInvariantCode.TEMPORAL_COLLAPSE,),
        )
    if target.startswith("scope:"):
        return (
            CounterfactualMutationKind.DELETE_SCOPE,
            (target,),
            (),
            (DifferenceInvariantCode.EXPLICIT_LIMIT_ERASURE,),
        )
    if target.startswith("polarity:"):
        return (
            CounterfactualMutationKind.DELETE_QUALIFIER,
            (target,),
            (),
            (DifferenceInvariantCode.POLARITY_REVERSAL,),
        )
    if target.startswith(("qualifier:", "epistemic:", "epistemic-state:")):
        return (
            CounterfactualMutationKind.DELETE_QUALIFIER,
            (target,),
            (),
            (DifferenceInvariantCode.EXPLICIT_LIMIT_ERASURE,),
        )
    if len(objects) >= 2:
        return (
            CounterfactualMutationKind.REPLACE_ROLE,
            ("role:right",),
            ("role:left",),
            (DifferenceInvariantCode.ROLE_COLLAPSE,),
        )
    if type(configuration) is QualifiedEventStateConfiguration:
        return (
            CounterfactualMutationKind.DELETE_OWNER,
            (configuration.owner_ref,),
            (),
            (DifferenceInvariantCode.ROLE_COLLAPSE,),
        )
    return (
        CounterfactualMutationKind.DELETE_ENDPOINT,
        (objects[-1],),
        (),
        (DifferenceInvariantCode.ENDPOINT_COLLAPSE,),
    )


def _retention_duties_for_configuration(
    grounded_view: GroundedSituationView,
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    objects = set(_configuration_object_refs(configuration))
    return _canonical(
        ref
        for basis in grounded_view.basis_rows
        if objects.intersection(basis.scope_object_refs)
        for ref in (
            *basis.required_retention_duty_refs,
            *basis.layer1_required_object_refs,
        )
    )


def _derive_required_differences(
    grounded_view: GroundedSituationView,
    configurations: Sequence[DifferenceConfiguration],
    observed_rows: Sequence[ObservedDistinctionRow],
) -> tuple[
    Tuple[CounterfactualMutationRow, ...],
    Tuple[RequiredDifferenceRow, ...],
]:
    by_ref = {
        configuration.configuration_id: configuration
        for configuration in configurations
    }
    mutations: list[CounterfactualMutationRow] = []
    required_rows: list[RequiredDifferenceRow] = []
    for observed in observed_rows:
        configuration = by_ref.get(observed.configuration_ref)
        if configuration is None:
            raise CMEEStage1ContractError(
                "observed_distinction_configuration_unbound"
            )
        mutation_kind, targets, replacements, invariants = _mutation_spec(
            observed, configuration
        )
        if mutation_kind not in _COUNTERFACTUAL_MUTATIONS_EXACT12:
            raise CMEEStage1ContractError(
                "counterfactual_mutation_kind_not_closed"
            )
        retention_duties = _retention_duties_for_configuration(
            grounded_view, configuration
        )
        invariant_set = set(invariants)
        if retention_duties:
            invariant_set.add(
                DifferenceInvariantCode.REQUIRED_RETENTION_ERASURE
            )
        canonical_invariants = tuple(
            value
            for value in DifferenceInvariantCode
            if value in invariant_set
        )
        if not canonical_invariants:
            continue
        mutation = CounterfactualMutationRow(
            schema_version=_SCHEMA_VERSION,
            mutation_id=(
                "counterfactual-mutation:pending"
                f"@{_COUNTERFACTUAL_MUTATION_REF_VERSION}"
            ),
            mutation_kind=mutation_kind,
            observed_distinction_ref=observed.distinction_id,
            target_component_refs=tuple(targets),
            replacement_refs=tuple(replacements),
            source_evidence_refs=observed.source_evidence_refs,
        )
        mutation = replace(
            mutation,
            mutation_id=counterfactual_mutation_id(mutation),
        )
        required = RequiredDifferenceRow(
            schema_version=_SCHEMA_VERSION,
            difference_id=(
                "required-difference:pending"
                f"@{_REQUIRED_DIFFERENCE_REF_VERSION}"
            ),
            observed_distinction_ref=observed.distinction_id,
            invariant_codes=canonical_invariants,
            retention_duty_refs=retention_duties,
            counterfactual_mutation_ref=mutation.mutation_id,
        )
        required = replace(
            required,
            difference_id=required_difference_id(required),
        )
        mutations.append(mutation)
        required_rows.append(required)
    # Both tuples retain the semantic Observed Distinction order above; their
    # content-derived IDs never choose or reorder meaning.
    return tuple(mutations), tuple(required_rows)


def _configurations_are_source_connected(
    left: DifferenceConfiguration,
    right: DifferenceConfiguration,
    grounded_view: GroundedSituationView,
) -> bool:
    del grounded_view
    left_objects = set(_configuration_object_refs(left))
    right_objects = set(_configuration_object_refs(right))
    if left_objects.intersection(right_objects):
        return True
    left_paths = (
        set(left.relation_path_refs)
        if type(left) is RelationalConfiguration
        else set()
    )
    right_paths = (
        set(right.relation_path_refs)
        if type(right) is RelationalConfiguration
        else set()
    )
    # Connectivity must be verifiable from the bundle-owned configurations.
    # An external bridge, shared evidence, or identical time value is not an
    # embedded source-connected proof.
    return bool(left_paths.intersection(right_paths))


def derive_requirement_bundle_set(
    grounded_view: GroundedSituationView,
    foreground_scope_derivation: ForegroundScopeDerivation,
    difference_configuration_derivation: DifferenceConfigurationDerivation,
    configurations: Sequence[DifferenceConfiguration],
    observed_distinction_rows: Sequence[ObservedDistinctionRow],
    required_difference_rows: Sequence[RequiredDifferenceRow],
) -> tuple[RequirementBundleDerivation, Tuple[RequirementBundle, ...]]:
    """Bundle only required, source-connected configurations (never evidence)."""

    if (
        type(difference_configuration_derivation)
        is not DifferenceConfigurationDerivation
        or type(foreground_scope_derivation) is not ForegroundScopeDerivation
    ):
        raise CMEEStage1ContractError(
            "requirement_bundle_derivation_input_invalid"
        )
    state = difference_configuration_derivation.state
    if state is not DifferenceConfigurationDerivationState.CONFIGURATION_SET_AVAILABLE:
        missing = difference_configuration_derivation.missing_structure_refs
        if not missing:
            missing = (
                f"requirement-bundle:upstream:{state.value}",
            )
        return (
            RequirementBundleDerivation(
                schema_version=_SCHEMA_VERSION,
                state=(
                    RequirementBundleDerivationState.UPSTREAM_STRUCTURE_INSUFFICIENT
                ),
                bundle_set=None,
                missing_structure_refs=_canonical(missing),
                derivation_evidence_refs=(
                    difference_configuration_derivation.derivation_evidence_refs
                ),
            ),
            (),
        )
    scope = foreground_scope_derivation.foreground_scope
    if type(scope) is not ForegroundScope:
        raise CMEEStage1ContractError(
            "requirement_bundle_foreground_scope_missing"
        )
    configuration_by_ref = {
        configuration.configuration_id: configuration
        for configuration in configurations
    }
    observed_configuration_by_ref = {
        row.distinction_id: row.configuration_ref
        for row in observed_distinction_rows
    }
    differences_by_configuration: dict[str, list[RequiredDifferenceRow]] = {}
    for difference in required_difference_rows:
        configuration_ref = observed_configuration_by_ref.get(
            difference.observed_distinction_ref
        )
        if configuration_ref is None or configuration_ref not in configuration_by_ref:
            raise CMEEStage1ContractError(
                "requirement_bundle_required_difference_unbound"
            )
        differences_by_configuration.setdefault(configuration_ref, []).append(
            difference
        )
    if not differences_by_configuration:
        return (
            RequirementBundleDerivation(
                schema_version=_SCHEMA_VERSION,
                state=RequirementBundleDerivationState.NO_REQUIRED_DIFFERENCE,
                bundle_set=None,
                missing_structure_refs=(),
                derivation_evidence_refs=(
                    difference_configuration_derivation.derivation_evidence_refs
                ),
            ),
            (),
        )

    required_configuration_refs = set(differences_by_configuration)
    bundles: list[RequirementBundle] = []
    for anchor in configurations:
        if anchor.configuration_id not in required_configuration_refs:
            continue
        adjacent = tuple(
            candidate.configuration_id
            for candidate in configurations
            if candidate.configuration_id != anchor.configuration_id
            and candidate.configuration_id in required_configuration_refs
            and _configurations_are_source_connected(
                anchor, candidate, grounded_view
            )
        )
        if len(adjacent) > 4:
            raise CMEEStage1ContractError(
                "requirement_bundle_adjacent_cardinality_overflow"
            )
        covered_configuration_refs = {
            anchor.configuration_id,
            *adjacent,
        }
        covered_differences = tuple(
            row
            for configuration_ref in covered_configuration_refs
            for row in differences_by_configuration[configuration_ref]
        )
        bundle = RequirementBundle(
            schema_version=_SCHEMA_VERSION,
            bundle_id=(
                "requirement-bundle:pending"
                f"@{_REQUIREMENT_BUNDLE_REF_VERSION}"
            ),
            foreground_scope_ref=scope.scope_id,
            anchor_configuration_ref=anchor.configuration_id,
            adjacent_configuration_refs=_canonical(adjacent),
            required_difference_refs=_canonical(
                row.difference_id for row in covered_differences
            ),
            retention_duty_refs=_canonical(
                ref
                for row in covered_differences
                for ref in row.retention_duty_refs
            ),
        )
        bundle = replace(bundle, bundle_id=requirement_bundle_id(bundle))
        bundles.append(bundle)
    # Anchor iteration follows the semantic configuration order; IDs do not
    # select a primary bundle or change its position.
    ordered_bundles = tuple(bundles)
    if not 1 <= len(ordered_bundles) <= 5:
        raise CMEEStage1ContractError(
            "requirement_bundle_set_cardinality_invalid"
        )
    bundle_set = RequirementBundleSet(
        schema_version=_SCHEMA_VERSION,
        foreground_scope_ref=scope.scope_id,
        bundle_refs=tuple(row.bundle_id for row in ordered_bundles),
    )
    return (
        RequirementBundleDerivation(
            schema_version=_SCHEMA_VERSION,
            state=RequirementBundleDerivationState.BUNDLE_SET_AVAILABLE,
            bundle_set=bundle_set,
            missing_structure_refs=(),
            derivation_evidence_refs=(
                difference_configuration_derivation.derivation_evidence_refs
            ),
        ),
        ordered_bundles,
    )


def _component_sort_key(
    value: MeaningComponentSemanticKey,
) -> bytes:
    # Historical IM00 identity uses canonical JSON byte ordering for these
    # nested component values.  IM02 top-level row ordering remains semantic.
    return stage1_canonical_json_bytes(value)


def _canonical_components(
    values: Iterable[MeaningComponentSemanticKey],
) -> Tuple[MeaningComponentSemanticKey, ...]:
    return tuple(sorted(set(values), key=_component_sort_key))


def _role_qualifier_parts(value: str) -> tuple[str, str, str] | None:
    if not value.startswith("qualifier:") or "=" not in value:
        return None
    key, qualifier_value = value.removeprefix("qualifier:").split("=", 1)
    for role in ("left", "right", "subject", "object", "target"):
        prefix = f"{role}_"
        if key.startswith(prefix):
            return role, key.removeprefix(prefix), qualifier_value
    return None


def _qualifiers_for_roles(
    qualifier_keys: Sequence[str],
    roles: set[str],
) -> Tuple[str, ...]:
    return tuple(
        sorted(
            {
                value
                for value in qualifier_keys
                if (
                    (parts := _role_qualifier_parts(value)) is None
                    or parts[0] in roles
                )
            }
        )
    )


def _summaries_for_role_qualifiers(
    baseline: MeaningSemanticSignature,
    qualifier_keys: Sequence[str],
) -> tuple[Tuple[str, ...], Tuple[str, ...]]:
    baseline_parts = tuple(
        parts
        for value in baseline.qualifier_keys
        if (parts := _role_qualifier_parts(value)) is not None
    )
    retained_parts = tuple(
        parts
        for value in qualifier_keys
        if (parts := _role_qualifier_parts(value)) is not None
    )
    temporal = set(baseline.temporal_state_keys)
    temporal.difference_update(
        f"time:{value}"
        for _role, axis, value in baseline_parts
        if axis == "time_scope"
    )
    temporal.update(
        f"time:{value}"
        for _role, axis, value in retained_parts
        if axis == "time_scope"
    )
    modality = set(baseline.modality_polarity_or_limitation_keys)
    modality.difference_update(
        f"{axis}:{value}"
        for _role, axis, value in baseline_parts
        if axis in {"modality", "polarity"}
    )
    modality.update(
        f"{axis}:{value}"
        for _role, axis, value in retained_parts
        if axis in {"modality", "polarity"}
    )
    return tuple(sorted(temporal)), tuple(sorted(modality))


def _swap_endpoint_roles(
    baseline: MeaningSemanticSignature,
) -> MeaningSemanticSignature:
    swap = {"role:left": "role:right", "role:right": "role:left"}
    components = _canonical_components(
        replace(value, role_key=swap.get(value.role_key, value.role_key))
        for value in baseline.component_semantic_keys
    )
    qualifiers: set[str] = set()
    role_swap = {"left": "right", "right": "left"}
    for value in baseline.qualifier_keys:
        parts = _role_qualifier_parts(value)
        if parts is None or parts[0] not in role_swap:
            qualifiers.add(value)
            continue
        role, axis, qualifier_value = parts
        qualifiers.add(
            f"qualifier:{role_swap[role]}_{axis}={qualifier_value}"
        )
    return replace(
        baseline,
        component_role_keys=tuple(
            sorted({value.role_key for value in components})
        ),
        qualifier_keys=tuple(sorted(qualifiers)),
        component_semantic_keys=components,
    )


def _delete_endpoint(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    if (
        len(mutation.target_component_refs) != 1
        or len(baseline.component_semantic_keys) < 2
    ):
        return baseline
    # Derived DELETE_ENDPOINT always owns the target endpoint of an admitted
    # direction row.  Its semantic role is ``right``; if that role is absent
    # the current signature cannot represent this owned mutation.
    candidates = tuple(
        value
        for value in baseline.component_semantic_keys
        if value.role_key == "role:right"
    )
    if len(candidates) != 1:
        return baseline
    removed = candidates[0]
    components = tuple(
        value
        for value in baseline.component_semantic_keys
        if value is not removed
    )
    center_kinds = {
        value.removeprefix("center:")
        for value in baseline.input_center_keys
    }
    remaining_kinds = {
        value.semantic_kind_key.removeprefix("semantic-kind:")
        for value in components
    }
    if not center_kinds.issubset(remaining_kinds):
        return baseline
    roles = {value.role_key.removeprefix("role:") for value in components}
    qualifiers = _qualifiers_for_roles(baseline.qualifier_keys, roles)
    temporal, modality = _summaries_for_role_qualifiers(
        baseline, qualifiers
    )
    return replace(
        baseline,
        component_role_keys=tuple(
            sorted({value.role_key for value in components})
        ),
        relation_direction_keys=(
            baseline.relation_direction_keys
            if len(components) >= 2 and len(roles) >= 2
            else ()
        ),
        temporal_state_keys=temporal,
        modality_polarity_or_limitation_keys=modality,
        qualifier_keys=qualifiers,
        component_semantic_keys=components,
    )


def _replace_role(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    if (
        len(mutation.target_component_refs) != 1
        or len(mutation.replacement_refs) != 1
    ):
        return baseline
    target_role = mutation.target_component_refs[0]
    replacement_role = mutation.replacement_refs[0]
    if (
        not target_role.startswith("role:")
        or not replacement_role.startswith("role:")
        or target_role
        not in {value.role_key for value in baseline.component_semantic_keys}
    ):
        return baseline
    components = _canonical_components(
        replace(value, role_key=replacement_role)
        if value.role_key == target_role
        else value
        for value in baseline.component_semantic_keys
    )
    target_name = target_role.removeprefix("role:")
    replacement_name = replacement_role.removeprefix("role:")
    qualifiers: set[str] = set()
    for value in baseline.qualifier_keys:
        parts = _role_qualifier_parts(value)
        if parts is None or parts[0] != target_name:
            qualifiers.add(value)
            continue
        _role, axis, qualifier_value = parts
        qualifiers.add(
            f"qualifier:{replacement_name}_{axis}={qualifier_value}"
        )
    temporal, modality = _summaries_for_role_qualifiers(
        baseline, tuple(sorted(qualifiers))
    )
    return replace(
        baseline,
        component_role_keys=tuple(
            sorted({value.role_key for value in components})
        ),
        relation_direction_keys=(
            baseline.relation_direction_keys
            if len(components) >= 2
            and len({value.role_key for value in components}) >= 2
            else ()
        ),
        temporal_state_keys=temporal,
        modality_polarity_or_limitation_keys=modality,
        qualifier_keys=tuple(sorted(qualifiers)),
        component_semantic_keys=components,
    )


def _replace_owner_with_unknown(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    if (
        len(mutation.target_component_refs) != 1
        or mutation.replacement_refs
    ):
        return baseline
    target_owner = mutation.target_component_refs[0].split("@", 1)[0]
    owner_matches = {
        value.owner_key
        for value in baseline.component_semantic_keys
        if value.owner_key == target_owner
    }
    if len(owner_matches) != 1 or target_owner == "owner:unknown":
        return baseline
    affected_roles = {
        value.role_key.removeprefix("role:")
        for value in baseline.component_semantic_keys
        if value.owner_key == target_owner
    }
    components = _canonical_components(
        replace(value, owner_key="owner:unknown")
        if value.owner_key == target_owner
        else value
        for value in baseline.component_semantic_keys
    )
    qualifiers: set[str] = set()
    for value in baseline.qualifier_keys:
        parts = _role_qualifier_parts(value)
        if (
            parts is not None
            and parts[0] in affected_roles
            and parts[1] == "actor"
        ):
            qualifiers.add(
                f"qualifier:{parts[0]}_actor=unknown"
            )
        else:
            qualifiers.add(value)
    worlds = {
        value
        for value in baseline.world_or_owner_distinction_keys
        if value.startswith("world:")
    }
    worlds.update(value.owner_key for value in components)
    return replace(
        baseline,
        world_or_owner_distinction_keys=tuple(sorted(worlds)),
        qualifier_keys=tuple(sorted(qualifiers)),
        component_semantic_keys=components,
    )


def _replace_world(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    if len(mutation.target_component_refs) != 1 or len(
        mutation.replacement_refs
    ) != 1:
        return baseline
    target = mutation.target_component_refs[0]
    replacement = mutation.replacement_refs[0]
    worlds = set(baseline.world_or_owner_distinction_keys)
    if target not in worlds:
        return baseline
    worlds.discard(target)
    worlds.add(replacement)
    return replace(
        baseline,
        world_or_owner_distinction_keys=tuple(sorted(worlds)),
    )


def _replace_time(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    if len(mutation.target_component_refs) != 1 or len(
        mutation.replacement_refs
    ) != 1:
        return baseline
    target = mutation.target_component_refs[0].replace("time_scope:", "time:")
    replacement = mutation.replacement_refs[0].replace(
        "time_scope:", "time:"
    )
    temporal = set(baseline.temporal_state_keys)
    if target not in temporal:
        return baseline
    temporal.remove(target)
    temporal.add(replacement)
    target_value = target.removeprefix("time:")
    replacement_value = replacement.removeprefix("time:")
    qualifiers = tuple(
        sorted(
            {
                (
                    f"qualifier:{parts[0]}_time_scope={replacement_value}"
                    if (
                        (parts := _role_qualifier_parts(value)) is not None
                        and parts[1] == "time_scope"
                        and parts[2] == target_value
                    )
                    else value
                )
                for value in baseline.qualifier_keys
            }
        )
    )
    return replace(
        baseline,
        temporal_state_keys=tuple(sorted(temporal)),
        qualifier_keys=qualifiers,
    )


def _delete_bound_qualifier(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    del mutation
    # The present exact7 signature cannot encode a qualifier deletion as one
    # owned mutation without either leaving its typed summary inconsistent or
    # changing a second closed axis.  IM02 therefore issues exact0 here.
    return baseline


def apply_counterfactual_mutation(
    baseline_semantic_signature: MeaningSemanticSignature,
    counterfactual_mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    """Apply exactly one mutation from the closed exact12 set, fail-closed."""

    validate_meaning_semantic_signature_local_shape(
        baseline_semantic_signature
    )
    validate_counterfactual_mutation_local_shape(counterfactual_mutation)
    kind = counterfactual_mutation.mutation_kind
    if kind is CounterfactualMutationKind.DELETE_ENDPOINT:
        result = _delete_endpoint(
            baseline_semantic_signature, counterfactual_mutation
        )
    elif kind is CounterfactualMutationKind.SWAP_ENDPOINTS:
        result = _swap_endpoint_roles(baseline_semantic_signature)
    elif kind is CounterfactualMutationKind.DELETE_PREDICATE:
        result = baseline_semantic_signature
    elif kind is CounterfactualMutationKind.DELETE_OWNER:
        result = _replace_owner_with_unknown(
            baseline_semantic_signature, counterfactual_mutation
        )
    elif kind is CounterfactualMutationKind.REPLACE_WORLD:
        result = _replace_world(
            baseline_semantic_signature, counterfactual_mutation
        )
    elif kind is CounterfactualMutationKind.REPLACE_ROLE:
        result = _replace_role(
            baseline_semantic_signature, counterfactual_mutation
        )
    elif kind is CounterfactualMutationKind.REPLACE_TIME:
        result = _replace_time(
            baseline_semantic_signature, counterfactual_mutation
        )
    elif kind in {
        CounterfactualMutationKind.DELETE_MODALITY,
        CounterfactualMutationKind.DELETE_ASPECT,
        CounterfactualMutationKind.DELETE_SCOPE,
    }:
        # These deletions are not separately representable in the current
        # exact7 signature; issuing a guessed row would violate §6.5.
        result = baseline_semantic_signature
    elif kind is CounterfactualMutationKind.DELETE_QUALIFIER:
        result = _delete_bound_qualifier(
            baseline_semantic_signature, counterfactual_mutation
        )
    elif kind is CounterfactualMutationKind.PROMOTE_UNKNOWN:
        if baseline_semantic_signature.resolution_treatment_keys != (
            "resolution:unresolved",
        ):
            result = baseline_semantic_signature
        else:
            result = replace(
                baseline_semantic_signature,
                resolution_treatment_keys=("resolution:resolved",),
            )
    else:
        raise CMEEStage1ContractError(
            "counterfactual_mutation_kind_not_closed"
        )
    validate_meaning_semantic_signature_local_shape(result)
    return result


def _consequence_code_for_mutation(
    mutation: CounterfactualMutationRow,
    baseline: MeaningSemanticSignature,
    mutated: MeaningSemanticSignature,
) -> WholeReadingConsequenceCode | None:
    if baseline == mutated:
        return None
    kind = mutation.mutation_kind
    if kind in {
        CounterfactualMutationKind.DELETE_ENDPOINT,
        CounterfactualMutationKind.SWAP_ENDPOINTS,
        CounterfactualMutationKind.REPLACE_ROLE,
    }:
        return WholeReadingConsequenceCode.RELATION_STRUCTURE_CHANGED
    if kind is CounterfactualMutationKind.REPLACE_TIME:
        return WholeReadingConsequenceCode.TEMPORAL_FLOW_CHANGED
    if kind in {
        CounterfactualMutationKind.DELETE_OWNER,
        CounterfactualMutationKind.REPLACE_WORLD,
    }:
        return WholeReadingConsequenceCode.WORLD_OR_OWNER_DISTINCTION_CHANGED
    if kind is CounterfactualMutationKind.PROMOTE_UNKNOWN:
        return WholeReadingConsequenceCode.RESOLUTION_TREATMENT_CHANGED
    if kind is CounterfactualMutationKind.DELETE_QUALIFIER:
        if mutation.target_component_refs == ("qualifier:not_generalized",):
            return WholeReadingConsequenceCode.EPISODICITY_BOUNDARY_CHANGED
        return (
            WholeReadingConsequenceCode.MODALITY_POLARITY_OR_LIMITATION_CHANGED
        )
    return None


def issue_whole_reading_consequence_row(
    *,
    foreground_scope: ForegroundScope,
    required_difference: RequiredDifferenceRow,
    counterfactual_mutation: CounterfactualMutationRow,
    baseline_semantic_signature: MeaningSemanticSignature,
) -> WholeReadingConsequenceRow | None:
    """Issue one exact7 row, or exact0 when the mutation has no closed delta."""

    if type(foreground_scope) is not ForegroundScope:
        raise CMEEStage1ContractError(
            "whole_reading_issuer_foreground_scope_invalid"
        )
    if type(required_difference) is not RequiredDifferenceRow:
        raise CMEEStage1ContractError(
            "whole_reading_issuer_required_difference_invalid"
        )
    if type(counterfactual_mutation) is not CounterfactualMutationRow:
        raise CMEEStage1ContractError(
            "whole_reading_issuer_mutation_invalid"
        )
    validate_counterfactual_mutation_local_shape(counterfactual_mutation)
    validate_meaning_semantic_signature_local_shape(
        baseline_semantic_signature
    )
    scope_tuple_fields = (
        foreground_scope.integrated_scope_object_refs,
        foreground_scope.basis_row_refs,
        foreground_scope.source_connected_relation_refs,
        foreground_scope.required_retention_duty_refs,
        foreground_scope.material_unknown_refs,
        foreground_scope.required_qualifier_refs,
        foreground_scope.source_evidence_refs,
    )
    if (
        foreground_scope.schema_version != _SCHEMA_VERSION
        or not all(_is_canonical(values) for values in scope_tuple_fields)
        or not foreground_scope.integrated_scope_object_refs
        or not foreground_scope.basis_row_refs
        or not foreground_scope.source_evidence_refs
        or foreground_scope.scope_id != foreground_scope_id(foreground_scope)
    ):
        raise CMEEStage1ContractError(
            "whole_reading_issuer_foreground_scope_invalid"
        )
    validate_version_qualified_ref(
        foreground_scope.scope_id,
        expected_types=("foreground-scope",),
    )
    invariants = required_difference.invariant_codes
    expected_invariants = tuple(
        value
        for value in DifferenceInvariantCode
        if value in set(invariants)
    ) if type(invariants) is tuple and all(
        type(value) is DifferenceInvariantCode for value in invariants
    ) else ()
    if (
        required_difference.schema_version != _SCHEMA_VERSION
        or not invariants
        or invariants != expected_invariants
        or not _is_canonical(required_difference.retention_duty_refs)
        or required_difference.difference_id
        != required_difference_id(required_difference)
    ):
        raise CMEEStage1ContractError(
            "whole_reading_issuer_required_difference_invalid"
        )
    for ref, ref_type, ref_version in (
        (
            required_difference.difference_id,
            "required-difference",
            _REQUIRED_DIFFERENCE_REF_VERSION,
        ),
        (
            required_difference.observed_distinction_ref,
            "observed-distinction",
            _OBSERVED_DISTINCTION_REF_VERSION,
        ),
        (
            required_difference.counterfactual_mutation_ref,
            "counterfactual-mutation",
            _COUNTERFACTUAL_MUTATION_REF_VERSION,
        ),
    ):
        validate_version_qualified_ref(ref, expected_types=(ref_type,))
        if not ref.endswith(f"@{ref_version}"):
            raise CMEEStage1ContractError(
                "whole_reading_issuer_required_difference_invalid"
            )
    if (
        required_difference.counterfactual_mutation_ref
        != counterfactual_mutation.mutation_id
        or required_difference.observed_distinction_ref
        != counterfactual_mutation.observed_distinction_ref
    ):
        raise CMEEStage1ContractError(
            "whole_reading_issuer_mutation_binding_mismatch"
        )
    evidence = counterfactual_mutation.source_evidence_refs
    if not evidence or not set(evidence).issubset(
        foreground_scope.source_evidence_refs
    ):
        raise CMEEStage1ContractError(
            "whole_reading_issuer_evidence_unbound"
        )
    mutated = apply_counterfactual_mutation(
        baseline_semantic_signature, counterfactual_mutation
    )
    consequence_code = _consequence_code_for_mutation(
        counterfactual_mutation,
        baseline_semantic_signature,
        mutated,
    )
    if consequence_code is None:
        return None
    if consequence_code not in _WHOLE_READING_CODES_EXACT7:
        raise CMEEStage1ContractError(
            "whole_reading_issuer_consequence_not_closed"
        )
    row = WholeReadingConsequenceRow(
        schema_version=_SCHEMA_VERSION,
        consequence_id=(
            "whole-reading-consequence:pending"
            f"@{_WHOLE_READING_CONSEQUENCE_REF_VERSION}"
        ),
        consequence_code=consequence_code,
        foreground_scope_ref=foreground_scope.scope_id,
        required_difference_ref=required_difference.difference_id,
        source_evidence_refs=evidence,
        counterfactual_mutation_ref=counterfactual_mutation.mutation_id,
        baseline_semantic_signature=baseline_semantic_signature,
        mutated_semantic_signature=mutated,
    )
    return replace(row, consequence_id=whole_reading_consequence_id(row))


def derive_input_specific_meaning_structure(
    grounded_view: GroundedSituationView,
    foreground_scope_derivation: ForegroundScopeDerivation,
) -> InputSpecificMeaningStructure:
    """Derive the complete providerless IM02 structure before Reception."""

    configuration_derivation, configurations = (
        derive_difference_configuration_set(
            grounded_view, foreground_scope_derivation
        )
    )
    if (
        configuration_derivation.state
        is DifferenceConfigurationDerivationState.CONFIGURATION_SET_AVAILABLE
    ):
        observed = _derive_observed_distinctions(
            grounded_view, configurations
        )
        mutations, required = _derive_required_differences(
            grounded_view, configurations, observed
        )
    else:
        observed = ()
        mutations = ()
        required = ()
    bundle_derivation, bundles = derive_requirement_bundle_set(
        grounded_view,
        foreground_scope_derivation,
        configuration_derivation,
        configurations,
        observed,
        required,
    )
    return InputSpecificMeaningStructure(
        schema_version=_SCHEMA_VERSION,
        difference_configuration_derivation=configuration_derivation,
        configurations=configurations,
        observed_distinction_rows=observed,
        counterfactual_mutation_rows=mutations,
        required_difference_rows=required,
        requirement_bundle_derivation=bundle_derivation,
        requirement_bundles=bundles,
        # Candidate semantic signatures arrive in IM03.  IM02 owns the closed
        # issuer but does not fabricate a pre-candidate baseline.
        whole_reading_consequence_rows=(),
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
    "apply_counterfactual_mutation",
    "derive_difference_configuration_set",
    "derive_foreground_scope_closed",
    "derive_grounded_situation_view",
    "derive_input_specific_meaning_structure",
    "derive_requirement_bundle_set",
    "foreground_scope_disposition",
    "issue_whole_reading_consequence_row",
)
