# -*- coding: utf-8 -*-
"""active_users_store.py (Phase 8+)

Active users table (Cron optimization)
-------------------------------------

目的:
- Cron が profiles を全走査して重くなるのを防ぐため、"直近アクティブ" なユーザーだけを
  バッチ対象にできるようにする。
- Phase8+ では subscription_tier も active_users にキャッシュして、Cron が tier 判定のために
  profiles を参照する回数を減らす。

設計:
- 失敗しても本処理を壊さない：touch は best-effort（例外は握りつぶす）
- DB は service_role で書く（RLS をバイパス）
- 書き込み頻度をスロットルして負荷を抑える（プロセス内・ユーザー単位）
- tier は必要に応じて profiles から best-effort で取得し、短いTTLでキャッシュする

必要ENV:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY

任意ENV:
- COCOLON_ACTIVE_USERS_TABLE (default: active_users)
- ACTIVE_USERS_TRACKING_ENABLED (default: true)
- ACTIVE_USERS_TOUCH_MIN_INTERVAL_SECONDS (default: 60)
- ACTIVE_USERS_TOUCH_TIMEOUT_SECONDS (default: 3.5)
- ACTIVE_USERS_INCLUDE_SUBSCRIPTION_TIER (default: true)
- ACTIVE_USERS_TIER_CACHE_TTL_SECONDS (default: 3600)
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

# Shared Supabase HTTP client (connection pooled)
from supabase_client import (
    sb_post as _sb_post_shared,
    sb_service_role_headers_json as _sb_headers_json_shared,
)

logger = logging.getLogger("active_users_store")

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()


def _env_truthy(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(str(raw).strip())
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(str(raw).strip())
    except Exception:
        return default


ACTIVE_USERS_TABLE = (os.getenv("COCOLON_ACTIVE_USERS_TABLE") or "active_users").strip() or "active_users"
ACTIVE_USERS_TRACKING_ENABLED = _env_truthy("ACTIVE_USERS_TRACKING_ENABLED", True)
ACTIVE_USERS_TOUCH_MIN_INTERVAL_SECONDS = max(0, _env_int("ACTIVE_USERS_TOUCH_MIN_INTERVAL_SECONDS", 60))
ACTIVE_USERS_TOUCH_TIMEOUT_SECONDS = max(0.5, _env_float("ACTIVE_USERS_TOUCH_TIMEOUT_SECONDS", 3.5))
ACTIVE_USERS_INCLUDE_SUBSCRIPTION_TIER = _env_truthy("ACTIVE_USERS_INCLUDE_SUBSCRIPTION_TIER", True)
ACTIVE_USERS_TIER_CACHE_TTL_SECONDS = max(0, _env_int("ACTIVE_USERS_TIER_CACHE_TTL_SECONDS", 3600))

# Process-local caches
_LOCK = threading.Lock()
_LAST_TOUCH_AT: Dict[str, float] = {}
_TIER_CACHE: Dict[str, Tuple[str, float]] = {}

# Optional imports (fail-open)
try:
    from subscription_store import get_subscription_tier_for_user  # type: ignore
except Exception:  # pragma: no cover
    get_subscription_tier_for_user = None  # type: ignore

try:
    from subscription import normalize_subscription_tier  # type: ignore
except Exception:  # pragma: no cover
    normalize_subscription_tier = None  # type: ignore


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    # Keep legacy helper but delegate to shared header builder.
    return _sb_headers_json_shared(prefer=prefer)


def _normalize_tier(raw: Optional[str]) -> str:
    s = str(raw or "").strip().lower()

    # If we have the project helper, use it (returns SubscriptionTier enum)
    if normalize_subscription_tier is not None:
        try:
            t = normalize_subscription_tier(s)  # type: ignore
            v = getattr(t, "value", None)
            if isinstance(v, str) and v:
                return v
            # Fallback for unexpected return type
            s2 = str(t).strip().lower()
            if s2 in ("free", "plus", "premium"):
                return s2
        except Exception:
            pass

    if s in ("free", "plus", "premium"):
        return s
    return "free"


async def _get_tier_cached(user_id: str, now_ts: float) -> str:
    """Best-effort tier lookup with a process-local TTL cache."""

    ttl = ACTIVE_USERS_TIER_CACHE_TTL_SECONDS
    if ttl > 0:
        with _LOCK:
            ent = _TIER_CACHE.get(user_id)
        if ent is not None:
            tier, cached_at = ent
            if now_ts - cached_at < ttl:
                return tier

    tier = "free"
    if get_subscription_tier_for_user is not None:
        try:
            t = await get_subscription_tier_for_user(user_id)  # type: ignore
            tier = getattr(t, "value", str(t))
        except Exception:
            tier = "free"

    tier = _normalize_tier(tier)
    with _LOCK:
        _TIER_CACHE[user_id] = (tier, now_ts)
    return tier


async def touch_active_user(
    user_id: str,
    *,
    activity: str = "unknown",
    at: Optional[datetime] = None,
    subscription_tier: Optional[str] = None,
    force: bool = False,
) -> None:
    """Upsert a row into active_users.

    Best-effort:
    - Any error is logged and swallowed.

    Notes:
    - `force=True` bypasses per-user min-interval throttling.
    - `subscription_tier` can be provided to avoid a profiles lookup and to refresh the cache immediately.
    """

    if not ACTIVE_USERS_TRACKING_ENABLED:
        return

    uid = str(user_id or "").strip()
    if not uid:
        return

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        # Fail-open: do nothing if config is missing.
        return

    now_ts = time.time()
    if not force and ACTIVE_USERS_TOUCH_MIN_INTERVAL_SECONDS > 0:
        with _LOCK:
            prev = _LAST_TOUCH_AT.get(uid)
            if prev is not None and (now_ts - prev) < float(ACTIVE_USERS_TOUCH_MIN_INTERVAL_SECONDS):
                return
            _LAST_TOUCH_AT[uid] = now_ts

    dt = at or datetime.now(timezone.utc)
    ts = _iso_z(dt)

    payload: Dict[str, Any] = {
        "user_id": uid,
        "last_active_at": ts,
        "last_activity": str(activity or "unknown")[:80],
        "last_activity_at": ts,
    }

    if ACTIVE_USERS_INCLUDE_SUBSCRIPTION_TIER:
        if subscription_tier is not None:
            tier = _normalize_tier(subscription_tier)
            with _LOCK:
                _TIER_CACHE[uid] = (tier, now_ts)
        else:
            tier = await _get_tier_cached(uid, now_ts)
        payload["subscription_tier"] = tier
        payload["subscription_tier_updated_at"] = ts

    params = {"on_conflict": "user_id"}

    try:
        resp = await _sb_post_shared(
            f"/rest/v1/{ACTIVE_USERS_TABLE}",
            params=params,
            json=payload,
            prefer="resolution=merge-duplicates,return=minimal",
            timeout=ACTIVE_USERS_TOUCH_TIMEOUT_SECONDS,
        )

        if resp.status_code not in (200, 201, 204):
            logger.warning(
                "active_users upsert failed: status=%s body=%s",
                resp.status_code,
                (resp.text or "")[:300],
            )

    except Exception as exc:
        logger.warning("active_users upsert failed (network/exception): %s", exc)
