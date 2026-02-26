# -*- coding: utf-8 -*-
"""astor_worker.py

Phase 6: ASTOR heavy processing worker (Render Background Worker)
----------------------------------------------------------------

Run:
  python astor_worker.py

Env:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - ASTOR_JOBS_TABLE=astor_jobs
  - ASTOR_WORKER_ID (optional)
  - ASTOR_WORKER_POLL_INTERVAL_SECONDS=1.0
  - ASTOR_WORKER_JOB_TYPES=myprofile_latest_refresh_v1,snapshot_generate_v1,generate_emotion_report_v1   (comma separated)
  - ASTOR_WORKER_LOG_LEVEL=INFO

This worker consumes jobs enqueued by API (e.g., emotion/submit) and executes
heavy tasks out-of-process, improving API stability.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from datetime import datetime, timezone
from typing import List

from astor_job_queue import (
    fetch_next_queued_job,
    claim_job,
    enqueue_job,
    mark_done_if_unchanged,
    requeue,
    mark_failed,
)

# NOTE:
# In your repo, the module is expected to be `astor_myprofile_report.py`.
# (This patch provides an updated version that adds `refresh_myprofile_latest_report`.)
from astor_myprofile_report import refresh_myprofile_latest_report  # type: ignore

# Phase X: material snapshots (central input snapshots)
from astor_material_snapshots import generate_and_store_material_snapshots  # type: ignore

# Phase X+: emotion structure reports (MyWeb weekly/monthly)
from api_myweb_reports import (
    _build_target_period as _myweb_build_target_period,
    _generate_and_save as _myweb_generate_and_save,
)  # type: ignore

# Generation lock (avoid concurrent snapshot generation per user/scope)
from generation_lock import build_lock_key, make_owner_id, release_lock, try_acquire_lock  # type: ignore


def _parse_job_types(raw: str) -> List[str]:
    xs: List[str] = []
    for p in (raw or "").split(","):
        s = p.strip()
        if s:
            xs.append(s)
    return xs



async def _handle_snapshot_generate_v1(*, user_id: str, payload: dict) -> dict:
    """Generate internal/public material snapshots for a user (v1).

    - Uses generation_lock to avoid concurrent runs for same user/scope.
    - Returns a small dict with status for worker flow control.
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    scope = str((payload or {}).get("scope") or "global").strip() or "global"
    trigger = str((payload or {}).get("trigger") or "worker").strip() or "worker"

    # Debounce hint (used only when the worker needs to requeue after an in-flight update)
    try:
        debounce_seconds = int((payload or {}).get("debounce_seconds") or os.getenv("ASTOR_SNAPSHOT_DEBOUNCE_SECONDS", "300") or "300")
    except Exception:
        debounce_seconds = 300

    lock_key = build_lock_key(
        namespace="snapshot",
        user_id=uid,
        report_type=f"{scope}:v1",
        period_start="all",
        period_end="all",
    )
    owner_id = make_owner_id(f"snapshot:{trigger}")

    # Acquire lock (fail-fast, then requeue)
    ttl = int(os.getenv("SNAPSHOT_LOCK_TTL_SECONDS", "180") or "180")
    lock_res = await try_acquire_lock(
        lock_key=lock_key,
        owner_id=owner_id,
        ttl_seconds=max(60, ttl),
        context={"scope": scope, "trigger": trigger},
    )
    if not getattr(lock_res, "acquired", False):
        return {"status": "skipped_locked", "user_id": uid, "scope": scope, "debounce_seconds": debounce_seconds}

    try:
        res = await generate_and_store_material_snapshots(user_id=uid, scope=scope, trigger=trigger)
        res["debounce_seconds"] = debounce_seconds
        return res
    finally:
        try:
            await release_lock(lock_key=lock_key, owner_id=owner_id)
        except Exception:
            pass



