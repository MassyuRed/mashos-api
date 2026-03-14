from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from supabase_client import sb_get

JST = timezone(timedelta(hours=9))
EMOTIONS_TABLE = "emotions"


class InputSummaryResponse(BaseModel):
    status: str = "ok"
    user_id: str = Field(...)
    today_count: int = 0
    week_count: int = 0
    month_count: int = 0
    streak_days: int = 0
    last_input_at: Optional[str] = None


async def _require_user_id(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return str(await _resolve_user_id_from_token(token))


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


async def _fetch_recent_rows(user_id: str, start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
    resp = await sb_get(
        f"/rest/v1/{EMOTIONS_TABLE}",
        params={
            "select": "created_at",
            "user_id": f"eq.{user_id}",
            "created_at": f"gte.{start_iso}",
            "order": "created_at.desc",
            "limit": "5000",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise HTTPException(status_code=502, detail="Failed to load input summary")

    rows = resp.json()
    rows = rows if isinstance(rows, list) else []
    end_dt = _to_utc(end_iso)
    if end_dt is None:
        return rows
    out = []
    for row in rows:
        dt = _to_utc(row.get("created_at"))
        if dt is None:
            continue
        if dt < end_dt:
            out.append(row)
    return out


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


def register_input_summary_routes(app: FastAPI) -> None:
    @app.get("/input/summary", response_model=InputSummaryResponse)
    async def get_input_summary(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> InputSummaryResponse:
        user_id = await _require_user_id(authorization)
        now_utc = datetime.now(timezone.utc)

        day_start = _jst_midnight_utc(now_utc)
        day_end = day_start + timedelta(days=1)
        month_start = _month_start_utc(now_utc)
        week_start = _week_start_utc(now_utc)
        streak_window_start = day_start - timedelta(days=35)

        fetch_start = min(month_start, week_start, streak_window_start)
        rows = await _fetch_recent_rows(
            user_id=user_id,
            start_iso=fetch_start.isoformat(),
            end_iso=day_end.isoformat(),
        )

        today_count = 0
        week_count = 0
        month_count = 0
        last_input_at = None
        date_keys: Set[str] = set()

        for row in rows:
            dt = _to_utc(row.get("created_at"))
            if dt is None:
                continue
            if last_input_at is None:
                last_input_at = row.get("created_at")
            if day_start <= dt < day_end:
                today_count += 1
            if week_start <= dt < day_end:
                week_count += 1
            if month_start <= dt < day_end:
                month_count += 1
            date_keys.add(_to_jst_date_key(dt))

        streak_days = _compute_streak(now_utc, date_keys)

        return InputSummaryResponse(
            user_id=user_id,
            today_count=today_count,
            week_count=week_count,
            month_count=month_count,
            streak_days=streak_days,
            last_input_at=last_input_at,
        )
