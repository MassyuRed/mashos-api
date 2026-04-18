# -*- coding: utf-8 -*-
from __future__ import annotations

"""Style adaptation rules for EmlisAI."""

from typing import List

from emlis_ai_types import EmlisAICapabilityConfig, SourceBundle, StyleProfile, WorldModel

_SELF_INSIGHT_TOKENS = {"自己理解", "SelfInsight"}
_ANALYTICAL_CATEGORY_TOKENS = {"仕事", "学習", "価値観"}
_SENSITIVE_CATEGORY_TOKENS = {"人間関係", "恋愛", "健康"}


def _memo_length(bundle: SourceBundle) -> int:
    memo = str(bundle.current_input.get("memo") or "").strip()
    memo_action = str(bundle.current_input.get("memo_action") or "").strip()
    return len(memo) + len(memo_action)


def _current_categories(bundle: SourceBundle) -> List[str]:
    raw = bundle.current_input.get("category")
    if not isinstance(raw, list):
        return []
    return [str(v).strip() for v in raw if str(v).strip()]


def build_style_profile(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
) -> StyleProfile:
    categories = set(_current_categories(bundle))
    dominant = str(world_model.facts.dominant_emotion or "").strip()
    memo_length = _memo_length(bundle)

    if dominant in _SELF_INSIGHT_TOKENS or categories & _ANALYTICAL_CATEGORY_TOKENS:
        return StyleProfile(
            family="structured" if capability.style_mode == "base" else "analytical",
            tone_reason="self_insight_or_analytical_category",
            lexical_softness="soft",
            structure_density="medium",
        )

    if categories & _SENSITIVE_CATEGORY_TOKENS:
        return StyleProfile(
            family="sensitive",
            tone_reason="sensitive_category",
            lexical_softness="soft",
            structure_density="light",
        )

    if memo_length <= 0:
        return StyleProfile(
            family="accepting",
            tone_reason="no_memo_input",
            lexical_softness="soft",
            structure_density="light",
        )

    if capability.style_mode == "personalized" and dominant in {"不安", "悲しみ", "怒り"}:
        return StyleProfile(
            family="accepting",
            tone_reason="premium_emotion_softening",
            lexical_softness="soft",
            structure_density="light",
        )

    if memo_length >= 120:
        return StyleProfile(
            family="structured",
            tone_reason="long_memo_prefers_structure",
            lexical_softness="soft",
            structure_density="medium",
        )

    if capability.style_mode == "adaptive":
        return StyleProfile(
            family="sensitive" if dominant in {"不安", "悲しみ"} else "accepting",
            tone_reason="adaptive_recent_input",
            lexical_softness="soft",
            structure_density="light",
        )

    return StyleProfile(
        family="accepting",
        tone_reason="default_accepting",
        lexical_softness="soft",
        structure_density="light",
    )
