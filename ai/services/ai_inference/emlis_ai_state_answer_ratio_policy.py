# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal ratio resolver material for EmlisAI state answers.

Phase 4 resolves the observation / human-follow balance described by the
state-answer design.  Phase 6 adds the two-stage reception-mode presets while
keeping the same material-only boundary: the resolver does not count characters
exactly, does not create user-facing ``comment_text``, does not add a public
response key, and does not alter API routes, DB physical names, or RN display
conditions.
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
from emlis_ai_reception_mode_resolver import resolve_emlis_reception_mode

EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis_ai_state_answer_ratio_policy.v1"
)
EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID: Final = "emlis_ai_state_answer_ratio_policy"
EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE: Final = "Phase4_state_answer_ratio_resolver"
EMLIS_AI_STATE_ANSWER_RATIO_POLICY_INTERNAL_NAME: Final = "EmlisAI状態回答 比率Resolver"
EMLIS_AI_STATE_ANSWER_RATIO_POLICY_TWO_STAGE_PHASE: Final = "Phase6_two_stage_reception_ratio_policy"
EMLIS_AI_STATE_ANSWER_RATIO_POLICY_META_ONLY_SANITIZER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.meta_only_sanitizer.v1"
)
EMLIS_AI_STATE_ANSWER_RATIO_POLICY_META_ONLY_SANITIZER_PHASE: Final = (
    "Phase18_product_quality_stabilization"
)

DEFAULT_OBSERVATION_RATIO: Final = 0.60
DEFAULT_HUMAN_FOLLOW_RATIO: Final = 0.40

_RATIO_PRESETS: Final = {
    "standard_state_answer": {
        "observation": 0.60,
        "human_follow": 0.40,
        "reason": "standard_state_answer",
        "range_key": "standard",
        "observation_units": 3,
        "human_follow_units": 2,
    },
    "structure_question_observation_thickened": {
        "observation": 0.70,
        "human_follow": 0.30,
        "reason": "structure_question_observation_thickened",
        "range_key": "structure_question",
        "observation_units": 4,
        "human_follow_units": 2,
    },
    "self_denial_follow_thickened": {
        "observation": 0.45,
        "human_follow": 0.55,
        "reason": "self_denial_follow_thickened",
        "range_key": "self_negative_or_uncertainty",
        "observation_units": 2,
        "human_follow_units": 3,
    },
    "grief_or_loneliness_follow_thickened": {
        "observation": 0.45,
        "human_follow": 0.55,
        "reason": "grief_or_loneliness_follow_thickened",
        "range_key": "self_denial_or_grief",
        "observation_units": 2,
        "human_follow_units": 3,
    },
    "exhaustion_balanced_follow": {
        "observation": 0.50,
        "human_follow": 0.50,
        "reason": "exhaustion_balanced_follow",
        "range_key": "exhaustion",
        "observation_units": 3,
        "human_follow_units": 3,
    },
    "anger_standard_with_inner_value_line": {
        "observation": 0.60,
        "human_follow": 0.40,
        "reason": "anger_standard_with_inner_value_line",
        "range_key": "standard",
        "observation_units": 3,
        "human_follow_units": 2,
    },
    "daily_unpleasant_reception_light": {
        "observation": 0.15,
        "human_follow": 0.85,
        "reason": "daily_unpleasant_reception_light",
        "range_key": "daily_reception",
        "observation_units": 1,
        "human_follow_units": 3,
    },
    "daily_positive_reception_light": {
        "observation": 0.20,
        "human_follow": 0.80,
        "reason": "daily_positive_reception_light",
        "range_key": "daily_reception",
        "observation_units": 1,
        "human_follow_units": 3,
    },
    "self_confidence_uncertainty_follow_thickened": {
        "observation": 0.35,
        "human_follow": 0.65,
        "reason": "self_confidence_uncertainty_follow_thickened",
        "range_key": "self_negative_or_uncertainty",
        "observation_units": 2,
        "human_follow_units": 4,
    },
}

_ALLOWED_RATIO_RANGES: Final = {
    "standard": {"observation_min": 0.55, "observation_max": 0.70},
    "self_denial_or_grief": {"observation_min": 0.40, "observation_max": 0.55},
    "structure_question": {"observation_min": 0.65, "observation_max": 0.75},
    "exhaustion": {"observation_min": 0.45, "observation_max": 0.55},
    "daily_reception": {"observation_min": 0.10, "observation_max": 0.30},
    "self_negative_or_uncertainty": {"observation_min": 0.30, "observation_max": 0.45},
}

_RATIO_PRESET_BY_RECEPTION_MODE: Final = {
    "daily_unpleasant_reception": "daily_unpleasant_reception_light",
    "daily_positive_reception": "daily_positive_reception_light",
    "self_denial_support": "self_denial_follow_thickened",
    "uncertainty_support": "self_confidence_uncertainty_follow_thickened",
    "structure_question_observation": "structure_question_observation_thickened",
}

_PHASE6_AUTO_RECEPTION_MODE_HINT_IDS: Final = frozenset(
    {
        "public_unpleasant_encounter",
        "positive_change_after_work_streaming",
        "self_confidence_uncertainty_attempt",
    }
)

