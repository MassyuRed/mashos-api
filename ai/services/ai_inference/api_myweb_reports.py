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
ANALYSIS_RESULTS_TABLE = (os.getenv("ANALYSIS_RESULTS_TABLE") or "analysis_results").strip() or "analysis_results"

# Governance / snapshots
MATERIAL_SNAPSHOTS_TABLE = (os.getenv("MATERIAL_SNAPSHOTS_TABLE") or "material_snapshots").strip() or "material_snapshots"
SNAPSHOT_SCOPE_DEFAULT = (os.getenv("SNAPSHOT_SCOPE_DEFAULT") or "global").strip() or "global"

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

TIME_BUCKET_ORDER: Tuple[str, ...] = ("0-6", "6-12", "12-18", "18-24")
TIME_BUCKET_LABELS: Dict[str, str] = {
    "0-6": "0-6",
    "6-12": "6-12",
    "12-18": "12-18",
    "18-24": "18-24",
}
_TIME_BUCKET_ALIASES: Dict[str, str] = {
    "0-6": "0-6",
    "00-06": "0-6",
    "00:00-06:00": "0-6",
    "0_6": "0-6",
    "night": "0-6",
    "late_night": "0-6",
    "overnight": "0-6",
    "6-12": "6-12",
    "06-12": "6-12",
    "06:00-12:00": "6-12",
    "6_12": "6-12",
    "morning": "6-12",
    "12-18": "12-18",
    "12:00-18:00": "12-18",
    "12_18": "12-18",
    "afternoon": "12-18",
    "daytime": "12-18",
    "18-24": "18-24",
    "18:00-24:00": "18-24",
    "18_24": "18-24",
    "evening": "18-24",
    "night_evening": "18-24",
}


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
    report_id: Optional[str] = None
    error: Optional[str] = None


class MyWebEnsureResponse(BaseModel):
    user_id: str
    now_iso: str
    results: List[MyWebEnsureItem]




class MyWebReportRecord(BaseModel):
    id: str = Field(..., description="myweb_reports.id (UUID)")
    report_type: str = Field(..., description="daily/weekly/monthly")
    period_start: str = Field(..., description="UTC ISO (Z)")
    period_end: str = Field(..., description="UTC ISO (Z)")
    title: Optional[str] = Field(default=None)
    content_text: Optional[str] = Field(default=None)
    content_json: Dict[str, Any] = Field(default_factory=dict)
    generated_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)


class MyWebReadyReportsResponse(BaseModel):
    status: str = Field(default="ok")
    user_id: str = Field(..., description="viewer user_id")
    report_type: str = Field(..., description="requested type")
    viewer_tier: str = Field(..., description="free/plus/premium")
    items: List[MyWebReportRecord] = Field(default_factory=list)

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



async def _fetch_latest_snapshot_hash(user_id: str, *, scope: str, snapshot_type: str) -> Optional[str]:
    """Fetch latest material snapshot source_hash (best-effort).

    - Returns None if snapshots table is missing or no rows.
    - This API uses service_role and is meant for internal governance checks.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return None
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "public"

    try:
        resp = await _sb_get(
            f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
            params=[
                ("select", "source_hash,created_at"),
                ("user_id", f"eq.{uid}"),
                ("scope", f"eq.{sc}"),
                ("snapshot_type", f"eq.{st}"),
                ("order", "created_at.desc"),
                ("limit", "1"),
            ],
        )
    except Exception:
        return None


async def _fetch_latest_snapshot_row(
    user_id: str,
    *,
    scope: str,
    snapshot_type: str,
) -> Optional[Dict[str, Any]]:
    """Fetch latest material snapshot row (payload + source_hash).

    Returns None if snapshots table is missing or no rows.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return None
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "public"

    try:
        resp = await _sb_get(
            f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
            params=[
                ("select", "id,source_hash,created_at,payload"),
                ("user_id", f"eq.{uid}"),
                ("scope", f"eq.{sc}"),
                ("snapshot_type", f"eq.{st}"),
                ("order", "created_at.desc"),
                ("limit", "1"),
            ],
        )
    except Exception:
        return None

    if resp.status_code not in (200, 206):
        return None
    try:
        rows = resp.json()
    except Exception:
        return None
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


async def _fetch_analysis_result(
    user_id: str,
    *,
    snapshot_id: str,
    analysis_type: str,
    analysis_stage: str = "standard",
    scope: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    sid = str(snapshot_id or "").strip()
    at = str(analysis_type or "").strip()
    stage = str(analysis_stage or "").strip() or "standard"
    if not uid or not sid or not at:
        return None

    params: List[Tuple[str, str]] = [
        ("select", "id,target_user_id,snapshot_id,analysis_type,scope,analysis_stage,analysis_version,source_hash,payload,created_at,updated_at"),
        ("target_user_id", f"eq.{uid}"),
        ("snapshot_id", f"eq.{sid}"),
        ("analysis_type", f"eq.{at}"),
        ("analysis_stage", f"eq.{stage}"),
        ("order", "updated_at.desc"),
        ("limit", "1"),
    ]
    sc = str(scope or "").strip()
    if sc:
        params.append(("scope", f"eq.{sc}"))

    try:
        resp = await _sb_get(f"/rest/v1/{ANALYSIS_RESULTS_TABLE}", params=params)
    except Exception:
        return None

    if resp.status_code not in (200, 206):
        return None
    try:
        rows = resp.json()
    except Exception:
        return None
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


def _range_line_jst(period_start_iso: str, period_end_iso: str) -> Optional[str]:
    try:
        s = datetime.fromisoformat(period_start_iso.replace("Z", "+00:00")).astimezone(JST)
        e = datetime.fromisoformat(period_end_iso.replace("Z", "+00:00")).astimezone(JST)
        return f"対象期間（JST）: {s.year}/{s.month}/{s.day} 00:00 〜 {e.year}/{e.month}/{e.day} 23:59"
    except Exception:
        return None

def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return int(default)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _normalize_time_bucket_key(value: Any) -> Optional[str]:
    s = str(value or "").strip()
    if not s:
        return None
    return _TIME_BUCKET_ALIASES.get(s, _TIME_BUCKET_ALIASES.get(s.lower()))


def _coerce_emotion_map(raw: Any) -> Dict[str, int]:
    out = {k: 0 for k in EMOTION_KEYS}
    if not isinstance(raw, dict):
        return out
    for k in EMOTION_KEYS:
        out[k] = _coerce_int(raw.get(k), 0)
    return out


def _dominant_key_from_map(raw: Any) -> Optional[str]:
    m = _coerce_emotion_map(raw)
    best_key: Optional[str] = None
    best_value = 0
    for k in EMOTION_KEYS:
        v = _coerce_int(m.get(k), 0)
        if v > best_value:
            best_value = v
            best_key = k if v > 0 else None
    return best_key


def _first_non_empty_emotion_map(*raw_maps: Any) -> Dict[str, int]:
    for raw in raw_maps:
        if not isinstance(raw, dict):
            continue
        m = _coerce_emotion_map(raw)
        if sum(m.values()) > 0:
            return m
    return {}


def _pick_top_share_items(share_map: Dict[str, int], *, limit: int = 2) -> List[Tuple[str, int]]:
    if not isinstance(share_map, dict):
        return []
    items: List[Tuple[str, int]] = []
    for k in EMOTION_KEYS:
        try:
            v = int(share_map.get(k, 0) or 0)
        except Exception:
            v = 0
        if v > 0:
            items.append((k, v))
    items.sort(key=lambda x: x[1], reverse=True)
    return items[: max(1, int(limit or 1))]


def _default_time_bucket_row(bucket_key: str) -> Dict[str, Any]:
    return {
        "bucket": bucket_key,
        "label": TIME_BUCKET_LABELS.get(bucket_key, bucket_key),
        "inputCount": 0,
        "weightedTotal": 0,
        "counts": {k: 0 for k in EMOTION_KEYS},
        "weightedCounts": {k: 0 for k in EMOTION_KEYS},
        "sharePct": {k: 0 for k in EMOTION_KEYS},
        "dominantKey": None,
    }


def _normalize_time_bucket_rows(raw: Any) -> List[Dict[str, Any]]:
    if raw is None:
        return []

    items: List[Tuple[str, Any]] = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            items.append((str(key), value))
    elif isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict):
                key = str(entry.get("bucket") or entry.get("key") or entry.get("label") or "")
                items.append((key, entry))
    else:
        return []

    bucket_map: Dict[str, Dict[str, Any]] = {}
    for raw_key, value in items:
        bucket_key = _normalize_time_bucket_key(raw_key)
        if bucket_key is None and isinstance(value, dict):
            bucket_key = _normalize_time_bucket_key(
                value.get("bucket") or value.get("key") or value.get("label")
            )
        if bucket_key is None:
            continue

        row = _default_time_bucket_row(bucket_key)
        data = value if isinstance(value, dict) else {}

        counts = _coerce_emotion_map(
            data.get("counts")
            or data.get("rawCounts")
            or data.get("inputCounts")
            or data.get("input_counts")
        )
        weighted_counts = _coerce_emotion_map(
            data.get("weightedCounts")
            or data.get("weighted_counts")
            or data.get("weights")
            or data.get("emotionWeights")
            or data.get("weighted")
        )
        share_pct = _coerce_emotion_map(data.get("sharePct") or data.get("share_pct"))

        input_count = _coerce_int(
            data.get("inputCount")
            or data.get("input_count")
            or data.get("count")
            or data.get("events")
            or 0
        )
        weighted_total = _coerce_int(
            data.get("weightedTotal") or data.get("weighted_total") or 0
        )
        if weighted_total <= 0:
            weighted_total = sum(weighted_counts.values())
        if input_count <= 0:
            input_count = sum(counts.values())

        if not any(share_pct.values()) and weighted_total > 0:
            share_pct = {
                k: int(round((_coerce_int(weighted_counts.get(k), 0) / weighted_total) * 100))
                for k in EMOTION_KEYS
            }

        dominant_key = str(
            data.get("dominantKey")
            or data.get("dominant_key")
            or data.get("dominant")
            or ""
        ).strip() or _dominant_key_from_map(weighted_counts)

        row.update(
            {
                "inputCount": input_count,
                "weightedTotal": weighted_total,
                "counts": counts,
                "weightedCounts": weighted_counts,
                "sharePct": share_pct,
                "dominantKey": dominant_key or None,
            }
        )
        bucket_map[bucket_key] = row

    if not bucket_map:
        return []

    return [bucket_map.get(bucket_key, _default_time_bucket_row(bucket_key)) for bucket_key in TIME_BUCKET_ORDER]


