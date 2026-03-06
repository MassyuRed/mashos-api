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
  - ASTOR_WORKER_JOB_TYPES=myprofile_latest_refresh_v1,snapshot_generate_v1,analyze_emotion_structure_standard_v1,analyze_emotion_structure_deep_v1,generate_emotion_report_v2,inspect_emotion_report_v1   (comma separated)
  - ASTOR_WORKER_LOG_LEVEL=INFO

This worker consumes jobs enqueued by API (e.g., emotion/submit) and executes
heavy tasks out-of-process, improving API stability.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import re
import signal
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
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
from supabase_client import sb_get, sb_patch, sb_post  # type: ignore


# NOTE:
# In your repo, the module is expected to be `astor_myprofile_report.py`.
# (This patch provides an updated version that adds `refresh_myprofile_latest_report`.)
from astor_myprofile_report import refresh_myprofile_latest_report  # type: ignore

# Phase X: material snapshots (central input snapshots)
from astor_material_snapshots import (
    generate_and_store_material_snapshots,
    fetch_emotion_meta_for_hash,
    compute_source_hash_from_emotion_meta,
    fetch_emotions_in_range,
    _parse_emotion_period_scope,
)  # type: ignore

# Phase X+: emotion structure reports (MyWeb weekly/monthly)
from api_myweb_reports import (
    _build_target_period as _myweb_build_target_period,
    _generate_and_save_from_snapshot as _myweb_generate_and_save_from_snapshot,
)  # type: ignore

from api_emotion_submit import _fetch_push_tokens_for_users, _send_fcm_push  # type: ignore

# Generation lock (avoid concurrent snapshot generation per user/scope)
from generation_lock import build_lock_key, make_owner_id, release_lock, try_acquire_lock  # type: ignore

# analysis_engine (sibling package under ai/services/analysis_engine)
# NOTE:
# Render では package export (__init__.py) が古い/未反映でも動くように、
# まず sibling package の parent を sys.path へ追加し、submodule 直 import を優先する。
_services_root = Path(__file__).resolve().parent.parent
if str(_services_root) not in sys.path:
    sys.path.insert(0, str(_services_root))

try:
    from analysis_engine.weekly import build_weekly_features, narrate_weekly  # type: ignore
    from analysis_engine.monthly import assemble_monthly, narrate_monthly  # type: ignore
    from analysis_engine.daily import narrate_daily  # type: ignore
except Exception:
    # Fallback: package __init__ export が正しく入っている環境では従来 import も許可
    from analysis_engine import (  # type: ignore
        build_weekly_features,
        narrate_weekly,
        assemble_monthly,
        narrate_monthly,
        narrate_daily,
    )

from analysis_engine_adapter import build_emotion_entries_from_rows  # type: ignore

MYWEB_REPORTS_TABLE = (os.getenv("MYWEB_REPORTS_TABLE") or "myweb_reports").strip() or "myweb_reports"
MATERIAL_SNAPSHOTS_TABLE = (os.getenv("MATERIAL_SNAPSHOTS_TABLE") or "material_snapshots").strip() or "material_snapshots"
SNAPSHOT_SCOPE_DEFAULT = (os.getenv("SNAPSHOT_SCOPE_DEFAULT") or "global").strip() or "global"
ANALYSIS_RESULTS_TABLE = (os.getenv("ANALYSIS_RESULTS_TABLE") or "analysis_results").strip() or "analysis_results"

# JST (UTC+9) fixed for MyWeb periods
JST = timezone(timedelta(hours=9))

EMOTION_REPORT_V2_ENABLED = (os.getenv("ASTOR_ENABLE_EMOTION_REPORT_V2", "false").strip().lower() == "true")

WORKER_LOGGER = logging.getLogger("astor_worker")

DEEP_MAX_CONTROL_PATTERNS = max(1, min(5, int(os.getenv("EMOTION_DEEP_MAX_CONTROL_PATTERNS", "5") or "5")))
DEEP_UI_LABELS: List[str] = ["joy", "sadness", "anxiety", "anger", "calm"]
_DEEP_PATTERN_LABEL_PRIORITY = ["calm", "joy", "sadness", "anxiety", "anger"]


def _parse_job_types(raw: str) -> List[str]:
    xs: List[str] = []
    for p in (raw or "").split(","):
        s = p.strip()
        if s:
            xs.append(s)
    return xs


# Always include the core job types required by the current pipeline even when
# ASTOR_WORKER_JOB_TYPES is left at an older/stale value in Render.
_REQUIRED_WORKER_JOB_TYPES: List[str] = [
    "myprofile_latest_refresh_v1",
    "snapshot_generate_v1",
    "analyze_emotion_structure_standard_v1",
    "analyze_emotion_structure_deep_v1",
    "generate_emotion_report_v2",
    "inspect_emotion_report_v1",
]