_PHASE6_DAILY_RECEPTION_MODE_IDS: Final = frozenset(
    {"daily_unpleasant_reception", "daily_positive_reception"}
)

_PHASE6_SELF_NEGATIVE_OR_UNCERTAINTY_MODE_IDS: Final = frozenset(
    {"self_denial_support", "uncertainty_support"}
)

# Internal-only detectors.  The resolver may read the current input to choose a
# ratio, but never returns the read string or any span body.
_SPACE_RE: Final = re.compile(r"\s+")
_SELF_DENIAL_RE: Final = re.compile(
    r"(自分(?:なんか|など|は)?[^。！？!?]{0,18}(?:嫌い|きらい|ダメ|だめ|価値がない|価値ない|いらない|最低|クズ|消えたい|死にたい|生きてる意味|生きる意味)|"
    r"(?:私|わたし|俺|僕)(?:なんか|など)[^。！？!?]{0,18}(?:ダメ|だめ|いらない|価値がない|価値ない)|"
    r"(?:全部|すべて)(?:自分|私|俺|僕)が悪い)"
)
_STRUCTURE_QUESTION_RE: Final = re.compile(
    r"(なぜ|何故|どういうこと|どういう状態|どうして|なんで|何で|理由|構造|同じことになる|繰り返す|戻る)"
)
_SADNESS_RE: Final = re.compile(r"(悲し|つらい|辛い|泣きたい|喪失|失った|失う|苦しい)")
_LONELINESS_RE: Final = re.compile(r"(孤独|ひとりぼっち|一人ぼっち|寂し|さみし|誰にも言えない)")
_EXHAUSTION_RE: Final = re.compile(r"(疲れ|疲労|消耗|へとへと|ぐったり|くたくた|何もできない|動けない|もう無理)")
_ANGER_RE: Final = re.compile(r"(怒り|腹が立|腹立|ムカつ|むかつ|イライラ|いらいら|許せない|理不尽|不公平)")
_SELF_CONFIDENCE_UNCERTAINTY_RE: Final = re.compile(
    r"(自信[^。！？!?]{0,24}(?:ない|なく|つけたい|持てない)|"
    r"(?:これでいい|大丈夫|頑張れてる|がんばれてる)(?:のかな|かな|か不安)|"
    r"中途半端|自分を好きになれる|好きになれるように|色々挑戦|いろいろ挑戦)"
)

_FORBIDDEN_META_ONLY_PAYLOAD_KEYS: Final = frozenset(
    {
        "surface_policy",
        "definition",
        "evidence_requirements",
        "allowed_inference",
        "forbidden_inference",
        "default_direction",
        "strong_hand_direction",
        "notes",
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
        "observation_zero_allowed",
        "human_follow_zero_allowed",
        "comfort_only_allowed",
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
    }
)


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


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_environment_state_output_frame(
    *,
    current_source: Any,
    environment_state_output_frame: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if isinstance(environment_state_output_frame, Mapping):
        return copy.deepcopy(dict(environment_state_output_frame))
    return build_environment_state_output_frame(current_source or {})


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
        "structure_question_ids": _dedupe(material.get("structure_question_ids") or []),
        "relation_policy_ids": _dedupe(material.get("relation_policy_ids") or material.get("constraint_ids") or []),
        "low_information_candidate": bool(material.get("low_information_candidate")),
        "dictionary_is_observation_material_only": True,
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _source(frame: Mapping[str, Any]) -> dict[str, Any]:
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
                "read_as": "state_label_not_diagnosis",
            }
        )
    return out


def _emotion_types(frame: Mapping[str, Any]) -> list[str]:
    return _dedupe(item.get("type") for item in _emotion_labels(frame))


def _output_theme_ids(frame: Mapping[str, Any]) -> list[str]:
    output_axis = _as_mapping(frame.get("output_axis"))
    ids = _dedupe(output_axis.get("output_theme_ids") or [])
    for item in output_axis.get("output_theme_candidates") or []:
        if isinstance(item, Mapping):
            ids.extend(_dedupe(item.get("theme_id")))
    return _dedupe(ids)


def _relation_role_ids(frame: Mapping[str, Any], material: Mapping[str, Any]) -> list[str]:
    bridge = _as_mapping(frame.get("observation_structure_bridge"))
    return _dedupe(
        list(material.get("selected_relation_ids") or [])
        + list(material.get("graph_relation_ids") or [])
        + list(bridge.get("selected_relation_ids") or [])
    )


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


