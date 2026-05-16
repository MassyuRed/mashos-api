# -*- coding: utf-8 -*-
from __future__ import annotations

"""Product-quality Tone Engine for EmlisAI Complete Composer.

The Tone Engine is a constraint layer for SentencePlan -> Surface Realizer.
It does not decorate an already finished observation, does not add meaning, and
never writes the public ``input_feedback.comment_text`` key.  Its job is to keep
Emlis' observation distance stable: not too close, not cold, not diagnostic, not
advice-like, and not generic comfort.
"""

from dataclasses import dataclass, field as dataclass_field, is_dataclass, asdict
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_limited_relation_taxonomy import canonical_relation_type, normalize_relation_type, relation_family

COMPLETE_TONE_ENGINE_VERSION = "emlis.complete_tone_engine.v1"
COMPLETE_TONE_POLICY_VERSION = "emlis.complete_tone_policy.v1"
COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION = "emlis.complete_product_quality_tone_engine.v1"
COMPLETE_TONE_GUARD_REPORT_VERSION = "emlis.complete_tone_guard_report.v1"
COMPLETE_TONE_ENGINE_STAGE = "Step5_Tone_Engine"
COMPLETE_TONE_ENGINE_STEP = COMPLETE_TONE_ENGINE_STAGE
COMPLETE_TONE_ENGINE_IMPLEMENTATION_UNIT = "Step5_Tone_Engine"

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
    "surface_text",
    "realized_text",
    "comment_text",
}

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"

_TONE_GUARD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("too_close", re.compile(r"(?:ずっとそばに|抱きしめ|絶対味方|何があっても味方|全部受け止めます)")),
    ("cold_tone", re.compile(r"(?:関係ありません|ただの反応です|それだけです|終わりです|問題ありません)")),
    ("over_empathy", re.compile(r"(?:つらかったね|よく頑張った|もう大丈夫|必ず良く|安心してください|泣いていい)")),
    ("diagnostic_tone", re.compile(r"(?:診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|PTSD|心理学的|医学的)")),
    ("advice_like", re.compile(r"(?:してください|しましょう|するべき|しなければ|行動しましょう|正解は|まずは.+やってみ)")),
    ("generic_comfort", re.compile(r"(?:よくあること|誰でも|大丈夫です|一緒に見ます|小さく扱いません|軽く扱いません)")),
)

_COVERAGE_TONE_DEFAULTS: Mapping[str, Mapping[str, Any]] = {
    "short_daily": {
        "distance_policy_key": "near_observation_not_general_comfort",
        "temperature_key": "low_warm",
        "read_feeling_policy_key": "keep_small_residue_specific",
        "guard_keys": ("generic_comfort", "overclaim"),
    },
    "long_meaning_arc": {
        "distance_policy_key": "structured_observation_without_report_voice",
        "temperature_key": "steady_warm",
        "read_feeling_policy_key": "keep_core_and_residue",
        "guard_keys": ("flat_generic", "focus_drift", "diagnostic_tone"),
    },
    "conflict": {
        "distance_policy_key": "hold_both_sides_without_true_self_claim",
        "temperature_key": "balanced_warm",
        "read_feeling_policy_key": "show_coexistence_or_contrast",
        "guard_keys": ("one_side_true_self", "overclaim"),
    },
    "recovery": {
        "distance_policy_key": "warm_without_over_comfort",
        "temperature_key": "warm_low",
        "read_feeling_policy_key": "keep_prior_load_with_recovery",
        "guard_keys": ("over_empathy", "over_comfort", "generic_comfort"),
    },
    "pressure": {
        "distance_policy_key": "steady_near_observer_under_load",
        "temperature_key": "calm_low",
        "read_feeling_policy_key": "name_pressure_without_cause_claim",
        "guard_keys": ("diagnostic_tone", "cause_overclaim", "cold_tone"),
    },
    "desire_fear": {
        "distance_policy_key": "hold_approach_and_avoidance_without_advice",
        "temperature_key": "steady_warm",
        "read_feeling_policy_key": "keep_desire_and_fear_together",
        "guard_keys": ("advice_like", "action_instruction", "generic_comfort"),
    },
    "relationship": {
        "distance_policy_key": "user_side_relation_observation_without_blame",
        "temperature_key": "careful_neutral_warm",
        "read_feeling_policy_key": "keep_user_side_distance_or_residue",
        "guard_keys": ("personality_claim", "blame_overclaim", "diagnostic_tone"),
    },
}

