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
  - ASTOR_WORKER_JOB_TYPES=myprofile_latest_refresh_v1,snapshot_generate_v1,generate_emotion_report_v2,inspect_emotion_report_v1   (comma separated)
  - ASTOR_WORKER_LOG_LEVEL=INFO

This worker consumes jobs enqueued by API (e.g., emotion/submit) and executes
heavy tasks out-of-process, improving API stability.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from astor_job_queue import (
    fetch_next_queued_job,
    claim_job,
    enqueue_job,
    mark_done_if_unchanged,
    requeue,
    mark_failed,
)
from supabase_client import sb_get, sb_patch  # type: ignore


# NOTE:
# In your repo, the module is expected to be `astor_myprofile_report.py`.
# (This patch provides an updated version that adds `refresh_myprofile_latest_report`.)
from astor_myprofile_report import refresh_myprofile_latest_report  # type: ignore

# Phase X: material snapshots (central input snapshots)
from astor_material_snapshots import (
    generate_and_store_material_snapshots,
    fetch_emotion_meta_for_hash,
    compute_source_hash_from_emotion_meta,
)  # type: ignore

# Phase X+: emotion structure reports (MyWeb weekly/monthly)
from api_myweb_reports import (
    _build_target_period as _myweb_build_target_period,
    _generate_and_save_from_snapshot as _myweb_generate_and_save_from_snapshot,
)  # type: ignore

# Generation lock (avoid concurrent snapshot generation per user/scope)
from generation_lock import build_lock_key, make_owner_id, release_lock, try_acquire_lock  # type: ignore

MYWEB_REPORTS_TABLE = (os.getenv("MYWEB_REPORTS_TABLE") or "myweb_reports").strip() or "myweb_reports"
MATERIAL_SNAPSHOTS_TABLE = (os.getenv("MATERIAL_SNAPSHOTS_TABLE") or "material_snapshots").strip() or "material_snapshots"
SNAPSHOT_SCOPE_DEFAULT = (os.getenv("SNAPSHOT_SCOPE_DEFAULT") or "global").strip() or "global"

# JST (UTC+9) fixed for MyWeb periods
JST = timezone(timedelta(hours=9))

EMOTION_REPORT_V2_ENABLED = (os.getenv("ASTOR_ENABLE_EMOTION_REPORT_V2", "false").strip().lower() == "true")



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



