# -*- coding: utf-8 -*-
"""piece_publish_entitlements.py

Monthly publish quota rules for the new emotion-generated Reflection flow.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from subscription import SubscriptionTier, normalize_subscription_tier
from subscription_store import get_subscription_tier_for_user

JST = ZoneInfo("Asia/Tokyo")
REFLECTION_PUBLISH_LIMITS: Dict[SubscriptionTier, Optional[int]] = {
    SubscriptionTier.FREE: 5,
    SubscriptionTier.PLUS: 30,
    SubscriptionTier.PREMIUM: None,
}


def resolve_reflection_publish_limit_for_tier(tier: Any) -> Optional[int]:
    normalized = normalize_subscription_tier(tier, default=SubscriptionTier.FREE)
    return REFLECTION_PUBLISH_LIMITS.get(normalized)


async def get_reflection_publish_policy_for_user(user_id: str) -> Dict[str, Any]:
    tier = await get_subscription_tier_for_user(user_id, default=SubscriptionTier.FREE)
    return {
        "subscription_tier": tier.value,
        "publish_limit": resolve_reflection_publish_limit_for_tier(tier),
    }


def get_current_month_window_jst(*, now: Optional[datetime] = None) -> Tuple[str, str, str]:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current_jst = current.astimezone(JST)

    start_jst = current_jst.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start_jst.month == 12:
        next_month_jst = start_jst.replace(year=start_jst.year + 1, month=1)
    else:
        next_month_jst = start_jst.replace(month=start_jst.month + 1)

    month_key = start_jst.strftime("%Y-%m")
    start_iso = start_jst.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    end_iso = next_month_jst.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return month_key, start_iso, end_iso


__all__ = [
    "JST",
    "REFLECTION_PUBLISH_LIMITS",
    "get_current_month_window_jst",
    "get_reflection_publish_policy_for_user",
    "resolve_reflection_publish_limit_for_tier",
]
