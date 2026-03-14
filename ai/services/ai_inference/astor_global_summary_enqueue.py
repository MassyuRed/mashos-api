# -*- coding: utf-8 -*-
"""Shared helper for enqueuing ASTOR global summary refresh jobs.

Purpose
-------
入力 API / operational API から、Global Summary 系の app-wide 日次集計再生成ジョブ
`refresh_global_summary_v1` を安全に enqueue するための共通ヘルパー。

Design
------
- best-effort: enqueue に失敗しても API 成功/失敗は巻き込まない
- coalescing: 同一 activity_date + timezone の refresh は job_key で 1 本へ自然に集約
- debounce: 入力連打を吸収し、日次 aggregate の無駄な再生成を抑える
- system actor: job の user_id は `system_global_summary` を採用し、監査用 actor は payload に積む
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - zoneinfo is expected on py3.9+
    ZoneInfo = None  # type: ignore

from astor_global_summary_store import (
    GLOBAL_SUMMARY_TIMEZONE,
    canonical_global_summary_activity_date,
    canonical_global_summary_timezone,
)

logger = logging.getLogger("astor_global_summary_enqueue")


JST = timezone(timedelta(hours=9))


def _env_truthy(name: str, default: str = "true") -> bool:
    value = os.getenv(name, default)
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


GLOBAL_SUMMARY_REFRESH_JOB_TYPE = "refresh_global_summary_v1"
GLOBAL_SUMMARY_REFRESH_JOB_KEY_PREFIX = "global_summary_refresh_v1"
GLOBAL_SUMMARY_SYSTEM_USER_ID = (
    os.getenv("ASTOR_GLOBAL_SUMMARY_SYSTEM_USER_ID") or "system_global_summary"
).strip() or "system_global_summary"

ASTOR_WORKER_QUEUE_ENABLED = _env_truthy("ASTOR_WORKER_QUEUE_ENABLED", "false")
ASTOR_GLOBAL_SUMMARY_ENQUEUE_ENABLED = _env_truthy(
    "ASTOR_GLOBAL_SUMMARY_ENQUEUE_ENABLED",
    "true",
)

try:
    ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS = int(
        os.getenv("ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS", "300") or "300"
    )
except Exception:
    ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS = 300


def _parse_requested_at(value: Optional[str]) -> datetime:
    s = str(value or "").strip()
    if not s:
        return datetime.now(timezone.utc).replace(microsecond=0)

    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        logger.warning("global summary enqueue received invalid requested_at=%s; fallback to now()", s)
        return datetime.now(timezone.utc).replace(microsecond=0)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def _tzinfo_for_name(timezone_name: str):
    tz_name = canonical_global_summary_timezone(timezone_name)
    if tz_name == "Asia/Tokyo":
        return JST
    if ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass
    return timezone.utc


def resolve_global_summary_activity_date(
    *,
    requested_at: Optional[str] = None,
    activity_date: Optional[Any] = None,
    timezone_name: Optional[str] = None,
) -> str:
    explicit_date = canonical_global_summary_activity_date(activity_date)
    if explicit_date:
        return explicit_date

    dt = _parse_requested_at(requested_at)
    tz_name = canonical_global_summary_timezone(timezone_name or GLOBAL_SUMMARY_TIMEZONE)
    local_dt = dt.astimezone(_tzinfo_for_name(tz_name))
    return local_dt.date().isoformat()


def _job_key_timezone_fragment(timezone_name: str) -> str:
    return (
        canonical_global_summary_timezone(timezone_name)
        .replace("/", "_")
        .replace(":", "")
        .replace(" ", "_")
    )


async def enqueue_global_summary_refresh(
    *,
    trigger: str,
    requested_at: Optional[str] = None,
    activity_date: Optional[Any] = None,
    timezone_name: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    actor_user_id: Optional[str] = None,
    system_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """Enqueue an app-wide global summary refresh job for one daily bucket."""
    trig = str(trigger or "").strip()
    actor_uid = str(actor_user_id or "").strip() or None
    tz_name = canonical_global_summary_timezone(timezone_name or GLOBAL_SUMMARY_TIMEZONE)
    act_date = resolve_global_summary_activity_date(
        requested_at=requested_at,
        activity_date=activity_date,
        timezone_name=tz_name,
    )
    system_uid = str(system_user_id or GLOBAL_SUMMARY_SYSTEM_USER_ID).strip() or GLOBAL_SUMMARY_SYSTEM_USER_ID

    if not trig:
        logger.warning(
            "global summary enqueue skipped: empty trigger (activity_date=%s timezone=%s)",
            act_date,
            tz_name,
        )
        return False

    if not ASTOR_WORKER_QUEUE_ENABLED:
        logger.debug(
            "global summary enqueue skipped: ASTOR_WORKER_QUEUE_ENABLED=false (activity_date=%s timezone=%s trigger=%s)",
            act_date,
            tz_name,
            trig,
        )
        return False

    if not ASTOR_GLOBAL_SUMMARY_ENQUEUE_ENABLED:
        logger.debug(
            "global summary enqueue skipped: ASTOR_GLOBAL_SUMMARY_ENQUEUE_ENABLED=false (activity_date=%s timezone=%s trigger=%s)",
            act_date,
            tz_name,
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
            "activity_date": act_date,
            "timezone": tz_name,
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
                else ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS
            )
        except Exception:
            delay = ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS
        delay = max(1, int(delay or ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS))
        payload["debounce_seconds"] = delay
        run_after_iso = (now_dt + timedelta(seconds=delay)).isoformat().replace(
            "+00:00", "Z"
        )

    try:
        # Local import: keep module light and avoid importing Supabase config on startup.
        from astor_job_queue import enqueue_job

        await enqueue_job(
            job_key=(
                f"{GLOBAL_SUMMARY_REFRESH_JOB_KEY_PREFIX}:"
                f"{act_date}:{_job_key_timezone_fragment(tz_name)}"
            ),
            job_type=GLOBAL_SUMMARY_REFRESH_JOB_TYPE,
            user_id=system_uid,
            payload=payload,
            priority=int(priority or 18),
            run_after_iso=run_after_iso,
        )
        return True
    except Exception as exc:
        logger.error(
            "global summary enqueue failed (activity_date=%s timezone=%s trigger=%s actor_user_id=%s): %s",
            act_date,
            tz_name,
            trig,
            actor_uid or "",
            exc,
        )
        return False


async def enqueue_global_summary_refresh_many(
    *,
    activity_dates: Iterable[Any],
    trigger: str,
    requested_at: Optional[str] = None,
    timezone_name: Optional[str] = None,
    debounce: bool = True,
    debounce_seconds: Optional[int] = None,
    priority: int = 18,
    actor_user_id: Optional[str] = None,
    system_user_id: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """Enqueue refresh jobs for multiple daily buckets."""
    results: Dict[str, bool] = {}
    seen = set()
    for raw_date in activity_dates or []:
        act_date = canonical_global_summary_activity_date(raw_date)
        if not act_date or act_date in seen:
            continue
        seen.add(act_date)
        results[act_date] = await enqueue_global_summary_refresh(
            trigger=trigger,
            requested_at=requested_at,
            activity_date=act_date,
            timezone_name=timezone_name,
            debounce=debounce,
            debounce_seconds=debounce_seconds,
            priority=priority,
            actor_user_id=actor_user_id,
            system_user_id=system_user_id,
            extra_payload=extra_payload,
        )
    return results


__all__ = [
    "GLOBAL_SUMMARY_REFRESH_JOB_TYPE",
    "GLOBAL_SUMMARY_REFRESH_JOB_KEY_PREFIX",
    "GLOBAL_SUMMARY_SYSTEM_USER_ID",
    "ASTOR_WORKER_QUEUE_ENABLED",
    "ASTOR_GLOBAL_SUMMARY_ENQUEUE_ENABLED",
    "ASTOR_GLOBAL_SUMMARY_DEBOUNCE_SECONDS",
    "resolve_global_summary_activity_date",
    "enqueue_global_summary_refresh",
    "enqueue_global_summary_refresh_many",
]
