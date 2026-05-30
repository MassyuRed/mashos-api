# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 Reception Mode Resolver for EmlisAI two-stage reception.

This module is internal material only.  It resolves the backend-only reception
mode from Phase 2 shared evidence plus the Phase 3 reception assistance
dictionary.  It does not generate ``comment_text``, add public response keys,
extend ``observation_status``, change RN visibility, or assert unknown-word
meaning.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import copy
import json
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_reception_assistance_dictionary_loader import (
    EmlisReceptionAssistanceDictionary,
    event_hint_can_create_emotion,
    load_reception_assistance_dictionary,
    select_reception_assistance_modes,
    select_reception_assistance_reaction_cues,
)
from emlis_ai_safety_boundary_service import classify_safety_boundary_text
from emlis_ai_shared_reception_evidence import (
    EmlisSharedReceptionEvidence,
    build_emlis_shared_reception_evidence,
)

EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION: Final = "cocolon.emlis_reception_mode_resolution.v1"
EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE: Final = "Phase4_reception_mode_resolver"
EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID: Final = "emlis_reception_mode_resolution"
# Backward-readable aliases for tests and later phases that use resolver wording.
EMLIS_RECEPTION_MODE_RESOLVER_SCHEMA_VERSION: Final = EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION
EMLIS_RECEPTION_MODE_RESOLVER_SOURCE_PHASE: Final = EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE
EMLIS_RECEPTION_MODE_RESOLVER_MATERIAL_ID: Final = EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID
EMLIS_RECEPTION_MODE_RESOLVER_PHASE: Final = EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE

MODE_DAILY_UNPLEASANT: Final = "daily_unpleasant_reception"
MODE_DAILY_POSITIVE: Final = "daily_positive_reception"
MODE_SELF_DENIAL: Final = "self_denial_support"
MODE_UNCERTAINTY: Final = "uncertainty_support"
MODE_SELF_UNDERSTANDING: Final = "self_understanding_follow"
MODE_STANDARD: Final = "standard_state_answer"
MODE_EFFORT: Final = "effort_support"
MODE_STRUCTURE: Final = "structure_question_observation"
MODE_LOW_INFORMATION: Final = "low_information_question"
MODE_SAFETY_EXISTING_PATH: Final = "existing_safety_path"
# Alias names for tests/later phases that use broader design vocabulary.
MODE_EFFORT_SUPPORT: Final = MODE_EFFORT
MODE_SAFETY_BOUNDARY: Final = MODE_SAFETY_EXISTING_PATH
MODE_STRUCTURE_QUESTION: Final = MODE_STRUCTURE

_SPACE_RE: Final = re.compile(r"\s+")
_STRUCTURE_REQUEST_PATTERNS: Final = (
    "構造を知りたい",
    "構造として知りたい",
    "どういう構造",
    "この反応の構造",
    "この気持ちの構造",
    "どういうこと",
    "どういう状態",
    "どういう流れ",
    "どうして",
    "なんで",
    "なぜ",
    "理由を知りたい",
    "繰り返す",
    "同じことになる",
    "なぜこうなるのか知りたい",
    "なぜこうなるのか見たい",
    "分析してほしい",
    "観測してほしい",
    "Emlisに観測してほしい",
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "memo",
        "memo_action",
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "candidate_comment_text",
        "public_comment_text",
        "observation_text",
        "reception_text",
        "reply_text",
        "surface_text",
        "realized_text",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "comment_text_generated",
        "public_response_key_added",
        "public_status_extended",
        "observation_status_enum_extended",
        "api_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "general_dictionary_used",
        "unknown_word_meaning_asserted",
        "event_hint_created_emotion",
        "event_hint_alone_activated_mode",
        "event_hint_alone_activated_reception_mode",
        "completed_reply_generated",
        "completed_reply_template_used",
        "target_judgement_agreement_allowed",
        "identity_claim_accepted_as_fact",
        "action_instruction_allowed",
    }
)

_MODE_PRIORITY: Final = (
    MODE_SELF_DENIAL,
    MODE_UNCERTAINTY,
    MODE_DAILY_UNPLEASANT,
    MODE_DAILY_POSITIVE,
    MODE_SELF_UNDERSTANDING,
    MODE_STANDARD,
    MODE_EFFORT,
    MODE_LOW_INFORMATION,
)

_RATIO_PRESET_BY_INTERNAL_MODE: Final = {
    MODE_STRUCTURE: "structure_question_observation_thickened",
    MODE_SAFETY_EXISTING_PATH: "safety_existing_path_no_reception_generation",
    MODE_LOW_INFORMATION: "low_information_light_prompt",
}

