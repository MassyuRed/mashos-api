# -*- coding: utf-8 -*-
"""astor_job_queue.py

Phase 6: DB-backed job queue for ASTOR heavy processing
------------------------------------------------------

Why
- API プロセス内で重い処理（例: MyProfile latest レポート生成）を実行すると、
  リクエスト数が増えた時に CPU/メモリが詰まりやすく、全体が不安定になりやすい。
- いったん最小実装として「Supabase(Postgres) のテーブルをキューにする」方式で分離する。

Design (minimal, no RPC)
- Table: public.astor_jobs (service_role で読み書き)
- API: enqueue は job_key をユニークにして「同種ジョブを自然に潰す (coalesce)」
- Worker: 2-step claim
    1) select queued job
    2) patch status=running (status=queued 条件付き) で claim
    3) process
    4) patch done / queued / failed

Important: running 中に enqueue が来た場合
- enqueue は status を勝手に queued に戻さない（= 二重実行を避ける）
- 代わりに payload と updated_at だけ更新する
- Worker は「claim 時点の updated_at と一致する場合のみ done にする」
  一致しない (= 実行中に更新が入った) 場合は queued に戻して再実行できる
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from supabase_client import ensure_supabase_config, sb_get, sb_post, sb_patch

logger = logging.getLogger("astor_job_queue")

JOBS_TABLE = (os.getenv("ASTOR_JOBS_TABLE", "astor_jobs") or "astor_jobs").strip() or "astor_jobs"


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _in_list(values: List[str]) -> str:
    """PostgREST in.(...) filter with quotes."""
    xs: List[str] = []
    for v in values:
        s = str(v or "").replace('"', '\"')
        xs.append(f'"{s}"')
    return f"in.({','.join(xs)})"


@dataclass
class AstorJob:
    job_key: str
    job_type: str
    user_id: str
    payload: Dict[str, Any]
    status: str
    priority: int
    run_after: Optional[str]
    attempts: int
    max_attempts: int
    worker_id: Optional[str]
    updated_at: Optional[str]
    started_at: Optional[str]


def _row_to_job(row: Dict[str, Any]) -> AstorJob:
    return AstorJob(
        job_key=str(row.get("job_key") or ""),
        job_type=str(row.get("job_type") or ""),
        user_id=str(row.get("user_id") or ""),
        payload=row.get("payload") if isinstance(row.get("payload"), dict) else {},
        status=str(row.get("status") or ""),
        priority=int(row.get("priority") or 0),
        run_after=row.get("run_after"),
        attempts=int(row.get("attempts") or 0),
        max_attempts=int(row.get("max_attempts") or 0),
        worker_id=row.get("worker_id"),
        updated_at=row.get("updated_at"),
        started_at=row.get("started_at"),
    )


async def enqueue_job(
    *,
    job_key: str,
    job_type: str,
    user_id: str,
    payload: Dict[str, Any],
    priority: int = 0,
    run_after_iso: Optional[str] = None,
    max_attempts: int = 8,
) -> None:
    """Enqueue a job (coalescing by job_key).

    Behavior:
    - If job exists and status == running:
        - update payload / meta (updated_at) only (do NOT flip to queued)
    - Else if job exists (queued/done/failed):
        - set status=queued and run_after=now
    - Else:
        - insert new row (defaults to queued)
    """
    ensure_supabase_config()

    jk = str(job_key or "").strip()
    jt = str(job_type or "").strip()
    uid = str(user_id or "").strip()
    if not jk or not jt or not uid:
        raise ValueError("job_key/job_type/user_id are required")

    now_iso = _now_iso_z()
    run_after = str(run_after_iso or now_iso)

    # 1) If running: update payload only
    patch_running = {
        "job_type": jt,
        "user_id": uid,
        "payload": payload or {},
        "priority": int(priority or 0),
        "max_attempts": int(max_attempts or 8),
        "updated_at": now_iso,
        # keep status=running, keep run_after as-is
    }
    resp = await sb_patch(
        f"/rest/v1/{JOBS_TABLE}",
        json=patch_running,
        params={"job_key": f"eq.{jk}", "status": "eq.running"},
        prefer="return=representation",
        timeout=6.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"enqueue_job(patch running) failed: {resp.status_code} {(resp.text or '')[:800]}")
    try:
        data = resp.json() if resp.status_code == 200 else []
    except Exception:
        data = []
    if isinstance(data, list) and len(data) > 0:
        return

    # 2) Not running: flip to queued
    patch_queue = {
        "job_type": jt,
        "user_id": uid,
        "payload": payload or {},
        "status": "queued",
        "priority": int(priority or 0),
        "run_after": run_after,
        "max_attempts": int(max_attempts or 8),
        "last_error": None,
        "updated_at": now_iso,
    }
    resp2 = await sb_patch(
        f"/rest/v1/{JOBS_TABLE}",
        json=patch_queue,
        params={"job_key": f"eq.{jk}", "status": "neq.running"},
        prefer="return=representation",
        timeout=6.0,
    )
    if resp2.status_code not in (200, 204):
        raise RuntimeError(f"enqueue_job(patch queued) failed: {resp2.status_code} {(resp2.text or '')[:800]}")
    try:
        data2 = resp2.json() if resp2.status_code == 200 else []
    except Exception:
        data2 = []
    if isinstance(data2, list) and len(data2) > 0:
        return

    # 3) Insert (upsert-safe). Do NOT include status to avoid flipping running -> queued on race.
    row = {
        "job_key": jk,
        "job_type": jt,
        "user_id": uid,
        "payload": payload or {},
        "priority": int(priority or 0),
        "run_after": run_after,
        "max_attempts": int(max_attempts or 8),
        "updated_at": now_iso,
    }
    resp3 = await sb_post(
        f"/rest/v1/{JOBS_TABLE}",
        json=row,
        params={"on_conflict": "job_key"},
        prefer="resolution=merge-duplicates,return=minimal",
        timeout=6.0,
    )
    if resp3.status_code not in (200, 201, 204):
        raise RuntimeError(f"enqueue_job(insert) failed: {resp3.status_code} {(resp3.text or '')[:800]}")


async def fetch_next_queued_job(
    *,
    job_types: Optional[List[str]] = None,
) -> Optional[AstorJob]:
    """Fetch one queued job (does NOT claim)."""
    ensure_supabase_config()
    now_iso = _now_iso_z()

    params: Dict[str, str] = {
        "select": "job_key,job_type,user_id,payload,status,priority,run_after,attempts,max_attempts,worker_id,updated_at,started_at",
        "status": "eq.queued",
        "run_after": f"lte.{now_iso}",
        "order": "priority.desc,updated_at.asc",
        "limit": "1",
    }
    if job_types:
        params["job_type"] = _in_list(job_types)

    resp = await sb_get(f"/rest/v1/{JOBS_TABLE}", params=params, timeout=6.0)
    if resp.status_code not in (200, 206):
        logger.error("fetch_next_queued_job failed: %s %s", resp.status_code, (resp.text or "")[:500])
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    if not (isinstance(data, list) and data and isinstance(data[0], dict)):
        return None
    return _row_to_job(data[0])


async def claim_job(
    *,
    job_key: str,
    worker_id: str,
    attempts: int,
) -> Optional[AstorJob]:
    """Try to claim the job by patching status queued -> running.

    Returns the claimed job row if succeeded, else None.
    """
    ensure_supabase_config()
    jk = str(job_key or "").strip()
    if not jk:
        return None

    now_iso = _now_iso_z()
    patch = {
        "status": "running",
        "worker_id": str(worker_id or "").strip() or None,
        "started_at": now_iso,
        "updated_at": now_iso,
        "attempts": int(attempts or 0) + 1,
    }

    resp = await sb_patch(
        f"/rest/v1/{JOBS_TABLE}",
        json=patch,
        params={"job_key": f"eq.{jk}", "status": "eq.queued"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        logger.error("claim_job failed: %s %s", resp.status_code, (resp.text or "")[:500])
        return None
    if resp.status_code == 204:
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    if not (isinstance(data, list) and data and isinstance(data[0], dict)):
        return None
    return _row_to_job(data[0])


async def mark_done_if_unchanged(
    *,
    job_key: str,
    worker_id: Optional[str] = None,
    expected_updated_at: Optional[str] = None,
) -> bool:
    """Mark done only if updated_at matches the expected value.

    This prevents clobbering an enqueue that happened while the job was running.
    Returns True if updated (done), False if no row matched the condition.
    """
    ensure_supabase_config()
    jk = str(job_key or "").strip()
    if not jk:
        return False
    now_iso = _now_iso_z()

    params: Dict[str, str] = {"job_key": f"eq.{jk}", "status": "eq.running"}
    if expected_updated_at:
        params["updated_at"] = f"eq.{expected_updated_at}"

    patch = {
        "status": "done",
        "worker_id": str(worker_id or "").strip() or None,
        "finished_at": now_iso,
        "last_error": None,
        "updated_at": now_iso,
        "run_after": now_iso,
    }

    resp = await sb_patch(
        f"/rest/v1/{JOBS_TABLE}",
        json=patch,
        params=params,
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        logger.error("mark_done_if_unchanged failed: %s %s", resp.status_code, (resp.text or "")[:500])
        return False
    if resp.status_code == 204:
        return False
    try:
        data = resp.json()
    except Exception:
        return False
    return bool(isinstance(data, list) and len(data) > 0)


async def requeue(
    *,
    job_key: str,
    worker_id: Optional[str] = None,
    error: Optional[str] = None,
    delay_seconds: int = 15,
) -> None:
    ensure_supabase_config()
    jk = str(job_key or "").strip()
    if not jk:
        return
    now_dt = datetime.now(timezone.utc).replace(microsecond=0)
    run_after_dt = now_dt + timedelta(seconds=max(1, int(delay_seconds or 15)))
    now_iso = now_dt.isoformat().replace("+00:00", "Z")
    run_after_iso = run_after_dt.isoformat().replace("+00:00", "Z")

    patch = {
        "status": "queued",
        "worker_id": str(worker_id or "").strip() or None,
        "run_after": run_after_iso,
        "last_error": (str(error)[:1500] if error else None),
        "updated_at": now_iso,
    }
    resp = await sb_patch(
        f"/rest/v1/{JOBS_TABLE}",
        json=patch,
        params={"job_key": f"eq.{jk}"},
        prefer="return=minimal",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        logger.error("requeue failed: %s %s", resp.status_code, (resp.text or "")[:500])


async def mark_failed(
    *,
    job_key: str,
    worker_id: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    ensure_supabase_config()
    jk = str(job_key or "").strip()
    if not jk:
        return
    now_iso = _now_iso_z()
    patch = {
        "status": "failed",
        "worker_id": str(worker_id or "").strip() or None,
        "finished_at": now_iso,
        "last_error": (str(error)[:1500] if error else None),
        "updated_at": now_iso,
    }
    resp = await sb_patch(
        f"/rest/v1/{JOBS_TABLE}",
        json=patch,
        params={"job_key": f"eq.{jk}"},
        prefer="return=minimal",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        logger.error("mark_failed failed: %s %s", resp.status_code, (resp.text or "")[:500])
