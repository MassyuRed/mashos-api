# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic Stage 1 interpretation and Layer 1 planning.

This module is deliberately private and side-effect free.  It does not call
the legacy realizer, mutate an :class:`ExperiencePlan`, or create a second plan
owner.  The complete builder consumes the already-frozen source, grounded
semantic plan, graph and parent plan.  The smaller builders also support a
single canonical path through that same frozen source and grounded plan.

Semantic construction never branches on source text or ``MeaningNode.value``.
The boundary validator replays source admission from the frozen envelope, then
binds canonical-plan rows to the graph only by owner, kind, endpoint,
grounding and exact evidence identity.
"""

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)

from .contracts import (
    ArgumentBinding,
    ArgumentRole,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEEStage1ContractError,
    EmlisInterpretationCandidate,
    EmlisMeaningField,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationRequest,
    GroundedMeaningGraph,
    InterpretationEpistemicState,
    InterpretationKind,
    MeaningEdge,
    MeaningFieldEntry,
    MeaningFieldSlot,
    MeaningNode,
    ObservationContributionKind,
    ObservationDepthClass,
    PlannedObservationContribution,
    RelationOperator,
    RouteBDisposition,
    SemanticOperator,
    recompute_stage1_identity,
    stage1_canonical_json_bytes,
    validate_stage1_identity,
)
from .source_kernel import (
    AdmittedTextSource,
    build_source_owner_universe,
    freeze_text_source,
    validate_evidence_refs,
)


INTERPRETATION_CANDIDATE_POOL_CAP = 16
INTERPRETATION_CANDIDATE_KIND_CAP = 2
LAYER1_OBSERVATION_CONTRIBUTION_CAP = 5
OBSERVATION_SEMANTIC_KEY_VERSION = (
    "cocolon.cmee.v1a.emlis_stage1.observation_semantic_key.v1"
)

_PROVISIONAL_QUALIFIER = "epistemic:provisional_interpretation"
_FORBIDDEN_PROMOTIONS = (
    "unsupported-cause",
    "personality-promotion",
    "hidden-intent-promotion",
    "diagnosis-promotion",
    "future-guarantee",
    "unknown-as-interpretation",
)
_FORBIDDEN_OBSERVATION_OPERATIONS = (
    "invent-cause",
    "invent-personality",
    "invent-hidden-intent",
    "invent-diagnosis",
    "promote-unknown",
    "complete-unfinished-meaning",
)
_ADMITTED_NUCLEUS_GROUNDING = frozenset({"explicit", "user_stated_relation"})
_ADMITTED_RELATION_GROUNDING = frozenset({"user_stated_relation"})
_CAUSE_RELATIONS = frozenset(
    {
        "cause",
        "causes",
        "caused_by",
        "because",
        "result_of",
        "user_stated_result",
    }
)
_DIRECTION_KINDS = frozenset(
    {"wish", "direction", "desire", "intention", "goal", "help_seeking"}
)
_BURDEN_KINDS = frozenset(
    {"constraint", "burden", "fatigue", "anxiety", "hesitation", "block"}
)
_ACTION_KINDS = frozenset({"action", "attempt"})
_CHANGE_KINDS = frozenset({"change", "bounded_change"})
_EVENT_KINDS = frozenset({"event", "action", "change"})
_RESIDUE_KINDS = frozenset(
    {"reaction", "residue", "lingering_state", "unfinished", "uncertainty"}
)
_UNFINISHED_KINDS = frozenset({"uncertainty", "unfinished", "open_question"})

_SLOT_ORDER = (
    MeaningFieldSlot.CENTER,
    MeaningFieldSlot.TENSION,
    MeaningFieldSlot.COEXISTENCE,
    MeaningFieldSlot.CHANGE,
    MeaningFieldSlot.TIME_RELATION,
    MeaningFieldSlot.DIRECTION,
    MeaningFieldSlot.BURDEN,
    MeaningFieldSlot.OUTPUT,
    MeaningFieldSlot.RESIDUE,
    MeaningFieldSlot.UNFINISHED,
)
_OPERATOR_PRIORITY = {
    RelationOperator.TENSION_WITH: 0,
    RelationOperator.COEXISTS_WITH: 1,
    RelationOperator.ACTION_PRECEDES_CHANGE: 2,
    RelationOperator.TEMPORALLY_PRECEDES: 3,
    RelationOperator.SOURCE_EXPLICIT_CAUSE: 4,
    RelationOperator.NO_RELATION_CLAIM: 5,
}
_RETENTION_PRIORITY = {"required": 0, "should": 1, "optional": 2}

# Canonical §8.1.1 cross-field allowlist: nine kinds and exact thirteen
# kind/operator/relation combinations.  Optional EXPERIENCER is validated
# separately for the three NO_RELATION rows which permit it.
INTERPRETATION_MATRIX_EXACT13 = (
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_ACTUAL_OUTPUT, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_DIRECTION, SemanticOperator.PRESENT_DIRECTION, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.COEXISTENCE, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.COEXISTS_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.TENSION, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.TENSION_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.DIRECTION_UNDER_BURDEN, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.COEXISTS_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.DIRECTION_UNDER_BURDEN, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.TENSION_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.ACTION_THEN_CHANGE_ONCE, SemanticOperator.PRESENT_CHANGE, RelationOperator.ACTION_PRECEDES_CHANGE, (ArgumentRole.ACTION, ArgumentRole.CHANGE)),
    (InterpretationKind.RESIDUE_AFTER_EVENT, SemanticOperator.PRESENT_RESIDUE, RelationOperator.TEMPORALLY_PRECEDES, (ArgumentRole.BEFORE, ArgumentRole.AFTER)),
    (InterpretationKind.SOURCE_STATED_CAUSE, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.SOURCE_EXPLICIT_CAUSE, (ArgumentRole.CAUSE, ArgumentRole.EFFECT)),
    (InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
)


@dataclass(frozen=True, slots=True)
class _PlanBinding:
    node_meta: Mapping[str, object]
    edge_meta: Mapping[str, object]
    required_node_ids: frozenset[str]
    required_edge_ids: frozenset[str]
    source_order: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _CandidateRow:
    candidate: EmlisInterpretationCandidate
    required: bool
    is_relation: bool
    retention_rank: int
    source_order: int


def _ordered(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _enum_or_text(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "")


def _cause_like_relation(value: object) -> bool:
    relation = _enum_or_text(value).lower()
    return (
        relation in _CAUSE_RELATIONS
        or "cause" in relation
        or "reason" in relation
        or relation.endswith("_result")
    )


def _graph_ref(graph: GroundedMeaningGraph) -> str:
    return f"grounded:{graph.graph_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _node_ref(node_id: str) -> str:
    return f"node:{node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _edge_ref(edge_id: str) -> str:
    return f"edge:{edge_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _evidence_ref(evidence_id: str, source_version: str) -> str:
    return f"evidence:{evidence_id}@{source_version}"


def _identified(value: object, field_name: str) -> object:
    return replace(value, **{field_name: recompute_stage1_identity(value)})


def _validate_graph_and_parent(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    if type(graph) is not GroundedMeaningGraph:
        raise CMEEStage1ContractError("stage1_grounded_graph_required")
    if type(parent_plan) is not ExperiencePlan:
        raise CMEEStage1ContractError("stage1_parent_plan_type_invalid")
    if (
        parent_plan.source_envelope_id != graph.source_envelope_id
        or parent_plan.source_version != graph.source_version
        or parent_plan.obligation_version != graph.obligation_version
        or parent_plan.owner_universe_digest != graph.owner_universe_digest
    ):
        raise CMEEStage1ContractError("stage1_parent_plan_lineage_mismatch")
    if (
        not parent_plan.observation_duty_id
        or not parent_plan.reception_duty_id
        or parent_plan.observation_duty_id == parent_plan.reception_duty_id
    ):
        raise CMEEStage1ContractError("stage1_parent_duty_ref_invalid")

    node_ids = tuple(row.node_id for row in graph.nodes)
    edge_ids = tuple(row.edge_id for row in graph.edges)
    if (
        any(type(row) is not MeaningNode for row in graph.nodes)
        or any(type(row) is not MeaningEdge for row in graph.edges)
        or any(not item for item in (*node_ids, *edge_ids))
        or len(node_ids) != len(set(node_ids))
        or len(edge_ids) != len(set(edge_ids))
        or set(node_ids) & set(edge_ids)
    ):
        raise CMEEStage1ContractError("stage1_grounded_graph_identity_invalid")
    if any(
        edge.source_node_id not in set(node_ids)
        or edge.target_node_id not in set(node_ids)
        for edge in graph.edges
    ):
        raise CMEEStage1ContractError("stage1_relation_endpoint_missing")

    visible = tuple(parent_plan.visible_owner_ids)
    required = tuple(parent_plan.required_observation_owner_ids)
    reception = tuple(parent_plan.reception_target_owner_ids)
    for refs, code in (
        (visible, "stage1_visible_owner_identity_invalid"),
        (required, "stage1_required_owner_identity_invalid"),
        (reception, "stage1_reception_owner_identity_invalid"),
    ):
        if (
            any(type(ref) is not str or not ref for ref in refs)
            or len(refs) != len(set(refs))
        ):
            raise CMEEStage1ContractError(code)
    if not set(required + reception).issubset(set(visible)):
        raise CMEEStage1ContractError("stage1_visible_owner_plan_mismatch")


def _visible_claim_ids(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> set[str]:
    visible_owners = set(parent_plan.visible_owner_ids)
    if not visible_owners:
        raise CMEEStage1ContractError("stage1_visible_source_empty")
    # The legacy plan's visible-owner set resolves the sole duty owner, but it
    # is not the Stage 1 semantic-pool denominator.  Every admitted graph row
    # remains a possible request-local interpretation annotation.  Candidate
    # construction below independently excludes UNKNOWN and non-admitted rows.
    graph_claim_ids = {row.node_id for row in graph.nodes} | {
        row.edge_id for row in graph.edges
    }
    if not graph.owner_dispositions:
        return graph_claim_ids

    disposition_by_owner = {
        row.meaning_owner_id: row for row in graph.owner_dispositions
    }
    if len(disposition_by_owner) != len(graph.owner_dispositions):
        raise CMEEStage1ContractError("stage1_owner_disposition_duplicate")
    positive = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for owner_id in visible_owners:
        row = disposition_by_owner.get(owner_id)
        if row is None or row.route_b_disposition not in positive:
            raise CMEEStage1ContractError("stage1_visible_owner_disposition_mismatch")
        if not set(row.visible_claim_refs).issubset(graph_claim_ids):
            raise CMEEStage1ContractError("stage1_visible_claim_ref_missing")
    if any(
        not set(row.visible_claim_refs).issubset(graph_claim_ids)
        for row in graph.owner_dispositions
    ):
        raise CMEEStage1ContractError("stage1_visible_claim_ref_missing")
    return graph_claim_ids


def _validate_canonical_semantic_inputs(
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    """Require the exact frozen-source/canonical-plan path used by Step 1."""

    if type(source) is not AdmittedTextSource:
        raise CMEEStage1ContractError("stage1_admitted_text_source_required")
    if type(grounded_plan) is not GroundedObservationPlan:
        raise CMEEStage1ContractError("stage1_grounded_observation_plan_required")
    try:
        raw = source.envelope.raw_utf8
        prefix = f"{source.envelope.source_encoding}\n@raw_json:".encode("ascii")
        if not raw.startswith(prefix):
            raise ValueError("source_frame_prefix_invalid")
        length_end = raw.index(b"\n", len(prefix))
        raw_json_length = int(raw[len(prefix) : length_end].decode("ascii"))
        raw_json_start = length_end + 1
        raw_json_end = raw_json_start + raw_json_length
        if raw_json_length <= 0 or raw_json_end > len(raw):
            raise ValueError("source_frame_json_length_invalid")
        source_snapshot = json.loads(raw[raw_json_start:raw_json_end].decode("utf-8"))
        expected_source = freeze_text_source(
            GenerationRequest(
                request_id="stage1-source-revalidation",
                current_input_bundle=build_emlis_current_input_bundle(
                    source_snapshot
                ),
                expected_source_record_id=source.envelope.source_record_id,
            )
        )
        validate_evidence_refs(source.envelope, source.evidence_refs)
        expected_universe = build_source_owner_universe(
            source.envelope, source.evidence_refs
        )
        resolver = build_evidence_span_resolver(
            expected_source.evidence_spans,
            current_input=expected_source.normalized_current_input,
        )
        issues = validate_grounded_observation_plan(grounded_plan, resolver)
        expected_plan = build_grounded_observation_plan(
            expected_source.normalized_current_input,
            evidence_spans=expected_source.evidence_spans,
        )
        # Local import avoids making the existing Step 1 implementation depend
        # on this disabled Step 2 module during module initialization.
        from .emlis_v1a import (
            _build_experience_plan,
            _build_graph,
            _ordered as _stage1_ordered,
            _planned_visible_source_ids,
        )

        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(expected_plan)
        )
        expected_graph = _build_graph(
            expected_source,
            expected_plan,
            _stage1_ordered((*required_nuclei, *reception_targets)),
            required_relations,
        )
        expected_parent = _build_experience_plan(
            expected_source,
            expected_graph,
            expected_plan,
            required_nuclei,
            required_relations,
            reception_targets,
        )
    except Exception:
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable") from None
    if source != expected_source or source.owner_universe != expected_universe:
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
    if issues or grounded_plan != expected_plan:
        raise CMEEStage1ContractError("stage1_grounded_observation_plan_noncanonical")
    if graph != expected_graph:
        raise CMEEStage1ContractError("stage1_grounded_graph_noncanonical")
    if parent_plan != expected_parent:
        raise CMEEStage1ContractError("stage1_parent_plan_noncanonical")


def _source_evidence_ids(
    source: AdmittedTextSource,
    span_ids: Sequence[str],
) -> tuple[str, ...]:
    try:
        refs = tuple(source.evidence_ref(span_id) for span_id in span_ids)
    except Exception:
        raise CMEEStage1ContractError("stage1_semantic_plan_evidence_unresolved") from None
    evidence = tuple(str(getattr(ref, "evidence_id", "") or "") for ref in refs)
    if not evidence or any(not row for row in evidence) or len(evidence) != len(set(evidence)):
        raise CMEEStage1ContractError("stage1_semantic_plan_evidence_invalid")
    return evidence


def _source_owner(source: AdmittedTextSource, span_ids: Sequence[str]) -> str:
    try:
        owners = _ordered(source.meaning_owner_for_span(span_id) for span_id in span_ids)
    except Exception:
        raise CMEEStage1ContractError("stage1_semantic_plan_owner_unresolved") from None
    if len(owners) != 1:
        raise CMEEStage1ContractError("stage1_semantic_plan_owner_ambiguous")
    return owners[0]


def _bind_grounded_plan(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: GroundedObservationPlan,
) -> _PlanBinding:
    envelope = getattr(source, "envelope", None)
    owner_universe = getattr(source, "owner_universe", None)
    if (
        envelope is None
        or owner_universe is None
        or getattr(envelope, "envelope_id", None) != graph.source_envelope_id
        or getattr(owner_universe, "source_version", None) != graph.source_version
        or getattr(owner_universe, "obligation_version", None)
        != graph.obligation_version
        or getattr(owner_universe, "owner_universe_digest", None)
        != graph.owner_universe_digest
    ):
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
    nuclei = getattr(grounded_plan, "nuclei", None)
    relations = getattr(grounded_plan, "relations", None)
    coverage = getattr(grounded_plan, "coverage_requirements", None)
    if type(nuclei) is not tuple or type(relations) is not tuple or coverage is None:
        raise CMEEStage1ContractError("stage1_semantic_plan_shape_invalid")
    required_nucleus_refs = getattr(coverage, "required_nucleus_ids", None)
    required_relation_refs = getattr(coverage, "required_relation_ids", None)
    if type(required_nucleus_refs) is not tuple or type(required_relation_refs) is not tuple:
        raise CMEEStage1ContractError("stage1_semantic_plan_required_refs_invalid")

    node_meta: dict[str, object] = {}
    nucleus_to_node: dict[str, str] = {}
    source_order: dict[str, int] = {}
    used_nodes: set[str] = set()
    for index, nucleus in enumerate(nuclei):
        grounding = _enum_or_text(getattr(nucleus, "grounding_kind", ""))
        if grounding not in _ADMITTED_NUCLEUS_GROUNDING:
            continue
        nucleus_id = str(getattr(nucleus, "nucleus_id", "") or "")
        kind = _enum_or_text(getattr(nucleus, "kind", ""))
        span_ids = getattr(nucleus, "source_span_ids", None)
        if not nucleus_id or not kind or type(span_ids) is not tuple:
            raise CMEEStage1ContractError("stage1_semantic_plan_nucleus_invalid")
        evidence = _source_evidence_ids(source, span_ids)
        owner = _source_owner(source, span_ids)
        matches = tuple(
            row
            for row in graph.nodes
            if row.node_id not in used_nodes
            and row.owner_id == owner
            and _enum_or_text(row.node_kind) == kind
            and _enum_or_text(row.grounding_kind) == grounding
            and tuple(row.evidence_ids) == evidence
            and row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        )
        if len(matches) != 1:
            raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
        node = matches[0]
        used_nodes.add(node.node_id)
        nucleus_to_node[nucleus_id] = node.node_id
        node_meta[node.node_id] = nucleus
        source_order[node.node_id] = index

    edge_meta: dict[str, object] = {}
    relation_to_edge: dict[str, str] = {}
    used_edges: set[str] = set()
    relation_offset = len(nuclei)
    for index, relation in enumerate(relations):
        grounding = _enum_or_text(getattr(relation, "grounding_kind", ""))
        if grounding not in _ADMITTED_RELATION_GROUNDING:
            continue
        relation_id = str(getattr(relation, "relation_id", "") or "")
        relation_kind = _enum_or_text(getattr(relation, "type", ""))
        from_id = str(getattr(relation, "from_nucleus_id", "") or "")
        to_id = str(getattr(relation, "to_nucleus_id", "") or "")
        span_ids = getattr(relation, "source_span_ids", None)
        if (
            not relation_id
            or not relation_kind
            or type(span_ids) is not tuple
            or from_id not in nucleus_to_node
            or to_id not in nucleus_to_node
        ):
            raise CMEEStage1ContractError("stage1_semantic_plan_relation_invalid")
        evidence = _source_evidence_ids(source, span_ids)
        owner = _source_owner(source, span_ids)
        matches = tuple(
            row
            for row in graph.edges
            if row.edge_id not in used_edges
            and row.owner_id == owner
            and _enum_or_text(row.relation) == relation_kind
            and row.source_node_id == nucleus_to_node[from_id]
            and row.target_node_id == nucleus_to_node[to_id]
            and _enum_or_text(row.grounding_kind) == grounding
            and tuple(row.evidence_ids) == evidence
            and row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        )
        if len(matches) != 1:
            raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
        edge = matches[0]
        used_edges.add(edge.edge_id)
        relation_to_edge[relation_id] = edge.edge_id
        edge_meta[edge.edge_id] = relation
        source_order[edge.edge_id] = relation_offset + index

    if any(ref not in nucleus_to_node for ref in required_nucleus_refs):
        raise CMEEStage1ContractError("stage1_required_nucleus_unresolved")
    if any(ref not in relation_to_edge for ref in required_relation_refs):
        raise CMEEStage1ContractError("stage1_required_relation_unresolved")
    required_edges = frozenset(relation_to_edge[ref] for ref in required_relation_refs)
    covered_nodes = {
        endpoint
        for edge in graph.edges
        if edge.edge_id in required_edges
        for endpoint in (edge.source_node_id, edge.target_node_id)
    }
    required_nodes = frozenset(
        nucleus_to_node[ref]
        for ref in required_nucleus_refs
        if nucleus_to_node[ref] not in covered_nodes
    )
    return _PlanBinding(
        node_meta=node_meta,
        edge_meta=edge_meta,
        required_node_ids=required_nodes,
        required_edge_ids=required_edges,
        source_order=source_order,
    )


def _resolve_binding(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    visible_claim_ids: set[str],
) -> _PlanBinding:
    _validate_canonical_semantic_inputs(
        source,
        grounded_plan,
        graph,
        parent_plan,
    )
    binding = _bind_grounded_plan(source, graph, grounded_plan)
    admitted_nodes = {
        row.node_id
        for row in graph.nodes
        if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        and _enum_or_text(row.grounding_kind) in _ADMITTED_NUCLEUS_GROUNDING
    }
    admitted_edges = {
        row.edge_id
        for row in graph.edges
        if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        and _enum_or_text(row.grounding_kind) in _ADMITTED_RELATION_GROUNDING
    }
    if (
        admitted_nodes != set(binding.node_meta)
        or admitted_edges != set(binding.edge_meta)
    ):
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
    visible_nodes = {
        row.node_id for row in graph.nodes if row.node_id in visible_claim_ids
    }
    visible_edges = {
        row.edge_id for row in graph.edges if row.edge_id in visible_claim_ids
    }
    if not binding.required_node_ids.issubset(visible_nodes) or not binding.required_edge_ids.issubset(visible_edges):
        raise CMEEStage1ContractError("stage1_required_semantic_not_visible")
    required_owners = set(parent_plan.required_observation_owner_ids)
    node_by_id = {row.node_id: row for row in graph.nodes}
    edge_by_id = {row.edge_id: row for row in graph.edges}
    required_semantic_owners = {
        *(node_by_id[row].owner_id for row in binding.required_node_ids),
        *(edge_by_id[row].owner_id for row in binding.required_edge_ids),
    }
    if not required_owners.issubset(required_semantic_owners):
        raise CMEEStage1ContractError("stage1_required_owner_uncovered")
    return binding


def _qualifiers(meta: Optional[object], *, role: Optional[str] = None) -> tuple[str, ...]:
    if meta is None:
        return (_PROVISIONAL_QUALIFIER,)
    frame = getattr(meta, "semantic_frame", None)
    if frame is None:
        return (_PROVISIONAL_QUALIFIER,)
    prefix = f"{role.lower()}_" if role else ""
    values = (
        ("actor", _enum_or_text(getattr(frame, "actor", ""))),
        ("polarity", _enum_or_text(getattr(frame, "polarity", ""))),
        ("modality", _enum_or_text(getattr(frame, "modality", ""))),
        ("time_scope", _enum_or_text(getattr(frame, "time_scope", ""))),
    )
    return (
        _PROVISIONAL_QUALIFIER,
        *(f"{prefix}{name}:{value}" for name, value in values if value),
    )


def _retention_rank(meta: object, *, required: bool) -> int:
    retention = _enum_or_text(getattr(meta, "retention", "")).lower()
    try:
        rank = _RETENTION_PRIORITY[retention]
    except KeyError:
        raise CMEEStage1ContractError("stage1_retention_invalid") from None
    if required and retention != "required":
        raise CMEEStage1ContractError("stage1_required_retention_mismatch")
    return rank


def _direct_shape(
    node: MeaningNode,
    meta: Optional[object],
) -> tuple[InterpretationKind, SemanticOperator]:
    kind = _enum_or_text(node.node_kind).lower()
    frame = getattr(meta, "semantic_frame", None)
    modality = _enum_or_text(getattr(frame, "modality", "")).lower()
    predicate = _enum_or_text(getattr(frame, "predicate_kind", "")).lower()
    attribute_codes = frozenset(
        _enum_or_text(row)
        for row in getattr(frame, "attribute_codes", ())
        if _enum_or_text(row)
    )
    if kind in _DIRECTION_KINDS or modality in {"wish", "intention"} or predicate == "wish":
        return InterpretationKind.DIRECT_DIRECTION, SemanticOperator.PRESENT_DIRECTION
    if (
        kind in _CHANGE_KINDS
        or predicate == "change"
        or "operator:change" in attribute_codes
        or "operator:positive_change" in attribute_codes
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE
    if (
        kind in _BURDEN_KINDS
        or predicate == "constraint"
        or "operator:constraint" in attribute_codes
        or "detected_type:limit_signal" in attribute_codes
        or "detected_type:fear" in attribute_codes
        or any(row.startswith("source_claim:pressure.") for row in attribute_codes)
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN
    if (
        kind in _ACTION_KINDS
        or predicate == "action"
        or "operator:action" in attribute_codes
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_ACTUAL_OUTPUT
    if (
        kind in _UNFINISHED_KINDS
        or modality == "uncertain"
        or "operator:uncertainty" in attribute_codes
    ):
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE


def _direct_argument_bindings(
    node: MeaningNode,
    meta: Optional[object],
) -> tuple[ArgumentBinding, ...]:
    semantic_ref = _node_ref(node.node_id)
    bindings = [ArgumentBinding(ArgumentRole.PRIMARY, semantic_ref)]
    frame = getattr(meta, "semantic_frame", None)
    modality = _enum_or_text(getattr(frame, "modality", "")).lower()
    actor = _enum_or_text(getattr(frame, "actor", "")).lower()
    if actor in {"current_user", "user"} and modality in {
        "feeling",
        "wish",
        "intention",
        "refusal",
        "uncertain",
    }:
        # The experiencer binding reuses the same canonical source proposition;
        # it never creates a person node or a free-form semantic ref.
        bindings.append(ArgumentBinding(ArgumentRole.EXPERIENCER, semantic_ref))
    return tuple(bindings)


def _validate_interpretation_matrix(
    candidate: EmlisInterpretationCandidate,
) -> None:
    matches = tuple(
        row
        for row in INTERPRETATION_MATRIX_EXACT13
        if row[:3]
        == (
            candidate.candidate_kind,
            candidate.semantic_operator,
            candidate.relation_operator,
        )
    )
    if len(matches) != 1:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    required_roles = matches[0][3]
    actual_roles = tuple(row.role for row in candidate.argument_bindings)
    direct_optional_experiencer = (
        candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM
        and actual_roles
        in {
            required_roles,
            (*required_roles, ArgumentRole.EXPERIENCER),
        }
    )
    if not direct_optional_experiencer and actual_roles != required_roles:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
        if candidate.relation_basis_refs:
            raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    elif len(candidate.relation_basis_refs) != 1:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")


def _is_direction(node: MeaningNode, meta: Optional[object]) -> bool:
    return _direct_shape(node, meta)[0] is InterpretationKind.DIRECT_DIRECTION


def _is_burden(node: MeaningNode, meta: Optional[object]) -> bool:
    return _direct_shape(node, meta)[1] is SemanticOperator.PRESENT_BURDEN


def _relation_shape(
    edge: MeaningEdge,
    node_by_id: Mapping[str, MeaningNode],
    binding: _PlanBinding,
) -> Optional[
    tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ]
]:
    relation = _enum_or_text(edge.relation)
    source = node_by_id[edge.source_node_id]
    target = node_by_id[edge.target_node_id]
    source_ref = _node_ref(source.node_id)
    target_ref = _node_ref(target.node_id)
    source_meta = binding.node_meta.get(source.node_id)
    target_meta = binding.node_meta.get(target.node_id)

    def symmetric(
        kind: InterpretationKind,
        operator: RelationOperator,
    ) -> tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ]:
        left, right = sorted((source_ref, target_ref))
        return (
            kind,
            SemanticOperator.SYNTHESIZE_RELATION,
            operator,
            (
                ArgumentBinding(ArgumentRole.LEFT, left),
                ArgumentBinding(ArgumentRole.RIGHT, right),
            ),
        )

    if relation == "coexistence":
        return symmetric(InterpretationKind.COEXISTENCE, RelationOperator.COEXISTS_WITH)
    if relation == "contrast":
        return symmetric(InterpretationKind.TENSION, RelationOperator.TENSION_WITH)
    if relation in {"wish_and_constraint", "preserves_despite", "attempt_and_block"}:
        if _is_direction(source, source_meta) and _is_burden(target, target_meta):
            operator = (
                RelationOperator.COEXISTS_WITH
                if relation == "wish_and_constraint"
                else RelationOperator.TENSION_WITH
            )
            return (
                InterpretationKind.DIRECTION_UNDER_BURDEN,
                SemanticOperator.SYNTHESIZE_RELATION,
                operator,
                (
                    ArgumentBinding(ArgumentRole.LEFT, source_ref),
                    ArgumentBinding(ArgumentRole.RIGHT, target_ref),
                ),
            )
        return None
    if relation == "action_supports_change":
        if (
            _enum_or_text(source.node_kind).lower() not in _ACTION_KINDS
            or _enum_or_text(target.node_kind).lower() not in _CHANGE_KINDS
        ):
            return None
        return (
            InterpretationKind.ACTION_THEN_CHANGE_ONCE,
            SemanticOperator.PRESENT_CHANGE,
            RelationOperator.ACTION_PRECEDES_CHANGE,
            (
                ArgumentBinding(ArgumentRole.ACTION, source_ref),
                ArgumentBinding(ArgumentRole.CHANGE, target_ref),
            ),
        )
    if relation in {"temporal_before_after", "shift_from_to"}:
        if (
            _enum_or_text(source.node_kind).lower() not in _EVENT_KINDS
            or _enum_or_text(target.node_kind).lower() not in _RESIDUE_KINDS
        ):
            return None
        return (
            InterpretationKind.RESIDUE_AFTER_EVENT,
            SemanticOperator.PRESENT_RESIDUE,
            RelationOperator.TEMPORALLY_PRECEDES,
            (
                ArgumentBinding(ArgumentRole.BEFORE, source_ref),
                ArgumentBinding(ArgumentRole.AFTER, target_ref),
            ),
        )
    if relation == "user_stated_cause":
        return (
            InterpretationKind.SOURCE_STATED_CAUSE,
            SemanticOperator.SYNTHESIZE_RELATION,
            RelationOperator.SOURCE_EXPLICIT_CAUSE,
            (
                ArgumentBinding(ArgumentRole.CAUSE, source_ref),
                ArgumentBinding(ArgumentRole.EFFECT, target_ref),
            ),
        )
    return None


def _candidate_from_direct(
    graph: GroundedMeaningGraph,
    node: MeaningNode,
    meta: Optional[object],
) -> EmlisInterpretationCandidate:
    kind, semantic_operator = _direct_shape(node, meta)
    semantic_ref = _node_ref(node.node_id)
    candidate = EmlisInterpretationCandidate(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        candidate_id="",
        candidate_kind=kind,
        claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
        semantic_operator=semantic_operator,
        argument_bindings=_direct_argument_bindings(node, meta),
        relation_operator=RelationOperator.NO_RELATION_CLAIM,
        relation_basis_refs=(),
        derivation_rule_id=(
            f"cocolon.cmee.v1a.stage1.direct.{kind.value.lower()}.v1"
        ),
        semantic_refs=(semantic_ref,),
        evidence_refs=tuple(
            _evidence_ref(row, graph.source_version) for row in node.evidence_ids
        ),
        basis_candidate_refs=(),
        epistemic_state=InterpretationEpistemicState.PROVISIONAL_INTERPRETATION,
        required_qualifiers=_qualifiers(meta),
        forbidden_promotions=_FORBIDDEN_PROMOTIONS,
    )
    _validate_interpretation_matrix(candidate)
    return _identified(candidate, "candidate_id")


def _candidate_from_relation(
    graph: GroundedMeaningGraph,
    edge: MeaningEdge,
    binding: _PlanBinding,
    shape: tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ],
) -> EmlisInterpretationCandidate:
    kind, semantic_operator, relation_operator, arguments = shape
    node_by_id = {row.node_id: row for row in graph.nodes}
    semantic_refs = tuple(row.semantic_ref for row in arguments)
    evidence_ids = _ordered(
        (
            *(item for ref in semantic_refs for item in node_by_id[_local_ref(ref)].evidence_ids),
            *edge.evidence_ids,
        )
    )
    qualifiers = [_PROVISIONAL_QUALIFIER]
    for argument in arguments:
        meta = binding.node_meta.get(_local_ref(argument.semantic_ref))
        qualifiers.extend(_qualifiers(meta, role=argument.role.value)[1:])
    candidate = EmlisInterpretationCandidate(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        candidate_id="",
        candidate_kind=kind,
        claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
        semantic_operator=semantic_operator,
        argument_bindings=arguments,
        relation_operator=relation_operator,
        relation_basis_refs=(_edge_ref(edge.edge_id),),
        derivation_rule_id=(
            "cocolon.cmee.v1a.stage1.relation."
            f"{_enum_or_text(edge.relation).lower()}.v1"
        ),
        semantic_refs=semantic_refs,
        evidence_refs=tuple(
            _evidence_ref(row, graph.source_version) for row in evidence_ids
        ),
        basis_candidate_refs=(),
        epistemic_state=InterpretationEpistemicState.PROVISIONAL_INTERPRETATION,
        required_qualifiers=tuple(qualifiers),
        forbidden_promotions=_FORBIDDEN_PROMOTIONS,
    )
    _validate_interpretation_matrix(candidate)
    return _identified(candidate, "candidate_id")


def _local_ref(value: str) -> str:
    try:
        return value.split(":", 1)[1].rsplit("@", 1)[0]
    except (IndexError, AttributeError):
        raise CMEEStage1ContractError("stage1_semantic_ref_invalid") from None


def _candidate_rows(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> tuple[_CandidateRow, ...]:
    _validate_graph_and_parent(graph, parent_plan)
    visible_claim_ids = _visible_claim_ids(graph, parent_plan)
    binding = _resolve_binding(
        graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        visible_claim_ids=visible_claim_ids,
    )
    node_by_id = {row.node_id: row for row in graph.nodes}
    rows: list[_CandidateRow] = []

    # Required relations own endpoint coverage before direct alternatives.
    for edge in graph.edges:
        if edge.edge_id not in visible_claim_ids:
            continue
        required = edge.edge_id in binding.required_edge_ids
        endpoints = (
            node_by_id[edge.source_node_id],
            node_by_id[edge.target_node_id],
        )
        if edge.source_node_id == edge.target_node_id:
            if required:
                raise CMEEStage1ContractError(
                    "stage1_relation_direction_invalid"
                )
            continue
        if (
            edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or _enum_or_text(edge.grounding_kind)
            not in _ADMITTED_RELATION_GROUNDING
            or not edge.evidence_ids
            or len(edge.evidence_ids) != len(set(edge.evidence_ids))
            or any(
                node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or _enum_or_text(node.grounding_kind)
                not in _ADMITTED_NUCLEUS_GROUNDING
                or not node.evidence_ids
                or len(node.evidence_ids) != len(set(node.evidence_ids))
                for node in endpoints
            )
        ):
            if required:
                raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
            continue
        shape = _relation_shape(edge, node_by_id, binding)
        if shape is None:
            if required:
                relation_kind = _enum_or_text(edge.relation)
                if _cause_like_relation(relation_kind):
                    raise CMEEStage1ContractError("stage1_unsupported_cause")
                if relation_kind in {
                    "wish_and_constraint",
                    "preserves_despite",
                    "attempt_and_block",
                    "action_supports_change",
                    "temporal_before_after",
                    "shift_from_to",
                }:
                    raise CMEEStage1ContractError(
                        "stage1_relation_direction_invalid"
                    )
                raise CMEEStage1ContractError(
                    "stage1_interpretation_matrix_invalid"
                )
            continue
        candidate = _candidate_from_relation(graph, edge, binding, shape)
        rows.append(
            _CandidateRow(
                candidate=candidate,
                required=required,
                is_relation=True,
                retention_rank=_retention_rank(
                    binding.edge_meta[edge.edge_id], required=required
                ),
                source_order=binding.source_order.get(edge.edge_id, len(graph.nodes)),
            )
        )

    for node in graph.nodes:
        if node.node_id not in visible_claim_ids:
            continue
        required = node.node_id in binding.required_node_ids
        if (
            node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or _enum_or_text(node.grounding_kind)
            not in _ADMITTED_NUCLEUS_GROUNDING
            or not node.evidence_ids
            or len(node.evidence_ids) != len(set(node.evidence_ids))
        ):
            if required:
                raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
            # UNKNOWN and source-explicit-not-realized rows never become an
            # InterpretationCandidate.
            continue
        candidate = _candidate_from_direct(
            graph, node, binding.node_meta.get(node.node_id)
        )
        rows.append(
            _CandidateRow(
                candidate=candidate,
                required=required,
                is_relation=False,
                retention_rank=_retention_rank(
                    binding.node_meta[node.node_id], required=required
                ),
                source_order=binding.source_order.get(node.node_id, 0),
            )
        )

    if not rows:
        raise CMEEStage1ContractError("stage1_candidate_pool_empty")
    rows.sort(
        key=lambda row: (
            0 if row.required else 1,
            0 if row.is_relation else 1,
            row.retention_rank,
            row.source_order,
            _OPERATOR_PRIORITY[row.candidate.relation_operator],
            row.candidate.semantic_refs,
            row.candidate.candidate_id,
        )
    )

    selected: list[_CandidateRow] = []
    kind_counts: dict[InterpretationKind, int] = {}
    for row in rows:
        count = kind_counts.get(row.candidate.candidate_kind, 0)
        if count >= INTERPRETATION_CANDIDATE_KIND_CAP:
            if row.required:
                raise CMEEStage1ContractError("stage1_required_candidate_overflow")
            continue
        selected.append(row)
        kind_counts[row.candidate.candidate_kind] = count + 1

    if len(selected) > INTERPRETATION_CANDIDATE_POOL_CAP:
        if any(row.required for row in selected[INTERPRETATION_CANDIDATE_POOL_CAP:]):
            raise CMEEStage1ContractError("stage1_required_candidate_overflow")
        selected = selected[:INTERPRETATION_CANDIDATE_POOL_CAP]
    if not selected or not any(row.required for row in selected):
        raise CMEEStage1ContractError("stage1_required_candidate_missing")
    return tuple(selected)


def build_interpretation_candidate_pool(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> tuple[EmlisInterpretationCandidate, ...]:
    """Build the canonical bounded provisional InterpretationCandidate pool."""

    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    candidates = tuple(row.candidate for row in rows)
    if len(candidates) > INTERPRETATION_CANDIDATE_POOL_CAP:
        raise CMEEStage1ContractError("stage1_candidate_pool_cap_exceeded")
    for candidate in candidates:
        validate_stage1_identity(candidate)
    return candidates


def validate_interpretation_candidate_pool(
    candidates: Sequence[EmlisInterpretationCandidate],
    *,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> None:
    if type(candidates) is not tuple:
        raise CMEEStage1ContractError("stage1_candidate_pool_not_tuple")
    expected = build_interpretation_candidate_pool(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    if tuple(candidates) != expected:
        raise CMEEStage1ContractError("stage1_candidate_pool_noncanonical")


def _candidate_slot(candidate: EmlisInterpretationCandidate) -> MeaningFieldSlot:
    if candidate.candidate_kind is InterpretationKind.DIRECT_DIRECTION:
        return MeaningFieldSlot.DIRECTION
    if candidate.candidate_kind is InterpretationKind.UNFINISHED:
        return MeaningFieldSlot.UNFINISHED
    if candidate.candidate_kind is InterpretationKind.COEXISTENCE:
        return MeaningFieldSlot.COEXISTENCE
    if candidate.candidate_kind in {
        InterpretationKind.TENSION,
        InterpretationKind.DIRECTION_UNDER_BURDEN,
    }:
        return (
            MeaningFieldSlot.COEXISTENCE
            if candidate.relation_operator is RelationOperator.COEXISTS_WITH
            else MeaningFieldSlot.TENSION
        )
    if candidate.candidate_kind is InterpretationKind.ACTION_THEN_CHANGE_ONCE:
        return MeaningFieldSlot.CHANGE
    if candidate.candidate_kind is InterpretationKind.RESIDUE_AFTER_EVENT:
        return MeaningFieldSlot.RESIDUE
    if candidate.candidate_kind is InterpretationKind.SOURCE_STATED_CAUSE:
        return MeaningFieldSlot.TIME_RELATION
    if candidate.semantic_operator is SemanticOperator.PRESENT_BURDEN:
        return MeaningFieldSlot.BURDEN
    if candidate.semantic_operator is SemanticOperator.PRESENT_CHANGE:
        return MeaningFieldSlot.CHANGE
    if candidate.semantic_operator is SemanticOperator.PRESENT_ACTUAL_OUTPUT:
        return MeaningFieldSlot.OUTPUT
    return MeaningFieldSlot.CENTER


def _entry(
    slot: MeaningFieldSlot,
    candidates: Sequence[EmlisInterpretationCandidate],
) -> MeaningFieldEntry:
    return MeaningFieldEntry(
        slot=slot,
        interpretation_candidate_refs=tuple(row.candidate_id for row in candidates),
        semantic_refs=_ordered(ref for row in candidates for ref in row.semantic_refs),
        evidence_refs=_ordered(ref for row in candidates for ref in row.evidence_refs),
    )


def _material_unknown_refs(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
) -> tuple[str, ...]:
    unknown_owners = tuple(parent_plan.visible_unknown_owner_ids)
    if (
        any(type(row) is not str or not row for row in unknown_owners)
        or len(unknown_owners) != len(set(unknown_owners))
        or not set(parent_plan.required_unknown_owner_ids).issubset(
            set(unknown_owners)
        )
        or not set(unknown_owners).issubset(set(parent_plan.unresolved_owner_ids))
    ):
        raise CMEEStage1ContractError("stage1_material_unknown_owner_invalid")
    disposition = {row.meaning_owner_id: row for row in graph.owner_dispositions}
    if len(disposition) != len(graph.owner_dispositions):
        raise CMEEStage1ContractError("stage1_owner_disposition_duplicate")
    node_by_id = {row.node_id: row for row in graph.nodes}
    source_evidence_ids = {row.evidence_id for row in source.evidence_refs}
    refs: list[str] = []
    for owner_id in unknown_owners:
        row = disposition.get(owner_id)
        target = row.target_unknown_ref if row is not None else None
        node = node_by_id.get(str(target or ""))
        if (
            row is None
            or row.route_b_disposition
            is not RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
            or type(target) is not str
            or not target
            or row.visible_claim_refs != (target,)
            or node is None
            or node.owner_id != owner_id
            or node.epistemic_state is not EpistemicState.UNKNOWN
            or not node.evidence_ids
            or len(node.evidence_ids) != len(set(node.evidence_ids))
            or tuple(node.evidence_ids) != tuple(row.evidence_refs)
            or not set(node.evidence_ids).issubset(source_evidence_ids)
        ):
            raise CMEEStage1ContractError("stage1_material_unknown_unreachable")
        refs.append(f"unknown:{target}@{graph.obligation_version}")
    return tuple(refs)


def build_emlis_meaning_field(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    candidates: Sequence[EmlisInterpretationCandidate],
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> EmlisMeaningField:
    """Project the canonical pool into Emlis request-local attention slots."""

    candidate_tuple = tuple(candidates)
    validate_interpretation_candidate_pool(
        candidate_tuple,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    required = tuple(row.candidate.candidate_id for row in rows if row.required)
    required_set = set(required)
    center = next(
        (row for row in candidate_tuple if row.candidate_id in required_set),
        candidate_tuple[0],
    )
    grouped: dict[MeaningFieldSlot, list[EmlisInterpretationCandidate]] = {}
    for candidate in candidate_tuple:
        grouped.setdefault(_candidate_slot(candidate), []).append(candidate)
    # ``center_candidate_ref`` owns request-local product attention.  Entries
    # own semantic slot membership, so the center pointer is not duplicated
    # into CENTER when its candidate belongs to another material slot.
    entries = tuple(
        _entry(slot, grouped[slot]) for slot in _SLOT_ORDER if grouped.get(slot)
    )
    entry_refs = tuple(
        ref for entry in entries for ref in entry.interpretation_candidate_refs
    )
    if (
        len(entry_refs) != len(set(entry_refs))
        or set(entry_refs) != {row.candidate_id for row in candidate_tuple}
        or any(entry_refs.count(ref) != 1 for ref in required)
    ):
        raise CMEEStage1ContractError(
            "stage1_meaning_field_required_not_exact_cover"
        )
    meaning_field = EmlisMeaningField(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        meaning_field_id="",
        grounded_graph_ref=_graph_ref(grounded_graph),
        center_candidate_ref=center.candidate_id,
        entries=entries,
        required_candidate_refs=required,
        material_unknown_refs=_material_unknown_refs(
            grounded_graph, parent_plan, source
        ),
    )
    result = _identified(meaning_field, "meaning_field_id")
    validate_stage1_identity(result)
    return result


def validate_emlis_meaning_field(
    meaning_field: EmlisMeaningField,
    *,
    candidates: Sequence[EmlisInterpretationCandidate],
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> None:
    candidate_ids = tuple(row.candidate_id for row in candidates)
    entry_refs = tuple(
        ref
        for entry in getattr(meaning_field, "entries", ())
        for ref in getattr(entry, "interpretation_candidate_refs", ())
    )
    if (
        type(meaning_field) is not EmlisMeaningField
        or meaning_field.center_candidate_ref not in set(candidate_ids)
        or len(entry_refs) != len(set(entry_refs))
        or set(entry_refs) != set(candidate_ids)
        or any(
            entry_refs.count(ref) != 1
            for ref in meaning_field.required_candidate_refs
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_meaning_field_required_not_exact_cover"
        )
    expected = build_emlis_meaning_field(
        grounded_graph,
        parent_plan,
        tuple(candidates),
        source=source,
        grounded_plan=grounded_plan,
    )
    if meaning_field != expected:
        raise CMEEStage1ContractError("stage1_meaning_field_noncanonical")


def _contribution_kind(
    candidate: EmlisInterpretationCandidate,
) -> ObservationContributionKind:
    slot = _candidate_slot(candidate)
    mapping = {
        MeaningFieldSlot.CENTER: ObservationContributionKind.OBSERVE_CENTER,
        MeaningFieldSlot.COEXISTENCE: ObservationContributionKind.OBSERVE_COEXISTENCE,
        MeaningFieldSlot.TENSION: ObservationContributionKind.OBSERVE_TENSION,
        MeaningFieldSlot.DIRECTION: ObservationContributionKind.OBSERVE_DIRECTION,
        MeaningFieldSlot.BURDEN: ObservationContributionKind.OBSERVE_BURDEN,
        MeaningFieldSlot.CHANGE: (
            ObservationContributionKind.OBSERVE_ACTION_THEN_CHANGE
            if candidate.candidate_kind is InterpretationKind.ACTION_THEN_CHANGE_ONCE
            else ObservationContributionKind.OBSERVE_CHANGE
        ),
        MeaningFieldSlot.OUTPUT: ObservationContributionKind.OBSERVE_ACTUAL_OUTPUT,
        MeaningFieldSlot.TIME_RELATION: ObservationContributionKind.OBSERVE_TIME_RELATION,
        MeaningFieldSlot.RESIDUE: ObservationContributionKind.PRESERVE_RESIDUE,
        MeaningFieldSlot.UNFINISHED: ObservationContributionKind.PRESERVE_UNFINISHED,
    }
    try:
        return mapping[slot]
    except KeyError:
        raise CMEEStage1ContractError(
            "stage1_observation_slot_mapping_invalid"
        ) from None


def _semantic_key(candidate: EmlisInterpretationCandidate) -> str:
    material = {
        "semantic_key_version": OBSERVATION_SEMANTIC_KEY_VERSION,
        "claim_domain": candidate.claim_domain,
        "semantic_operator": candidate.semantic_operator,
        "argument_bindings": candidate.argument_bindings,
        "relation_operator": candidate.relation_operator,
        "relation_basis_refs": candidate.relation_basis_refs,
        "required_qualifiers": candidate.required_qualifiers,
    }
    digest = hashlib.sha256(stage1_canonical_json_bytes(material)).hexdigest()
    return f"observation-key-{digest}"


def _selected_contribution_candidates(
    rows: Sequence[_CandidateRow],
) -> tuple[_CandidateRow, ...]:
    required = [row for row in rows if row.required]
    if len(required) > LAYER1_OBSERVATION_CONTRIBUTION_CAP:
        raise CMEEStage1ContractError("stage1_required_observation_unrealizable")
    optional = [
        row
        for row in rows
        if not row.required
    ]
    # Optional meanings deepen a single required observation by exact1.  They
    # never inflate an already-layered/dense required set or manufacture depth
    # from sentence budget alone.
    selected_optional = optional[:1] if len(required) == 1 else []
    return tuple((*required, *selected_optional))


def plan_layer1_observation(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    candidates: Sequence[EmlisInterpretationCandidate],
    meaning_field: EmlisMeaningField,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> tuple[PlannedObservationContribution, ...]:
    """Select exact-cover Layer 1 contributions and suppress optional tail."""

    candidate_tuple = tuple(candidates)
    validate_emlis_meaning_field(
        meaning_field,
        candidates=candidate_tuple,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    selected = _selected_contribution_candidates(rows)
    contributions: list[PlannedObservationContribution] = []
    for row in selected:
        candidate = row.candidate
        contribution = PlannedObservationContribution(
            schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            contribution_id="",
            parent_duty_ref=parent_plan.observation_duty_id,
            contribution_kind=_contribution_kind(candidate),
            interpretation_candidate_refs=(candidate.candidate_id,),
            semantic_operator=candidate.semantic_operator,
            argument_bindings=candidate.argument_bindings,
            relation_operator=candidate.relation_operator,
            relation_basis_refs=candidate.relation_basis_refs,
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.layer1."
                f"{_contribution_kind(candidate).value.lower()}.v1"
            ),
            semantic_refs=candidate.semantic_refs,
            evidence_refs=candidate.evidence_refs,
            retention="REQUIRED" if row.required else "OPTIONAL",
            semantic_key_version=OBSERVATION_SEMANTIC_KEY_VERSION,
            canonical_semantic_key=_semantic_key(candidate),
            prerequisite_contribution_refs=(),
            forbidden_operations=_FORBIDDEN_OBSERVATION_OPERATIONS,
        )
        identified = _identified(contribution, "contribution_id")
        validate_stage1_identity(identified)
        contributions.append(identified)
    if not contributions:
        raise CMEEStage1ContractError("stage1_observation_contribution_missing")
    return tuple(contributions)


def classify_observation_depth(
    contributions: Sequence[PlannedObservationContribution],
) -> ObservationDepthClass:
    """Classify depth from selected distinct contribution count only."""

    rows = tuple(contributions)
    if any(type(row) is not PlannedObservationContribution for row in rows):
        raise CMEEStage1ContractError("stage1_contribution_type_invalid")
    keys = tuple(row.canonical_semantic_key for row in rows)
    if len(keys) != len(set(keys)):
        raise CMEEStage1ContractError("stage1_duplicate_observation_contribution")
    count = len(rows)
    if count == 1:
        return ObservationDepthClass.FOCUSED
    if 2 <= count <= 3:
        return ObservationDepthClass.LAYERED
    if 4 <= count <= LAYER1_OBSERVATION_CONTRIBUTION_CAP:
        return ObservationDepthClass.DENSE
    raise CMEEStage1ContractError("stage1_observation_depth_unrealizable")


# Compatibility with the terminology used by the Step 2 execution row.
observation_depth_class = classify_observation_depth


def validate_layer1_observation_plan(
    contributions: Sequence[PlannedObservationContribution],
    *,
    candidates: Sequence[EmlisInterpretationCandidate],
    meaning_field: EmlisMeaningField,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> None:
    if type(contributions) is not tuple:
        raise CMEEStage1ContractError("stage1_contribution_array_not_tuple")
    candidate_by_id = {row.candidate_id: row for row in candidates}
    for contribution in contributions:
        if len(contribution.interpretation_candidate_refs) != 1:
            raise CMEEStage1ContractError(
                "stage1_observation_semantic_key_mismatch"
            )
        candidate = candidate_by_id.get(
            contribution.interpretation_candidate_refs[0]
        )
        if (
            candidate is None
            or contribution.semantic_key_version
            != OBSERVATION_SEMANTIC_KEY_VERSION
            or contribution.canonical_semantic_key != _semantic_key(candidate)
        ):
            raise CMEEStage1ContractError(
                "stage1_observation_semantic_key_mismatch"
            )
    expected = plan_layer1_observation(
        grounded_graph,
        parent_plan,
        tuple(candidates),
        meaning_field,
        source=source,
        grounded_plan=grounded_plan,
    )
    if tuple(contributions) != expected:
        raise CMEEStage1ContractError("stage1_observation_plan_noncanonical")
    classify_observation_depth(contributions)


def build_layer1_semantics(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> tuple[
    tuple[EmlisInterpretationCandidate, ...],
    EmlisMeaningField,
    tuple[PlannedObservationContribution, ...],
    tuple[str, ...],
    ObservationDepthClass,
]:
    """Build the complete Step 2 Layer 1 semantic tuple.

    The returned tuple is not another plan contract.  Its elements are the
    registered Step 1 children, their exact contribution order, and depth
    derived from that selected contribution count.
    """

    candidates = build_interpretation_candidate_pool(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    meaning_field = build_emlis_meaning_field(
        grounded_graph,
        parent_plan,
        candidates,
        source=source,
        grounded_plan=grounded_plan,
    )
    contributions = plan_layer1_observation(
        grounded_graph,
        parent_plan,
        candidates,
        meaning_field,
        source=source,
        grounded_plan=grounded_plan,
    )
    ordered_refs = tuple(row.contribution_id for row in contributions)
    depth = classify_observation_depth(contributions)
    return candidates, meaning_field, contributions, ordered_refs, depth


__all__ = [
    "INTERPRETATION_CANDIDATE_KIND_CAP",
    "INTERPRETATION_CANDIDATE_POOL_CAP",
    "INTERPRETATION_MATRIX_EXACT13",
    "LAYER1_OBSERVATION_CONTRIBUTION_CAP",
    "OBSERVATION_SEMANTIC_KEY_VERSION",
    "build_emlis_meaning_field",
    "build_interpretation_candidate_pool",
    "build_layer1_semantics",
    "classify_observation_depth",
    "observation_depth_class",
    "plan_layer1_observation",
    "validate_emlis_meaning_field",
    "validate_interpretation_candidate_pool",
    "validate_layer1_observation_plan",
]
