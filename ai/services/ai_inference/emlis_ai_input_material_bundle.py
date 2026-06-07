# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-3 input material bundle for EmlisAI.

This module reads the existing current-input bundle as an internal material
bundle.  It does not add public API keys, DB fields, RN-visible fields, fixed
fallback text, or case-id runtime conditions.  The purpose is to decide the
observable range from thought/action/emotion/category together, so that low
information means material shortage rather than short text length.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import EmlisCurrentInputBundle, build_emlis_current_input_bundle
from emlis_ai_safety_triage import (
    EmlisSafetyTriageDecision,
    TRIAGE_SAFE_OBSERVATION,
    build_emlis_safety_triage_decision,
)

EMLIS_INPUT_MATERIAL_BUNDLE_SCHEMA_VERSION: Final = "cocolon.emlis.input_material_bundle.v1"
EMLIS_INPUT_MATERIAL_BUNDLE_SOURCE_PHASE: Final = "Phase20-3_Input_Material_Bundle"
EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY: Final = "emlis_input_material_bundle"

MATERIAL_QUALITY_ELIGIBLE: Final = "eligible"
MATERIAL_QUALITY_LOW_INFORMATION: Final = "low_information"
MATERIAL_QUALITY_LIMITED_GROUNDING: Final = "limited_grounding"
MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED: Final = "safety_triage_required"

VISIBLE_MATERIAL_SLOT_EVENT: Final = "event"
VISIBLE_MATERIAL_SLOT_TARGET: Final = "target"
VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION: Final = "emotion_direction"
VISIBLE_MATERIAL_SLOT_RELATIONSHIP: Final = "relationship"
VISIBLE_MATERIAL_SLOT_ACTION: Final = "action"
VISIBLE_MATERIAL_SLOT_CHANGE: Final = "change"
VISIBLE_MATERIAL_SLOT_TIME: Final = "time"
VISIBLE_MATERIAL_SLOT_VALUE: Final = "value"
VISIBLE_MATERIAL_SLOT_UNRESOLVED_WEIGHT: Final = "unresolved_weight"

VISIBLE_SLOT_EVENT: Final = VISIBLE_MATERIAL_SLOT_EVENT
VISIBLE_SLOT_TARGET: Final = VISIBLE_MATERIAL_SLOT_TARGET
VISIBLE_SLOT_EMOTION_DIRECTION: Final = VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION
VISIBLE_SLOT_RELATIONSHIP: Final = VISIBLE_MATERIAL_SLOT_RELATIONSHIP
VISIBLE_SLOT_ACTION: Final = VISIBLE_MATERIAL_SLOT_ACTION
VISIBLE_SLOT_CHANGE: Final = VISIBLE_MATERIAL_SLOT_CHANGE
VISIBLE_SLOT_TIME: Final = VISIBLE_MATERIAL_SLOT_TIME
VISIBLE_SLOT_VALUE: Final = VISIBLE_MATERIAL_SLOT_VALUE
VISIBLE_SLOT_UNRESOLVED_WEIGHT: Final = VISIBLE_MATERIAL_SLOT_UNRESOLVED_WEIGHT

UNKNOWN_SLOT_EVENT: Final = "event"
UNKNOWN_SLOT_TARGET: Final = "target"
UNKNOWN_SLOT_CAUSE: Final = "cause"
UNKNOWN_SLOT_RELATIONSHIP: Final = "relationship"
UNKNOWN_SLOT_DURATION: Final = "duration"
UNKNOWN_SLOT_USER_INTENT: Final = "user_intent"
UNKNOWN_SLOT_NEXT_ACTION: Final = "next_action"
UNKNOWN_SLOT_IMPACT: Final = "impact"

