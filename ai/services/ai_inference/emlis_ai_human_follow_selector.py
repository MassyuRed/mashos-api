# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal Follow-4 selector material for EmlisAI state answers.

Phase 3 chooses the human-follow role plan that is later consumed by the
state-answer surface contract / Composer / Gate pipeline.  The selector returns
material roles only: it does not create user-facing ``comment_text``, does not
change public response keys, does not alter API routes or DB names, and does
not turn follow keys into personality claims.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import copy
import json
import re
from typing import Any, Final

from cocolon_environment_state_output_frame import (
    ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    build_environment_state_output_frame,
)
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle

EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION: Final = "cocolon.emlis_ai_human_follow_selector.v1"
EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID: Final = "emlis_ai_human_follow_selector"
EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE: Final = "Phase3_human_follow_selector"
EMLIS_AI_HUMAN_FOLLOW_SELECTOR_INTERNAL_NAME: Final = "EmlisAIフォロー4 Selector"

# Compatibility aliases used by the state-answer surface contract connection.
EMLIS_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION: Final = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION
EMLIS_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID: Final = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID
EMLIS_HUMAN_FOLLOW_SELECTOR_PHASE: Final = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE

FOLLOW_MODE: Final = "emlis_impression_not_fact"

# Canonical Follow-4 keys from the design.  Several input types use companion
# keys, but every selection still exposes one primary slot, two secondary slots,
# and one afterglow slot.
FOLLOW_INTENTION_AFFIRMATION: Final = "intention_affirmation"
FOLLOW_FEAR_OR_LOAD_UNDERSTANDING: Final = "fear_or_load_understanding"
FOLLOW_EFFORT_RECEIVING: Final = "effort_receiving"
FOLLOW_EXISTENCE_RESPECT: Final = "existence_respect"
FOLLOW_IMPORTANT_VALUE_RECEIVING: Final = "important_value_receiving"
FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE: Final = "identity_claim_not_accepted_with_input_evidence"
FOLLOW_RESPONSIBILITY_SCOPE_OBSERVATION: Final = "responsibility_scope_observation"
FOLLOW_REASON_VISIBILITY_RECEIVING: Final = "reason_visibility_receiving"
FOLLOW_NEXT_OBSERVATION_MARGIN: Final = "next_observation_margin"
FOLLOW_SELF_DENIAL_EFFORT_EXISTENCE: Final = "self_denial_effort_and_existence_receiving"
FOLLOW_INTENTION_AND_FEAR: Final = "intention_affirmation_with_fear_understanding"

FOLLOW_KEY_FAMILIES: Final = {
    FOLLOW_INTENTION_AFFIRMATION: {
        "follow4_family": "intention_affirmation",
        "role_kind": "input_intention_receiving",
        "must_not_read_as": ["personality_praise", "virtue_claim", "success_certification"],
    },
    FOLLOW_FEAR_OR_LOAD_UNDERSTANDING: {
        "follow4_family": "fear_or_load_understanding",
        "role_kind": "difficulty_or_load_receiving",
        "must_not_read_as": ["avoidance_justification", "action_instruction", "recovery_prescription"],
    },
    FOLLOW_EFFORT_RECEIVING: {
        "follow4_family": "effort_receiving",
        "role_kind": "input_effort_not_erased",
        "must_not_read_as": ["success_certification", "blanket_praise", "personality_claim"],
    },
    FOLLOW_EXISTENCE_RESPECT: {
        "follow4_family": "existence_respect",
        "role_kind": "placed_words_are_received",
        "must_not_read_as": ["absolute_support", "over_close_support", "identity_claim"],
    },
    FOLLOW_IMPORTANT_VALUE_RECEIVING: {
        "follow4_family": "intention_affirmation",
        "role_kind": "inner_value_line_receiving",
        "must_not_read_as": ["target_judgement_agreement", "target_attack", "personality_claim"],
    },
    FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE: {
        "follow4_family": "effort_receiving",
        "role_kind": "limited_emlis_counter_opinion",
        "must_not_read_as": ["blanket_personality_praise", "absolute_denial", "diagnosis"],
    },
    FOLLOW_RESPONSIBILITY_SCOPE_OBSERVATION: {
        "follow4_family": "fear_or_load_understanding",
        "role_kind": "responsibility_boundary_observation",
        "must_not_read_as": ["fault_assignment", "guilt_amplification", "solution_instruction"],
    },
    FOLLOW_REASON_VISIBILITY_RECEIVING: {
        "follow4_family": "effort_receiving",
        "role_kind": "self_understanding_progress_receiving",
        "must_not_read_as": ["completion_claim", "personality_tendency", "period_tendency"],
    },
    FOLLOW_NEXT_OBSERVATION_MARGIN: {
        "follow4_family": "existence_respect",
        "role_kind": "space_for_next_observation",
        "must_not_read_as": ["action_instruction", "solution", "fixed_advice"],
    },
    FOLLOW_SELF_DENIAL_EFFORT_EXISTENCE: {
        "follow4_family": "effort_receiving_plus_existence_respect",
        "role_kind": "self_denial_strong_follow_primary",
        "must_not_read_as": ["blanket_personality_praise", "absolute_support", "identity_claim"],
    },
    FOLLOW_INTENTION_AND_FEAR: {
        "follow4_family": "intention_affirmation_plus_fear_understanding",
        "role_kind": "ambivalence_primary_follow",
        "must_not_read_as": ["choice_instruction", "solution", "personality_claim"],
    },
}

_ALLOWED_FOLLOW_KEYS: Final = frozenset(FOLLOW_KEY_FAMILIES)
_STRONG_FOLLOW_INPUT_TYPES: Final = frozenset(
    {
        "self_denial",
        "anger",
        "sadness",
        "loneliness",
        "exhaustion",
    }
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
        "comment_text_generated",
        "comment_text_included",
        "completed_reply_generated",
        "db_physical_name_changed",
        "display_gate_relaxed",
        "external_ai_used",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_used",
        "local_llm_used",
        "period_tendency_from_single_record",
        "personality_claim_allowed",
        "personality_tendency_allowed",
        "public_payload_changed",
        "public_response_key_added",
        "public_response_key_change",
        "public_status_extended",
        "raw_input_included",
        "raw_text_included",
        "response_key_changed",
        "rn_visible_contract_changed",
        "schema_file_materialized",
        "target_judgement_agreement_allowed",
        "target_attack_amplification_allowed",
    }
)

