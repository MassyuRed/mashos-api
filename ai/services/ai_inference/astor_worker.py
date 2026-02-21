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
  - ASTOR_WORKER_JOB_TYPES=myprofile_latest_refresh_v1   (comma separated)
  - ASTOR_WORKER_LOG_LEVEL=INFO

This worker consumes jobs enqueued by API (e.g., emotion/submit) and executes
heavy tasks out-of-process, improving API stability.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import List

from astor_job_queue import (
    fetch_next_queued_job,
    claim_job,
    mark_done_if_unchanged,
    requeue,
    mark_failed,
)

# NOTE:
# In your repo, the module is expected to be `astor_myprofile_report.py`.
# (This patch provides an updated version that adds `refresh_myprofile_latest_report`.)
from astor_myprofile_report import refresh_myprofile_latest_report  # type: ignore


def _parse_job_types(raw: str) -> List[str]:
    xs: List[str] = []
    for p in (raw or "").split(","):
        s = p.strip()
        if s:
            xs.append(s)
    return xs


async def _worker_loop() -> None:
    worker_id = (os.getenv("ASTOR_WORKER_ID") or "").strip() or f"astor-worker-{os.getpid()}"
    poll_interval = float(os.getenv("ASTOR_WORKER_POLL_INTERVAL_SECONDS", "1.0") or "1.0")
    job_types = _parse_job_types(os.getenv("ASTOR_WORKER_JOB_TYPES", "myprofile_latest_refresh_v1"))

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
