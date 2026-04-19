from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from publish_governance import history_retention_bounds_for_query, normalize_tier_str

try:
    from subscription import SubscriptionTier
    from subscription_store import get_subscription_tier_for_user
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore


@dataclass(frozen=True)
class ViewerSubscriptionContext:
    user_id: str
    subscription_tier: str
    history_retention: Dict[str, Any]


async def resolve_subscription_tier_str(user_id: str, *, default: str = "free") -> str:
    uid = str(user_id or "").strip()
    fallback = normalize_tier_str(default)
    if not uid or SubscriptionTier is None or get_subscription_tier_for_user is None:
        return fallback
    try:
        tier = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
        return normalize_tier_str(getattr(tier, "value", tier))
    except Exception:
        return fallback


async def resolve_viewer_subscription_context(
    user_id: str,
    *,
    now_utc: Optional[datetime] = None,
) -> ViewerSubscriptionContext:
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    tier_str = await resolve_subscription_tier_str(user_id)
    retention = history_retention_bounds_for_query(tier_str, now_utc=now)
    return ViewerSubscriptionContext(
        user_id=str(user_id or "").strip(),
        subscription_tier=tier_str,
        history_retention=retention,
    )


__all__ = [
    "ViewerSubscriptionContext",
    "resolve_subscription_tier_str",
    "resolve_viewer_subscription_context",
]
