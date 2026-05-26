# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal EmlisAI state-answer surface contract material.

Phase 2 materializes the internal contract described by the EmlisAI
state-answer / human-follow design.  The contract is deliberately text-free: it
separates the observation layer from the human-follow layer and exposes only
ids, source-field names, evidence span ids, section roles, and guard policies.

This module does not generate user-facing ``comment_text``, does not add a
public response key, does not materialize a JSON schema file, and does not
change API routes, DB physical names, or RN display conditions.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import copy
import json
from typing import Any, Final

from cocolon_environment_state_output_frame import (
    ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
    build_environment_state_output_frame,
)
from emlis_ai_human_follow_selector import (
    EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID,
    EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE,
    EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION,
    build_emlis_ai_human_follow_selection,
    human_follow_selection_composer_payload,
    human_follow_selection_forward_meta,
    human_follow_selection_gate_report,
)
from emlis_ai_state_answer_ratio_policy import (
    EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID,
    EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE,
    EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION,
    build_emlis_ai_state_answer_ratio_policy,
    state_answer_ratio_policy_composer_payload,
    state_answer_ratio_policy_forward_meta,
    state_answer_ratio_policy_gate_report,
)
from emlis_ai_state_answer_special_cases import (
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
    EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
    build_emlis_ai_state_answer_special_cases,
    state_answer_special_cases_composer_payload,
    state_answer_special_cases_forward_meta,
    state_answer_special_cases_gate_report,
)
from emlis_ai_safe_daily_metaphor_material import (
    EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID,
    EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE,
    EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION,
    build_emlis_ai_safe_daily_metaphor_material,
    safe_daily_metaphor_material_composer_payload,
    safe_daily_metaphor_material_forward_meta,
    safe_daily_metaphor_material_gate_report,
)
EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION: Final = (
    "cocolon.emlis_state_answer_surface_contract.v1"
)
EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID: Final = "emlis_state_answer_surface_contract"
EMLIS_STATE_ANSWER_SURFACE_CONTRACT_PHASE: Final = "Phase2_state_answer_surface_contract_material"
EMLIS_STATE_ANSWER_SURFACE_CONTRACT_INTERNAL_NAME: Final = (
    "EmlisAI状態回答・人間的フォローsurface contract"
)

_DEFAULT_RATIO: Final = {"observation": 0.6, "human_follow": 0.4}
_ALLOWED_RATIO_RANGES: Final = {
    "standard": {"observation_min": 0.55, "observation_max": 0.70},
    "self_denial_or_grief": {"observation_min": 0.40, "observation_max": 0.55},
    "structure_question": {"observation_min": 0.65, "observation_max": 0.75},
}

_OBSERVATION_STEP_ORDER: Final = (
    "intent_pickup",
    "surface_state_observation",
    "unconfirmed_area",
    "deeper_state_observation",
    "fact_boundary",
)

_FORBIDDEN_RAW_PAYLOAD_KEYS: Final = frozenset(
    {
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "memo",
        "memo_action",
        "memoText",
        "memoAction",
        "thought_text",
        "action_text",
        "comment_text",
        "commentText",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "completed_reply_text",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "api_response_key_change",
        "comment_text_body_included",
        "comment_text_included",
        "comment_text_generated",
        "completed_reply_generated",
        "db_physical_name_changed",
        "display_gate_relaxed",
        "external_ai_used",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "gate_relaxed",
        "input_specific_template_used",
        "local_llm_used",
        "period_tendency_from_single_record",
        "personality_tendency_allowed",
        "public_payload_changed",
        "public_response_key_added",
        "public_response_key_change",
        "public_status_extended",
        "raw_input_included",
        "raw_text_included",
        "recovery_prescription_allowed",
        "response_key_changed",
        "rn_visible_contract_changed",
        "schema_file_materialized",
    }
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Any) -> list[str]:
    if values is None:
        iterable: list[Any] = []
    elif isinstance(values, (str, bytes)) or isinstance(values, Mapping):
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


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _deepcopy_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return copy.deepcopy(dict(value or {}))


def _span_ids_for_fields(frame: Mapping[str, Any], *source_fields: str) -> list[str]:
    wanted = {field for field in source_fields if field}
    spans = (_as_mapping(frame.get("evidence")).get("spans") or [])
    out: list[str] = []
    for span in spans:
        if not isinstance(span, Mapping):
            continue
        if _clean(span.get("source_field")) not in wanted:
            continue
        span_id = _clean(span.get("span_id"))
        if span_id and span_id not in out:
            out.append(span_id)
    return out


def _all_frame_span_ids(frame: Mapping[str, Any]) -> list[str]:
    spans = (_as_mapping(frame.get("evidence")).get("spans") or [])
    return _dedupe(span.get("span_id") for span in spans if isinstance(span, Mapping))


def _relation_ids_from_material(material_meta: Mapping[str, Any]) -> list[str]:
    return _dedupe(
        material_meta.get("selected_relation_ids")
        or material_meta.get("structure_relation_ids")
        or material_meta.get("graph_relation_ids")
        or []
    )


def _axis_presence(frame: Mapping[str, Any]) -> dict[str, bool]:
    axis = _as_mapping(frame.get("axis_presence"))
    return {
        "has_environment_axis": bool(axis.get("has_environment_axis")),
        "has_state_axis": bool(axis.get("has_state_axis")),
        "has_output_axis": bool(axis.get("has_output_axis")),
        "has_all_single_record_axes": bool(axis.get("has_all_single_record_axes")),
    }


