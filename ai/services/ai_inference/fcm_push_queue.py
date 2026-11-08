# -*- coding: utf-8 -*-
"""FCM push dedicated queue helpers for Cocolon.

Purpose
-------
FCM sending is an external network operation and can become a burst bottleneck
when many users submit emotions or reports complete at the same time.  This
module keeps API / heavy worker paths light by writing push-send work into the
existing DB-backed worker queue (`astor_jobs`) as `send_fcm_push_v1` jobs.

Design
------
- No new DB table is required.
- Device tokens are not stored in the job payload by default; the worker stores
  recipient user ids and resolves current push tokens just before sending.
- Jobs are chunked so large fan-out notifications can be processed by multiple
  notification workers.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from astor_job_queue import JOBS_TABLE, enqueue_job
from supabase_client import ensure_supabase_config, sb_post

FCM_PUSH_JOB_TYPE = "send_fcm_push_v1"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except Exception:
        return int(default)


FCM_PUSH_QUEUE_CHUNK_SIZE = max(1, min(500, _env_int("FCM_PUSH_QUEUE_CHUNK_SIZE", 200)))
FCM_PUSH_QUEUE_MAX_ATTEMPTS = max(1, min(10, _env_int("FCM_PUSH_QUEUE_MAX_ATTEMPTS", 5)))


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ordered_unique_strs(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values or []:
        s = str(value or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _chunk(values: List[str], size: int) -> List[List[str]]:
    n = max(1, int(size or FCM_PUSH_QUEUE_CHUNK_SIZE))
    return [values[i : i + n] for i in range(0, len(values), n)]


def _safe_data_payload(data: Optional[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(data, dict):
        return out
    for key, value in data.items():
        if key is None or value is None:
            continue
        out[str(key)] = str(value)
    return out


def _digest_for_job_key(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]


def _normalize_job_key_prefix(value: Optional[str]) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    # Keep job keys compact and PostgREST-friendly.  A digest preserves uniqueness
    # without leaking long / arbitrary strings into the key.
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


async def _insert_push_job_once(*, job_key: str, user_id: str,
                                payload: Dict[str, Any], priority: int,
                                max_attempts: int) -> bool:
    """Reserve one existing queue key without changing any prior generation."""
    ensure_supabase_config()
    now = _now_iso_z()
    response = await sb_post(
        f"/rest/v1/{JOBS_TABLE}",
        params={"on_conflict": "job_key"},
        json={"job_key": job_key, "job_type": FCM_PUSH_JOB_TYPE,
            "user_id": user_id, "payload": payload, "priority": priority,
            "status": "queued", "attempts": 0,
            "max_attempts": max_attempts, "run_after": now, "updated_at": now},
        prefer="resolution=ignore-duplicates,return=representation",
        timeout=6.0,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"push_once_insert_failed:{response.status_code}")
    try:
        rows = response.json()
    except (TypeError, ValueError):
        raise RuntimeError("push_once_insert_invalid") from None
    if type(rows) is not list or len(rows) > 1 or (rows and type(rows[0]) is not dict):
        raise RuntimeError("push_once_insert_invalid")
    return bool(rows)


async def enqueue_user_push_notification_jobs(
    *,
    recipient_user_ids: Iterable[Any],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    actor_user_id: Optional[str] = None,
    exclude_user_ids: Optional[Iterable[Any]] = None,
    event_type: str = "generic",
    job_key_prefix: Optional[str] = None,
    priority: int = 5,
    chunk_size: Optional[int] = None,
    max_attempts: Optional[int] = None,
    only_if_absent: bool = False,
) -> int:
    """Enqueue FCM push jobs addressed by user id.

    Returns the number of queued chunks.  Each chunk is processed by a worker and
    resolves push tokens at send time, so updated push_enabled / push_token values
    are respected.

    only_if_absent atomically reserves a new queue key and leaves any prior
    queued, running or terminal job untouched. External-send retries remain
    at-least-once; reserving a job once does not guarantee one device delivery.
    """
    recipients = _ordered_unique_strs(recipient_user_ids)
    actor = str(actor_user_id or "").strip()
    excluded = set(_ordered_unique_strs(exclude_user_ids or []))
    if excluded:
        recipients = [uid for uid in recipients if uid not in excluded]
    if not recipients:
        return 0

    title_s = str(title or "").strip()[:160]
    body_s = str(body or "").strip()[:512]
    if not title_s or not body_s:
        return 0

    event = str(event_type or "generic").strip() or "generic"
    data_s = _safe_data_payload(data)
    chunks = _chunk(recipients, int(chunk_size or FCM_PUSH_QUEUE_CHUNK_SIZE))
    prefix_digest = _normalize_job_key_prefix(job_key_prefix)
    queued = 0

    for index, chunk_user_ids in enumerate(chunks):
        payload: Dict[str, Any] = {
            "schema_version": "fcm.push.job.v1",
            "recipient_mode": "user_ids",
            "recipient_user_ids": chunk_user_ids,
            "exclude_user_ids": sorted(excluded),
            "title": title_s,
            "body": body_s,
            "data": data_s,
            "event_type": event,
            "actor_user_id": actor,
            "queued_at": _now_iso_z(),
            "chunk_index": index,
            "chunk_count": len(chunks),
        }
        digest_payload = {
            "event_type": event,
            "prefix": prefix_digest,
            "actor_user_id": actor,
            "recipient_user_ids": chunk_user_ids,
            "title": title_s,
            "body": body_s,
            "data": data_s,
            "chunk_index": index,
        }
        digest = _digest_for_job_key(digest_payload)
        job_key_parts = ["fcm_push", event]
        if prefix_digest:
            job_key_parts.append(prefix_digest)
        job_key_parts.extend([str(index), digest])
        job_key = ":".join(job_key_parts)

        if only_if_absent:
            queued += int(await _insert_push_job_once(
                job_key=job_key, user_id=actor or chunk_user_ids[0], payload=payload,
                priority=int(priority or 5),
                max_attempts=int(max_attempts or FCM_PUSH_QUEUE_MAX_ATTEMPTS)))
        else:
            await enqueue_job(
                job_key=job_key,
                job_type=FCM_PUSH_JOB_TYPE,
                user_id=actor or chunk_user_ids[0],
                payload=payload,
                priority=int(priority or 5),
                max_attempts=int(max_attempts or FCM_PUSH_QUEUE_MAX_ATTEMPTS),
            )
            queued += 1

    return queued


async def enqueue_single_user_push_notification(
    *,
    user_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    event_type: str = "generic",
    job_key_prefix: Optional[str] = None,
    priority: int = 5,
    only_if_absent: bool = False,
) -> int:
    """Convenience wrapper for one-recipient push notifications."""
    uid = str(user_id or "").strip()
    if not uid:
        return 0
    return await enqueue_user_push_notification_jobs(
        recipient_user_ids=[uid],
        title=title,
        body=body,
        data=data,
        actor_user_id=uid,
        event_type=event_type,
        job_key_prefix=job_key_prefix,
        priority=priority,
        chunk_size=1,
        only_if_absent=only_if_absent,
    )
