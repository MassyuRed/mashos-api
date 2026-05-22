# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 5 RelationGraph 2.0 bridge for EmlisAI Complete Composer.

This module is an additive internal bridge.  It connects the existing limited
relation taxonomy to the Complete Composer initial ObservationGraph v2 contract
so relation_type is preserved before SentencePlan/Surface Realizer run.

It does not generate ``comment_text`` and does not change DB physical names,
API routes, public response keys, or RN display contracts.
"""

from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_STAGE
from emlis_ai_complete_focus_selector import (
    CompleteCoveragePlan,
    build_complete_coverage_plan,
)
from emlis_ai_observation_material_connector import (
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    observation_material_connector_forward_meta,
)
from emlis_ai_limited_relation_taxonomy import (
    allowed_relation_types,
    build_limited_relation_taxonomy_meta,
    canonical_relation_type,
    normalize_relation_type,
    relation_definition,
    relation_family,
)

COMPLETE_RELATION_GRAPH_SERVICE_VERSION = "emlis.complete_relation_graph_service.v1"
COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION = "emlis.complete_observation_graph.v2"
COMPLETE_RELATION_GRAPH_SCHEMA_VERSION = COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION
COMPLETE_RELATION_GRAPH_NODE_SCHEMA_VERSION = "emlis.complete_relation_graph_node.v1"
COMPLETE_RELATION_GRAPH_EDGE_SCHEMA_VERSION = "emlis.complete_relation_graph_edge.v1"
COMPLETE_RELATION_BINDING_SEED_SCHEMA_VERSION = "emlis.complete_relation_binding_seed.v1"
COMPLETE_RELATION_GRAPH_STAGE = "Step5_RelationGraph_2_0_bridge"
COMPLETE_RELATION_GRAPH_STEP = COMPLETE_RELATION_GRAPH_STAGE
COMPLETE_RELATION_GRAPH_TARGET_STEP = COMPLETE_RELATION_GRAPH_STAGE
COMPLETE_RELATION_GRAPH_IMPLEMENTATION_UNIT = "Commit 5"

COMPLETE_RELATION_GRAPH_STATUS_READY = "ready"
COMPLETE_RELATION_GRAPH_STATUS_UNAVAILABLE = "unavailable"

RAW_INPUT_META_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
}

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"

# These are developer-facing constraints, not completed output sentences.
# They mirror the Step 5 design table: relation is a pre-generation constraint,
# not a post-hoc judgment over already generated text.
RELATION_SURFACE_POLICIES: dict[str, dict[str, Any]] = {
    "contrast": {
        "surface_intent": "place_different_grounded_states_side_by_side",
        "allowed_operation": "parallelize_without_declaring_true_side",
        "forbidden_surface_keys": ["single_true_feeling_claim", "collapse_one_side_as_real", "winner_side_claim"],
    },
    "coexistence": {
        "surface_intent": "keep_two_grounded_states_coexisting",
        "allowed_operation": "hold_both_without_positive_negative_simplification",
        "forbidden_surface_keys": ["positive_only_simplification", "negative_only_simplification", "single_axis_reduction"],
    },
    "pressure": {
        "surface_intent": "observe_pressure_without_personality_or_cause_claim",
        "allowed_operation": "name_load_or_pressure_inside_input_scope",
        "forbidden_surface_keys": ["personality_cause_claim", "diagnosis_claim", "blame_agent_claim"],
    },
    "approach_avoidance": {
        "surface_intent": "preserve_approach_and_avoidance_together",
        "allowed_operation": "show_both_movement_and_holdback",
        "forbidden_surface_keys": ["action_instruction", "choose_one_side", "push_toward_behavior"],
    },
    "recovery": {
        "surface_intent": "observe_small_recovery_without_over_comfort",
        "allowed_operation": "keep_recovery_connected_to_previous_load_when_present",
        "forbidden_surface_keys": ["already_fine_claim", "over_comfort", "recovery_as_resolution"],
    },
    "residue": {
        "surface_intent": "keep_aftereffect_or_remaining_feeling_grounded",
        "allowed_operation": "name_residue_without_symptom_or_trauma_conversion",
        "forbidden_surface_keys": ["trauma_claim", "symptom_claim", "diagnosis_conversion"],
    },
    "limit": {
        "surface_intent": "observe_boundary_or_limit_without_action_pressure",
        "allowed_operation": "name_limit_in_input_scope",
        "forbidden_surface_keys": ["urgent_action_instruction", "personality_boundary_claim"],
    },
    "context": {
        "surface_intent": "attach_explicit_context_only_when_anchor_exists",
        "allowed_operation": "use_context_as_supporting_constraint",
        "forbidden_surface_keys": ["unstated_history_fill", "cross_core_assumption"],
    },
    "center": {
        "surface_intent": "state_current_observation_focus",
        "allowed_operation": "use_single_grounded_focus",
        "forbidden_surface_keys": ["general_advice", "unanchored_summary"],
    },
}

DEFAULT_RELATION_POLICY = {
    "surface_intent": "preserve_grounded_relation",
    "allowed_operation": "use_relation_only_as_structural_constraint",
    "forbidden_surface_keys": ["overclaim", "diagnosis_claim", "fixed_sentence_template"],
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _dedupe(values: Iterable[Any] | Any | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        src: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        src = values
    else:
        src = [values]
    out: list[str] = []
    seen: set[str] = set()
    for raw in src:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean(key)
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out



def _observation_forward_meta(value: Any) -> dict[str, Any]:
    return observation_material_connector_forward_meta(value)


def _row_observation_meta(row: Mapping[str, Any]) -> dict[str, Any]:
    return _observation_forward_meta(row) or _observation_forward_meta(row.get("meta") if isinstance(row, Mapping) else None)


def _is_low_information_observation(meta: Mapping[str, Any] | None) -> bool:
    if not isinstance(meta, Mapping):
        return False
    return (
        _clean(meta.get("observation_reply_kind")) == OBSERVATION_REPLY_KIND_LOW_INFORMATION
        or bool(meta.get("low_information_known_scope_only"))
        or bool(meta.get("known_scope_only"))
    )


def _safe_int(value: Any, *, default: int = 0, minimum: int = 0, maximum: int = 999) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    out: dict[str, Any] = {}
    for key in (
        "node_id",
        "material_id",
        "phrase_unit_id",
        "evidence_span_id",
        "role",
        "polarity",
        "relation_type",
        "canonical_relation_type",
        "relation_family",
        "focus_rank",
        "focus_role",
        "must_keep",
        "line_role_hint",
        "source_anchor_present",
        "selection_reasons",
        "meta",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def relation_surface_policy(relation_type: Any) -> dict[str, Any]:
    relation = normalize_relation_type(relation_type)
    canonical = canonical_relation_type(relation)
    policy = RELATION_SURFACE_POLICIES.get(relation) or RELATION_SURFACE_POLICIES.get(canonical) or DEFAULT_RELATION_POLICY
    return {
        "relation_type": relation,
        "canonical_relation_type": canonical,
        "relation_family": relation_family(relation),
        "surface_intent": policy["surface_intent"],
        "allowed_operation": policy["allowed_operation"],
        "forbidden_surface_keys": list(policy["forbidden_surface_keys"]),
        "policy_is_sentence_template": False,
        "raw_input_included": False,
    }


def _line_role_for_rank(rank: int, total: int, required_line_roles: Sequence[Any], relation: str) -> str:
    required = tuple(_dedupe(required_line_roles))
    if rank <= 1:
        return "opening"
    if relation in {"contrast", "coexistence", "approach_avoidance", "pressure", "recovery", "residue"} and "relation" in required:
        return "relation"
    if rank >= total and "closing" in required and total >= 3:
        return "closing"
    return "core"


def _coerce_required_line_roles(value: Any) -> Tuple[str, ...]:
    roles = tuple(item for item in _dedupe(value) if item in {"opening", "core", "relation", "closing"})
    return roles or ("opening", "core", "relation")


@dataclass(frozen=True)
class CompleteRelationGraphNode:
    node_id: str
    material_id: str
    phrase_unit_id: str
    evidence_span_id: str
    role: str
    relation_type: str
    focus_rank: int = 1
    focus_role: str = "primary"
    polarity: str = "neutral"
    must_keep: bool = False
    line_role_hint: str = ""
    source_anchor_present: bool = False
    selection_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    source: str = "focus_selector"
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_RELATION_GRAPH_NODE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        role = _clean(self.role)
        relation = normalize_relation_type(self.relation_type, roles=(role,) if role else (), line_role=self.line_role_hint or role)
        object.__setattr__(self, "node_id", _clean(self.node_id))
        object.__setattr__(self, "material_id", _clean(self.material_id))
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "relation_type", relation)
        object.__setattr__(self, "focus_rank", _safe_int(self.focus_rank, default=1, minimum=1, maximum=999))
        object.__setattr__(self, "focus_role", _clean(self.focus_role) or "primary")
        object.__setattr__(self, "polarity", _clean(self.polarity) or "neutral")
        object.__setattr__(self, "must_keep", bool(self.must_keep))
        object.__setattr__(self, "line_role_hint", _clean(self.line_role_hint))
        object.__setattr__(self, "source_anchor_present", bool(self.source_anchor_present or self.evidence_span_id))
        object.__setattr__(self, "selection_reasons", tuple(_dedupe(self.selection_reasons)))
        object.__setattr__(self, "source", _clean(self.source) or "focus_selector")
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_RELATION_GRAPH_NODE_SCHEMA_VERSION)

    @property
    def canonical_relation_type(self) -> str:
        return canonical_relation_type(self.relation_type)

    @property
    def relation_family(self) -> str:
        return relation_family(self.relation_type)

    @property
    def relation_known(self) -> bool:
        return bool(relation_definition(self.relation_type) is not None)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.node_id:
            errors.append("relation_graph_node_id_missing")
        if not self.material_id:
            errors.append("material_id_missing")
        if not self.phrase_unit_id:
            errors.append("phrase_unit_id_missing")
        if not self.evidence_span_id:
            errors.append("evidence_span_id_missing")
        if not self.role:
            errors.append("role_missing")
        if not self.relation_type:
            errors.append("relation_type_missing")
        if self.relation_type and not self.relation_known:
            errors.append("relation_type_unmapped")
        if not self.source_anchor_present:
            errors.append("source_anchor_missing")
        return tuple(dict.fromkeys(errors))

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_sentence_plan_focus(self) -> dict[str, Any]:
        seed = {
            "node_id": self.node_id,
            "material_id": self.material_id,
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "role": self.role,
            "relation_type": self.relation_type,
            "canonical_relation_type": self.canonical_relation_type,
            "relation_family": self.relation_family,
            "focus_rank": self.focus_rank,
            "focus_role": self.focus_role,
            "must_keep": self.must_keep,
            "line_role_hint": self.line_role_hint,
            "relation_pre_generation_constraint": True,
            "raw_input_included": False,
        }
        seed.update(_observation_forward_meta(self.meta))
        return seed

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "node_id": self.node_id,
            "material_id": self.material_id,
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "role": self.role,
            "polarity": self.polarity,
            "relation_type": self.relation_type,
            "canonical_relation_type": self.canonical_relation_type,
            "relation_family": self.relation_family,
            **_observation_forward_meta(self.meta),
            "relation_known": self.relation_known,
            "focus_rank": self.focus_rank,
            "focus_role": self.focus_role,
            "must_keep": self.must_keep,
            "line_role_hint": self.line_role_hint,
            "source_anchor_present": self.source_anchor_present,
            "selection_reasons": list(self.selection_reasons),
            "relation_surface_policy": relation_surface_policy(self.relation_type),
            "relation_pre_generation_constraint": True,
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "comment_text_generated": False,
            "completion_sentence_template": False,
            "fixed_sentence_template": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "source": self.source,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class CompleteRelationGraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    edge_role: str = "relation_sequence"
    source_relation_type: str = ""
    target_relation_type: str = ""
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_RELATION_GRAPH_EDGE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        relation = normalize_relation_type(self.relation_type)
        object.__setattr__(self, "edge_id", _clean(self.edge_id))
        object.__setattr__(self, "source_node_id", _clean(self.source_node_id))
        object.__setattr__(self, "target_node_id", _clean(self.target_node_id))
        object.__setattr__(self, "relation_type", relation)
        object.__setattr__(self, "edge_role", _clean(self.edge_role) or "relation_sequence")
        object.__setattr__(self, "source_relation_type", normalize_relation_type(self.source_relation_type) if self.source_relation_type else "")
        object.__setattr__(self, "target_relation_type", normalize_relation_type(self.target_relation_type) if self.target_relation_type else "")
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_RELATION_GRAPH_EDGE_SCHEMA_VERSION)

    @property
    def canonical_relation_type(self) -> str:
        return canonical_relation_type(self.relation_type)

    @property
    def relation_family(self) -> str:
        return relation_family(self.relation_type)

    @property
    def relation_known(self) -> bool:
        return bool(relation_definition(self.relation_type) is not None)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.edge_id:
            errors.append("relation_graph_edge_id_missing")
        if not self.source_node_id or not self.target_node_id:
            errors.append("relation_graph_edge_endpoint_missing")
        if not self.relation_type:
            errors.append("relation_type_missing")
        if self.relation_type and not self.relation_known:
            errors.append("relation_type_unmapped")
        return tuple(dict.fromkeys(errors))

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_role": self.edge_role,
            "relation_type": self.relation_type,
            "canonical_relation_type": self.canonical_relation_type,
            "relation_family": self.relation_family,
            **_observation_forward_meta(self.meta),
            "relation_known": self.relation_known,
            "source_relation_type": self.source_relation_type,
            "target_relation_type": self.target_relation_type,
            "relation_pre_generation_constraint": True,
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


def _coerce_node(value: CompleteRelationGraphNode | Mapping[str, Any], *, index: int) -> CompleteRelationGraphNode | None:
    if isinstance(value, CompleteRelationGraphNode):
        return value
    row = _as_mapping(value)
    if not row:
        return None
    node_id = _clean(row.get("node_id")) or f"rg_node_{index}"
    material_id = _clean(row.get("material_id")) or node_id
    role = _clean(row.get("role"))
    relation = _clean(row.get("relation_type") or row.get("canonical_relation_type"))
    return CompleteRelationGraphNode(
        node_id=node_id,
        material_id=material_id,
        phrase_unit_id=_clean(row.get("phrase_unit_id")) or material_id,
        evidence_span_id=_clean(row.get("evidence_span_id")),
        role=role,
        relation_type=relation,
        focus_rank=row.get("focus_rank") or index,
        focus_role=row.get("focus_role") or ("primary" if index == 1 else "support"),
        polarity=row.get("polarity") or "neutral",
        must_keep=bool(row.get("must_keep")) or index == 1,
        line_role_hint=row.get("line_role_hint") or row.get("line_role") or "",
        source_anchor_present=bool(row.get("source_anchor_present") or row.get("evidence_span_id")),
        selection_reasons=row.get("selection_reasons") or (),
        source=row.get("source") or "focus_selector",
        meta={**(row.get("meta") or {}), **_row_observation_meta(row)},
    )


def _edge_relation(left: CompleteRelationGraphNode, right: CompleteRelationGraphNode) -> str:
    pair = {left.relation_type, right.relation_type}
    if "approach_avoidance" in pair:
        return "approach_avoidance"
    if "contrast" in pair:
        return "contrast"
    if "coexistence" in pair:
        return "coexistence"
    if pair == {"pressure", "recovery"} or pair == {"recovery", "pressure"}:
        return "recovery"
    return right.relation_type or left.relation_type or "coexistence"


def _edges_for_nodes(nodes: Sequence[CompleteRelationGraphNode]) -> Tuple[CompleteRelationGraphEdge, ...]:
    edges: list[CompleteRelationGraphEdge] = []
    for index in range(max(0, len(nodes) - 1)):
        left = nodes[index]
        right = nodes[index + 1]
        relation = _edge_relation(left, right)
        edges.append(
            CompleteRelationGraphEdge(
                edge_id=f"rg_edge_{index + 1}",
                source_node_id=left.node_id,
                target_node_id=right.node_id,
                relation_type=relation,
                source_relation_type=left.relation_type,
                target_relation_type=right.relation_type,
                edge_role="relation_sequence" if relation != "recovery" else "recovery_after_load_bridge",
                meta={"source_rank": left.focus_rank, "target_rank": right.focus_rank},
            )
        )
    return tuple(edges)


@dataclass(frozen=True)
class CompleteObservationGraphV2:
    coverage_group: str
    relation_nodes: Iterable[CompleteRelationGraphNode | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    optional_nodes: Iterable[CompleteRelationGraphNode | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    relation_edges: Iterable[CompleteRelationGraphEdge | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    sentence_budget: int = 0
    required_line_roles: Iterable[str] = dataclass_field(default_factory=tuple)
    requested_coverage_group: str = ""
    source_coverage_plan_meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    graph_id: str = "complete_observation_graph_v2"
    schema_version: str = COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION

    def __post_init__(self) -> None:
        nodes = tuple(node for node in (_coerce_node(item, index=index) for index, item in enumerate(tuple(self.relation_nodes or ()), start=1)) if node is not None)
        optional = tuple(node for node in (_coerce_node(item, index=index) for index, item in enumerate(tuple(self.optional_nodes or ()), start=len(nodes) + 1)) if node is not None)
        edges: list[CompleteRelationGraphEdge] = []
        for row in self.relation_edges:
            if isinstance(row, CompleteRelationGraphEdge):
                edges.append(row)
            elif isinstance(row, Mapping):
                edges.append(
                    CompleteRelationGraphEdge(
                        edge_id=row.get("edge_id") or f"rg_edge_{len(edges) + 1}",
                        source_node_id=row.get("source_node_id") or "",
                        target_node_id=row.get("target_node_id") or "",
                        relation_type=row.get("relation_type") or "",
                        edge_role=row.get("edge_role") or "relation_sequence",
                        source_relation_type=row.get("source_relation_type") or "",
                        target_relation_type=row.get("target_relation_type") or "",
                        meta=row.get("meta") or {},
                    )
                )
        if not edges and len(nodes) >= 2:
            edges = list(_edges_for_nodes(nodes))
        object.__setattr__(self, "coverage_group", _clean(self.coverage_group) or "unknown")
        object.__setattr__(self, "relation_nodes", nodes)
        object.__setattr__(self, "optional_nodes", optional)
        object.__setattr__(self, "relation_edges", tuple(edges))
        object.__setattr__(self, "sentence_budget", _safe_int(self.sentence_budget, default=len(nodes) or 0, minimum=0, maximum=5))
        object.__setattr__(self, "required_line_roles", _coerce_required_line_roles(self.required_line_roles))
        object.__setattr__(self, "requested_coverage_group", _clean(self.requested_coverage_group))
        object.__setattr__(self, "source_coverage_plan_meta", _json_safe_mapping(self.source_coverage_plan_meta))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "graph_id", _clean(self.graph_id) or "complete_observation_graph_v2")
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION)

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(node.evidence_span_id for node in self.relation_nodes))

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(node.phrase_unit_id for node in self.relation_nodes))

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(node.relation_type for node in self.relation_nodes))

    @property
    def edge_relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(edge.relation_type for edge in self.relation_edges))

    @property
    def all_relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(list(self.relation_types) + list(self.edge_relation_types)))

    @property
    def canonical_relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(canonical_relation_type(item) for item in self.all_relation_types))

    @property
    def relation_families(self) -> Tuple[str, ...]:
        return tuple(_dedupe(relation_family(item) for item in self.all_relation_types))

    @property
    def role_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(node.role for node in self.relation_nodes))

    @property
    def unmapped_relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item for item in self.all_relation_types if item and relation_definition(item) is None))

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.relation_nodes:
            errors.append("relation_graph_nodes_missing")
        if self.relation_nodes and not self.used_evidence_span_ids:
            errors.append("used_evidence_span_ids_missing")
        if self.relation_nodes and not self.used_phrase_unit_ids:
            errors.append("used_phrase_unit_ids_missing")
        if self.relation_nodes and not self.relation_types:
            errors.append("relation_type_missing")
        for node in self.relation_nodes:
            errors.extend(node.validation_errors)
        for edge in self.relation_edges:
            errors.extend(edge.validation_errors)
        if self.unmapped_relation_types:
            errors.append("relation_type_unmapped")
        return tuple(dict.fromkeys(errors))

    @property
    def ready(self) -> bool:
        return bool(self.relation_nodes) and not self.validation_errors

    @property
    def status(self) -> str:
        return COMPLETE_RELATION_GRAPH_STATUS_READY if self.ready else COMPLETE_RELATION_GRAPH_STATUS_UNAVAILABLE

    @property
    def relation_surface_policies(self) -> Tuple[dict[str, Any], ...]:
        return tuple(relation_surface_policy(relation) for relation in self.all_relation_types)

    def as_relation_binding_seed(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        total = len(self.relation_nodes)
        for rank, node in enumerate(self.relation_nodes, start=1):
            line_role = _line_role_for_rank(rank, total, self.required_line_roles, node.relation_type)
            rows.append(
                {
                    "version": COMPLETE_RELATION_BINDING_SEED_SCHEMA_VERSION,
                    "sentence_id": f"complete_rg_s{rank}",
                    "pending_sentence_id": f"complete_rg_s{rank}",
                    "node_id": node.node_id,
                    "line_role": line_role,
                    "relation_type": node.relation_type,
                    "canonical_relation_type": node.canonical_relation_type,
                    "relation_family": node.relation_family,
                    "used_evidence_span_ids": [node.evidence_span_id] if node.evidence_span_id else [],
                    "used_phrase_unit_ids": [node.phrase_unit_id] if node.phrase_unit_id else [],
                    "focus_rank": node.focus_rank,
                    "must_include": bool(node.must_keep or rank == 1),
                    "relation_pre_generation_constraint": True,
                    "relation_from_observation_graph_v2": True,
                    **_observation_forward_meta(node.meta),
                    "raw_input_included": False,
                }
            )
        return {
            "version": COMPLETE_RELATION_BINDING_SEED_SCHEMA_VERSION,
            "source_step": COMPLETE_RELATION_GRAPH_STAGE,
            "target_step": "Step6_SentencePlan_2_0",
            "binding_stage": "complete_relation_graph_2_0_bridge",
            "graph_id": self.graph_id,
            "coverage_group": self.coverage_group,
            "binding_count": len(rows),
            "sentence_binding_count": len(rows),
            "relation_types": list(self.relation_types),
            "canonical_relation_types": list(self.canonical_relation_types),
            "relation_families": list(self.relation_families),
            **_observation_forward_meta(self.meta),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_rows": rows,
            "bindings": rows,
            "sentence_bindings": rows,
            "relation_type_preserved": bool(rows),
            "relation_pre_generation_constraint": True,
            "response_shape_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
        }

    def as_sentence_plan_seed(self) -> dict[str, Any]:
        return {
            "version": COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION,
            "source_step": COMPLETE_RELATION_GRAPH_STAGE,
            "target_step": "Step6_SentencePlan_2_0",
            "graph_id": self.graph_id,
            "coverage_group": self.coverage_group,
            "sentence_budget": self.sentence_budget,
            "required_line_roles": list(self.required_line_roles),
            "graph_nodes": [node.as_sentence_plan_focus() for node in self.relation_nodes],
            "optional_graph_nodes": [node.as_sentence_plan_focus() for node in self.optional_nodes],
            "relation_edges": [edge.as_meta() for edge in self.relation_edges],
            "relation_binding_seed": self.as_relation_binding_seed(),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "canonical_relation_types": list(self.canonical_relation_types),
            "relation_families": list(self.relation_families),
            **_observation_forward_meta(self.meta),
            "relation_surface_policies": list(self.relation_surface_policies),
            "relation_type_pre_generation_constraint": True,
            "summarize_all_materials": False,
            "response_shape_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
        }

    def as_meta(self) -> dict[str, Any]:
        taxonomy_meta = build_limited_relation_taxonomy_meta(
            coverage_scope=self.coverage_group,
            sentence_bindings=self.as_relation_binding_seed().get("sentence_bindings") or (),
            relation_types=self.all_relation_types,
        )
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "target_step": COMPLETE_RELATION_GRAPH_STAGE,
            "step": COMPLETE_RELATION_GRAPH_STAGE,
            "implementation_unit": COMPLETE_RELATION_GRAPH_IMPLEMENTATION_UNIT,
            "stage": COMPLETE_COMPOSER_STAGE,
            "source": "complete_relation_graph_service",
            "status": self.status,
            "ready": self.ready,
            "graph_id": self.graph_id,
            "relation_graph_bridge_added": True,
            "observation_graph_2_0_bridge_added": True,
            "existing_relation_taxonomy_bridged": True,
            "relation_taxonomy_source_version": taxonomy_meta.get("version"),
            "relation_type_pre_generation_constraint": True,
            "relation_type_preserved_in_meta": True,
            "relation_type_preserved_in_sentence_binding_seed": True,
            "sentence_plan_pre_stage": True,
            "surface_realizer_pre_stage": True,
            "coverage_group": self.coverage_group,
            "requested_coverage_group": self.requested_coverage_group,
            "sentence_budget": self.sentence_budget,
            "required_line_roles": list(self.required_line_roles),
            "graph_node_count": len(self.relation_nodes),
            "optional_node_count": len(self.optional_nodes),
            "relation_edge_count": len(self.relation_edges),
            "relation_types": list(self.relation_types),
            "edge_relation_types": list(self.edge_relation_types),
            "all_relation_types": list(self.all_relation_types),
            "canonical_relation_types": list(self.canonical_relation_types),
            "relation_families": list(self.relation_families),
            "unmapped_relation_types": list(self.unmapped_relation_types),
            "all_relation_types_mapped": not bool(self.unmapped_relation_types),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "role_types": list(self.role_types),
            **_observation_forward_meta(self.meta),
            "graph_nodes": [node.as_meta() for node in self.relation_nodes],
            "optional_graph_nodes": [node.as_meta() for node in self.optional_nodes],
            "relation_edges": [edge.as_meta() for edge in self.relation_edges],
            "relation_surface_policies": list(self.relation_surface_policies),
            "relation_binding_seed": self.as_relation_binding_seed(),
            "sentence_plan_seed": self.as_sentence_plan_seed(),
            "limited_relation_taxonomy_bridge": taxonomy_meta,
            "allowed_relation_types": list(allowed_relation_types()),
            "required_major_relation_types": ["contrast", "coexistence", "pressure", "recovery", "approach_avoidance", "residue"],
            "relation_not_expressed_traceable": True,
            "relation_after_text_generation": False,
            "comment_text_generated": False,
            "comment_text_contract": "passed_only",
            "completion_sentence_templates_added": False,
            "fixed_sentence_template_added": False,
            "fixed_sentence_template_allowed": False,
            "input_specific_template_added": False,
            "external_ai_used": False,
            "external_ai_allowed": False,
            "local_llm_used": False,
            "local_llm_allowed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_improvement": False,
            "validation_errors": list(self.validation_errors),
            "source_coverage_plan_summary": {
                "version": self.source_coverage_plan_meta.get("version"),
                "source_step": self.source_coverage_plan_meta.get("target_step") or self.source_coverage_plan_meta.get("source_step"),
                "coverage_group": self.source_coverage_plan_meta.get("coverage_group") or self.coverage_group,
                "selected_focus_count": self.source_coverage_plan_meta.get("selected_focus_count"),
                "optional_focus_count": self.source_coverage_plan_meta.get("optional_focus_count"),
                "raw_input_included": False,
            },
            "contract_boundary": {
                "comment_text_contract": "passed_only",
                "db_physical_name_changed": False,
                "api_route_changed": False,
                "public_response_key_change": False,
                "rn_visible_title_changed": False,
                "response_shape_changed": False,
            },
            "source_policy": {
                "external_ai_allowed": False,
                "local_llm_allowed": False,
                "fixed_sentence_template_allowed": False,
            },
            "meta": dict(self.meta),
        }


def build_complete_relation_graph_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta()
    return {
        "version": COMPLETE_RELATION_GRAPH_SERVICE_VERSION,
        "target_step": COMPLETE_RELATION_GRAPH_STAGE,
        "step": COMPLETE_RELATION_GRAPH_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_RELATION_GRAPH_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta.get("target_composer_term"),
        "target_composer_family_term": term_meta.get("target_composer_family_term"),
        "complete_composer_initial_term": term_meta.get("complete_composer_initial_term"),
        "relation_graph_bridge_added": True,
        "observation_graph_2_0_bridge_added": True,
        "observation_material_connector_supported": True,
        "observation_reply_kind_preserved_in_relation_meta": True,
        "internal_question_ids_preserved_in_relation_meta": True,
        "eligible_deep_relation_allowed": True,
        "low_information_relation_confidence_limited": True,
        "existing_relation_taxonomy_bridged": True,
        "accepts_complete_focus_selector_output": True,
        "accepts_complete_material_service_output": True,
        "sentence_plan_pre_stage": True,
        "relation_type_pre_generation_constraint": True,
        "relation_type_preserved_in_meta": True,
        "relation_type_preserved_in_sentence_binding_seed": True,
        "allowed_relation_types": list(allowed_relation_types()),
        "required_major_relation_types": ["contrast", "coexistence", "pressure", "recovery", "approach_avoidance", "residue"],
        "relation_after_text_generation": False,
        "comment_text_generated": False,
        "comment_text_contract": "passed_only",
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_allowed": False,
        "completion_sentence_templates_added": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
    }


def _coverage_plan_rows(plan: Any) -> tuple[list[Any], list[Any], str, int, Tuple[str, ...], dict[str, Any], str]:
    if isinstance(plan, CompleteCoveragePlan):
        return (
            list(plan.focus_items),
            list(plan.optional_items),
            plan.coverage_group,
            plan.sentence_budget,
            tuple(plan.required_line_roles),
            plan.as_meta(),
            plan.requested_coverage_group,
        )
    if isinstance(plan, Mapping):
        rows = plan.get("focus_items") or plan.get("focus_rows") or plan.get("graph_nodes") or plan.get("materials") or ()
        optional = plan.get("optional_focus_items") or plan.get("optional_rows") or plan.get("optional_graph_nodes") or ()
        group = _clean(plan.get("coverage_group") or plan.get("coverage_scope") or "")
        budget = _safe_int(plan.get("sentence_budget"), default=len(tuple(rows or ())) or 0, minimum=0, maximum=5)
        required = _coerce_required_line_roles(plan.get("required_line_roles") or ())
        return (list(rows or ()), list(optional or ()), group, budget, required, _json_safe_mapping(plan), _clean(plan.get("requested_coverage_group")))
    return ([], [], "", 0, tuple(), {}, "")


def _build_nodes_from_rows(rows: Sequence[Any], *, start_index: int = 1) -> Tuple[CompleteRelationGraphNode, ...]:
    nodes: list[CompleteRelationGraphNode] = []
    for offset, row in enumerate(rows, start=start_index):
        node = _coerce_node(row, index=offset)
        if node is not None:
            if not node.node_id or node.node_id == f"rg_node_{offset}":
                node = CompleteRelationGraphNode(
                    node_id=f"rg_node_{offset}",
                    material_id=node.material_id,
                    phrase_unit_id=node.phrase_unit_id,
                    evidence_span_id=node.evidence_span_id,
                    role=node.role,
                    relation_type=node.relation_type,
                    focus_rank=node.focus_rank,
                    focus_role=node.focus_role,
                    polarity=node.polarity,
                    must_keep=node.must_keep,
                    line_role_hint=node.line_role_hint,
                    source_anchor_present=node.source_anchor_present,
                    selection_reasons=node.selection_reasons,
                    source=node.source,
                    meta=node.meta,
                )
            nodes.append(node)
    return tuple(nodes)


def build_complete_relation_graph(
    *,
    coverage_plan: CompleteCoveragePlan | Mapping[str, Any] | None = None,
    relation_graph_input: CompleteCoveragePlan | Mapping[str, Any] | None = None,
    material_bundle: Any = None,
    focus_selector_input: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    coverage_group: str = "",
    meta: Mapping[str, Any] | None = None,
) -> CompleteObservationGraphV2:
    """Build ObservationGraph 2.0 bridge from FocusSelector/CoveragePlan output."""

    plan: Any = coverage_plan if coverage_plan is not None else relation_graph_input
    if plan is None:
        plan = build_complete_coverage_plan(
            material_bundle=material_bundle,
            focus_selector_input=focus_selector_input,
            evidence_spans=evidence_spans,
            phrase_units=phrase_units,
            coverage_group=coverage_group,
        )
    rows, optional_rows, group, budget, required_roles, source_meta, requested_group = _coverage_plan_rows(plan)
    connector_meta = _observation_forward_meta(source_meta)
    if not connector_meta:
        for row in list(rows) + list(optional_rows):
            if isinstance(row, Mapping):
                connector_meta.update(_row_observation_meta(row))
            else:
                connector_meta.update(_observation_forward_meta(getattr(row, "meta", None)))
    nodes = _build_nodes_from_rows(rows, start_index=1)
    optional_nodes = _build_nodes_from_rows(optional_rows, start_index=len(nodes) + 1)
    edges = _edges_for_nodes(nodes)
    return CompleteObservationGraphV2(
        coverage_group=group or coverage_group or "unknown",
        relation_nodes=nodes,
        optional_nodes=optional_nodes,
        relation_edges=edges,
        sentence_budget=budget or len(nodes),
        required_line_roles=required_roles or ("opening", "core", "relation"),
        requested_coverage_group=requested_group or coverage_group,
        source_coverage_plan_meta=source_meta,
        meta={**build_complete_relation_graph_contract_meta(), **_json_safe_mapping(meta), **connector_meta},
    )


def build_complete_observation_graph_v2(**kwargs: Any) -> CompleteObservationGraphV2:
    return build_complete_relation_graph(**kwargs)


def bridge_complete_relation_graph(**kwargs: Any) -> CompleteObservationGraphV2:
    return build_complete_relation_graph(**kwargs)


def build_complete_relation_graph_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_relation_graph(**kwargs).as_meta()


def build_complete_observation_graph_v2_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_relation_graph(**kwargs).as_meta()


def complete_relation_graph_nodes(graph: CompleteObservationGraphV2 | None) -> Tuple[CompleteRelationGraphNode, ...]:
    if isinstance(graph, CompleteObservationGraphV2):
        return tuple(graph.relation_nodes)
    return tuple()


CompleteRelationGraph = CompleteObservationGraphV2
CompleteRelationGraphV2 = CompleteObservationGraphV2
ObservationGraphV2 = CompleteObservationGraphV2
CompleteRelationNode = CompleteRelationGraphNode
CompleteRelationEdge = CompleteRelationGraphEdge

__all__ = [
    "COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION",
    "COMPLETE_RELATION_GRAPH_SCHEMA_VERSION",
    "COMPLETE_RELATION_BINDING_SEED_SCHEMA_VERSION",
    "COMPLETE_RELATION_GRAPH_EDGE_SCHEMA_VERSION",
    "COMPLETE_RELATION_GRAPH_IMPLEMENTATION_UNIT",
    "COMPLETE_RELATION_GRAPH_NODE_SCHEMA_VERSION",
    "COMPLETE_RELATION_GRAPH_SERVICE_VERSION",
    "COMPLETE_RELATION_GRAPH_STAGE",
    "COMPLETE_RELATION_GRAPH_STATUS_READY",
    "COMPLETE_RELATION_GRAPH_STATUS_UNAVAILABLE",
    "COMPLETE_RELATION_GRAPH_STEP",
    "COMPLETE_RELATION_GRAPH_TARGET_STEP",
    "CompleteObservationGraphV2",
    "CompleteRelationGraph",
    "CompleteRelationGraphEdge",
    "CompleteRelationEdge",
    "CompleteRelationGraphNode",
    "CompleteRelationNode",
    "CompleteRelationGraphV2",
    "ObservationGraphV2",
    "RELATION_SURFACE_POLICIES",
    "bridge_complete_relation_graph",
    "build_complete_observation_graph_v2",
    "build_complete_observation_graph_v2_meta",
    "build_complete_relation_graph",
    "build_complete_relation_graph_contract_meta",
    "build_complete_relation_graph_meta",
    "complete_relation_graph_nodes",
    "relation_surface_policy",
]
