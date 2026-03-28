from __future__ import annotations

import asyncio
import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Header, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from api_account_visibility import _require_user_id
from publish_governance import decide_myweb_report_publish
from response_microcache import build_cache_key, get_or_compute
from supabase_client import sb_get

try:
    from subscription import SubscriptionTier  # type: ignore
    from subscription_store import get_subscription_tier_for_user  # type: ignore
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore

logger = logging.getLogger("myweb_reads_api")
JST = timezone(timedelta(hours=9))

MYWEB_HOME_SUMMARY_CACHE_TTL_SECONDS = 15.0

STRENGTH_SCORE: Dict[str, int] = {"weak": 1, "medium": 2, "strong": 3}
JP_TO_KEY: Dict[str, str] = {
    "喜び": "joy",
    "悲しみ": "sadness",
    "不安": "anxiety",
    "怒り": "anger",
    "平穏": "calm",
}
EMOTION_KEYS: Tuple[str, ...] = ("joy", "sadness", "anxiety", "anger", "calm")
SELF_INSIGHT_LABELS = {"自己理解", "SelfInsight"}


class MyWebWeeklySummary(BaseModel):
    count: int = 0
    top: List[List[Any]] = Field(default_factory=list)
    error: str = ""


class MyWebMonthlySummary(BaseModel):
    count: int = 0
    error: str = ""


class MyWebHomeSummaryResponse(BaseModel):
    status: str = "ok"
    weekly: MyWebWeeklySummary
    monthly: MyWebMonthlySummary


class MyWebWeeklyDay(BaseModel):
    dateKey: str
    label: str
    joy: int = 0
    sadness: int = 0
    anxiety: int = 0
    anger: int = 0
    calm: int = 0
    dominantKey: Optional[str] = None


class MyWebWeeklyDaysResponse(BaseModel):
    status: str = "ok"
    report_id: str
    source: str = "computed"
    days: List[MyWebWeeklyDay] = Field(default_factory=list)


def _pick_rows(resp) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _coerce_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _parse_iso(value: str) -> datetime:
    s = str(value or "").strip()
    if not s:
        raise ValueError("missing datetime")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def _resolve_viewer_tier(user_id: str) -> str:
    tier_str = "free"
    if user_id and SubscriptionTier is not None and get_subscription_tier_for_user is not None:
        try:
            tier_enum = await get_subscription_tier_for_user(user_id, default=SubscriptionTier.FREE)
            tier_str = tier_enum.value if hasattr(tier_enum, "value") else str(tier_enum)
        except Exception:
            tier_str = "free"
    return str(tier_str or "free")


