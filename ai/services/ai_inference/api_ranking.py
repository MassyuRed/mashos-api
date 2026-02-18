# -*- coding: utf-8 -*-
"""Ranking API for Cocolon (MashOS / FastAPI)

Endpoints (Phase: ranking feature)
--------------------------------
- GET /ranking/emotions?range=week
- GET /ranking/emotions/self?range=week
- GET /ranking/input_count?range=week&limit=30
- GET /ranking/input_length?range=week&limit=30
- GET /ranking/mymodel_used?range=week&limit=30

Notes
-----
* Requires Supabase Auth access token via Authorization: Bearer <access_token>
* Uses Supabase PostgREST RPC (service role) to call SQL functions:
  - rank_emotions(p_range)
  - rank_user_emotions(p_user_id, p_range)
  - rank_input_count(p_range, p_limit)
  - rank_input_length(p_range, p_limit)
  - rank_mymodel_used(p_range, p_limit)
* Timezone / boundary: JST (Asia/Tokyo) at 00:00, handled in SQL.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, Header, HTTPException, Query

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)


logger = logging.getLogger("ranking_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


VISIBILITY_TABLE = (os.getenv("COCOLON_VISIBILITY_SETTINGS_TABLE", "account_visibility_settings") or "account_visibility_settings").strip()

# MyModel Create (template Q&A) answers table. Used for input_count / input_length aggregation.
MYMODEL_CREATE_ANSWERS_TABLE = (
    os.getenv("COCOLON_MYMODEL_CREATE_ANSWERS_TABLE", "mymodel_create_answers") or "mymodel_create_answers"
).strip() or "mymodel_create_answers"

_JST = ZoneInfo("Asia/Tokyo")


def _canonical_range(v: str) -> str:
    s = str(v or "").strip()
    if s in ("日",):
        return "day"
    if s in ("週",):
        return "week"
    if s in ("月",):
        return "month"
    if s in ("年",):
        return "year"
    return s or "week"


def _range_since_iso(*, p_range: str) -> Optional[str]:
    """Return UTC ISO string (Z) for the start boundary of the given range.

    Boundary is JST 00:00.
    - day  : today 00:00 JST
    - week : past 7 days (today + previous 6 days), start at 00:00 JST
    - month: past 30 days (today + previous 29 days), start at 00:00 JST
    - year : total (None)
    """
    r = _canonical_range(p_range)
    if r == "year":
        return None
    now_jst = datetime.now(_JST)
    start_jst = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    if r == "week":
        start_jst = start_jst - timedelta(days=6)
    elif r == "month":
        start_jst = start_jst - timedelta(days=29)
    # day: keep today 00:00 JST
    start_utc = start_jst.astimezone(timezone.utc).replace(microsecond=0)
    return start_utc.isoformat().replace("+00:00", "Z")


async def _fetch_mymodel_create_agg(*, p_range: str) -> Dict[str, Dict[str, int]]:
    """Aggregate MyModel Create answers for the given range.

    Returns: { user_id: {"count": int, "chars": int} }

    Notes:
    - For day/week/month: filters by updated_at >= since (JST boundary).
    - For year(total): no time filter.
    """
    since_iso = _range_since_iso(p_range=p_range)

    base_params: Dict[str, str] = {
        "select": "user_id,answer_text,updated_at",
        "order": "updated_at.desc",
    }
    if since_iso:
        base_params["updated_at"] = f"gte.{since_iso}"

    out: Dict[str, Dict[str, int]] = {}
    chunk = 1000
    offset = 0
    while True:
        params = dict(base_params)
        params["limit"] = str(chunk)
        params["offset"] = str(offset)
        resp = await _sb_get(f"/rest/v1/{MYMODEL_CREATE_ANSWERS_TABLE}", params=params)
        if resp.status_code >= 300:
            logger.warning(
                "Supabase %s fetch failed (create agg): %s %s",
                MYMODEL_CREATE_ANSWERS_TABLE,
                resp.status_code,
                (resp.text or "")[:800],
            )
            return {}

        rows = resp.json()
        if not isinstance(rows, list) or not rows:
            break

        for r in rows:
            if not isinstance(r, dict):
                continue
            uid = str(r.get("user_id") or "").strip()
            if not uid:
                continue
            txt = r.get("answer_text")
            s = "" if txt is None else str(txt)
            if not s.strip():
                # Skip empty/blank answers just in case.
                continue
            rec = out.get(uid)
            if rec is None:
                rec = {"count": 0, "chars": 0}
                out[uid] = rec
            rec["count"] += 1
            rec["chars"] += len(s)

        if len(rows) < chunk:
            break
        offset += chunk

    return out


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


async def _fetch_ranking_visibility_map(user_ids: List[str]) -> Dict[str, bool]:
    """Return map user_id -> is_ranking_visible.

    Missing settings rows are treated as visible (True).
    """
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return {}

    # Default visible unless explicitly disabled.
    out: Dict[str, bool] = {uid: True for uid in ids}

    # Chunk to avoid huge query strings.
    chunk_size = 200
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        in_list = ",".join(chunk)
        resp = await _sb_get(
            f"/rest/v1/{VISIBILITY_TABLE}",
            params={
                "select": "user_id,is_ranking_visible",
                "user_id": f"in.({in_list})",
            },
        )
        if resp.status_code >= 300:
            logger.warning(
                "Supabase visibility settings fetch failed (ranking filter): %s %s",
                resp.status_code,
                (resp.text or "")[:500],
            )
            continue
        rows = resp.json()
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            uid = str(r.get("user_id") or "").strip()
            if not uid:
                continue
            flag = r.get("is_ranking_visible")
            if flag is False:
                out[uid] = False
            elif flag is True:
                out[uid] = True

    return out


async def _filter_rows_by_ranking_visibility(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter ranking rows by is_ranking_visible.

    This keeps server-side aggregation intact but hides users who opted out.
    """
    raw_rows = [r for r in (rows or []) if isinstance(r, dict)]
    user_ids = [str(r.get("user_id") or "").strip() for r in raw_rows]
    user_ids = [uid for uid in user_ids if uid]
    if not user_ids:
        return raw_rows

    vis = await _fetch_ranking_visibility_map(user_ids)
    filtered = [
        r for r in raw_rows
        if vis.get(str(r.get("user_id") or "").strip(), True)
    ]

    # Stable ordering by original rank (keep server-side ranking incl. ties).
    def _rk(v: Dict[str, Any]) -> int:
        try:
            return int(v.get("rank") or 0)
        except Exception:
            return 0

    filtered.sort(key=_rk)
    return filtered


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

        # Use server-side ranking (RPC) and keep ranks (incl. ties).
        # Prefetch > limit so visibility filtering can still return up to limit items.
        prefetch_limit = max(int(p_limit), 300)
        rows = await _rpc("rank_input_count", {"p_range": p_range, "p_limit": prefetch_limit})
        rows = await _filter_rows_by_ranking_visibility(rows)
        rows = rows[: int(p_limit)]

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

        # Use server-side ranking (RPC) and keep ranks (incl. ties).
        # Prefetch > limit so visibility filtering can still return up to limit items.
        prefetch_limit = max(int(p_limit), 300)
        rows = await _rpc("rank_input_length", {"p_range": p_range, "p_limit": prefetch_limit})
        rows = await _filter_rows_by_ranking_visibility(rows)
        rows = rows[: int(p_limit)]

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



    @app.get("/ranking/mymodel_questions")
    async def ranking_mymodel_questions(
        range: str = Query(default="year"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        await _require_user_id(authorization)
        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)

        # Use server-side ranking (RPC) and keep ranks (incl. ties).
        # Prefetch > limit so visibility filtering can still return up to limit items.
        prefetch_limit = max(int(p_limit), 300)
        rows = await _rpc("rank_mymodel_questions", {"p_range": p_range, "p_limit": prefetch_limit})
        rows = await _filter_rows_by_ranking_visibility(rows)
        rows = rows[: int(p_limit)]

        user_ids = [str(r.get("user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles = await _fetch_profiles_map(user_ids)

        items: List[Dict[str, Any]] = []
        for r in rows:
            uid = str(r.get("user_id") or "").strip()
            rank = int(r.get("rank") or 0)
            cnt = int(r.get("mymodel_questions_total") or 0)
            prof = profiles.get(uid) or {}
            items.append(
                {
                    "rank": rank,
                    "user_id": uid,
                    "display_name": prof.get("display_name"),
                    "mymodel_questions_total": cnt,
                    "value": cnt,
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
        rows = await _filter_rows_by_ranking_visibility(rows)
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
