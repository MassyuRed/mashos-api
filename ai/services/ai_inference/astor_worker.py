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
  - ASTOR_WORKER_JOB_TYPES=myprofile_latest_refresh_v1,snapshot_generate_v1,analyze_emotion_structure_standard_v1,analyze_emotion_structure_deep_v1,analyze_self_structure_standard_v1,analyze_self_structure_deep_v1,generate_premium_reflections_v1,inspect_reflection_v1,generate_emotion_report_v2,inspect_emotion_report_v1,refresh_ranking_board_v1,inspect_ranking_board_v1,refresh_account_status_v1,inspect_account_status_v1,refresh_friend_feed_v1,inspect_friend_feed_v1,refresh_global_summary_v1,inspect_global_summary_v1   (comma separated)
  - ASTOR_WORKER_LOG_LEVEL=INFO

This worker consumes jobs enqueued by API (e.g., emotion/submit) and executes
heavy tasks out-of-process, improving API stability.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import signal
import statistics
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx

_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))


def _install_optional_perf_runtime_stubs() -> None:
    """Keep worker startup alive if additive perf helper modules are absent.

    Some deployments may momentarily run the worker on a revision where helper
    files (response_microcache / request_metrics) are missing or not yet synced.
    In that case we degrade to no-op behavior instead of crash-looping at import
    time before the worker can even start polling jobs.
    """

    if "request_metrics" not in sys.modules:
        try:
            import request_metrics  # type: ignore  # noqa: F401
        except Exception:
            stub = types.ModuleType("request_metrics")

            def _noop(*args, **kwargs):
                return None

            stub.begin_request_metrics = lambda *args, **kwargs: None  # type: ignore[attr-defined]
            stub.finish_request_metrics = _noop  # type: ignore[attr-defined]
            stub.snapshot_request_metrics = lambda: {}  # type: ignore[attr-defined]
            stub.record_cache_coalesced = _noop  # type: ignore[attr-defined]
            stub.record_cache_hit = _noop  # type: ignore[attr-defined]
            stub.record_cache_miss = _noop  # type: ignore[attr-defined]
            stub.record_supabase_call = _noop  # type: ignore[attr-defined]
            sys.modules["request_metrics"] = stub

    if "response_microcache" not in sys.modules:
        try:
            import response_microcache  # type: ignore  # noqa: F401
        except Exception:
            stub = types.ModuleType("response_microcache")

            async def _get_or_compute(key, ttl_seconds, producer, *, ttl_resolver=None):
                return await producer()

            def _build_cache_key(prefix, payload=None):
                base = str(prefix or "").strip().rstrip(":")
                if not payload:
                    return base
                try:
                    encoded = json.dumps(
                        payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        default=str,
                    )
                except Exception:
                    encoded = str(payload)
                return f"{base}:{encoded}"

            async def _invalidate_prefix(prefix):
                return 0

            async def _invalidate_exact(key):
                return 0

            stub.get_or_compute = _get_or_compute  # type: ignore[attr-defined]
            stub.build_cache_key = _build_cache_key  # type: ignore[attr-defined]
            stub.invalidate_prefix = _invalidate_prefix  # type: ignore[attr-defined]
            stub.invalidate_exact = _invalidate_exact  # type: ignore[attr-defined]
            sys.modules["response_microcache"] = stub


_install_optional_perf_runtime_stubs()

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
    _is_self_insight_only_row,
    _exclude_rows_by_ids,
)  # type: ignore

# Phase X+: emotion structure reports (MyWeb weekly/monthly)
from api_myweb_reports import (
    _build_target_period as _myweb_build_target_period,
    _generate_and_save_from_snapshot as _myweb_generate_and_save_from_snapshot,
)  # type: ignore

from api_emotion_submit import _fetch_push_tokens_for_users, _send_fcm_push  # type: ignore

try:
    from report_distribution_push_store import ReportDistributionPushStore
except Exception:  # pragma: no cover
    ReportDistributionPushStore = None  # type: ignore

# Generation lock (avoid concurrent snapshot generation per user/scope)
from generation_lock import build_lock_key, make_owner_id, release_lock, try_acquire_lock  # type: ignore

# analysis_engine (sibling package under ai/services/analysis_engine)
# NOTE:
# Render では package export (__init__.py) が古い/未反映でも動くように、
# まず sibling package の parent を sys.path へ追加し、submodule 直 import を優先する。
_services_root = Path(__file__).resolve().parent.parent
if str(_services_root) not in sys.path:
    sys.path.insert(0, str(_services_root))

# Emotion structure engine
try:
    from analysis_engine.emotion_structure_engine.weekly import build_weekly_features, narrate_weekly  # type: ignore
    from analysis_engine.emotion_structure_engine.monthly import assemble_monthly, narrate_monthly  # type: ignore
    from analysis_engine.emotion_structure_engine.daily import narrate_daily  # type: ignore
except Exception:
    # Backward-compatible fallback for older flat layouts.
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

# Self structure engine
from analysis_engine.self_structure_engine.signal_extraction import extract_signal_results  # type: ignore
from analysis_engine.self_structure_engine.fusion import fuse_signal_results  # type: ignore
from analysis_engine.self_structure_engine.builders import (  # type: ignore
    build_self_structure_standard_row,
    build_self_structure_deep_row,
)
from analysis_engine.models import BuildContext, SelfStructureInput  # type: ignore

from analysis_engine_adapter import build_emotion_entries_from_rows  # type: ignore
try:
    from analysis_engine_adapter import build_self_structure_inputs_from_snapshot_payload  # type: ignore
except Exception:  # pragma: no cover - backward compatibility while adapter lands
    build_self_structure_inputs_from_snapshot_payload = None  # type: ignore


from astor_reflection_engine import build_generation_plan as build_reflection_generation_plan  # type: ignore
from astor_reflection_store import (  # type: ignore
    fetch_active_generated_reflections,
    stage_generation_plan as stage_reflection_generation_plan,
    promote_reflection as promote_generated_reflection,
    reject_reflection as reject_generated_reflection,
    fail_reflection as fail_generated_reflection,
)

from astor_ranking_boards import (  # type: ignore
    RANKING_BOARDS_TABLE,
    RANKING_BOARD_VERSION,
    BOARD_STATUS_READY,
    fail_ranking_board,
    promote_ranking_board,
    select_board_rows,
    upsert_ranking_board_draft,
)
from astor_ranking_kernel import (  # type: ignore
    SUPPORTED_RANKING_METRICS,
    RANKING_RANGE_KEYS as RANKING_BOARD_RANGE_KEYS,
    generate_ranking_board,
)

from astor_account_status_store import (  # type: ignore
    ACCOUNT_STATUS_SUMMARIES_TABLE,
    ACCOUNT_STATUS_VERSION,
    STATUS_READY as ACCOUNT_STATUS_STATUS_READY,
    fail_account_status_summary,
    promote_account_status_summary,
    upsert_account_status_draft,
)
from astor_account_status_kernel import (  # type: ignore
    SUPPORTED_ACCOUNT_STATUS_TOTAL_KEYS,
    generate_account_status_summary,
)

from astor_friend_feed_store import (  # type: ignore
    FRIEND_FEED_SUMMARIES_TABLE,
    FRIEND_FEED_VERSION,
    FRIEND_FEED_MAX_ITEMS,
    ALLOWED_STRENGTHS as FRIEND_FEED_ALLOWED_STRENGTHS,
    STATUS_READY as FRIEND_FEED_STATUS_READY,
    fail_friend_feed_summary,
    promote_friend_feed_summary,
    select_friend_feed_items,
    upsert_friend_feed_draft,
)
from astor_friend_feed_kernel import (  # type: ignore
    generate_friend_feed,
)

from astor_global_summary_store import (  # type: ignore
    GLOBAL_ACTIVITY_SUMMARIES_TABLE,
    GLOBAL_SUMMARY_TIMEZONE,
    GLOBAL_SUMMARY_TOTAL_KEYS,
    GLOBAL_SUMMARY_VERSION,
    STATUS_READY as GLOBAL_SUMMARY_STATUS_READY,
    build_global_summary_source_hash,
    canonical_global_summary_activity_date,
    canonical_global_summary_timezone,
    fail_global_summary,
    promote_global_summary,
    upsert_global_summary_draft,
)
from astor_global_summary_kernel import (  # type: ignore
    generate_global_summary_payload,
)
from astor_global_summary_enqueue import (  # type: ignore
    resolve_global_summary_activity_date,
)


MYWEB_REPORTS_TABLE = (os.getenv("MYWEB_REPORTS_TABLE") or "myweb_reports").strip() or "myweb_reports"
MATERIAL_SNAPSHOTS_TABLE = (os.getenv("MATERIAL_SNAPSHOTS_TABLE") or "material_snapshots").strip() or "material_snapshots"
SNAPSHOT_SCOPE_DEFAULT = (os.getenv("SNAPSHOT_SCOPE_DEFAULT") or "global").strip() or "global"
ANALYSIS_RESULTS_TABLE = (os.getenv("ANALYSIS_RESULTS_TABLE") or "analysis_results").strip() or "analysis_results"
MYMODEL_REFLECTIONS_TABLE = (os.getenv("MYMODEL_REFLECTIONS_TABLE") or "mymodel_reflections").strip() or "mymodel_reflections"

# JST (UTC+9) fixed for MyWeb periods
JST = timezone(timedelta(hours=9))

EMOTION_REPORT_V2_ENABLED = (os.getenv("ASTOR_ENABLE_EMOTION_REPORT_V2", "false").strip().lower() == "true")

WORKER_LOGGER = logging.getLogger("astor_worker")

DEEP_MAX_CONTROL_PATTERNS = max(1, min(5, int(os.getenv("EMOTION_DEEP_MAX_CONTROL_PATTERNS", "5") or "5")))
DEEP_UI_LABELS: List[str] = ["joy", "sadness", "anxiety", "anger", "calm"]

_DEEP_PATTERN_LABEL_PRIORITY = ["calm", "joy", "sadness", "anxiety", "anger"]

_DEEP_EMOTION_LABELS: Dict[str, str] = {
    "joy": "喜び",
    "sadness": "悲しみ",
    "anxiety": "不安",
    "anger": "怒り",
    "calm": "平穏",
}

_DEEP_THEME_HINT_LABELS: Dict[str, str] = {
    "self_pressure": "自分を急がせる言葉",
    "interpersonal_caution": "人との距離を気にする言葉",
    "fatigue_limit": "限界を感じる言葉",
    "self_doubt": "自分を責めやすい言葉",
    "generic": "前に出ていた言葉",
}

_MONTHLY_PHASE_LABELS: Dict[str, str] = {
    "first_half": "前半",
    "second_half": "後半",
}


