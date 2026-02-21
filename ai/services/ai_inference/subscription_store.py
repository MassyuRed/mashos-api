# -*- coding: utf-8 -*-
"""subscription_store.py (Step 2)

Subscription tier lookup (Supabase)
----------------------------------

Step 1 defined the tier/mode primitives in :mod:`subscription`.
Step 2 adds the *runtime* lookup of a user's subscription tier.

Current MVP design:
- Store the current tier on `public.profiles.subscription_tier` (text).
- Values: 'free' | 'plus' | 'premium'
- Default: 'free'

Why profiles?
- profiles is already used as the canonical per-user public table
  (display_name / friend_code / myprofile_code etc.).

Fail-closed policy:
- If we cannot look up the tier for any reason, we return FREE.
  This prevents accidental over-entitlement.

Recommended DB migration (Supabase SQL Editor)
---------------------------------------------

```sql
alter table public.profiles
  add column if not exists subscription_tier text not null default 'free';

alter table public.profiles
  add constraint profiles_subscription_tier_check
  check (subscription_tier in ('free','plus','premium'));
```

(You can skip the check constraint initially if you want fast iteration.)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx

from subscription import SubscriptionTier, TierLike, normalize_subscription_tier

# Shared Supabase HTTP client (connection pooled)
from supabase_client import (
    ensure_supabase_config as _ensure_supabase_config_shared,
    sb_auth_headers as _sb_auth_headers_shared,
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_service_role_headers as _sb_headers_shared,
)

logger = logging.getLogger("subscription_store")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Table / column knobs (keep simple for now)
PROFILES_TABLE = os.getenv("COCOLON_SUBSCRIPTION_TABLE", "profiles")
TIER_COLUMN = os.getenv("COCOLON_SUBSCRIPTION_TIER_COLUMN", "subscription_tier")


# In-memory tier cache (best-effort)
# - Speeds up endpoints that call tier lookups multiple times (e.g., QnA list/unread).
# - Process-local (not shared across instances).
TIER_CACHE_TTL_SECONDS = int(os.getenv("COCOLON_SUBSCRIPTION_TIER_CACHE_TTL_SECONDS", "60") or "60")
TIER_CACHE_MAX_ITEMS = int(os.getenv("COCOLON_SUBSCRIPTION_TIER_CACHE_MAX_ITEMS", "5000") or "5000")
_tier_cache: Dict[str, Tuple[float, SubscriptionTier]] = {}


def _tier_cache_get(user_id: str) -> Optional[SubscriptionTier]:
    if int(TIER_CACHE_TTL_SECONDS) <= 0:
        return None
    uid = str(user_id or "").strip()
    if not uid:
        return None
    now = time.time()
    ent = _tier_cache.get(uid)
    if not ent:
        return None
    exp, tier = ent
    if exp <= now:
        _tier_cache.pop(uid, None)
        return None
    return tier


def _tier_cache_set(user_id: str, tier: SubscriptionTier) -> None:
    if int(TIER_CACHE_TTL_SECONDS) <= 0:
        return
    uid = str(user_id or "").strip()
    if not uid:
        return
    # Simple bound to avoid unbounded memory (safe for MVP).
    if int(TIER_CACHE_MAX_ITEMS) > 0 and len(_tier_cache) >= int(TIER_CACHE_MAX_ITEMS):
        _tier_cache.clear()
    _tier_cache[uid] = (time.time() + float(int(TIER_CACHE_TTL_SECONDS)), tier)


def _ensure_supabase_config() -> None:
    # Delegate to the shared config check (single source of truth)
    _ensure_supabase_config_shared()


def _sb_headers() -> Dict[str, str]:
    return _sb_headers_shared()


async def _fetch_profile_row(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single profile row for the given user id.

    Returns dict row or None.
    """
    _ensure_supabase_config()
    uid = str(user_id or "").strip()
    if not uid:
        return None

    params = {
        # Keep '*' to be schema-tolerant (column might not exist in some envs).
        "select": "*",
        "id": f"eq.{uid}",
        "limit": "1",
    }

    try:
        resp = await _sb_get_shared(
            f"/rest/v1/{PROFILES_TABLE}",
            params=params,
            headers=_sb_headers(),
            timeout=5.0,
        )
    except Exception as exc:
        logger.warning("Supabase profile fetch failed (network): %s", exc)
        return None

    if resp.status_code >= 300:
        logger.warning(
            "Supabase profile fetch failed: status=%s body=%s",
            resp.status_code,
            resp.text[:800],
        )
        return None

    try:
        rows = resp.json()
    except Exception:
        logger.warning("Supabase profile fetch returned non-JSON")
        return None

    if isinstance(rows, list) and rows:
        row0 = rows[0]
        return row0 if isinstance(row0, dict) else None

    if isinstance(rows, dict):
        return rows

    return None


