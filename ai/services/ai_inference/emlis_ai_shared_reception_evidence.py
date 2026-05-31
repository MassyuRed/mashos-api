# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared Evidence Builder for EmlisAI two-stage reception.

Phase 2 creates a text-free internal evidence material that can be shared by
later observation/reception builders.  It reads the existing current-input
bundle, but the exported meta intentionally contains only booleans, ids,
counts, and source-field names.  It does not generate ``comment_text``, add
public response keys, use a general dictionary, or assert unknown-word meaning.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import EmlisCurrentInputBundle, build_emlis_current_input_bundle

EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION: Final = "cocolon.emlis_shared_reception_evidence.v1"
EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE: Final = "Phase2_shared_reception_evidence"
EMLIS_SHARED_RECEPTION_EVIDENCE_MATERIAL_ID: Final = "emlis_shared_reception_evidence"

_EVENT_FACT_MIN_CHARS: Final = 4
_SPACE_RE: Final = re.compile(r"\s+")
_ONLY_VAGUE_EVENT_RE: Final = re.compile(r"^(あれ|それ|これ|あの|その|なんか|なんとなく|いろいろ|色々|特になし|なし|ない)$")

_REACTION_CUE_PATTERNS: Final = {
    "disgust": (
        "気持ち悪い",
        "気持ちわるい",
        "きもちわるい",
        "きもい",
        "キモい",
        "嫌",
        "いや",
        "最悪",
    ),
    "anger_irritation": (
        "イライラ",
        "いらいら",
        "怒り",
        "怒っ",
        "腹が立",
        "ムカつ",
        "むかつ",
    ),
    "fear": (
        "怖い",
        "こわい",
        "恐怖",
        "怖さ",
    ),
    "joy_or_surprise": (
        "嬉しい",
        "うれしい",
        "びっくり",
        "驚",
        "動揺",
        "ほっと",
        "楽しい",
    ),
    "fatigue_or_load": (
        "疲れ",
        "くたくた",
        "しんど",
        "元気がない",
        "我慢",
        "余裕ない",
    ),
    "uncertainty": (
        "これでいいのかな",
        "大丈夫なのかな",
        "頑張れてるかな",
        "不安",
        "自信がなく",
        "自信ない",
    ),
    "self_denial": (
        "中途半端",
        "自分を好き",
        "好きになれる",
        "自信をつけたい",
        "なんで私はこう",
        "自分を責め",
        "自分を追い込",
    ),
    "self_understanding_effort": (
        "向き合",
        "気づいて",
        "優しく見",
        "ちゃんと見て",
        "見てあげる",
        "整えて",
        "直したい",
        "挑戦",
        "頑張りたい",
        "小さくても大事",
    ),
    "self_understanding_learning_shift": (
        "疑問の対象",
        "人について考えすぎ",
        "人への興味",
        "人との話し方",
        "すぐに行動",
        "勇気",
        "日常",
        "傷",
        "汚れ",
        "メモ",
        "進歩",
        "大丈夫",
    ),
    "relationship_gratitude_recovery": (
        "彼氏と別れ",
        "別れた",
        "関係の終わり",
        "友達",
        "変わらず",
        "優しく",
        "優しさ",
        "私のために怒って",
        "怒ってくれて",
        "感謝",
        "区切り",
        "返していきたい",
        "別の形で",
    ),
    "effort_pace": (
        "自立",
        "動けるようになりたい",
        "体調をちゃんと見",
        "続けていけるペース",
        "長く続け",
        "無理をして頑張りすぎるんじゃなくて",
    ),
}

_EMOTION_LABEL_IDS: Final = {
    "怒り": "anger",
    "悲しみ": "sadness",
    "喜び": "joy",
    "平穏": "calm",
    "自己理解": "self_understanding",
    "恐怖": "fear",
    "不安": "anxiety",
    "嫌悪": "disgust",
    "安心": "relief",
}

_CATEGORY_TOPIC_IDS: Final = {
    "生活": "life",
    "人間関係": "relationship",
    "恋愛": "relationship_love",
    "価値観": "values",
    "仕事": "work",
    "学校": "school",
    "学習": "learning",
    "家族": "family",
    "体調": "health",
    "お金": "money",
}