def _jst_week_range_for_now() -> Tuple[str, str]:
    now_jst = _now_utc().astimezone(JST)
    end_jst = now_jst.replace(hour=23, minute=59, second=59, microsecond=999000)
    start_jst = (end_jst - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        start_jst.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        end_jst.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def _jst_month_range_for_now() -> Tuple[str, str]:
    now_jst = _now_utc().astimezone(JST)
    start_jst = datetime(now_jst.year, now_jst.month, 1, tzinfo=JST)
    if now_jst.month == 12:
        next_jst = datetime(now_jst.year + 1, 1, 1, tzinfo=JST)
    else:
        next_jst = datetime(now_jst.year, now_jst.month + 1, 1, tzinfo=JST)
    return (
        start_jst.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        next_jst.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


async def _fetch_emotions(
    user_id: str,
    *,
    select: str,
    start_iso: str,
    end_iso: str,
    end_op: str = "lte",
    include_secret: bool = True,
    ascending: bool = False,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    clauses = [
        f"created_at.gte.{start_iso}",
        f"created_at.{end_op}.{end_iso}",
    ]
    if not include_secret:
        clauses.append("is_secret.eq.false")

    resp = await sb_get(
        "/rest/v1/emotions",
        params={
            "select": select,
            "user_id": f"eq.{user_id}",
            "and": f"({','.join(clauses)})",
            "order": f"created_at.{'asc' if ascending else 'desc'}",
            "limit": str(max(1, int(limit or 5000))),
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning("emotions select failed: %s %s", resp.status_code, (resp.text or "")[:800])
        raise HTTPException(status_code=502, detail="Failed to load emotions")
    return _pick_rows(resp)


def _summarize_weekly(rows: List[Dict[str, Any]]) -> MyWebWeeklySummary:
    counter: Counter[str] = Counter()
    for row in rows:
        emotions = row.get("emotions") if isinstance(row.get("emotions"), list) else []
        for value in emotions:
            token = str(value or "").strip()
            if token:
                counter[token] += 1
    top = [[name, count] for name, count in counter.most_common(3)]
    return MyWebWeeklySummary(count=len(rows), top=top, error="")


def _normalize_content_json(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _map_key(value: Any) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw in JP_TO_KEY:
        return JP_TO_KEY[raw]
    if raw in EMOTION_KEYS:
        return raw
    return None


def _normalize_saved_days(raw_days: Any) -> List[MyWebWeeklyDay]:
    if not isinstance(raw_days, list):
        return []
    out: List[MyWebWeeklyDay] = []
    for item in raw_days:
        if not isinstance(item, dict):
            continue
        out.append(
            MyWebWeeklyDay(
                dateKey=str(item.get("dateKey") or item.get("date_key") or ""),
                label=str(item.get("label") or ""),
                joy=_coerce_int(item.get("joy")),
                sadness=_coerce_int(item.get("sadness")),
                anxiety=_coerce_int(item.get("anxiety")),
                anger=_coerce_int(item.get("anger")),
                calm=_coerce_int(item.get("calm")),
                dominantKey=(str(item.get("dominantKey") or item.get("dominant_key") or "").strip() or None),
            )
        )
    return out


def _extract_saved_days(content_json: Dict[str, Any]) -> List[MyWebWeeklyDay]:
    candidates: List[Any] = []
    candidates.append(content_json.get("days"))
    standard_report = content_json.get("standardReport") if isinstance(content_json.get("standardReport"), dict) else {}
    standard_report_alt = content_json.get("standard_report") if isinstance(content_json.get("standard_report"), dict) else {}
    features = standard_report.get("features") if isinstance(standard_report.get("features"), dict) else {}
    features_alt = standard_report_alt.get("features") if isinstance(standard_report_alt.get("features"), dict) else {}
    candidates.append(features.get("days"))
    candidates.append(features_alt.get("days"))
    for raw in candidates:
        days = _normalize_saved_days(raw)
        if days:
            return days
    return []


def _build_days_from_rows(rows: List[Dict[str, Any]]) -> List[MyWebWeeklyDay]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        try:
            created = _parse_iso(str(row.get("created_at") or "")).astimezone(JST)
        except Exception:
            continue
        date_key = f"{created.year}-{created.month:02d}-{created.day:02d}"
        label = f"{created.month}/{created.day}"
        bucket = buckets.setdefault(
            date_key,
            {
                "dateKey": date_key,
                "label": label,
                "sortKey": created.replace(hour=0, minute=0, second=0, microsecond=0),
                "joy": 0,
                "sadness": 0,
                "anxiety": 0,
                "anger": 0,
                "calm": 0,
            },
        )

        details = row.get("emotion_details") if isinstance(row.get("emotion_details"), list) else None
        if not isinstance(details, list):
            emotions = row.get("emotions") if isinstance(row.get("emotions"), list) else []
            details = [{"type": token, "strength": "medium"} for token in emotions]

        for item in details:
            if not isinstance(item, dict):
                continue
            t = str(item.get("type") or "").strip()
            if t in SELF_INSIGHT_LABELS:
                continue
            key = _map_key(t)
            if not key:
                continue
            weight = STRENGTH_SCORE.get(str(item.get("strength") or "").strip(), 0)
            bucket[key] += weight

    ordered = sorted(buckets.values(), key=lambda x: x["sortKey"])
    out: List[MyWebWeeklyDay] = []
    for bucket in ordered:
        dominant_key: Optional[str] = None
        max_val = 0
        for key in EMOTION_KEYS:
            val = _coerce_int(bucket.get(key))
            if val > max_val:
                max_val = val
                dominant_key = key if val > 0 else None
        out.append(
            MyWebWeeklyDay(
                dateKey=str(bucket.get("dateKey") or ""),
                label=str(bucket.get("label") or ""),
                joy=_coerce_int(bucket.get("joy")),
                sadness=_coerce_int(bucket.get("sadness")),
                anxiety=_coerce_int(bucket.get("anxiety")),
                anger=_coerce_int(bucket.get("anger")),
                calm=_coerce_int(bucket.get("calm")),
                dominantKey=dominant_key,
            )
        )
    return out


async def _fetch_myweb_report_row(user_id: str, report_id: str, *, tier_str: str) -> Dict[str, Any]:
    resp = await sb_get(
        "/rest/v1/myweb_reports",
        params={
            "select": "id,report_type,period_start,period_end,content_json",
            "id": f"eq.{report_id}",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning("myweb_reports select failed: %s %s", resp.status_code, (resp.text or "")[:800])
        raise HTTPException(status_code=502, detail="Failed to load MyWeb report")
    rows = _pick_rows(resp)
    if not rows:
        raise HTTPException(status_code=404, detail="MyWeb report not found")
    published_row = decide_myweb_report_publish(rows[0], tier_str=tier_str)
    if not published_row:
        raise HTTPException(status_code=404, detail="MyWeb report not found")
    return published_row




async def get_myweb_home_summary_payload_for_user(user_id: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return jsonable_encoder(
            MyWebHomeSummaryResponse(
                status="ok",
                weekly=MyWebWeeklySummary(count=0, top=[], error=""),
                monthly=MyWebMonthlySummary(count=0, error=""),
            )
        )

    cache_key = build_cache_key(f"myweb:home_summary:{uid}")

    async def _build_payload() -> Dict[str, Any]:
        week_start, week_end = _jst_week_range_for_now()
        month_start, next_month_start = _jst_month_range_for_now()

        weekly_task = _fetch_emotions(
            uid,
            select="id,emotions,created_at",
            start_iso=week_start,
            end_iso=week_end,
            end_op="lte",
            include_secret=True,
            ascending=False,
        )
        monthly_task = _fetch_emotions(
            uid,
            select="id,created_at",
            start_iso=month_start,
            end_iso=next_month_start,
            end_op="lt",
            include_secret=True,
            ascending=False,
        )

        weekly_rows, monthly_rows = await asyncio.gather(weekly_task, monthly_task)

        response = MyWebHomeSummaryResponse(
            status="ok",
            weekly=_summarize_weekly(weekly_rows),
            monthly=MyWebMonthlySummary(count=len(monthly_rows), error=""),
        )
        return jsonable_encoder(response)

    return await get_or_compute(cache_key, MYWEB_HOME_SUMMARY_CACHE_TTL_SECONDS, _build_payload)


def register_myweb_read_routes(app: FastAPI) -> None:
    @app.get("/myweb/home-summary", response_model=MyWebHomeSummaryResponse)
    async def get_myweb_home_summary(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyWebHomeSummaryResponse:
        me = await _require_user_id(authorization)
        payload = await get_myweb_home_summary_payload_for_user(me)
        return MyWebHomeSummaryResponse(**payload)

    @app.get("/myweb/reports/{report_id}/weekly-days", response_model=MyWebWeeklyDaysResponse)
    async def get_myweb_report_weekly_days(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyWebWeeklyDaysResponse:
        me = await _require_user_id(authorization)
        tier_str = await _resolve_viewer_tier(me)
        row = await _fetch_myweb_report_row(me, str(report_id or "").strip(), tier_str=tier_str)
        report_type = str(row.get("report_type") or "").strip().lower()
        if report_type != "weekly":
            raise HTTPException(status_code=400, detail="weekly report only")

        content_json = _normalize_content_json(row.get("content_json"))
        saved_days = _extract_saved_days(content_json)
        if saved_days:
            return MyWebWeeklyDaysResponse(
                report_id=str(row.get("id") or report_id),
                source="saved",
                days=saved_days,
            )

        period_start = str(row.get("period_start") or "").strip()
        period_end = str(row.get("period_end") or "").strip()
        if not period_start or not period_end:
            raise HTTPException(status_code=400, detail="Report period is missing")

        emotion_rows = await _fetch_emotions(
            me,
            select="created_at,emotions,emotion_details,is_secret",
            start_iso=period_start,
            end_iso=period_end,
            end_op="lte",
            include_secret=False,
            ascending=True,
        )
        days = _build_days_from_rows(emotion_rows)
        return MyWebWeeklyDaysResponse(
            report_id=str(row.get("id") or report_id),
            source="computed",
            days=days,
        )
