# -*- coding: utf-8 -*-
"""Shared helper for enqueuing ASTOR ranking board refresh jobs.

Purpose
-------
入力 API / operational API から、Ranking 系の global board 再生成ジョブ
`refresh_ranking_board_v1` を安全に enqueue するための共通ヘルパー。

Design
------
- best-effort: enqueue に失敗しても API 成功/失敗は巻き込まない
- coalescing: 同一 metric の board refresh は job_key で 1 本へ自然に集約
- debounce: 入力連打を吸収し、global ranking の無駄な再生成を抑える
- global board: user_id は「誰の操作で汚れたか」の監査用。集約の本体は metric_key
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger("astor_ranking_enqueue")


def _env_truthy(name: str, default: str = "true") -> bool:
    value = os.getenv(name, default)
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


RANKING_BOARD_REFRESH_JOB_TYPE = "refresh_ranking_board_v1"
RANKING_BOARD_REFRESH_JOB_KEY_PREFIX = "ranking_board_refresh_v1"

ASTOR_WORKER_QUEUE_ENABLED = _env_truthy("ASTOR_WORKER_QUEUE_ENABLED", "false")
ASTOR_RANKING_ENQUEUE_ENABLED = _env_truthy("ASTOR_RANKING_ENQUEUE_ENABLED", "true")

try:
    ASTOR_RANKING_DEBOUNCE_SECONDS = int(
        os.getenv("ASTOR_RANKING_DEBOUNCE_SECONDS", "300") or "300"
    )
except Exception:
    ASTOR_RANKING_DEBOUNCE_SECONDS = 300


async def enqueue_ranking_board_refresh(
    *,
    metric_key: str,
    user_id: str,
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """Enqueue a global ranking board refresh job for one metric.

    Parameters
    ----------
    metric_key:
        Ranking metric identifier, e.g. ``input_count`` or ``login_streak``.
    user_id:
        User who triggered the refresh. This is used for auditability only;
        coalescing is done by metric-specific job_key.
    trigger:
        Source event name, e.g. ``emotion_submit``.
    requested_at:
        ISO timestamp of the originating event.
    debounce:
        Whether to delay the job slightly to absorb bursts.
    debounce_seconds:
        Override debounce duration in seconds.
    priority:
        Job queue priority. Higher runs sooner.
    extra_payload:
        Optional extra payload merged into the job payload.

    Returns
    -------
    bool
        True when enqueue was attempted successfully, False when skipped or failed.
    """
    mk = str(metric_key or "").strip()
    uid = str(user_id or "").strip()
    trig = str(trigger or "").strip()

    if not mk:
        logger.warning("ranking enqueue skipped: empty metric_key")
        return False
    if not uid:
        logger.warning("ranking enqueue skipped: empty user_id (metric_key=%s)", mk)
        return False
    if not trig:
        logger.warning(
            "ranking enqueue skipped: empty trigger (metric_key=%s user_id=%s)",
            mk,
            uid,
        )
        return False

    if not ASTOR_WORKER_QUEUE_ENABLED:
        logger.debug(
            "ranking enqueue skipped: ASTOR_WORKER_QUEUE_ENABLED=false (metric_key=%s user_id=%s trigger=%s)",
            mk,
            uid,
            trig,
        )
        return False

    if not ASTOR_RANKING_ENQUEUE_ENABLED:
        logger.debug(
            "ranking enqueue skipped: ASTOR_RANKING_ENQUEUE_ENABLED=false (metric_key=%s user_id=%s trigger=%s)",
            mk,
            uid,
            trig,
        )
        return False

    now_dt = datetime.now(timezone.utc).replace(microsecond=0)
    now_iso = now_dt.isoformat().replace("+00:00", "Z")
    req_at = str(requested_at or now_iso).strip() or now_iso

    payload: Dict[str, Any] = {}
    if isinstance(extra_payload, dict) and extra_payload:
        payload.update(extra_payload)
    payload.update(
        {
            "metric_key": mk,
            "trigger": trig,
            "requested_at": req_at,
            "phase": "rpc_kernel_v1",
        }
    )

    run_after_iso: Optional[str] = None
    if debounce:
        try:
            delay = int(
                debounce_seconds
                if debounce_seconds is not None
                else ASTOR_RANKING_DEBOUNCE_SECONDS
            )
        except Exception:
            delay = ASTOR_RANKING_DEBOUNCE_SECONDS
        delay = max(1, int(delay or ASTOR_RANKING_DEBOUNCE_SECONDS))
        payload["debounce_seconds"] = delay
        run_after_iso = (now_dt + timedelta(seconds=delay)).isoformat().replace(
            "+00:00", "Z"
        )

    try:
        # Local import: keep module light and avoid importing Supabase config on startup.
        from astor_job_queue import enqueue_job

        await enqueue_job(
            job_key=f"{RANKING_BOARD_REFRESH_JOB_KEY_PREFIX}:{mk}",
            job_type=RANKING_BOARD_REFRESH_JOB_TYPE,
            user_id=uid,
            payload=payload,
            priority=int(priority or 18),
            run_after_iso=run_after_iso,
        )
        return True
    except Exception as exc:
        logger.error(
            "ranking enqueue failed (metric_key=%s user_id=%s trigger=%s): %s",
            mk,
            uid,
            trig,
            exc,
        )
        return False


async def enqueue_ranking_board_refresh_many(
    *,
    metric_keys: Iterable[str],
    user_id: str,
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """Enqueue ranking board refresh jobs for multiple metrics.

    Duplicate / empty metric keys are ignored. The same ``requested_at`` and
    ``trigger`` are reused for all metrics so a single API event can fan out
    into multiple global board refresh requests.
    """
    results: Dict[str, bool] = {}
    seen = set()

    for raw_key in metric_keys or []:
        mk = str(raw_key or "").strip()
        if not mk or mk in seen:
            continue
        seen.add(mk)
        results[mk] = await enqueue_ranking_board_refresh(
            metric_key=mk,
            user_id=user_id,
            trigger=trigger,
            requested_at=requested_at,
            debounce=debounce,
            debounce_seconds=debounce_seconds,
            priority=priority,
            extra_payload=extra_payload,
        )
    return results


__all__ = [
    "RANKING_BOARD_REFRESH_JOB_TYPE",
    "RANKING_BOARD_REFRESH_JOB_KEY_PREFIX",
    "ASTOR_WORKER_QUEUE_ENABLED",
    "ASTOR_RANKING_ENQUEUE_ENABLED",
    "ASTOR_RANKING_DEBOUNCE_SECONDS",
    "enqueue_ranking_board_refresh",
    "enqueue_ranking_board_refresh_many",
]