_LEARNING_SHIFT_FEATURE_PATTERNS: Final = {
    "object_focus_shift": (
        "疑問の対象",
        "対象が物",
        "物を見る",
        "人について考えすぎ",
        "人への興味",
    ),
    "communication_load_reduced": (
        "コミュニケーション",
        "もやもや",
        "人との話し方",
        "話し方を思い出",
    ),
    "learning_observation_action": (
        "授業",
        "日常",
        "傷",
        "汚れ",
        "メモ",
    ),
    "immediate_action_courage": (
        "すぐに行動",
        "勇気",
    ),
    "small_progress_self_reassurance": (
        "少しずつ",
        "進歩",
        "大丈夫",
    ),
}

_RELATIONSHIP_GRATITUDE_FEATURE_PATTERNS: Final = {
    "relationship_end": (
        "別れた",
        "関係の終わり",
        "区切り",
    ),
    "friend_support_remains": (
        "友達",
        "変わらず",
        "優しく",
        "優しさ",
    ),
    "friend_anger_for_user": (
        "私のために怒って",
        "怒ってくれて",
    ),
    "gratitude_for_care": (
        "感謝",
        "嬉しい",
        "実感",
    ),
    "sadness_and_kindness_coexist": (
        "悲しい",
        "優しさ",
        "見逃してしまいそう",
    ),
    "boundary_growth": (
        "区切り",
        "成長",
    ),
    "return_kindness_intent": (
        "返していきたい",
        "別の形で",
    ),
}

_EVENT_HINT_PATTERNS: Final = {
    "public_unpleasant_encounter": (
        "立ちション",
        "すれ違",
        "出くわ",
        "見かけ",
        "遭遇",
    ),
    "positive_change_after_work_streaming": (
        "配信",
        "誰かとお話",
        "話したい",
        "仕事があった日",
        "大きな変化",
    ),
    "self_confidence_uncertainty_attempt": (
        "自信をつけたい",
        "中途半端",
        "色々挑戦",
        "これでいいのかな",
        "大丈夫なのかな",
    ),
    "self_blame_to_gentle_self_observation": (
        "自分を責め",
        "気持ちが沈",
        "向き合わないと",
        "優しく見て",
        "気持ちをちゃんと見て",
    ),
    "independence_life_health_money_pace": (
        "自立",
        "生活のこと",
        "体調のこと",
        "お金のこと",
        "長く続けていけるペース",
    ),
    "relationship_end_gratitude_recovery_context": (
        "別れた",
        "関係の終わり",
        "私のために怒って",
        "怒ってくれて",
        "返していきたい",
        "友達",
        "優しさ",
    ),
}

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
        "category_used_as_cause",
        "emotion_strength_used_as_cause",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _haystack(*parts: Any) -> str:
    return "\n".join(_clean(part) for part in parts if _clean(part))


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _has_action_event_fact(action_text: str) -> bool:
    text = _clean(action_text)
    if len(text) < _EVENT_FACT_MIN_CHARS:
        return False
    if _ONLY_VAGUE_EVENT_RE.fullmatch(text):
        return False
    return True


def _extract_reaction_cue_ids(text: str) -> tuple[str, ...]:
    return _dedupe(
        cue_id for cue_id, patterns in _REACTION_CUE_PATTERNS.items() if _contains_any(text, patterns)
    )


