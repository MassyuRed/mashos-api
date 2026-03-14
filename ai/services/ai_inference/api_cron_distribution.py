# -*- coding: utf-8 -*-
"""api_cron_distribution.py

Phase 4: 0:00配布を“本当に配布”にする（サーバCron）
------------------------------------------------------

目的
- アプリが起動していなくても、JST 0:00 配布をサーバ側で確実に実行する。
- MyWeb（日報/週報/月報）と MyProfile（月次）を冪等に upsert し、履歴増殖を防ぐ。

実装方針
- Cron専用エンドポイントを追加し、X-Cron-Token で認証。
- user_id 一覧は Supabase の profiles からバッチ取得（offset/limit で分割実行可能）。
  ※将来的に active_users テーブルへ置き換え可能。

注意
- Render 等の実行時間制限を考慮し、1回のCronで処理するユーザー数を制限できる。
- 大量ユーザーになったら batch_size を下げて複数回叩く運用にする。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import _ensure_supabase_config, _fetch_push_tokens_for_users, _send_fcm_push

# Phase11: observability (structured logs + optional slack notifications)
try:
    from observability import (
        SLACK_INCLUDE_ERROR_SAMPLES,
        SLACK_NOTIFY_ON_CRON_ERRORS,
        SLACK_NOTIFY_ON_CRON_FAILURE,
        elapsed_ms,
        log_event,
        log_alert,
        monotonic_ms,
        new_run_id,
        send_slack_webhook,
    )
except Exception:  # pragma: no cover
    SLACK_INCLUDE_ERROR_SAMPLES = False  # type: ignore
    SLACK_NOTIFY_ON_CRON_ERRORS = False  # type: ignore
    SLACK_NOTIFY_ON_CRON_FAILURE = False  # type: ignore

    def monotonic_ms() -> float:  # type: ignore
        import time as _time
        return _time.monotonic() * 1000.0

    def elapsed_ms(start_ms: float) -> int:  # type: ignore
        import time as _time
        try:
            return int(max(0.0, (_time.monotonic() * 1000.0) - float(start_ms)))
        except Exception:
            return 0

    def log_event(_logger, _event: str, *, level: str = "info", **_fields):  # type: ignore
        try:
            getattr(_logger, level, _logger.info)(f"{_event} {_fields}")
        except Exception:
            pass


    def log_alert(_logger, _key: str, *, level: str = "warning", **_fields):  # type: ignore
        try:
            getattr(_logger, level, _logger.warning)(f"ALERT::{_key} {_fields}")
        except Exception:
            pass

    async def send_slack_webhook(**_kwargs):  # type: ignore
        return None

    def new_run_id(prefix: str = "run") -> str:  # type: ignore
        import uuid as _uuid
        return f"{prefix}_{_uuid.uuid4().hex[:12]}"




# Phase11+: persist cron run results to Supabase (dashboard)
try:
    from cron_run_store import cron_run_complete, cron_run_failed, cron_run_start
except Exception:  # pragma: no cover
    cron_run_start = None  # type: ignore
    cron_run_complete = None  # type: ignore
    cron_run_failed = None  # type: ignore

# Phase10: generation lock (dedupe concurrent generation)
try:
    from generation_lock import (
        build_lock_key,
        make_owner_id,
        release_lock,
        try_acquire_lock,
    )
except Exception:  # pragma: no cover
    build_lock_key = None  # type: ignore
    make_owner_id = None  # type: ignore
    release_lock = None  # type: ignore
    try_acquire_lock = None  # type: ignore

# MyWeb: reuse Phase1 helpers (on-demand ensure implementation)
try:
    from api_myweb_reports import _build_target_period as _myweb_build_target_period
    from api_myweb_reports import _generate_and_save as _myweb_generate_and_save
    from api_myweb_reports import _report_exists as _myweb_report_exists
except Exception:  # pragma: no cover
    _myweb_build_target_period = None  # type: ignore
    _myweb_generate_and_save = None  # type: ignore
    _myweb_report_exists = None  # type: ignore

# Shared publish visibility guard for past empty MyWeb rows.
try:
    from publish_governance import myweb_report_has_visible_content
except Exception:  # pragma: no cover
    def myweb_report_has_visible_content(_content_json):  # type: ignore
        return True

# MyProfile monthly report generator
try:
    from astor_myprofile_report import build_myprofile_monthly_report, parse_period_days
except Exception:  # pragma: no cover
    build_myprofile_monthly_report = None  # type: ignore
    parse_period_days = None  # type: ignore

# Tier-based report_mode selection (best-effort)
try:
    from subscription_store import get_subscription_tier_for_user
    from subscription import allowed_myprofile_modes_for_tier
except Exception:  # pragma: no cover
    get_subscription_tier_for_user = None  # type: ignore
    allowed_myprofile_modes_for_tier = None  # type: ignore

try:
    from report_distribution_push_store import ReportDistributionPushStore
except Exception:  # pragma: no cover
    ReportDistributionPushStore = None  # type: ignore

try:
    from report_distribution_settings_store import (
        ReportDistributionSettingsStore,
        REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME,
        REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED,
        REPORT_DISTRIBUTION_DEFAULT_TIMEZONE,
        is_bundle_due_for_settings,
    )
except Exception:  # pragma: no cover
    ReportDistributionSettingsStore = None  # type: ignore
    REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME = "00:00"  # type: ignore
    REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED = True  # type: ignore
    REPORT_DISTRIBUTION_DEFAULT_TIMEZONE = "Asia/Tokyo"  # type: ignore

    def is_bundle_due_for_settings(*, candidate_created_at, settings, now_utc=None):  # type: ignore
        return True


logger = logging.getLogger("cron_distribution")

# Phase11: Supabase HTTP instrumentation (log for 502/timeout monitoring)
OBS_LOG_SUPABASE_HTTP = (os.getenv("OBS_LOG_SUPABASE_HTTP", "true").strip().lower() != "false")
OBS_SUPABASE_SLOW_THRESHOLD_MS = int(os.getenv("OBS_SUPABASE_SLOW_THRESHOLD_MS", "1500") or "1500")


SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

PROFILES_TABLE = (os.getenv("COCOLON_PROFILES_TABLE", "profiles") or "profiles").strip()
MYWEB_REPORTS_TABLE = (os.getenv("MYWEB_REPORTS_TABLE", "myweb_reports") or "myweb_reports").strip()
MYPROFILE_REPORTS_TABLE = (os.getenv("MYPROFILE_REPORTS_TABLE", "myprofile_reports") or "myprofile_reports").strip()

MYPROFILE_REPORT_SCHEMA_VERSION = "myprofile.report.v4"

CRON_TOKEN_ENV = (
    os.getenv("MASHOS_CRON_TOKEN")
    or os.getenv("MYMODEL_CRON_TOKEN")
    or os.getenv("COCOLON_CRON_TOKEN")
    or ""
).strip()

DEFAULT_BATCH_SIZE = int(os.getenv("CRON_BATCH_SIZE", "200") or "200")
DEFAULT_CONCURRENCY = int(os.getenv("CRON_CONCURRENCY", "4") or "4")

# Phase10 lock tuning (env)
CRON_MYWEB_LOCK_TTL_SECONDS = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYWEB", "120") or "120")
CRON_MYPROFILE_MONTHLY_LOCK_TTL_SECONDS = int(
    os.getenv("GENERATION_LOCK_TTL_SECONDS_MYPROFILE_MONTHLY", "360") or "360"
)

# MyProfile monthly distribution defaults
DEFAULT_MYPROFILE_MONTHLY_PERIOD = (
    os.getenv("MYPROFILE_MONTHLY_DISTRIBUTION_PERIOD")
    or os.getenv("MYPROFILE_MONTHLY_PERIOD")
    or "28d"
).strip()

MYPROFILE_MONTHLY_INCLUDE_SECRET = (os.getenv("MYPROFILE_MONTHLY_INCLUDE_SECRET", "true").strip().lower() != "false")

# JST fixed
JST = timezone(timedelta(hours=9))
DAY = timedelta(days=1)


# ----------------------------
# Models
# ----------------------------

class CronBatchRequest(BaseModel):
    user_ids: Optional[List[str]] = Field(
        default=None,
        description="処理対象 user_id を直接指定する（未指定なら profiles から offset/limit で取得）",
    )
    offset: int = Field(default=0, ge=0, description="profiles 走査の offset")
    limit: int = Field(default=DEFAULT_BATCH_SIZE, ge=1, le=2000, description="profiles 走査の limit")
    shard_total: int = Field(
        default=1,
        ge=1,
        le=64,
        description="分割実行: 全シャード数（1なら分割なし）",
    )
    shard_index: int = Field(
        default=0,
        ge=0,
        le=63,
        description="分割実行: この実行のシャード番号（0..shard_total-1）",
    )
    force: bool = Field(default=False, description="true の場合、既存があっても再生成して上書き")
    dry_run: bool = Field(default=False, description="true の場合、DBへの書き込みを行わない")
    include_astor: bool = Field(default=True, description="MyWeb weekly/monthly で ASTOR 洞察を付与")
    now_iso: Optional[str] = Field(
        default=None,
        description="テスト用: 現在時刻(UTC ISO)。未指定ならサーバ現在時刻。",
    )


class CronBatchResponse(BaseModel):
    status: str = "ok"
    job: str
    now_iso: str
    offset: int
    limit: int
    shard_total: int = Field(default=1, description="分割実行: 全シャード数")
    shard_index: int = Field(default=0, description="分割実行: この実行のシャード番号")
    processed: int
    generated: int
    exists: int
    errors: int
    next_offset: Optional[int] = None
    done: bool
    error_samples: List[str] = Field(default_factory=list)


class ReportDistributionPushBatchRequest(BaseModel):
    limit: int = Field(default=300, ge=1, le=2000, description="最大bundle件数")
    dry_run: bool = Field(default=False, description="true の場合、送信・既読化せず候補を見る")
    now_iso: Optional[str] = Field(default=None, description="テスト用: 現在時刻(UTC ISO)。")


class ReportDistributionPushBatchResponse(BaseModel):
    status: str = "ok"
    job: str = "report_distribution_push"
    now_iso: str
    processed: int
    sent: int
    skipped: int
    errors: int
    bundles: int
    sent_users: List[str] = Field(default_factory=list)
    skipped_users: List[str] = Field(default_factory=list)
    error_samples: List[str] = Field(default_factory=list)


# ----------------------------
# Sharding helpers (Phase 4.5)
# ----------------------------

def _stable_shard_index(user_id: str, shard_total: int) -> int:
    """Deterministic shard index for a user_id.

    - Pythonのhash()はプロセスごとに変わり得るので使わない。
    - md5の先頭8桁をint化してmodを取る。
    """
    h = hashlib.md5(user_id.encode("utf-8")).hexdigest()[:8]
    return int(h, 16) % shard_total


def _validate_shard(shard_total: int, shard_index: int) -> None:
    if shard_total < 1 or shard_total > 64:
        raise HTTPException(status_code=400, detail="shard_total must be 1..64")
    if shard_index < 0 or shard_index >= shard_total:
        raise HTTPException(status_code=400, detail="shard_index must be within 0..shard_total-1")


def _apply_shard(user_ids: List[str], shard_total: int, shard_index: int) -> List[str]:
    if shard_total <= 1:
        return user_ids
    out: List[str] = []
    for uid in user_ids:
        try:
            if _stable_shard_index(uid, shard_total) == shard_index:
                out.append(uid)
        except Exception:
            # 万一の変換失敗はそのユーザーをスキップ（cron全体は止めない）
            continue
    return out



# Supabase helpers
# ----------------------------


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


def _parse_now_utc(now_iso: Optional[str]) -> datetime:
    if not now_iso:
        return datetime.now(timezone.utc)
    try:
        s = now_iso.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid now_iso")


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _sb_path_from_url(url: str) -> str:
    base = (SUPABASE_URL or "").rstrip("/")
    if base and url.startswith(base):
        return url[len(base):] or "/"
    return url


async def _sb_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    params: Optional[Dict[str, str]] = None,
    json_body: Any = None,
    op: str = "",
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> httpx.Response:
    """Instrumented Supabase request wrapper.

    - Logs status_code, duration_ms for monitoring (esp. 502 / timeout).
    - Does NOT log sensitive payloads (params/body are not logged).
    """
    start_ms = monotonic_ms()
    path = _sb_path_from_url(url)

    try:
        resp = await client.request(method, url, headers=headers, params=params, json=json_body)
        dur = elapsed_ms(start_ms)
        if OBS_LOG_SUPABASE_HTTP:
            lvl = "info"
            if resp.status_code >= 500 or dur >= OBS_SUPABASE_SLOW_THRESHOLD_MS:
                lvl = "warning"
            log_event(
                logger,
                "supabase_http",
                level=lvl,
                op=(op or None),
                method=method,
                path=path,
                status_code=resp.status_code,
                duration_ms=dur,
                job=job,
                run_id=run_id,
            )

            # Alert-friendly markers (Render grep)
            if resp.status_code >= 500:
                log_alert(
                    logger,
                    "SUPABASE_HTTP_5XX",
                    level="warning",
                    job=job,
                    run_id=run_id,
                    op=(op or None),
                    method=method,
                    path=path,
                    status_code=resp.status_code,
                    duration_ms=dur,
                )
            elif resp.status_code == 429:
                log_alert(
                    logger,
                    "SUPABASE_HTTP_429",
                    level="warning",
                    job=job,
                    run_id=run_id,
                    op=(op or None),
                    method=method,
                    path=path,
                    status_code=resp.status_code,
                    duration_ms=dur,
                )
        return resp

    except httpx.TimeoutException as exc:
        dur = elapsed_ms(start_ms)
        log_event(
            logger,
            "supabase_timeout",
            level="error",
            op=(op or None),
            method=method,
            path=path,
            duration_ms=dur,
            job=job,
            run_id=run_id,
            error=str(exc),
        )
        log_alert(
            logger,
            "SUPABASE_TIMEOUT",
            level="error",
            op=(op or None),
            method=method,
            path=path,
            duration_ms=dur,
            job=job,
            run_id=run_id,
        )
        raise

    except httpx.RequestError as exc:
        dur = elapsed_ms(start_ms)
        log_event(
            logger,
            "supabase_request_error",
            level="error",
            op=(op or None),
            method=method,
            path=path,
            duration_ms=dur,
            job=job,
            run_id=run_id,
            error=str(exc),
            exc_type=type(exc).__name__,
        )
        log_alert(
            logger,
            "SUPABASE_REQUEST_ERROR",
            level="error",
            op=(op or None),
            method=method,
            path=path,
            duration_ms=dur,
            job=job,
            run_id=run_id,
            exc_type=type(exc).__name__,
        )
        raise



async def _fetch_user_ids_from_profiles(
    client: httpx.AsyncClient,
    *,
    offset: int,
    limit: int,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> List[str]:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}/rest/v1/{PROFILES_TABLE}"
    params = {
        "select": "id",
        "order": "id.asc",
        "offset": str(offset),
        "limit": str(limit),
    }
    try:
        resp = await _sb_request(
            client,
            "GET",
            url,
            headers=_sb_headers(),
            params=params,
            op="profiles_list",
            run_id=run_id,
            job=job,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to list profiles")

    if resp.status_code >= 300:
        logger.error("profiles list failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to list profiles")

    rows = resp.json()
    out: List[str] = []
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict) and r.get("id"):
                out.append(str(r["id"]))
    return out


# ----------------------------
# Cron auth
# ----------------------------


def _require_cron_token(x_cron_token: Optional[str]) -> None:
    tok = str(x_cron_token or "").strip()
    if not CRON_TOKEN_ENV:
        # Fail closed: if env is not set, do not expose cron routes.
        raise HTTPException(status_code=500, detail="Cron token is not configured")
    if not tok or tok != CRON_TOKEN_ENV:
        raise HTTPException(status_code=401, detail="Invalid cron token")


# ----------------------------
# MyProfile monthly helpers
# ----------------------------


def _jst_midnight_utc(year: int, month: int, day: int) -> datetime:
    jst_dt = datetime(year, month, day, 0, 0, 0, 0, tzinfo=JST)
    return jst_dt.astimezone(timezone.utc)


def _last_monthly_distribution_utc(now_utc: datetime) -> datetime:
    now_jst = now_utc.astimezone(JST)
    return _jst_midnight_utc(now_jst.year, now_jst.month, 1)



async def _myprofile_monthly_exists(
    client: httpx.AsyncClient,
    *,
    user_id: str,
    period_start_iso: str,
    period_end_iso: str,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Optional[int]:
    url = f"{SUPABASE_URL}/rest/v1/{MYPROFILE_REPORTS_TABLE}"
    params = {
        "select": "id",
        "user_id": f"eq.{user_id}",
        "report_type": "eq.monthly",
        "period_start": f"eq.{period_start_iso}",
        "period_end": f"eq.{period_end_iso}",
        "limit": "1",
    }
    try:
        resp = await _sb_request(
            client,
            "GET",
            url,
            headers=_sb_headers(),
            params=params,
            op="myprofile_monthly_exists",
            run_id=run_id,
            job=job,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to query myprofile_reports")

    if resp.status_code >= 300:
        logger.error("myprofile_reports exists check failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to query myprofile_reports")

    rows = resp.json()
    if isinstance(rows, list) and rows:
        rid = rows[0].get("id")
        return int(rid) if rid is not None else None
    return None



def _unwrap_myprofile_content_json(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cj = (row or {}).get("content_json")
    if not isinstance(cj, dict):
        return {}
    if isinstance(cj.get("meta"), dict) and not isinstance(cj.get("version"), str):
        merged = dict(cj.get("meta") or {})
        for k, v in cj.items():
            if k == "meta":
                continue
            merged.setdefault(k, v)
        return merged
    return cj


def _myprofile_monthly_row_is_current_schema(row: Optional[Dict[str, Any]]) -> bool:
    cj = _unwrap_myprofile_content_json(row)
    return str(cj.get("version") or "").strip() == MYPROFILE_REPORT_SCHEMA_VERSION


def _myprofile_history_fingerprint(row: Optional[Dict[str, Any]]) -> Optional[str]:
    cj = _unwrap_myprofile_content_json(row)
    history = cj.get("history") if isinstance(cj.get("history"), dict) else {}
    s = str(history.get("history_fingerprint") or "").strip()
    return s or None


def _myprofile_has_visible_content(row: Optional[Dict[str, Any]]) -> bool:
    cj = _unwrap_myprofile_content_json(row)
    visibility = cj.get("visibility") if isinstance(cj.get("visibility"), dict) else {}
    if "has_visible_content" in visibility:
        return bool(visibility.get("has_visible_content"))
    return bool(str((row or {}).get("content_text") or "").strip())


async def _fetch_myprofile_monthly_row(
    client: httpx.AsyncClient,
    *,
    user_id: str,
    period_start_iso: str,
    period_end_iso: str,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/{MYPROFILE_REPORTS_TABLE}"
    params = {
        "select": "id,title,content_text,content_json,generated_at,updated_at,period_start,period_end",
        "user_id": f"eq.{user_id}",
        "report_type": "eq.monthly",
        "period_start": f"eq.{period_start_iso}",
        "period_end": f"eq.{period_end_iso}",
        "limit": "1",
    }
    resp = await _sb_request(
        client,
        "GET",
        url,
        headers=_sb_headers(),
        params=params,
        op="myprofile_monthly_fetch_row",
        run_id=run_id,
        job=job,
    )
    if resp.status_code >= 300:
        logger.error("myprofile_reports fetch failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to query myprofile_reports")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _fetch_previous_myprofile_monthly_row(
    client: httpx.AsyncClient,
    *,
    user_id: str,
    before_period_end_iso: str,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/{MYPROFILE_REPORTS_TABLE}"
    params = {
        "select": "id,title,content_text,content_json,generated_at,updated_at,period_start,period_end",
        "user_id": f"eq.{user_id}",
        "report_type": "eq.monthly",
        "period_end": f"lt.{before_period_end_iso}",
        "order": "period_end.desc,generated_at.desc",
        "limit": "1",
    }
    resp = await _sb_request(
        client,
        "GET",
        url,
        headers=_sb_headers(),
        params=params,
        op="myprofile_monthly_fetch_previous_row",
        run_id=run_id,
        job=job,
    )
    if resp.status_code >= 300:
        logger.error("myprofile_reports previous fetch failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to query previous myprofile_reports")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _myprofile_monthly_upsert(
    client: httpx.AsyncClient,
    *,
    payload: Dict[str, Any],
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Optional[int]:
    url = f"{SUPABASE_URL}/rest/v1/{MYPROFILE_REPORTS_TABLE}"
    params = {
        "on_conflict": "user_id,report_type,period_start,period_end",
    }
    try:
        resp = await _sb_request(
            client,
            "POST",
            url,
            headers=_sb_headers(prefer="resolution=merge-duplicates,return=representation"),
            params=params,
            json_body=payload,
            op="myprofile_monthly_upsert",
            run_id=run_id,
            job=job,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to save myprofile monthly report")

    if resp.status_code not in (200, 201):
        logger.error("myprofile_reports upsert failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to save myprofile monthly report")

    rows = resp.json()
    if isinstance(rows, list) and rows:
        rid = rows[0].get("id")
        return int(rid) if rid is not None else None
    return None


async def _delete_myprofile_monthly_row(
    client: httpx.AsyncClient,
    *,
    row_id: Any,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> None:
    if row_id is None:
        return
    url = f"{SUPABASE_URL}/rest/v1/{MYPROFILE_REPORTS_TABLE}"
    params = {"id": f"eq.{row_id}"}
    resp = await _sb_request(
        client,
        "DELETE",
        url,
        headers=_sb_headers(),
        params=params,
        op="myprofile_monthly_delete",
        run_id=run_id,
        job=job,
    )
    if resp.status_code not in (200, 204):
        logger.error("myprofile_reports delete failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to delete stale myprofile monthly report")


async def _select_monthly_report_mode(user_id: str) -> str:
    """Tierに応じて MyProfile（月報）の report_mode を返す。

    Spec v2:
    - free    : entitlementなし（"" を返す）
    - plus    : standard
    - premium : structural

    Fail-closed: 取得に失敗したら entitlementなし。
    """

    if get_subscription_tier_for_user is None or allowed_myprofile_modes_for_tier is None:
        return ""

    try:
        tier = await get_subscription_tier_for_user(user_id)
        if str(getattr(tier, "value", tier)) == "free":
            return ""
        modes = allowed_myprofile_modes_for_tier(tier)
        if modes:
            # Prefer highest allowed mode
            return modes[-1].value
    except Exception:
        return ""
    return ""


@dataclass(frozen=True)
class MonthlyTarget:
    dist_utc: datetime
    period_start_utc: datetime
    period_end_utc: datetime
    period_start_iso: str
    period_end_iso: str
    title: str


def _build_myprofile_monthly_target(now_utc: datetime, period: str) -> MonthlyTarget:
    if parse_period_days is None:
        raise HTTPException(status_code=500, detail="astor_myprofile_report is not available")

    days = parse_period_days(period)
    dist_utc = _last_monthly_distribution_utc(now_utc)
    period_end_utc = dist_utc - timedelta(milliseconds=1)
    period_start_utc = dist_utc - timedelta(days=max(days, 1))

    # title range in JST
    s = period_start_utc.astimezone(JST)
    e = period_end_utc.astimezone(JST)
    title_range = f"{s.month}/{s.day} ～ {e.month}/{e.day}"
    title = f"自己構造レポート：{title_range}（{days}日分）"

    return MonthlyTarget(
        dist_utc=dist_utc,
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
        period_start_iso=_iso_utc(period_start_utc),
        period_end_iso=_iso_utc(period_end_utc),
        title=title,
    )


# ----------------------------
# Core runners
# ----------------------------


def _count_status(items: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    gen = sum(1 for it in items if it.get("status") == "generated")
    ex = sum(1 for it in items if it.get("status") == "exists")
    err = sum(1 for it in items if it.get("status") == "error")
    return gen, ex, err


async def _fetch_myweb_report_row(
    *,
    user_id: str,
    report_type: str,
    period_start_iso: str,
    period_end_iso: str,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/{MYWEB_REPORTS_TABLE}"
    params = {
        "select": "id,report_type,period_start,period_end,content_json",
        "user_id": f"eq.{user_id}",
        "report_type": f"eq.{report_type}",
        "period_start": f"eq.{period_start_iso}",
        "period_end": f"eq.{period_end_iso}",
        "limit": "1",
    }
    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await _sb_request(
            client,
            "GET",
            url,
            headers=_sb_headers(),
            params=params,
            op="myweb_report_fetch_row",
            run_id=run_id,
            job=job,
        )
    if resp.status_code >= 300:
        return None
    try:
        rows = resp.json()
    except Exception:
        return None
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


async def _run_myweb_for_users(
    *,
    report_type: Literal["daily", "weekly", "monthly"],
    user_ids: List[str],
    now_utc: datetime,
    force: bool,
    dry_run: bool,
    include_astor: bool,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    if _myweb_build_target_period is None or _myweb_generate_and_save is None or _myweb_report_exists is None:
        raise HTTPException(status_code=500, detail="api_myweb_reports is not available")

    sem = asyncio.Semaphore(max(1, DEFAULT_CONCURRENCY))
    errors: List[str] = []
    distribution_key = _distribution_key_for_now(now_utc)

    async def one(uid: str) -> Dict[str, Any]:
        async with sem:
            try:
                target = _myweb_build_target_period(report_type, now_utc)
                existing_id = await _myweb_report_exists(uid, report_type, target.period_start_iso, target.period_end_iso)
                if existing_id is not None and not force:
                    existing_row = await _fetch_myweb_report_row(
                        user_id=uid,
                        report_type=report_type,
                        period_start_iso=target.period_start_iso,
                        period_end_iso=target.period_end_iso,
                        run_id=run_id,
                        job=job,
                    )
                    if isinstance(existing_row, dict) and not myweb_report_has_visible_content(existing_row.get("content_json")):
                        return {"user_id": uid, "status": "skipped", "report_id": existing_id, "skip_reason": "no_visible_content"}
                    if not dry_run:
                        await _enqueue_report_distribution_candidate(
                            user_id=uid,
                            distribution_key=distribution_key,
                            report_family=f"emotion_{report_type}",
                            report_table=MYWEB_REPORTS_TABLE,
                            report_id=existing_id,
                            report_type=report_type,
                            period_start=target.period_start_iso,
                            period_end=target.period_end_iso,
                            open_target={
                                "screen": "MyWeb",
                                "open_mode": "reportHistory",
                                "report_type": report_type,
                            },
                        )
                    return {"user_id": uid, "status": "exists", "report_id": existing_id}
                if dry_run:
                    return {"user_id": uid, "status": "generated", "dry_run": True}

                # ---- Phase10: generation lock ----
                lock_key = None
                lock_owner = None
                lock_acquired = True
                if build_lock_key is not None and try_acquire_lock is not None:
                    try:
                        lock_key = build_lock_key(
                            namespace="myweb",
                            user_id=uid,
                            report_type=report_type,
                            period_start=target.period_start_iso,
                            period_end=target.period_end_iso,
                        )
                        lock_owner = (make_owner_id(f"cron_myweb_{report_type}") if make_owner_id is not None else None)
                        lr = await try_acquire_lock(
                            lock_key=lock_key,
                            ttl_seconds=CRON_MYWEB_LOCK_TTL_SECONDS,
                            owner_id=lock_owner,
                            context={
                                "namespace": "myweb",
                                "user_id": uid,
                                "report_type": report_type,
                                "period_start": target.period_start_iso,
                                "period_end": target.period_end_iso,
                                "source": f"cron_myweb_{report_type}",
                            },
                        )
                        lock_acquired = bool(getattr(lr, "acquired", False))
                        lock_owner = getattr(lr, "owner_id", lock_owner)
                    except Exception:
                        lock_acquired = True

                if not lock_acquired:
                    return {"user_id": uid, "status": "exists", "skipped": "locked"}

                try:
                    _text, _cjson, _astor_text, meta = await _myweb_generate_and_save(
                        uid,
                        target,
                        include_astor=include_astor,
                    )
                finally:
                    if lock_key and release_lock is not None:
                        await release_lock(lock_key=lock_key, owner_id=lock_owner)
                meta_dict = dict(meta) if isinstance(meta, dict) else {}
                meta_status = str(meta_dict.get("status") or "generated").strip() or "generated"
                report_id = meta_dict.get("report_id")
                if meta_status == "skipped":
                    return {
                        "user_id": uid,
                        "status": "skipped",
                        "report_id": None,
                        "skip_reason": meta_dict.get("skip_reason"),
                    }
                if not dry_run:
                    await _enqueue_report_distribution_candidate(
                        user_id=uid,
                        distribution_key=distribution_key,
                        report_family=f"emotion_{report_type}",
                        report_table=MYWEB_REPORTS_TABLE,
                        report_id=report_id,
                        report_type=report_type,
                        period_start=target.period_start_iso,
                        period_end=target.period_end_iso,
                        open_target={
                            "screen": "MyWeb",
                            "open_mode": "reportHistory",
                            "report_type": report_type,
                        },
                    )
                return {"user_id": uid, "status": "generated", "report_id": report_id}
            except Exception as exc:
                msg = f"{uid}: {exc}"
                errors.append(msg)
                return {"user_id": uid, "status": "error", "error": str(exc)}

    results = await asyncio.gather(*[one(uid) for uid in user_ids])
    return results, errors


async def _run_myprofile_monthly_for_users(
    *,
    user_ids: List[str],
    now_utc: datetime,
    force: bool,
    dry_run: bool,
    period: str,
    include_secret: bool,
    run_id: Optional[str] = None,
    job: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    if build_myprofile_monthly_report is None:
        raise HTTPException(status_code=500, detail="astor_myprofile_report is not available")

    target = _build_myprofile_monthly_target(now_utc, period)

    sem = asyncio.Semaphore(max(1, DEFAULT_CONCURRENCY))
    errors: List[str] = []
    distribution_key = _distribution_key_for_now(now_utc)

    async with httpx.AsyncClient(timeout=12.0) as client:

        async def one(uid: str) -> Dict[str, Any]:
            async with sem:
                try:
                    existing_row = await _fetch_myprofile_monthly_row(
                        client,
                        user_id=uid,
                        period_start_iso=target.period_start_iso,
                        period_end_iso=target.period_end_iso,
                        run_id=run_id,
                        job=job,
                    )
                    existing_id = existing_row.get("id") if isinstance(existing_row, dict) else None
                    existing_row_is_legacy = bool(existing_row is not None and not _myprofile_monthly_row_is_current_schema(existing_row))
                    if existing_row is not None and not force and _myprofile_monthly_row_is_current_schema(existing_row):
                        if not dry_run and existing_id is not None:
                            await _enqueue_report_distribution_candidate(
                                user_id=uid,
                                distribution_key=distribution_key,
                                report_family="self_structure_monthly",
                                report_table=MYPROFILE_REPORTS_TABLE,
                                report_id=existing_id,
                                report_type="monthly",
                                period_start=target.period_start_iso,
                                period_end=target.period_end_iso,
                                open_target={
                                    "screen": "MyWeb",
                                    "open_mode": "selfReportHistory",
                                    "self_report_type": "monthly",
                                },
                            )
                        return {"user_id": uid, "status": "exists", "report_id": existing_id}

                    report_mode = await _select_monthly_report_mode(uid)

                    # Spec v2: free users have no entitlement for MyProfile（月報）本文。
                    if not report_mode:
                        return {"user_id": uid, "status": "skipped", "skipped": "not_entitled"}

                    if dry_run:
                        return {"user_id": uid, "status": "generated", "dry_run": True, "report_mode": report_mode}

                    # ---- Phase10: generation lock ----
                    lock_key = None
                    lock_owner = None
                    lock_acquired = True
                    if build_lock_key is not None and try_acquire_lock is not None:
                        try:
                            lock_key = build_lock_key(
                                namespace="myprofile",
                                user_id=uid,
                                report_type="monthly",
                                period_start=target.period_start_iso,
                                period_end=target.period_end_iso,
                            )
                            lock_owner = (
                                make_owner_id("cron_myprofile_monthly") if make_owner_id is not None else None
                            )
                            lr = await try_acquire_lock(
                                lock_key=lock_key,
                                ttl_seconds=CRON_MYPROFILE_MONTHLY_LOCK_TTL_SECONDS,
                                owner_id=lock_owner,
                                context={
                                    "namespace": "myprofile",
                                    "user_id": uid,
                                    "report_type": "monthly",
                                    "period_start": target.period_start_iso,
                                    "period_end": target.period_end_iso,
                                    "period": period,
                                    "report_mode": report_mode,
                                    "source": "cron_myprofile_monthly",
                                },
                            )
                            lock_acquired = bool(getattr(lr, "acquired", False))
                            lock_owner = getattr(lr, "owner_id", lock_owner)
                        except Exception:
                            lock_acquired = True

                    if not lock_acquired:
                        return {"user_id": uid, "status": "exists", "skipped": "locked", "report_mode": report_mode}

                    try:
                        prev_saved_row = await _fetch_previous_myprofile_monthly_row(
                            client,
                            user_id=uid,
                            before_period_end_iso=target.period_end_iso,
                            run_id=run_id,
                            job=job,
                        )
                        prev_report_text = str(prev_saved_row.get("content_text") or "") if isinstance(prev_saved_row, dict) else None
                        prev_report_json = _unwrap_myprofile_content_json(prev_saved_row) if isinstance(prev_saved_row, dict) else None

                        # Generate at dist_utc boundary (end exclusive)
                        text, meta = build_myprofile_monthly_report(
                            user_id=uid,
                            period=period,
                            report_mode=report_mode,
                            include_secret=include_secret,
                            now=target.dist_utc,
                            prev_report_text=prev_report_text,
                            prev_report_json=prev_report_json,
                            report_type="monthly",
                            distribution_utc=_iso_utc(target.dist_utc),
                        )

                        text = str(text or "").strip()
                        if not text:
                            return {"user_id": uid, "status": "skipped", "skipped": "empty"}

                        visibility = meta.get("visibility") if isinstance(meta, dict) else {}
                        has_visible_content = bool((visibility or {}).get("has_visible_content"))
                        if not has_visible_content:
                            if existing_row_is_legacy and existing_id is not None:
                                await _delete_myprofile_monthly_row(
                                    client,
                                    row_id=existing_id,
                                    run_id=run_id,
                                    job=job,
                                )
                            return {
                                "user_id": uid,
                                "status": "skipped",
                                "skipped": str(((meta.get("history") if isinstance(meta, dict) else {}) or {}).get("skip_reason") or "no_visible_content"),
                                "report_mode": report_mode,
                            }

                        history_fingerprint = str(((meta.get("history") if isinstance(meta, dict) else {}) or {}).get("history_fingerprint") or "").strip() or None
                        prev_history_fingerprint = _myprofile_history_fingerprint(prev_saved_row)
                        if history_fingerprint and prev_history_fingerprint and history_fingerprint == prev_history_fingerprint:
                            if existing_row_is_legacy and existing_id is not None:
                                await _delete_myprofile_monthly_row(
                                    client,
                                    row_id=existing_id,
                                    run_id=run_id,
                                    job=job,
                                )
                            return {
                                "user_id": uid,
                                "status": "skipped",
                                "skipped": "unchanged",
                                "report_mode": report_mode,
                            }

                        content_json = {
                            **(meta or {}),
                            "source": "cron_myprofile_monthly",
                            "report_type": "monthly",
                            "report_mode": report_mode,
                            "period": period,
                            "dist_utc": _iso_utc(target.dist_utc),
                            "include_secret": include_secret,
                            "period_start": target.period_start_iso,
                            "period_end": target.period_end_iso,
                        }
                        content_json["history"] = {
                            **(content_json.get("history") if isinstance(content_json.get("history"), dict) else {}),
                            "archive_eligible": True,
                            "history_fingerprint": history_fingerprint,
                            "skip_reason": None,
                            "history_saved": True,
                        }

                        payload = {
                            "user_id": uid,
                            "report_type": "monthly",
                            "period_start": target.period_start_iso,
                            "period_end": target.period_end_iso,
                            "title": target.title,
                            "content_text": text,
                            "content_json": content_json,
                            "generated_at": _iso_utc(target.dist_utc),
                        }

                        rid = await _myprofile_monthly_upsert(client, payload=payload, run_id=run_id, job=job)
                        if not dry_run and rid is not None:
                            await _enqueue_report_distribution_candidate(
                                user_id=uid,
                                distribution_key=distribution_key,
                                report_family="self_structure_monthly",
                                report_table=MYPROFILE_REPORTS_TABLE,
                                report_id=rid,
                                report_type="monthly",
                                period_start=target.period_start_iso,
                                period_end=target.period_end_iso,
                                open_target={
                                    "screen": "MyWeb",
                                    "open_mode": "selfReportHistory",
                                    "self_report_type": "monthly",
                                },
                            )
                        return {"user_id": uid, "status": "generated", "report_id": rid, "report_mode": report_mode}
                    finally:
                        if lock_key and release_lock is not None:
                            await release_lock(lock_key=lock_key, owner_id=lock_owner)

                except Exception as exc:
                    msg = f"{uid}: {exc}"
                    errors.append(msg)
                    return {"user_id": uid, "status": "error", "error": str(exc)}

        results = await asyncio.gather(*[one(uid) for uid in user_ids])

    return results, errors



# ----------------------------
# Cron run persistence (Phase11+)
# ----------------------------

async def _maybe_record_cron_start(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    body: CronBatchRequest,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    if cron_run_start is None:
        return
    try:
        await cron_run_start(
            job=job,
            run_id=run_id,
            now_iso=now_iso,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            force=body.force,
            dry_run=body.dry_run,
            meta=meta or {},
        )
    except Exception:
        return


async def _maybe_record_cron_complete(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    body: CronBatchRequest,
    processed: int,
    generated: int,
    exists: int,
    errors: int,
    duration_ms: int,
    done: bool,
    next_offset: Optional[int],
    error_samples: List[str],
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    if cron_run_complete is None:
        return
    try:
        await cron_run_complete(
            job=job,
            run_id=run_id,
            now_iso=now_iso,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            processed=processed,
            generated=generated,
            exists=exists,
            errors=errors,
            duration_ms=duration_ms,
            done=done,
            next_offset=next_offset,
            error_samples=error_samples,
            meta=meta or {},
        )
    except Exception:
        return


async def _maybe_record_cron_failed(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    body: CronBatchRequest,
    duration_ms: int,
    err: Exception,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    if cron_run_failed is None:
        return
    try:
        await cron_run_failed(
            job=job,
            run_id=run_id,
            now_iso=now_iso,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            duration_ms=duration_ms,
            error=str(err),
            exc_type=type(err).__name__,
            meta=meta or {},
        )
    except Exception:
        return

# ----------------------------
# Route registration
# ----------------------------


def _distribution_key_for_now(now_utc: datetime) -> str:
    return now_utc.astimezone(JST).date().isoformat()


def _report_distribution_family_priority(family: str) -> int:
    order = {
        "emotion_daily": 10,
        "emotion_weekly": 20,
        "emotion_monthly": 30,
        "self_structure_monthly": 40,
    }
    return order.get(str(family or "").strip(), 999)


def _candidate_report_label(row: Dict[str, Any]) -> str:
    family = str((row or {}).get("report_family") or "").strip()
    if family == "emotion_daily":
        return "日報"
    if family == "emotion_weekly":
        return "週報"
    if family == "emotion_monthly":
        return "月報"
    if family == "self_structure_monthly":
        return "自己構造月報"
    return "レポート"


async def _enqueue_report_distribution_candidate(
    *,
    user_id: str,
    distribution_key: str,
    report_family: str,
    report_table: str,
    report_id: Any,
    report_type: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
    open_target: Dict[str, Any],
) -> None:
    if ReportDistributionPushStore is None:
        return
    try:
        store = ReportDistributionPushStore()
        await store.create_candidate(
            user_id=str(user_id or "").strip(),
            distribution_key=str(distribution_key or "").strip(),
            report_family=str(report_family or "").strip(),
            report_table=str(report_table or "").strip(),
            report_id=report_id,
            report_type=(str(report_type or "").strip() or None),
            period_start=(str(period_start or "").strip() or None),
            period_end=(str(period_end or "").strip() or None),
            open_target=(open_target or {}),
        )
    except Exception as exc:
        logger.warning(
            "enqueue report_distribution candidate failed. user=%s family=%s err=%s",
            str(user_id or "").strip(),
            str(report_family or "").strip(),
            exc,
        )


def _build_report_distribution_push_payload(bundle_rows: List[Dict[str, Any]], *, distribution_key: str) -> Dict[str, Any]:
    rows = sorted(bundle_rows or [], key=lambda r: _report_distribution_family_priority(str((r or {}).get("report_family") or "")))
    families = [str((r or {}).get("report_family") or "").strip() for r in rows if str((r or {}).get("report_family") or "").strip()]
    labels = [_candidate_report_label(r) for r in rows]
    unique_labels: List[str] = []
    for label in labels:
        if label not in unique_labels:
            unique_labels.append(label)

    title = "Cocolon"
    body = "新しいレポートが届きました"
    open_mode = "home"
    report_type = ""
    self_report_type = ""

    if len(families) == 1:
        family = families[0]
        if family == "emotion_daily":
            body = "日報が届きました"
            open_mode = "reportHistory"
            report_type = "daily"
        elif family == "emotion_weekly":
            body = "週報が届きました"
            open_mode = "reportHistory"
            report_type = "weekly"
        elif family == "emotion_monthly":
            body = "月報が届きました"
            open_mode = "reportHistory"
            report_type = "monthly"
        elif family == "self_structure_monthly":
            body = "自己構造月報が届きました"
            open_mode = "selfReportHistory"
            self_report_type = "monthly"
    elif unique_labels:
        body = f"新しいレポートが届きました（{'・'.join(unique_labels[:4])}）"

    return {
        "title": title,
        "body": body,
        "data": {
            "type": "report_distribution",
            "screen": "MyWeb",
            "distribution_key": str(distribution_key or "").strip(),
            "bundle_families": ",".join(families),
            "open_mode": open_mode,
            "report_type": report_type,
            "self_report_type": self_report_type,
        },
        "families": families,
    }


async def _send_report_distribution_bundle_push(
    *,
    user_id: str,
    distribution_key: str,
    bundle_rows: List[Dict[str, Any]],
    dry_run: bool,
) -> Dict[str, Any]:
    payload = _build_report_distribution_push_payload(bundle_rows, distribution_key=distribution_key)
    families = list(payload.get("families") or [])
    data_payload = dict(payload.get("data") or {})
    token_map = await _fetch_push_tokens_for_users([str(user_id or "").strip()])
    token = str((token_map or {}).get(str(user_id or "").strip()) or "").strip()

    send_status = "sent"
    if dry_run:
        send_status = "dry_run"
    elif token:
        await _send_fcm_push(
            tokens=[token],
            title=str(payload.get("title") or "Cocolon"),
            body=str(payload.get("body") or "新しいレポートが届きました"),
            data=data_payload,
        )
    else:
        send_status = "skipped_no_token"

    return {
        "send_status": send_status,
        "payload": data_payload,
        "bundle_families": families,
    }


def _build_slack_text_for_cron(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    processed: int,
    generated: int,
    exists: int,
    errors: int,
    shard_total: int,
    shard_index: int,
    offset: int,
    limit: int,
    done: bool,
    error_samples: Optional[List[str]] = None,
) -> str:
    lines = [
        f"job={job}",
        f"run_id={run_id}",
        f"now={now_iso}",
        f"processed={processed} generated={generated} exists={exists} errors={errors}",
        f"shard={shard_index}/{shard_total} offset={offset} limit={limit} done={done}",
    ]
    if SLACK_INCLUDE_ERROR_SAMPLES and error_samples:
        lines.append("")
        lines.append("error_samples:")
        for s in error_samples[:5]:
            lines.append(f"- {s}")
    return "\n".join(lines)


async def _maybe_notify_slack_cron_result(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    body: CronBatchRequest,
    processed: int,
    generated: int,
    exists: int,
    errors: int,
    done: bool,
    error_samples: List[str],
) -> None:
    # Only notify when there are errors
    if errors <= 0:
        return
    if not SLACK_NOTIFY_ON_CRON_ERRORS:
        return

    title = f"[MashOS][cron] {job} errors={errors}"
    text = _build_slack_text_for_cron(
        job=job,
        run_id=run_id,
        now_iso=now_iso,
        processed=processed,
        generated=generated,
        exists=exists,
        errors=errors,
        shard_total=body.shard_total,
        shard_index=body.shard_index,
        offset=body.offset,
        limit=body.limit,
        done=done,
        error_samples=error_samples,
    )
    try:
        await send_slack_webhook(title=title, text=text, key=f"cron:{job}:errors")
    except Exception:
        # best-effort
        return


async def _maybe_notify_slack_cron_failure(
    *,
    job: str,
    run_id: str,
    body: CronBatchRequest,
    err: Exception,
) -> None:
    if not SLACK_NOTIFY_ON_CRON_FAILURE:
        return
    title = f"[MashOS][cron] {job} FAILED"
    text = "\n".join(
        [
            f"job={job}",
            f"run_id={run_id}",
            f"shard={body.shard_index}/{body.shard_total} offset={body.offset} limit={body.limit}",
            f"error={type(err).__name__}: {err}",
        ]
    )
    try:
        await send_slack_webhook(title=title, text=text, key=f"cron:{job}:failure")
    except Exception:
        return


def register_cron_distribution_routes(app: FastAPI) -> None:

    @app.post("/cron/myweb/daily", response_model=CronBatchResponse)
    async def cron_myweb_daily(
        body: CronBatchRequest,
        x_cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    ) -> CronBatchResponse:
        job = "myweb_daily"
        _require_cron_token(x_cron_token)
        run_id = new_run_id(job)
        start_ms = monotonic_ms()

        log_event(
            logger,
            "cron_batch_start",
            job=job,
            run_id=run_id,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            force=body.force,
            dry_run=body.dry_run,
        )

        try:
            now_utc = _parse_now_utc(body.now_iso)
            _validate_shard(body.shard_total, body.shard_index)

            await _maybe_record_cron_start(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                meta={"report_type": "daily", "include_astor": False},
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                raw_user_ids = body.user_ids or await _fetch_user_ids_from_profiles(
                    client, offset=body.offset, limit=body.limit, run_id=run_id, job=job
                )
            raw_count = len(raw_user_ids)
            user_ids = _apply_shard(raw_user_ids, body.shard_total, body.shard_index)

            results, errs = await _run_myweb_for_users(
                report_type="daily",
                user_ids=user_ids,
                now_utc=now_utc,
                force=body.force,
                dry_run=body.dry_run,
                include_astor=False,
                run_id=run_id,
                job=job,
            )
            gen, ex, er = _count_status(results)
            next_offset = None if body.user_ids else (body.offset + raw_count)
            done = bool(body.user_ids) or (raw_count < body.limit)

            duration = elapsed_ms(start_ms)
            log_event(
                logger,
                "cron_batch_complete",
                level=("warning" if er > 0 else "info"),
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                offset=body.offset,
                limit=body.limit,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                done=done,
            )

            if er > 0:
                log_alert(
                    logger,
                    "CRON_ERRORS",
                    level="warning",
                    job=job,
                    run_id=run_id,
                    processed=len(user_ids),
                    generated=gen,
                    exists=ex,
                    errors=er,
                )

            await _maybe_record_cron_complete(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                done=done,
                next_offset=next_offset,
                error_samples=errs,
                meta={"report_type": "daily", "include_astor": False},
            )

            await _maybe_notify_slack_cron_result(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                done=done,
                error_samples=errs,
            )

            return CronBatchResponse(
                job=job,
                now_iso=_iso_utc(now_utc),
                offset=body.offset,
                limit=body.limit,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                next_offset=next_offset,
                done=done,
                error_samples=errs[:10],
            )
        except HTTPException as he:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                status_code=he.status_code,
                detail=str(he.detail),
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                status_code=he.status_code,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=he,
                meta={"report_type": "daily"},
            )
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=he)
            raise
        except Exception as exc:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                error=str(exc),
                exc_type=type(exc).__name__,
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                exc_type=type(exc).__name__,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=exc,
                meta={"job": job},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=exc)
            raise

    @app.post("/cron/myweb/weekly", response_model=CronBatchResponse)
    async def cron_myweb_weekly(
        body: CronBatchRequest,
        x_cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    ) -> CronBatchResponse:
        job = "myweb_weekly"
        _require_cron_token(x_cron_token)
        run_id = new_run_id(job)
        start_ms = monotonic_ms()

        log_event(
            logger,
            "cron_batch_start",
            job=job,
            run_id=run_id,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            force=body.force,
            dry_run=body.dry_run,
            include_astor=body.include_astor,
        )

        try:
            now_utc = _parse_now_utc(body.now_iso)
            _validate_shard(body.shard_total, body.shard_index)

            await _maybe_record_cron_start(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                meta={"report_type": "weekly", "include_astor": bool(body.include_astor)},
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                raw_user_ids = body.user_ids or await _fetch_user_ids_from_profiles(
                    client, offset=body.offset, limit=body.limit, run_id=run_id, job=job
                )
            raw_count = len(raw_user_ids)
            user_ids = _apply_shard(raw_user_ids, body.shard_total, body.shard_index)

            results, errs = await _run_myweb_for_users(
                report_type="weekly",
                user_ids=user_ids,
                now_utc=now_utc,
                force=body.force,
                dry_run=body.dry_run,
                include_astor=body.include_astor,
                run_id=run_id,
                job=job,
            )
            gen, ex, er = _count_status(results)
            next_offset = None if body.user_ids else (body.offset + raw_count)
            done = bool(body.user_ids) or (raw_count < body.limit)

            duration = elapsed_ms(start_ms)
            log_event(
                logger,
                "cron_batch_complete",
                level=("warning" if er > 0 else "info"),
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                offset=body.offset,
                limit=body.limit,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                done=done,
            )

            if er > 0:
                log_alert(
                    logger,
                    "CRON_ERRORS",
                    level="warning",
                    job=job,
                    run_id=run_id,
                    processed=len(user_ids),
                    generated=gen,
                    exists=ex,
                    errors=er,
                )

            await _maybe_record_cron_complete(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                done=done,
                next_offset=next_offset,
                error_samples=errs,
                meta={"job": job, "include_astor": bool(body.include_astor)},
            )

            await _maybe_notify_slack_cron_result(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                done=done,
                error_samples=errs,
            )

            return CronBatchResponse(
                job=job,
                now_iso=_iso_utc(now_utc),
                offset=body.offset,
                limit=body.limit,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                next_offset=next_offset,
                done=done,
                error_samples=errs[:10],
            )
        except HTTPException as he:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                status_code=he.status_code,
                detail=str(he.detail),
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                status_code=he.status_code,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=he,
                meta={"job": job, "status_code": he.status_code},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=he)
            raise
        except Exception as exc:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                error=str(exc),
                exc_type=type(exc).__name__,
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                exc_type=type(exc).__name__,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=exc,
                meta={"job": job},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=exc)
            raise

    @app.post("/cron/myweb/monthly", response_model=CronBatchResponse)
    async def cron_myweb_monthly(
        body: CronBatchRequest,
        x_cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    ) -> CronBatchResponse:
        job = "myweb_monthly"
        _require_cron_token(x_cron_token)
        run_id = new_run_id(job)
        start_ms = monotonic_ms()

        log_event(
            logger,
            "cron_batch_start",
            job=job,
            run_id=run_id,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            force=body.force,
            dry_run=body.dry_run,
            include_astor=body.include_astor,
        )

        try:
            now_utc = _parse_now_utc(body.now_iso)
            _validate_shard(body.shard_total, body.shard_index)

            await _maybe_record_cron_start(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                meta={"report_type": "monthly", "include_astor": bool(body.include_astor)},
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                raw_user_ids = body.user_ids or await _fetch_user_ids_from_profiles(
                    client, offset=body.offset, limit=body.limit, run_id=run_id, job=job
                )
            raw_count = len(raw_user_ids)
            user_ids = _apply_shard(raw_user_ids, body.shard_total, body.shard_index)

            results, errs = await _run_myweb_for_users(
                report_type="monthly",
                user_ids=user_ids,
                now_utc=now_utc,
                force=body.force,
                dry_run=body.dry_run,
                include_astor=body.include_astor,
                run_id=run_id,
                job=job,
            )
            gen, ex, er = _count_status(results)
            next_offset = None if body.user_ids else (body.offset + raw_count)
            done = bool(body.user_ids) or (raw_count < body.limit)

            duration = elapsed_ms(start_ms)
            log_event(
                logger,
                "cron_batch_complete",
                level=("warning" if er > 0 else "info"),
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                offset=body.offset,
                limit=body.limit,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                done=done,
            )

            if er > 0:
                log_alert(
                    logger,
                    "CRON_ERRORS",
                    level="warning",
                    job=job,
                    run_id=run_id,
                    processed=len(user_ids),
                    generated=gen,
                    exists=ex,
                    errors=er,
                )

            await _maybe_record_cron_complete(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                done=done,
                next_offset=next_offset,
                error_samples=errs,
                meta={"job": job, "include_astor": bool(body.include_astor)},
            )

            await _maybe_notify_slack_cron_result(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                done=done,
                error_samples=errs,
            )

            return CronBatchResponse(
                job=job,
                now_iso=_iso_utc(now_utc),
                offset=body.offset,
                limit=body.limit,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                next_offset=next_offset,
                done=done,
                error_samples=errs[:10],
            )
        except HTTPException as he:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                status_code=he.status_code,
                detail=str(he.detail),
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                status_code=he.status_code,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=he,
                meta={"job": job, "status_code": he.status_code},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=he)
            raise
        except Exception as exc:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                error=str(exc),
                exc_type=type(exc).__name__,
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                exc_type=type(exc).__name__,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=exc,
                meta={"job": job},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=exc)
            raise

    @app.post("/cron/myprofile/monthly", response_model=CronBatchResponse)
    async def cron_myprofile_monthly(
        body: CronBatchRequest,
        x_cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    ) -> CronBatchResponse:
        job = "myprofile_monthly"
        _require_cron_token(x_cron_token)
        run_id = new_run_id(job)
        start_ms = monotonic_ms()

        log_event(
            logger,
            "cron_batch_start",
            job=job,
            run_id=run_id,
            offset=body.offset,
            limit=body.limit,
            shard_total=body.shard_total,
            shard_index=body.shard_index,
            force=body.force,
            dry_run=body.dry_run,
        )

        try:
            now_utc = _parse_now_utc(body.now_iso)
            period = DEFAULT_MYPROFILE_MONTHLY_PERIOD
            _validate_shard(body.shard_total, body.shard_index)

            await _maybe_record_cron_start(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                meta={"report_type": "myprofile_monthly", "period": period, "include_secret": bool(MYPROFILE_MONTHLY_INCLUDE_SECRET)},
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                raw_user_ids = body.user_ids or await _fetch_user_ids_from_profiles(
                    client, offset=body.offset, limit=body.limit, run_id=run_id, job=job
                )
            raw_count = len(raw_user_ids)
            user_ids = _apply_shard(raw_user_ids, body.shard_total, body.shard_index)

            results, errs = await _run_myprofile_monthly_for_users(
                user_ids=user_ids,
                now_utc=now_utc,
                force=body.force,
                dry_run=body.dry_run,
                period=period,
                include_secret=MYPROFILE_MONTHLY_INCLUDE_SECRET,
                run_id=run_id,
                job=job,
            )
            gen, ex, er = _count_status(results)
            next_offset = None if body.user_ids else (body.offset + raw_count)
            done = bool(body.user_ids) or (raw_count < body.limit)

            duration = elapsed_ms(start_ms)
            log_event(
                logger,
                "cron_batch_complete",
                level=("warning" if er > 0 else "info"),
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                offset=body.offset,
                limit=body.limit,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                done=done,
                period=period,
            )

            if er > 0:
                log_alert(
                    logger,
                    "CRON_ERRORS",
                    level="warning",
                    job=job,
                    run_id=run_id,
                    processed=len(user_ids),
                    generated=gen,
                    exists=ex,
                    errors=er,
                    period=period,
                )

            await _maybe_record_cron_complete(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                duration_ms=duration,
                done=done,
                next_offset=next_offset,
                error_samples=errs,
                meta={
                    "report_type": "myprofile_monthly",
                    "period": period,
                    "include_secret": bool(MYPROFILE_MONTHLY_INCLUDE_SECRET),
                },
            )

            await _maybe_notify_slack_cron_result(
                job=job,
                run_id=run_id,
                now_iso=_iso_utc(now_utc),
                body=body,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                done=done,
                error_samples=errs,
            )

            return CronBatchResponse(
                job=job,
                now_iso=_iso_utc(now_utc),
                offset=body.offset,
                limit=body.limit,
                processed=len(user_ids),
                generated=gen,
                exists=ex,
                errors=er,
                shard_total=body.shard_total,
                shard_index=body.shard_index,
                next_offset=next_offset,
                done=done,
                error_samples=errs[:10],
            )
        except HTTPException as he:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                status_code=he.status_code,
                detail=str(he.detail),
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                status_code=he.status_code,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=he,
                meta={"job": job, "status_code": he.status_code},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=he)
            raise
        except Exception as exc:
            log_event(
                logger,
                "cron_batch_failed",
                level="error",
                job=job,
                run_id=run_id,
                duration_ms=elapsed_ms(start_ms),
                error=str(exc),
                exc_type=type(exc).__name__,
            )
            log_alert(
                logger,
                "CRON_FAILED",
                level="error",
                job=job,
                run_id=run_id,
                exc_type=type(exc).__name__,
            )
            await _maybe_record_cron_failed(
                job=job,
                run_id=run_id,
                now_iso=(body.now_iso or _iso_utc(datetime.now(timezone.utc))),
                body=body,
                duration_ms=elapsed_ms(start_ms),
                err=exc,
                meta={"job": job},
            )
            # slack notify (best-effort)
            await _maybe_notify_slack_cron_failure(job=job, run_id=run_id, body=body, err=exc)
            raise


    @app.post("/cron/report-distribution/push", response_model=ReportDistributionPushBatchResponse)
    async def cron_report_distribution_push(
        body: ReportDistributionPushBatchRequest,
        x_cron_token: Optional[str] = Header(default=None, alias="X-Cron-Token"),
    ) -> ReportDistributionPushBatchResponse:
        _require_cron_token(x_cron_token)
        now_utc = _parse_now_utc(body.now_iso)
        if ReportDistributionPushStore is None:
            raise HTTPException(status_code=500, detail="report_distribution_push_store is not available")

        store = ReportDistributionPushStore()
        candidate_limit = max(1, min(int(body.limit or 300) * 6, 2000))
        rows = await store.list_pending_candidates(limit=candidate_limit)

        bundles: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("user_id") or "").strip()
            dist_key = str(row.get("distribution_key") or "").strip()
            if not uid or not dist_key:
                continue
            bundles.setdefault((uid, dist_key), []).append(row)

        settings_store = ReportDistributionSettingsStore() if ReportDistributionSettingsStore is not None else None
        settings_map: Dict[str, Dict[str, Any]] = {}
        if settings_store is not None and bundles:
            try:
                settings_map = await settings_store.fetch_settings_map_for_users(sorted({uid for (uid, _dist) in bundles.keys()}))
            except Exception:
                logger.exception("report_distribution_push: fetch settings map failed")
                settings_map = {}

        processed = 0
        sent = 0
        skipped = 0
        errors = 0
        sent_users: List[str] = []
        skipped_users: List[str] = []
        error_samples: List[str] = []

        for (uid, dist_key), bundle_rows in sorted(bundles.items(), key=lambda item: (item[0][1], item[0][0]))[: max(1, int(body.limit or 300))]:
            processed += 1
            try:
                settings = dict((settings_map or {}).get(uid) or {
                    "notification_enabled": REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED,
                    "delivery_time_local": REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME,
                    "timezone_name": REPORT_DISTRIBUTION_DEFAULT_TIMEZONE,
                })
                created_values = [
                    str((row or {}).get("created_at") or "").strip()
                    for row in (bundle_rows or [])
                    if str((row or {}).get("created_at") or "").strip()
                ]
                candidate_created_at = max(created_values) if created_values else None

                if settings_store is not None and not bool(settings.get("notification_enabled", True)):
                    skipped += 1
                    skipped_users.append(uid)
                    if not body.dry_run:
                        preview_payload = _build_report_distribution_push_payload(bundle_rows, distribution_key=dist_key)
                        await store.mark_bundle_delivered(
                            user_id=uid,
                            distribution_key=dist_key,
                            bundle_families=[str(x or "").strip() for x in list(preview_payload.get("families") or []) if str(x or "").strip()],
                            payload={
                                "sent_at": _iso_utc(now_utc),
                                "send_status": "suppressed_disabled",
                                "data": dict(preview_payload.get("data") or {}),
                                "settings": settings,
                            },
                        )
                    continue

                if settings_store is not None and not is_bundle_due_for_settings(
                    candidate_created_at=candidate_created_at,
                    settings=settings,
                    now_utc=now_utc,
                ):
                    skipped += 1
                    skipped_users.append(uid)
                    continue

                send_res = await _send_report_distribution_bundle_push(
                    user_id=uid,
                    distribution_key=dist_key,
                    bundle_rows=bundle_rows,
                    dry_run=bool(body.dry_run),
                )
                send_status = str((send_res or {}).get("send_status") or "sent")
                families = [str(x or "").strip() for x in list((send_res or {}).get("bundle_families") or []) if str(x or "").strip()]
                payload_json = {
                    "sent_at": _iso_utc(now_utc),
                    "send_status": send_status,
                    "data": dict((send_res or {}).get("payload") or {}),
                    "settings": settings,
                }
                if not body.dry_run:
                    await store.mark_bundle_delivered(
                        user_id=uid,
                        distribution_key=dist_key,
                        bundle_families=families,
                        payload=payload_json,
                    )
                if send_status == "sent":
                    sent += 1
                    sent_users.append(uid)
                else:
                    skipped += 1
                    skipped_users.append(uid)
            except Exception as exc:
                errors += 1
                if len(error_samples) < 10:
                    error_samples.append(f"{uid}:{dist_key}:{exc}")
                logger.warning(
                    "report_distribution_push failed. user=%s distribution_key=%s err=%s",
                    uid,
                    dist_key,
                    exc,
                )

        return ReportDistributionPushBatchResponse(
            status="ok",
            now_iso=_iso_utc(now_utc),
            processed=processed,
            sent=sent,
            skipped=skipped,
            errors=errors,
            bundles=processed,
            sent_users=sent_users,
            skipped_users=skipped_users,
            error_samples=error_samples,
        )