async def get_subscription_tier_for_user(user_id: str, *, default: SubscriptionTier = SubscriptionTier.FREE) -> SubscriptionTier:
    """Return the user's subscription tier.

    - Reads `public.profiles.subscription_tier`.
    - Unknown/missing → default (FREE).

    This is intentionally fail-closed.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return default

    cached = _tier_cache_get(uid)
    if cached is not None:
        return cached

    row = await _fetch_profile_row(uid)
    if not row:
        _tier_cache_set(uid, default)
        return default

    raw = row.get(TIER_COLUMN)
    tier = normalize_subscription_tier(raw, default=default)
    _tier_cache_set(uid, tier)
    return tier


async def get_subscription_tier_from_access_token(
    access_token: str,
    *,
    default: SubscriptionTier = SubscriptionTier.FREE,
) -> SubscriptionTier:
    """Convenience: resolve user id from Supabase access token, then return tier.

    This mirrors existing code that uses Supabase Auth `/auth/v1/user`.
    """
    _ensure_supabase_config()
    tok = str(access_token or "").strip()
    if not tok:
        return default

    try:
        resp = await _sb_get_shared(
            "/auth/v1/user",
            headers=_sb_auth_headers_shared(tok),
            timeout=5.0,
        )
    except Exception as exc:
        logger.warning("Supabase auth user lookup failed (network): %s", exc)
        return default

    if resp.status_code != 200:
        logger.warning(
            "Supabase auth user lookup failed: status=%s body=%s",
            resp.status_code,
            resp.text[:800],
        )
        return default

    try:
        data = resp.json()
    except Exception:
        return default

    uid = str(data.get("id") or "").strip()
    if not uid:
        return default

    return await get_subscription_tier_for_user(uid, default=default)


# -----------------
# Tier update (IAP)
# -----------------


async def _patch_profile_row(user_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """PATCH a single profile row.

    Uses Supabase PostgREST with service_role.
    Returns the updated row (dict) when possible.
    """
    _ensure_supabase_config()
    uid = str(user_id or "").strip()
    if not uid:
        return None

    params = {"id": f"eq.{uid}"}
    headers = {
        **_sb_headers(),
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    try:
        resp = await _sb_patch_shared(
            f"/rest/v1/{PROFILES_TABLE}",
            params=params,
            json=patch,
            headers=headers,
            timeout=6.0,
        )
    except Exception as exc:
        logger.warning("Supabase profile update failed (network): %s", exc)
        return None

    if resp.status_code >= 300:
        logger.warning(
            "Supabase profile update failed: status=%s body=%s",
            resp.status_code,
            resp.text[:1200],
        )
        return None

    try:
        data = resp.json()
    except Exception:
        # Some PostgREST configs may return empty body.
        return {}

    if isinstance(data, list) and data:
        row0 = data[0]
        return row0 if isinstance(row0, dict) else {}
    if isinstance(data, dict):
        return data
    return {}


async def set_subscription_tier_for_user(
    user_id: str,
    tier: TierLike,
    *,
    default: SubscriptionTier = SubscriptionTier.FREE,
) -> SubscriptionTier:
    """Update a user's subscription tier in `public.profiles`.

    Notes:
    - Uses service_role key, so RLS will be bypassed.
    - Returns the normalized tier that was requested.
    - Raises RuntimeError on failure (network / schema / permission).

    This function intentionally does NOT do purchase verification.
    Verification should be handled at the API layer (or upstream service).
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    t = normalize_subscription_tier(tier, default=default)

    # PATCH profiles where id == user_id
    updated = await _patch_profile_row(uid, {TIER_COLUMN: t.value})
    if updated is None:
        raise RuntimeError(
            "Failed to update subscription tier in Supabase. "
            "Ensure public.profiles has column 'subscription_tier' and SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are set."
        )

    _tier_cache_set(uid, t)

    return t
