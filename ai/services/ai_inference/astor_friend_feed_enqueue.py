# -*- coding: utf-8 -*-
"""Shared helper for enqueuing ASTOR emotion log feed refresh jobs.

Purpose
-------
emotion submit などのイベントから、EmotionLog の viewer 単位 feed 再生成ジョブ
`refresh_friend_feed_v1` を安全に enqueue するための共通ヘルパー。

Design
------
- best-effort: enqueue に失敗しても API 成功/失敗は巻き込まない
- coalescing: 同一 viewer_user_id の feed refresh は job_key で 1 本へ自然に集約
- debounce: 連続入力を吸収し、不要な再生成を抑える
- per-viewer feed: job の user_id は viewer_user_id を採用し、worker 側でそのまま扱える

Notes
-----
- worker / queue / DB 互換のため、job_type・job_key_prefix は legacy の
  ``friend_*`` を維持する。
- env は canonical ``ASTOR_EMOTION_LOG_*`` を優先し、legacy ``ASTOR_FRIEND_*`` を fallback とする。
- このモジュール名も互換優先で ``astor_friend_feed_enqueue.py`` のまま残す。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger("astor_friend_feed_enqueue")


def _env_truthy(name: str, default: str = "true") -> bool:
    value = os.getenv(name, default)
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


FRIEND_FEED_REFRESH_JOB_TYPE = "refresh_friend_feed_v1"
FRIEND_FEED_REFRESH_JOB_KEY_PREFIX = "friend_feed_refresh_v1"

ASTOR_WORKER_QUEUE_ENABLED = _env_truthy("ASTOR_WORKER_QUEUE_ENABLED", "false")
ASTOR_FRIEND_FEED_ENQUEUE_ENABLED = _env_truthy(
    "ASTOR_EMOTION_LOG_FEED_ENQUEUE_ENABLED",
    os.getenv("ASTOR_FRIEND_FEED_ENQUEUE_ENABLED", "true"),
)

try:
    ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS = int(
        os.getenv(
            "ASTOR_EMOTION_LOG_FEED_DEBOUNCE_SECONDS",
            os.getenv("ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS", "10"),
        )
        or "10"
    )
except Exception:
    ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS = 10

# Canonical aliases for the follow / emotion-log implementation.
EMOTION_LOG_FEED_REFRESH_JOB_TYPE = FRIEND_FEED_REFRESH_JOB_TYPE
EMOTION_LOG_FEED_REFRESH_JOB_KEY_PREFIX = FRIEND_FEED_REFRESH_JOB_KEY_PREFIX
ASTOR_EMOTION_LOG_FEED_ENQUEUE_ENABLED = ASTOR_FRIEND_FEED_ENQUEUE_ENABLED
ASTOR_EMOTION_LOG_FEED_DEBOUNCE_SECONDS = ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS


async def enqueue_emotion_log_feed_refresh(
    *,
    viewer_user_id: str,
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    owner_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """Enqueue an EmotionLog feed refresh job for one viewer user.

    Parameters
    ----------
    viewer_user_id:
        User whose EmotionLog feed should be regenerated.
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
    owner_user_id:
        Optional owner whose emotion event dirtied the viewer feed.
        Useful for auditability and debugging.
    extra_payload:
        Optional extra payload merged into the job payload.

    Returns
    -------
    bool
        True when enqueue was attempted successfully, False when skipped or failed.
    """
    viewer_uid = str(viewer_user_id or "").strip()
    trig = str(trigger or "").strip()
    owner_uid = str(owner_user_id or "").strip() or None

    if not viewer_uid:
        logger.warning("emotion log feed enqueue skipped: empty viewer_user_id")
        return False
    if not trig:
        logger.warning(
            "emotion log feed enqueue skipped: empty trigger (viewer_user_id=%s)",
            viewer_uid,
        )
        return False

    if not ASTOR_WORKER_QUEUE_ENABLED:
        logger.debug(
            "emotion log feed enqueue skipped: ASTOR_WORKER_QUEUE_ENABLED=false (viewer_user_id=%s trigger=%s)",
            viewer_uid,
            trig,
        )
        return False

    if not ASTOR_FRIEND_FEED_ENQUEUE_ENABLED:
        logger.debug(
            "emotion log feed enqueue skipped: ASTOR_FRIEND_FEED_ENQUEUE_ENABLED=false (viewer_user_id=%s trigger=%s)",
            viewer_uid,
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
            "viewer_user_id": viewer_uid,
            "trigger": trig,
            "requested_at": req_at,
            "phase": "emotion_log_feed_v1",
            "surface": "emotion_log",
        }
    )
    if owner_uid:
        payload["owner_user_id"] = owner_uid

    run_after_iso: Optional[str] = None
    if debounce:
        try:
            delay = int(
                debounce_seconds
                if debounce_seconds is not None
                else ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS
            )
        except Exception:
            delay = ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS
        delay = max(1, int(delay or ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS))
        payload["debounce_seconds"] = delay
        run_after_iso = (now_dt + timedelta(seconds=delay)).isoformat().replace(
            "+00:00", "Z"
        )

    try:
        # Local import: keep module light and avoid importing Supabase config on startup.
        from astor_job_queue import enqueue_job

        await enqueue_job(
            job_key=f"{EMOTION_LOG_FEED_REFRESH_JOB_KEY_PREFIX}:{viewer_uid}",
            job_type=EMOTION_LOG_FEED_REFRESH_JOB_TYPE,
            user_id=viewer_uid,
            payload=payload,
            priority=int(priority or 18),
            run_after_iso=run_after_iso,
        )
        return True
    except Exception as exc:
        logger.error(
            "emotion log feed enqueue failed (viewer_user_id=%s trigger=%s owner_user_id=%s): %s",
            viewer_uid,
            trig,
            owner_uid or "",
            exc,
        )
        return False


async def enqueue_emotion_log_feed_refresh_many(
    *,
    viewer_user_ids: Iterable[str],
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    owner_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """Enqueue EmotionLog feed refresh jobs for multiple viewer users.

    Duplicate / empty viewer_user_ids are ignored. The same ``requested_at`` and
    ``trigger`` are reused for all viewers so a single owner event can fan out
    into multiple per-viewer feed refresh requests.
    """
    results: Dict[str, bool] = {}
    seen = set()

    for raw_viewer in viewer_user_ids or []:
        viewer_uid = str(raw_viewer or "").strip()
        if not viewer_uid or viewer_uid in seen:
            continue
        seen.add(viewer_uid)
        results[viewer_uid] = await enqueue_emotion_log_feed_refresh(
            viewer_user_id=viewer_uid,
            trigger=trigger,
            requested_at=requested_at,
            debounce=debounce,
            debounce_seconds=debounce_seconds,
            priority=priority,
            owner_user_id=owner_user_id,
            extra_payload=extra_payload,
        )
    return results


async def enqueue_friend_feed_refresh(
    *,
    viewer_user_id: str,
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    owner_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """Backward-compatible wrapper for the legacy friend-named API."""
    return await enqueue_emotion_log_feed_refresh(
        viewer_user_id=viewer_user_id,
        trigger=trigger,
        requested_at=requested_at,
        debounce=debounce,
        debounce_seconds=debounce_seconds,
        priority=priority,
        owner_user_id=owner_user_id,
        extra_payload=extra_payload,
    )


async def enqueue_friend_feed_refresh_many(
    *,
    viewer_user_ids: Iterable[str],
    trigger: str,
    requested_at: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    owner_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """Backward-compatible wrapper for the legacy friend-named bulk API."""
    return await enqueue_emotion_log_feed_refresh_many(
        viewer_user_ids=viewer_user_ids,
        trigger=trigger,
        requested_at=requested_at,
        debounce=debounce,
        debounce_seconds=debounce_seconds,
        priority=priority,
        owner_user_id=owner_user_id,
        extra_payload=extra_payload,
    )


__all__ = [
    "FRIEND_FEED_REFRESH_JOB_TYPE",
    "FRIEND_FEED_REFRESH_JOB_KEY_PREFIX",
    "EMOTION_LOG_FEED_REFRESH_JOB_TYPE",
    "EMOTION_LOG_FEED_REFRESH_JOB_KEY_PREFIX",
    "ASTOR_WORKER_QUEUE_ENABLED",
    "ASTOR_FRIEND_FEED_ENQUEUE_ENABLED",
    "ASTOR_FRIEND_FEED_DEBOUNCE_SECONDS",
    "ASTOR_EMOTION_LOG_FEED_ENQUEUE_ENABLED",
    "ASTOR_EMOTION_LOG_FEED_DEBOUNCE_SECONDS",
    "enqueue_emotion_log_feed_refresh",
    "enqueue_emotion_log_feed_refresh_many",
    "enqueue_friend_feed_refresh",
    "enqueue_friend_feed_refresh_many",
]