def _merge_required_job_types(job_types: List[str]) -> List[str]:
    merged: List[str] = []
    seen = set()
    for jt in list(job_types or []) + list(_REQUIRED_WORKER_JOB_TYPES):
        s = str(jt or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        merged.append(s)
    return merged



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


def _build_myweb_ready_push_payload(report_type: str) -> Dict[str, Any]:
    rt = str(report_type or "").strip().lower()
    body = "新しいレポートが届きました"
    if rt == "daily":
        body = "今日の自己観測が届きました"
    elif rt == "weekly":
        body = "今週の自己観測レポートが完成しました"
    elif rt == "monthly":
        body = "今月の自己構造レポートが完成しました"

    return {
        "title": "Cocolon",
        "body": body,
        "data": {
            "type": "myweb_report",
            "screen": "MyWeb",
            "report_type": (rt or "unknown"),
        },
    }


async def _send_myweb_report_ready_push(*, user_id: str, report_row: Dict[str, Any]) -> bool:
    uid = str(user_id or "").strip()
    if not uid:
        return False

    token_map = await _fetch_push_tokens_for_users([uid])
    tokens = [str(tok or "").strip() for tok in list((token_map or {}).values()) if str(tok or "").strip()]
    if not tokens:
        return False

    push_payload = _build_myweb_ready_push_payload(str((report_row or {}).get("report_type") or ""))
    data_payload = dict((push_payload or {}).get("data") or {})

    report_id = str((report_row or {}).get("id") or "").strip()
    if report_id:
        data_payload["report_id"] = report_id

    period_start = (report_row or {}).get("period_start")
    if period_start:
        data_payload["period_start"] = str(period_start)

    period_end = (report_row or {}).get("period_end")
    if period_end:
        data_payload["period_end"] = str(period_end)

    await _send_fcm_push(
        tokens=tokens,
        title=str((push_payload or {}).get("title") or "Cocolon"),
        body=str((push_payload or {}).get("body") or "新しいレポートが届きました"),
        data=data_payload,
    )
    return True


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
    previous_status = str(pub.get("status") or "").strip().upper()

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

    ready_push_sent = False
    if patched and status == "READY" and previous_status != "READY":
        try:
            ready_push_sent = await _send_myweb_report_ready_push(user_id=uid, report_row=row)
        except Exception as exc:
            WORKER_LOGGER.warning(
                "MyWeb READY push failed. user=%s report_id=%s err=%s",
                uid,
                report_id,
                exc,
            )

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
        "previous_status": (previous_status or None),
        "ready_push_sent": bool(ready_push_sent),
    }



def _scope_from_emotion_period_scope(scope: str) -> str:
    sc = str(scope or "").strip()
    if sc.startswith("emotion_daily:"):
        return "daily"
    if sc.startswith("emotion_weekly:"):
        return "weekly"
    if sc.startswith("emotion_monthly:"):
        return "monthly"
    return "unknown"


