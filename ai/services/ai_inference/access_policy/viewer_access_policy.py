from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Set, Tuple

from access_policy.piece_access_policy import (
    PieceTierResolution,
    resolve_owner_reflection_policies,
    resolve_owner_reflection_policy,
    resolve_piece_tiers,
    resolve_view_tier_for_user,
    viewer_history_retention,
)
from access_policy.report_access_policy import (
    apply_myprofile_report_access,
    apply_myweb_report_access,
    build_history_retention,
)
from access_policy.subscription_context import (
    ViewerSubscriptionContext,
    resolve_subscription_tier_str,
    resolve_viewer_subscription_context,
)


async def resolve_viewer_tier_str(user_id: str) -> str:
    return await resolve_subscription_tier_str(user_id)


async def resolve_report_view_context(
    user_id: str,
    *,
    now_utc: Optional[datetime] = None,
) -> ViewerSubscriptionContext:
    return await resolve_viewer_subscription_context(user_id, now_utc=now_utc)


def build_report_history_retention(tier_str: Any, *, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    return build_history_retention(tier_str, now_utc=now_utc)


def apply_myweb_report_access_for_viewer(
    row: Dict[str, Any],
    *,
    context: Optional[ViewerSubscriptionContext] = None,
    tier_str: Any = None,
    requested_report_type: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    tier = tier_str
    if context is not None:
        tier = context.subscription_tier
    return apply_myweb_report_access(
        row,
        tier_str=tier,
        requested_report_type=requested_report_type,
        now_utc=now_utc,
    )


def apply_myprofile_report_access_for_viewer(
    row: Dict[str, Any],
    *,
    context: Optional[ViewerSubscriptionContext] = None,
    tier_str: Any = None,
    requested_report_type: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    tier = tier_str
    if context is not None:
        tier = context.subscription_tier
    return apply_myprofile_report_access(
        row,
        tier_str=tier,
        requested_report_type=requested_report_type,
        now_utc=now_utc,
    )


async def resolve_piece_view_tiers(*, viewer_user_id: str, target_user_id: str) -> PieceTierResolution:
    return await resolve_piece_tiers(viewer_user_id=viewer_user_id, target_user_id=target_user_id)


async def resolve_piece_view_tier_for_user(user_id: str) -> str:
    return await resolve_view_tier_for_user(user_id)


async def resolve_piece_owner_reflection_policy(owner_user_id: str) -> Dict[str, Any]:
    return await resolve_owner_reflection_policy(owner_user_id)


async def resolve_piece_owner_reflection_policies(owner_user_ids: Iterable[str] | Set[str]) -> Dict[str, Dict[str, Any]]:
    return await resolve_owner_reflection_policies(owner_user_ids)


def piece_viewer_history_retention(viewer_tier: Any, *, now_utc: Optional[datetime] = None) -> Tuple[str, Dict[str, Any]]:
    return viewer_history_retention(
        viewer_tier,
        now_utc=(now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc),
    )


__all__ = [
    "apply_myprofile_report_access_for_viewer",
    "apply_myweb_report_access_for_viewer",
    "build_report_history_retention",
    "piece_viewer_history_retention",
    "resolve_piece_owner_reflection_policies",
    "resolve_piece_owner_reflection_policy",
    "resolve_piece_view_tier_for_user",
    "resolve_piece_view_tiers",
    "resolve_report_view_context",
    "resolve_viewer_tier_str",
]
