# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase16-2 TwoStage Section Surface Plan for EmlisAI.

This module converts the already-built state-answer Composer role plan into a
small, Complete Composer-friendly section plan.  It is internal material only:
it does not render completed reply text, it does not copy raw input text, and it
does not add public response keys.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final

EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis_two_stage.section_surface_plan.v1"
)
EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID: Final = (
    "emlis_two_stage_section_surface_plan"
)
EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_PHASE: Final = (
    "Phase16_two_stage_composer_surface_connection"
)
EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis_two_stage.section_budget_policy.v1"
)
EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SOURCE_PHASE: Final = (
    "Phase17_4_mode_section_budget_normalization"
)
EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION: Final = "cocolon.emlis.two_stage.mode_context.v1"
EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE: Final = "Phase18_product_quality_stabilization"
EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID: Final = "daily_unpleasant_reception"
EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RATIO_REASON: Final = "daily_unpleasant_reception_light"
EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL: Final = "見えたこと"
EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL: Final = "Emlisから"
EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE: Final = "labelled_two_stage_text"
EMLIS_TWO_STAGE_SECTION_ORDER: Final = ("observation", "reception")


_PUBLIC_CONTRACT_UNCHANGED: Final = {
    "public_response_key_added": False,
    "observation_text_public_response_key_added": False,
    "reception_text_public_response_key_added": False,
    "section_text_public_response_keys_added": False,
    "rn_visible_contract_changed": False,
    "db_physical_name_changed": False,
    "api_route_changed": False,
    "response_key_changed": False,
}

_MODE_SECTION_BUDGET_DEFAULT: Final = {
    "observation_min": 1,
    "observation_max": 1,
    "reception_min": 1,
    "reception_max": 2,
}

# Phase17-4: internal policy only. These are sentence-count boundaries for
# labelled two-stage product surfaces; they do not contain completed reply text
# and they do not add public response keys.
_MODE_SECTION_BUDGET_BY_MODE: Final = {
    "daily_unpleasant_reception": dict(_MODE_SECTION_BUDGET_DEFAULT),
    "self_denial_support": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "uncertainty_support": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "daily_positive_reception": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "self_understanding_follow": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "self_understanding_learning_shift": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 1,
        "reception_max": 1,
    },
    "relationship_gratitude_recovery": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "standard_state_answer": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "effort_support": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
}

