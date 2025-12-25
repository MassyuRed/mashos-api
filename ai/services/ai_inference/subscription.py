# -*- coding: utf-8 -*-
"""subscription.py

Subscription / Mode primitives (Step 1)
--------------------------------------
This module defines:

- SubscriptionTier: free / plus / premium
- MyProfileMode:    light / standard / deep
- TierPermissionMap: allowed MyProfile modes per tier

Design notes:
- Keep this file dependency-free (std lib only).
- Normalization helpers accept common variants (case, JP labels).
- Other feature entitlements (MyWeb, Deep Insight limits, etc.) will be added
  in later steps; Step 1 focuses on tier+mode primitives.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, List, Optional, Tuple, Union


class SubscriptionTier(str, Enum):
    """Cocolon subscription tier."""

    FREE = "free"
    PLUS = "plus"
    PREMIUM = "premium"


class MyProfileMode(str, Enum):
    """MyProfile output mode."""

    LIGHT = "light"
    STANDARD = "standard"
    DEEP = "deep"


# --- Tier → allowed MyProfile modes (Single source of truth) ---
TIER_ALLOWED_MYPROFILE_MODES: Dict[SubscriptionTier, Tuple[MyProfileMode, ...]] = {
    SubscriptionTier.FREE: (MyProfileMode.LIGHT,),
    SubscriptionTier.PLUS: (MyProfileMode.LIGHT, MyProfileMode.STANDARD),
    SubscriptionTier.PREMIUM: (MyProfileMode.LIGHT, MyProfileMode.STANDARD, MyProfileMode.DEEP),
}


# --- Normalization helpers ---
_TIER_ALIASES: Dict[str, SubscriptionTier] = {
    # canonical
    "free": SubscriptionTier.FREE,
    "plus": SubscriptionTier.PLUS,
    "premium": SubscriptionTier.PREMIUM,
    # common UI labels
    "無料": SubscriptionTier.FREE,
    "無課金": SubscriptionTier.FREE,
    "フリー": SubscriptionTier.FREE,
    "プラス": SubscriptionTier.PLUS,
    "プレミアム": SubscriptionTier.PREMIUM,
    # typical casing
    "Free": SubscriptionTier.FREE,
    "Plus": SubscriptionTier.PLUS,
    "Premium": SubscriptionTier.PREMIUM,
}


_MODE_ALIASES: Dict[str, MyProfileMode] = {
    # canonical
    "light": MyProfileMode.LIGHT,
    "standard": MyProfileMode.STANDARD,
    "deep": MyProfileMode.DEEP,
    # typical casing
    "Light": MyProfileMode.LIGHT,
    "Standard": MyProfileMode.STANDARD,
    "Deep": MyProfileMode.DEEP,
    # JP labels
    "ライト": MyProfileMode.LIGHT,
    "スタンダード": MyProfileMode.STANDARD,
    "ディープ": MyProfileMode.DEEP,
}


TierLike = Union[SubscriptionTier, str, None]
ModeLike = Union[MyProfileMode, str, None]


def normalize_subscription_tier(tier: TierLike, *, default: SubscriptionTier = SubscriptionTier.FREE) -> SubscriptionTier:
    """Normalize incoming tier.

    Accepts:
    - SubscriptionTier enum
    - strings like "free"/"Plus"/"無料"/"無課金" etc.
    - None → default
    """

    if tier is None:
        return default
    if isinstance(tier, SubscriptionTier):
        return tier
    s = str(tier).strip()
    if not s:
        return default
    # First: direct alias match (preserve casing variants)
    if s in _TIER_ALIASES:
        return _TIER_ALIASES[s]
    # Fallback: lowercase canonical
    s2 = s.lower()
    return _TIER_ALIASES.get(s2, default)


def normalize_myprofile_mode(mode: ModeLike, *, default: MyProfileMode = MyProfileMode.LIGHT) -> MyProfileMode:
    """Normalize incoming MyProfile mode."""

    if mode is None:
        return default
    if isinstance(mode, MyProfileMode):
        return mode
    s = str(mode).strip()
    if not s:
        return default
    if s in _MODE_ALIASES:
        return _MODE_ALIASES[s]
    s2 = s.lower()
    return _MODE_ALIASES.get(s2, default)


def allowed_myprofile_modes_for_tier(tier: TierLike) -> List[MyProfileMode]:
    """Return allowed MyProfile modes for the given tier."""

    t = normalize_subscription_tier(tier)
    return list(TIER_ALLOWED_MYPROFILE_MODES.get(t, (MyProfileMode.LIGHT,)))


def is_myprofile_mode_allowed(tier: TierLike, mode: ModeLike) -> bool:
    """True if tier allows the mode."""

    t = normalize_subscription_tier(tier)
    m = normalize_myprofile_mode(mode)
    allowed = TIER_ALLOWED_MYPROFILE_MODES.get(t, (MyProfileMode.LIGHT,))
    return m in allowed


def assert_myprofile_mode_allowed(tier: TierLike, mode: ModeLike) -> None:
    """Raise ValueError if tier does not allow the mode."""

    if not is_myprofile_mode_allowed(tier, mode):
        t = normalize_subscription_tier(tier)
        m = normalize_myprofile_mode(mode)
        allowed = ",".join([x.value for x in allowed_myprofile_modes_for_tier(t)])
        raise ValueError(f"MyProfile mode '{m.value}' is not allowed for tier '{t.value}'. Allowed: {allowed}")
