# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 6 SentencePlan 2.0 for EmlisAI Complete Composer initial version.

This additive internal planner consumes Step 5 ObservationGraph 2.0 output and
creates a binding-first ``CompleteSentencePlanV2``.  It decides sentence count,
line order, must/optional roles, relation expression requirements, and closing
policy before Surface Realizer 2.0 runs.

It does not generate user-facing ``comment_text`` and does not change DB
physical names, API routes, public response keys, or RN display contracts.
"""

from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_STAGE,
    COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION,
    COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION,
    CompleteSentencePlanLine,
    CompleteSentencePlanV2,
)
from emlis_ai_complete_relation_graph_service import (
    CompleteObservationGraphV2,
    build_complete_relation_graph,
    relation_surface_policy,
)
from emlis_ai_observation_sentence_plan_roles import (
    OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
    annotate_observation_sentence_plan_lines,
    build_observation_sentence_plan_roles_contract_meta,
    build_observation_sentence_plan_roles_meta,
)
from emlis_ai_limited_relation_taxonomy import (
    canonical_relation_type,
    normalize_relation_type,
    relation_definition,
    relation_family,
)

COMPLETE_SENTENCE_PLANNER_VERSION = "emlis.complete_sentence_planner.v1"
COMPLETE_SENTENCE_PLANNER_SERVICE_VERSION = COMPLETE_SENTENCE_PLANNER_VERSION
COMPLETE_SENTENCE_PLAN_SERVICE_VERSION = COMPLETE_SENTENCE_PLANNER_VERSION
COMPLETE_SENTENCE_PLAN_BUILD_META_VERSION = "emlis.complete_sentence_plan_2_0.build_meta.v1"
COMPLETE_SENTENCE_PLAN_STAGE = "Step6_SentencePlan_2_0"
COMPLETE_SENTENCE_PLAN_V2_STAGE = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLANNER_STAGE = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLAN_STEP = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLAN_V2_STEP = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLANNER_STEP = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLAN_TARGET_STEP = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLAN_V2_TARGET_STEP = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLANNER_TARGET_STEP = COMPLETE_SENTENCE_PLAN_STAGE
COMPLETE_SENTENCE_PLAN_IMPLEMENTATION_UNIT = "Commit 6"
COMPLETE_SENTENCE_PLANNER_IMPLEMENTATION_UNIT = COMPLETE_SENTENCE_PLAN_IMPLEMENTATION_UNIT

COMPLETE_SENTENCE_PLAN_STATUS_READY = "ready"
COMPLETE_SENTENCE_PLAN_STATUS_UNAVAILABLE = "unavailable"

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

MAJOR_RELATION_LINE_TYPES = {
    "contrast",
    "coexistence",
    "pressure",
    "approach_avoidance",
    "recovery",
    "residue",
    "tension",
    "distance",
    "limit",
}

COVERAGE_SENTENCE_BUDGETS: dict[str, tuple[int, int, int]] = {
    "short_daily": (2, 2, 2),
    "long_meaning_arc": (3, 4, 3),
    "conflict": (3, 3, 3),
    "recovery": (2, 3, 3),
    "pressure": (2, 4, 3),
    "desire_fear": (2, 4, 3),
    "relationship": (3, 3, 3),
    "history_cross_core": (2, 3, 2),
}

COVERAGE_ALIASES = {
    "short": "short_daily",
    "daily": "short_daily",
    "short_daily_input": "short_daily",
    "long": "long_meaning_arc",
    "long_arc": "long_meaning_arc",
    "long_input": "long_meaning_arc",
    "meaning_arc": "long_meaning_arc",
    "desire_fear": "desire_fear",
    "desire-fear": "desire_fear",
    "desire_and_fear": "desire_fear",
    "wish_fear": "desire_fear",
    "approach_avoidance": "desire_fear",
    "positive_progress_recovery": "recovery",
    "positive_progress": "recovery",
    "energy_recovery": "recovery",
    "energy_fatigue_pressure": "pressure",
    "anxiety_anticipation_loop": "pressure",
    "fatigue_pressure": "pressure",
    "relationship_approach_avoidance": "relationship",
    "current_input_core": "short_daily",
}

LINE_ROLE_DEFAULT_FORBIDDEN_KEYS: dict[str, tuple[str, ...]] = {
    "opening": (
        "general_advice",
        "fixed_sentence_template",
        "overinterpretation",
        "diagnosis_claim",
    ),
    "core": (
        "unsupported_sentence",
        "overclaim",
        "diagnosis_claim",
        "personality_claim",
        "fixed_sentence_template",
    ),
    "relation": (
        "relation_not_expressed",
        "single_true_feeling_claim",
        "choose_one_side",
        "action_instruction",
        "fixed_sentence_template",
    ),
    "closing": (
        "action_instruction",
        "diagnosis_claim",
        "over_comfort",
        "command_surface",
        "fixed_sentence_template",
    ),
}

LINE_ROLE_REPAIR_POLICIES: dict[str, tuple[str, ...]] = {
    "opening": (
        "keep_primary_phrase",
        "avoid_generalization",
        "do_not_remove_must_include",
    ),
    "core": (
        "keep_must_include",
        "rebind_to_source_bound_material",
        "do_not_remove_must_include",
    ),
    "relation": (
        "relation_not_expressed",
        "make_relation_line_explicit",
        "connector_rewrite_only",
        "do_not_remove_must_include",
    ),
    "closing": (
        "trim_optional_only",
        "shorten_closing_without_new_meaning",
        "no_action_instruction",
    ),
}

LINE_ROLE_SURFACE_INTENTS: dict[str, str] = {
    "opening": "receive_input_atmosphere_without_generalization",
    "core": "observe_primary_source_bound_material",
    "relation": "express_pre_generation_relation_constraint",
    "closing": "close_with_emlis_distance_without_instruction",
}

LINE_ROLE_MAX_CHARS: dict[str, int] = {
    "opening": 96,
    "core": 124,
    "relation": 120,
    "closing": 88,
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
        "relation_pre_generation_constraint",
        "meta",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def _safe_int(value: Any, *, default: int = 0, minimum: int = 0, maximum: int = 999) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _normalize_coverage_group(value: Any) -> str:
    group = _clean(value)
    if not group:
        return ""
    group = group.lower().replace("-", "_").replace(" ", "_")
    return COVERAGE_ALIASES.get(group, group)


def _coverage_budget(coverage_group: str, requested_budget: Any = 0, *, relation_count: int = 0, node_count: int = 0) -> int:
    group = _normalize_coverage_group(coverage_group) or "short_daily"
    minimum, maximum, default = COVERAGE_SENTENCE_BUDGETS.get(group, (2, 5, 3))
    requested = _safe_int(requested_budget, default=0, minimum=0, maximum=5)
    if requested:
        wanted = requested
    elif group == "long_meaning_arc":
        wanted = 4 if node_count >= 4 or relation_count >= 3 else 3
    elif group == "pressure":
        wanted = 4 if node_count >= 3 and relation_count >= 2 else default
    elif group == "recovery":
        wanted = 3 if node_count >= 2 else 2
    elif group == "desire_fear":
        wanted = 3 if relation_count >= 1 or node_count >= 2 else default
    else:
        wanted = default
    return max(2, min(maximum, max(minimum, wanted)))


def _relation_known(relation_type: str) -> bool:
    return bool(relation_type and relation_definition(relation_type) is not None)


def _row_relation(row: Mapping[str, Any]) -> str:
    role = _clean(row.get("role"))
    relation = _clean(row.get("relation_type") or row.get("canonical_relation_type"))
    return normalize_relation_type(relation, roles=(role,) if role else (), line_role=row.get("line_role_hint") or role)


@dataclass(frozen=True)
class CompleteSentencePlanRejection:
    reason_codes: Iterable[str]
    node_id: str = ""
    material_id: str = ""
    phrase_unit_id: str = ""
    evidence_span_id: str = ""
    role: str = ""
    relation_type: str = ""
    source: str = "sentence_planner"
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = "emlis.complete_sentence_plan_rejection.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(_dedupe(self.reason_codes)))
        object.__setattr__(self, "node_id", _clean(self.node_id))
        object.__setattr__(self, "material_id", _clean(self.material_id))
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "role", _clean(self.role))
        object.__setattr__(self, "relation_type", normalize_relation_type(self.relation_type) if self.relation_type else "")
        object.__setattr__(self, "source", _clean(self.source) or "sentence_planner")
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or "emlis.complete_sentence_plan_rejection.v1")

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "target_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "node_id": self.node_id,
            "material_id": self.material_id,
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "role": self.role,
            "relation_type": self.relation_type,
            "source": self.source,
            "reason_codes": list(self.reason_codes),
            "rejection_reasons": list(self.reason_codes),
            "raw_text_included": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class _PlanNode:
    node_id: str
    material_id: str
    phrase_unit_id: str
    evidence_span_id: str
    role: str
    relation_type: str
    focus_rank: int
    focus_role: str = "support"
    polarity: str = "neutral"
    must_keep: bool = False
    line_role_hint: str = ""
    source_anchor_present: bool = False
    relation_pre_generation_constraint: bool = True
    selection_reasons: Tuple[str, ...] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    @property
    def canonical_relation_type(self) -> str:
        return canonical_relation_type(self.relation_type)

    @property
    def relation_family(self) -> str:
        return relation_family(self.relation_type)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.node_id:
            errors.append("node_id_missing")
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
        if self.relation_type and not _relation_known(self.relation_type):
            errors.append("relation_type_unmapped")
        if not self.source_anchor_present:
            errors.append("source_anchor_missing")
        if not self.relation_pre_generation_constraint:
            errors.append("relation_pre_generation_constraint_missing")
        return tuple(dict.fromkeys(errors))

    def as_meta(self) -> dict[str, Any]:
        return {
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
            "source_anchor_present": self.source_anchor_present,
            "relation_pre_generation_constraint": self.relation_pre_generation_constraint,
            "selection_reasons": list(self.selection_reasons),
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


def _coerce_plan_node(value: Any, *, index: int) -> tuple[_PlanNode | None, CompleteSentencePlanRejection | None]:
    row = _as_mapping(value)
    if not row:
        return None, CompleteSentencePlanRejection(reason_codes=("sentence_plan_seed_row_empty",), source="sentence_planner")
    node_id = _clean(row.get("node_id") or f"sp_node_{index}")
    material_id = _clean(row.get("material_id") or node_id)
    phrase_unit_id = _clean(row.get("phrase_unit_id") or material_id)
    evidence_span_id = _clean(row.get("evidence_span_id"))
    role = _clean(row.get("role"))
    relation = _row_relation(row)
    node = _PlanNode(
        node_id=node_id,
        material_id=material_id,
        phrase_unit_id=phrase_unit_id,
        evidence_span_id=evidence_span_id,
        role=role,
        relation_type=relation,
        focus_rank=_safe_int(row.get("focus_rank"), default=index, minimum=1, maximum=999),
        focus_role=_clean(row.get("focus_role")) or ("primary" if index == 1 else "support"),
        polarity=_clean(row.get("polarity")) or "neutral",
        must_keep=bool(row.get("must_keep")) or index == 1,
        line_role_hint=_clean(row.get("line_role_hint") or row.get("line_role")),
        source_anchor_present=bool(row.get("source_anchor_present") or evidence_span_id),
        relation_pre_generation_constraint=bool(row.get("relation_pre_generation_constraint", True)),
        selection_reasons=tuple(_dedupe(row.get("selection_reasons") or ())),
        meta=_json_safe_mapping(row.get("meta") or {}),
    )
    if node.validation_errors:
        return None, CompleteSentencePlanRejection(
            reason_codes=node.validation_errors,
            node_id=node.node_id,
            material_id=node.material_id,
            phrase_unit_id=node.phrase_unit_id,
            evidence_span_id=node.evidence_span_id,
            role=node.role,
            relation_type=node.relation_type,
            source="sentence_planner",
        )
    return node, None


def _graph_seed_from_input(
    *,
    observation_graph: CompleteObservationGraphV2 | Mapping[str, Any] | None = None,
    relation_graph: CompleteObservationGraphV2 | Mapping[str, Any] | None = None,
    sentence_plan_seed: Mapping[str, Any] | None = None,
    coverage_plan: Any = None,
    material_bundle: Any = None,
    focus_selector_input: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    coverage_group: str = "",
) -> tuple[dict[str, Any], dict[str, Any], CompleteObservationGraphV2 | None]:
    graph_input = observation_graph if observation_graph is not None else relation_graph
    if sentence_plan_seed is not None:
        return _json_safe_mapping(sentence_plan_seed), _json_safe_mapping(sentence_plan_seed), None
    if isinstance(graph_input, CompleteObservationGraphV2):
        return graph_input.as_sentence_plan_seed(), graph_input.as_meta(), graph_input
    if isinstance(graph_input, Mapping):
        seed = _json_safe_mapping(graph_input)
        if "graph_nodes" not in seed and "relation_nodes" in graph_input:
            seed["graph_nodes"] = [_json_safe_mapping(_as_mapping(item)) for item in graph_input.get("relation_nodes") or ()]
        if "optional_graph_nodes" not in seed and "optional_nodes" in graph_input:
            seed["optional_graph_nodes"] = [_json_safe_mapping(_as_mapping(item)) for item in graph_input.get("optional_nodes") or ()]
        return seed, seed, None
    graph = build_complete_relation_graph(
        coverage_plan=coverage_plan,
        material_bundle=material_bundle,
        focus_selector_input=focus_selector_input,
        evidence_spans=evidence_spans,
        phrase_units=phrase_units,
        coverage_group=coverage_group,
    )
    return graph.as_sentence_plan_seed(), graph.as_meta(), graph


def _nodes_from_seed(seed: Mapping[str, Any]) -> tuple[list[_PlanNode], list[_PlanNode], list[CompleteSentencePlanRejection]]:
    raw_nodes = (
        seed.get("graph_nodes")
        or seed.get("focus_items")
        or seed.get("relation_rows")
        or seed.get("sentence_bindings")
        or seed.get("bindings")
        or seed.get("materials")
        or ()
    )
    raw_optional = seed.get("optional_graph_nodes") or seed.get("optional_focus_items") or seed.get("optional_rows") or ()
    nodes: list[_PlanNode] = []
    optional: list[_PlanNode] = []
    rejected: list[CompleteSentencePlanRejection] = []
    for index, row in enumerate(list(raw_nodes or ()), start=1):
        node, rejection = _coerce_plan_node(row, index=index)
        if node is not None:
            nodes.append(node)
        if rejection is not None:
            rejected.append(rejection)
    for index, row in enumerate(list(raw_optional or ()), start=len(nodes) + 1):
        node, rejection = _coerce_plan_node(row, index=index)
        if node is not None:
            optional.append(node)
        if rejection is not None:
            rejected.append(rejection)
    return nodes, optional, rejected


def _needs_relation_line(coverage_group: str, nodes: Sequence[_PlanNode], required_line_roles: Sequence[str]) -> bool:
    group = _normalize_coverage_group(coverage_group)
    relation_types = set(_dedupe(node.relation_type for node in nodes))
    if "relation" in set(required_line_roles) and relation_types.intersection(MAJOR_RELATION_LINE_TYPES):
        return group != "short_daily" or len(relation_types) >= 2
    if group in {"conflict", "relationship"}:
        return True
    if group in {"long_meaning_arc", "pressure", "recovery"} and len(relation_types) >= 2:
        return True
    return bool(len(relation_types) >= 3)


def _pick_primary(nodes: Sequence[_PlanNode]) -> _PlanNode | None:
    if not nodes:
        return None
    ranked = sorted(
        nodes,
        key=lambda node: (
            1 if node.focus_role == "primary" else 0,
            1 if node.must_keep else 0,
            -node.focus_rank,
        ),
        reverse=True,
    )
    return ranked[0]


def _pick_next(nodes: Sequence[_PlanNode], used_node_ids: set[str], *, prefer_relation: bool = False) -> _PlanNode | None:
    candidates = [node for node in nodes if node.node_id not in used_node_ids]
    if not candidates:
        candidates = list(nodes)
    if not candidates:
        return None
    if prefer_relation:
        relation_candidates = [node for node in candidates if node.relation_type in MAJOR_RELATION_LINE_TYPES]
        if relation_candidates:
            candidates = relation_candidates
    return sorted(candidates, key=lambda node: (1 if node.must_keep else 0, -node.focus_rank), reverse=True)[0]


def _merge_node_ids(nodes: Iterable[_PlanNode], attr: str) -> Tuple[str, ...]:
    return tuple(_dedupe(getattr(node, attr, "") for node in nodes))


def _relation_line_nodes(nodes: Sequence[_PlanNode], primary: _PlanNode | None, core: _PlanNode | None) -> Tuple[_PlanNode, ...]:
    selected: list[_PlanNode] = []

    def add(node: _PlanNode | None) -> None:
        if node is not None and node not in selected:
            selected.append(node)

    # Step7 anti-template: when a relation line is needed, make the relation
    # line actually bind to the major relation material first.  The old order
    # could turn a relation line into another center/core sentence, which then
    # encouraged the repeated "同じ時間の中" style backbone downstream.
    relation_nodes = [node for node in nodes if node.relation_type in MAJOR_RELATION_LINE_TYPES]
    for node in relation_nodes[:2]:
        add(node)
    if selected:
        add(primary)
        add(core)
    else:
        add(primary)
        add(core)
        for node in nodes:
            if node.relation_type in MAJOR_RELATION_LINE_TYPES:
                add(node)
            if len(selected) >= 2:
                break
    if not selected and nodes:
        add(nodes[0])
    return tuple(selected[:3])


def _line_relation(nodes: Sequence[_PlanNode], fallback: str = "center") -> str:
    relations = tuple(_dedupe(node.relation_type for node in nodes))
    if "approach_avoidance" in relations:
        return "approach_avoidance"
    if "contrast" in relations:
        return "contrast"
    if "coexistence" in relations:
        return "coexistence"
    if "pressure" in relations and "recovery" in relations:
        return "recovery"
    return relations[0] if relations else fallback


def _line_policy(line_role: str, relation_type: str) -> tuple[tuple[str, ...], str, tuple[str, ...]]:
    forbidden = list(LINE_ROLE_DEFAULT_FORBIDDEN_KEYS.get(line_role, ()))
    surface_intent = LINE_ROLE_SURFACE_INTENTS.get(line_role, f"{line_role}_observation")
    if relation_type:
        policy = relation_surface_policy(relation_type)
        forbidden.extend(policy.get("forbidden_surface_keys") or ())
        if line_role == "relation":
            surface_intent = _clean(policy.get("surface_intent")) or surface_intent
    repair = LINE_ROLE_REPAIR_POLICIES.get(line_role, ("keep_must_include",))
    return tuple(_dedupe(forbidden)), surface_intent, tuple(_dedupe(repair))


def _plan_line(
    *,
    plan_id: str,
    index: int,
    line_role: str,
    nodes: Sequence[_PlanNode],
    coverage_group: str,
    must_include_roles: Iterable[str],
    optional_roles: Iterable[str] = (),
    extra_forbidden: Iterable[str] = (),
    extra_repair: Iterable[str] = (),
) -> CompleteSentencePlanLine:
    relation = _line_relation(nodes)
    forbidden, surface_intent, repair_policy = _line_policy(line_role, relation)
    if line_role == "closing":
        # Closing is optional, but it still remains source-bound.  It may be
        # trimmed by repair; it may not introduce action advice or diagnosis.
        optional_roles = tuple(_dedupe(list(optional_roles) + ["closing", "distance_policy"]))
    evidence_ids = _merge_node_ids(nodes, "evidence_span_id")
    phrase_ids = _merge_node_ids(nodes, "phrase_unit_id")
    roles = tuple(_dedupe(must_include_roles))
    relation_policy = relation_surface_policy(relation)
    return CompleteSentencePlanLine(
        sentence_id=f"{plan_id}_s{index}",
        line_role=line_role,
        relation_type=relation,
        focus_rank=index,
        phrase_unit_ids=phrase_ids,
        evidence_span_ids=evidence_ids,
        must_include_roles=roles,
        optional_roles=tuple(_dedupe(optional_roles)),
        forbidden_surface_keys=tuple(_dedupe(list(forbidden) + list(extra_forbidden))),
        max_chars=LINE_ROLE_MAX_CHARS.get(line_role, 112),
        surface_intent=surface_intent,
        repair_policy=tuple(_dedupe(list(repair_policy) + list(extra_repair))),
        meta={
            "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "coverage_group": coverage_group,
            "node_ids": [node.node_id for node in nodes],
            "material_ids": [node.material_id for node in nodes],
            "relation_family": relation_family(relation),
            "canonical_relation_type": canonical_relation_type(relation),
            "relation_surface_policy": relation_policy,
            "must_include_repair_protected": line_role != "closing",
            "optional_line": line_role == "closing",
            "surface_realizer_must_follow_plan": True,
            "raw_input_included": False,
        },
    )


def _build_lines(*, plan_id: str, coverage_group: str, budget: int, nodes: Sequence[_PlanNode], required_line_roles: Sequence[str]) -> tuple[CompleteSentencePlanLine, ...]:
    if not nodes:
        return tuple()
    ordered_nodes = sorted(nodes, key=lambda node: node.focus_rank)
    primary = _pick_primary(ordered_nodes) or ordered_nodes[0]
    used_ids = {primary.node_id}
    core = _pick_next(ordered_nodes, used_ids) or primary
    used_ids.add(core.node_id)
    needs_relation = _needs_relation_line(coverage_group, ordered_nodes, required_line_roles)

    lines: list[CompleteSentencePlanLine] = []
    lines.append(
        _plan_line(
            plan_id=plan_id,
            index=1,
            line_role="opening",
            nodes=(primary,),
            coverage_group=coverage_group,
            must_include_roles=(primary.role, "primary_phrase"),
            extra_forbidden=("full_summary",) if coverage_group == "long_meaning_arc" else (),
            extra_repair=("short_input_overinterpretation_guard",) if coverage_group == "short_daily" else (),
        )
    )
    if budget <= 1:
        return tuple(lines)

    lines.append(
        _plan_line(
            plan_id=plan_id,
            index=2,
            line_role="core",
            nodes=(core,),
            coverage_group=coverage_group,
            must_include_roles=(core.role, "evidence_ids", "phrase_unit_ids", "relation_type"),
            extra_repair=("do_not_remove_must_include",),
        )
    )

    if len(lines) >= budget:
        return tuple(lines[:budget])

    if needs_relation and len(lines) < budget:
        relation_nodes = _relation_line_nodes(ordered_nodes, primary, core)
        lines.append(
            _plan_line(
                plan_id=plan_id,
                index=len(lines) + 1,
                line_role="relation",
                nodes=relation_nodes,
                coverage_group=coverage_group,
                must_include_roles=("relation_ids", "relation_type") + tuple(_dedupe(node.role for node in relation_nodes)),
                extra_forbidden=("relation_after_text_generation", "invented_relation"),
                extra_repair=("relation_not_expressed",),
            )
        )

    if len(lines) < budget and ("closing" in set(required_line_roles) or coverage_group in {"long_meaning_arc", "pressure", "desire_fear", "relationship", "recovery", "history_cross_core"}):
        closing_node = _pick_next(ordered_nodes, {line.meta.get("node_ids", [""])[0] for line in lines if line.meta.get("node_ids")}) or primary
        lines.append(
            _plan_line(
                plan_id=plan_id,
                index=len(lines) + 1,
                line_role="closing",
                nodes=(closing_node,),
                coverage_group=coverage_group,
                must_include_roles=(closing_node.role,),
                optional_roles=("closing", "distance_policy"),
                extra_forbidden=("action_instruction", "diagnosis_claim", "over_comfort"),
                extra_repair=("trim_optional_only",),
            )
        )

    # Fill remaining budget with source-bound core lines if the plan has room.
    while len(lines) < budget:
        next_node = _pick_next(ordered_nodes, {node_id for line in lines for node_id in line.meta.get("node_ids", [])})
        if next_node is None:
            break
        lines.append(
            _plan_line(
                plan_id=plan_id,
                index=len(lines) + 1,
                line_role="core",
                nodes=(next_node,),
                coverage_group=coverage_group,
                must_include_roles=(next_node.role, "evidence_ids", "phrase_unit_ids", "relation_type"),
                optional_roles=("supporting_core",),
                extra_repair=("trim_optional_only",) if not next_node.must_keep else ("do_not_remove_must_include",),
            )
        )
        if len({line.sentence_id for line in lines}) != len(lines):
            break
    return tuple(lines[:budget])


def build_complete_sentence_planner_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta()
    return {
        "version": COMPLETE_SENTENCE_PLANNER_VERSION,
        "target_step": COMPLETE_SENTENCE_PLAN_STAGE,
        "step": COMPLETE_SENTENCE_PLAN_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_SENTENCE_PLAN_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta.get("target_composer_term"),
        "target_composer_family_term": term_meta.get("target_composer_family_term"),
        "complete_composer_initial_term": term_meta.get("complete_composer_initial_term"),
        "sentence_plan_2_0_added": True,
        "sentence_plan_v2_added": True,
        "sentence_planner_added": True,
        "accepts_relation_graph_2_0_output": True,
        "accepts_complete_relation_graph_output": True,
        "accepts_focus_selector_output": True,
        "accepts_complete_focus_selector_output": True,
        "accepts_material_service_output": True,
        "accepts_complete_material_service_output": True,
        "surface_realizer_pre_stage": True,
        "surface_realizer_must_follow_plan": True,
        "sentence_budget_range": "2..5",
        "short_daily_budget": 2,
        "short_daily_max_sentence_budget": 2,
        "long_meaning_arc_budget": "3..4",
        "long_meaning_arc_min_sentence_budget": 3,
        "conflict_budget": 3,
        "recovery_budget": "2..3",
        "pressure_budget": "2..4",
        "desire_fear_budget": "2..4",
        "relationship_budget": 3,
        "history_cross_core_budget": "2..3",
        "must_include_repair_protected": True,
        "must_include_locked": True,
        "optional_only_repair_can_trim": True,
        "optional_only_repairable": True,
        "relation_line_forced_for_all_inputs": False,
        "full_summary_mode": False,
        "summarize_all_materials": False,
        "long_input_full_summary_blocked": True,
        "short_input_overinterpretation_guard_enabled": True,
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
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
        "observation_sentence_plan_roles_supported": True,
        "observation_sentence_plan_roles_step": OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
        "sentence_plan_observation_roles_added": True,
        "existing_line_role_preserved": True,
        "observation_roles_meta_only": True,
        "short_eligible_role_merge_allowed": True,
        "low_info_question_role_required": True,
        "public_line_role_enum_extended": False,
        "line_role_public_enum_extended": False,
        "observation_sentence_plan_roles_contract": build_observation_sentence_plan_roles_contract_meta(),
    }


def _planner_meta_for_plan(
    *,
    plan: CompleteSentencePlanV2,
    coverage_group: str,
    budget: int,
    nodes: Sequence[_PlanNode],
    optional_nodes: Sequence[_PlanNode],
    rejected_rows: Sequence[CompleteSentencePlanRejection],
    source_graph_meta: Mapping[str, Any],
    required_line_roles: Sequence[str],
) -> dict[str, Any]:
    contract = build_complete_sentence_planner_contract_meta()
    line_roles = tuple(_dedupe(line.line_role for line in plan.sentence_plans))
    relation_line_present = "relation" in line_roles
    status = COMPLETE_SENTENCE_PLAN_STATUS_READY if plan.usable else COMPLETE_SENTENCE_PLAN_STATUS_UNAVAILABLE
    observation_role_meta = build_observation_sentence_plan_roles_meta(
        lines=plan.sentence_plans,
        observation_context=plan.meta,
        coverage_group=coverage_group,
    )
    observation_role_meta_for_planner = {
        key: value
        for key, value in observation_role_meta.items()
        if key not in {"version", "schema_version", "source_step", "step", "target_step", "coverage_group", "status", "ready"}
    }
    return {
        **contract,
        **observation_role_meta_for_planner,
        "observation_sentence_plan_roles_meta": observation_role_meta,
        "status": status,
        "ready": plan.usable,
        "schema_version": COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION,
        "plan_id": plan.plan_id,
        "coverage_group": coverage_group,
        "sentence_budget": budget,
        "planned_sentence_count": len(plan.sentence_plans),
        "usable_sentence_plan_count": len(plan.usable_sentence_plans),
        "line_roles": list(line_roles),
        "line_role_order": list(line_roles),
        "required_line_roles": list(_dedupe(required_line_roles)),
        "relation_line_present": relation_line_present,
        "relation_line_added": relation_line_present,
        "relation_line_needed": _needs_relation_line(coverage_group, nodes, required_line_roles),
        "relation_line_forced_for_all_inputs": False,
        "must_include_roles": list(_dedupe(role for line in plan.sentence_plans for role in line.must_include_roles)),
        "optional_roles": list(_dedupe(role for line in plan.sentence_plans for role in line.optional_roles)),
        "forbidden_surface_keys": list(_dedupe(key for line in plan.sentence_plans for key in line.forbidden_surface_keys)),
        "repair_policy": list(_dedupe(key for line in plan.sentence_plans for key in line.repair_policy)),
        "selected_node_ids": [node.node_id for node in nodes],
        "optional_node_ids": [node.node_id for node in optional_nodes],
        "used_evidence_span_ids": list(plan.used_evidence_span_ids),
        "used_phrase_unit_ids": list(plan.used_phrase_unit_ids),
        "relation_types": list(plan.relation_types),
        "canonical_relation_types": list(_dedupe(canonical_relation_type(item) for item in plan.relation_types)),
        "relation_families": list(_dedupe(relation_family(item) for item in plan.relation_types)),
        "all_lines_source_bound": bool(plan.sentence_plans) and all(bool(line.evidence_span_ids and line.phrase_unit_ids and line.relation_type) for line in plan.sentence_plans),
        "source_bound_sentence_count": len(tuple(line for line in plan.sentence_plans if line.evidence_span_ids and line.phrase_unit_ids and line.relation_type)),
        "must_include_repair_protected": True,
        "must_include_locked": True,
        "optional_only_repair_can_trim": True,
        "optional_only_repairable": True,
        "surface_realizer_must_follow_plan": True,
        "surface_realizer_free_invention_blocked": True,
        "long_input_full_summary_blocked": coverage_group == "long_meaning_arc",
        "short_input_overinterpretation_guard_enabled": coverage_group == "short_daily",
        "closing_optional": any(line.line_role == "closing" for line in plan.sentence_plans),
        "closing_line_optional": any(line.line_role == "closing" for line in plan.sentence_plans),
        "long_input_min_sentence_budget_respected": coverage_group != "long_meaning_arc" or budget >= 3,
        "short_input_max_sentence_budget_respected": coverage_group != "short_daily" or budget <= 2,
        "full_summary_mode": False,
        "summarize_all_materials": False,
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
        "validation_errors": list(plan.validation_errors) + list(_dedupe(reason for row in rejected_rows for reason in row.reason_codes)),
        "rejected_rows": [row.as_meta() for row in rejected_rows],
        "source_relation_graph_summary": {
            "version": source_graph_meta.get("version"),
            "source_step": source_graph_meta.get("target_step") or source_graph_meta.get("source_step"),
            "status": source_graph_meta.get("status"),
            "ready": source_graph_meta.get("ready"),
            "coverage_group": source_graph_meta.get("coverage_group") or coverage_group,
            "graph_node_count": source_graph_meta.get("graph_node_count"),
            "relation_type_pre_generation_constraint": source_graph_meta.get("relation_type_pre_generation_constraint", True),
            "raw_input_included": False,
        },
        "source_graph_summary": {
            "version": source_graph_meta.get("version"),
            "source_step": source_graph_meta.get("target_step") or source_graph_meta.get("source_step"),
            "status": source_graph_meta.get("status"),
            "ready": source_graph_meta.get("ready"),
            "coverage_group": source_graph_meta.get("coverage_group") or coverage_group,
            "graph_node_count": source_graph_meta.get("graph_node_count"),
            "relation_type_pre_generation_constraint": source_graph_meta.get("relation_type_pre_generation_constraint", True),
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
    }


def build_complete_sentence_plan_v2(
    *,
    observation_graph: CompleteObservationGraphV2 | Mapping[str, Any] | None = None,
    relation_graph: CompleteObservationGraphV2 | Mapping[str, Any] | None = None,
    sentence_plan_seed: Mapping[str, Any] | None = None,
    coverage_plan: Any = None,
    material_bundle: Any = None,
    focus_selector_input: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    coverage_group: str = "",
    meta: Mapping[str, Any] | None = None,
) -> CompleteSentencePlanV2:
    """Build a binding-first Complete SentencePlan 2.0.

    The returned object is still an internal plan.  It is safe to place under
    additive meta; it is not a public response and it never emits comment_text.
    """

    seed, source_graph_meta, _graph = _graph_seed_from_input(
        observation_graph=observation_graph,
        relation_graph=relation_graph,
        sentence_plan_seed=sentence_plan_seed,
        coverage_plan=coverage_plan,
        material_bundle=material_bundle,
        focus_selector_input=focus_selector_input,
        evidence_spans=evidence_spans,
        phrase_units=phrase_units,
        coverage_group=coverage_group,
    )
    nodes, optional_nodes, rejected = _nodes_from_seed(seed)
    source_group = _normalize_coverage_group(coverage_group) or _normalize_coverage_group(seed.get("coverage_group")) or _normalize_coverage_group(source_graph_meta.get("coverage_group")) or "short_daily"
    relation_count = len(_dedupe(node.relation_type for node in nodes))
    budget = _coverage_budget(source_group, seed.get("sentence_budget"), relation_count=relation_count, node_count=len(nodes))
    required_roles = tuple(_dedupe(seed.get("required_line_roles") or ())) or ("opening", "core", "relation")
    plan_id = f"complete_sentence_plan_v2_{source_group}"
    lines = _build_lines(plan_id=plan_id, coverage_group=source_group, budget=budget, nodes=nodes, required_line_roles=required_roles)
    observation_role_context = _json_safe_mapping({**source_graph_meta, **seed, **_json_safe_mapping(meta)})
    lines = annotate_observation_sentence_plan_lines(
        lines,
        observation_context=observation_role_context,
        coverage_group=source_group,
    )
    observation_role_meta = build_observation_sentence_plan_roles_meta(
        lines=lines,
        observation_context=observation_role_context,
        coverage_group=source_group,
    )
    observation_role_meta_for_plan = {
        key: value
        for key, value in observation_role_meta.items()
        if key not in {"version", "schema_version", "source_step", "step", "target_step", "coverage_group", "status", "ready"}
    }
    # Build the plan first so its own validation can be included in planner meta.
    base_meta = {
        **build_complete_sentence_planner_contract_meta(),
        **_json_safe_mapping(meta),
        "source_relation_graph_summary": {
            "version": source_graph_meta.get("version"),
            "source_step": source_graph_meta.get("target_step") or source_graph_meta.get("source_step"),
            "coverage_group": source_group,
            "raw_input_included": False,
        },
        "source_graph_summary": {
            "version": source_graph_meta.get("version"),
            "source_step": source_graph_meta.get("target_step") or source_graph_meta.get("source_step"),
            "coverage_group": source_group,
            "raw_input_included": False,
        },
        "rejected_rows": [row.as_meta() for row in rejected],
        **observation_role_meta_for_plan,
        "observation_sentence_plan_roles_meta": observation_role_meta,
    }
    plan = CompleteSentencePlanV2(
        plan_id=plan_id,
        sentence_budget=budget,
        coverage_group=source_group,
        sentence_plans=lines,
        meta=base_meta,
    )
    planner_meta = _planner_meta_for_plan(
        plan=plan,
        coverage_group=source_group,
        budget=budget,
        nodes=nodes,
        optional_nodes=optional_nodes,
        rejected_rows=rejected,
        source_graph_meta=source_graph_meta,
        required_line_roles=required_roles,
    )
    return CompleteSentencePlanV2(
        plan_id=plan.plan_id,
        sentence_budget=plan.sentence_budget,
        coverage_group=plan.coverage_group,
        sentence_plans=plan.sentence_plans,
        meta={**planner_meta, **_json_safe_mapping(meta)},
    )


def build_complete_sentence_plan(**kwargs: Any) -> CompleteSentencePlanV2:
    return build_complete_sentence_plan_v2(**kwargs)


def build_complete_sentence_plan_2_0(**kwargs: Any) -> CompleteSentencePlanV2:
    return build_complete_sentence_plan_v2(**kwargs)


def build_complete_sentence_planner(**kwargs: Any) -> CompleteSentencePlanV2:
    return build_complete_sentence_plan_v2(**kwargs)


def plan_complete_sentences(**kwargs: Any) -> CompleteSentencePlanV2:
    return build_complete_sentence_plan_v2(**kwargs)



def _step6_sentence_binding_bundle(plan: CompleteSentencePlanV2) -> dict[str, Any]:
    bundle = plan.as_sentence_binding_bundle_meta()
    bundle = _json_safe_mapping(bundle)
    rows = list(bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items") or ())
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        clean_row = _json_safe_mapping(row)
        clean_row["source_step"] = COMPLETE_SENTENCE_PLAN_STAGE
        clean_row["target_step"] = "Step7_Surface_Realizer_2_0"
        clean_row["relation_pre_generation_constraint"] = True
        clean_row["surface_realizer_must_follow_plan"] = True
        clean_row["raw_input_included"] = False
        normalized_rows.append(clean_row)
    bundle.update(
        {
            "version": COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION,
            "bundle_version": COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION,
            "source": "complete_sentence_planner",
            "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "target_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "next_step": "Step7_Surface_Realizer_2_0",
            "binding_stage": "complete_sentence_plan_2_0",
            "type_binding_stage": "complete_sentence_plan_2_0_service_added",
            "binding_count": len(normalized_rows),
            "sentence_binding_count": len(normalized_rows),
            "expected_binding_count": len(normalized_rows),
            "bindings": normalized_rows,
            "sentence_bindings": normalized_rows,
            "items": normalized_rows,
            "relation_type_pre_generation_constraint": True,
            "surface_realizer_must_follow_plan": True,
            "response_shape_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
        }
    )
    return bundle


def build_complete_sentence_binding_bundle_meta(plan: CompleteSentencePlanV2 | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(plan, CompleteSentencePlanV2):
        return _step6_sentence_binding_bundle(plan)
    if isinstance(plan, Mapping):
        built = CompleteSentencePlanV2(
            plan_id=plan.get("plan_id") or "complete_sentence_plan_2_0",
            sentence_budget=plan.get("sentence_budget") or 2,
            coverage_group=plan.get("coverage_group") or plan.get("coverage_scope") or "unknown",
            sentence_plans=plan.get("sentence_plans") or plan.get("lines") or (),
            meta=plan.get("meta") or {},
        )
        return _step6_sentence_binding_bundle(built)
    return _step6_sentence_binding_bundle(CompleteSentencePlanV2(plan_id="complete_sentence_plan_2_0_unavailable", sentence_budget=2, coverage_group="unknown"))

def build_complete_sentence_plan_v2_meta(**kwargs: Any) -> dict[str, Any]:
    plan = build_complete_sentence_plan_v2(**kwargs)
    meta = plan.as_meta()
    # Flatten planner keys for Step 6 service tests while preserving the nested
    # internal type meta created by CompleteSentencePlanV2.
    for key, value in dict(plan.meta).items():
        if key == "validation_errors":
            meta["validation_errors"] = list(dict.fromkeys(list(meta.get("validation_errors") or []) + list(value or [])))
        elif key not in meta:
            meta[key] = value
    meta["sentence_binding_bundle"] = _step6_sentence_binding_bundle(plan)
    meta["sentence_binding_bundle_step6"] = meta["sentence_binding_bundle"]
    meta["raw_input_included"] = False
    meta["response_shape_changed"] = False
    return meta


def build_complete_sentence_planner_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_sentence_plan_v2_meta(**kwargs)


def complete_sentence_plan_meta(plan: CompleteSentencePlanV2) -> dict[str, Any]:
    meta = plan.as_meta()
    for key, value in dict(plan.meta).items():
        if key == "validation_errors":
            meta["validation_errors"] = list(dict.fromkeys(list(meta.get("validation_errors") or []) + list(value or [])))
        elif key not in meta:
            meta[key] = value
    meta["sentence_binding_bundle"] = _step6_sentence_binding_bundle(plan)
    meta["sentence_binding_bundle_step6"] = meta["sentence_binding_bundle"]
    meta["target_step"] = COMPLETE_SENTENCE_PLAN_STAGE
    meta["step"] = COMPLETE_SENTENCE_PLAN_STAGE
    meta["source"] = "complete_sentence_planner"
    meta["raw_input_included"] = False
    meta["response_shape_changed"] = False
    return _json_safe_mapping(meta)


def build_complete_sentence_plan_contract_meta() -> dict[str, Any]:
    return build_complete_sentence_planner_contract_meta()


def build_complete_sentence_plan_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_sentence_plan_v2_meta(**kwargs)


def complete_sentence_plan_lines(plan: CompleteSentencePlanV2 | None) -> Tuple[CompleteSentencePlanLine, ...]:
    if isinstance(plan, CompleteSentencePlanV2):
        return tuple(plan.sentence_plans)
    return tuple()


CompleteSentencePlan = CompleteSentencePlanV2
CompleteSentencePlanResult = CompleteSentencePlanV2
CompleteSentencePlannerResult = CompleteSentencePlanV2
SentencePlanV2 = CompleteSentencePlanV2

__all__ = [
    "COMPLETE_SENTENCE_PLAN_IMPLEMENTATION_UNIT",
    "COMPLETE_SENTENCE_PLAN_STAGE",
    "COMPLETE_SENTENCE_PLAN_SERVICE_VERSION",
    "COMPLETE_SENTENCE_PLAN_STATUS_READY",
    "COMPLETE_SENTENCE_PLAN_STATUS_UNAVAILABLE",
    "COMPLETE_SENTENCE_PLAN_STEP",
    "COMPLETE_SENTENCE_PLAN_V2_STAGE",
    "COMPLETE_SENTENCE_PLAN_V2_STEP",
    "COMPLETE_SENTENCE_PLAN_V2_TARGET_STEP",
    "COMPLETE_SENTENCE_PLAN_TARGET_STEP",
    "COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION",
    "COMPLETE_SENTENCE_PLAN_BUILD_META_VERSION",
    "COMPLETE_SENTENCE_PLANNER_IMPLEMENTATION_UNIT",
    "COMPLETE_SENTENCE_PLANNER_STAGE",
    "COMPLETE_SENTENCE_PLANNER_STEP",
    "COMPLETE_SENTENCE_PLANNER_TARGET_STEP",
    "COMPLETE_SENTENCE_PLANNER_SERVICE_VERSION",
    "COMPLETE_SENTENCE_PLANNER_VERSION",
    "CompleteSentencePlan",
    "CompleteSentencePlanRejection",
    "CompleteSentencePlanResult",
    "CompleteSentencePlannerResult",
    "SentencePlanV2",
    "build_complete_sentence_binding_bundle_meta",
    "build_complete_sentence_plan",
    "build_complete_sentence_plan_2_0",
    "build_complete_sentence_plan_v2",
    "build_complete_sentence_plan_v2_meta",
    "complete_sentence_plan_meta",
    "build_complete_sentence_planner",
    "build_complete_sentence_planner_contract_meta",
    "build_complete_sentence_planner_meta",
    "complete_sentence_plan_lines",
    "plan_complete_sentences",
    "OBSERVATION_SENTENCE_PLAN_ROLES_STEP",
]