def _coerce_reception_mode_summary(
    *,
    current_source: Any,
    reception_mode_resolution: Any = None,
    reception_mode: str | None = None,
) -> dict[str, Any]:
    """Return the text-free subset of Reception Mode Resolver material.

    Phase 6 lets Ratio Policy read the backend-internal reception mode, but it
    must not forward the full resolver payload or any source text.  This summary
    keeps only ids, reason codes, flags, and policy ids required to pick a ratio
    preset.
    """

    raw: Mapping[str, Any] = {}
    source = "none"
    if reception_mode_resolution is not None:
        source = "provided_material"
        if hasattr(reception_mode_resolution, "as_meta"):
            try:
                candidate = reception_mode_resolution.as_meta()
                raw = candidate if isinstance(candidate, Mapping) else {}
            except Exception:
                raw = {}
                source = "provided_material_unreadable"
        elif isinstance(reception_mode_resolution, Mapping):
            raw = reception_mode_resolution
            source = "provided_mapping"
        else:
            scalar_mode = _clean(reception_mode_resolution)
            raw = {"reception_mode": scalar_mode} if scalar_mode else {}
            source = "provided_scalar"
    elif reception_mode:
        raw = {"reception_mode": reception_mode}
        source = "provided_reception_mode"
    elif current_source is not None:
        try:
            raw = resolve_emlis_reception_mode(current_source).as_meta()
            source = "resolved_from_current_input"
        except Exception:
            raw = {}
            source = "resolution_failed_closed"

    mode_policy = _as_mapping(raw.get("mode_policy"))
    selected_policy = _as_mapping(raw.get("selected_mode_policy"))
    mode_id = _clean(
        raw.get("reception_mode_id")
        or raw.get("reception_mode")
        or raw.get("selected_reception_mode_id")
    )
    ratio_preset = _clean(raw.get("ratio_preset") or mode_policy.get("ratio_preset") or selected_policy.get("ratio_preset"))
    primary_reason = _clean(raw.get("primary_reason"))
    secondary_mode_ids = _dedupe(raw.get("secondary_reception_mode_ids") or [])
    eligible_mode_ids = _dedupe(raw.get("eligible_dictionary_mode_ids") or raw.get("resolved_mode_ids") or [])
    if mode_id == "self_denial_support" and (
        "uncertainty_support" in set(secondary_mode_ids)
        or "uncertainty_support" in set(eligible_mode_ids)
        or "uncertainty" in primary_reason
    ):
        ratio_preset = "self_confidence_uncertainty_follow_thickened"
    elif ratio_preset not in _RATIO_PRESETS:
        ratio_preset = _RATIO_PRESET_BY_RECEPTION_MODE.get(mode_id, "")

    return {
        "available": bool(mode_id),
        "source": source,
        "reception_mode_id": mode_id,
        "primary_reason": primary_reason,
        "ratio_preset": ratio_preset,
        "event_hint_ids": _dedupe(raw.get("event_hint_ids") or []),
        "secondary_reception_mode_ids": secondary_mode_ids,
        "eligible_reception_mode_ids": eligible_mode_ids,
        "low_information_question_required": bool(raw.get("low_information_question_required")),
        "low_information_question_allowed": bool(raw.get("low_information_question_allowed")),
        "safety_path_required": bool(raw.get("safety_path_required") or raw.get("existing_safety_path_required")),
        "event_fact_present": bool(raw.get("event_fact_present")),
        "reaction_present": bool(raw.get("reaction_present")),
        "phase6_reception_mode_ratio_policy_connected": True,
        "general_dictionary_used": False,
        "unknown_word_meaning_asserted": False,
        "event_hint_created_emotion": False,
        "event_hint_alone_activated_mode": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
    }


def _reason_from_reception_mode_summary(summary: Mapping[str, Any]) -> str:
    if not summary.get("available"):
        return ""
    if summary.get("safety_path_required") or summary.get("low_information_question_required"):
        return ""

    preset = _clean(summary.get("ratio_preset"))
    if preset not in _RATIO_PRESETS:
        return ""

    source = _clean(summary.get("source"))
    mode_id = _clean(summary.get("reception_mode_id"))
    if source.startswith("provided"):
        return preset

    event_hints = set(_dedupe(summary.get("event_hint_ids") or []))
    if mode_id in _PHASE6_DAILY_RECEPTION_MODE_IDS:
        return preset if event_hints.intersection(_PHASE6_AUTO_RECEPTION_MODE_HINT_IDS) else ""
    if mode_id in _PHASE6_SELF_NEGATIVE_OR_UNCERTAINTY_MODE_IDS:
        return preset if event_hints.intersection(_PHASE6_AUTO_RECEPTION_MODE_HINT_IDS) else ""
    return ""


def _current_signal(current_source: Any) -> dict[str, bool]:
    if current_source is None:
        return {
            "self_denial_signal": False,
            "self_confidence_uncertainty_signal": False,
            "structure_question_signal": False,
            "sadness_signal": False,
            "loneliness_signal": False,
            "exhaustion_signal": False,
            "anger_signal": False,
        }
    bundle = build_emlis_current_input_bundle(current_source)
    # Internal-only.  Do not expose this joined value in the returned material.
    joined = "\n".join(
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
        "self_denial_signal": bool(_SELF_DENIAL_RE.search(joined)),
        "self_confidence_uncertainty_signal": bool(_SELF_CONFIDENCE_UNCERTAINTY_RE.search(joined)),
        "structure_question_signal": bool(_STRUCTURE_QUESTION_RE.search(joined)),
        "sadness_signal": bool(_SADNESS_RE.search(joined)),
        "loneliness_signal": bool(_LONELINESS_RE.search(joined)),
        "exhaustion_signal": bool(_EXHAUSTION_RE.search(joined)),
        "anger_signal": bool(_ANGER_RE.search(joined)),
    }


