# -*- coding: utf-8 -*-
"""supabase_auth_token_cache.py (Phase 8+++)

目的
- FastAPI middleware で active_users を touch する際、JWT を *未検証デコード* せずに
  Supabase Auth で検証して user_id を取得する。
- リクエスト毎に Supabase へ問い合わせると重いので、短TTLのプロセス内キャッシュで
  通信回数を抑える。

方針
- Supabase Auth: GET /auth/v1/user を使用
  - Authorization: Bearer <access_token>
  - apikey: SUPABASE_ANON_KEY（無ければ SUPABASE_SERVICE_ROLE_KEY を利用）
- キャッシュ:
  - key は access_token の sha256（トークン自体をメモリに保持しない）
  - 正常系/異常系それぞれ TTL を設定可能
  - LRU で上限を超えたら古いものから破棄

ENV
- ACTIVE_USERS_MIDDLEWARE_VERIFY_WITH_SUPABASE (default: true)
- ACTIVE_USERS_MIDDLEWARE_AUTH_CACHE_TTL_SECONDS (default: 60)
- ACTIVE_USERS_MIDDLEWARE_AUTH_NEGATIVE_TTL_SECONDS (default: 10)
- ACTIVE_USERS_MIDDLEWARE_AUTH_CACHE_MAX_SIZE (default: 2048)
- ACTIVE_USERS_MIDDLEWARE_AUTH_TIMEOUT_SECONDS (default: 3.0)

注意
- キャッシュはプロセス内のみ（複数インスタンス/複数ワーカー間では共有されません）。
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Optional, Tuple

import httpx

# Shared HTTP client (connection pooled)
from supabase_client import get_async_client

logger = logging.getLogger("supabase_auth_token_cache")


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


_SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
# Prefer anon key for /auth endpoint; fall back to service role.
_SUPABASE_API_KEY = (
    (os.getenv("SUPABASE_ANON_KEY") or "").strip()
    or (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
)

_VERIFY_ENABLED = _env_truthy("ACTIVE_USERS_MIDDLEWARE_VERIFY_WITH_SUPABASE", True)
_CACHE_TTL = max(0, _env_int("ACTIVE_USERS_MIDDLEWARE_AUTH_CACHE_TTL_SECONDS", 60))
_NEG_TTL = max(0, _env_int("ACTIVE_USERS_MIDDLEWARE_AUTH_NEGATIVE_TTL_SECONDS", 10))
_MAX_SIZE = max(64, _env_int("ACTIVE_USERS_MIDDLEWARE_AUTH_CACHE_MAX_SIZE", 2048))
_TIMEOUT = max(0.5, _env_float("ACTIVE_USERS_MIDDLEWARE_AUTH_TIMEOUT_SECONDS", 3.0))

# LRU cache: key -> (user_id_or_none, expires_at)
_LOCK = threading.Lock()
_CACHE: "OrderedDict[str, Tuple[Optional[str], float]]" = OrderedDict()

# Sentinel to distinguish cache-miss from a cached negative (None)
_MISS = object()


def _digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _cache_get(key: str, now_ts: float):
    with _LOCK:
        ent = _CACHE.get(key)
        if ent is None:
            return _MISS
        user_id, expires_at = ent
        if expires_at <= now_ts:
            try:
                del _CACHE[key]
            except Exception:
                pass
            return _MISS
        try:
            _CACHE.move_to_end(key)
        except Exception:
            pass
        return user_id


def _cache_set(key: str, user_id: Optional[str], expires_at: float) -> None:
    with _LOCK:
        _CACHE[key] = (user_id, expires_at)
        try:
            _CACHE.move_to_end(key)
        except Exception:
            pass
        # Evict LRU
        while len(_CACHE) > _MAX_SIZE:
            try:
                _CACHE.popitem(last=False)
            except Exception:
                break


async def _verify_with_supabase(access_token: str) -> Optional[str]:
    if not _SUPABASE_URL or not _SUPABASE_API_KEY:
        return None

    url = f"{_SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": _SUPABASE_API_KEY,
    }

    try:
        client = await get_async_client()
        resp = await client.get(url, headers=headers, timeout=_TIMEOUT)
    except Exception as exc:
        logger.debug("Supabase auth verify request failed: %s", exc)
        return None

    if resp.status_code != 200:
        # Invalid / expired / revoked token
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    uid = data.get("id")
    if not uid:
        return None

    return str(uid)


async def resolve_user_id_verified_cached(access_token: str) -> Optional[str]:
    """Resolve user_id from a Supabase access token (verified + cached).

    Returns:
        user_id (uuid string) on success, or None.
    """

    tok = str(access_token or "").strip()
    if not tok:
        return None

    if not _VERIFY_ENABLED:
        return None

    now_ts = time.time()
    key = _digest_token(tok)

    cached = _cache_get(key, now_ts)
    if cached is not _MISS:
        # NOTE: cached can be None (negative cache), so we return it.
        return cached

    uid = await _verify_with_supabase(tok)

    ttl = _CACHE_TTL if uid else _NEG_TTL
    expires_at = now_ts + float(ttl)
    _cache_set(key, uid, expires_at)
    return uid
