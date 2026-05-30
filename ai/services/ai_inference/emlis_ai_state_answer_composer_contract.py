# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 8 internal Composer role-plan connection for EmlisAI state answers.

This module turns the text-free ``emlis_state_answer_surface_contract`` into a
Composer-facing role plan.  It does not render completed sentences.  It only
marks the labelled two-stage boundary between the ``見えたこと`` observation
section and the ``Emlisから`` reception section, forwards the already-built
contract material, and exposes small gate-safe metadata for ConversationComposer
/ LimitedComposer.
"""

from collections.abc import Mapping, Sequence
import copy
from typing import Any, Final

from emlis_ai_state_answer_surface_contract import (
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
    state_answer_surface_contract_composer_payload,
    state_answer_surface_contract_gate_report,
)
from emlis_ai_two_stage_section_surface_plan import (
    EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID,
    EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION,
    assert_two_stage_section_surface_plan,
    build_two_stage_section_surface_plan,
)

EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis_state_answer.composer_role_plan.v1"
)
EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID: Final = (
    "emlis_state_answer_composer_role_plan"
)
EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_PHASE: Final = (
    "Phase8_composer_role_plan_two_stage_reception"
)
EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL: Final = "見えたこと"
EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL: Final = "Emlisから"
EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE: Final = "labelled_two_stage_text"
EMLIS_TWO_STAGE_SECTION_ORDER: Final = ("observation", "reception")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _clean(value: Any) -> str:
    return str(value or "").strip()


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


def _copy_mapping(value: Any) -> dict[str, Any]:
    return copy.deepcopy(dict(value or {})) if isinstance(value, Mapping) else {}


def _two_stage_contract_summary(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the Phase 8 two-stage display contract without completed text."""

    two_stage = _as_mapping(contract.get("two_stage_reception"))
    observation_layer = _as_mapping(contract.get("observation_layer"))
    reception_section = _as_mapping(contract.get("reception_section_material"))
    human_follow = _as_mapping(contract.get("human_follow_layer"))
    reception_mode = _as_mapping(contract.get("reception_mode"))
    labels = _as_mapping(two_stage.get("display_labels"))
    observation_label = (
        _clean(labels.get("observation"))
        or _clean(observation_layer.get("display_label"))
        or EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL
    ).rstrip("：:")
    reception_label = (
        _clean(labels.get("reception"))
        or _clean(reception_section.get("display_label"))
        or _clean(human_follow.get("display_label"))
        or EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL
    ).rstrip("：:")
    section_order = _dedupe(two_stage.get("section_order") or EMLIS_TWO_STAGE_SECTION_ORDER)
    if section_order != list(EMLIS_TWO_STAGE_SECTION_ORDER):
        section_order = list(EMLIS_TWO_STAGE_SECTION_ORDER)
    mode_id = _clean(reception_mode.get("reception_mode_id") or reception_mode.get("mode_id"))
    return {
        "enabled": True,
        "two_stage_display_required": True,
        "two_stage_reception_surface_required": True,
        "section_labels_required": True,
        "display_labels": {
            "observation": observation_label,
            "reception": reception_label,
        },
        "two_stage_reception_labels": [observation_label, reception_label],
        "section_order": section_order,
        "section_id_order": section_order,
        "display_label_order": [observation_label, reception_label],
        "observation_display_label": observation_label,
        "reception_display_label": reception_label,
        "observation_label_marker": f"{observation_label}：",
        "reception_label_marker": f"{reception_label}：",
        "surface_joiner": _clean(two_stage.get("surface_joiner")) or "comment_text_two_stage_joiner",
        "joined_comment_text_required": True,
        "expected_comment_text_shape": (
            _clean(two_stage.get("expected_comment_text_shape"))
            or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE
        ),
        "reception_mode_id": mode_id or "standard_state_answer",
        "daily_reception_natural_short_comment_allowed": True,
        "daily_reception_may_use_natural_short_comment": True,
        "current_reception_mode_may_use_natural_short_comment": bool(mode_id.startswith("daily_")),
        "must_not_prompt_for_event_when_event_fact_present": True,
        "public_response_key_added": False,
        "observation_text_public_response_key_added": False,
        "reception_text_public_response_key_added": False,
        "section_text_public_response_keys_added": False,
        "public_payload_changed": False,
        "response_key_changed": False,
        "rn_visible_contract_changed": False,
        "completed_reply_generated": False,
        "fixed_sentence_template_used": False,
    }