def _input_type_from_follow_layer(human_follow_layer: Mapping[str, Any] | None) -> str:
    layer = _as_mapping(human_follow_layer)
    return _clean(layer.get("selector_input_type") or layer.get("input_type"))


def _input_type_from_signals(
    *,
    emotion_types: Sequence[str],
    output_theme_ids: Sequence[str],
    relation_role_ids: Sequence[str],
    current_signal: Mapping[str, bool],
) -> str:
    emotions = " ".join(emotion_types)
    themes = set(output_theme_ids)
    relations = set(relation_role_ids)
    if current_signal.get("self_denial_signal") or any(term in emotions for term in ("自己否定", "自責", "無価値")):
        return "self_denial"
    if current_signal.get("self_confidence_uncertainty_signal"):
        return "self_confidence_uncertainty"
    if current_signal.get("anger_signal") or any(term in emotions for term in ("怒り", "苛立ち", "イライラ")):
        return "anger"
    if current_signal.get("loneliness_signal") or any(term in emotions for term in ("孤独", "寂しさ", "さみしさ", "寂しい")):
        return "loneliness"
    if current_signal.get("sadness_signal") or any(term in emotions for term in ("悲しみ", "悲しい", "喪失")):
        return "sadness"
    if current_signal.get("exhaustion_signal") or any(term in emotions for term in ("疲れ", "疲労", "消耗", "しんどい")):
        return "exhaustion"
    if themes.intersection({"direction_concern", "unformed_self_insight", "reason_became_visible"}) or relations.intersection({"unformed_self_insight", "self_insight_discovery"}):
        return "structure_question" if current_signal.get("structure_question_signal") else "standard_state_answer"
    return "standard_state_answer"


def _structure_question_detected(
    *,
    material: Mapping[str, Any],
    output_theme_ids: Sequence[str],
    relation_role_ids: Sequence[str],
    current_signal: Mapping[str, bool],
    human_follow_layer: Mapping[str, Any] | None,
) -> bool:
    layer = _as_mapping(human_follow_layer)
    selector_basis = _dedupe(layer.get("selector_basis") or [])
    # Observation-structure material may carry internal question ids for the
    # dictionary itself.  That is not the same as the user asking for structure
    # understanding.  Phase 4 thickens observation only when the current input or
    # an explicit upstream flag says the user is asking "why / what is this".
    return bool(
        current_signal.get("structure_question_signal")
        or bool(layer.get("structure_question_requested"))
        or bool(material.get("structure_question_requested"))
        or bool(material.get("user_structure_question_requested"))
        or "structure_question" in selector_basis
    )


def _strong_temperature(
    *,
    input_type: str,
    strength_summary: Mapping[str, Any],
    current_signal: Mapping[str, bool],
    human_follow_layer: Mapping[str, Any] | None,
) -> bool:
    if _as_mapping(human_follow_layer).get("strong_follow_candidate"):
        return True
    if input_type in {"self_denial", "self_confidence_uncertainty", "sadness", "loneliness", "exhaustion"}:
        return True
    return bool(strength_summary.get("has_strong") or int(strength_summary.get("max_strength_score") or 0) >= 3)


def _resolve_reason(
    *,
    input_type: str,
    structure_question_detected: bool,
    strong_temperature: bool,
    reception_mode_summary: Mapping[str, Any],
) -> str:
    reception_mode_reason = _reason_from_reception_mode_summary(reception_mode_summary)
    if reception_mode_reason:
        return reception_mode_reason

    # Emotional safety takes precedence over observation-thickening.  A self-denial
    # or grief-like question still needs a receivable temperature rather than a
    # cold 7:3 explanation.
    if input_type == "self_denial":
        return "self_denial_follow_thickened"
    if input_type == "self_confidence_uncertainty":
        return "self_confidence_uncertainty_follow_thickened"
    if input_type in {"sadness", "loneliness"}:
        return "grief_or_loneliness_follow_thickened"
    if input_type == "exhaustion":
        return "exhaustion_balanced_follow"
    if structure_question_detected and input_type not in {"anger"}:
        return "structure_question_observation_thickened"
    if input_type == "anger":
        return "anger_standard_with_inner_value_line"
    return "standard_state_answer"


def _follow_key_count(human_follow_layer: Mapping[str, Any] | None) -> int:
    layer = _as_mapping(human_follow_layer)
    slots = layer.get("follow_key_slots") or []
    if isinstance(slots, Sequence) and not isinstance(slots, (str, bytes)):
        count = len([slot for slot in slots if isinstance(slot, Mapping)])
        if count:
            return count
    secondaries = _dedupe(layer.get("secondary_follow_keys") or [])
    return int(bool(_clean(layer.get("primary_follow_key")))) + len(secondaries) + int(bool(_clean(layer.get("afterglow_follow_key"))))