def _safe_frame_projection(frame: Mapping[str, Any]) -> dict[str, Any]:
    """Return the frame fields Phase 2 needs without raw memo/action text."""

    environment_axis = _as_mapping(frame.get("environment_axis"))
    state_axis = _as_mapping(frame.get("state_axis"))
    output_axis = _as_mapping(frame.get("output_axis"))
    time_axis = _as_mapping(frame.get("time_axis"))
    bridge = _as_mapping(frame.get("observation_structure_bridge"))
    surface_policy = _as_mapping(frame.get("surface_policy"))
    source = _as_mapping(frame.get("source"))

    category_labels = []
    for item in environment_axis.get("category_labels") or []:
        if not isinstance(item, Mapping):
            continue
        label = _clean(item.get("label"))
        if not label:
            continue
        category_labels.append(
            {
                "label": label,
                "source_field": "category",
                "evidence_span_ids": _dedupe(item.get("evidence_span_ids") or []),
                "read_as": "topic_direction",
                "must_not_read_as": "cause",
            }
        )

    emotion_labels = []
    for item in state_axis.get("emotion_labels") or []:
        if not isinstance(item, Mapping):
            continue
        emotion_type = _clean(item.get("type"))
        if not emotion_type:
            continue
        emotion_labels.append(
            {
                "type": emotion_type,
                "strength": _clean(item.get("strength")),
                "source_field": _clean(item.get("source_field")) or "emotion_details",
                "evidence_span_ids": _dedupe(item.get("evidence_span_ids") or []),
                "read_as": "state_label",
                "must_not_read_as": "diagnosis",
            }
        )

    output_theme_candidates = []
    for item in output_axis.get("output_theme_candidates") or []:
        if not isinstance(item, Mapping):
            continue
        theme_id = _clean(item.get("theme_id"))
        if not theme_id:
            continue
        output_theme_candidates.append(
            {
                "theme_id": theme_id,
                "source_field": _clean(item.get("source_field")) or "memo",
                "evidence_span_ids": _dedupe(item.get("evidence_span_ids") or []),
                "confidence_kind": _clean(item.get("confidence_kind")) or "explicit_text_evidence",
                "allowed_surface_strength": _clean(item.get("allowed_surface_strength")) or "soft",
                "supporting_observation_relation_ids": _dedupe(
                    item.get("supporting_observation_relation_ids") or []
                ),
                "must_not_read_as": _dedupe(
                    item.get("must_not_read_as")
                    or ["personality_tendency", "period_tendency", "diagnosis", "cause"]
                ),
            }
        )

    evidence_span_ids = _all_frame_span_ids(frame)
    return {
        "schema_version": frame.get("schema_version") or ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
        "material_id": frame.get("material_id") or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
        "phase": frame.get("phase") or "",
        "projection_kind": "phase2_state_answer_contract_safe_projection",
        "source": {
            "source_kind": source.get("source_kind") or "current_input",
            "source_record_id": _clean(source.get("source_record_id")),
            "selected_at": _clean(source.get("selected_at")),
            "bundle_schema_version": _clean(source.get("bundle_schema_version")),
        },
        "axis_presence": _axis_presence(frame),
        "environment_axis": {
            "category_labels": category_labels,
            "has_action_text": bool(_as_mapping(environment_axis.get("action_evidence")).get("has_action_text")),
            "action_evidence_span_ids": _span_ids_for_fields(frame, "memo_action"),
            "confidence_kind": _clean(environment_axis.get("confidence_kind")) or "environment_axis_missing",
            "read_as": "environment_or_topic_direction",
            "must_not_read_as": ["cause"],
            "raw_text_included": False,
        },
        "state_axis": {
            "emotion_labels": emotion_labels,
            "strength_summary": _deepcopy_mapping(_as_mapping(state_axis.get("strength_summary"))),
            "state_text_gap_candidate_ids": _dedupe(
                item.get("candidate_id")
                for item in (state_axis.get("state_text_gap_candidates") or [])
                if isinstance(item, Mapping)
            ),
            "confidence_kind": _clean(state_axis.get("confidence_kind")) or "state_axis_missing",
            "read_as": "state_label",
            "must_not_read_as": ["diagnosis", "cause"],
        },
        "output_axis": {
            "has_thought_text": bool(_as_mapping(output_axis.get("thought_evidence")).get("has_thought_text")),
            "thought_evidence_span_ids": _span_ids_for_fields(frame, "memo"),
            "output_theme_candidates": output_theme_candidates,
            "output_theme_ids": _dedupe(item.get("theme_id") for item in output_theme_candidates),
            "confidence_kind": _clean(output_axis.get("confidence_kind")) or "output_axis_missing",
            "read_as": "output_content",
            "must_not_read_as": ["personality_tendency", "period_tendency", "diagnosis", "cause"],
            "raw_text_included": False,
        },
        "time_axis": {
            "selected_at_present": bool(time_axis.get("selected_at")),
            "period_scope": time_axis.get("period_scope") or "single_record",
            "must_not_use_for_period_tendency": True,
        },
        "observation_structure_bridge": {
            "selected_relation_ids": _dedupe(bridge.get("selected_relation_ids") or []),
            "relation_ids_are_candidates_only": bool(bridge.get("relation_ids_are_candidates_only", True)),
            "bridge_used_for_surface_text": False,
        },
        "evidence": {
            "evidence_span_ids": evidence_span_ids,
            "span_count": len(evidence_span_ids),
            "raw_text_included": False,
            "redacted_preview_included": False,
        },
        "frame_policy": {
            "single_record_only": True,
            "must_use_scope_marker": bool(surface_policy.get("must_use_scope_marker", True)),
            "scope_marker": surface_policy.get("scope_marker") or "今回の入力では",
            "forbidden_claims": _dedupe(
                surface_policy.get("forbidden_claims")
                or [
                    "personality_tendency",
                    "diagnosis",
                    "cause_from_category",
                    "cause_from_emotion_strength",
                    "period_tendency_from_single_record",
                    "recovery_prescription",
                ]
            ),
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "public_payload_changed": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
            "personality_tendency_allowed": False,
            "recovery_prescription_allowed": False,
        },
    }


def _ratio_policy(
    *,
    current_input: Any = None,
    frame_projection: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    human_follow_layer: Mapping[str, Any],
) -> dict[str, Any]:
    ratio_policy = build_emlis_ai_state_answer_ratio_policy(
        current_input,
        environment_state_output_frame=frame_projection,
        observation_structure_material=material_meta,
        human_follow_layer=human_follow_layer,
    )
    return state_answer_ratio_policy_forward_meta(ratio_policy)


def _observation_step(
    *,
    step_id: str,
    claim_kind: str,
    surface_strength: str,
    source_span_ids: Sequence[str],
    relation_ids: Sequence[str] = (),
    must_not_read_as: Sequence[str],
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "claim_kind": claim_kind,
        "surface_strength": surface_strength,
        "source_span_ids": _dedupe(source_span_ids),
        "observation_relation_ids": _dedupe(relation_ids),
        "section_role": "observation",
        "must_not_read_as": _dedupe(must_not_read_as),
        "completed_reply_generated": False,
        "raw_text_included": False,
    }


