# -*- coding: utf-8 -*-
"""Current Piece views ranking API owner.

This module owns the current-vocabulary Piece views ranking route and its
runtime helpers. Legacy MyModel-named modules should delegate here during the
rename-safe phase.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, Query

from api_ranking import (  # noqa: F401
    _fetch_private_account_map,
    _fetch_profiles_map,
    _filter_rows_by_ranking_visibility,
    _normalize_limit,
    _normalize_range,
    _require_user_id,
    _rpc,
)
from astor_ranking_boards import fetch_latest_ready_ranking_board, select_board_rows


logger = logging.getLogger("ranking_piece_views")


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


async def _build_ranking_piece_views_payload(
    *,
    range: str,
    limit: Optional[int],
    authorization: Optional[str],
) -> Dict[str, Any]:
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
        logger.warning(
            "ranking board publish failed: metric=mymodel_views range=%s err=%s",
            p_range,
            exc,
        )

    rows = await _rpc("rank_mymodel_views", {"p_range": p_range, "p_limit": p_limit})
    items = await _publish_view_items(rows, limit=p_limit)

    return {
        "status": "ok",
        "range": p_range,
        "timezone": "Asia/Tokyo",
        "limit": p_limit,
        "items": items,
    }


def register_ranking_piece_views_routes(app: FastAPI) -> None:
    """Register /ranking/piece_views endpoint."""

    @app.get("/ranking/piece_views")
    async def ranking_piece_views(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        return await _build_ranking_piece_views_payload(
            range=range,
            limit=limit,
            authorization=authorization,
        )


__all__ = [
    "_build_ranking_piece_views_payload",
    "_fetch_ready_board_rows",
    "_publish_view_items",
    "register_ranking_piece_views_routes",
]