def _deep_emotion_label_ja(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    return _DEEP_EMOTION_LABELS.get(s, s)


def _deep_localize_transition_key(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    if "->" in s:
        left, right = s.split("->", 1)
        return f"{_deep_emotion_label_ja(left)} → {_deep_emotion_label_ja(right)}"
    if "→" in s:
        left, right = s.split("→", 1)
        return f"{_deep_emotion_label_ja(left)} → {_deep_emotion_label_ja(right)}"
    return _deep_emotion_label_ja(s)


def _deep_theme_hint_label(value: Any) -> str:
    hint = str(value or "generic").strip() or "generic"
    return _DEEP_THEME_HINT_LABELS.get(hint, _DEEP_THEME_HINT_LABELS["generic"])


def _iso_z(dt: datetime) -> str:
    value = dt
    if not isinstance(value, datetime):
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _quote_phrase(value: Any) -> str:
    s = str(value or "").strip().strip("「」『』\"'")
    if not s:
        return ""
    return f"「{s}」"


def _ordered_unique_strs(values: List[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in list(values or []):
        s = str(value or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


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
    "analyze_self_structure_standard_v1",
    "analyze_self_structure_deep_v1",
    "generate_premium_reflections_v1",
    "inspect_reflection_v1",
    "generate_emotion_report_v2",
    "inspect_emotion_report_v1",
    "refresh_ranking_board_v1",
    "inspect_ranking_board_v1",
    "refresh_account_status_v1",
    "inspect_account_status_v1",
    "refresh_friend_feed_v1",
    "inspect_friend_feed_v1",
    "refresh_global_summary_v1",
    "inspect_global_summary_v1",
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



NO_PUBLIC_EMOTION_SKIP_REASON = "no_public_emotion_entries"


def _extract_public_emotion_count_from_snapshot_row(snapshot_row: Optional[Dict[str, Any]]) -> int:
    payload = snapshot_row.get("payload") if isinstance(snapshot_row, dict) else {}
    summary = payload.get("summary") if isinstance(payload, dict) and isinstance(payload.get("summary"), dict) else {}
    try:
        return int(summary.get("emotions_public") or 0)
    except Exception:
        return 0


def _filter_non_self_insight_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    exclude_ids = {str(r.get("id") or "") for r in (rows or []) if _is_self_insight_only_row(r)}
    return _exclude_rows_by_ids(rows or [], exclude_ids) if exclude_ids else list(rows or [])


def _build_emotion_analysis_skip_result(
    *,
    user_id: str,
    scope: str,
    scope_kind: str,
    analysis_stage: str,
    analysis_version: str,
    snapshot_row: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    snap = snapshot_row if isinstance(snapshot_row, dict) else {}
    return {
        "status": "skipped_no_input",
        "user_id": str(user_id or "").strip(),
        "scope": str(scope or "").strip(),
        "scope_kind": str(scope_kind or "").strip(),
        "snapshot_id": str(snap.get("id") or ""),
        "source_hash": str(snap.get("source_hash") or ""),
        "entry_count": 0,
        "analysis_stage": analysis_stage,
        "analysis_version": analysis_version,
        "skip_reason": NO_PUBLIC_EMOTION_SKIP_REASON,
    }


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

    generated: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    errors: Dict[str, str] = {}
    for sc in scopes:
        try:
            _text, _json, _astor_text, meta = await _myweb_generate_and_save_from_snapshot(uid, scope=sc, include_astor=include_astor)
            rid = None
            rt = None
            pub_hash = None
            meta_status = "generated"
            skip_reason = None
            if isinstance(meta, dict):
                rid = meta.get("report_id")
                rt = meta.get("report_type")
                pub_hash = meta.get("public_source_hash")
                meta_status = str(meta.get("status") or "generated").strip() or "generated"
                skip_reason = str(meta.get("skip_reason") or "").strip() or None
            if meta_status == "skipped":
                skipped.append({
                    "scope": sc,
                    "report_type": rt,
                    "report_id": rid,
                    "public_source_hash": pub_hash,
                    "status": "skipped",
                    "skip_reason": skip_reason or NO_PUBLIC_EMOTION_SKIP_REASON,
                })
                continue
            generated.append({"scope": sc, "report_type": rt, "report_id": rid, "public_source_hash": pub_hash, "status": "ok"})
        except Exception as exc:
            errors[sc] = str(exc)

    if generated:
        return {"status": "ok", "user_id": uid, "generated": generated, "skipped": (skipped or None), "errors": (errors or None)}

    if skipped and not errors:
        return {"status": "skipped_no_input", "user_id": uid, "generated": [], "skipped": skipped, "errors": None}

    if skipped and errors:
        return {"status": "skipped_no_input", "user_id": uid, "generated": [], "skipped": skipped, "errors": errors}

    raise RuntimeError(f"generate_emotion_report_v2 failed: {errors}")


# ----------------------------
# Inspection: Emotion report (MyWeb) publish gating
# ----------------------------

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Very loose phone detector (JP + general digit sequences)
_PHONE_RE = re.compile(r"(?:\b0\d{1,4}[- ]?\d{1,4}[- ]?\d{4}\b|\b\d{10,11}\b)")


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_distribution_key(raw: Any) -> Optional[str]:
    s = str(raw or "").strip()
    if not s:
        return None
    return s if len(s) == 10 else None


def _distribution_key_from_requested_at(raw: Any) -> Optional[str]:
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST).date().isoformat()
    except Exception:
        return None


def _emotion_distribution_family(report_type: Any) -> Optional[str]:
    rt = str(report_type or "").strip().lower()
    if rt == "daily":
        return "emotion_daily"
    if rt == "weekly":
        return "emotion_weekly"
    if rt == "monthly":
        return "emotion_monthly"
    return None


async def _enqueue_emotion_report_distribution_candidate(
    *,
    user_id: str,
    report_row: Dict[str, Any],
    payload: Dict[str, Any],
) -> bool:
    if ReportDistributionPushStore is None:
        return False
    if not bool((payload or {}).get("distribution_origin")):
        return False
    distribution_key = (
        _normalize_distribution_key((payload or {}).get("distribution_key"))
        or _distribution_key_from_requested_at((payload or {}).get("requested_at"))
    )
    if not distribution_key:
        return False
    family = _emotion_distribution_family((report_row or {}).get("report_type"))
    if not family:
        return False
    try:
        store = ReportDistributionPushStore()
        await store.create_candidate(
            user_id=str(user_id or "").strip(),
            distribution_key=distribution_key,
            report_family=family,
            report_table=MYWEB_REPORTS_TABLE,
            report_id=(report_row or {}).get("id"),
            report_type=str((report_row or {}).get("report_type") or "").strip() or None,
            period_start=str((report_row or {}).get("period_start") or "").strip() or None,
            period_end=str((report_row or {}).get("period_end") or "").strip() or None,
            open_target={
                "screen": "MyWeb",
                "open_mode": "reportHistory",
                "report_type": str((report_row or {}).get("report_type") or "").strip() or None,
            },
        )
        return True
    except Exception as exc:
        WORKER_LOGGER.warning(
            "Failed to enqueue report distribution candidate. user=%s report_id=%s err=%s",
            str(user_id or "").strip(),
            str((report_row or {}).get("id") or "").strip(),
            exc,
        )
        return False


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
                    payload={
                        "trigger": "inspect_mismatch",
                        "requested_at": inspected_at,
                        "scope": scope,
                        "include_astor": True,
                        "distribution_origin": bool((payload or {}).get("distribution_origin")),
                        "distribution_key": (payload or {}).get("distribution_key"),
                    },
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

    distribution_candidate_enqueued = False
    if status == "READY":
        try:
            distribution_candidate_enqueued = await _enqueue_emotion_report_distribution_candidate(
                user_id=uid,
                report_row=row,
                payload=(payload or {}),
            )
        except Exception as exc:
            WORKER_LOGGER.warning(
                "Emotion distribution candidate enqueue failed. user=%s report_id=%s err=%s",
                uid,
                report_id,
                exc,
            )

    ready_push_sent = False

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
        "distribution_candidate_enqueued": bool(distribution_candidate_enqueued),
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


async def _fetch_latest_snapshot_row(*, user_id: str, scope: str, snapshot_type: str) -> Optional[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    sc = str(scope or "").strip()
    st = str(snapshot_type or "").strip()
    if not uid or not sc or not st:
        return None
    try:
        resp = await sb_get(
            f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
            params={
                "select": "id,user_id,scope,snapshot_type,source_hash,payload,created_at",
                "user_id": f"eq.{uid}",
                "scope": f"eq.{sc}",
                "snapshot_type": f"eq.{st}",
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


async def _fetch_latest_public_snapshot_row(*, user_id: str, scope: str) -> Optional[Dict[str, Any]]:
    return await _fetch_latest_snapshot_row(user_id=user_id, scope=scope, snapshot_type="public")


def _extract_snapshot_payload(snapshot_row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    payload = (snapshot_row or {}).get("payload")
    return payload if isinstance(payload, dict) else {}


def _extract_snapshot_summary(snapshot_row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    payload = _extract_snapshot_payload(snapshot_row)
    summary = payload.get("summary")
    return summary if isinstance(summary, dict) else {}


def _extract_snapshot_public_emotion_count(snapshot_row: Optional[Dict[str, Any]]) -> int:
    summary = _extract_snapshot_summary(snapshot_row)
    try:
        return int(summary.get("emotions_public") or 0)
    except Exception:
        return 0


async def _fetch_latest_internal_snapshot_row(*, user_id: str, scope: str) -> Optional[Dict[str, Any]]:
    return await _fetch_latest_snapshot_row(user_id=user_id, scope=scope, snapshot_type="internal")



def _extract_premium_reflection_view_from_snapshot(snapshot_row: Dict[str, Any]) -> Dict[str, Any]:
    payload = snapshot_row.get("payload")
    if isinstance(payload, dict):
        if isinstance(payload.get("premium_reflection_view"), dict):
            return payload.get("premium_reflection_view") or {}
        views = payload.get("views")
        if isinstance(views, dict) and isinstance(views.get("premium_reflection_view"), dict):
            return views.get("premium_reflection_view") or {}
    raise RuntimeError("premium_reflection_view not found in snapshot payload")


async def _fetch_reflection_row(*, reflection_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    rid = str(reflection_id or "").strip()
    uid = str(user_id or "").strip()
    if not rid or not uid:
        return None
    try:
        resp = await sb_get(
            f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}",
            params={
                "select": "*",
                "id": f"eq.{rid}",
                "owner_user_id": f"eq.{uid}",
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


async def _handle_generate_premium_reflections_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    scope = str((payload or {}).get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
    if scope != SNAPSHOT_SCOPE_DEFAULT:
        raise ValueError(f"unsupported scope for premium reflection generation: {scope}")

    snap = await _fetch_latest_public_snapshot_row(user_id=uid, scope=scope)
    if not snap:
        raise RuntimeError("public global snapshot not found")

    latest_hash = str(snap.get("source_hash") or "").strip()
    requested_hash = str((payload or {}).get("source_hash") or "").strip()
    if requested_hash and latest_hash and requested_hash != latest_hash:
        return {
            "status": "skipped_stale",
            "user_id": uid,
            "scope": scope,
            "requested_source_hash": requested_hash,
            "latest_source_hash": latest_hash,
        }

    reflection_view = _extract_premium_reflection_view_from_snapshot(snap)
    existing_dynamic = await fetch_active_generated_reflections(user_id=uid)

    plan = build_reflection_generation_plan(
        user_id=uid,
        snapshot_id=str(snap.get("id") or ""),
        source_hash=latest_hash,
        premium_reflection_view=reflection_view,
        existing_dynamic_reflections=existing_dynamic,
    )

    staged = await stage_reflection_generation_plan(
        user_id=uid,
        snapshot_id=str(snap.get("id") or ""),
        source_hash=latest_hash,
        generation_plan=plan,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "scope": scope,
        "snapshot_id": str(snap.get("id") or ""),
        "source_hash": latest_hash,
        "plan": plan.get("stats") or {},
        "stage": staged,
    }


async def _handle_inspect_reflection_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    rid = str((payload or {}).get("reflection_id") or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not rid:
        raise ValueError("payload.reflection_id is required")

    row = await _fetch_reflection_row(reflection_id=rid, user_id=uid)
    if not row:
        return {"status": "missing", "user_id": uid, "reflection_id": rid}

    if str(row.get("source_type") or "").strip() != "generated":
        raise ValueError("inspect_reflection_v1 supports generated reflections only")

    question = str(row.get("question") or "").strip()
    answer = str(row.get("answer") or "").strip()
    row_source_hash = str(row.get("source_hash") or "").strip()

    flags: List[str] = []
    if not str(row.get("topic_key") or "").strip():
        flags.append("topic_key_missing")
    if not str(row.get("category") or "").strip():
        flags.append("category_missing")
    if not question:
        flags.append("question_empty")
    if not answer:
        flags.append("answer_empty")
    elif len(answer) < 2:
        flags.append("answer_too_short")
    if not row_source_hash:
        flags.append("source_hash_missing")

    latest_public_hash = await _fetch_latest_public_source_hash(uid, scope=SNAPSHOT_SCOPE_DEFAULT)
    if not latest_public_hash:
        flags.append("latest_public_source_hash_missing")
    elif row_source_hash and row_source_hash != latest_public_hash:
        flags.append("public_snapshot_mismatch")

    pii_flags = _detect_pii("\n".join([question, answer]))
    for pf in pii_flags:
        flags.append(f"pii:{pf}")

    if flags:
        reject_res = await reject_generated_reflection(reflection_id=rid)
        return {
            "status": "rejected",
            "user_id": uid,
            "reflection_id": rid,
            "flags": flags,
            "latest_public_source_hash": latest_public_hash,
            "reject": reject_res,
        }

    promote_res = await promote_generated_reflection(reflection_id=rid)
    return {
        "status": "ready",
        "user_id": uid,
        "reflection_id": rid,
        "flags": [],
        "latest_public_source_hash": latest_public_hash,
        "promote": promote_res,
    }


async def _upsert_analysis_result(*, row: Dict[str, Any]) -> bool:
    resp = await sb_post(
        f"/rest/v1/{ANALYSIS_RESULTS_TABLE}",
        json=row,
        params={"on_conflict": "target_user_id,snapshot_id,analysis_type,analysis_stage"},
        prefer="resolution=merge-duplicates,return=minimal",
        timeout=10.0,
    )
    return resp.status_code in (200, 201, 204)


async def _fetch_ranking_board_row_by_id(board_id: str) -> Optional[Dict[str, Any]]:
    bid = str(board_id or "").strip()
    if not bid:
        return None
    resp = await sb_get(
        f"/rest/v1/{RANKING_BOARDS_TABLE}",
        params={
            "select": "id,metric_key,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{bid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch ranking_board by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


try:
    _ASTOR_RANKING_BOARD_MAX_ROWS = int(os.getenv("ASTOR_RANKING_BOARD_MAX_ROWS", "200") or "200")
except Exception:
    _ASTOR_RANKING_BOARD_MAX_ROWS = 200


_SUPPORTED_RANKING_METRIC_SET = {
    str(x or "").strip()
    for x in (SUPPORTED_RANKING_METRICS or [])
    if str(x or "").strip()
}


def _coerce_ranking_int(value: Any) -> Optional[int]:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return int(value)
    except Exception:
        try:
            return int(float(str(value)))
        except Exception:
            return None


def _validate_ranking_board_payload(metric_key: str, payload: Any) -> List[str]:
    flags: List[str] = []
    mk = str(metric_key or "").strip()
    if not mk:
        flags.append("metric_key_missing")
        return flags
    if mk not in _SUPPORTED_RANKING_METRIC_SET:
        flags.append(f"unsupported_metric:{mk}")

    if not isinstance(payload, dict):
        flags.append("payload_missing")
        return flags

    version = str(payload.get("version") or "").strip()
    if version != RANKING_BOARD_VERSION:
        flags.append(f"version_mismatch:{version or 'missing'}")

    ranges = payload.get("ranges")
    if not isinstance(ranges, dict):
        flags.append("ranges_missing")
        return flags

    for rk in list(RANKING_BOARD_RANGE_KEYS or []):
        if rk not in ranges:
            flags.append(f"range_missing:{rk}")
            continue

        rows = select_board_rows(payload, rk)
        if not isinstance(rows, list):
            flags.append(f"range_not_list:{rk}")
            continue
        if len(rows) > _ASTOR_RANKING_BOARD_MAX_ROWS:
            flags.append(f"range_too_large:{rk}:{len(rows)}")

        seen_user_ids = set()
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                flags.append(f"row_not_object:{rk}:{idx}")
                continue

            if _coerce_ranking_int(row.get("rank")) is None:
                flags.append(f"rank_invalid:{rk}:{idx}")

            if mk == "emotions":
                emotion = str(row.get("emotion") or "").strip()
                if not emotion:
                    flags.append(f"emotion_missing:{rk}:{idx}")
                if (
                    _coerce_ranking_int(row.get("value")) is None
                    and _coerce_ranking_int(row.get("count")) is None
                ):
                    flags.append(f"value_missing:{rk}:{idx}")
            else:
                uid = str(row.get("user_id") or "").strip()
                if not uid:
                    flags.append(f"user_id_missing:{rk}:{idx}")
                elif uid in seen_user_ids:
                    flags.append(f"duplicate_user_id:{rk}:{uid}")
                else:
                    seen_user_ids.add(uid)
                if _coerce_ranking_int(row.get("value")) is None:
                    flags.append(f"value_missing:{rk}:{idx}")

    return flags


async def _handle_refresh_ranking_board_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    metric_key = str((payload or {}).get("metric_key") or "").strip()
    if not metric_key:
        raise ValueError("payload.metric_key is required")

    trigger = str((payload or {}).get("trigger") or "worker").strip() or "worker"
    requested_at = str((payload or {}).get("requested_at") or _now_iso_z()).strip() or _now_iso_z()

    board_payload = await generate_ranking_board(metric_key)
    board_row = await upsert_ranking_board_draft(
        metric_key,
        board_payload,
        meta={
            "trigger": trigger,
            "requested_at": requested_at,
            "job_type": "refresh_ranking_board_v1",
            "kernel": "rpc_kernel_v1",
        },
        version=1,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "metric_key": metric_key,
        "board_id": str((board_row or {}).get("id") or ""),
        "board_status": str((board_row or {}).get("status") or ""),
        "source_hash": str((board_row or {}).get("source_hash") or ""),
    }


async def _handle_inspect_ranking_board_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    board_id = str((payload or {}).get("board_id") or "").strip()
    if not board_id:
        raise ValueError("payload.board_id is required")

    board_row = await _fetch_ranking_board_row_by_id(board_id)
    if not board_row:
        return {"status": "missing", "user_id": uid, "board_id": board_id}

    metric_key = str(board_row.get("metric_key") or (payload or {}).get("metric_key") or "").strip()
    board_payload = board_row.get("payload") if isinstance(board_row.get("payload"), dict) else {}
    flags = _validate_ranking_board_payload(metric_key, board_payload)

    if flags:
        failed = await fail_ranking_board(
            board_id,
            "ranking board inspection failed",
            flags={
                "issues": flags,
                "metric_key": metric_key,
                "inspector": "inspect_ranking_board_v1",
            },
        )
        return {
            "status": "failed",
            "user_id": uid,
            "board_id": board_id,
            "metric_key": metric_key,
            "source_hash": str(board_row.get("source_hash") or ""),
            "flags": flags,
            "board_status": str((failed or {}).get("status") or ""),
        }

    promoted = await promote_ranking_board(
        board_id,
        extra_meta={
            "inspection": {
                "checked_at": _now_iso_z(),
                "inspector": "inspect_ranking_board_v1",
                "metric_key": metric_key,
                "flags": [],
            }
        },
    )
    return {
        "status": "ready",
        "user_id": uid,
        "board_id": board_id,
        "metric_key": metric_key,
        "source_hash": str(board_row.get("source_hash") or ""),
        "board_status": str((promoted or {}).get("status") or ""),
        "flags": [],
    }



async def _fetch_account_status_summary_row_by_id(summary_id: str) -> Optional[Dict[str, Any]]:
    sid = str(summary_id or "").strip()
    if not sid:
        return None
    resp = await sb_get(
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        params={
            "select": "id,target_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{sid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch account_status_summary by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


def _validate_account_status_payload(payload: Any) -> List[str]:
    flags: List[str] = []
    if not isinstance(payload, dict):
        flags.append("payload_missing")
        return flags

    version = str(payload.get("version") or "").strip()
    if version != ACCOUNT_STATUS_VERSION:
        flags.append(f"version_mismatch:{version or 'missing'}")

    target_user_id = str(payload.get("target_user_id") or "").strip()
    if not target_user_id:
        flags.append("target_user_id_missing")

    totals = payload.get("totals")
    if not isinstance(totals, dict):
        flags.append("totals_missing")
        return flags

    for key in list(SUPPORTED_ACCOUNT_STATUS_TOTAL_KEYS or []):
        if key not in totals:
            flags.append(f"total_missing:{key}")
            continue
        coerced = _coerce_ranking_int(totals.get(key))
        if coerced is None:
            flags.append(f"total_invalid:{key}")
        elif coerced < 0:
            flags.append(f"total_negative:{key}")

    return flags


async def _handle_refresh_account_status_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    target_user_id = str((payload or {}).get("target_user_id") or uid).strip()
    if not target_user_id:
        raise ValueError("payload.target_user_id is required")

    trigger = str((payload or {}).get("trigger") or "worker").strip() or "worker"
    requested_at = str((payload or {}).get("requested_at") or _now_iso_z()).strip() or _now_iso_z()
    actor_user_id = str((payload or {}).get("actor_user_id") or uid).strip() or uid

    summary_payload = await generate_account_status_summary(target_user_id)
    meta: Dict[str, Any] = {
        "trigger": trigger,
        "requested_at": requested_at,
        "job_type": "refresh_account_status_v1",
        "kernel": "rpc_kernel_v1",
    }
    if actor_user_id:
        meta["actor_user_id"] = actor_user_id

    summary_row = await upsert_account_status_draft(
        target_user_id,
        summary_payload,
        meta=meta,
        version=1,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "target_user_id": target_user_id,
        "summary_id": str((summary_row or {}).get("id") or ""),
        "summary_status": str((summary_row or {}).get("status") or ""),
        "source_hash": str((summary_row or {}).get("source_hash") or ""),
    }


async def _handle_inspect_account_status_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    summary_id = str((payload or {}).get("summary_id") or "").strip()
    if not summary_id:
        raise ValueError("payload.summary_id is required")

    summary_row = await _fetch_account_status_summary_row_by_id(summary_id)
    if not summary_row:
        return {"status": "missing", "user_id": uid, "summary_id": summary_id}

    target_user_id = str(summary_row.get("target_user_id") or (payload or {}).get("target_user_id") or "").strip()
    summary_payload = summary_row.get("payload") if isinstance(summary_row.get("payload"), dict) else {}
    flags = _validate_account_status_payload(summary_payload)

    if target_user_id and isinstance(summary_payload, dict):
        payload_target = str(summary_payload.get("target_user_id") or "").strip()
        if payload_target and payload_target != target_user_id:
            flags.append("target_user_id_mismatch")

    if flags:
        failed = await fail_account_status_summary(
            summary_id,
            "account status summary inspection failed",
            flags={
                "issues": flags,
                "target_user_id": target_user_id,
                "inspector": "inspect_account_status_v1",
            },
        )
        return {
            "status": "failed",
            "user_id": uid,
            "target_user_id": target_user_id,
            "summary_id": summary_id,
            "source_hash": str(summary_row.get("source_hash") or ""),
            "flags": flags,
            "summary_status": str((failed or {}).get("status") or ""),
        }

    promoted = await promote_account_status_summary(
        summary_id,
        extra_meta={
            "inspection": {
                "checked_at": _now_iso_z(),
                "inspector": "inspect_account_status_v1",
                "target_user_id": target_user_id,
                "flags": [],
            }
        },
    )
    return {
        "status": "ready",
        "user_id": uid,
        "target_user_id": target_user_id,
        "summary_id": summary_id,
        "source_hash": str(summary_row.get("source_hash") or ""),
        "summary_status": str((promoted or {}).get("status") or ""),
        "flags": [],
    }


async def _fetch_friend_feed_summary_row_by_id(summary_id: str) -> Optional[Dict[str, Any]]:
    sid = str(summary_id or "").strip()
    if not sid:
        return None
    resp = await sb_get(
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_TABLE}",
        params={
            "select": "id,viewer_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{sid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch friend_feed_summary by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


def _validate_friend_feed_payload(payload: Any) -> List[str]:
    flags: List[str] = []
    if not isinstance(payload, dict):
        flags.append("payload_missing")
        return flags

    version = str(payload.get("version") or "").strip()
    if version != FRIEND_FEED_VERSION:
        flags.append(f"version_mismatch:{version or 'missing'}")

    viewer_user_id = str(payload.get("viewer_user_id") or "").strip()
    if not viewer_user_id:
        flags.append("viewer_user_id_missing")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        flags.append("items_missing")
        return flags

    items = select_friend_feed_items(payload)
    if len(raw_items) > FRIEND_FEED_MAX_ITEMS or len(items) > FRIEND_FEED_MAX_ITEMS:
        flags.append(f"items_too_many:{max(len(raw_items), len(items))}")

    for idx, row in enumerate(items):
        if not isinstance(row, dict):
            flags.append(f"item_not_object:{idx}")
            continue

        item_id = str(row.get("id") or "").strip()
        if not item_id:
            flags.append(f"item_id_missing:{idx}")

        owner_name = str(row.get("owner_name") or "").strip()
        if not owner_name:
            flags.append(f"owner_name_missing:{idx}")

        created_at = str(row.get("created_at") or "").strip()
        if not created_at:
            flags.append(f"created_at_missing:{idx}")

        emotions = row.get("items")
        if not isinstance(emotions, list):
            flags.append(f"emotion_items_missing:{idx}")
            continue

        for jdx, emo in enumerate(emotions):
            if not isinstance(emo, dict):
                flags.append(f"emotion_item_not_object:{idx}:{jdx}")
                continue
            emotion_type = str(emo.get("type") or "").strip()
            if not emotion_type:
                flags.append(f"emotion_type_missing:{idx}:{jdx}")
            strength = str(emo.get("strength") or "").strip().lower()
            if strength and strength not in FRIEND_FEED_ALLOWED_STRENGTHS:
                flags.append(f"emotion_strength_invalid:{idx}:{jdx}:{strength}")

    return flags


async def _handle_refresh_friend_feed_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    viewer_user_id = str((payload or {}).get("viewer_user_id") or uid).strip()
    if not viewer_user_id:
        raise ValueError("payload.viewer_user_id is required")

    trigger = str((payload or {}).get("trigger") or "worker").strip() or "worker"
    requested_at = str((payload or {}).get("requested_at") or _now_iso_z()).strip() or _now_iso_z()
    owner_user_id = str((payload or {}).get("owner_user_id") or "").strip()

    summary_payload = await generate_friend_feed(viewer_user_id)
    meta: Dict[str, Any] = {
        "trigger": trigger,
        "requested_at": requested_at,
        "job_type": "refresh_friend_feed_v1",
        "kernel": "friend_feed_source_v1",
    }
    if owner_user_id:
        meta["owner_user_id"] = owner_user_id

    summary_row = await upsert_friend_feed_draft(
        viewer_user_id,
        summary_payload,
        meta=meta,
        version=1,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "viewer_user_id": viewer_user_id,
        "summary_id": str((summary_row or {}).get("id") or ""),
        "summary_status": str((summary_row or {}).get("status") or ""),
        "source_hash": str((summary_row or {}).get("source_hash") or ""),
    }


async def _handle_inspect_friend_feed_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    summary_id = str((payload or {}).get("summary_id") or "").strip()
    if not summary_id:
        raise ValueError("payload.summary_id is required")

    summary_row = await _fetch_friend_feed_summary_row_by_id(summary_id)
    if not summary_row:
        return {"status": "missing", "user_id": uid, "summary_id": summary_id}

    viewer_user_id = str(summary_row.get("viewer_user_id") or (payload or {}).get("viewer_user_id") or "").strip()
    summary_payload = summary_row.get("payload") if isinstance(summary_row.get("payload"), dict) else {}
    flags = _validate_friend_feed_payload(summary_payload)

    if viewer_user_id and isinstance(summary_payload, dict):
        payload_viewer = str(summary_payload.get("viewer_user_id") or "").strip()
        if payload_viewer and payload_viewer != viewer_user_id:
            flags.append("viewer_user_id_mismatch")

    if flags:
        failed = await fail_friend_feed_summary(
            summary_id,
            "friend feed summary inspection failed",
            flags={
                "issues": flags,
                "viewer_user_id": viewer_user_id,
                "inspector": "inspect_friend_feed_v1",
            },
        )
        return {
            "status": "failed",
            "user_id": uid,
            "viewer_user_id": viewer_user_id,
            "summary_id": summary_id,
            "source_hash": str(summary_row.get("source_hash") or ""),
            "flags": flags,
            "summary_status": str((failed or {}).get("status") or ""),
        }

    promoted = await promote_friend_feed_summary(
        summary_id,
        extra_meta={
            "inspection": {
                "checked_at": _now_iso_z(),
                "inspector": "inspect_friend_feed_v1",
                "viewer_user_id": viewer_user_id,
                "flags": [],
            }
        },
    )
    return {
        "status": "ready",
        "user_id": uid,
        "viewer_user_id": viewer_user_id,
        "summary_id": summary_id,
        "source_hash": str(summary_row.get("source_hash") or ""),
        "summary_status": str((promoted or {}).get("status") or ""),
        "flags": [],
    }


async def _fetch_global_summary_row_by_id(summary_id: str) -> Optional[Dict[str, Any]]:
    sid = str(summary_id or "").strip()
    if not sid:
        return None
    resp = await sb_get(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        params={
            "select": "id,activity_date,timezone,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{sid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch global_activity_summary by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


_GLOBAL_SUMMARY_ALLOWED_TOP_LEVEL_KEYS = {
    "version",
    "activity_date",
    "timezone",
    "generated_at",
    "totals",
}


def _validate_global_summary_payload(payload: Any) -> List[str]:
    flags: List[str] = []
    if not isinstance(payload, dict):
        flags.append("payload_missing")
        return flags

    version = str(payload.get("version") or "").strip()
    if version != GLOBAL_SUMMARY_VERSION:
        flags.append(f"version_mismatch:{version or 'missing'}")

    activity_date = canonical_global_summary_activity_date(payload.get("activity_date"))
    if not activity_date:
        flags.append("activity_date_missing")

    raw_timezone = str(payload.get("timezone") or "").strip()
    payload_timezone = canonical_global_summary_timezone(raw_timezone)
    expected_timezone = canonical_global_summary_timezone(GLOBAL_SUMMARY_TIMEZONE)
    if not raw_timezone:
        flags.append("timezone_missing")
    elif payload_timezone != expected_timezone:
        flags.append(f"timezone_mismatch:{payload_timezone}")

    generated_at = str(payload.get("generated_at") or "").strip()
    if not generated_at:
        flags.append("generated_at_missing")

    totals = payload.get("totals")
    if not isinstance(totals, dict):
        flags.append("totals_missing")
        return flags

    for key in list(payload.keys()):
        ks = str(key or "").strip()
        if ks and ks not in _GLOBAL_SUMMARY_ALLOWED_TOP_LEVEL_KEYS:
            flags.append(f"unexpected_key:{ks}")

    allowed_total_keys = {str(x or "").strip() for x in (GLOBAL_SUMMARY_TOTAL_KEYS or []) if str(x or "").strip()}
    for key in list(totals.keys()):
        ks = str(key or "").strip()
        if ks and ks not in allowed_total_keys:
            flags.append(f"unexpected_total_key:{ks}")

    for key in list(GLOBAL_SUMMARY_TOTAL_KEYS or []):
        if key not in totals:
            flags.append(f"total_missing:{key}")
            continue
        coerced = _coerce_ranking_int(totals.get(key))
        if coerced is None:
            flags.append(f"total_invalid:{key}")
        elif coerced < 0:
            flags.append(f"total_negative:{key}")

    return flags


async def _handle_refresh_global_summary_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    trigger = str((payload or {}).get("trigger") or "worker").strip() or "worker"
    requested_at = str((payload or {}).get("requested_at") or _now_iso_z()).strip() or _now_iso_z()
    timezone_name = canonical_global_summary_timezone(
        (payload or {}).get("timezone") or (payload or {}).get("tz") or GLOBAL_SUMMARY_TIMEZONE
    )
    activity_date = resolve_global_summary_activity_date(
        requested_at=requested_at,
        activity_date=(payload or {}).get("activity_date"),
        timezone_name=timezone_name,
    )
    actor_user_id = str((payload or {}).get("actor_user_id") or "").strip()

    prefer_refresh_raw = (payload or {}).get("prefer_refresh")
    if prefer_refresh_raw is None:
        prefer_refresh = True
    elif isinstance(prefer_refresh_raw, str):
        prefer_refresh = prefer_refresh_raw.strip().lower() in ("1", "true", "yes", "y", "on")
    else:
        prefer_refresh = bool(prefer_refresh_raw)

    fallback_to_table_raw = (payload or {}).get("fallback_to_table")
    if fallback_to_table_raw is None:
        fallback_to_table = True
    elif isinstance(fallback_to_table_raw, str):
        fallback_to_table = fallback_to_table_raw.strip().lower() in ("1", "true", "yes", "y", "on")
    else:
        fallback_to_table = bool(fallback_to_table_raw)

    allow_empty_raw = (payload or {}).get("allow_empty")
    if allow_empty_raw is None:
        allow_empty = False
    elif isinstance(allow_empty_raw, str):
        allow_empty = allow_empty_raw.strip().lower() in ("1", "true", "yes", "y", "on")
    else:
        allow_empty = bool(allow_empty_raw)

    summary_payload = await generate_global_summary_payload(
        activity_date,
        timezone_name=timezone_name,
        prefer_refresh=prefer_refresh,
        fallback_to_table=fallback_to_table,
        allow_empty=allow_empty,
    )
    meta: Dict[str, Any] = {
        "trigger": trigger,
        "requested_at": requested_at,
        "job_type": "refresh_global_summary_v1",
        "kernel": "rpc_kernel_v1",
        "timezone": timezone_name,
    }
    if actor_user_id:
        meta["actor_user_id"] = actor_user_id

    summary_row = await upsert_global_summary_draft(
        activity_date,
        summary_payload,
        meta=meta,
        timezone_name=timezone_name,
        version=1,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "activity_date": activity_date,
        "timezone": timezone_name,
        "summary_id": str((summary_row or {}).get("id") or ""),
        "summary_status": str((summary_row or {}).get("status") or ""),
        "source_hash": str((summary_row or {}).get("source_hash") or ""),
    }


async def _handle_inspect_global_summary_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    summary_id = str((payload or {}).get("summary_id") or "").strip()
    if not summary_id:
        raise ValueError("payload.summary_id is required")

    summary_row = await _fetch_global_summary_row_by_id(summary_id)
    if not summary_row:
        return {"status": "missing", "user_id": uid, "summary_id": summary_id}

    activity_date = canonical_global_summary_activity_date(
        summary_row.get("activity_date") or (payload or {}).get("activity_date")
    )
    timezone_name = canonical_global_summary_timezone(
        summary_row.get("timezone") or (payload or {}).get("timezone") or GLOBAL_SUMMARY_TIMEZONE
    )
    summary_payload = summary_row.get("payload") if isinstance(summary_row.get("payload"), dict) else {}
    flags = _validate_global_summary_payload(summary_payload)

    payload_activity_date = canonical_global_summary_activity_date(summary_payload.get("activity_date"))
    if activity_date and payload_activity_date and payload_activity_date != activity_date:
        flags.append("activity_date_mismatch")

    payload_timezone = canonical_global_summary_timezone(summary_payload.get("timezone") or timezone_name)
    if timezone_name and payload_timezone and payload_timezone != timezone_name:
        flags.append("timezone_row_mismatch")

    source_hash = str(summary_row.get("source_hash") or "").strip()
    if not source_hash:
        flags.append("source_hash_missing")
    else:
        try:
            recomputed_hash = build_global_summary_source_hash(
                activity_date or payload_activity_date,
                summary_payload,
                timezone_name=timezone_name or payload_timezone,
            )
            if recomputed_hash != source_hash:
                flags.append("source_hash_mismatch")
        except Exception as exc:
            flags.append(f"source_hash_recompute_failed:{exc.__class__.__name__}")

    if flags:
        failed = await fail_global_summary(
            summary_id,
            "global summary inspection failed",
            flags={
                "issues": flags,
                "activity_date": activity_date,
                "timezone": timezone_name,
                "inspector": "inspect_global_summary_v1",
            },
        )
        return {
            "status": "failed",
            "user_id": uid,
            "activity_date": activity_date,
            "timezone": timezone_name,
            "summary_id": summary_id,
            "source_hash": source_hash,
            "flags": flags,
            "summary_status": str((failed or {}).get("status") or ""),
        }

    promoted = await promote_global_summary(
        summary_id,
        extra_meta={
            "inspection": {
                "checked_at": _now_iso_z(),
                "inspector": "inspect_global_summary_v1",
                "activity_date": activity_date,
                "timezone": timezone_name,
                "flags": [],
            }
        },
    )
    return {
        "status": "ready",
        "user_id": uid,
        "activity_date": activity_date,
        "timezone": timezone_name,
        "summary_id": summary_id,
        "source_hash": source_hash,
        "summary_status": str((promoted or {}).get("status") or ""),
        "flags": [],
    }


def _coerce_str_list(value: Any) -> List[str]:
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            s = str(item or "").strip()
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    return []


_SOURCE_TYPE_ALIASES: Dict[str, str] = {
    "emotion": "emotion_input",
    "emotion_input": "emotion_input",
    "mymodel": "mymodel_create",
    "my_model_create": "mymodel_create",
    "mymodel_create": "mymodel_create",
    "deepinsight": "deep_insight",
    "deep_insight": "deep_insight",
    "echo": "echo",
    "echoes": "echo",
    "discovery": "discovery",
    "discoveries": "discovery",
}


def _normalize_self_structure_source_type(raw: Any, default: str = "emotion_input") -> str:
    s = str(raw or "").strip().lower()
    if not s:
        return default
    return _SOURCE_TYPE_ALIASES.get(s, s)


_SOURCE_VIEW_KEYS: List[tuple[str, str]] = [
    ("emotion_input", "emotion_inputs"),
    ("emotion_input", "emotion_input"),
    ("mymodel_create", "mymodel_creates"),
    ("mymodel_create", "mymodel_create"),
    ("deep_insight", "deep_insights"),
    ("deep_insight", "deep_insight"),
    ("echo", "echoes"),
    ("echo", "echo"),
    ("discovery", "discoveries"),
    ("discovery", "discovery"),
]


def _extract_self_structure_view_from_snapshot(snapshot_row: Dict[str, Any]) -> Any:
    payload = snapshot_row.get("payload")
    if isinstance(payload, dict):
        if "self_structure_view" in payload:
            return payload.get("self_structure_view")
        if "items" in payload:
            return payload
        for _, key in _SOURCE_VIEW_KEYS:
            if key in payload:
                return payload
    if isinstance(payload, list):
        return payload
    raise RuntimeError("self_structure_view not found in snapshot payload")


def _default_snapshot_timestamp(snapshot_row: Dict[str, Any]) -> str:
    return str(snapshot_row.get("created_at") or _now_iso_z())


def _coerce_self_structure_item(raw: Dict[str, Any], *, default_source_type: str, default_ts: str, idx: int) -> SelfStructureInput:
    source_type = _normalize_self_structure_source_type(raw.get("source_type"), default=default_source_type)
    source_id = str(raw.get("source_id") or raw.get("id") or f"{source_type}:{idx}").strip()
    timestamp = str(raw.get("timestamp") or raw.get("created_at") or raw.get("updated_at") or default_ts).strip() or default_ts

    text_primary = str(
        raw.get("text_primary")
        or raw.get("text")
        or raw.get("memo")
        or raw.get("answer")
        or raw.get("content")
        or raw.get("body")
        or raw.get("message")
        or ""
    )
    text_secondary = str(
        raw.get("text_secondary")
        or raw.get("memo_action")
        or raw.get("action_text")
        or raw.get("notes")
        or raw.get("note")
        or ""
    )

    prompt_key = raw.get("prompt_key") or raw.get("question_key") or raw.get("q_key")
    question_text = raw.get("question_text") or raw.get("question") or raw.get("prompt") or raw.get("prompt_text")

    try:
        source_weight = float(raw.get("source_weight") or 1.0)
    except Exception:
        source_weight = 1.0

    return SelfStructureInput(
        source_type=source_type,
        source_id=source_id,
        timestamp=timestamp,
        text_primary=text_primary,
        text_secondary=text_secondary,
        prompt_key=(str(prompt_key).strip() if prompt_key is not None and str(prompt_key).strip() else None),
        question_text=(str(question_text).strip() if question_text is not None and str(question_text).strip() else None),
        emotion_signals=_coerce_str_list(raw.get("emotion_signals")),
        action_signals=_coerce_str_list(raw.get("action_signals")),
        social_signals=_coerce_str_list(raw.get("social_signals")),
        source_weight=source_weight,
    )


def _build_self_structure_inputs_from_snapshot_payload(snapshot_view: Any, *, snapshot_row: Optional[Dict[str, Any]] = None) -> List[SelfStructureInput]:
    if callable(build_self_structure_inputs_from_snapshot_payload):
        try:
            items = build_self_structure_inputs_from_snapshot_payload(snapshot_view)  # type: ignore[misc]
            if isinstance(items, list):
                return items
        except Exception:
            WORKER_LOGGER.exception("self_structure adapter failed; falling back to local coercion")

    default_ts = _default_snapshot_timestamp(snapshot_row or {})
    out: List[SelfStructureInput] = []

    if isinstance(snapshot_view, list):
        for idx, it in enumerate(snapshot_view):
            if isinstance(it, SelfStructureInput):
                out.append(it)
            elif isinstance(it, dict):
                out.append(_coerce_self_structure_item(it, default_source_type="emotion_input", default_ts=default_ts, idx=idx))
        return out

    if isinstance(snapshot_view, dict):
        if isinstance(snapshot_view.get("items"), list):
            for idx, it in enumerate(snapshot_view.get("items") or []):
                if isinstance(it, SelfStructureInput):
                    out.append(it)
                elif isinstance(it, dict):
                    out.append(_coerce_self_structure_item(
                        it,
                        default_source_type=_normalize_self_structure_source_type(it.get("source_type"), default="emotion_input"),
                        default_ts=default_ts,
                        idx=idx,
                    ))
            return out

        running_idx = 0
        for default_source_type, key in _SOURCE_VIEW_KEYS:
            items = snapshot_view.get(key)
            if not isinstance(items, list):
                continue
            for it in items:
                if isinstance(it, SelfStructureInput):
                    out.append(it)
                elif isinstance(it, dict):
                    out.append(_coerce_self_structure_item(it, default_source_type=default_source_type, default_ts=default_ts, idx=running_idx))
                running_idx += 1
        return out

    return out


def _build_self_structure_build_context(*, user_id: str, snapshot_row: Dict[str, Any], stage: str) -> BuildContext:
    stg = str(stage or "standard").strip().lower() or "standard"
    if stg not in ("standard", "deep"):
        raise ValueError(f"unsupported self structure stage: {stage}")
    return BuildContext(
        target_user_id=str(user_id or "").strip(),
        snapshot_id=str(snapshot_row.get("id") or "").strip(),
        scope=str(snapshot_row.get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT,
        source_hash=str(snapshot_row.get("source_hash") or "").strip(),
        analysis_type="self_structure",
        analysis_version=f"self_structure.{stg}.v1",
        generated_at=_now_iso_z(),
    )


async def _handle_analyze_self_structure_standard_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    scope = str((payload or {}).get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
    if scope != SNAPSHOT_SCOPE_DEFAULT:
        raise ValueError(f"unsupported scope for self structure standard analysis: {scope}")

    snap = await _fetch_latest_internal_snapshot_row(user_id=uid, scope=scope)
    if not snap:
        raise RuntimeError("internal global snapshot not found")

    view = _extract_self_structure_view_from_snapshot(snap)
    inputs = _build_self_structure_inputs_from_snapshot_payload(view, snapshot_row=snap)
    results = extract_signal_results(inputs, stage="standard")
    fusion = fuse_signal_results(results, stage="standard")
    ctx = _build_self_structure_build_context(user_id=uid, snapshot_row=snap, stage="standard")
    row = build_self_structure_standard_row(ctx=ctx, fusion=fusion, results=results)
    row["updated_at"] = _now_iso_z()
    ok = await _upsert_analysis_result(row=row)
    if not ok:
        raise RuntimeError("analysis_results upsert failed")

    return {
        "status": "ok",
        "user_id": uid,
        "scope": scope,
        "snapshot_id": str(snap.get("id") or ""),
        "source_hash": str(snap.get("source_hash") or ""),
        "analysis_stage": "standard",
        "analysis_version": ctx.analysis_version,
        "evidence_count": len(results),
        "top_role_count": len(list(getattr(fusion, "template_role_scores", []) or [])),
    }


async def _handle_analyze_self_structure_deep_v1(*, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    scope = str((payload or {}).get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
    if scope != SNAPSHOT_SCOPE_DEFAULT:
        raise ValueError(f"unsupported scope for self structure deep analysis: {scope}")

    snap = await _fetch_latest_internal_snapshot_row(user_id=uid, scope=scope)
    if not snap:
        raise RuntimeError("internal global snapshot not found")

    view = _extract_self_structure_view_from_snapshot(snap)
    inputs = _build_self_structure_inputs_from_snapshot_payload(view, snapshot_row=snap)
    results = extract_signal_results(inputs, stage="deep")
    fusion = fuse_signal_results(results, stage="deep")
    ctx = _build_self_structure_build_context(user_id=uid, snapshot_row=snap, stage="deep")
    row = build_self_structure_deep_row(ctx=ctx, fusion=fusion, results=results)
    row["updated_at"] = _now_iso_z()
    ok = await _upsert_analysis_result(row=row)
    if not ok:
        raise RuntimeError("analysis_results upsert failed")

    return {
        "status": "ok",
        "user_id": uid,
        "scope": scope,
        "snapshot_id": str(snap.get("id") or ""),
        "source_hash": str(snap.get("source_hash") or ""),
        "analysis_stage": "deep",
        "analysis_version": ctx.analysis_version,
        "evidence_count": len(results),
        "gap_count": len(list(getattr(fusion, "role_gaps", []) or [])),
        "unknown_count": len(list(getattr(fusion, "unknowns", []) or [])),
    }


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


_MEMO_PHRASE_SPLIT_RE = re.compile(r"[\n\r。．！？!?、,]+")
_MEMO_PHRASE_PRIORITY_RE = re.compile(r"(しなきゃ|したくない|気がする|かも|無理|怖い|しんど|疲れ|迷惑|大丈夫)")


def _sanitize_phrase_sample(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    s = s.strip("「」『』\"'")
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    if re.search(r"https?://|www\.", s, re.IGNORECASE):
        return ""
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s):
        return ""
    if re.search(r"\d{3,}", s):
        return ""
    if len(s) < 4 or len(s) > 24:
        return ""
    return s


def _extract_memo_phrase_candidates(text: str) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return []

    scored: List[tuple[int, int, str]] = []
    seen = set()
    fragments = [frag for frag in _MEMO_PHRASE_SPLIT_RE.split(raw) if str(frag or "").strip()]
    for idx, fragment in enumerate(fragments):
        phrase = _sanitize_phrase_sample(fragment)
        if not phrase or phrase in seen:
            continue
        seen.add(phrase)

        score = 0
        if _MEMO_PHRASE_PRIORITY_RE.search(phrase):
            score += 3
        if re.search(r"(たい|ない|かも|気がする|しんど|疲れ|無理|不安|怖|でき|だめ|ダメ|嫌)", phrase):
            score += 2
        if re.search(r"[ぁ-んァ-ヴー一-龯]", phrase):
            score += 1
        scored.append((score, -idx, phrase))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    picked = [phrase for _score, _idx, phrase in scored[:3]]
    return picked


def _classify_memo_theme_hint(*, keyword: str, phrase_samples: List[str]) -> str:
    keyword_text = str(keyword or "").lower()
    if re.search(r"(疲れ|しんど|無理|限界)", keyword_text):
        return "fatigue_limit"
    if re.search(r"(できてない|ダメ|だめ|無価値|自信ない|うまくいかない)", keyword_text):
        return "self_doubt"
    if re.search(r"(迷惑|気をつか|余計なこと|嫌われ)", keyword_text):
        return "interpersonal_caution"
    if re.search(r"(しなきゃ|遅れて|間に合わせ|ちゃんと)", keyword_text):
        return "self_pressure"

    merged = " ".join([keyword_text] + [str(x or "") for x in list(phrase_samples or [])]).lower()
    if re.search(r"(疲れ|しんど|無理|限界)", merged):
        return "fatigue_limit"
    if re.search(r"(できてない|ダメ|だめ|無価値|自信ない|うまくいかない)", merged):
        return "self_doubt"
    if re.search(r"(迷惑|気をつか|余計なこと|嫌われ)", merged):
        return "interpersonal_caution"
    if re.search(r"(しなきゃ|遅れて|間に合わせ|ちゃんと)", merged):
        return "self_pressure"
    return "generic"


def _build_memo_themes_from_triggers(memo_triggers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for item in list(memo_triggers or []):
        count = int(item.get("count") or 0)
        if count < 2:
            continue
        theme_hint = str(item.get("theme_hint") or item.get("themeHint") or "generic").strip() or "generic"
        group = grouped.setdefault(
            theme_hint,
            {
                "theme_hint": theme_hint,
                "keywords": [],
                "phrase_samples": [],
                "linked_transition_keys": Counter(),
                "dominant_time_buckets": Counter(),
                "count": 0,
                "evidence": {"triggerCount": 0, "phraseCount": 0},
                "notes": [],
            },
        )

        keyword = str(item.get("keyword") or "").strip()
        if keyword and keyword not in group["keywords"]:
            group["keywords"].append(keyword)

        for phrase in list(item.get("phrase_samples") or item.get("phraseSamples") or []):
            phrase_s = _sanitize_phrase_sample(phrase)
            if phrase_s and phrase_s not in group["phrase_samples"]:
                group["phrase_samples"].append(phrase_s)

        for key in list(item.get("source_transition_keys") or item.get("sourceTransitionKeys") or item.get("related_transitions") or item.get("relatedTransitions") or []):
            key_s = str(key or "").strip()
            if key_s:
                group["linked_transition_keys"][key_s] += 1

        for bucket in list(item.get("dominant_time_buckets") or item.get("dominantTimeBuckets") or []):
            bucket_s = str(bucket or "").strip()
            if bucket_s:
                group["dominant_time_buckets"][bucket_s] += 1

        group["count"] += count
        group["evidence"]["triggerCount"] += 1
        group["evidence"]["phraseCount"] = len(group["phrase_samples"])

    ordered_groups = sorted(grouped.values(), key=lambda item: int(item.get("count") or 0), reverse=True)[:2]
    out: List[Dict[str, Any]] = []
    for idx, group in enumerate(ordered_groups, start=1):
        out.append(
            {
                "theme_id": f"theme_{idx}",
                "theme_hint": str(group.get("theme_hint") or "generic"),
                "keywords": list(group.get("keywords") or [])[:4],
                "phrase_samples": list(group.get("phrase_samples") or [])[:3],
                "linked_transition_keys": [k for k, _ in group["linked_transition_keys"].most_common(4)],
                "dominant_time_buckets": [k for k, _ in group["dominant_time_buckets"].most_common(2)],
                "count": int(group.get("count") or 0),
                "evidence": dict(group.get("evidence") or {}),
                "notes": list(group.get("notes") or []),
            }
        )
    return out


def _select_recovery_route_for_pattern(
    edge_keys: List[str],
    recovery_time: List[Dict[str, Any]],
) -> Optional[str]:
    if not edge_keys or not recovery_time:
        return None

    related_labels = set()
    for edge_key in list(edge_keys or []):
        if "->" not in str(edge_key or ""):
            continue
        left, right = str(edge_key or "").split("->", 1)
        related_labels.add(left)
        related_labels.add(right)

    def _recovery_key(item: Dict[str, Any]) -> str:
        return f"{str(item.get('from_label') or '')}->{str(item.get('to_label') or '')}"

    candidates: List[Dict[str, Any]] = []
    for row in list(recovery_time or []):
        if not isinstance(row, dict):
            continue
        from_label = str(row.get("from_label") or "").strip()
        to_label = str(row.get("to_label") or "").strip()
        if not from_label or not to_label:
            continue
        if _recovery_key(row) in edge_keys or from_label in related_labels or to_label in related_labels:
            candidates.append(row)

    recovery_candidates = [row for row in candidates if str(row.get("to_label") or "") in ("calm", "joy")]
    if not recovery_candidates:
        return None

    recovery_candidates.sort(
        key=lambda row: (
            int(row.get("count") or 0),
            -float(row.get("mean_minutes") or row.get("meanMinutes") or 0.0),
        ),
        reverse=True,
    )
    top = recovery_candidates[0]
    return f"{str(top.get('from_label') or '')}->{str(top.get('to_label') or '')}" or None


def _build_pattern_episodes(
    control_patterns: List[Dict[str, Any]],
    memo_themes: List[Dict[str, Any]],
    recovery_time: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, pattern in enumerate(list(control_patterns or [])[:2], start=1):
        edge_keys = [str(x).strip() for x in list(pattern.get("transition_keys") or pattern.get("transitionKeys") or []) if str(x).strip()]
        linked_theme_ids: List[str] = []
        dominant_time_counter = Counter()
        for theme in list(memo_themes or []):
            theme_keys = set(str(x).strip() for x in list(theme.get("linked_transition_keys") or []) if str(x).strip())
            if theme_keys.intersection(edge_keys):
                theme_id = str(theme.get("theme_id") or theme.get("themeId") or "").strip()
                if theme_id:
                    linked_theme_ids.append(theme_id)
                for bucket in list(theme.get("dominant_time_buckets") or []):
                    bucket_s = str(bucket or "").strip()
                    if bucket_s:
                        dominant_time_counter[bucket_s] += 1

        if not dominant_time_counter:
            for bucket in list(pattern.get("dominant_time_buckets") or pattern.get("dominantTimeBuckets") or []):
                bucket_s = str(bucket or "").strip()
                if bucket_s:
                    dominant_time_counter[bucket_s] += 1

        recovery_route_key = _select_recovery_route_for_pattern(edge_keys, recovery_time)
        out.append(
            {
                "pattern_id": f"pattern_{idx}",
                "linked_theme_ids": linked_theme_ids,
                "route_keys": edge_keys[:4],
                "recovery_route_key": recovery_route_key,
                "dominant_time_buckets": [k for k, _ in dominant_time_counter.most_common(2)],
                "count": int((pattern.get("evidence") or {}).get("transitionCount") or pattern.get("size") or 0),
                "evidence": {
                    "transitionCount": int((pattern.get("evidence") or {}).get("transitionCount") or pattern.get("size") or 0),
                    "themeCount": len(linked_theme_ids),
                },
                "notes": [],
            }
        )
    return out




def _build_monthly_phase_windows(
    *,
    period_start_utc: datetime,
    period_end_exclusive_utc: datetime,
) -> List[Dict[str, Any]]:
    midpoint_utc = period_start_utc + timedelta(days=14)
    return [
        {
            "phase_id": "first_half",
            "phase_label": _MONTHLY_PHASE_LABELS["first_half"],
            "start_utc": period_start_utc,
            "end_utc": midpoint_utc,
        },
        {
            "phase_id": "second_half",
            "phase_label": _MONTHLY_PHASE_LABELS["second_half"],
            "start_utc": midpoint_utc,
            "end_utc": period_end_exclusive_utc,
        },
    ]


def _summarize_monthly_phase_model(
    *,
    phase_id: str,
    phase_label: str,
    phase_entries: List[Any],
    phase_model: Dict[str, Any],
    period_start_utc: datetime,
    period_end_exclusive_utc: datetime,
) -> Optional[Dict[str, Any]]:
    if len(list(phase_entries or [])) < 2:
        return None

    model = phase_model if isinstance(phase_model, dict) else {}
    phase_summary = model.get("summary") if isinstance(model.get("summary"), dict) else {}
    memo_themes = [item for item in list(model.get("memo_themes") or []) if isinstance(item, dict)]
    memo_triggers = [item for item in list(model.get("memo_triggers") or []) if isinstance(item, dict)]
    pattern_episodes = [item for item in list(model.get("pattern_episodes") or []) if isinstance(item, dict)]
    transition_edges = [item for item in list(model.get("transition_edges") or []) if isinstance(item, dict)]
    recovery_time = [item for item in list(model.get("recovery_time") or []) if isinstance(item, dict)]

    theme_hints = _ordered_unique_strs([
        item.get("theme_hint") or item.get("themeHint") or "generic"
        for item in memo_themes
    ])[:2]
    theme_labels = [_deep_theme_hint_label(hint) for hint in theme_hints]

    phrase_samples: List[str] = []
    for theme in memo_themes:
        for phrase in list(theme.get("phrase_samples") or theme.get("phraseSamples") or []):
            clean = _sanitize_phrase_sample(str(phrase or ""))
            if clean and clean not in phrase_samples:
                phrase_samples.append(clean)
    if not phrase_samples:
        for trigger in memo_triggers:
            for phrase in list(trigger.get("phrase_samples") or trigger.get("phraseSamples") or []):
                clean = _sanitize_phrase_sample(str(phrase or ""))
                if clean and clean not in phrase_samples:
                    phrase_samples.append(clean)
    phrase_samples = phrase_samples[:3]

    route_keys: List[str] = []
    for episode in pattern_episodes:
        route_keys.extend(list(episode.get("route_keys") or episode.get("routeKeys") or []))
    if not route_keys:
        for edge in transition_edges:
            key = f"{str(edge.get('from_label') or edge.get('fromLabel') or '').strip()}->{str(edge.get('to_label') or edge.get('toLabel') or '').strip()}"
            if key != "->":
                route_keys.append(key)
    route_keys = _ordered_unique_strs(route_keys)[:4]
    route_labels = [_deep_localize_transition_key(key) for key in route_keys]

    recovery_route_key = ""
    for episode in pattern_episodes:
        recovery_route_key = str(episode.get("recovery_route_key") or episode.get("recoveryRouteKey") or "").strip()
        if recovery_route_key:
            break
    if not recovery_route_key:
        recovery_route_key = str(_select_recovery_route_for_pattern(route_keys, recovery_time) or "").strip()
    recovery_route_label = _deep_localize_transition_key(recovery_route_key) if recovery_route_key else ""

    dominant_time_buckets: List[str] = []
    for episode in pattern_episodes:
        dominant_time_buckets.extend(list(episode.get("dominant_time_buckets") or episode.get("dominantTimeBuckets") or []))
    if not dominant_time_buckets:
        for theme in memo_themes:
            dominant_time_buckets.extend(list(theme.get("dominant_time_buckets") or theme.get("dominantTimeBuckets") or []))
    if not dominant_time_buckets:
        for edge in transition_edges:
            dominant_time_buckets.extend(list(edge.get("dominant_time_buckets") or edge.get("dominantTimeBuckets") or []))
    dominant_time_buckets = _ordered_unique_strs(dominant_time_buckets)[:2]

    pattern_ids = _ordered_unique_strs([
        episode.get("pattern_id") or episode.get("patternId") or ""
        for episode in pattern_episodes
    ])[:4]

    if not (theme_hints or phrase_samples or route_keys or recovery_route_key):
        return None

    lead = _quote_phrase(phrase_samples[0]) if phrase_samples else (theme_labels[0] if theme_labels else "")
    primary_route_label = route_labels[0] if route_labels else ""
    if lead and primary_route_label:
        phase_comment = f"{phase_label}は、{lead}が前に出る場面で、{primary_route_label}が目立っていました。"
    elif primary_route_label:
        phase_comment = f"{phase_label}は、{primary_route_label}が目立つ流れでした。"
    elif lead:
        phase_comment = f"{phase_label}は、{lead}が前に出やすい時期でした。"
    else:
        phase_comment = f"{phase_label}は、この時期らしい流れが見えていました。"

    if recovery_route_label:
        if primary_route_label and recovery_route_label != primary_route_label:
            phase_comment += f" そのあとも、{recovery_route_label}へ戻る道が見えていました。"
        else:
            phase_comment += f" {recovery_route_label}へ戻る整え直しも見えていました。"

    return {
        "phase_id": phase_id,
        "phase_label": phase_label,
        "period_start_iso": _iso_z(period_start_utc),
        "period_end_iso": _iso_z(period_end_exclusive_utc),
        "entry_count": len(list(phase_entries or [])),
        "transition_count": int(phase_summary.get("transitionCount") or len(transition_edges)),
        "theme_hints": theme_hints,
        "theme_labels": theme_labels,
        "phrase_samples": phrase_samples,
        "route_keys": route_keys,
        "route_labels": route_labels,
        "recovery_route_key": recovery_route_key,
        "recovery_route_label": recovery_route_label,
        "dominant_time_buckets": dominant_time_buckets,
        "pattern_ids": pattern_ids,
        "phase_comment": phase_comment,
        "evidence": {
            "themeCount": len(theme_hints),
            "patternCount": len(pattern_ids),
            "quoteSampleCount": len(phrase_samples),
        },
        "notes": [],
    }


def _build_monthly_phase_items(
    entries: List[Any],
    *,
    period_start_utc: datetime,
    period_end_exclusive_utc: datetime,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for window in _build_monthly_phase_windows(
        period_start_utc=period_start_utc,
        period_end_exclusive_utc=period_end_exclusive_utc,
    ):
        phase_entries = _entries_in_window(entries, window["start_utc"], window["end_utc"])
        if len(list(phase_entries or [])) < 2:
            continue

        phase_period_label = f"{_iso_z(window['start_utc'])}..{_iso_z(window['end_utc'])}"
        phase_model = _build_deep_control_model_payload(
            phase_entries,
            scope_kind="monthly_phase",
            period_label=phase_period_label,
        )
        item = _summarize_monthly_phase_model(
            phase_id=str(window.get("phase_id") or "phase").strip() or "phase",
            phase_label=str(window.get("phase_label") or "この時期").strip() or "この時期",
            phase_entries=phase_entries,
            phase_model=phase_model,
            period_start_utc=window["start_utc"],
            period_end_exclusive_utc=window["end_utc"],
        )
        if item:
            out.append(item)

    phase_rank = {"first_half": 0, "second_half": 1}
    out.sort(key=lambda item: phase_rank.get(str(item.get("phase_id") or ""), 99))
    return out[:2]


def _classify_monthly_shift_direction(
    *,
    from_phase: Dict[str, Any],
    to_phase: Dict[str, Any],
) -> str:
    from_routes = set(_ordered_unique_strs(list(from_phase.get("route_keys") or [])))
    to_routes = set(_ordered_unique_strs(list(to_phase.get("route_keys") or [])))
    emerging_route_keys = [key for key in _ordered_unique_strs(list(to_phase.get("route_keys") or [])) if key not in from_routes]

    def _route_target(route_key: str) -> str:
        text = str(route_key or "").strip()
        if "->" in text:
            return text.split("->", 1)[1].strip()
        if "→" in text:
            return text.split("→", 1)[1].strip()
        return ""

    emerging_targets = {_route_target(key) for key in emerging_route_keys if _route_target(key)}
    from_recovery_target = _route_target(str(from_phase.get("recovery_route_key") or ""))
    to_recovery_target = _route_target(str(to_phase.get("recovery_route_key") or ""))

    if (
        "calm" in emerging_targets
        or "joy" in emerging_targets
        or (to_recovery_target in ("calm", "joy") and from_recovery_target not in ("calm", "joy"))
    ):
        return "recovery_shift"
    if "anxiety" in emerging_targets or "anger" in emerging_targets:
        return "tension_shift"
    return "mixed"


def _build_monthly_shift_items(
    monthly_phases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    phases = [item for item in list(monthly_phases or []) if isinstance(item, dict)]
    if len(phases) < 2:
        return []

    phase_rank = {"first_half": 0, "second_half": 1}
    phases.sort(key=lambda item: phase_rank.get(str(item.get("phase_id") or ""), 99))
    from_phase = phases[0]
    to_phase = phases[1]

    from_phase_id = str(from_phase.get("phase_id") or "first_half").strip() or "first_half"
    to_phase_id = str(to_phase.get("phase_id") or "second_half").strip() or "second_half"
    from_phase_label = str(from_phase.get("phase_label") or _MONTHLY_PHASE_LABELS.get(from_phase_id, from_phase_id)).strip() or "前半"
    to_phase_label = str(to_phase.get("phase_label") or _MONTHLY_PHASE_LABELS.get(to_phase_id, to_phase_id)).strip() or "後半"

    from_theme_hints = _ordered_unique_strs(list(from_phase.get("theme_hints") or []))
    to_theme_hints = _ordered_unique_strs(list(to_phase.get("theme_hints") or []))
    emerging_theme_hints = [hint for hint in to_theme_hints if hint not in set(from_theme_hints)][:3]
    settling_theme_hints = [hint for hint in from_theme_hints if hint not in set(to_theme_hints)][:3]
    emerging_theme_labels = [_deep_theme_hint_label(hint) for hint in emerging_theme_hints]
    settling_theme_labels = [_deep_theme_hint_label(hint) for hint in settling_theme_hints]

    from_route_keys = _ordered_unique_strs(list(from_phase.get("route_keys") or []))
    to_route_keys = _ordered_unique_strs(list(to_phase.get("route_keys") or []))
    emerging_route_keys = [key for key in to_route_keys if key not in set(from_route_keys)][:4]
    settling_route_keys = [key for key in from_route_keys if key not in set(to_route_keys)][:4]
    emerging_route_labels = [_deep_localize_transition_key(key) for key in emerging_route_keys]
    settling_route_labels = [_deep_localize_transition_key(key) for key in settling_route_keys]

    from_recovery_route_key = str(from_phase.get("recovery_route_key") or "").strip()
    to_recovery_route_key = str(to_phase.get("recovery_route_key") or "").strip()
    from_recovery_route_label = str(from_phase.get("recovery_route_label") or _deep_localize_transition_key(from_recovery_route_key)).strip()
    to_recovery_route_label = str(to_phase.get("recovery_route_label") or _deep_localize_transition_key(to_recovery_route_key)).strip()

    direction_hint = _classify_monthly_shift_direction(from_phase=from_phase, to_phase=to_phase)
    if direction_hint == "recovery_shift":
        shift_label = "後半は静かに戻ろうとする流れが増えました"
    elif direction_hint == "tension_shift":
        shift_label = "後半は張りつめる流れが増えました"
    elif settling_route_labels and emerging_route_labels:
        shift_label = f"{settling_route_labels[0]}から{emerging_route_labels[0]}への変化"
    else:
        shift_label = "前半と後半で動き方が変わりました"

    settling_lead = settling_route_labels[0] if settling_route_labels else (settling_theme_labels[0] if settling_theme_labels else "")
    emerging_lead = emerging_route_labels[0] if emerging_route_labels else (emerging_theme_labels[0] if emerging_theme_labels else "")
    if settling_lead and emerging_lead:
        shift_comment = f"{from_phase_label}は{settling_lead}が目立っていましたが、{to_phase_label}は{emerging_lead}が前に出ていました。"
    elif emerging_lead:
        shift_comment = f"{to_phase_label}に入ってから、{emerging_lead}が増えていました。"
    elif settling_lead:
        shift_comment = f"{from_phase_label}で目立っていた{settling_lead}は、{to_phase_label}では少し静かになっていました。"
    else:
        shift_comment = f"{from_phase_label}と{to_phase_label}で、目立つ流れが少し入れ替わっていました。"

    if from_recovery_route_label and to_recovery_route_label and from_recovery_route_label != to_recovery_route_label:
        shift_comment += f" 整え直し方も、{from_recovery_route_label}から{to_recovery_route_label}へ少し移っていました。"
    elif to_recovery_route_label and direction_hint == "recovery_shift":
        shift_comment += f" {to_phase_label}は、{to_recovery_route_label}へ戻る流れが見えやすくなっていました。"

    if not (
        emerging_theme_hints
        or settling_theme_hints
        or emerging_route_keys
        or settling_route_keys
        or from_recovery_route_key
        or to_recovery_route_key
    ):
        return []

    return [
        {
            "shift_id": f"{from_phase_id}_to_{to_phase_id}",
            "from_phase_id": from_phase_id,
            "from_phase_label": from_phase_label,
            "to_phase_id": to_phase_id,
            "to_phase_label": to_phase_label,
            "emerging_theme_hints": emerging_theme_hints,
            "settling_theme_hints": settling_theme_hints,
            "emerging_theme_labels": emerging_theme_labels,
            "settling_theme_labels": settling_theme_labels,
            "emerging_route_keys": emerging_route_keys,
            "settling_route_keys": settling_route_keys,
            "emerging_route_labels": emerging_route_labels,
            "settling_route_labels": settling_route_labels,
            "from_recovery_route_key": from_recovery_route_key,
            "to_recovery_route_key": to_recovery_route_key,
            "from_recovery_route_label": from_recovery_route_label,
            "to_recovery_route_label": to_recovery_route_label,
            "direction_hint": direction_hint,
            "shift_label": shift_label,
            "shift_comment": shift_comment,
            "evidence": {
                "fromEntryCount": int(from_phase.get("entry_count") or from_phase.get("count") or 0),
                "toEntryCount": int(to_phase.get("entry_count") or to_phase.get("count") or 0),
                "routeDeltaCount": len(emerging_route_keys) + len(settling_route_keys),
                "themeDeltaCount": len(emerging_theme_hints) + len(settling_theme_hints),
            },
            "notes": [],
        }
    ]


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
        phrase_candidates = _extract_memo_phrase_candidates(memo_text)
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
                "phrase_candidates": phrase_candidates,
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
                "phrase_samples": [],
                "theme_hints": Counter(),
                "source_transition_keys": Counter(),
            })
            stat["count"] += 1
            stat["related_emotions"][from_label] += 1
            stat["related_emotions"][to_label] += 1
            stat["related_transitions"][key] += 1
            stat["time_buckets"][str(t.get("time_bucket") or "unknown")] += 1
            phrase_candidates = list(t.get("phrase_candidates") or [])
            theme_hint = _classify_memo_theme_hint(keyword=kw, phrase_samples=phrase_candidates)
            for phrase in phrase_candidates:
                phrase_s = _sanitize_phrase_sample(phrase)
                if phrase_s and phrase_s not in stat["phrase_samples"]:
                    stat["phrase_samples"].append(phrase_s)
            stat["theme_hints"][theme_hint] += 1
            stat["source_transition_keys"][key] += 1

    total_transitions = max(1, len(transitions))
    transition_edges: List[Dict[str, Any]] = []
    recovery_time: List[Dict[str, Any]] = []
    edge_vectors_by_key: Dict[str, List[float]] = {}

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
        edge_vectors_by_key[key] = [
            float(label_index.get(from_label, 0)),
            float(label_index.get(to_label, 0)),
            math.log1p(float(len(rows))),
            math.log1p(float(mean_minutes or 0.0) + 1.0),
            float(edge.get("mean_intensity_from") or 0.0),
            float(edge.get("mean_intensity_to") or 0.0),
            float(bucket_index.get(dominant_bucket, 1.5)),
        ]

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
                "phrase_samples": list(stat.get("phrase_samples") or [])[:3],
                "source_transition_keys": [k for k, _ in stat["source_transition_keys"].most_common(5)],
                "theme_hint": (stat["theme_hints"].most_common(1)[0][0] if stat.get("theme_hints") and stat["theme_hints"] else "generic"),
                "evidence": {"count": int(stat.get("count") or 0)},
                "notes": [],
            }
        )

    sorted_edge_vectors = [
        edge_vectors_by_key.get(f"{str(edge.get('from_label') or '')}->{str(edge.get('to_label') or '')}", [0.0] * 7)
        for edge in transition_edges
    ]
    cluster_labels, clustering_name = _choose_cluster_labels(sorted_edge_vectors, DEEP_MAX_CONTROL_PATTERNS)
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

    memo_themes = _build_memo_themes_from_triggers(memo_triggers)
    pattern_episodes = _build_pattern_episodes(
        control_patterns=control_patterns,
        memo_themes=memo_themes,
        recovery_time=recovery_time,
    )

    top_edges = [f"{e.get('from_label')}→{e.get('to_label')}" for e in transition_edges[:5]]
    return {
        "period": period_label,
        "scope": scope_kind,
        "transition_matrix": transition_matrix,
        "transition_edges": transition_edges,
        "recovery_time": recovery_time,
        "memo_triggers": memo_triggers[:10],
        "memo_themes": memo_themes,
        "control_patterns": control_patterns,
        "pattern_episodes": pattern_episodes,
        "summary": {
            "transitionCount": len(transitions),
            "edgeCount": len(transition_edges),
            "memoKeywordCount": len(memo_triggers),
            "memoThemeCount": len(memo_themes),
            "patternCount": len(control_patterns),
            "patternEpisodeCount": len(pattern_episodes),
            "quoteSampleCount": sum(len(list(x.get("phrase_samples") or [])) for x in memo_themes),
            "themeLinkedTransitionCount": len({
                key
                for theme in memo_themes
                for key in list(theme.get("linked_transition_keys") or [])
                if str(key or "").strip()
            }),
            "dominantTransitions": top_edges,
        },
        "meta": {
            "analysisVersion": "emotion_structure.deep.v2",
            "clustering": clustering_name,
            "memoMode": "keyword_phrase",
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

    snapshot_public_count = _extract_snapshot_public_emotion_count(snap)
    if snapshot_public_count <= 0:
        return {
            "status": "skipped_no_input",
            "user_id": uid,
            "scope": scope,
            "scope_kind": scope_kind,
            "snapshot_id": str(snap.get("id") or ""),
            "source_hash": str(snap.get("source_hash") or ""),
            "entry_count": 0,
            "analysis_stage": "deep",
            "analysis_version": "emotion_structure.deep.v2",
            "skip_reason": "no_public_emotion_entries",
        }

    period_info = _parse_emotion_period_scope(scope)
    start_iso = str(period_info.get("period_start_iso") or "").strip()
    end_iso = str(period_info.get("period_end_iso") or "").strip()
    if not start_iso or not end_iso:
        raise RuntimeError("snapshot period meta missing")

    rows = await fetch_emotions_in_range(uid, start_iso=start_iso, end_iso=end_iso, include_secret=False)
    rows = _filter_non_self_insight_rows(rows)
    entries = _normalize_entries_to_jst(build_emotion_entries_from_rows(rows))
    if not entries:
        return {
            "status": "skipped_no_input",
            "user_id": uid,
            "scope": scope,
            "scope_kind": scope_kind,
            "snapshot_id": str(snap.get("id") or ""),
            "source_hash": str(snap.get("source_hash") or ""),
            "entry_count": 0,
            "analysis_stage": "deep",
            "analysis_version": "emotion_structure.deep.v2",
            "skip_reason": "no_public_emotion_entries",
        }



    period_label = f"{start_iso}..{end_iso}"

    deep_model = _build_deep_control_model_payload(entries, scope_kind=scope_kind, period_label=period_label)

    monthly_phases: List[Dict[str, Any]] = []
    monthly_shifts: List[Dict[str, Any]] = []
    period_start_utc = period_info.get("period_start_utc")
    period_end_exclusive_utc = period_info.get("dist_utc") if scope_kind == "monthly" else None
    if (
        scope_kind == "monthly"
        and isinstance(period_start_utc, datetime)
        and isinstance(period_end_exclusive_utc, datetime)
    ):
        monthly_phases = _build_monthly_phase_items(
            entries,
            period_start_utc=period_start_utc,
            period_end_exclusive_utc=period_end_exclusive_utc,
        )
        monthly_shifts = _build_monthly_shift_items(monthly_phases)
        deep_model["monthly_phases"] = monthly_phases
        deep_model["monthly_shifts"] = monthly_shifts
        deep_model.setdefault("summary", {})["phaseCount"] = len(monthly_phases)
        deep_model.setdefault("summary", {})["shiftCount"] = len(monthly_shifts)
        deep_model.setdefault("meta", {})["monthlyPhaseMode"] = "half_split_14d"
        deep_model.setdefault("meta", {})["monthlyShiftMode"] = "first_to_second"

    analysis_payload: Dict[str, Any] = {
        "engine": "analysis_engine",
        "analysis_type": "emotion_structure",
        "scope": scope_kind,
        "analysis_stage": "deep",
        "analysis_version": "emotion_structure.deep.v2",
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
        "patternEpisodes": list(deep_model.get("pattern_episodes") or []),
        "transitionMatrix": deep_model.get("transition_matrix") or {},
        "transitionEdges": list(deep_model.get("transition_edges") or []),
        "recoveryTime": list(deep_model.get("recovery_time") or []),
        "memoTriggers": list(deep_model.get("memo_triggers") or []),
        "memoThemes": list(deep_model.get("memo_themes") or []),
        "monthly_phases": list(deep_model.get("monthly_phases") or []),
        "monthly_shifts": list(deep_model.get("monthly_shifts") or []),
        "monthlyPhases": list(deep_model.get("monthly_phases") or []),
        "monthlyShifts": list(deep_model.get("monthly_shifts") or []),
    }
    row = {
        "target_user_id": uid,
        "snapshot_id": str(snap.get("id") or ""),
        "analysis_type": "emotion_structure",
        "scope": scope_kind,
        "analysis_stage": "deep",
        "analysis_version": "emotion_structure.deep.v2",
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
        "analysis_version": "emotion_structure.deep.v2",
        "pattern_count": int(len(list(deep_model.get("control_patterns") or []))),
    }


def _worker_poll_backoff_seconds(base_seconds: float, consecutive_errors: int) -> float:
    base = max(0.5, float(base_seconds or 1.0))
    steps = min(max(int(consecutive_errors) - 1, 0), 5)
    return min(30.0, base * (2 ** steps))


async def _sleep_after_worker_poll_error(
    *,
    logger: logging.Logger,
    stage: str,
    worker_id: str,
    poll_interval: float,
    consecutive_errors: int,
    exc: Exception,
) -> None:
    delay = _worker_poll_backoff_seconds(poll_interval, consecutive_errors)
    if isinstance(exc, (httpx.HTTPError, asyncio.TimeoutError)):
        logger.warning(
            "worker %s failed. worker_id=%s consecutive_errors=%s retry_in=%.2fs err=%r",
            stage,
            worker_id,
            consecutive_errors,
            delay,
            exc,
        )
    else:
        logger.exception(
            "worker %s failed unexpectedly. worker_id=%s consecutive_errors=%s retry_in=%.2fs",
            stage,
            worker_id,
            consecutive_errors,
            delay,
        )
    await asyncio.sleep(delay)


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

    snapshot_public_count = _extract_snapshot_public_emotion_count(snap)
    if snapshot_public_count <= 0:
        return {
            "status": "skipped_no_input",
            "user_id": uid,
            "scope": scope,
            "scope_kind": scope_kind,
            "snapshot_id": str(snap.get("id") or ""),
            "source_hash": str(snap.get("source_hash") or ""),
            "entry_count": 0,
            "analysis_stage": "standard",
            "analysis_version": "emotion_structure.standard.v1",
            "skip_reason": "no_public_emotion_entries",
        }

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
    rows = _filter_non_self_insight_rows(rows)
    entries = _normalize_entries_to_jst(build_emotion_entries_from_rows(rows))
    if not entries:
        return {
            "status": "skipped_no_input",
            "user_id": uid,
            "scope": scope,
            "scope_kind": scope_kind,
            "snapshot_id": str(snap.get("id") or ""),
            "source_hash": str(snap.get("source_hash") or ""),
            "entry_count": 0,
            "analysis_stage": "standard",
            "analysis_version": "emotion_structure.standard.v1",
            "skip_reason": "no_public_emotion_entries",
        }

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
                "myprofile_latest_refresh_v1,snapshot_generate_v1,analyze_emotion_structure_standard_v1,analyze_emotion_structure_deep_v1,analyze_self_structure_standard_v1,analyze_self_structure_deep_v1,generate_premium_reflections_v1,inspect_reflection_v1,generate_emotion_report_v2,inspect_emotion_report_v1,refresh_ranking_board_v1,inspect_ranking_board_v1,refresh_account_status_v1,inspect_account_status_v1,refresh_friend_feed_v1,inspect_friend_feed_v1,refresh_global_summary_v1,inspect_global_summary_v1",
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

    consecutive_poll_errors = 0

    while not stop_event.is_set():
        try:
            job = await fetch_next_queued_job(job_types=job_types)
            consecutive_poll_errors = 0
        except Exception as exc:
            consecutive_poll_errors += 1
            await _sleep_after_worker_poll_error(
                logger=logger,
                stage="fetch_next_queued_job",
                worker_id=worker_id,
                poll_interval=poll_interval,
                consecutive_errors=consecutive_poll_errors,
                exc=exc,
            )
            continue

        if not job:
            await asyncio.sleep(max(0.1, poll_interval))
            continue

        try:
            claimed = await claim_job(job_key=job.job_key, worker_id=worker_id, attempts=job.attempts)
            consecutive_poll_errors = 0
        except Exception as exc:
            consecutive_poll_errors += 1
            await _sleep_after_worker_poll_error(
                logger=logger,
                stage="claim_job",
                worker_id=worker_id,
                poll_interval=poll_interval,
                consecutive_errors=consecutive_poll_errors,
                exc=exc,
            )
            continue

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
                    elif snap_status == "skipped_no_input":
                        # Zero-input periods are a normal no-op; do not fan out downstream work.
                        pass
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
                                # Global internal snapshot committed -> enqueue self structure standard analysis.
                                try:
                                    internal_hash = str(internal.get("source_hash") or "")
                                    if internal_hash:
                                        await enqueue_job(
                                            job_key=f"analysis_self_structure_standard:{claimed.user_id}:global:{internal_hash}",
                                            job_type="analyze_self_structure_standard_v1",
                                            user_id=claimed.user_id,
                                            payload={
                                                "trigger": "snapshot_generate_v1",
                                                "requested_at": (claimed.payload or {}).get("requested_at"),
                                                "scope": SNAPSHOT_SCOPE_DEFAULT,
                                                "source_hash": internal_hash,
                                            },
                                            priority=18,
                                        )
                                    else:
                                        raise RuntimeError("internal source_hash missing for global scope")
                                except Exception as exc:
                                    logger.error("Self structure downstream enqueue failed: %s", exc)

                                try:
                                    public_hash = str(public.get("source_hash") or "")
                                    if public_hash:
                                        await enqueue_job(
                                            job_key=f"generate_premium_reflections:{claimed.user_id}:global:{public_hash}",
                                            job_type="generate_premium_reflections_v1",
                                            user_id=claimed.user_id,
                                            payload={
                                                "trigger": "snapshot_generate_v1",
                                                "requested_at": (claimed.payload or {}).get("requested_at"),
                                                "scope": SNAPSHOT_SCOPE_DEFAULT,
                                                "source_hash": public_hash,
                                            },
                                            priority=16,
                                        )
                                    else:
                                        raise RuntimeError("public source_hash missing for global scope")
                                except Exception as exc:
                                    logger.error("Premium reflection downstream enqueue failed: %s", exc)

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
                                                "distribution_origin": bool((claimed.payload or {}).get("distribution_origin")),
                                                "distribution_key": (claimed.payload or {}).get("distribution_key"),
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
                        analysis_status = str((analysis_res or {}).get("status") or "").strip()
                        if EMOTION_REPORT_V2_ENABLED and analysis_status == "ok":
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
                                        "distribution_origin": bool((claimed.payload or {}).get("distribution_origin")),
                                        "distribution_key": (claimed.payload or {}).get("distribution_key"),
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
                                        "distribution_origin": bool((claimed.payload or {}).get("distribution_origin")),
                                        "distribution_key": (claimed.payload or {}).get("distribution_key"),
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
                        analysis_status = str((analysis_res or {}).get("status") or "").strip()
                        if EMOTION_REPORT_V2_ENABLED and analysis_status == "ok":
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
                                        "distribution_origin": bool((claimed.payload or {}).get("distribution_origin")),
                                        "distribution_key": (claimed.payload or {}).get("distribution_key"),
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
            elif claimed.job_type == "analyze_self_structure_standard_v1":
                analysis_res = await _handle_analyze_self_structure_standard_v1(
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
                        scope = str((analysis_res or {}).get("scope") or (claimed.payload or {}).get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
                        src_hash = str((analysis_res or {}).get("source_hash") or (claimed.payload or {}).get("source_hash") or "").strip()
                        if scope == SNAPSHOT_SCOPE_DEFAULT and src_hash:
                            await enqueue_job(
                                job_key=f"analysis_self_structure_deep:{claimed.user_id}:{scope}:{src_hash}",
                                job_type="analyze_self_structure_deep_v1",
                                user_id=claimed.user_id,
                                payload={
                                    "trigger": "analyze_self_structure_standard_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                    "scope": scope,
                                    "source_hash": src_hash,
                                },
                                priority=17,
                            )
                    except Exception as exc:
                        logger.error("Self structure deep enqueue after standard failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    analysis_res,
                )
            elif claimed.job_type == "analyze_self_structure_deep_v1":
                analysis_res = await _handle_analyze_self_structure_deep_v1(
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
                        scope = str((analysis_res or {}).get("scope") or (claimed.payload or {}).get("scope") or SNAPSHOT_SCOPE_DEFAULT).strip() or SNAPSHOT_SCOPE_DEFAULT
                        src_hash = str((analysis_res or {}).get("source_hash") or (claimed.payload or {}).get("source_hash") or "").strip()
                        if scope == SNAPSHOT_SCOPE_DEFAULT and src_hash:
                            await enqueue_job(
                                job_key=f"myprofile_latest_refresh:{claimed.user_id}:{scope}:{src_hash}",
                                job_type="myprofile_latest_refresh_v1",
                                user_id=claimed.user_id,
                                payload={
                                    "trigger": "analyze_self_structure_deep_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                    "scope": scope,
                                    "source_hash": src_hash,
                                    "force": True,
                                },
                                priority=14,
                            )
                    except Exception as exc:
                        logger.error("MyProfile latest enqueue after deep self structure failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    analysis_res,
                )
            elif claimed.job_type == "generate_premium_reflections_v1":
                gen_res = await _handle_generate_premium_reflections_v1(
                    user_id=claimed.user_id,
                    payload=(claimed.payload or {}),
                )
                gen_status = str((gen_res or {}).get("status") or "")
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
                elif gen_status == "ok":
                    try:
                        inspection_targets = list((((gen_res or {}).get("stage") or {}).get("inspection_targets") or []))
                        for reflection_id in inspection_targets:
                            rid = str(reflection_id or "").strip()
                            if not rid:
                                continue
                            await enqueue_job(
                                job_key=f"inspect_reflection:{claimed.user_id}:{rid}",
                                job_type="inspect_reflection_v1",
                                user_id=claimed.user_id,
                                payload={
                                    "reflection_id": rid,
                                    "trigger": "generate_premium_reflections_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                },
                                priority=28,
                            )
                    except Exception as exc:
                        logger.error("Reflection inspect enqueue failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    gen_res,
                )
            elif claimed.job_type == "inspect_reflection_v1":
                insp_res = await _handle_inspect_reflection_v1(
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
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    insp_res,
                )
            elif claimed.job_type == "refresh_ranking_board_v1":
                ranking_res = await _handle_refresh_ranking_board_v1(
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
                        board_id = str((ranking_res or {}).get("board_id") or "").strip()
                        metric_key = str((ranking_res or {}).get("metric_key") or (claimed.payload or {}).get("metric_key") or "").strip()
                        board_status = str((ranking_res or {}).get("board_status") or "").strip().lower()
                        if board_id and metric_key and board_status != BOARD_STATUS_READY:
                            await enqueue_job(
                                job_key=f"inspect_ranking_board:{metric_key}:{board_id}",
                                job_type="inspect_ranking_board_v1",
                                user_id=claimed.user_id,
                                payload={
                                    "board_id": board_id,
                                    "metric_key": metric_key,
                                    "source_hash": (ranking_res or {}).get("source_hash"),
                                    "trigger": "refresh_ranking_board_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                },
                                priority=24,
                            )
                    except Exception as exc:
                        logger.error("Ranking inspect enqueue failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    ranking_res,
                )
            elif claimed.job_type == "inspect_ranking_board_v1":
                insp_res = await _handle_inspect_ranking_board_v1(
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
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    insp_res,
                )
            elif claimed.job_type == "refresh_account_status_v1":
                account_status_res = await _handle_refresh_account_status_v1(
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
                        summary_id = str((account_status_res or {}).get("summary_id") or "").strip()
                        target_user_id = str((account_status_res or {}).get("target_user_id") or (claimed.payload or {}).get("target_user_id") or claimed.user_id or "").strip()
                        summary_status = str((account_status_res or {}).get("summary_status") or "").strip().lower()
                        if summary_id and target_user_id and summary_status != ACCOUNT_STATUS_STATUS_READY:
                            await enqueue_job(
                                job_key=f"inspect_account_status:{target_user_id}:{summary_id}",
                                job_type="inspect_account_status_v1",
                                user_id=target_user_id,
                                payload={
                                    "summary_id": summary_id,
                                    "target_user_id": target_user_id,
                                    "source_hash": (account_status_res or {}).get("source_hash"),
                                    "trigger": "refresh_account_status_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                },
                                priority=24,
                            )
                    except Exception as exc:
                        logger.error("Account status inspect enqueue failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    account_status_res,
                )
            elif claimed.job_type == "inspect_account_status_v1":
                insp_res = await _handle_inspect_account_status_v1(
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
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    insp_res,
                )
            elif claimed.job_type == "refresh_friend_feed_v1":
                friend_feed_res = await _handle_refresh_friend_feed_v1(
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
                        summary_id = str((friend_feed_res or {}).get("summary_id") or "").strip()
                        viewer_user_id = str((friend_feed_res or {}).get("viewer_user_id") or (claimed.payload or {}).get("viewer_user_id") or claimed.user_id or "").strip()
                        summary_status = str((friend_feed_res or {}).get("summary_status") or "").strip().lower()
                        if summary_id and viewer_user_id and summary_status != FRIEND_FEED_STATUS_READY:
                            await enqueue_job(
                                job_key=f"inspect_friend_feed:{viewer_user_id}:{summary_id}",
                                job_type="inspect_friend_feed_v1",
                                user_id=viewer_user_id,
                                payload={
                                    "summary_id": summary_id,
                                    "viewer_user_id": viewer_user_id,
                                    "source_hash": (friend_feed_res or {}).get("source_hash"),
                                    "trigger": "refresh_friend_feed_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                },
                                priority=24,
                            )
                    except Exception as exc:
                        logger.error("Friend feed inspect enqueue failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    friend_feed_res,
                )
            elif claimed.job_type == "inspect_friend_feed_v1":
                insp_res = await _handle_inspect_friend_feed_v1(
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
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    insp_res,
                )
            elif claimed.job_type == "refresh_global_summary_v1":
                global_summary_res = await _handle_refresh_global_summary_v1(
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
                        summary_id = str((global_summary_res or {}).get("summary_id") or "").strip()
                        activity_date = str((global_summary_res or {}).get("activity_date") or (claimed.payload or {}).get("activity_date") or "").strip()
                        timezone_name = str((global_summary_res or {}).get("timezone") or (claimed.payload or {}).get("timezone") or (claimed.payload or {}).get("tz") or GLOBAL_SUMMARY_TIMEZONE).strip()
                        summary_status = str((global_summary_res or {}).get("summary_status") or "").strip().lower()
                        if summary_id and summary_status != GLOBAL_SUMMARY_STATUS_READY:
                            await enqueue_job(
                                job_key=f"inspect_global_summary:{summary_id}",
                                job_type="inspect_global_summary_v1",
                                user_id=claimed.user_id,
                                payload={
                                    "summary_id": summary_id,
                                    "activity_date": activity_date,
                                    "timezone": timezone_name,
                                    "source_hash": (global_summary_res or {}).get("source_hash"),
                                    "trigger": "refresh_global_summary_v1",
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                },
                                priority=24,
                            )
                    except Exception as exc:
                        logger.error("Global summary inspect enqueue failed: %s", exc)
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    global_summary_res,
                )
            elif claimed.job_type == "inspect_global_summary_v1":
                insp_res = await _handle_inspect_global_summary_v1(
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
                logger.info(
                    "job done. key=%s type=%s user=%s res=%s",
                    claimed.job_key,
                    claimed.job_type,
                    claimed.user_id,
                    insp_res,
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
                                    "requested_at": (claimed.payload or {}).get("requested_at"),
                                    "distribution_origin": bool((claimed.payload or {}).get("distribution_origin")),
                                    "distribution_key": (claimed.payload or {}).get("distribution_key"),
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
                    try:
                        if claimed.job_type == "inspect_reflection_v1":
                            reflection_id = str(((claimed.payload or {}).get("reflection_id")) or "").strip()
                            if reflection_id:
                                await fail_generated_reflection(reflection_id=reflection_id)
                        elif claimed.job_type == "inspect_ranking_board_v1":
                            board_id = str(((claimed.payload or {}).get("board_id")) or "").strip()
                            if board_id:
                                await fail_ranking_board(
                                    board_id,
                                    str(exc),
                                    flags={
                                        "job_type": "inspect_ranking_board_v1",
                                        "phase": "worker_exception",
                                    },
                                )
                        elif claimed.job_type == "inspect_account_status_v1":
                            summary_id = str(((claimed.payload or {}).get("summary_id")) or "").strip()
                            if summary_id:
                                await fail_account_status_summary(
                                    summary_id,
                                    str(exc),
                                    flags={
                                        "job_type": "inspect_account_status_v1",
                                        "phase": "worker_exception",
                                    },
                                )
                        elif claimed.job_type == "inspect_friend_feed_v1":
                            summary_id = str(((claimed.payload or {}).get("summary_id")) or "").strip()
                            if summary_id:
                                await fail_friend_feed_summary(
                                    summary_id,
                                    str(exc),
                                    flags={
                                        "job_type": "inspect_friend_feed_v1",
                                        "phase": "worker_exception",
                                    },
                                )
                        elif claimed.job_type == "inspect_global_summary_v1":
                            summary_id = str(((claimed.payload or {}).get("summary_id")) or "").strip()
                            if summary_id:
                                await fail_global_summary(
                                    summary_id,
                                    str(exc),
                                    flags={
                                        "job_type": "inspect_global_summary_v1",
                                        "phase": "worker_exception",
                                    },
                                )
                    except Exception:
                        pass
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