_RELATION_TONE_OVERRIDES: Mapping[str, Mapping[str, Any]] = {
    "pressure": {
        "distance_policy_key": "steady_near_observer_under_load",
        "temperature_key": "calm_low",
        "guard_keys": ("diagnostic_tone", "cause_overclaim"),
    },
    "recovery": {
        "distance_policy_key": "warm_without_over_comfort",
        "temperature_key": "warm_low",
        "guard_keys": ("over_empathy", "generic_comfort"),
    },
    "approach_avoidance": {
        "distance_policy_key": "hold_approach_and_avoidance_without_advice",
        "temperature_key": "steady_warm",
        "guard_keys": ("advice_like", "action_instruction"),
    },
    "contrast": {
        "distance_policy_key": "hold_both_sides_without_true_self_claim",
        "temperature_key": "balanced_warm",
        "guard_keys": ("one_side_true_self", "overclaim"),
    },
    "coexistence": {
        "distance_policy_key": "hold_coexistence_without_simplifying",
        "temperature_key": "balanced_warm",
        "guard_keys": ("generic_comfort", "overclaim"),
    },
    "residue": {
        "distance_policy_key": "observe_residue_without_symptom_label",
        "temperature_key": "low_warm",
        "guard_keys": ("diagnostic_tone", "generic_comfort"),
    },
    "limit": {
        "distance_policy_key": "hold_limit_without_command",
        "temperature_key": "calm_low",
        "guard_keys": ("advice_like", "diagnostic_tone"),
    },
}