def _ratio_basis(
    *,
    preset: Mapping[str, Any],
    human_follow_layer: Mapping[str, Any] | None,
) -> dict[str, Any]:
    observation_units = int(preset.get("observation_units") or 3)
    human_follow_units = int(preset.get("human_follow_units") or 2)
    return {
        "measurement_basis": ["section_role", "sentence_plan_unit_count", "follow_key_count"],
        "character_count_exact": False,
        "strict_character_count_used": False,
        "section_role_unit_plan": {
            "observation_section_role": "state_answer_observation",
            "human_follow_section_role": "human_follow",
            "observation_units": observation_units,
            "human_follow_units": human_follow_units,
            "total_units": observation_units + human_follow_units,
        },
        "follow_key_count": _follow_key_count(human_follow_layer) or 4,
        "primary_follow_required": True,
        "secondary_follow_required_count": 2,
        "afterglow_follow_required": True,
        "observation_zero_allowed": False,
        "human_follow_zero_allowed": False,
        "comfort_only_allowed": False,
        "observation_section_required_even_when_follow_thickened": True,
        "human_follow_section_required_even_when_observation_thickened": True,
    }


def _surface_policy() -> dict[str, Any]:
    return {
        "material_only": True,
        "ratio_is_character_count_exact": False,
        "must_not_generate_completed_reply": True,
        "must_not_generate_comment_text": True,
        "observation_zero_allowed": False,
        "human_follow_zero_allowed": False,
        "comfort_only_allowed": False,
        "consolation_only_allowed": False,
        "action_instruction_allowed": False,
        "diagnosis_allowed": False,
        "personality_claim_allowed": False,
        "cause_from_category": False,
        "cause_from_emotion_strength": False,
        "period_tendency_from_single_record": False,
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
        "display_gate_relaxed": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }


def _surface_policy_meta_flags(policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Project the internal ratio surface policy into safe scalar flags.

    Phase18 keeps the full policy available inside the dataclass, but does not
    expose a ``surface_policy`` key through meta / forward / composer / gate
    payloads.  The exported fields are bodyless booleans and counts only.
    """

    policy = _as_mapping(policy)
    return {
        "state_answer_ratio_policy_meta_only_sanitizer_schema_version": EMLIS_AI_STATE_ANSWER_RATIO_POLICY_META_ONLY_SANITIZER_SCHEMA_VERSION,
        "state_answer_ratio_policy_meta_only_sanitizer_source_phase": EMLIS_AI_STATE_ANSWER_RATIO_POLICY_META_ONLY_SANITIZER_PHASE,
        "state_answer_ratio_surface_policy_material_only": bool(policy.get("material_only", True)),
        "state_answer_ratio_surface_policy_must_not_generate_completed_reply": bool(
            policy.get("must_not_generate_completed_reply", True)
        ),
        "state_answer_ratio_surface_policy_must_not_generate_comment_text": bool(
            policy.get("must_not_generate_comment_text", True)
        ),
        "state_answer_ratio_surface_policy_observation_zero_allowed": bool(
            policy.get("observation_zero_allowed", False)
        ),
        "state_answer_ratio_surface_policy_human_follow_zero_allowed": bool(
            policy.get("human_follow_zero_allowed", False)
        ),
        "state_answer_ratio_surface_policy_comfort_only_allowed": bool(
            policy.get("comfort_only_allowed", False)
        ),
        "state_answer_ratio_surface_policy_action_instruction_allowed": bool(
            policy.get("action_instruction_allowed", False)
        ),
        "state_answer_ratio_surface_policy_diagnosis_allowed": bool(policy.get("diagnosis_allowed", False)),
        "state_answer_ratio_surface_policy_personality_claim_allowed": bool(
            policy.get("personality_claim_allowed", False)
        ),
        "state_answer_ratio_surface_policy_cause_from_category": bool(policy.get("cause_from_category", False)),
        "state_answer_ratio_surface_policy_cause_from_emotion_strength": bool(
            policy.get("cause_from_emotion_strength", False)
        ),
        "state_answer_ratio_surface_policy_period_tendency_from_single_record": bool(
            policy.get("period_tendency_from_single_record", False)
        ),
        "state_answer_ratio_surface_policy_comment_text_body_included": bool(
            policy.get("comment_text_body_included", False)
        ),
        "state_answer_ratio_surface_policy_raw_input_included": bool(policy.get("raw_input_included", False)),
        "state_answer_ratio_surface_policy_raw_text_included": bool(policy.get("raw_text_included", False)),
    }


@dataclass(frozen=True)
class EmlisStateAnswerRatioPolicy:
    """Text-free Phase 4 material for observation / follow ratio resolution."""

    source: Mapping[str, Any]
    default_ratio: Mapping[str, float]
    resolved_ratio: Mapping[str, Any]
    allowed_ranges: Mapping[str, Any]
    ratio_basis: Mapping[str, Any]
    resolver_context: Mapping[str, Any]
    surface_policy: Mapping[str, Any]
    schema_version: str = EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION
    material_id: str = EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID
    internal_name: str = EMLIS_AI_STATE_ANSWER_RATIO_POLICY_INTERNAL_NAME
    phase: str = EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE
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
            "default_ratio": _deepcopy_mapping(self.default_ratio),
            "resolved_ratio": _deepcopy_mapping(self.resolved_ratio),
            "allowed_ranges": copy.deepcopy(dict(self.allowed_ranges or {})),
            "ratio_basis": _deepcopy_mapping(self.ratio_basis),
            "resolver_context": _deepcopy_mapping(self.resolver_context),
            **_surface_policy_meta_flags(self.surface_policy),
            "ratio_policy_resolver_connected": True,
            "state_answer_ratio_policy_connected": True,
            "state_answer_ratio_policy_material_only": True,
            "phase6_reception_mode_ratio_policy_connected": True,
            "reception_mode_resolution_connected": bool(
                _as_mapping(self.resolver_context).get("reception_mode_resolution_connected")
            ),
            "phase6_source_phase": EMLIS_AI_STATE_ANSWER_RATIO_POLICY_TWO_STAGE_PHASE,
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
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
            "personality_claim_allowed": False,
            "personality_tendency_allowed": False,
        }
        assert_state_answer_ratio_policy_contract(meta)
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
            "state_answer_ratio_policy_connected": True,
            "state_answer_ratio_policy_material_only": True,
            "phase6_reception_mode_ratio_policy_connected": True,
            "resolved_ratio": _deepcopy_mapping(meta.get("resolved_ratio")),
            "ratio_reason": _as_mapping(meta.get("resolved_ratio")).get("reason") or "",
            "ratio_basis": _deepcopy_mapping(meta.get("ratio_basis")),
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
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
            "default_ratio": _deepcopy_mapping(meta.get("default_ratio")),
            "resolved_ratio": _deepcopy_mapping(meta.get("resolved_ratio")),
            "allowed_ranges": copy.deepcopy(dict(meta.get("allowed_ranges") or {})),
            "ratio_basis": _deepcopy_mapping(meta.get("ratio_basis")),
            "resolver_context": _deepcopy_mapping(meta.get("resolver_context")),
            "state_answer_ratio_policy_connected": True,
            "state_answer_ratio_policy_material_only": True,
            "phase6_reception_mode_ratio_policy_connected": True,
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
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


def build_emlis_ai_state_answer_ratio_policy(
    current_source: Any = None,
    *,
    environment_state_output_frame: Mapping[str, Any] | None = None,
    observation_structure_material: Any = None,
    human_follow_layer: Mapping[str, Any] | None = None,
    reception_mode_resolution: Any = None,
    reception_mode: str | None = None,
) -> EmlisStateAnswerRatioPolicy:
    """Resolve the Phase 4 observation / human-follow ratio.

    The resolver uses input type, structure-question signals, section roles, and
    follow-key slots.  It deliberately avoids exact character counting and
    returns only internal material.
    """

    frame = _coerce_environment_state_output_frame(
        current_source=current_source,
        environment_state_output_frame=environment_state_output_frame,
    )
    material = _material_summary(observation_structure_material)
    emotion_types = _emotion_types(frame)
    output_themes = _output_theme_ids(frame)
    relations = _relation_role_ids(frame, material)
    strength = _strength_summary(frame)
    signal = _current_signal(current_source)
    follow_layer = _as_mapping(human_follow_layer)
    reception_mode_summary = _coerce_reception_mode_summary(
        current_source=current_source,
        reception_mode_resolution=reception_mode_resolution,
        reception_mode=reception_mode,
    )

    input_type = _input_type_from_follow_layer(follow_layer) or _input_type_from_signals(
        emotion_types=emotion_types,
        output_theme_ids=output_themes,
        relation_role_ids=relations,
        current_signal=signal,
    )
    structure_question = _structure_question_detected(
        material=material,
        output_theme_ids=output_themes,
        relation_role_ids=relations,
        current_signal=signal,
        human_follow_layer=follow_layer,
    )
    strong_temperature = _strong_temperature(
        input_type=input_type,
        strength_summary=strength,
        current_signal=signal,
        human_follow_layer=follow_layer,
    )
    reason = _resolve_reason(
        input_type=input_type,
        structure_question_detected=structure_question,
        strong_temperature=strong_temperature,
        reception_mode_summary=reception_mode_summary,
    )
    preset = _RATIO_PRESETS[reason]
    resolved_ratio = {
        "observation": _safe_float(preset.get("observation"), default=DEFAULT_OBSERVATION_RATIO),
        "human_follow": _safe_float(preset.get("human_follow"), default=DEFAULT_HUMAN_FOLLOW_RATIO),
        "reason": preset.get("reason") or reason,
        "range_key": preset.get("range_key") or "standard",
        "resolver_phase": EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE,
    }
    context = {
        "input_type": input_type or "standard_state_answer",
        "structure_question_detected": bool(structure_question),
        "strong_temperature": bool(strong_temperature),
        "emotion_types": _dedupe(emotion_types),
        "output_theme_ids": _dedupe(output_themes),
        "relation_role_ids": _dedupe(relations),
        "structure_question_ids": _dedupe(material.get("structure_question_ids") or []),
        "strength_summary": _deepcopy_mapping(strength),
        "follow_layer_input_type": _input_type_from_follow_layer(follow_layer),
        "reception_mode_summary": _deepcopy_mapping(reception_mode_summary),
        "reception_mode_resolution_connected": bool(reception_mode_summary.get("available")),
        "reception_mode_resolution_source": _clean(reception_mode_summary.get("source")),
        "reception_mode": _clean(reception_mode_summary.get("reception_mode_id")),
        "reception_mode_id": _clean(reception_mode_summary.get("reception_mode_id")),
        "reception_mode_ratio_preset": _clean(reception_mode_summary.get("ratio_preset")),
        "reception_mode_primary_reason": _clean(reception_mode_summary.get("primary_reason")),
        "reception_mode_secondary_ids": _dedupe(reception_mode_summary.get("secondary_reception_mode_ids") or []),
        "reception_mode_eligible_dictionary_mode_ids": _dedupe(reception_mode_summary.get("eligible_reception_mode_ids") or []),
        "reception_mode_event_fact_present": bool(reception_mode_summary.get("event_fact_present")),
        "reception_mode_reaction_present": bool(reception_mode_summary.get("reaction_present")),
        "phase6_reception_mode_ratio_policy_connected": True,
        "reception_mode_ratio_reason_used": reason
        if reason == _clean(reception_mode_summary.get("ratio_preset"))
        else "",
        "strong_follow_candidate": bool(follow_layer.get("strong_follow_candidate")),
        "current_signal_ids": _dedupe(
            [key[:-7] for key, enabled in signal.items() if enabled and key.endswith("_signal")]
        ),
        "safety_precedence": "emotional_temperature_over_structure_question" if reason in {"self_denial_follow_thickened", "self_confidence_uncertainty_follow_thickened", "grief_or_loneliness_follow_thickened", "exhaustion_balanced_follow"} else "standard_or_structure_question",
        "category_read_as": "topic_direction_not_cause",
        "emotion_strength_read_as": "weight_not_cause",
        "single_record_only": True,
        "raw_text_included": False,
    }
    policy = EmlisStateAnswerRatioPolicy(
        source=_source(frame),
        default_ratio={"observation": DEFAULT_OBSERVATION_RATIO, "human_follow": DEFAULT_HUMAN_FOLLOW_RATIO},
        resolved_ratio=resolved_ratio,
        allowed_ranges=copy.deepcopy(_ALLOWED_RATIO_RANGES),
        ratio_basis=_ratio_basis(preset=preset, human_follow_layer=follow_layer),
        resolver_context=context,
        surface_policy=_surface_policy(),
    )
    assert_state_answer_ratio_policy_contract(policy)
    return policy


def state_answer_ratio_policy_forward_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerRatioPolicy):
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
        "default_ratio",
        "resolved_ratio",
        "allowed_ranges",
        "ratio_basis",
        "resolver_context",
        "state_answer_ratio_policy_meta_only_sanitizer_schema_version",
        "state_answer_ratio_policy_meta_only_sanitizer_source_phase",
        "state_answer_ratio_surface_policy_material_only",
        "state_answer_ratio_surface_policy_must_not_generate_completed_reply",
        "state_answer_ratio_surface_policy_must_not_generate_comment_text",
        "state_answer_ratio_surface_policy_observation_zero_allowed",
        "state_answer_ratio_surface_policy_human_follow_zero_allowed",
        "state_answer_ratio_surface_policy_comfort_only_allowed",
        "state_answer_ratio_surface_policy_action_instruction_allowed",
        "state_answer_ratio_surface_policy_diagnosis_allowed",
        "state_answer_ratio_surface_policy_personality_claim_allowed",
        "state_answer_ratio_surface_policy_cause_from_category",
        "state_answer_ratio_surface_policy_cause_from_emotion_strength",
        "state_answer_ratio_surface_policy_period_tendency_from_single_record",
        "state_answer_ratio_surface_policy_comment_text_body_included",
        "state_answer_ratio_surface_policy_raw_input_included",
        "state_answer_ratio_surface_policy_raw_text_included",
        "phase6_reception_mode_ratio_policy_connected",
        "ratio_policy_resolver_connected",
        "state_answer_ratio_policy_connected",
        "state_answer_ratio_policy_material_only",
        "ratio_is_character_count_exact",
        "observation_zero_allowed",
        "human_follow_zero_allowed",
        "comfort_only_allowed",
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
        "personality_claim_allowed",
        "personality_tendency_allowed",
    }
    out = {key: copy.deepcopy(meta.get(key)) for key in keys if key in meta}
    assert_state_answer_ratio_policy_contract(out)
    return out


def state_answer_ratio_policy_gate_report(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerRatioPolicy):
        report = value.gate_report()
    elif isinstance(value, Mapping):
        meta = state_answer_ratio_policy_forward_meta(value)
        if not meta:
            return {}
        report = {
            "schema_version": meta.get("schema_version") or EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION,
            "material_id": meta.get("material_id") or EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID,
            "passed": bool(meta.get("passed", True)),
            "evaluated": True,
            "status": meta.get("status") or "passed",
            "rejection_reasons": list(meta.get("rejection_reasons") or []),
            "state_answer_ratio_policy_connected": True,
            "state_answer_ratio_policy_material_only": True,
            "resolved_ratio": _deepcopy_mapping(_as_mapping(meta.get("resolved_ratio"))),
            "ratio_reason": _as_mapping(meta.get("resolved_ratio")).get("reason") or "",
            "ratio_basis": _deepcopy_mapping(_as_mapping(meta.get("ratio_basis"))),
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
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
    assert_state_answer_ratio_policy_contract(report)
    return report


def state_answer_ratio_policy_composer_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisStateAnswerRatioPolicy):
        payload = value.composer_payload()
    elif isinstance(value, Mapping):
        meta = state_answer_ratio_policy_forward_meta(value)
        if not meta:
            return {}
        payload = {
            "schema_version": meta.get("schema_version") or EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION,
            "material_id": meta.get("material_id") or EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID,
            "source_phase": meta.get("source_phase") or meta.get("phase") or EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE,
            "default_ratio": _deepcopy_mapping(_as_mapping(meta.get("default_ratio"))),
            "resolved_ratio": _deepcopy_mapping(_as_mapping(meta.get("resolved_ratio"))),
            "allowed_ranges": copy.deepcopy(dict(meta.get("allowed_ranges") or {})),
            "ratio_basis": _deepcopy_mapping(_as_mapping(meta.get("ratio_basis"))),
            "resolver_context": _deepcopy_mapping(_as_mapping(meta.get("resolver_context"))),
            "state_answer_ratio_policy_connected": True,
            "state_answer_ratio_policy_material_only": True,
            "ratio_is_character_count_exact": False,
            "observation_zero_allowed": False,
            "human_follow_zero_allowed": False,
            "comfort_only_allowed": False,
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
    assert_state_answer_ratio_policy_contract(payload)
    return payload


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_name = _clean(key)
            if key_name in _FORBIDDEN_RAW_PAYLOAD_KEYS or key_name in _FORBIDDEN_META_ONLY_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


def assert_state_answer_ratio_policy_contract(value: Any, *, source: str = "state_answer_ratio_policy") -> None:
    if isinstance(value, EmlisStateAnswerRatioPolicy):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    schema_version = _clean(value.get("schema_version"))
    if schema_version not in {"", EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION}:
        raise ValueError(f"{source} has unexpected schema_version")
    material_id = _clean(value.get("material_id"))
    if material_id not in {"", EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID}:
        raise ValueError(f"{source} has unexpected material_id")

    resolved = _as_mapping(value.get("resolved_ratio"))
    if resolved:
        observation = _safe_float(resolved.get("observation"), default=-1.0)
        human_follow = _safe_float(resolved.get("human_follow"), default=-1.0)
        if observation <= 0.0 or human_follow <= 0.0:
            raise ValueError(f"{source} must not resolve observation or human_follow to zero")
        if observation + human_follow <= 0.0:
            raise ValueError(f"{source} resolved ratio must be positive")
        if not _clean(resolved.get("reason")):
            raise ValueError(f"{source} resolved_ratio.reason is required")
        range_key = _clean(resolved.get("range_key"))
        allowed = _as_mapping(_as_mapping(value.get("allowed_ranges")).get(range_key))
        if allowed:
            min_observation = _safe_float(allowed.get("observation_min"), default=-1.0)
            max_observation = _safe_float(allowed.get("observation_max"), default=2.0)
            if not (min_observation <= observation <= max_observation):
                raise ValueError(f"{source} resolved observation ratio outside allowed range")

    basis = _as_mapping(value.get("ratio_basis"))
    if basis:
        if bool(basis.get("character_count_exact")):
            raise ValueError(f"{source} must not use exact character count")
        unit_plan = _as_mapping(basis.get("section_role_unit_plan"))
        if unit_plan:
            if int(unit_plan.get("observation_units") or 0) <= 0:
                raise ValueError(f"{source} must keep observation section units above zero")
            if int(unit_plan.get("human_follow_units") or 0) <= 0:
                raise ValueError(f"{source} must keep human follow section units above zero")
        if bool(basis.get("comfort_only_allowed")):
            raise ValueError(f"{source} must not allow comfort-only output")

    if value.get("material_is_completed_reply_template") is True:
        raise ValueError(f"{source} must not be a completed reply template")
    if value.get("state_answer_ratio_policy_connected") is False:
        raise ValueError(f"{source} must keep state_answer_ratio_policy_connected=true when present")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


# Aliases for call-site readability.
build_state_answer_ratio_policy = build_emlis_ai_state_answer_ratio_policy
assert_emlis_ai_state_answer_ratio_policy_contract = assert_state_answer_ratio_policy_contract

__all__ = [
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_SCHEMA_VERSION",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_MATERIAL_ID",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_PHASE",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_INTERNAL_NAME",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_META_ONLY_SANITIZER_SCHEMA_VERSION",
    "EMLIS_AI_STATE_ANSWER_RATIO_POLICY_META_ONLY_SANITIZER_PHASE",
    "DEFAULT_OBSERVATION_RATIO",
    "DEFAULT_HUMAN_FOLLOW_RATIO",
    "EmlisStateAnswerRatioPolicy",
    "build_emlis_ai_state_answer_ratio_policy",
    "build_state_answer_ratio_policy",
    "state_answer_ratio_policy_forward_meta",
    "state_answer_ratio_policy_gate_report",
    "state_answer_ratio_policy_composer_payload",
    "assert_state_answer_ratio_policy_contract",
    "assert_emlis_ai_state_answer_ratio_policy_contract",
]