async def _fetch_latest_public_snapshot_row(*, user_id: str, scope: str) -> Optional[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    sc = str(scope or "").strip()
    if not uid or not sc:
        return None
    try:
        resp = await sb_get(
            f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
            params={
                "select": "id,user_id,scope,snapshot_type,source_hash,payload,created_at",
                "user_id": f"eq.{uid}",
                "scope": f"eq.{sc}",
                "snapshot_type": "eq.public",
                "order": "created_at.desc",
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


async def _upsert_analysis_result(*, row: Dict[str, Any]) -> bool:
    resp = await sb_post(
        f"/rest/v1/{ANALYSIS_RESULTS_TABLE}",
        json=row,
        params={"on_conflict": "target_user_id,snapshot_id,analysis_type,analysis_stage"},
        prefer="resolution=merge-duplicates,return=minimal",
        timeout=10.0,
    )
    return resp.status_code in (200, 201, 204)


def _entries_in_window(entries: List[Any], start_dt: datetime, end_dt: datetime) -> List[Any]:
    out: List[Any] = []
    for e in entries or []:
        try:
            s = str(getattr(e, "timestamp", "") or "")
            if not s:
                continue
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
        except Exception:
            continue
        if start_dt <= dt < end_dt:
            out.append(e)
    return out


def _normalize_entries_to_jst(entries: List[Any]) -> List[Any]:
    out: List[Any] = []
    for e in entries or []:
        try:
            s = str(getattr(e, "timestamp", "") or "")
            if not s:
                out.append(e)
                continue
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            jst_dt = dt.astimezone(JST)
            try:
                e.timestamp = jst_dt.isoformat()
            except Exception:
                pass
            try:
                e.date = jst_dt.date().isoformat()
            except Exception:
                pass
        except Exception:
            pass
        out.append(e)
    return out


def _deep_label(label: str) -> str:
    s = str(label or "").strip().lower()
    if s == "peace":
        return "calm"
    return s


def _parse_entry_dt(entry: Any) -> Optional[datetime]:
    try:
        s = str(getattr(entry, "timestamp", "") or "")
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST)
    except Exception:
        return None


def _deep_time_bucket(dt: Optional[datetime]) -> str:
    if not isinstance(dt, datetime):
        return "unknown"
    h = int(dt.hour)
    if 0 <= h < 6:
        return "0-6"
    if 6 <= h < 12:
        return "6-12"
    if 12 <= h < 18:
        return "12-18"
    return "18-24"


def _extract_memo_keywords(text: str) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    stopwords = {
        "こと", "もの", "感じ", "ちょっと", "かな", "けど", "ので", "ため", "よう", "さん", "する", "した",
        "して", "ある", "いる", "なる", "今日", "昨日", "明日", "ほんと", "なんか", "そして", "また",
        "それ", "これ", "そこ", "ここ", "です", "ます", "だった", "だっ", "the", "and", "for", "with",
    }
    tokens: List[str] = []
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9_-]{1,20}|[一-龯ぁ-んァ-ヴー]{2,12}", raw):
        tok = str(m.group(0) or "").strip().lower()
        if len(tok) < 2 or tok in stopwords:
            continue
        tokens.append(tok)
    uniq: List[str] = []
    seen = set()
    for tok in tokens:
        if tok in seen:
            continue
        seen.add(tok)
        uniq.append(tok)
    return uniq[:8]


def _mean(xs: List[float]) -> Optional[float]:
    vals = [float(x) for x in xs if x is not None]
    if not vals:
        return None
    return float(sum(vals) / len(vals))


def _median(xs: List[float]) -> Optional[float]:
    vals = [float(x) for x in xs if x is not None]
    if not vals:
        return None
    try:
        return float(statistics.median(vals))
    except Exception:
        vals = sorted(vals)
        mid = len(vals) // 2
        if len(vals) % 2:
            return float(vals[mid])
        return float((vals[mid - 1] + vals[mid]) / 2.0)


def _p75(xs: List[float]) -> Optional[float]:
    vals = sorted(float(x) for x in xs if x is not None)
    if not vals:
        return None
    idx = max(0, min(len(vals) - 1, int(math.ceil(0.75 * len(vals))) - 1))
    return float(vals[idx])


def _build_transition_records(entries: List[Any]) -> List[Dict[str, Any]]:
    seq = sorted(list(entries or []), key=lambda e: str(getattr(e, "timestamp", "") or ""))
    out: List[Dict[str, Any]] = []
    for prev, cur in zip(seq, seq[1:]):
        prev_dt = _parse_entry_dt(prev)
        cur_dt = _parse_entry_dt(cur)
        if prev_dt is None or cur_dt is None:
            continue
        delta_minutes = max(0.0, float((cur_dt - prev_dt).total_seconds()) / 60.0)
        from_label = _deep_label(str(getattr(prev, "label", "") or ""))
        to_label = _deep_label(str(getattr(cur, "label", "") or ""))
        if from_label not in DEEP_UI_LABELS or to_label not in DEEP_UI_LABELS:
            continue
        memo_text = "\n".join(
            [
                str(getattr(prev, "memo", "") or "").strip(),
                str(getattr(cur, "memo", "") or "").strip(),
            ]
        ).strip()
        out.append(
            {
                "from_label": from_label,
                "to_label": to_label,
                "minutes": delta_minutes,
                "time_bucket": _deep_time_bucket(prev_dt),
                "from_intensity": int(getattr(prev, "intensity", 0) or 0),
                "to_intensity": int(getattr(cur, "intensity", 0) or 0),
                "from_timestamp": prev_dt.isoformat(),
                "to_timestamp": cur_dt.isoformat(),
                "memo": memo_text,
                "keywords": _extract_memo_keywords(memo_text),
            }
        )
    return out


def _choose_cluster_labels(vectors: List[List[float]], max_patterns: int) -> tuple[List[int], str]:
    n = len(vectors)
    if n <= 0:
        return ([], "none")
    if n == 1:
        return ([0], "single")

    try:
        import hdbscan  # type: ignore
        clusterer = hdbscan.HDBSCAN(min_cluster_size=max(2, min(3, n)), min_samples=1, allow_single_cluster=True)
        labels = list(clusterer.fit_predict(vectors))
        # noise points become individual clusters to keep downstream deterministic
        next_id = (max([x for x in labels if x >= 0], default=-1) + 1)
        for i, val in enumerate(labels):
            if val < 0:
                labels[i] = next_id
                next_id += 1
        return (labels, "hdbscan")
    except Exception:
        pass

    try:
        from sklearn.cluster import AgglomerativeClustering  # type: ignore
        from sklearn.metrics import silhouette_score  # type: ignore
        from sklearn.preprocessing import StandardScaler  # type: ignore

        X = StandardScaler().fit_transform(vectors)
        if n == 2:
            return ([0, 1], "agglomerative_fallback")

        best_labels: Optional[List[int]] = None
        best_score = -1.0
        upper = max(2, min(max_patterns, n))
        for k in range(2, upper + 1):
            try:
                model = AgglomerativeClustering(n_clusters=k)
                labels = list(model.fit_predict(X))
                if len(set(labels)) < 2:
                    continue
                score = float(silhouette_score(X, labels))
                if score > best_score:
                    best_score = score
                    best_labels = labels
            except Exception:
                continue
        if best_labels is not None:
            return (best_labels, "agglomerative")
    except Exception:
        pass

    return ([0 for _ in range(n)], "single_fallback")


def _pattern_label_from_edges(edges: List[Dict[str, Any]]) -> str:
    if not edges:
        return "制御傾向"
    top = sorted(edges, key=lambda x: int(x.get("count", 0) or 0), reverse=True)[0]
    to_label = str(top.get("to_label") or "")
    from_label = str(top.get("from_label") or "")
    if to_label in ("calm", "joy"):
        return "回復傾向"
    if to_label == "sadness":
        return "沈静傾向"
    if from_label == to_label:
        return "停滞傾向"
    if to_label in ("anxiety", "anger"):
        return "緊張循環傾向"
    return "制御傾向"


def _pattern_description(pattern_label: str, edges: List[Dict[str, Any]]) -> str:
    if not edges:
        return "この期間の感情の流れから、1つの制御傾向が観測されました。"
    top = sorted(edges, key=lambda x: int(x.get("count", 0) or 0), reverse=True)[:2]
    route = " / ".join([f"{e.get('from_label')}→{e.get('to_label')}" for e in top])
    if pattern_label == "回復傾向":
        return f"{route} の流れが比較的多く、整え直す方向への移動が見られます。"
    if pattern_label == "沈静傾向":
        return f"{route} の流れが見られ、感情を落ち着かせる方向への移動が観測されます。"
    if pattern_label == "停滞傾向":
        return f"{route} の流れが見られ、同じ感情圏にとどまりやすい傾向があります。"
    if pattern_label == "緊張循環傾向":
        return f"{route} の流れが見られ、張りつめた感情圏を行き来する傾向があります。"
    return f"{route} の流れが見られ、この期間の特徴的な感情移動として観測されました。"


def _build_deep_control_model_payload(entries: List[Any], *, scope_kind: str, period_label: str) -> Dict[str, Any]:
    transitions = _build_transition_records(entries)
    transition_matrix: Dict[str, Dict[str, int]] = {
        from_label: {to_label: 0 for to_label in DEEP_UI_LABELS} for from_label in DEEP_UI_LABELS
    }
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    keyword_stats: Dict[str, Dict[str, Any]] = {}

    for t in transitions:
        from_label = str(t.get("from_label") or "")
        to_label = str(t.get("to_label") or "")
        if from_label in transition_matrix and to_label in transition_matrix[from_label]:
            transition_matrix[from_label][to_label] += 1
        key = f"{from_label}->{to_label}"
        grouped[key].append(t)
        for kw in list(t.get("keywords") or []):
            stat = keyword_stats.setdefault(kw, {
                "count": 0,
                "related_emotions": Counter(),
                "related_transitions": Counter(),
                "time_buckets": Counter(),
            })
            stat["count"] += 1
            stat["related_emotions"][from_label] += 1
            stat["related_emotions"][to_label] += 1
            stat["related_transitions"][key] += 1
            stat["time_buckets"][str(t.get("time_bucket") or "unknown")] += 1

    total_transitions = max(1, len(transitions))
    transition_edges: List[Dict[str, Any]] = []
    recovery_time: List[Dict[str, Any]] = []
    edge_vectors: List[List[float]] = []

    label_index = {lab: idx for idx, lab in enumerate(DEEP_UI_LABELS)}
    bucket_index = {"0-6": 0.0, "6-12": 1.0, "12-18": 2.0, "18-24": 3.0, "unknown": 1.5}

    for key, rows in grouped.items():
        from_label, to_label = key.split("->", 1)
        minutes = [float(r.get("minutes") or 0.0) for r in rows]
        mean_minutes = _mean(minutes)
        edge = {
            "from_label": from_label,
            "to_label": to_label,
            "count": len(rows),
            "share": round(float(len(rows)) / float(total_transitions), 4),
            "mean_minutes": round(mean_minutes, 2) if mean_minutes is not None else None,
            "median_minutes": round(_median(minutes), 2) if _median(minutes) is not None else None,
            "p75_minutes": round(_p75(minutes), 2) if _p75(minutes) is not None else None,
            "mean_intensity_from": round(_mean([float(r.get("from_intensity") or 0) for r in rows]) or 0.0, 2),
            "mean_intensity_to": round(_mean([float(r.get("to_intensity") or 0) for r in rows]) or 0.0, 2),
            "dominant_time_buckets": [k for k, _ in Counter([str(r.get("time_bucket") or "unknown") for r in rows]).most_common(2)],
            "evidence": {"count": len(rows)},
            "notes": [],
        }
        transition_edges.append(edge)
        recovery_time.append(
            {
                "from_label": from_label,
                "to_label": to_label,
                "count": len(rows),
                "mean_minutes": edge.get("mean_minutes"),
                "median_minutes": edge.get("median_minutes"),
                "min_minutes": round(min(minutes), 2) if minutes else None,
                "max_minutes": round(max(minutes), 2) if minutes else None,
                "dominant_time_buckets": list(edge.get("dominant_time_buckets") or []),
                "evidence": {"count": len(rows)},
                "notes": [],
            }
        )
        dominant_bucket = list(edge.get("dominant_time_buckets") or ["unknown"])[0]
        edge_vectors.append(
            [
                float(label_index.get(from_label, 0)),
                float(label_index.get(to_label, 0)),
                math.log1p(float(len(rows))),
                math.log1p(float(mean_minutes or 0.0) + 1.0),
                float(edge.get("mean_intensity_from") or 0.0),
                float(edge.get("mean_intensity_to") or 0.0),
                float(bucket_index.get(dominant_bucket, 1.5)),
            ]
        )

    transition_edges.sort(key=lambda x: (int(x.get("count", 0) or 0), float(x.get("share") or 0.0)), reverse=True)
    recovery_time.sort(key=lambda x: (int(x.get("count", 0) or 0), float(x.get("mean_minutes") or 0.0) * -1.0), reverse=True)

    memo_triggers: List[Dict[str, Any]] = []
    for keyword, stat in sorted(keyword_stats.items(), key=lambda kv: int((kv[1] or {}).get("count") or 0), reverse=True)[:20]:
        memo_triggers.append(
            {
                "keyword": keyword,
                "count": int(stat.get("count") or 0),
                "related_emotions": [k for k, _ in stat["related_emotions"].most_common(5)],
                "related_transitions": [k for k, _ in stat["related_transitions"].most_common(5)],
                "dominant_time_buckets": [k for k, _ in stat["time_buckets"].most_common(2)],
                "evidence": {"count": int(stat.get("count") or 0)},
                "notes": [],
            }
        )

    cluster_labels, clustering_name = _choose_cluster_labels(edge_vectors, DEEP_MAX_CONTROL_PATTERNS)
    clusters: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for edge, label in zip(transition_edges, cluster_labels):
        clusters[int(label)].append(edge)

    control_patterns: List[Dict[str, Any]] = []
    total_edge_count = max(1, sum(int(e.get("count", 0) or 0) for e in transition_edges))
    for idx, (_cluster_id, edges_in_cluster) in enumerate(sorted(clusters.items(), key=lambda kv: sum(int(e.get("count", 0) or 0) for e in kv[1]), reverse=True)[:DEEP_MAX_CONTROL_PATTERNS], start=1):
        edge_keys = [f"{e.get('from_label')}->{e.get('to_label')}" for e in edges_in_cluster]
        dominant_buckets = Counter([b for e in edges_in_cluster for b in list(e.get("dominant_time_buckets") or [])]).most_common(2)
        pattern_memos = [m for m in memo_triggers if set(m.get("related_transitions") or []).intersection(edge_keys)]
        size = sum(int(e.get("count", 0) or 0) for e in edges_in_cluster)
        p_label = _pattern_label_from_edges(edges_in_cluster)
        control_patterns.append(
            {
                "pattern_id": f"pattern_{idx}",
                "label": p_label,
                "description": _pattern_description(p_label, edges_in_cluster),
                "size": int(size),
                "score": round(float(size) / float(total_edge_count), 4),
                "transition_keys": edge_keys,
                "representative_edges": edges_in_cluster[:3],
                "memo_triggers": pattern_memos[:3],
                "dominant_time_buckets": [k for k, _ in dominant_buckets],
                "evidence": {"edgeCount": len(edges_in_cluster), "transitionCount": int(size)},
                "notes": [],
            }
        )

    top_edges = [f"{e.get('from_label')}→{e.get('to_label')}" for e in transition_edges[:5]]
    return {
        "period": period_label,
        "scope": scope_kind,
        "transition_matrix": transition_matrix,
        "transition_edges": transition_edges,
        "recovery_time": recovery_time,
        "memo_triggers": memo_triggers[:10],
        "control_patterns": control_patterns,
        "summary": {
            "transitionCount": len(transitions),
            "edgeCount": len(transition_edges),
            "memoKeywordCount": len(memo_triggers),
            "patternCount": len(control_patterns),
            "dominantTransitions": top_edges,
        },
        "meta": {
            "analysisVersion": "emotion_structure.deep.v1",
            "clustering": clustering_name,
            "memoMode": "keyword",
            "maxPatterns": DEEP_MAX_CONTROL_PATTERNS,
        },
        "notes": [
            "この deep モデルでは、連続するすべての感情遷移を観測対象として扱っています。",
            "制御パターン数はデータから決まり、最大5件まで返します。",
        ],
    }


async def _handle_analyze_emotion_structure_deep_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    scope = str((payload or {}).get("scope") or "").strip()
    if not scope:
        raise ValueError("payload.scope is required")

    scope_kind = _scope_from_emotion_period_scope(scope)
    if scope_kind not in ("daily", "weekly", "monthly"):
        raise ValueError(f"unsupported scope for emotion structure deep analysis: {scope}")

    snap = await _fetch_latest_public_snapshot_row(user_id=uid, scope=scope)
    if not snap:
        raise RuntimeError("public emotion_period snapshot not found")

    period_info = _parse_emotion_period_scope(scope)
    start_iso = str(period_info.get("period_start_iso") or "").strip()
    end_iso = str(period_info.get("period_end_iso") or "").strip()
    if not start_iso or not end_iso:
        raise RuntimeError("snapshot period meta missing")

    rows = await fetch_emotions_in_range(uid, start_iso=start_iso, end_iso=end_iso, include_secret=False)
    entries = _normalize_entries_to_jst(build_emotion_entries_from_rows(rows))
    period_label = f"{start_iso}..{end_iso}"

    deep_model = _build_deep_control_model_payload(entries, scope_kind=scope_kind, period_label=period_label)
    analysis_payload: Dict[str, Any] = {
        "engine": "analysis_engine",
        "analysis_type": "emotion_structure",
        "scope": scope_kind,
        "analysis_stage": "deep",
        "analysis_version": "emotion_structure.deep.v1",
        "source_hash": str(snap.get("source_hash") or ""),
        "snapshot_ref": {
            "snapshot_id": str(snap.get("id") or ""),
            "scope": scope,
            "snapshot_type": "public",
        },
        "period": {
            "start_iso": start_iso,
            "end_iso": end_iso,
        },
        "entry_count": len(entries),
        "deep_control_model": deep_model,
        "controlPatterns": list(deep_model.get("control_patterns") or []),
        "transitionMatrix": deep_model.get("transition_matrix") or {},
        "transitionEdges": list(deep_model.get("transition_edges") or []),
        "recoveryTime": list(deep_model.get("recovery_time") or []),
        "memoTriggers": list(deep_model.get("memo_triggers") or []),
    }

    row = {
        "target_user_id": uid,
        "snapshot_id": str(snap.get("id") or ""),
        "analysis_type": "emotion_structure",
        "scope": scope_kind,
        "analysis_stage": "deep",
        "analysis_version": "emotion_structure.deep.v1",
        "source_hash": str(snap.get("source_hash") or "") or None,
        "payload": analysis_payload,
        "updated_at": _now_iso_z(),
    }
    ok = await _upsert_analysis_result(row=row)
    if not ok:
        raise RuntimeError("analysis_results upsert failed")

    return {
        "status": "ok",
        "user_id": uid,
        "scope": scope,
        "scope_kind": scope_kind,
        "snapshot_id": str(snap.get("id") or ""),
        "source_hash": str(snap.get("source_hash") or ""),
        "entry_count": len(entries),
        "analysis_stage": "deep",
        "analysis_version": "emotion_structure.deep.v1",
        "pattern_count": int(len(list(deep_model.get("control_patterns") or []))),
    }


async def _handle_analyze_emotion_structure_standard_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    scope = str((payload or {}).get("scope") or "").strip()
    if not scope:
        raise ValueError("payload.scope is required")

    scope_kind = _scope_from_emotion_period_scope(scope)
    if scope_kind not in ("daily", "weekly", "monthly"):
        raise ValueError(f"unsupported scope for emotion structure analysis: {scope}")

    snap = await _fetch_latest_public_snapshot_row(user_id=uid, scope=scope)
    if not snap:
        raise RuntimeError("public emotion_period snapshot not found")

    period_info = _parse_emotion_period_scope(scope)
    start_iso = str(period_info.get("period_start_iso") or "").strip()
    end_iso = str(period_info.get("period_end_iso") or "").strip()
    if not start_iso or not end_iso:
        raise RuntimeError("snapshot period meta missing")

    rows = await fetch_emotions_in_range(
        uid,
        start_iso=start_iso,
        end_iso=end_iso,
        include_secret=False,
    )
    entries = _normalize_entries_to_jst(build_emotion_entries_from_rows(rows))

    period_label = f"{start_iso}..{end_iso}"

    analysis_payload: Dict[str, Any] = {
        "engine": "analysis_engine",
        "analysis_type": "emotion_structure",
        "scope": scope_kind,
        "analysis_stage": "standard",
        "analysis_version": "emotion_structure.standard.v1",
        "source_hash": str(snap.get("source_hash") or ""),
        "snapshot_ref": {
            "snapshot_id": str(snap.get("id") or ""),
            "scope": scope,
            "snapshot_type": "public",
        },
        "period": {
            "start_iso": start_iso,
            "end_iso": end_iso,
        },
        "entry_count": len(entries),
    }

    if scope_kind == "daily":
        narrative = narrate_daily(entries, period=period_label)
        analysis_payload["narrative"] = narrative.to_dict()
    elif scope_kind == "weekly":
        weekly_snapshot = build_weekly_features(entries, period=period_label)
        narrative = narrate_weekly(weekly_snapshot, baseline=None)
        weekly_snapshot_dict = weekly_snapshot.to_dict()
        analysis_payload["weekly_snapshot"] = weekly_snapshot_dict
        if isinstance(weekly_snapshot_dict.get("time_buckets"), list):
            analysis_payload["time_buckets"] = weekly_snapshot_dict.get("time_buckets") or []
        analysis_payload["narrative"] = narrative.to_dict()
    else:
        period_start_utc = period_info.get("period_start_utc")
        if not isinstance(period_start_utc, datetime):
            raise RuntimeError("invalid monthly period_start_utc")

        weeks = []
        for i in range(4):
            w_start = period_start_utc + timedelta(days=7 * i)
            w_end = w_start + timedelta(days=7)
            w_entries = _entries_in_window(entries, w_start, w_end)
            weeks.append(build_weekly_features(w_entries, period=f"{w_start.date().isoformat()}..{(w_end - timedelta(days=1)).date().isoformat()}"))

        monthly_report = assemble_monthly(weeks, period=period_label)
        narrative = narrate_monthly(monthly_report)
        monthly_report_dict = monthly_report.to_dict()
        analysis_payload["monthly_report"] = monthly_report_dict
        if isinstance(monthly_report_dict.get("time_buckets"), list):
            analysis_payload["time_buckets"] = monthly_report_dict.get("time_buckets") or []
        analysis_payload["narrative"] = narrative.to_dict()

    row = {
        "target_user_id": uid,
        "snapshot_id": str(snap.get("id") or ""),
        "analysis_type": "emotion_structure",
        "scope": scope_kind,
        "analysis_stage": "standard",
        "analysis_version": "emotion_structure.standard.v1",
        "source_hash": str(snap.get("source_hash") or "") or None,
        "payload": analysis_payload,
        "updated_at": _now_iso_z(),
    }
    ok = await _upsert_analysis_result(row=row)
    if not ok:
        raise RuntimeError("analysis_results upsert failed")

    return {
        "status": "ok",
        "user_id": uid,
        "scope": scope,
        "scope_kind": scope_kind,
        "snapshot_id": str(snap.get("id") or ""),
        "source_hash": str(snap.get("source_hash") or ""),
        "entry_count": len(entries),
        "analysis_stage": "standard",
        "analysis_version": "emotion_structure.standard.v1",
    }


async def _worker_loop() -> None:
    worker_id = (os.getenv("ASTOR_WORKER_ID") or "").strip() or f"astor-worker-{os.getpid()}"
    poll_interval = float(os.getenv("ASTOR_WORKER_POLL_INTERVAL_SECONDS", "1.0") or "1.0")
    job_types = _merge_required_job_types(
        _parse_job_types(
            os.getenv(
                "ASTOR_WORKER_JOB_TYPES",
                "myprofile_latest_refresh_v1,snapshot_generate_v1,analyze_emotion_structure_standard_v1,analyze_emotion_structure_deep_v1,generate_emotion_report_v2,inspect_emotion_report_v1",
            )
        )
    )

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
                            # NOTE:
                            # Downstream jobs must be enqueued even when the snapshot row was not newly inserted.
                            # Otherwise, after deploying a new analysis/report pipeline, existing unchanged snapshots
                            # would never trigger downstream processing.
                            # Job coalescing is handled by astor_job_queue via job_key.
                            if scope == SNAPSHOT_SCOPE_DEFAULT:

                                # Auto-enqueue emotion_period snapshots (weekly/monthly) for future snapshot-driven analysis.
                                # We intentionally keep daily out of this branch to preserve the existing daily
                                # distribution timing path.
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
                                # emotion_period snapshot committed (or already existed) -> enqueue emotion structure analysis.
                                if (
                                    scope.startswith("emotion_daily:")
                                    or scope.startswith("emotion_weekly:")
                                    or scope.startswith("emotion_monthly:")
                                ):
                                    try:
                                        pub_hash = str(public.get("source_hash") or "")
                                        if not pub_hash:
                                            raise RuntimeError("public source_hash missing for emotion_period scope")
                                        await enqueue_job(
                                            job_key=f"analysis_emotion_structure_standard:{claimed.user_id}:{scope}:{pub_hash}",
                                            job_type="analyze_emotion_structure_standard_v1",
                                            user_id=claimed.user_id,
                                            payload={
                                                "trigger": "snapshot_generate_v1",
                                                "requested_at": (claimed.payload or {}).get("requested_at"),
                                                "scope": scope,
                                                "source_hash": pub_hash,
                                            },
                                            priority=18,
                                        )
                                    except Exception as exc:
                                        logger.error("Downstream analysis enqueue failed: %s", exc)
                        except Exception as exc:
                            logger.error("Downstream enqueue failed: %s", exc)
                logger.info("job done. key=%s type=%s user=%s res=%s", claimed.job_key, claimed.job_type, claimed.user_id, snap_res)
            elif claimed.job_type == "analyze_emotion_structure_standard_v1":
                analysis_res = await _handle_analyze_emotion_structure_standard_v1(
                    user_id=claimed.user_id,
                    payload=(claimed.payload or {}),
                )
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
                else:
                    try:
                        if EMOTION_REPORT_V2_ENABLED:
                            scope = str((analysis_res or {}).get("scope") or (claimed.payload or {}).get("scope") or "").strip()
                            pub_hash = str((analysis_res or {}).get("source_hash") or (claimed.payload or {}).get("source_hash") or "").strip()
                            if scope and pub_hash:
                                include_astor = not scope.startswith("emotion_daily:")
                                await enqueue_job(
                                    job_key=f"analysis_emotion_structure_deep:{claimed.user_id}:{scope}:{pub_hash}",
                                    job_type="analyze_emotion_structure_deep_v1",
                                    user_id=claimed.user_id,
                                    payload={
                                        "trigger": "analyze_emotion_structure_standard_v1",
                                        "requested_at": (claimed.payload or {}).get("requested_at"),
                                        "scope": scope,
                                        "source_hash": pub_hash,
                                    },
                                    priority=17,
                                )
                                await enqueue_job(
                                    job_key=f"emotion_report_v2_refresh:{claimed.user_id}:{scope}:{pub_hash}",
                                    job_type="generate_emotion_report_v2",
                                    user_id=claimed.user_id,
                                    payload={
                                        "trigger": "analyze_emotion_structure_standard_v1",
                                        "requested_at": (claimed.payload or {}).get("requested_at"),
                                        "scope": scope,
                                        "include_astor": include_astor,
                                        "source_hash": pub_hash,
                                    },
                                    priority=12,
                                )
                    except Exception as exc:
                        logger.error("Emotion report enqueue after analysis failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    analysis_res,
                )
            elif claimed.job_type == "analyze_emotion_structure_deep_v1":
                analysis_res = await _handle_analyze_emotion_structure_deep_v1(
                    user_id=claimed.user_id,
                    payload=(claimed.payload or {}),
                )
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
                else:
                    try:
                        if EMOTION_REPORT_V2_ENABLED:
                            scope = str((analysis_res or {}).get("scope") or (claimed.payload or {}).get("scope") or "").strip()
                            pub_hash = str((analysis_res or {}).get("source_hash") or (claimed.payload or {}).get("source_hash") or "").strip()
                            if scope and pub_hash:
                                include_astor = not scope.startswith("emotion_daily:")
                                await enqueue_job(
                                    job_key=f"emotion_report_v2_refresh:{claimed.user_id}:{scope}:{pub_hash}",
                                    job_type="generate_emotion_report_v2",
                                    user_id=claimed.user_id,
                                    payload={
                                        "trigger": "analyze_emotion_structure_deep_v1",
                                        "requested_at": (claimed.payload or {}).get("requested_at"),
                                        "scope": scope,
                                        "include_astor": include_astor,
                                        "source_hash": pub_hash,
                                    },
                                    priority=11,
                                )
                    except Exception as exc:
                        logger.error("Emotion report enqueue after deep analysis failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    analysis_res,
                )
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