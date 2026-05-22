# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal current-input bundle normalization for EmlisAI.

This module owns the Phase 1 boundary between the public /emotion/submit
payload and EmlisAI's internal reading model.  It does not change public API
request/response keys, DB physical names, or user-facing text.  The goal is to
make the existing ``current_input`` dict explicit as a typed input bundle:

- thought_text  <- memo
- action_text   <- memo_action
- emotions      <- emotion_details / emotions
- categories    <- category
- selected_at   <- created_at
- source_record_id <- id

The exported ``normalize_emlis_current_input`` function returns the same legacy
shape that downstream services already consume, but with the fields normalized
from the typed bundle.  No raw text is added to public metadata here.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION = "emlis.current_input_bundle.v1"

_STRENGTH_SCORE = {
    "": 0,
    "weak": 1,
    "medium": 2,
    "strong": 3,
}

_STRENGTH_ALIASES = {
    "弱": "weak",
    "中": "medium",
    "強": "strong",
    "low": "weak",
    "mid": "medium",
    "middle": "medium",
    "normal": "medium",
    "high": "strong",
}


@dataclass(frozen=True)
class EmlisEmotionInput:
    """One emotion selected in the current input bundle."""

    type: str
    strength: str = ""
    source_field: str = "emotion_details"

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"type": self.type}
        if self.strength:
            payload["strength"] = self.strength
        return payload


@dataclass(frozen=True)
class EmlisEmotionStrengthSummary:
    """Strength summary used only as internal structure material."""

    primary_type: str = ""
    primary_strength: str = ""
    strongest_type: str = ""
    strongest_strength: str = ""
    max_strength_score: int = 0
    has_strong: bool = False
    strength_counts: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_type": self.primary_type,
            "primary_strength": self.primary_strength,
            "strongest_type": self.strongest_type,
            "strongest_strength": self.strongest_strength,
            "max_strength_score": self.max_strength_score,
            "has_strong": self.has_strong,
            "strength_counts": {key: count for key, count in self.strength_counts},
        }


@dataclass(frozen=True)
class EmlisCurrentInputBundle:
    """Typed internal view of the current input used by EmlisAI.

    The raw payload is kept only to preserve unrelated internal fields when the
    bundle is converted back to the legacy ``current_input`` dict.  It is not a
    public response payload.
    """

    thought_text: str = ""
    action_text: str = ""
    emotions: Tuple[EmlisEmotionInput, ...] = field(default_factory=tuple)
    emotion_strength_summary: EmlisEmotionStrengthSummary = field(default_factory=EmlisEmotionStrengthSummary)
    categories: Tuple[str, ...] = field(default_factory=tuple)
    selected_at: str = ""
    source_record_id: str = ""
    is_secret: bool = False
    selection_seed: str = ""
    schema_version: str = EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION
    raw_current_input: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def to_current_input_payload(self) -> Dict[str, Any]:
        """Return the legacy current_input shape with normalized values.

        Existing downstream services consume ``memo``, ``memo_action``,
        ``emotion_details``, ``emotions``, and ``category``.  Those keys remain
        stable; this method only normalizes their internal values.
        """

        payload: Dict[str, Any] = dict(self.raw_current_input or {})
        had_emotions_key = "emotions" in payload or "emotion" in payload
        payload.update(
            {
                "id": self.source_record_id or payload.get("id"),
                "created_at": self.selected_at or payload.get("created_at"),
                "memo": self.thought_text,
                "memo_action": self.action_text,
                "emotion_details": [emotion.to_dict() for emotion in self.emotions],
                "category": list(self.categories),
                "is_secret": bool(self.is_secret),
            }
        )
        # Preserve the legacy ``emotions`` tag list when the caller already owns
        # that field (the /emotion/submit path does).  Do not introduce an extra
        # duplicate structured field for direct internal callers that only passed
        # ``emotion_details``.
        if had_emotions_key:
            payload["emotions"] = [emotion.type for emotion in self.emotions]
        if self.selection_seed:
            payload["selection_seed"] = self.selection_seed
        return payload

    def to_internal_summary(self) -> Dict[str, Any]:
        """Return text-free structural metadata for tests or diagnostics."""

        return {
            "schema_version": self.schema_version,
            "has_thought_text": bool(self.thought_text),
            "has_action_text": bool(self.action_text),
            "emotion_count": len(self.emotions),
            "category_count": len(self.categories),
            "selected_at_present": bool(self.selected_at),
            "source_record_id_present": bool(self.source_record_id),
            "emotion_strength_summary": self.emotion_strength_summary.to_dict(),
        }


def _clean(value: Any) -> str:
    return str(value or "").replace("\u3000", " ").strip()