_LINE_ROLE_TONE: Mapping[str, Mapping[str, Any]] = {
    "opening": {
        "subject_policy_key": "omit_second_person_subject",
        "closing_policy_key": "none",
        "predicate_strength_key": "receive_as_observation",
        "ending_policy_key": "plain_observation",
    },
    "core": {
        "subject_policy_key": "omit_second_person_subject",
        "closing_policy_key": "none",
        "predicate_strength_key": "grounded_state",
        "ending_policy_key": "grounded_observation",
    },
    "relation": {
        "subject_policy_key": "omit_second_person_subject",
        "closing_policy_key": "none",
        "predicate_strength_key": "relation_not_decision",
        "ending_policy_key": "relation_observation",
    },
    "closing": {
        "subject_policy_key": "omit_second_person_subject",
        "closing_policy_key": "soft_observation_closing_no_instruction",
        "predicate_strength_key": "soft_close_without_instruction",
        "ending_policy_key": "quiet_observation_close",
    },
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _clean_token(value: Any) -> str:
    return re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")


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
    if is_dataclass(value):
        return _json_safe_value(asdict(value))
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


def _coverage_group(value: Any) -> str:
    group = _clean_token(value) or "short_daily"
    aliases = {
        "wish_fear": "desire_fear",
        "desire_and_fear": "desire_fear",
        "desire-fear": "desire_fear",
        "approach_avoidance": "desire_fear",
        "limit_escape": "pressure",
        "positive_recovery": "recovery",
        "history_cross_core": "long_meaning_arc",
    }
    return aliases.get(group, group)


def _relation(value: Any) -> str:
    relation = normalize_relation_type(value)
    return relation or "center"


def _plan_lines(sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None) -> tuple[CompleteSentencePlanLine, ...]:
    if isinstance(sentence_plan, CompleteSentencePlanV2):
        return tuple(sentence_plan.sentence_plans)
    if isinstance(sentence_plan, Mapping):
        plan = CompleteSentencePlanV2(
            plan_id=sentence_plan.get("plan_id") or "complete_sentence_plan_v2",
            sentence_budget=sentence_plan.get("sentence_budget") or 2,
            coverage_group=sentence_plan.get("coverage_group") or sentence_plan.get("coverage_scope") or "short_daily",
            sentence_plans=sentence_plan.get("sentence_plans") or sentence_plan.get("lines") or (),
            meta=sentence_plan.get("meta") or {},
        )
        return tuple(plan.sentence_plans)
    return tuple()


def _relations_from_plan(sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None, relation_types: Iterable[Any] | None = None) -> tuple[str, ...]:
    relations = [_relation(item) for item in list(relation_types or ())]
    for line in _plan_lines(sentence_plan):
        relations.append(_relation(line.relation_type))
    return tuple(dict.fromkeys(relations))


def _default_coverage_tone(group: str) -> dict[str, Any]:
    return dict(_COVERAGE_TONE_DEFAULTS.get(_coverage_group(group)) or _COVERAGE_TONE_DEFAULTS["short_daily"])


def _merge_constraint_base(group: str, relation_type: str, line_role: str) -> dict[str, Any]:
    coverage = _default_coverage_tone(group)
    relation_key = _relation(relation_type)
    relation = dict(_RELATION_TONE_OVERRIDES.get(relation_key) or _RELATION_TONE_OVERRIDES.get(canonical_relation_type(relation_key)) or {})
    role = dict(_LINE_ROLE_TONE.get(_clean_token(line_role) or "core") or _LINE_ROLE_TONE["core"])
    guard_keys = _dedupe([
        *list(coverage.get("guard_keys") or ()),
        *list(relation.get("guard_keys") or ()),
        "diagnostic_tone",
        "advice_like",
    ])
    payload = {
        **coverage,
        **relation,
        **role,
        "guard_keys": guard_keys,
        "relation_type": relation_key,
        "canonical_relation_type": canonical_relation_type(relation_key),
        "relation_family": relation_family(relation_key),
    }
    if _clean_token(line_role) == "closing":
        payload["guard_keys"] = _dedupe([*payload["guard_keys"], "over_empathy", "generic_comfort", "action_instruction"])
        payload["distance_policy_key"] = "soft_observation_closing_no_instruction"
        payload["temperature_key"] = "low_warm"
    return payload


@dataclass(frozen=True)
class CompleteToneLineConstraint:
    sentence_id: str
    line_role: str
    relation_type: str
    distance_policy_key: str
    temperature_key: str
    subject_policy_key: str = "omit_second_person_subject"
    predicate_strength_key: str = "grounded_state"
    ending_policy_key: str = "grounded_observation"
    closing_policy_key: str = "none"
    read_feeling_policy_key: str = "input_specific_structure_reflected"
    guard_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    version: str = COMPLETE_TONE_POLICY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "sentence_id", _clean_token(self.sentence_id))
        object.__setattr__(self, "line_role", _clean_token(self.line_role) or "core")
        object.__setattr__(self, "relation_type", _relation(self.relation_type))
        object.__setattr__(self, "distance_policy_key", _clean_token(self.distance_policy_key) or "observe_without_overclaim")
        object.__setattr__(self, "temperature_key", _clean_token(self.temperature_key) or "steady_warm")
        object.__setattr__(self, "subject_policy_key", _clean_token(self.subject_policy_key) or "omit_second_person_subject")
        object.__setattr__(self, "predicate_strength_key", _clean_token(self.predicate_strength_key) or "grounded_state")
        object.__setattr__(self, "ending_policy_key", _clean_token(self.ending_policy_key) or "grounded_observation")
        object.__setattr__(self, "closing_policy_key", _clean_token(self.closing_policy_key) or "none")
        object.__setattr__(self, "read_feeling_policy_key", _clean_token(self.read_feeling_policy_key) or "input_specific_structure_reflected")
        object.__setattr__(self, "guard_keys", _dedupe(self.guard_keys))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "version", _clean(self.version) or COMPLETE_TONE_POLICY_VERSION)

    @property
    def non_diagnostic(self) -> bool:
        return True

    @property
    def non_advice(self) -> bool:
        return True

    @property
    def meaning_added(self) -> bool:
        return False

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "sentence_id": self.sentence_id,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "canonical_relation_type": canonical_relation_type(self.relation_type),
            "relation_family": relation_family(self.relation_type),
            "distance_policy_key": self.distance_policy_key,
            "temperature_key": self.temperature_key,
            "subject_policy_key": self.subject_policy_key,
            "predicate_strength_key": self.predicate_strength_key,
            "ending_policy_key": self.ending_policy_key,
            "closing_policy_key": self.closing_policy_key,
            "read_feeling_policy_key": self.read_feeling_policy_key,
            "guard_keys": list(self.guard_keys),
            "non_diagnostic": True,
            "non_advice": True,
            "over_empathy_guard_enabled": True,
            "generic_comfort_guard_enabled": True,
            "meaning_added": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class CompleteTonePolicy:
    coverage_group: str = "short_daily"
    relation_types: Iterable[str] = dataclass_field(default_factory=tuple)
    line_constraints: Iterable[CompleteToneLineConstraint | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    version: str = COMPLETE_TONE_POLICY_VERSION

    def __post_init__(self) -> None:
        group = _coverage_group(self.coverage_group)
        relations = tuple(_relation(item) for item in tuple(self.relation_types or ())) or ("center",)
        constraints: list[CompleteToneLineConstraint] = []
        for item in tuple(self.line_constraints or ()): 
            if isinstance(item, CompleteToneLineConstraint):
                constraints.append(item)
            elif isinstance(item, Mapping):
                constraints.append(
                    CompleteToneLineConstraint(
                        sentence_id=item.get("sentence_id") or "",
                        line_role=item.get("line_role") or "core",
                        relation_type=item.get("relation_type") or "center",
                        distance_policy_key=item.get("distance_policy_key") or "observe_without_overclaim",
                        temperature_key=item.get("temperature_key") or "steady_warm",
                        subject_policy_key=item.get("subject_policy_key") or "omit_second_person_subject",
                        predicate_strength_key=item.get("predicate_strength_key") or "grounded_state",
                        ending_policy_key=item.get("ending_policy_key") or "grounded_observation",
                        closing_policy_key=item.get("closing_policy_key") or "none",
                        read_feeling_policy_key=item.get("read_feeling_policy_key") or "input_specific_structure_reflected",
                        guard_keys=item.get("guard_keys") or (),
                        meta=item.get("meta") or {},
                    )
                )
        object.__setattr__(self, "coverage_group", group)
        object.__setattr__(self, "relation_types", tuple(dict.fromkeys(relations)))
        object.__setattr__(self, "line_constraints", tuple(constraints))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "version", _clean(self.version) or COMPLETE_TONE_POLICY_VERSION)

    @property
    def guard_keys(self) -> Tuple[str, ...]:
        return _dedupe(key for line in self.line_constraints for key in line.guard_keys)

    @property
    def tone_guard_enabled(self) -> bool:
        return True

    @property
    def meaning_added(self) -> bool:
        return False

    def constraint_for(self, *, sentence_id: Any = "", line_role: Any = "core", relation_type: Any = "center") -> CompleteToneLineConstraint:
        sid = _clean_token(sentence_id)
        role = _clean_token(line_role) or "core"
        relation = _relation(relation_type)
        for constraint in self.line_constraints:
            if sid and constraint.sentence_id == sid:
                return constraint
        base = _merge_constraint_base(self.coverage_group, relation, role)
        return CompleteToneLineConstraint(
            sentence_id=sid or f"tone_{role}",
            line_role=role,
            relation_type=relation,
            distance_policy_key=base.get("distance_policy_key") or "observe_without_overclaim",
            temperature_key=base.get("temperature_key") or "steady_warm",
            subject_policy_key=base.get("subject_policy_key") or "omit_second_person_subject",
            predicate_strength_key=base.get("predicate_strength_key") or "grounded_state",
            ending_policy_key=base.get("ending_policy_key") or "grounded_observation",
            closing_policy_key=base.get("closing_policy_key") or "none",
            read_feeling_policy_key=base.get("read_feeling_policy_key") or "input_specific_structure_reflected",
            guard_keys=base.get("guard_keys") or (),
        )

    def as_meta(self) -> dict[str, Any]:
        term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
        return {
            "version": self.version,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "target_step": COMPLETE_TONE_ENGINE_STAGE,
            "step": COMPLETE_TONE_ENGINE_STAGE,
            "stage": "complete_composer_initial",
            "implementation_unit": COMPLETE_TONE_ENGINE_IMPLEMENTATION_UNIT,
            "target_composer_term": term_meta["target_composer_term"],
            "target_composer_family_term": term_meta["target_composer_family_term"],
            "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
            "coverage_group": self.coverage_group,
            "relation_types": list(self.relation_types),
            "distance_policy_enabled": True,
            "temperature_policy_enabled": True,
            "non_diagnostic_policy_enabled": True,
            "non_advice_policy_enabled": True,
            "read_feeling_policy_enabled": True,
            "closing_policy_enabled": True,
            "over_empathy_guard_enabled": True,
            "generic_comfort_guard_enabled": True,
            "tone_policy_applies_to_sentence_plan": True,
            "tone_is_surface_constraint_not_post_decoration": True,
            "meaning_added": False,
            "meaning_added_allowed": False,
            "line_constraint_count": len(tuple(self.line_constraints)),
            "line_constraints": [line.as_meta() for line in self.line_constraints],
            "guard_keys": list(self.guard_keys),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_key_written": False,
            "comment_text_contract": "passed_only",
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "fixed_sentence_template_used": False,
            "meta": dict(self.meta),
        }