async def _handle_generate_emotion_report_v1(*, user_id: str, payload: dict) -> dict:
    """Generate emotion structure reports (MyWeb weekly/monthly) for a user (v1).

    v1 方針:
    - 既存の MyWeb 週報/月報ロジックを利用して生成→myweb_reports へ upsert する。
    - Snapshot を“入力”として使うのは v2 以降（まずは snapshot をトリガー/冪等の基準にする）。
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    types = (payload or {}).get("types") or ["weekly", "monthly"]
    include_astor = bool((payload or {}).get("include_astor", True))

    now_utc = datetime.now(timezone.utc)

    generated = []
    errors = {}
    for t in types:
        rt = str(t or "").strip()
        if not rt:
            continue
        try:
            target = _myweb_build_target_period(rt, now_utc)
            _text, _json, _astor_text, meta = await _myweb_generate_and_save(uid, target, include_astor=include_astor)
            rid = None
            if isinstance(meta, dict):
                rid = meta.get("report_id")
            generated.append({"report_type": rt, "report_id": rid, "status": "ok"})
        except Exception as exc:
            errors[rt] = str(exc)

    if not generated:
        raise RuntimeError(f"generate_emotion_report_v1 failed: {errors}")

    return {"status": "ok", "user_id": uid, "generated": generated, "errors": (errors or None)}
async def _worker_loop() -> None:
    worker_id = (os.getenv("ASTOR_WORKER_ID") or "").strip() or f"astor-worker-{os.getpid()}"
    poll_interval = float(os.getenv("ASTOR_WORKER_POLL_INTERVAL_SECONDS", "1.0") or "1.0")
    job_types = _parse_job_types(os.getenv("ASTOR_WORKER_JOB_TYPES", "myprofile_latest_refresh_v1,snapshot_generate_v1,generate_emotion_report_v1"))

    logger = logging.getLogger("astor_worker")
    logger.info("ASTOR worker started. worker_id=%s job_types=%s poll=%.2fs", worker_id, job_types, poll_interval)

    stop_event = asyncio.Event()

    def _request_stop(*_args):  # type: ignore
        try:
            stop_event.set()
        except Exception:
            pass

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _request_stop)
            except NotImplementedError:
                # Some environments may not support add_signal_handler (e.g., Windows)
                signal.signal(sig, lambda *_: _request_stop())
    except Exception:
        pass

    while not stop_event.is_set():
        job = await fetch_next_queued_job(job_types=job_types)
        if not job:
            await asyncio.sleep(max(0.1, poll_interval))
            continue

        claimed = await claim_job(job_key=job.job_key, worker_id=worker_id, attempts=job.attempts)
        if not claimed:
            # someone else claimed; try again
            await asyncio.sleep(0)
            continue

        # Process claimed job
        try:
            if claimed.job_type == "myprofile_latest_refresh_v1":
                res = await refresh_myprofile_latest_report(
                    user_id=claimed.user_id,
                    trigger=(claimed.payload or {}).get("trigger") or "worker",
                    force=bool((claimed.payload or {}).get("force", False)),
                )

                status = str((res or {}).get("status") or "")
                if status == "skipped_locked":
                    # Another generator is running; retry shortly.
                    await requeue(job_key=claimed.job_key, worker_id=worker_id, error="locked", delay_seconds=10)
                else:
                    done = await mark_done_if_unchanged(
                        job_key=claimed.job_key,
                        worker_id=worker_id,
                        expected_updated_at=claimed.updated_at,
                    )
                    if not done:
                        # The job was updated while running; queue it again for a fresh run.
                        await requeue(
                            job_key=claimed.job_key,
                            worker_id=worker_id,
                            error="updated_while_running",
                            delay_seconds=1,
                        )
                logger.info("job done. key=%s type=%s user=%s res=%s", claimed.job_key, claimed.job_type, claimed.user_id, res)
            elif claimed.job_type == "snapshot_generate_v1":
                # Central material snapshots (internal/public). Debounced via run_after and requeue delay.
                snap_res = await _handle_snapshot_generate_v1(user_id=claimed.user_id, payload=(claimed.payload or {}))
                snap_status = str((snap_res or {}).get("status") or "")
                if snap_status == "skipped_locked":
                    await requeue(job_key=claimed.job_key, worker_id=worker_id, error="locked", delay_seconds=10)
                else:
                    done = await mark_done_if_unchanged(
                        job_key=claimed.job_key,
                        worker_id=worker_id,
                        expected_updated_at=claimed.updated_at,
                    )
                    if not done:
                        # Updated while running: apply debounce delay (default 5min) before re-run.
                        try:
                            delay = int((snap_res or {}).get("debounce_seconds") or 300)
                        except Exception:
                            delay = 300
                        await requeue(
                            job_key=claimed.job_key,
                            worker_id=worker_id,
                            error="updated_while_running",
                            delay_seconds=max(1, delay),
                        )
                    else:
                        # Snapshot committed without concurrent updates -> enqueue downstream generation jobs.
                        try:
                            internal = (snap_res or {}).get("internal") or {}
                            public = (snap_res or {}).get("public") or {}
                            if bool(internal.get("inserted")) or bool(public.get("inserted")):
                                internal_hash = str(internal.get("source_hash") or "")
                                await enqueue_job(
                                    job_key=f"emotion_report_refresh:{claimed.user_id}",
                                    job_type="generate_emotion_report_v1",
                                    user_id=claimed.user_id,
                                    payload={
                                        "trigger": "snapshot_generate_v1",
                                        "requested_at": (claimed.payload or {}).get("requested_at"),
                                        "scope": str((claimed.payload or {}).get("scope") or "global"),
                                        "source_hash": internal_hash,
                                        "types": ["weekly", "monthly"],
                                        "include_astor": True,
                                    },
                                    priority=10,
                                )
                        except Exception as exc:
                            logger.error("Downstream enqueue failed: %s", exc)
                logger.info("job done. key=%s type=%s user=%s res=%s", claimed.job_key, claimed.job_type, claimed.user_id, snap_res)
            elif claimed.job_type == "generate_emotion_report_v1":
                gen_res = await _handle_generate_emotion_report_v1(user_id=claimed.user_id, payload=(claimed.payload or {}))
                done = await mark_done_if_unchanged(
                    job_key=claimed.job_key,
                    worker_id=worker_id,
                    expected_updated_at=claimed.updated_at,
                )
                if not done:
                    # The job was updated while running; queue it again for a fresh run.
                    await requeue(
                        job_key=claimed.job_key,
                        worker_id=worker_id,
                        error="updated_while_running",
                        delay_seconds=1,
                    )
                logger.info("job done. key=%s type=%s user=%s res=%s", claimed.job_key, claimed.job_type, claimed.user_id, gen_res)


            else:
                await mark_failed(job_key=claimed.job_key, worker_id=worker_id, error=f"Unknown job_type: {claimed.job_type}")
                logger.warning("unknown job_type. key=%s type=%s", claimed.job_key, claimed.job_type)
        except Exception as exc:
            # Retry with backoff, then fail
            try:
                attempts = int(claimed.attempts or 0)
                max_attempts = int(claimed.max_attempts or 0) or 8
                if attempts >= max_attempts:
                    await mark_failed(job_key=claimed.job_key, worker_id=worker_id, error=str(exc))
                else:
                    # simple backoff: 5s, 10s, 20s, 40s... capped
                    delay = min(120, max(5, 5 * (2 ** max(0, attempts - 1))))
                    await requeue(job_key=claimed.job_key, worker_id=worker_id, error=str(exc), delay_seconds=int(delay))
            except Exception:
                pass
            logger.exception("job failed. key=%s type=%s err=%s", claimed.job_key, claimed.job_type, exc)

    logger.info("ASTOR worker stopping.")


def main() -> None:
    log_level = (os.getenv("ASTOR_WORKER_LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    asyncio.run(_worker_loop())


if __name__ == "__main__":
    main()
