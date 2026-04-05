# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from subscription import (
    SubscriptionTier,
    allowed_myprofile_modes_for_tier,
    normalize_subscription_tier,
)
from subscription_store import get_subscription_tier_for_user, set_subscription_tier_for_user
from supabase_client import (
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_post as _sb_post_shared,
    sb_service_role_headers_json as _sb_headers_shared,
)

logger = logging.getLogger("subscription_projection")

CLAIMS_TABLE = "subscription_purchase_claims"
ENTITLEMENTS_TABLE = "subscription_entitlements"
NOTIFICATION_LOG_TABLE = "store_notification_log"

ENTITLEMENT_STATUS_NONE = "none"
ACTIVE_ENTITLEMENT_STATUSES = {"active", "grace_period"}
ENTITLEMENT_STATUS_PRIORITY = {
    "active": 0,
    "grace_period": 1,
    "pending": 2,
    "account_hold": 3,
    "paused": 4,
    "cancelled": 5,
    "expired": 6,
    "revoked": 7,
}


class PurchaseOwnershipConflictError(RuntimeError):
    pass


@dataclass(slots=True)
class VerifiedPurchase:
    store: str
    product_id: str
    plan_code: Optional[str]
    status: str
    verification_status: str
    store_ref: str
    base_plan_id: Optional[str] = None
    purchase_token: Optional[str] = None
    transaction_id: Optional[str] = None
    original_transaction_id: Optional[str] = None
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
    auto_renew: bool = False
    source: str = "store_verification"
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    app_user_id_hint: Optional[str] = None
    needs_acknowledge: bool = False


@dataclass(slots=True)
class CanonicalSubscriptionState:
    user_id: str
    subscription_tier: str
    allowed_myprofile_modes: list[str]
    plan_code: Optional[str] = None
    entitlement_status: str = ENTITLEMENT_STATUS_NONE
    expires_at: Optional[str] = None
    auto_renew: bool = False
    store: Optional[str] = None
    product_id: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "subscription_tier": self.subscription_tier,
            "allowed_myprofile_modes": list(self.allowed_myprofile_modes),
            "plan_code": self.plan_code,
            "entitlement_status": self.entitlement_status,
            "expires_at": self.expires_at,
            "auto_renew": self.auto_renew,
            "store": self.store,
            "product_id": self.product_id,
        }


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    return _sb_headers_shared(prefer=prefer)



def clean_optional_str(value: Any) -> Optional[str]:
    s = str(value or "").strip()
    return s or None



def normalize_platform(platform: Optional[str]) -> Optional[str]:
    plat = str(platform or "").strip().lower()
    if plat in {"ios", "android"}:
        return plat
    return None



def normalize_plan_code(value: Optional[str]) -> Optional[str]:
    plan = str(value or "").strip().lower()
    if plan in {SubscriptionTier.PLUS.value, SubscriptionTier.PREMIUM.value}:
        return plan
    return None



def plan_code_to_tier(plan_code: Optional[str]) -> SubscriptionTier:
    plan = normalize_plan_code(plan_code)
    if plan == SubscriptionTier.PREMIUM.value:
        return SubscriptionTier.PREMIUM
    if plan == SubscriptionTier.PLUS.value:
        return SubscriptionTier.PLUS
    return SubscriptionTier.FREE



def normalize_entitlement_status(value: Optional[str]) -> str:
    status = str(value or "").strip().lower()
    if status in ENTITLEMENT_STATUS_PRIORITY:
        return status
    return ENTITLEMENT_STATUS_NONE



def iso_or_none(value: Any) -> Optional[str]:
    return clean_optional_str(value)



def parse_iso_ts(value: Any) -> float:
    s = clean_optional_str(value)
    if not s:
        return 0.0
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0



def _split_env_list(name: str) -> list[str]:
    raw = str(os.getenv(name, "") or "")
    return [s.strip() for s in raw.split(",") if s.strip()]



