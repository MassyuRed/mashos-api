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
    BasisEpistemicTier,
    BasisProvenanceKind,
    BasisProvenanceRow,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_READING_CONSEQUENCE_REQUIREMENT_CODES_EXACT4,
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
    GroundedInterpretationProjection,
    GroundedSemanticComponentProjection,
    GroundedSourceRelationRow,
    InputSpecificMeaningCandidate,
    InputSpecificityEvidence,
    InputSpecificMeaningStructure,
    InterpretationKind,
    LimitedMeaningOutcome,
    LimitedMeaningOutcomeState,
    MeaningDecisionReasonCode,
    MeaningDecisionTrace,
    MeaningDecisionTraceKind,
    MeaningDecisionTraceRow,
    MeaningComponentSemanticKey,
    MeaningReadingOperation,
    MeaningSemanticSignature,
    MeaningEdge,
    MeaningNode,
    ObservedDistinctionDerivationKind,
    ObservedDistinctionRow,
    OwnerClass,
    PreMeaningGroundedInputs,
    ReadingConsequence,
    QualifiedEventStateConfiguration,
    RelationOperator,
    RelationDirectionRow,
    RelationalConfiguration,
    RequiredDifferenceRow,
    RequirementBundle,
    RequirementBundleDerivation,
    RequirementBundleDerivationState,
    RequirementBundleSet,
    SelectedEmlisProvisionalReading,
    SealedEmlisProvisionalReading,
    SourceOwnerDisposition,
    VisibleAuthority,
    WholeReadingConsequenceCode,
    WholeReadingConsequenceRow,
    apply_meaning_signature_mutation,
    counterfactual_mutation_id,
    difference_configuration_id,
    foreground_scope_basis_row_ref,
    foreground_scope_id,
    input_specific_meaning_candidate_core_payload,
    input_specific_meaning_candidate_dominates,
    input_specific_meaning_candidate_id,
    input_specific_meaning_configuration_source_component_rows,
    input_specific_meaning_candidate_source_component_rows,
    input_specific_meaning_candidate_source_component_refs,
    input_specificity_evidence_id,
    reading_consequence_id,
    reading_consequence_source_constraint_refs,
    meaning_decision_candidate_reason_codes,
    meaning_selection_assessment_refs,
    recompute_input_specific_meaning_candidate_signature,
    observed_distinction_id,
    required_difference_id,
    requirement_bundle_id,
    resolve_mutation_application_spec,
    selected_emlis_provisional_reading_id,
    stage1_canonical_json_bytes,
    validate_counterfactual_mutation_local_shape,
    validate_meaning_semantic_signature_local_shape,
    validate_mutation_signature_delta,
    validate_version_qualified_ref,
    whole_reading_consequence_id,
)


_SCHEMA_VERSION = "1.0"
_ROOT_SCHEMA_VERSION = "1.1"
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
    semantic_interpretation_projections: Tuple[
        GroundedInterpretationProjection, ...
    ] = ()


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


def _stable_unique(values: Iterable[str]) -> Tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if type(value) is not str or not value:
            raise CMEEStage1ContractError(
                "input_specific_meaning_source_projection_ref_invalid"
            )
        if value not in result:
            result.append(value)
    return tuple(result)


def _project_grounded_interpretations(
    premeaning_inputs: PreMeaningGroundedInputs,
    *,
    nodes_by_ref: Mapping[str, MeaningNode],
    qualifiers_by_node: Mapping[str, Tuple[str, ...]],
    unknowns_by_node: Mapping[str, Tuple[str, ...]],
) -> Tuple[GroundedInterpretationProjection, ...]:
    """Retain source leaves needed by IM03 without storing a signature."""

    graph = premeaning_inputs.grounded_graph
    node_rank = {
        _node_ref(node): index for index, node in enumerate(graph.nodes)
    }
    contribution_refs_by_candidate: dict[str, list[str]] = {}
    for contribution in premeaning_inputs.observation_contribution_rows:
        for candidate_ref in contribution.interpretation_candidate_refs:
            contribution_refs_by_candidate.setdefault(candidate_ref, []).append(
                contribution.contribution_id
            )
    result: list[GroundedInterpretationProjection] = []
    for candidate_rank, candidate in enumerate(
        premeaning_inputs.interpretation_candidate_rows
    ):
        component_rows: list[GroundedSemanticComponentProjection] = []
        for binding in candidate.argument_bindings:
            node = nodes_by_ref.get(binding.semantic_ref)
            if node is None:
                raise CMEEStage1ContractError(
                    "input_specific_meaning_source_projection_component_unbound"
                )
            qualifier_refs = qualifiers_by_node.get(binding.semantic_ref)
            if qualifier_refs is None:
                raise CMEEStage1ContractError(
                    "input_specific_meaning_source_projection_qualifier_missing"
                )
            qualifier_values = {
                axis: body
                for value in qualifier_refs
                if ":" in value
                for axis, body in (value.split(":", 1),)
            }
            if not {"actor", "time_scope", "modality", "polarity"}.issubset(
                qualifier_values
            ):
                raise CMEEStage1ContractError(
                    "input_specific_meaning_source_projection_leaf_missing"
                )
            actor = qualifier_values["actor"]
            time_scope = qualifier_values["time_scope"]
            modality = qualifier_values["modality"]
            polarity = qualifier_values["polarity"]
            component_rows.append(
                GroundedSemanticComponentProjection(
                    schema_version=_SCHEMA_VERSION,
                    source_object_ref=binding.semantic_ref,
                    source_declaration_rank=node_rank[binding.semantic_ref],
                    typed_predicate_key=(
                        "predicate:"
                        f"{candidate.semantic_operator.value.lower()}"
                    ),
                    semantic_kind_key=(
                        f"semantic-kind:{node.node_kind.lower()}"
                    ),
                    owner_key=f"owner:{actor}",
                    scope_key="scope:source_bounded",
                    role_key=f"role:{binding.role.value.lower()}",
                    epistemic_state_key=(
                        f"epistemic:{node.epistemic_state.value.lower()}"
                    ),
                    temporal_state_key=f"time:{time_scope}",
                    modality_key=f"modality:{modality}",
                    polarity_key=f"polarity:{polarity}",
                    qualifier_refs=tuple(qualifier_refs),
                    source_evidence_refs=_evidence_refs(
                        (node,), source_version=graph.source_version
                    ),
                    material_unknown_refs=tuple(
                        unknowns_by_node.get(binding.semantic_ref, ())
                    ),
                )
            )
        if not component_rows:
            raise CMEEStage1ContractError(
                "input_specific_meaning_source_projection_component_missing"
            )
        result.append(
            GroundedInterpretationProjection(
                schema_version=_SCHEMA_VERSION,
                interpretation_candidate_ref=candidate.candidate_id,
                source_declaration_rank=candidate_rank,
                candidate_kind=candidate.candidate_kind,
                semantic_operator=candidate.semantic_operator,
                relation_operator=candidate.relation_operator,
                component_rows=tuple(component_rows),
                relation_path_refs=tuple(candidate.relation_basis_refs),
                source_evidence_refs=tuple(candidate.evidence_refs),
                basis_contribution_refs=_stable_unique(
                    contribution_refs_by_candidate.get(
                        candidate.candidate_id, ()
                    )
                ),
                approved_derivation_refs=(candidate.derivation_rule_id,),
                required_qualifier_refs=tuple(
                    candidate.required_qualifiers
                ),
                forbidden_promotion_codes=tuple(
                    candidate.forbidden_promotions
                ),
            )
        )
    return tuple(result)


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
        # A source-explicit connective nucleus (for example a contrast
        # marker) proves the relation carried by its grounded edge; it is not
        # itself a target, topic, or scope object.  Keeping it as an
        # independent object creates an artificial competing scope beside
        # the two source-bound endpoints.
        and not (
            node.node_kind == "other_explicit"
            and node.grounding_kind == "user_stated_relation"
        )
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
        semantic_interpretation_projections=(
            _project_grounded_interpretations(
                premeaning_inputs,
                nodes_by_ref=nodes_by_ref,
                qualifiers_by_node=qualifiers_by_node,
                unknowns_by_node=unknowns_by_node,
            )
        ),
    )


