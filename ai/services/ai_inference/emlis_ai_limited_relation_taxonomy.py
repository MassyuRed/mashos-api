# -*- coding: utf-8 -*-
from __future__ import annotations

"""Relation taxonomy for the EmlisAI limited Composer extension.

Step 5 adds a structural relation contract.  It is meta-only: the taxonomy
classifies sentence-plan / sentence-binding relation types so later Reader and
Grounding steps can reason about them without relying on fixed user-facing
sentences or input-specific templates.
"""

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

LIMITED_RELATION_TAXONOMY_VERSION = "emlis.relation_taxonomy.limited.v1"
LIMITED_RELATION_TAXONOMY_TARGET_STEP = "5_relation_taxonomy_addition"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


@dataclass(frozen=True)
class LimitedRelationDefinition:
    relation_type: str
    canonical_type: str
    family: str
    purpose: str
    typical_line_roles: tuple[str, ...] = ()
    role_hints: tuple[str, ...] = ()
    surface_signal_hints: tuple[str, ...] = ()

    def as_meta(self) -> dict[str, Any]:
        return {
            "relation_type": self.relation_type,
            "canonical_type": self.canonical_type,
            "family": self.family,
            "purpose": self.purpose,
            "typical_line_roles": list(self.typical_line_roles),
            "role_hints": list(self.role_hints),
            "surface_signal_hints": list(self.surface_signal_hints),
        }


# Values here are relation labels and developer-facing hints only.  They are not
# completed output sentences and must not be used as user-facing templates.
_RELATION_DEFINITIONS: dict[str, LimitedRelationDefinition] = {
    "center": LimitedRelationDefinition(
        "center",
        "center",
        "focus",
        "The first body sentence states the current observation focus.",
        typical_line_roles=("current_input_core", "state"),
        surface_signal_hints=("center",),
    ),
    "surface": LimitedRelationDefinition(
        "surface",
        "surface",
        "surface_emotion",
        "A visible reaction or surface emotion is placed first without diagnosis.",
        typical_line_roles=("receive",),
        role_hints=("anger_surface",),
        surface_signal_hints=("surface_visible", "front"),
    ),
    "value": LimitedRelationDefinition(
        "value",
        "value",
        "wish_or_value",
        "A value, wish, or intention is shown as a grounded observation.",
        typical_line_roles=("value", "approach"),
        role_hints=("value_wish", "wish_to_rely"),
        surface_signal_hints=("worded", "front"),
    ),
    "pressure": LimitedRelationDefinition(
        "pressure",
        "pressure",
        "pressure_or_load",
        "Load, fatigue, loop, or pressure is treated as a relation type.",
        typical_line_roles=("fatigue", "loop", "state", "tension"),
        role_hints=("fatigue_accumulation", "loss_of_control", "anticipation_loop"),
        surface_signal_hints=("strong_remain", "continue"),
    ),
    "coexistence": LimitedRelationDefinition(
        "coexistence",
        "coexistence",
        "coexisting_states",
        "Two grounded materials are present together without forcing a conclusion.",
        typical_line_roles=("control", "fear", "pressure", "tension_detail", "contrast_detail"),
        role_hints=("known_action", "perfection_fear", "burden_fear", "rejection_fear", "loss_of_control"),
        surface_signal_hints=("mixed", "stack", "parallel", "remain", "visible"),
    ),
    "contrast": LimitedRelationDefinition(
        "contrast",
        "contrast",
        "contrast_or_shift",
        "A shift, drop, or difference between grounded materials is expressed.",
        typical_line_roles=("contrast",),
        role_hints=("anxiety_return", "reality_damage", "fall_contrast"),
        surface_signal_hints=("return", "impact", "stack"),
    ),
    "tension": LimitedRelationDefinition(
        "tension",
        "tension",
        "internal_tension",
        "Wish, fear, limit, and reality are held as tension without diagnosing.",
        typical_line_roles=("tension",),
        role_hints=("ordinary_life_wish", "worsening_risk", "value_wish", "avoidance_wish"),
        surface_signal_hints=("tension", "co_remain"),
    ),
    "approach": LimitedRelationDefinition(
        "approach",
        "approach",
        "approach_wish",
        "A movement toward relying, consulting, or naming a wish is grounded.",
        typical_line_roles=("approach",),
        role_hints=("wish_to_rely",),
        surface_signal_hints=("worded", "front"),
    ),
    "approach_avoidance": LimitedRelationDefinition(
        "approach_avoidance",
        "approach_avoidance",
        "approach_avoidance",
        "Approach and avoidance are both preserved as a relation, not collapsed.",
        typical_line_roles=("tension",),
        role_hints=("wish_to_rely", "burden_fear", "rejection_fear"),
        surface_signal_hints=("stack", "visible"),
    ),
    "limit": LimitedRelationDefinition(
        "limit",
        "limit",
        "limit_or_boundary",
        "Limit, escape wish, or boundary pressure is carried as a relation.",
        typical_line_roles=("limit", "escape"),
        role_hints=("limit", "avoidance_wish"),
        surface_signal_hints=("limit_arrived", "remain", "exists"),
    ),
    "distance": LimitedRelationDefinition(
        "distance",
        "distance",
        "distance_or_withdrawal",
        "Withdrawal or distance is represented without adding motive.",
        typical_line_roles=("distance",),
        role_hints=("withdrawal",),
        surface_signal_hints=("written", "continue"),
    ),
    "context": LimitedRelationDefinition(
        "context",
        "context",
        "contextual_awareness",
        "Known context or self-awareness is attached to another relation.",
        typical_line_roles=("context", "detail"),
        role_hints=("known_action",),
        surface_signal_hints=("visible", "stack", "remain"),
    ),
    "progress": LimitedRelationDefinition(
        "progress",
        "recovery",
        "recovery_or_progress",
        "A small action, relief, or progress signal is handled as recovery/progress.",
        typical_line_roles=("progress", "progress_detail", "repair"),
        role_hints=("small_action", "achievement", "relieved_weight", "small_repair", "positive_state"),
        surface_signal_hints=("progress_shape", "visible", "continue"),
    ),
    "sequence": LimitedRelationDefinition(
        "sequence",
        "recovery",
        "recovery_or_progress",
        "A later grounded material follows an earlier one without fixed story completion.",
        typical_line_roles=("receive", "repair", "progress_detail"),
        role_hints=("small_repair", "small_action", "positive_state"),
        surface_signal_hints=("continue", "visible", "progress_shape"),
    ),
    "continuation": LimitedRelationDefinition(
        "continuation",
        "recovery",
        "recovery_or_progress",
        "The shallow path keeps a following grounded material connected.",
        typical_line_roles=("current_input_core",),
        role_hints=("small_repair", "positive_state"),
        surface_signal_hints=("continue", "visible", "remain"),
    ),
    "recovery": LimitedRelationDefinition(
        "recovery",
        "recovery",
        "recovery_or_progress",
        "A recovery signal is explicit as a structural relation type.",
        typical_line_roles=("repair", "progress_detail"),
        role_hints=("small_repair", "small_action", "relieved_weight", "achievement", "positive_state"),
        surface_signal_hints=("progress_shape", "visible", "continue"),
    ),
    "residue": LimitedRelationDefinition(
        "residue",
        "residue",
        "residue_or_aftereffect",
        "A remaining feeling or aftereffect is preserved without over-explaining.",
        typical_line_roles=("contrast_detail", "detail"),
        role_hints=("fall_contrast", "anxiety_return"),
        surface_signal_hints=("remain",),
    ),
    "candidate_used_phrase_unit": LimitedRelationDefinition(
        "candidate_used_phrase_unit",
        "candidate_used_phrase_unit",
        "core_adapter_plan",
        "Common Core adapter plan for already used phrase units.",
        typical_line_roles=("candidate_line",),
    ),
}