def plan_code_from_product_id(store: Optional[str], product_id: Optional[str]) -> Optional[str]:
    pid = clean_optional_str(product_id)
    if not pid:
        return None

    low = pid.lower()
    if "premium" in low:
        return SubscriptionTier.PREMIUM.value
    if "plus" in low:
        return SubscriptionTier.PLUS.value

    platform = normalize_platform(store)
    if platform == "android":
        plus_ids = set(_split_env_list("COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS"))
        premium_ids = set(_split_env_list("COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS"))
    elif platform == "ios":
        plus_ids = set(_split_env_list("COCOLON_IAP_IOS_PLUS_PRODUCT_IDS"))
        premium_ids = set(_split_env_list("COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS"))
    else:
        plus_ids = set()
        premium_ids = set()

    plus_match = pid in plus_ids
    premium_match = pid in premium_ids
    if premium_match and not plus_match:
        return SubscriptionTier.PREMIUM.value
    if plus_match and not premium_match:
        return SubscriptionTier.PLUS.value
    return None


def plan_code_from_android_purchase(
    product_id: Optional[str],
    base_plan_id: Optional[str],
) -> Optional[str]:
    base_plan = clean_optional_str(base_plan_id)
    if base_plan:
        low = base_plan.lower()
        if "premium" in low:
            return SubscriptionTier.PREMIUM.value
        if "plus" in low or "trial" in low:
            return SubscriptionTier.PLUS.value

        plus_base_plan_ids = set(
            _split_env_list("COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS")
            or ["plus"]
        )
        premium_base_plan_ids = set(
            _split_env_list("COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS")
            or ["premium"]
        )
        if base_plan in premium_base_plan_ids:
            return SubscriptionTier.PREMIUM.value
        if base_plan in plus_base_plan_ids:
            return SubscriptionTier.PLUS.value

    return plan_code_from_product_id("android", product_id)


def entitlement_confers_access(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False

    status = normalize_entitlement_status(row.get("status"))
    if status in ACTIVE_ENTITLEMENT_STATUSES:
        return True

    if status == "cancelled":
        expires_at = parse_iso_ts(row.get("expires_at"))
        return expires_at > datetime.now(timezone.utc).timestamp()

    return False



def verified_purchase_confers_access(v: VerifiedPurchase) -> bool:
    return entitlement_confers_access({"status": v.status, "expires_at": v.expires_at})



def _entitlement_priority(row: Dict[str, Any]) -> tuple[int, float, float, float]:
    status = normalize_entitlement_status(row.get("status"))
    priority = ENTITLEMENT_STATUS_PRIORITY.get(status, 999)
    expires_ts = parse_iso_ts(row.get("expires_at"))
    updated_ts = parse_iso_ts(row.get("updated_at")) or parse_iso_ts(row.get("created_at"))
    try:
        numeric_id = float(row.get("id") or 0)
    except Exception:
        numeric_id = 0.0
    return (priority, -expires_ts, -updated_ts, -numeric_id)



def _rows_from_json(data: Any) -> list[Dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


# ---------------------------------------------------------------------------
# PostgREST helpers
# ---------------------------------------------------------------------------


async def fetch_rows(table: str, *, params: Dict[str, str], timeout: float = 6.0) -> list[Dict[str, Any]]:
    resp = await _sb_get_shared(
        f"/rest/v1/{table}",
        params=params,
        headers=_headers(),
        timeout=timeout,
    )
    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to fetch {table}: status={resp.status_code} body={resp.text[:1200]}"
        )
    try:
        return _rows_from_json(resp.json())
    except Exception as exc:
        raise RuntimeError(f"{table} response was not JSON") from exc


async def fetch_first_row(table: str, *, params: Dict[str, str], timeout: float = 6.0) -> Optional[Dict[str, Any]]:
    q = dict(params)
    q.setdefault("limit", "1")
    rows = await fetch_rows(table, params=q, timeout=timeout)
    return rows[0] if rows else None


async def insert_row(
    table: str,
    payload: Dict[str, Any],
    *,
    on_conflict: Optional[str] = None,
    timeout: float = 6.0,
) -> Dict[str, Any]:
    params: Dict[str, str] = {}
    prefer = "return=representation"
    if on_conflict:
        params["on_conflict"] = on_conflict
        prefer = "resolution=merge-duplicates,return=representation"

    resp = await _sb_post_shared(
        f"/rest/v1/{table}",
        params=params or None,
        json=payload,
        headers=_headers(prefer=prefer),
        timeout=timeout,
    )
    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to insert {table}: status={resp.status_code} body={resp.text[:1200]}"
        )

    try:
        rows = _rows_from_json(resp.json())
        return rows[0] if rows else {}
    except Exception:
        return {}


