from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from mymodel_entitlements import resolve_mymodel_entitlement
from publish_governance import history_retention_bounds_for_query, normalize_tier_str

try:
    from subscription import SubscriptionTier
    from subscription_store import get_subscription_tier_for_user
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore


@dataclass(frozen=True)
class PieceTierResolution:
    subscription_tier: str
    view_tier: str
    build_tier: str
    effective_tier: str


async def _resolve_subscription_tier_enum(user_id: str):
    if SubscriptionTier is None or get_subscription_tier_for_user is None:
        return None
    try:
        return await get_subscription_tier_for_user(str(user_id or "").strip(), default=SubscriptionTier.FREE)
    except Exception:
        return SubscriptionTier.FREE


def build_tier_for_subscription(tier: Any) -> str:
    entitlement = resolve_mymodel_entitlement(tier)
    return str(entitlement.build_tier or "light")


def view_tier_for_subscription(tier: Any) -> str:
    # Viewing remains open across subscription tiers; creation/build stays owner-tier-bound.
    return "standard"


def effective_tier(*, view_tier: str, build_tier: str) -> str:
    order = {"light": 0, "standard": 1}
    v = order.get(str(view_tier or "").strip().lower(), 0)
    b = order.get(str(build_tier or "").strip().lower(), 0)
    return "standard" if min(v, b) >= 1 else "light"


async def resolve_view_tier_for_user(user_id: str) -> str:
    tier = await _resolve_subscription_tier_enum(user_id)
    if tier is None:
        return "light"
    return view_tier_for_subscription(tier)


async def resolve_piece_tiers(*, viewer_user_id: str, target_user_id: str) -> PieceTierResolution:
    viewer_tier = await _resolve_subscription_tier_enum(viewer_user_id)
    target_tier = await _resolve_subscription_tier_enum(target_user_id)

    viewer_subscription_tier = normalize_tier_str(getattr(viewer_tier, "value", viewer_tier))
    view_tier = view_tier_for_subscription(viewer_tier)
    build_tier = build_tier_for_subscription(target_tier)
    return PieceTierResolution(
        subscription_tier=viewer_subscription_tier,
        view_tier=view_tier,
        build_tier=build_tier,
        effective_tier=effective_tier(view_tier=view_tier, build_tier=build_tier),
    )


def owner_reflection_policy_from_tier(tier: Any) -> Dict[str, Any]:
    entitlement = resolve_mymodel_entitlement(tier)
    subscription_tier = normalize_tier_str(getattr(tier, "value", tier))
    return {
        "subscription_tier": subscription_tier,
        "build_tier": str(entitlement.build_tier or "light"),
        "template_question_limit": int(entitlement.template_question_limit),
        "can_expose_generated_reflections": bool(entitlement.can_expose_generated_reflections),
        "can_expose_original_reflections": bool(entitlement.can_expose_original_reflections),
    }


async def resolve_owner_reflection_policy(owner_user_id: str) -> Dict[str, Any]:
    tier = await _resolve_subscription_tier_enum(owner_user_id)
    return owner_reflection_policy_from_tier(tier)


async def resolve_owner_reflection_policies(owner_user_ids: Iterable[str] | Set[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for owner_user_id in owner_user_ids or set():
        oid = str(owner_user_id or "").strip()
        if not oid or oid in out:
            continue
        out[oid] = await resolve_owner_reflection_policy(oid)
    return out


def viewer_history_retention(viewer_tier: Any, *, now_utc: Optional[datetime] = None) -> Tuple[str, Dict[str, Any]]:
    tier_str = normalize_tier_str(getattr(viewer_tier, "value", viewer_tier))
    bounds = history_retention_bounds_for_query(
        tier_str,
        now_utc=(now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc),
    )
    return tier_str, bounds


__all__ = [
    "PieceTierResolution",
    "build_tier_for_subscription",
    "effective_tier",
    "owner_reflection_policy_from_tier",
    "resolve_owner_reflection_policies",
    "resolve_owner_reflection_policy",
    "resolve_piece_tiers",
    "resolve_view_tier_for_user",
    "view_tier_for_subscription",
    "viewer_history_retention",
]
