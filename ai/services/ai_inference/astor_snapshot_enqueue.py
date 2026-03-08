# -*- coding: utf-8 -*-
"""Shared helper for enqueuing ASTOR material snapshot refresh jobs.

Purpose
-------
Create / DeepInsight / QNA などの入力 API から、中央材料庁の
`snapshot_generate_v1` を安全に enqueue するための共通ヘルパー。

Design
------
- best-effort: enqueue に失敗しても API 成功/失敗は巻き込まない
- coalescing: 同一 user の global snapshot は job_key で自然に 1 本へ集約
- debounce: 通常入力は少し遅延させて連打を吸収する
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("astor_snapshot_enqueue")


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


ASTOR_WORKER_QUEUE_ENABLED = _env_truthy("ASTOR_WORKER_QUEUE_ENABLED", "false")
ASTOR_SNAPSHOT_ENQUEUE_ENABLED = _env_truthy("ASTOR_SNAPSHOT_ENQUEUE_ENABLED", "true")

try:
    ASTOR_SNAPSHOT_DEBOUNCE_SECONDS = int(
        os.getenv("ASTOR_SNAPSHOT_DEBOUNCE_SECONDS", "300") or "300"
    )
except Exception:
    ASTOR_SNAPSHOT_DEBOUNCE_SECONDS = 300


async def enqueue_global_snapshot_refresh(
    *,
    user_id: str,
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 20,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """Enqueue `snapshot_generate_v1` for the user's global material snapshot.

    Returns
    -------
    bool
        True when enqueue was attempted successfully, False when skipped or failed.
    """
    uid = str(user_id or "").strip()
    trig = str(trigger or "").strip()
    if not uid:
        logger.warning("snapshot enqueue skipped: empty user_id")
        return False
    if not trig:
        logger.warning("snapshot enqueue skipped: empty trigger (user_id=%s)", uid)
        return False

    if not ASTOR_WORKER_QUEUE_ENABLED:
        logger.debug(
            "snapshot enqueue skipped: ASTOR_WORKER_QUEUE_ENABLED=false (user_id=%s trigger=%s)",
            uid,
            trig,
        )
        return False

    if not ASTOR_SNAPSHOT_ENQUEUE_ENABLED:
        logger.debug(
            "snapshot enqueue skipped: ASTOR_SNAPSHOT_ENQUEUE_ENABLED=false (user_id=%s trigger=%s)",
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
            "trigger": trig,
            "requested_at": req_at,
            "scope": "global",
        }
    )

    run_after_iso: Optional[str] = None
    if debounce:
        try:
            delay = int(
                debounce_seconds
                if debounce_seconds is not None
                else ASTOR_SNAPSHOT_DEBOUNCE_SECONDS
            )
        except Exception:
            delay = ASTOR_SNAPSHOT_DEBOUNCE_SECONDS
        delay = max(1, int(delay or 300))
        payload["debounce_seconds"] = delay
        run_after_iso = (now_dt + timedelta(seconds=delay)).isoformat().replace(
            "+00:00", "Z"
        )

    try:
        # Local import: keep module light and avoid importing Supabase config on startup.
        from astor_job_queue import enqueue_job

        await enqueue_job(
            job_key=f"snapshot:{uid}:global:internal",
            job_type="snapshot_generate_v1",
            user_id=uid,
            payload=payload,
            priority=int(priority or 20),
            run_after_iso=run_after_iso,
        )
        return True
    except Exception as exc:
        logger.error(
            "snapshot enqueue failed (user_id=%s trigger=%s): %s",
            uid,
            trig,
            exc,
        )
        return False


__all__ = [
    "ASTOR_WORKER_QUEUE_ENABLED",
    "ASTOR_SNAPSHOT_ENQUEUE_ENABLED",
    "ASTOR_SNAPSHOT_DEBOUNCE_SECONDS",
    "enqueue_global_snapshot_refresh",
]
