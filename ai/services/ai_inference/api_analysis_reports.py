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
from fastapi import FastAPI, Header, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from access_policy.viewer_access_policy import (
    apply_myweb_report_access_for_viewer,
    build_report_history_retention,
    resolve_report_view_context,
    resolve_viewer_tier_str as _resolve_viewer_tier_str_from_policy,
)

from response_microcache import build_cache_key, get_or_compute, invalidate_prefix
from supabase_client import sb_get, sb_post

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
    from astor_analysis_insight import generate_myweb_insight_payload
except Exception:  # pragma: no cover
    generate_myweb_insight_payload = None  # type: ignore

# Optional: subscription tier (MyWeb v3 output gating)
try:
    from subscription import SubscriptionTier
    from subscription_store import get_subscription_tier_for_user
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore

# Shared no-input gate for emotion-period snapshots.
try:
    from astor_material_snapshots import get_emotion_period_public_input_status
except Exception:  # pragma: no cover
    get_emotion_period_public_input_status = None  # type: ignore

# New national system: Analysis core validity gate (additive content_json meta).
try:
    from analysis_report_validity_gate import (
        attach_report_validity_meta,
        evaluate_analysis_report_validity,
        infer_emotion_material_fields_from_rows,
    )
except Exception:  # pragma: no cover
    attach_report_validity_meta = None  # type: ignore
    evaluate_analysis_report_validity = None  # type: ignore
    infer_emotion_material_fields_from_rows = None  # type: ignore