_PROFILE_RELATION_FAMILY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "mixed_positive_anxiety": ("recovery_or_progress", "contrast_or_shift"),
    "anger_hurt_boundary": ("surface_emotion", "contrast_or_shift"),
    "self_understanding_loop": ("pressure_or_load", "coexisting_states"),
    "positive_progress": ("recovery_or_progress",),
    "relationship_approach_avoidance": ("approach_wish", "approach_avoidance", "limit_or_boundary"),
    "reality_escape_tension": ("recovery_or_progress", "contrast_or_shift", "internal_tension"),
    "energy_fatigue": ("pressure_or_load", "coexisting_states"),
    "anxiety_anticipation": ("pressure_or_load", "coexisting_states"),
    "value_wish": ("wish_or_value", "coexisting_states"),
    "long_meaning_arc": ("pressure_or_load", "internal_tension"),
    "current_input_core": ("focus",),
}

_PROFILE_COVERAGE_GROUPS: dict[str, str] = {
    "mixed_positive_anxiety": "positive_anxiety_contrast",
    "anger_hurt_boundary": "anger_hurt_boundary",
    "self_understanding_loop": "anticipation_perfection_loop",
    "positive_progress": "positive_progress_recovery",
    "relationship_approach_avoidance": "relationship_approach_avoidance",
    "reality_escape_tension": "reality_escape_tension",
    "energy_fatigue": "energy_fatigue_pressure",
    "anxiety_anticipation": "anxiety_anticipation_loop",
    "value_wish": "value_wish_pressure",
    "long_meaning_arc": "long_meaning_arc",
    "current_input_core": "current_input_core",
}