def _observation_layer(frame_projection: Mapping[str, Any], material_meta: Mapping[str, Any]) -> dict[str, Any]:
    output_axis = _as_mapping(frame_projection.get("output_axis"))
    state_axis = _as_mapping(frame_projection.get("state_axis"))
    environment_axis = _as_mapping(frame_projection.get("environment_axis"))
    bridge = _as_mapping(frame_projection.get("observation_structure_bridge"))
    relation_ids = _dedupe(bridge.get("selected_relation_ids") or _relation_ids_from_material(material_meta))

    thought_span_ids = _dedupe(output_axis.get("thought_evidence_span_ids") or [])
    state_span_ids: list[str] = []
    for label in state_axis.get("emotion_labels") or []:
        if isinstance(label, Mapping):
            state_span_ids.extend(_dedupe(label.get("evidence_span_ids") or []))
    state_span_ids = _dedupe(state_span_ids)
    action_span_ids = _dedupe(environment_axis.get("action_evidence_span_ids") or [])
    all_span_ids = _dedupe(thought_span_ids + state_span_ids + action_span_ids + _all_frame_span_ids(frame_projection))

    steps = [
        _observation_step(
            step_id="intent_pickup",
            claim_kind="user_intent_from_input",
            surface_strength="soft",
            source_span_ids=thought_span_ids or all_span_ids,
            relation_ids=relation_ids,
            must_not_read_as=("personality_claim", "diagnosis", "cause_claim"),
        ),
        _observation_step(
            step_id="surface_state_observation",
            claim_kind="state_label_from_current_input",
            surface_strength="soft",
            source_span_ids=state_span_ids or all_span_ids,
            relation_ids=relation_ids,
            must_not_read_as=("diagnosis", "personality_tendency", "cause_claim"),
        ),
        _observation_step(
            step_id="unconfirmed_area",
            claim_kind="known_unknown_boundary",
            surface_strength="medium",
            source_span_ids=_dedupe(thought_span_ids + action_span_ids) or all_span_ids,
            relation_ids=relation_ids,
            must_not_read_as=("cause_claim", "action_instruction", "target_judgement"),
        ),
        _observation_step(
            step_id="deeper_state_observation",
            claim_kind="state_answer",
            surface_strength="medium",
            source_span_ids=all_span_ids,
            relation_ids=relation_ids,
            must_not_read_as=("personality_tendency", "period_tendency", "diagnosis"),
        ),
        _observation_step(
            step_id="fact_boundary",
            claim_kind="known_unknown_boundary",
            surface_strength="soft",
            source_span_ids=all_span_ids,
            relation_ids=relation_ids,
            must_not_read_as=("advice", "solution", "cause_claim"),
        ),
    ]

    # Keep a stable order for downstream SentencePlan role selection.
    order_index = {step_id: index for index, step_id in enumerate(_OBSERVATION_STEP_ORDER)}
    steps.sort(key=lambda item: order_index.get(str(item.get("step_id")), 999))

    return {
        "section_role": "state_answer_observation",
        "steps": steps,
        "step_ids": [item.get("step_id") for item in steps],
        "step_order": list(_OBSERVATION_STEP_ORDER),
        "scope_marker_policy": {
            "single_record_only": True,
            "must_use_scope_marker": bool(_as_mapping(frame_projection.get("frame_policy")).get("must_use_scope_marker", True)),
            "required_scope_marker": _as_mapping(frame_projection.get("frame_policy")).get("scope_marker") or "今回の入力では",
            "must_not_surface_as_period_tendency": True,
            "allowed_scope_marker_family": "current_input_scope",
        },
        "environment_state_output_frame_connected": bool(frame_projection),
        "observation_structure_material_connected": bool(material_meta),
        "completed_reply_generated": False,
        "raw_text_included": False,
    }


def _human_follow_layer(
    frame_projection: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    current_input: Any = None,
) -> dict[str, Any]:
    evidence_span_ids = _dedupe(
        _as_mapping(frame_projection.get("evidence")).get("evidence_span_ids")
        or material_meta.get("evidence_span_ids")
        or []
    )
    selector = build_emlis_ai_human_follow_selection(
        current_input=current_input,
        environment_state_output_frame=frame_projection,
        observation_structure_material=material_meta,
    )
    selector_meta = human_follow_selection_forward_meta(selector)
    selector_payload = human_follow_selection_composer_payload(selector_meta)
    selection = _as_mapping(selector_meta.get("selection"))
    guard_policy = _as_mapping(selector_meta.get("guard_policy"))
    return {
        "section_role": "human_follow",
        "primary_follow_key": selection.get("primary_follow_key") or selector_meta.get("primary_follow_key") or "fear_or_load_understanding",
        "secondary_follow_keys": list(selection.get("secondary_follow_keys") or selector_meta.get("secondary_follow_keys") or ["intention_affirmation", "effort_receiving"]),
        "afterglow_follow_key": selection.get("afterglow_follow_key") or selector_meta.get("afterglow_follow_key") or "existence_respect",
        "follow_mode": selection.get("follow_mode") or "emlis_impression_not_fact",
        "selector_phase": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE,
        "selector_schema_version": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION,
        "selector_material_id": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID,
        "human_follow_selector_connected": True,
        "human_follow_selector_gate_report": human_follow_selection_gate_report(selector_meta),
        "human_follow_selector_payload": selector_payload,
        "input_type": selection.get("input_type") or "standard_state_answer",
        "selector_input_type": selection.get("input_type") or "standard_state_answer",
        "input_type": selection.get("input_type") or "standard_state_answer",
        "selector_basis": list(selection.get("selector_basis") or []),
        "input_type_candidates": copy.deepcopy(list(selection.get("input_type_candidates") or [])),
        "follow_key_slots": copy.deepcopy(list(selector_meta.get("follow_key_slots") or [])),
        "strong_follow_candidate": bool(selection.get("strong_follow_candidate")),
        "surface_risk_ids": list(selector_meta.get("surface_risk_ids") or []),
        "detected_input_signal_ids": list(selector_meta.get("detected_input_signal_ids") or []),
        "emotion_label_only_selection": False,
        "must_ground_to_input": True,
        "grounding_source_span_ids": evidence_span_ids,
        "personality_claim_allowed": False,
        "target_judgement_agreement_allowed": bool(guard_policy.get("target_judgement_agreement_allowed", False)),
        "target_attack_amplification_allowed": bool(guard_policy.get("target_attack_amplification_allowed", False)),
        "allowed_impression_claims": list(
            selector_meta.get("allowed_impression_claims")
            or [
                "intention_seen_as_care",
                "effort_not_erased",
                "difficulty_is_understood",
                "placed_words_are_received",
            ]
        ),
        "must_not_read_as": ["personality_claim", "diagnosis", "absolute_support", "action_instruction"],
        "completed_reply_generated": False,
        "raw_text_included": False,
    }


def _special_handling(
    *,
    current_input: Any = None,
    frame_projection: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    human_follow_layer: Mapping[str, Any],
) -> dict[str, Any]:
    special_cases = build_emlis_ai_state_answer_special_cases(
        current_input=current_input,
        environment_state_output_frame=frame_projection,
        observation_structure_material=material_meta,
        human_follow_layer=human_follow_layer,
    )
    meta = state_answer_special_cases_forward_meta(special_cases)
    # Keep the Phase 2 public shape (`special_handling.anger/self_denial`) while
    # adding Phase 5 material identity and gate/composer summaries.
    return {
        "schema_version": meta.get("schema_version") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_SCHEMA_VERSION,
        "material_id": meta.get("material_id") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_MATERIAL_ID,
        "source_phase": meta.get("source_phase") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
        "phase": meta.get("phase") or EMLIS_AI_STATE_ANSWER_SPECIAL_CASES_PHASE,
        "state_answer_special_cases_connected": True,
        "state_answer_special_cases_material_only": True,
        "enabled_case_ids": list(meta.get("enabled_case_ids") or []),
        "self_denial": _deepcopy_mapping(_as_mapping(meta.get("self_denial"))),
        "anger": _deepcopy_mapping(_as_mapping(meta.get("anger"))),
        "surface_exception_policy": _deepcopy_mapping(_as_mapping(meta.get("surface_exception_policy"))),
        "gate_policy": _deepcopy_mapping(_as_mapping(meta.get("gate_policy"))),
        "selector_context": _deepcopy_mapping(_as_mapping(meta.get("selector_context"))),
        "state_answer_special_cases_gate_report": state_answer_special_cases_gate_report(meta),
        "state_answer_special_cases_payload": state_answer_special_cases_composer_payload(meta),
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
        "display_gate_relaxed": False,
    }


