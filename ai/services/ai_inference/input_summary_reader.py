from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from response_microcache import get_or_compute
from supabase_client import sb_get

JST = timezone(timedelta(hours=9))
EMOTIONS_TABLE = "emotions"
INPUT_SUMMARY_READER_CACHE_TTL_SECONDS = 10.0
INPUT_SUMMARY_STREAK_LOOKBACK_DAYS = max(35, int(os.getenv("INPUT_SUMMARY_STREAK_LOOKBACK_DAYS", "60") or "60"))
INPUT_SUMMARY_STREAK_PAGE_SIZE = max(100, int(os.getenv("INPUT_SUMMARY_STREAK_PAGE_SIZE", "400") or "400"))
INPUT_SUMMARY_STREAK_MAX_SCAN_ROWS = max(
    INPUT_SUMMARY_STREAK_PAGE_SIZE,
    int(os.getenv("INPUT_SUMMARY_STREAK_MAX_SCAN_ROWS", "4000") or "4000"),
)


def _to_utc(iso: str) -> Optional[datetime]:
    s = str(iso or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _to_jst_date_key(dt: datetime) -> str:
    j = dt.astimezone(JST)
    return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"


def _jst_midnight_utc(now_utc: datetime) -> datetime:
    now_jst = now_utc.astimezone(JST)
    return datetime(now_jst.year, now_jst.month, now_jst.day, tzinfo=JST).astimezone(timezone.utc)


def _month_start_utc(now_utc: datetime) -> datetime:
    now_jst = now_utc.astimezone(JST)
    return datetime(now_jst.year, now_jst.month, 1, tzinfo=JST).astimezone(timezone.utc)


def _week_start_utc(now_utc: datetime) -> datetime:
    now_jst = now_utc.astimezone(JST)
    midnight_jst = datetime(now_jst.year, now_jst.month, now_jst.day, tzinfo=JST)
    days_since_sunday = (now_jst.weekday() + 1) % 7
    return (midnight_jst - timedelta(days=days_since_sunday)).astimezone(timezone.utc)


def _parse_content_range_total(content_range: str) -> Optional[int]:
    raw = str(content_range or "").strip()
    if not raw or "/" not in raw:
        return None
    tail = raw.split("/")[-1].strip()
    if not tail or tail == "*":
        return None
    try:
        return int(tail)
    except Exception:
        return None


def _range_params(
    *,
    user_id: str,
    start_iso: str,
    end_iso: str,
    select: str,
    limit: int = 1,
    offset: int = 0,
    order: Optional[str] = None,
) -> List[Tuple[str, str]]:
    params: List[Tuple[str, str]] = [
        ("select", select),
        ("user_id", f"eq.{user_id}"),
        ("created_at", f"gte.{start_iso}"),
        ("created_at", f"lt.{end_iso}"),
        ("limit", str(max(1, int(limit)))),
    ]
    if offset > 0:
        params.append(("offset", str(max(0, int(offset)))))
    if order:
        params.append(("order", order))
    return params


async def _fetch_range_count(user_id: str, start_iso: str, end_iso: str) -> int:
    resp = await sb_get(
        f"/rest/v1/{EMOTIONS_TABLE}",
        params=_range_params(
            user_id=user_id,
            start_iso=start_iso,
            end_iso=end_iso,
            select="id",
            limit=1,
        ),
        prefer="count=exact",
        timeout=8.0,
    )
    total = _parse_content_range_total(resp.headers.get("content-range") or resp.headers.get("Content-Range") or "")
    if resp.status_code not in (200, 206) or total is None:
        raise RuntimeError("Failed to load input summary counts")
    return max(0, int(total))


async def _fetch_last_input_at(user_id: str) -> Optional[str]:
    resp = await sb_get(
        f"/rest/v1/{EMOTIONS_TABLE}",
        params={
            "select": "created_at",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError("Failed to load latest input timestamp")
    rows = resp.json() if hasattr(resp, "json") else []
    rows = rows if isinstance(rows, list) else []
    if not rows:
        return None
    row0 = rows[0] if isinstance(rows[0], dict) else {}
    return str(row0.get("created_at") or "").strip() or None


async def _fetch_recent_streak_date_keys(user_id: str, start_iso: str, end_iso: str) -> Set[str]:
    page_size = int(INPUT_SUMMARY_STREAK_PAGE_SIZE)
    max_rows = int(INPUT_SUMMARY_STREAK_MAX_SCAN_ROWS)
    offset = 0
    fetched_rows = 0
    date_keys: Set[str] = set()

    while fetched_rows < max_rows:
        resp = await sb_get(
            f"/rest/v1/{EMOTIONS_TABLE}",
            params=_range_params(
                user_id=user_id,
                start_iso=start_iso,
                end_iso=end_iso,
                select="created_at",
                limit=page_size,
                offset=offset,
                order="created_at.desc",
            ),
            timeout=8.0,
        )
        if resp.status_code not in (200, 206):
            raise RuntimeError("Failed to load input streak rows")
        rows = resp.json() if hasattr(resp, "json") else []
        rows = rows if isinstance(rows, list) else []
        if not rows:
            break

        for row in rows:
            if not isinstance(row, dict):
                continue
            dt = _to_utc(str(row.get("created_at") or ""))
            if dt is None:
                continue
            date_keys.add(_to_jst_date_key(dt))

        fetched_rows += len(rows)
        if len(rows) < page_size or fetched_rows >= max_rows:
            break
        offset += len(rows)

    return date_keys


def _compute_streak(now_utc: datetime, date_keys: Set[str]) -> int:
    now_jst = now_utc.astimezone(JST)
    today_key = f"{now_jst.year:04d}-{now_jst.month:02d}-{now_jst.day:02d}"
    base_jst = now_jst if today_key in date_keys else (now_jst - timedelta(days=1))

    streak = 0
    for i in range(60):
        d = base_jst - timedelta(days=i)
        key = f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
        if key in date_keys:
            streak += 1
        else:
            break
    return streak


async def _build_payload(user_id: str) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    day_start = _jst_midnight_utc(now_utc)
    day_end = day_start + timedelta(days=1)
    month_start = _month_start_utc(now_utc)
    week_start = _week_start_utc(now_utc)
    streak_window_start = day_start - timedelta(days=INPUT_SUMMARY_STREAK_LOOKBACK_DAYS)

    today_count, week_count, month_count, last_input_at, date_keys = await asyncio.gather(
        _fetch_range_count(user_id, day_start.isoformat(), day_end.isoformat()),
        _fetch_range_count(user_id, week_start.isoformat(), day_end.isoformat()),
        _fetch_range_count(user_id, month_start.isoformat(), day_end.isoformat()),
        _fetch_last_input_at(user_id),
        _fetch_recent_streak_date_keys(user_id, streak_window_start.isoformat(), day_end.isoformat()),
    )

    return {
        "status": "ok",
        "user_id": str(user_id),
        "today_count": int(today_count or 0),
        "week_count": int(week_count or 0),
        "month_count": int(month_count or 0),
        "streak_days": _compute_streak(now_utc, date_keys),
        "last_input_at": last_input_at,
    }


async def get_input_summary_snapshot(user_id: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return {
            "status": "ok",
            "user_id": "",
            "today_count": 0,
            "week_count": 0,
            "month_count": 0,
            "streak_days": 0,
            "last_input_at": None,
        }

    return await get_or_compute(
        f"input_summary_reader:{uid}",
        INPUT_SUMMARY_READER_CACHE_TTL_SECONDS,
        lambda: _build_payload(uid),
    )