async def patch_rows(
    table: str,
    *,
    filters: Dict[str, str],
    patch: Dict[str, Any],
    timeout: float = 6.0,
) -> Dict[str, Any]:
    resp = await _sb_patch_shared(
        f"/rest/v1/{table}",
        params=filters,
        json=patch,
        headers=_headers(prefer="return=representation"),
        timeout=timeout,
    )
    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to patch {table}: status={resp.status_code} body={resp.text[:1200]}"
        )

    try:
        rows = _rows_from_json(resp.json())
        return rows[0] if rows else {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Runtime table helpers
# ---------------------------------------------------------------------------


async def fetch_user_entitlement_rows(user_id: str) -> list[Dict[str, Any]]:
    return await fetch_rows(
        ENTITLEMENTS_TABLE,
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "updated_at.desc",
            "limit": "20",
        },
    )


async def find_entitlement_by_store_ref(store: str, store_ref: str) -> Optional[Dict[str, Any]]:
    if not store or not store_ref:
        return None
    return await fetch_first_row(
        ENTITLEMENTS_TABLE,
        params={
            "select": "*",
            "store": f"eq.{store}",
            "store_ref": f"eq.{store_ref}",
        },
    )


async def find_purchase_claim(
    *,
    store: str,
    purchase_token: Optional[str] = None,
    transaction_id: Optional[str] = None,
    original_transaction_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    search_order = [
        ("original_transaction_id", clean_optional_str(original_transaction_id)),
        ("purchase_token", clean_optional_str(purchase_token)),
        ("transaction_id", clean_optional_str(transaction_id)),
    ]
    for column, value in search_order:
        if not value:
            continue
        row = await fetch_first_row(
            CLAIMS_TABLE,
            params={
                "select": "*",
                "store": f"eq.{store}",
                column: f"eq.{value}",
            },
        )
        if row:
            return row
    return None


async def build_subscription_state(user_id: str) -> CanonicalSubscriptionState:
    profile_tier = await get_subscription_tier_for_user(user_id)

    best_entitlement: Optional[Dict[str, Any]] = None
    try:
        ent_rows = await fetch_user_entitlement_rows(user_id)
        best_entitlement = sorted(
            [row for row in ent_rows if isinstance(row, dict)],
            key=_entitlement_priority,
        )[0] if ent_rows else None
    except Exception as exc:
        logger.warning(
            "Failed to fetch entitlement rows, falling back to profiles.subscription_tier: %s",
            exc,
        )
        best_entitlement = None

    if best_entitlement:
        entitlement_status = normalize_entitlement_status(best_entitlement.get("status"))
        plan_code = normalize_plan_code(best_entitlement.get("plan_code"))
        tier = plan_code_to_tier(plan_code) if entitlement_confers_access(best_entitlement) else SubscriptionTier.FREE
        expires_at = iso_or_none(best_entitlement.get("expires_at"))
        auto_renew = bool(best_entitlement.get("auto_renew"))
        store = clean_optional_str(best_entitlement.get("store"))
        product_id = clean_optional_str(best_entitlement.get("product_id"))
    else:
        tier = profile_tier
        plan_code = profile_tier.value if profile_tier in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM) else None
        entitlement_status = "legacy_profile_tier" if plan_code else ENTITLEMENT_STATUS_NONE
        expires_at = None
        auto_renew = False
        store = None
        product_id = None

    modes = [m.value for m in allowed_myprofile_modes_for_tier(tier)]

    return CanonicalSubscriptionState(
        user_id=user_id,
        subscription_tier=tier.value,
        allowed_myprofile_modes=modes,
        plan_code=plan_code,
        entitlement_status=entitlement_status,
        expires_at=expires_at,
        auto_renew=auto_renew,
        store=store,
        product_id=product_id,
    )


