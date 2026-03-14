# -*- coding: utf-8 -*-
"""mymodel_entitlements.py

Single source of truth for MyModel Create / Reflections entitlement rules.

Design goals
------------
- Keep build-tier semantics cumulative and server-authoritative.
- Allow the DB to temporarily contain more/fewer rows than the product spec
  without breaking callers.
- Separate template-question visibility from original/generated reflection
  visibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from subscription import SubscriptionTier, normalize_subscription_tier


LIGHT_BUILD_TIER = "light"
STANDARD_BUILD_TIER = "standard"
ALLOWED_BUILD_TIERS: Tuple[str, ...] = (LIGHT_BUILD_TIER, STANDARD_BUILD_TIER)

FREE_TEMPLATE_QUESTION_LIMIT = 5
PAID_TEMPLATE_QUESTION_LIMIT = 20

_BUILD_TIER_VISIBLE_TIERS: Dict[str, Tuple[str, ...]] = {
    LIGHT_BUILD_TIER: (LIGHT_BUILD_TIER,),
    STANDARD_BUILD_TIER: (LIGHT_BUILD_TIER, STANDARD_BUILD_TIER),
}

_BUILD_TIER_TEMPLATE_LIMITS: Dict[str, int] = {
    LIGHT_BUILD_TIER: FREE_TEMPLATE_QUESTION_LIMIT,
    STANDARD_BUILD_TIER: PAID_TEMPLATE_QUESTION_LIMIT,
}


@dataclass(frozen=True)
class MyModelEntitlement:
    subscription_tier: str
    build_tier: str
    visible_question_tiers: Tuple[str, ...]
    template_question_limit: int
    can_edit_existing_answers: bool
    can_expose_original_reflections: bool

    @property
    def can_expose_generated_reflections(self) -> bool:
        return bool(self.can_expose_original_reflections)


def normalize_build_tier(build_tier: Any, *, default: str = LIGHT_BUILD_TIER) -> str:
    s = str(build_tier or "").strip().lower()
    return s if s in ALLOWED_BUILD_TIERS else default


def question_tiers_for_build_tier(build_tier: Any) -> Tuple[str, ...]:
    tier = normalize_build_tier(build_tier)
    return _BUILD_TIER_VISIBLE_TIERS.get(tier, _BUILD_TIER_VISIBLE_TIERS[LIGHT_BUILD_TIER])


def template_question_limit_for_build_tier(build_tier: Any) -> int:
    tier = normalize_build_tier(build_tier)
    return int(_BUILD_TIER_TEMPLATE_LIMITS.get(tier, FREE_TEMPLATE_QUESTION_LIMIT))


def resolve_mymodel_entitlement(subscription_tier: Any) -> MyModelEntitlement:
    tier = normalize_subscription_tier(subscription_tier, default=SubscriptionTier.FREE)
    build_tier = LIGHT_BUILD_TIER if tier == SubscriptionTier.FREE else STANDARD_BUILD_TIER
    return MyModelEntitlement(
        subscription_tier=tier.value,
        build_tier=build_tier,
        visible_question_tiers=question_tiers_for_build_tier(build_tier),
        template_question_limit=template_question_limit_for_build_tier(build_tier),
        can_edit_existing_answers=(tier in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM)),
        can_expose_original_reflections=(tier == SubscriptionTier.PREMIUM),
    )


def _coerce_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _is_active_flag(value: Any) -> bool:
    if value is None:
        return True
    if value is True:
        return True
    if value is False:
        return False
    if isinstance(value, str):
        return value.strip().lower() in ("true", "t", "1", "yes", "y")
    if isinstance(value, int):
        return value == 1
    return bool(value)


def filter_question_rows_for_build_tier(
    rows: Sequence[Dict[str, Any]] | Iterable[Dict[str, Any]],
    *,
    build_tier: Any,
) -> List[Dict[str, Any]]:
    visible_tiers = {str(x).strip().lower() for x in question_tiers_for_build_tier(build_tier)}
    limit = template_question_limit_for_build_tier(build_tier)

    filtered: List[Dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        if not _is_active_flag(row.get("is_active")):
            continue
        row_tier = str(row.get("tier") or "").strip().lower() or LIGHT_BUILD_TIER
        if row_tier not in visible_tiers:
            continue
        filtered.append(row)

    filtered.sort(
        key=lambda r: (
            _coerce_int(r.get("sort_order"), default=10**9),
            _coerce_int(r.get("id"), default=10**9),
        )
    )
    return filtered[: int(limit)]


__all__ = [
    "ALLOWED_BUILD_TIERS",
    "FREE_TEMPLATE_QUESTION_LIMIT",
    "LIGHT_BUILD_TIER",
    "MyModelEntitlement",
    "PAID_TEMPLATE_QUESTION_LIMIT",
    "STANDARD_BUILD_TIER",
    "filter_question_rows_for_build_tier",
    "normalize_build_tier",
    "question_tiers_for_build_tier",
    "resolve_mymodel_entitlement",
    "template_question_limit_for_build_tier",
]