logger = logging.getLogger("myweb_reports_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Current bridge view is backend read-only. Keep REPORTS_TABLE for legacy write/ensure paths.
REPORTS_TABLE = os.getenv("MYWEB_REPORTS_TABLE", "myweb_reports").strip() or "myweb_reports"
REPORTS_READ_TABLE = (
    os.getenv("COCOLON_ANALYSIS_REPORTS_READ_TABLE")
    or os.getenv("ANALYSIS_REPORTS_READ_TABLE")
    or os.getenv("COCOLON_MYWEB_REPORTS_READ_TABLE")
    or os.getenv("MYWEB_REPORTS_READ_TABLE")
    or "analysis_reports"
).strip() or "analysis_reports"
ANALYSIS_RESULTS_TABLE = (os.getenv("ANALYSIS_RESULTS_TABLE") or "analysis_results").strip() or "analysis_results"

# Governance / snapshots
MATERIAL_SNAPSHOTS_TABLE = (os.getenv("MATERIAL_SNAPSHOTS_TABLE") or "material_snapshots").strip() or "material_snapshots"
SNAPSHOT_SCOPE_DEFAULT = (os.getenv("SNAPSHOT_SCOPE_DEFAULT") or "global").strip() or "global"

# Phase10 lock tuning (env)
MYWEB_LOCK_TTL_SECONDS = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYWEB", "120") or "120")
MYWEB_LOCK_WAIT_SECONDS = float(os.getenv("GENERATION_LOCK_WAIT_SECONDS_MYWEB", "25") or "25")
MYWEB_READY_CACHE_TTL_SECONDS = float(os.getenv("MYWEB_READY_CACHE_TTL_SECONDS", "60") or "60")
MYWEB_DETAIL_CACHE_TTL_SECONDS = float(os.getenv("MYWEB_DETAIL_CACHE_TTL_SECONDS", "30") or "30")

MYWEB_READY_CANDIDATE_SELECT = (
    "id,report_type,period_start,period_end,title,generated_at,updated_at,"
    "publish_status:content_json->publish->>status,"
    "metrics_total_all:content_json->metrics->>totalAll,"
    "standard_total_all:content_json->standardReport->metrics->>totalAll"
)
MYWEB_READY_FULL_SELECT = "id,report_type,period_start,period_end,title,content_text,content_json,generated_at,updated_at"
MYWEB_READY_LATEST_RAW_PAGE_SIZE = max(2, int(os.getenv("MYWEB_READY_LATEST_RAW_PAGE_SIZE", "4") or "4"))

# JST fixed
JST_OFFSET = timedelta(hours=9)
JST = timezone(JST_OFFSET)

DAY = timedelta(days=1)


def _attach_analysis_report_validity_meta_if_available(
    content_json: Dict[str, Any],
    *,
    material_count: int,
    output_text: Any,
    output_payload: Any = None,
    material_fields: Optional[List[str]] = None,
    target_period: Optional[str] = None,
) -> Dict[str, Any]:
    if evaluate_analysis_report_validity is None or attach_report_validity_meta is None:
        return content_json
    try:
        result = evaluate_analysis_report_validity(
            domain="emotion_structure",
            material_count=material_count,
            output_text=output_text,
            output_payload=output_payload,
            material_fields=material_fields or [],
            target_period=target_period,
            save_requested=True,
        )
        return attach_report_validity_meta(content_json, result)
    except Exception:
        return content_json


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
    status: Literal["generated", "exists", "skipped", "error"]
    period_start: str
    period_end: str
    title: str
    report_id: Optional[str] = None
    error: Optional[str] = None
    skip_reason: Optional[str] = None


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
    limit: int = Field(default=10)
    offset: int = Field(default=0)
    has_more: bool = Field(default=False)
    next_offset: Optional[int] = Field(default=None)
    items: List[MyWebReportRecord] = Field(default_factory=list)


class MyWebReportDetailResponse(BaseModel):
    status: str = Field(default="ok")
    user_id: str = Field(..., description="viewer user_id")
    viewer_tier: str = Field(..., description="free/plus/premium")
    item: MyWebReportRecord


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
    return await sb_get(path, params=dict(params), timeout=10.0, headers=_sb_headers())


async def _sb_post(path: str, *, params: List[Tuple[str, str]], json_body: Any, prefer: str) -> httpx.Response:
    return await sb_post(path, params=dict(params), json=json_body, prefer=prefer, timeout=10.0, headers=_sb_headers(prefer=prefer))


def _pick_rows_from_response(resp: httpx.Response) -> List[Dict[str, Any]]:
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
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


async def _resolve_viewer_tier_str(user_id: str) -> str:
    return await _resolve_viewer_tier_str_from_policy(user_id)


def _build_myweb_report_record(row: Dict[str, Any], *, include_body: bool) -> MyWebReportRecord:
    content_json = row.get("content_json") if isinstance(row.get("content_json"), dict) else {}
    return MyWebReportRecord(
        id=str(row.get("id") or ""),
        report_type=str(row.get("report_type") or ""),
        period_start=str(row.get("period_start") or ""),
        period_end=str(row.get("period_end") or ""),
        title=row.get("title"),
        content_text=(row.get("content_text") if include_body else None),
        content_json=(content_json if include_body else {}),
        generated_at=row.get("generated_at"),
        updated_at=row.get("updated_at"),
    )


def _build_myweb_retention_params(retention: Dict[str, Any]) -> List[Tuple[str, str]]:
    params: List[Tuple[str, str]] = []
    gte_iso = str(retention.get("gte_iso") or "").strip()
    lt_iso = str(retention.get("lt_iso") or "").strip()
    if gte_iso:
        params.append(("period_end", f"gte.{gte_iso}"))
    if lt_iso:
        params.append(("period_end", f"lt.{lt_iso}"))
    return params


def _build_myweb_id_in_filter(report_ids: List[str]) -> Optional[str]:
    values = [str(rid or "").strip() for rid in report_ids if str(rid or "").strip()]
    if not values:
        return None
    return f"in.({','.join(values)})"


async def _fetch_myweb_ready_candidate_chunk(
    user_id: str,
    report_type: str,
    *,
    retention: Dict[str, Any],
    raw_page_size: int,
    raw_offset: int,
) -> List[Dict[str, Any]]:
    params: List[Tuple[str, str]] = [
        ("select", MYWEB_READY_CANDIDATE_SELECT),
        ("user_id", f"eq.{user_id}"),
        ("report_type", f"eq.{report_type}"),
        ("order", "period_start.desc"),
        ("limit", str(raw_page_size)),
        ("offset", str(raw_offset)),
    ]
    params.extend(_build_myweb_retention_params(retention))

    resp = await _sb_get(
        f"/rest/v1/{REPORTS_READ_TABLE}",
        params=params,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"Supabase projection select failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    rows = _pick_rows_from_response(resp)
    if rows and not any(
        any(key in row for key in ("publish_status", "metrics_total_all", "standard_total_all"))
        for row in rows[:3]
    ):
        raise RuntimeError("Supabase projection select returned rows without expected projection fields")
    return rows


async def _fetch_myweb_ready_full_candidate_chunk(
    user_id: str,
    report_type: str,
    *,
    retention: Dict[str, Any],
    raw_page_size: int,
    raw_offset: int,
) -> List[Dict[str, Any]]:
    params: List[Tuple[str, str]] = [
        ("select", MYWEB_READY_FULL_SELECT),
        ("user_id", f"eq.{user_id}"),
        ("report_type", f"eq.{report_type}"),
        ("order", "period_start.desc"),
        ("limit", str(max(1, raw_page_size))),
        ("offset", str(max(0, raw_offset))),
    ]
    params.extend(_build_myweb_retention_params(retention))

    resp = await _sb_get(
        f"/rest/v1/{REPORTS_READ_TABLE}",
        params=params,
    )
    if resp.status_code not in (200, 206):
        logger.error("Supabase latest myweb_reports select failed: %s %s", resp.status_code, (resp.text or "")[:800])
        raise HTTPException(status_code=502, detail="Supabase query failed")
    return _pick_rows_from_response(resp)


async def _fetch_myweb_full_rows_by_ids(user_id: str, report_ids: List[str]) -> List[Dict[str, Any]]:
    id_filter = _build_myweb_id_in_filter(report_ids)
    if not id_filter:
        return []

    resp = await _sb_get(
        f"/rest/v1/{REPORTS_READ_TABLE}",
        params=[
            ("select", MYWEB_READY_FULL_SELECT),
            ("user_id", f"eq.{user_id}"),
            ("id", id_filter),
            ("limit", str(max(1, len(report_ids)))),
        ],
    )
    if resp.status_code not in (200, 206):
        logger.error("Supabase select myweb_reports by ids failed: %s %s", resp.status_code, (resp.text or "")[:800])
        raise HTTPException(status_code=502, detail="Supabase query failed")
    return _pick_rows_from_response(resp)



async def _build_myweb_ready_payload_projection_first(
    *,
    user_id: str,
    report_type: str,
    lim: int,
    off: int,
    include_body: bool,
) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    view_ctx = await resolve_report_view_context(user_id, now_utc=now_utc)
    tier_str = str(view_ctx.subscription_tier)
    retention = dict(view_ctx.history_retention or {})

    if include_body and lim == 1 and off == 0:
        needed = 2
        raw_page_size = max(2, min(MYWEB_READY_LATEST_RAW_PAGE_SIZE, 10))
        raw_offset = 0
        visible_rows: List[Dict[str, Any]] = []

        while len(visible_rows) < needed:
            rows = await _fetch_myweb_ready_full_candidate_chunk(
                user_id,
                report_type,
                retention=retention,
                raw_page_size=raw_page_size,
                raw_offset=raw_offset,
            )
            if not rows:
                break

            raw_offset += len(rows)

            for row in rows:
                published_row = apply_myweb_report_access_for_viewer(
                    row,
                    context=view_ctx,
                    requested_report_type=report_type,
                    now_utc=now_utc,
                )
                if not published_row:
                    continue
                visible_rows.append(published_row)
                if len(visible_rows) >= needed:
                    break

            if len(rows) < raw_page_size:
                break

        page_rows = visible_rows[:1]
        has_more = len(visible_rows) > 1
        response = MyWebReadyReportsResponse(
            user_id=user_id,
            report_type=str(report_type),
            viewer_tier=str(tier_str),
            limit=lim,
            offset=off,
            has_more=bool(has_more),
            next_offset=(1 if has_more else None),
            items=[_build_myweb_report_record(row, include_body=True) for row in page_rows],
        )
        return jsonable_encoder(response)

    needed = off + lim + 1
    raw_page_size = max(lim * 4, 30)
    raw_offset = 0
    visible_candidates: List[Dict[str, Any]] = []

    while len(visible_candidates) < needed:
        rows = await _fetch_myweb_ready_candidate_chunk(
            user_id,
            report_type,
            retention=retention,
            raw_page_size=raw_page_size,
            raw_offset=raw_offset,
        )
        if not rows:
            break

        raw_offset += len(rows)

        for row in rows:
            published_row = apply_myweb_report_access_for_viewer(
                row,
                context=view_ctx,
                requested_report_type=report_type,
                now_utc=now_utc,
            )
            if not published_row:
                continue
            visible_candidates.append(published_row)
            if len(visible_candidates) >= needed:
                break

        if len(rows) < raw_page_size:
            break

    page_rows = visible_candidates[off : off + lim]
    has_more = len(visible_candidates) > (off + lim)
    next_offset = (off + lim) if has_more else None

    materialized_rows: List[Dict[str, Any]] = []
    if include_body and page_rows:
        page_ids = [str(row.get("id") or "").strip() for row in page_rows if str(row.get("id") or "").strip()]
        full_rows = await _fetch_myweb_full_rows_by_ids(user_id, page_ids)
        full_row_map = {str(row.get("id") or "").strip(): row for row in full_rows if isinstance(row, dict)}
        for row in page_rows:
            rid = str(row.get("id") or "").strip()
            full_row = full_row_map.get(rid)
            if not isinstance(full_row, dict):
                continue
            published_row = apply_myweb_report_access_for_viewer(
                full_row,
                context=view_ctx,
                requested_report_type=report_type,
                now_utc=now_utc,
            )
            if published_row:
                materialized_rows.append(published_row)
    else:
        materialized_rows = page_rows

    items = [_build_myweb_report_record(row, include_body=include_body) for row in materialized_rows]

    response = MyWebReadyReportsResponse(
        user_id=user_id,
        report_type=str(report_type),
        viewer_tier=str(tier_str),
        limit=lim,
        offset=off,
        has_more=bool(has_more),
        next_offset=next_offset,
        items=items,
    )
    return jsonable_encoder(response)


async def _build_myweb_detail_payload(*, user_id: str, report_id: str) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    view_ctx = await resolve_report_view_context(user_id, now_utc=now_utc)
    tier_str = str(view_ctx.subscription_tier)

    rows = await _fetch_myweb_full_rows_by_ids(user_id, [report_id])
    if not rows:
        raise HTTPException(status_code=404, detail="MyWeb report not found")

    published_row = apply_myweb_report_access_for_viewer(
        rows[0],
        context=view_ctx,
        now_utc=now_utc,
    )
    if not published_row:
        raise HTTPException(status_code=404, detail="MyWeb report not found")

    response = MyWebReportDetailResponse(
        user_id=user_id,
        viewer_tier=str(tier_str),
        item=_build_myweb_report_record(published_row, include_body=True),
    )
    return jsonable_encoder(response)


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

COMMON_OBSERVATION_NOTE_LINES = (
    "このレポートは、入力から見える変化をまとめた『観測』です。",
    "診断や断定を目的としたものではありません。",
)


def _observation_section_titles(report_type: str) -> Tuple[str, str, str, str, str]:
    if report_type == "daily":
        return (
            "【昨日、見えていたこと】",
            "【気持ちが動いた流れ】",
            "【昨日、気持ちが出やすかった時間】",
            "【あなたへのコメント】",
            "【このレポートについて】",
        )
    if report_type == "weekly":
        return (
            "【今週、見えていたこと】",
            "【気持ちが動いた流れ】",
            "【今週、気持ちが出やすかった時間】",
            "【あなたへのコメント】",
            "【このレポートについて】",
        )
    return (
        "【今月、見えていたこと】",
        "【気持ちが動いた流れ】",
        "【今月、気持ちが出やすかった時間】",
        "【あなたへのコメント】",
        "【このレポートについて】",
    )


def _common_observation_note_lines() -> List[str]:
    return list(COMMON_OBSERVATION_NOTE_LINES)


def _fallback_overview_line(report_type: str) -> str:
    if report_type == "daily":
        return "昨日は、ひとつの流れとして言い切るほど強い偏りはまだ見えていません。"
    if report_type == "weekly":
        return "今週は、ひとつの流れとして言い切るほど強い偏りはまだ見えていません。"
    return "今月は、ひとつの流れとして言い切るほど強い偏りはまだ見えていません。"


def _fallback_reader_comment(report_type: str) -> str:
    if report_type == "daily":
        return "まとまりきらない感じそのものが、昨日の自然な状態だったのかもしれません。"
    if report_type == "weekly":
        return "日によって違う動きが出ていたこと自体に、今週らしさが表れていたようです。"
    return "いくつかの流れが重なっていたこと自体が、今月の自然な特徴だったようです。"


def _fallback_time_comment(report_type: str) -> str:
    if report_type == "daily":
        return "昨日は特定の時間だけが強かったというより、一日の中に反応が広く散っていました。"
    if report_type == "weekly":
        return "今週は特定の時間に固定されるより、朝から夜まで広く反応が出ていました。"
    return "今月は特定の時間だけが際立つというより、時間帯ごとに反応の出方が分かれていました。"


def _time_bucket_reader_label(value: Any) -> str:
    key = _normalize_time_bucket_key(value)
    if key:
        return TIME_BUCKET_READER_LABELS.get(key, key)
    s = str(value or "").strip()
    return s or "特定の時間帯"


def _time_bucket_dominant_key(row: Dict[str, Any]) -> Optional[str]:
    if not isinstance(row, dict):
        return None
    raw = str(row.get("dominantKey") or row.get("dominant_key") or "").strip()
    if raw:
        if raw in EMOTION_KEYS:
            return raw
        if raw in JP_TO_KEY:
            return JP_TO_KEY.get(raw)
    for candidate in (row.get("weightedCounts"), row.get("weighted_counts"), row.get("counts"), row.get("sharePct"), row.get("share_pct")):
        key = _dominant_key_from_map(candidate)
        if key:
            return key
    return None


def _build_time_bucket_comment(
    *,
    report_type: str,
    peak_bucket: Optional[Dict[str, Any]],
    fallback_dominant_key: Optional[str] = None,
) -> str:
    if not isinstance(peak_bucket, dict) or _coerce_int(peak_bucket.get("inputCount"), 0) <= 0:
        return _fallback_time_comment(report_type)

    bucket_key = _normalize_time_bucket_key(peak_bucket.get("bucket") or peak_bucket.get("label"))
    time_label = _time_bucket_reader_label(peak_bucket.get("bucket") or peak_bucket.get("label"))
    bucket_dom_key = _time_bucket_dominant_key(peak_bucket) or fallback_dominant_key
    bucket_dom_label = KEY_TO_JP.get(bucket_dom_key, bucket_dom_key) if bucket_dom_key else ""
    context_clause = TIME_BUCKET_CONTEXT_CLAUSES.get(bucket_key or "", "その時間帯がひとつの山になっていた")

    if report_type == "daily":
        first = f"昨日は{time_label}に気持ちが表へ上がりやすい一日でした。"
    elif report_type == "weekly":
        first = f"今週は{time_label}に気持ちが表へ上がりやすい流れがありました。"
    else:
        first = f"今月は{time_label}に反応が集まりやすい傾向が続いていました。"

    if bucket_dom_label:
        second = f"とくに「{bucket_dom_label}」がこの時間に出やすく、{context_clause}と読むと自然です。"
    else:
        second = f"{context_clause}と読むと自然です。"

    if report_type == "monthly":
        return f"{first}{second}この偏りは、月の中で何度か繰り返されていた流れでした。"
    return f"{first}{second}"

def _normalize_summary_movement_items(summary: Dict[str, Any]) -> List[str]:
    items: List[str] = []

    raw = summary.get("movementItems")
    if isinstance(raw, list):
        for x in raw:
            s = str(x or "").strip()
            if s:
                items.append(s)

    if not items:
        evidence = summary.get("evidence") if isinstance(summary.get("evidence"), dict) else {}
        ev_items = evidence.get("items") if isinstance(evidence.get("items"), list) else []
        for row in ev_items:
            if isinstance(row, dict):
                s = str(row.get("text") or "").strip()
                if s:
                    items.append(s)

    return items


EMOTION_NEED_PHRASE = {
    "joy": "前向きさや手応えを感じたい気持ち",
    "sadness": "気持ちを守りながら静かに整理したい気持ち",
    "anxiety": "先を見通して安心を確かめたい気持ち",
    "anger": "自分の納得できる線を守りたい気持ち",
    "calm": "落ち着ける感覚を保ちたい気持ち",
}

EMOTION_FLOW_PHRASE = {
    "joy": "手応えや前向きさを確かめたい流れ",
    "sadness": "気持ちを急がせず、静かに整理したい流れ",
    "anxiety": "先を見通して安心できる位置を確かめたい流れ",
    "anger": "自分の納得できる線を守りたい流れ",
    "calm": "落ち着ける感覚を保ち直したい流れ",
}

TIME_BUCKET_READER_LABELS: Dict[str, str] = {
    "0-6": "深夜から早朝",
    "6-12": "朝",
    "12-18": "昼から夕方",
    "18-24": "夜",
}

TIME_BUCKET_CONTEXT_CLAUSES: Dict[str, str] = {
    "0-6": "周囲が静かになる中で、内側の反応が表面へ上がりやすかった",
    "6-12": "一日の始まりに、その日の向きが比較的はっきり表れやすかった",
    "12-18": "日中の動きの中で、反応がまとまって出やすかった",
    "18-24": "一日の終わりにかけて、残っていた気持ちが表面へ上がりやすかった",
}


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
    weekly_snapshot = payload.get("weekly_snapshot") if isinstance(payload.get("weekly_snapshot"), dict) else {}
    time_buckets = _extract_time_bucket_rows(snapshot_views=views, analysis_payload=payload)
    peak_bucket = _find_peak_time_bucket(time_buckets)

    movement_items: List[str] = []
    overview_comment = ""
    time_comment = ""
    reader_comment = ""

    if report_type == "daily":
        metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        share_map = _first_non_empty_emotion_map(metrics.get("sharePct"))
        weighted_counts = _first_non_empty_emotion_map(metrics.get("totals"))
        top_items = _pick_top_share_items(share_map, limit=2)
        dominant_key = str(metrics.get("dominantKey") or "").strip() or _dominant_key_from_map(weighted_counts) or (top_items[0][0] if top_items else None)
        dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"
        secondary_label = KEY_TO_JP.get(top_items[1][0], top_items[1][0]) if len(top_items) >= 2 else None
        total_all = _coerce_int(metrics.get("totalAll") or snap_summary.get("emotions_public") or snap_summary.get("emotions_total"), 0)
        movement_key = str(movement.get("key") or "").strip()
        flow_phrase = EMOTION_FLOW_PHRASE.get(dominant_key, "何かを保ち直したい流れ")
        peak_time_label = _time_bucket_reader_label((peak_bucket or {}).get("bucket") or (peak_bucket or {}).get("label")) if peak_bucket else ""

        if total_all > 0 and dominant_key:
            overview_comment = f"昨日は、「{dominant_label}」が強く跳ねたというより、{flow_phrase}が一日の土台に残っていたようです。"
            if secondary_label and secondary_label != dominant_label:
                overview_comment += f" そこに「{secondary_label}」も重なり、気持ちが一つだけでは言い切れない一日でした。"
            elif movement_key == "down":
                overview_comment += " 少しずつ静かなほうへ戻ろうとする向きも見えていました。"
            elif movement_key == "up":
                overview_comment += " 表に出る反応が前日より少し濃くなっていたようです。"
            elif movement_key == "swing":
                overview_comment += " 昨日までとは少し違う角度の反応も混ざっていました。"
        elif total_all > 0:
            overview_comment = "昨日は、ひとつの感情に言い切れないままでも、気持ちがいくつかの向きで重なっていた一日でした。"
        else:
            overview_comment = "昨日は入力が少なめで、ひとつの流れとして言い切るほどの偏りはまだ見えていません。"

        if dominant_key:
            movement_items.append(f"いちばん前に出ていたのは「{dominant_label}」でした。")
        if secondary_label and secondary_label != dominant_label:
            movement_items.append(f"「{secondary_label}」も重なり、同じテーマに対して別の角度の反応が混ざっていました。")
        if movement_key:
            movement_line = _render_daily_motion_line(movement)
            if movement_line and movement_line not in movement_items:
                movement_items.append(movement_line)

        time_comment = _build_time_bucket_comment(
            report_type="daily",
            peak_bucket=peak_bucket,
            fallback_dominant_key=dominant_key,
        )

        if total_all > 0:
            reader_parts = []
            if dominant_key:
                reader_parts.append(
                    f"昨日の反応は、「{dominant_label}」が一度強く出たというより、{flow_phrase}がじわっと続いていたようです。"
                )
            else:
                reader_parts.append("昨日は、気持ちが一つにまとまりきらないまま重なっていた一日として読むほうが自然です。")
            if secondary_label and secondary_label != dominant_label:
                reader_parts.append(
                    f"「{secondary_label}」が混ざっていたのは、同じテーマに対して心が別の角度からも反応していたためと考えると納得しやすい流れです。"
                )
            else:
                reader_parts.append(
                    "似た反応がまとまっていたことから、その場ごとの小さな揺れより、気になっているものが続いていた可能性があります。"
                )
            if peak_time_label:
                reader_parts.append(
                    f"とくに{peak_time_label}に気持ちが上がりやすかったぶん、その時間になると残っていたものが見えやすかったのかもしれません。"
                )
            else:
                reader_parts.append(
                    "時間が変わっても似た向きが残っていたのは、気持ちの芯が一日の中で続いていたためと見るほうが自然です。"
                )
            reader_comment = "".join(reader_parts)
        else:
            reader_comment = _fallback_reader_comment("daily")

    elif report_type == "weekly":
        snapshot_metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        share_map = _first_non_empty_emotion_map(weekly_snapshot.get("share"), snapshot_metrics.get("sharePct"))
        weighted_counts = _first_non_empty_emotion_map(weekly_snapshot.get("wcounts"), snapshot_metrics.get("totals"))
        top_items = _pick_top_share_items(share_map, limit=2)
        dominant_key = _dominant_key_from_map(weighted_counts) or (top_items[0][0] if top_items else None)
        dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"
        secondary_label = KEY_TO_JP.get(top_items[1][0], top_items[1][0]) if len(top_items) >= 2 else None
        n_events = _coerce_int(weekly_snapshot.get("n_events") or snap_summary.get("emotions_public") or snap_summary.get("emotions_total"), 0)
        alternation_rate = _coerce_float(weekly_snapshot.get("alternation_rate"), 0.0)
        flow_phrase = EMOTION_FLOW_PHRASE.get(dominant_key, "何かを保ち直したい流れ")
        peak_time_label = _time_bucket_reader_label((peak_bucket or {}).get("bucket") or (peak_bucket or {}).get("label")) if peak_bucket else ""

        if dominant_key:
            overview_comment = f"今週は、「{dominant_label}」が目立ったというより、{flow_phrase}が週の土台に残っていたようです。"
            if secondary_label and secondary_label != dominant_label:
                overview_comment += f" そこに「{secondary_label}」も重なり、ひとつの空気感だけでは言い切れない週でした。"
            if alternation_rate >= 0.55:
                overview_comment += " 日ごとの切り替わりも比較的多く、そのたびに気持ちの置き場を探し直していたようです。"
            elif 0 < alternation_rate <= 0.25:
                overview_comment += " 大きな切り替わりは少なく、近い向きの反応が続いていました。"
            else:
                overview_comment += " 週の中で少しずつ向きが変わる場面も見えていました。"
        elif n_events > 0:
            overview_comment = "今週は入力があり、ひとつに言い切れないままでも気持ちの流れを追える週でした。"
        else:
            overview_comment = "今週は入力が少なめで、ひとつの流れとして言い切るほどの偏りはまだ見えていません。"

        if dominant_key:
            movement_items.append(f"週全体では「{dominant_label}」の比重がいちばん高めでした。")
        if secondary_label and secondary_label != dominant_label:
            movement_items.append(f"「{secondary_label}」も重なり、同じテーマに対する反応の角度が週の中で少し変わっていました。")
        if alternation_rate >= 0.55:
            movement_items.append("日ごとに気持ちの向きが切り替わる場面が比較的多めでした。")
        elif 0 < alternation_rate <= 0.25:
            movement_items.append("大きな切り替わりは少なく、近い反応が続きやすい週でした。")
        elif n_events > 0:
            movement_items.append("気持ちの向きは週の中でゆるやかに動いていました。")

        time_comment = _build_time_bucket_comment(
            report_type="weekly",
            peak_bucket=peak_bucket,
            fallback_dominant_key=dominant_key,
        )

        if n_events > 0:
            reader_parts = []
            if dominant_key:
                reader_parts.append(
                    f"今週の反応は、「{dominant_label}」が単発で強かったというより、{flow_phrase}が週を通して残っていたようです。"
                )
            else:
                reader_parts.append("今週は、日ごとの差よりも、重なっていた空気感そのものを受け取るほうが自然です。")
            if secondary_label and secondary_label != dominant_label:
                reader_parts.append(
                    f"「{secondary_label}」が重なっていたのは、同じテーマに対して心が別の角度からも反応していたためと考えると納得しやすい流れです。"
                )
            else:
                reader_parts.append(
                    "似た反応が何度も戻っていたことから、日ごとの差よりも、週を通して残っていたもののほうが大きかった可能性があります。"
                )
            if alternation_rate >= 0.55:
                reader_parts.append(
                    "切り替わりが多かったのも、気分がばらばらだったというより、そのたびに気持ちの置き場を探し直していた流れとして読むほうが自然です。"
                )
            elif 0 < alternation_rate <= 0.25:
                reader_parts.append(
                    "大きく切り替わらなかったのは、週のあいだ同じ方向の反応が静かに残っていたためと見られます。"
                )
            else:
                reader_parts.append(
                    "週の中で向きが少しずつ変わっていても、底にある反応の軸は大きくは変わっていませんでした。"
                )
            if peak_time_label:
                reader_parts.append(
                    f"とくに{peak_time_label}に気持ちが上がりやすかったぶん、その時間帯に週らしさが集まっていたのかもしれません。"
                )
            else:
                reader_parts.append(
                    "時間帯が変わっても近い向きが残っていたのは、週の土台に同じ反応が続いていたためと見るほうが自然です。"
                )
            reader_comment = "".join(reader_parts)
        else:
            reader_comment = _fallback_reader_comment("weekly")

    else:
        snapshot_metrics = views.get("metrics") if isinstance(views.get("metrics"), dict) else {}
        weeks = views.get("weeks") if isinstance(views.get("weeks"), list) else []
        share_map = _first_non_empty_emotion_map(snapshot_metrics.get("sharePct"))
        totals_map = _first_non_empty_emotion_map(snapshot_metrics.get("totals"))
        dominant_key = _dominant_key_from_map(totals_map) or _dominant_key_from_map(share_map)
        dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"
        top_items = _pick_top_share_items(share_map, limit=2)
        secondary_label = KEY_TO_JP.get(top_items[1][0], top_items[1][0]) if len(top_items) >= 2 else None
        total_all = _coerce_int(snapshot_metrics.get("totalAll") or snap_summary.get("emotions_public") or snap_summary.get("emotions_total"), 0)
        flow_phrase = EMOTION_FLOW_PHRASE.get(dominant_key, "何かを保ち直したい流れ")
        peak_time_label = _time_bucket_reader_label((peak_bucket or {}).get("bucket") or (peak_bucket or {}).get("label")) if peak_bucket else ""

        peak_week = None
        peak_week_total = -1
        calm_first_half = 0
        calm_second_half = 0
        dominant_repeat_count = 0
        week_switches = 0
        last_week_dom: Optional[str] = None
        for idx, week in enumerate(weeks or []):
            if not isinstance(week, dict):
                continue
            total = _coerce_int(week.get("total"), 0)
            if total <= 0:
                total = sum(_coerce_int(week.get(k), 0) for k in EMOTION_KEYS)
            if total > peak_week_total:
                peak_week_total = total
                peak_week = week
            if idx < 2:
                calm_first_half += _coerce_int(week.get("calm"), 0)
            else:
                calm_second_half += _coerce_int(week.get("calm"), 0)
            week_dom = _dominant_key_from_map(week)
            if week_dom:
                if last_week_dom and last_week_dom != week_dom:
                    week_switches += 1
                last_week_dom = week_dom
                if dominant_key and week_dom == dominant_key:
                    dominant_repeat_count += 1

        peak_week_label = str((peak_week or {}).get("label") or "") if peak_week else ""

        if dominant_key:
            overview_comment = f"今月は、「{dominant_label}」が強く出たというより、{flow_phrase}が月の土台に残っていたようです。"
            if secondary_label and secondary_label != dominant_label:
                overview_comment += f" そこに「{secondary_label}」も重なり、ひとつの感情だけでは言い切れない月でした。"
            if dominant_repeat_count >= 3:
                overview_comment += f" 週をまたいで「{dominant_label}」が何度も中心に戻っていたのも、そのテーマが長く気にかかっていたことを示していそうです。"
            elif week_switches >= 2:
                overview_comment += " 週ごとに向きが入れ替わっていても、まったく別の反応になったというより、同じテーマの表れ方が変わっていたようです。"
            else:
                overview_comment += " 近い方向の反応が、月を通して静かに続いていました。"
            if peak_week_label:
                overview_comment += f" とくに{peak_week_label}は動きが強めでした。"
            if calm_second_half > calm_first_half and calm_second_half > 0:
                overview_comment += " 後半には、少し整え直そうとする向きも見えていました。"
        else:
            overview_comment = "今月は入力が少なめで、ひとつの流れとして言い切るほどの偏りはまだ見えていません。"

        if dominant_key:
            movement_items.append(f"月全体では「{dominant_label}」の比重がいちばん高めでした。")
        if secondary_label and secondary_label != dominant_label:
            movement_items.append(f"「{secondary_label}」も重なり、同じテーマへの反応に別の角度が加わっていました。")
        if peak_week_label:
            movement_items.append(f"{peak_week_label}は、今月の中でも反応の動きが強めでした。")
        if calm_second_half > calm_first_half and calm_second_half > 0:
            movement_items.append("後半にかけて『平穏』が少し増え、整え直す向きも見えていました。")
        elif week_switches >= 2:
            movement_items.append("週をまたぐごとに、気持ちの向きが少しずつ入れ替わっていました。")

        time_comment = _build_time_bucket_comment(
            report_type="monthly",
            peak_bucket=peak_bucket,
            fallback_dominant_key=dominant_key,
        )

        if total_all > 0:
            reader_parts = []
            if dominant_key:
                lead = f"今月は「{dominant_label}」を軸にしながら"
                if secondary_label and secondary_label != dominant_label:
                    lead += f"、「{secondary_label}」も重なり、"
                else:
                    lead += "、"
                lead += "同じテーマに対する反応の質が少しずつ変わっていた月でした。"
                reader_parts.append(lead)
            else:
                reader_parts.append("今月は、ひとつに言い切れない流れがそのまま重なっていた月として読むほうが自然です。")
            if dominant_repeat_count >= 3 and dominant_key:
                reader_parts.append(
                    f"週をまたいで「{dominant_label}」が何度も中心に戻っていたため、単発の揺れより、長く気にかかるテーマが続いていた可能性があります。"
                )
            elif week_switches >= 2:
                reader_parts.append(
                    "週ごとに中心は入れ替わっていましたが、反応が別物になったというより、同じテーマへの表れ方が変化していたようです。"
                )
            else:
                reader_parts.append(
                    f"大きく軸が変わらなかったのは、月のあいだ{flow_phrase}が土台に残っていたためと見るほうが自然です。"
                )
            if peak_week_label:
                reader_parts.append(
                    f"とくに{peak_week_label}は反応の動きが強く、その週が今月全体の空気を押し上げていたようです。"
                )
            if calm_second_half > calm_first_half and calm_second_half > 0:
                reader_parts.append(
                    "後半に『平穏』が少し増えていたのは、月の終わりに向けて気持ちを整え直す動きが入っていたためと読むと自然です。"
                )
            else:
                reader_parts.append(
                    "月末にかけても大きく静まりきらなかったことから、反応の軸は最後まで残っていたようです。"
                )
            reader_parts.append(
                "複数の感情が重なっていたのは、ひとつの理由だけで揺れたというより、同じテーマに対して心が何度も別の角度から反応していたためと考えると納得しやすい流れです。"
            )
            if peak_time_label:
                reader_parts.append(
                    f"とくに{peak_time_label}に気持ちが上がりやすかったぶん、その時間帯に今月らしさが集まっていたのかもしれません。"
                )
            reader_comment = "".join(reader_parts)
        else:
            reader_comment = _fallback_reader_comment("monthly")

    clean_movement_items = [s for s in movement_items if str(s or "").strip()][:4]
    return {
        "overviewComment": overview_comment.strip() or None,
        "movementItems": clean_movement_items,
        "timeComment": time_comment.strip() or None,
        "readerComment": reader_comment.strip() or None,
        "structuralComment": overview_comment.strip() or None,
        "gentleComment": reader_comment.strip() or None,
        "nextPoints": [],
        "evidence": {
            "items": [{"text": s} for s in clean_movement_items]
        },
        "compositionMode": "replace",
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
    sec_overview, sec_movement, sec_time, sec_comment, sec_note = _observation_section_titles(report_type)

    overview = str(
        summary.get("overviewComment")
        or summary.get("structuralComment")
        or ""
    ).strip()

    movement_items = _normalize_summary_movement_items(summary)

    time_comment = str(
        summary.get("timeComment")
        or ""
    ).strip()

    reader_comment = str(
        summary.get("readerComment")
        or summary.get("gentleComment")
        or ""
    ).strip()

    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)

    lines.append("")
    lines.append(sec_overview)
    lines.append(overview or _fallback_overview_line(report_type))
    lines.append("")

    lines.append(sec_movement)
    if movement_items:
        for item in movement_items[:4]:
            lines.append(f"・{item}")
    else:
        lines.append("・大きな動きとしてはまだまとまりませんでした。")
    lines.append("")

    lines.append(sec_time)
    lines.append(time_comment or _fallback_time_comment(report_type))
    lines.append("")

    lines.append(sec_comment)
    lines.append(reader_comment or _fallback_reader_comment(report_type))
    lines.append("")

    lines.append(sec_note)
    lines.extend(_common_observation_note_lines())

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

    lines.append("【このレポートについて】")
    lines.extend(_common_observation_note_lines())
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

    if not summary.get("overviewComment") and isinstance(narrative.get("structural_comment"), str):
        summary["overviewComment"] = str(narrative.get("structural_comment") or "").strip() or None
    if not summary.get("readerComment") and isinstance(narrative.get("gentle_comment"), str):
        summary["readerComment"] = str(narrative.get("gentle_comment") or "").strip() or None
    if not summary.get("structuralComment") and isinstance(narrative.get("structural_comment"), str):
        summary["structuralComment"] = str(narrative.get("structural_comment") or "").strip() or None
    if not summary.get("gentleComment") and isinstance(narrative.get("gentle_comment"), str):
        summary["gentleComment"] = str(narrative.get("gentle_comment") or "").strip() or None
    summary["nextPoints"] = []
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



def _emotion_label_ja(label: Any) -> str:
    s = str(label or "").strip()
    return KEY_TO_JP.get(s, s)


def _format_minutes_ja(value: Any) -> Optional[str]:
    try:
        v = float(value)
    except Exception:
        return None
    if v < 0:
        return None
    mins = int(round(v))
    if mins >= 60:
        hours = mins // 60
        rem = mins % 60
        if rem == 0:
            return f"{hours}時間"
        return f"{hours}時間{rem}分"
    return f"{mins}分"


def _localize_transition_key(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    if "->" in s:
        left, right = s.split("->", 1)
        return f"{_emotion_label_ja(left)} → {_emotion_label_ja(right)}"
    if "→" in s:
        left, right = s.split("→", 1)
        return f"{_emotion_label_ja(left)} → {_emotion_label_ja(right)}"
    return _emotion_label_ja(s)


DEEP_THEME_HINT_LABELS: Dict[str, str] = {
    "self_pressure": "自分を急がせる言葉",
    "interpersonal_caution": "人との距離を気にする言葉",
    "fatigue_limit": "限界を感じる言葉",
    "self_doubt": "自分を責めやすい言葉",
    "generic": "前に出ていた言葉",
}



DEEP_THEME_HINT_MEANING_COMMENTS: Dict[str, str] = {
    "self_pressure": "自分を整えたい気持ちが強いほど、内側の緊張も高まりやすい週でした。",
    "interpersonal_caution": "人への配慮が強い場面で、静かな不安が続きやすい週でした。",
    "fatigue_limit": "しんどさが言葉に出たあと、疲れから静けさへ戻る流れも見えていました。",
    "self_doubt": "うまくできていない感覚が前に出るほど、焦りや落ち込みにつながりやすい週でした。",
    "generic": "この言葉のまとまりが、今週の気持ちの動きとつながって見えていました。",
}

DEEP_SUMMARY_SOURCE_V1 = "api_deep_summary"
DEEP_SUMMARY_SOURCE_WEEKLY_V2 = "api_deep_summary_v2"
DEEP_SUMMARY_SOURCE_DAILY_V2 = "api_deep_summary_daily_v2"
DEEP_SUMMARY_SOURCE_MONTHLY_V2 = "api_deep_summary_monthly_v2"

MONTHLY_PHASE_LABELS: Dict[str, str] = {
    "first_half": "前半",
    "second_half": "後半",
}


def _normalize_transition_matrix(raw: Any) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    if not isinstance(raw, dict):
        return out
    for from_label, row in raw.items():
        f = str(from_label or "").strip()
        if not f:
            continue
        out[f] = {}
        row_dict = row if isinstance(row, dict) else {}
        for to_label in EMOTION_KEYS:
            out[f][to_label] = _coerce_int(row_dict.get(to_label), 0)
        for to_label, value in row_dict.items():
            t = str(to_label or "").strip()
            if t and t not in out[f]:
                out[f][t] = _coerce_int(value, 0)
    return out


def _localize_transition_matrix(matrix: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    localized: Dict[str, Dict[str, int]] = {}
    for from_label, row in (matrix or {}).items():
        localized[_emotion_label_ja(from_label)] = {
            _emotion_label_ja(to_label): _coerce_int(value, 0)
            for to_label, value in (row or {}).items()
        }
    return localized


def _normalize_transition_edges(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        from_label = str(item.get("from_label") or item.get("fromLabel") or "").strip()
        to_label = str(item.get("to_label") or item.get("toLabel") or "").strip()
        if not from_label or not to_label:
            continue
        out.append(
            {
                "fromLabel": from_label,
                "toLabel": to_label,
                "fromLabelJa": _emotion_label_ja(from_label),
                "toLabelJa": _emotion_label_ja(to_label),
                "routeLabel": f"{_emotion_label_ja(from_label)} → {_emotion_label_ja(to_label)}",
                "count": _coerce_int(item.get("count"), 0),
                "share": _coerce_float(item.get("share"), 0.0),
                "meanMinutes": item.get("mean_minutes") if item.get("mean_minutes") is not None else item.get("meanMinutes"),
                "medianMinutes": item.get("median_minutes") if item.get("median_minutes") is not None else item.get("medianMinutes"),
                "p75Minutes": item.get("p75_minutes") if item.get("p75_minutes") is not None else item.get("p75Minutes"),
                "meanIntensityFrom": item.get("mean_intensity_from") if item.get("mean_intensity_from") is not None else item.get("meanIntensityFrom"),
                "meanIntensityTo": item.get("mean_intensity_to") if item.get("mean_intensity_to") is not None else item.get("meanIntensityTo"),
                "dominantTimeBuckets": list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or []),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )
    out.sort(key=lambda x: (_coerce_int(x.get("count"), 0), _coerce_float(x.get("share"), 0.0)), reverse=True)
    return out


def _normalize_recovery_time_rows(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        from_label = str(item.get("from_label") or item.get("fromLabel") or "").strip()
        to_label = str(item.get("to_label") or item.get("toLabel") or "").strip()
        if not from_label or not to_label:
            continue
        out.append(
            {
                "fromLabel": from_label,
                "toLabel": to_label,
                "fromLabelJa": _emotion_label_ja(from_label),
                "toLabelJa": _emotion_label_ja(to_label),
                "routeLabel": f"{_emotion_label_ja(from_label)} → {_emotion_label_ja(to_label)}",
                "count": _coerce_int(item.get("count"), 0),
                "meanMinutes": item.get("mean_minutes") if item.get("mean_minutes") is not None else item.get("meanMinutes"),
                "medianMinutes": item.get("median_minutes") if item.get("median_minutes") is not None else item.get("medianMinutes"),
                "minMinutes": item.get("min_minutes") if item.get("min_minutes") is not None else item.get("minMinutes"),
                "maxMinutes": item.get("max_minutes") if item.get("max_minutes") is not None else item.get("maxMinutes"),
                "dominantTimeBuckets": list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or []),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )
    out.sort(key=lambda x: (_coerce_int(x.get("count"), 0), -_coerce_float(x.get("meanMinutes"), 0.0)), reverse=True)
    return out


def _normalize_memo_triggers(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        keyword = str(item.get("keyword") or "").strip()
        if not keyword:
            continue
        related_emotions = [_emotion_label_ja(x) for x in list(item.get("related_emotions") or item.get("relatedEmotions") or []) if str(x or "").strip()]
        related_transitions = [_localize_transition_key(x) for x in list(item.get("related_transitions") or item.get("relatedTransitions") or []) if str(x or "").strip()]
        out.append(
            {
                "keyword": keyword,
                "count": _coerce_int(item.get("count"), 0),
                "relatedEmotions": related_emotions[:5],
                "relatedTransitions": related_transitions[:5],
                "dominantTimeBuckets": list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or []),
                "phraseSamples": list(item.get("phrase_samples") or item.get("phraseSamples") or [])[:3],
                "sourceTransitionKeys": [
                    str(x).strip()
                    for x in list(item.get("source_transition_keys") or item.get("sourceTransitionKeys") or [])
                    if str(x).strip()
                ][:5],
                "themeHint": str(item.get("theme_hint") or item.get("themeHint") or "generic").strip() or "generic",
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )
    out.sort(key=lambda x: _coerce_int(x.get("count"), 0), reverse=True)
    return out


def _normalize_memo_themes(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        theme_id = str(item.get("theme_id") or item.get("themeId") or item.get("themeLabel") or "").strip()
        theme_hint = str(item.get("theme_hint") or item.get("themeHint") or "generic").strip() or "generic"
        phrase_samples = [str(x).strip() for x in list(item.get("phrase_samples") or item.get("phraseSamples") or []) if str(x).strip()]
        linked_transition_keys = [str(x).strip() for x in list(item.get("linked_transition_keys") or item.get("linkedTransitionKeys") or []) if str(x).strip()]
        theme_label = str(item.get("themeLabel") or item.get("theme_label") or DEEP_THEME_HINT_LABELS.get(theme_hint, DEEP_THEME_HINT_LABELS["generic"]))
        if not theme_id and not theme_label:
            continue
        out.append(
            {
                "themeId": theme_id or theme_label or "theme",
                "themeHint": theme_hint,
                "themeLabel": theme_label,
                "keywords": [str(x).strip() for x in list(item.get("keywords") or []) if str(x).strip()][:4],
                "phraseSamples": phrase_samples[:3],
                "linkedTransitionKeys": linked_transition_keys[:4],
                "linkedRouteLabels": [_localize_transition_key(x) for x in linked_transition_keys[:4]],
                "dominantTimeBuckets": list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or [])[:2],
                "count": _coerce_int(item.get("count"), 0),
                "meaningComment": str(item.get("meaningComment") or item.get("meaning_comment") or DEEP_THEME_HINT_MEANING_COMMENTS.get(theme_hint, DEEP_THEME_HINT_MEANING_COMMENTS["generic"])).strip(),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )
    out.sort(key=lambda x: _coerce_int(x.get("count"), 0), reverse=True)
    return out[:3]


def _normalize_pattern_episodes(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pattern_id = str(item.get("pattern_id") or item.get("patternId") or item.get("patternLabel") or "").strip()
        route_keys = [str(x).strip() for x in list(item.get("route_keys") or item.get("routeKeys") or []) if str(x).strip()]
        route_labels = list(item.get("routeLabels") or item.get("route_labels") or [])
        if not route_labels:
            route_labels = [_localize_transition_key(x) for x in route_keys]
        recovery_route_key = str(item.get("recovery_route_key") or item.get("recoveryRouteKey") or "").strip()
        out.append(
            {
                "patternId": pattern_id or "pattern",
                "linkedThemeIds": [str(x).strip() for x in list(item.get("linked_theme_ids") or item.get("linkedThemeIds") or []) if str(x).strip()],
                "routeKeys": route_keys[:4],
                "routeLabels": [str(x).strip() for x in list(route_labels or []) if str(x).strip()][:4],
                "recoveryRouteKey": recovery_route_key,
                "recoveryRouteLabel": str(item.get("recoveryRouteLabel") or item.get("recovery_route_label") or _localize_transition_key(recovery_route_key)).strip(),
                "dominantTimeBuckets": list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or [])[:2],
                "count": _coerce_int(item.get("count"), 0),
                "patternLabel": str(item.get("patternLabel") or item.get("pattern_label") or item.get("label") or "").strip(),
                "patternComment": str(item.get("patternComment") or item.get("pattern_comment") or item.get("description") or "").strip(),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )
    out.sort(key=lambda x: _coerce_int(x.get("count"), 0), reverse=True)
    return out[:5]




def _normalize_monthly_phases(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out

    for item in raw:
        if not isinstance(item, dict):
            continue

        phase_id = str(item.get("phase_id") or item.get("phaseId") or "").strip()
        phase_label = str(
            item.get("phase_label")
            or item.get("phaseLabel")
            or MONTHLY_PHASE_LABELS.get(phase_id, "")
        ).strip()

        theme_hints = [
            str(x).strip()
            for x in list(item.get("theme_hints") or item.get("themeHints") or [])
            if str(x).strip()
        ][:3]
        theme_labels = [
            str(x).strip()
            for x in list(item.get("theme_labels") or item.get("themeLabels") or [])
            if str(x).strip()
        ]
        if not theme_labels:
            theme_labels = [
                DEEP_THEME_HINT_LABELS.get(hint, DEEP_THEME_HINT_LABELS["generic"])
                for hint in theme_hints
            ]

        route_keys = [
            str(x).strip()
            for x in list(item.get("route_keys") or item.get("routeKeys") or [])
            if str(x).strip()
        ][:4]
        route_labels = [
            str(x).strip()
            for x in list(item.get("route_labels") or item.get("routeLabels") or [])
            if str(x).strip()
        ]
        if not route_labels:
            route_labels = [_localize_transition_key(x) for x in route_keys]

        recovery_route_key = str(
            item.get("recovery_route_key") or item.get("recoveryRouteKey") or ""
        ).strip()
        recovery_route_label = str(
            item.get("recovery_route_label")
            or item.get("recoveryRouteLabel")
            or _localize_transition_key(recovery_route_key)
        ).strip()

        dominant_buckets = [
            _normalize_time_bucket_key(x) or str(x).strip()
            for x in list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or [])
            if str(x).strip()
        ][:2]

        entry_count = _coerce_int(item.get("entry_count") or item.get("entryCount"), 0)
        transition_count = _coerce_int(item.get("transition_count") or item.get("transitionCount"), 0)

        if not phase_id and not phase_label:
            continue
        if entry_count <= 0 and transition_count <= 0 and not theme_hints and not route_keys and not recovery_route_key:
            continue

        out.append(
            {
                "phaseId": phase_id or phase_label or "phase",
                "phaseLabel": phase_label or phase_id or "区間",
                "periodStartIso": str(item.get("period_start_iso") or item.get("periodStartIso") or "").strip(),
                "periodEndIso": str(item.get("period_end_iso") or item.get("periodEndIso") or "").strip(),
                "entryCount": entry_count,
                "transitionCount": transition_count,
                "themeHints": theme_hints,
                "themeLabels": theme_labels[:3],
                "phraseSamples": [
                    str(x).strip()
                    for x in list(item.get("phrase_samples") or item.get("phraseSamples") or [])
                    if str(x).strip()
                ][:3],
                "routeKeys": route_keys,
                "routeLabels": route_labels[:4],
                "recoveryRouteKey": recovery_route_key,
                "recoveryRouteLabel": recovery_route_label,
                "dominantTimeBuckets": dominant_buckets,
                "dominantTimeBucketLabels": [_time_bucket_reader_label(x) for x in dominant_buckets],
                "patternIds": [
                    str(x).strip()
                    for x in list(item.get("pattern_ids") or item.get("patternIds") or [])
                    if str(x).strip()
                ][:4],
                "phaseComment": str(item.get("phase_comment") or item.get("phaseComment") or "").strip(),
                "count": _coerce_int(item.get("count"), entry_count),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )

    phase_rank = {"first_half": 0, "second_half": 1}
    out.sort(
        key=lambda x: (
            str(x.get("periodStartIso") or ""),
            phase_rank.get(str(x.get("phaseId") or ""), 99),
        )
    )
    return out[:2]



def _normalize_monthly_shifts(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out

    for item in raw:
        if not isinstance(item, dict):
            continue

        shift_id = str(item.get("shift_id") or item.get("shiftId") or "").strip()
        from_phase_id = str(item.get("from_phase_id") or item.get("fromPhaseId") or "").strip()
        to_phase_id = str(item.get("to_phase_id") or item.get("toPhaseId") or "").strip()
        if not shift_id and not (from_phase_id and to_phase_id):
            continue

        emerging_theme_hints = [
            str(x).strip()
            for x in list(item.get("emerging_theme_hints") or item.get("emergingThemeHints") or [])
            if str(x).strip()
        ][:3]
        settling_theme_hints = [
            str(x).strip()
            for x in list(item.get("settling_theme_hints") or item.get("settlingThemeHints") or [])
            if str(x).strip()
        ][:3]

        emerging_theme_labels = [
            str(x).strip()
            for x in list(item.get("emerging_theme_labels") or item.get("emergingThemeLabels") or [])
            if str(x).strip()
        ] or [
            DEEP_THEME_HINT_LABELS.get(hint, DEEP_THEME_HINT_LABELS["generic"])
            for hint in emerging_theme_hints
        ]
        settling_theme_labels = [
            str(x).strip()
            for x in list(item.get("settling_theme_labels") or item.get("settlingThemeLabels") or [])
            if str(x).strip()
        ] or [
            DEEP_THEME_HINT_LABELS.get(hint, DEEP_THEME_HINT_LABELS["generic"])
            for hint in settling_theme_hints
        ]

        emerging_route_keys = [
            str(x).strip()
            for x in list(item.get("emerging_route_keys") or item.get("emergingRouteKeys") or [])
            if str(x).strip()
        ][:4]
        settling_route_keys = [
            str(x).strip()
            for x in list(item.get("settling_route_keys") or item.get("settlingRouteKeys") or [])
            if str(x).strip()
        ][:4]

        emerging_route_labels = [
            str(x).strip()
            for x in list(item.get("emerging_route_labels") or item.get("emergingRouteLabels") or [])
            if str(x).strip()
        ] or [_localize_transition_key(x) for x in emerging_route_keys]
        settling_route_labels = [
            str(x).strip()
            for x in list(item.get("settling_route_labels") or item.get("settlingRouteLabels") or [])
            if str(x).strip()
        ] or [_localize_transition_key(x) for x in settling_route_keys]

        from_recovery_route_key = str(
            item.get("from_recovery_route_key") or item.get("fromRecoveryRouteKey") or ""
        ).strip()
        to_recovery_route_key = str(
            item.get("to_recovery_route_key") or item.get("toRecoveryRouteKey") or ""
        ).strip()
        from_recovery_route_label = str(
            item.get("from_recovery_route_label")
            or item.get("fromRecoveryRouteLabel")
            or _localize_transition_key(from_recovery_route_key)
        ).strip()
        to_recovery_route_label = str(
            item.get("to_recovery_route_label")
            or item.get("toRecoveryRouteLabel")
            or _localize_transition_key(to_recovery_route_key)
        ).strip()

        normalized = {
            "shiftId": shift_id or f"{from_phase_id}_to_{to_phase_id}",
            "fromPhaseId": from_phase_id,
            "fromPhaseLabel": str(
                item.get("from_phase_label")
                or item.get("fromPhaseLabel")
                or MONTHLY_PHASE_LABELS.get(from_phase_id, from_phase_id)
            ).strip() or "前半",
            "toPhaseId": to_phase_id,
            "toPhaseLabel": str(
                item.get("to_phase_label")
                or item.get("toPhaseLabel")
                or MONTHLY_PHASE_LABELS.get(to_phase_id, to_phase_id)
            ).strip() or "後半",
            "emergingThemeHints": emerging_theme_hints,
            "settlingThemeHints": settling_theme_hints,
            "emergingThemeLabels": emerging_theme_labels[:3],
            "settlingThemeLabels": settling_theme_labels[:3],
            "emergingRouteKeys": emerging_route_keys,
            "settlingRouteKeys": settling_route_keys,
            "emergingRouteLabels": emerging_route_labels[:4],
            "settlingRouteLabels": settling_route_labels[:4],
            "fromRecoveryRouteKey": from_recovery_route_key,
            "toRecoveryRouteKey": to_recovery_route_key,
            "fromRecoveryRouteLabel": from_recovery_route_label,
            "toRecoveryRouteLabel": to_recovery_route_label,
            "directionHint": str(item.get("direction_hint") or item.get("directionHint") or "mixed").strip() or "mixed",
            "shiftLabel": str(item.get("shift_label") or item.get("shiftLabel") or "").strip(),
            "shiftComment": str(item.get("shift_comment") or item.get("shiftComment") or "").strip(),
            "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
            "notes": list(item.get("notes") or []),
        }
        if not (
            normalized["shiftLabel"]
            or normalized["shiftComment"]
            or normalized["emergingThemeLabels"]
            or normalized["settlingThemeLabels"]
            or normalized["emergingRouteLabels"]
            or normalized["settlingRouteLabels"]
            or normalized["fromRecoveryRouteLabel"]
            or normalized["toRecoveryRouteLabel"]
        ):
            continue
        out.append(normalized)

    return out[:3]


def _normalize_control_patterns(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pattern_id = str(item.get("pattern_id") or item.get("patternId") or "").strip()
        label = str(item.get("label") or "").strip()
        if not pattern_id and not label:
            continue
        rep_edges = _normalize_transition_edges(list(item.get("representative_edges") or item.get("representativeEdges") or []))
        memo_triggers = _normalize_memo_triggers(list(item.get("memo_triggers") or item.get("memoTriggers") or []))
        transition_keys_raw = [str(x).strip() for x in list(item.get("transition_keys") or item.get("transitionKeys") or []) if str(x).strip()]
        out.append(
            {
                "patternId": pattern_id or label or "pattern",
                "label": label or "制御傾向",
                "description": str(item.get("description") or "").strip() or None,
                "size": _coerce_int(item.get("size"), 0),
                "score": _coerce_float(item.get("score"), 0.0),
                "transitionKeys": transition_keys_raw,
                "transitionRouteLabels": [_localize_transition_key(x) for x in transition_keys_raw],
                "representativeEdges": rep_edges[:3],
                "memoTriggers": memo_triggers[:3],
                "dominantTimeBuckets": list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or []),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "notes": list(item.get("notes") or []),
            }
        )
    out.sort(key=lambda x: (_coerce_int(x.get("size"), 0), _coerce_float(x.get("score"), 0.0)), reverse=True)
    return out[:5]


def _extract_deep_control_model_payload(analysis_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = analysis_payload if isinstance(analysis_payload, dict) else {}
    deep_model = payload.get("deep_control_model") if isinstance(payload.get("deep_control_model"), dict) else {}
    return deep_model if deep_model else payload


def _quote_phrase_sample(value: Any) -> str:
    s = str(value or "").strip().strip("「」『』\"'")
    if not s:
        return ""
    return f"「{s}」"



def _daily_deep_v2_reader_comment(
    theme_hints: List[str],
    *,
    overview_route: str,
    recovery_route: str,
) -> str:
    hints = set(str(x or "").strip() for x in list(theme_hints or []) if str(x or "").strip())
    if "self_pressure" in hints:
        if recovery_route:
            return f"昨日のあなたは、自分を支えるために強い言葉を内側へ向けながらも、{recovery_route}へ戻ろうとする動きも持っていたようです。"
        return "昨日のあなたは、自分を支えるために強い言葉を内側へ向けるほど、気持ちも張りつめやすかったようです。"
    if "interpersonal_caution" in hints:
        if recovery_route:
            return f"昨日のあなたは、人との距離を丁寧に考えるほど緊張も抱えやすく、そのあとで{recovery_route}へ戻ろうとする流れも見えていました。"
        return "昨日のあなたは、人との距離を丁寧に考えるほど、内側では緊張を抱えやすかったようです。"
    if "fatigue_limit" in hints:
        if recovery_route:
            return f"昨日のあなたは、しんどさに気づいたあとで、{recovery_route}へ静かに戻ろうとしていたように見えます。"
        return "昨日のあなたは、しんどさを押し込めるより、限界に気づきながら静かな方へ戻ろうとしていたように見えます。"
    if "self_doubt" in hints:
        if recovery_route:
            return f"昨日のあなたは、うまくできていない感覚に引っぱられながらも、{recovery_route}へ整え直そうとしていたようです。"
        return "昨日のあなたは、うまくできていない感覚に引っぱられながらも、整え直す流れを探していたようです。"
    if recovery_route:
        return f"昨日のあなたは、揺れたままで終わるのではなく、{recovery_route}へ戻ろうとする整え直し方も持っていたようです。"
    if overview_route:
        return f"昨日のあなたは、{overview_route}に動きやすい場面があり、その切り替わりが一日の手がかりになっていたようです。"
    return "昨日のあなたは、ただ揺れていたというより、その時々で自分を支えようとする言葉を内側に向けていたように見えます。"



def _build_daily_deep_v2_summary(
    *,
    memo_themes: List[Dict[str, Any]],
    memo_triggers: List[Dict[str, Any]],
    transition_edges: List[Dict[str, Any]],
    recovery_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    working_themes = list(memo_themes or [])
    if not working_themes:
        fallback_themes: List[Dict[str, Any]] = []
        for idx, memo in enumerate(list(memo_triggers or [])[:2], start=1):
            keyword = str(memo.get("keyword") or "").strip()
            phrase_samples = [str(x).strip() for x in list(memo.get("phraseSamples") or []) if str(x).strip()]
            if not phrase_samples and keyword:
                phrase_samples = [keyword]
            fallback_themes.append(
                {
                    "themeId": f"memo_trigger_{idx}",
                    "themeHint": str(memo.get("themeHint") or "generic").strip() or "generic",
                    "themeLabel": DEEP_THEME_HINT_LABELS.get(
                        str(memo.get("themeHint") or "generic").strip() or "generic",
                        DEEP_THEME_HINT_LABELS["generic"],
                    ),
                    "keywords": [keyword] if keyword else [],
                    "phraseSamples": phrase_samples[:2],
                    "linkedRouteLabels": list(memo.get("relatedTransitions") or [])[:2],
                    "dominantTimeBuckets": list(memo.get("dominantTimeBuckets") or [])[:2],
                    "count": _coerce_int(memo.get("count"), 0),
                    "meaningComment": DEEP_THEME_HINT_MEANING_COMMENTS.get(
                        str(memo.get("themeHint") or "generic").strip() or "generic",
                        DEEP_THEME_HINT_MEANING_COMMENTS["generic"],
                    ),
                }
            )
        working_themes = fallback_themes

    theme_items: List[Dict[str, Any]] = []
    for theme in list(working_themes or [])[:2]:
        theme_id = str(theme.get("themeId") or theme.get("theme_id") or theme.get("themeLabel") or "theme").strip()
        theme_hint = str(theme.get("themeHint") or theme.get("theme_hint") or "generic").strip() or "generic"
        theme_label = str(
            theme.get("themeLabel")
            or theme.get("theme_label")
            or DEEP_THEME_HINT_LABELS.get(theme_hint, DEEP_THEME_HINT_LABELS["generic"])
        )
        phrase_samples = [
            str(x).strip()
            for x in list(theme.get("phraseSamples") or theme.get("phrase_samples") or [])
            if str(x).strip()
        ][:2]
        lead_seed = phrase_samples[0] if phrase_samples else (
            list(theme.get("keywords") or [theme_label])[0] if list(theme.get("keywords") or []) else theme_label
        )
        linked_route_labels = [
            str(x).strip()
            for x in list(theme.get("linkedRouteLabels") or theme.get("linked_route_labels") or [])
            if str(x).strip()
        ][:2]
        theme_items.append(
            {
                "themeId": theme_id,
                "themeLead": f"{_quote_phrase_sample(lead_seed) or theme_label}が前に出る場面",
                "themeLabel": theme_label,
                "phraseSamples": phrase_samples,
                "meaningComment": str(
                    theme.get("meaningComment")
                    or theme.get("meaning_comment")
                    or DEEP_THEME_HINT_MEANING_COMMENTS.get(theme_hint, DEEP_THEME_HINT_MEANING_COMMENTS["generic"])
                ).strip(),
                "linkedRouteLabels": linked_route_labels,
                "dominantTimeBuckets": list(theme.get("dominantTimeBuckets") or theme.get("dominant_time_buckets") or [])[:2],
                "count": _coerce_int(theme.get("count"), 0),
                "themeHint": theme_hint,
            }
        )

    top_theme = theme_items[0] if theme_items else {}
    overview_phrases = [str(x).strip() for x in list(top_theme.get("phraseSamples") or []) if str(x).strip()][:2]
    overview_phrase_text = "、".join([_quote_phrase_sample(x) for x in overview_phrases])
    overview_route = str((list(top_theme.get("linkedRouteLabels") or [])[:1] or [""])[0] or "").strip()
    if not overview_route:
        overview_route = str((transition_edges[0] or {}).get("routeLabel") or "").strip() if transition_edges else ""
    recovery_route = str((recovery_rows[0] or {}).get("routeLabel") or "").strip() if recovery_rows else ""

    if overview_phrase_text and overview_route:
        overview_comment = f"昨日は、{overview_phrase_text}のような言葉が前に出る場面で、{overview_route}に動きやすい流れが見えていました。"
    elif overview_phrase_text and recovery_route:
        overview_comment = f"昨日は、{overview_phrase_text}のような言葉が出たあとで、{recovery_route}へ戻ろうとする流れも見えていました。"
    elif overview_phrase_text:
        overview_comment = f"昨日は、{overview_phrase_text}のような言葉が前に出る場面が残っていました。"
    elif overview_route:
        overview_comment = f"昨日は、{overview_route}に動きやすい流れが見えていました。"
    elif recovery_route:
        overview_comment = f"昨日は、{recovery_route}へ戻る整え直しの流れが見えていました。"
    else:
        overview_comment = "昨日は深いところの流れを言い切るには、材料がまだ少なめでした。"

    movement_items: List[str] = []
    for theme in theme_items[:2]:
        phrase = str((list(theme.get("phraseSamples") or [])[:1] or [""])[0] or "").strip()
        route = str((list(theme.get("linkedRouteLabels") or [])[:1] or [""])[0] or "").strip()
        if phrase and route:
            movement_items.append(f"{_quote_phrase_sample(phrase)}が出た場面で、{route}に動きやすい流れがありました。")
        elif route:
            movement_items.append(f"{route}に動きやすい流れが見えていました。")
    if recovery_route:
        movement_items.append(f"そのあとで、{recovery_route}へ戻る動きも見えていました。")
    if not movement_items and overview_route:
        movement_items.append(f"{overview_route}に向かう切り替わりが、昨日の手がかりとして見えていました。")
    deduped_movement: List[str] = []
    seen_movement = set()
    for text in movement_items:
        s = str(text or "").strip()
        if not s or s in seen_movement:
            continue
        seen_movement.add(s)
        deduped_movement.append(s)
    movement_items = deduped_movement[:3]

    reader_comment = _daily_deep_v2_reader_comment(
        [str(item.get("themeHint") or "generic") for item in theme_items],
        overview_route=overview_route,
        recovery_route=recovery_route,
    )
    summary = {
        "overviewComment": overview_comment,
        "themeItems": [
            {
                key: value
                for key, value in item.items()
                if key != "themeHint"
            }
            for item in theme_items
        ],
        "movementItems": movement_items,
        "readerComment": reader_comment,
    }
    summary["structuralComment"] = summary["overviewComment"]
    summary["gentleComment"] = summary["readerComment"]
    evidence_items = [{"text": x} for x in summary["movementItems"][:2]]
    if overview_route:
        evidence_items.append({"text": f"{overview_route} が昨日の流れの手がかりとして見えていました。"})
    summary["evidence"] = {"items": evidence_items[:3]}
    summary["nextPoints"] = []
    summary["source"] = DEEP_SUMMARY_SOURCE_DAILY_V2
    return summary



def _render_daily_deep_v2_text(
    *,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    summary: Dict[str, Any],
) -> str:
    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.append("")

    lines.append("【昨日、見えていたこと】")
    lines.append(
        str((summary or {}).get("overviewComment") or "").strip()
        or "昨日は深いところの流れを言い切るには、材料がまだ少なめでした。"
    )
    lines.append("")

    theme_items = list((summary or {}).get("themeItems") or [])
    if theme_items:
        lines.append("【あなたの言葉から見えていたテーマ】")
        for theme in theme_items[:2]:
            if not isinstance(theme, dict):
                continue
            phrases = [
                _quote_phrase_sample(x)
                for x in list(theme.get("phraseSamples") or [])[:2]
                if str(x or "").strip()
            ]
            if phrases:
                lines.append(f"- {' / '.join(phrases)}")
            label = str(theme.get("themeLabel") or "").strip()
            meaning = str(theme.get("meaningComment") or "").strip()
            linked_routes = [
                str(x).strip()
                for x in list(theme.get("linkedRouteLabels") or [])[:2]
                if str(x).strip()
            ]
            if label and meaning:
                lines.append(f"  {label}: {meaning}")
            elif meaning:
                lines.append(f"  {meaning}")
            if linked_routes:
                lines.append(f"  つながりやすかった流れ: {' / '.join(linked_routes)}")
        lines.append("")

    movement_items = [str(x).strip() for x in list((summary or {}).get("movementItems") or []) if str(x).strip()]
    if movement_items:
        lines.append("【言葉と気持ちがつながった流れ】")
        for item in movement_items[:3]:
            lines.append(f"- {item}")
        lines.append("")

    reader_comment = str((summary or {}).get("readerComment") or "").strip()
    if reader_comment:
        lines.append("【あなたへのコメント】")
        lines.append(reader_comment)
        lines.append("")

    lines.append("【このレポートについて】")
    lines.extend(_common_observation_note_lines())
    return "\n".join(lines).strip()

def _weekly_deep_v2_pattern_label(theme_hints: List[str], recovery_route_label: str) -> str:
    hints = set(str(x or "").strip() for x in list(theme_hints or []) if str(x or "").strip())
    if "self_pressure" in hints:
        return "抱え込みから張りつめる流れ"
    if "fatigue_limit" in hints:
        return "疲れから静けさへ戻る流れ"
    if "interpersonal_caution" in hints:
        return "気をつかい続けて張りつめる流れ"
    if "self_doubt" in hints:
        return "自分を責めて沈みやすい流れ"
    if recovery_route_label:
        return "整え直しが見えていた流れ"
    return "今週、くり返しやすかった流れ"


def _weekly_deep_v2_pattern_comment(route_labels: List[str], recovery_route_label: str) -> str:
    routes = [str(x).strip() for x in list(route_labels or []) if str(x).strip()]
    first_route = routes[0] if routes else "この流れ"
    if recovery_route_label:
        return f"{first_route} に動いたあとも、{recovery_route_label} へ戻る道が見えていました。"
    if len(routes) >= 2:
        return f"{routes[0]} を入り口にして、{routes[1]} へつながる流れが今週の中で重なっていました。"
    return f"{first_route} を中心に、同じ流れが今週の中で何度か重なっていました。"


def _weekly_deep_v2_reader_comment(theme_hints: List[str]) -> str:
    hints = set(str(x or "").strip() for x in list(theme_hints or []) if str(x or "").strip())
    if "self_pressure" in hints:
        return "今週のあなたは、ただ揺れていたというより、自分を支えるために強い言葉を何度も内側へ向けていたように見えます。"
    if "interpersonal_caution" in hints:
        return "今週のあなたは、人との距離を丁寧に考えるほど、内側では緊張を抱えやすかったようです。"
    if "fatigue_limit" in hints:
        return "今週のあなたは、しんどさを押し込めるより、限界に気づきながら整え直そうとしていたように見えます。"
    if "self_doubt" in hints:
        return "今週のあなたは、うまくできていない感覚に引っぱられながらも、整え直す流れを探していたように見えます。"
    return "今週のあなたは、ただ揺れていたというより、その時々で自分を支えようとする言葉を内側に向けていたように見えます。"


def _build_weekly_deep_v2_summary(
    *,
    memo_themes: List[Dict[str, Any]],
    pattern_episodes: List[Dict[str, Any]],
    memo_triggers: List[Dict[str, Any]],
    transition_edges: List[Dict[str, Any]],
    recovery_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    working_themes = list(memo_themes or [])
    if not working_themes:
        fallback_themes: List[Dict[str, Any]] = []
        for idx, memo in enumerate(list(memo_triggers or [])[:2], start=1):
            keyword = str(memo.get("keyword") or "").strip()
            phrase_samples = [str(x).strip() for x in list(memo.get("phraseSamples") or []) if str(x).strip()]
            if not phrase_samples and keyword:
                phrase_samples = [keyword]
            fallback_themes.append(
                {
                    "themeId": f"memo_trigger_{idx}",
                    "themeHint": str(memo.get("themeHint") or "generic").strip() or "generic",
                    "themeLabel": DEEP_THEME_HINT_LABELS.get(str(memo.get("themeHint") or "generic").strip() or "generic", DEEP_THEME_HINT_LABELS["generic"]),
                    "keywords": [keyword] if keyword else [],
                    "phraseSamples": phrase_samples[:2],
                    "linkedRouteLabels": list(memo.get("relatedTransitions") or [])[:2],
                    "dominantTimeBuckets": list(memo.get("dominantTimeBuckets") or [])[:2],
                    "count": _coerce_int(memo.get("count"), 0),
                    "meaningComment": DEEP_THEME_HINT_MEANING_COMMENTS.get(str(memo.get("themeHint") or "generic").strip() or "generic", DEEP_THEME_HINT_MEANING_COMMENTS["generic"]),
                }
            )
        working_themes = fallback_themes

    theme_items: List[Dict[str, Any]] = []
    for theme in list(working_themes or [])[:2]:
        theme_id = str(theme.get("themeId") or theme.get("theme_id") or theme.get("themeLabel") or "theme").strip()
        theme_hint = str(theme.get("themeHint") or theme.get("theme_hint") or "generic").strip() or "generic"
        theme_label = str(theme.get("themeLabel") or theme.get("theme_label") or DEEP_THEME_HINT_LABELS.get(theme_hint, DEEP_THEME_HINT_LABELS["generic"]))
        phrase_samples = [str(x).strip() for x in list(theme.get("phraseSamples") or theme.get("phrase_samples") or []) if str(x).strip()][:2]
        lead_seed = phrase_samples[0] if phrase_samples else (list(theme.get("keywords") or [theme_label])[0] if list(theme.get("keywords") or []) else theme_label)
        linked_route_labels = [str(x).strip() for x in list(theme.get("linkedRouteLabels") or theme.get("linked_route_labels") or []) if str(x).strip()][:2]
        theme_items.append(
            {
                "themeId": theme_id,
                "themeLead": f"{_quote_phrase_sample(lead_seed) or theme_label}が前に出る場面",
                "themeLabel": theme_label,
                "phraseSamples": phrase_samples,
                "meaningComment": str(theme.get("meaningComment") or theme.get("meaning_comment") or DEEP_THEME_HINT_MEANING_COMMENTS.get(theme_hint, DEEP_THEME_HINT_MEANING_COMMENTS["generic"])).strip(),
                "linkedRouteLabels": linked_route_labels,
                "dominantTimeBuckets": list(theme.get("dominantTimeBuckets") or theme.get("dominant_time_buckets") or [])[:2],
                "count": _coerce_int(theme.get("count"), 0),
                "themeHint": theme_hint,
            }
        )

    top_theme = theme_items[0] if theme_items else {}
    overview_phrases = [str(x).strip() for x in list(top_theme.get("phraseSamples") or []) if str(x).strip()][:2]
    overview_phrase_text = "、".join([_quote_phrase_sample(x) for x in overview_phrases])
    overview_route = str((list(top_theme.get("linkedRouteLabels") or [])[:1] or [""])[0] or "").strip()
    if not overview_route:
        overview_route = str((transition_edges[0] or {}).get("routeLabel") or "").strip() if transition_edges else ""
    if overview_phrase_text and overview_route:
        overview_comment = f"今週は、{overview_phrase_text}のような言葉が前に出る場面で、{overview_route}に動く流れが何度か重なっていました。"
    elif overview_phrase_text:
        overview_comment = f"今週は、{overview_phrase_text}のような言葉が前に出る場面が重なっていました。"
    elif overview_route:
        overview_comment = f"今週は、{overview_route}に動く流れが何度か重なっていました。"
    else:
        overview_comment = "今週は深いところの流れを言い切るには、材料がまだ少なめでした。"

    movement_items: List[str] = []
    for theme in theme_items:
        phrase = str((list(theme.get("phraseSamples") or [])[:1] or [""])[0] or "").strip()
        route = str((list(theme.get("linkedRouteLabels") or [])[:1] or [""])[0] or "").strip()
        if phrase and route:
            movement_items.append(f"{_quote_phrase_sample(phrase)}が出た場面で、{route}に動きやすい流れがありました。")
        elif route:
            movement_items.append(f"{route}に動きやすい流れが見えていました。")
    if recovery_rows:
        recovery_route = str((recovery_rows[0] or {}).get("routeLabel") or "").strip()
        if recovery_route:
            movement_items.append(f"{recovery_route}へ戻る流れも見えていました。")
    deduped_movement: List[str] = []
    seen_movement = set()
    for text in movement_items:
        s = str(text or "").strip()
        if not s or s in seen_movement:
            continue
        seen_movement.add(s)
        deduped_movement.append(s)
    movement_items = deduped_movement[:3]

    theme_hint_by_id = {str(item.get("themeId") or ""): str(item.get("themeHint") or "generic") for item in theme_items}
    working_pattern_episodes = list(pattern_episodes or [])
    if not working_pattern_episodes and (theme_items or transition_edges):
        top_edge_route = str((transition_edges[0] or {}).get("routeLabel") or "").strip() if transition_edges else ""
        top_recovery_route = str((recovery_rows[0] or {}).get("routeLabel") or "").strip() if recovery_rows else ""
        working_pattern_episodes = [
            {
                "patternId": "pattern_1",
                "linkedThemeIds": [str((theme_items[0] or {}).get("themeId") or "")] if theme_items else [],
                "routeLabels": [top_edge_route] if top_edge_route else [],
                "recoveryRouteLabel": top_recovery_route,
                "count": _coerce_int((transition_edges[0] or {}).get("count"), 0) if transition_edges else 0,
            }
        ]

    pattern_items: List[Dict[str, Any]] = []
    for episode in list(working_pattern_episodes or [])[:2]:
        linked_theme_ids = [str(x).strip() for x in list(episode.get("linkedThemeIds") or episode.get("linked_theme_ids") or []) if str(x).strip()]
        theme_hints = [theme_hint_by_id.get(theme_id, "generic") for theme_id in linked_theme_ids if theme_id]
        route_labels = [str(x).strip() for x in list(episode.get("routeLabels") or episode.get("route_labels") or []) if str(x).strip()][:2]
        recovery_route_label = str(episode.get("recoveryRouteLabel") or episode.get("recovery_route_label") or "").strip()
        pattern_label = str(episode.get("patternLabel") or episode.get("pattern_label") or _weekly_deep_v2_pattern_label(theme_hints, recovery_route_label)).strip()
        pattern_comment = str(episode.get("patternComment") or episode.get("pattern_comment") or _weekly_deep_v2_pattern_comment(route_labels, recovery_route_label)).strip()
        pattern_items.append(
            {
                "patternId": str(episode.get("patternId") or episode.get("pattern_id") or "pattern").strip() or "pattern",
                "patternLabel": pattern_label,
                "linkedThemeIds": linked_theme_ids,
                "routeLabels": route_labels,
                "recoveryRouteLabel": recovery_route_label,
                "patternComment": pattern_comment,
                "count": _coerce_int(episode.get("count"), 0),
            }
        )

    reader_comment = _weekly_deep_v2_reader_comment([str(item.get("themeHint") or "generic") for item in theme_items])
    summary = {
        "overviewComment": overview_comment,
        "themeItems": [
            {
                key: value
                for key, value in item.items()
                if key != "themeHint"
            }
            for item in theme_items
        ],
        "movementItems": movement_items,
        "patternItems": pattern_items,
        "readerComment": reader_comment,
    }
    summary["structuralComment"] = summary["overviewComment"]
    summary["gentleComment"] = summary["readerComment"]
    summary["evidence"] = {"items": [{"text": x} for x in summary["movementItems"][:3]]}
    summary["nextPoints"] = []
    summary["source"] = DEEP_SUMMARY_SOURCE_WEEKLY_V2
    return summary


def _render_weekly_deep_v2_text(
    *,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    summary: Dict[str, Any],
) -> str:
    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.append("")

    lines.append("【今週、見えていたこと】")
    lines.append(str((summary or {}).get("overviewComment") or "今週は深いところの流れを言い切るには、材料がまだ少なめでした。"))
    lines.append("")

    theme_items = list((summary or {}).get("themeItems") or [])
    if theme_items:
        lines.append("【あなたの言葉から見えていたテーマ】")
        for theme in theme_items[:2]:
            if not isinstance(theme, dict):
                continue
            phrases = [_quote_phrase_sample(x) for x in list(theme.get("phraseSamples") or [])[:2] if str(x or "").strip()]
            if phrases:
                lines.append(f"- {' / '.join(phrases)}")
            label = str(theme.get("themeLabel") or "").strip()
            meaning = str(theme.get("meaningComment") or "").strip()
            if label and meaning:
                lines.append(f"  {label}: {meaning}")
            elif meaning:
                lines.append(f"  {meaning}")
        lines.append("")

    movement_items = [str(x).strip() for x in list((summary or {}).get("movementItems") or []) if str(x).strip()]
    if movement_items:
        lines.append("【言葉と気持ちがつながった流れ】")
        for item in movement_items[:3]:
            lines.append(f"- {item}")
        lines.append("")

    pattern_items = list((summary or {}).get("patternItems") or [])
    if pattern_items:
        lines.append("【今週、くり返しやすかったパターン】")
        for idx, pattern in enumerate(pattern_items[:2]):
            if not isinstance(pattern, dict):
                continue
            label = str(pattern.get("patternLabel") or "").strip()
            comment = str(pattern.get("patternComment") or "").strip()
            if label:
                lines.append(f"- {label}")
            if comment:
                lines.append(f"  {comment}")
            if idx != min(len(pattern_items), 2) - 1:
                lines.append("")
        lines.append("")

    reader_comment = str((summary or {}).get("readerComment") or "").strip()
    if reader_comment:
        lines.append("【あなたへのコメント】")
        lines.append(reader_comment)
        lines.append("")

    lines.append("【このレポートについて】")
    lines.extend(_common_observation_note_lines())
    return "\n".join(lines).strip()




def _monthly_deep_v2_pattern_comment(route_labels: List[str], recovery_route_label: str) -> str:
    routes = [str(x).strip() for x in list(route_labels or []) if str(x).strip()]
    first_route = routes[0] if routes else "この流れ"
    if recovery_route_label:
        return f"{first_route} が前に出たあとも、{recovery_route_label} へ戻る道が見えていました。"
    if len(routes) >= 2:
        return f"{routes[0]} を入り口にして、{routes[1]} へつながる流れが今月の中で重なっていました。"
    return f"{first_route} を中心に、同じ流れが今月の中で何度か重なっていました。"



def _monthly_deep_v2_phase_comment(phase: Dict[str, Any]) -> str:
    explicit = str(phase.get("phaseComment") or "").strip()
    if explicit:
        return explicit

    phase_label = str(phase.get("phaseLabel") or "この時期").strip() or "この時期"
    phrase = str((list(phase.get("phraseSamples") or [])[:1] or [""])[0] or "").strip()
    theme_label = str((list(phase.get("themeLabels") or [])[:1] or [""])[0] or "").strip()
    lead = _quote_phrase_sample(phrase) if phrase else theme_label
    route = str((list(phase.get("routeLabels") or [])[:1] or [""])[0] or "").strip()
    recovery = str(phase.get("recoveryRouteLabel") or "").strip()
    time_label = str((list(phase.get("dominantTimeBucketLabels") or [])[:1] or [""])[0] or "").strip()

    if lead and route:
        text = f"{phase_label}は、{lead}が前に出る場面で、{route}に動きやすい流れでした。"
    elif route:
        text = f"{phase_label}は、{route}が目立つ流れでした。"
    elif lead:
        text = f"{phase_label}は、{lead}が前に出やすい時期でした。"
    else:
        text = f"{phase_label}は、この時期らしい流れが見えていました。"

    if recovery:
        if route and recovery != route:
            text += f" そのあとも、{recovery}へ戻る道が見えていました。"
        else:
            text += f" {recovery}へ戻る整え直しも見えていました。"

    if time_label:
        text += f" とくに{time_label}に出やすい傾向でした。"

    return text



def _monthly_deep_v2_shift_label(shift: Dict[str, Any]) -> str:
    explicit = str(shift.get("shiftLabel") or "").strip()
    if explicit:
        return explicit

    direction = str(shift.get("directionHint") or "mixed").strip() or "mixed"
    settling_route = str((list(shift.get("settlingRouteLabels") or [])[:1] or [""])[0] or "").strip()
    emerging_route = str((list(shift.get("emergingRouteLabels") or [])[:1] or [""])[0] or "").strip()

    if direction == "recovery_shift":
        return "後半は静かに戻る流れ"
    if direction == "tension_shift":
        return "後半は張りつめる流れ"
    if settling_route and emerging_route:
        return f"{settling_route}から{emerging_route}への変化"
    return "前半と後半で動き方が変化"



def _monthly_deep_v2_shift_comment(shift: Dict[str, Any]) -> str:
    explicit = str(shift.get("shiftComment") or "").strip()
    if explicit:
        return explicit

    from_phase = str(shift.get("fromPhaseLabel") or "前半").strip() or "前半"
    to_phase = str(shift.get("toPhaseLabel") or "後半").strip() or "後半"

    settling = str((list(shift.get("settlingRouteLabels") or [])[:1] or [""])[0] or "").strip()
    if not settling:
        settling = str((list(shift.get("settlingThemeLabels") or [])[:1] or [""])[0] or "").strip()

    emerging = str((list(shift.get("emergingRouteLabels") or [])[:1] or [""])[0] or "").strip()
    if not emerging:
        emerging = str((list(shift.get("emergingThemeLabels") or [])[:1] or [""])[0] or "").strip()

    from_recovery = str(shift.get("fromRecoveryRouteLabel") or "").strip()
    to_recovery = str(shift.get("toRecoveryRouteLabel") or "").strip()

    if settling and emerging:
        text = f"{from_phase}は{settling}が目立っていましたが、{to_phase}は{emerging}が前に出ていました。"
    elif emerging:
        text = f"{to_phase}に入ってから、{emerging}が増えていました。"
    elif settling:
        text = f"{from_phase}で目立っていた{settling}は、{to_phase}では少し静かになっていました。"
    else:
        text = f"{from_phase}と{to_phase}で、目立つ流れが少し入れ替わっていました。"

    if from_recovery and to_recovery and from_recovery != to_recovery:
        text += f" 整え直し方も、{from_recovery}から{to_recovery}へ少し移っていました。"
    elif to_recovery:
        text += f" {to_phase}では、{to_recovery}へ戻る流れが見えやすくなっていました。"

    return text



def _monthly_deep_v2_reader_comment(*, theme_hints: List[str], monthly_shifts: List[Dict[str, Any]]) -> str:
    top_shift = monthly_shifts[0] if monthly_shifts else {}
    direction = str((top_shift or {}).get("directionHint") or "").strip()
    if direction == "recovery_shift":
        return "今月のあなたは、張りつめ続けるよりも、後半にかけて少し静かに戻る方向を探していたように見えます。"
    if direction == "tension_shift":
        return "今月のあなたは、後半にかけて気持ちを守ろうとする反応が強まりやすかったように見えます。"

    hints = set(str(x or "").strip() for x in list(theme_hints or []) if str(x or "").strip())
    if "self_pressure" in hints:
        return "今月のあなたは、自分を支えるために強い言葉を何度も内側へ向けていたように見えます。"
    if "interpersonal_caution" in hints:
        return "今月のあなたは、人との距離を丁寧に考えるほど、内側では緊張を抱えやすかったようです。"
    if "fatigue_limit" in hints:
        return "今月のあなたは、しんどさに気づきながら、静かに整え直す方向も探していたように見えます。"
    if "self_doubt" in hints:
        return "今月のあなたは、自分を責める感覚に引っぱられながらも、整え直す流れを探していたように見えます。"
    return "今月のあなたは、ただ揺れていたというより、その時々で自分を支えようとする言葉を内側に向けていたように見えます。"



def _build_monthly_deep_v2_summary(
    *,
    memo_themes: List[Dict[str, Any]],
    pattern_episodes: List[Dict[str, Any]],
    memo_triggers: List[Dict[str, Any]],
    transition_edges: List[Dict[str, Any]],
    recovery_rows: List[Dict[str, Any]],
    monthly_phases: List[Dict[str, Any]],
    monthly_shifts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    working_themes = list(memo_themes or [])
    if not working_themes:
        fallback_themes: List[Dict[str, Any]] = []
        for idx, memo in enumerate(list(memo_triggers or [])[:2], start=1):
            keyword = str(memo.get("keyword") or "").strip()
            phrase_samples = [str(x).strip() for x in list(memo.get("phraseSamples") or []) if str(x).strip()]
            if not phrase_samples and keyword:
                phrase_samples = [keyword]
            fallback_themes.append(
                {
                    "themeId": f"theme_{idx}",
                    "themeHint": str(memo.get("themeHint") or "generic").strip() or "generic",
                    "themeLabel": DEEP_THEME_HINT_LABELS.get(str(memo.get("themeHint") or "generic").strip() or "generic", DEEP_THEME_HINT_LABELS["generic"]),
                    "keywords": [keyword] if keyword else [],
                    "phraseSamples": phrase_samples[:2],
                    "linkedRouteLabels": list(memo.get("relatedTransitions") or [])[:2],
                    "dominantTimeBuckets": list(memo.get("dominantTimeBuckets") or [])[:2],
                    "count": _coerce_int(memo.get("count"), 0),
                    "meaningComment": DEEP_THEME_HINT_MEANING_COMMENTS.get(str(memo.get("themeHint") or "generic").strip() or "generic", DEEP_THEME_HINT_MEANING_COMMENTS["generic"]),
                }
            )
        working_themes = fallback_themes

    theme_items: List[Dict[str, Any]] = []
    for theme in list(working_themes or [])[:2]:
        theme_id = str(theme.get("themeId") or theme.get("theme_id") or theme.get("themeLabel") or "theme").strip()
        theme_hint = str(theme.get("themeHint") or theme.get("theme_hint") or "generic").strip() or "generic"
        theme_label = str(theme.get("themeLabel") or theme.get("theme_label") or DEEP_THEME_HINT_LABELS.get(theme_hint, DEEP_THEME_HINT_LABELS["generic"]))
        phrase_samples = [str(x).strip() for x in list(theme.get("phraseSamples") or theme.get("phrase_samples") or []) if str(x).strip()][:2]
        lead_seed = phrase_samples[0] if phrase_samples else (list(theme.get("keywords") or [theme_label])[0] if list(theme.get("keywords") or []) else theme_label)
        linked_route_labels = [str(x).strip() for x in list(theme.get("linkedRouteLabels") or theme.get("linked_route_labels") or []) if str(x).strip()][:2]
        theme_items.append(
            {
                "themeId": theme_id,
                "themeLead": f"{_quote_phrase_sample(lead_seed) or theme_label}が前に出る場面",
                "themeLabel": theme_label,
                "phraseSamples": phrase_samples,
                "meaningComment": str(theme.get("meaningComment") or theme.get("meaning_comment") or DEEP_THEME_HINT_MEANING_COMMENTS.get(theme_hint, DEEP_THEME_HINT_MEANING_COMMENTS["generic"])).strip(),
                "linkedRouteLabels": linked_route_labels,
                "dominantTimeBuckets": list(theme.get("dominantTimeBuckets") or theme.get("dominant_time_buckets") or [])[:2],
                "count": _coerce_int(theme.get("count"), 0),
                "themeHint": theme_hint,
            }
        )

    top_theme = theme_items[0] if theme_items else {}
    overview_phrases = [str(x).strip() for x in list(top_theme.get("phraseSamples") or []) if str(x).strip()][:2]
    overview_phrase_text = "、".join([_quote_phrase_sample(x) for x in overview_phrases])
    overview_route = str((list(top_theme.get("linkedRouteLabels") or [])[:1] or [""])[0] or "").strip()
    if not overview_route:
        overview_route = str((transition_edges[0] or {}).get("routeLabel") or "").strip() if transition_edges else ""
    if overview_phrase_text and overview_route:
        overview_comment = f"今月は、{overview_phrase_text}のような言葉が前に出る場面で、{overview_route}に動く流れが何度か重なっていました。"
    elif overview_phrase_text:
        overview_comment = f"今月は、{overview_phrase_text}のような言葉が前に出る場面が重なっていました。"
    elif overview_route:
        overview_comment = f"今月は、{overview_route}に動く流れが何度か重なっていました。"
    else:
        overview_comment = "今月は深いところの流れを言い切るには、材料がまだ少なめでした。"

    movement_items: List[str] = []
    for theme in theme_items:
        phrase = str((list(theme.get("phraseSamples") or [])[:1] or [""])[0] or "").strip()
        route = str((list(theme.get("linkedRouteLabels") or [])[:1] or [""])[0] or "").strip()
        if phrase and route:
            movement_items.append(f"{_quote_phrase_sample(phrase)}が出た場面で、{route}に動きやすい流れがありました。")
        elif route:
            movement_items.append(f"{route}に動きやすい流れが見えていました。")
    if recovery_rows:
        recovery_route = str((recovery_rows[0] or {}).get("routeLabel") or "").strip()
        if recovery_route:
            movement_items.append(f"{recovery_route}へ戻る流れも見えていました。")
    deduped_movement: List[str] = []
    seen_movement = set()
    for text in movement_items:
        s = str(text or "").strip()
        if not s or s in seen_movement:
            continue
        seen_movement.add(s)
        deduped_movement.append(s)
    movement_items = deduped_movement[:3]

    theme_hint_by_id = {str(item.get("themeId") or ""): str(item.get("themeHint") or "generic") for item in theme_items}
    working_pattern_episodes = list(pattern_episodes or [])
    if not working_pattern_episodes and (theme_items or transition_edges):
        top_edge_route = str((transition_edges[0] or {}).get("routeLabel") or "").strip() if transition_edges else ""
        top_recovery_route = str((recovery_rows[0] or {}).get("routeLabel") or "").strip() if recovery_rows else ""
        working_pattern_episodes = [
            {
                "patternId": "pattern_1",
                "linkedThemeIds": [str((theme_items[0] or {}).get("themeId") or "")] if theme_items else [],
                "routeLabels": [top_edge_route] if top_edge_route else [],
                "recoveryRouteLabel": top_recovery_route,
                "count": _coerce_int((transition_edges[0] or {}).get("count"), 0) if transition_edges else 0,
            }
        ]

    pattern_items: List[Dict[str, Any]] = []
    for episode in list(working_pattern_episodes or [])[:2]:
        linked_theme_ids = [str(x).strip() for x in list(episode.get("linkedThemeIds") or episode.get("linked_theme_ids") or []) if str(x).strip()]
        theme_hints = [theme_hint_by_id.get(theme_id, "generic") for theme_id in linked_theme_ids if theme_id]
        route_labels = [str(x).strip() for x in list(episode.get("routeLabels") or episode.get("route_labels") or []) if str(x).strip()][:2]
        recovery_route_label = str(episode.get("recoveryRouteLabel") or episode.get("recovery_route_label") or "").strip()
        pattern_label = str(episode.get("patternLabel") or episode.get("pattern_label") or _weekly_deep_v2_pattern_label(theme_hints, recovery_route_label)).strip()
        pattern_comment = str(episode.get("patternComment") or episode.get("pattern_comment") or _monthly_deep_v2_pattern_comment(route_labels, recovery_route_label)).strip()
        pattern_items.append(
            {
                "patternId": str(episode.get("patternId") or episode.get("pattern_id") or "pattern").strip() or "pattern",
                "patternLabel": pattern_label,
                "linkedThemeIds": linked_theme_ids,
                "routeLabels": route_labels,
                "recoveryRouteLabel": recovery_route_label,
                "patternComment": pattern_comment,
                "count": _coerce_int(episode.get("count"), 0),
            }
        )

    phase_items: List[Dict[str, Any]] = []
    for phase in list(monthly_phases or [])[:2]:
        phase_label = str(phase.get("phaseLabel") or "").strip()
        theme_labels = [str(x).strip() for x in list(phase.get("themeLabels") or []) if str(x).strip()][:2]
        phrase_samples = [str(x).strip() for x in list(phase.get("phraseSamples") or []) if str(x).strip()][:2]
        route_labels = [str(x).strip() for x in list(phase.get("routeLabels") or []) if str(x).strip()][:2]
        recovery_route_label = str(phase.get("recoveryRouteLabel") or "").strip()
        time_labels = [str(x).strip() for x in list(phase.get("dominantTimeBucketLabels") or []) if str(x).strip()][:2]
        if not phase_label:
            continue
        if not (theme_labels or phrase_samples or route_labels or recovery_route_label):
            continue
        phase_items.append(
            {
                "phaseId": str(phase.get("phaseId") or "phase").strip() or "phase",
                "phaseLabel": phase_label,
                "phaseFocusLabel": str(phase.get("phaseFocusLabel") or (theme_labels[0] if theme_labels else (route_labels[0] if route_labels else ""))).strip(),
                "themeLabels": theme_labels,
                "phraseSamples": phrase_samples,
                "routeLabels": route_labels,
                "recoveryRouteLabel": recovery_route_label,
                "dominantTimeBucketLabels": time_labels,
                "phaseComment": _monthly_deep_v2_phase_comment(phase),
                "count": _coerce_int(phase.get("count"), _coerce_int(phase.get("entryCount"), 0)),
            }
        )

    shift_items: List[Dict[str, Any]] = []
    for shift in list(monthly_shifts or [])[:1]:
        from_phase_label = str(shift.get("fromPhaseLabel") or "前半").strip() or "前半"
        to_phase_label = str(shift.get("toPhaseLabel") or "後半").strip() or "後半"
        emerging_theme_labels = [str(x).strip() for x in list(shift.get("emergingThemeLabels") or []) if str(x).strip()][:2]
        settling_theme_labels = [str(x).strip() for x in list(shift.get("settlingThemeLabels") or []) if str(x).strip()][:2]
        emerging_route_labels = [str(x).strip() for x in list(shift.get("emergingRouteLabels") or []) if str(x).strip()][:2]
        settling_route_labels = [str(x).strip() for x in list(shift.get("settlingRouteLabels") or []) if str(x).strip()][:2]
        if not (emerging_theme_labels or settling_theme_labels or emerging_route_labels or settling_route_labels or str(shift.get("shiftLabel") or "").strip() or str(shift.get("shiftComment") or "").strip()):
            continue
        shift_items.append(
            {
                "shiftId": str(shift.get("shiftId") or f"{from_phase_label}_to_{to_phase_label}").strip(),
                "fromPhaseLabel": from_phase_label,
                "toPhaseLabel": to_phase_label,
                "shiftLabel": _monthly_deep_v2_shift_label(shift),
                "shiftComment": _monthly_deep_v2_shift_comment(shift),
                "emergingThemeLabels": emerging_theme_labels,
                "settlingThemeLabels": settling_theme_labels,
                "emergingRouteLabels": emerging_route_labels,
                "settlingRouteLabels": settling_route_labels,
                "fromRecoveryRouteLabel": str(shift.get("fromRecoveryRouteLabel") or "").strip(),
                "toRecoveryRouteLabel": str(shift.get("toRecoveryRouteLabel") or "").strip(),
                "directionHint": str(shift.get("directionHint") or "mixed").strip() or "mixed",
            }
        )

    reader_comment = _monthly_deep_v2_reader_comment(
        theme_hints=[str(item.get("themeHint") or "generic") for item in theme_items],
        monthly_shifts=monthly_shifts,
    )
    summary = {
        "overviewComment": overview_comment,
        "themeItems": [{key: value for key, value in item.items() if key != "themeHint"} for item in theme_items],
        "movementItems": movement_items,
        "patternItems": pattern_items,
        "phaseItems": phase_items,
        "shiftItems": shift_items,
        "readerComment": reader_comment,
    }
    summary["structuralComment"] = summary["overviewComment"]
    summary["gentleComment"] = summary["readerComment"]
    evidence_items = [{"text": x} for x in summary["movementItems"][:2]]
    if shift_items and str((shift_items[0] or {}).get("shiftLabel") or "").strip():
        evidence_items.append({"text": str((shift_items[0] or {}).get("shiftLabel") or "").strip()})
    summary["evidence"] = {"items": evidence_items}
    summary["nextPoints"] = []
    summary["source"] = DEEP_SUMMARY_SOURCE_MONTHLY_V2
    return summary



def _monthly_deep_v2_phase_section_title(
    phase_items: List[Dict[str, Any]],
    shift_items: List[Dict[str, Any]],
) -> str:
    if len(list(phase_items or [])) >= 2 or list(shift_items or []):
        return "【前半と後半で変わっていたこと】"
    return "【今月の中で見えていた流れ】"



def _render_monthly_deep_v2_phase_lines(phase: Dict[str, Any]) -> List[str]:
    phase_label = str(phase.get("phaseLabel") or "この時期").strip() or "この時期"
    focus_label = str(phase.get("phaseFocusLabel") or "").strip()
    header = f"{phase_label}: {focus_label}" if focus_label else phase_label
    comment = str(phase.get("phaseComment") or "").strip() or _monthly_deep_v2_phase_comment(phase)

    lines: List[str] = [f"- {header}"]
    if comment:
        lines.append(f"  {comment}")
    return lines



def _render_monthly_deep_v2_shift_lines(shift: Dict[str, Any]) -> List[str]:
    label = str(shift.get("shiftLabel") or "").strip()
    comment = str(shift.get("shiftComment") or "").strip()

    if not label and not comment:
        label = "月の前半と後半で、流れの重心が少し切り替わっていました。"

    lines: List[str] = []
    if label:
        lines.append(f"- 変化: {label}")
    else:
        lines.append("- 変化")

    if comment and comment != label:
        lines.append(f"  {comment}")

    return lines



def _render_monthly_deep_v2_text(
    *,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    summary: Dict[str, Any],
) -> str:
    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.append("")

    lines.append("【今月、見えていたこと】")
    lines.append(
        str((summary or {}).get("overviewComment") or "").strip()
        or "今月は深いところの流れを言い切るには、材料がまだ少なめでした。"
    )
    lines.append("")

    theme_items = list((summary or {}).get("themeItems") or [])
    if theme_items:
        lines.append("【あなたの言葉から見えていたテーマ】")
        for theme in theme_items[:2]:
            if not isinstance(theme, dict):
                continue
            phrases = [_quote_phrase_sample(x) for x in list(theme.get("phraseSamples") or [])[:2] if str(x or "").strip()]
            if phrases:
                lines.append(f"- {' / '.join(phrases)}")
            label = str(theme.get("themeLabel") or "").strip()
            meaning = str(theme.get("meaningComment") or "").strip()
            linked_routes = [str(x).strip() for x in list(theme.get("linkedRouteLabels") or [])[:2] if str(x).strip()]
            if label and meaning:
                lines.append(f"  {label}: {meaning}")
            elif meaning:
                lines.append(f"  {meaning}")
            if linked_routes:
                lines.append(f"  つながりやすかった流れ: {' / '.join(linked_routes)}")
        lines.append("")

    movement_items = [str(x).strip() for x in list((summary or {}).get("movementItems") or []) if str(x).strip()]
    if movement_items:
        lines.append("【言葉と気持ちがつながった流れ】")
        for item in movement_items[:3]:
            lines.append(f"- {item}")
        lines.append("")

    pattern_items = list((summary or {}).get("patternItems") or [])
    if pattern_items:
        lines.append("【今月、くり返しやすかったパターン】")
        for idx, pattern in enumerate(pattern_items[:2]):
            if not isinstance(pattern, dict):
                continue
            label = str(pattern.get("patternLabel") or "").strip()
            comment = str(pattern.get("patternComment") or "").strip()
            if label:
                lines.append(f"- {label}")
            if comment:
                lines.append(f"  {comment}")
            if idx != min(len(pattern_items), 2) - 1:
                lines.append("")
        lines.append("")

    phase_items = list((summary or {}).get("phaseItems") or [])
    shift_items = list((summary or {}).get("shiftItems") or [])
    if phase_items or shift_items:
        lines.append(_monthly_deep_v2_phase_section_title(phase_items, shift_items))
        for phase in phase_items[:2]:
            if not isinstance(phase, dict):
                continue
            lines.extend(_render_monthly_deep_v2_phase_lines(phase))
        if shift_items:
            if phase_items:
                lines.append("")
            first_shift = shift_items[0] if isinstance(shift_items[0], dict) else {}
            lines.extend(_render_monthly_deep_v2_shift_lines(first_shift))
        lines.append("")

    reader_comment = str((summary or {}).get("readerComment") or "").strip()
    if reader_comment:
        lines.append("【あなたへのコメント】")
        lines.append(reader_comment)
        lines.append("")

    lines.append("【このレポートについて】")
    lines.extend(_common_observation_note_lines())
    return "\n".join(lines).strip()




def _build_structural_summary_object(
    *,
    report_type: str,
    deep_payload: Dict[str, Any],
) -> Dict[str, Any]:
    payload = deep_payload if isinstance(deep_payload, dict) else {}
    deep_model = _extract_deep_control_model_payload(payload)
    transition_edges = _normalize_transition_edges(
        deep_model.get("transition_edges") or deep_model.get("transitionEdges") or []
    )
    patterns = _normalize_control_patterns(deep_model.get("control_patterns") or deep_model.get("controlPatterns") or [])
    recovery_rows = _normalize_recovery_time_rows(deep_model.get("recovery_time") or deep_model.get("recoveryTime") or [])
    memo_triggers = _normalize_memo_triggers(deep_model.get("memo_triggers") or deep_model.get("memoTriggers") or [])
    memo_themes = _normalize_memo_themes(deep_model.get("memo_themes") or deep_model.get("memoThemes") or [])
    pattern_episodes = _normalize_pattern_episodes(deep_model.get("pattern_episodes") or deep_model.get("patternEpisodes") or [])
    monthly_phases = _normalize_monthly_phases(
        deep_model.get("monthly_phases")
        or deep_model.get("monthlyPhases")
        or payload.get("monthlyPhases")
        or payload.get("monthly_phases")
        or []
    )
    monthly_shifts = _normalize_monthly_shifts(
        deep_model.get("monthly_shifts")
        or deep_model.get("monthlyShifts")
        or payload.get("monthlyShifts")
        or payload.get("monthly_shifts")
        or []
    )
    summary_raw = deep_model.get("summary") if isinstance(deep_model.get("summary"), dict) else {}
    meta_raw = deep_model.get("meta") if isinstance(deep_model.get("meta"), dict) else {}
    pattern_count = _coerce_int(summary_raw.get("patternCount"), len(patterns))
    transition_count = _coerce_int(summary_raw.get("transitionCount"), len(transition_edges))
    analysis_version = str(payload.get("analysis_version") or meta_raw.get("analysisVersion") or "").strip()
    is_deep_v2_family = analysis_version == "emotion_structure.deep.v2"

    if report_type == "daily" and is_deep_v2_family:
        return _build_daily_deep_v2_summary(
            memo_themes=memo_themes,
            memo_triggers=memo_triggers,
            transition_edges=transition_edges,
            recovery_rows=recovery_rows,
        )

    if report_type == "weekly" and (memo_themes or memo_triggers):
        return _build_weekly_deep_v2_summary(
            memo_themes=memo_themes,
            pattern_episodes=pattern_episodes,
            memo_triggers=memo_triggers,
            transition_edges=transition_edges,
            recovery_rows=recovery_rows,
        )

    if report_type == "monthly" and monthly_phases:
        return _build_monthly_deep_v2_summary(
            memo_themes=memo_themes,
            pattern_episodes=pattern_episodes,
            memo_triggers=memo_triggers,
            transition_edges=transition_edges,
            recovery_rows=recovery_rows,
            monthly_phases=monthly_phases,
            monthly_shifts=monthly_shifts,
        )

    top_edge = transition_edges[0] if transition_edges else {}
    top_route = str(top_edge.get("routeLabel") or "").strip()
    top_edge_count = _coerce_int(top_edge.get("count"), 0)
    top_pattern = patterns[0] if patterns else {}
    top_pattern_label = str(top_pattern.get("label") or "").strip()
    top_pattern_routes = " / ".join(list(top_pattern.get("transitionRouteLabels") or [])[:2])
    top_recovery = recovery_rows[0] if recovery_rows else {}
    top_recovery_route = str(top_recovery.get("routeLabel") or "").strip()
    top_recovery_mean = _format_minutes_ja(top_recovery.get("meanMinutes"))
    top_keyword = str((memo_triggers[0] or {}).get("keyword") or "").strip() if memo_triggers else ""

    structural_comment = ""
    gentle_comment = ""
    next_points: List[str] = []
    evidence_items: List[Dict[str, str]] = []

    if report_type == "daily":
        if top_route:
            structural_comment = f"昨日は {top_route} への切り替わりがいちばん目立ち、その流れが一日の中で何度か繰り返されていました。"
            if top_edge_count > 0:
                structural_comment += f" この切り替わりは {top_edge_count} 回見られています。"
        elif transition_count > 0:
            structural_comment = f"昨日は気持ちの切り替わりが {transition_count} 回あり、その動き方にまだ余韻が残っていたようです。"
        else:
            structural_comment = "昨日は深いところの動きを言い切るには、材料がまだ少なめでした。"

        if top_recovery_route and top_recovery_mean:
            structural_comment += f" とくに {top_recovery_route} は平均 {top_recovery_mean} ほどで起きていました。"

        if top_keyword:
            gentle_comment = f"「{top_keyword}」という言葉が、昨日の切り替わりに近い場所で何度か現れていました。"
        elif top_recovery_route:
            gentle_comment = f"{top_recovery_route} が起きた前後の考え方を短く振り返ると、昨日の流れが受け取りやすくなります。"

        if transition_count > 0:
            evidence_items.append({"text": f"昨日は感情の切り替わりが合計 {transition_count} 件ありました。"})
        if top_route and top_edge_count > 0:
            evidence_items.append({"text": f"{top_route} が昨日の中でいちばん多い流れでした。"})
        if top_keyword:
            evidence_items.append({"text": f"思考メモでは「{top_keyword}」が切り替わりの手がかりとして目立っていました。"})
        if top_recovery_route and top_recovery_mean:
            evidence_items.append({"text": f"{top_recovery_route} は平均 {top_recovery_mean} ほどで起きていました。"})

        if top_route:
            next_points.append(f"{top_route} が起きた前後で、何を考えていたかを一言だけ残してみてください。")
        if top_keyword:
            next_points.append(f"「{top_keyword}」が出た場面で、感情がどう動いたかを見返してみてください。")

    elif report_type == "weekly":
        if patterns:
            structural_comment = f"今週は、気持ちを整えようとするときの出方が {pattern_count or len(patterns)} 個ほどまとまりとして見えていました。"
            if top_pattern_label:
                structural_comment += f" いちばん前に出やすかったのは「{top_pattern_label}」です。"
            if top_pattern_routes:
                structural_comment += f" 代表的な切り替わりは {top_pattern_routes} でした。"
        elif top_route:
            structural_comment = f"今週は {top_route} への切り替わりが目立ち、その流れが何度か繰り返されていました。"
        elif transition_count > 0:
            structural_comment = f"今週は気持ちの切り替わりが {transition_count} 回あり、その動き方にひとつの癖が見え始めていました。"
        else:
            structural_comment = "今週は深いところの動きを言い切るには、材料がまだ少なめでした。"

        if top_recovery_route and top_recovery_mean:
            gentle_comment = f"{top_recovery_route} は平均 {top_recovery_mean} ほどで起きており、今週の整え直し方の特徴として見えていました。"
        if top_keyword:
            if gentle_comment:
                gentle_comment += f" また、「{top_keyword}」という言葉も切り替わりの手がかりとして現れやすかったようです。"
            else:
                gentle_comment = f"「{top_keyword}」という言葉が、今週の切り替わりに近い場所で何度か現れていました。"

        if transition_count > 0:
            evidence_items.append({"text": f"今週は感情の切り替わりが合計 {transition_count} 件ありました。"})
        if pattern_count > 0:
            evidence_items.append({"text": f"動き方のまとまりは {pattern_count} 個ほど見られました。"})
        if top_route and top_edge_count > 0:
            evidence_items.append({"text": f"{top_route} が今週の中で目立つ流れでした。"})
        if top_keyword:
            evidence_items.append({"text": f"思考メモでは「{top_keyword}」が手がかりとして目立っていました。"})

        if top_pattern_label:
            next_points.append(f"「{top_pattern_label}」が強く出た日の前後を見返して、共通点を探してみてください。")
        if top_keyword:
            next_points.append(f"「{top_keyword}」が出た場面で、感情がどの流れに向かいやすいかを見比べてみてください。")
        elif top_route:
            next_points.append(f"{top_route} が起きた前後に、どんな出来事や受け止め方があったかを振り返ってみてください。")

    else:
        if patterns:
            structural_comment = f"今月は、気持ちを整えようとするときの出方が {pattern_count or len(patterns)} 個ほどまとまりとして見えていました。"
            if top_pattern_label:
                structural_comment += f" いちばん前に出やすかったのは「{top_pattern_label}」です。"
            if top_pattern_routes:
                structural_comment += f" 代表的な切り替わりは {top_pattern_routes} でした。"
            if len(patterns) >= 2:
                structural_comment += " いくつかの動き方が同時に重なっていた月でもあります。"
        elif top_route:
            structural_comment = f"今月は {top_route} への切り替わりが目立ち、その流れが月の中で何度か繰り返されていました。"
        elif transition_count > 0:
            structural_comment = f"今月は気持ちの切り替わりが {transition_count} 回あり、その動き方に月らしい癖が見え始めていました。"
        else:
            structural_comment = "今月は深いところの動きを言い切るには、材料がまだ少なめでした。"

        if top_recovery_route and top_recovery_mean:
            gentle_comment = f"{top_recovery_route} は平均 {top_recovery_mean} ほどで起きており、今月の整え直し方のひとつとして見えていました。"
        if top_keyword:
            if gentle_comment:
                gentle_comment += f" また、「{top_keyword}」という言葉も切り替わりに関わる手がかりとして現れやすかったようです。"
            else:
                gentle_comment = f"「{top_keyword}」という言葉が、今月の切り替わりに近い場所で何度か現れていました。"

        if transition_count > 0:
            evidence_items.append({"text": f"今月は感情の切り替わりが合計 {transition_count} 件ありました。"})
        if pattern_count > 0:
            evidence_items.append({"text": f"動き方のまとまりは {pattern_count} 個ほど見られました。"})
        if top_route and top_edge_count > 0:
            evidence_items.append({"text": f"{top_route} が今月の中で代表的な流れでした。"})
        if top_keyword:
            evidence_items.append({"text": f"思考メモでは「{top_keyword}」が手がかりとして目立っていました。"})

        if top_pattern_label:
            next_points.append(f"「{top_pattern_label}」が出やすい週や時間帯を見比べると、今月の動き方がつかみやすくなります。")
        if top_keyword:
            next_points.append(f"「{top_keyword}」が出た場面で、どの流れに入りやすいかを来月も見比べてみてください。")
        elif top_route:
            next_points.append(f"{top_route} が起きる前後で、思考や時間帯の共通点を見返してみてください。")

    return {
        "structuralComment": structural_comment.strip() or None,
        "gentleComment": gentle_comment.strip() or None,
        "nextPoints": [str(x).strip() for x in next_points if str(x).strip()][:4],
        "evidence": {
            "items": [item for item in evidence_items if isinstance(item, dict) and str(item.get("text") or "").strip()][:4]
        },
        "source": DEEP_SUMMARY_SOURCE_V1,
    }


def _render_structural_text_from_summary(
    *,
    title: str,
    report_type: str,
    period_start_iso: str,
    period_end_iso: str,
    summary: Dict[str, Any],
    patterns: List[Dict[str, Any]],
    recovery_rows: List[Dict[str, Any]],
    memo_triggers: List[Dict[str, Any]],
) -> str:
    summary_source = str((summary or {}).get("source") or "").strip()
    if summary_source == DEEP_SUMMARY_SOURCE_DAILY_V2:
        return _render_daily_deep_v2_text(
            title=title,
            period_start_iso=period_start_iso,
            period_end_iso=period_end_iso,
            summary=summary,
        )
    if summary_source == DEEP_SUMMARY_SOURCE_WEEKLY_V2:
        return _render_weekly_deep_v2_text(
            title=title,
            period_start_iso=period_start_iso,
            period_end_iso=period_end_iso,
            summary=summary,
        )
    if summary_source == DEEP_SUMMARY_SOURCE_MONTHLY_V2:
        return _render_monthly_deep_v2_text(
            title=title,
            period_start_iso=period_start_iso,
            period_end_iso=period_end_iso,
            summary=summary,
        )

    structural_comment = str((summary or {}).get("structuralComment") or "").strip()
    gentle_comment = str((summary or {}).get("gentleComment") or "").strip()
    evidence = (summary or {}).get("evidence") if isinstance((summary or {}).get("evidence"), dict) else {}
    evidence_items = evidence.get("items") if isinstance(evidence.get("items"), list) else []

    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.append("")

    if report_type == "daily":
        lines.append("【昨日、深いところで動いていた流れ】")
        lines.append(structural_comment or "昨日は深いところの流れを言い切るには、材料がまだ少なめでした。")
        lines.append("")

        if recovery_rows:
            lines.append("【切り替わりやすかった流れ】")
            for row in recovery_rows[:2]:
                mean_text = _format_minutes_ja(row.get("meanMinutes"))
                if mean_text:
                    lines.append(f"- {row.get('routeLabel')}: 平均 {mean_text}")
            lines.append("")

        if memo_triggers:
            lines.append("【手がかりになりやすかった考え】")
            for memo in memo_triggers[:2]:
                keyword = str(memo.get("keyword") or "").strip()
                related = " / ".join(list(memo.get("relatedTransitions") or [])[:2])
                if keyword and related:
                    lines.append(f"- 「{keyword}」: {related}")
                elif keyword:
                    lines.append(f"- 「{keyword}」")
            lines.append("")

        if evidence_items:
            lines.append("【見えていた手がかり】")
            for item in evidence_items[:3]:
                if isinstance(item, dict):
                    t = str(item.get("text") or "").strip()
                    if t:
                        lines.append(f"- {t}")
            lines.append("")

        if gentle_comment:
            lines.append("【こう受け取ると自然です】")
            lines.append(gentle_comment)
            lines.append("")

        lines.append("【このレポートについて】")
        lines.extend(_common_observation_note_lines())
        return "\n".join(lines).strip()

    if report_type == "weekly":
        lines.append("【今週、深いところで動いていた流れ】")
        lines.append(structural_comment or "今週は深いところの流れを言い切るには、材料がまだ少なめでした。")
        lines.append("")

        if patterns:
            lines.append("【主に見えていた動き方】")
            for pattern in patterns[:3]:
                label = str(pattern.get("label") or "").strip() or "動き方"
                desc = str(pattern.get("description") or "").strip()
                routes = " / ".join(list(pattern.get("transitionRouteLabels") or [])[:2])
                if desc:
                    lines.append(f"- {label}: {desc}")
                elif routes:
                    lines.append(f"- {label}: {routes}")
                else:
                    lines.append(f"- {label}")
            lines.append("")

        if recovery_rows:
            lines.append("【切り替わりやすかった流れ】")
            for row in recovery_rows[:3]:
                mean_text = _format_minutes_ja(row.get("meanMinutes"))
                if mean_text:
                    lines.append(f"- {row.get('routeLabel')}: 平均 {mean_text}")
            lines.append("")

        if memo_triggers:
            lines.append("【手がかりになりやすかった考え】")
            for memo in memo_triggers[:3]:
                keyword = str(memo.get("keyword") or "").strip()
                related = " / ".join(list(memo.get("relatedTransitions") or [])[:2])
                if keyword and related:
                    lines.append(f"- 「{keyword}」: {related}")
                elif keyword:
                    lines.append(f"- 「{keyword}」")
            lines.append("")

        if evidence_items:
            lines.append("【見えていた手がかり】")
            for item in evidence_items[:3]:
                if isinstance(item, dict):
                    t = str(item.get("text") or "").strip()
                    if t:
                        lines.append(f"- {t}")
            lines.append("")

        if gentle_comment:
            lines.append("【こう受け取ると自然です】")
            lines.append(gentle_comment)
            lines.append("")

        lines.append("【このレポートについて】")
        lines.extend(_common_observation_note_lines())
        return "\n".join(lines).strip()

    lines.append("【今月、深いところで続いていた流れ】")
    lines.append(structural_comment or "今月は深いところの流れを言い切るには、材料がまだ少なめでした。")
    lines.append("")

    if patterns:
        lines.append("【主に見えていた動き方】")
        for pattern in patterns[:5]:
            label = str(pattern.get("label") or "").strip() or "動き方"
            desc = str(pattern.get("description") or "").strip()
            routes = " / ".join(list(pattern.get("transitionRouteLabels") or [])[:2])
            if desc:
                lines.append(f"- {label}: {desc}")
            elif routes:
                lines.append(f"- {label}: {routes}")
            else:
                lines.append(f"- {label}")
        lines.append("")

    if recovery_rows:
        lines.append("【切り替わりやすかった流れ】")
        for row in recovery_rows[:4]:
            mean_text = _format_minutes_ja(row.get("meanMinutes"))
            if mean_text:
                lines.append(f"- {row.get('routeLabel')}: 平均 {mean_text}")
        lines.append("")

    if memo_triggers:
        lines.append("【手がかりになりやすかった考え】")
        for memo in memo_triggers[:4]:
            keyword = str(memo.get("keyword") or "").strip()
            related = " / ".join(list(memo.get("relatedTransitions") or [])[:2])
            if keyword and related:
                lines.append(f"- 「{keyword}」: {related}")
            elif keyword:
                lines.append(f"- 「{keyword}」")
        lines.append("")

    if evidence_items:
        lines.append("【見えていた手がかり】")
        for item in evidence_items[:4]:
            if isinstance(item, dict):
                t = str(item.get("text") or "").strip()
                if t:
                    lines.append(f"- {t}")
        lines.append("")

    if gentle_comment:
        lines.append("【こう受け取ると自然です】")
        lines.append(gentle_comment)
        lines.append("")

    lines.append("【このレポートについて】")
    lines.extend(_common_observation_note_lines())
    return "\n".join(lines).strip()



def _resolve_deep_report_contract(
    *,
    report_type: str,
    summary: Dict[str, Any],
    deep_payload: Dict[str, Any],
) -> Dict[str, str]:
    source = str((summary or {}).get("source") or "").strip()
    payload = deep_payload if isinstance(deep_payload, dict) else {}
    deep_model = _extract_deep_control_model_payload(payload)
    meta_raw = deep_model.get("meta") if isinstance(deep_model.get("meta"), dict) else {}
    analysis_version = str(payload.get("analysis_version") or meta_raw.get("analysisVersion") or "").strip()
    is_deep_v2_family = analysis_version == "emotion_structure.deep.v2"

    if source == DEEP_SUMMARY_SOURCE_MONTHLY_V2:
        return {
            "version": "myweb.deep.v2",
            "scopeVersion": "myweb.deep.monthly.v2",
            "presentationProfile": "monthly_model",
            "displayMode": "cards_graph_text",
        }

    if source == DEEP_SUMMARY_SOURCE_DAILY_V2:
        return {
            "version": "myweb.deep.v2",
            "scopeVersion": "myweb.deep.daily.v2",
            "presentationProfile": "daily_observation",
            "displayMode": "text",
        }

    if report_type == "weekly" and (source == DEEP_SUMMARY_SOURCE_WEEKLY_V2 or is_deep_v2_family):
        return {
            "version": "myweb.deep.v2",
            "scopeVersion": "myweb.deep.weekly.v2",
            "presentationProfile": "weekly_theme_pattern",
            "displayMode": "cards_graph_text",
        }

    return {
        "version": "myweb.structural.v1",
        "scopeVersion": "",
        "presentationProfile": "",
        "displayMode": "text" if report_type == "daily" else "graph_text",
    }




def _build_structural_report_payload(
    *,
    report_type: str,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    deep_analysis_payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    payload = deep_analysis_payload if isinstance(deep_analysis_payload, dict) else {}
    if not payload:
        return None

    deep_model = _extract_deep_control_model_payload(payload)
    transition_matrix = _normalize_transition_matrix(
        deep_model.get("transition_matrix") or deep_model.get("transitionMatrix") or payload.get("transitionMatrix") or {}
    )
    transition_edges = _normalize_transition_edges(
        deep_model.get("transition_edges") or deep_model.get("transitionEdges") or payload.get("transitionEdges") or []
    )
    recovery_rows = _normalize_recovery_time_rows(
        deep_model.get("recovery_time") or deep_model.get("recoveryTime") or payload.get("recoveryTime") or []
    )
    memo_triggers = _normalize_memo_triggers(
        deep_model.get("memo_triggers") or deep_model.get("memoTriggers") or payload.get("memoTriggers") or []
    )
    memo_themes = _normalize_memo_themes(
        deep_model.get("memo_themes") or deep_model.get("memoThemes") or payload.get("memoThemes") or []
    )
    control_patterns = _normalize_control_patterns(
        deep_model.get("control_patterns") or deep_model.get("controlPatterns") or payload.get("controlPatterns") or []
    )
    pattern_episodes = _normalize_pattern_episodes(
        deep_model.get("pattern_episodes") or deep_model.get("patternEpisodes") or payload.get("patternEpisodes") or []
    )
    monthly_phases = _normalize_monthly_phases(
        deep_model.get("monthly_phases")
        or deep_model.get("monthlyPhases")
        or payload.get("monthlyPhases")
        or payload.get("monthly_phases")
        or []
    )
    monthly_shifts = _normalize_monthly_shifts(
        deep_model.get("monthly_shifts")
        or deep_model.get("monthlyShifts")
        or payload.get("monthlyShifts")
        or payload.get("monthly_shifts")
        or []
    )
    summary_raw = deep_model.get("summary") if isinstance(deep_model.get("summary"), dict) else {}
    meta_raw = deep_model.get("meta") if isinstance(deep_model.get("meta"), dict) else {}

    summary = _build_structural_summary_object(
        report_type=report_type,
        deep_payload=payload,
    )
    content_text = _render_structural_text_from_summary(
        title=title,
        report_type=report_type,
        period_start_iso=period_start_iso,
        period_end_iso=period_end_iso,
        summary=summary,
        patterns=control_patterns,
        recovery_rows=recovery_rows,
        memo_triggers=memo_triggers,
    )
    contract = _resolve_deep_report_contract(report_type=report_type, summary=summary, deep_payload=payload)

    metrics = {
        "transitionCount": _coerce_int(summary_raw.get("transitionCount"), len(transition_edges)),
        "edgeCount": _coerce_int(summary_raw.get("edgeCount"), len(transition_edges)),
        "memoKeywordCount": _coerce_int(summary_raw.get("memoKeywordCount"), len(memo_triggers)),
        "memoThemeCount": _coerce_int(summary_raw.get("memoThemeCount"), len(memo_themes)),
        "patternCount": _coerce_int(summary_raw.get("patternCount"), len(control_patterns)),
        "patternEpisodeCount": _coerce_int(summary_raw.get("patternEpisodeCount"), len(pattern_episodes)),
        "quoteSampleCount": _coerce_int(summary_raw.get("quoteSampleCount"), 0),
        "themeLinkedTransitionCount": _coerce_int(summary_raw.get("themeLinkedTransitionCount"), 0),
        "recoveryRouteCount": _coerce_int(
            summary_raw.get("recoveryRouteCount"),
            len([row for row in recovery_rows if row.get("routeLabel")]),
        ),
        "phaseCount": _coerce_int(summary_raw.get("phaseCount"), len(monthly_phases)),
        "shiftCount": _coerce_int(summary_raw.get("shiftCount"), len(monthly_shifts)),
    }
    features = {
        "emotionLabels": {k: KEY_TO_JP.get(k, k) for k in EMOTION_KEYS},
        "memoThemes": memo_themes,
        "patternEpisodes": pattern_episodes,
        "controlPatterns": control_patterns,
        "memoTriggers": memo_triggers,
        "monthlyPhases": monthly_phases,
        "monthlyShifts": monthly_shifts,
        "meta": meta_raw,
        "snapshotRef": payload.get("snapshot_ref") if isinstance(payload.get("snapshot_ref"), dict) else {},
        "period": payload.get("period") if isinstance(payload.get("period"), dict) else {},
    }
    if transition_matrix:
        features["transitionMatrixJa"] = _localize_transition_matrix(transition_matrix)

    structural_report: Dict[str, Any] = {
        "version": contract["version"],
        "displayMode": contract["displayMode"],
        "reportType": str(report_type or ""),
        "contentText": content_text,
        "summary": summary,
        "metrics": metrics,
        "features": features,
        "transitionMatrix": transition_matrix,
        "transitionMatrixJa": _localize_transition_matrix(transition_matrix),
        "transitionEdges": transition_edges,
        "recoveryTime": recovery_rows,
        "memoTriggers": memo_triggers,
        "memoThemes": memo_themes,
        "controlPatterns": control_patterns,
        "patternEpisodes": pattern_episodes,
        "monthlyPhases": monthly_phases,
        "monthlyShifts": monthly_shifts,
        "analysisPayload": payload,
    }

    scope_version = str(contract.get("scopeVersion") or "").strip()
    presentation_profile = str(contract.get("presentationProfile") or "").strip()
    if scope_version:
        structural_report["scopeVersion"] = scope_version
    if presentation_profile:
        structural_report["presentationProfile"] = presentation_profile
    return structural_report


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
        title = f"日報：{title_date}"
        meta = {"titleDate": title_date}
    elif report_type == "weekly":
        s = _format_jst_md(ps)
        e = _format_jst_md(pe)
        title_range = f"{s} ～ {e}"
        title = f"週報：{title_range}"
        meta = {"titleRange": title_range}
    elif report_type == "monthly":
        end_jst = pe.astimezone(JST)
        title_month = f"{end_jst.year}/{end_jst.month}"
        title = f"月報：{title_month}"
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
        title = f"日報：{title_date}"
        meta = {"titleDate": title_date}
    elif report_type == "weekly":
        period_start_utc = dist_utc - 7 * DAY
        s = _format_jst_md(period_start_utc)
        e = _format_jst_md(period_end_utc)
        title_range = f"{s} ～ {e}"
        title = f"週報：{title_range}"
        meta = {"titleRange": title_range}
    else:
        # monthly (28 days)
        period_start_utc = dist_utc - 28 * DAY
        end_jst = period_end_utc.astimezone(JST)
        title_month = f"{end_jst.year}/{end_jst.month}"
        title = f"月報：{title_month}"
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


NO_PUBLIC_EMOTION_SKIP_REASON = "no_public_emotion_entries"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _has_renderable_emotion_content(row: Dict[str, Any]) -> bool:
    for it in _normalize_details(row):
        if _map_key(str(it.get("type") or "")):
            return True
    return False


def _filter_renderable_emotion_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in (rows or []) if _has_renderable_emotion_content(r)]


def _metrics_total_all(metrics: Any) -> int:
    if isinstance(metrics, dict):
        return _safe_int(metrics.get("totalAll") or 0, 0)
    return 0


def _build_myweb_skip_meta(
    *,
    report_type: str,
    scope: Optional[str] = None,
    public_source_hash: Optional[str] = None,
    skip_reason: str = NO_PUBLIC_EMOTION_SKIP_REASON,
) -> Dict[str, Any]:
    return {
        "status": "skipped",
        "report_type": str(report_type or "").strip() or None,
        "scope": str(scope or "").strip() or None,
        "report_id": None,
        "public_source_hash": str(public_source_hash or "").strip() or None,
        "skip_reason": str(skip_reason or NO_PUBLIC_EMOTION_SKIP_REASON),
    }


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
    totals = metrics.get("totals") if isinstance(metrics.get("totals"), dict) else {}
    total_all = int(metrics.get("totalAll") or 0)
    dominant = _dominant_label(metrics)

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

    switches = 0
    last = None
    for dk in dom_keys:
        if dk and last and dk != last:
            switches += 1
        if dk:
            last = dk

    top_pairs: List[Tuple[str, int]] = []
    for k in EMOTION_KEYS:
        try:
            v = int(totals.get(k, 0) or 0)
        except Exception:
            v = 0
        if v > 0:
            top_pairs.append((k, v))
    top_pairs.sort(key=lambda x: x[1], reverse=True)

    if total_all <= 0:
        overview = "今週は入力が少なめで、はっきりした傾向は読み取りにくい週でした。"
    else:
        overview = f"今週は「{dominant}」が中心に現れていました。"
        if len(top_pairs) >= 2:
            k2, _v2 = top_pairs[1]
            overview += f"その一方で、「{KEY_TO_JP.get(k2, k2)}」も重なる場面がありました。"
        if switches >= 3:
            overview += "日によって気持ちの向きが切り替わりやすい流れも見られました。"
        elif switches == 0:
            overview += "大きな切り替わりは少なく、全体としては近い空気感が続いていました。"

    movement_lines: List[str] = []
    if peak_day_label:
        movement_lines.append(f"感情の動きが強めに出たのは {peak_day_label} でした。")
    if total_all > 0:
        movement_lines.append(f"今週は「{dominant}」の比重が高く出ていました。")
    if len(top_pairs) >= 2:
        movement_lines.append(f"次に目立ったのは「{KEY_TO_JP.get(top_pairs[1][0], top_pairs[1][0])}」でした。")

    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.extend([
        "",
        "【今週、見えていたこと】",
        overview,
        "",
        "【気持ちが動いた流れ】",
    ])
    if movement_lines:
        for item in movement_lines[:3]:
            lines.append(f"・{item}")
    else:
        lines.append("・大きな動きとしてはまだまとまりませんでした。")
    lines.extend([
        "",
        "【このレポートについて】",
    ])
    lines.extend(_common_observation_note_lines())
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
    totals = metrics.get("totals") if isinstance(metrics.get("totals"), dict) else {}
    total_all = int(metrics.get("totalAll") or 0)
    dominant = _dominant_label(metrics)

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
        if wt > 0:
            week_summaries.append(f"{label}は「{dom_jp}」が中心でした。")

    reset_hint = False
    if len(calm_by_week) >= 4:
        try:
            first_half = calm_by_week[0] + calm_by_week[1]
            second_half = calm_by_week[2] + calm_by_week[3]
            reset_hint = second_half > first_half and second_half > 0
        except Exception:
            reset_hint = False

    if total_all <= 0:
        overview = "今月は入力が少なめで、はっきりした傾向は読み取りにくい月でした。"
    else:
        overview = f"今月は「{dominant}」が中心に現れていました。"
        dom_count = sum(1 for d in week_doms if d == dominant)
        if dom_count >= 3:
            overview += f"週をまたいで「{dominant}」が繰り返し中心になっていました。"
        elif dom_count == 2:
            overview += f"「{dominant}」が中心の週が複数あり、似た流れが戻ってきやすい月でした。"
        else:
            overview += "週ごとに中心感情が変わりやすく、その時々の状況に合わせて空気感が動いていた月でした。"

    movement_lines: List[str] = []
    movement_lines.extend(week_summaries[:2])
    if reset_hint:
        movement_lines.append("後半にかけて、少し整え直すような流れも見えていました。")

    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.extend([
        "",
        "【今月、見えていたこと】",
        overview,
        "",
        "【気持ちが動いた流れ】",
    ])
    if movement_lines:
        for item in movement_lines[:3]:
            lines.append(f"・{item}")
    else:
        lines.append("・大きな動きとしてはまだまとまりませんでした。")
    lines.extend([
        "",
        "【このレポートについて】",
    ])
    lines.extend(_common_observation_note_lines())
    return "\n".join(lines).strip()

def _render_daily_motion_line(movement: Dict[str, Any]) -> str:
    key = str((movement or {}).get("key") or "").strip()
    if key == "swing":
        return "前日とは少し違う気持ちの向きが出ていました。"
    if key == "up":
        return "前日より反応が表に出やすい一日でした。"
    if key == "down":
        return "前日より少し静かに落ち着いていく流れでした。"
    return "前日と近い空気感のまま推移していました。"

def _render_daily_hint_line(metrics: Dict[str, Any], movement: Dict[str, Any]) -> str:
    return ""

def _render_daily_standard_v3_text(
    *,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    metrics: Dict[str, Any],
    summary: Dict[str, Any],
    movement: Dict[str, Any],
) -> str:
    share = (metrics or {}).get("sharePct") if isinstance((metrics or {}).get("sharePct"), dict) else {}
    dominant_key = str((metrics or {}).get("dominantKey") or "").strip() or None
    if not dominant_key:
        totals = (metrics or {}).get("totals") if isinstance((metrics or {}).get("totals"), dict) else {}
        dominant_key = _dominant_key_from_map(totals)
    dominant_label = KEY_TO_JP.get(dominant_key, dominant_key) if dominant_key else "—"

    try:
        input_count = int((summary or {}).get("emotions_public") or 0)
    except Exception:
        input_count = 0
    if input_count <= 0:
        try:
            input_count = int((summary or {}).get("emotions_total") or 0)
        except Exception:
            input_count = 0
    if input_count <= 0:
        try:
            input_count = int((metrics or {}).get("totalAll") or 0)
        except Exception:
            input_count = 0

    try:
        dominant_pct = int(share.get(dominant_key, 0)) if dominant_key else 0
    except Exception:
        dominant_pct = 0

    if input_count <= 0:
        overview = "昨日は入力が少なめで、はっきりした傾向はまだ読み取りにくい日でした。"
    else:
        overview = f"昨日は「{dominant_label}」が比較的出やすい一日でした。"
        if dominant_pct > 0:
            overview += f"全体としては「{dominant_label}」の比重が高く、"
        overview += _render_daily_motion_line(movement)

    movement_lines: List[str] = []
    if dominant_key:
        movement_lines.append(f"最も強く出ていたのは「{dominant_label}」でした。")
    movement_lines.append(_render_daily_motion_line(movement))

    lines: List[str] = [title]
    rng = _range_line_jst(period_start_iso, period_end_iso)
    if rng:
        lines.append(rng)
    lines.extend([
        "",
        "【昨日、見えていたこと】",
        overview,
        "",
        "【気持ちが動いた流れ】",
    ])
    for item in movement_lines[:2]:
        lines.append(f"・{item}")
    lines.extend([
        "",
        "【このレポートについて】",
    ])
    lines.extend(_common_observation_note_lines())
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
    rows = _filter_renderable_emotion_rows(rows)

    if not rows:
        return "", {}, None, _build_myweb_skip_meta(report_type=target.report_type)

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
        text = _render_daily_standard_v3_text(
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            metrics=metrics,
            summary={"emotions_public": len(rows), "emotions_total": len(rows)},
            movement={"key": "stable"},
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
            content_json["deepReport"] = astor_report
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

    material_fields = []
    try:
        if infer_emotion_material_fields_from_rows is not None:
            material_fields = infer_emotion_material_fields_from_rows(rows)
    except Exception:
        material_fields = []
    content_json = _attach_analysis_report_validity_meta_if_available(
        content_json,
        material_count=len(rows or []),
        output_text=text,
        output_payload=content_json,
        material_fields=material_fields,
        target_period=f"{target.period_start_iso}/{target.period_end_iso}",
    )

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

    return text, content_json, astor_text, {"status": "generated", "report_id": rid}



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

    summary_public_raw = summary.get("emotions_public") if isinstance(summary, dict) else None
    summary_public = None
    if summary_public_raw not in (None, ""):
        summary_public = _safe_int(summary_public_raw, 0)
    metrics_total = _metrics_total_all(metrics)
    if (summary_public is not None and summary_public <= 0) or metrics_total <= 0:
        return "", content_json, None, _build_myweb_skip_meta(
            report_type=report_type,
            scope=sc,
            public_source_hash=snap_hash,
        )

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

    # analysis_results → Standard / Deep report source
    analysis_row: Optional[Dict[str, Any]] = None
    analysis_payload: Dict[str, Any] = {}
    deep_analysis_row: Optional[Dict[str, Any]] = None
    deep_analysis_payload: Dict[str, Any] = {}
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

        deep_analysis_row = await _fetch_analysis_result(
            uid,
            snapshot_id=snap_id,
            analysis_type="emotion_structure",
            analysis_stage="deep",
            scope=report_type,
        )
        if deep_analysis_row and isinstance(deep_analysis_row.get("payload"), dict):
            deep_analysis_payload = deep_analysis_row.get("payload") or {}

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
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
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
    if deep_analysis_row:
        content_json["deepAnalysisMeta"] = {
            "analysis_result_id": str((deep_analysis_row or {}).get("id") or "") or None,
            "analysis_type": str((deep_analysis_row or {}).get("analysis_type") or "emotion_structure"),
            "analysis_stage": str((deep_analysis_row or {}).get("analysis_stage") or "deep"),
            "analysis_version": str((deep_analysis_row or {}).get("analysis_version") or ""),
            "snapshot_id": snap_id,
            "source_hash": str((deep_analysis_row or {}).get("source_hash") or "") or snap_hash,
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

        structural_report = _build_structural_report_payload(
            report_type=report_type,
            title=target.title,
            period_start_iso=target.period_start_iso,
            period_end_iso=target.period_end_iso,
            deep_analysis_payload=deep_analysis_payload,
        )
        if isinstance(structural_report, dict):
            content_json["deepReport"] = structural_report
        elif astor_report:
            content_json["deepReport"] = astor_report
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

    snapshot_material_count = metrics_total
    if summary_public is not None:
        snapshot_material_count = max(snapshot_material_count, summary_public)
    content_json = _attach_analysis_report_validity_meta_if_available(
        content_json,
        material_count=snapshot_material_count,
        output_text=light_text,
        output_payload=content_json,
        material_fields=["emotion_details", "timestamp", "memo", "categories"],
        target_period=f"{target.period_start_iso}/{target.period_end_iso}",
    )

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

    return light_text, content_json, astor_text, {"status": "generated", "report_id": rid, "report_type": report_type, "scope": sc, "public_source_hash": snap_hash}



# Current-vocabulary aliases. DB/table/cache namespaces stay MyWeb-compatible until DB rename.
AnalysisEnsureRequest = MyWebEnsureRequest
AnalysisEnsureItem = MyWebEnsureItem
AnalysisEnsureResponse = MyWebEnsureResponse
AnalysisReportRecord = MyWebReportRecord
AnalysisReadyReportsResponse = MyWebReadyReportsResponse
AnalysisReportDetailResponse = MyWebReportDetailResponse
_build_analysis_target_period = _build_target_period
_analysis_report_exists = _report_exists
_generate_analysis_report_and_save = _generate_and_save
_generate_analysis_report_and_save_from_snapshot = _generate_and_save_from_snapshot


def register_analysis_report_routes(app: FastAPI) -> None:
    """Register current Analysis report routes on the given FastAPI app."""

    @app.post("/analysis/reports/ensure", response_model=AnalysisEnsureResponse)
    async def analysis_reports_ensure(
        req: AnalysisEnsureRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> AnalysisEnsureResponse:
        token = _extract_bearer_token(authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Missing authorization token")

        user_id = await _resolve_user_id_from_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authorization token")

        now_utc = _parse_now_utc(req.now_iso)

        types = req.types or ["weekly", "monthly"]
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
                            report_type=rt,
                            status="exists",
                            period_start=target.period_start_iso,
                            period_end=target.period_end_iso,
                            title=target.title,
                            report_id=existing_id,
                        )
                    )
                    continue

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
                    except Exception:
                        lock_acquired = True

                if not lock_acquired:
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
                                report_type=rt,
                                status="exists",
                                period_start=target.period_start_iso,
                                period_end=target.period_end_iso,
                                title=target.title,
                                report_id=waited_id,
                            )
                        )
                        continue
                    raise HTTPException(status_code=409, detail="Report generation is in progress")

                meta = None
                try:
                    if rt in ("daily", "weekly", "monthly"):
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

                                try:
                                    _text, _cjson, _astor_text, meta = await _generate_and_save_from_snapshot(
                                        user_id,
                                        scope=scope,
                                        include_astor=req.include_astor,
                                    )
                                except HTTPException as he2:
                                    if int(getattr(he2, "status_code", 0) or 0) == 404 and callable(get_emotion_period_public_input_status):
                                        status = await get_emotion_period_public_input_status(user_id=user_id, scope=scope)
                                        if not bool((status or {}).get("has_public_input")):
                                            meta = _build_myweb_skip_meta(report_type=rt, scope=scope)
                                        else:
                                            raise
                                    else:
                                        raise
                            else:
                                raise

                        try:
                            meta_status = str((meta or {}).get("status") or "generated") if isinstance(meta, dict) else "generated"
                            rid = (meta or {}).get("report_id") if isinstance(meta, dict) else None
                            expected_public_hash = (meta or {}).get("public_source_hash") if isinstance(meta, dict) else None
                            if meta_status == "generated" and rid:
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
                meta_dict = dict(meta) if isinstance(meta, dict) else {}
                item_status = "skipped" if str(meta_dict.get("status") or "generated") == "skipped" else "generated"
                results.append(
                    MyWebEnsureItem(
                        report_type=rt,
                        status=item_status,
                        period_start=target.period_start_iso,
                        period_end=target.period_end_iso,
                        title=target.title,
                        report_id=meta_dict.get("report_id"),
                        skip_reason=meta_dict.get("skip_reason"),
                    )
                )
            except HTTPException as he:
                results.append(
                    MyWebEnsureItem(
                        report_type=rt,
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
                        report_type=rt,
                        status="error",
                        period_start="",
                        period_end="",
                        title="",
                        error=str(e),
                    )
                )

        await invalidate_prefix(f"myweb:ready:{user_id}")
        await invalidate_prefix(f"myweb:detail:{user_id}")
        await invalidate_prefix(f"report_reads:myweb_unread:{user_id}")
        return AnalysisEnsureResponse(
            user_id=user_id,
            now_iso=now_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
            results=results,
        )

    @app.get("/analysis/reports/ready", response_model=AnalysisReadyReportsResponse)
    async def analysis_reports_ready(
        report_type: Literal["daily", "weekly", "monthly"] = "weekly",
        limit: int = 10,
        offset: int = 0,
        include_body: bool = Query(default=True, description="When false, return list metadata only for future list/detail clients."),
        authorization: Optional[str] = Header(default=None),
    ) -> AnalysisReadyReportsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        lim = max(1, min(int(limit or 10), 50))
        off = max(0, int(offset or 0))
        include_body_bool = bool(include_body)
        cache_key = build_cache_key(
            f"myweb:ready:{user_id}",
            {"report_type": str(report_type), "limit": lim, "offset": off, "include_body": include_body_bool},
        )

        async def _build_payload() -> Dict[str, Any]:
            try:
                return await _build_myweb_ready_payload_projection_first(
                    user_id=user_id,
                    report_type=str(report_type),
                    lim=lim,
                    off=off,
                    include_body=include_body_bool,
                )
            except Exception as exc:
                logger.error(
                    "myweb ready artifact-only projection failed: user_id=%s report_type=%s include_body=%s err=%r",
                    user_id,
                    report_type,
                    include_body_bool,
                    exc,
                )
                if isinstance(exc, HTTPException):
                    raise
                raise HTTPException(
                    status_code=503,
                    detail="MyWeb artifact projection is unavailable",
                ) from exc

        payload = await get_or_compute(
            cache_key,
            MYWEB_READY_CACHE_TTL_SECONDS,
            _build_payload,
            ttl_resolver=lambda payload: 0.75 if not list((payload or {}).get("items") or []) else MYWEB_READY_CACHE_TTL_SECONDS,
        )
        return AnalysisReadyReportsResponse(**payload)

    @app.get("/analysis/reports/{report_id}", response_model=AnalysisReportDetailResponse)
    async def analysis_report_detail(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None),
    ) -> AnalysisReportDetailResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        rid = str(report_id or "").strip()
        cache_key = build_cache_key(
            f"myweb:detail:{user_id}",
            {"report_id": rid},
        )

        payload = await get_or_compute(
            cache_key,
            MYWEB_DETAIL_CACHE_TTL_SECONDS,
            lambda: _build_myweb_detail_payload(user_id=user_id, report_id=rid),
        )
        return AnalysisReportDetailResponse(**payload)



def register_myweb_report_routes(app: FastAPI) -> None:
    """Legacy MyWeb registrar kept for direct legacy imports."""
    register_analysis_report_routes(app)


__all__ = [
    "AnalysisEnsureRequest",
    "AnalysisEnsureItem",
    "AnalysisEnsureResponse",
    "AnalysisReportRecord",
    "AnalysisReadyReportsResponse",
    "AnalysisReportDetailResponse",
    "MyWebEnsureRequest",
    "MyWebEnsureItem",
    "MyWebEnsureResponse",
    "MyWebReportRecord",
    "MyWebReadyReportsResponse",
    "MyWebReportDetailResponse",
    "_build_analysis_target_period",
    "_analysis_report_exists",
    "_generate_analysis_report_and_save",
    "_generate_analysis_report_and_save_from_snapshot",
    "register_analysis_report_routes",
    "register_myweb_report_routes",
]
