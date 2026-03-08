# -*- coding: utf-8 -*-
"""Ranking API for Cocolon (MashOS / FastAPI)

Endpoints (Phase: ranking feature)
--------------------------------
- GET /ranking/emotions?range=week
- GET /ranking/emotions/self?range=week
- GET /ranking/input_count?range=week&limit=30
- GET /ranking/input_length?range=week&limit=30
- GET /ranking/mymodel_used?range=week&limit=30
- GET /ranking/login_streak?range=week&limit=30

Notes
-----
* Requires Supabase Auth access token via Authorization: Bearer <access_token>
* Uses Supabase PostgREST RPC (service role) to call SQL functions:
  - rank_emotions(p_range)
  - rank_user_emotions(p_user_id, p_range)
  - rank_input_count(p_range, p_limit)
  - rank_input_length(p_range, p_limit)
  - rank_mymodel_used(p_range, p_limit)
  - rank_login_streak(p_range, p_limit)
* Timezone / boundary: JST (Asia/Tokyo) at 00:00, handled in SQL.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)

from api_ranking import _filter_rows_by_ranking_visibility, _rpc as _rpc_shared
from astor_ranking_boards import fetch_latest_ready_ranking_board, select_board_rows


logger = logging.getLogger("ranking_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
VISIBILITY_TABLE = (
    os.getenv("COCOLON_VISIBILITY_SETTINGS_TABLE", "account_visibility_settings")
    or "account_visibility_settings"
).strip() or "account_visibility_settings"


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_post(path: str, *, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.post(url, headers=_sb_headers_json(prefer=prefer), json=json)


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.get(url, headers=_sb_headers_json(), params=params)


async def _require_user_id(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return await _resolve_user_id_from_token(token)



def _normalize_range(v: Optional[str]) -> str:
    s = str(v or "").strip()
    if not s:
        return "week"
    s_lower = s.lower()
    allowed = {"day", "week", "month", "year", "日", "週", "月", "年"}
    if s_lower in allowed:
        return s_lower
    if s in allowed:
        return s
    raise HTTPException(status_code=400, detail="Invalid range. Use day/week/month/year (or 日/週/月/年).")



def _normalize_limit(v: Optional[int], *, default: int = 30, min_v: int = 1, max_v: int = 100) -> int:
    if v is None:
        return default
    try:
        n = int(v)
    except Exception:
        return default
    if n < min_v:
        return min_v
    if n > max_v:
        return max_v
    return n


async def _rpc(fn: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    resp = await _sb_post(f"/rest/v1/rpc/{fn}", json=payload)
    if resp.status_code >= 300:
        logger.error("Supabase rpc %s failed: %s %s", fn, resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to fetch ranking")
    data = resp.json()
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


async def _fetch_profiles_map(user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return {}
    # PostgREST in.(...) expects comma separated values.
    in_list = ",".join(ids)
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name",
            "id": f"in.({in_list})",
        },
    )
    if resp.status_code >= 300:
        logger.warning("Supabase profiles fetch failed: %s %s", resp.status_code, resp.text[:800])
        return {}
    rows = resp.json()
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("id") or "").strip()
            if not rid:
                continue
            out[rid] = r
    return out


async def _fetch_private_account_map(user_ids: List[str]) -> Dict[str, bool]:
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return {}

    out: Dict[str, bool] = {uid: False for uid in ids}
    chunk_size = 200

    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        in_list = ",".join(chunk)
        resp = await _sb_get(
            f"/rest/v1/{VISIBILITY_TABLE}",
            params={
                "select": "user_id,is_private_account",
                "user_id": f"in.({in_list})",
            },
        )
        if resp.status_code >= 300:
            logger.warning(
                "Supabase %s fetch failed (private map): %s %s",
                VISIBILITY_TABLE,
                resp.status_code,
                (resp.text or "")[:800],
            )
            continue

        rows = resp.json()
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                uid = str(r.get("user_id") or "").strip()
                if not uid:
                    continue
                out[uid] = bool(r.get("is_private_account") or False)

    return out


async def _fetch_ready_board_rows(metric_key: str, range_key: str) -> Optional[List[Dict[str, Any]]]:
    try:
        board = await fetch_latest_ready_ranking_board(metric_key)
    except Exception as exc:
        logger.warning("ranking board fetch failed: metric=%s err=%s", metric_key, exc)
        return None
    if not board:
        return None
    try:
        rows = select_board_rows(board, range_key)
    except Exception as exc:
        logger.warning(
            "ranking board row selection failed: metric=%s range=%s err=%s",
            metric_key,
            range_key,
            exc,
        )
        return None
    return [r for r in rows if isinstance(r, dict)]



def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        return int(default)



def _coerce_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None



def _pick_streak_days(row: Dict[str, Any]) -> int:
    for key in ("streak_days", "streak", "days", "value"):
        if row.get(key) is not None:
            return _coerce_int(row.get(key), 0)
    return 0



def _pick_last_login_date(row: Dict[str, Any]) -> Optional[str]:
    for key in ("last_login_date", "last_date"):
        if row.get(key) is not None:
            return _coerce_text(row.get(key))
    return None


async def _publish_login_streak_items(rows: List[Dict[str, Any]], *, limit: int) -> List[Dict[str, Any]]:
    raw_rows = [dict(r) for r in (rows or []) if isinstance(r, dict)]
    if not raw_rows:
        return []

    filtered = await _filter_rows_by_ranking_visibility(raw_rows)
    if not filtered:
        return []

    user_ids = [str((r or {}).get("user_id") or "").strip() for r in filtered]
    user_ids = [uid for uid in user_ids if uid]
    profiles = await _fetch_profiles_map(user_ids)
    private_map = await _fetch_private_account_map(user_ids)

    items: List[Dict[str, Any]] = []
    for r in filtered:
        if not isinstance(r, dict):
            continue
        uid = str(r.get("user_id") or "").strip()
        if not uid:
            continue

        rank = _coerce_int(r.get("rank"), len(items) + 1)
        streak_days = _pick_streak_days(r)
        last_login_date = _pick_last_login_date(r)
        prof = profiles.get(uid) if isinstance(profiles.get(uid), dict) else {}
        is_private = bool(private_map.get(uid, bool(r.get("is_private_account") or False)))

        items.append(
            {
                "rank": rank,
                "user_id": uid,
                "display_name": _coerce_text((prof or {}).get("display_name")),
                "is_private_account": is_private,
                "streak_days": streak_days,
                "last_login_date": last_login_date,
                "value": streak_days,
            }
        )

    items.sort(key=lambda x: int(x.get("rank") or 0))
    return items[: max(1, int(limit or 30))]


async def _build_login_streak_response(*, p_range: str, p_limit: int) -> Dict[str, Any]:
    try:
        board_rows = await _fetch_ready_board_rows("login_streak", p_range)
        if board_rows is not None:
            items = await _publish_login_streak_items(board_rows, limit=p_limit)
            return {
                "status": "ok",
                "range": p_range,
                "timezone": "Asia/Tokyo",
                "limit": p_limit,
                "items": items,
            }
    except Exception as exc:
        logger.warning("ranking board publish failed: metric=login_streak range=%s err=%s", p_range, exc)

    rows = await _rpc_shared("rank_login_streak", {"p_range": p_range, "p_limit": p_limit})
    items = await _publish_login_streak_items(rows, limit=p_limit)
    return {
        "status": "ok",
        "range": p_range,
        "timezone": "Asia/Tokyo",
        "limit": p_limit,
        "items": items,
    }


def register_ranking_routes(app: FastAPI) -> None:
    """Register ranking endpoints on the given FastAPI app."""

    @app.get("/ranking/emotions")
    async def ranking_emotions(
        range: str = Query(default="week"),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        # Auth required (prevents public scraping)
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        rows = await _rpc("rank_emotions", {"p_range": p_range})
        items: List[Dict[str, Any]] = []
        for r in rows:
            emotion = str(r.get("emotion") or "").strip()
            count = int(r.get("count") or 0)
            rank = int(r.get("rank") or 0)
            items.append({"rank": rank, "emotion": emotion, "count": count, "value": count})
        return {"status": "ok", "range": p_range, "timezone": "Asia/Tokyo", "items": items}

    @app.get("/ranking/emotions/self")
    async def ranking_emotions_self(
        range: str = Query(default="week"),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        user_id = await _require_user_id(authorization)
        p_range = _normalize_range(range)
        rows = await _rpc("rank_user_emotions", {"p_user_id": user_id, "p_range": p_range})
        items: List[Dict[str, Any]] = []
        for r in rows:
            emotion = str(r.get("emotion") or "").strip()
            count = int(r.get("count") or 0)
            rank = int(r.get("rank") or 0)
            items.append({"rank": rank, "emotion": emotion, "count": count, "value": count})
        return {"status": "ok", "range": p_range, "timezone": "Asia/Tokyo", "items": items}

    @app.get("/ranking/input_count")
    async def ranking_input_count(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)
        rows = await _rpc("rank_input_count", {"p_range": p_range, "p_limit": p_limit})
        user_ids = [str(r.get("user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles = await _fetch_profiles_map(user_ids)
        items: List[Dict[str, Any]] = []
        for r in rows:
            uid = str(r.get("user_id") or "").strip()
            rank = int(r.get("rank") or 0)
            cnt = int(r.get("input_count") or 0)
            prof = profiles.get(uid) or {}
            items.append(
                {
                    "rank": rank,
                    "user_id": uid,
                    "display_name": prof.get("display_name"),
                    "input_count": cnt,
                    "value": cnt,
                }
            )
        return {"status": "ok", "range": p_range, "timezone": "Asia/Tokyo", "limit": p_limit, "items": items}

    @app.get("/ranking/input_length")
    async def ranking_input_length(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)
        rows = await _rpc("rank_input_length", {"p_range": p_range, "p_limit": p_limit})
        user_ids = [str(r.get("user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles = await _fetch_profiles_map(user_ids)
        items: List[Dict[str, Any]] = []
        for r in rows:
            uid = str(r.get("user_id") or "").strip()
            rank = int(r.get("rank") or 0)
            chars = int(r.get("total_chars") or 0)
            prof = profiles.get(uid) or {}
            items.append(
                {
                    "rank": rank,
                    "user_id": uid,
                    "display_name": prof.get("display_name"),
                    "total_chars": chars,
                    "value": chars,
                }
            )
        return {"status": "ok", "range": p_range, "timezone": "Asia/Tokyo", "limit": p_limit, "items": items}

    @app.get("/ranking/mymodel_used")
    async def ranking_mymodel_used(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)
        rows = await _rpc("rank_mymodel_used", {"p_range": p_range, "p_limit": p_limit})
        user_ids = [str(r.get("user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles = await _fetch_profiles_map(user_ids)
        items: List[Dict[str, Any]] = []
        for r in rows:
            uid = str(r.get("user_id") or "").strip()
            rank = int(r.get("rank") or 0)
            used = int(r.get("used_count") or 0)
            prof = profiles.get(uid) or {}
            items.append(
                {
                    "rank": rank,
                    "user_id": uid,
                    "display_name": prof.get("display_name"),
                    "used_count": used,
                    "value": used,
                }
            )
        return {"status": "ok", "range": p_range, "timezone": "Asia/Tokyo", "limit": p_limit, "items": items}

    @app.get("/ranking/login_streak")
    async def ranking_login_streak(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)
        return await _build_login_streak_response(p_range=p_range, p_limit=p_limit)



def register_ranking_login_streak_routes(app: FastAPI) -> None:
    """Register only /ranking/login_streak endpoint.

    This avoids duplicating other /ranking/* routes when app.py conditionally
    adds login_streak.
    """

    @app.get("/ranking/login_streak")
    async def ranking_login_streak(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)
        return await _build_login_streak_response(p_range=p_range, p_limit=p_limit)