def _contract_from_structure_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    structure_payload = _as_mapping(
        payload.get("observation_structure_material") or payload.get("observation_structure_dictionary")
    )
    contract = _as_mapping(structure_payload.get("state_answer_surface_contract"))
    if not contract:
        return {}
    return state_answer_surface_contract_composer_payload(contract)


def state_answer_surface_contract_from_composer_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Extract the state-answer surface contract from a Composer payload.

    The contract may already be attached at the top level by Phase 8, or may be
    nested inside the observation-structure material from Phase 2.  The returned
    shape is the sanitized composer payload from the state-answer contract
    module; raw memo / memo_action / comment body fields are never added here.
    """

    if not isinstance(payload, Mapping):
        return {}
    direct = _as_mapping(payload.get("state_answer_surface_contract"))
    if direct:
        return state_answer_surface_contract_composer_payload(direct)
    return _contract_from_structure_payload(payload)


def _ratio_summary(contract: Mapping[str, Any]) -> dict[str, Any]:
    ratio_policy = _as_mapping(contract.get("ratio_policy"))
    resolved = _as_mapping(ratio_policy.get("resolved_ratio"))
    basis = _as_mapping(ratio_policy.get("ratio_basis"))
    unit_plan = _as_mapping(basis.get("section_role_unit_plan"))
    try:
        observation = float(resolved.get("observation") or 0.0)
    except (TypeError, ValueError):
        observation = 0.0
    try:
        human_follow = float(resolved.get("human_follow") or 0.0)
    except (TypeError, ValueError):
        human_follow = 0.0
    return {
        "resolved_ratio": {
            "observation": observation,
            "human_follow": human_follow,
            "reason": _clean(resolved.get("reason")) or "standard_state_answer",
            "range_key": _clean(resolved.get("range_key")),
        },
        "measurement_basis": _dedupe(
            basis.get("measurement_basis")
            or ["section_role", "sentence_plan_unit_count", "follow_key_count"]
        ),
        "character_count_exact": False,
        "observation_units": int(unit_plan.get("observation_units") or 0),
        "human_follow_units": int(unit_plan.get("human_follow_units") or 0),
        "total_units": int(unit_plan.get("total_units") or 0),
        "observation_zero_allowed": False,
        "human_follow_zero_allowed": False,
        "comfort_only_allowed": False,
    }


def _observation_section(contract: Mapping[str, Any], *, sentence_plan_unit_count: int) -> dict[str, Any]:
    observation_layer = _as_mapping(contract.get("observation_layer"))
    two_stage = _two_stage_contract_summary(contract)
    observation_label = two_stage["observation_display_label"]
    steps = [item for item in list(observation_layer.get("steps") or []) if isinstance(item, Mapping)]
    step_ids = _dedupe(
        observation_layer.get("step_ids")
        or [item.get("step_id") for item in steps if _clean(item.get("step_id"))]
    )
    return {
        "section_id": "observation",
        "section_role": "state_answer_observation",
        "source_layer": "observation_layer",
        "display_label": observation_label,
        "section_label": observation_label,
        "comment_text_section_label": f"{observation_label}：",
        "section_label_required": True,
        "two_stage_reception_section": True,
        "two_stage_display_section": True,
        "expected_comment_text_shape": two_stage["expected_comment_text_shape"],
        "position": "front",
        "section_order_index": 0,
        "sentence_plan_unit_role": "observation_section",
        "sentence_plan_unit_count": max(1, int(sentence_plan_unit_count or len(step_ids) or 1)),
        "step_ids": step_ids,
        "claim_kinds": _dedupe(item.get("claim_kind") for item in steps),
        "surface_strengths": _dedupe(item.get("surface_strength") for item in steps),
        "source_span_ids": _dedupe(span_id for item in steps for span_id in list(item.get("source_span_ids") or [])),
        "must_use_scope_marker": bool(
            _as_mapping(observation_layer.get("scope_marker_policy")).get("must_use_scope_marker", True)
        ),
        "required_scope_marker": _clean(
            _as_mapping(observation_layer.get("scope_marker_policy")).get("required_scope_marker")
        ) or "今回の入力では",
        "must_not_read_as": _dedupe(
            item for step in steps for item in list(step.get("must_not_read_as") or [])
        ),
        "must_not_include_human_follow": True,
        "must_not_generate_completed_sentence": True,
        "completed_reply_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _human_follow_section(contract: Mapping[str, Any], *, sentence_plan_unit_count: int) -> dict[str, Any]:
    human_follow = _as_mapping(contract.get("human_follow_layer"))
    two_stage = _two_stage_contract_summary(contract)
    reception_label = two_stage["reception_display_label"]
    reception_section = _as_mapping(contract.get("reception_section_material"))
    secondary = _dedupe(human_follow.get("secondary_follow_keys") or [])
    slots = []
    raw_slots = human_follow.get("follow_key_slots")
    if isinstance(raw_slots, Sequence) and not isinstance(raw_slots, (str, bytes, bytearray)):
        for item in raw_slots:
            if isinstance(item, Mapping):
                slots.append(
                    {
                        "slot": _clean(item.get("slot")),
                        "follow_key": _clean(item.get("follow_key")),
                        "role": _clean(item.get("role")),
                    }
                )
    follow_key_count = 1 + len(secondary) + (1 if _clean(human_follow.get("afterglow_follow_key")) else 0)
    return {
        "section_id": "reception",
        "section_role": "human_follow",
        "reception_section_role": _clean(reception_section.get("section_role")) or "emlis_reception",
        "source_layer": "human_follow_layer",
        "display_label": reception_label,
        "section_label": reception_label,
        "comment_text_section_label": f"{reception_label}：",
        "section_label_required": True,
        "two_stage_reception_section": True,
        "two_stage_display_section": True,
        "expected_comment_text_shape": two_stage["expected_comment_text_shape"],
        "position": "back",
        "section_order_index": 1,
        "sentence_plan_unit_role": "human_follow_section",
        "sentence_plan_unit_count": max(1, int(sentence_plan_unit_count or follow_key_count or 1)),
        "primary_follow_key": _clean(human_follow.get("primary_follow_key")) or "fear_or_load_understanding",
        "secondary_follow_keys": secondary,
        "afterglow_follow_key": _clean(human_follow.get("afterglow_follow_key")) or "existence_respect",
        "follow_key_slots": slots,
        "follow_mode": _clean(human_follow.get("follow_mode")) or "emlis_impression_not_fact",
        "selector_input_type": _clean(human_follow.get("selector_input_type") or human_follow.get("input_type")) or "standard_state_answer",
        "must_ground_to_input": bool(human_follow.get("must_ground_to_input", True)),
        "grounding_source_span_ids": _dedupe(human_follow.get("grounding_source_span_ids") or []),
        "personality_claim_allowed": False,
        "target_judgement_agreement_allowed": False,
        "target_attack_amplification_allowed": False,
        "must_not_read_as": _dedupe(
            human_follow.get("must_not_read_as")
            or ["personality_claim", "diagnosis", "absolute_support", "action_instruction"]
        ),
        "must_not_include_new_observation_claim": True,
        "must_not_generate_action_instruction": True,
        "must_not_generate_completed_sentence": True,
        "completed_reply_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def build_state_answer_composer_role_plan(contract: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build the Phase 8 role plan consumed by Composer paths."""

    contract_payload = state_answer_surface_contract_composer_payload(contract or {}) if isinstance(contract, Mapping) and contract else {}
    if not contract_payload:
        return {}
    ratio = _ratio_summary(contract_payload)
    two_stage = _two_stage_contract_summary(contract_payload)
    observation_layer = _as_mapping(contract_payload.get("observation_layer"))
    steps = [item for item in list(observation_layer.get("steps") or []) if isinstance(item, Mapping)]
    human_follow = _as_mapping(contract_payload.get("human_follow_layer"))
    secondary = _dedupe(human_follow.get("secondary_follow_keys") or [])
    follow_key_count = 1 + len(secondary) + (1 if _clean(human_follow.get("afterglow_follow_key")) else 0)
    observation_unit_count = max(1, int(ratio.get("observation_units") or len(steps) or 1))
    human_follow_unit_count = max(1, int(ratio.get("human_follow_units") or follow_key_count or 1))
    observation_section = _observation_section(contract_payload, sentence_plan_unit_count=observation_unit_count)
    human_follow_section = _human_follow_section(contract_payload, sentence_plan_unit_count=human_follow_unit_count)
    plan = {
        "schema_version": EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION,
        "material_id": EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID,
        "source_phase": EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_PHASE,
        "phase": EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_PHASE,
        "connected": True,
        "state_answer_surface_contract_connected": True,
        "state_answer_surface_contract_material_id": _clean(contract_payload.get("material_id")) or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
        "state_answer_surface_contract_schema_version": _clean(contract_payload.get("schema_version")) or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
        "role_plan_kind": "observation_then_human_follow_sections",
        "two_stage_display_required": True,
        "two_stage_reception_surface_required": True,
        "section_labels_required": True,
        "display_labels": dict(two_stage.get("display_labels") or {}),
        "two_stage_reception_labels": list(two_stage.get("two_stage_reception_labels") or []),
        "observation_display_label": two_stage.get("observation_display_label") or EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL,
        "reception_display_label": two_stage.get("reception_display_label") or EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL,
        "observation_label_marker": two_stage.get("observation_label_marker") or "見えたこと：",
        "reception_label_marker": two_stage.get("reception_label_marker") or "Emlisから：",
        "section_id_order": list(two_stage.get("section_id_order") or EMLIS_TWO_STAGE_SECTION_ORDER),
        "display_label_order": list(two_stage.get("display_label_order") or []),
        "labelled_section_order_required": True,
        "joined_comment_text_required": True,
        "expected_comment_text_shape": two_stage.get("expected_comment_text_shape") or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE,
        "comment_text_shape": two_stage.get("expected_comment_text_shape") or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE,
        "surface_joiner": two_stage.get("surface_joiner") or "comment_text_two_stage_joiner",
        "observation_section_must_precede_reception_section": True,
        "observation_section_must_not_include_human_follow": True,
        "reception_section_must_not_include_new_observation_claim": True,
        "daily_reception_may_use_natural_short_comment": bool(
            two_stage.get("daily_reception_may_use_natural_short_comment", True)
        ),
        "current_reception_mode_may_use_natural_short_comment": bool(
            two_stage.get("current_reception_mode_may_use_natural_short_comment")
        ),
        "must_not_prompt_for_event_when_event_fact_present": True,
        "section_boundary_required": True,
        "section_boundary_on_sentence_plan": True,
        "observation_section_required": True,
        "human_follow_section_required": True,
        "front_section_role": "state_answer_observation",
        "back_section_role": "human_follow",
        "sections": [observation_section, human_follow_section],
        "section_role_order": ["state_answer_observation", "human_follow"],
        "sentence_plan_unit_roles": ["observation_section", "human_follow_section"],
        "observation_step_ids": observation_section.get("step_ids") or [],
        "primary_follow_key": human_follow_section.get("primary_follow_key") or "",
        "secondary_follow_keys": human_follow_section.get("secondary_follow_keys") or [],
        "afterglow_follow_key": human_follow_section.get("afterglow_follow_key") or "",
        "selector_input_type": human_follow_section.get("selector_input_type") or "standard_state_answer",
        "resolved_ratio": ratio.get("resolved_ratio") or {},
        "ratio_measurement_basis": ratio.get("measurement_basis") or [],
        "observation_sentence_plan_units": observation_unit_count,
        "human_follow_sentence_plan_units": human_follow_unit_count,
        "total_sentence_plan_units": observation_unit_count + human_follow_unit_count,
        "ratio_is_character_count_exact": False,
        "observation_zero_allowed": False,
        "human_follow_zero_allowed": False,
        "comfort_only_allowed": False,
        "material_is_completed_reply_template": False,
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "fixed_sentence_template_used": False,
        "runtime_renderer_marker_used": False,
        "input_feedback_comment_text_public_contract_unchanged": True,
        "passed_only_display_condition_unchanged": True,
        "public_payload_changed": False,
        "public_response_key_added": False,
        "observation_text_public_response_key_added": False,
        "reception_text_public_response_key_added": False,
        "section_text_public_response_keys_added": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }
    assert_state_answer_composer_role_plan(plan)
    return plan