def _normalize_emotion_label_ids(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    ids: list[str] = []
    for emotion in bundle.emotions:
        label_id = _EMOTION_LABEL_IDS.get(_clean(emotion.type))
        if label_id:
            ids.append(label_id)
    return _dedupe(ids)


def _emotion_label_source_fields(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return _dedupe(emotion.source_field or "emotion_details" for emotion in bundle.emotions)


def _extract_category_topic_ids(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return _dedupe(_CATEGORY_TOPIC_IDS.get(_clean(category), "") for category in bundle.categories)


def _extract_event_hint_ids(text: str) -> tuple[str, ...]:
    return _dedupe(
        hint_id for hint_id, patterns in _EVENT_HINT_PATTERNS.items() if _contains_any(text, patterns)
    )


def _extract_learning_shift_feature_ids(text: str) -> tuple[str, ...]:
    return _dedupe(
        feature_id
        for feature_id, patterns in _LEARNING_SHIFT_FEATURE_PATTERNS.items()
        if _contains_any(text, patterns)
    )


def _extract_relationship_gratitude_feature_ids(text: str) -> tuple[str, ...]:
    return _dedupe(
        feature_id
        for feature_id, patterns in _RELATIONSHIP_GRATITUDE_FEATURE_PATTERNS.items()
        if _contains_any(text, patterns)
    )


def _source_fields_for_reaction(
    *,
    thought_text: str,
    reaction_cue_ids: Sequence[str],
    emotion_source_fields: Sequence[str],
) -> tuple[str, ...]:
    fields: list[str] = []
    if thought_text and reaction_cue_ids:
        fields.append("memo")
    fields.extend(emotion_source_fields)
    return _dedupe(fields)


def _candidate_modes(
    *,
    event_fact_present: bool,
    reaction_present: bool,
    reaction_cue_ids: Sequence[str],
    event_hint_ids: Sequence[str],
    category_topic_ids: Sequence[str],
    emotion_label_ids: Sequence[str],
    learning_shift_feature_ids: Sequence[str],
    relationship_gratitude_feature_ids: Sequence[str],
) -> tuple[str, ...]:
    cues = set(reaction_cue_ids)
    hints = set(event_hint_ids)
    categories = set(category_topic_ids)
    emotion_labels = set(emotion_label_ids)
    learning_shift_features = set(learning_shift_feature_ids)
    relationship_gratitude_features = set(relationship_gratitude_feature_ids)
    modes: list[str] = []

    relationship_categories = {"relationship", "relationship_love"}
    relationship_support_features = {
        "friend_support_remains",
        "friend_anger_for_user",
        "gratitude_for_care",
        "sadness_and_kindness_coexist",
        "boundary_growth",
        "return_kindness_intent",
    }
    if (
        event_fact_present
        and reaction_present
        and categories.intersection(relationship_categories)
        and "relationship_end" in relationship_gratitude_features
        and relationship_gratitude_features.intersection(relationship_support_features)
    ):
        modes.append("relationship_gratitude_recovery")
        modes.append("self_understanding_follow")

    if (
        len(learning_shift_features) >= 2
        and reaction_present
        and ("self_understanding" in emotion_labels or "learning" in categories or event_fact_present)
    ):
        modes.append("self_understanding_learning_shift")
        modes.append("self_understanding_follow")

    negative_daily_cues = {"disgust", "fear", "anger_irritation"}
    if event_fact_present and reaction_present and cues.intersection(negative_daily_cues):
        modes.append("daily_unpleasant_reception")

    if "joy_or_surprise" in cues or "positive_change_after_work_streaming" in hints:
        modes.append("daily_positive_reception")
        modes.append("self_understanding_follow")

    if "self_denial" in cues:
        modes.append("self_denial_support")
    if "uncertainty" in cues:
        modes.append("uncertainty_support")
    if "self_understanding_learning_shift" in cues and reaction_present:
        modes.append("self_understanding_learning_shift")
        modes.append("self_understanding_follow")
    if "self_understanding_effort" in cues or "self_blame_to_gentle_self_observation" in hints:
        modes.append("self_understanding_follow")
    if "effort_pace" in cues or "independence_life_health_money_pace" in hints:
        modes.append("standard_state_answer")
        modes.append("effort_support")

    if not modes and reaction_present:
        modes.append("standard_state_answer")
    if not modes:
        modes.append("low_information_question")

    # Category can support topic direction only; it should not create emotion or
    # a reception mode by itself.  Keep this branch limited to a non-causal
    # standard candidate when some reaction is already present.
    if reaction_present and not modes and category_topic_ids:
        modes.append("standard_state_answer")

    return _dedupe(modes)


def _mode_reason(
    modes: Sequence[str], *, event_fact_present: bool, reaction_present: bool) -> str:
    if "relationship_gratitude_recovery" in modes and event_fact_present and reaction_present:
        return "relationship_end_gratitude_recovery"
    if "daily_unpleasant_reception" in modes and event_fact_present and reaction_present:
        return "event_fact_with_explicit_negative_reaction"
    if "self_denial_support" in modes and "uncertainty_support" in modes:
        return "self_denial_and_uncertainty_cues_present"
    if "daily_positive_reception" in modes:
        return "positive_change_or_surprise_cues_present"
    if "self_understanding_learning_shift" in modes:
        return "self_understanding_learning_shift_present"
    if "self_understanding_follow" in modes:
        return "self_understanding_direction_present"
    if "effort_support" in modes:
        return "effort_pace_context_present"
    if reaction_present:
        return "explicit_reaction_present"
    return "insufficient_shared_reception_evidence"


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


@dataclass(frozen=True)
class EmlisSharedReceptionEvidence:
    """Text-free shared evidence for later two-stage reception phases."""

    event_fact_present: bool = False
    event_fact_source_fields: tuple[str, ...] = field(default_factory=tuple)
    reaction_present: bool = False
    reaction_source_fields: tuple[str, ...] = field(default_factory=tuple)
    explicit_reaction_cue_ids: tuple[str, ...] = field(default_factory=tuple)
    explicit_emotion_label_ids: tuple[str, ...] = field(default_factory=tuple)
    category_topic_ids: tuple[str, ...] = field(default_factory=tuple)
    event_hint_ids: tuple[str, ...] = field(default_factory=tuple)
    learning_shift_feature_ids: tuple[str, ...] = field(default_factory=tuple)
    relationship_gratitude_feature_ids: tuple[str, ...] = field(default_factory=tuple)
    reception_candidate_mode_ids: tuple[str, ...] = field(default_factory=tuple)
    primary_reason: str = "insufficient_shared_reception_evidence"
    event_fact_count: int = 0
    reaction_cue_count: int = 0
    emotion_label_count: int = 0
    event_hint_count: int = 0
    learning_shift_feature_count: int = 0
    relationship_gratitude_feature_count: int = 0
    schema_version: str = EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION
    source_phase: str = EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE
    material_id: str = EMLIS_SHARED_RECEPTION_EVIDENCE_MATERIAL_ID

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "source_phase": self.source_phase,
            "material_id": self.material_id,
            "shared_reception_evidence_ready": True,
            "event_fact_present": bool(self.event_fact_present),
            "event_fact_source_fields": list(self.event_fact_source_fields),
            "event_fact_count": int(self.event_fact_count),
            "reaction_present": bool(self.reaction_present),
            "reaction_source_fields": list(self.reaction_source_fields),
            "reaction_cue_count": int(self.reaction_cue_count),
            "emotion_label_count": int(self.emotion_label_count),
            "explicit_reaction_cue_ids": list(self.explicit_reaction_cue_ids),
            "explicit_emotion_label_ids": list(self.explicit_emotion_label_ids),
            "category_topic_ids": list(self.category_topic_ids),
            "event_hint_ids": list(self.event_hint_ids),
            "event_hint_count": int(self.event_hint_count),
            "learning_shift_feature_family": "self_understanding_learning_shift" if self.learning_shift_feature_ids else "",
            "learning_shift_feature_ids": list(self.learning_shift_feature_ids),
            "learning_shift_feature_count": int(self.learning_shift_feature_count),
            "self_understanding_learning_shift_detected": bool(self.learning_shift_feature_ids),
            "relationship_gratitude_feature_family": "relationship_gratitude_recovery" if self.relationship_gratitude_feature_ids else "",
            "relationship_gratitude_feature_ids": list(self.relationship_gratitude_feature_ids),
            "relationship_gratitude_feature_count": int(self.relationship_gratitude_feature_count),
            "relationship_gratitude_recovery_detected": bool(self.relationship_gratitude_feature_ids),
            "reception_candidate_mode_ids": list(self.reception_candidate_mode_ids),
            "primary_reason": self.primary_reason,
            "unknown_word_policy": {
                "unknown_word_meaning_asserted": False,
                "meaning_assertion_allowed": False,
                "event_hint_can_support_mode_only": True,
                "event_hint_must_not_create_emotion": True,
            },
            "general_dictionary_used": False,
            "unknown_word_meaning_asserted": False,
            "event_hint_created_emotion": False,
            "category_used_as_cause": False,
            "emotion_strength_used_as_cause": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "public_response_key_added": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_emlis_shared_reception_evidence_contract(meta)
        return meta


def build_emlis_shared_reception_evidence(current_input: Any) -> EmlisSharedReceptionEvidence:
    """Build Phase 2 shared evidence from the current input bundle.

    The builder uses only the existing current-input fields.  It returns ids and
    structural flags, not raw user text or completed reply material.
    """

    bundle = build_emlis_current_input_bundle(current_input)
    thought_text = _clean(bundle.thought_text)
    action_text = _clean(bundle.action_text)
    text = _haystack(thought_text, action_text)

    event_fact_present = _has_action_event_fact(action_text)
    event_fact_source_fields = ("memo_action",) if event_fact_present else ()
    event_fact_count = 1 if event_fact_present else 0

    reaction_cue_ids = _extract_reaction_cue_ids(thought_text)
    emotion_label_ids = _normalize_emotion_label_ids(bundle)
    emotion_source_fields = _emotion_label_source_fields(bundle)
    reaction_present = bool(reaction_cue_ids or emotion_label_ids)
    reaction_source_fields = _source_fields_for_reaction(
        thought_text=thought_text,
        reaction_cue_ids=reaction_cue_ids,
        emotion_source_fields=emotion_source_fields,
    ) if reaction_present else ()

    category_topic_ids = _extract_category_topic_ids(bundle)
    event_hint_ids = _extract_event_hint_ids(text)
    learning_shift_feature_ids = _extract_learning_shift_feature_ids(text)
    relationship_gratitude_feature_ids = _extract_relationship_gratitude_feature_ids(text)
    mode_ids = _candidate_modes(
        event_fact_present=event_fact_present,
        reaction_present=reaction_present,
        reaction_cue_ids=reaction_cue_ids,
        event_hint_ids=event_hint_ids,
        category_topic_ids=category_topic_ids,
        emotion_label_ids=emotion_label_ids,
        learning_shift_feature_ids=learning_shift_feature_ids,
        relationship_gratitude_feature_ids=relationship_gratitude_feature_ids,
    )

    return EmlisSharedReceptionEvidence(
        event_fact_present=event_fact_present,
        event_fact_source_fields=event_fact_source_fields,
        reaction_present=reaction_present,
        reaction_source_fields=reaction_source_fields,
        explicit_reaction_cue_ids=reaction_cue_ids,
        explicit_emotion_label_ids=emotion_label_ids,
        category_topic_ids=category_topic_ids,
        event_hint_ids=event_hint_ids,
        learning_shift_feature_ids=learning_shift_feature_ids,
        relationship_gratitude_feature_ids=relationship_gratitude_feature_ids,
        reception_candidate_mode_ids=mode_ids,
        primary_reason=_mode_reason(mode_ids, event_fact_present=event_fact_present, reaction_present=reaction_present),
        event_fact_count=event_fact_count,
        reaction_cue_count=len(reaction_cue_ids),
        emotion_label_count=len(emotion_label_ids),
        event_hint_count=len(event_hint_ids),
        learning_shift_feature_count=len(learning_shift_feature_ids),
        relationship_gratitude_feature_count=len(relationship_gratitude_feature_ids),
    )


def build_emlis_shared_reception_evidence_meta(current_input: Any) -> dict[str, Any]:
    """Return text-free meta for the Phase 2 shared evidence material."""

    return build_emlis_shared_reception_evidence(current_input).as_meta()


def assert_emlis_shared_reception_evidence_contract(meta: Mapping[str, Any]) -> None:
    """Validate that Phase 2 evidence meta stays structural and public-safe."""

    if meta.get("schema_version") != EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("unexpected shared reception evidence schema version")
    if meta.get("source_phase") != EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE:
        raise ValueError("unexpected shared reception evidence phase")
    if meta.get("material_id") != EMLIS_SHARED_RECEPTION_EVIDENCE_MATERIAL_ID:
        raise ValueError("unexpected shared reception evidence material id")

    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"forbidden true flag in shared reception evidence: {flag}")

    # These raw-text keys are forbidden as payload fields.  Source-field values
    # such as "memo" or "memo_action" are allowed inside *_source_fields.
    for key in _TEXT_PAYLOAD_KEYS:
        if key in meta:
            raise ValueError(f"raw text payload key is not allowed in shared reception evidence: {key}")

    if _contains_text_payload_key(meta):
        raise ValueError("shared reception evidence must not contain raw text payload keys")

    if meta.get("general_dictionary_used") is not False:
        raise ValueError("shared reception evidence must not use a general dictionary")
    if meta.get("unknown_word_meaning_asserted") is not False:
        raise ValueError("shared reception evidence must not assert unknown-word meaning")

    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


__all__ = [
    "EMLIS_SHARED_RECEPTION_EVIDENCE_MATERIAL_ID",
    "EMLIS_SHARED_RECEPTION_EVIDENCE_SCHEMA_VERSION",
    "EMLIS_SHARED_RECEPTION_EVIDENCE_SOURCE_PHASE",
    "EmlisSharedReceptionEvidence",
    "assert_emlis_shared_reception_evidence_contract",
    "build_emlis_shared_reception_evidence",
    "build_emlis_shared_reception_evidence_meta",
]
