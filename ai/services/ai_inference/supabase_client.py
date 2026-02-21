# -*- coding: utf-8 -*-
"""supabase_client.py

Shared Supabase HTTP client (Phase 1)
-----------------------------------

Why this exists
  - Many API modules were creating a new ``httpx.AsyncClient`` per request.
    That defeats connection pooling and can cause "sometimes slow" behavior
    due to repeated TLS handshakes and TCP setup.

What this module provides
  - A single, lazily-initialized ``httpx.AsyncClient`` (connection pooled)
  - Small helpers for Supabase PostgREST + RPC calls using service_role
  - Ability to override headers/timeout per request when needed (e.g. /auth/v1/user)

Notes
  - This module does NOT implement auth caching. (That is handled elsewhere.)
  - The client is kept open for the process lifetime. In production (uvicorn),
    this is fine; if you want clean shutdown, call ``aclose_async_client`` on
    app shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("supabase_client")


# --- Env / config ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def ensure_supabase_config() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Supabase configuration missing: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY"
        )


# --- Client singleton ---
_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


def _build_limits() -> httpx.Limits:
    # Conservative defaults; tune via env if needed.
    max_conn = int(os.getenv("SUPABASE_HTTP_MAX_CONNECTIONS", "100") or "100")
    max_keepalive = int(
        os.getenv("SUPABASE_HTTP_MAX_KEEPALIVE_CONNECTIONS", "20") or "20"
    )
    return httpx.Limits(
        max_connections=max(1, max_conn),
        max_keepalive_connections=max(1, max_keepalive),
    )


def _build_timeout() -> httpx.Timeout:
    # Default per-request timeout. Individual calls can override.
    t = float(os.getenv("SUPABASE_HTTP_TIMEOUT_SECONDS", "8.0") or "8.0")
    if t <= 0:
        t = 8.0
    return httpx.Timeout(t)


async def get_async_client() -> httpx.AsyncClient:
    """Return a shared AsyncClient (connection pooled)."""

    global _client
    if _client is not None:
        return _client

    async with _client_lock:
        if _client is None:
            _client = httpx.AsyncClient(
                timeout=_build_timeout(),
                limits=_build_limits(),
            )
        return _client


async def aclose_async_client() -> None:
    """Close the shared AsyncClient (optional)."""

    global _client
    if _client is None:
        return
    try:
        await _client.aclose()
    finally:
        _client = None


# --- Headers helpers ---


def sb_service_role_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    """Headers for Supabase service_role requests (non-JSON)."""
    ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def sb_service_role_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    """Headers for Supabase service_role requests (JSON)."""
    h = sb_service_role_headers(prefer=prefer)
    h["Content-Type"] = "application/json"
    return h


def sb_auth_headers(access_token: str) -> Dict[str, str]:
    """Headers for Supabase Auth endpoints that need the user's access token."""
    ensure_supabase_config()
    tok = str(access_token or "").strip()
    return {
        "Authorization": f"Bearer {tok}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
    }


def _merge_prefer(headers: Dict[str, str], prefer: Optional[str]) -> Dict[str, str]:
    if not prefer:
        return headers
    p0 = str(headers.get("Prefer") or "").strip()
    if not p0:
        headers["Prefer"] = prefer
        return headers
    # Avoid duplicate prefer tokens.
    parts = [x.strip() for x in (p0.split(",") + prefer.split(",")) if x.strip()]
    # Preserve order while deduping.
    seen = set()
    merged = []
    for x in parts:
        if x in seen:
            continue
        merged.append(x)
        seen.add(x)
    headers["Prefer"] = ",".join(merged)
    return headers


# --- Core request helpers ---


async def sb_request(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, str]] = None,
    json: Any = None,
    headers: Optional[Dict[str, str]] = None,
    prefer: Optional[str] = None,
    timeout: Optional[float] = None,
) -> httpx.Response:
    """Send a request to Supabase (base URL + path).

    - ``path`` should start with ``/`` (e.g. ``/rest/v1/profiles``)
    - If ``headers`` is not provided, service_role JSON headers are used.
    """

    ensure_supabase_config()
    p = str(path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    url = f"{SUPABASE_URL}{p}"

    h = dict(headers) if headers else sb_service_role_headers_json()
    h = _merge_prefer(h, prefer)

    client = await get_async_client()
    return await client.request(
        method=str(method or "GET").upper(),
        url=url,
        headers=h,
        params=params,
        json=json,
        timeout=timeout,
    )


async def sb_get(
    path: str,
    *,
    params: Optional[Dict[str, str]] = None,
    prefer: Optional[str] = None,
    timeout: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    return await sb_request(
        "GET",
        path,
        params=params,
        headers=headers,
        prefer=prefer,
        timeout=timeout,
    )


async def sb_post(
    path: str,
    *,
    json: Any,
    params: Optional[Dict[str, str]] = None,
    prefer: Optional[str] = None,
    timeout: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    return await sb_request(
        "POST",
        path,
        params=params,
        json=json,
        headers=headers,
        prefer=prefer,
        timeout=timeout,
    )


async def sb_patch(
    path: str,
    *,
    json: Any,
    params: Optional[Dict[str, str]] = None,
    prefer: Optional[str] = None,
    timeout: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    return await sb_request(
        "PATCH",
        path,
        params=params,
        json=json,
        headers=headers,
        prefer=prefer,
        timeout=timeout,
    )


async def sb_delete(
    path: str,
    *,
    params: Optional[Dict[str, str]] = None,
    prefer: Optional[str] = None,
    timeout: Optional[float] = None,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.Response:
    return await sb_request(
        "DELETE",
        path,
        params=params,
        headers=headers,
        prefer=prefer,
        timeout=timeout,
    )


async def sb_post_rpc(
    fn: str,
    payload: Dict[str, Any],
    *,
    timeout: Optional[float] = None,
) -> httpx.Response:
    """Call a Supabase PostgREST RPC: POST /rest/v1/rpc/<fn>."""

    f = str(fn or "").strip()
    if not f:
        raise ValueError("fn is required")
    return await sb_post(
        f"/rest/v1/rpc/{f}",
        json=payload,
        timeout=timeout,
    )


def _parse_content_range_total(content_range: str) -> Optional[int]:
    # Format: "0-0/123" or "*/123" etc.
    if not content_range:
        return None
    if "/" not in content_range:
        return None
    tail = content_range.split("/")[-1].strip()
    if tail.isdigit():
        return int(tail)
    try:
        return int(tail)
    except Exception:
        return None


async def sb_count(
    path: str,
    *,
    params: Dict[str, str],
    timeout: Optional[float] = None,
) -> int:
    """Return exact row count using PostgREST Content-Range header."""

    resp = await sb_get(
        path,
        params=params,
        prefer="count=exact",
        timeout=timeout,
    )

    if resp.status_code >= 300:
        logger.error("Supabase count failed: %s %s", resp.status_code, resp.text[:800])
        return 0

    cr = resp.headers.get("content-range") or resp.headers.get("Content-Range") or ""
    total = _parse_content_range_total(cr)
    if total is not None:
        return int(total)

    # Fallback: count JSON rows (best-effort)
    try:
        data = resp.json()
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0