def _extract_time_bucket_rows(*, snapshot_views: Dict[str, Any], analysis_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    views = snapshot_views if isinstance(snapshot_views, dict) else {}
    payload = analysis_payload if isinstance(analysis_payload, dict) else {}
    weekly_snapshot = payload.get("weekly_snapshot") if isinstance(payload.get("weekly_snapshot"), dict) else {}
    monthly_report = payload.get("monthly_report") if isinstance(payload.get("monthly_report"), dict) else {}

    candidates = [
        views.get("timeBuckets"),
        views.get("time_buckets"),
        payload.get("timeBuckets"),
        payload.get("time_buckets"),
        weekly_snapshot.get("timeBuckets"),
        weekly_snapshot.get("time_buckets"),
        monthly_report.get("timeBuckets"),
        monthly_report.get("time_buckets"),
    ]
    for candidate in candidates:
        rows = _normalize_time_bucket_rows(candidate)
        if rows:
            return rows
    return []


def _find_peak_time_bucket(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    best_count = -1
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        count = _coerce_int(row.get("inputCount"), 0)
        if count > best_count:
            best = row
            best_count = count
    if best_count <= 0:
        return None
    return best


def _build_standard_summary_object(
    *,
    report_type: str,
    analysis_payload: Dict[str, Any],
    snapshot_summary: Dict[str, Any],
    snapshot_views: Dict[str, Any],
    light_text: str,
) -> Dict[str, Any]:
    payload = analysis_payload if isinstance(analysis_payload, dict) else {}
    views = snapshot_views if isinstance(snapshot_views, dict) else {}
    snap_summary = snapshot_summary if isinstance(snapshot_summary, dict) else {}

    movement = views.get("movement") if isinstance(views.get("movement"), dict) else {}
    day = views.get("day") if isinstance(views.get("day"), dict) else {}
    weekly_snapshot = payload.get("weekly_snapshot") if isinstance(payload.get("weekly_snapshot"), dict) else {}
    monthly_report = payload.get("monthly_report") if isinstance(payload.get("monthly_report"), dict) else {}
    time_buckets = _extract_time_bucket_rows(snapshot_views=views, analysis_payload=payload)
    peak_bucket = _find_peak_time_bucket(time_buckets)

    evidence_items: List[Dict[str, str]] = []
    next_points: List[str] = []
    structural_comment = ""
    gentle_comment = ""

    if report_type == "daily":
        metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        share_map = _first_non_empty_emotion_map(metrics.get("sharePct"))
        top_items = _pick_top_share_items(share_map, limit=2)
        dominant_key = str(metrics.get("dominantKey") or "").strip() or (top_items[0][0] if top_items else None)
        dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"
        total_all = _coerce_int(metrics.get("totalAll"), 0)
        movement_key = str(movement.get("key") or "").strip()

        if total_all > 0:
            structural_comment = f"昨日は「{dominant_label}」が中心に現れていました。"
            if peak_bucket and peak_bucket.get("inputCount"):
                peak_label = str(peak_bucket.get("label") or peak_bucket.get("bucket") or "")
                peak_dom = KEY_TO_JP.get(str(peak_bucket.get("dominantKey") or ""), str(peak_bucket.get("dominantKey") or ""))
                if peak_dom and peak_dom != "":
                    structural_comment += f"入力は {peak_label} に集まりやすく、{peak_label} では「{peak_dom}」の比重が高めでした。"
            if movement_key == "swing":
                structural_comment += "前日から中心感情の切り替わりも見られます。"
        else:
            structural_comment = "昨日は入力が少なめで、はっきりした傾向はまだ読み取りにくい日でした。"

        if peak_bucket and peak_bucket.get("inputCount"):
            peak_label = str(peak_bucket.get("label") or peak_bucket.get("bucket") or "")
            gentle_comment = f"{peak_label} の前後で何を考えていたかを短く振り返ると、感情の流れが見えやすくなります。"
            next_points.append(f"{peak_label} の入力前後にあった出来事や受け止め方を一言残してみてください。")
        elif dominant_key:
            gentle_comment = f"「{dominant_label}」が強く出た場面の共通点を一言で残すと、次の比較がしやすくなります。"
            next_points.append(f"「{dominant_label}」が強く出た時間帯の共通点を探してみてください。")

        if dominant_key and top_items:
            evidence_items.append({"text": f"昨日は「{dominant_label}」の比重が最も高めでした。"})
        if peak_bucket and peak_bucket.get("inputCount"):
            evidence_items.append({"text": f"入力は {peak_bucket.get('label') or peak_bucket.get('bucket')} に {int(peak_bucket.get('inputCount') or 0)} 件ありました。"})
        if movement_key:
            evidence_items.append({"text": f"前日比では「{_render_daily_motion_line(movement)}」の動きが見られます。"})

    elif report_type == "weekly":
        snapshot_metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        share_map = _first_non_empty_emotion_map(weekly_snapshot.get("share"), snapshot_metrics.get("sharePct"))
        weighted_counts = _first_non_empty_emotion_map(weekly_snapshot.get("wcounts"), snapshot_metrics.get("totals"))
        top_items = _pick_top_share_items(share_map, limit=2)
        dominant_key = _dominant_key_from_map(weighted_counts) or (top_items[0][0] if top_items else None)
        dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"
        n_events = _coerce_int(weekly_snapshot.get("n_events") or snap_summary.get("emotions_public") or snap_summary.get("emotions_total"), 0)
        alternation_rate = _coerce_float(weekly_snapshot.get("alternation_rate"), 0.0)

        if dominant_key:
            structural_comment = f"今週は「{dominant_label}」が中心に現れていました。"
        elif n_events > 0:
            structural_comment = f"今週は {n_events} 件の入力をもとに、感情の傾向を観測できます。"
        else:
            structural_comment = "今週は入力が少なめで、はっきりした傾向は読み取りにくい週でした。"

        if peak_bucket and peak_bucket.get("inputCount"):
            peak_label = str(peak_bucket.get("label") or peak_bucket.get("bucket") or "")
            peak_dom_key = str(peak_bucket.get("dominantKey") or "").strip() or None
            peak_dom_label = KEY_TO_JP.get(peak_dom_key, peak_dom_key) if peak_dom_key else None
            structural_comment += f" 入力は {peak_label} に集まりやすく"
            if peak_dom_label:
                structural_comment += f"、{peak_label} では「{peak_dom_label}」の比重が高めでした。"
            else:
                structural_comment += "、時間帯ごとの偏りも見られます。"

        if alternation_rate >= 0.55:
            structural_comment += " 感情の切り替わりは比較的多めでした。"
        elif 0 < alternation_rate <= 0.25:
            structural_comment += " 感情の切り替わりは比較的穏やかでした。"

        if peak_bucket and peak_bucket.get("inputCount"):
            peak_label = str(peak_bucket.get("label") or peak_bucket.get("bucket") or "")
            gentle_comment = f"{peak_label} の前後で何を考えていたかを短く振り返ると、週の流れが見えやすくなります。"
            next_points.append(f"{peak_label} に入力が集まる日の共通点を一言で残してみてください。")
        elif dominant_key:
            gentle_comment = f"「{dominant_label}」が強く出た日を見返すと、今週の感情の流れをつかみやすくなります。"
            next_points.append(f"「{dominant_label}」が強く出た日の前後を振り返ってみてください。")

        if dominant_key:
            evidence_items.append({"text": f"全体では「{dominant_label}」の比重が最も高めでした。"})
        if len(top_items) >= 2:
            second_label = KEY_TO_JP.get(top_items[1][0], top_items[1][0])
            evidence_items.append({"text": f"次に目立ったのは「{second_label}」で、全体の約{top_items[1][1]}%でした。"})
        if peak_bucket and peak_bucket.get("inputCount"):
            evidence_items.append({"text": f"入力は {peak_bucket.get('label') or peak_bucket.get('bucket')} に {int(peak_bucket.get('inputCount') or 0)} 件ありました。"})
        if alternation_rate > 0:
            evidence_items.append({"text": f"感情の切り替わり率は {alternation_rate:.2f} でした。"})

    else:
        snapshot_metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        weeks = views.get("weeks") if isinstance(views.get("weeks"), list) else []
        share_map = _first_non_empty_emotion_map(snapshot_metrics.get("sharePct"))
        totals_map = _first_non_empty_emotion_map(snapshot_metrics.get("totals"))
        dominant_key = _dominant_key_from_map(totals_map) or _dominant_key_from_map(share_map)
        dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"

        peak_week = None
        peak_week_total = -1
        week_dominants: List[str] = []
        calm_first_half = 0
        calm_second_half = 0
        for idx, week in enumerate(weeks or []):
            if not isinstance(week, dict):
                continue
            total = _coerce_int(week.get("total"), 0)
            if total <= 0:
                total = sum(_coerce_int(week.get(k), 0) for k in EMOTION_KEYS)
            if total > peak_week_total:
                peak_week_total = total
                peak_week = week
            week_dom_key = _dominant_key_from_map(week)
            week_dominants.append(str(week_dom_key or ""))
            if idx < 2:
                calm_first_half += _coerce_int(week.get("calm"), 0)
            else:
                calm_second_half += _coerce_int(week.get("calm"), 0)

        if dominant_key:
            structural_comment = f"今月は「{dominant_label}」が月全体の中心でした。"
        else:
            structural_comment = "今月は週ごとの変化を見ながら、月全体の傾向を観測できます。"

        if peak_week and peak_week_total > 0:
            peak_week_label = str(peak_week.get("label") or "ある週")
            peak_week_dom = KEY_TO_JP.get(_dominant_key_from_map(peak_week), _dominant_key_from_map(peak_week))
            if peak_week_dom:
                structural_comment += f" {peak_week_label} は「{peak_week_dom}」の比重が高く、動きが強めの週でした。"
            else:
                structural_comment += f" {peak_week_label} に動きが集まりやすい月でした。"

        if peak_bucket and peak_bucket.get("inputCount"):
            peak_label = str(peak_bucket.get("label") or peak_bucket.get("bucket") or "")
            structural_comment += f" 時間帯では {peak_label} の入力が最も多めでした。"

        if calm_second_half > calm_first_half and calm_second_half > 0:
            structural_comment += " 後半にかけて「平穏」が増え、整え直しの動きも見られます。"

        if dominant_key:
            gentle_comment = f"週ごとの違いと時間帯の偏りを見比べると、「{dominant_label}」がどの場面で強く出やすいかを追いやすくなります。"
        else:
            gentle_comment = "週ごとの変化と時間帯の偏りを並べて見ると、月の流れがつかみやすくなります。"

        if peak_week and peak_week_total > 0:
            next_points.append(f"{peak_week.get('label') or '動きが強い週'} の前後で、気持ちの切り替わりが起きた場面を振り返ってみてください。")
        if peak_bucket and peak_bucket.get("inputCount"):
            next_points.append(f"{peak_bucket.get('label') or peak_bucket.get('bucket')} の入力前後に、どんな受け止め方が多いかを見比べてみてください。")

        if dominant_key:
            evidence_items.append({"text": f"月全体では「{dominant_label}」の比重が最も高めでした。"})
        if peak_week and peak_week_total > 0:
            evidence_items.append({"text": f"{peak_week.get('label') or 'ある週'} は合計 {peak_week_total} と、今月で最も動きが強めでした。"})
        if peak_bucket and peak_bucket.get("inputCount"):
            evidence_items.append({"text": f"入力は {peak_bucket.get('label') or peak_bucket.get('bucket')} に {int(peak_bucket.get('inputCount') or 0)} 件ありました。"})
        if calm_second_half > calm_first_half and calm_second_half > 0:
            evidence_items.append({"text": "後半にかけて『平穏』の比重が増えていました。"})

    return {
        "structuralComment": structural_comment.strip() or None,
        "gentleComment": gentle_comment.strip() or None,
        "nextPoints": [str(x).strip() for x in next_points if str(x).strip()][:4],
        "evidence": {
            "items": [item for item in evidence_items if isinstance(item, dict) and str(item.get("text") or "").strip()][:4]
        },
        "compositionMode": "additive" if report_type == "daily" else "replace",
        "source": "api_hybrid_summary",
    }


def _render_standard_text_from_summary(
    *,
    title: str,
    report_type: str,
    period_start_iso: str,
    period_end_iso: str,
    summary: Dict[str, Any],
    light_text: str = "",
) -> str:
    structural_comment = str((summary or {}).get("structuralComment") or "").strip()
    gentle_comment = str((summary or {}).get("gentleComment") or "").strip()
    next_points = (summary or {}).get("nextPoints") if isinstance((summary or {}).get("nextPoints"), list) else []
    evidence = (summary or {}).get("evidence") if isinstance((summary or {}).get("evidence"), dict) else {}
    evidence_items = evidence.get("items") if isinstance(evidence.get("items"), list) else []

    if report_type == "daily" and str(light_text or "").strip():
        lines: List[str] = [str(light_text).strip()]
        extra_added = False
        if structural_comment or evidence_items or gentle_comment or next_points:
            lines.append("")
            lines.append("【もう少し詳しく】")
            extra_added = True
        if structural_comment:
            lines.append(structural_comment)
        if evidence_items:
            for item in evidence_items[:3]:
                if isinstance(item, dict):
                    t = str(item.get("text") or "").strip()
                    if t:
                        lines.append(f"・{t}")
        if gentle_comment:
            lines.append(gentle_comment)
        if next_points:
            lines.append("")
            lines.append("【次の観測】")
            for point in next_points[:2]:
                s = str(point or "").strip()
                if s:
                    lines.append(f"・{s}")
        if extra_added:
            lines.append("")
            lines.append("【注記】")
            lines.append("このレポートは、入力から見える変化をまとめた『観測』であり、診断や断定を目的としたものではありません。")
        return "\n".join(lines).strip()

    if report_type == "daily":
        summary_title = "【今日の構造サマリー】"
    elif report_type == "weekly":
        summary_title = "【今週の構造サマリー】"
    else:
        summary_title = "【今月の構造サマリー】"

    lines = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.append("")
    lines.append(summary_title)
    if structural_comment:
        lines.append(structural_comment)
    else:
        lines.append("今回の構造サマリーはまだ十分に生成されていません。")
    lines.append("")

    if evidence_items:
        lines.append("【観測ポイント】")
        for item in evidence_items[:4]:
            if isinstance(item, dict):
                t = str(item.get("text") or "").strip()
                if t:
                    lines.append(f"- {t}")
        lines.append("")

    if gentle_comment:
        lines.append("【やさしい視点】")
        lines.append(gentle_comment)
        lines.append("")

    if next_points:
        lines.append("【次の観測】")
        for point in next_points[:4]:
            s = str(point or "").strip()
            if s:
                lines.append(f"- {s}")
        lines.append("")

    lines.append("【注記】")
    lines.append("このレポートは、入力から見える変化や傾向をまとめた『観測』であり、診断や断定を目的としたものではありません。")
    return "\n".join(lines).strip()


def _render_analysis_standard_text(
    *,
    title: str,
    report_type: str,
    period_start_iso: str,
    period_end_iso: str,
    analysis_payload: Dict[str, Any],
) -> str:
    payload = analysis_payload if isinstance(analysis_payload, dict) else {}
    narrative = payload.get("narrative") if isinstance(payload.get("narrative"), dict) else {}
    structural_comment = str(narrative.get("structural_comment") or "").strip()
    gentle_comment = str(narrative.get("gentle_comment") or "").strip()
    next_points = narrative.get("next_points") if isinstance(narrative.get("next_points"), list) else []
    evidence = narrative.get("evidence") if isinstance(narrative.get("evidence"), dict) else {}
    evidence_items = evidence.get("items") if isinstance(evidence.get("items"), list) else []

    if report_type == "daily":
        summary_title = "【今日の構造サマリー】"
    elif report_type == "weekly":
        summary_title = "【今週の構造サマリー】"
    else:
        summary_title = "【今月の構造サマリー】"

    if not structural_comment:
        if report_type == "weekly":
            ws = payload.get("weekly_snapshot") if isinstance(payload.get("weekly_snapshot"), dict) else {}
            try:
                n_events = int(ws.get("n_events") or 0)
            except Exception:
                n_events = 0
            if n_events > 0:
                structural_comment = f"この期間は {n_events} 件の感情入力が構造分析に使われました。数値とグラフから、感情の傾向と推移を観測できます。"
        elif report_type == "monthly":
            mr = payload.get("monthly_report") if isinstance(payload.get("monthly_report"), dict) else {}
            weeks = mr.get("weeks") if isinstance(mr.get("weeks"), list) else []
            if weeks:
                structural_comment = "この期間は週ごとの構造変化をまとめています。数値とグラフから、感情の傾向と推移を観測できます。"
        elif report_type == "daily":
            try:
                n_entries = int(payload.get("entry_count") or 0)
            except Exception:
                n_entries = 0
            if n_entries > 0:
                structural_comment = f"この日は {n_entries} 件の感情入力が構造分析に使われました。時間帯ごとの変化を中心に観測できます。"

    lines: List[str] = []
    lines.append(title)
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.append("")

    lines.append(summary_title)
    if structural_comment:
        lines.append(structural_comment)
    else:
        lines.append("今回の構造サマリーはまだ十分に生成されていません。")
    lines.append("")

    if evidence_items:
        lines.append("【観測ポイント】")
        for it in evidence_items[:4]:
            if not isinstance(it, dict):
                continue
            t = str(it.get("text") or "").strip()
            if t:
                lines.append(f"- {t}")
        lines.append("")

    if gentle_comment:
        lines.append("【やさしい視点】")
        lines.append(gentle_comment)
        lines.append("")

    if next_points:
        lines.append("【次の観測】")
        for p in next_points[:4]:
            s = str(p or "").strip()
            if s:
                lines.append(f"- {s}")
        lines.append("")

    lines.append("【注記】")
    lines.append("このレポートは、入力から見える変化や傾向をまとめた『観測』であり、診断や断定を目的としたものではありません。")
    return "\n".join(lines).strip()


def _build_standard_report_payload(
    *,
    report_type: str,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    analysis_payload: Dict[str, Any],
    snapshot_summary: Optional[Dict[str, Any]] = None,
    snapshot_views: Optional[Dict[str, Any]] = None,
    light_text: str = "",
) -> Dict[str, Any]:
    payload = analysis_payload if isinstance(analysis_payload, dict) else {}
    views = snapshot_views if isinstance(snapshot_views, dict) else {}
    snap_summary = snapshot_summary if isinstance(snapshot_summary, dict) else {}
    narrative = payload.get("narrative") if isinstance(payload.get("narrative"), dict) else {}

    has_snapshot_views = bool(views)
    has_payload = bool(payload)
    standard_report: Dict[str, Any] = {
        "version": "myweb.standard.v3" if (has_payload or has_snapshot_views) else "myweb.standard.v1",
        "displayMode": "text" if report_type == "daily" else "graph_text",
        "reportType": str(report_type or ""),
    }

    summary = _build_standard_summary_object(
        report_type=report_type,
        analysis_payload=payload,
        snapshot_summary=snap_summary,
        snapshot_views=views,
        light_text=light_text,
    )
    standard_text = _render_standard_text_from_summary(
        title=title,
        report_type=report_type,
        period_start_iso=period_start_iso,
        period_end_iso=period_end_iso,
        summary=summary,
        light_text=light_text,
    )
    standard_report["contentText"] = str(standard_text or light_text or "")

    metrics: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    timeline: Any = []
    time_buckets = _extract_time_bucket_rows(snapshot_views=views, analysis_payload=payload)

    if report_type == "daily":
        metrics_src = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        day = views.get("day") if isinstance(views.get("day"), dict) else {}
        movement = views.get("movement") if isinstance(views.get("movement"), dict) else {}
        entry_count = _coerce_int(payload.get("entry_count") or snap_summary.get("emotions_public") or snap_summary.get("emotions_total"), 0)
        metrics = {
            "entryCount": entry_count,
            "share": metrics_src.get("sharePct") if isinstance(metrics_src.get("sharePct"), dict) else {},
            "weightedCounts": metrics_src.get("totals") if isinstance(metrics_src.get("totals"), dict) else {},
            "totalAll": metrics_src.get("totalAll"),
        }
        features = {
            "day": day,
            "movement": movement,
            "snapshotRef": payload.get("snapshot_ref") if isinstance(payload.get("snapshot_ref"), dict) else {},
            "period": payload.get("period") if isinstance(payload.get("period"), dict) else {},
        }
        if time_buckets:
            features["timeBuckets"] = time_buckets
            features["timeBucketMode"] = "weighted_count"
            features["timeBucketScope"] = "snapshot"
        timeline = payload.get("timeline") if isinstance(payload.get("timeline"), list) else []

    elif report_type == "weekly":
        ws = payload.get("weekly_snapshot") if isinstance(payload.get("weekly_snapshot"), dict) else {}
        snapshot_metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        days = views.get("days") if isinstance(views.get("days"), list) else []
        metrics = {
            "eventCount": ws.get("n_events") or snap_summary.get("emotions_public") or snap_summary.get("emotions_total"),
            "alternationRate": ws.get("alternation_rate"),
            "entropy": ws.get("entropy"),
            "giniSimpson": ws.get("gini_simpson"),
            "share": ws.get("share") if isinstance(ws.get("share"), dict) else (snapshot_metrics.get("sharePct") if isinstance(snapshot_metrics.get("sharePct"), dict) else {}),
            "counts": ws.get("counts") if isinstance(ws.get("counts"), dict) else (snapshot_metrics.get("totals") if isinstance(snapshot_metrics.get("totals"), dict) else {}),
            "weightedCounts": ws.get("wcounts") if isinstance(ws.get("wcounts"), dict) else (snapshot_metrics.get("totals") if isinstance(snapshot_metrics.get("totals"), dict) else {}),
            "totalAll": snapshot_metrics.get("totalAll"),
        }
        features = {
            "days": days,
            "runStats": ws.get("run_stats") if isinstance(ws.get("run_stats"), dict) else {},
            "intensity": ws.get("intensity") if isinstance(ws.get("intensity"), dict) else {},
            "motifs": ws.get("motifs") if isinstance(ws.get("motifs"), list) else [],
            "motifCounts": ws.get("motif_counts") if isinstance(ws.get("motif_counts"), dict) else {},
            "center2d": ws.get("center2d") if isinstance(ws.get("center2d"), dict) else {},
            "keywords": ws.get("keywords") if isinstance(ws.get("keywords"), list) else [],
            "snapshotRef": payload.get("snapshot_ref") if isinstance(payload.get("snapshot_ref"), dict) else {},
            "period": payload.get("period") if isinstance(payload.get("period"), dict) else {},
        }
        if time_buckets:
            features["timeBuckets"] = time_buckets
            features["timeBucketMode"] = "weighted_count"
            features["timeBucketScope"] = "snapshot"
            metrics["timeBucketInputTotal"] = sum(_coerce_int(row.get("inputCount"), 0) for row in time_buckets)
        timeline = ws.get("daily_share") if isinstance(ws.get("daily_share"), list) else days

    elif report_type == "monthly":
        mr = payload.get("monthly_report") if isinstance(payload.get("monthly_report"), dict) else {}
        snapshot_metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        weeks = views.get("weeks") if isinstance(views.get("weeks"), list) else []
        weekly_breakdown: List[Dict[str, Any]] = []
        for week in weeks:
            if not isinstance(week, dict):
                continue
            week_total = _coerce_int(week.get("total"), 0)
            if week_total <= 0:
                week_total = sum(_coerce_int(week.get(k), 0) for k in EMOTION_KEYS)
            week_dom = _dominant_key_from_map(week)
            weekly_breakdown.append(
                {
                    "label": str(week.get("label") or "週"),
                    "total": week_total,
                    "dominantKey": week_dom,
                    "dominantLabel": KEY_TO_JP.get(week_dom, week_dom) if week_dom else None,
                }
            )

        metrics = {
            "share": snapshot_metrics.get("sharePct") if isinstance(snapshot_metrics.get("sharePct"), dict) else {},
            "counts": snapshot_metrics.get("totals") if isinstance(snapshot_metrics.get("totals"), dict) else {},
            "weightedCounts": snapshot_metrics.get("totals") if isinstance(snapshot_metrics.get("totals"), dict) else {},
            "totalAll": snapshot_metrics.get("totalAll"),
            "shareTrend": mr.get("share_trend") if isinstance(mr.get("share_trend"), list) else [],
            "alternationTrend": mr.get("alternation_trend") if isinstance(mr.get("alternation_trend"), list) else [],
            "intensityStdTrend": mr.get("intensity_std_trend") if isinstance(mr.get("intensity_std_trend"), list) else [],
            "centerShift": mr.get("center_shift") if isinstance(mr.get("center_shift"), dict) else {},
        }
        features = {
            "weeks": weeks,
            "weeklyBreakdown": weekly_breakdown,
            "motifTrend": mr.get("motif_trend") if isinstance(mr.get("motif_trend"), list) else [],
            "snapshotRef": payload.get("snapshot_ref") if isinstance(payload.get("snapshot_ref"), dict) else {},
            "period": payload.get("period") if isinstance(payload.get("period"), dict) else {},
        }
        if time_buckets:
            features["timeBuckets"] = time_buckets
            features["timeBucketMode"] = "weighted_count"
            features["timeBucketScope"] = "snapshot"
            metrics["timeBucketInputTotal"] = sum(_coerce_int(row.get("inputCount"), 0) for row in time_buckets)
        timeline = mr.get("share_trend") if isinstance(mr.get("share_trend"), list) else weeks

    if not summary.get("structuralComment") and isinstance(narrative.get("structural_comment"), str):
        summary["structuralComment"] = str(narrative.get("structural_comment") or "").strip() or None
    if not summary.get("gentleComment") and isinstance(narrative.get("gentle_comment"), str):
        summary["gentleComment"] = str(narrative.get("gentle_comment") or "").strip() or None
    if not summary.get("nextPoints") and isinstance(narrative.get("next_points"), list):
        summary["nextPoints"] = narrative.get("next_points")
    if not summary.get("evidence") and isinstance(narrative.get("evidence"), dict):
        summary["evidence"] = narrative.get("evidence")

    standard_report["metrics"] = metrics
    standard_report["features"] = features
    standard_report["timeline"] = timeline
    standard_report["summary"] = summary
    if time_buckets:
        standard_report["timeBuckets"] = time_buckets
    if payload:
        standard_report["analysisPayload"] = payload
    return standard_report


def _parse_iso_utc(iso: str) -> Optional[datetime]:
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


def _infer_myweb_report_type_from_scope(scope: str) -> Optional[str]:
    sc = str(scope or "").strip()
    if sc.startswith("emotion_daily:"):
        return "daily"
    if sc.startswith("emotion_weekly:"):
        return "weekly"
    if sc.startswith("emotion_monthly:"):
        return "monthly"
    return None


def _build_target_period_from_snapshot(report_type: str, period_start_iso: str, period_end_iso: str) -> TargetPeriod:
    ps = _parse_iso_utc(period_start_iso)
    pe = _parse_iso_utc(period_end_iso)
    if ps is None or pe is None:
        raise HTTPException(status_code=500, detail="Invalid snapshot period ISO")

    # dist_utc is the boundary instant; our stored period_end is dist - 1ms
    dist_utc = pe + timedelta(milliseconds=1)

    if report_type == "daily":
        title_date = _format_jst_md(ps)
        title = f"日報：{title_date}（1日分）"
        meta = {"titleDate": title_date}
    elif report_type == "weekly":
        s = _format_jst_md(ps)
        e = _format_jst_md(pe)
        title_range = f"{s} ～ {e}"
        title = f"週報：{title_range}（7日分）"
        meta = {"titleRange": title_range}
    elif report_type == "monthly":
        end_jst = pe.astimezone(JST)
        title_month = f"{end_jst.year}/{end_jst.month}"
        title = f"月報：{title_month}（28日分）"
        meta = {"titleMonth": title_month}
    else:
        raise HTTPException(status_code=400, detail="Unsupported report type for snapshot-driven generation")

    def iso(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    return TargetPeriod(
        report_type=str(report_type),
        dist_utc=dist_utc,
        period_start_utc=ps,
        period_end_utc=pe,
        period_start_iso=iso(ps),
        period_end_iso=iso(pe),
        title=title,
        title_meta=meta,
    )

    if resp.status_code not in (200, 206):
        return None
    try:
        rows = resp.json()
    except Exception:
        return None
    if isinstance(rows, list) and rows:
        sh = str((rows[0] or {}).get("source_hash") or "").strip()
        return sh or None
    return None


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


async def _report_exists(user_id: str, report_type: str, start_iso: str, end_iso: str) -> Optional[str]:
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
            return str(rid) if rid is not None else None
        return None
    except Exception:
        return None


async def _upsert_report(payload: Dict[str, Any]) -> Optional[str]:
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
            return str(rid) if rid is not None else None
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


def _render_weekly_standard_v3_text(
    *,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    metrics: Dict[str, Any],
    days: List[Dict[str, Any]],
    supplement_text: Optional[str] = None,
) -> str:
    """Render Weekly Standard report text.

    This keeps the output observational and user-facing (no system notes).
    """

    def _range_line() -> Optional[str]:
        try:
            s = datetime.fromisoformat(period_start_iso.replace("Z", "+00:00")).astimezone(JST)
            e = datetime.fromisoformat(period_end_iso.replace("Z", "+00:00")).astimezone(JST)
            return f"対象期間（JST）: {s.year}/{s.month}/{s.day} 00:00 〜 {e.year}/{e.month}/{e.day} 23:59"
        except Exception:
            return None

    totals = metrics.get("totals") if isinstance(metrics.get("totals"), dict) else {}
    share = metrics.get("sharePct") if isinstance(metrics.get("sharePct"), dict) else {}
    top = metrics.get("top") if isinstance(metrics.get("top"), list) else []
    total_all = int(metrics.get("totalAll") or 0)
    dominant = _dominant_label(metrics)

    # Peak day (by total weight)
    peak_day_label: Optional[str] = None
    peak_total = -1
    dom_keys: List[Optional[str]] = []
    for d in (days or []):
        try:
            day_total = sum(int(d.get(k, 0) or 0) for k in EMOTION_KEYS)
        except Exception:
            day_total = 0
        if day_total > peak_total:
            peak_total = day_total
            peak_day_label = str(d.get("label") or "").strip() or None
        dk = str(d.get("dominantKey") or "").strip() or None
        dom_keys.append(dk)

    # Dominant switches (rough rhythm)
    switches = 0
    last = None
    for dk in dom_keys:
        if dk and last and dk != last:
            switches += 1
        if dk:
            last = dk

    # Two most prominent emotions (user-facing)
    top_pairs: List[Tuple[str, int]] = []
    for it in top:
        if isinstance(it, list) and len(it) == 2:
            k = str(it[0] or "").strip()
            try:
                v = int(it[1] or 0)
            except Exception:
                v = 0
            if k:
                top_pairs.append((k, v))
    top_pairs = top_pairs[:2]

    def _pct(k: str) -> Optional[int]:
        try:
            return int(share.get(k, 0))
        except Exception:
            return None

    lines: List[str] = []
    lines.append(title)
    rng = _range_line()
    if rng:
        lines.append(rng)
    lines.append("")

    # 1) Summary
    lines.append("【観測サマリー】")
    if total_all <= 0:
        lines.append("今週は入力が少なめで、はっきりした傾向は読み取りにくい週でした。")
    else:
        s1 = f"今週は「{dominant}」が中心に現れていました。"
        if top_pairs:
            k1, _v1 = top_pairs[0]
            p1 = _pct(k1)
            if p1 is not None and p1 > 0:
                s1 += f"（全体の約{p1}%）"
        lines.append(s1)
        if len(top_pairs) >= 2:
            k2, _v2 = top_pairs[1]
            p2 = _pct(k2)
            if p2 is not None and p2 > 0:
                lines.append(f"次に目立ったのは「{KEY_TO_JP.get(k2, k2)}」で、約{p2}%でした。")
    lines.append("")

    # 2) Pattern detection
    lines.append("【パターン検出】")
    if total_all <= 0:
        lines.append("大きな揺れは観測されませんでした（入力量が少ないため）。")
    else:
        if peak_day_label:
            lines.append(f"感情の動きが強めに出たのは {peak_day_label} でした。")
        if switches >= 3:
            lines.append("日ごとの中心感情が切り替わりやすく、揺れが出やすい週だったかもしれません。")
        elif switches == 0:
            lines.append("中心感情は大きくは切り替わらず、一定のリズムで推移していました。")
        else:
            lines.append("中心感情はときどき切り替わりつつ、全体としてはまとまりのある動きでした。")
    lines.append("")

    # 3) Movement
    lines.append("【感情の動き】")
    for k in EMOTION_KEYS:
        try:
            v = int(totals.get(k, 0) or 0)
        except Exception:
            v = 0
        if v > 0:
            lines.append(f"- {KEY_TO_JP.get(k, k)}: {v}")
    if total_all <= 0:
        lines.append("（今週は合計が0のため、グラフ中心で確認するのが良さそうです）")
    lines.append("")

    # 4) Hint
    lines.append("【感情観測ヒント】")
    lines.append("ピークが出た日の『思考メモ（出来事の受け止め方）』を短く振り返ると、次の観測がしやすくなります。")
    lines.append("同じ感情が続いた日は『何が安心材料だったか／何が引き金だったか』を一言で残すのがおすすめです。")
    lines.append("")

    # Optional supplement
    if supplement_text:
        st = str(supplement_text or "").strip()
        if st:
            lines.append("【補足】")
            lines.append(st)
            lines.append("")

    # 5) Note
    lines.append("【注記】")
    lines.append("このレポートは、入力から見える変化をまとめた『観測』であり、診断や断定を目的としたものではありません。")

    return "\n".join(lines).strip()


def _render_monthly_standard_v3_text(
    *,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    metrics: Dict[str, Any],
    weeks: List[Dict[str, Any]],
    supplement_text: Optional[str] = None,
) -> str:
    """Render Monthly Standard report text (28d / 4-week buckets)."""

    def _range_line() -> Optional[str]:
        try:
            s = datetime.fromisoformat(period_start_iso.replace("Z", "+00:00")).astimezone(JST)
            e = datetime.fromisoformat(period_end_iso.replace("Z", "+00:00")).astimezone(JST)
            return f"対象期間（JST）: {s.year}/{s.month}/{s.day} 00:00 〜 {e.year}/{e.month}/{e.day} 23:59"
        except Exception:
            return None

    totals = metrics.get("totals") if isinstance(metrics.get("totals"), dict) else {}
    share = metrics.get("sharePct") if isinstance(metrics.get("sharePct"), dict) else {}
    total_all = int(metrics.get("totalAll") or 0)
    dominant = _dominant_label(metrics)

    # Week summaries
    week_summaries: List[str] = []
    week_doms: List[str] = []
    calm_by_week: List[int] = []
    for w in (weeks or []):
        label = str(w.get("label") or "").strip() or "週"
        wt = 0
        best_k = None
        best_v = 0
        for k in EMOTION_KEYS:
            try:
                v = int(w.get(k, 0) or 0)
            except Exception:
                v = 0
            wt += v
            if v > best_v:
                best_v = v
                best_k = k
        calm_by_week.append(int(w.get("calm", 0) or 0))
        dom_jp = KEY_TO_JP.get(best_k, best_k) if best_k else "—"
        week_doms.append(str(dom_jp))
        if wt <= 0:
            week_summaries.append(f"- {label}: 入力量が少なめでした")
        else:
            week_summaries.append(f"- {label}: 「{dom_jp}」が中心（合計 {wt}）")

    # Simple "reset" signal: calm increasing in later weeks
    reset_hint = None
    if len(calm_by_week) >= 4:
        try:
            first_half = calm_by_week[0] + calm_by_week[1]
            second_half = calm_by_week[2] + calm_by_week[3]
            if second_half > first_half and second_half > 0:
                reset_hint = "後半にかけて『平穏』が増え、整え直しの動きが出ていた可能性があります。"
        except Exception:
            reset_hint = None

    def _pct(k: str) -> Optional[int]:
        try:
            return int(share.get(k, 0))
        except Exception:
            return None

    lines: List[str] = []
    lines.append(title)
    rng = _range_line()
    if rng:
        lines.append(rng)
    lines.append("")

    lines.append("【観測サマリー】")
    if total_all <= 0:
        lines.append("今月は入力が少なめで、はっきりした傾向は読み取りにくい月でした。")
    else:
        s1 = f"今月は「{dominant}」が中心に現れていました。"
        # Try show share of dominant by key (reverse map JP -> key when possible)
        dom_key = None
        for k, jp in KEY_TO_JP.items():
            if jp == dominant:
                dom_key = k
                break
        if dom_key:
            p1 = _pct(dom_key)
            if p1 is not None and p1 > 0:
                s1 += f"（全体の約{p1}%）"
        lines.append(s1)
    lines.append("")

    lines.append("【今月の傾向】")
    if total_all <= 0:
        lines.append("入力が少ないため、傾向の比較は控えめにしておきます。")
    else:
        # Very simple repetition hint: dominant appears in many weeks
        dom_count = sum(1 for d in week_doms if d == dominant)
        if dom_count >= 3:
            lines.append(f"週をまたいで「{dominant}」が繰り返し中心になっていました。")
        elif dom_count == 2:
            lines.append(f"「{dominant}」が中心の週が複数あり、同じ流れが戻ってきやすい月だったかもしれません。")
        else:
            lines.append("週ごとに中心感情が変わりやすく、状況に合わせて揺れやすい月だったかもしれません。")
    lines.append("")

    lines.append("【週ごとの推移】")
    if week_summaries:
        lines.extend(week_summaries)
    else:
        lines.append("週ごとの集計が取得できませんでした。")
    lines.append("")

    lines.append("【整え直しの動き】")
    if reset_hint:
        lines.append(reset_hint)
    else:
        lines.append("落ち着き（平穏）の出方や戻り方を、週ごとのグラフで合わせて確認すると傾向がつかみやすいです。")
    lines.append("")

    lines.append("【感情の動き】")
    for k in EMOTION_KEYS:
        try:
            v = int(totals.get(k, 0) or 0)
        except Exception:
            v = 0
        if v > 0:
            lines.append(f"- {KEY_TO_JP.get(k, k)}: {v}")
    lines.append("")

    lines.append("【感情観測ヒント】")
    lines.append("繰り返し出た感情がある場合、その週に共通していた『思考のパターン』を一言でメモすると、次月の比較がしやすくなります。")
    lines.append("月の中で切り替わりが多い場合は、切り替わり直前にあった出来事や受け止め方を短く残すのがおすすめです。")
    lines.append("")

    if supplement_text:
        st = str(supplement_text or "").strip()
        if st:
            lines.append("【補足】")
            lines.append(st)
            lines.append("")

    lines.append("【注記】")
    lines.append("このレポートは、入力から見える変化をまとめた『観測』であり、診断や断定を目的としたものではありません。")

    return "\n".join(lines).strip()


def _render_daily_motion_line(movement: Dict[str, Any]) -> str:
    key = str((movement or {}).get("key") or "").strip()
    if key == "swing":
        return "前日と中心感情が入れ替わりました（揺れ）"
    if key == "up":
        return "前日より観測量が増えています（上昇）"
    if key == "down":
        return "前日より観測量が落ち着いています（減少）"
    return "前日とほぼ同じ観測量でした（安定）"


def _render_daily_hint_line(metrics: Dict[str, Any], movement: Dict[str, Any]) -> str:
    total_all = int((metrics or {}).get("totalAll") or 0)
    if total_all <= 0:
        return "入力が少ない日は、一言だけでも残しておくと次の比較がしやすくなります。"

    motion_key = str((movement or {}).get("key") or "").strip()
    if motion_key == "swing":
        return "感情の中心が動いた日でした。切り替わりのきっかけを短く残すと流れが見えやすくなります。"

    top = (metrics or {}).get("top") if isinstance((metrics or {}).get("top"), list) else []
    dominant_key = None
    if top and isinstance(top[0], list) and len(top[0]) >= 1:
        dominant_key = str(top[0][0] or "").strip() or None

    if dominant_key == "joy":
        return "前向きなエネルギーが出やすい一日でした。何が追い風だったか一言残すと再現しやすくなります。"
    if dominant_key == "sadness":
        return "気持ちが内側に向きやすい一日でした。負荷になった場面を短く残すと次の比較がしやすくなります。"
    if dominant_key == "anxiety":
        return "緊張や気がかりが前に出やすい一日でした。引き金になった出来事を一言残すと流れが見えやすくなります。"
    if dominant_key == "anger":
        return "反応が強く出やすい一日でした。どこで負荷がかかったかを短く残すと切り分けしやすくなります。"
    if dominant_key == "calm":
        return "整っている時間が比較的多い一日でした。落ち着けた条件を残しておくと次にも活かしやすくなります。"
    return "その日の中心感情ときっかけを一言で残すと、次の比較がしやすくなります。"


def _render_daily_standard_v3_text(
    *,
    metrics: Dict[str, Any],
    summary: Dict[str, Any],
    movement: Dict[str, Any],
) -> str:
    top = (metrics or {}).get("top") if isinstance((metrics or {}).get("top"), list) else []
    share = (metrics or {}).get("sharePct") if isinstance((metrics or {}).get("sharePct"), dict) else {}

    dominant_key = None
    if top and isinstance(top[0], list) and len(top[0]) >= 1:
        dominant_key = str(top[0][0] or "").strip() or None

    dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"
    try:
        dominant_pct = int(share.get(dominant_key, 0)) if dominant_key else 0
    except Exception:
        dominant_pct = 0

    input_count = 0
    try:
        input_count = int((summary or {}).get("emotions_public"))
    except Exception:
        input_count = 0
    if input_count <= 0:
        try:
            input_count = int((summary or {}).get("emotions_total") or 0)
        except Exception:
            input_count = 0

    lines: List[str] = []
    lines.append("【昨日の観測サマリー】")
    lines.append(f"・最も強かった感情: {dominant_label}（{dominant_pct}%）")
    lines.append(f"・総入力: {input_count}件")
    lines.append("")
    lines.append("【昨日の動き】")
    lines.append(f"・{_render_daily_motion_line(movement)}")
    lines.append("")
    lines.append("【ひとこと視点】")
    lines.append(f"・{_render_daily_hint_line(metrics, movement)}")
    return "\n".join(lines).strip()


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
        lines.append("【構造洞察（補足）】")
        lines.append(astor_text.strip())
    return "\n".join(lines).strip()


async def _generate_and_save(
    user_id: str,
    target: TargetPeriod,
    *,
    include_astor: bool,
) -> Tuple[str, Dict[str, Any], Optional[str], Optional[Dict[str, Any]]]:
    # NOTE: Legacy direct-read generation is deprecated for weekly/monthly.
    #       Weekly/Monthly must be generated via snapshot-driven path (_generate_and_save_from_snapshot).
    if target.report_type in ("weekly", "monthly"):
        raise HTTPException(
            status_code=410,
            detail="Legacy weekly/monthly generation is disabled; use snapshot-driven generation",
        )

    # 1) fetch emotions
    rows_all = await _fetch_emotion_rows(user_id, target.period_start_iso, target.period_end_iso)
    # NOTE: public output should exclude secret materials (governance v1)
    rows = [r for r in (rows_all or []) if not bool((r or {}).get("is_secret"))]

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
    is_plus_or_higher = (
        bool(tier_enum in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM)) if SubscriptionTier is not None else False
    )

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
        if include_astor and is_plus_or_higher and generate_myweb_insight_payload is not None:
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
        text = _render_weekly_standard_v3_text(
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            metrics=metrics,
            days=days,
            supplement_text=astor_text,
        )
    else:
        weeks = _build_weeks_fixed4(rows, target.period_start_utc)
        metrics = _compute_monthly_metrics(weeks)
        content_json["metrics"] = metrics
        # viewer fallback support
        content_json["weeks"] = weeks
        if include_astor and is_plus_or_higher and generate_myweb_insight_payload is not None:
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
        text = _render_monthly_standard_v3_text(
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            metrics=metrics,
            weeks=weeks,
            supplement_text=astor_text,
        )

    # 3) upsert

    # --- MyWeb report v3 structure (Standard / Structural) ---
    try:
        content_json.setdefault("reportVersion", "myweb.report.v3")
        content_json["standardReport"] = {
            "version": "myweb.standard.v1",
            "contentText": text,
        }
        if astor_report and is_premium:
            content_json["structuralReport"] = astor_report
    except Exception:
        pass

    # --- Governance: publish meta (DRAFT -> inspect -> READY) ---
    # We store publish status and the public-material fingerprint so the inspector / API can
    # decide whether this artifact is safe to return.
    try:
        scope = SNAPSHOT_SCOPE_DEFAULT
        public_hash = None
        try:
            public_hash = await _fetch_latest_snapshot_hash(user_id, scope=scope, snapshot_type="public")
        except Exception:
            public_hash = None

        # normalize tier string (for audit/debug)
        tier_str = None
        try:
            tier_str = tier_enum.value if tier_enum is not None and hasattr(tier_enum, "value") else (str(tier_enum) if tier_enum is not None else None)
        except Exception:
            tier_str = None

        pub = content_json.get("publish") if isinstance(content_json.get("publish"), dict) else {}
        pub.update(
            {
                "status": "READY",
                "scope": scope,
                "snapshotType": "public",
                "publicSourceHash": public_hash,
                "generatedForTier": tier_str,
                "secretExcluded": True,
                "inspectedAt": None,
            }
        )
        content_json["publish"] = pub
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

    # Enqueue inspection (best-effort). This keeps DRAFT/READY gating consistent whether
    # the report was generated by API (on-demand) or by worker.
    try:
        if rid:
            from astor_job_queue import enqueue_job as _enqueue_job

            await _enqueue_job(
                job_key=f"inspect_emotion_report:{rid}",
                job_type="inspect_emotion_report_v1",
                user_id=user_id,
                payload={
                    "report_id": rid,
                    "report_type": target.report_type,
                    "period_start": target.period_start_iso,
                    "period_end": target.period_end_iso,
                    "scope": SNAPSHOT_SCOPE_DEFAULT,
                    "expected_public_source_hash": (content_json.get("publish") or {}).get("publicSourceHash") if isinstance(content_json.get("publish"), dict) else None,
                },
                priority=10,
            )
    except Exception as exc:
        logger.error("Failed to enqueue inspect_emotion_report_v1: %s", exc)

    return text, content_json, astor_text, {"report_id": rid}



async def _generate_and_save_from_snapshot(
    user_id: str,
    *,
    scope: str,
    include_astor: bool,
) -> Tuple[str, Dict[str, Any], Optional[str], Optional[Dict[str, Any]]]:
    """Generate daily/weekly/monthly MyWeb reports from emotion_period snapshots (v2).

    This is an internal helper for astor_worker.
    - Reads material_snapshots (snapshot_type=public) for the given scope.
    - Does NOT read the emotions table.
    - Does NOT enqueue inspection (worker handles it).
    """
    uid = str(user_id or "").strip()
    sc = str(scope or "").strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not sc:
        raise HTTPException(status_code=400, detail="scope is required")

    report_type = _infer_myweb_report_type_from_scope(sc)
    if report_type not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Unsupported scope for snapshot-driven generation")

    snap = await _fetch_latest_snapshot_row(uid, scope=sc, snapshot_type="public")
    if not snap:
        raise HTTPException(status_code=404, detail="material snapshot not found")

    snap_id = str((snap or {}).get("id") or "").strip() or None
    snap_hash = str((snap or {}).get("source_hash") or "").strip() or None
    payload = (snap or {}).get("payload") if isinstance((snap or {}).get("payload"), dict) else {}
    period = payload.get("period") if isinstance(payload.get("period"), dict) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    views = payload.get("views") if isinstance(payload.get("views"), dict) else {}

    period_start_iso = str(period.get("periodStartIso") or "").strip()
    period_end_iso = str(period.get("periodEndIso") or "").strip()
    if not period_start_iso or not period_end_iso:
        raise HTTPException(status_code=500, detail="snapshot period meta missing")

    target = _build_target_period_from_snapshot(report_type, period_start_iso, period_end_iso)

    # 2) metrics from snapshot
    content_json: Dict[str, Any] = {}
    astor_text: Optional[str] = None
    astor_report: Optional[Dict[str, Any]] = None
    astor_meta: Optional[Dict[str, Any]] = None
    astor_error: Optional[str] = None

    metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
    content_json["metrics"] = metrics

    if report_type == "daily":
        day = views.get("day") if isinstance(views.get("day"), dict) else {}
        movement = views.get("movement") if isinstance(views.get("movement"), dict) else {}
        content_json["summary"] = summary
        content_json["day"] = day
        content_json["movement"] = movement
        days = []
        weeks = []
    elif report_type == "weekly":
        days = views.get("days") if isinstance(views.get("days"), list) else []
        content_json["days"] = days
        weeks = []
        day = {}
        movement = {}
    else:
        weeks = views.get("weeks") if isinstance(views.get("weeks"), list) else []
        content_json["weeks"] = weeks
        days = []
        day = {}
        movement = {}

    # Current tier (used for premium structural report gating only).
    tier_enum = None
    is_premium = False
    is_plus_or_higher = False
    if SubscriptionTier is not None and get_subscription_tier_for_user is not None:
        try:
            tier_enum = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
        except Exception:
            tier_enum = SubscriptionTier.FREE
        is_premium = bool(tier_enum == SubscriptionTier.PREMIUM) if SubscriptionTier is not None else False
        is_plus_or_higher = (
            bool(tier_enum in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM)) if SubscriptionTier is not None else False
        )

    # analysis_results → Standard report source
    analysis_row: Optional[Dict[str, Any]] = None
    analysis_payload: Dict[str, Any] = {}
    if snap_id:
        analysis_row = await _fetch_analysis_result(
            uid,
            snapshot_id=snap_id,
            analysis_type="emotion_structure",
            analysis_stage="standard",
            scope=report_type,
        )
        if analysis_row and isinstance(analysis_row.get("payload"), dict):
            analysis_payload = analysis_row.get("payload") or {}

    # Optional ASTOR insight (kept same behavior as v1; may read additional materials)
    if report_type in ("weekly", "monthly") and include_astor and is_plus_or_higher and generate_myweb_insight_payload is not None:
        try:
            period_days = 7 if report_type == "weekly" else 28
            astor_text, astor_report = generate_myweb_insight_payload(user_id=uid, period_days=period_days, lang="ja")
            astor_meta = {"engine": "astor_myweb_insight", "period_days": period_days, "version": "0.3"}
        except Exception as e:
            astor_error = str(e)

    if astor_text:
        content_json["astorText"] = astor_text
        if astor_meta:
            content_json["astorMeta"] = astor_meta
    if astor_error:
        content_json["astorError"] = astor_error

    # Light text is always stored in legacy content_text.
    if report_type == "daily":
        light_text = _render_daily_standard_v3_text(
            metrics=metrics,
            summary=summary,
            movement=movement,
        )
    elif report_type == "weekly":
        light_text = _render_weekly_standard_v3_text(
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            metrics=metrics,
            days=days,
            supplement_text=None,
        )
    else:
        light_text = _render_monthly_standard_v3_text(
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            metrics=metrics,
            weeks=weeks,
            supplement_text=None,
        )

    standard_text = light_text
    if analysis_row:
        content_json["analysisMeta"] = {
            "analysis_result_id": str((analysis_row or {}).get("id") or "") or None,
            "analysis_type": str((analysis_row or {}).get("analysis_type") or "emotion_structure"),
            "analysis_stage": str((analysis_row or {}).get("analysis_stage") or "standard"),
            "analysis_version": str((analysis_row or {}).get("analysis_version") or ""),
            "snapshot_id": snap_id,
            "source_hash": str((analysis_row or {}).get("source_hash") or "") or snap_hash,
        }

    # --- MyWeb report v3 structure (Light / Standard / Structural) ---
    try:
        content_json.setdefault("reportVersion", "myweb.report.v3")
        standard_report = _build_standard_report_payload(
            report_type=report_type,
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            analysis_payload=analysis_payload,
            snapshot_summary=summary,
            snapshot_views=views,
            light_text=light_text,
        )
        if isinstance(standard_report, dict):
            content_json["standardReport"] = standard_report
            standard_text = str(standard_report.get("contentText") or light_text or "")
        if astor_report and is_premium:
            content_json["structuralReport"] = astor_report
    except Exception:
        standard_text = light_text

    # --- Governance: publish meta (DRAFT -> inspect -> READY) ---
    try:
        tier_str = None
        try:
            tier_str = (
                tier_enum.value
                if tier_enum is not None and hasattr(tier_enum, "value")
                else (str(tier_enum) if tier_enum is not None else None)
            )
        except Exception:
            tier_str = None

        pub = content_json.get("publish") if isinstance(content_json.get("publish"), dict) else {}
        pub.update(
            {
                "status": "READY",
                "scope": sc,
                "snapshotType": "public",
                "publicSourceHash": snap_hash,
                "generatedForTier": tier_str,
                "secretExcluded": True,
                "inspectedAt": None,
            }
        )
        content_json["publish"] = pub
    except Exception:
        pass

    payload_upsert = {
        "user_id": uid,
        "report_type": report_type,
        "period_start": target.period_start_iso,
        "period_end": target.period_end_iso,
        "title": target.title,
        "content_text": light_text,
        "content_json": content_json,
        "generated_at": target.dist_utc.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
    }
    rid = await _upsert_report(payload_upsert)
    payload_upsert["_id"] = rid

    return light_text, content_json, astor_text, {"report_id": rid, "report_type": report_type, "scope": sc, "public_source_hash": snap_hash}


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
                    if rt in ("daily", "weekly", "monthly"):
                        # v2: snapshot-driven generation (emotion_period scope)
                        if rt == "daily":
                            start_jst = target.period_start_utc.astimezone(JST)
                            scope = f"emotion_daily:{start_jst.year:04d}-{start_jst.month:02d}-{start_jst.day:02d}"
                        elif rt == "weekly":
                            dist_jst = target.dist_utc.astimezone(JST)
                            scope = f"emotion_weekly:{dist_jst.year:04d}-{dist_jst.month:02d}-{dist_jst.day:02d}"
                        else:
                            end_jst = target.period_end_utc.astimezone(JST)
                            scope = f"emotion_monthly:{end_jst.year:04d}-{end_jst.month:02d}"

                        try:
                            _text, _cjson, _astor_text, meta = await _generate_and_save_from_snapshot(
                                user_id,
                                scope=scope,
                                include_astor=req.include_astor,
                            )
                        except HTTPException as he:
                            # If snapshot is missing, enqueue snapshot generation and retry once (best-effort).
                            if int(getattr(he, "status_code", 0) or 0) == 404:
                                try:
                                    from astor_job_queue import enqueue_job as _enqueue_job

                                    await _enqueue_job(
                                        job_key=f"snapshot_generate_v1:{user_id}:{scope}",
                                        job_type="snapshot_generate_v1",
                                        user_id=user_id,
                                        payload={
                                            "scope": scope,
                                            "trigger": "on_demand_myweb_reports_ensure",
                                            "requested_at": datetime.now(timezone.utc)
                                            .isoformat(timespec="seconds")
                                            .replace("+00:00", "Z"),
                                        },
                                        priority=12,
                                        debounce_seconds=10,
                                    )
                                except Exception as exc:
                                    logger.error("Failed to enqueue snapshot_generate_v1: %s", exc)

                                if poll_until is not None and MYWEB_LOCK_WAIT_SECONDS > 0:
                                    try:
                                        await poll_until(
                                            lambda: _fetch_latest_snapshot_row(
                                                user_id, scope=scope, snapshot_type="public"
                                            ),
                                            timeout_seconds=MYWEB_LOCK_WAIT_SECONDS,
                                        )
                                    except Exception:
                                        pass

                                _text, _cjson, _astor_text, meta = await _generate_and_save_from_snapshot(
                                    user_id,
                                    scope=scope,
                                    include_astor=req.include_astor,
                                )
                            else:
                                raise

                        # Enqueue inspection (best-effort) for API-generated artifacts.
                        try:
                            rid = (meta or {}).get("report_id") if isinstance(meta, dict) else None
                            expected_public_hash = (meta or {}).get("public_source_hash") if isinstance(meta, dict) else None
                            if rid:
                                from astor_job_queue import enqueue_job as _enqueue_job

                                await _enqueue_job(
                                    job_key=f"inspect_emotion_report:{rid}",
                                    job_type="inspect_emotion_report_v1",
                                    user_id=user_id,
                                    payload={
                                        "report_id": rid,
                                        "report_type": rt,
                                        "period_start": target.period_start_iso,
                                        "period_end": target.period_end_iso,
                                        "scope": scope,
                                        "expected_public_source_hash": expected_public_hash,
                                    },
                                    priority=10,
                                )
                        except Exception as exc:
                            logger.error("Failed to enqueue inspect_emotion_report_v1: %s", exc)
                    else:
                        _text, _cjson, _astor_text, meta = await _generate_and_save(
                            user_id,
                            target,
                            include_astor=req.include_astor,
                        )
                finally:
                    if lock_key and release_lock is not None:
                        await release_lock(lock_key=lock_key, owner_id=lock_owner)
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


    @app.get("/myweb/reports/ready", response_model=MyWebReadyReportsResponse)
    async def myweb_reports_ready(
        report_type: Literal["daily", "weekly", "monthly"] = "weekly",
        limit: int = 10,
        authorization: Optional[str] = Header(default=None),
    ) -> MyWebReadyReportsResponse:
        """Return READY (or PUBLISHED) MyWeb reports only.

        Minimal decide_publish:
        - status in (READY, PUBLISHED)
        - retention window by current subscription tier
        - strip premium-only fields based on current tier
        """
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)

        # Resolve current tier (default: free)
        tier_enum = None
        tier_str = "free"
        if SubscriptionTier is not None and get_subscription_tier_for_user is not None:
            try:
                tier_enum = await get_subscription_tier_for_user(user_id, default=SubscriptionTier.FREE)
                tier_str = tier_enum.value if hasattr(tier_enum, "value") else str(tier_enum)
            except Exception:
                tier_str = "free"

        def _parse_dt(iso: str) -> Optional[datetime]:
            s = (iso or "").strip()
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

        # Retention boundaries
        now_utc = datetime.now(timezone.utc)
        now_jst = now_utc.astimezone(JST)
        cur_month_start_jst = datetime(now_jst.year, now_jst.month, 1, tzinfo=JST)
        if now_jst.month == 1:
            prev_year, prev_month = now_jst.year - 1, 12
        else:
            prev_year, prev_month = now_jst.year, now_jst.month - 1
        prev_month_start_jst = datetime(prev_year, prev_month, 1, tzinfo=JST)

        if cur_month_start_jst.month == 12:
            next_year, next_month = cur_month_start_jst.year + 1, 1
        else:
            next_year, next_month = cur_month_start_jst.year, cur_month_start_jst.month + 1
        next_month_start_jst = datetime(next_year, next_month, 1, tzinfo=JST)

        prev_month_start_utc = prev_month_start_jst.astimezone(timezone.utc)
        next_month_start_utc = next_month_start_jst.astimezone(timezone.utc)
        plus_window_start_utc = (now_utc - timedelta(days=365))

        def _retention_ok(period_end_iso: str) -> bool:
            pe = _parse_dt(period_end_iso)
            if pe is None:
                return False
            if tier_str == "premium":
                return True
            if tier_str == "plus":
                return pe >= plus_window_start_utc
            return prev_month_start_utc <= pe < next_month_start_utc

        def _shape_content_json(cj: Dict[str, Any]) -> Dict[str, Any]:
            # 生成物は全ユーザー分を保持し、表示制御は RN / クライアント側で行う。
            # そのため、ready API では content_json を tier によって削らない。
            return dict(cj or {})

        lim = max(1, min(int(limit or 10), 50))
        # Fetch more than requested to allow filtering by status/retention.
        fetch_limit = max(lim * 4, 30)

        resp = await _sb_get(
            f"/rest/v1/{REPORTS_TABLE}",
            params=[
                ("select", "id,report_type,period_start,period_end,title,content_text,content_json,generated_at,updated_at"),
                ("user_id", f"eq.{user_id}"),
                ("report_type", f"eq.{report_type}"),
                ("order", "period_start.desc"),
                ("limit", str(fetch_limit)),
            ],
        )
        if resp.status_code not in (200, 206):
            logger.error("Supabase select myweb_reports failed: %s %s", resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Supabase query failed")
        try:
            rows = resp.json()
        except Exception:
            rows = []

        items: List[MyWebReportRecord] = []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                cj = r.get("content_json") if isinstance(r.get("content_json"), dict) else {}
                pub = cj.get("publish") if isinstance(cj.get("publish"), dict) else {}
                st = str(pub.get("status") or "").strip().upper()
                if st not in ("READY", "PUBLISHED"):
                    continue

                # 日報は「前日の入力が0件」の場合は配布しない
                if report_type == "daily":
                    metrics = cj.get("metrics") if isinstance(cj.get("metrics"), dict) else {}
                    try:
                        daily_total_all = int(metrics.get("totalAll") or 0)
                    except Exception:
                        daily_total_all = 0
                    if daily_total_all <= 0:
                        continue

                pe = str(r.get("period_end") or "")
                if not _retention_ok(pe):
                    continue

                items.append(
                    MyWebReportRecord(
                        id=str(r.get("id") or ""),
                        report_type=str(r.get("report_type") or ""),
                        period_start=str(r.get("period_start") or ""),
                        period_end=str(r.get("period_end") or ""),
                        title=r.get("title"),
                        content_text=r.get("content_text"),
                        content_json=_shape_content_json(cj),
                        generated_at=r.get("generated_at"),
                        updated_at=r.get("updated_at"),
                    )
                )
                if len(items) >= lim:
                    break

        return MyWebReadyReportsResponse(
            user_id=user_id,
            report_type=str(report_type),
            viewer_tier=str(tier_str),
            items=items,
        )