def validate_grounded_situation_view(
    view: GroundedSituationView,
    premeaning_inputs: PreMeaningGroundedInputs,
    grounded_graph: GroundedMeaningGraph,
) -> None:
    """Validate the carried view and its safe source projection in place."""

    if (
        type(view) is not GroundedSituationView
        or view.schema_version != _SCHEMA_VERSION
        or type(premeaning_inputs) is not PreMeaningGroundedInputs
        or type(grounded_graph) is not GroundedMeaningGraph
        or premeaning_inputs.grounded_graph != grounded_graph
        or type(view.basis_rows) is not tuple
        or type(view.compatibility_rows) is not tuple
        or type(view.source_connected_relations) is not tuple
        or type(view.missing_structure_refs) is not tuple
        or type(view.semantic_interpretation_projections) is not tuple
    ):
        raise CMEEStage1ContractError(
            "grounded_situation_view_validation_invalid"
        )
    nodes_by_ref = {_node_ref(node): node for node in grounded_graph.nodes}
    qualifiers_by_node = _qualifiers_by_node_ref(premeaning_inputs)
    unknowns_by_node, _missing = _unknowns_by_node_ref(
        premeaning_inputs, nodes_by_ref
    )
    expected_projections = _project_grounded_interpretations(
        premeaning_inputs,
        nodes_by_ref=nodes_by_ref,
        qualifiers_by_node=qualifiers_by_node,
        unknowns_by_node=unknowns_by_node,
    )
    if view.semantic_interpretation_projections != expected_projections:
        raise CMEEStage1ContractError(
            "grounded_situation_view_source_projection_mismatch"
        )
    if len(view.basis_rows) != len(set(view.basis_rows)):
        raise CMEEStage1ContractError(
            "grounded_situation_view_basis_duplicate"
        )
    compatibility_refs = {
        row.scope_object_ref for row in view.compatibility_rows
    }
    if any(
        ref not in compatibility_refs
        for row in view.basis_rows
        for ref in row.scope_object_refs
    ):
        raise CMEEStage1ContractError(
            "grounded_situation_view_compatibility_incomplete"
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
    adjacency: dict[str, set[str]] = {}
    for row in relations:
        adjacency.setdefault(row.source_object_ref, set()).add(
            row.target_object_ref
        )
        adjacency.setdefault(row.target_object_ref, set()).add(
            row.source_object_ref
        )
    visited = {left_object_ref}
    pending = [left_object_ref]
    while pending:
        current = pending.pop()
        for candidate in adjacency.get(current, ()):
            if candidate == right_object_ref:
                return True
            if candidate not in visited:
                visited.add(candidate)
                pending.append(candidate)
    return False


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
                # UNKNOWN is an optional material leaf, unlike the required
                # carrier axes above.  A source-connected relation may keep
                # an unknown on one facet and its absence on the other as a
                # distinct value; treating the absent side as missing would
                # prevent the closed union from preserving that unknown.
                if not (
                    axis is ForegroundScopeCompatibilityAxis.UNKNOWN
                    and relation_bridges_rows
                ):
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
                    if not (
                        axis is ForegroundScopeCompatibilityAxis.UNKNOWN
                        and not same_object
                        and connected
                    ):
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


def _candidate_configuration_qualifier_refs(
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    if type(configuration) is RelationalConfiguration:
        return configuration.source_qualifier_refs
    if type(configuration) is QualifiedEventStateConfiguration:
        return _stable_unique(
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


def _qualified_material_modifier_refs(
    profile: ForegroundScopeObjectCompatibilityRow,
) -> Tuple[str, ...]:
    """Return non-default typed leaves that can make a qualified facet material."""

    return _canonical(
        (
            *(ref for ref in profile.world_refs if ref != "world:unknown"),
            *(
                ref
                for ref in profile.modality_refs
                if ref != "modality:fact"
            ),
            *(
                ref
                for ref in profile.time_refs
                if ref != "time_scope:current_input"
            ),
            *(
                ref
                for ref in profile.aspect_refs
                if ref != "aspect:unknown"
            ),
            *(
                ref
                for ref in profile.polarity_refs
                if ref != "polarity:neutral"
            ),
            *(
                ref
                for ref in profile.scope_refs
                if ref != "scope:source_bounded"
            ),
            *(
                ref
                for ref in profile.required_qualifier_refs
                if ref.startswith("qualifier:")
            ),
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
    # Each typed source relation owns one binary configuration.  Connected
    # multi-facet inputs are integrated later by the requirement-bundle and
    # material-seed graph; folding an entire path into one configuration
    # would violate the binary endpoint contract and duplicate the shared
    # endpoint during counterfactual mutation.
    for relation_component in tuple((relation,) for relation in admitted_relations):
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

    # A relational endpoint is normally not duplicated as a qualified
    # configuration.  The closed exception is category-neutral: an
    # independently grounded NO_RELATION projection may retain a distinct
    # qualified facet on the same source object when its predicate and owner
    # are source-bound.  Material non-default modifier admission is checked
    # below from the exact typed compatibility profile.  Candidate kind and
    # semantic operator are deliberately unreachable from this admission
    # decision; they would be a fixed-category selector.
    independently_projected_qualified_refs = {
        row.source_object_ref
        for projection in grounded_view.semantic_interpretation_projections
        if not projection.relation_path_refs
        and projection.relation_operator is RelationOperator.NO_RELATION_CLAIM
        for row in projection.component_rows
        for profile in (profiles_by_object.get(row.source_object_ref),)
        if profile is not None
        and len(profile.owner_refs) == 1
        and row.scope_key == "scope:source_bounded"
        and row.typed_predicate_key.startswith("predicate:")
        and bool(row.typed_predicate_key.removeprefix("predicate:"))
        and row.owner_key == profile.owner_refs[0].split("@", 1)[0]
    }
    qualified_object_refs = (
        scope_objects - relationally_covered
    ) | (relationally_covered & independently_projected_qualified_refs)
    for object_ref in sorted(qualified_object_refs):
        profile = profiles_by_object.get(object_ref)
        if profile is None:
            continue
        if len(profile.owner_refs) != 1:
            missing.append(_missing_ref("qualified-owner", object_ref))
            continue
        # owner + the carrier defaults (fact/current-input/unknown-aspect/
        # neutral/source-bounded) do not constitute the material qualifier
        # difference required by QUALIFIED_EVENT_ADMISSION.  Without a
        # non-default typed modifier this is a thin source event, not a
        # provisional input-specific reading.
        material_modifier_refs = _qualified_material_modifier_refs(profile)
        if not material_modifier_refs:
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
        qualified_material_modifiers: Tuple[str, ...] = ()
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
            profile = profiles_by_object.get(configuration.predicate_ref)
            if profile is None:
                raise CMEEStage1ContractError(
                    "qualified_observed_profile_unbound"
                )
            qualified_material_modifiers = (
                _qualified_material_modifier_refs(profile)
            )
            if not qualified_material_modifiers:
                raise CMEEStage1ContractError(
                    "qualified_observed_material_modifier_missing"
                )
            rows.append(
                _new_observed_distinction(
                    configuration_ref=configuration.configuration_id,
                    derivation_kind=(
                        ObservedDistinctionDerivationKind.QUALIFIED_PREDICATE_OWNER_MODIFIER
                    ),
                    axis=_qualifier_axis(qualified_material_modifiers),
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

        qualifier_owner_count: dict[str, int] = {}
        if type(configuration) is RelationalConfiguration:
            for object_ref in objects:
                profile = profiles_by_object.get(object_ref)
                if profile is None:
                    continue
                for qualifier in set(_profile_source_qualifiers(profile)):
                    qualifier_owner_count[qualifier] = (
                        qualifier_owner_count.get(qualifier, 0) + 1
                    )
        bound_qualifiers = tuple(
            value
            for value in qualifiers
            if not value.startswith("unknown:")
            and (
                (
                    type(configuration)
                    is QualifiedEventStateConfiguration
                    and value in qualified_material_modifiers
                )
                or (
                    type(configuration) is RelationalConfiguration
                    and qualifier_owner_count.get(value) == 1
                )
            )
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
            ("resolution:unresolved",),
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
    required_configurations = tuple(
        configuration
        for configuration in configurations
        if configuration.configuration_id in required_configuration_refs
    )
    remaining = set(range(len(required_configurations)))
    connected_components: list[tuple[DifferenceConfiguration, ...]] = []
    while remaining:
        first = min(remaining)
        selected = {first}
        changed = True
        while changed:
            changed = False
            for index in tuple(sorted(remaining - selected)):
                if any(
                    _configurations_are_source_connected(
                        required_configurations[index],
                        required_configurations[member],
                        grounded_view,
                    )
                    for member in selected
                ):
                    selected.add(index)
                    changed = True
        connected_components.append(
            tuple(required_configurations[index] for index in sorted(selected))
        )
        remaining.difference_update(selected)

    for component in connected_components:
        anchor = component[0]
        adjacent = tuple(
            candidate.configuration_id for candidate in component[1:]
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
    # Each source-connected component owns one bundle.  Its first semantic
    # configuration is the stable anchor; alternate anchor permutations are
    # not distinct readings.
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
    *,
    source_component_refs: Sequence[str] | None = None,
    source_component_rows: Sequence[
        GroundedSemanticComponentProjection
    ] | None = None,
    mutation_scope_component_rows: Sequence[
        GroundedSemanticComponentProjection
    ] | None = None,
) -> MeaningSemanticSignature:
    """Apply exactly one mutation from the closed exact12 set, fail-closed."""

    return apply_meaning_signature_mutation(
        baseline_semantic_signature,
        counterfactual_mutation,
        source_component_refs=source_component_refs,
        source_component_rows=source_component_rows,
        mutation_scope_component_rows=mutation_scope_component_rows,
    )


def _consequence_code_for_mutation(
    mutation: CounterfactualMutationRow,
    baseline: MeaningSemanticSignature,
    mutated: MeaningSemanticSignature,
) -> WholeReadingConsequenceCode | None:
    if baseline == mutated:
        return None
    return resolve_mutation_application_spec(
        mutation
    ).whole_reading_consequence_code


def issue_whole_reading_consequence_row(
    *,
    foreground_scope: ForegroundScope,
    required_difference: RequiredDifferenceRow,
    counterfactual_mutation: CounterfactualMutationRow,
    baseline_semantic_signature: MeaningSemanticSignature,
    source_component_refs: Sequence[str] | None = None,
    source_component_rows: Sequence[
        GroundedSemanticComponentProjection
    ] | None = None,
    mutation_scope_component_rows: Sequence[
        GroundedSemanticComponentProjection
    ] | None = None,
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
    try:
        mutated = apply_counterfactual_mutation(
            baseline_semantic_signature,
            counterfactual_mutation,
            source_component_refs=source_component_refs,
            source_component_rows=source_component_rows,
            mutation_scope_component_rows=mutation_scope_component_rows,
        )
    except CMEEStage1ContractError as exc:
        if str(exc) in {
            "mutation_target_absent_candidate_invalid",
            "mutation_material_semantic_collapse_candidate_invalid",
        }:
            return None
        raise
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


def _configuration_primary_refs(
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    if type(configuration) is RelationalConfiguration:
        return configuration.endpoint_component_refs
    return (configuration.predicate_ref,)


def _configuration_qualifier_refs(
    configuration: DifferenceConfiguration,
) -> Tuple[str, ...]:
    if type(configuration) is RelationalConfiguration:
        return configuration.source_qualifier_refs
    return _stable_unique(
        (
            *configuration.modality_refs,
            *configuration.time_refs,
            *configuration.aspect_refs,
            *configuration.scope_refs,
            *configuration.qualifier_refs,
        )
    )


def _primary_refs_in_source_declaration_order(
    grounded_view: GroundedSituationView,
    refs: Iterable[str],
) -> Tuple[str, ...]:
    """Order a material component set only by its source declaration rank."""

    values = _stable_unique(refs)
    rank_by_ref: dict[str, int] = {}
    for projection in grounded_view.semantic_interpretation_projections:
        for row in projection.component_rows:
            if row.source_object_ref not in values:
                continue
            prior = rank_by_ref.get(row.source_object_ref)
            if prior is not None and prior != row.source_declaration_rank:
                raise CMEEStage1ContractError(
                    "input_specific_meaning_source_rank_conflict_red"
                )
            rank_by_ref[row.source_object_ref] = row.source_declaration_rank
    if set(rank_by_ref) != set(values) or len(set(rank_by_ref.values())) != len(
        rank_by_ref
    ):
        raise CMEEStage1ContractError(
            "input_specific_meaning_source_rank_cover_red"
        )
    return tuple(sorted(values, key=rank_by_ref.__getitem__))


def _candidate_operation(
    *,
    configurations: Sequence[DifferenceConfiguration],
    projections: Sequence[GroundedInterpretationProjection],
    material_unknown_refs: Sequence[str],
) -> MeaningReadingOperation:
    if material_unknown_refs:
        return MeaningReadingOperation.HOLD_UNRESOLVED
    relational = tuple(
        value
        for value in configurations
        if type(value) is RelationalConfiguration
    )
    qualified = tuple(
        value
        for value in configurations
        if type(value) is QualifiedEventStateConfiguration
    )
    if relational and qualified:
        return MeaningReadingOperation.KEEP_DISTINCT
    if relational:
        relation_kinds = {
            row.relation_operator for row in projections
        }
        if any("PRECEDES" in value.value for value in relation_kinds):
            return MeaningReadingOperation.TRACK_TRANSITION
        if any(
            value.value in {"COEXISTS_WITH", "TENSION_WITH"}
            for value in relation_kinds
        ):
            return MeaningReadingOperation.HOLD_RELATION
        return MeaningReadingOperation.NOTICE_PERSISTENCE
    if qualified and any(
        value.candidate_kind
        in {
            InterpretationKind.ACTION_THEN_CHANGE_ONCE,
            InterpretationKind.RESIDUE_AFTER_EVENT,
        }
        for value in projections
    ):
        return MeaningReadingOperation.RECOGNIZE_BOUNDED_ACTUALITY
    return MeaningReadingOperation.HOLD_QUALIFIED_EVENT_STATE


def _material_interpretation_projections(
    *,
    grounded_view: GroundedSituationView,
    configurations: Sequence[DifferenceConfiguration],
) -> Tuple[GroundedInterpretationProjection, ...]:
    """Resolve only projections owned by the candidate's material bases."""

    relation_refs = {
        ref
        for configuration in configurations
        if type(configuration) is RelationalConfiguration
        for ref in configuration.relation_path_refs
    }
    qualified_object_refs = {
        configuration.predicate_ref
        for configuration in configurations
        if type(configuration) is QualifiedEventStateConfiguration
    }
    primary_refs = {
        ref
        for configuration in configurations
        for ref in _configuration_primary_refs(configuration)
    }
    return tuple(
        projection
        for projection in grounded_view.semantic_interpretation_projections
        if (
            (
                bool(projection.relation_path_refs)
                and set(projection.relation_path_refs).issubset(relation_refs)
                and {
                    row.source_object_ref for row in projection.component_rows
                }.issubset(primary_refs)
            )
            or (
                not projection.relation_path_refs
                and any(
                    row.source_object_ref in qualified_object_refs
                    for row in projection.component_rows
                )
            )
        )
    )


def _material_binding_seed_partition(
    *,
    grounded_view: GroundedSituationView,
    configurations: Sequence[DifferenceConfiguration],
) -> Tuple[Tuple[DifferenceConfiguration, ...], ...]:
    """Partition material basis vertices by the closed compatibility graph."""

    values = tuple(configurations)
    vertex_rows: list[
        tuple[BasisProvenanceKind, str, DifferenceConfiguration]
    ] = []
    for configuration in values:
        if type(configuration) is RelationalConfiguration:
            vertex_rows.extend(
                (
                    BasisProvenanceKind.RELATION_BRIDGE,
                    ref,
                    configuration,
                )
                for ref in configuration.relation_path_refs
            )
        elif type(configuration) is QualifiedEventStateConfiguration:
            vertex_rows.append(
                (
                    BasisProvenanceKind.QUALIFIED_EVENT_STATE,
                    configuration.configuration_id,
                    configuration,
                )
            )
        else:
            raise CMEEStage1ContractError(
                "material_binding_seed_configuration_type_red"
            )
    vertices = tuple(vertex_rows)
    if not vertices:
        return ((),)
    relation_by_ref = {
        row.relation_ref: row
        for row in grounded_view.source_connected_relations
    }
    foreground_object_refs = {
        ref
        for basis in grounded_view.basis_rows
        for ref in basis.scope_object_refs
    }
    owner_by_object: dict[str, set[str]] = {}
    for projection in grounded_view.semantic_interpretation_projections:
        for row in projection.component_rows:
            owner_by_object.setdefault(row.source_object_ref, set()).add(
                row.owner_key
            )
    relation_adjacency: dict[str, list[tuple[str, str]]] = {}
    for relation in grounded_view.source_connected_relations:
        if (
            type(relation.relation_kind) is not ForegroundScopeRelationKind
            or relation.relation_kind not in _RELATION_KINDS_EXACT4
            or not relation.source_evidence_refs
        ):
            raise CMEEStage1ContractError(
                "material_binding_seed_relation_allowlist_red"
            )
        relation_adjacency.setdefault(
            relation.source_object_ref, []
        ).append((relation.target_object_ref, relation.relation_ref))
        relation_adjacency.setdefault(
            relation.target_object_ref, []
        ).append((relation.source_object_ref, relation.relation_ref))

    def vertex_object_refs(
        kind: BasisProvenanceKind,
        ref: str,
        configuration: DifferenceConfiguration,
    ) -> set[str]:
        if kind is BasisProvenanceKind.RELATION_BRIDGE:
            relation = relation_by_ref.get(ref)
            if relation is None:
                raise CMEEStage1ContractError(
                    "material_binding_seed_relation_unbound_red"
                )
            return {
                relation.source_object_ref,
                relation.target_object_ref,
            }
        if type(configuration) is not QualifiedEventStateConfiguration:
            raise CMEEStage1ContractError(
                "material_binding_seed_basis_owner_red"
            )
        return {configuration.predicate_ref}

    def source_connected_path(
        left_objects: set[str],
        right_objects: set[str],
    ) -> tuple[bool, Tuple[str, ...]]:
        if left_objects.intersection(right_objects):
            return True, ()
        queue = list(sorted(left_objects))
        visited = set(left_objects)
        path_by_object: dict[str, Tuple[str, ...]] = {
            ref: () for ref in left_objects
        }
        while queue:
            current = queue.pop(0)
            for adjacent, relation_ref in relation_adjacency.get(current, ()):
                if adjacent in visited:
                    continue
                visited.add(adjacent)
                path = (*path_by_object[current], relation_ref)
                path_by_object[adjacent] = path
                if adjacent in right_objects:
                    return True, path
                queue.append(adjacent)
        return False, ()

    def compatible(left_index: int, right_index: int) -> bool:
        left_kind, left_ref, left_configuration = vertices[left_index]
        right_kind, right_ref, right_configuration = vertices[right_index]
        if left_index == right_index:
            return True
        left_objects = vertex_object_refs(
            left_kind, left_ref, left_configuration
        )
        right_objects = vertex_object_refs(
            right_kind, right_ref, right_configuration
        )
        source_connected_typed_path, path_refs = source_connected_path(
            left_objects,
            right_objects,
        )
        same_foreground_scope_and_center = (
            bool(left_objects)
            and bool(right_objects)
            and left_objects.issubset(foreground_object_refs)
            and right_objects.issubset(foreground_object_refs)
            and source_connected_typed_path
        )
        owner_sets = tuple(
            owner_by_object.get(ref, set())
            for ref in (*sorted(left_objects), *sorted(right_objects))
        )
        typed_owner_compatible = (
            bool(owner_sets)
            and all(len(owners) == 1 for owners in owner_sets)
            and (
                len({next(iter(owners)) for owners in owner_sets}) == 1
                or source_connected_typed_path
            )
        )
        involved_relation_refs = tuple(
            dict.fromkeys(
                ref
                for ref in (
                    left_ref
                    if left_kind is BasisProvenanceKind.RELATION_BRIDGE
                    else "",
                    right_ref
                    if right_kind is BasisProvenanceKind.RELATION_BRIDGE
                    else "",
                    *path_refs,
                )
                if ref
            )
        )
        source_explicit_allowlist_relation = all(
            ref in relation_by_ref
            and relation_by_ref[ref].relation_kind in _RELATION_KINDS_EXACT4
            and bool(relation_by_ref[ref].source_evidence_refs)
            for ref in involved_relation_refs
        )
        return all(
            (
                same_foreground_scope_and_center,
                typed_owner_compatible,
                source_connected_typed_path,
                source_explicit_allowlist_relation,
            )
        )

    remaining = set(range(len(vertices)))
    result: list[Tuple[DifferenceConfiguration, ...]] = []
    vertex_components: list[Tuple[int, ...]] = []
    while remaining:
        first = min(remaining)
        selected = {first}
        changed = True
        while changed:
            changed = False
            for index in tuple(sorted(remaining - selected)):
                if any(compatible(index, member) for member in selected):
                    selected.add(index)
                    changed = True
        ordered_indexes = tuple(sorted(selected))
        if any(
            not compatible(left, right)
            for left, right in combinations(ordered_indexes, 2)
        ):
            raise CMEEStage1ContractError(
                "material_binding_seed_nontransitive_compatibility_red"
            )
        seed = tuple(
            dict.fromkeys(
                vertices[index][2]
                for index in ordered_indexes
            )
        )
        vertex_components.append(ordered_indexes)
        result.append(seed)
        remaining.difference_update(selected)
    assigned_vertex_indexes = {
        index for component in vertex_components for index in component
    }
    configuration_component_indexes: dict[str, set[int]] = {}
    for component_index, component in enumerate(vertex_components):
        for vertex_index in component:
            configuration_component_indexes.setdefault(
                vertices[vertex_index][2].configuration_id,
                set(),
            ).add(component_index)
    if any(
        len(component_indexes) != 1
        for component_indexes in configuration_component_indexes.values()
    ):
        raise CMEEStage1ContractError(
            "material_binding_seed_configuration_split_red"
        )
    if (
        assigned_vertex_indexes != set(range(len(vertices)))
        or set(configuration_component_indexes)
        != {value.configuration_id for value in values}
    ):
        raise CMEEStage1ContractError(
            "material_binding_seed_partition_incomplete_red"
        )
    return tuple(result)


def _enumerate_candidate_lanes(
    seeds: Sequence[Sequence[DifferenceConfiguration]],
) -> Tuple[
    tuple[
        MeaningReadingOperation,
        BasisEpistemicTier,
        Tuple[DifferenceConfiguration, ...],
    ],
    ...,
]:
    """Return exact7 × exact2 lanes for every canonical material seed."""

    normalized_seeds = tuple(tuple(seed) for seed in seeds) or ((),)
    return tuple(
        (operation, tier, seed)
        for operation in MeaningReadingOperation
        for tier in BasisEpistemicTier
        for seed in normalized_seeds
    )


def _derive_basis_provenance_rows(
    *,
    grounded_view: GroundedSituationView,
    configurations: Sequence[DifferenceConfiguration],
    relation_path_refs: Sequence[str],
    projections: Sequence[GroundedInterpretationProjection],
) -> Tuple[BasisProvenanceRow, ...]:
    relation_by_ref = {
        row.relation_ref: row
        for row in grounded_view.source_connected_relations
    }
    result: list[BasisProvenanceRow] = []
    for ref in relation_path_refs:
        relation = relation_by_ref.get(ref)
        if relation is None or not relation.source_evidence_refs:
            raise CMEEStage1ContractError(
                "input_specific_meaning_relation_provenance_unbound"
            )
        result.append(
            BasisProvenanceRow(
                schema_version=_SCHEMA_VERSION,
                basis_kind=BasisProvenanceKind.RELATION_BRIDGE,
                basis_ref=ref,
                basis_epistemic_tier=BasisEpistemicTier.SOURCE_EXPLICIT,
                source_evidence_refs=relation.source_evidence_refs,
                approved_derivation_refs=(),
            )
        )
    for configuration in configurations:
        if type(configuration) is not QualifiedEventStateConfiguration:
            continue
        matching_projections = tuple(
            projection
            for projection in projections
            if any(
                row.source_object_ref == configuration.predicate_ref
                for row in projection.component_rows
            )
        )
        derivation_refs = _stable_unique(
            ref
            for projection in matching_projections
            for ref in projection.approved_derivation_refs
        )
        if not derivation_refs or not configuration.source_evidence_refs:
            raise CMEEStage1ContractError(
                "input_specific_meaning_qualified_provenance_unbound"
            )
        result.append(
            BasisProvenanceRow(
                schema_version=_SCHEMA_VERSION,
                basis_kind=BasisProvenanceKind.QUALIFIED_EVENT_STATE,
                basis_ref=configuration.configuration_id,
                basis_epistemic_tier=(
                    BasisEpistemicTier.RULE_ADMITTED_PROVISIONAL
                ),
                source_evidence_refs=configuration.source_evidence_refs,
                approved_derivation_refs=derivation_refs,
            )
        )
    return tuple(result)


def _candidate_trace_source_refs(
    candidate: InputSpecificMeaningCandidate,
    evidence: InputSpecificityEvidence,
    consequence_by_ref: Mapping[str, WholeReadingConsequenceRow],
) -> Tuple[str, ...]:
    interpretation_refs = tuple(
        ref
        for ref in candidate.basis_derivation_refs
        if ref.startswith(("interpretation-candidate:", "candidate:"))
    )
    approved_derivation_refs = tuple(
        ref
        for ref in candidate.basis_derivation_refs
        if ref not in interpretation_refs
    )
    return _stable_unique(
        (
            *candidate.basis_contribution_refs,
            *candidate.relation_path_refs,
            *interpretation_refs,
            *candidate.source_qualifier_refs,
            *candidate.material_unknown_refs,
            *approved_derivation_refs,
            *candidate.primary_component_refs,
            evidence.foreground_scope_ref,
            *candidate.basis_configuration_refs,
            *candidate.requirement_bundle_refs,
            *candidate.preserved_difference_refs,
            *(
                consequence_by_ref[ref].counterfactual_mutation_ref
                for ref in evidence.whole_reading_consequence_refs
                if ref in consequence_by_ref
            ),
            *evidence.whole_reading_consequence_refs,
        )
    )


def _empty_signature_shell(
    operation: MeaningReadingOperation,
    projection: GroundedInterpretationProjection,
) -> MeaningSemanticSignature:
    component = projection.component_rows[0]
    semantic_component = MeaningComponentSemanticKey(
        typed_predicate_key=component.typed_predicate_key,
        semantic_kind_key=component.semantic_kind_key,
        owner_key=component.owner_key,
        scope_key=component.scope_key,
        role_key=component.role_key,
    )
    return MeaningSemanticSignature(
        schema_version=_SCHEMA_VERSION,
        reading_operation=operation,
        input_center_keys=(
            f"center:{component.semantic_kind_key.removeprefix('semantic-kind:')}",
        ),
        component_role_keys=(component.role_key,),
        relation_direction_keys=(),
        epistemic_state_keys=(component.epistemic_state_key,),
        temporal_state_keys=(component.temporal_state_key,),
        resolution_treatment_keys=(),
        world_or_owner_distinction_keys=(component.owner_key,),
        modality_polarity_or_limitation_keys=tuple(
            sorted({"scope:bounded", component.modality_key, component.polarity_key})
        ),
        episodicity_boundary_keys=(),
        qualifier_keys=(),
        component_semantic_keys=(semantic_component,),
    )


def _apply_counterfactual_mutation_with_spec(
    baseline: MeaningSemanticSignature,
    mutation: CounterfactualMutationRow,
) -> MeaningSemanticSignature:
    mutated = apply_counterfactual_mutation(baseline, mutation)
    validate_mutation_signature_delta(
        mutation=mutation,
        baseline_semantic_signature=baseline,
        mutated_semantic_signature=mutated,
    )
    return mutated


def _forbidden_semantic_collapse_refs(
    required_difference_refs: Sequence[str],
    *,
    required_by_ref: Mapping[str, RequiredDifferenceRow],
    mutation_by_ref: Mapping[str, CounterfactualMutationRow],
) -> Tuple[str, ...]:
    """Project protected source leaves from the owned required mutations."""

    return _stable_unique(
        ref
        for required_ref in required_difference_refs
        for required in (required_by_ref[required_ref],)
        for mutation in (
            mutation_by_ref[required.counterfactual_mutation_ref],
        )
        if mutation.mutation_kind
        is not CounterfactualMutationKind.PROMOTE_UNKNOWN
        for ref in mutation.target_component_refs
    )


def _derive_candidate_semantic_loss_codes(
    *,
    candidate: InputSpecificMeaningCandidate,
    grounded_view: GroundedSituationView,
    foreground_scope: ForegroundScope,
    bundle: RequirementBundle,
    configurations: Sequence[DifferenceConfiguration],
    observed_by_ref: Mapping[str, ObservedDistinctionRow],
    required_by_ref: Mapping[str, RequiredDifferenceRow],
    mutation_by_ref: Mapping[str, CounterfactualMutationRow],
) -> Tuple[DifferenceInvariantCode, ...]:
    """Re-derive actual loss from the source cover before candidate sealing."""

    values = tuple(configurations)
    losses: set[DifferenceInvariantCode] = set()
    expected_primary_refs = _primary_refs_in_source_declaration_order(
        grounded_view,
        (
            ref
            for configuration in values
            for ref in _configuration_primary_refs(configuration)
        ),
    )
    expected_relation_refs = _stable_unique(
        ref
        for configuration in values
        if type(configuration) is RelationalConfiguration
        for ref in configuration.relation_path_refs
    )
    expected_qualifier_refs = _stable_unique(
        ref
        for configuration in values
        for ref in _candidate_configuration_qualifier_refs(configuration)
    )
    expected_protected_refs = _forbidden_semantic_collapse_refs(
        bundle.required_difference_refs,
        required_by_ref=required_by_ref,
        mutation_by_ref=mutation_by_ref,
    )
    component_owner_by_key: dict[MeaningComponentSemanticKey, str] = {}
    selected_projections = _material_interpretation_projections(
        grounded_view=grounded_view,
        configurations=values,
    )
    for projection in selected_projections:
        for row in projection.component_rows:
            if row.source_object_ref not in expected_primary_refs:
                continue
            key = MeaningComponentSemanticKey(
                typed_predicate_key=row.typed_predicate_key,
                semantic_kind_key=row.semantic_kind_key,
                owner_key=row.owner_key,
                scope_key=row.scope_key,
                role_key=row.role_key,
            )
            prior_owner = component_owner_by_key.get(key)
            if prior_owner is not None and prior_owner != row.source_object_ref:
                losses.add(DifferenceInvariantCode.ENDPOINT_COLLAPSE)
            component_owner_by_key[key] = row.source_object_ref
    if candidate.primary_component_refs != expected_primary_refs:
        losses.add(DifferenceInvariantCode.ENDPOINT_COLLAPSE)
    if candidate.relation_path_refs != expected_relation_refs or any(
        type(configuration) is RelationalConfiguration
        and (
            not configuration.direction_rows
            or {
                row.relation_ref for row in configuration.direction_rows
            }
            != set(configuration.relation_path_refs)
        )
        for configuration in values
    ):
        losses.add(DifferenceInvariantCode.DIRECTION_REVERSAL)
    missing_qualifiers = set(expected_qualifier_refs) - set(
        candidate.source_qualifier_refs
    )
    for ref in missing_qualifiers:
        if ref.startswith("world:"):
            losses.add(DifferenceInvariantCode.WORLD_COLLAPSE)
        elif ref.startswith(("time:", "time_scope:")):
            losses.add(DifferenceInvariantCode.TEMPORAL_COLLAPSE)
        elif ref.startswith("polarity:"):
            losses.add(DifferenceInvariantCode.POLARITY_REVERSAL)
        elif ref.startswith("modality:"):
            losses.add(DifferenceInvariantCode.MODALITY_PROMOTION)
        elif ref.startswith("unknown:"):
            losses.add(DifferenceInvariantCode.UNKNOWN_ERASURE)
        else:
            losses.add(DifferenceInvariantCode.EXPLICIT_LIMIT_ERASURE)
    if candidate.material_unknown_refs != foreground_scope.material_unknown_refs:
        losses.add(DifferenceInvariantCode.UNKNOWN_ERASURE)
    if candidate.forbidden_semantic_collapse_refs != expected_protected_refs:
        losses.update(
            invariant
            for required_ref in bundle.required_difference_refs
            for invariant in required_by_ref[required_ref].invariant_codes
        )
    if candidate.preserved_difference_refs != bundle.required_difference_refs:
        losses.update(
            invariant
            for required_ref in bundle.required_difference_refs
            for invariant in required_by_ref[required_ref].invariant_codes
        )
    expected_forbidden_promotions = _stable_unique(
        ref
        for projection in selected_projections
        for ref in projection.forbidden_promotion_codes
    )
    if candidate.forbidden_promotion_codes != expected_forbidden_promotions:
        losses.add(DifferenceInvariantCode.MODALITY_PROMOTION)
    source_rows = input_specific_meaning_candidate_source_component_rows(
        candidate,
        grounded_view=grounded_view,
    )
    source_refs = tuple(row.source_object_ref for row in source_rows)
    source_signature = recompute_input_specific_meaning_candidate_signature(
        candidate,
        grounded_view=grounded_view,
    )
    for required_ref in bundle.required_difference_refs:
        required = required_by_ref[required_ref]
        mutation = mutation_by_ref[required.counterfactual_mutation_ref]
        observed = observed_by_ref[required.observed_distinction_ref]
        configuration = next(
            value
            for value in values
            if value.configuration_id == observed.configuration_ref
        )
        mutation_scope_rows = (
            input_specific_meaning_configuration_source_component_rows(
                candidate,
                configuration,
                grounded_view=grounded_view,
                mutation=mutation,
            )
        )
        try:
            apply_meaning_signature_mutation(
                source_signature,
                mutation,
                source_component_refs=source_refs,
                source_component_rows=source_rows,
                mutation_scope_component_rows=mutation_scope_rows,
            )
        except CMEEStage1ContractError as exc:
            if str(exc) == "mutation_material_semantic_collapse_candidate_invalid":
                losses.update(required.invariant_codes)
            elif str(exc) == "mutation_target_absent_candidate_invalid":
                continue
            else:
                raise
    return tuple(value for value in DifferenceInvariantCode if value in losses)


def _evaluate_candidate_hard_validity(
    *,
    candidate: InputSpecificMeaningCandidate,
    grounded_view: GroundedSituationView,
    foreground_scope: ForegroundScope,
    bundle: RequirementBundle,
    configurations: Sequence[DifferenceConfiguration],
    observed_by_ref: Mapping[str, ObservedDistinctionRow],
    required_by_ref: Mapping[str, RequiredDifferenceRow],
    mutation_by_ref: Mapping[str, CounterfactualMutationRow],
    expected_required_difference_refs: Sequence[str],
    consequence_rows: Sequence[WholeReadingConsequenceRow],
) -> bool:
    values = tuple(configurations)
    expected_primary_refs = _primary_refs_in_source_declaration_order(
        grounded_view,
        (
            ref
            for configuration in values
            for ref in _configuration_primary_refs(configuration)
        ),
    )
    expected_relation_refs = _stable_unique(
        ref
        for configuration in values
        if type(configuration) is RelationalConfiguration
        for ref in configuration.relation_path_refs
    )
    expected_qualified_refs = tuple(
        configuration.configuration_id
        for configuration in values
        if type(configuration) is QualifiedEventStateConfiguration
    )
    projected_component_refs = {
        row.source_object_ref
        for projection in grounded_view.semantic_interpretation_projections
        if projection.interpretation_candidate_ref
        in candidate.basis_derivation_refs
        for row in projection.component_rows
    }
    relation_by_ref = {
        row.relation_ref: row
        for row in grounded_view.source_connected_relations
    }
    required_refs = tuple(expected_required_difference_refs)
    try:
        actual_loss_codes = _derive_candidate_semantic_loss_codes(
            candidate=candidate,
            grounded_view=grounded_view,
            foreground_scope=foreground_scope,
            bundle=bundle,
            configurations=values,
            observed_by_ref=observed_by_ref,
            required_by_ref=required_by_ref,
            mutation_by_ref=mutation_by_ref,
        )
        recomputed_signature = (
            recompute_input_specific_meaning_candidate_signature(
                candidate,
                grounded_view=grounded_view,
            )
        )
    except CMEEStage1ContractError:
        return False
    if (
        candidate.semantic_loss_codes != actual_loss_codes
        or actual_loss_codes
        or candidate.semantic_signature != recomputed_signature
        or candidate.requirement_bundle_refs != (bundle.bundle_id,)
        or candidate.basis_configuration_refs
        != tuple(value.configuration_id for value in values)
        or candidate.primary_component_refs != expected_primary_refs
        or not set(expected_primary_refs).issubset(projected_component_refs)
        or candidate.relation_path_refs != expected_relation_refs
        or any(ref not in relation_by_ref for ref in expected_relation_refs)
        or candidate.qualified_event_state_refs != expected_qualified_refs
        or candidate.preserved_difference_refs != required_refs
        or required_refs != bundle.required_difference_refs
        or set(candidate.source_qualifier_refs)
        != {
            ref
            for configuration in values
            for ref in _candidate_configuration_qualifier_refs(configuration)
        }
        or candidate.material_unknown_refs
        != foreground_scope.material_unknown_refs
        or candidate.emlis_reading_status != "EMLIS_PROVISIONAL_READING"
        or len(consequence_rows) != len(required_refs)
    ):
        return False
    for configuration in values:
        if type(configuration) is RelationalConfiguration:
            if (
                len(configuration.endpoint_component_refs) != 2
                or not configuration.direction_rows
                or not configuration.relation_path_refs
            ):
                return False
        elif type(configuration) is QualifiedEventStateConfiguration:
            if (
                not configuration.predicate_ref
                or not configuration.owner_ref
                or not (
                    configuration.modality_refs
                    or configuration.time_refs
                    or configuration.aspect_refs
                    or configuration.scope_refs
                    or configuration.qualifier_refs
                )
            ):
                return False
        else:
            return False
    for required_ref, row in zip(required_refs, consequence_rows):
        required = required_by_ref.get(required_ref)
        mutation = (
            mutation_by_ref.get(required.counterfactual_mutation_ref)
            if required is not None
            else None
        )
        if (
            required is None
            or mutation is None
            or row.required_difference_ref != required_ref
            or row.counterfactual_mutation_ref != mutation.mutation_id
            or row.baseline_semantic_signature != candidate.semantic_signature
            or row.mutated_semantic_signature == candidate.semantic_signature
            or row.consequence_code
            is not resolve_mutation_application_spec(
                mutation
            ).whole_reading_consequence_code
            or not row.source_evidence_refs
            or not set(row.source_evidence_refs).issubset(
                foreground_scope.source_evidence_refs
            )
        ):
            return False
    return True


def _derive_candidate_for_bundle(
    *,
    grounded_view: GroundedSituationView,
    foreground_scope: ForegroundScope,
    bundle: RequirementBundle,
    configurations: Sequence[DifferenceConfiguration],
    observed_by_ref: Mapping[str, ObservedDistinctionRow],
    required_by_ref: Mapping[str, RequiredDifferenceRow],
    mutation_by_ref: Mapping[str, CounterfactualMutationRow],
    lane_operation: MeaningReadingOperation,
    lane_tier: BasisEpistemicTier,
    seed_configurations: Sequence[DifferenceConfiguration],
) -> tuple[
    InputSpecificMeaningCandidate,
    InputSpecificityEvidence,
    Tuple[WholeReadingConsequenceRow, ...],
] | None:
    owned_bundle_refs = (
        bundle.anchor_configuration_ref,
        *bundle.adjacent_configuration_refs,
    )
    owned_configurations = tuple(seed_configurations)
    if (
        not owned_configurations
        or tuple(value.configuration_id for value in owned_configurations)
        != tuple(
            ref for ref in owned_bundle_refs if ref in {
                value.configuration_id for value in owned_configurations
            }
        )
        or set(value.configuration_id for value in owned_configurations)
        != set(owned_bundle_refs)
    ):
        return None
    primary_members = _stable_unique(
        ref
        for configuration in owned_configurations
        for ref in _configuration_primary_refs(configuration)
    )
    if not primary_members:
        raise CMEEStage1ContractError(
            "input_specific_meaning_candidate_primary_capability_red"
        )
    if len(primary_members) > 5:
        raise CMEEStage1ContractError(
            "input_specific_meaning_primary_component_cardinality_red"
        )
    projections = _material_interpretation_projections(
        grounded_view=grounded_view,
        configurations=owned_configurations,
    )
    if (
        not projections
        or {
            row.source_object_ref
            for projection in projections
            for row in projection.component_rows
            if row.source_object_ref in primary_members
        }
        != set(primary_members)
    ):
        raise CMEEStage1ContractError(
            "input_specific_meaning_candidate_projection_capability_red"
        )
    primary_refs = _primary_refs_in_source_declaration_order(
        grounded_view,
        primary_members,
    )
    relation_paths = _stable_unique(
        ref
        for configuration in owned_configurations
        if type(configuration) is RelationalConfiguration
        for ref in configuration.relation_path_refs
    )
    qualified_refs = tuple(
        configuration.configuration_id
        for configuration in owned_configurations
        if type(configuration) is QualifiedEventStateConfiguration
    )
    provenance = _derive_basis_provenance_rows(
        grounded_view=grounded_view,
        configurations=owned_configurations,
        relation_path_refs=relation_paths,
        projections=projections,
    )
    if not provenance:
        raise CMEEStage1ContractError(
            "input_specific_meaning_candidate_provenance_capability_red"
        )
    tier = (
        BasisEpistemicTier.RULE_ADMITTED_PROVISIONAL
        if any(
            row.basis_epistemic_tier
            is BasisEpistemicTier.RULE_ADMITTED_PROVISIONAL
            for row in provenance
        )
        else BasisEpistemicTier.SOURCE_EXPLICIT
    )
    if tier is not lane_tier:
        return None
    operation = _candidate_operation(
        configurations=owned_configurations,
        projections=projections,
        material_unknown_refs=foreground_scope.material_unknown_refs,
    )
    if operation is not lane_operation:
        return None
    basis_derivation_refs = _stable_unique(
        (
            *(value.interpretation_candidate_ref for value in projections),
            *(
                ref
                for value in projections
                for ref in value.approved_derivation_refs
            ),
        )
    )
    protected_collapse_refs = _forbidden_semantic_collapse_refs(
        bundle.required_difference_refs,
        required_by_ref=required_by_ref,
        mutation_by_ref=mutation_by_ref,
    )
    shell = _empty_signature_shell(operation, projections[0])
    candidate = InputSpecificMeaningCandidate(
        schema_version=_SCHEMA_VERSION,
        candidate_id="input-specific-meaning-candidate:pending",
        reading_operation=operation,
        basis_contribution_refs=_stable_unique(
            ref
            for projection in projections
            for ref in projection.basis_contribution_refs
        ),
        basis_configuration_refs=tuple(
            value.configuration_id for value in owned_configurations
        ),
        requirement_bundle_refs=(bundle.bundle_id,),
        primary_component_refs=primary_refs,
        relation_path_refs=relation_paths,
        qualified_event_state_refs=qualified_refs,
        basis_provenance_rows=provenance,
        basis_epistemic_tier=tier,
        basis_derivation_refs=basis_derivation_refs,
        source_qualifier_refs=_stable_unique(
            ref
            for value in owned_configurations
            for ref in _candidate_configuration_qualifier_refs(value)
        ),
        preserved_difference_refs=bundle.required_difference_refs,
        material_unknown_refs=foreground_scope.material_unknown_refs,
        forbidden_promotion_codes=_stable_unique(
            ref
            for projection in projections
            for ref in projection.forbidden_promotion_codes
        ),
        forbidden_semantic_collapse_refs=protected_collapse_refs,
        semantic_loss_codes=(),
        input_specificity_evidence_ref="input-specificity-evidence:pending",
        emlis_reading_status="EMLIS_PROVISIONAL_READING",
        semantic_signature=shell,
    )
    candidate = replace(
        candidate,
        semantic_loss_codes=_derive_candidate_semantic_loss_codes(
            candidate=candidate,
            grounded_view=grounded_view,
            foreground_scope=foreground_scope,
            bundle=bundle,
            configurations=owned_configurations,
            observed_by_ref=observed_by_ref,
            required_by_ref=required_by_ref,
            mutation_by_ref=mutation_by_ref,
        ),
    )
    if candidate.semantic_loss_codes:
        return None
    signature = recompute_input_specific_meaning_candidate_signature(
        candidate,
        grounded_view=grounded_view,
    )
    candidate = replace(candidate, semantic_signature=signature)
    signature_source_component_rows = (
        input_specific_meaning_candidate_source_component_rows(
            candidate, grounded_view=grounded_view
        )
    )
    signature_source_component_refs = tuple(
        row.source_object_ref for row in signature_source_component_rows
    )
    rows: list[WholeReadingConsequenceRow] = []
    for required_ref in candidate.preserved_difference_refs:
        required = required_by_ref[required_ref]
        mutation = mutation_by_ref[required.counterfactual_mutation_ref]
        observed = observed_by_ref[required.observed_distinction_ref]
        configuration = next(
            value
            for value in owned_configurations
            if value.configuration_id == observed.configuration_ref
        )
        mutation_scope_rows = (
            input_specific_meaning_configuration_source_component_rows(
                candidate,
                configuration,
                grounded_view=grounded_view,
                mutation=mutation,
            )
        )
        try:
            row = issue_whole_reading_consequence_row(
                foreground_scope=foreground_scope,
                required_difference=required,
                counterfactual_mutation=mutation,
                baseline_semantic_signature=signature,
                source_component_refs=signature_source_component_refs,
                source_component_rows=signature_source_component_rows,
                mutation_scope_component_rows=mutation_scope_rows,
            )
        except CMEEStage1ContractError as exc:
            if str(exc) in {
                "mutation_target_absent_candidate_invalid",
                "mutation_material_semantic_collapse_candidate_invalid",
            }:
                return None
            raise
        if row is None:
            return None
        rows.append(row)
    candidate = replace(
        candidate,
        candidate_id=input_specific_meaning_candidate_id(
            candidate,
            recomputed_semantic_signature=signature,
        ),
    )
    evidence = InputSpecificityEvidence(
        candidate_ref=candidate.candidate_id,
        foreground_scope_ref=foreground_scope.scope_id,
        required_difference_refs=candidate.preserved_difference_refs,
        discriminative_necessity_refs=candidate.preserved_difference_refs,
        whole_reading_consequence_refs=tuple(
            row.consequence_id for row in rows
        ),
    )
    evidence_ref = input_specificity_evidence_id(
        evidence,
        whole_reading_consequence_rows=rows,
    )
    candidate = replace(
        candidate,
        input_specificity_evidence_ref=evidence_ref,
    )
    if not _evaluate_candidate_hard_validity(
        candidate=candidate,
        grounded_view=grounded_view,
        foreground_scope=foreground_scope,
        bundle=bundle,
        configurations=owned_configurations,
        observed_by_ref=observed_by_ref,
        required_by_ref=required_by_ref,
        mutation_by_ref=mutation_by_ref,
        expected_required_difference_refs=bundle.required_difference_refs,
        consequence_rows=rows,
    ):
        raise CMEEStage1ContractError(
            "input_specific_meaning_candidate_validator_capability_red"
        )
    return candidate, evidence, tuple(rows)


def _seal_and_dedupe_candidate_records(
    records: Sequence[
        tuple[
            InputSpecificMeaningCandidate,
            InputSpecificityEvidence,
            Tuple[WholeReadingConsequenceRow, ...],
        ]
    ],
) -> Tuple[
    tuple[
        InputSpecificMeaningCandidate,
        InputSpecificityEvidence,
        Tuple[WholeReadingConsequenceRow, ...],
    ],
    ...,
]:
    by_core: dict[
        str,
        tuple[
            InputSpecificMeaningCandidate,
            InputSpecificityEvidence,
            Tuple[WholeReadingConsequenceRow, ...],
        ],
    ] = {}
    for record in records:
        candidate, evidence, rows = record
        recomputed_core_id = input_specific_meaning_candidate_id(
            candidate,
            recomputed_semantic_signature=candidate.semantic_signature,
        )
        if candidate.candidate_id != recomputed_core_id:
            if candidate.candidate_id in by_core:
                raise CMEEStage1ContractError(
                    "input_specific_meaning_same_core_payload_diverged"
                )
            raise CMEEStage1ContractError(
                "input_specific_meaning_candidate_identity_mismatch"
            )
        if evidence.candidate_ref != candidate.candidate_id:
            raise CMEEStage1ContractError(
                "input_specificity_evidence_candidate_back_binding_invalid"
            )
        if candidate.input_specificity_evidence_ref != input_specificity_evidence_id(
            evidence,
            whole_reading_consequence_rows=rows,
        ):
            raise CMEEStage1ContractError(
                "input_specificity_evidence_identity_mismatch"
            )
        prior = by_core.get(recomputed_core_id)
        if prior is not None and prior != record:
            raise CMEEStage1ContractError(
                "input_specific_meaning_same_core_payload_diverged"
            )
        by_core[recomputed_core_id] = record
    return tuple(
        sorted(
            by_core.values(),
            key=lambda value: (
                stage1_canonical_json_bytes(value[0].semantic_signature),
                stage1_canonical_json_bytes(
                    input_specific_meaning_candidate_core_payload(
                        value[0],
                        recomputed_semantic_signature=(
                            value[0].semantic_signature
                        ),
                    )
                ),
            ),
        )
    )


def _dedupe_whole_reading_consequence_rows(
    records: Sequence[
        tuple[
            InputSpecificMeaningCandidate,
            InputSpecificityEvidence,
            Tuple[WholeReadingConsequenceRow, ...],
        ]
    ],
) -> Tuple[WholeReadingConsequenceRow, ...]:
    result: list[WholeReadingConsequenceRow] = []
    by_ref: dict[str, WholeReadingConsequenceRow] = {}
    for _candidate, _evidence, rows in records:
        for row in rows:
            prior = by_ref.get(row.consequence_id)
            if prior is not None:
                if prior != row:
                    raise CMEEStage1ContractError(
                        "whole_reading_consequence_identity_collision"
                    )
                continue
            by_ref[row.consequence_id] = row
            result.append(row)
    return tuple(result)


def _candidate_dominates(
    candidate: InputSpecificMeaningCandidate,
    other: InputSpecificMeaningCandidate,
) -> bool:
    return input_specific_meaning_candidate_dominates(candidate, other)


def _build_canonical_meaning_decision_trace(
    *,
    candidates: Sequence[InputSpecificMeaningCandidate],
    evidence_by_candidate: Mapping[str, InputSpecificityEvidence],
    selected_candidate_ref: str | None,
    limited_state_ref: str | None,
    limited_reason_code: MeaningDecisionReasonCode | None,
    consequence_by_ref: Mapping[str, WholeReadingConsequenceRow] | None = None,
    limited_source_refs: Sequence[str] = (),
) -> MeaningDecisionTrace:
    consequence_lookup = consequence_by_ref or {}
    rows: list[MeaningDecisionTraceRow] = []

    if selected_candidate_ref is not None:
        selected = next(
            value
            for value in candidates
            if value.candidate_id == selected_candidate_ref
        )
        rows.append(
            MeaningDecisionTraceRow(
                trace_kind=MeaningDecisionTraceKind.SELECTED,
                subject_ref=selected.candidate_id,
                reason_codes=meaning_decision_candidate_reason_codes(
                    selected,
                    evidence_by_candidate[selected.candidate_id],
                    candidates=candidates,
                    selected=True,
                ),
                source_refs=_candidate_trace_source_refs(
                    selected,
                    evidence_by_candidate[selected.candidate_id],
                    consequence_lookup,
                ),
            )
        )
    for candidate in candidates:
        if candidate.candidate_id == selected_candidate_ref:
            continue
        rows.append(
            MeaningDecisionTraceRow(
                trace_kind=MeaningDecisionTraceKind.NONSELECTED_VALID,
                subject_ref=candidate.candidate_id,
                reason_codes=meaning_decision_candidate_reason_codes(
                    candidate,
                    evidence_by_candidate[candidate.candidate_id],
                    candidates=candidates,
                    selected=False,
                ),
                source_refs=_candidate_trace_source_refs(
                    candidate,
                    evidence_by_candidate[candidate.candidate_id],
                    consequence_lookup,
                ),
            )
        )
    if limited_state_ref is not None:
        if limited_reason_code is None:
            raise CMEEStage1ContractError(
                "limited_meaning_trace_reason_missing"
            )
        limited_sources = _stable_unique(limited_source_refs)
        if not limited_sources:
            limited_sources = (limited_state_ref,)
        rows.append(
            MeaningDecisionTraceRow(
                trace_kind=MeaningDecisionTraceKind.LIMITED_BASIS,
                subject_ref=limited_state_ref,
                reason_codes=(limited_reason_code,),
                source_refs=limited_sources,
            )
        )
    return MeaningDecisionTrace(
        schema_version=_SCHEMA_VERSION,
        rows=tuple(rows),
    )


def project_selected_reading(
    selected_candidate: InputSpecificMeaningCandidate,
    canonical_trace: MeaningDecisionTrace,
) -> SelectedEmlisProvisionalReading:
    selected_row = next(
        row
        for row in canonical_trace.rows
        if row.trace_kind is MeaningDecisionTraceKind.SELECTED
        and row.subject_ref == selected_candidate.candidate_id
    )
    reading = SelectedEmlisProvisionalReading(
        schema_version=_ROOT_SCHEMA_VERSION,
        reading_id="selected-emlis-provisional-reading:pending",
        selected_candidate_ref=selected_candidate.candidate_id,
        primary_reading_focus_ref=(
            selected_candidate.primary_component_refs[0]
        ),
        supporting_facet_refs=(
            selected_candidate.primary_component_refs[1:]
        ),
        reading_component_refs=selected_candidate.primary_component_refs,
        reading_relation_refs=selected_candidate.relation_path_refs,
        qualified_event_state_refs=(
            selected_candidate.qualified_event_state_refs
        ),
        basis_provenance_rows=selected_candidate.basis_provenance_rows,
        basis_epistemic_tier=selected_candidate.basis_epistemic_tier,
        reading_status=selected_candidate.emlis_reading_status,
        unresolved_alternative_refs=(
            selected_candidate.material_unknown_refs
        ),
        selection_reason_codes=selected_row.reason_codes,
        decision_trace=canonical_trace,
    )
    return replace(
        reading,
        reading_id=selected_emlis_provisional_reading_id(reading),
    )


def select_input_specific_meaning(
    *,
    candidates: Sequence[InputSpecificMeaningCandidate],
    evidence_records: Sequence[InputSpecificityEvidence],
    consequence_rows: Sequence[WholeReadingConsequenceRow] = (),
) -> SelectedEmlisProvisionalReading | None:
    if not candidates:
        return None
    evidence_by_candidate = {
        value.candidate_ref: value for value in evidence_records
    }
    _tier_admitted_refs, nondominated_refs = (
        meaning_selection_assessment_refs(candidates)
    )
    nondominated = tuple(
        candidate
        for candidate in candidates
        if candidate.candidate_id in nondominated_refs
    )
    if len(nondominated) != 1:
        return None
    selected = nondominated[0]
    trace = _build_canonical_meaning_decision_trace(
        candidates=candidates,
        evidence_by_candidate=evidence_by_candidate,
        selected_candidate_ref=selected.candidate_id,
        limited_state_ref=None,
        limited_reason_code=None,
        consequence_by_ref={
            value.consequence_id: value for value in consequence_rows
        },
    )
    return project_selected_reading(selected, trace)


def _limited_meaning_outcome(
    *,
    state: LimitedMeaningOutcomeState,
    derivation_state_ref: str,
    reason_code: MeaningDecisionReasonCode,
    foreground_scope_derivation: ForegroundScopeDerivation,
    grounded_view: GroundedSituationView,
    candidates: Sequence[InputSpecificMeaningCandidate] = (),
    evidence_records: Sequence[InputSpecificityEvidence] = (),
    consequence_rows: Sequence[WholeReadingConsequenceRow] = (),
) -> LimitedMeaningOutcome:
    evidence_by_candidate = {
        value.candidate_ref: value for value in evidence_records
    }
    trace = _build_canonical_meaning_decision_trace(
        candidates=candidates,
        evidence_by_candidate=evidence_by_candidate,
        selected_candidate_ref=None,
        limited_state_ref=derivation_state_ref,
        limited_reason_code=reason_code,
        consequence_by_ref={
            value.consequence_id: value for value in consequence_rows
        },
        limited_source_refs=_stable_unique(
            (
                *foreground_scope_derivation.derivation_evidence_refs,
                *foreground_scope_derivation.retained_foreground_source_object_refs,
                *foreground_scope_derivation.unresolved_scope_refs,
                *foreground_scope_derivation.missing_structure_refs,
                *(
                    ref
                    for candidate in candidates
                    for ref in candidate.primary_component_refs
                ),
            )
        ),
    )
    scope = foreground_scope_derivation.foreground_scope
    basis_by_ref = {
        foreground_scope_basis_row_ref(row): row
        for row in grounded_view.basis_rows
    }
    retained_source_refs = set(
        foreground_scope_derivation.retained_foreground_source_object_refs
    )
    retained_layer1_refs = _stable_unique(
        ref
        for row in (
            tuple(basis_by_ref[basis_ref] for basis_ref in scope.basis_row_refs)
            if type(scope) is ForegroundScope
            else grounded_view.basis_rows
        )
        if type(scope) is ForegroundScope
        or retained_source_refs.intersection(row.source_object_refs)
        for ref in row.layer1_required_object_refs
    )
    return LimitedMeaningOutcome(
        schema_version=_ROOT_SCHEMA_VERSION,
        outcome_state=state,
        retained_layer1_refs=retained_layer1_refs,
        foreground_source_object_refs=(
            scope.integrated_scope_object_refs
            if type(scope) is ForegroundScope
            else foreground_scope_derivation.retained_foreground_source_object_refs
        ),
        retained_qualifier_refs=(
            scope.required_qualifier_refs
            if type(scope) is ForegroundScope
            else ()
        ),
        unresolved_alternative_refs=(
            scope.material_unknown_refs
            if type(scope) is ForegroundScope
            else foreground_scope_derivation.unresolved_scope_refs
        ),
        derivation_state_ref=derivation_state_ref,
        product_acceptance_eligible=(
            state
            is not LimitedMeaningOutcomeState.LIMITED_STRUCTURE_INSUFFICIENT
        ),
        outcome_reason_codes=(reason_code,),
        decision_trace=trace,
    )


def derive_reading_consequence(
    structure: InputSpecificMeaningStructure,
) -> ReadingConsequence:
    """Derive the sole post-selection consequence without Reception input."""

    if type(structure) is not InputSpecificMeaningStructure:
        raise CMEEStage1ContractError("reading_consequence_structure_invalid")
    selected = structure.meaning_decision_outcome
    if type(selected) is not SelectedEmlisProvisionalReading:
        raise CMEEStage1ContractError("reading_consequence_selected_missing")
    candidates = tuple(
        row
        for row in structure.candidate_records
        if row.candidate_id == selected.selected_candidate_ref
    )
    if len(candidates) != 1:
        raise CMEEStage1ContractError(
            "reading_consequence_candidate_closure_invalid"
        )
    candidate = candidates[0]
    whole_by_ref = {
        row.consequence_id: row for row in structure.whole_reading_consequence_rows
    }
    if len(whole_by_ref) != len(structure.whole_reading_consequence_rows):
        raise CMEEStage1ContractError(
            "reading_consequence_whole_row_duplicate"
        )
    evidence_records: list[InputSpecificityEvidence] = []
    for evidence in structure.input_specificity_evidence_records:
        try:
            resolved_rows = tuple(
                whole_by_ref[ref]
                for ref in evidence.whole_reading_consequence_refs
            )
        except KeyError:
            raise CMEEStage1ContractError(
                "reading_consequence_whole_row_foreign"
            ) from None
        if input_specificity_evidence_id(
            evidence,
            whole_reading_consequence_rows=resolved_rows,
        ) == candidate.input_specificity_evidence_ref:
            evidence_records.append(evidence)
    if len(evidence_records) != 1:
        raise CMEEStage1ContractError(
            "reading_consequence_evidence_closure_invalid"
        )
    evidence = evidence_records[0]
    resolved_rows = tuple(
        whole_by_ref[ref] for ref in evidence.whole_reading_consequence_refs
    )
    changed_codes = tuple(
        code
        for code in WholeReadingConsequenceCode
        if code in {row.consequence_code for row in resolved_rows}
    )
    if not changed_codes:
        raise CMEEStage1ContractError(
            "MEANING_RESPONSE_CONSEQUENCE_GAP"
        )
    return ReadingConsequence(
        selected_reading_ref=selected.reading_id,
        input_specificity_evidence_ref=(
            candidate.input_specificity_evidence_ref
        ),
        whole_reading_consequence_refs=(
            evidence.whole_reading_consequence_refs
        ),
        changed_whole_reading_codes=changed_codes,
        response_consequence_requirement_codes=(
            CMEE_READING_CONSEQUENCE_REQUIREMENT_CODES_EXACT4
        ),
        source_constraint_refs=(
            reading_consequence_source_constraint_refs(candidate)
        ),
    )


def derive_sealed_emlis_provisional_reading(
    structure: InputSpecificMeaningStructure,
    consequence: ReadingConsequence,
) -> SealedEmlisProvisionalReading:
    """Bind one already-selected reading to its semantic consequence."""

    selected = structure.meaning_decision_outcome
    if (
        type(selected) is not SelectedEmlisProvisionalReading
        or type(consequence) is not ReadingConsequence
        or consequence.selected_reading_ref != selected.reading_id
    ):
        raise CMEEStage1ContractError("sealed_reading_input_invalid")
    whole_by_ref = {
        row.consequence_id: row for row in structure.whole_reading_consequence_rows
    }
    try:
        resolved_rows = tuple(
            whole_by_ref[ref]
            for ref in consequence.whole_reading_consequence_refs
        )
    except KeyError:
        raise CMEEStage1ContractError(
            "sealed_reading_whole_row_foreign"
        ) from None
    return SealedEmlisProvisionalReading(
        selected_reading_ref=selected.reading_id,
        reading_consequence_ref=reading_consequence_id(
            consequence,
            whole_reading_consequence_rows=resolved_rows,
        ),
    )


def derive_input_specific_meaning_structure(
    grounded_view: GroundedSituationView,
    foreground_scope_derivation: ForegroundScopeDerivation,
) -> InputSpecificMeaningStructure:
    """Derive and seal the complete providerless IM03 structure."""

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
    candidates: Tuple[InputSpecificMeaningCandidate, ...] = ()
    evidence_records: Tuple[InputSpecificityEvidence, ...] = ()
    consequence_rows: Tuple[WholeReadingConsequenceRow, ...] = ()
    scope = foreground_scope_derivation.foreground_scope
    if (
        type(scope) is ForegroundScope
        and bundle_derivation.state
        is RequirementBundleDerivationState.BUNDLE_SET_AVAILABLE
    ):
        required_by_ref = {
            value.difference_id: value for value in required
        }
        observed_by_ref = {
            value.distinction_id: value for value in observed
        }
        mutation_by_ref = {
            value.mutation_id: value for value in mutations
        }
        configuration_by_ref = {
            value.configuration_id: value for value in configurations
        }
        bundle_seeds = tuple(
            (
                bundle,
                _material_binding_seed_partition(
                    grounded_view=grounded_view,
                    configurations=tuple(
                        configuration_by_ref[ref]
                        for ref in (
                            bundle.anchor_configuration_ref,
                            *bundle.adjacent_configuration_refs,
                        )
                    ),
                ),
            )
            for bundle in bundles
        )
        candidate_max = sum(
            len(MeaningReadingOperation)
            * len(BasisEpistemicTier)
            * max(1, len(seeds))
            for _bundle, seeds in bundle_seeds
        )
        draft_records = tuple(
            record
            for bundle, seeds in bundle_seeds
            for operation, tier, seed in _enumerate_candidate_lanes(seeds)
            for record in (
                _derive_candidate_for_bundle(
                    grounded_view=grounded_view,
                    foreground_scope=scope,
                    bundle=bundle,
                    configurations=configurations,
                    observed_by_ref=observed_by_ref,
                    required_by_ref=required_by_ref,
                    mutation_by_ref=mutation_by_ref,
                    lane_operation=operation,
                    lane_tier=tier,
                    seed_configurations=seed,
                ),
            )
            if record is not None
        )
        if len(draft_records) > candidate_max:
            raise CMEEStage1ContractError(
                "CANDIDATE_CARDINALITY_OVERFLOW"
            )
        sealed_records = _seal_and_dedupe_candidate_records(draft_records)
        candidates = tuple(value[0] for value in sealed_records)
        evidence_records = tuple(value[1] for value in sealed_records)
        consequence_rows = _dedupe_whole_reading_consequence_rows(
            sealed_records
        )
    if candidates:
        selected = select_input_specific_meaning(
            candidates=candidates,
            evidence_records=evidence_records,
            consequence_rows=consequence_rows,
        )
        if selected is not None:
            outcome: SelectedEmlisProvisionalReading | LimitedMeaningOutcome = (
                selected
            )
        else:
            outcome = _limited_meaning_outcome(
                state=(
                    LimitedMeaningOutcomeState.LIMITED_COMPETING_MATERIAL_READINGS
                ),
                derivation_state_ref="LIMITED_COMPETING_MATERIAL_READINGS",
                reason_code=MeaningDecisionReasonCode.LIM03,
                foreground_scope_derivation=foreground_scope_derivation,
                grounded_view=grounded_view,
                candidates=candidates,
                evidence_records=evidence_records,
                consequence_rows=consequence_rows,
            )
    elif foreground_scope_derivation.state is (
        ForegroundScopeDerivationState.COMPETING_MATERIAL_SCOPES
    ):
        outcome = _limited_meaning_outcome(
            state=LimitedMeaningOutcomeState.LIMITED_COMPETING_MATERIAL_READINGS,
            derivation_state_ref="COMPETING_MATERIAL_SCOPES",
            reason_code=MeaningDecisionReasonCode.LIM03,
            foreground_scope_derivation=foreground_scope_derivation,
            grounded_view=grounded_view,
        )
    elif foreground_scope_derivation.state is not (
        ForegroundScopeDerivationState.FOREGROUND_SCOPE_AVAILABLE
    ):
        outcome = _limited_meaning_outcome(
            state=LimitedMeaningOutcomeState.LIMITED_STRUCTURE_INSUFFICIENT,
            derivation_state_ref="UPSTREAM_STRUCTURE_INSUFFICIENT",
            reason_code=MeaningDecisionReasonCode.LIM02,
            foreground_scope_derivation=foreground_scope_derivation,
            grounded_view=grounded_view,
        )
    elif configuration_derivation.state is (
        DifferenceConfigurationDerivationState.THIN_NO_SAFE_CONFIGURATION
    ):
        outcome = _limited_meaning_outcome(
            state=(
                LimitedMeaningOutcomeState.LIMITED_NO_SAFE_INPUT_SPECIFIC_CONFIGURATION
            ),
            derivation_state_ref="THIN_NO_SAFE_CONFIGURATION",
            reason_code=MeaningDecisionReasonCode.LIM01,
            foreground_scope_derivation=foreground_scope_derivation,
            grounded_view=grounded_view,
        )
    elif bundle_derivation.state is (
        RequirementBundleDerivationState.UPSTREAM_STRUCTURE_INSUFFICIENT
    ):
        outcome = _limited_meaning_outcome(
            state=LimitedMeaningOutcomeState.LIMITED_STRUCTURE_INSUFFICIENT,
            derivation_state_ref="UPSTREAM_STRUCTURE_INSUFFICIENT",
            reason_code=MeaningDecisionReasonCode.LIM02,
            foreground_scope_derivation=foreground_scope_derivation,
            grounded_view=grounded_view,
        )
    else:
        derivation_ref = (
            "NO_REQUIRED_DIFFERENCE"
            if bundle_derivation.state
            is RequirementBundleDerivationState.NO_REQUIRED_DIFFERENCE
            else "ALL_DRAFTS_SOURCE_GROUNDED_HARD_INVALID"
        )
        outcome = _limited_meaning_outcome(
            state=(
                LimitedMeaningOutcomeState.LIMITED_NO_SAFE_INPUT_SPECIFIC_CONFIGURATION
            ),
            derivation_state_ref=derivation_ref,
            reason_code=MeaningDecisionReasonCode.LIM01,
            foreground_scope_derivation=foreground_scope_derivation,
            grounded_view=grounded_view,
        )
    return InputSpecificMeaningStructure(
        schema_version=_ROOT_SCHEMA_VERSION,
        difference_configuration_derivation=configuration_derivation,
        configurations=configurations,
        observed_distinction_rows=observed,
        counterfactual_mutation_rows=mutations,
        required_difference_rows=required,
        requirement_bundle_derivation=bundle_derivation,
        requirement_bundles=bundles,
        whole_reading_consequence_rows=consequence_rows,
        candidate_records=candidates,
        input_specificity_evidence_records=evidence_records,
        meaning_decision_outcome=outcome,
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


def validate_foreground_scope_disposition(
    disposition: ForegroundScopeDisposition,
    foreground_scope_derivation: ForegroundScopeDerivation,
) -> None:
    """Validate the carried disposition without deriving a replacement."""

    if (
        type(disposition) is not ForegroundScopeDisposition
        or type(foreground_scope_derivation) is not ForegroundScopeDerivation
        or disposition.schema_version != _SCHEMA_VERSION
        or disposition.derivation_state
        is not foreground_scope_derivation.state
        or disposition.code
        is not _DISPOSITION_BY_DERIVATION_STATE.get(
            foreground_scope_derivation.state
        )
        or disposition.retained_foreground_source_object_refs
        != foreground_scope_derivation.retained_foreground_source_object_refs
        or disposition.unresolved_scope_refs
        != foreground_scope_derivation.unresolved_scope_refs
        or disposition.missing_structure_refs
        != foreground_scope_derivation.missing_structure_refs
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_disposition_validation_invalid"
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
    "derive_reading_consequence",
    "derive_sealed_emlis_provisional_reading",
    "derive_requirement_bundle_set",
    "foreground_scope_disposition",
    "issue_whole_reading_consequence_row",
    "project_selected_reading",
    "select_input_specific_meaning",
    "validate_foreground_scope_disposition",
    "validate_grounded_situation_view",
)