def _safe_daily_metaphor_payload_for_state_answer(value: Any) -> dict[str, Any]:
    """Composer-facing safe metaphor payload without nested surface_policy.

    Observation-structure composer payloads intentionally keep the upstream
    environment-state projection compact and have a legacy regression that
    forbids surfacing a nested ``surface_policy`` key there.  Phase 6 therefore
    keeps the full safe-metaphor material available through its own module while
    passing only the id/selection/gate-safe subset through the state-answer
    contract payload.
    """

    payload = safe_daily_metaphor_material_composer_payload(value)
    payload.pop("surface_policy", None)
    return payload


def _metaphor_policy(
    *,
    current_input: Any = None,
    frame_projection: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    special_handling: Mapping[str, Any],
) -> dict[str, Any]:
    metaphor_material = build_emlis_ai_safe_daily_metaphor_material(
        current_input=current_input,
        environment_state_output_frame=frame_projection,
        observation_structure_material=material_meta,
        special_handling=special_handling,
    )
    meta = safe_daily_metaphor_material_forward_meta(metaphor_material)
    selection = _as_mapping(meta.get("selection"))
    return {
        "schema_version": meta.get("schema_version") or EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION,
        "material_id": meta.get("material_id") or EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID,
        "source_phase": meta.get("source_phase") or EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE,
        "phase": meta.get("phase") or EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE,
        "mode": selection.get("mode") or meta.get("mode") or "none",
        "allowed_when": list(selection.get("allowed_when") or ["structure_question", "repeated_confusion"]),
        "must_use_safe_daily_analogy": True,
        "free_metaphor_generation_allowed": False,
        "selected_analogy_family": selection.get("selected_analogy_family"),
        "selected_analogy_family_id": selection.get("selected_analogy_family_id"),
        "selected_safe_daily_analogy_id": selection.get("safe_daily_analogy_id"),
        "safe_daily_analogy_id": selection.get("safe_daily_analogy_id"),
        "safe_daily_metaphor_material_connected": True,
        "safe_daily_metaphor_material_only": True,
        "safe_daily_metaphor_material_gate_report": safe_daily_metaphor_material_gate_report(meta),
        "safe_daily_metaphor_material_payload": _safe_daily_metaphor_payload_for_state_answer(meta),
        "safe_daily_metaphor_gate_report": safe_daily_metaphor_material_gate_report(meta),
        "safe_daily_metaphor_payload": _safe_daily_metaphor_payload_for_state_answer(meta),
        "selection": _deepcopy_mapping(selection),
        "gate_policy": _deepcopy_mapping(_as_mapping(meta.get("gate_policy"))),
        "completed_metaphor_sentence_generated": False,
        "fixed_metaphor_template_used": False,
        "free_metaphor_generated": False,
        "action_instruction_allowed": False,
        "metaphor_as_instruction_allowed": False,
        "professional_domain_analogy_allowed": False,
        "medical_domain_analogy_allowed": False,
        "legal_domain_analogy_allowed": False,
        "religious_domain_analogy_allowed": False,
        "political_domain_analogy_allowed": False,
        "aggressive_surface_allowed": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
        "display_gate_relaxed": False,
    }

def _surface_policy(frame_projection: Mapping[str, Any], material_meta: Mapping[str, Any]) -> dict[str, Any]:
    frame_policy = _as_mapping(frame_projection.get("frame_policy"))
    return {
        "must_not_generate_action_instruction": True,
        "must_not_generate_diagnosis": True,
        "must_not_generate_personality_type": True,
        "must_not_generate_cause_from_category": True,
        "must_not_generate_cause_from_emotion_strength": True,
        "must_not_generate_period_tendency_from_single_record": True,
        "must_not_generate_recovery_prescription": True,
        "must_not_generate_over_close_support": True,
        "examples_are_not_runtime_templates": True,
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "fixed_sentence_template_used": False,
        "fixed_sentence_template_added": False,
        "schema_file_materialized": False,
        "public_payload_changed": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "display_gate_relaxed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "single_record_only": True,
        "must_use_scope_marker": bool(frame_policy.get("must_use_scope_marker", True)),
        "forbidden_claims": _dedupe(
            frame_policy.get("forbidden_claims")
            or [
                "personality_tendency",
                "diagnosis",
                "cause_from_category",
                "cause_from_emotion_strength",
                "period_tendency_from_single_record",
                "recovery_prescription",
            ]
        ),
        "environment_state_output_frame_material_id": frame_projection.get("material_id")
        or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
        "observation_structure_material_schema_version": material_meta.get("schema_version") or "",
        "cause_from_category": False,
        "cause_from_emotion_strength": False,
        "period_tendency_from_single_record": False,
        "personality_tendency_allowed": False,
        "recovery_prescription_allowed": False,
    }


def _source(frame_projection: Mapping[str, Any]) -> dict[str, Any]:
    source = _as_mapping(frame_projection.get("source"))
    return {
        "source_kind": source.get("source_kind") or "current_input",
        "source_record_id": _clean(source.get("source_record_id")),
        "selected_at": _clean(source.get("selected_at")),
        "environment_state_output_frame_id": frame_projection.get("material_id") or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    }