def build_complete_tone_policy_contract_meta() -> dict[str, Any]:
    return {
        **CompleteTonePolicy().as_meta(),
        "tone_engine_added": True,
        "tone_policy_added": True,
        "product_quality_step": COMPLETE_TONE_ENGINE_STAGE,
        "distance_policy_added": True,
        "temperature_policy_added": True,
        "non_diagnostic_policy_added": True,
        "non_advice_policy_added": True,
        "read_feeling_policy_added": True,
        "closing_policy_added": True,
        "over_empathy_guard_added": True,
        "flat_generic_guard_added": True,
        "surface_realizer_constraint": True,
        "post_gate_decoration": False,
        "fixed_comfort_sentence_added": False,
    }


def build_complete_tone_policy(
    *,
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    coverage_group: str = "",
    relation_types: Iterable[Any] | None = None,
    meta: Mapping[str, Any] | None = None,
) -> CompleteTonePolicy:
    plan_lines = _plan_lines(sentence_plan)
    group = _coverage_group(coverage_group or (getattr(sentence_plan, "coverage_group", "") if sentence_plan is not None else ""))
    if not group and isinstance(sentence_plan, Mapping):
        group = _coverage_group(sentence_plan.get("coverage_group") or sentence_plan.get("coverage_scope"))
    relations = _relations_from_plan(sentence_plan, relation_types)
    constraints: list[CompleteToneLineConstraint] = []
    for line in plan_lines:
        relation = _relation(line.relation_type)
        base = _merge_constraint_base(group, relation, line.line_role)
        constraints.append(
            CompleteToneLineConstraint(
                sentence_id=line.sentence_id,
                line_role=line.line_role,
                relation_type=relation,
                distance_policy_key=base.get("distance_policy_key") or "observe_without_overclaim",
                temperature_key=base.get("temperature_key") or "steady_warm",
                subject_policy_key=base.get("subject_policy_key") or "omit_second_person_subject",
                predicate_strength_key=base.get("predicate_strength_key") or "grounded_state",
                ending_policy_key=base.get("ending_policy_key") or "grounded_observation",
                closing_policy_key=base.get("closing_policy_key") or "none",
                read_feeling_policy_key=base.get("read_feeling_policy_key") or "input_specific_structure_reflected",
                guard_keys=base.get("guard_keys") or (),
                meta={
                    "source_sentence_plan_line_id": line.sentence_id,
                    "surface_intent": line.surface_intent,
                    "raw_input_included": False,
                },
            )
        )
    if not constraints:
        relation = next(iter(relations), "center")
        base = _merge_constraint_base(group, relation, "core")
        constraints.append(
            CompleteToneLineConstraint(
                sentence_id="tone_core",
                line_role="core",
                relation_type=relation,
                distance_policy_key=base.get("distance_policy_key") or "observe_without_overclaim",
                temperature_key=base.get("temperature_key") or "steady_warm",
                guard_keys=base.get("guard_keys") or (),
            )
        )
    return CompleteTonePolicy(
        coverage_group=group,
        relation_types=relations,
        line_constraints=constraints,
        meta={
            **_json_safe_mapping(meta),
            "source_step": "SentencePlan_to_Surface_Realizer",
            "target_step": COMPLETE_TONE_ENGINE_STAGE,
            "raw_input_included": False,
        },
    )