def state_answer_composer_payload_fragment(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return top-level Phase 8 fields for a Composer request payload."""

    contract = state_answer_surface_contract_from_composer_payload(payload)
    if not contract:
        return {}
    role_plan = build_state_answer_composer_role_plan(contract)
    gate_report = state_answer_surface_contract_gate_report(contract)
    section_surface_plan = build_two_stage_section_surface_plan(
        role_plan,
        state_answer_surface_contract=contract,
    )
    if section_surface_plan:
        assert_two_stage_section_surface_plan(section_surface_plan)
    return {
        "state_answer_surface_contract": contract,
        "state_answer_surface_contract_connected": True,
        "state_answer_surface_contract_material_id": contract.get("material_id") or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
        "state_answer_surface_contract_schema_version": contract.get("schema_version") or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
        "state_answer_surface_contract_material_only": True,
        "state_answer_surface_contract_gate_report": gate_report,
        "state_answer_composer_role_plan": role_plan,
        "state_answer_composer_role_plan_connected": bool(role_plan),
        "state_answer_composer_role_plan_material_id": role_plan.get("material_id") or "",
        "state_answer_composer_role_plan_schema_version": role_plan.get("schema_version") or "",
        "two_stage_section_surface_plan": section_surface_plan,
        "two_stage_section_surface_plan_connected": bool(section_surface_plan),
        "two_stage_section_surface_plan_material_id": section_surface_plan.get("material_id") or "",
        "two_stage_section_surface_plan_schema_version": section_surface_plan.get("schema_version") or "",
    }


def state_answer_composition_contract_fragment(role_plan: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(role_plan, Mapping) or not role_plan:
        return {}
    section_surface_plan = build_two_stage_section_surface_plan(role_plan)
    if section_surface_plan:
        assert_two_stage_section_surface_plan(section_surface_plan)
    return {
        "state_answer_surface_contract_connected": True,
        "state_answer_role_plan_connected": True,
        "two_stage_section_surface_plan_connected": bool(section_surface_plan),
        "two_stage_section_surface_plan_required": bool(section_surface_plan),
        "two_stage_section_surface_plan_material_id": section_surface_plan.get("material_id") or "",
        "two_stage_section_surface_plan_schema_version": section_surface_plan.get("schema_version") or "",
        "two_stage_section_surface_plan_section_order": list(section_surface_plan.get("section_order") or []),
        "two_stage_section_surface_plan_section_ids": list(section_surface_plan.get("section_ids") or []),
        "two_stage_section_surface_plan_expected_comment_text_shape": _clean(
            section_surface_plan.get("expected_comment_text_shape")
        ),
        "two_stage_reception_surface_required": True,
        "two_stage_display_required": True,
        "section_labels_required": True,
        "two_stage_reception_labels": list(role_plan.get("two_stage_reception_labels") or []),
        "two_stage_section_order": list(role_plan.get("section_id_order") or EMLIS_TWO_STAGE_SECTION_ORDER),
        "observation_display_label": _clean(
            role_plan.get("observation_display_label") or EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL
        ),
        "reception_display_label": _clean(
            role_plan.get("reception_display_label") or EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL
        ),
        "joined_comment_text_required": True,
        "expected_comment_text_shape": _clean(
            role_plan.get("expected_comment_text_shape") or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE
        ),
        "observation_section_must_precede_reception_section": True,
        "observation_section_must_not_include_human_follow": True,
        "reception_section_must_not_include_new_observation_claim": True,
        "daily_reception_may_use_natural_short_comment": bool(
            role_plan.get("daily_reception_may_use_natural_short_comment", True)
        ),
        "current_reception_mode_may_use_natural_short_comment": bool(
            role_plan.get("current_reception_mode_may_use_natural_short_comment")
        ),
        "must_not_prompt_for_event_when_event_fact_present": True,
        "state_answer_section_boundary_required": True,
        "state_answer_section_boundary_on_sentence_plan": True,
        "state_answer_observation_section_required": True,
        "state_answer_human_follow_section_required": True,
        "state_answer_front_section_role": "state_answer_observation",
        "state_answer_back_section_role": "human_follow",
        "state_answer_section_role_order": list(role_plan.get("section_role_order") or ["state_answer_observation", "human_follow"]),
        "state_answer_sentence_plan_unit_roles": list(role_plan.get("sentence_plan_unit_roles") or []),
        "state_answer_observation_step_ids": list(role_plan.get("observation_step_ids") or []),
        "state_answer_primary_follow_key": _clean(role_plan.get("primary_follow_key")),
        "state_answer_secondary_follow_keys": list(role_plan.get("secondary_follow_keys") or []),
        "state_answer_afterglow_follow_key": _clean(role_plan.get("afterglow_follow_key")),
        "state_answer_ratio_is_character_count_exact": False,
        "state_answer_observation_zero_allowed": False,
        "state_answer_human_follow_zero_allowed": False,
        "state_answer_comfort_only_allowed": False,
        "state_answer_must_not_generate_action_instruction": True,
        "state_answer_must_not_generate_diagnosis": True,
        "state_answer_must_not_generate_personality_type": True,
        "state_answer_public_contract_unchanged": True,
        "state_answer_input_feedback_comment_text_contract_unchanged": True,
        "state_answer_passed_only_display_condition_unchanged": True,
        "state_answer_dictionary_must_not_generate_completed_sentence": True,
        "state_answer_material_is_not_fixed_template": True,
        "public_response_key_added": False,
        "observation_text_public_response_key_added": False,
        "reception_text_public_response_key_added": False,
        "section_text_public_response_keys_added": False,
        "response_key_changed": False,
    }


def attach_state_answer_composer_meta(meta: Mapping[str, Any] | None, payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Attach Phase 8 connection metadata to a response composer_meta mapping."""

    out = _copy_mapping(meta)
    fragment = state_answer_composer_payload_fragment(payload)
    role_plan = _as_mapping(fragment.get("state_answer_composer_role_plan"))
    contract = _as_mapping(fragment.get("state_answer_surface_contract"))
    if not role_plan or not contract:
        return out
    out["state_answer_surface_contract_connected"] = True
    out["state_answer_surface_contract_material_id"] = contract.get("material_id") or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    out["state_answer_surface_contract_schema_version"] = contract.get("schema_version") or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION
    out["state_answer_surface_contract_material_only"] = True
    out["state_answer_surface_contract_gate_report"] = fragment.get("state_answer_surface_contract_gate_report") or {}
    out["state_answer_composer_role_plan"] = dict(role_plan)
    out["state_answer_composer_role_plan_connected"] = True
    out["state_answer_composer_role_plan_material_id"] = role_plan.get("material_id") or EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID
    out["state_answer_composer_role_plan_schema_version"] = role_plan.get("schema_version") or EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION
    section_surface_plan = _as_mapping(fragment.get("two_stage_section_surface_plan"))
    if section_surface_plan:
        out["two_stage_section_surface_plan"] = dict(section_surface_plan)
        out["two_stage_section_surface_plan_connected"] = True
        out["two_stage_section_surface_plan_material_id"] = (
            section_surface_plan.get("material_id") or EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID
        )
        out["two_stage_section_surface_plan_schema_version"] = (
            section_surface_plan.get("schema_version") or EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION
        )
        out["two_stage_section_surface_plan_required"] = bool(section_surface_plan.get("required", True))
        out["two_stage_section_surface_plan_section_order"] = list(section_surface_plan.get("section_order") or [])
        out["two_stage_section_surface_plan_section_ids"] = list(section_surface_plan.get("section_ids") or [])
        out["two_stage_section_surface_plan_expected_comment_text_shape"] = _clean(
            section_surface_plan.get("expected_comment_text_shape")
        )
    out["state_answer_two_stage_display_required"] = True
    out["state_answer_two_stage_reception_surface_required"] = True
    out["state_answer_section_labels_required"] = True
    out["state_answer_two_stage_reception_labels"] = list(role_plan.get("two_stage_reception_labels") or [])
    out["state_answer_observation_display_label"] = _clean(
        role_plan.get("observation_display_label") or EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL
    )
    out["state_answer_reception_display_label"] = _clean(
        role_plan.get("reception_display_label") or EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL
    )
    out["state_answer_two_stage_section_order"] = list(role_plan.get("section_id_order") or [])
    out["state_answer_expected_comment_text_shape"] = _clean(
        role_plan.get("expected_comment_text_shape") or EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE
    )
    out["state_answer_joined_comment_text_required"] = True
    out["state_answer_observation_section_must_precede_reception_section"] = True
    out["state_answer_observation_section_must_not_include_human_follow"] = True
    out["state_answer_reception_section_must_not_include_new_observation_claim"] = True
    out["state_answer_daily_reception_may_use_natural_short_comment"] = bool(
        role_plan.get("daily_reception_may_use_natural_short_comment", True)
    )
    out["state_answer_current_reception_mode_may_use_natural_short_comment"] = bool(
        role_plan.get("current_reception_mode_may_use_natural_short_comment")
    )
    out["state_answer_must_not_prompt_for_event_when_event_fact_present"] = True
    out["state_answer_section_boundary_required"] = True
    out["state_answer_section_boundary_on_sentence_plan"] = True
    out["state_answer_observation_section_required"] = True
    out["state_answer_human_follow_section_required"] = True
    out["state_answer_section_role_order"] = list(role_plan.get("section_role_order") or [])
    out["state_answer_sentence_plan_unit_roles"] = list(role_plan.get("sentence_plan_unit_roles") or [])
    out["state_answer_observation_step_ids"] = list(role_plan.get("observation_step_ids") or [])
    out["state_answer_primary_follow_key"] = role_plan.get("primary_follow_key") or ""
    out["state_answer_secondary_follow_keys"] = list(role_plan.get("secondary_follow_keys") or [])
    out["state_answer_afterglow_follow_key"] = role_plan.get("afterglow_follow_key") or ""
    out["state_answer_resolved_ratio"] = dict(role_plan.get("resolved_ratio") or {})
    out["state_answer_ratio_is_character_count_exact"] = False
    out["state_answer_observation_zero_allowed"] = False
    out["state_answer_human_follow_zero_allowed"] = False
    out["state_answer_comfort_only_allowed"] = False
    out["state_answer_completed_reply_generated_from_contract"] = False
    out["state_answer_fixed_sentence_template_used"] = False
    out["state_answer_runtime_renderer_marker_used"] = False
    out["state_answer_input_feedback_comment_text_public_contract_unchanged"] = True
    out["state_answer_passed_only_display_condition_unchanged"] = True
    out["state_answer_public_payload_changed"] = False
    out["state_answer_public_response_key_added"] = False
    out["state_answer_observation_text_public_response_key_added"] = False
    out["state_answer_reception_text_public_response_key_added"] = False
    out["state_answer_section_text_public_response_keys_added"] = False
    return out


def assert_state_answer_composer_role_plan(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("state_answer_composer_role_plan must be a mapping")
    if _clean(value.get("schema_version")) not in {"", EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION}:
        raise ValueError("unexpected state_answer_composer_role_plan schema_version")
    if _clean(value.get("material_id")) not in {"", EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID}:
        raise ValueError("unexpected state_answer_composer_role_plan material_id")
    if bool(value.get("completed_reply_generated")):
        raise ValueError("state_answer_composer_role_plan must not generate completed replies")
    if bool(value.get("fixed_sentence_template_used")):
        raise ValueError("state_answer_composer_role_plan must not use fixed templates")
    if bool(value.get("runtime_renderer_marker_used")):
        raise ValueError("state_answer_composer_role_plan must not use runtime renderer markers")
    sections = value.get("sections")
    if not isinstance(sections, Sequence) or isinstance(sections, (str, bytes, bytearray)) or len(sections) < 2:
        raise ValueError("state_answer_composer_role_plan requires observation and human_follow sections")
    roles = [item.get("section_role") for item in sections if isinstance(item, Mapping)]
    if roles[:2] != ["state_answer_observation", "human_follow"]:
        raise ValueError("state_answer_composer_role_plan must preserve observation -> human_follow order")
    if bool(value.get("observation_zero_allowed")) or bool(value.get("human_follow_zero_allowed")):
        raise ValueError("state_answer_composer_role_plan must not allow zero observation/follow sections")
    if bool(value.get("comfort_only_allowed")):
        raise ValueError("state_answer_composer_role_plan must not allow comfort-only output")
    if not bool(value.get("two_stage_display_required")):
        raise ValueError("state_answer_composer_role_plan requires two-stage display")
    if not bool(value.get("section_labels_required")):
        raise ValueError("state_answer_composer_role_plan requires section labels")
    labels = _as_mapping(value.get("display_labels"))
    if labels.get("observation") != EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL:
        raise ValueError("state_answer_composer_role_plan must keep observation display label")
    if labels.get("reception") != EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL:
        raise ValueError("state_answer_composer_role_plan must keep reception display label")
    if list(value.get("section_id_order") or []) != list(EMLIS_TWO_STAGE_SECTION_ORDER):
        raise ValueError("state_answer_composer_role_plan must preserve observation -> reception order")
    if bool(value.get("public_response_key_added")):
        raise ValueError("state_answer_composer_role_plan must not add public response keys")
    if bool(value.get("observation_text_public_response_key_added")):
        raise ValueError("state_answer_composer_role_plan must not add observation_text public key")
    if bool(value.get("reception_text_public_response_key_added")):
        raise ValueError("state_answer_composer_role_plan must not add reception_text public key")


__all__ = [
    "EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID",
    "EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_PHASE",
    "EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION",
    "EMLIS_TWO_STAGE_COMMENT_TEXT_SHAPE",
    "EMLIS_TWO_STAGE_OBSERVATION_DISPLAY_LABEL",
    "EMLIS_TWO_STAGE_RECEPTION_DISPLAY_LABEL",
    "EMLIS_TWO_STAGE_SECTION_ORDER",
    "attach_state_answer_composer_meta",
    "build_state_answer_composer_role_plan",
    "build_two_stage_section_surface_plan",
    "state_answer_composer_payload_fragment",
    "state_answer_composition_contract_fragment",
    "state_answer_surface_contract_from_composer_payload",
    "assert_state_answer_composer_role_plan",
]