async def _handle_generate_emotion_report_v2(*, user_id: str, payload: dict) -> dict:
    """Generate emotion structure reports from emotion_period snapshots for a user (v2).

    v2 方針:
    - emotion_period material_snapshots (weekly/monthly) を入力として使用する。
    - emotions テーブルを直接読まない（materials 経由の国家設計）。
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    include_astor = bool((payload or {}).get("include_astor", True))

    scopes: List[str] = []
    if isinstance((payload or {}).get("scopes"), list):
        scopes = [str(x or "").strip() for x in (payload or {}).get("scopes") if str(x or "").strip()]
    else:
        sc = str((payload or {}).get("scope") or "").strip()
        if sc:
            scopes = [sc]

    if not scopes:
        raise ValueError("payload.scope(s) is required")

    generated = []
    errors: Dict[str, str] = {}
    for sc in scopes:
        try:
            _text, _json, _astor_text, meta = await _myweb_generate_and_save_from_snapshot(uid, scope=sc, include_astor=include_astor)
            rid = None
            rt = None
            pub_hash = None
            if isinstance(meta, dict):
                rid = meta.get("report_id")
                rt = meta.get("report_type")
                pub_hash = meta.get("public_source_hash")
            generated.append({"scope": sc, "report_type": rt, "report_id": rid, "public_source_hash": pub_hash, "status": "ok"})
        except Exception as exc:
            errors[sc] = str(exc)

    if not generated:
        raise RuntimeError(f"generate_emotion_report_v2 failed: {errors}")

    return {"status": "ok", "user_id": uid, "generated": generated, "errors": (errors or None)}


# ----------------------------
# Inspection: Emotion report (MyWeb) publish gating
# ----------------------------

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Very loose phone detector (JP + general digit sequences)
_PHONE_RE = re.compile(r"(?:\b0\d{1,4}[- ]?\d{1,4}[- ]?\d{4}\b|\b\d{10,11}\b)")


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _detect_pii(text: str) -> List[str]:
    t = str(text or "")
    flags: List[str] = []
    try:
        if _EMAIL_RE.search(t):
            flags.append("email")
    except Exception:
        pass
    try:
        if _PHONE_RE.search(t):
            flags.append("phone")
    except Exception:
        pass
    return flags


async def _fetch_latest_public_source_hash(user_id: str, *, scope: str) -> Optional[str]:
    """Best-effort: prefer material_snapshots.latest(public), else compute from emotions meta."""
    uid = str(user_id or "").strip()
    if not uid:
        return None
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT

    # 1) Try snapshots table (fast path)
    try:
        resp = await sb_get(
            f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
            params={
                "select": "source_hash,created_at",
                "user_id": f"eq.{uid}",
                "scope": f"eq.{sc}",
                "snapshot_type": "eq.public",
                "order": "created_at.desc",
                "limit": "1",
            },
            timeout=8.0,
        )
        if resp.status_code in (200, 206):
            rows = resp.json()
            if isinstance(rows, list) and rows:
                sh = str((rows[0] or {}).get("source_hash") or "").strip()
                if sh:
                    return sh
    except Exception:
        pass

    # 2) Fallback: compute from emotion meta (may be heavier)
    try:
        meta = await fetch_emotion_meta_for_hash(uid)
        return compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="public", meta_rows=meta)
    except Exception:
        return None


async def _fetch_myweb_report_row(report_id: str, *, user_id: str) -> Optional[Dict[str, Any]]:
    rid = str(report_id or "").strip()
    uid = str(user_id or "").strip()
    if not rid or not uid:
        return None
    try:
        resp = await sb_get(
            f"/rest/v1/{MYWEB_REPORTS_TABLE}",
            params={
                "select": "id,user_id,report_type,period_start,period_end,title,content_text,content_json,generated_at,updated_at",
                "id": f"eq.{rid}",
                "user_id": f"eq.{uid}",
                "limit": "1",
            },
            timeout=10.0,
        )
        if resp.status_code not in (200, 206):
            return None
        rows = resp.json()
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0]
    except Exception:
        return None
    return None


async def _patch_myweb_report_content_json(report_id: str, *, content_json: Dict[str, Any]) -> bool:
    rid = str(report_id or "").strip()
    if not rid:
        return False
    try:
        resp = await sb_patch(
            f"/rest/v1/{MYWEB_REPORTS_TABLE}",
            params={"id": f"eq.{rid}"},
            json={
                "content_json": content_json,
                "updated_at": _now_iso_z(),
            },
            prefer="return=minimal",
            timeout=10.0,
        )
        return resp.status_code in (200, 204)
    except Exception:
        return False


async def _handle_inspect_emotion_report_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Inspect a generated emotion report and set publish.status.

    Expected payload:
    - report_id (required)
    - scope (optional, default SNAPSHOT_SCOPE_DEFAULT)
    - expected_public_source_hash (optional)
    """
    uid = str(user_id or "").strip()
    report_id = str((payload or {}).get("report_id") or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not report_id:
        raise ValueError("payload.report_id is required")

    row = await _fetch_myweb_report_row(report_id, user_id=uid)
    if not row:
        return {"status": "missing", "user_id": uid, "report_id": report_id}

    cj = row.get("content_json") if isinstance(row.get("content_json"), dict) else {}
    pub = cj.get("publish") if isinstance(cj.get("publish"), dict) else {}

    scope = str((payload or {}).get("scope") or pub.get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
    expected_hash = (payload or {}).get("expected_public_source_hash") or pub.get("publicSourceHash")
    secret_excluded = bool(pub.get("secretExcluded"))  # should be True for publishable artifacts

    # --- public alignment ---
    current_hash = await _fetch_latest_public_source_hash(uid, scope=scope)
    hash_match = bool(expected_hash and current_hash and str(expected_hash) == str(current_hash))

    flags: List[str] = []
    if not secret_excluded:
        flags.append("secret_excluded_missing")
    if not expected_hash:
        flags.append("expected_public_source_hash_missing")
    if not current_hash:
        flags.append("current_public_source_hash_missing")
    if expected_hash and current_hash and not hash_match:
        flags.append("public_snapshot_mismatch")

    # --- PII check (rule-based, minimal) ---
    text_parts: List[str] = []
    try:
        if isinstance(row.get("content_text"), str):
            text_parts.append(row.get("content_text") or "")
    except Exception:
        pass
    try:
        if isinstance(cj.get("astorText"), str):
            text_parts.append(cj.get("astorText") or "")
    except Exception:
        pass
    pii_flags = _detect_pii("\n".join(text_parts))
    for pf in pii_flags:
        flags.append(f"pii:{pf}")

    inspected_at = _now_iso_z()

    status = "READY"
    if flags:
        status = "NEEDS_REVIEW"

    # If missing governance meta or public mismatch, request regeneration (best-effort)
    need_regen = any(
        f in flags for f in ("secret_excluded_missing", "expected_public_source_hash_missing", "public_snapshot_mismatch")
    )
    if need_regen:
        try:
            # Use v2 regeneration for emotion_period-scoped artifacts (v1 is deprecated).
            if scope.startswith("emotion_weekly:") or scope.startswith("emotion_monthly:"):
                regen_hash = str(current_hash or expected_hash or "")
                await enqueue_job(
                    job_key=f"emotion_report_v2_refresh:{uid}:{scope}:{regen_hash}",
                    job_type="generate_emotion_report_v2",
                    user_id=uid,
                    payload={"trigger": "inspect_mismatch", "requested_at": inspected_at, "scope": scope, "include_astor": True},
                    priority=20,
                    debounce_seconds=10,
                )
        except Exception:
            pass

    pub2 = dict(pub or {})
    pub2.update(
        {
            "status": status,
            "inspectedAt": inspected_at,
            "latestPublicSourceHash": current_hash,
            "hashMatch": bool(hash_match),
            "inspectionFlags": flags,
            "inspector": {"job_type": "inspect_emotion_report_v1"},
        }
    )
    cj2 = dict(cj or {})
    cj2["publish"] = pub2

    patched = await _patch_myweb_report_content_json(report_id, content_json=cj2)
    return {
        "status": status,
        "user_id": uid,
        "report_id": report_id,
        "patched": bool(patched),
        "scope": scope,
        "expected_public_source_hash": expected_hash,
        "latest_public_source_hash": current_hash,
        "hash_match": bool(hash_match),
        "flags": flags,
    }



async def _worker_loop() -> None:
    worker_id = (os.getenv("ASTOR_WORKER_ID") or "").strip() or f"astor-worker-{os.getpid()}"
    poll_interval = float(os.getenv("ASTOR_WORKER_POLL_INTERVAL_SECONDS", "1.0") or "1.0")
    job_types = _parse_job_types(os.getenv("ASTOR_WORKER_JOB_TYPES", "myprofile_latest_refresh_v1,snapshot_generate_v1,generate_emotion_report_v2,inspect_emotion_report_v1"))

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
                            scope = str((claimed.payload or {}).get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
                            if bool(internal.get("inserted")) or bool(public.get("inserted")):
                                # Global snapshot committed -> auto-enqueue emotion_period snapshots (weekly/monthly).
                                # emotion_period snapshot committed -> enqueue snapshot-driven MyWeb generation (v2).
                                if scope == SNAPSHOT_SCOPE_DEFAULT:

                                    # Auto-enqueue emotion_period snapshots (weekly/monthly) for future snapshot-driven analysis.
                                    try:
                                        now_utc = datetime.now(timezone.utc)
                                        weekly_target = _myweb_build_target_period("weekly", now_utc)
                                        weekly_dist_jst = weekly_target.dist_utc.astimezone(JST)
                                        weekly_scope = f"emotion_weekly:{weekly_dist_jst.year:04d}-{weekly_dist_jst.month:02d}-{weekly_dist_jst.day:02d}"

                                        monthly_target = _myweb_build_target_period("monthly", now_utc)
                                        monthly_end_jst = monthly_target.period_end_utc.astimezone(JST)
                                        monthly_scope = f"emotion_monthly:{monthly_end_jst.year:04d}-{monthly_end_jst.month:02d}"

                                        req_at = (claimed.payload or {}).get("requested_at")
                                        await enqueue_job(
                                            job_key=f"snapshot_generate_v1:{claimed.user_id}:{weekly_scope}",
                                            job_type="snapshot_generate_v1",
                                            user_id=claimed.user_id,
                                            payload={"scope": weekly_scope, "trigger": "auto_emotion_period", "requested_at": req_at},
                                            priority=12,
                                        )
                                        await enqueue_job(
                                            job_key=f"snapshot_generate_v1:{claimed.user_id}:{monthly_scope}",
                                            job_type="snapshot_generate_v1",
                                            user_id=claimed.user_id,
                                            payload={"scope": monthly_scope, "trigger": "auto_emotion_period", "requested_at": req_at},
                                            priority=12,
                                        )
                                    except Exception as exc:
                                        logger.error("Emotion period snapshot enqueue failed: %s", exc)
                                else:
                                    # emotion_period snapshot committed -> enqueue snapshot-driven MyWeb generation (v2)
                                    if EMOTION_REPORT_V2_ENABLED and (
                                        scope.startswith("emotion_daily:")
                                        or scope.startswith("emotion_weekly:")
                                        or scope.startswith("emotion_monthly:")
                                    ):
                                        try:
                                            pub_hash = str(public.get("source_hash") or "")
                                            include_astor = not scope.startswith("emotion_daily:")
                                            await enqueue_job(
                                                job_key=f"emotion_report_v2_refresh:{claimed.user_id}:{scope}:{pub_hash}",
                                                job_type="generate_emotion_report_v2",
                                                user_id=claimed.user_id,
                                                payload={
                                                    "trigger": "snapshot_generate_v1",
                                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                                    "scope": scope,
                                                    "include_astor": include_astor,
                                                    "source_hash": pub_hash,
                                                },
                                                priority=12,
                                            )
                                        except Exception as exc:
                                            logger.error("Downstream enqueue v2 failed: %s", exc)
                        except Exception as exc:
                            logger.error("Downstream enqueue failed: %s", exc)
                logger.info("job done. key=%s type=%s user=%s res=%s", claimed.job_key, claimed.job_type, claimed.user_id, snap_res)
            elif claimed.job_type == "generate_emotion_report_v2":
                gen_res = await _handle_generate_emotion_report_v2(user_id=claimed.user_id, payload=(claimed.payload or {}))
                # Enqueue inspection jobs for publish gating (best-effort).
                try:
                    gen_list = (gen_res or {}).get("generated") or []
                    if isinstance(gen_list, list) and gen_list:
                        for it in gen_list:
                            if not isinstance(it, dict):
                                continue
                            rid = str(it.get("report_id") or "").strip()
                            if not rid:
                                continue
                            scope = str(it.get("scope") or "").strip() or SNAPSHOT_SCOPE_DEFAULT
                            expected_public_hash = it.get("public_source_hash")
                            await enqueue_job(
                                job_key=f"inspect_emotion_report:{claimed.user_id}:{rid}",
                                job_type="inspect_emotion_report_v1",
                                user_id=claimed.user_id,
                                payload={
                                    "report_id": rid,
                                    "scope": scope,
                                    "expected_public_source_hash": expected_public_hash,
                                    "trigger": "generate_emotion_report_v2",
                                },
                                priority=30,
                            )
                except Exception as exc:
                    logger.error("Inspect enqueue failed (v2): %s", exc)

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
            elif claimed.job_type == "inspect_emotion_report_v1":
                insp_res = await _handle_inspect_emotion_report_v1(user_id=claimed.user_id, payload=(claimed.payload or {}))
                done = await mark_done_if_unchanged(
                    job_key=claimed.job_key,
                    worker_id=worker_id,
                    expected_updated_at=claimed.updated_at,
                )
                if not done:
                    await requeue(
                        job_key=claimed.job_key,
                        worker_id=worker_id,
                        error="updated_while_running",
                        delay_seconds=1,
                    )
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    insp_res,
                )

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