_SPACE_RE: Final = re.compile(r"\s+")
_SELF_DENIAL_RE: Final = re.compile(
    r"(自分(?:なんか|など|は)?[^。！？!?]{0,18}(?:嫌い|きらい|ダメ|だめ|価値がない|価値ない|いらない|最低|クズ|消えたい|死にたい|生きてる意味|生きる意味)|"
    r"(?:私|わたし|俺|僕)(?:なんか|など)[^。！？!?]{0,18}(?:ダメ|だめ|いらない|価値がない|価値ない)|"
    r"(?:全部|すべて)(?:自分|私|俺|僕)が悪い)"
)
_ANGER_RE: Final = re.compile(r"(怒り|腹が立|腹立|ムカつ|むかつ|イライラ|いらいら|許せない|理不尽|不公平)")
_SADNESS_RE: Final = re.compile(r"(悲し|つらい|辛い|泣きたい|喪失|失った|失う|苦しい)")
_LONELINESS_RE: Final = re.compile(r"(孤独|ひとりぼっち|一人ぼっち|寂し|さみし|誰にも言えない)")
_EXHAUSTION_RE: Final = re.compile(r"(疲れ|疲労|消耗|へとへと|ぐったり|くたくた|何もできない|動けない|もう無理)")
_GUILT_RE: Final = re.compile(r"(罪悪感|申し訳|ごめん|自分のせい|悪いことをした|責任を感じ)")
_AMBIVALENCE_RE: Final = re.compile(r"(迷い|迷って|どうしたら|どうすれば|決められ|選べない|わからない|分からない|悩んで)")
_JOY_RE: Final = re.compile(r"(嬉し|うれし|喜び|楽しか|安心|達成|できた|ほっと|よかった|良かった)")
_SELF_UNDERSTANDING_RE: Final = re.compile(r"(自己理解|理由が.*(?:見え|わか|分か)|納得|整理でき|気づいた)")

_INPUT_TYPE_ORDER: Final = (
    "self_denial",
    "anger",
    "loneliness",
    "sadness",
    "exhaustion",
    "guilt",
    "self_understanding",
    "joy_or_relief",
    "ambivalence",
    "anxiety",
    "standard_state_answer",
)

_INPUT_TYPE_FOLLOW_PLAN: Final = {
    "anxiety": {
        "primary_follow_key": FOLLOW_FEAR_OR_LOAD_UNDERSTANDING,
        "secondary_follow_keys": [FOLLOW_EFFORT_RECEIVING, FOLLOW_EXISTENCE_RESPECT],
        "afterglow_follow_key": FOLLOW_INTENTION_AFFIRMATION,
        "reason": "anxiety_or_uncertainty_input",
    },
    "anger": {
        "primary_follow_key": FOLLOW_IMPORTANT_VALUE_RECEIVING,
        "secondary_follow_keys": [FOLLOW_FEAR_OR_LOAD_UNDERSTANDING, FOLLOW_EXISTENCE_RESPECT],
        "afterglow_follow_key": FOLLOW_EFFORT_RECEIVING,
        "reason": "anger_inner_value_line_without_target_agreement",
    },
    "sadness": {
        "primary_follow_key": FOLLOW_EXISTENCE_RESPECT,
        "secondary_follow_keys": [FOLLOW_EFFORT_RECEIVING, FOLLOW_IMPORTANT_VALUE_RECEIVING],
        "afterglow_follow_key": FOLLOW_FEAR_OR_LOAD_UNDERSTANDING,
        "reason": "sadness_or_grief_receivable_temperature",
    },
    "self_denial": {
        "primary_follow_key": FOLLOW_SELF_DENIAL_EFFORT_EXISTENCE,
        "secondary_follow_keys": [FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE, FOLLOW_INTENTION_AFFIRMATION],
        "afterglow_follow_key": FOLLOW_EXISTENCE_RESPECT,
        "reason": "self_denial_separate_felt_state_from_identity_claim",
    },
    "ambivalence": {
        "primary_follow_key": FOLLOW_INTENTION_AND_FEAR,
        "secondary_follow_keys": [FOLLOW_EXISTENCE_RESPECT, FOLLOW_FEAR_OR_LOAD_UNDERSTANDING],
        "afterglow_follow_key": FOLLOW_EFFORT_RECEIVING,
        "reason": "ambivalence_intention_and_fear",
    },
    "guilt": {
        "primary_follow_key": FOLLOW_INTENTION_AFFIRMATION,
        "secondary_follow_keys": [FOLLOW_RESPONSIBILITY_SCOPE_OBSERVATION, FOLLOW_FEAR_OR_LOAD_UNDERSTANDING],
        "afterglow_follow_key": FOLLOW_EXISTENCE_RESPECT,
        "reason": "guilt_responsibility_scope_without_fault_assignment",
    },
    "loneliness": {
        "primary_follow_key": FOLLOW_EXISTENCE_RESPECT,
        "secondary_follow_keys": [FOLLOW_FEAR_OR_LOAD_UNDERSTANDING, FOLLOW_EFFORT_RECEIVING],
        "afterglow_follow_key": FOLLOW_INTENTION_AFFIRMATION,
        "reason": "loneliness_or_missing_connection",
    },
    "exhaustion": {
        "primary_follow_key": FOLLOW_EFFORT_RECEIVING,
        "secondary_follow_keys": [FOLLOW_EXISTENCE_RESPECT, FOLLOW_FEAR_OR_LOAD_UNDERSTANDING],
        "afterglow_follow_key": FOLLOW_INTENTION_AFFIRMATION,
        "reason": "exhaustion_or_load_accumulation",
    },
    "joy_or_relief": {
        "primary_follow_key": FOLLOW_EFFORT_RECEIVING,
        "secondary_follow_keys": [FOLLOW_INTENTION_AFFIRMATION, FOLLOW_EXISTENCE_RESPECT],
        "afterglow_follow_key": FOLLOW_NEXT_OBSERVATION_MARGIN,
        "reason": "joy_relief_or_progress",
    },
    "self_understanding": {
        "primary_follow_key": FOLLOW_REASON_VISIBILITY_RECEIVING,
        "secondary_follow_keys": [FOLLOW_EFFORT_RECEIVING, FOLLOW_EXISTENCE_RESPECT],
        "afterglow_follow_key": FOLLOW_NEXT_OBSERVATION_MARGIN,
        "reason": "self_understanding_reason_visibility",
    },
    "standard_state_answer": {
        "primary_follow_key": FOLLOW_FEAR_OR_LOAD_UNDERSTANDING,
        "secondary_follow_keys": [FOLLOW_INTENTION_AFFIRMATION, FOLLOW_EFFORT_RECEIVING],
        "afterglow_follow_key": FOLLOW_EXISTENCE_RESPECT,
        "reason": "standard_state_answer_default",
    },
}


