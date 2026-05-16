# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 4 FocusSelector / CoveragePlan for EmlisAI Complete Composer.

This additive internal service receives the source-bound materials created by
Step 3 and chooses the observation nuclei that should be passed to
SentencePlan 2.0.  It intentionally does not summarize all materials, create
user-facing ``comment_text``, relax gates, or change DB/API/RN contracts.
"""

from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_STAGE
from emlis_ai_complete_material_service import (
    CompleteMaterialBundle,
    CompleteMaterialUnit,
    build_complete_material_bundle,
)
from emlis_ai_limited_relation_taxonomy import (
    canonical_relation_type,
    normalize_relation_type,
    relation_family,
)

COMPLETE_FOCUS_SELECTOR_VERSION = "emlis.complete_focus_selector.v1"
COMPLETE_COVERAGE_PLAN_SCHEMA_VERSION = "emlis.complete_coverage_plan.v1"
COMPLETE_FOCUS_ITEM_SCHEMA_VERSION = "emlis.complete_focus_item.v1"
COMPLETE_FOCUS_REJECTION_SCHEMA_VERSION = "emlis.complete_focus_rejection.v1"
COMPLETE_FOCUS_SELECTOR_STAGE = "Step4_FocusSelector_CoveragePlan"
COMPLETE_FOCUS_SELECTOR_STEP = COMPLETE_FOCUS_SELECTOR_STAGE
COMPLETE_COVERAGE_PLAN_STAGE = COMPLETE_FOCUS_SELECTOR_STAGE
COMPLETE_FOCUS_SELECTOR_IMPLEMENTATION_UNIT = "Commit 4"

COMPLETE_FOCUS_STATUS_READY = "ready"
COMPLETE_FOCUS_STATUS_UNAVAILABLE = "unavailable"

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


@dataclass(frozen=True)
class CoveragePolicy:
    coverage_group: str
    sentence_budget_min: int
    sentence_budget_max: int
    default_sentence_budget: int
    max_focus_items: int
    required_relations: tuple[str, ...] = ()
    preferred_relations: tuple[str, ...] = ()
    preferred_roles: tuple[str, ...] = ()
    support_relations: tuple[str, ...] = ()
    selection_mode: str = "focus_nucleus"
    plan_intent: str = "select_observation_nucleus"

    def as_meta(self) -> dict[str, Any]:
        return {
            "coverage_group": self.coverage_group,
            "sentence_budget_min": self.sentence_budget_min,
            "sentence_budget_max": self.sentence_budget_max,
            "default_sentence_budget": self.default_sentence_budget,
            "max_focus_items": self.max_focus_items,
            "required_relations": list(self.required_relations),
            "preferred_relations": list(self.preferred_relations),
            "preferred_roles": list(self.preferred_roles),
            "support_relations": list(self.support_relations),
            "selection_mode": self.selection_mode,
            "plan_intent": self.plan_intent,
            "summarize_all_materials": False,
            "raw_input_included": False,
        }


COVERAGE_POLICIES: dict[str, CoveragePolicy] = {
    "short_daily": CoveragePolicy(
        coverage_group="short_daily",
        sentence_budget_min=2,
        sentence_budget_max=2,
        default_sentence_budget=2,
        max_focus_items=2,
        preferred_relations=("center", "coexistence", "pressure", "recovery", "contrast"),
        selection_mode="minimal_state_and_wobble",
        plan_intent="avoid_overinterpretation_for_short_input",
    ),
    "long_meaning_arc": CoveragePolicy(
        coverage_group="long_meaning_arc",
        sentence_budget_min=3,
        sentence_budget_max=4,
        default_sentence_budget=3,
        max_focus_items=4,
        preferred_relations=("pressure", "tension", "coexistence", "residue", "contrast", "recovery"),
        selection_mode="recurring_core_and_residue",
        plan_intent="select_meaning_core_not_full_summary",
    ),
    "conflict": CoveragePolicy(
        coverage_group="conflict",
        sentence_budget_min=3,
        sentence_budget_max=3,
        default_sentence_budget=3,
        max_focus_items=3,
        required_relations=("contrast", "coexistence", "approach_avoidance", "tension"),
        preferred_relations=("approach_avoidance", "contrast", "coexistence", "tension"),
        preferred_roles=("wish_to_rely", "burden_fear", "rejection_fear", "avoidance_wish", "value_wish", "perfection_fear"),
        selection_mode="hold_both_sides",
        plan_intent="preserve_coexisting_or_conflicting_materials",
    ),
    "recovery": CoveragePolicy(
        coverage_group="recovery",
        sentence_budget_min=2,
        sentence_budget_max=3,
        default_sentence_budget=3,
        max_focus_items=3,
        preferred_relations=("recovery", "pressure", "contrast", "coexistence"),
        support_relations=("pressure", "contrast", "residue"),
        preferred_roles=("small_repair", "small_action", "achievement", "relieved_weight", "positive_state", "fatigue_accumulation"),
        selection_mode="recovery_with_prior_load",
        plan_intent="keep_recovery_connected_to_previous_load",
    ),
    "pressure": CoveragePolicy(
        coverage_group="pressure",
        sentence_budget_min=2,
        sentence_budget_max=4,
        default_sentence_budget=3,
        max_focus_items=4,
        preferred_relations=("pressure", "limit", "residue", "coexistence", "contrast"),
        preferred_roles=("fatigue_accumulation", "loss_of_control", "anticipation_loop", "low_energy", "limit", "avoidance_wish"),
        selection_mode="pressure_without_diagnosis",
        plan_intent="observe_load_without_personality_or_diagnosis",
    ),
    "relationship": CoveragePolicy(
        coverage_group="relationship",
        sentence_budget_min=3,
        sentence_budget_max=3,
        default_sentence_budget=3,
        max_focus_items=3,
        preferred_relations=("approach_avoidance", "approach", "limit", "distance", "residue", "coexistence"),
        preferred_roles=("wish_to_rely", "burden_fear", "rejection_fear", "withdrawal", "hurt_core", "avoidance_wish"),
        selection_mode="self_side_relation_observation",
        plan_intent="avoid_other_person_personality_claims",
    ),
    "history_cross_core": CoveragePolicy(
        coverage_group="history_cross_core",
        sentence_budget_min=2,
        sentence_budget_max=3,
        default_sentence_budget=2,
        max_focus_items=3,
        preferred_relations=("context", "coexistence", "pressure", "recovery", "contrast"),
        preferred_roles=("known_action", "safe_home", "small_repair", "fatigue_accumulation", "value_wish"),
        selection_mode="explicit_evidence_only",
        plan_intent="use_cross_core_only_when_material_has_anchor",
    ),
}

COVERAGE_ALIASES = {
    "short": "short_daily",
    "daily": "short_daily",
    "short_daily_input": "short_daily",
    "long": "long_meaning_arc",
    "long_arc": "long_meaning_arc",
    "long_input": "long_meaning_arc",
    "meaning_arc": "long_meaning_arc",
    "desire_fear": "conflict",
    "desire-fear": "conflict",
    "approach_avoidance": "conflict",
    "positive_progress_recovery": "recovery",
    "positive_progress": "recovery",
    "energy_recovery": "recovery",
    "energy_fatigue_pressure": "pressure",
    "anxiety_anticipation_loop": "pressure",
    "fatigue_pressure": "pressure",
    "relationship_approach_avoidance": "relationship",
    "current_input_core": "short_daily",
}

RELATION_PRIORITY_BY_POLICY: dict[str, tuple[str, ...]] = {
    key: policy.preferred_relations + tuple(relation for relation in ("pressure", "recovery", "contrast", "coexistence", "approach_avoidance", "residue", "limit", "context") if relation not in policy.preferred_relations)
    for key, policy in COVERAGE_POLICIES.items()
}


ROLE_COVERAGE_HINTS: tuple[tuple[set[str], str], ...] = (
    ({"wish_to_rely", "burden_fear", "rejection_fear", "withdrawal", "hurt_core"}, "relationship"),
    ({"avoidance_wish", "value_wish", "perfection_fear", "ordinary_life_wish"}, "conflict"),
    ({"small_repair", "small_action", "achievement", "relieved_weight", "positive_state", "safe_home"}, "recovery"),
    ({"fatigue_accumulation", "loss_of_control", "anticipation_loop", "low_energy", "limit", "worsening_risk"}, "pressure"),
)


RELATION_COVERAGE_HINTS: tuple[tuple[set[str], str], ...] = (
    ({"approach_avoidance", "approach", "distance"}, "relationship"),
    ({"tension"}, "conflict"),
    ({"recovery"}, "recovery"),
    ({"pressure", "limit"}, "pressure"),
)


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


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    out: dict[str, Any] = {}
    for key in (
        "material_id",
        "phrase_unit_id",
        "evidence_span_id",
        "material_text",
        "role",
        "polarity",
        "must_keep",
        "relation_type",
        "canonical_relation_type",
        "relation_family",
        "source_anchor",
        "focus_rank",
        "meta",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


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


def _source_anchor_present(value: Any) -> bool:
    row = _as_mapping(value)
    anchor = row.get("source_anchor") or {}
    evidence_span_id = _clean(row.get("evidence_span_id"))
    if isinstance(anchor, Mapping) and anchor:
        return bool(anchor.get("source_anchor_present")) or bool(anchor.get("evidence_span_id")) or bool(evidence_span_id)
    return bool(evidence_span_id)


def _normalize_coverage_group(value: Any) -> str:
    group = _clean(value)
    if not group:
        return ""
    group = group.lower().replace("-", "_").replace(" ", "_")
    return COVERAGE_ALIASES.get(group, group)


def _material_relation(row: Mapping[str, Any]) -> str:
    role = _clean(row.get("role"))
    relation = _clean(row.get("relation_type") or row.get("canonical_relation_type"))
    return normalize_relation_type(relation, roles=(role,) if role else (), line_role=role)


def _infer_coverage_group(rows: Sequence[Mapping[str, Any]], requested: str = "") -> str:
    requested_group = _normalize_coverage_group(requested)
    if requested_group in COVERAGE_POLICIES:
        return requested_group
    roles = set(_clean(row.get("role")) for row in rows if _clean(row.get("role")))
    relations = set(_material_relation(row) for row in rows if _material_relation(row))
    if len(rows) >= 5:
        return "long_meaning_arc"
    for relation_set, group in RELATION_COVERAGE_HINTS:
        if relations.intersection(relation_set):
            if group == "recovery" and (relations.intersection({"pressure", "contrast", "coexistence"}) or len(rows) <= 3):
                return "recovery"
            if group in {"relationship", "conflict", "pressure"}:
                return group
    for role_set, group in ROLE_COVERAGE_HINTS:
        if roles.intersection(role_set):
            return group
    if len(rows) <= 2:
        return "short_daily"
    if relations.intersection({"contrast", "coexistence"}):
        return "conflict"
    return "short_daily" if len(rows) <= 2 else "long_meaning_arc"


def _policy_for_group(group: str) -> CoveragePolicy:
    normalized = _normalize_coverage_group(group)
    return COVERAGE_POLICIES.get(normalized) or COVERAGE_POLICIES["short_daily"]


def _relation_priority(policy: CoveragePolicy, relation: str) -> int:
    ordered = RELATION_PRIORITY_BY_POLICY.get(policy.coverage_group, ())
    relation = normalize_relation_type(relation)
    if relation in ordered:
        return max(1, len(ordered) - ordered.index(relation))
    canonical = canonical_relation_type(relation)
    for index, item in enumerate(ordered):
        if canonical_relation_type(item) == canonical:
            return max(1, len(ordered) - index - 1)
    return 0


def _role_priority(policy: CoveragePolicy, role: str) -> int:
    role = _clean(role)
    if role in policy.preferred_roles:
        return max(1, len(policy.preferred_roles) - list(policy.preferred_roles).index(role))
    return 0


def _safe_focus_limit(policy: CoveragePolicy, material_count: int) -> int:
    if material_count <= 0:
        return 0
    return max(1, min(policy.max_focus_items, material_count, max(policy.sentence_budget_max, policy.default_sentence_budget)))


def _budget_for(policy: CoveragePolicy, selected_count: int, material_count: int, relation_count: int) -> int:
    if material_count <= 0 or selected_count <= 0:
        return 0
    if policy.coverage_group == "long_meaning_arc":
        wanted = 4 if material_count >= 6 or relation_count >= 3 else 3
    elif policy.coverage_group == "pressure":
        wanted = min(4, max(2, selected_count + (1 if relation_count > 1 else 0)))
    elif policy.coverage_group == "recovery":
        wanted = 3 if selected_count >= 2 or relation_count >= 2 else 2
    else:
        wanted = policy.default_sentence_budget
    return max(policy.sentence_budget_min, min(wanted, policy.sentence_budget_max))


def _line_roles_for(policy: CoveragePolicy, selected_items: Sequence["CompleteFocusItem"]) -> Tuple[str, ...]:
    if not selected_items:
        return tuple()
    roles = ["opening", "core"]
    selected_relations = {item.relation_type for item in selected_items}
    if policy.coverage_group in {"conflict", "relationship"} or len(selected_relations) >= 2:
        roles.append("relation")
    if policy.default_sentence_budget >= 3 or policy.coverage_group in {"long_meaning_arc", "pressure", "relationship"}:
        roles.append("closing")
    return tuple(dict.fromkeys(roles))


def _selection_reason(policy: CoveragePolicy, row: Mapping[str, Any], rank: int) -> Tuple[str, ...]:
    relation = _material_relation(row)
    role = _clean(row.get("role"))
    reasons: list[str] = []
    if bool(row.get("must_keep")):
        reasons.append("must_keep_material")
    if relation in policy.required_relations:
        reasons.append("required_relation_for_coverage")
    if relation in policy.preferred_relations or canonical_relation_type(relation) in {canonical_relation_type(item) for item in policy.preferred_relations}:
        reasons.append("preferred_relation_for_coverage")
    if role in policy.preferred_roles:
        reasons.append("preferred_role_for_coverage")
    if _source_anchor_present(row):
        reasons.append("source_anchor_present")
    if rank == 1:
        reasons.append("primary_focus")
    return tuple(dict.fromkeys(reasons)) or ("coverage_focus_candidate",)


def _score_row(policy: CoveragePolicy, row: Mapping[str, Any], index: int) -> tuple[int, int, int, int, int]:
    relation = _material_relation(row)
    role = _clean(row.get("role"))
    must_keep = 1 if bool(row.get("must_keep")) else 0
    anchor = 1 if _source_anchor_present(row) else 0
    relation_score = _relation_priority(policy, relation)
    role_score = _role_priority(policy, role)
    support_score = 2 if relation in policy.support_relations else 0
    # Negative index keeps stable input order for equal scores.
    return (must_keep, relation_score + support_score, role_score, anchor, -index)


def _material_rows_from_bundle(material_bundle: Any) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    if isinstance(material_bundle, CompleteMaterialBundle):
        return ([item.as_focus_seed() for item in material_bundle.usable_materials], material_bundle.coverage_group, material_bundle.as_meta())
    if isinstance(material_bundle, Mapping):
        materials = material_bundle.get("materials") or material_bundle.get("rows") or material_bundle.get("focus_materials") or ()
        return ([dict(item) for item in materials if isinstance(item, Mapping)], _clean(material_bundle.get("coverage_group")), _json_safe_mapping(material_bundle))
    if isinstance(material_bundle, Sequence) and not isinstance(material_bundle, (str, bytes)):
        return ([_as_mapping(item) for item in material_bundle], "", {})
    return ([], "", {})


@dataclass(frozen=True)
class CompleteFocusItem:
    material_id: str
    phrase_unit_id: str
    evidence_span_id: str
    role: str
    relation_type: str
    focus_rank: int
    focus_role: str = "primary"
    polarity: str = "neutral"
    must_keep: bool = False
    source_anchor_present: bool = False
    selection_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_FOCUS_ITEM_SCHEMA_VERSION

    def __post_init__(self) -> None:
        role = _clean(self.role)
        relation = normalize_relation_type(self.relation_type, roles=(role,) if role else (), line_role=role)
        object.__setattr__(self, "material_id", _clean(self.material_id))
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "relation_type", relation)
        object.__setattr__(self, "focus_rank", max(1, int(self.focus_rank or 1)))
        object.__setattr__(self, "focus_role", _clean(self.focus_role) or "primary")
        object.__setattr__(self, "polarity", _clean(self.polarity) or "neutral")
        object.__setattr__(self, "must_keep", bool(self.must_keep))
        object.__setattr__(self, "source_anchor_present", bool(self.source_anchor_present or self.evidence_span_id))
        object.__setattr__(self, "selection_reasons", tuple(_dedupe(self.selection_reasons)))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_FOCUS_ITEM_SCHEMA_VERSION)

    @property
    def canonical_relation_type(self) -> str:
        return canonical_relation_type(self.relation_type)

    @property
    def relation_family(self) -> str:
        return relation_family(self.relation_type)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
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
        if not self.source_anchor_present:
            errors.append("source_anchor_missing")
        return tuple(errors)

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_sentence_plan_focus(self) -> dict[str, Any]:
        return {
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
            "raw_input_included": False,
        }

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "material_id": self.material_id,
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "role": self.role,
            "polarity": self.polarity,
            "relation_type": self.relation_type,
            "canonical_relation_type": self.canonical_relation_type,
            "relation_family": self.relation_family,
            "focus_rank": self.focus_rank,
            "focus_role": self.focus_role,
            "must_keep": self.must_keep,
            "source_anchor_present": self.source_anchor_present,
            "selection_reasons": list(self.selection_reasons),
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "raw_text_included": False,
            "raw_input_included": False,
            "comment_text_generated": False,
            "completion_sentence_template": False,
            "fixed_sentence_template": False,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class CompleteFocusRejection:
    reason_codes: Iterable[str]
    material_id: str = ""
    phrase_unit_id: str = ""
    evidence_span_id: str = ""
    role: str = ""
    relation_type: str = ""
    source: str = "focus_selector"
    schema_version: str = COMPLETE_FOCUS_REJECTION_SCHEMA_VERSION
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(_dedupe(self.reason_codes)))
        object.__setattr__(self, "material_id", _clean(self.material_id))
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "role", _clean(self.role))
        object.__setattr__(self, "relation_type", _clean(self.relation_type))
        object.__setattr__(self, "source", _clean(self.source) or "focus_selector")
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_FOCUS_REJECTION_SCHEMA_VERSION)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "target_step": COMPLETE_FOCUS_SELECTOR_STAGE,
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
class CompleteCoveragePlan:
    coverage_group: str
    focus_items: Iterable[CompleteFocusItem] = dataclass_field(default_factory=tuple)
    optional_items: Iterable[CompleteFocusItem] = dataclass_field(default_factory=tuple)
    rejected_rows: Iterable[CompleteFocusRejection | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    sentence_budget: int = 0
    sentence_budget_min: int = 0
    sentence_budget_max: int = 0
    requested_coverage_group: str = ""
    policy: CoveragePolicy | None = None
    material_count: int = 0
    source_material_meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_COVERAGE_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        group = _normalize_coverage_group(self.coverage_group) or "short_daily"
        policy = self.policy if isinstance(self.policy, CoveragePolicy) else _policy_for_group(group)
        focus_items = tuple(item for item in self.focus_items if isinstance(item, CompleteFocusItem))
        optional_items = tuple(item for item in self.optional_items if isinstance(item, CompleteFocusItem))
        rejected: list[CompleteFocusRejection] = []
        for row in self.rejected_rows:
            if isinstance(row, CompleteFocusRejection):
                rejected.append(row)
            elif isinstance(row, Mapping):
                rejected.append(
                    CompleteFocusRejection(
                        reason_codes=row.get("reason_codes") or row.get("rejection_reasons") or (),
                        material_id=row.get("material_id") or "",
                        phrase_unit_id=row.get("phrase_unit_id") or "",
                        evidence_span_id=row.get("evidence_span_id") or "",
                        role=row.get("role") or "",
                        relation_type=row.get("relation_type") or "",
                        source=row.get("source") or "focus_selector",
                    )
                )
        budget = int(self.sentence_budget or 0)
        budget_min = int(self.sentence_budget_min or policy.sentence_budget_min)
        budget_max = int(self.sentence_budget_max or policy.sentence_budget_max)
        if focus_items:
            budget = max(budget_min, min(budget or policy.default_sentence_budget, budget_max))
        else:
            budget = 0
        object.__setattr__(self, "coverage_group", group)
        object.__setattr__(self, "policy", policy)
        object.__setattr__(self, "focus_items", focus_items)
        object.__setattr__(self, "optional_items", optional_items)
        object.__setattr__(self, "rejected_rows", tuple(rejected))
        object.__setattr__(self, "sentence_budget", budget)
        object.__setattr__(self, "sentence_budget_min", budget_min if focus_items else 0)
        object.__setattr__(self, "sentence_budget_max", budget_max if focus_items else 0)
        object.__setattr__(self, "requested_coverage_group", _clean(self.requested_coverage_group))
        object.__setattr__(self, "material_count", max(int(self.material_count or 0), len(focus_items) + len(optional_items)))
        object.__setattr__(self, "source_material_meta", _json_safe_mapping(self.source_material_meta))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_COVERAGE_PLAN_SCHEMA_VERSION)

    @property
    def selected_material_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.material_id for item in self.focus_items))

    @property
    def optional_material_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.material_id for item in self.optional_items))

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.evidence_span_id for item in self.focus_items))

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.phrase_unit_id for item in self.focus_items))

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.relation_type for item in self.focus_items))

    @property
    def canonical_relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.canonical_relation_type for item in self.focus_items))

    @property
    def relation_families(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.relation_family for item in self.focus_items))

    @property
    def role_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.role for item in self.focus_items))

    @property
    def must_include_role_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.role for item in self.focus_items if item.must_keep or item.focus_role in {"primary", "support"}))

    @property
    def relation_density(self) -> float:
        if not self.focus_items:
            return 0.0
        return round(len(self.relation_types) / max(1, len(self.focus_items)), 3)

    @property
    def ready(self) -> bool:
        return bool(self.focus_items) and all(item.usable for item in self.focus_items)

    @property
    def status(self) -> str:
        return COMPLETE_FOCUS_STATUS_READY if self.ready else COMPLETE_FOCUS_STATUS_UNAVAILABLE

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.focus_items:
            errors.append("focus_materials_missing")
        if self.focus_items and not self.used_evidence_span_ids:
            errors.append("used_evidence_span_ids_missing")
        if self.focus_items and not self.used_phrase_unit_ids:
            errors.append("used_phrase_unit_ids_missing")
        if self.focus_items and not self.relation_types:
            errors.append("relation_type_missing")
        for item in self.focus_items:
            errors.extend(item.validation_errors)
        for row in self.rejected_rows:
            errors.extend(row.reason_codes)
        return tuple(dict.fromkeys(errors))

    @property
    def required_line_roles(self) -> Tuple[str, ...]:
        return _line_roles_for(self.policy or _policy_for_group(self.coverage_group), list(self.focus_items))

    def as_sentence_plan_seed(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "source_step": COMPLETE_FOCUS_SELECTOR_STAGE,
            "target_step": "Step6_SentencePlan_2_0",
            "coverage_group": self.coverage_group,
            "sentence_budget": self.sentence_budget,
            "sentence_budget_min": self.sentence_budget_min,
            "sentence_budget_max": self.sentence_budget_max,
            "focus_items": [item.as_sentence_plan_focus() for item in self.focus_items],
            "optional_focus_items": [item.as_sentence_plan_focus() for item in self.optional_items],
            "selected_material_ids": list(self.selected_material_ids),
            "optional_material_ids": list(self.optional_material_ids),
            "must_include_role_types": list(self.must_include_role_types),
            "optional_role_types": list(_dedupe(item.role for item in self.optional_items)),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "canonical_relation_types": list(self.canonical_relation_types),
            "relation_families": list(self.relation_families),
            "required_line_roles": list(self.required_line_roles),
            "summarize_all_materials": False,
            "raw_input_included": False,
            "response_shape_changed": False,
        }

    def as_meta(self) -> dict[str, Any]:
        policy = self.policy or _policy_for_group(self.coverage_group)
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "target_step": COMPLETE_FOCUS_SELECTOR_STAGE,
            "step": COMPLETE_FOCUS_SELECTOR_STAGE,
            "implementation_unit": COMPLETE_FOCUS_SELECTOR_IMPLEMENTATION_UNIT,
            "stage": COMPLETE_COMPOSER_STAGE,
            "source": "complete_focus_selector",
            "status": self.status,
            "ready": self.ready,
            "focus_selector_added": True,
            "coverage_plan_added": True,
            "coverage_group": self.coverage_group,
            "requested_coverage_group": self.requested_coverage_group,
            "coverage_policy": policy.as_meta(),
            "material_count": self.material_count,
            "selected_focus_count": len(self.focus_items),
            "optional_focus_count": len(self.optional_items),
            "selected_material_ids": list(self.selected_material_ids),
            "optional_material_ids": list(self.optional_material_ids),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "canonical_relation_types": list(self.canonical_relation_types),
            "relation_families": list(self.relation_families),
            "role_types": list(self.role_types),
            "must_include_role_types": list(self.must_include_role_types),
            "sentence_budget": self.sentence_budget,
            "sentence_budget_min": self.sentence_budget_min,
            "sentence_budget_max": self.sentence_budget_max,
            "relation_density": self.relation_density,
            "required_line_roles": list(self.required_line_roles),
            "summarize_all_materials": False,
            "full_summary_mode": False,
            "observation_nucleus_selected": self.ready,
            "short_input_overinterpretation_guard_enabled": self.coverage_group == "short_daily",
            "long_input_full_summary_blocked": self.coverage_group == "long_meaning_arc",
            "history_cross_core_requires_explicit_evidence": self.coverage_group == "history_cross_core",
            "gate_relaxed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
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
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_improvement": False,
            "validation_errors": list(self.validation_errors),
            "focus_rows": [item.as_meta() for item in self.focus_items],
            "optional_rows": [item.as_meta() for item in self.optional_items],
            "rejected_rows": [row.as_meta() for row in self.rejected_rows],
            "sentence_plan_seed": self.as_sentence_plan_seed(),
            "source_material_summary": {
                "version": self.source_material_meta.get("version"),
                "source_step": self.source_material_meta.get("target_step") or self.source_material_meta.get("source_step"),
                "usable_material_count": self.source_material_meta.get("usable_material_count") or self.source_material_meta.get("material_count"),
                "rejected_material_count": self.source_material_meta.get("rejected_material_count"),
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


def build_complete_focus_selector_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta()
    return {
        "version": COMPLETE_FOCUS_SELECTOR_VERSION,
        "target_step": COMPLETE_FOCUS_SELECTOR_STAGE,
        "step": COMPLETE_FOCUS_SELECTOR_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_FOCUS_SELECTOR_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta.get("target_composer_term"),
        "target_composer_family_term": term_meta.get("target_composer_family_term"),
        "complete_composer_initial_term": term_meta.get("complete_composer_initial_term"),
        "focus_selector_added": True,
        "coverage_plan_added": True,
        "runtime_client_connected": False,
        "accepts_complete_material_service_output": True,
        "material_service_required": True,
        "sentence_plan_pre_stage": True,
        "selects_observation_nucleus": True,
        "summarize_all_materials": False,
        "coverage_groups_supported": list(COVERAGE_POLICIES.keys()),
        "sentence_budget_range": "2..4_pre_sentence_plan",
        "short_daily_budget": 2,
        "long_meaning_arc_budget": "3..4",
        "conflict_budget": 3,
        "recovery_budget": "2..3",
        "pressure_budget": "2..4",
        "relationship_budget": 3,
        "history_cross_core_budget": "2..3",
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


def _focus_items_for_rows(rows: Sequence[Mapping[str, Any]], policy: CoveragePolicy) -> tuple[list[CompleteFocusItem], list[CompleteFocusItem], list[CompleteFocusRejection]]:
    rejected: list[CompleteFocusRejection] = []
    valid_rows: list[tuple[int, Mapping[str, Any]]] = []
    for index, row in enumerate(rows, start=1):
        material_id = _clean(row.get("material_id") or f"cm{index}")
        phrase_unit_id = _clean(row.get("phrase_unit_id") or material_id)
        evidence_span_id = _clean(row.get("evidence_span_id"))
        relation = _material_relation(row)
        role = _clean(row.get("role"))
        reasons: list[str] = []
        if not material_id:
            reasons.append("material_id_missing")
        if not phrase_unit_id:
            reasons.append("phrase_unit_id_missing")
        if not evidence_span_id:
            reasons.append("evidence_span_id_missing")
        if not role:
            reasons.append("role_missing")
        if not relation:
            reasons.append("relation_type_missing")
        if not _source_anchor_present(row):
            reasons.append("source_anchor_missing")
        if policy.coverage_group == "history_cross_core" and not _source_anchor_present(row):
            reasons.append("history_cross_core_evidence_anchor_missing")
        if reasons:
            rejected.append(CompleteFocusRejection(reason_codes=reasons, material_id=material_id, phrase_unit_id=phrase_unit_id, evidence_span_id=evidence_span_id, role=role, relation_type=relation))
        else:
            valid_rows.append((index, row))
    if not valid_rows:
        if not rows:
            rejected.append(CompleteFocusRejection(reason_codes=("complete_materials_missing", "focus_materials_missing")))
        return [], [], rejected

    ranked = sorted(valid_rows, key=lambda item: _score_row(policy, item[1], item[0]), reverse=True)
    limit = _safe_focus_limit(policy, len(valid_rows))
    selected_pairs = ranked[:limit]

    # For relation-heavy coverage, preserve at least two different relation types when available.
    if policy.coverage_group in {"conflict", "relationship", "recovery", "pressure", "long_meaning_arc"} and limit >= 2:
        selected_relations = {_material_relation(row) for _idx, row in selected_pairs}
        for pair in ranked[limit:]:
            relation = _material_relation(pair[1])
            if relation not in selected_relations:
                selected_pairs[-1] = pair
                selected_relations.add(relation)
                break

    selected_identity = {id(row) for _idx, row in selected_pairs}
    selected: list[CompleteFocusItem] = []
    optional: list[CompleteFocusItem] = []
    for rank, (index, row) in enumerate(selected_pairs, start=1):
        relation = _material_relation(row)
        role = _clean(row.get("role"))
        selected.append(
            CompleteFocusItem(
                material_id=_clean(row.get("material_id") or f"cm{index}"),
                phrase_unit_id=_clean(row.get("phrase_unit_id") or row.get("material_id") or f"cm{index}"),
                evidence_span_id=_clean(row.get("evidence_span_id")),
                role=role,
                relation_type=relation,
                focus_rank=rank,
                focus_role="primary" if rank == 1 else ("support" if relation in policy.support_relations else "relation" if relation in policy.required_relations else "support"),
                polarity=_clean(row.get("polarity")) or "neutral",
                must_keep=bool(row.get("must_keep")) or rank == 1,
                source_anchor_present=_source_anchor_present(row),
                selection_reasons=_selection_reason(policy, row, rank),
                meta={"source_index": index, "coverage_group": policy.coverage_group},
            )
        )
    optional_rank = len(selected) + 1
    for index, row in valid_rows:
        if id(row) in selected_identity:
            continue
        relation = _material_relation(row)
        role = _clean(row.get("role"))
        optional.append(
            CompleteFocusItem(
                material_id=_clean(row.get("material_id") or f"cm{index}"),
                phrase_unit_id=_clean(row.get("phrase_unit_id") or row.get("material_id") or f"cm{index}"),
                evidence_span_id=_clean(row.get("evidence_span_id")),
                role=role,
                relation_type=relation,
                focus_rank=optional_rank,
                focus_role="optional",
                polarity=_clean(row.get("polarity")) or "neutral",
                must_keep=bool(row.get("must_keep")),
                source_anchor_present=_source_anchor_present(row),
                selection_reasons=("optional_material_deferred",),
                meta={"source_index": index, "coverage_group": policy.coverage_group},
            )
        )
        optional_rank += 1
    return selected, optional, rejected


def build_complete_coverage_plan(
    *,
    material_bundle: CompleteMaterialBundle | Mapping[str, Any] | Sequence[Any] | None = None,
    focus_selector_input: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    coverage_group: str = "",
    meta: Mapping[str, Any] | None = None,
) -> CompleteCoveragePlan:
    """Select Focus nuclei and build a CoveragePlan from Step 3 materials."""

    source_meta: dict[str, Any] = {}
    requested_group = _normalize_coverage_group(coverage_group)
    rows: list[dict[str, Any]] = []
    inferred_source_group = ""

    if material_bundle is not None:
        rows, inferred_source_group, source_meta = _material_rows_from_bundle(material_bundle)
    elif focus_selector_input is not None:
        rows, inferred_source_group, source_meta = _material_rows_from_bundle(focus_selector_input)
    elif evidence_spans is not None or phrase_units is not None:
        bundle = build_complete_material_bundle(evidence_spans=evidence_spans, phrase_units=phrase_units, coverage_group=coverage_group or "complete_initial_materials")
        rows, inferred_source_group, source_meta = _material_rows_from_bundle(bundle)
    else:
        rows = []

    effective_requested = requested_group or _normalize_coverage_group(inferred_source_group)
    group = _infer_coverage_group(rows, effective_requested)
    policy = _policy_for_group(group)
    selected, optional, rejected = _focus_items_for_rows(rows, policy)
    relation_count = len(_dedupe(item.relation_type for item in selected))
    budget = _budget_for(policy, selected_count=len(selected), material_count=len(rows), relation_count=relation_count)
    return CompleteCoveragePlan(
        coverage_group=policy.coverage_group,
        requested_coverage_group=effective_requested,
        focus_items=tuple(selected),
        optional_items=tuple(optional),
        rejected_rows=tuple(rejected),
        sentence_budget=budget,
        sentence_budget_min=policy.sentence_budget_min,
        sentence_budget_max=policy.sentence_budget_max,
        policy=policy,
        material_count=len(rows),
        source_material_meta=source_meta,
        meta={**build_complete_focus_selector_contract_meta(), **_json_safe_mapping(meta)},
    )


def build_complete_focus_selection(**kwargs: Any) -> CompleteCoveragePlan:
    return build_complete_coverage_plan(**kwargs)


def select_complete_focus(**kwargs: Any) -> CompleteCoveragePlan:
    return build_complete_coverage_plan(**kwargs)


def build_complete_coverage_plan_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_coverage_plan(**kwargs).as_meta()


def build_complete_focus_selector_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_coverage_plan(**kwargs).as_meta()


def complete_focus_items(plan: CompleteCoveragePlan | None) -> Tuple[CompleteFocusItem, ...]:
    if isinstance(plan, CompleteCoveragePlan):
        return tuple(plan.focus_items)
    return tuple()


CompleteFocusSelection = CompleteCoveragePlan
CoveragePlan = CompleteCoveragePlan
FocusSelectorResult = CompleteCoveragePlan

__all__ = [
    "COMPLETE_COVERAGE_PLAN_SCHEMA_VERSION",
    "COMPLETE_COVERAGE_PLAN_STAGE",
    "COMPLETE_FOCUS_ITEM_SCHEMA_VERSION",
    "COMPLETE_FOCUS_REJECTION_SCHEMA_VERSION",
    "COMPLETE_FOCUS_SELECTOR_IMPLEMENTATION_UNIT",
    "COMPLETE_FOCUS_SELECTOR_STAGE",
    "COMPLETE_FOCUS_SELECTOR_STEP",
    "COMPLETE_FOCUS_SELECTOR_VERSION",
    "COMPLETE_FOCUS_STATUS_READY",
    "COMPLETE_FOCUS_STATUS_UNAVAILABLE",
    "COVERAGE_POLICIES",
    "CoveragePlan",
    "CoveragePolicy",
    "CompleteCoveragePlan",
    "CompleteFocusItem",
    "CompleteFocusRejection",
    "CompleteFocusSelection",
    "FocusSelectorResult",
    "build_complete_coverage_plan",
    "build_complete_coverage_plan_meta",
    "build_complete_focus_selection",
    "build_complete_focus_selector_contract_meta",
    "build_complete_focus_selector_meta",
    "complete_focus_items",
    "select_complete_focus",
]
