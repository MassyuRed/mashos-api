# -*- coding: utf-8 -*-
"""piece_generated_metrics.py

Helpers for generated Piece totals and rankings.

Purpose
-------
- Define Piece count as active/published `emotion_generated` reflections only.
- Provide repo-local helpers so Account Status / Ranking can align without
  waiting for external RPC or projection updates.

Notes
-----
- We count rows in `mymodel_reflections` with:
    source_type = emotion_generated
    is_active   = true
    status      in (ready, published)
- For range-based rankings, published_at is used as the generation timestamp.
- The legacy API field name `mymodel_questions_total` is preserved as an alias
  for backward compatibility, but the semantic source is now Piece rows.
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from supabase_client import ensure_supabase_config, sb_get

MYMODEL_REFLECTIONS_TABLE = (
    os.getenv("MYMODEL_REFLECTIONS_TABLE") or "mymodel_reflections"
).strip() or "mymodel_reflections"
EMOTION_GENERATED_SOURCE_TYPE = "emotion_generated"
_READY_STATUS_FILTER = "in.(ready,published)"
_JST = ZoneInfo("Asia/Tokyo")


def _canonical_range(value: Any) -> str:
    s = str(value or "").strip().lower()
    if s in ("日",):
        return "day"
    if s in ("週",):
        return "week"
    if s in ("月",):
        return "month"
    if s in ("年",):
        return "year"
    if s in {"day", "week", "month", "year"}:
        return s
    return s or "year"


def _range_since_iso(*, range_key: str) -> Optional[str]:
    rk = _canonical_range(range_key)
    if rk == "year":
        return None
    now_jst = datetime.now(_JST)
    start_jst = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    if rk == "week":
        start_jst = start_jst - timedelta(days=6)
    elif rk == "month":
        start_jst = start_jst - timedelta(days=29)
    start_utc = start_jst.astimezone(timezone.utc).replace(microsecond=0)
    return start_utc.isoformat().replace("+00:00", "Z")


def _parse_exact_count(resp: Any) -> int:
    try:
        cr = resp.headers.get("content-range") or resp.headers.get("Content-Range") or ""
        if "/" not in cr:
            return 0
        total = cr.split("/", 1)[1].strip()
        return 0 if total in ("", "*") else max(0, int(total))
    except Exception:
        return 0


def _piece_base_params(*, range_key: str, owner_user_id: Optional[str] = None) -> Dict[str, str]:
    params: Dict[str, str] = {
        "source_type": f"eq.{EMOTION_GENERATED_SOURCE_TYPE}",
        "is_active": "eq.true",
        "status": _READY_STATUS_FILTER,
    }
    owner = str(owner_user_id or "").strip()
    if owner:
        params["owner_user_id"] = f"eq.{owner}"
    since_iso = _range_since_iso(range_key=range_key)
    if since_iso:
        params["published_at"] = f"gte.{since_iso}"
    return params


def _piece_count_alias_payload(count: int) -> Dict[str, int]:
    value = max(0, int(count or 0))
    return {
        "piece_generated_total": value,
        "mymodel_questions_total": value,
        "questions_total": value,
        "value": value,
    }


async def count_piece_generated_total_for_owner(
    owner_user_id: str,
    *,
    range_key: str = "year",
) -> int:
    uid = str(owner_user_id or "").strip()
    if not uid:
        return 0
    ensure_supabase_config()
    params = {
        "select": "id",
        **_piece_base_params(range_key=range_key, owner_user_id=uid),
        "limit": "0",
    }
    resp = await sb_get(
        f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}",
        params=params,
        prefer="count=exact",
        timeout=10.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"piece_generated owner count failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    return _parse_exact_count(resp)


async def build_piece_generated_ranking_rows(*, range_key: str = "year") -> List[Dict[str, Any]]:
    ensure_supabase_config()
    rk = _canonical_range(range_key)
    params_base: Dict[str, str] = {
        "select": "owner_user_id",
        **_piece_base_params(range_key=rk),
        "order": "published_at.desc,updated_at.desc,id.desc",
    }

    counts: Counter[str] = Counter()
    chunk = 1000
    offset = 0
    while True:
        params = dict(params_base)
        params["limit"] = str(chunk)
        params["offset"] = str(offset)
        resp = await sb_get(
            f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}",
            params=params,
            timeout=12.0,
        )
        if resp.status_code not in (200, 206):
            raise RuntimeError(
                f"piece_generated ranking fetch failed: {resp.status_code} {(resp.text or '')[:800]}"
            )
        data = resp.json()
        if not isinstance(data, list) or not data:
            break
        for row in data:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("owner_user_id") or "").strip()
            if not uid:
                continue
            counts[uid] += 1
        if len(data) < chunk:
            break
        offset += chunk

    ordered: List[Tuple[str, int]] = sorted(counts.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    out: List[Dict[str, Any]] = []
    prev_count: Optional[int] = None
    current_rank = 0
    for idx, (uid, cnt) in enumerate(ordered, start=1):
        if prev_count is None or int(cnt) != int(prev_count):
            current_rank = idx
            prev_count = int(cnt)
        out.append({
            "rank": current_rank,
            "user_id": uid,
            **_piece_count_alias_payload(int(cnt)),
        })
    return out


__all__ = [
    "EMOTION_GENERATED_SOURCE_TYPE",
    "MYMODEL_REFLECTIONS_TABLE",
    "build_piece_generated_ranking_rows",
    "count_piece_generated_total_for_owner",
]