def _allowed_impression_claims_for_keys(keys: Sequence[str]) -> list[str]:
    claim_by_key = {
        FOLLOW_INTENTION_AFFIRMATION: "intention_seen_as_care",
        FOLLOW_FEAR_OR_LOAD_UNDERSTANDING: "difficulty_is_understood",
        FOLLOW_EFFORT_RECEIVING: "effort_not_erased",
        FOLLOW_EXISTENCE_RESPECT: "placed_words_are_received",
        FOLLOW_IMPORTANT_VALUE_RECEIVING: "valued_line_seen_without_target_judgement",
        FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE: "identity_claim_not_accepted_as_fact",
        FOLLOW_RESPONSIBILITY_SCOPE_OBSERVATION: "responsibility_scope_not_overexpanded",
        FOLLOW_REASON_VISIBILITY_RECEIVING: "reason_seen_not_erased",
        FOLLOW_NEXT_OBSERVATION_MARGIN: "next_observation_margin_left",
        FOLLOW_SELF_DENIAL_EFFORT_EXISTENCE: "effort_and_existence_not_erased",
        FOLLOW_INTENTION_AND_FEAR: "intention_and_difficulty_both_seen",
    }
    return _dedupe(claim_by_key.get(key) for key in keys)


def _surface_risk_ids_for_input_type(input_type: str) -> list[str]:
    if input_type == "self_denial":
        return ["identity_claim_risk", "strong_follow_temperature"]
    if input_type == "anger":
        return ["target_judgement_agreement_risk", "strong_follow_temperature"]
    if input_type in {"sadness", "loneliness", "exhaustion"}:
        return ["observation_temperature_risk", "strong_follow_temperature"]
    if input_type == "guilt":
        return ["responsibility_overreach_risk"]
    if input_type == "ambivalence":
        return ["action_instruction_risk"]
    return []


def _detected_input_signal_ids(selection: Mapping[str, Any]) -> list[str]:
    basis = _dedupe(selection.get("selector_basis") or [])
    input_type = _clean(selection.get("input_type"))
    signals = [f"{input_type}_selector" if input_type else "standard_selector"]
    signals.extend(basis)
    return _dedupe(signals)


@dataclass(frozen=True)
class EmlisHumanFollowSelection:
    """Text-free Follow-4 selector result for one current input."""

    source: Mapping[str, Any]
    selector_input_summary: Mapping[str, Any]
    selection: Mapping[str, Any]
    follow_key_slots: Sequence[Mapping[str, Any]]
    guard_policy: Mapping[str, Any]
    environment_state_output_frame: Mapping[str, Any]
    observation_structure_material: Mapping[str, Any]
    schema_version: str = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION
    material_id: str = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID
    internal_name: str = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_INTERNAL_NAME
    phase: str = EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE
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
            "selector_input_summary": _deepcopy_mapping(self.selector_input_summary),
            "selection": _deepcopy_mapping(self.selection),
            "input_type": self.selection.get("input_type") or "standard_state_answer",
            "input_type_candidates": copy.deepcopy(list(self.selection.get("input_type_candidates") or [])),
            "selector_basis": _dedupe(self.selection.get("selector_basis") or []),
            "detected_input_signal_ids": _detected_input_signal_ids(self.selection),
            "surface_risk_ids": _surface_risk_ids_for_input_type(_clean(self.selection.get("input_type"))),
            "allowed_impression_claims": _allowed_impression_claims_for_keys(
                [
                    self.selection.get("primary_follow_key"),
                    *(self.selection.get("secondary_follow_keys") or []),
                    self.selection.get("afterglow_follow_key"),
                ]
            ),
            "follow_key_slots": copy.deepcopy(list(self.follow_key_slots or [])),
            "guard_policy": _deepcopy_mapping(self.guard_policy),
            "environment_state_output_frame": _deepcopy_mapping(self.environment_state_output_frame),
            "observation_structure_material": _deepcopy_mapping(self.observation_structure_material),
            "environment_state_output_frame_connected": bool(self.environment_state_output_frame),
            "observation_structure_material_connected": bool(self.observation_structure_material),
            "human_follow_selector_connected": True,
            "human_follow_selector_material_only": True,
            "follow_key_slots_count": len(list(self.follow_key_slots or [])),
            "primary_follow_key": self.selection.get("primary_follow_key") or "",
            "secondary_follow_keys": list(self.selection.get("secondary_follow_keys") or []),
            "afterglow_follow_key": self.selection.get("afterglow_follow_key") or "",
            "follow_mode": self.selection.get("follow_mode") or FOLLOW_MODE,
            "strong_follow_candidate": bool(self.selection.get("strong_follow_candidate")),
            "emotion_label_only_selection": False,
            "material_is_completed_reply_template": False,
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
            "display_gate_relaxed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "personality_claim_allowed": False,
            "personality_tendency_allowed": False,
            "target_judgement_agreement_allowed": False,
            "target_attack_amplification_allowed": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
        }
        assert_human_follow_selection_contract(meta)
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
            "human_follow_selector_connected": True,
            "human_follow_selector_material_only": True,
            "input_type": meta["selection"].get("input_type") or "",
            "primary_follow_key": meta["primary_follow_key"],
            "secondary_follow_keys": meta["secondary_follow_keys"],
            "afterglow_follow_key": meta["afterglow_follow_key"],
            "follow_key_slots_count": meta["follow_key_slots_count"],
            "strong_follow_candidate": meta["strong_follow_candidate"],
            "emotion_label_only_selection": False,
            "follow_mode": FOLLOW_MODE,
            "personality_claim_allowed": False,
            "target_judgement_agreement_allowed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
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
            "selection": _deepcopy_mapping(meta.get("selection")),
            "follow_key_slots": copy.deepcopy(list(meta.get("follow_key_slots") or [])),
            "guard_policy": _deepcopy_mapping(meta.get("guard_policy")),
            "selector_input_summary": _deepcopy_mapping(meta.get("selector_input_summary")),
            "allowed_impression_claims": list(meta.get("allowed_impression_claims") or []),
            "detected_input_signal_ids": list(meta.get("detected_input_signal_ids") or []),
            "surface_risk_ids": list(meta.get("surface_risk_ids") or []),
            "human_follow_selector_connected": True,
            "human_follow_selector_material_only": True,
            "follow_mode": FOLLOW_MODE,
            "personality_claim_allowed": False,
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


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _deepcopy_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return copy.deepcopy(dict(value or {}))


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
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _coerce_environment_state_output_frame(
    *,
    current_input: Any,
    environment_state_output_frame: Mapping[str, Any] | None,
    relation_ids: Sequence[str],
) -> dict[str, Any]:
    if isinstance(environment_state_output_frame, Mapping):
        return copy.deepcopy(dict(environment_state_output_frame))
    return build_environment_state_output_frame(
        current_input or {},
        observation_structure_relation_ids=list(relation_ids),
    )