async def _refresh_purchase_claim(existing_claim: Dict[str, Any], verified_purchase: VerifiedPurchase) -> Dict[str, Any]:
    claim_id = existing_claim.get("id")
    if claim_id is None:
        return existing_claim

    now_iso = datetime.now(timezone.utc).isoformat()
    patch: Dict[str, Any] = {
        "plan_code": normalize_plan_code(verified_purchase.plan_code),
        "product_id": clean_optional_str(verified_purchase.product_id),
        "last_seen_at": now_iso,
        "raw_payload": verified_purchase.raw_payload,
        "verification_status": verified_purchase.verification_status,
    }
    if verified_purchase.verification_status in {"verified", "replayed", "rejected", "expired", "revoked", "pending", "error"}:
        patch["verified_at"] = now_iso
    try:
        updated = await patch_rows(
            CLAIMS_TABLE,
            filters={"id": f"eq.{claim_id}"},
            patch=patch,
        )
        return updated or existing_claim
    except Exception as exc:
        logger.warning("Failed to refresh purchase claim: %s", exc)
        return existing_claim


async def upsert_purchase_claim(*, user_id: str, verified_purchase: VerifiedPurchase) -> Dict[str, Any]:
    existing = await find_purchase_claim(
        store=verified_purchase.store,
        purchase_token=verified_purchase.purchase_token,
        transaction_id=verified_purchase.transaction_id,
        original_transaction_id=verified_purchase.original_transaction_id,
    )
    if existing:
        existing_user_id = str(existing.get("user_id") or "").strip()
        if existing_user_id and existing_user_id != user_id:
            raise PurchaseOwnershipConflictError("This purchase is already linked to another Cocolon account.")
        return await _refresh_purchase_claim(existing, verified_purchase)

    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "user_id": user_id,
        "store": verified_purchase.store,
        "plan_code": normalize_plan_code(verified_purchase.plan_code),
        "product_id": clean_optional_str(verified_purchase.product_id),
        "purchase_token": clean_optional_str(verified_purchase.purchase_token),
        "transaction_id": clean_optional_str(verified_purchase.transaction_id),
        "original_transaction_id": clean_optional_str(verified_purchase.original_transaction_id),
        "verification_status": verified_purchase.verification_status,
        "verified_at": now_iso if verified_purchase.verification_status in {"verified", "replayed", "expired", "revoked", "pending"} else None,
        "last_seen_at": now_iso,
        "raw_payload": verified_purchase.raw_payload,
    }
    return await insert_row(CLAIMS_TABLE, payload)


async def upsert_entitlement_from_verified_purchase(*, user_id: str, verified_purchase: VerifiedPurchase) -> Dict[str, Any]:
    store_ref = clean_optional_str(verified_purchase.store_ref)
    if not store_ref:
        raise RuntimeError("verified_purchase.store_ref is required")

    existing = await find_entitlement_by_store_ref(verified_purchase.store, store_ref)
    if existing:
        existing_user_id = str(existing.get("user_id") or "").strip()
        if existing_user_id and existing_user_id != user_id:
            raise PurchaseOwnershipConflictError("This purchase entitlement is already linked to another Cocolon account.")
        patch = {
            "plan_code": normalize_plan_code(verified_purchase.plan_code),
            "product_id": clean_optional_str(verified_purchase.product_id),
            "status": normalize_entitlement_status(verified_purchase.status),
            "starts_at": iso_or_none(verified_purchase.starts_at),
            "expires_at": iso_or_none(verified_purchase.expires_at),
            "auto_renew": bool(verified_purchase.auto_renew),
            "source": clean_optional_str(verified_purchase.source) or "store_verification",
            "raw_last_payload": verified_purchase.raw_payload,
        }
        updated = await patch_rows(
            ENTITLEMENTS_TABLE,
            filters={"id": f"eq.{existing.get('id')}"},
            patch=patch,
        )
        return updated or existing

    payload = {
        "user_id": user_id,
        "plan_code": normalize_plan_code(verified_purchase.plan_code),
        "store": verified_purchase.store,
        "product_id": clean_optional_str(verified_purchase.product_id),
        "status": normalize_entitlement_status(verified_purchase.status),
        "starts_at": iso_or_none(verified_purchase.starts_at),
        "expires_at": iso_or_none(verified_purchase.expires_at),
        "auto_renew": bool(verified_purchase.auto_renew),
        "store_ref": store_ref,
        "source": clean_optional_str(verified_purchase.source) or "store_verification",
        "raw_last_payload": verified_purchase.raw_payload,
    }
    return await insert_row(ENTITLEMENTS_TABLE, payload)


