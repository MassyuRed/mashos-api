# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 7 internal Composer connection for EmlisAI state answers.

This module turns the text-free ``emlis_state_answer_surface_contract`` into a
Composer-facing role plan.  It does not render completed sentences.  It only
marks the section boundary between the observation half and the human-follow
half, forwards the already-built contract material, and exposes small gate-safe
metadata for ConversationComposer / LimitedComposer.
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

EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis_state_answer.composer_role_plan.v1"
)
EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID: Final = (
    "emlis_state_answer_composer_role_plan"
)
EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_PHASE: Final = (
    "Phase7_limited_conversation_composer_connection"
)


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

    The contract may already be attached at the top level by Phase 7, or may be
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
    steps = [item for item in list(observation_layer.get("steps") or []) if isinstance(item, Mapping)]
    step_ids = _dedupe(
        observation_layer.get("step_ids")
        or [item.get("step_id") for item in steps if _clean(item.get("step_id"))]
    )
    return {
        "section_id": "observation",
        "section_role": "state_answer_observation",
        "source_layer": "observation_layer",
        "position": "front",
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
        "must_not_generate_completed_sentence": True,
        "completed_reply_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _human_follow_section(contract: Mapping[str, Any], *, sentence_plan_unit_count: int) -> dict[str, Any]:
    human_follow = _as_mapping(contract.get("human_follow_layer"))
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
        "section_id": "human_follow",
        "section_role": "human_follow",
        "source_layer": "human_follow_layer",
        "position": "back",
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
        "must_not_generate_completed_sentence": True,
        "completed_reply_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def build_state_answer_composer_role_plan(contract: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build the Phase 7 role plan consumed by Composer paths."""

    contract_payload = state_answer_surface_contract_composer_payload(contract or {}) if isinstance(contract, Mapping) and contract else {}
    if not contract_payload:
        return {}
    ratio = _ratio_summary(contract_payload)
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
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }
    assert_state_answer_composer_role_plan(plan)
    return plan


def state_answer_composer_payload_fragment(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return top-level Phase 7 fields for a Composer request payload."""

    contract = state_answer_surface_contract_from_composer_payload(payload)
    if not contract:
        return {}
    role_plan = build_state_answer_composer_role_plan(contract)
    gate_report = state_answer_surface_contract_gate_report(contract)
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
    }


def state_answer_composition_contract_fragment(role_plan: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(role_plan, Mapping) or not role_plan:
        return {}
    return {
        "state_answer_surface_contract_connected": True,
        "state_answer_role_plan_connected": True,
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
    }


def attach_state_answer_composer_meta(meta: Mapping[str, Any] | None, payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Attach Phase 7 connection metadata to a response composer_meta mapping."""

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


__all__ = [
    "EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_MATERIAL_ID",
    "EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_PHASE",
    "EMLIS_STATE_ANSWER_COMPOSER_ROLE_PLAN_SCHEMA_VERSION",
    "attach_state_answer_composer_meta",
    "build_state_answer_composer_role_plan",
    "state_answer_composer_payload_fragment",
    "state_answer_composition_contract_fragment",
    "state_answer_surface_contract_from_composer_payload",
    "assert_state_answer_composer_role_plan",
]