_OBSERVATION_REPLY_KIND_BY_INTERNAL_MODE: Final = {
    MODE_STRUCTURE: "eligible_observation",
    MODE_SAFETY_EXISTING_PATH: "safety_blocked",
    MODE_LOW_INFORMATION: "low_information_question",
}


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> tuple[str, ...]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _mapping_from_evidence(evidence: EmlisSharedReceptionEvidence | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(evidence, EmlisSharedReceptionEvidence):
        return evidence.as_meta()
    if not isinstance(evidence, Mapping):
        raise TypeError("shared_evidence must be EmlisSharedReceptionEvidence or mapping")
    return evidence


def _list_from_meta(meta: Mapping[str, Any], key: str) -> tuple[str, ...]:
    return _dedupe(meta.get(key) or ())


def _detect_structure_request(current_input: Any | None) -> bool:
    if current_input is None:
        return False
    bundle = build_emlis_current_input_bundle(current_input)
    text = _clean("\n".join(part for part in (bundle.thought_text, bundle.action_text) if part))
    if not text:
        return False
    return any(pattern in text for pattern in _STRUCTURE_REQUEST_PATTERNS)


def _detect_safety_boundary_type_ids(current_input: Any | None) -> tuple[str, ...]:
    if current_input is None:
        return ()
    bundle = build_emlis_current_input_bundle(current_input)
    detected: list[str] = []
    for part in (bundle.thought_text, bundle.action_text):
        detected.extend(classify_safety_boundary_text(part))
    return _dedupe(detected)




def detect_emlis_structure_question_requested(current_input: Any | None) -> bool:
    """Return whether the current input explicitly asks for structure observation."""

    return _detect_structure_request(current_input)


def detect_emlis_safety_risk_codes(current_input: Any | None) -> tuple[str, ...]:
    """Return stable safety kind codes without exposing source text."""

    return _detect_safety_boundary_type_ids(current_input)


def _reaction_family_ids(
    dictionary: EmlisReceptionAssistanceDictionary,
    reaction_cue_ids: Sequence[str],
) -> tuple[str, ...]:
    families: list[str] = []
    for cue_id in reaction_cue_ids:
        cues = select_reception_assistance_reaction_cues(dictionary, cue_id=cue_id)
        if cues:
            families.append(str(cues[0].get("reaction_family") or ""))
    return _dedupe(families)


def _reaction_allowed_mode_ids(
    dictionary: EmlisReceptionAssistanceDictionary,
    reaction_cue_ids: Sequence[str],
) -> tuple[str, ...]:
    modes: list[str] = []
    for cue_id in reaction_cue_ids:
        cues = select_reception_assistance_reaction_cues(dictionary, cue_id=cue_id)
        if cues:
            modes.extend(str(mode_id) for mode_id in cues[0].get("allowed_reception_modes") or [])
    return _dedupe(modes)


def _event_hint_supported_mode_ids(
    dictionary: EmlisReceptionAssistanceDictionary,
    event_hint_ids: Sequence[str],
) -> tuple[str, ...]:
    hint_by_id = {str(hint.get("hint_id")): hint for hint in dictionary.event_hints}
    modes: list[str] = []
    for hint_id in event_hint_ids:
        if hint_id not in hint_by_id:
            continue
        if event_hint_can_create_emotion(dictionary, hint_id):
            continue
        modes.extend(str(mode_id) for mode_id in hint_by_id[hint_id].get("can_support_modes") or [])
    return _dedupe(modes)


def _dictionary_mode_by_id(
    dictionary: EmlisReceptionAssistanceDictionary,
    mode_id: str,
) -> Mapping[str, Any] | None:
    selected = select_reception_assistance_modes(dictionary, mode_id=mode_id)
    return selected[0] if selected else None


def _mode_activation_satisfied(
    mode: Mapping[str, Any],
    *,
    event_fact_present: bool,
    reaction_present: bool,
    event_fact_source_fields: Sequence[str] = (),
    reaction_source_fields: Sequence[str] = (),
    reaction_family_ids: Sequence[str],
    structure_requested: bool,
    safety_required: bool,
    self_denial_primary: bool,
) -> bool:
    activation = mode.get("activation") if isinstance(mode.get("activation"), Mapping) else {}
    if activation.get("fallback_only") is True:
        return False
    if activation.get("requires_event_fact_present") is True and not event_fact_present:
        return False
    if activation.get("requires_reaction_present") is True and not reaction_present:
        return False
    if activation.get("event_hint_alone_can_activate") is False and not reaction_present:
        return False
    if activation.get("excludes_structure_question") is True and structure_requested:
        return False
    if activation.get("excludes_safety_risk") is True and safety_required:
        return False
    if activation.get("excludes_self_denial_primary") is True and self_denial_primary:
        return False
    required_families = set(_dedupe(activation.get("requires_any_reaction_family") or ()))
    if required_families and not required_families.intersection(set(reaction_family_ids)):
        return False
    return True


def _sort_modes_by_priority(mode_ids: Iterable[str]) -> tuple[str, ...]:
    priority = {mode_id: index for index, mode_id in enumerate(_MODE_PRIORITY)}
    return tuple(sorted(_dedupe(mode_ids), key=lambda mode_id: (priority.get(mode_id, 999), mode_id)))


def _eligible_dictionary_mode_ids(
    dictionary: EmlisReceptionAssistanceDictionary,
    *,
    candidate_mode_ids: Sequence[str],
    reaction_allowed_mode_ids: Sequence[str],
    event_hint_supported_mode_ids: Sequence[str],
    event_fact_present: bool,
    reaction_present: bool,
    event_fact_source_fields: Sequence[str] = (),
    reaction_source_fields: Sequence[str] = (),
    reaction_family_ids: Sequence[str],
    structure_requested: bool,
    safety_required: bool,
    event_hint_ids: Sequence[str],
) -> tuple[str, ...]:
    candidate_set = set(candidate_mode_ids)
    candidate_set.update(reaction_allowed_mode_ids)
    if reaction_present:
        candidate_set.update(event_hint_supported_mode_ids)
    self_denial_primary = MODE_SELF_DENIAL in candidate_set and "self_negative_reaction" in set(reaction_family_ids)
    eligible: list[str] = []
    for mode in dictionary.reception_modes:
        mode_id = _clean(mode.get("mode_id"))
        if mode_id not in candidate_set:
            continue
        if mode_id != MODE_LOW_INFORMATION and mode_id not in set(reaction_allowed_mode_ids):
            continue
        if mode_id == MODE_DAILY_UNPLEASANT:
            if not event_fact_present or not reaction_present:
                continue
            if not set(reaction_family_ids).intersection({"negative_daily_reaction", "fear_reaction", "anger_reaction"}):
                continue
            if event_hint_ids and event_hint_supported_mode_ids and MODE_DAILY_UNPLEASANT not in event_hint_supported_mode_ids:
                continue
        if _mode_activation_satisfied(
            mode,
            event_fact_present=event_fact_present,
            reaction_present=reaction_present,
            reaction_family_ids=reaction_family_ids,
            structure_requested=structure_requested,
            safety_required=safety_required,
            self_denial_primary=self_denial_primary,
        ):
            eligible.append(mode_id)
    if not reaction_present and MODE_LOW_INFORMATION in candidate_set:
        eligible.append(MODE_LOW_INFORMATION)
    return _sort_modes_by_priority(eligible)


def _choose_reception_mode(
    *,
    event_fact_present: bool,
    reaction_present: bool,
    event_hint_ids: Sequence[str],
    reaction_cue_ids: Sequence[str],
    eligible_mode_ids: Sequence[str],
    structure_requested: bool,
    safety_required: bool,
) -> tuple[str, str]:
    eligible = set(eligible_mode_ids)
    hints = set(event_hint_ids)
    cues = set(reaction_cue_ids)
    if safety_required:
        return MODE_SAFETY_EXISTING_PATH, "safety_boundary_existing_path_required"
    if "self_blame_to_gentle_self_observation" in hints and "self_understanding_effort" in cues and MODE_SELF_UNDERSTANDING in eligible:
        return MODE_SELF_UNDERSTANDING, "self_blame_to_gentle_self_observation"
    if MODE_SELF_DENIAL in eligible:
        if MODE_UNCERTAINTY in eligible:
            return MODE_SELF_DENIAL, "self_denial_and_uncertainty_cues_present"
        return MODE_SELF_DENIAL, "self_denial_cues_present"
    if structure_requested:
        return MODE_STRUCTURE, "explicit_structure_question_observation_thickened"
    for mode_id in (
        MODE_DAILY_UNPLEASANT,
        MODE_DAILY_POSITIVE,
        MODE_UNCERTAINTY,
        MODE_SELF_UNDERSTANDING,
        MODE_STANDARD,
        MODE_EFFORT,
    ):
        if mode_id in eligible:
            reasons = {
                MODE_DAILY_UNPLEASANT: "event_fact_with_explicit_negative_reaction",
                MODE_DAILY_POSITIVE: "positive_change_or_surprise_cues_present",
                MODE_UNCERTAINTY: "uncertainty_cues_present",
                MODE_SELF_UNDERSTANDING: "self_understanding_direction_present",
                MODE_EFFORT: "effort_pace_context_present",
                MODE_STANDARD: "effort_pace_context_present" if "independence_life_health_money_pace" in hints or MODE_EFFORT in eligible else "standard_state_answer_material_present",
            }
            return mode_id, reasons[mode_id]
    if reaction_present:
        return MODE_STANDARD, "explicit_reaction_present"
    return MODE_LOW_INFORMATION, "insufficient_shared_reception_evidence"


def _mode_policy(
    dictionary: EmlisReceptionAssistanceDictionary,
    mode_id: str,
) -> tuple[str, dict[str, Any], dict[str, Any], tuple[str, ...], bool]:
    mode = _dictionary_mode_by_id(dictionary, mode_id)
    if mode is not None:
        return (
            _clean(mode.get("ratio_preset")) or mode_id,
            copy.deepcopy(dict(mode.get("observation_policy") or {})),
            copy.deepcopy(dict(mode.get("reception_policy") or {})),
            _dedupe(mode.get("forbidden") or ()),
            True,
        )
    if mode_id == MODE_STRUCTURE:
        return (
            _RATIO_PRESET_BY_INTERNAL_MODE[MODE_STRUCTURE],
            {"max_sentences": 3, "claim_strength": "single_input_soft", "observation_thickened": True},
            {"allowed_tone_family": "balanced_state_answer", "min_sentences": 1, "max_sentences": 2},
            ("diagnosis", "personality_claim", "cause_overclaim", "action_instruction"),
            False,
        )
    if mode_id == MODE_SAFETY_EXISTING_PATH:
        return (
            _RATIO_PRESET_BY_INTERNAL_MODE[MODE_SAFETY_EXISTING_PATH],
            {"normal_observation_allowed": False, "claim_strength": "safety_boundary"},
            {"allowed_tone_family": "existing_safety_path", "min_sentences": 0, "max_sentences": 0},
            ("normal_reception_generation", "comment_text_generation", "public_status_extension"),
            False,
        )
    return (
        _RATIO_PRESET_BY_INTERNAL_MODE.get(mode_id, mode_id),
        {"max_sentences": 1, "claim_strength": "visible_scope_only"},
        {"allowed_tone_family": "balanced_state_answer", "min_sentences": 0, "max_sentences": 1},
        ("raw_detail_request", "public_status_extension"),
        False,
    )


def _observation_reply_kind(mode_id: str) -> str:
    return _OBSERVATION_REPLY_KIND_BY_INTERNAL_MODE.get(mode_id, "eligible_observation")


@dataclass(frozen=True)
class EmlisReceptionModeResolution:
    """Text-free Phase 4 reception mode material."""

    reception_mode: str
    primary_reason: str
    resolved_mode_ids: tuple[str, ...] = field(default_factory=tuple)
    candidate_mode_ids: tuple[str, ...] = field(default_factory=tuple)
    eligible_dictionary_mode_ids: tuple[str, ...] = field(default_factory=tuple)
    event_fact_present: bool = False
    reaction_present: bool = False
    event_fact_source_fields: tuple[str, ...] = field(default_factory=tuple)
    reaction_source_fields: tuple[str, ...] = field(default_factory=tuple)
    reaction_family_ids: tuple[str, ...] = field(default_factory=tuple)
    reaction_allowed_mode_ids: tuple[str, ...] = field(default_factory=tuple)
    event_hint_supported_mode_ids: tuple[str, ...] = field(default_factory=tuple)
    explicit_reaction_cue_ids: tuple[str, ...] = field(default_factory=tuple)
    explicit_emotion_label_ids: tuple[str, ...] = field(default_factory=tuple)
    event_hint_ids: tuple[str, ...] = field(default_factory=tuple)
    category_topic_ids: tuple[str, ...] = field(default_factory=tuple)
    structure_question_requested: bool = False
    safety_path_required: bool = False
    safety_boundary_type_ids: tuple[str, ...] = field(default_factory=tuple)
    low_information_question_allowed: bool = False
    low_information_question_required: bool = False
    observation_reply_kind: str = "eligible_observation"
    ratio_preset: str = ""
    observation_policy: Mapping[str, Any] = field(default_factory=dict)
    reception_policy: Mapping[str, Any] = field(default_factory=dict)
    forbidden_inference_ids: tuple[str, ...] = field(default_factory=tuple)
    dictionary_mode_policy_used: bool = False
    schema_version: str = EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION
    source_phase: str = EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE
    material_id: str = EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID

    @property
    def reception_mode_id(self) -> str:
        return self.reception_mode

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "source_phase": self.source_phase,
            "material_id": self.material_id,
            "reception_mode_resolver_ready": True,
            "reception_mode": self.reception_mode,
            "reception_mode_id": self.reception_mode_id,
            "selected_reception_mode_id": self.reception_mode,
            "resolved_mode_ids": list(self.resolved_mode_ids),
            "candidate_mode_ids": list(self.candidate_mode_ids),
            "eligible_dictionary_mode_ids": list(self.eligible_dictionary_mode_ids),
            "secondary_reception_mode_ids": [mode_id for mode_id in self.eligible_dictionary_mode_ids if mode_id != self.reception_mode],
            "primary_reason": self.primary_reason,
            "reason_codes": [self.primary_reason],
            "event_fact_present": bool(self.event_fact_present),
            "reaction_present": bool(self.reaction_present),
            "reaction_family_ids": list(self.reaction_family_ids),
            "matched_reaction_family_ids": list(self.reaction_family_ids),
            "reaction_allowed_mode_ids": list(self.reaction_allowed_mode_ids),
            "event_hint_supported_mode_ids": list(self.event_hint_supported_mode_ids),
            "explicit_reaction_cue_ids": list(self.explicit_reaction_cue_ids),
            "explicit_emotion_label_ids": list(self.explicit_emotion_label_ids),
            "event_hint_ids": list(self.event_hint_ids),
            "category_topic_ids": list(self.category_topic_ids),
            "structure_question_requested": bool(self.structure_question_requested),
            "safety_path_required": bool(self.safety_path_required),
            "existing_safety_path_required": bool(self.safety_path_required),
            "safety_boundary_type_ids": list(self.safety_boundary_type_ids),
            "safety_reason_codes": list(self.safety_boundary_type_ids),
            "safety_risk_detected": bool(self.safety_path_required),
            "low_information_question_allowed": bool(self.low_information_question_allowed),
            "low_information_question_required": bool(self.low_information_question_required),
            "question_required": bool(self.low_information_question_required),
            "observation_reply_kind": self.observation_reply_kind,
            "ratio_preset": self.ratio_preset,
            "mode_policy": {
                "ratio_preset": self.ratio_preset,
                "observation_policy": copy.deepcopy(dict(self.observation_policy or {})),
                "reception_policy": copy.deepcopy(dict(self.reception_policy or {})),
                "forbidden_inference_ids": list(self.forbidden_inference_ids),
                "forbidden": list(self.forbidden_inference_ids),
                "dictionary_mode_policy_used": bool(self.dictionary_mode_policy_used),
            },
            "selected_mode_policy": {
                "ratio_preset": self.ratio_preset,
                "observation_policy": copy.deepcopy(dict(self.observation_policy or {})),
                "reception_policy": copy.deepcopy(dict(self.reception_policy or {})),
                "forbidden": list(self.forbidden_inference_ids),
            },
            "selected_from_dictionary": bool(self.dictionary_mode_policy_used),
            "selected_mode_defined_in_dictionary": bool(self.dictionary_mode_policy_used),
            "observation_thickened": bool(self.reception_mode == MODE_STRUCTURE or dict(self.observation_policy or {}).get("observation_thickened")),
            "event_hint_alone_used": False,
            "event_hint_alone_created_mode": False,
            "unknown_word_policy": {
                "unknown_word_meaning_asserted": False,
                "meaning_assertion_allowed": False,
                "event_hint_can_support_mode_only": True,
                "event_hint_must_not_create_emotion": True,
            },
            "mode_selection_contract": {
                "user_selected_mode": False,
                "backend_internal_mode_only": True,
                "event_hint_alone_can_activate": False,
                "event_hint_alone_activated_mode": False,
                "event_hint_alone_activated_reception_mode": False,
                "self_denial_must_not_be_lightly_daily": True,
                "safety_uses_existing_path": bool(self.safety_path_required),
            },
            "general_dictionary_used": False,
            "unknown_word_meaning_asserted": False,
            "event_hint_created_emotion": False,
            "event_hint_alone_activated_mode": False,
            "event_hint_alone_activated_reception_mode": False,
            "category_used_as_cause": False,
            "emotion_strength_used_as_cause": False,
            "target_judgement_agreement_allowed": False,
            "identity_claim_accepted_as_fact": False,
            "action_instruction_allowed": False,
            "comment_text_generated": False,
            "completed_reply_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "public_response_key_added": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_emlis_reception_mode_resolution_contract(meta)
        return meta


def resolve_emlis_reception_mode(
    current_input: Any | None = None,
    *,
    shared_evidence: EmlisSharedReceptionEvidence | Mapping[str, Any] | None = None,
    dictionary: EmlisReceptionAssistanceDictionary | None = None,
    user_structure_question_requested: bool | None = None,
    safety_boundary_type_ids: Sequence[str] | None = None,
) -> EmlisReceptionModeResolution:
    """Resolve Phase 4 reception mode without producing surface text."""

    if dictionary is None:
        dictionary = load_reception_assistance_dictionary()
    if shared_evidence is None:
        if current_input is None:
            raise ValueError("current_input or shared_evidence is required")
        shared_evidence = build_emlis_shared_reception_evidence(current_input)
    evidence_meta = _mapping_from_evidence(shared_evidence)

    event_fact_present = bool(evidence_meta.get("event_fact_present"))
    reaction_present = bool(evidence_meta.get("reaction_present"))
    reaction_cue_ids = _list_from_meta(evidence_meta, "explicit_reaction_cue_ids")
    emotion_label_ids = _list_from_meta(evidence_meta, "explicit_emotion_label_ids")
    event_hint_ids = _list_from_meta(evidence_meta, "event_hint_ids")
    category_topic_ids = _list_from_meta(evidence_meta, "category_topic_ids")
    candidate_mode_ids = _list_from_meta(evidence_meta, "reception_candidate_mode_ids")

    reaction_families = _reaction_family_ids(dictionary, reaction_cue_ids)
    reaction_allowed_modes = _reaction_allowed_mode_ids(dictionary, reaction_cue_ids)
    hint_supported_modes = _event_hint_supported_mode_ids(dictionary, event_hint_ids)
    for hint_id in event_hint_ids:
        if event_hint_can_create_emotion(dictionary, hint_id):
            raise ValueError(f"event hint must not create emotion: {hint_id}")

    safety_types = _dedupe(safety_boundary_type_ids) or _detect_safety_boundary_type_ids(current_input)
    safety_required = bool(safety_types)
    structure_requested = bool(user_structure_question_requested)
    if user_structure_question_requested is None:
        structure_requested = _detect_structure_request(current_input)

    eligible_modes = _eligible_dictionary_mode_ids(
        dictionary,
        candidate_mode_ids=candidate_mode_ids,
        reaction_allowed_mode_ids=reaction_allowed_modes,
        event_hint_supported_mode_ids=hint_supported_modes,
        event_fact_present=event_fact_present,
        reaction_present=reaction_present,
        reaction_family_ids=reaction_families,
        structure_requested=structure_requested,
        safety_required=safety_required,
        event_hint_ids=event_hint_ids,
    )
    mode_id, reason = _choose_reception_mode(
        event_fact_present=event_fact_present,
        reaction_present=reaction_present,
        event_hint_ids=event_hint_ids,
        reaction_cue_ids=reaction_cue_ids,
        eligible_mode_ids=eligible_modes,
        structure_requested=structure_requested,
        safety_required=safety_required,
    )
    ratio_preset, observation_policy, reception_policy, forbidden, policy_from_dictionary = _mode_policy(dictionary, mode_id)
    low_information = mode_id == MODE_LOW_INFORMATION

    resolved_modes = _dedupe([mode_id] + list(eligible_modes))
    return EmlisReceptionModeResolution(
        reception_mode=mode_id,
        primary_reason=reason,
        resolved_mode_ids=resolved_modes,
        candidate_mode_ids=candidate_mode_ids,
        eligible_dictionary_mode_ids=eligible_modes,
        event_fact_present=event_fact_present,
        reaction_present=reaction_present,
        event_fact_source_fields=_list_from_meta(evidence_meta, "event_fact_source_fields"),
        reaction_source_fields=_list_from_meta(evidence_meta, "reaction_source_fields"),
        reaction_family_ids=reaction_families,
        reaction_allowed_mode_ids=reaction_allowed_modes,
        event_hint_supported_mode_ids=hint_supported_modes,
        explicit_reaction_cue_ids=reaction_cue_ids,
        explicit_emotion_label_ids=emotion_label_ids,
        event_hint_ids=event_hint_ids,
        category_topic_ids=category_topic_ids,
        structure_question_requested=structure_requested,
        safety_path_required=safety_required,
        safety_boundary_type_ids=safety_types,
        low_information_question_allowed=low_information,
        low_information_question_required=low_information,
        observation_reply_kind=_observation_reply_kind(mode_id),
        ratio_preset=ratio_preset,
        observation_policy=observation_policy,
        reception_policy=reception_policy,
        forbidden_inference_ids=forbidden,
        dictionary_mode_policy_used=policy_from_dictionary,
    )



def resolve_emlis_reception_mode_from_evidence(
    shared_evidence: EmlisSharedReceptionEvidence | Mapping[str, Any],
    *,
    dictionary: EmlisReceptionAssistanceDictionary | None = None,
    safety_boundary_type_ids: Sequence[str] | None = None,
) -> EmlisReceptionModeResolution:
    return resolve_emlis_reception_mode(
        None,
        shared_evidence=shared_evidence,
        dictionary=dictionary,
        safety_boundary_type_ids=safety_boundary_type_ids,
    )


def resolve_emlis_reception_mode_meta(
    current_input: Any | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return resolve_emlis_reception_mode(current_input, **kwargs).as_meta()


def build_emlis_reception_mode_resolution_meta(
    current_input: Any | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return resolve_emlis_reception_mode_meta(current_input, **kwargs)


def build_emlis_reception_mode_resolver_meta(
    current_input: Any | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return resolve_emlis_reception_mode_meta(current_input, **kwargs)


def build_emlis_reception_mode_resolution(
    current_input: Any | None = None,
    **kwargs: Any,
) -> EmlisReceptionModeResolution:
    return resolve_emlis_reception_mode(current_input, **kwargs)


def build_emlis_reception_mode_resolver(
    current_input: Any | None = None,
    **kwargs: Any,
) -> EmlisReceptionModeResolution:
    return resolve_emlis_reception_mode(current_input, **kwargs)


def reception_mode_resolution_forward_meta(value: EmlisReceptionModeResolution | Mapping[str, Any]) -> dict[str, Any]:
    meta = value.as_meta() if isinstance(value, EmlisReceptionModeResolution) else dict(value)
    assert_emlis_reception_mode_resolution_contract(meta)
    return copy.deepcopy(meta)


def reception_mode_resolution_gate_report(value: EmlisReceptionModeResolution | Mapping[str, Any]) -> dict[str, Any]:
    meta = reception_mode_resolution_forward_meta(value)
    report = {
        "schema_version": meta["schema_version"],
        "source_phase": meta["source_phase"],
        "material_id": meta["material_id"],
        "evaluated": True,
        "passed": True,
        "reception_mode": meta["reception_mode"],
        "primary_reason": meta["primary_reason"],
        "low_information_question_allowed": meta["low_information_question_allowed"],
        "low_information_question_required": meta["low_information_question_required"],
        "observation_reply_kind": meta["observation_reply_kind"],
        "event_fact_present": meta["event_fact_present"],
        "reaction_present": meta["reaction_present"],
        "safety_path_required": meta["safety_path_required"],
        "existing_safety_path_required": meta["existing_safety_path_required"],
        "general_dictionary_used": False,
        "unknown_word_meaning_asserted": False,
        "event_hint_created_emotion": False,
        "event_hint_alone_activated_mode": False,
        "event_hint_alone_activated_reception_mode": False,
        "target_judgement_agreement_allowed": False,
        "identity_claim_accepted_as_fact": False,
        "action_instruction_allowed": False,
        "public_response_key_added": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "comment_text_generated": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "completed_reply_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "mode_selection_contract": copy.deepcopy(dict(meta["mode_selection_contract"])),
    }
    assert_emlis_reception_mode_resolution_contract(report)
    return report


def reception_mode_resolution_composer_payload(value: EmlisReceptionModeResolution | Mapping[str, Any]) -> dict[str, Any]:
    meta = reception_mode_resolution_forward_meta(value)
    payload = {
        "schema_version": meta["schema_version"],
        "source_phase": meta["source_phase"],
        "material_id": meta["material_id"],
        "reception_mode": meta["reception_mode"],
        "primary_reason": meta["primary_reason"],
        "ratio_preset": meta["ratio_preset"],
        "mode_policy": copy.deepcopy(dict(meta["mode_policy"])),
        "low_information_question_allowed": meta["low_information_question_allowed"],
        "low_information_question_required": meta["low_information_question_required"],
        "observation_reply_kind": meta["observation_reply_kind"],
        "event_fact_present": meta["event_fact_present"],
        "reaction_present": meta["reaction_present"],
        "safety_path_required": meta["safety_path_required"],
        "existing_safety_path_required": meta["existing_safety_path_required"],
        "general_dictionary_used": False,
        "unknown_word_meaning_asserted": False,
        "event_hint_created_emotion": False,
        "event_hint_alone_activated_mode": False,
        "event_hint_alone_activated_reception_mode": False,
        "target_judgement_agreement_allowed": False,
        "identity_claim_accepted_as_fact": False,
        "action_instruction_allowed": False,
        "public_response_key_added": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "comment_text_generated": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "completed_reply_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "mode_selection_contract": copy.deepcopy(dict(meta["mode_selection_contract"])),
    }
    assert_emlis_reception_mode_resolution_contract(payload)
    return payload


def dump_emlis_reception_mode_resolution_contract(value: EmlisReceptionModeResolution | Mapping[str, Any]) -> str:
    meta = value.as_meta() if isinstance(value, EmlisReceptionModeResolution) else dict(value)
    assert_emlis_reception_mode_resolution_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


def assert_emlis_reception_mode_resolution_contract(meta: Mapping[str, Any]) -> None:
    if meta.get("schema_version") != EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION:
        raise ValueError("unexpected reception mode resolution schema version")
    if meta.get("source_phase") != EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE:
        raise ValueError("unexpected reception mode resolution source phase")
    if meta.get("material_id") != EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID:
        raise ValueError("unexpected reception mode resolution material id")
    if not _clean(meta.get("reception_mode")):
        raise ValueError("reception mode resolution requires reception_mode")
    if not _clean(meta.get("primary_reason")):
        raise ValueError("reception mode resolution requires primary_reason")

    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"forbidden true flag in reception mode resolution: {flag}")
    for key in _TEXT_PAYLOAD_KEYS:
        if key in meta:
            raise ValueError(f"raw/public text payload key is not allowed in reception mode resolution: {key}")
    if _contains_text_payload_key(meta):
        raise ValueError("reception mode resolution must not contain raw/public text payload keys")
    if meta.get("general_dictionary_used") is not False:
        raise ValueError("reception mode resolution must not use a general dictionary")
    if meta.get("unknown_word_meaning_asserted") is not False:
        raise ValueError("reception mode resolution must not assert unknown-word meaning")
    if meta.get("public_response_key_added") is not False:
        raise ValueError("reception mode resolution must not add public response keys")
    if meta.get("rn_visible_contract_changed") is not False:
        raise ValueError("reception mode resolution must not change RN visibility")

    mode = _clean(meta.get("reception_mode"))
    if mode == MODE_DAILY_UNPLEASANT:
        if meta.get("event_fact_present") is not True or meta.get("reaction_present") is not True:
            raise ValueError("daily_unpleasant_reception requires event fact and explicit reaction")
        if meta.get("low_information_question_allowed") is not False:
            raise ValueError("daily_unpleasant_reception must not allow low-information question")
    if mode != MODE_LOW_INFORMATION and meta.get("low_information_question_allowed") is not False:
        raise ValueError("low-information question is only allowed for low_information_question")
    if mode == MODE_LOW_INFORMATION and meta.get("low_information_question_required") is not True:
        raise ValueError("low_information_question must require question")
    if mode == MODE_SAFETY_EXISTING_PATH and meta.get("existing_safety_path_required") is not True:
        raise ValueError("safety mode must require existing safety path")

    contract = meta.get("mode_selection_contract")
    if not isinstance(contract, Mapping):
        raise ValueError("reception mode resolution missing mode_selection_contract")
    if contract.get("backend_internal_mode_only") is not True:
        raise ValueError("reception mode must remain backend-internal")
    if contract.get("event_hint_alone_activated_mode") is not False:
        raise ValueError("event hint alone must not activate mode")
    if contract.get("event_hint_alone_activated_reception_mode") is not False:
        raise ValueError("event hint alone must not activate reception mode")

    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


__all__ = [
    "EMLIS_RECEPTION_MODE_RESOLUTION_MATERIAL_ID",
    "EMLIS_RECEPTION_MODE_RESOLUTION_SCHEMA_VERSION",
    "EMLIS_RECEPTION_MODE_RESOLUTION_SOURCE_PHASE",
    "EMLIS_RECEPTION_MODE_RESOLVER_MATERIAL_ID",
    "EMLIS_RECEPTION_MODE_RESOLVER_SCHEMA_VERSION",
    "EMLIS_RECEPTION_MODE_RESOLVER_SOURCE_PHASE",
    "EMLIS_RECEPTION_MODE_RESOLVER_PHASE",
    "EmlisReceptionModeResolution",
    "MODE_DAILY_POSITIVE",
    "MODE_DAILY_UNPLEASANT",
    "MODE_EFFORT",
    "MODE_EFFORT_SUPPORT",
    "MODE_LOW_INFORMATION",
    "MODE_SAFETY_EXISTING_PATH",
    "MODE_SAFETY_BOUNDARY",
    "MODE_SELF_DENIAL",
    "MODE_SELF_UNDERSTANDING",
    "MODE_STANDARD",
    "MODE_STRUCTURE",
    "MODE_STRUCTURE_QUESTION",
    "MODE_UNCERTAINTY",
    "assert_emlis_reception_mode_resolution_contract",
    "build_emlis_reception_mode_resolution",
    "build_emlis_reception_mode_resolution_meta",
    "build_emlis_reception_mode_resolver",
    "build_emlis_reception_mode_resolver_meta",
    "detect_emlis_safety_risk_codes",
    "detect_emlis_structure_question_requested",
    "reception_mode_resolution_composer_payload",
    "reception_mode_resolution_forward_meta",
    "reception_mode_resolution_gate_report",
    "resolve_emlis_reception_mode",
    "resolve_emlis_reception_mode_from_evidence",
    "resolve_emlis_reception_mode_meta",
]