_ALLOWED_VISIBLE_MATERIAL_SLOTS: Final = frozenset(
    {
        VISIBLE_MATERIAL_SLOT_EVENT,
        VISIBLE_MATERIAL_SLOT_TARGET,
        VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION,
        VISIBLE_MATERIAL_SLOT_RELATIONSHIP,
        VISIBLE_MATERIAL_SLOT_ACTION,
        VISIBLE_MATERIAL_SLOT_CHANGE,
        VISIBLE_MATERIAL_SLOT_TIME,
        VISIBLE_MATERIAL_SLOT_VALUE,
        VISIBLE_MATERIAL_SLOT_UNRESOLVED_WEIGHT,
    }
)
_ALLOWED_UNKNOWN_SLOTS: Final = frozenset(
    {
        UNKNOWN_SLOT_EVENT,
        UNKNOWN_SLOT_TARGET,
        UNKNOWN_SLOT_CAUSE,
        UNKNOWN_SLOT_RELATIONSHIP,
        UNKNOWN_SLOT_DURATION,
        UNKNOWN_SLOT_USER_INTENT,
        UNKNOWN_SLOT_NEXT_ACTION,
        UNKNOWN_SLOT_IMPACT,
    }
)
_ALLOWED_MATERIAL_QUALITIES: Final = frozenset(
    {
        MATERIAL_QUALITY_ELIGIBLE,
        MATERIAL_QUALITY_LOW_INFORMATION,
        MATERIAL_QUALITY_LIMITED_GROUNDING,
        MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    }
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "memo",
        "memo_action",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
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
        "fixed_fallback_used",
        "case_id_runtime_condition_used",
        "phase_name_runtime_condition_used",
        "phase19_cd_specific_cue_runtime_used",
        "phase19_case_specific_route_used",
        "low_information_is_length_only",
    }
)