def _material_summary(value: Any) -> dict[str, Any]:
    if hasattr(value, "as_meta"):
        try:
            value = value.as_meta()
        except Exception:
            value = {}
    material = _as_mapping(value)
    return {
        "schema_version": _clean(material.get("schema_version")),
        "source_phase": _clean(material.get("source_phase") or material.get("phase")),
        "selected_relation_ids": _dedupe(
            material.get("selected_relation_ids")
            or material.get("structure_relation_ids")
            or material.get("graph_relation_ids")
            or []
        ),
        "graph_relation_ids": _dedupe(material.get("graph_relation_ids") or []),
        "relation_policy_ids": _dedupe(material.get("relation_policy_ids") or material.get("constraint_ids") or []),
        "structure_question_ids": _dedupe(material.get("structure_question_ids") or []),
        "selected_entry_types": _dedupe(material.get("selected_entry_types") or []),
        "low_information_candidate": bool(material.get("low_information_candidate")),
        "dictionary_is_observation_material_only": True,
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _frame_source(frame: Mapping[str, Any]) -> dict[str, Any]:
    source = _as_mapping(frame.get("source"))
    return {
        "source_kind": source.get("source_kind") or "current_input",
        "source_record_id": _clean(source.get("source_record_id")),
        "selected_at": _clean(source.get("selected_at")),
        "environment_state_output_frame_id": _clean(frame.get("material_id")) or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    }


def _emotion_labels(frame: Mapping[str, Any]) -> list[dict[str, str]]:
    state_axis = _as_mapping(frame.get("state_axis"))
    out: list[dict[str, str]] = []
    for item in state_axis.get("emotion_labels") or []:
        if not isinstance(item, Mapping):
            continue
        emotion_type = _clean(item.get("type"))
        if not emotion_type:
            continue
        out.append(
            {
                "type": emotion_type,
                "strength": _clean(item.get("strength")),
                "read_as": "state_label",
                "must_not_read_as": "diagnosis",
            }
        )
    return out


def _emotion_types(frame: Mapping[str, Any]) -> list[str]:
    return _dedupe(item.get("type") for item in _emotion_labels(frame))


def _strength_summary(frame: Mapping[str, Any]) -> dict[str, Any]:
    state_axis = _as_mapping(frame.get("state_axis"))
    summary = _as_mapping(state_axis.get("strength_summary"))
    return {
        "primary_type": _clean(summary.get("primary_type")),
        "primary_strength": _clean(summary.get("primary_strength")),
        "strongest_type": _clean(summary.get("strongest_type")),
        "strongest_strength": _clean(summary.get("strongest_strength")),
        "has_strong": bool(summary.get("has_strong")),
        "max_strength_score": int(summary.get("max_strength_score") or 0),
    }


def _output_theme_ids(frame: Mapping[str, Any]) -> list[str]:
    output_axis = _as_mapping(frame.get("output_axis"))
    candidates = output_axis.get("output_theme_candidates") or []
    if not candidates and output_axis.get("output_theme_ids"):
        return _dedupe(output_axis.get("output_theme_ids") or [])
    ids: list[str] = []
    for item in candidates:
        if isinstance(item, Mapping):
            ids.extend(_dedupe(item.get("theme_id")))
    return _dedupe(ids)


def _category_labels(frame: Mapping[str, Any]) -> list[str]:
    env = _as_mapping(frame.get("environment_axis"))
    labels: list[str] = []
    for item in env.get("category_labels") or []:
        if isinstance(item, Mapping):
            labels.extend(_dedupe(item.get("label")))
    return _dedupe(labels)


def _relation_ids(frame: Mapping[str, Any], material: Mapping[str, Any], explicit_relation_ids: Sequence[str]) -> list[str]:
    bridge = _as_mapping(frame.get("observation_structure_bridge"))
    return _dedupe(
        list(explicit_relation_ids or [])
        + list(material.get("selected_relation_ids") or [])
        + list(material.get("graph_relation_ids") or [])
        + list(bridge.get("selected_relation_ids") or [])
    )


def _bundle_signal(current_input: Any) -> dict[str, Any]:
    if current_input is None:
        return {
            "self_denial_signal": False,
            "anger_signal": False,
            "sadness_signal": False,
            "loneliness_signal": False,
            "exhaustion_signal": False,
            "guilt_signal": False,
            "ambivalence_signal": False,
            "joy_or_relief_signal": False,
            "self_understanding_signal": False,
        }
    bundle = build_emlis_current_input_bundle(current_input)
    # Internal-only classification source.  The returned material never exposes
    # this string or any raw span.
    combined = "\n".join(
        part
        for part in [
            bundle.thought_text,
            bundle.action_text,
            " ".join(bundle.categories),
            " ".join(emotion.type for emotion in bundle.emotions),
        ]
        if part
    )
    return {
        "self_denial_signal": bool(_SELF_DENIAL_RE.search(combined)),
        "anger_signal": bool(_ANGER_RE.search(combined)),
        "sadness_signal": bool(_SADNESS_RE.search(combined)),
        "loneliness_signal": bool(_LONELINESS_RE.search(combined)),
        "exhaustion_signal": bool(_EXHAUSTION_RE.search(combined)),
        "guilt_signal": bool(_GUILT_RE.search(combined)),
        "ambivalence_signal": bool(_AMBIVALENCE_RE.search(combined)),
        "joy_or_relief_signal": bool(_JOY_RE.search(combined)),
        "self_understanding_signal": bool(_SELF_UNDERSTANDING_RE.search(combined)),
    }


def _score_candidates(
    *,
    emotion_types: Sequence[str],
    output_theme_ids: Sequence[str],
    relation_ids: Sequence[str],
    category_labels: Sequence[str],
    strength_summary: Mapping[str, Any],
    material: Mapping[str, Any],
    bundle_signal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    emotions = " ".join(emotion_types)
    themes = set(output_theme_ids)
    relations = set(relation_ids)
    categories = " ".join(category_labels)

    def add(candidates: list[dict[str, Any]], input_type: str, points: int, basis: Sequence[str]) -> None:
        if points <= 0:
            return
        candidates.append(
            {
                "input_type": input_type,
                "score": int(points),
                "basis": _dedupe(basis),
            }
        )

    scored: list[dict[str, Any]] = []

    add(scored, "self_denial", 22 if bundle_signal.get("self_denial_signal") else 0, ["current_input_internal_signal"])
    add(scored, "self_denial", 18 if any(term in emotions for term in ("自己否定", "自責", "無価値")) else 0, ["emotion_labels"])

    add(scored, "anger", 11 if any(term in emotions for term in ("怒り", "苛立ち", "イライラ")) else 0, ["emotion_labels"])
    add(scored, "anger", 6 if "unfairness_concern" in themes else 0, ["output_theme_candidates"])
    add(scored, "anger", 5 if any(rid in relations for rid in ("priority_pressure", "pressure_gap")) and bundle_signal.get("anger_signal") else 0, ["relation_role_ids", "current_input_internal_signal"])

    add(scored, "sadness", 10 if any(term in emotions for term in ("悲しみ", "悲しい", "喪失")) else 0, ["emotion_labels"])
    add(scored, "sadness", 6 if bundle_signal.get("sadness_signal") else 0, ["current_input_internal_signal"])

    add(scored, "loneliness", 10 if any(term in emotions for term in ("孤独", "寂しさ", "さみしさ", "寂しい")) else 0, ["emotion_labels"])
    add(scored, "loneliness", 20 if bundle_signal.get("loneliness_signal") else 0, ["current_input_internal_signal"])
    add(scored, "loneliness", 4 if "relation_loss_concern" in themes else 0, ["output_theme_candidates"])

    add(scored, "exhaustion", 10 if any(term in emotions for term in ("疲れ", "疲労", "消耗", "しんどい")) else 0, ["emotion_labels"])
    add(scored, "exhaustion", 6 if bundle_signal.get("exhaustion_signal") else 0, ["current_input_internal_signal"])
    add(scored, "exhaustion", 5 if any(rid in relations for rid in ("load_accumulation", "action_blocked")) else 0, ["relation_role_ids"])

    add(scored, "guilt", 10 if any(term in emotions for term in ("罪悪感", "申し訳なさ", "後悔")) else 0, ["emotion_labels"])
    add(scored, "guilt", 12 if bundle_signal.get("guilt_signal") else 0, ["current_input_internal_signal"])

    add(scored, "self_understanding", 12 if any(term in emotions for term in ("自己理解", "気づき")) else 0, ["emotion_labels"])
    add(scored, "self_understanding", 7 if "reason_became_visible" in themes else 0, ["output_theme_candidates"])
    add(scored, "self_understanding", 7 if "self_insight_discovery" in relations else 0, ["relation_role_ids"])
    add(scored, "self_understanding", 5 if bundle_signal.get("self_understanding_signal") else 0, ["current_input_internal_signal"])

    add(scored, "joy_or_relief", 10 if any(term in emotions for term in ("喜び", "嬉しい", "安心", "達成", "平穏")) else 0, ["emotion_labels"])
    add(scored, "joy_or_relief", 5 if bundle_signal.get("joy_or_relief_signal") else 0, ["current_input_internal_signal"])

    add(scored, "ambivalence", 8 if any(term in emotions for term in ("迷い", "葛藤", "困惑")) else 0, ["emotion_labels"])
    add(scored, "ambivalence", 6 if "direction_concern" in themes or "unformed_self_insight" in themes else 0, ["output_theme_candidates"])
    add(scored, "ambivalence", 6 if any(rid in relations for rid in ("thought_action_discrepancy", "unformed_self_insight", "category_parallel")) else 0, ["relation_role_ids"])
    add(scored, "ambivalence", 10 if bundle_signal.get("ambivalence_signal") else 0, ["current_input_internal_signal"])

    add(scored, "anxiety", 8 if any(term in emotions for term in ("不安", "恐れ", "怖さ", "焦り")) else 0, ["emotion_labels"])
    add(
        scored,
        "anxiety",
        6
        if themes.intersection(
            {
                "continuation_concern",
                "relation_loss_concern",
                "maintenance_concern",
                "direction_concern",
            }
        )
        else 0,
        ["output_theme_candidates"],
    )
    add(scored, "anxiety", 5 if any(rid in relations for rid in ("pressure_gap", "action_blocked", "state_text_gap")) else 0, ["relation_role_ids"])

    if material.get("low_information_candidate") and strength_summary.get("has_strong"):
        add(scored, "sadness", 3, ["low_information_candidate", "emotion_strength_context"])

    if not scored:
        scored.append(
            {
                "input_type": "standard_state_answer",
                "score": 1,
                "basis": _dedupe(
                    [
                        "environment_axis" if categories else "",
                        "emotion_labels" if emotion_types else "",
                        "output_theme_candidates" if output_theme_ids else "",
                        "relation_role_ids" if relation_ids else "",
                    ]
                )
                or ["standard_default"],
            }
        )

    grouped: dict[str, dict[str, Any]] = {}
    for item in scored:
        input_type = _clean(item.get("input_type"))
        if not input_type:
            continue
        existing = grouped.setdefault(input_type, {"input_type": input_type, "score": 0, "basis": []})
        existing["score"] += int(item.get("score") or 0)
        existing["basis"] = _dedupe(list(existing.get("basis") or []) + list(item.get("basis") or []))

    order = {input_type: index for index, input_type in enumerate(_INPUT_TYPE_ORDER)}
    candidates = list(grouped.values())
    candidates.sort(key=lambda item: (-int(item.get("score") or 0), order.get(str(item.get("input_type")), 999)))
    return candidates


def _selected_input_type(candidates: Sequence[Mapping[str, Any]]) -> str:
    if not candidates:
        return "standard_state_answer"
    value = _clean(candidates[0].get("input_type"))
    return value if value in _INPUT_TYPE_FOLLOW_PLAN else "standard_state_answer"


def _follow_slot(slot: str, key: str, *, order: int, source_basis: Sequence[str]) -> dict[str, Any]:
    family = FOLLOW_KEY_FAMILIES.get(key, {})
    return {
        "slot": slot,
        "order": int(order),
        "follow_key": key,
        "follow4_family": family.get("follow4_family") or key,
        "role_kind": family.get("role_kind") or "human_follow_material_role",
        "section_role": "human_follow",
        "follow_mode": FOLLOW_MODE,
        "source_basis": _dedupe(source_basis),
        "must_ground_to_input": True,
        "personality_claim_allowed": False,
        "must_not_read_as": _dedupe(
            family.get("must_not_read_as")
            or ["personality_claim", "diagnosis", "action_instruction", "absolute_support"]
        ),
        "completed_reply_generated": False,
        "raw_text_included": False,
    }


def _follow_key_slots(selection: Mapping[str, Any], *, basis: Sequence[str]) -> list[dict[str, Any]]:
    primary = _clean(selection.get("primary_follow_key"))
    secondaries = _dedupe(selection.get("secondary_follow_keys") or [])[:2]
    while len(secondaries) < 2:
        fallback = FOLLOW_EXISTENCE_RESPECT if FOLLOW_EXISTENCE_RESPECT not in [primary, *secondaries] else FOLLOW_EFFORT_RECEIVING
        secondaries.append(fallback)
        secondaries = _dedupe(secondaries)
    afterglow = _clean(selection.get("afterglow_follow_key")) or FOLLOW_EXISTENCE_RESPECT
    return [
        _follow_slot("primary", primary, order=1, source_basis=basis),
        _follow_slot("secondary", secondaries[0], order=2, source_basis=basis),
        _follow_slot("secondary", secondaries[1], order=3, source_basis=basis),
        _follow_slot("afterglow", afterglow, order=4, source_basis=basis),
    ]


def _guard_policy(input_type: str) -> dict[str, Any]:
    return {
        "follow_mode": FOLLOW_MODE,
        "follow_keys_are_material_roles": True,
        "must_ground_to_input": True,
        "personality_claim_allowed": False,
        "personality_tendency_allowed": False,
        "blanket_personality_praise_allowed": False,
        "absolute_support_allowed": False,
        "action_instruction_allowed": False,
        "diagnosis_allowed": False,
        "category_is_topic_direction_not_cause": True,
        "emotion_strength_affects_weight_only": True,
        "cause_from_category": False,
        "cause_from_emotion_strength": False,
        "period_tendency_from_single_record": False,
        "anger_target_judgement_agreement_allowed": False,
        "target_judgement_agreement_allowed": False,
        "target_attack_amplification_allowed": False,
        "self_denial_identity_claim_as_fact_allowed": False,
        "self_denial_requires_evidence_for_counter_opinion": input_type == "self_denial",
        "limited_counter_opinion_allowed": input_type == "self_denial",
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_payload_changed": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }


def _selector_input_summary(
    *,
    frame: Mapping[str, Any],
    material: Mapping[str, Any],
    relation_ids: Sequence[str],
    emotion_labels: Sequence[Mapping[str, str]],
    output_theme_ids: Sequence[str],
    category_labels: Sequence[str],
    strength_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "axis_presence": _deepcopy_mapping(_as_mapping(frame.get("axis_presence"))),
        "emotion_labels": copy.deepcopy(list(emotion_labels)),
        "emotion_types": _dedupe([item.get("type") for item in emotion_labels]),
        "strength_summary": _deepcopy_mapping(strength_summary),
        "output_theme_ids": _dedupe(output_theme_ids),
        "relation_role_ids": _dedupe(relation_ids),
        "category_topic_labels": _dedupe(category_labels),
        "structure_question_ids": _dedupe(material.get("structure_question_ids") or []),
        "low_information_candidate": bool(material.get("low_information_candidate")),
        "uses_environment_state_output_frame": True,
        "uses_output_theme_candidates": bool(output_theme_ids),
        "uses_relation_role_ids": bool(relation_ids),
        "emotion_label_only_selection": False,
        "category_read_as": "topic_direction_not_cause",
        "emotion_strength_read_as": "state_weight_not_cause",
        "single_record_only": True,
        "raw_text_included": False,
    }


def build_emlis_ai_human_follow_selection(
    current_input: Any = None,
    *,
    environment_state_output_frame: Mapping[str, Any] | None = None,
    observation_structure_material: Any = None,
    relation_role_ids: Sequence[str] | None = None,
) -> EmlisHumanFollowSelection:
    """Build the Phase 3 Follow-4 selector material.

    Selection uses emotion labels together with the environment/state/output
    frame's output-theme candidates and observation relation ids.  The result is
    a role plan, not a completed user-facing sentence.
    """

    material = _material_summary(observation_structure_material)
    explicit_relation_ids = _dedupe(relation_role_ids or [])
    provisional_relations = _dedupe(explicit_relation_ids + list(material.get("selected_relation_ids") or []))
    frame = _coerce_environment_state_output_frame(
        current_input=current_input,
        environment_state_output_frame=environment_state_output_frame,
        relation_ids=provisional_relations,
    )
    relations = _relation_ids(frame, material, explicit_relation_ids)
    emotions = _emotion_labels(frame)
    emotion_types = _emotion_types(frame)
    themes = _output_theme_ids(frame)
    categories = _category_labels(frame)
    strength = _strength_summary(frame)
    bundle_signals = _bundle_signal(current_input)
    candidates = _score_candidates(
        emotion_types=emotion_types,
        output_theme_ids=themes,
        relation_ids=relations,
        category_labels=categories,
        strength_summary=strength,
        material=material,
        bundle_signal=bundle_signals,
    )
    input_type = _selected_input_type(candidates)
    plan = copy.deepcopy(dict(_INPUT_TYPE_FOLLOW_PLAN.get(input_type) or _INPUT_TYPE_FOLLOW_PLAN["standard_state_answer"]))
    primary = _clean(plan.get("primary_follow_key"))
    secondaries = _dedupe(plan.get("secondary_follow_keys") or [])[:2]
    afterglow = _clean(plan.get("afterglow_follow_key"))
    basis = _dedupe(candidates[0].get("basis") if candidates else [])
    if themes and "output_theme_candidates" not in basis:
        basis.append("output_theme_candidates")
    if relations and "relation_role_ids" not in basis:
        basis.append("relation_role_ids")
    if emotion_types and "emotion_labels" not in basis:
        basis.append("emotion_labels")
    basis = _dedupe(basis)

    selection = {
        "input_type": input_type,
        "input_type_candidates": copy.deepcopy(candidates),
        "primary_follow_key": primary,
        "secondary_follow_keys": secondaries,
        "afterglow_follow_key": afterglow,
        "follow_mode": FOLLOW_MODE,
        "selector_reason": plan.get("reason") or input_type,
        "selector_phase": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE,
        "selector_basis": basis,
        "primary_plus_secondary_plus_afterglow": True,
        "primary_slot_count": 1,
        "secondary_slot_count": 2,
        "afterglow_slot_count": 1,
        "strong_follow_candidate": input_type in _STRONG_FOLLOW_INPUT_TYPES,
        "emotion_label_only_selection": False,
        "personality_claim_allowed": False,
        "completed_reply_generated": False,
        "raw_text_included": False,
    }

    summary = _selector_input_summary(
        frame=frame,
        material=material,
        relation_ids=relations,
        emotion_labels=emotions,
        output_theme_ids=themes,
        category_labels=categories,
        strength_summary=strength,
    )
    selector = EmlisHumanFollowSelection(
        source=_frame_source(frame),
        selector_input_summary=summary,
        selection=selection,
        follow_key_slots=_follow_key_slots(selection, basis=basis),
        guard_policy=_guard_policy(input_type),
        environment_state_output_frame={
            "schema_version": _clean(frame.get("schema_version")),
            "material_id": _clean(frame.get("material_id")) or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
            "phase": _clean(frame.get("phase")),
            "axis_presence": _deepcopy_mapping(_as_mapping(frame.get("axis_presence"))),
            "output_theme_ids": _dedupe(themes),
            "relation_role_ids": _dedupe(relations),
            "single_record_only": True,
            "raw_text_included": False,
        },
        observation_structure_material=material,
    )
    assert_human_follow_selection_contract(selector)
    return selector


def human_follow_selection_forward_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisHumanFollowSelection):
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
        "selector_input_summary",
        "selection",
        "input_type",
        "input_type_candidates",
        "selector_basis",
        "detected_input_signal_ids",
        "surface_risk_ids",
        "allowed_impression_claims",
        "follow_key_slots",
        "guard_policy",
        "environment_state_output_frame",
        "observation_structure_material",
        "environment_state_output_frame_connected",
        "observation_structure_material_connected",
        "human_follow_selector_connected",
        "human_follow_selector_material_only",
        "follow_key_slots_count",
        "primary_follow_key",
        "secondary_follow_keys",
        "afterglow_follow_key",
        "follow_mode",
        "strong_follow_candidate",
        "emotion_label_only_selection",
        "personality_claim_allowed",
        "target_judgement_agreement_allowed",
        "target_attack_amplification_allowed",
        "material_is_completed_reply_template",
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
    }
    out = {key: copy.deepcopy(meta.get(key)) for key in keys if key in meta}
    assert_human_follow_selection_contract(out)
    return out


def human_follow_selection_gate_report(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisHumanFollowSelection):
        report = value.gate_report()
    elif isinstance(value, Mapping):
        meta = human_follow_selection_forward_meta(value)
        if not meta:
            return {}
        selection = _as_mapping(meta.get("selection"))
        report = {
            "schema_version": meta.get("schema_version") or EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION,
            "material_id": meta.get("material_id") or EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID,
            "passed": bool(meta.get("passed", True)),
            "evaluated": True,
            "status": meta.get("status") or "passed",
            "rejection_reasons": list(meta.get("rejection_reasons") or []),
            "human_follow_selector_connected": True,
            "human_follow_selector_material_only": True,
            "input_type": selection.get("input_type") or "",
            "primary_follow_key": selection.get("primary_follow_key") or meta.get("primary_follow_key") or "",
            "secondary_follow_keys": list(selection.get("secondary_follow_keys") or meta.get("secondary_follow_keys") or []),
            "afterglow_follow_key": selection.get("afterglow_follow_key") or meta.get("afterglow_follow_key") or "",
            "follow_key_slots_count": len(list(meta.get("follow_key_slots") or [])),
            "strong_follow_candidate": bool(selection.get("strong_follow_candidate") or meta.get("strong_follow_candidate")),
            "emotion_label_only_selection": False,
            "follow_mode": FOLLOW_MODE,
            "personality_claim_allowed": False,
            "target_judgement_agreement_allowed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
    else:
        return {}
    assert_human_follow_selection_contract(report)
    return report


def human_follow_selection_composer_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisHumanFollowSelection):
        payload = value.composer_payload()
    elif isinstance(value, Mapping):
        meta = human_follow_selection_forward_meta(value)
        if not meta:
            return {}
        payload = {
            "schema_version": meta.get("schema_version") or EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION,
            "material_id": meta.get("material_id") or EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID,
            "source_phase": meta.get("source_phase") or meta.get("phase") or EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE,
            "selection": _deepcopy_mapping(_as_mapping(meta.get("selection"))),
            "follow_key_slots": copy.deepcopy(list(meta.get("follow_key_slots") or [])),
            "guard_policy": _deepcopy_mapping(_as_mapping(meta.get("guard_policy"))),
            "selector_input_summary": _deepcopy_mapping(_as_mapping(meta.get("selector_input_summary"))),
            "human_follow_selector_connected": True,
            "human_follow_selector_material_only": True,
            "follow_mode": FOLLOW_MODE,
            "personality_claim_allowed": False,
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
    assert_human_follow_selection_contract(payload)
    return payload


def human_follow_selector_guard_policy_meta() -> dict[str, Any]:
    """Return a small policy summary for quality guards.

    This is a policy/material boundary, not a runtime sentence template.
    """

    return {
        "schema_version": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION,
        "material_id": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID,
        "source_phase": EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE,
        "follow_keys_are_material_roles": True,
        "primary_secondary_afterglow_required": True,
        "follow_mode": FOLLOW_MODE,
        "personality_claim_allowed": False,
        "diagnosis_allowed": False,
        "action_instruction_allowed": False,
        "target_judgement_agreement_allowed": False,
        "free_sentence_template_added": False,
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _FORBIDDEN_RAW_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


def _slot_counts(slots: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {"primary": 0, "secondary": 0, "afterglow": 0}
    for slot in slots:
        slot_name = _clean(slot.get("slot"))
        if slot_name in counts:
            counts[slot_name] += 1
    return counts


def assert_human_follow_selection_contract(value: Any, *, source: str = "human_follow_selector") -> None:
    if isinstance(value, EmlisHumanFollowSelection):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    schema_version = _clean(value.get("schema_version"))
    if schema_version not in {"", EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION}:
        raise ValueError(f"{source} has unexpected schema_version")
    material_id = _clean(value.get("material_id"))
    if material_id not in {"", EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID}:
        raise ValueError(f"{source} has unexpected material_id")

    selection = _as_mapping(value.get("selection"))
    if selection:
        primary = _clean(selection.get("primary_follow_key"))
        secondaries = _dedupe(selection.get("secondary_follow_keys") or [])
        afterglow = _clean(selection.get("afterglow_follow_key"))
        unknown = [key for key in [primary, afterglow, *secondaries] if key and key not in _ALLOWED_FOLLOW_KEYS]
        if unknown:
            raise ValueError(f"{source} has unknown follow keys: {unknown}")
        if bool(selection.get("personality_claim_allowed")):
            raise ValueError(f"{source} must keep personality_claim_allowed=false")

    slots = value.get("follow_key_slots") or []
    if slots:
        counts = _slot_counts([slot for slot in slots if isinstance(slot, Mapping)])
        if counts.get("primary") != 1 or counts.get("secondary") != 2 or counts.get("afterglow") != 1:
            raise ValueError(f"{source} must expose primary1 secondary2 afterglow1 follow slots")
        for slot in slots:
            if not isinstance(slot, Mapping):
                raise ValueError(f"{source} follow slots must be mappings")
            if bool(slot.get("personality_claim_allowed")):
                raise ValueError(f"{source} follow slots must not allow personality claims")
            if bool(slot.get("raw_text_included")):
                raise ValueError(f"{source} follow slots must not include raw text")

    if value.get("material_is_completed_reply_template") is True:
        raise ValueError(f"{source} must not be a completed reply template")
    if value.get("human_follow_selector_connected") is False:
        raise ValueError(f"{source} must keep human_follow_selector_connected=true when present")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


# Aliases for call-site readability.
build_human_follow_selection = build_emlis_ai_human_follow_selection
select_emlis_human_follow = build_emlis_ai_human_follow_selection
assert_emlis_ai_human_follow_selection_contract = assert_human_follow_selection_contract

__all__ = [
    "EMLIS_AI_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION",
    "EMLIS_AI_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID",
    "EMLIS_AI_HUMAN_FOLLOW_SELECTOR_PHASE",
    "EMLIS_AI_HUMAN_FOLLOW_SELECTOR_INTERNAL_NAME",
    "EMLIS_HUMAN_FOLLOW_SELECTOR_SCHEMA_VERSION",
    "EMLIS_HUMAN_FOLLOW_SELECTOR_MATERIAL_ID",
    "EMLIS_HUMAN_FOLLOW_SELECTOR_PHASE",
    "FOLLOW_MODE",
    "FOLLOW_INTENTION_AFFIRMATION",
    "FOLLOW_FEAR_OR_LOAD_UNDERSTANDING",
    "FOLLOW_EFFORT_RECEIVING",
    "FOLLOW_EXISTENCE_RESPECT",
    "FOLLOW_IMPORTANT_VALUE_RECEIVING",
    "FOLLOW_IDENTITY_COUNTER_WITH_EVIDENCE",
    "FOLLOW_RESPONSIBILITY_SCOPE_OBSERVATION",
    "FOLLOW_REASON_VISIBILITY_RECEIVING",
    "FOLLOW_NEXT_OBSERVATION_MARGIN",
    "EmlisHumanFollowSelection",
    "build_emlis_ai_human_follow_selection",
    "build_human_follow_selection",
    "select_emlis_human_follow",
    "human_follow_selection_forward_meta",
    "human_follow_selection_gate_report",
    "human_follow_selection_composer_payload",
    "human_follow_selector_guard_policy_meta",
    "assert_human_follow_selection_contract",
    "assert_emlis_ai_human_follow_selection_contract",
]
