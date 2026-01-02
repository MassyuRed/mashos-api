# -*- coding: utf-8 -*-
"""cron_run_store.py

Phase11+ : Cron結果をSupabaseテーブルに永続化（ダッシュボード化）
------------------------------------------------------------

目的
- /cron の実行結果（generated / exists / errors / duration 等）を Supabase に保存し、
  後からダッシュボード/運用で追えるようにする。
- 失敗時も best-effort で記録（記録失敗がCron本体を落とさない）。

設計
- PostgREST 互換の upsert（on_conflict=run_id）を使う。
- service_role で書く前提（RLSは有効化するがポリシーは作らない）。
- エラーサンプルは最大N件に丸める（データ肥大防止）。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from api_emotion_submit import _ensure_supabase_config

try:
    from observability import elapsed_ms, log_event, log_alert, monotonic_ms
except Exception:  # pragma: no cover
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


logger = logging.getLogger("cron_run_store")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

CRON_RUNS_TABLE = (os.getenv("CRON_RUNS_TABLE", "cron_runs") or "cron_runs").strip()

CRON_RUNS_ENABLED = (os.getenv("CRON_RUNS_ENABLED", "true").strip().lower() != "false")
CRON_RUNS_TIMEOUT_SECONDS = float(os.getenv("CRON_RUNS_TIMEOUT_SECONDS", "4.0") or "4.0")

try:
    CRON_RUNS_SAVE_ERROR_SAMPLES_MAX = int(os.getenv("CRON_RUNS_SAVE_ERROR_SAMPLES_MAX", "20") or "20")
except Exception:
    CRON_RUNS_SAVE_ERROR_SAMPLES_MAX = 20


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


async def _upsert_row(payload: Dict[str, Any], *, run_id: Optional[str] = None, job: Optional[str] = None) -> None:
    """Upsert a cron_runs row (best-effort)."""
    if not CRON_RUNS_ENABLED:
        return
    _ensure_supabase_config()
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return

    url = f"{SUPABASE_URL}/rest/v1/{CRON_RUNS_TABLE}"
    params = {"on_conflict": "run_id"}
    headers = _sb_headers(prefer="resolution=merge-duplicates,return=minimal")

    start_ms = monotonic_ms()
    try:
        async with httpx.AsyncClient(timeout=CRON_RUNS_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, params=params, headers=headers, json=payload)
        dur = elapsed_ms(start_ms)

        if resp.status_code not in (200, 201, 204):
            log_event(
                logger,
                "cron_runs_upsert_failed",
                level="warning",
                job=job,
                run_id=run_id,
                status_code=resp.status_code,
                duration_ms=dur,
                body=resp.text[:500],
            )
            # Alert marker for dashboards/ops
            log_alert(
                logger,
                "CRON_RUNS_UPSERT_FAILED",
                level="warning",
                job=job,
                run_id=run_id,
                status_code=resp.status_code,
            )
            return

        log_event(
            logger,
            "cron_runs_upsert_ok",
            level="info",
            job=job,
            run_id=run_id,
            duration_ms=dur,
        )
    except Exception as exc:
        log_event(
            logger,
            "cron_runs_upsert_exception",
            level="warning",
            job=job,
            run_id=run_id,
            error=str(exc),
            exc_type=type(exc).__name__,
        )
        log_alert(
            logger,
            "CRON_RUNS_UPSERT_EXCEPTION",
            level="warning",
            job=job,
            run_id=run_id,
            exc_type=type(exc).__name__,
        )


def _trim_error_samples(samples: Optional[List[str]]) -> List[str]:
    if not samples:
        return []
    out: List[str] = []
    for s in samples:
        if s is None:
            continue
        out.append(str(s)[:400])
        if len(out) >= max(0, CRON_RUNS_SAVE_ERROR_SAMPLES_MAX):
            break
    return out


async def cron_run_start(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    offset: int,
    limit: int,
    shard_total: int,
    shard_index: int,
    force: bool,
    dry_run: bool,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a cron run start (status=running)."""
    t = _utc_now()
    payload: Dict[str, Any] = {
        "run_id": run_id,
        "job": job,
        "status": "running",
        "started_at": _iso_utc(t),
        "now_iso": now_iso,
        "offset": offset,
        "limit": limit,
        "shard_total": shard_total,
        "shard_index": shard_index,
        "force": bool(force),
        "dry_run": bool(dry_run),
        "meta": meta or {},
        "updated_at": _iso_utc(t),
    }
    await _upsert_row(payload, run_id=run_id, job=job)


async def cron_run_complete(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    offset: int,
    limit: int,
    shard_total: int,
    shard_index: int,
    processed: int,
    generated: int,
    exists: int,
    errors: int,
    duration_ms: int,
    done: bool,
    next_offset: Optional[int],
    error_samples: Optional[List[str]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Record cron run completion (status=ok|error)."""
    t = _utc_now()
    status = "ok" if int(errors or 0) <= 0 else "error"
    payload: Dict[str, Any] = {
        "run_id": run_id,
        "job": job,
        "status": status,
        "finished_at": _iso_utc(t),
        "duration_ms": int(duration_ms or 0),
        "now_iso": now_iso,
        "offset": offset,
        "limit": limit,
        "shard_total": shard_total,
        "shard_index": shard_index,
        "processed": int(processed or 0),
        "generated": int(generated or 0),
        "exists": int(exists or 0),
        "errors": int(errors or 0),
        "done": bool(done),
        "next_offset": (int(next_offset) if next_offset is not None else None),
        "error_samples": _trim_error_samples(error_samples),
        "meta": meta or {},
        "updated_at": _iso_utc(t),
    }
    await _upsert_row(payload, run_id=run_id, job=job)


async def cron_run_failed(
    *,
    job: str,
    run_id: str,
    now_iso: str,
    offset: int,
    limit: int,
    shard_total: int,
    shard_index: int,
    duration_ms: int,
    error: str,
    exc_type: str,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Record cron run failure (status=failed)."""
    t = _utc_now()
    payload: Dict[str, Any] = {
        "run_id": run_id,
        "job": job,
        "status": "failed",
        "finished_at": _iso_utc(t),
        "duration_ms": int(duration_ms or 0),
        "now_iso": now_iso,
        "offset": offset,
        "limit": limit,
        "shard_total": shard_total,
        "shard_index": shard_index,
        "errors": 1,
        "error_samples": _trim_error_samples([f"{exc_type}: {error}"]),
        "meta": {"exc_type": exc_type, **(meta or {})},
        "updated_at": _iso_utc(t),
    }
    await _upsert_row(payload, run_id=run_id, job=job)