async def project_profile_tier(user_id: str) -> CanonicalSubscriptionState:
    snapshot = await build_subscription_state(user_id)
    projected_tier = normalize_subscription_tier(snapshot.subscription_tier, default=SubscriptionTier.FREE)
    await set_subscription_tier_for_user(user_id, projected_tier)
    return await build_subscription_state(user_id)


async def persist_verified_purchase(*, user_id: str, verified_purchase: VerifiedPurchase) -> CanonicalSubscriptionState:
    await upsert_purchase_claim(user_id=user_id, verified_purchase=verified_purchase)
    await upsert_entitlement_from_verified_purchase(user_id=user_id, verified_purchase=verified_purchase)
    return await project_profile_tier(user_id)


async def resolve_user_id_for_purchase(
    *,
    store: str,
    purchase_token: Optional[str] = None,
    transaction_id: Optional[str] = None,
    original_transaction_id: Optional[str] = None,
    app_user_id_hint: Optional[str] = None,
) -> Optional[str]:
    hinted = clean_optional_str(app_user_id_hint)
    if hinted:
        return hinted

    claim = await find_purchase_claim(
        store=store,
        purchase_token=purchase_token,
        transaction_id=transaction_id,
        original_transaction_id=original_transaction_id,
    )
    claim_user_id = clean_optional_str((claim or {}).get("user_id"))
    if claim_user_id:
        return claim_user_id

    for store_ref in (
        clean_optional_str(original_transaction_id),
        clean_optional_str(purchase_token),
        clean_optional_str(transaction_id),
    ):
        if not store_ref:
            continue
        ent = await find_entitlement_by_store_ref(store, store_ref)
        ent_user_id = clean_optional_str((ent or {}).get("user_id"))
        if ent_user_id:
            return ent_user_id

    return None


# ---------------------------------------------------------------------------
# Notification logging helpers
# ---------------------------------------------------------------------------


async def log_store_notification(*, store: str, event_id: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized_store = normalize_platform(store) or "android"
    eid = clean_optional_str(event_id)
    etype = clean_optional_str(event_type) or "unknown"
    if not eid:
        raise RuntimeError("event_id is required")

    existing = await fetch_first_row(
        NOTIFICATION_LOG_TABLE,
        params={
            "select": "*",
            "store": f"eq.{normalized_store}",
            "event_id": f"eq.{eid}",
        },
    )
    if existing:
        return existing

    return await insert_row(
        NOTIFICATION_LOG_TABLE,
        {
            "store": normalized_store,
            "event_id": eid,
            "event_type": etype,
            "payload": payload,
            "processed": False,
            "error_message": None,
        },
    )


async def mark_store_notification_processed(notification_id: Any, *, processed: bool, error_message: Optional[str] = None) -> Dict[str, Any]:
    patch = {
        "processed": bool(processed),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "error_message": clean_optional_str(error_message),
    }
    return await patch_rows(
        NOTIFICATION_LOG_TABLE,
        filters={"id": f"eq.{notification_id}"},
        patch=patch,
    )
