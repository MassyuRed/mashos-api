# -*- coding: utf-8 -*-
"""Shared helper for enqueuing ASTOR account status refresh jobs.

Purpose
-------
入力 API / operational API から、Account Status 系の per-user summary 再生成ジョブ
`refresh_account_status_v1` を安全に enqueue するための共通ヘルパー。

Design
------
- best-effort: enqueue に失敗しても API 成功/失敗は巻き込まない
- coalescing: 同一 target_user_id の summary refresh は job_key で 1 本へ自然に集約
- debounce: 入力連打を吸収し、不要な再生成を抑える
- per-user summary: job の user_id は target_user_id を採用し、worker 側でそのまま扱える
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger("astor_account_status_enqueue")


def _env_truthy(name: str, default: str = "true") -> bool:
    value = os.getenv(name, default)
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


ACCOUNT_STATUS_REFRESH_JOB_TYPE = "refresh_account_status_v1"
ACCOUNT_STATUS_REFRESH_JOB_KEY_PREFIX = "account_status_refresh_v1"

ASTOR_WORKER_QUEUE_ENABLED = _env_truthy("ASTOR_WORKER_QUEUE_ENABLED", "false")
ASTOR_ACCOUNT_STATUS_ENQUEUE_ENABLED = _env_truthy(
    "ASTOR_ACCOUNT_STATUS_ENQUEUE_ENABLED",
    "true",
)

try:
    ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS = int(
        os.getenv("ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS", "300") or "300"
    )
except Exception:
    ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS = 300


async def enqueue_account_status_refresh(
    *,
    target_user_id: str,
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    actor_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """Enqueue an Account Status refresh job for one target user.

    Parameters
    ----------
    target_user_id:
        User whose account status summary should be regenerated.
    trigger:
        Source event name, e.g. ``emotion_submit`` or ``qna_view``.
    requested_at:
        ISO timestamp of the originating event.
    debounce:
        Whether to delay the job slightly to absorb bursts.
    debounce_seconds:
        Override debounce duration in seconds.
    priority:
        Job queue priority. Higher runs sooner.
    actor_user_id:
        Optional actor who caused the target summary to become stale.
        Useful for auditability when the target differs from the viewer,
        e.g. qna view / resonance / discovery events.
    extra_payload:
        Optional extra payload merged into the job payload.

    Returns
    -------
    bool
        True when enqueue was attempted successfully, False when skipped or failed.
    """
    target_uid = str(target_user_id or "").strip()
    trig = str(trigger or "").strip()
    actor_uid = str(actor_user_id or "").strip() or None

    if not target_uid:
        logger.warning("account status enqueue skipped: empty target_user_id")
        return False
    if not trig:
        logger.warning(
            "account status enqueue skipped: empty trigger (target_user_id=%s)",
            target_uid,
        )
        return False

    if not ASTOR_WORKER_QUEUE_ENABLED:
        logger.debug(
            "account status enqueue skipped: ASTOR_WORKER_QUEUE_ENABLED=false (target_user_id=%s trigger=%s)",
            target_uid,
            trig,
        )
        return False

    if not ASTOR_ACCOUNT_STATUS_ENQUEUE_ENABLED:
        logger.debug(
            "account status enqueue skipped: ASTOR_ACCOUNT_STATUS_ENQUEUE_ENABLED=false (target_user_id=%s trigger=%s)",
            target_uid,
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
            "target_user_id": target_uid,
            "trigger": trig,
            "requested_at": req_at,
            "phase": "rpc_kernel_v1",
        }
    )
    if actor_uid:
        payload["actor_user_id"] = actor_uid

    run_after_iso: Optional[str] = None
    if debounce:
        try:
            delay = int(
                debounce_seconds
                if debounce_seconds is not None
                else ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS
            )
        except Exception:
            delay = ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS
        delay = max(1, int(delay or ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS))
        payload["debounce_seconds"] = delay
        run_after_iso = (now_dt + timedelta(seconds=delay)).isoformat().replace(
            "+00:00", "Z"
        )

    try:
        # Local import: keep module light and avoid importing Supabase config on startup.
        from astor_job_queue import enqueue_job

        await enqueue_job(
            job_key=f"{ACCOUNT_STATUS_REFRESH_JOB_KEY_PREFIX}:{target_uid}",
            job_type=ACCOUNT_STATUS_REFRESH_JOB_TYPE,
            user_id=target_uid,
            payload=payload,
            priority=int(priority or 18),
            run_after_iso=run_after_iso,
        )
        return True
    except Exception as exc:
        logger.error(
            "account status enqueue failed (target_user_id=%s trigger=%s actor_user_id=%s): %s",
            target_uid,
            trig,
            actor_uid or "",
            exc,
        )
        return False


async def enqueue_account_status_refresh_many(
    *,
    target_user_ids: Iterable[str],
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    actor_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """Enqueue Account Status refresh jobs for multiple target users.

    Duplicate / empty target_user_ids are ignored. The same ``requested_at`` and
    ``trigger`` are reused for all targets so a single API event can fan out
    into multiple per-user summary refresh requests.
    """
    results: Dict[str, bool] = {}
    seen = set()

    for raw_target in target_user_ids or []:
        target_uid = str(raw_target or "").strip()
        if not target_uid or target_uid in seen:
            continue
        seen.add(target_uid)
        results[target_uid] = await enqueue_account_status_refresh(
            target_user_id=target_uid,
            trigger=trigger,
            requested_at=requested_at,
            debounce=debounce,
            debounce_seconds=debounce_seconds,
            priority=priority,
            actor_user_id=actor_user_id,
            extra_payload=extra_payload,
        )
    return results


__all__ = [
    "ACCOUNT_STATUS_REFRESH_JOB_TYPE",
    "ACCOUNT_STATUS_REFRESH_JOB_KEY_PREFIX",
    "ASTOR_WORKER_QUEUE_ENABLED",
    "ASTOR_ACCOUNT_STATUS_ENQUEUE_ENABLED",
    "ASTOR_ACCOUNT_STATUS_DEBOUNCE_SECONDS",
    "enqueue_account_status_refresh",
    "enqueue_account_status_refresh_many",
]