def _material_summary(material_meta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": material_meta.get("schema_version") or "",
        "source_phase": material_meta.get("source_phase") or material_meta.get("phase") or "",
        "dictionary_id": material_meta.get("dictionary_id") or "",
        "selected_entry_ids": _dedupe(material_meta.get("selected_entry_ids") or []),
        "selected_relation_ids": _relation_ids_from_material(material_meta),
        "structure_question_ids": _dedupe(material_meta.get("structure_question_ids") or []),
        "matched_source_fields": _dedupe(material_meta.get("matched_source_fields") or []),
        "relation_policy_ids": _dedupe(material_meta.get("relation_policy_ids") or material_meta.get("constraint_ids") or []),
        "low_information_candidate": bool(material_meta.get("low_information_candidate")),
        "dictionary_is_observation_material_only": True,
        "dictionary_returns_completed_reply": False,
        "completed_reply_from_dictionary": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


@dataclass(frozen=True)
class EmlisStateAnswerSurfaceContract:
    """Text-free Phase 2 material consumed by later Composer/Gate phases."""

    source: Mapping[str, Any]
    ratio_policy: Mapping[str, Any]
    observation_layer: Mapping[str, Any]
    human_follow_layer: Mapping[str, Any]
    special_handling: Mapping[str, Any]
    metaphor_policy: Mapping[str, Any]
    surface_policy: Mapping[str, Any]
    environment_state_output_frame: Mapping[str, Any]
    observation_structure_material: Mapping[str, Any]
    schema_version: str = EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION
    material_id: str = EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    internal_name: str = EMLIS_STATE_ANSWER_SURFACE_CONTRACT_INTERNAL_NAME
    phase: str = EMLIS_STATE_ANSWER_SURFACE_CONTRACT_PHASE
    passed: bool = True
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_meta(self) -> dict[str, Any]:
        meta = {
            "schema_version": self.schema_version,
            "version": self.schema_version,
            "material_id": self.material_id,
            "internal_name": self.internal_name,
            "source_phase": self.phase,
            "phase": self.phase,
            "passed": bool(self.passed),
            "evaluated": True,
            "status": "passed" if self.passed else "rejected",
            "rejection_reasons": list(self.rejection_reasons),
            "source": _deepcopy_mapping(self.source),
            "ratio_policy": _deepcopy_mapping(self.ratio_policy),
            "observation_layer": _deepcopy_mapping(self.observation_layer),
            "human_follow_layer": _deepcopy_mapping(self.human_follow_layer),
            "special_handling": _deepcopy_mapping(self.special_handling),
            "metaphor_policy": _deepcopy_mapping(self.metaphor_policy),
            "surface_policy": _deepcopy_mapping(self.surface_policy),
            "environment_state_output_frame": _deepcopy_mapping(self.environment_state_output_frame),
            "observation_structure_material": _deepcopy_mapping(self.observation_structure_material),
            "environment_state_output_frame_connected": bool(self.environment_state_output_frame),
            "observation_structure_material_connected": bool(self.observation_structure_material),
            "state_answer_observation_layer_connected": True,
            "observation_layer_connected": True,
            "human_follow_layer_connected": True,
            "state_answer_surface_contract_connected": True,
            "state_answer_surface_contract_material_only": True,
            "material_is_completed_reply_template": False,
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "fixed_sentence_template_used": False,
            "schema_file_materialized": False,
            "public_payload_changed": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "request_key_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "display_gate_relaxed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
            "personality_tendency_allowed": False,
            "recovery_prescription_allowed": False,
        }
        assert_state_answer_surface_contract(meta)
        return meta

    def gate_report(self) -> dict[str, Any]:
        meta = self.as_meta()
        return {
            "schema_version": meta["schema_version"],
            "material_id": meta["material_id"],
            "passed": meta["passed"],
            "evaluated": True,
            "status": meta["status"],
            "rejection_reasons": meta["rejection_reasons"],
            "state_answer_surface_contract_connected": True,
            "state_answer_surface_contract_material_only": True,
            "environment_state_output_frame_connected": meta["environment_state_output_frame_connected"],
            "observation_structure_material_connected": meta["observation_structure_material_connected"],
            "observation_step_ids": [
                item.get("step_id")
                for item in _as_mapping(meta.get("observation_layer")).get("steps", [])
                if isinstance(item, Mapping)
            ],
            "human_follow_mode": _as_mapping(meta.get("human_follow_layer")).get("follow_mode") or "",
            "primary_follow_key": _as_mapping(meta.get("human_follow_layer")).get("primary_follow_key") or "",
            "human_follow_primary_key": _as_mapping(meta.get("human_follow_layer")).get("primary_follow_key") or "",
            "human_follow_secondary_keys": list(_as_mapping(meta.get("human_follow_layer")).get("secondary_follow_keys") or []),
            "state_answer_ratio_policy_connected": bool(_as_mapping(meta.get("ratio_policy")).get("state_answer_ratio_policy_connected")),
            "state_answer_ratio_policy_material_id": _as_mapping(meta.get("ratio_policy")).get("material_id") or "",
            "state_answer_ratio_policy_schema_version": _as_mapping(meta.get("ratio_policy")).get("schema_version") or "",
            "state_answer_ratio_policy_phase": _as_mapping(meta.get("ratio_policy")).get("phase") or _as_mapping(meta.get("ratio_policy")).get("source_phase") or "",
            "state_answer_ratio_policy_gate_report": state_answer_ratio_policy_gate_report(meta.get("ratio_policy") or {}),
            "resolved_ratio": _deepcopy_mapping(_as_mapping(_as_mapping(meta.get("ratio_policy")).get("resolved_ratio"))),
            "ratio_reason": _as_mapping(_as_mapping(meta.get("ratio_policy")).get("resolved_ratio")).get("reason") or "",
            "state_answer_special_cases_connected": bool(_as_mapping(meta.get("special_handling")).get("state_answer_special_cases_connected")),
            "state_answer_special_cases_material_id": _as_mapping(meta.get("special_handling")).get("material_id") or "",
            "state_answer_special_cases_schema_version": _as_mapping(meta.get("special_handling")).get("schema_version") or "",
            "state_answer_special_cases_phase": _as_mapping(meta.get("special_handling")).get("source_phase") or "",
            "state_answer_special_cases_gate_report": state_answer_special_cases_gate_report(meta.get("special_handling") or {}),
            "safe_daily_metaphor_material_connected": bool(_as_mapping(meta.get("metaphor_policy")).get("safe_daily_metaphor_material_connected")),
            "safe_daily_metaphor_material_id": _as_mapping(meta.get("metaphor_policy")).get("material_id") or "",
            "safe_daily_metaphor_schema_version": _as_mapping(meta.get("metaphor_policy")).get("schema_version") or "",
            "safe_daily_metaphor_phase": _as_mapping(meta.get("metaphor_policy")).get("source_phase") or "",
            "safe_daily_metaphor_material_gate_report": safe_daily_metaphor_material_gate_report(meta.get("metaphor_policy") or {}),
            "safe_daily_metaphor_mode": _as_mapping(meta.get("metaphor_policy")).get("mode") or "none",
            "selected_analogy_family": _as_mapping(meta.get("metaphor_policy")).get("selected_analogy_family"),
            "selected_safe_daily_analogy_id": _as_mapping(meta.get("metaphor_policy")).get("selected_safe_daily_analogy_id"),
            "free_metaphor_generation_allowed": False,
            "completed_metaphor_sentence_generated": False,
            "self_denial_special_handling_enabled": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("self_denial")).get("enabled")),
            "self_denial_identity_claim_is_not_accepted": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("self_denial")).get("identity_claim_is_not_accepted")),
            "self_denial_emlis_impression_has_evidence": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("self_denial")).get("emlis_impression_has_evidence")),
            "anger_special_handling_enabled": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("anger")).get("enabled")),
            "anger_inner_value_line_receiving_allowed": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("anger")).get("inner_value_line_receiving_allowed")),
            "anger_target_judgement_agreement_allowed": False,
            "target_judgement_agreement_allowed": False,
            "target_attack_amplification_allowed": False,
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
            "must_not_generate_action_instruction": True,
            "must_not_generate_diagnosis": True,
            "must_not_generate_personality_type": True,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
            "personality_tendency_allowed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }

    def composer_payload(self) -> dict[str, Any]:
        meta = self.as_meta()
        return {
            "schema_version": meta["schema_version"],
            "material_id": meta["material_id"],
            "source_phase": meta["source_phase"],
            "source": _deepcopy_mapping(meta.get("source")),
            "ratio_policy": state_answer_ratio_policy_composer_payload(meta.get("ratio_policy") or {}),
            "state_answer_ratio_policy_connected": bool(_as_mapping(meta.get("ratio_policy")).get("state_answer_ratio_policy_connected")),
            "state_answer_ratio_policy_material_id": _as_mapping(meta.get("ratio_policy")).get("material_id") or "",
            "state_answer_ratio_policy_schema_version": _as_mapping(meta.get("ratio_policy")).get("schema_version") or "",
            "state_answer_ratio_policy_payload": state_answer_ratio_policy_composer_payload(meta.get("ratio_policy") or {}),
            "observation_layer": _deepcopy_mapping(meta.get("observation_layer")),
            "human_follow_layer": _deepcopy_mapping(meta.get("human_follow_layer")),
            "special_handling": _deepcopy_mapping(meta.get("special_handling")),
            "state_answer_special_cases_connected": bool(_as_mapping(meta.get("special_handling")).get("state_answer_special_cases_connected")),
            "state_answer_special_cases_material_id": _as_mapping(meta.get("special_handling")).get("material_id") or "",
            "state_answer_special_cases_schema_version": _as_mapping(meta.get("special_handling")).get("schema_version") or "",
            "state_answer_special_cases_payload": state_answer_special_cases_composer_payload(meta.get("special_handling") or {}),
            "metaphor_policy": _deepcopy_mapping(meta.get("metaphor_policy")),
            "safe_daily_metaphor_material_connected": bool(_as_mapping(meta.get("metaphor_policy")).get("safe_daily_metaphor_material_connected")),
            "safe_daily_metaphor_material_id": _as_mapping(meta.get("metaphor_policy")).get("material_id") or "",
            "safe_daily_metaphor_schema_version": _as_mapping(meta.get("metaphor_policy")).get("schema_version") or "",
            "safe_daily_metaphor_payload": _safe_daily_metaphor_payload_for_state_answer(meta.get("metaphor_policy") or {}),
            "environment_state_output_frame": _deepcopy_mapping(meta.get("environment_state_output_frame")),
            "observation_structure_material": _deepcopy_mapping(meta.get("observation_structure_material")),
            "state_answer_surface_contract_connected": True,
            "state_answer_surface_contract_material_only": True,
            "dictionary_is_observation_material_only": True,
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "fixed_sentence_template_used": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }


def _coerce_environment_state_output_frame(
    *,
    current_input: Any,
    environment_state_output_frame: Mapping[str, Any] | None,
    selected_relation_ids: Sequence[str],
) -> dict[str, Any]:
    if isinstance(environment_state_output_frame, Mapping):
        return _safe_frame_projection(environment_state_output_frame)
    frame = build_environment_state_output_frame(
        current_input,
        observation_structure_relation_ids=list(selected_relation_ids),
    )
    return _safe_frame_projection(frame)


def _coerce_observation_material(
    *,
    current_input: Any,
    observation_structure_material: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
    selected_relation_ids: Sequence[str] = (),
) -> dict[str, Any]:
    if isinstance(observation_structure_material, Mapping):
        return _material_summary(observation_structure_material)
    if hasattr(observation_structure_material, "as_meta"):
        try:
            return _material_summary(observation_structure_material.as_meta())
        except Exception:
            return _material_summary({"selected_relation_ids": selected_relation_ids})

    try:
        # Lazy import avoids a cycle: observation_structure_material_service
        # imports this module to attach the contract, while standalone callers
        # still need a way to build the upstream observation material.
        from emlis_ai_observation_structure_material_service import (
            build_observation_structure_material,
            observation_structure_material_forward_meta,
        )

        material = build_observation_structure_material(
            current_input=current_input,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
        return observation_structure_material_forward_meta(material)
    except Exception:
        return _material_summary(
            {
                "selected_relation_ids": _dedupe(selected_relation_ids),
                "dictionary_is_observation_material_only": True,
                "dictionary_returns_completed_reply": False,
                "completed_reply_from_dictionary": False,
                "comment_text_generated": False,
                "raw_input_included": False,
                "raw_text_included": False,
            }
        )


def build_emlis_state_answer_surface_contract(
    current_input: Any = None,
    *,
    environment_state_output_frame: Mapping[str, Any] | None = None,
    observation_structure_material: Any = None,
    observation_structure_relation_ids: Sequence[str] | None = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
) -> EmlisStateAnswerSurfaceContract:
    """Build Phase 2 state-answer surface contract from one current input.

    The builder consumes the environment/state/output frame and the observation
    structure material as internal sources.  It returns material for later
    Composer/Gate phases, not public API data and not a completed sentence.
    """

    explicit_relation_ids = _dedupe(observation_structure_relation_ids or [])
    material_meta = _coerce_observation_material(
        current_input=current_input,
        observation_structure_material=observation_structure_material,
        evidence_ledger=evidence_ledger,
        observation_graph=observation_graph,
        selected_relation_ids=explicit_relation_ids,
    )
    selected_relation_ids = _dedupe(explicit_relation_ids + _relation_ids_from_material(material_meta))
    frame_projection = _coerce_environment_state_output_frame(
        current_input=current_input,
        environment_state_output_frame=environment_state_output_frame,
        selected_relation_ids=selected_relation_ids,
    )

    human_follow_layer = _human_follow_layer(frame_projection, material_meta, current_input=current_input)
    ratio_policy = _ratio_policy(
        current_input=current_input,
        frame_projection=frame_projection,
        material_meta=material_meta,
        human_follow_layer=human_follow_layer,
    )
    special_handling = _special_handling(
        current_input=current_input,
        frame_projection=frame_projection,
        material_meta=material_meta,
        human_follow_layer=human_follow_layer,
    )
    metaphor_policy = _metaphor_policy(
        current_input=current_input,
        frame_projection=frame_projection,
        material_meta=material_meta,
        special_handling=special_handling,
    )

    contract = EmlisStateAnswerSurfaceContract(
        source=_source(frame_projection),
        ratio_policy=ratio_policy,
        observation_layer=_observation_layer(frame_projection, material_meta),
        human_follow_layer=human_follow_layer,
        special_handling=special_handling,
        metaphor_policy=metaphor_policy,
        surface_policy=_surface_policy(frame_projection, material_meta),
        environment_state_output_frame=frame_projection,
        observation_structure_material=_material_summary(material_meta),
    )
    assert_state_answer_surface_contract(contract)
    return contract


def state_answer_surface_contract_forward_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerSurfaceContract):
        meta = value.as_meta()
    elif isinstance(value, Mapping):
        meta = dict(value)
    else:
        return {}
    keys = {
        "schema_version",
        "version",
        "material_id",
        "internal_name",
        "source_phase",
        "phase",
        "passed",
        "evaluated",
        "status",
        "rejection_reasons",
        "source",
        "ratio_policy",
        "observation_layer",
        "human_follow_layer",
        "special_handling",
        "metaphor_policy",
        "surface_policy",
        "environment_state_output_frame",
        "observation_structure_material",
        "environment_state_output_frame_connected",
        "observation_structure_material_connected",
        "state_answer_observation_layer_connected",
        "observation_layer_connected",
        "human_follow_layer_connected",
        "state_answer_surface_contract_connected",
        "state_answer_surface_contract_material_only",
        "completed_reply_generated",
        "comment_text_generated",
        "comment_text_included",
        "comment_text_body_included",
        "raw_input_included",
        "raw_text_included",
        "fixed_sentence_template_used",
        "schema_file_materialized",
        "public_payload_changed",
        "public_response_key_added",
        "api_route_changed",
        "request_key_changed",
        "response_key_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "external_ai_used",
        "local_llm_used",
        "cause_from_category",
        "cause_from_emotion_strength",
        "period_tendency_from_single_record",
        "personality_tendency_allowed",
        "recovery_prescription_allowed",
    }
    out = {key: copy.deepcopy(meta.get(key)) for key in keys if key in meta}
    assert_state_answer_surface_contract(out)
    return out


