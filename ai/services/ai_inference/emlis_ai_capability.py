# -*- coding: utf-8 -*-
from __future__ import annotations

"""Capability mapping for EmlisAI."""

from typing import Any, Dict

from emlis_ai_types import EmlisAICapabilityConfig

try:
    from subscription import SubscriptionTier, normalize_subscription_tier
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    normalize_subscription_tier = None  # type: ignore


_CAPABILITY_BY_TIER: Dict[str, EmlisAICapabilityConfig] = {
    "free": EmlisAICapabilityConfig(
        tier="free",
        history_mode="none",
        continuity_mode="off",
        style_mode="base",
        partner_mode="off",
        retrieval_window_days=None,
        max_same_day_inputs=0,
        max_similar_inputs=0,
        include_input_summary=False,
        include_myweb_summary=False,
        include_today_question_history=False,
        include_long_term_history=False,
        strict_evidence_mode=True,
    ),
    "plus": EmlisAICapabilityConfig(
        tier="plus",
        history_mode="extended",
        continuity_mode="basic",
        style_mode="adaptive",
        partner_mode="on_basic",
        retrieval_window_days=365,
        max_same_day_inputs=3,
        max_similar_inputs=3,
        include_input_summary=True,
        include_myweb_summary=True,
        include_today_question_history=True,
        include_long_term_history=False,
        strict_evidence_mode=True,
    ),
    "premium": EmlisAICapabilityConfig(
        tier="premium",
        history_mode="full",
        continuity_mode="advanced",
        style_mode="personalized",
        partner_mode="on_advanced",
        retrieval_window_days=3650,
        max_same_day_inputs=5,
        max_similar_inputs=6,
        include_input_summary=True,
        include_myweb_summary=True,
        include_today_question_history=True,
        include_long_term_history=True,
        strict_evidence_mode=True,
    ),
}


def _normalize_tier(raw_tier: Any) -> str:
    if normalize_subscription_tier is not None and SubscriptionTier is not None:
        tier_enum = normalize_subscription_tier(raw_tier, default=SubscriptionTier.FREE)
        if hasattr(tier_enum, "value"):
            return str(tier_enum.value)
    value = str(raw_tier or "").strip().lower()
    return value if value in _CAPABILITY_BY_TIER else "free"


def resolve_emlis_ai_capability_for_tier(raw_tier: Any) -> EmlisAICapabilityConfig:
    return _CAPABILITY_BY_TIER[_normalize_tier(raw_tier)]


def build_emlis_ai_public_plan_meta(raw_tier: Any) -> Dict[str, Any]:
    capability = resolve_emlis_ai_capability_for_tier(raw_tier)
    return {
        "history_mode": capability.history_mode,
        "continuity_mode": capability.continuity_mode,
        "style_mode": capability.style_mode,
        "partner_mode": capability.partner_mode,
    }
