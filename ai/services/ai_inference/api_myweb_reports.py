# -*- coding: utf-8 -*-
"""
api_myweb_reports.py

Phase1: MyWeb ensure API (on-demand, per-user)

目的
- クライアント(アプリ)が画面表示時などに「配布されているべき」MyWebレポートが
  Supabase に存在するかを確認し、無ければサーバ側で生成して保存(upsert)する。
- JST(UTC+9) 固定で period を計算し、端末TZやアプリ稼働状況に依存しない。

提供エンドポイント
- POST /myweb/reports/ensure

設計
- 対象: 認証された自分自身(user_id)
- 生成対象: daily / weekly / monthly（デフォは全部）
- 冪等: (user_id, report_type, period_start, period_end) をキーに upsert
- 失敗しても他のタイプ生成を継続し、結果を配列で返す
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)

# Phase10: generation lock (dedupe concurrent generation)
try:
    from generation_lock import (
        build_lock_key,
        make_owner_id,
        poll_until,
        release_lock,
        try_acquire_lock,
    )
except Exception:  # pragma: no cover
    build_lock_key = None  # type: ignore
    make_owner_id = None  # type: ignore
    poll_until = None  # type: ignore
    release_lock = None  # type: ignore
    try_acquire_lock = None  # type: ignore


# Optional: enrich weekly/monthly with ASTOR insight (structure patterns based)
try:
    from astor_myweb_insight import generate_myweb_insight_payload
except Exception:  # pragma: no cover
    generate_myweb_insight_payload = None  # type: ignore

# Optional: subscription tier (MyWeb v3 output gating)
try:
    from subscription import SubscriptionTier
    from subscription_store import get_subscription_tier_for_user
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore


logger = logging.getLogger("myweb_reports_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

REPORTS_TABLE = os.getenv("MYWEB_REPORTS_TABLE", "myweb_reports").strip() or "myweb_reports"

# Phase10 lock tuning (env)
MYWEB_LOCK_TTL_SECONDS = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYWEB", "120") or "120")
MYWEB_LOCK_WAIT_SECONDS = float(os.getenv("GENERATION_LOCK_WAIT_SECONDS_MYWEB", "25") or "25")

# JST fixed
JST_OFFSET = timedelta(hours=9)
JST = timezone(JST_OFFSET)

DAY = timedelta(days=1)

# Strength weights (match client)
STRENGTH_SCORE: Dict[str, int] = {"weak": 1, "medium": 2, "strong": 3}

# Emotion mapping (JP labels -> keys)
JP_TO_KEY: Dict[str, str] = {
    "喜び": "joy",
    "悲しみ": "sadness",
    "不安": "anxiety",
    "怒り": "anger",
    "平穏": "calm",
}
EMOTION_KEYS: Tuple[str, ...] = ("joy", "sadness", "anxiety", "anger", "calm")
KEY_TO_JP: Dict[str, str] = {v: k for k, v in JP_TO_KEY.items()}


class MyWebEnsureRequest(BaseModel):
    types: Optional[List[Literal["daily", "weekly", "monthly"]]] = Field(
        default=None,
        description="生成対象。未指定なら weekly/monthly。",
    )
    force: bool = Field(
        default=False,
        description="true の場合、既存レポートがあっても再生成して upsert する（上書き）。",
    )
    now_iso: Optional[str] = Field(
        default=None,
        description="テスト用: 現在時刻(UTC ISO)。未指定ならサーバ現在時刻。",
    )
    include_astor: bool = Field(
        default=True,
        description="weekly/monthly に ASTOR の構造洞察テキストを付与する（失敗しても生成は継続）。",
    )


class MyWebEnsureItem(BaseModel):
    report_type: Literal["daily", "weekly", "monthly"]
    status: Literal["generated", "exists", "error"]
    period_start: str
    period_end: str
    title: str
    report_id: Optional[int] = None
    error: Optional[str] = None


class MyWebEnsureResponse(BaseModel):
    user_id: str
    now_iso: str
    results: List[MyWebEnsureItem]


@dataclass(frozen=True)
class TargetPeriod:
    report_type: str
    dist_utc: datetime
    period_start_utc: datetime
    period_end_utc: datetime
    period_start_iso: str
    period_end_iso: str
    title: str
    title_meta: Dict[str, Any]


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get(path: str, *, params: List[Tuple[str, str]]) -> httpx.Response:
    _ensure_supabase_config()
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Supabase URL is not configured")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.get(url, headers=_sb_headers(), params=params)


async def _sb_post(path: str, *, params: List[Tuple[str, str]], json_body: Any, prefer: str) -> httpx.Response:
    _ensure_supabase_config()
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Supabase URL is not configured")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.post(url, headers=_sb_headers(prefer=prefer), params=params, json=json_body)


def _parse_now_utc(now_iso: Optional[str]) -> datetime:
    if not now_iso:
        return datetime.now(timezone.utc)
    try:
        # accept both "...Z" and "+00:00"
        s = now_iso.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid now_iso (must be ISO datetime in UTC)")


def _jst_midnight_utc(year: int, month: int, day: int) -> datetime:
    """JSTの指定日 00:00 を UTC datetime で返す。"""
    jst_dt = datetime(year, month, day, 0, 0, 0, 0, tzinfo=JST)
    return jst_dt.astimezone(timezone.utc)


def _last_distribution_utc(report_type: str, now_utc: datetime) -> datetime:
    now_jst = now_utc.astimezone(JST)

    if report_type == "daily":
        return _jst_midnight_utc(now_jst.year, now_jst.month, now_jst.day)

    if report_type == "weekly":
        # Sunday 00:00 JST
        # weekday(): Mon=0 ... Sun=6
        days_back = (now_jst.weekday() + 1) % 7
        last_sun = (now_jst.date() - timedelta(days=days_back))
        return _jst_midnight_utc(last_sun.year, last_sun.month, last_sun.day)

    if report_type == "monthly":
        # 1st day 00:00 JST
        return _jst_midnight_utc(now_jst.year, now_jst.month, 1)

    raise ValueError("Unknown report_type")


def _format_jst_date_only(dt_utc: datetime) -> str:
    j = dt_utc.astimezone(JST)
    return f"{j.year}/{j.month}/{j.day}"


def _format_jst_md(dt_utc: datetime) -> str:
    j = dt_utc.astimezone(JST)
    return f"{j.month}/{j.day}"


def _build_target_period(report_type: str, now_utc: datetime) -> TargetPeriod:
    dist_utc = _last_distribution_utc(report_type, now_utc)
    period_end_utc = dist_utc - timedelta(milliseconds=1)

    if report_type == "daily":
        period_start_utc = dist_utc - DAY
        title_date = _format_jst_md(period_start_utc)
        title = f"日報：{title_date}（1日分）"
        meta = {"titleDate": title_date}
    elif report_type == "weekly":
        period_start_utc = dist_utc - 7 * DAY
        s = _format_jst_md(period_start_utc)
        e = _format_jst_md(period_end_utc)
        title_range = f"{s} ～ {e}"
        title = f"週報：{title_range}（7日分）"
        meta = {"titleRange": title_range}
    else:
        # monthly (28 days)
        period_start_utc = dist_utc - 28 * DAY
        end_jst = period_end_utc.astimezone(JST)
        title_month = f"{end_jst.year}/{end_jst.month}"
        title = f"月報：{title_month}（28日分）"
        meta = {"titleMonth": title_month}

    # ISO: always UTC with milliseconds like JS's toISOString()
    def iso(dt: datetime) -> str:
        dt2 = dt.astimezone(timezone.utc)
        # Keep milliseconds
        return dt2.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    return TargetPeriod(
        report_type=report_type,
        dist_utc=dist_utc,
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
        period_start_iso=iso(period_start_utc),
        period_end_iso=iso(period_end_utc),
        title=title,
        title_meta=meta,
    )


def _normalize_details(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    details = row.get("emotion_details")
    if isinstance(details, list):
        out = []
        for it in details:
            if isinstance(it, dict):
                t = str(it.get("type") or "").strip()
                s = str(it.get("strength") or "medium").strip().lower()
                if not t:
                    continue
                if s not in STRENGTH_SCORE:
                    s = "medium"
                out.append({"type": t, "strength": s})
        return out

    emos = row.get("emotions")
    if isinstance(emos, list):
        out = []
        for t in emos:
            tt = str(t or "").strip()
            if not tt:
                continue
            out.append({"type": tt, "strength": "medium"})
        return out

    return []


def _map_key(jp: str) -> Optional[str]:
    return JP_TO_KEY.get(str(jp).strip())


async def _fetch_emotion_rows(user_id: str, start_iso: str, end_iso: str) -> List[Dict[str, Any]]:
    resp = await _sb_get(
        "/rest/v1/emotions",
        params=[
            ("select", "created_at,emotions,emotion_details,memo,is_secret"),
            ("user_id", f"eq.{user_id}"),
            ("created_at", f"gte.{start_iso}"),
            ("created_at", f"lte.{end_iso}"),
            ("order", "created_at.asc"),
        ],
    )
    if resp.status_code != 200:
        logger.error("Supabase emotions fetch failed: %s %s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=502, detail="Failed to fetch emotions")
    try:
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


async def _report_exists(user_id: str, report_type: str, start_iso: str, end_iso: str) -> Optional[int]:
    resp = await _sb_get(
        f"/rest/v1/{REPORTS_TABLE}",
        params=[
            ("select", "id"),
            ("user_id", f"eq.{user_id}"),
            ("report_type", f"eq.{report_type}"),
            ("period_start", f"eq.{start_iso}"),
            ("period_end", f"eq.{end_iso}"),
            ("limit", "1"),
        ],
    )
    if resp.status_code != 200:
        logger.error("Supabase myweb_reports exists check failed: %s %s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=502, detail="Failed to query myweb reports")
    try:
        rows = resp.json()
        if isinstance(rows, list) and rows:
            rid = rows[0].get("id")
            return int(rid) if rid is not None else None
        return None
    except Exception:
        return None


async def _upsert_report(payload: Dict[str, Any]) -> Optional[int]:
    resp = await _sb_post(
        f"/rest/v1/{REPORTS_TABLE}",
        params=[("on_conflict", "user_id,report_type,period_start,period_end")],
        json_body=payload,
        prefer="resolution=merge-duplicates,return=representation",
    )
    if resp.status_code not in (200, 201):
        logger.error("Supabase myweb_reports upsert failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to save myweb report")
    try:
        rows = resp.json()
        if isinstance(rows, list) and rows:
            rid = rows[0].get("id")
            return int(rid) if rid is not None else None
        return None
    except Exception:
        return None


def _build_daily_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {k: 0 for k in EMOTION_KEYS}
    for row in rows:
        for it in _normalize_details(row):
            k = _map_key(it.get("type", ""))
            if not k:
                continue
            w = STRENGTH_SCORE.get(str(it.get("strength", "medium")).lower(), 0)
            totals[k] += w
    total_all = sum(totals.values())
    share_pct = {k: 0 for k in EMOTION_KEYS}
    if total_all > 0:
        for k in EMOTION_KEYS:
            share_pct[k] = int(round((totals[k] / total_all) * 100))
    dominant = None
    maxv = 0
    for k in EMOTION_KEYS:
        v = totals.get(k, 0)
        if v > maxv:
            maxv = v
            dominant = k if v > 0 else None
    return {
        "totals": totals,
        "totalAll": total_all,
        "sharePct": share_pct,
        "dominantKey": dominant,
        "hasData": total_all > 0,
    }


def _build_days_fixed7(rows: List[Dict[str, Any]], period_start_utc: datetime) -> List[Dict[str, Any]]:
    buckets: List[Dict[str, Any]] = []
    for i in range(7):
        utc_start = period_start_utc + i * DAY
        j = utc_start.astimezone(JST)
        date_key = f"{j.year:04d}-{j.month:02d}-{j.day:02d}"
        buckets.append(
            {
                "dateKey": date_key,
                "label": f"{j.month}/{j.day}",
                "utcStartMs": int(utc_start.timestamp() * 1000),
                "joy": 0,
                "sadness": 0,
                "anxiety": 0,
                "anger": 0,
                "calm": 0,
                "dominantKey": None,
            }
        )

    for row in rows:
        try:
            t = row.get("created_at")
            if not t:
                continue
            s = str(t)
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
        except Exception:
            continue

        idx = int(((dt - period_start_utc).total_seconds()) // 86400)
        if idx < 0 or idx >= 7:
            continue
        bucket = buckets[idx]
        for it in _normalize_details(row):
            k = _map_key(it.get("type", ""))
            if not k:
                continue
            w = STRENGTH_SCORE.get(str(it.get("strength", "medium")).lower(), 0)
            bucket[k] += w

    # dominant key per day
    for b in buckets:
        dom = None
        maxv = 0
        for k in EMOTION_KEYS:
            v = int(b.get(k, 0))
            if v > maxv:
                maxv = v
                dom = k if v > 0 else None
        b["dominantKey"] = dom

    return buckets


def _build_weeks_fixed4(rows: List[Dict[str, Any]], period_start_utc: datetime) -> List[Dict[str, Any]]:
    buckets: List[Dict[str, Any]] = [
        {"index": 0, "label": "第1週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
        {"index": 1, "label": "第2週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
        {"index": 2, "label": "第3週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
        {"index": 3, "label": "第4週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
    ]

    for row in rows:
        try:
            t = row.get("created_at")
            if not t:
                continue
            s = str(t)
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
        except Exception:
            continue

        idx_raw = int(((dt - period_start_utc).total_seconds()) // (7 * 86400))
        idx = max(0, min(3, idx_raw))
        bucket = buckets[idx]

        for it in _normalize_details(row):
            k = _map_key(it.get("type", ""))
            if not k:
                continue
            w = STRENGTH_SCORE.get(str(it.get("strength", "medium")).lower(), 0)
            bucket[k] += w
            bucket["total"] += w

    return buckets


def _compute_weekly_metrics(days: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {k: 0 for k in EMOTION_KEYS}
    for d in days:
        for k in EMOTION_KEYS:
            totals[k] += int(d.get(k, 0))
    total_all = sum(totals.values())
    share_pct = {k: 0 for k in EMOTION_KEYS}
    if total_all > 0:
        for k in EMOTION_KEYS:
            share_pct[k] = int(round((totals[k] / total_all) * 100))
    # top list like JS: [["joy", 10], ...]
    top = sorted([[k, totals[k]] for k in EMOTION_KEYS], key=lambda x: x[1], reverse=True)
    return {
        "totals": totals,
        "totalAll": total_all,
        "sharePct": share_pct,
        "top": top,
        "hasData": total_all > 0,
    }


def _compute_monthly_metrics(weeks: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {k: 0 for k in EMOTION_KEYS}
    for w in weeks:
        for k in EMOTION_KEYS:
            totals[k] += int(w.get(k, 0))
    total_all = sum(totals.values())
    share_pct = {k: 0 for k in EMOTION_KEYS}
    if total_all > 0:
        for k in EMOTION_KEYS:
            share_pct[k] = int(round((totals[k] / total_all) * 100))
    return {
        "weeks": weeks,
        "totals": totals,
        "totalAll": total_all,
        "sharePct": share_pct,
        "hasData": total_all > 0,
    }


def _dominant_label(metrics: Dict[str, Any]) -> str:
    dom = metrics.get("dominantKey") or None
    if dom:
        return KEY_TO_JP.get(dom, dom)
    # fallback by totals
    totals = metrics.get("totals") or {}
    if isinstance(totals, dict):
        best = None
        bestv = 0
        for k in EMOTION_KEYS:
            v = int(totals.get(k, 0))
            if v > bestv:
                bestv = v
                best = k
        if best and bestv > 0:
            return KEY_TO_JP.get(best, best)
    return "—"


def _render_simple_report_text(
    report_type: str,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    metrics: Dict[str, Any],
    astor_text: Optional[str] = None,
) -> str:
    lines: List[str] = []
    lines.append(title)
    lines.append("")
    # Range in JST (for readability)
    try:
        s = datetime.fromisoformat(period_start_iso.replace("Z", "+00:00")).astimezone(JST)
        e = datetime.fromisoformat(period_end_iso.replace("Z", "+00:00")).astimezone(JST)
        lines.append(f"対象期間（JST）: {s.year}/{s.month}/{s.day} 00:00 〜 {e.year}/{e.month}/{e.day} 23:59")
    except Exception:
        pass
    lines.append("")
    lines.append("【感情の重み付け合計】")
    totals = metrics.get("totals") or {}
    for k in EMOTION_KEYS:
        lines.append(f"- {KEY_TO_JP.get(k, k)}: {int(totals.get(k, 0))}")
    lines.append("")
    lines.append(f"中心に出ている傾向: {_dominant_label(metrics)}")
    lines.append("")
    if report_type in ("weekly", "monthly") and astor_text:
        lines.append("【ASTOR 構造洞察（補足）】")
        lines.append(astor_text.strip())
    return "\n".join(lines).strip()


async def _generate_and_save(
    user_id: str,
    target: TargetPeriod,
    *,
    include_astor: bool,
) -> Tuple[str, Dict[str, Any], Optional[str], Optional[Dict[str, Any]]]:
    # 1) fetch emotions
    rows = await _fetch_emotion_rows(user_id, target.period_start_iso, target.period_end_iso)

    # 2) metrics
    content_json: Dict[str, Any] = {}
    astor_text: Optional[str] = None
    astor_report: Optional[Dict[str, Any]] = None
    astor_meta: Optional[Dict[str, Any]] = None
    astor_error: Optional[str] = None

    # MyWeb report v3: Standard / Structural (tier-gated)
    tier_enum = None
    if SubscriptionTier is not None and get_subscription_tier_for_user is not None:
        try:
            tier_enum = await get_subscription_tier_for_user(user_id, default=SubscriptionTier.FREE)
        except Exception:
            tier_enum = SubscriptionTier.FREE
    is_premium = bool(tier_enum == SubscriptionTier.PREMIUM) if SubscriptionTier is not None else False

    if target.report_type == "daily":
        metrics = _build_daily_metrics(rows)
        content_json["metrics"] = metrics
        text = _render_simple_report_text(
            "daily",
            target.title,
            target.period_start_iso,
            target.period_end_iso,
            metrics,
            astor_text=None,
        )
    elif target.report_type == "weekly":
        days = _build_days_fixed7(rows, target.period_start_utc)
        metrics = _compute_weekly_metrics(days)
        content_json["metrics"] = metrics
        content_json["days"] = days
        if include_astor and is_premium and generate_myweb_insight_payload is not None:
            try:
                astor_text, astor_report = generate_myweb_insight_payload(user_id=user_id, period_days=7, lang="ja")
                astor_meta = {"engine": "astor_myweb_insight", "period_days": 7, "version": "0.3"}
            except Exception as e:
                astor_error = str(e)
        if astor_text:
            content_json["astorText"] = astor_text
            if astor_meta:
                content_json["astorMeta"] = astor_meta
        if astor_error:
            content_json["astorError"] = astor_error
        text = _render_simple_report_text(
            "weekly",
            target.title,
            target.period_start_iso,
            target.period_end_iso,
            metrics,
            astor_text=astor_text,
        )
    else:
        weeks = _build_weeks_fixed4(rows, target.period_start_utc)
        metrics = _compute_monthly_metrics(weeks)
        content_json["metrics"] = metrics
        # viewer fallback support
        content_json["weeks"] = weeks
        if include_astor and is_premium and generate_myweb_insight_payload is not None:
            try:
                astor_text, astor_report = generate_myweb_insight_payload(user_id=user_id, period_days=28, lang="ja")
                astor_meta = {"engine": "astor_myweb_insight", "period_days": 28, "version": "0.3"}
            except Exception as e:
                astor_error = str(e)
        if astor_text:
            content_json["astorText"] = astor_text
            if astor_meta:
                content_json["astorMeta"] = astor_meta
        if astor_error:
            content_json["astorError"] = astor_error
        text = _render_simple_report_text(
            "monthly",
            target.title,
            target.period_start_iso,
            target.period_end_iso,
            metrics,
            astor_text=astor_text,
        )

    # 3) upsert

    # --- MyWeb report v3 structure (Standard / Structural) ---
    try:
        content_json.setdefault("reportVersion", "myweb.report.v3")
        content_json["standardReport"] = {
            "version": "myweb.standard.v1",
            "contentText": text,
        }
        if astor_report:
            content_json["structuralReport"] = astor_report
    except Exception:
        pass

    payload = {
        "user_id": user_id,
        "report_type": target.report_type,
        "period_start": target.period_start_iso,
        "period_end": target.period_end_iso,
        "title": target.title,
        "content_text": text,
        "content_json": content_json,
        "generated_at": (target.dist_utc if target.report_type in ("weekly", "monthly") else datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }
    rid = await _upsert_report(payload)
    payload["_id"] = rid
    return text, content_json, astor_text, {"report_id": rid}


def register_myweb_report_routes(app: FastAPI) -> None:
    @app.post("/myweb/reports/ensure", response_model=MyWebEnsureResponse)
    async def myweb_reports_ensure(
        req: MyWebEnsureRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> MyWebEnsureResponse:
        """
        MyWeb レポート（daily/weekly/monthly）の “配布されているべき分” を確認し、
        無ければ生成して保存する（on-demand）。

        認証: Authorization: Bearer <supabase access token>
        """
        token = _extract_bearer_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Missing authorization token")

        # resolve user_id
        user_id = await _resolve_user_id_from_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authorization token")

        now_utc = _parse_now_utc(req.now_iso)

        # NOTE: 日報(daily)はUX上は廃止方針のため、未指定時は weekly/monthly のみを ensure する。
        #       ただし後方互換のため、types に daily が明示された場合は生成を許可する。
        types = req.types or ["weekly", "monthly"]
        # normalize & unique keep order
        cleaned: List[str] = []
        for t in types:
            if t not in ("daily", "weekly", "monthly"):
                continue
            if t not in cleaned:
                cleaned.append(t)
        if not cleaned:
            cleaned = ["weekly", "monthly"]

        results: List[MyWebEnsureItem] = []

        for rt in cleaned:
            try:
                target = _build_target_period(rt, now_utc)
                existing_id = await _report_exists(
                    user_id, rt, target.period_start_iso, target.period_end_iso
                )
                if existing_id is not None and not req.force:
                    results.append(
                        MyWebEnsureItem(
                            report_type=rt,  # type: ignore
                            status="exists",
                            period_start=target.period_start_iso,
                            period_end=target.period_end_iso,
                            title=target.title,
                            report_id=existing_id,
                        )
                    )
                    continue

                # ---- Phase10: generation lock ----
                lock_acquired = True
                lock_owner = None
                lock_key = None
                if build_lock_key is not None and try_acquire_lock is not None:
                    try:
                        lock_key = build_lock_key(
                            namespace="myweb",
                            user_id=user_id,
                            report_type=rt,
                            period_start=target.period_start_iso,
                            period_end=target.period_end_iso,
                        )
                        lock_owner = (make_owner_id("myweb") if make_owner_id is not None else None)
                        lr = await try_acquire_lock(
                            lock_key=lock_key,
                            ttl_seconds=MYWEB_LOCK_TTL_SECONDS,
                            owner_id=lock_owner,
                            context={
                                "namespace": "myweb",
                                "user_id": user_id,
                                "report_type": rt,
                                "period_start": target.period_start_iso,
                                "period_end": target.period_end_iso,
                                "source": "on_demand_myweb_reports_ensure",
                            },
                        )
                        lock_acquired = bool(getattr(lr, "acquired", False))
                        lock_owner = getattr(lr, "owner_id", lock_owner)
                    except Exception as _exc:
                        # Lock is best-effort: if anything goes wrong, proceed without blocking.
                        lock_acquired = True

                if not lock_acquired:
                    # Someone else is generating. Wait briefly for the row to appear.
                    waited_id = None
                    if poll_until is not None and MYWEB_LOCK_WAIT_SECONDS > 0:
                        waited_id = await poll_until(
                            lambda: _report_exists(
                                user_id,
                                rt,
                                target.period_start_iso,
                                target.period_end_iso,
                            ),
                            timeout_seconds=MYWEB_LOCK_WAIT_SECONDS,
                        )
                    if waited_id is not None:
                        results.append(
                            MyWebEnsureItem(
                                report_type=rt,  # type: ignore
                                status="exists",
                                period_start=target.period_start_iso,
                                period_end=target.period_end_iso,
                                title=target.title,
                                report_id=waited_id,
                            )
                        )
                        continue
                    raise HTTPException(status_code=409, detail="Report generation is in progress")

                try:
                    _text, _cjson, _astor_text, meta = await _generate_and_save(
                        user_id,
                        target,
                        include_astor=req.include_astor,
                    )
                finally:
                    if lock_key and release_lock is not None:
                        await release_lock(lock_key=lock_key, owner_id=lock_owner)
                results.append(
                    MyWebEnsureItem(
                        report_type=rt,  # type: ignore
                        status="generated",
                        period_start=target.period_start_iso,
                        period_end=target.period_end_iso,
                        title=target.title,
                        report_id=(meta or {}).get("report_id"),
                    )
                )
            except HTTPException as he:
                results.append(
                    MyWebEnsureItem(
                        report_type=rt,  # type: ignore
                        status="error",
                        period_start="",
                        period_end="",
                        title="",
                        error=str(he.detail),
                    )
                )
            except Exception as e:
                results.append(
                    MyWebEnsureItem(
                        report_type=rt,  # type: ignore
                        status="error",
                        period_start="",
                        period_end="",
                        title="",
                        error=str(e),
                    )
                )

        return MyWebEnsureResponse(
            user_id=user_id,
            now_iso=now_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
            results=results,
        )
