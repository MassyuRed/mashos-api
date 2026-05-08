from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "services", ROOT / "services" / "ai_inference"):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import subscription_projection as sp
from subscription import SubscriptionTier


def _iso_after(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_entitlement_access_requires_future_expiry_for_renewable_statuses():
    future = _iso_after(3)
    past = _iso_after(-3)

    assert sp.entitlement_confers_access({"status": "active", "expires_at": future}) is True
    assert sp.entitlement_confers_access({"status": "grace_period", "expires_at": future}) is True
    assert sp.entitlement_confers_access({"status": "cancelled", "expires_at": future}) is True

    assert sp.entitlement_confers_access({"status": "active", "expires_at": past}) is False
    assert sp.entitlement_confers_access({"status": "grace_period", "expires_at": past}) is False
    assert sp.entitlement_confers_access({"status": "cancelled", "expires_at": past}) is False
    assert sp.entitlement_confers_access({"status": "active", "expires_at": None}) is False


def test_effective_entitlement_status_marks_expired_active_row_as_expired():
    assert sp.effective_entitlement_status({"status": "active", "expires_at": _iso_after(-1)}) == "expired"
    assert sp.effective_entitlement_status({"status": "cancelled", "expires_at": _iso_after(-1)}) == "expired"
    assert sp.effective_entitlement_status({"status": "cancelled", "expires_at": _iso_after(1)}) == "cancelled"


def test_build_subscription_state_prefers_valid_entitlement_over_expired_active(monkeypatch):
    async def fake_profile_tier(user_id: str):
        return SubscriptionTier.PLUS

    async def fake_entitlements(user_id: str):
        return [
            {
                "id": 1,
                "user_id": user_id,
                "plan_code": "premium",
                "status": "active",
                "expires_at": _iso_after(-2),
                "updated_at": _iso_after(-2),
                "store": "android",
                "product_id": "cocolon_premium_monthly",
                "store_ref": "expired-token",
            },
            {
                "id": 2,
                "user_id": user_id,
                "plan_code": "plus",
                "status": "cancelled",
                "expires_at": _iso_after(2),
                "updated_at": _iso_after(-1),
                "store": "android",
                "product_id": "cocolon_plus_monthly",
                "store_ref": "valid-token",
            },
        ]

    monkeypatch.setattr(sp, "get_subscription_tier_for_user", fake_profile_tier)
    monkeypatch.setattr(sp, "fetch_user_entitlement_rows", fake_entitlements)

    state = asyncio.run(sp.build_subscription_state("user-1"))

    assert state.subscription_tier == "plus"
    assert state.entitlement_status == "cancelled"
    assert state.store_ref == "valid-token"


def test_build_subscription_state_ignores_paid_profile_tier_when_no_entitlement(monkeypatch):
    async def fake_profile_tier(user_id: str):
        return SubscriptionTier.PLUS

    async def fake_entitlements(user_id: str):
        return []

    monkeypatch.delenv("COCOLON_SUBSCRIPTION_ALLOW_LEGACY_PROFILE_TIER", raising=False)
    monkeypatch.setattr(sp, "get_subscription_tier_for_user", fake_profile_tier)
    monkeypatch.setattr(sp, "fetch_user_entitlement_rows", fake_entitlements)

    state = asyncio.run(sp.build_subscription_state("user-1"))

    assert state.subscription_tier == "free"
    assert state.plan_code is None
    assert state.entitlement_status == "none"