_ROLE_DEFAULT_RELATIONS: tuple[tuple[set[str], str], ...] = (
    ({"wish_to_rely", "burden_fear", "rejection_fear"}, "approach_avoidance"),
    ({"value_wish", "loss_of_control"}, "coexistence"),
    ({"fatigue_accumulation", "loss_of_control", "anticipation_loop"}, "pressure"),
    ({"safe_home", "reality_damage"}, "contrast"),
    ({"ordinary_life_wish", "worsening_risk", "avoidance_wish"}, "tension"),
    ({"small_repair", "small_action", "relieved_weight", "achievement", "positive_state"}, "recovery"),
    ({"limit"}, "limit"),
    ({"known_action", "perfection_fear"}, "coexistence"),
)


def relation_definition(relation_type: Any) -> LimitedRelationDefinition | None:
    return _RELATION_DEFINITIONS.get(_clean(relation_type))


def allowed_relation_types() -> tuple[str, ...]:
    return tuple(_RELATION_DEFINITIONS.keys())


def canonical_relation_type(relation_type: Any) -> str:
    definition = relation_definition(relation_type)
    if definition is not None:
        return definition.canonical_type
    return _clean(relation_type)


def relation_family(relation_type: Any) -> str:
    definition = relation_definition(relation_type)
    if definition is not None:
        return definition.family
    return "unmapped"


def infer_relation_type_from_roles(roles: Iterable[Any] | None) -> str:
    role_set = set(_dedupe(roles or ()))
    if not role_set:
        return ""
    for required_roles, relation in _ROLE_DEFAULT_RELATIONS:
        if role_set.intersection(required_roles):
            return relation
    return "coexistence"


def normalize_relation_type(relation_type: Any, *, roles: Iterable[Any] | None = None, line_role: Any = "") -> str:
    relation = _clean(relation_type)
    if relation and relation in _RELATION_DEFINITIONS:
        return relation
    if relation in {"", "observation", "unknown"}:
        inferred = infer_relation_type_from_roles(roles)
        if inferred:
            return inferred
        line = _clean(line_role)
        if line in {"progress", "progress_detail", "repair"}:
            return "recovery"
        if line in {"tension", "fear"}:
            return "coexistence"
        if line in {"contrast", "contrast_detail"}:
            return "contrast"
        if line in {"limit", "escape"}:
            return "limit"
        return "coexistence"
    return relation


def _unit_role(unit: Any) -> str:
    return _clean(_mapping_get(unit, "role", ""))


def _unit_id(unit: Any) -> str:
    return _clean(_mapping_get(unit, "phrase_unit_id", ""))


def _plan_relation(plan: Any) -> str:
    return _clean(_mapping_get(plan, "relation_type", ""))


def _plan_line_role(plan: Any) -> str:
    return _clean(_mapping_get(plan, "line_role", ""))


def _plan_phrase_ids(plan: Any) -> list[str]:
    return _dedupe(_mapping_get(plan, "phrase_unit_ids", ()))


def _binding_relation(binding: Any) -> str:
    return _clean(_mapping_get(binding, "relation_type", _mapping_get(binding, "relation", "")))


def _binding_line_role(binding: Any) -> str:
    return _clean(_mapping_get(binding, "line_role", _mapping_get(binding, "role", "")))


def _binding_phrase_ids(binding: Any) -> list[str]:
    return _dedupe(_mapping_get(binding, "used_phrase_unit_ids", _mapping_get(binding, "phrase_unit_ids", ())))


def _binding_sentence_id(binding: Any, index: int) -> str:
    return _clean(_mapping_get(binding, "sentence_id", _mapping_get(binding, "id", f"s{index}"))) or f"s{index}"


def _roles_for_ids(phrase_unit_ids: Sequence[str], phrase_units: Sequence[Any]) -> list[str]:
    by_id = {_unit_id(unit): unit for unit in phrase_units if _unit_id(unit)}
    return _dedupe(_unit_role(by_id[unit_id]) for unit_id in phrase_unit_ids if unit_id in by_id)