def state_answer_surface_contract_gate_report(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerSurfaceContract):
        report = value.gate_report()
    elif isinstance(value, Mapping):
        meta = state_answer_surface_contract_forward_meta(value)
        if not meta:
            return {}
        observation_layer = _as_mapping(meta.get("observation_layer"))
        human_follow_layer = _as_mapping(meta.get("human_follow_layer"))
        report = {
            "schema_version": meta.get("schema_version") or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
            "material_id": meta.get("material_id") or EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
            "passed": bool(meta.get("passed", True)),
            "evaluated": True,
            "status": meta.get("status") or "passed",
            "rejection_reasons": list(meta.get("rejection_reasons") or []),
            "state_answer_surface_contract_connected": True,
            "state_answer_surface_contract_material_only": True,
            "environment_state_output_frame_connected": bool(meta.get("environment_state_output_frame_connected")),
            "observation_structure_material_connected": bool(meta.get("observation_structure_material_connected")),
            "observation_step_ids": [
                item.get("step_id")
                for item in observation_layer.get("steps", [])
                if isinstance(item, Mapping)
            ],
            "human_follow_mode": human_follow_layer.get("follow_mode") or "",
            "primary_follow_key": human_follow_layer.get("primary_follow_key") or "",
            "human_follow_primary_key": human_follow_layer.get("primary_follow_key") or "",
            "human_follow_secondary_keys": list(human_follow_layer.get("secondary_follow_keys") or []),
            "state_answer_ratio_policy_connected": bool(_as_mapping(meta.get("ratio_policy")).get("state_answer_ratio_policy_connected")),
            "state_answer_ratio_policy_material_id": _as_mapping(meta.get("ratio_policy")).get("material_id") or "",
            "state_answer_ratio_policy_schema_version": _as_mapping(meta.get("ratio_policy")).get("schema_version") or "",
            "state_answer_ratio_policy_phase": _as_mapping(meta.get("ratio_policy")).get("phase") or _as_mapping(meta.get("ratio_policy")).get("source_phase") or "",
            "state_answer_ratio_policy_gate_report": state_answer_ratio_policy_gate_report(meta.get("ratio_policy") or {}),
            "resolved_ratio": _deepcopy_mapping(_as_mapping(_as_mapping(meta.get("ratio_policy")).get("resolved_ratio"))),
            "ratio_reason": _as_mapping(_as_mapping(meta.get("ratio_policy")).get("resolved_ratio")).get("reason") or "",
            "state_answer_special_cases_connected": bool(_as_mapping(meta.get("special_handling")).get("state_answer_special_cases_connected")),
            "state_answer_special_cases_material_id": _as_mapping(meta.get("special_handling")).get("material_id") or "",
            "state_answer_special_cases_schema_version": _as_mapping(meta.get("special_handling")).get("schema_version") or "",
            "state_answer_special_cases_phase": _as_mapping(meta.get("special_handling")).get("source_phase") or "",
            "state_answer_special_cases_gate_report": state_answer_special_cases_gate_report(meta.get("special_handling") or {}),
            "safe_daily_metaphor_material_connected": bool(_as_mapping(meta.get("metaphor_policy")).get("safe_daily_metaphor_material_connected")),
            "safe_daily_metaphor_material_id": _as_mapping(meta.get("metaphor_policy")).get("material_id") or "",
            "safe_daily_metaphor_schema_version": _as_mapping(meta.get("metaphor_policy")).get("schema_version") or "",
            "safe_daily_metaphor_phase": _as_mapping(meta.get("metaphor_policy")).get("source_phase") or "",
            "safe_daily_metaphor_material_gate_report": safe_daily_metaphor_material_gate_report(meta.get("metaphor_policy") or {}),
            "safe_daily_metaphor_mode": _as_mapping(meta.get("metaphor_policy")).get("mode") or "none",
            "selected_analogy_family": _as_mapping(meta.get("metaphor_policy")).get("selected_analogy_family"),
            "selected_safe_daily_analogy_id": _as_mapping(meta.get("metaphor_policy")).get("selected_safe_daily_analogy_id"),
            "free_metaphor_generation_allowed": False,
            "completed_metaphor_sentence_generated": False,
            "self_denial_special_handling_enabled": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("self_denial")).get("enabled")),
            "self_denial_identity_claim_is_not_accepted": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("self_denial")).get("identity_claim_is_not_accepted")),
            "self_denial_emlis_impression_has_evidence": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("self_denial")).get("emlis_impression_has_evidence")),
            "anger_special_handling_enabled": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("anger")).get("enabled")),
            "anger_inner_value_line_receiving_allowed": bool(_as_mapping(_as_mapping(meta.get("special_handling")).get("anger")).get("inner_value_line_receiving_allowed")),
            "anger_target_judgement_agreement_allowed": False,
            "target_judgement_agreement_allowed": False,
            "target_attack_amplification_allowed": False,
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
            "must_not_generate_action_instruction": True,
            "must_not_generate_diagnosis": True,
            "must_not_generate_personality_type": True,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
            "personality_tendency_allowed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
    else:
        return {}
    assert_state_answer_surface_contract(report)
    return report