def coerce_complete_tone_policy(value: CompleteTonePolicy | Mapping[str, Any] | None, *, sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None, coverage_group: str = "") -> CompleteTonePolicy:
    if isinstance(value, CompleteTonePolicy):
        return value
    if isinstance(value, Mapping) and value.get("line_constraints"):
        return CompleteTonePolicy(
            coverage_group=value.get("coverage_group") or coverage_group,
            relation_types=value.get("relation_types") or (),
            line_constraints=value.get("line_constraints") or (),
            meta=value.get("meta") or {},
            version=value.get("version") or COMPLETE_TONE_POLICY_VERSION,
        )
    return build_complete_tone_policy(sentence_plan=sentence_plan, coverage_group=coverage_group)


def _surface_rows(surface_realization: Any = None, *, comment_text: Any = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if surface_realization is not None and hasattr(surface_realization, "surface_lines"):
        for line in list(getattr(surface_realization, "surface_lines", []) or []):
            rows.append(
                {
                    "sentence_id": _clean(getattr(line, "sentence_id", "")),
                    "line_role": _clean(getattr(line, "line_role", "")),
                    "surface_text": _clean(getattr(line, "surface_text", "")),
                    "tone_guard_keys": list(getattr(line, "tone_guard_keys", []) or ()),
                    "tone_policy_key": _clean(getattr(line, "tone_policy_key", "")),
                }
            )
    elif isinstance(surface_realization, Mapping):
        for item in list(surface_realization.get("surface_lines") or surface_realization.get("surface_component_rows") or ()): 
            if isinstance(item, Mapping):
                rows.append(
                    {
                        "sentence_id": _clean(item.get("sentence_id")),
                        "line_role": _clean(item.get("line_role")),
                        "surface_text": _clean(item.get("surface_text")),
                        "tone_guard_keys": list(item.get("tone_guard_keys") or ()),
                        "tone_policy_key": _clean(item.get("tone_policy_key")),
                    }
                )
    text = _clean(comment_text)
    if text and not rows:
        rows.append({"sentence_id": "text", "line_role": "unknown", "surface_text": text, "tone_guard_keys": [], "tone_policy_key": ""})
    return rows


def build_complete_tone_guard_report(
    *,
    comment_text: Any = "",
    surface_realization: Any = None,
    tone_policy: CompleteTonePolicy | Mapping[str, Any] | None = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = coerce_complete_tone_policy(tone_policy, coverage_group=(composer_meta or {}).get("coverage_group", "") if isinstance(composer_meta, Mapping) else "")
    rows = _surface_rows(surface_realization, comment_text=comment_text)
    if not rows and isinstance(composer_meta, Mapping):
        surface = composer_meta.get("surface_realizer")
        if isinstance(surface, Mapping):
            rows = _surface_rows(surface)
    hits: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        text = _clean(row.get("surface_text"))
        if not text:
            continue
        for reason, pattern in _TONE_GUARD_PATTERNS:
            if pattern.search(text):
                hits.append(
                    {
                        "sentence_id": row.get("sentence_id") or f"s{index}",
                        "line_role": row.get("line_role") or "unknown",
                        "reason": reason,
                        "tone_policy_key": row.get("tone_policy_key") or "",
                    }
                )
    reason_counts: dict[str, int] = {}
    for hit in hits:
        reason = _clean_token(hit.get("reason"))
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    blocker_reasons = list(reason_counts.keys())
    return {
        "version": COMPLETE_TONE_GUARD_REPORT_VERSION,
        "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
        "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
        "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "target_step": COMPLETE_TONE_ENGINE_STAGE,
        "coverage_group": policy.coverage_group,
        "relation_types": list(policy.relation_types),
        "tone_guard_enabled": True,
        "tone_policy_applied": True,
        "line_count": len(rows),
        "guarded_sentence_ids": [row.get("sentence_id") for row in rows if row.get("sentence_id")],
        "tone_guard_major_count": len(hits),
        "tone_guard_hit_count": len(hits),
        "tone_guard_hits": hits,
        "tone_guard_reasons": blocker_reasons,
        "tone_reason_counts": reason_counts,
        "too_close_count": reason_counts.get("too_close", 0),
        "cold_tone_count": reason_counts.get("cold_tone", 0),
        "over_empathy_count": reason_counts.get("over_empathy", 0),
        "diagnostic_tone_count": reason_counts.get("diagnostic_tone", 0),
        "advice_like_count": reason_counts.get("advice_like", 0),
        "generic_comfort_count": reason_counts.get("generic_comfort", 0),
        "too_close_guard_passed": reason_counts.get("too_close", 0) == 0,
        "cold_tone_guard_passed": reason_counts.get("cold_tone", 0) == 0,
        "over_empathy_guard_passed": reason_counts.get("over_empathy", 0) == 0,
        "diagnostic_tone_guard_passed": reason_counts.get("diagnostic_tone", 0) == 0,
        "advice_like_guard_passed": reason_counts.get("advice_like", 0) == 0,
        "generic_comfort_guard_passed": reason_counts.get("generic_comfort", 0) == 0,
        "passed": not bool(hits),
        "release_blocker": bool(hits),
        "blocker_reasons": blocker_reasons,
        "meaning_added": False,
        "meaning_added_by_tone_policy": False,
        "post_gate_decoration": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_key_written": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
    }


def build_complete_tone_policy_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_tone_policy(**kwargs).as_meta()


__all__ = [
    "COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION",
    "COMPLETE_TONE_ENGINE_IMPLEMENTATION_UNIT",
    "COMPLETE_TONE_ENGINE_STAGE",
    "COMPLETE_TONE_ENGINE_STEP",
    "COMPLETE_TONE_ENGINE_VERSION",
    "COMPLETE_TONE_GUARD_REPORT_VERSION",
    "COMPLETE_TONE_POLICY_VERSION",
    "CompleteToneLineConstraint",
    "CompleteTonePolicy",
    "build_complete_tone_guard_report",
    "build_complete_tone_policy",
    "build_complete_tone_policy_contract_meta",
    "build_complete_tone_policy_meta",
    "coerce_complete_tone_policy",
]