def _planned_relation_rows(sentence_plans: Sequence[Any], phrase_units: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate(sentence_plans or (), start=1):
        phrase_ids = _plan_phrase_ids(plan)
        roles = _roles_for_ids(phrase_ids, phrase_units)
        relation = normalize_relation_type(_plan_relation(plan), roles=roles, line_role=_plan_line_role(plan))
        definition = relation_definition(relation)
        rows.append(
            {
                "plan_index": index,
                "line_role": _plan_line_role(plan),
                "relation_type": relation,
                "canonical_relation_type": canonical_relation_type(relation),
                "relation_family": relation_family(relation),
                "known_relation_type": bool(definition is not None),
                "phrase_unit_ids": phrase_ids,
                "role_hints": roles,
            }
        )
    return rows


def _binding_relation_rows(sentence_bindings: Sequence[Any], phrase_units: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, binding in enumerate(sentence_bindings or (), start=1):
        phrase_ids = _binding_phrase_ids(binding)
        roles = _roles_for_ids(phrase_ids, phrase_units)
        relation = normalize_relation_type(_binding_relation(binding), roles=roles, line_role=_binding_line_role(binding))
        definition = relation_definition(relation)
        rows.append(
            {
                "sentence_id": _binding_sentence_id(binding, index),
                "line_role": _binding_line_role(binding),
                "relation_type": relation,
                "canonical_relation_type": canonical_relation_type(relation),
                "relation_family": relation_family(relation),
                "known_relation_type": bool(definition is not None),
                "used_phrase_unit_ids": phrase_ids,
                "role_hints": roles,
                "raw_text_included": False,
            }
        )
    return rows


def build_limited_relation_taxonomy_meta(
    *,
    profile_key: str = "",
    coverage_scope: str = "",
    sentence_plans: Sequence[Any] | None = None,
    sentence_bindings: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    relation_types: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Build sanitized Step 5 relation-taxonomy meta.

    This returns structural labels and ids only. It never includes raw input and
    never creates user-facing text.
    """

    units = list(phrase_units or ())
    plans = list(sentence_plans or ())
    bindings = list(sentence_bindings or ())
    planned_rows = _planned_relation_rows(plans, units)
    binding_rows = _binding_relation_rows(bindings, units)
    explicit_relations = _dedupe(relation_types or ())
    all_relations = _dedupe(
        [row.get("relation_type") for row in planned_rows]
        + [row.get("relation_type") for row in binding_rows]
        + explicit_relations
    )
    normalized_relations = _dedupe(normalize_relation_type(relation) for relation in all_relations)
    canonical_relations = _dedupe(canonical_relation_type(relation) for relation in normalized_relations)
    relation_families = _dedupe(relation_family(relation) for relation in normalized_relations)
    unmapped = [relation for relation in normalized_relations if relation not in _RELATION_DEFINITIONS]
    profile = _clean(profile_key)
    expected_families = list(_PROFILE_RELATION_FAMILY_REQUIREMENTS.get(profile, ()))
    missing_expected = [family for family in expected_families if family not in relation_families]
    coverage_group = _PROFILE_COVERAGE_GROUPS.get(profile) or _clean(coverage_scope) or "unclassified"

    return {
        "version": LIMITED_RELATION_TAXONOMY_VERSION,
        "taxonomy_version": LIMITED_RELATION_TAXONOMY_VERSION,
        "target_step": LIMITED_RELATION_TAXONOMY_TARGET_STEP,
        "step": LIMITED_RELATION_TAXONOMY_TARGET_STEP,
        "relation_taxonomy_added": True,
        "relation_taxonomy_enabled": True,
        "relation_not_expressed_traceable": True,
        "relation_type_source": "sentence_plan_and_sentence_binding",
        "profile_key": profile,
        "coverage_scope": _clean(coverage_scope),
        "coverage_group": coverage_group,
        "allowed_relation_types": list(allowed_relation_types()),
        "required_major_relation_types": ["contrast", "coexistence", "pressure", "recovery", "approach_avoidance"],
        "relation_types": normalized_relations,
        "relation_count": len(normalized_relations),
        "canonical_relation_types": canonical_relations,
        "canonical_relation_count": len(canonical_relations),
        "relation_families": relation_families,
        "relation_family_count": len(relation_families),
        "expected_relation_families": expected_families,
        "missing_expected_relation_families": missing_expected,
        "unmapped_relation_types": unmapped,
        "all_relation_types_mapped": not bool(unmapped),
        "major_coverage_group_relation_unset": bool(not normalized_relations),
        "plan_relation_rows": planned_rows,
        "binding_relation_rows": binding_rows,
        "definition_rows": [definition.as_meta() for definition in _RELATION_DEFINITIONS.values()],
        "definition_count": len(_RELATION_DEFINITIONS),
        "taxonomy_is_structural": True,
        "surface_text_required": False,
        "reader_gate_relaxed": False,
        "display_gate_relaxed": False,
        "completion_sentence_templates_added": False,
        "input_specific_template_added": False,
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
    }


__all__ = [
    "LIMITED_RELATION_TAXONOMY_TARGET_STEP",
    "LIMITED_RELATION_TAXONOMY_VERSION",
    "LimitedRelationDefinition",
    "allowed_relation_types",
    "build_limited_relation_taxonomy_meta",
    "canonical_relation_type",
    "infer_relation_type_from_roles",
    "normalize_relation_type",
    "relation_definition",
    "relation_family",
]
