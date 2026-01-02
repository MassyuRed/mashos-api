# -*- coding: utf-8 -*-
"""generation_lock.py

Phase10: 競合対策（同時実行の防止）
----------------------------------

目的
- Cron や on-demand ensure が同時に走ったとき、同じ user_id / 同じ期間 のレポート生成が
  重複実行される（= 生成コストが無駄に走る）問題を抑える。

実装
- Supabase(Postgres) に "generation_locks" テーブルを用意し、
  "insert できた人がロック獲得" 方式で排他する。
- ロックは TTL(expires_at) を持ち、クラッシュ等で release されなくても自然に回復できる。

このモジュールは FastAPI の on-demand / cron の双方から呼ばれる。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, TypeVar

import httpx
from fastapi import HTTPException

from api_emotion_submit import _ensure_supabase_config

# Phase11: observability (structured logs)
try:
    from observability import elapsed_ms, log_event, log_alert, monotonic_ms
except Exception:  # pragma: no cover
    def monotonic_ms() -> float:  # type: ignore
        import time as _time
        return _time.monotonic() * 1000.0

    def elapsed_ms(start_ms: float) -> int:  # type: ignore
        import time as _time
        try:
            return int(max(0.0, (_time.monotonic() * 1000.0) - float(start_ms)))
        except Exception:
            return 0

    def log_event(_logger, _event: str, *, level: str = "info", **_fields):  # type: ignore
        try:
            getattr(_logger, level, _logger.info)(f"{_event} {_fields}")
        except Exception:
            pass

    def log_alert(_logger, _key: str, *, level: str = "warning", **_fields):  # type: ignore
        try:
            getattr(_logger, level, _logger.warning)(f"ALERT::{_key} {_fields}")
        except Exception:
            pass



logger = logging.getLogger("generation_lock")

# Phase11: Supabase HTTP instrumentation
OBS_LOG_SUPABASE_HTTP = (os.getenv("OBS_LOG_SUPABASE_HTTP", "true").strip().lower() != "false")
OBS_SUPABASE_SLOW_THRESHOLD_MS = int(os.getenv("OBS_SUPABASE_SLOW_THRESHOLD_MS", "1500") or "1500")


SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

LOCKS_TABLE = (
    os.getenv("GENERATION_LOCKS_TABLE")
    or os.getenv("REPORT_GENERATION_LOCKS_TABLE")
    or "generation_locks"
).strip() or "generation_locks"

LOCKS_ENABLED = (os.getenv("GENERATION_LOCK_ENABLED", "true").strip().lower() != "false")

# Defaults (can be overridden per-call)
DEFAULT_TTL_SECONDS = int(os.getenv("GENERATION_LOCK_TTL_SECONDS", "180") or "180")
DEFAULT_POLL_INTERVAL_SECONDS = float(os.getenv("GENERATION_LOCK_POLL_INTERVAL_SECONDS", "0.5") or "0.5")


T = TypeVar("T")


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse_iso_dt(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        s = str(iso).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    params: Optional[Dict[str, str]] = None,
    json_body: Any = None,
    op: str = "",
) -> httpx.Response:
    start_ms = monotonic_ms()
    try:
        resp = await client.request(method, url, headers=headers, params=params, json=json_body)
        dur = elapsed_ms(start_ms)
        if OBS_LOG_SUPABASE_HTTP:
            lvl = "info"
            if resp.status_code >= 500 or dur >= OBS_SUPABASE_SLOW_THRESHOLD_MS:
                lvl = "warning"
            log_event(
                logger,
                "supabase_http",
                level=lvl,
                op=(op or None),
                method=method,
                path=url,
                status_code=resp.status_code,
                duration_ms=dur,
                component="generation_lock",
            )

            if resp.status_code >= 500:
                log_alert(
                    logger,
                    "SUPABASE_HTTP_5XX",
                    level="warning",
                    op=(op or None),
                    method=method,
                    path=url,
                    status_code=resp.status_code,
                    duration_ms=dur,
                    component="generation_lock",
                )
            elif resp.status_code == 429:
                log_alert(
                    logger,
                    "SUPABASE_HTTP_429",
                    level="warning",
                    op=(op or None),
                    method=method,
                    path=url,
                    status_code=resp.status_code,
                    duration_ms=dur,
                    component="generation_lock",
                )
        return resp
    except httpx.TimeoutException as exc:
        dur = elapsed_ms(start_ms)
        log_event(
            logger,
            "supabase_timeout",
            level="error",
            op=(op or None),
            method=method,
            path=url,
            duration_ms=dur,
            component="generation_lock",
            error=str(exc),
        )
        log_alert(
            logger,
            "SUPABASE_TIMEOUT",
            level="error",
            op=(op or None),
            method=method,
            path=url,
            duration_ms=dur,
            component="generation_lock",
        )
        raise
    except httpx.RequestError as exc:
        dur = elapsed_ms(start_ms)
        log_event(
            logger,
            "supabase_request_error",
            level="error",
            op=(op or None),
            method=method,
            path=url,
            duration_ms=dur,
            component="generation_lock",
            error=str(exc),
            exc_type=type(exc).__name__,
        )
        log_alert(
            logger,
            "SUPABASE_REQUEST_ERROR",
            level="error",
            op=(op or None),
            method=method,
            path=url,
            duration_ms=dur,
            component="generation_lock",
            exc_type=type(exc).__name__,
        )
        raise


def build_lock_key(
    *,
    namespace: str,
    user_id: str,
    report_type: str,
    period_start: str,
    period_end: str,
) -> str:
    """Build a stable short lock key.

    We store details in context_json separately to avoid very long primary keys.
    """
    raw = f"{namespace}|{user_id}|{report_type}|{period_start}|{period_end}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    ns = (namespace or "gen").replace(":", "_")
    return f"{ns}:{digest}"  # text PK


def make_owner_id(prefix: str = "mashos") -> str:
    """Best-effort owner id (for debugging)."""
    seed = f"{prefix}:{os.getpid()}:{time.time_ns()}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()[:16]


@dataclass(frozen=True)
class LockAcquireResult:
    acquired: bool
    lock_key: str
    owner_id: str
    expires_at: str


async def try_acquire_lock(
    *,
    lock_key: str,
    ttl_seconds: Optional[int] = None,
    owner_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    timeout_seconds: float = 4.0,
) -> LockAcquireResult:
    """Try to acquire a generation lock.

    Algorithm:
    1) INSERT new lock row. If success => acquired.
    2) If conflict:
       - If existing lock is expired: DELETE (where expires_at < now) then retry INSERT once.
       - Otherwise => not acquired.

    This keeps the core operation compatible with PostgREST (no custom RPC required).
    """
    if not LOCKS_ENABLED:
        return LockAcquireResult(acquired=True, lock_key=lock_key, owner_id=owner_id or "disabled", expires_at=_iso_z(datetime.now(timezone.utc)))

    _ensure_supabase_config()
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Supabase URL is not configured")

    owner = (owner_id or make_owner_id("lock")).strip() or make_owner_id("lock")
    ttl = int(ttl_seconds or DEFAULT_TTL_SECONDS)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=max(1, ttl))
    expires_iso = _iso_z(expires)

    url = f"{SUPABASE_URL}/rest/v1/{LOCKS_TABLE}"
    payload = {
        "lock_key": lock_key,
        "owner_id": owner,
        "acquired_at": _iso_z(now),
        "expires_at": expires_iso,
        "context": context or {},
    }

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        # 1) try insert
        resp = await _sb_request(
            client,
            "POST",
            url,
            headers=_sb_headers(prefer="return=minimal"),
            json_body=payload,
            op="lock_insert",
        )
        if resp.status_code in (200, 201, 204):
            return LockAcquireResult(acquired=True, lock_key=lock_key, owner_id=owner, expires_at=expires_iso)

        # If not a conflict, treat as non-acquired (do not break main flow)
        if resp.status_code not in (400, 409):
            logger.warning(
                "Lock insert failed (non-conflict): %s %s",
                resp.status_code,
                resp.text[:800],
            )
            return LockAcquireResult(acquired=False, lock_key=lock_key, owner_id=owner, expires_at=expires_iso)

        # 2) conflict path: check if expired
        resp2 = await _sb_request(
            client,
            "GET",
            url,
            headers=_sb_headers(),
            params={
                "select": "expires_at,owner_id",
                "lock_key": f"eq.{lock_key}",
                "limit": "1",
            },
            op="lock_select",
        )
        if resp2.status_code == 200:
            rows = resp2.json()
            if isinstance(rows, list) and rows:
                expires_at = _parse_iso_dt(rows[0].get("expires_at"))
                if expires_at and expires_at < now:
                    # Delete expired lock (best-effort)
                    try:
                        _ = await _sb_request(
                            client,
                            "DELETE",
                            url,
                            headers=_sb_headers(prefer="return=minimal"),
                            params={
                                "lock_key": f"eq.{lock_key}",
                                "expires_at": f"lt.{_iso_z(now)}",
                            },
                            op="lock_delete_expired",
                        )
                    except Exception:
                        pass
                    # Retry insert once
                    resp3 = await _sb_request(
                        client,
                        "POST",
                        url,
                        headers=_sb_headers(prefer="return=minimal"),
                        json_body=payload,
                        op="lock_insert_retry",
                    )
                    if resp3.status_code in (200, 201, 204):
                        return LockAcquireResult(
                            acquired=True,
                            lock_key=lock_key,
                            owner_id=owner,
                            expires_at=expires_iso,
                        )

        return LockAcquireResult(acquired=False, lock_key=lock_key, owner_id=owner, expires_at=expires_iso)


async def release_lock(
    *,
    lock_key: str,
    owner_id: Optional[str] = None,
    timeout_seconds: float = 4.0,
) -> None:
    """Release lock (best-effort)."""
    if not LOCKS_ENABLED:
        return
    _ensure_supabase_config()
    if not SUPABASE_URL:
        return

    url = f"{SUPABASE_URL}/rest/v1/{LOCKS_TABLE}"
    params: Dict[str, str] = {"lock_key": f"eq.{lock_key}"}
    if owner_id:
        params["owner_id"] = f"eq.{owner_id}"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await _sb_request(
                client,
                "DELETE",
                url,
                headers=_sb_headers(prefer="return=minimal"),
                params=params,
                op="lock_release",
            )
        if resp.status_code not in (200, 204):
            logger.debug("Lock release non-2xx: %s %s", resp.status_code, resp.text[:500])
    except Exception as exc:
        logger.debug("Lock release failed: %s", exc)


async def poll_until(
    fn: Callable[[], Awaitable[Optional[T]]],
    *,
    timeout_seconds: float,
    interval_seconds: Optional[float] = None,
) -> Optional[T]:
    """Poll async fn until it returns a truthy value (or timeout)."""
    interval = float(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS)
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        try:
            v = await fn()
            if v is not None:
                return v
        except Exception:
            # polling should be best-effort
            pass
        if time.monotonic() >= deadline:
            return None
        await asyncio.sleep(max(0.05, interval))