_SPACE_RE: Final = re.compile(r"\s+")
_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?\n]+")
_VAGUE_ONLY_RE: Final = re.compile(r"^(なんか|なんとなく|全部|いろいろ|色々|あれ|それ|これ|つらい|しんどい|だるい|疲れた|無理|特になし|なし|ない)$")
_VAGUE_LOAD_RE: Final = re.compile(r"(なんか|なんとなく|全部|だる|しんど|つら|疲れ|何もしたくない|無理|重い|余裕ない|わからない|分からない|モヤモヤ|もやもや)")
_EMOTION_WORD_RE: Final = re.compile(r"(不安|悲し|怒|怖|恐|嫌|安心|嬉し|うれし|寂し|さみし|つら|しんど|だる|悔し|焦)")
_RELATIONSHIP_RE: Final = re.compile(r"(友達|友人|彼氏|彼女|恋人|元彼|元カレ|元恋人|家族|母|父|親|子ども|職場|上司|同僚|相手|人間関係|恋愛|関係)")
_EVENT_RE: Final = re.compile(r"(会っ|言われ|話し|話す|聞い|見た|起き|別れ|終わり|終わっ|怒って|怒ら|メモ|書い|考え|行動|出かけ|仕事|学校|配信|投稿|連絡|返して)")
_ACTION_RE: Final = re.compile(r"(したい|しよう|行動|返していきたい|始め|続け|やめ|向き合|直したい|学び|メモ|書い)")
_CHANGE_RE: Final = re.compile(r"(変わ|変化|進歩|大丈夫|できるよう|なりたい|終わり|区切り|別れ|戻|回復|整理)")
_TIME_RE: Final = re.compile(r"(今日|昨日|明日|最近|今|さっき|いつも|また|前|後|日常|朝|夜|週|月)")
_VALUE_RE: Final = re.compile(r"(感謝|ありがた|優し|優しく|大事|大切|勇気|価値|返していきたい|守りたい|区切り)")
_TARGET_RE: Final = re.compile(r"(対象|疑問|人|物|仕事|学校|体調|お金|生活|恋愛|価値観|学習|家族|関係|日常|メモ)")
_GENERIC_RELATION_MATERIAL_PATTERNS: Final = {
    "relationship_end": ("別れ", "別れた", "関係の終わり", "終わり"),
    "support_from_other": ("友達", "友人", "優しく", "優しさ", "怒ってくれて", "私のために怒って"),
    "gratitude_or_return_intent": ("感謝", "返していきたい", "別の形で", "ありがた"),
    "self_understanding_learning": ("疑問", "対象", "人について", "人への興味", "人との話し方", "メモ", "進歩", "勇気"),
    "boundary_or_transition": ("区切り", "大丈夫", "変わ", "行動", "日常", "傷", "汚れ"),
}
_SEMANTIC_MATERIAL_PATTERNS: Final = {
    # P7: these are general, text-grounded material ids for limited reception.
    # They are not H/I/J case routes and are not generated surface text.
    "recovered_energy": (
        "気力",
        "やる気力",
        "やってみたい",
        "出来るかもしれない",
        "できるかもしれない",
        "挑戦",
        "頑張",
    ),
    "future_intention": (
        "このタイミング",
        "逃したくない",
        "逃したら",
        "次どう頑張",
        "つぎどう頑張",
        "していきたい",
        "出会えたら",
        "過ごしていきたい",
        "知って行きたい",
        "知っていきたい",
    ),
    "relationship_wish": (
        "そばに",
        "側に",
        "居てくれる",
        "いてくれる",
        "恋愛",
        "出会え",
        "素敵な人",
        "存在",
        "甘え",
    ),
    "comparison_baseline_shift": (
        "昨日の自分",
        "人と比べ",
        "比べる相手",
        "他の誰か",
    ),
    "small_change_preservation": (
        "小さな変化",
        "少し出来",
        "少しでき",
        "少し勇気",
        "少し気持ちを言葉",
        "言葉に出来",
        "言葉にでき",
        "少し前に進",
        "ほんの少し前",
    ),
    "value_preservation": (
        "大事",
        "大切",
    ),
    "self_observation": (
        "なぜ",
        "なんで",
        "どうして",
        "自分について",
        "思ったんだろう",
        "基準",
    ),
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


def _joined_text(bundle: EmlisCurrentInputBundle) -> str:
    return "\n".join(part for part in (_clean(bundle.thought_text), _clean(bundle.action_text)) if part)


def _sentence_count(text: str) -> int:
    parts = [_clean(part) for part in _SENTENCE_SPLIT_RE.split(text) if _clean(part)]
    return len(parts) or (1 if _clean(text) else 0)


def _has_non_vague_event_text(text: str) -> bool:
    value = _clean(text)
    if not value:
        return False
    if _VAGUE_ONLY_RE.fullmatch(value):
        return False
    return bool(_EVENT_RE.search(value) or len(value) >= 18)


def _category_labels(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return _dedupe(bundle.categories)


def _emotion_labels(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return _dedupe(emotion.type for emotion in bundle.emotions)


def _emotion_intensities(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return _dedupe(emotion.strength for emotion in bundle.emotions if _clean(emotion.strength))


def _source_field_ids(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    fields: list[str] = []
    if _clean(bundle.thought_text):
        fields.append("memo")
    if _clean(bundle.action_text):
        fields.append("memo_action")
    if bundle.emotions:
        fields.append("emotion_details")
    if bundle.categories:
        fields.append("category")
    return _dedupe(fields)


def _generic_relation_material_ids(text: str, categories: Sequence[str]) -> tuple[str, ...]:
    text_value = _clean(text)
    category_value = " ".join(_clean(category) for category in categories)
    haystack = "\n".join([text_value, category_value])
    ids: list[str] = []
    for material_id, patterns in _GENERIC_RELATION_MATERIAL_PATTERNS.items():
        if any(pattern in haystack for pattern in patterns):
            ids.append(material_id)
    # P7 semantic material ids must be grounded in the user's written text.
    # Category labels alone can show topic direction, but they must not create
    # recovery/wish/comparison semantics by themselves.
    if text_value:
        for material_id, patterns in _SEMANTIC_MATERIAL_PATTERNS.items():
            if any(pattern in text_value for pattern in patterns):
                ids.append(material_id)
    if any(category in {"人間関係", "恋愛", "家族"} for category in categories):
        ids.append("relationship_category_direction")
    # Phase20-3 uses generic material ids rather than Phase19 case cue ids.
    # These compatibility aliases are intentionally broad relation materials,
    # not reception modes and not completed surface selections.
    if any(item in ids for item in ("relationship_end", "relationship_category_direction")):
        ids.append("relationship_material")
    if "support_from_other" in ids:
        ids.append("support_received_material")
    if "self_understanding_learning" in ids:
        ids.append("value_or_self_understanding_material")
    return _dedupe(ids)

def _visible_material_slots(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    text = _joined_text(bundle)
    categories = _category_labels(bundle)
    slots: list[str] = []
    if _clean(bundle.action_text) and _has_non_vague_event_text(bundle.action_text):
        slots.append(VISIBLE_MATERIAL_SLOT_EVENT)
        slots.append(VISIBLE_MATERIAL_SLOT_ACTION)
    elif _EVENT_RE.search(text):
        slots.append(VISIBLE_MATERIAL_SLOT_EVENT)
    if bundle.emotions or _EMOTION_WORD_RE.search(text):
        slots.append(VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION)
    if _RELATIONSHIP_RE.search(text) or any(category in {"人間関係", "恋愛", "家族"} for category in categories):
        slots.append(VISIBLE_MATERIAL_SLOT_RELATIONSHIP)
        slots.append(VISIBLE_MATERIAL_SLOT_TARGET)
    elif _TARGET_RE.search(text) or categories:
        slots.append(VISIBLE_MATERIAL_SLOT_TARGET)
    if _ACTION_RE.search(text) or _clean(bundle.action_text):
        slots.append(VISIBLE_MATERIAL_SLOT_ACTION)
    if _CHANGE_RE.search(text):
        slots.append(VISIBLE_MATERIAL_SLOT_CHANGE)
    if _TIME_RE.search(text):
        slots.append(VISIBLE_MATERIAL_SLOT_TIME)
    if _VALUE_RE.search(text):
        slots.append(VISIBLE_MATERIAL_SLOT_VALUE)
    if _VAGUE_LOAD_RE.search(text):
        slots.append(VISIBLE_MATERIAL_SLOT_UNRESOLVED_WEIGHT)
    return _dedupe(slots)


def _unknown_slots(visible_slots: Sequence[str], *, has_text: bool) -> tuple[str, ...]:
    visible = set(visible_slots)
    unknown: list[str] = []
    if VISIBLE_MATERIAL_SLOT_EVENT not in visible:
        unknown.append(UNKNOWN_SLOT_EVENT)
    if VISIBLE_MATERIAL_SLOT_TARGET not in visible:
        unknown.append(UNKNOWN_SLOT_TARGET)
    if VISIBLE_MATERIAL_SLOT_RELATIONSHIP not in visible:
        unknown.append(UNKNOWN_SLOT_RELATIONSHIP)
    if VISIBLE_MATERIAL_SLOT_TIME not in visible:
        unknown.append(UNKNOWN_SLOT_DURATION)
    if VISIBLE_MATERIAL_SLOT_ACTION not in visible:
        unknown.append(UNKNOWN_SLOT_NEXT_ACTION)
    if has_text and VISIBLE_MATERIAL_SLOT_CHANGE not in visible:
        unknown.append(UNKNOWN_SLOT_IMPACT)
    unknown.append(UNKNOWN_SLOT_CAUSE)
    if VISIBLE_MATERIAL_SLOT_ACTION not in visible and VISIBLE_MATERIAL_SLOT_VALUE not in visible:
        unknown.append(UNKNOWN_SLOT_USER_INTENT)
    return _dedupe(unknown)


def _triage_kind(decision: EmlisSafetyTriageDecision | Mapping[str, Any] | None) -> str:
    if decision is None:
        return TRIAGE_SAFE_OBSERVATION
    if isinstance(decision, EmlisSafetyTriageDecision):
        return _clean(decision.safety_triage_kind) or TRIAGE_SAFE_OBSERVATION
    if isinstance(decision, Mapping):
        return _clean(decision.get("safety_triage_kind")) or TRIAGE_SAFE_OBSERVATION
    return TRIAGE_SAFE_OBSERVATION


def _material_quality(
    *,
    bundle: EmlisCurrentInputBundle,
    visible_slots: Sequence[str],
    unknown_slots: Sequence[str],
    safety_triage_kind: str,
) -> str:
    if safety_triage_kind and safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
        return MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED

    text = _joined_text(bundle)
    has_text = bool(_clean(text))
    visible = set(visible_slots)
    sentence_count = _sentence_count(text)
    text_len = len(_clean(text))
    has_event = VISIBLE_MATERIAL_SLOT_EVENT in visible
    has_target = VISIBLE_MATERIAL_SLOT_TARGET in visible
    has_relation = VISIBLE_MATERIAL_SLOT_RELATIONSHIP in visible
    has_emotion_direction = VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION in visible
    has_unresolved_weight = VISIBLE_MATERIAL_SLOT_UNRESOLVED_WEIGHT in visible
    has_time = VISIBLE_MATERIAL_SLOT_TIME in visible
    has_action = VISIBLE_MATERIAL_SLOT_ACTION in visible
    has_value_or_change = bool({VISIBLE_MATERIAL_SLOT_VALUE, VISIBLE_MATERIAL_SLOT_CHANGE}.intersection(visible))

    if not has_text and not bundle.emotions and not bundle.categories:
        return MATERIAL_QUALITY_LOW_INFORMATION

    # A-like inputs are not detected by A's wording.  They are detected because
    # the input bundle exposes emotion/category/unresolved weight but not event,
    # target, relation, or action material.  This keeps "low information" away
    # from pure length checks.
    if (
        has_unresolved_weight
        and not has_event
        and not has_relation
        and not has_action
        and sentence_count <= 2
    ):
        return MATERIAL_QUALITY_LOW_INFORMATION

    if (
        has_emotion_direction
        and has_unresolved_weight
        and not has_event
        and not has_relation
        and not has_time
        and not has_action
        and not has_value_or_change
        and sentence_count <= 2
    ):
        return MATERIAL_QUALITY_LOW_INFORMATION

    if (
        has_emotion_direction
        and not has_event
        and not has_target
        and not has_relation
        and not has_time
        and not has_action
        and not has_value_or_change
    ):
        return MATERIAL_QUALITY_LOW_INFORMATION

    if len(visible) <= 1 and len(unknown_slots) >= 5:
        return MATERIAL_QUALITY_LOW_INFORMATION

    if (has_time or has_value_or_change or has_action or has_target or has_relation) and has_emotion_direction:
        if not has_event or not has_target:
            return MATERIAL_QUALITY_LIMITED_GROUNDING
        return MATERIAL_QUALITY_ELIGIBLE

    if text_len >= 70 and len(unknown_slots) >= 4:
        return MATERIAL_QUALITY_LIMITED_GROUNDING

    if has_event and (has_emotion_direction or has_relation or has_target):
        return MATERIAL_QUALITY_ELIGIBLE

    if visible:
        return MATERIAL_QUALITY_LIMITED_GROUNDING
    return MATERIAL_QUALITY_LOW_INFORMATION


@dataclass(frozen=True)
class EmlisInputMaterialBundle:
    """Internal Phase20-3 material bundle.

    ``thought_text`` and ``action_text`` are kept inside the dataclass to match
    the design schema and to support internal routing.  ``as_meta`` deliberately
    emits only structural ids/counts and never raw text.
    """

    thought_text: str = ""
    action_text: str = ""
    emotion_labels: tuple[str, ...] = field(default_factory=tuple)
    emotion_intensities: tuple[str, ...] = field(default_factory=tuple)
    category_labels: tuple[str, ...] = field(default_factory=tuple)
    visible_material_slots: tuple[str, ...] = field(default_factory=tuple)
    unknown_slots: tuple[str, ...] = field(default_factory=tuple)
    material_quality: str = MATERIAL_QUALITY_LOW_INFORMATION
    safety_triage_kind: str = TRIAGE_SAFE_OBSERVATION
    source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    generic_relation_material_ids: tuple[str, ...] = field(default_factory=tuple)
    source_record_id_present: bool = False
    selected_at_present: bool = False
    schema_version: str = EMLIS_INPUT_MATERIAL_BUNDLE_SCHEMA_VERSION
    source_phase: str = EMLIS_INPUT_MATERIAL_BUNDLE_SOURCE_PHASE

    def to_schema_payload(self) -> dict[str, Any]:
        """Return the design-shaped internal payload, including internal text."""

        return {
            "schema_version": self.schema_version,
            "source_phase": self.source_phase,
            "thought_text": self.thought_text,
            "action_text": self.action_text,
            "emotion_labels": list(self.emotion_labels),
            "emotion_intensities": list(self.emotion_intensities),
            "category_labels": list(self.category_labels),
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "material_quality": self.material_quality,
            "safety_triage_kind": self.safety_triage_kind,
            "source_field_ids": list(self.source_field_ids),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
        }

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "source_phase": self.source_phase,
            "input_material_bundle_ready": True,
            "thought_text_present": bool(self.thought_text),
            "action_text_present": bool(self.action_text),
            "emotion_count": len(self.emotion_labels),
            "emotion_intensity_count": len(self.emotion_intensities),
            "category_count": len(self.category_labels),
            "source_record_id_present": bool(self.source_record_id_present),
            "selected_at_present": bool(self.selected_at_present),
            "source_field_ids": list(self.source_field_ids),
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "material_quality": self.material_quality,
            "safety_triage_kind": self.safety_triage_kind,
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "generic_relation_material_count": len(self.generic_relation_material_ids),
            "relation_material_ids": list(self.generic_relation_material_ids),
            "low_information_is_bundle_material_shortage": self.material_quality == MATERIAL_QUALITY_LOW_INFORMATION,
            "short_text_alone_decides_low_information": False,
            "low_information_is_length_only": False,
            "phase20_3_a_compact_signal_replaced_by_material_quality": True,
            "phase20_3_phase19_cd_specific_cues_runtime_disabled": True,
            "phase19_cd_specific_cue_runtime_used": False,
            "phase19_runtime_cue_used": False,
            "c_d_specific_runtime_cue_used": False,
            "a_low_information_case_route_used": False,
            "case_specific_route_used": False,
            "phase19_case_route_used": False,
            "phase19_case_specific_route_used": False,
            "case_id_runtime_condition_used": False,
            "phase_name_runtime_condition_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "fixed_fallback_used": False,
            "public_response_key_added": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_emlis_input_material_bundle_meta_contract(meta)
        return meta


def build_emlis_input_material_bundle(
    current_input: Any,
    *,
    safety_triage_decision: EmlisSafetyTriageDecision | Mapping[str, Any] | None = None,
) -> EmlisInputMaterialBundle:
    bundle = build_emlis_current_input_bundle(current_input)
    if safety_triage_decision is None:
        safety_triage_decision = build_emlis_safety_triage_decision(current_input=bundle.to_current_input_payload())
    safety_kind = _triage_kind(safety_triage_decision)
    visible_slots = _visible_material_slots(bundle)
    unknown = _unknown_slots(visible_slots, has_text=bool(_joined_text(bundle)))
    categories = _category_labels(bundle)
    generic_relation_ids = _generic_relation_material_ids(_joined_text(bundle), categories)
    quality = _material_quality(
        bundle=bundle,
        visible_slots=visible_slots,
        unknown_slots=unknown,
        safety_triage_kind=safety_kind,
    )
    return EmlisInputMaterialBundle(
        thought_text=_clean(bundle.thought_text),
        action_text=_clean(bundle.action_text),
        emotion_labels=_emotion_labels(bundle),
        emotion_intensities=_emotion_intensities(bundle),
        category_labels=categories,
        visible_material_slots=visible_slots,
        unknown_slots=unknown,
        material_quality=quality,
        safety_triage_kind=safety_kind,
        source_field_ids=_source_field_ids(bundle),
        generic_relation_material_ids=generic_relation_ids,
        source_record_id_present=bool(_clean(bundle.source_record_id)),
        selected_at_present=bool(_clean(bundle.selected_at)),
    )


def build_emlis_input_material_bundle_meta(
    current_input: Any,
    *,
    safety_triage_decision: EmlisSafetyTriageDecision | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return build_emlis_input_material_bundle(
        current_input,
        safety_triage_decision=safety_triage_decision,
    ).as_meta()


def assert_emlis_input_material_bundle_meta_contract(meta: Mapping[str, Any]) -> None:
    if meta.get("schema_version") != EMLIS_INPUT_MATERIAL_BUNDLE_SCHEMA_VERSION:
        raise ValueError("unexpected input material bundle schema version")
    if meta.get("source_phase") != EMLIS_INPUT_MATERIAL_BUNDLE_SOURCE_PHASE:
        raise ValueError("unexpected input material bundle source phase")
    if meta.get("input_material_bundle_ready") is not True:
        raise ValueError("input material bundle meta must be ready")
    if meta.get("material_quality") not in _ALLOWED_MATERIAL_QUALITIES:
        raise ValueError("unsupported material_quality")
    for slot in meta.get("visible_material_slots") or []:
        if slot not in _ALLOWED_VISIBLE_MATERIAL_SLOTS:
            raise ValueError(f"unsupported visible material slot: {slot}")
    for slot in meta.get("unknown_slots") or []:
        if slot not in _ALLOWED_UNKNOWN_SLOTS:
            raise ValueError(f"unsupported unknown slot: {slot}")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"forbidden true flag in input material bundle meta: {flag}")
    for key in _TEXT_PAYLOAD_KEYS:
        if key in meta:
            raise ValueError(f"raw text payload key is not allowed in input material bundle meta: {key}")
    if _contains_text_payload_key(meta):
        raise ValueError("input material bundle meta must not contain raw text payload keys")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


# Compatibility alias for callers/tests that use the shorter assertion name.
def assert_emlis_input_material_bundle_meta(meta: Mapping[str, Any]) -> None:
    assert_emlis_input_material_bundle_meta_contract(meta)

# Backward-compatible Phase20-3 names used by existing service/test files.
VISIBLE_SLOT_EVENT = VISIBLE_MATERIAL_SLOT_EVENT
VISIBLE_SLOT_TARGET = VISIBLE_MATERIAL_SLOT_TARGET
VISIBLE_SLOT_EMOTION_DIRECTION = VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION
VISIBLE_SLOT_RELATIONSHIP = VISIBLE_MATERIAL_SLOT_RELATIONSHIP
VISIBLE_SLOT_ACTION = VISIBLE_MATERIAL_SLOT_ACTION
VISIBLE_SLOT_CHANGE = VISIBLE_MATERIAL_SLOT_CHANGE
VISIBLE_SLOT_TIME = VISIBLE_MATERIAL_SLOT_TIME
VISIBLE_SLOT_VALUE = VISIBLE_MATERIAL_SLOT_VALUE
VISIBLE_SLOT_UNRESOLVED_WEIGHT = VISIBLE_MATERIAL_SLOT_UNRESOLVED_WEIGHT

__all__ = [
    "EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY",
    "EMLIS_INPUT_MATERIAL_BUNDLE_SCHEMA_VERSION",
    "EMLIS_INPUT_MATERIAL_BUNDLE_SOURCE_PHASE",
    "MATERIAL_QUALITY_ELIGIBLE",
    "MATERIAL_QUALITY_LIMITED_GROUNDING",
    "MATERIAL_QUALITY_LOW_INFORMATION",
    "MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED",
    "EmlisInputMaterialBundle",
    "VISIBLE_SLOT_EVENT",
    "VISIBLE_SLOT_TARGET",
    "VISIBLE_SLOT_EMOTION_DIRECTION",
    "VISIBLE_SLOT_RELATIONSHIP",
    "VISIBLE_SLOT_ACTION",
    "VISIBLE_SLOT_CHANGE",
    "VISIBLE_SLOT_TIME",
    "VISIBLE_SLOT_VALUE",
    "VISIBLE_SLOT_UNRESOLVED_WEIGHT",
    "assert_emlis_input_material_bundle_meta",
    "assert_emlis_input_material_bundle_meta_contract",
    "build_emlis_input_material_bundle",
    "build_emlis_input_material_bundle_meta",
]