# Phase18-5: some legacy/isolated builders pass only the resolved ratio reason
# even though the reception mode has already been determined upstream.  The
# section plan must not let that fall back to ``standard_state_answer`` because
# SurfaceRealizer dispatch is mode-specific and daily_unpleasant must stay in
# its own surface policy.  This map is internal material only; it does not carry
# raw input or completed reply text.
_RECEPTION_MODE_BY_RATIO_REASON: Final = {
    EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RATIO_REASON: EMLIS_TWO_STAGE_DAILY_UNPLEASANT_RECEPTION_MODE_ID,
    "self_understanding_learning_shift": "self_understanding_learning_shift",
    "relationship_end_gratitude_recovery": "relationship_gratitude_recovery",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _label(value: Any, *, default: str) -> str:
    text = _clean(value).rstrip("：:")
    return text or default


def _marker(label: str) -> str:
    return f"{label.rstrip('：:')}：" if label else ""


def _dedupe(values: Any) -> list[str]:
    if values is None:
        iterable: list[Any] = []
    elif isinstance(values, (str, bytes, bytearray)) or isinstance(values, Mapping):
        iterable = [values]
    else:
        try:
            iterable = list(values)
        except TypeError:
            iterable = [values]
    out: list[str] = []
    for value in iterable:
        text = _clean(value)
        if text and text not in out:
            out.append(text)
    return out


def _int_at_least(value: Any, *, minimum: int = 1, default: int = 1, maximum: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = int(default)
    number = max(int(minimum), number)
    if maximum is not None:
        number = min(int(maximum), number)
    return number


def _sequence_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _surface_contract_two_stage_labels(surface_contract: Mapping[str, Any]) -> Mapping[str, Any]:
    two_stage = _as_mapping(surface_contract.get("two_stage_reception"))
    return _as_mapping(two_stage.get("display_labels"))


def _display_labels(
    *,
    role_plan: Mapping[str, Any],
    surface_contract: Mapping[str, Any],
    composition_contract: Mapping[str, Any],
) -> dict[str, str]:
    role_labels = _as_mapping(role_plan.get("display_labels"))
    surface_labels = _surface_contract_two_stage_labels(surface_contract)
    observation = _label(
        composition_contract.get("observation_display_label")
        or role_plan.get("observation_display_label")
        or role_labels.get("observation")
        or surface_labels.get("observation"),
        default=EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL,
    )
    reception = _label(
        composition_contract.get("reception_display_label")
        or role_plan.get("reception_display_label")
        or role_labels.get("reception")
        or surface_labels.get("reception"),
        default=EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL,
    )
    return {"observation": observation, "reception": reception}


def _expected_comment_text_shape(
    *,
    role_plan: Mapping[str, Any],
    surface_contract: Mapping[str, Any],
    composition_contract: Mapping[str, Any],
) -> str:
    two_stage = _as_mapping(surface_contract.get("two_stage_reception"))
    return (
        _clean(composition_contract.get("expected_comment_text_shape"))
        or _clean(role_plan.get("expected_comment_text_shape"))
        or _clean(role_plan.get("comment_text_shape"))
        or _clean(two_stage.get("expected_comment_text_shape"))
        or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE
    )


def _required(
    *,
    role_plan: Mapping[str, Any],
    composition_contract: Mapping[str, Any],
    expected_shape: str,
) -> bool:
    return bool(
        role_plan.get("two_stage_display_required")
        or role_plan.get("two_stage_reception_surface_required")
        or role_plan.get("section_labels_required")
        or role_plan.get("joined_comment_text_required")
        or composition_contract.get("two_stage_reception_surface_required")
        or composition_contract.get("two_stage_display_required")
        or composition_contract.get("section_labels_required")
        or expected_shape == EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE
    )


def _section_order(role_plan: Mapping[str, Any], composition_contract: Mapping[str, Any]) -> list[str]:
    order = _dedupe(
        composition_contract.get("two_stage_section_order")
        or role_plan.get("section_id_order")
        or EMLIS_TWO_STAGE_SECTION_ORDER
    )
    return order if order == list(EMLIS_TWO_STAGE_SECTION_ORDER) else list(EMLIS_TWO_STAGE_SECTION_ORDER)


def _role_section_by_id(role_plan: Mapping[str, Any], section_id: str) -> Mapping[str, Any]:
    for section in _sequence_mappings(role_plan.get("sections")):
        if _clean(section.get("section_id")) == section_id:
            return section
    if section_id == "observation":
        for section in _sequence_mappings(role_plan.get("sections")):
            if _clean(section.get("section_role")) == "state_answer_observation":
                return section
    if section_id == "reception":
        for section in _sequence_mappings(role_plan.get("sections")):
            if _clean(section.get("reception_section_role")) == "emlis_reception":
                return section
        for section in _sequence_mappings(role_plan.get("sections")):
            if _clean(section.get("section_role")) in {"human_follow", "emlis_reception"}:
                return section
    return {}


def _ratio_reason(surface_contract: Mapping[str, Any], role_plan: Mapping[str, Any]) -> str:
    role_ratio = _as_mapping(role_plan.get("resolved_ratio"))
    surface_ratio_policy = _as_mapping(surface_contract.get("ratio_policy"))
    surface_resolved = _as_mapping(surface_ratio_policy.get("resolved_ratio"))
    return (
        _clean(role_ratio.get("reason"))
        or _clean(surface_resolved.get("reason"))
        or "standard_state_answer"
    )


def _reception_mode_info(
    surface_contract: Mapping[str, Any],
    role_plan: Mapping[str, Any],
    composition_contract: Mapping[str, Any],
) -> tuple[str, bool, str]:
    reception_mode = _as_mapping(surface_contract.get("reception_mode"))
    ratio_policy = _as_mapping(surface_contract.get("ratio_policy"))
    resolver_context = _as_mapping(ratio_policy.get("resolver_context"))
    candidates = (
        (composition_contract.get("reception_mode_id"), "composition_contract.reception_mode_id"),
        (reception_mode.get("reception_mode_id"), "surface_contract.reception_mode.reception_mode_id"),
        (reception_mode.get("mode_id"), "surface_contract.reception_mode.mode_id"),
        (resolver_context.get("reception_mode_id"), "surface_contract.ratio_policy.resolver_context.reception_mode_id"),
        (role_plan.get("selector_input_type"), "role_plan.selector_input_type"),
    )
    for value, source in candidates:
        mode_id = _clean(value)
        if mode_id:
            return mode_id, True, source
    ratio_reason = _ratio_reason(surface_contract, role_plan)
    mode_from_ratio = _RECEPTION_MODE_BY_RATIO_REASON.get(ratio_reason)
    if mode_from_ratio:
        return mode_from_ratio, True, "role_or_surface.resolved_ratio.reason"
    return "standard_state_answer", False, "fallback.standard_state_answer"


def _reception_mode_id(surface_contract: Mapping[str, Any], role_plan: Mapping[str, Any], composition_contract: Mapping[str, Any]) -> str:
    mode_id, _explicit, _source = _reception_mode_info(surface_contract, role_plan, composition_contract)
    return mode_id


def two_stage_mode_section_budget(reception_mode_id: Any) -> dict[str, int]:
    mode_id = _clean(reception_mode_id)
    budget = _MODE_SECTION_BUDGET_BY_MODE.get(mode_id) or _MODE_SECTION_BUDGET_DEFAULT
    return {key: int(value) for key, value in budget.items()}


def build_two_stage_section_budget_policy(
    reception_mode_id: Any,
    *,
    mode_explicit: bool = True,
    mode_source: str = "",
) -> dict[str, Any]:
    mode_id = _clean(reception_mode_id) or "standard_state_answer"
    budget = two_stage_mode_section_budget(mode_id)
    return {
        "schema_version": EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SCHEMA_VERSION,
        "source_phase": EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SOURCE_PHASE,
        "policy_id": "two_stage_mode_section_budget_policy",
        "supported": True,
        "applied": bool(mode_explicit),
        "mode_id": mode_id,
        "mode_explicit": bool(mode_explicit),
        "mode_source": _clean(mode_source) or "unknown",
        "selected_budget": dict(budget),
        "observation_min": budget["observation_min"],
        "observation_max": budget["observation_max"],
        "reception_min": budget["reception_min"],
        "reception_max": budget["reception_max"],
        "target_total_min": budget["observation_min"] + budget["reception_min"],
        "target_total_max": budget["observation_max"] + budget["reception_max"],
        "public_contract": dict(_PUBLIC_CONTRACT_UNCHANGED),
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "comment_text_generated": False,
        "completed_reply_template_used": False,
        "fixed_sentence_template_used": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
    }

def _observation_section_plan(
    *,
    role_section: Mapping[str, Any],
    labels: Mapping[str, str],
    expected_shape: str,
    reception_mode_id: str,
    ratio_reason: str,
    mode_context_source: str,
    section_budget: Mapping[str, int],
) -> dict[str, Any]:
    display_label = labels["observation"]
    sentence_units = _int_at_least(role_section.get("sentence_plan_unit_count"), default=1, minimum=1)
    observation_min = int(section_budget.get("observation_min", 1))
    observation_max = int(section_budget.get("observation_max", 1))
    return {
        "section_id": "observation",
        "section_role": _clean(role_section.get("section_role")) or "state_answer_observation",
        "display_label": display_label,
        "comment_text_section_label": _marker(display_label),
        "position": "front",
        "section_order_index": 0,
        "sentence_plan_unit_role": _clean(role_section.get("sentence_plan_unit_role")) or "observation_section",
        "sentence_plan_unit_count": sentence_units,
        "min_sentences": observation_min,
        "max_sentences": observation_max,
        "section_budget_min_sentences": observation_min,
        "section_budget_max_sentences": observation_max,
        "max_chars": _int_at_least(role_section.get("max_chars"), default=96, minimum=24),
        "claim_strength": _clean(role_section.get("claim_strength")) or "single_input_soft",
        "required_scope": "current_input_only",
        "must_ground_to_input": bool(role_section.get("must_ground_to_input", True)),
        "must_not_include_human_follow": bool(role_section.get("must_not_include_human_follow", True)),
        "must_not_include_new_observation_claim": False,
        "section_label_required": True,
        "two_stage_section_label_required": True,
        "expected_comment_text_shape": expected_shape,
        "reception_mode_id": reception_mode_id,
        "ratio_reason": ratio_reason,
        "mode_context_schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "mode_context_source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "mode_context_source": mode_context_source or "two_stage_section_surface_plan",
        "mode_context_propagated_to_sentence_line": True,
        "mode_context_propagated_to_surface_realizer": True,
        "coverage_group_only_mode_selection_used": False,
        "case_id_branch_used": False,
        "source_role_plan_section_role": _clean(role_section.get("section_role")) or "state_answer_observation",
        "source_step_ids": _dedupe(role_section.get("step_ids")),
        "source_span_ids": _dedupe(role_section.get("source_span_ids")),
        "must_not_read_as": _dedupe(
            role_section.get("must_not_read_as")
            or [
                "diagnosis",
                "personality_claim",
                "period_tendency",
                "cause_overclaim",
                "action_instruction",
            ]
        ),
        "allowed_surface_intents": [
            "brief_current_input_observation",
            "reaction_and_event_seen_without_over_explaining",
        ],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "completed_reply_template_used": False,
    }


def _reception_section_plan(
    *,
    role_section: Mapping[str, Any],
    labels: Mapping[str, str],
    expected_shape: str,
    reception_mode_id: str,
    ratio_reason: str,
    mode_context_source: str,
    section_budget: Mapping[str, int],
) -> dict[str, Any]:
    display_label = labels["reception"]
    reception_min = int(section_budget.get("reception_min", 1))
    reception_max = int(section_budget.get("reception_max", 2))
    sentence_units = max(
        _int_at_least(role_section.get("sentence_plan_unit_count"), default=2, minimum=1),
        reception_min,
    )
    follow_keys = _dedupe(
        [role_section.get("primary_follow_key")]
        + list(role_section.get("secondary_follow_keys") or [])
        + [role_section.get("afterglow_follow_key")]
    )
    return {
        "section_id": "reception",
        "section_role": _clean(role_section.get("reception_section_role")) or "emlis_reception",
        "source_role_plan_section_role": _clean(role_section.get("section_role")) or "human_follow",
        "display_label": display_label,
        "comment_text_section_label": _marker(display_label),
        "position": "back",
        "section_order_index": 1,
        "sentence_plan_unit_role": _clean(role_section.get("sentence_plan_unit_role")) or "human_follow_section",
        "sentence_plan_unit_count": sentence_units,
        "min_sentences": reception_min,
        "max_sentences": reception_max,
        "section_budget_min_sentences": reception_min,
        "section_budget_max_sentences": reception_max,
        "max_chars": _int_at_least(role_section.get("max_chars"), default=180, minimum=48),
        "follow_mode": _clean(role_section.get("follow_mode")) or "emlis_impression_not_fact",
        "must_ground_to_input": bool(role_section.get("must_ground_to_input", True)),
        "must_not_include_human_follow": False,
        "must_not_include_new_observation_claim": bool(role_section.get("must_not_include_new_observation_claim", True)),
        "target_judgement_agreement_allowed": bool(role_section.get("target_judgement_agreement_allowed", False)),
        "action_instruction_allowed": False,
        "section_label_required": True,
        "two_stage_section_label_required": True,
        "expected_comment_text_shape": expected_shape,
        "reception_mode_id": reception_mode_id,
        "ratio_reason": ratio_reason,
        "mode_context_schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "mode_context_source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "mode_context_source": mode_context_source or "two_stage_section_surface_plan",
        "mode_context_propagated_to_sentence_line": True,
        "mode_context_propagated_to_surface_realizer": True,
        "coverage_group_only_mode_selection_used": False,
        "case_id_branch_used": False,
        "allowed_tone_family": _clean(role_section.get("allowed_tone_family")) or "natural_short_reception",
        "primary_follow_key": _clean(role_section.get("primary_follow_key")),
        "secondary_follow_keys": _dedupe(role_section.get("secondary_follow_keys")),
        "afterglow_follow_key": _clean(role_section.get("afterglow_follow_key")),
        "follow_key_ids": follow_keys,
        "must_not_read_as": _dedupe(
            role_section.get("must_not_read_as")
            or ["diagnosis", "personality_claim", "cause_overclaim", "action_instruction"]
        ),
        "allowed_surface_intents": _dedupe(
            role_section.get("allowed_surface_intents")
            or follow_keys
            or [
                "explicit_reaction_receiving",
                "fear_or_load_understanding",
                "not_over_explaining_daily_event",
            ]
        ),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "completed_reply_template_used": False,
    }


def build_two_stage_section_surface_plan(
    state_answer_composer_role_plan: Mapping[str, Any] | None,
    state_answer_surface_contract: Mapping[str, Any] | None = None,
    composition_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Complete Composer-facing two-stage section material.

    The returned mapping is deliberately a plan, not a renderer.  It can tell the
    CompleteSentencePlanner/CompleteSurfaceRealizer which two sections must be
    carried, but it never includes completed section body text.
    """

    role_plan = _as_mapping(state_answer_composer_role_plan)
    if not role_plan:
        return {}
    surface_contract = _as_mapping(state_answer_surface_contract)
    composition = _as_mapping(composition_contract)
    expected_shape = _expected_comment_text_shape(
        role_plan=role_plan,
        surface_contract=surface_contract,
        composition_contract=composition,
    )
    required = _required(role_plan=role_plan, composition_contract=composition, expected_shape=expected_shape)
    if not required:
        return {}

    labels = _display_labels(
        role_plan=role_plan,
        surface_contract=surface_contract,
        composition_contract=composition,
    )
    reception_mode, reception_mode_explicit, reception_mode_source = _reception_mode_info(surface_contract, role_plan, composition)
    ratio_reason = _ratio_reason(surface_contract, role_plan)
    mode_context = {
        "schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "section_ids": list(EMLIS_TWO_STAGE_SECTION_ORDER),
        "reception_mode_id": reception_mode,
        "ratio_reason": ratio_reason,
        "mode_context_source": reception_mode_source or "two_stage_section_surface_plan",
        "mode_context_propagated_to_sentence_line": True,
        "mode_context_propagated_to_surface_realizer": True,
        "coverage_group_only_mode_selection_used": False,
        "case_id_branch_used": False,
        "public_contract": dict(_PUBLIC_CONTRACT_UNCHANGED),
        "comment_text_body_included": False,
        "raw_input_included": False,
        "public_response_key_added": False,
    }
    section_budget_policy = build_two_stage_section_budget_policy(
        reception_mode,
        mode_explicit=reception_mode_explicit,
        mode_source=reception_mode_source,
    )
    section_budget = two_stage_mode_section_budget(reception_mode)
    observation_role_section = _role_section_by_id(role_plan, "observation")
    reception_role_section = _role_section_by_id(role_plan, "reception")
    observation_section = _observation_section_plan(
        role_section=observation_role_section,
        labels=labels,
        expected_shape=expected_shape,
        reception_mode_id=reception_mode,
        ratio_reason=ratio_reason,
        mode_context_source=reception_mode_source,
        section_budget=section_budget,
    )
    reception_section = _reception_section_plan(
        role_section=reception_role_section,
        labels=labels,
        expected_shape=expected_shape,
        reception_mode_id=reception_mode,
        ratio_reason=ratio_reason,
        mode_context_source=reception_mode_source,
        section_budget=section_budget,
    )
    section_order = _section_order(role_plan, composition)

    return {
        "schema_version": EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION,
        "material_id": EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID,
        "source_phase": EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_PHASE,
        "phase": EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_PHASE,
        "enabled": True,
        "required": True,
        "state_answer_composer_role_plan_connected": True,
        "state_answer_surface_contract_connected": bool(surface_contract),
        "composition_contract_connected": bool(composition),
        "expected_comment_text_shape": expected_shape,
        "comment_text_shape": expected_shape,
        "display_labels": dict(labels),
        "comment_text_section_labels": {
            "observation": observation_section["comment_text_section_label"],
            "reception": reception_section["comment_text_section_label"],
        },
        "section_order": section_order,
        "section_id_order": section_order,
        "section_count": 2,
        "section_ids": ["observation", "reception"],
        "reception_mode_id": reception_mode,
        "reception_mode_explicit": reception_mode_explicit,
        "reception_mode_source": reception_mode_source,
        "ratio_reason": ratio_reason,
        "mode_context_schema_version": EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION,
        "mode_context_source_phase": EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE,
        "mode_context": mode_context,
        "mode_context_source": mode_context["mode_context_source"],
        "mode_context_propagated_to_sentence_line": True,
        "mode_context_propagated_to_surface_realizer": True,
        "coverage_group_only_mode_selection_used": False,
        "case_id_branch_used": False,
        "section_budget_policy_schema_version": EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SCHEMA_VERSION,
        "section_budget_policy_source_phase": EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SOURCE_PHASE,
        "section_budget_policy_supported": True,
        "section_budget_policy_applied": bool(section_budget_policy.get("applied")),
        "mode_section_budget": dict(section_budget),
        "section_budget_policy": section_budget_policy,
        "section_budget_public_contract": dict(_PUBLIC_CONTRACT_UNCHANGED),
        "section_budget_comment_text_body_included": False,
        "section_budget_raw_input_included": False,
        "section_budget_display_gate_relaxed": False,
        "section_budget_grounding_gate_relaxed": False,
        "surface_joiner": _clean(role_plan.get("surface_joiner")) or "comment_text_two_stage_joiner",
        "joined_comment_text_required": True,
        "section_labels_required": True,
        "observation_section_must_precede_reception_section": True,
        "observation_section_must_not_include_human_follow": True,
        "reception_section_must_not_include_new_observation_claim": True,
        "sentence_plan_unit_count_by_section": {
            "observation": observation_section["sentence_plan_unit_count"],
            "reception": reception_section["sentence_plan_unit_count"],
        },
        "sections": [observation_section, reception_section],
        "public_contract": dict(_PUBLIC_CONTRACT_UNCHANGED),
        "public_response_key_added": False,
        "observation_text_public_response_key_added": False,
        "reception_text_public_response_key_added": False,
        "section_text_public_response_keys_added": False,
        "rn_visible_contract_changed": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "completed_reply_template_used": False,
        "fixed_sentence_template_used": False,
        "completed_reply_generated": False,
    }


def assert_two_stage_section_surface_plan(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("two_stage_section_surface_plan must be a mapping")
    if _clean(value.get("schema_version")) not in {"", EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION}:
        raise ValueError("unexpected two_stage_section_surface_plan schema_version")
    if _clean(value.get("material_id")) not in {"", EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID}:
        raise ValueError("unexpected two_stage_section_surface_plan material_id")
    if not bool(value.get("required")):
        raise ValueError("two_stage_section_surface_plan must be required when present")
    if value.get("expected_comment_text_shape") != EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE:
        raise ValueError("two_stage_section_surface_plan must require labelled_two_stage_text")
    labels = _as_mapping(value.get("display_labels"))
    if labels.get("observation") != EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL:
        raise ValueError("two_stage_section_surface_plan must keep observation display label")
    if labels.get("reception") != EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL:
        raise ValueError("two_stage_section_surface_plan must keep reception display label")
    if list(value.get("section_order") or []) != list(EMLIS_TWO_STAGE_SECTION_ORDER):
        raise ValueError("two_stage_section_surface_plan must preserve observation -> reception order")
    sections = _sequence_mappings(value.get("sections"))
    if len(sections) != 2:
        raise ValueError("two_stage_section_surface_plan requires exactly two sections")
    if [section.get("section_id") for section in sections] != list(EMLIS_TWO_STAGE_SECTION_ORDER):
        raise ValueError("two_stage_section_surface_plan section ids must be observation -> reception")
    for section in sections:
        if _int_at_least(section.get("sentence_plan_unit_count"), default=0, minimum=0) <= 0:
            raise ValueError("two_stage_section_surface_plan sections require sentence_plan_unit_count")
        if bool(section.get("comment_text_generated")) or bool(section.get("completed_reply_template_used")):
            raise ValueError("two_stage_section_surface_plan sections must not generate completed replies")
    if bool(value.get("comment_text_generated")) or bool(value.get("completed_reply_template_used")):
        raise ValueError("two_stage_section_surface_plan must not generate completed replies")
    if bool(value.get("public_response_key_added")):
        raise ValueError("two_stage_section_surface_plan must not add public response keys")
    if bool(value.get("raw_input_included")) or bool(value.get("raw_text_included")):
        raise ValueError("two_stage_section_surface_plan must not include raw input")


__all__ = [
    "EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE",
    "EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL",
    "EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL",
    "EMLIS_TWO_STAGE_SECTION_ORDER",
    "EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID",
    "EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_PHASE",
    "EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION",
    "EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SCHEMA_VERSION",
    "EMLIS_TWO_STAGE_SECTION_BUDGET_POLICY_SOURCE_PHASE",
    "EMLIS_TWO_STAGE_MODE_CONTEXT_SCHEMA_VERSION",
    "EMLIS_TWO_STAGE_MODE_CONTEXT_SOURCE_PHASE",
    "assert_two_stage_section_surface_plan",
    "build_two_stage_section_surface_plan",
    "build_two_stage_section_budget_policy",
    "two_stage_mode_section_budget",
]