def state_answer_surface_contract_composer_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerSurfaceContract):
        payload = value.composer_payload()
    elif isinstance(value, Mapping):
        meta = state_answer_surface_contract_forward_meta(value)
        if not meta:
            return {}
        payload = {
            "schema_version": meta.get("schema_version"),
            "material_id": meta.get("material_id"),
            "source_phase": meta.get("source_phase"),
            "source": _deepcopy_mapping(_as_mapping(meta.get("source"))),
            "ratio_policy": state_answer_ratio_policy_composer_payload(meta.get("ratio_policy") or {}),
            "state_answer_ratio_policy_connected": bool(_as_mapping(meta.get("ratio_policy")).get("state_answer_ratio_policy_connected")),
            "state_answer_ratio_policy_material_id": _as_mapping(meta.get("ratio_policy")).get("material_id") or "",
            "state_answer_ratio_policy_schema_version": _as_mapping(meta.get("ratio_policy")).get("schema_version") or "",
            "state_answer_ratio_policy_payload": state_answer_ratio_policy_composer_payload(meta.get("ratio_policy") or {}),
            "observation_layer": _deepcopy_mapping(_as_mapping(meta.get("observation_layer"))),
            "human_follow_layer": _deepcopy_mapping(_as_mapping(meta.get("human_follow_layer"))),
            "special_handling": _deepcopy_mapping(_as_mapping(meta.get("special_handling"))),
            "state_answer_special_cases_connected": bool(_as_mapping(meta.get("special_handling")).get("state_answer_special_cases_connected")),
            "state_answer_special_cases_payload": state_answer_special_cases_composer_payload(meta.get("special_handling") or {}),
            "metaphor_policy": _deepcopy_mapping(_as_mapping(meta.get("metaphor_policy"))),
            "safe_daily_metaphor_material_connected": bool(_as_mapping(meta.get("metaphor_policy")).get("safe_daily_metaphor_material_connected")),
            "safe_daily_metaphor_material_id": _as_mapping(meta.get("metaphor_policy")).get("material_id") or "",
            "safe_daily_metaphor_schema_version": _as_mapping(meta.get("metaphor_policy")).get("schema_version") or "",
            "safe_daily_metaphor_payload": _safe_daily_metaphor_payload_for_state_answer(meta.get("metaphor_policy") or {}),
            "environment_state_output_frame": _deepcopy_mapping(_as_mapping(meta.get("environment_state_output_frame"))),
            "observation_structure_material": _deepcopy_mapping(_as_mapping(meta.get("observation_structure_material"))),
            "state_answer_surface_contract_connected": True,
            "state_answer_surface_contract_material_only": True,
            "dictionary_is_observation_material_only": True,
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "fixed_sentence_template_used": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
    else:
        return {}
    assert_state_answer_surface_contract(payload)
    return payload


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _FORBIDDEN_RAW_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_payload_key(child) for child in value)
    return False


def assert_state_answer_surface_contract(value: Any, *, source: str = "state_answer_surface_contract") -> None:
    if isinstance(value, EmlisStateAnswerSurfaceContract):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    if _clean(value.get("schema_version")) not in {
        "",
        EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
    }:
        raise ValueError(f"{source} has unexpected schema_version")
    if _clean(value.get("material_id")) not in {"", EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID}:
        raise ValueError(f"{source} has unexpected material_id")
    ratio_policy = _as_mapping(value.get("ratio_policy"))
    if ratio_policy:
        if _clean(ratio_policy.get("material_id")) not in {"", EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID}:
            raise ValueError(f"{source} has unexpected state_answer_ratio_policy material_id")
        if _clean(ratio_policy.get("schema_version")) not in {"", EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION}:
            raise ValueError(f"{source} has unexpected state_answer_ratio_policy schema_version")
        resolved = _as_mapping(ratio_policy.get("resolved_ratio"))
        if resolved:
            try:
                observation_ratio = float(resolved.get("observation") or 0.0)
                follow_ratio = float(resolved.get("human_follow") or 0.0)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{source} has invalid resolved_ratio") from exc
            if observation_ratio <= 0.0 or follow_ratio <= 0.0:
                raise ValueError(f"{source} must not resolve observation or follow ratio to zero")

    metaphor_policy = _as_mapping(value.get("metaphor_policy"))
    if metaphor_policy:
        if _clean(metaphor_policy.get("material_id")) not in {"", EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID}:
            raise ValueError(f"{source} has unexpected safe_daily_metaphor material_id")
        if _clean(metaphor_policy.get("schema_version")) not in {"", EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION}:
            raise ValueError(f"{source} has unexpected safe_daily_metaphor schema_version")
        if metaphor_policy.get("free_metaphor_generation_allowed") is True:
            raise ValueError(f"{source} must keep free metaphor generation disabled")
        if metaphor_policy.get("completed_metaphor_sentence_generated") is True:
            raise ValueError(f"{source} must not generate completed metaphor sentences")
        if _clean(metaphor_policy.get("mode")) == "safe_daily_analogy":
            if not _clean(metaphor_policy.get("selected_analogy_family")):
                raise ValueError(f"{source} must keep selected_analogy_family when analogy mode is active")
            if not _clean(metaphor_policy.get("selected_safe_daily_analogy_id") or metaphor_policy.get("safe_daily_analogy_id")):
                raise ValueError(f"{source} must keep selected_safe_daily_analogy_id when analogy mode is active")

    if value.get("material_is_completed_reply_template") is True:
        raise ValueError(f"{source} must not be a completed reply template")
    if value.get("state_answer_surface_contract_connected") is False:
        raise ValueError(f"{source} must keep state_answer_surface_contract_connected=true when present")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


# Project-local aliases for later connection phases.
build_state_answer_surface_contract = build_emlis_state_answer_surface_contract
assert_emlis_state_answer_surface_contract = assert_state_answer_surface_contract

__all__ = [
    "EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION",
    "EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID",
    "EMLIS_STATE_ANSWER_SURFACE_CONTRACT_PHASE",
    "EMLIS_STATE_ANSWER_SURFACE_CONTRACT_INTERNAL_NAME",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE",
    "EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION",
    "EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID",
    "EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE",
    "EmlisStateAnswerSurfaceContract",
    "build_emlis_state_answer_surface_contract",
    "build_state_answer_surface_contract",
    "state_answer_surface_contract_forward_meta",
    "state_answer_surface_contract_gate_report",
    "state_answer_surface_contract_composer_payload",
    "assert_state_answer_surface_contract",
    "assert_emlis_state_answer_surface_contract",
]
