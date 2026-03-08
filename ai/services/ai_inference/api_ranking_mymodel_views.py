# -*- coding: utf-8 -*-
"""MyModel QnA Views Ranking API (Cocolon / MashOS / FastAPI)

Endpoint
--------
- GET /ranking/mymodel_views?range=week&limit=30

Notes
-----
* Requires Supabase Auth access token via Authorization: Bearer <access_token>
* Uses Supabase PostgREST RPC (service role) to call SQL function:
  - rank_mymodel_views(p_range, p_limit)
* Timezone / boundary: JST (Asia/Tokyo) at 00:00, handled in SQL.

Expected RPC result schema
--------------------------
rank_mymodel_views(...) should return a list of rows like:
- rank: int
- user_id: uuid
- view_count: int
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, Query

# Reuse the existing ranking helpers (auth, range/limit normalization, RPC, profiles).
from api_ranking import (  # noqa: F401
    _fetch_private_account_map,
    _fetch_profiles_map,
    _normalize_limit,
    _normalize_range,
    _require_user_id,
    _rpc,
    _filter_rows_by_ranking_visibility,
)
from astor_ranking_boards import fetch_latest_ready_ranking_board, select_board_rows


logger = logging.getLogger("ranking_mymodel_views")


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


def _pick_view_count(row: Dict[str, Any]) -> int:
    for key in ("view_count", "views", "count", "value"):
        if row.get(key) is not None:
            return _coerce_int(row.get(key), 0)
    return 0


async def _publish_view_items(rows: List[Dict[str, Any]], *, limit: int) -> List[Dict[str, Any]]:
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
        cnt = _pick_view_count(r)
        prof = profiles.get(uid) if isinstance(profiles.get(uid), dict) else {}
        is_private = bool(private_map.get(uid, bool(r.get("is_private_account") or False)))

        items.append(
            {
                "rank": rank,
                "user_id": uid,
                "display_name": _coerce_text((prof or {}).get("display_name")),
                "is_private_account": is_private,
                "view_count": cnt,
                "value": cnt,
            }
        )

    items.sort(key=lambda x: int(x.get("rank") or 0))
    return items[: max(1, int(limit or 30))]


def register_ranking_mymodel_views_routes(app: FastAPI) -> None:
    """Register /ranking/mymodel_views endpoint."""

    @app.get("/ranking/mymodel_views")
    async def ranking_mymodel_views(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        # Auth required (prevents public scraping)
        await _require_user_id(authorization)

        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)

        try:
            board_rows = await _fetch_ready_board_rows("mymodel_views", p_range)
            if board_rows is not None:
                items = await _publish_view_items(board_rows, limit=p_limit)
                return {
                    "status": "ok",
                    "range": p_range,
                    "timezone": "Asia/Tokyo",
                    "limit": p_limit,
                    "items": items,
                }
        except Exception as exc:
            logger.warning("ranking board publish failed: metric=mymodel_views range=%s err=%s", p_range, exc)

        rows = await _rpc("rank_mymodel_views", {"p_range": p_range, "p_limit": p_limit})
        items = await _publish_view_items(rows, limit=p_limit)

        return {
            "status": "ok",
            "range": p_range,
            "timezone": "Asia/Tokyo",
            "limit": p_limit,
            "items": items,
        }
