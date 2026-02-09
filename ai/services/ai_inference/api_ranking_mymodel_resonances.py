# -*- coding: utf-8 -*-
"""MyModel QnA Resonances Ranking API (Cocolon / MashOS / FastAPI)

Endpoint
--------
- GET /ranking/mymodel_resonances?range=week&limit=30

Notes
-----
* Requires Supabase Auth access token via Authorization: Bearer <access_token>
* Uses Supabase PostgREST RPC (service role) to call SQL function:
  - rank_mymodel_resonances(p_range, p_limit)
* Timezone / boundary: JST (Asia/Tokyo) at 00:00, handled in SQL.

Expected RPC result schema
--------------------------
rank_mymodel_resonances(...) should return a list of rows like:
- rank: int
- user_id: uuid
- resonance_count: int
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, Query

# Reuse the existing ranking helpers (auth, range/limit normalization, RPC, profiles).
from api_ranking import (  # noqa: F401
    _fetch_profiles_map,
    _normalize_limit,
    _normalize_range,
    _require_user_id,
    _rpc,
    _filter_rows_by_ranking_visibility,
)


logger = logging.getLogger("ranking_mymodel_resonances")


def register_ranking_mymodel_resonances_routes(app: FastAPI) -> None:
    """Register /ranking/mymodel_resonances endpoint."""

    @app.get("/ranking/mymodel_resonances")
    async def ranking_mymodel_resonances(
        range: str = Query(default="week"),
        limit: Optional[int] = Query(default=30),
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        # Auth required (prevents public scraping)
        await _require_user_id(authorization)

        p_range = _normalize_range(range)
        p_limit = _normalize_limit(limit, default=30, min_v=1, max_v=100)

        rows = await _rpc("rank_mymodel_resonances", {"p_range": p_range, "p_limit": p_limit})
        rows = await _filter_rows_by_ranking_visibility(rows)

        user_ids = [
            str((r or {}).get("user_id") or "").strip()
            for r in rows
            if isinstance(r, dict)
        ]
        profiles = await _fetch_profiles_map(user_ids)

        items: List[Dict[str, Any]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue

            uid = str(r.get("user_id") or "").strip()
            if not uid:
                continue

            try:
                rk = int(r.get("rank") or 0)
            except Exception:
                rk = 0

            # Prefer resonance_count (RPC), but accept "resonances" as a fallback.
            raw_cnt = r.get("resonance_count")
            if raw_cnt is None:
                raw_cnt = r.get("resonances")
            try:
                cnt = int(raw_cnt or 0)
            except Exception:
                cnt = 0

            prof = profiles.get(uid) or {}
            items.append(
                {
                    "rank": rk or (len(items) + 1),
                    "user_id": uid,
                    "display_name": prof.get("display_name"),
                    "resonance_count": cnt,
                    "value": cnt,
                }
            )

        # Stable ordering
        items.sort(key=lambda x: int(x.get("rank") or 0))

        return {
            "status": "ok",
            "range": p_range,
            "timezone": "Asia/Tokyo",
            "limit": p_limit,
            "items": items,
        }