def _mapping_get(data: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data.get(key)
    return None


def _first_text(data: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = _clean(data.get(key))
        if value:
            return value
    return ""


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _clean(value).lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", ""}:
        return False
    return bool(value)


def _iter_values(value: Any) -> Iterable[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _as_mapping(value: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return value
    return None


def _normalize_strength(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    lowered = text.lower()
    mapped = _STRENGTH_ALIASES.get(text) or _STRENGTH_ALIASES.get(lowered) or lowered
    return mapped if mapped in _STRENGTH_SCORE else lowered


def _emotion_from_value(value: Any, *, source_field: str) -> Optional[EmlisEmotionInput]:
    mapping = _as_mapping(value)
    if mapping is not None:
        emotion_type = _first_text(mapping, "type", "name", "label", "value")
        strength = _normalize_strength(_mapping_get(mapping, "strength", "intensity", "level"))
        if not emotion_type:
            return None
        return EmlisEmotionInput(type=emotion_type, strength=strength, source_field=source_field)

    emotion_type = _clean(getattr(value, "type", ""))
    if not emotion_type:
        emotion_type = _clean(value)
    strength = _normalize_strength(getattr(value, "strength", ""))
    if not emotion_type:
        return None
    return EmlisEmotionInput(type=emotion_type, strength=strength, source_field=source_field)


def _normalize_emotions(data: Mapping[str, Any]) -> Tuple[EmlisEmotionInput, ...]:
    raw_details = _mapping_get(data, "emotion_details", "emotionDetails")
    source_field = "emotion_details"
    values = list(_iter_values(raw_details))
    if not values:
        raw_emotions = _mapping_get(data, "emotions", "emotion")
        values = list(_iter_values(raw_emotions))
        source_field = "emotions"

    normalized = []
    seen = set()
    for value in values:
        item = _emotion_from_value(value, source_field=source_field)
        if item is None:
            continue
        key = (item.type, item.strength)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return tuple(normalized)


def _normalize_categories(data: Mapping[str, Any]) -> Tuple[str, ...]:
    raw_categories = _mapping_get(data, "category", "categories")
    categories = []
    seen = set()
    for value in _iter_values(raw_categories):
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        categories.append(text)
    return tuple(categories)


def _build_strength_summary(emotions: Tuple[EmlisEmotionInput, ...]) -> EmlisEmotionStrengthSummary:
    if not emotions:
        return EmlisEmotionStrengthSummary()

    primary = emotions[0]
    strongest = primary
    counts: Dict[str, int] = {}
    for emotion in emotions:
        strength = emotion.strength or ""
        counts[strength] = counts.get(strength, 0) + 1
        if _STRENGTH_SCORE.get(emotion.strength, 0) > _STRENGTH_SCORE.get(strongest.strength, 0):
            strongest = emotion

    return EmlisEmotionStrengthSummary(
        primary_type=primary.type,
        primary_strength=primary.strength,
        strongest_type=strongest.type,
        strongest_strength=strongest.strength,
        max_strength_score=int(_STRENGTH_SCORE.get(strongest.strength, 0)),
        has_strong=any(emotion.strength == "strong" for emotion in emotions),
        strength_counts=tuple(sorted(counts.items(), key=lambda item: item[0])),
    )


def build_emlis_current_input_bundle(current_input: Any) -> EmlisCurrentInputBundle:
    """Build the typed internal bundle from legacy or alias-shaped input."""

    if isinstance(current_input, EmlisCurrentInputBundle):
        return current_input

    data: Mapping[str, Any]
    if isinstance(current_input, Mapping):
        data = current_input
    else:
        data = {}

    emotions = _normalize_emotions(data)
    return EmlisCurrentInputBundle(
        thought_text=_first_text(data, "thought_text", "thoughtText", "memo", "memo_text", "memoText"),
        action_text=_first_text(data, "action_text", "actionText", "memo_action", "memoAction"),
        emotions=emotions,
        emotion_strength_summary=_build_strength_summary(emotions),
        categories=_normalize_categories(data),
        selected_at=_first_text(data, "selected_at", "selectedAt", "created_at", "createdAt"),
        source_record_id=_first_text(data, "source_record_id", "sourceRecordId", "id"),
        is_secret=_boolish(_mapping_get(data, "is_secret", "isSecret")),
        selection_seed=_first_text(data, "selection_seed", "selectionSeed"),
        raw_current_input=data,
    )


def normalize_emlis_current_input(current_input: Any) -> Dict[str, Any]:
    """Normalize ``current_input`` while preserving its public/internal legacy keys."""

    return build_emlis_current_input_bundle(current_input).to_current_input_payload()


__all__ = [
    "EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION",
    "EmlisCurrentInputBundle",
    "EmlisEmotionInput",
    "EmlisEmotionStrengthSummary",
    "build_emlis_current_input_bundle",
    "normalize_emlis_current_input",
]
