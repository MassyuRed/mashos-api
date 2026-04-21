# -*- coding: utf-8 -*-
"""MyProfile ID (share) API for Cocolon (MashOS / FastAPI)

Friend機能と同じ発想で、MyProfileID（短い公開ID）を入力して
「申請 → 承諾/拒否 → 登録（閲覧可能）」の最小フローを提供する。

データモデル（想定）
----------------------
- profiles.myprofile_code  ... ユーザーごとの公開用短いID（= MyProfileID）
- myprofile_requests
    - id (bigint)
    - requester_user_id (uuid)
    - requested_user_id (uuid)
    - status (pending/accepted/rejected/cancelled)
    - created_at, responded_at
- myprofile_links
    - viewer_user_id (uuid)
    - owner_user_id (uuid)
    - created_at
    - PK(viewer_user_id, owner_user_id)

Notes
-----
* 呼び出し元は Authorization: Bearer <supabase_access_token> を必須。
* user_id の解決は Supabase Auth `/auth/v1/user` を利用。
* DB write は service_role で /rest/v1/... に書き込む。
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Reuse auth helpers & config checks from emotion submit module
from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)

try:
    from astor_myprofile_report import MYPROFILE_REPORT_SCHEMA_VERSION
except Exception:  # pragma: no cover
    # Keep a safe fallback here as well because api_myprofile.py uses the
    # schema check during /myprofile/latest reads before any regeneration path.
    MYPROFILE_REPORT_SCHEMA_VERSION = "myprofile.report.v5"

# Shared Supabase HTTP client (connection pooled)
from supabase_client import (
    sb_delete as _sb_delete_shared,
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_post as _sb_post_shared,
    sb_post_rpc as _sb_post_rpc_shared,
    sb_service_role_headers_json as _sb_headers_json_shared,
)

# Phase10: generation lock (dedupe concurrent generation)
try:
    from generation_lock import (
        build_lock_key,
        make_owner_id,
        poll_until,
        release_lock,
        try_acquire_lock,
    )
except Exception:  # pragma: no cover
    build_lock_key = None  # type: ignore
    make_owner_id = None  # type: ignore
    poll_until = None  # type: ignore
    release_lock = None  # type: ignore
    try_acquire_lock = None  # type: ignore

try:
    from report_distribution_push_store import ReportDistributionPushStore
except Exception:  # pragma: no cover
    ReportDistributionPushStore = None  # type: ignore

logger = logging.getLogger("myprofile_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Phase2: Follow list RPC name (Supabase SQL function)
MYPROFILE_FOLLOW_LIST_RPC = (os.getenv("COCOLON_MYPROFILE_FOLLOW_LIST_RPC", "myprofile_follow_list_v1") or "myprofile_follow_list_v1").strip()

# Phase10 lock tuning (env)
MYPROFILE_LATEST_LOCK_TTL_SECONDS = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYPROFILE_LATEST", "180") or "180")
MYPROFILE_LATEST_LOCK_WAIT_SECONDS = float(os.getenv("GENERATION_LOCK_WAIT_SECONDS_MYPROFILE_LATEST", "30") or "30")
MYPROFILE_MONTHLY_LOCK_TTL_SECONDS = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYPROFILE_MONTHLY", "360") or "360")
MYPROFILE_MONTHLY_LOCK_WAIT_SECONDS = float(os.getenv("GENERATION_LOCK_WAIT_SECONDS_MYPROFILE_MONTHLY", "60") or "60")


# ----------------------------
# Pydantic models
# ----------------------------


class MyProfileRequestCreateBody(BaseModel):
    myprofile_code: str = Field(
        ...,
        min_length=4,
        max_length=64,
        description="Target user's myprofile_code (MyProfileID)",
    )


class MyProfileRequestCreateResponse(BaseModel):
    status: str = Field(..., description="ok | already_registered | already_pending")
    request_id: Optional[int] = None
    owner_user_id: Optional[str] = None
    owner_display_name: Optional[str] = None


class MyProfileRequestActionResponse(BaseModel):
    status: str = Field(..., description="ok")
    request_id: int


class MyProfileLinkBody(BaseModel):
    """Follow (link) create/delete body.

    - owner_user_id: target user's UUID (preferred)
    - myprofile_code: target user's short public ID (optional fallback)

    Note: viewer_user_id is always derived from the caller's access token.
    """

    owner_user_id: Optional[str] = Field(
        default=None,
        description="Target user's UUID (profiles.id)",
    )
    myprofile_code: Optional[str] = Field(
        default=None,
        description="Target user's myprofile_code (MyProfileID)",
    )


class MyProfileRemoveFollowerBody(BaseModel):
    viewer_user_id: str = Field(
        ...,
        description="Follower user's UUID (profiles.id)",
    )


class MyProfileLinkActionResponse(BaseModel):
    status: str = Field(..., description="ok")
    viewer_user_id: str
    owner_user_id: str
    is_following: bool
    is_follow_requested: bool = False
    result: Optional[str] = None


class MyProfileFollowStatsResponse(BaseModel):
    status: str = Field(..., description="ok")
    target_user_id: str
    following_count: int
    follower_count: int
    is_following: bool
    is_follow_requested: bool = False

class MyProfileFollowListItem(BaseModel):
    id: str
    display_name: Optional[str] = None
    friend_code: Optional[str] = None
    myprofile_code: Optional[str] = None
    is_private_account: bool = False


class MyProfileFollowListResponse(BaseModel):
    status: str = Field(..., description="ok")
    target_user_id: str
    tab: str = Field(..., description="following | followers")
    rows: list[MyProfileFollowListItem]


class MyProfileLookupResponse(BaseModel):
    status: str = Field("ok", description="ok")
    found: bool = False
    target_user_id: Optional[str] = None
    display_name: Optional[str] = None
    myprofile_code: Optional[str] = None
    is_private_account: bool = False
    is_following: bool = False
    is_follow_requested: bool = False


class MyProfileFollowRequestCancelBody(BaseModel):
    target_user_id: str = Field(..., description="Target user's UUID (profiles.id)")


class MyProfileFollowRequestIdBody(BaseModel):
    request_id: str = Field(..., description="Follow request UUID")


class MyProfileIncomingFollowRequestItem(BaseModel):
    request_id: str
    requester_user_id: str
    requester_display_name: Optional[str] = None
    requester_myprofile_code: Optional[str] = None
    created_at: Optional[str] = None


class MyProfileIncomingFollowRequestsResponse(BaseModel):
    status: str = Field("ok", description="ok")
    total_items: int
    requests: list[MyProfileIncomingFollowRequestItem]



class MyProfileOutgoingFollowRequestItem(BaseModel):
    request_id: str
    target_user_id: str
    target_display_name: Optional[str] = None
    target_myprofile_code: Optional[str] = None
    created_at: Optional[str] = None


class MyProfileOutgoingFollowRequestsResponse(BaseModel):
    status: str = Field("ok", description="ok")
    total_items: int
    requests: list[MyProfileOutgoingFollowRequestItem]


# ----------------------------
# MyProfile Latest report (ensure / refresh)
# ----------------------------

# 既存アプリ互換: latest は period_start/end を固定値にして 1 行を使い回す
LATEST_REPORT_PERIOD_START = "1970-01-01T00:00:00.000Z"
LATEST_REPORT_PERIOD_END = "1970-01-01T00:00:00.000Z"

# Default lookback window for "latest" report generation (can be overridden by query or env)
DEFAULT_LATEST_PERIOD = (os.getenv("MYPROFILE_LATEST_PERIOD", "28d") or "28d").strip()

# Structure patterns table name (B1)
ASTOR_STRUCTURE_PATTERNS_TABLE = (
    os.getenv("ASTOR_STRUCTURE_PATTERNS_TABLE", "mymodel_structure_patterns")
    or "mymodel_structure_patterns"
).strip()


class MyProfileLatestEnsureResponse(BaseModel):
    status: str = Field("ok", description="ok")
    refreshed: bool = Field(..., description="True if report was regenerated & saved")
    reason: str = Field(
        ...,
        description="missing | stale_analysis | schema_mismatch | force | up_to_date | no_analysis | no_visible_content | in_progress",
    )
    report_mode: str = Field(..., description="standard | deep")
    period: str = Field(..., description="lookback period (e.g. 28d)")
    patterns_updated_at: Optional[str] = Field(
        default=None, description="updated_at of structure patterns"
    )
    latest_generated_at: Optional[str] = Field(
        default=None, description="generated_at of saved latest report"
    )
    generated_at: Optional[str] = Field(
        default=None, description="generated_at of returned report (after refresh)"
    )
    period_start: Optional[str] = Field(default=None, description="content window start (ISO)")
    period_end: Optional[str] = Field(default=None, description="content window end (ISO)")
    title: Optional[str] = Field(default=None, description="report title")
    content_text: Optional[str] = Field(default=None, description="report body")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="metadata JSON")
    has_visible_content: bool = Field(default=True, description="false when the latest view is no-data only")
    skip_reason: Optional[str] = Field(default=None, description="optional no-save reason")


class MyProfileLatestStatusResponse(BaseModel):
    status: str = Field("ok", description="ok")
    version_key: Optional[str] = Field(default=None, description="stable content/version key for app-internal banner polling")
    generated_at: Optional[str] = Field(default=None, description="generated_at of the saved latest report")
    saved_report_mode: Optional[str] = Field(default=None, description="saved latest report mode (standard | deep)")
    has_visible_content: bool = Field(default=False, description="false when the latest view is no-data only")
    skip_reason: Optional[str] = Field(default=None, description="optional no-data reason")


# ----------------------------
# MyProfile Monthly report (distribution ensure)
# ----------------------------

# Default lookback window for "monthly distribution" report generation.
# Note: monthly report is anchored to JST month boundary (1st 00:00 JST) and should be stable within the month.
DEFAULT_MONTHLY_DISTRIBUTION_PERIOD = (
    os.getenv("MYPROFILE_MONTHLY_DISTRIBUTION_PERIOD", "28d") or "28d"
).strip()


class MyProfileMonthlyEnsureBody(BaseModel):
    force: bool = Field(
        default=False,
        description="true の場合、当月配布分が存在しても再生成して上書き(upsert)する。",
    )
    period: Optional[str] = Field(
        default=None,
        description="lookback period (e.g. 28d). 未指定なら 28d。",
    )
    report_mode: Optional[str] = Field(
        default=None,
        description="Requested report mode (standard|deep). Tier-gated.",
    )
    include_secret: bool = Field(
        default=True,
        description="true の場合、secret も含めて自己レポートを生成する。",
    )
    now_iso: Optional[str] = Field(
        default=None,
        description="テスト用: 現在時刻(UTC ISO)。未指定ならサーバ現在時刻。",
    )
    trigger: Optional[str] = Field(
        default=None,
        description="Server trigger name (e.g. internal_rollover). Additive-only metadata.",
    )
    requested_at: Optional[str] = Field(
        default=None,
        description="Requested-at timestamp (UTC ISO). Additive-only metadata.",
    )
    distribution_key: Optional[str] = Field(
        default=None,
        description="JST distribution bucket key (YYYY-MM-DD). Additive-only metadata.",
    )
    distribution_origin: bool = Field(
        default=False,
        description="true の場合、0:00配布由来として通知候補を積む。",
    )




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
        jst = timezone(timedelta(hours=9))
        return dt.astimezone(jst).date().isoformat()
    except Exception:
        return None


async def _enqueue_self_structure_monthly_distribution_candidate(
    *,
    user_id: str,
    distribution_key: Optional[str],
    report_row: Optional[Dict[str, Any]],
    period_start: Optional[str],
    period_end: Optional[str],
) -> bool:
    # 2026-03 policy change:
    # 自己構造分析の月報は生成・保存は継続するが、Push 通知候補には積まない。
    return False


class MyProfileMonthlyEnsureResponse(BaseModel):
    status: str = Field("ok", description="ok")
    refreshed: bool = Field(..., description="True if regenerated & saved")
    reason: str = Field(..., description="missing | force | mode_mismatch | schema_mismatch | up_to_date | no_visible_content | unchanged | in_progress")
    report_mode: str = Field(..., description="standard | deep")
    period: str = Field(..., description="lookback period (e.g. 28d)")
    period_start: str = Field(..., description="period_start (ISO)")
    period_end: str = Field(..., description="period_end (ISO)")
    generated_at: Optional[str] = Field(default=None, description="generated_at of returned report")
    title: Optional[str] = Field(default=None, description="report title")
    content_text: Optional[str] = Field(default=None, description="report body")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="metadata JSON")
    history_saved: bool = Field(default=False, description="true when a monthly snapshot row was persisted")
    has_visible_content: bool = Field(default=False, description="false when the generated body is no-data only")
    skip_reason: Optional[str] = Field(default=None, description="optional skip reason for no-save cases")


# ----------------------------
# Report mode compatibility helpers
# ----------------------------

def _canonicalize_report_mode_value(x: Any) -> str:
    """
    Normalize external/internal MyProfile report mode into one of: standard | deep.

    Backward-compat:
    - structural -> deep
    - light -> standard
    """
    s = str(x or "").strip().lower()
    if not s:
        return "standard"
    if s == "structural":
        return "deep"
    if s == "light":
        return "standard"
    if s in ("standard", "deep"):
        return s
    return s


def _subscription_mode_input(x: Optional[str]) -> Optional[str]:
    """
    Convert API-facing mode aliases to the subscription module's expected inputs.

    If the subscription module still uses "structural", map incoming "deep" -> "structural"
    before normalize_myprofile_mode() is called.
    """
    s = str(x or "").strip().lower()
    if not s:
        return None
    if s == "deep":
        return "structural"
    return s

def _extract_report_content_json(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cj = (row or {}).get("content_json")
    if not isinstance(cj, dict):
        return {}
    if isinstance(cj.get("meta"), dict) and not isinstance(cj.get("version"), str):
        merged = dict(cj.get("meta") or {})
        for k, v in cj.items():
            if k == "meta":
                continue
            merged.setdefault(k, v)
        return merged
    return cj


def _extract_saved_report_mode(row: Optional[Dict[str, Any]]) -> Optional[str]:
    cj = _extract_report_content_json(row)
    mode = cj.get("report_mode") or cj.get("reportMode")
    if not mode:
        return None
    return _canonicalize_report_mode_value(mode)


def _row_matches_requested_mode(row: Optional[Dict[str, Any]], requested_mode: str) -> bool:
    saved = _extract_saved_report_mode(row)
    if not saved:
        return False
    return _canonicalize_report_mode_value(saved) == _canonicalize_report_mode_value(requested_mode)


def _extract_saved_self_structure_ref_source_hash(
    row: Optional[Dict[str, Any]],
    stage: str,
) -> Optional[str]:
    cj = _extract_report_content_json(row)
    refs = cj.get("analysis_refs") if isinstance(cj.get("analysis_refs"), dict) else {}
    ss = refs.get("self_structure") if isinstance(refs.get("self_structure"), dict) else {}
    stage_key = "deep" if _canonicalize_report_mode_value(stage) == "deep" else "standard"
    node = ss.get(stage_key) if isinstance(ss.get(stage_key), dict) else {}
    sh = node.get("source_hash") if isinstance(node, dict) else None
    s = str(sh or "").strip()
    return s or None


def _extract_saved_report_version(row: Optional[Dict[str, Any]]) -> Optional[str]:
    cj = _extract_report_content_json(row)
    s = str(cj.get("version") or "").strip()
    return s or None


def _row_uses_current_myprofile_schema(row: Optional[Dict[str, Any]]) -> bool:
    return _extract_saved_report_version(row) == MYPROFILE_REPORT_SCHEMA_VERSION


def _extract_saved_history_fingerprint(row: Optional[Dict[str, Any]]) -> Optional[str]:
    cj = _extract_report_content_json(row)
    history = cj.get("history") if isinstance(cj.get("history"), dict) else {}
    s = str(history.get("history_fingerprint") or "").strip()
    return s or None


def _extract_saved_has_visible_content(row: Optional[Dict[str, Any]]) -> bool:
    cj = _extract_report_content_json(row)
    visibility = cj.get("visibility") if isinstance(cj.get("visibility"), dict) else {}
    if "has_visible_content" in visibility:
        return bool(visibility.get("has_visible_content"))
    return bool(str((row or {}).get("content_text") or "").strip())


def _extract_report_window(row: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    cj = _extract_report_content_json(row)
    distribution = cj.get("distribution") if isinstance(cj.get("distribution"), dict) else {}
    ps = str(distribution.get("period_start") or (row or {}).get("period_start") or "").strip() or None
    pe = str(distribution.get("period_end") or (row or {}).get("period_end") or "").strip() or None
    return ps, pe


def _extract_saved_skip_reason(row: Optional[Dict[str, Any]]) -> Optional[str]:
    cj = _extract_report_content_json(row)
    history = cj.get("history") if isinstance(cj.get("history"), dict) else {}
    s = str(history.get("skip_reason") or cj.get("skip_reason") or "").strip()
    return s or None


SELF_STRUCTURE_MONTHLY_TITLE_BASE = "自己構造レポート"
_SELF_STRUCTURE_MONTHLY_LABEL_PATTERN = re.compile(r"自己構造分析レポート[（(]月次[）)]")


def _sanitize_self_structure_report_text(text: Any) -> str:
    s = str(text or "")
    if not s:
        return ""
    return _SELF_STRUCTURE_MONTHLY_LABEL_PATTERN.sub("自己構造分析レポート", s)


def _sanitize_self_structure_monthly_title(title: Any) -> str:
    s = str(title or "").strip()
    if not s:
        return SELF_STRUCTURE_MONTHLY_TITLE_BASE
    if re.match(r"^自己構造レポート[：:]", s):
        return SELF_STRUCTURE_MONTHLY_TITLE_BASE
    return s


def _build_latest_version_key(row: Optional[Dict[str, Any]]) -> Optional[str]:
    if not row:
        return None

    fingerprint = _extract_saved_history_fingerprint(row)
    if fingerprint:
        return fingerprint

    content_text = str((row or {}).get("content_text") or "").strip()
    if not content_text and not _extract_saved_skip_reason(row):
        return None

    raw = "|".join(
        [
            str(_extract_saved_report_mode(row) or ""),
            "1" if _extract_saved_has_visible_content(row) else "0",
            str(_extract_saved_skip_reason(row) or ""),
            content_text,
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


async def _fetch_latest_self_structure_analysis_row(
    user_id: str,
    stage: str,
) -> Optional[Dict[str, Any]]:
    stage_key = "deep" if _canonicalize_report_mode_value(stage) == "deep" else "standard"
    resp = await _sb_get(
        "/rest/v1/analysis_results",
        params={
            "select": "id,snapshot_id,source_hash,created_at,updated_at,analysis_type,scope,analysis_stage",
            "target_user_id": f"eq.{user_id}",
            "analysis_type": "eq.self_structure",
            "scope": "eq.global",
            "analysis_stage": f"eq.{stage_key}",
            "order": "updated_at.desc,created_at.desc",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase analysis_results(self_structure) select failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to load self structure analysis")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


# ----------------------------
# Supabase helpers
# ----------------------------


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    # Keep legacy helper name but delegate to the shared client headers.
    return _sb_headers_json_shared(prefer=prefer)


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    return await _sb_get_shared(path, params=params)


async def _sb_count(path: str, *, params: Dict[str, str]) -> int:
    """Return exact row count for a given REST endpoint query (PostgREST count header)."""
    # Use the shared pooled client, but keep behavior (raise on failure).
    resp = await _sb_get_shared(
        path,
        params=params,
        prefer="count=exact",
    )

    if resp.status_code >= 300:
        logger.error("Supabase count failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to count rows")

    content_range = resp.headers.get("content-range") or resp.headers.get("Content-Range") or ""
    if "/" in content_range:
        tail = content_range.split("/")[-1].strip()
        if tail.isdigit():
            return int(tail)
        try:
            return int(tail)
        except Exception:
            pass

    try:
        data = resp.json()
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0


async def _sb_post(path: str, *, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    return await _sb_post_shared(path, json=json, prefer=prefer)


async def _sb_patch(path: str, *, params: Dict[str, str], json: Any, prefer: Optional[str] = None) -> httpx.Response:
    return await _sb_patch_shared(path, params=params, json=json, prefer=prefer)


async def _sb_delete(path: str, *, params: Dict[str, str]) -> httpx.Response:
    return await _sb_delete_shared(path, params=params)


async def _sb_post_rpc(fn: str, *, payload: Dict[str, Any]) -> httpx.Response:
    """Call a Supabase RPC function via POST /rest/v1/rpc/<fn> (service_role)."""
    return await _sb_post_rpc_shared(fn, payload)


async def _lookup_profile_by_myprofile_code(myprofile_code: str) -> Optional[Dict[str, Any]]:
    """Return {id, display_name, myprofile_code} or None"""
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,myprofile_code",
            "myprofile_code": f"eq.{myprofile_code}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase profiles lookup failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to look up myprofile_code")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _is_already_registered(viewer_user_id: str, owner_user_id: str) -> bool:
    resp = await _sb_get(
        "/rest/v1/myprofile_links",
        params={
            "select": "viewer_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "owner_user_id": f"eq.{owner_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase myprofile_links select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to check myprofile link")
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def _find_existing_pending_request(viewer_user_id: str, owner_user_id: str) -> Optional[Dict[str, Any]]:
    resp = await _sb_get(
        "/rest/v1/myprofile_requests",
        params={
            "select": "id,requester_user_id,requested_user_id,status,created_at",
            "status": "eq.pending",
            "requester_user_id": f"eq.{viewer_user_id}",
            "requested_user_id": f"eq.{owner_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase myprofile_requests select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query myprofile requests")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _get_request_by_id(req_id: int) -> Dict[str, Any]:
    resp = await _sb_get(
        "/rest/v1/myprofile_requests",
        params={
            "select": "id,requester_user_id,requested_user_id,status,created_at,responded_at",
            "id": f"eq.{req_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase myprofile_requests get failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query myprofile request")
    rows = resp.json()
    if not (isinstance(rows, list) and rows):
        raise HTTPException(status_code=404, detail="MyProfile request not found")
    return rows[0]


async def _insert_myprofile_link(viewer_user_id: str, owner_user_id: str) -> None:
    payload = {"viewer_user_id": viewer_user_id, "owner_user_id": owner_user_id}
    resp = await _sb_post(
        "/rest/v1/myprofile_links",
        json=payload,
        prefer="return=minimal",
    )

    # 201/204 ok. 409 can happen if already exists; treat as ok.
    if resp.status_code in (200, 201, 204):
        return
    if resp.status_code == 409:
        logger.info("myprofile_links already exist for viewer=%s owner=%s", viewer_user_id, owner_user_id)
        return
    logger.error("Supabase insert myprofile_links failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to create myprofile link")


async def _delete_myprofile_link(viewer_user_id: str, owner_user_id: str) -> None:
    params = {
        "viewer_user_id": f"eq.{viewer_user_id}",
        "owner_user_id": f"eq.{owner_user_id}",
    }
    resp = await _sb_delete("/rest/v1/myprofile_links", params=params)

    # 200/204 ok (even if 0 rows).
    if resp.status_code in (200, 204):
        return

    logger.error("Supabase delete myprofile_links failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to delete myprofile link")


# ----------------------------
# Follow approval (private account) helpers
# ----------------------------

VISIBILITY_TABLE = (os.getenv("COCOLON_VISIBILITY_SETTINGS_TABLE", "account_visibility_settings") or "account_visibility_settings").strip()
FOLLOW_REQUESTS_TABLE = (os.getenv("COCOLON_FOLLOW_REQUESTS_TABLE", "follow_requests") or "follow_requests").strip()


async def _is_private_account(user_id: str) -> bool:
    """Return True if the user has is_private_account enabled.

    Missing row => treated as public (False).
    """
    uid = str(user_id or "").strip()
    if not uid:
        return False

    resp = await _sb_get(
        f"/rest/v1/{VISIBILITY_TABLE}",
        params={
            "select": "user_id,is_private_account",
            "user_id": f"eq.{uid}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase visibility select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query visibility settings")

    rows = resp.json()
    if isinstance(rows, list) and rows:
        return bool(rows[0].get("is_private_account") or False)

    return False


async def _find_existing_follow_request_id(requester_user_id: str, target_user_id: str) -> Optional[str]:
    resp = await _sb_get(
        f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
        params={
            "select": "id",
            "requester_user_id": f"eq.{requester_user_id}",
            "target_user_id": f"eq.{target_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase follow_requests select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query follow requests")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        rid = str((rows[0] or {}).get("id") or "").strip()
        return rid or None
    return None


async def _has_follow_request(requester_user_id: str, target_user_id: str) -> bool:
    rid = await _find_existing_follow_request_id(requester_user_id, target_user_id)
    return bool(rid)


async def _insert_follow_request(requester_user_id: str, target_user_id: str) -> bool:
    payload = {
        "requester_user_id": requester_user_id,
        "target_user_id": target_user_id,
    }
    resp = await _sb_post(
        f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
        json=payload,
        prefer="return=minimal",
    )

    # 201/204 ok. 409 means already exists.
    if resp.status_code in (200, 201, 204):
        return True
    if resp.status_code == 409:
        return False

    logger.error("Supabase insert follow_requests failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to create follow request")


async def _delete_follow_request_pair(requester_user_id: str, target_user_id: str) -> None:
    resp = await _sb_delete(
        f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
        params={
            "requester_user_id": f"eq.{requester_user_id}",
            "target_user_id": f"eq.{target_user_id}",
        },
    )

    if resp.status_code in (200, 204):
        return

    logger.error("Supabase delete follow_requests failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to delete follow request")


async def _delete_follow_request_by_id(request_id: str) -> None:
    rid = str(request_id or "").strip()
    if not rid:
        return
    resp = await _sb_delete(
        f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
        params={
            "id": f"eq.{rid}",
        },
    )

    if resp.status_code in (200, 204):
        return

    logger.error("Supabase delete follow_requests by id failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to delete follow request")


async def _get_follow_request_by_id(request_id: str) -> Optional[Dict[str, Any]]:
    rid = str(request_id or "").strip()
    if not rid:
        return None

    resp = await _sb_get(
        f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
        params={
            "select": "id,requester_user_id,target_user_id,created_at",
            "id": f"eq.{rid}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase follow_requests get failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query follow request")
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


async def _fetch_profiles_basic_map(user_ids: list[str]) -> Dict[str, Dict[str, Any]]:
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return {}

    # PostgREST in.(...) expects comma separated values.
    in_list = ",".join(ids)
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,myprofile_code",
            "id": f"in.({in_list})",
        },
    )
    if resp.status_code >= 300:
        logger.warning("Supabase profiles fetch failed: %s %s", resp.status_code, resp.text[:800])
        return {}

    rows = resp.json()
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            rid2 = str(r.get("id") or "").strip()
            if not rid2:
                continue
            out[rid2] = r
    return out


# ----------------------------
# Route registration
# ----------------------------


def register_myprofile_routes(app: FastAPI) -> None:
    """Register MyProfileID request endpoints on the given FastAPI app."""

    @app.get("/myprofile/lookup", response_model=MyProfileLookupResponse)
    async def lookup_myprofile_by_code(
        myprofile_code: str = Query(..., min_length=4, max_length=64, description="Target user's myprofile_code (Connect ID)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLookupResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)
        code = str(myprofile_code or "").strip()
        if not code:
            raise HTTPException(status_code=400, detail="myprofile_code is required")

        target_profile = await _lookup_profile_by_myprofile_code(code)
        if not target_profile:
            return MyProfileLookupResponse(status="ok", found=False)

        owner_user_id = str(target_profile.get("id") or "").strip()
        if not owner_user_id:
            return MyProfileLookupResponse(status="ok", found=False)

        is_private_account = False
        try:
            is_private_account = await _is_private_account(owner_user_id)
        except Exception:
            is_private_account = False

        is_following = False
        is_follow_requested = False
        if viewer_user_id and str(viewer_user_id) != owner_user_id:
            try:
                is_following = await _is_already_registered(str(viewer_user_id), owner_user_id)
            except Exception:
                is_following = False

            if not is_following:
                try:
                    is_follow_requested = bool(await _has_follow_request(str(viewer_user_id), owner_user_id))
                except Exception:
                    is_follow_requested = False

        return MyProfileLookupResponse(
            status="ok",
            found=True,
            target_user_id=owner_user_id,
            display_name=(target_profile.get("display_name") if isinstance(target_profile.get("display_name"), str) else None),
            myprofile_code=(target_profile.get("myprofile_code") if isinstance(target_profile.get("myprofile_code"), str) else code),
            is_private_account=bool(is_private_account),
            is_following=bool(is_following),
            is_follow_requested=bool(is_follow_requested),
        )

    @app.post("/myprofile/request", response_model=MyProfileRequestCreateResponse)
    async def create_myprofile_request(
        body: MyProfileRequestCreateBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileRequestCreateResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        requester_user_id = await _resolve_user_id_from_token(access_token)
        myprofile_code = body.myprofile_code.strip()
        if not myprofile_code:
            raise HTTPException(status_code=400, detail="myprofile_code is required")

        target_profile = await _lookup_profile_by_myprofile_code(myprofile_code)
        if not target_profile:
            raise HTTPException(status_code=404, detail="User not found for the given myprofile_code")

        owner_user_id = str(target_profile.get("id") or "")
        owner_display_name = target_profile.get("display_name") or None

        if not owner_user_id:
            raise HTTPException(status_code=404, detail="User not found for the given myprofile_code")

        if owner_user_id == requester_user_id:
            raise HTTPException(status_code=400, detail="You cannot request your own MyProfile")

        # If already registered -> idempotent ok
        if await _is_already_registered(requester_user_id, owner_user_id):
            return MyProfileRequestCreateResponse(
                status="already_registered",
                request_id=None,
                owner_user_id=owner_user_id,
                owner_display_name=owner_display_name,
            )

        # If pending already exists -> return that
        existing = await _find_existing_pending_request(requester_user_id, owner_user_id)
        if existing:
            return MyProfileRequestCreateResponse(
                status="already_pending",
                request_id=int(existing.get("id")),
                owner_user_id=owner_user_id,
                owner_display_name=owner_display_name,
            )

        # Create request
        payload = {
            "requester_user_id": requester_user_id,
            "requested_user_id": owner_user_id,
            "status": "pending",
        }
        resp = await _sb_post(
            "/rest/v1/myprofile_requests",
            json=payload,
            prefer="return=representation",
        )
        if resp.status_code not in (200, 201):
            # Unique pending pair index may fire -> try to return existing pending
            if resp.status_code == 409:
                existing2 = await _find_existing_pending_request(requester_user_id, owner_user_id)
                if existing2:
                    return MyProfileRequestCreateResponse(
                        status="already_pending",
                        request_id=int(existing2.get("id")),
                        owner_user_id=owner_user_id,
                        owner_display_name=owner_display_name,
                    )
            logger.error("Supabase insert myprofile_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to create myprofile request")

        data = resp.json()
        row = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
        return MyProfileRequestCreateResponse(
            status="ok",
            request_id=int(row.get("id")) if row.get("id") is not None else None,
            owner_user_id=owner_user_id,
            owner_display_name=owner_display_name,
        )

    @app.post("/myprofile/requests/{request_id}/accept", response_model=MyProfileRequestActionResponse)
    async def accept_myprofile_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="MyProfile request is not pending")

        requested_user_id = str(req.get("requested_user_id"))
        requester_user_id = str(req.get("requester_user_id"))
        if requested_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to accept this request")

        now = datetime.now(timezone.utc).isoformat()
        # Update request status
        resp = await _sb_patch(
            "/rest/v1/myprofile_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "accepted", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase update myprofile_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to accept myprofile request")

        # Create link (viewer -> owner)
        await _insert_myprofile_link(requester_user_id, requested_user_id)
        return MyProfileRequestActionResponse(status="ok", request_id=request_id)

    @app.post("/myprofile/requests/{request_id}/reject", response_model=MyProfileRequestActionResponse)
    async def reject_myprofile_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="MyProfile request is not pending")

        requested_user_id = str(req.get("requested_user_id"))
        if requested_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to reject this request")

        now = datetime.now(timezone.utc).isoformat()
        resp = await _sb_patch(
            "/rest/v1/myprofile_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "rejected", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase update myprofile_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to reject myprofile request")

        return MyProfileRequestActionResponse(status="ok", request_id=request_id)


    @app.post("/myprofile/requests/{request_id}/cancel", response_model=MyProfileRequestActionResponse)
    async def cancel_myprofile_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="MyProfile request is not pending")

        requester_user_id = str(req.get("requester_user_id"))
        if requester_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to cancel this request")

        now = datetime.now(timezone.utc).isoformat()
        resp = await _sb_patch(
            "/rest/v1/myprofile_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "cancelled", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase cancel myprofile_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to cancel myprofile request")

        return MyProfileRequestActionResponse(status="ok", request_id=request_id)




    # ------------------------------
    # Follow / Unfollow (direct link)
    # - DB: myprofile_links (viewer_user_id -> owner_user_id)
    # - Writes are performed via service_role to avoid RLS issues on the client.
    # ------------------------------

    @app.post("/myprofile/follow", response_model=MyProfileLinkActionResponse)
    async def follow_myprofile(
        body: MyProfileLinkBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLinkActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)

        owner_user_id = str(body.owner_user_id or "").strip()
        if not owner_user_id:
            code = str(body.myprofile_code or "").strip()
            if not code:
                raise HTTPException(status_code=400, detail="owner_user_id or myprofile_code is required")
            target_profile = await _lookup_profile_by_myprofile_code(code)
            if not target_profile:
                raise HTTPException(status_code=404, detail="User not found for the given myprofile_code")
            owner_user_id = str(target_profile.get("id") or "").strip()

        if not owner_user_id:
            raise HTTPException(status_code=404, detail="Owner user not found")

        if owner_user_id == viewer_user_id:
            raise HTTPException(status_code=400, detail="You cannot follow yourself")

        # If already following, treat as ok (idempotent).
        try:
            if await _is_already_registered(viewer_user_id, owner_user_id):
                return MyProfileLinkActionResponse(
                    status="ok",
                    viewer_user_id=viewer_user_id,
                    owner_user_id=owner_user_id,
                    is_following=True,
                    is_follow_requested=False,
                    result="followed",
                )
        except Exception:
            # Best-effort; fall through.
            pass

        # Private account => create a follow request (approval required)
        is_private = False
        try:
            is_private = await _is_private_account(owner_user_id)
        except Exception:
            is_private = False

        if is_private:
            existing_id = await _find_existing_follow_request_id(viewer_user_id, owner_user_id)
            if existing_id:
                return MyProfileLinkActionResponse(
                    status="ok",
                    viewer_user_id=viewer_user_id,
                    owner_user_id=owner_user_id,
                    is_following=False,
                    is_follow_requested=True,
                    result="requested",
                )

            created = await _insert_follow_request(viewer_user_id, owner_user_id)
            if not created:
                # Likely already requested (race). Treat as requested.
                return MyProfileLinkActionResponse(
                    status="ok",
                    viewer_user_id=viewer_user_id,
                    owner_user_id=owner_user_id,
                    is_following=False,
                    is_follow_requested=True,
                    result="requested",
                )

            return MyProfileLinkActionResponse(
                status="ok",
                viewer_user_id=viewer_user_id,
                owner_user_id=owner_user_id,
                is_following=False,
                is_follow_requested=True,
                result="requested",
            )

        # Public account => create link immediately
        await _insert_myprofile_link(viewer_user_id, owner_user_id)

        # If there was a pending request from the same viewer->owner, clean it up (best-effort).
        try:
            await _delete_follow_request_pair(viewer_user_id, owner_user_id)
        except Exception:
            pass

        return MyProfileLinkActionResponse(
            status="ok",
            viewer_user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            is_following=True,
            is_follow_requested=False,
            result="followed",
        )

    @app.post("/myprofile/unfollow", response_model=MyProfileLinkActionResponse)
    async def unfollow_myprofile(
        body: MyProfileLinkBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLinkActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)

        owner_user_id = str(body.owner_user_id or "").strip()
        if not owner_user_id:
            code = str(body.myprofile_code or "").strip()
            if not code:
                raise HTTPException(status_code=400, detail="owner_user_id or myprofile_code is required")
            target_profile = await _lookup_profile_by_myprofile_code(code)
            if not target_profile:
                raise HTTPException(status_code=404, detail="User not found for the given myprofile_code")
            owner_user_id = str(target_profile.get("id") or "").strip()

        if not owner_user_id:
            raise HTTPException(status_code=404, detail="Owner user not found")

        # Deleting a non-existing link is treated as ok (idempotent)
        await _delete_myprofile_link(viewer_user_id, owner_user_id)
        return MyProfileLinkActionResponse(
            status="ok",
            viewer_user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            is_following=False,
        )
    

    @app.post("/myprofile/remove-follower", response_model=MyProfileLinkActionResponse)
    async def remove_myprofile_follower(
        body: MyProfileRemoveFollowerBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLinkActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        owner_user_id = await _resolve_user_id_from_token(access_token)

        viewer_user_id = str(body.viewer_user_id or "").strip()
        if not viewer_user_id:
            raise HTTPException(status_code=400, detail="viewer_user_id is required")

        if viewer_user_id == owner_user_id:
            raise HTTPException(status_code=400, detail="You cannot remove yourself")

        # Delete follower link: viewer -> owner(me)
        await _delete_myprofile_link(viewer_user_id, owner_user_id)
        return MyProfileLinkActionResponse(
            status="ok",
            viewer_user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            is_following=False,
        )


    @app.get("/myprofile/follow-stats", response_model=MyProfileFollowStatsResponse)
    async def get_myprofile_follow_stats(
        target_user_id: str = Query(..., description="Target user's UUID (profiles.id)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileFollowStatsResponse:
        """Return follow stats for a target user.

        - following_count: number of users the target is following
        - follower_count: number of users following the target
        - is_following: whether the caller follows the target (false if not authenticated)
        """
        uid = str(target_user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        # Resolve viewer (optional). If no token, is_following is always False.
        viewer_user_id: Optional[str] = None
        access_token = _extract_bearer_token(authorization)
        if access_token:
            try:
                viewer_user_id = await _resolve_user_id_from_token(access_token)
            except Exception:
                viewer_user_id = None

        # Count following / followers via service_role (avoid client-side RLS)
        following_count = await _sb_count(
            "/rest/v1/myprofile_links",
            params={
                "select": "owner_user_id",
                "viewer_user_id": f"eq.{uid}",
                "limit": "1",
            },
        )

        follower_count = await _sb_count(
            "/rest/v1/myprofile_links",
            params={
                "select": "viewer_user_id",
                "owner_user_id": f"eq.{uid}",
                "limit": "1",
            },
        )

        is_following = False
        if viewer_user_id and str(viewer_user_id) != uid:
            try:
                is_following = await _is_already_registered(str(viewer_user_id), uid)
            except Exception:
                is_following = False

        is_follow_requested = False
        if viewer_user_id and str(viewer_user_id) != uid and (not is_following):
            try:
                is_follow_requested = bool(await _has_follow_request(str(viewer_user_id), uid))
            except Exception:
                is_follow_requested = False

        return MyProfileFollowStatsResponse(
            status="ok",
            target_user_id=uid,
            following_count=int(following_count or 0),
            follower_count=int(follower_count or 0),
            is_following=bool(is_following),
            is_follow_requested=bool(is_follow_requested),
        )



    @app.post("/myprofile/follow-request/cancel")
    async def cancel_follow_request(
        body: MyProfileFollowRequestCancelBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        requester_user_id = await _resolve_user_id_from_token(access_token)
        tgt = str(body.target_user_id or "").strip()
        if not tgt:
            return JSONResponse(status_code=400, content={"detail": "target_user_id is required", "code": "invalid_target_user_id"})
        if tgt == str(requester_user_id):
            return JSONResponse(status_code=400, content={"detail": "You cannot cancel for yourself", "code": "invalid_target_user_id"})

        existing_id = await _find_existing_follow_request_id(str(requester_user_id), tgt)
        if not existing_id:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        await _delete_follow_request_pair(str(requester_user_id), tgt)
        return {"status": "ok", "result": "canceled", "target_user_id": tgt}


    @app.get("/myprofile/follow-requests/incoming", response_model=MyProfileIncomingFollowRequestsResponse)
    async def incoming_follow_requests(
        limit: int = Query(default=100, ge=1, le=300, description="Max number of requests"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileIncomingFollowRequestsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
            params={
                "select": "id,requester_user_id,created_at",
                "target_user_id": f"eq.{me}",
                "order": "created_at.desc",
                "limit": str(int(limit)),
            },
        )
        if resp.status_code >= 300:
            logger.error("Supabase follow_requests incoming failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to load follow requests")

        rows = resp.json()
        if not isinstance(rows, list):
            rows = []

        requester_ids = [str((r or {}).get("requester_user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles_map = await _fetch_profiles_basic_map(requester_ids)

        items: list[MyProfileIncomingFollowRequestItem] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            req_id = str(r.get("id") or "").strip()
            requester_id = str(r.get("requester_user_id") or "").strip()
            if not req_id or not requester_id:
                continue
            p = profiles_map.get(requester_id) or {}
            items.append(
                MyProfileIncomingFollowRequestItem(
                    request_id=req_id,
                    requester_user_id=requester_id,
                    requester_display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    requester_myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    created_at=(str(r.get("created_at")) if r.get("created_at") is not None else None),
                )
            )

        return MyProfileIncomingFollowRequestsResponse(status="ok", total_items=len(items), requests=items)


    @app.get("/myprofile/follow-requests/outgoing", response_model=MyProfileOutgoingFollowRequestsResponse)
    async def outgoing_follow_requests(
        limit: int = Query(default=100, ge=1, le=300, description="Max number of requests"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileOutgoingFollowRequestsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
            params={
                "select": "id,target_user_id,created_at",
                "requester_user_id": f"eq.{me}",
                "order": "created_at.desc",
                "limit": str(int(limit)),
            },
        )
        if resp.status_code >= 300:
            logger.error("Supabase follow_requests outgoing failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to load follow requests")

        rows = resp.json()
        if not isinstance(rows, list):
            rows = []

        target_ids = [str((r or {}).get("target_user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles_map = await _fetch_profiles_basic_map(target_ids)

        items: list[MyProfileOutgoingFollowRequestItem] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            req_id = str(r.get("id") or "").strip()
            target_id = str(r.get("target_user_id") or "").strip()
            if not req_id or not target_id:
                continue
            p = profiles_map.get(target_id) or {}
            items.append(
                MyProfileOutgoingFollowRequestItem(
                    request_id=req_id,
                    target_user_id=target_id,
                    target_display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    target_myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    created_at=(str(r.get("created_at")) if r.get("created_at") is not None else None),
                )
            )

        return MyProfileOutgoingFollowRequestsResponse(status="ok", total_items=len(items), requests=items)


    @app.post("/myprofile/follow-requests/approve")
    async def approve_follow_request(
        body: MyProfileFollowRequestIdBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        request_id = str(body.request_id or "").strip()
        if not request_id:
            return JSONResponse(status_code=400, content={"detail": "request_id is required", "code": "invalid_request_id"})

        req = await _get_follow_request_by_id(request_id)
        if not req:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        target_user_id = str(req.get("target_user_id") or "").strip()
        requester_user_id = str(req.get("requester_user_id") or "").strip()
        if not target_user_id or not requester_user_id:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        if str(target_user_id) != str(me):
            raise HTTPException(status_code=403, detail="You are not allowed to approve this request")

        # Create link (requester follows me)
        await _insert_myprofile_link(requester_user_id, str(me))

        # Remove request (best-effort)
        try:
            await _delete_follow_request_by_id(request_id)
        except Exception:
            pass

        return {
            "status": "ok",
            "result": "approved",
            "request_id": request_id,
            "requester_user_id": requester_user_id,
            "target_user_id": str(me),
        }


    @app.post("/myprofile/follow-requests/reject")
    async def reject_follow_request(
        body: MyProfileFollowRequestIdBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        request_id = str(body.request_id or "").strip()
        if not request_id:
            return JSONResponse(status_code=400, content={"detail": "request_id is required", "code": "invalid_request_id"})

        req = await _get_follow_request_by_id(request_id)
        if not req:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        target_user_id = str(req.get("target_user_id") or "").strip()
        if str(target_user_id) != str(me):
            raise HTTPException(status_code=403, detail="You are not allowed to reject this request")

        await _delete_follow_request_by_id(request_id)

        return {
            "status": "ok",
            "result": "rejected",
            "request_id": request_id,
        }


    @app.get("/myprofile/follow-list", response_model=MyProfileFollowListResponse)
    async def get_myprofile_follow_list(
        target_user_id: str = Query(..., description="Target user's UUID (profiles.id)"),
        tab: str = Query(default="following", description="following | followers"),
        limit: int = Query(default=1000, ge=1, le=1000, description="Max number of rows"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileFollowListResponse:
        """Return follow list (profiles) for a target user.

        - tab=following: users the target is following
        - tab=followers: users who follow the target
        """
        uid = str(target_user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        t = str(tab or "").strip().lower()
        if t not in ("following", "followers"):
            t = "following"

        # authorization is accepted for future-proofing, but currently optional
        _ = authorization  # noqa: F841

        # Phase2: Fetch follow list via Supabase RPC (single roundtrip)
        fn = (MYPROFILE_FOLLOW_LIST_RPC or "myprofile_follow_list_v1").strip() or "myprofile_follow_list_v1"
        payload = {
            "p_target_user_id": uid,
            "p_tab": t,
            "p_limit": int(limit),
        }
        resp = await _sb_post_rpc(fn, payload=payload)
        if resp.status_code >= 300:
            logger.error(
                "Supabase rpc %s failed: %s %s",
                fn,
                resp.status_code,
                (resp.text or "")[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to load follow list")

        data = resp.json()
        if not isinstance(data, list):
            data = []

        ordered: list[MyProfileFollowListItem] = []
        for r in data:
            if not isinstance(r, dict):
                continue
            pid = str(r.get("id") or "").strip()
            if not pid:
                continue
            ordered.append(
                MyProfileFollowListItem(
                    id=pid,
                    display_name=(r.get("display_name") if isinstance(r.get("display_name"), str) else None),
                    friend_code=(r.get("friend_code") if isinstance(r.get("friend_code"), str) else None),
                    myprofile_code=(r.get("myprofile_code") if isinstance(r.get("myprofile_code"), str) else None),
                    is_private_account=bool(r.get("is_private_account") or False),
                )
            )

        return MyProfileFollowListResponse(
            status="ok",
            target_user_id=uid,
            tab=t,
            rows=ordered,
        )
    @app.get("/myprofile/latest/status", response_model=MyProfileLatestStatusResponse)
    async def get_myprofile_latest_status(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLatestStatusResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        uid = await _resolve_user_id_from_token(access_token)

        try:
            resp = await _sb_get(
                "/rest/v1/myprofile_reports",
                params={
                    "select": "generated_at,content_text,content_json,title,period_start,period_end",
                    "user_id": f"eq.{uid}",
                    "report_type": "eq.latest",
                    "order": "generated_at.desc",
                    "limit": "1",
                },
            )
            if resp.status_code >= 300:
                logger.error(
                    "Supabase select myprofile_reports(latest status) failed: %s %s",
                    resp.status_code,
                    resp.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to load latest MyProfile status")
            rows = resp.json()
            latest_row = rows[0] if isinstance(rows, list) and rows else None
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to load latest MyProfile status: %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load latest MyProfile status")

        return MyProfileLatestStatusResponse(
            version_key=_build_latest_version_key(latest_row),
            generated_at=(latest_row.get("generated_at") if latest_row else None),
            saved_report_mode=_extract_saved_report_mode(latest_row) if latest_row else None,
            has_visible_content=_extract_saved_has_visible_content(latest_row) if latest_row else False,
            skip_reason=_extract_saved_skip_reason(latest_row) if latest_row else None,
        )


    @app.get("/myprofile/latest", response_model=MyProfileLatestEnsureResponse)
    async def get_or_refresh_myprofile_latest(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
        ensure: bool = Query(
            default=True,
            description="If true, regenerate when stale/missing",
        ),
        force: bool = Query(
            default=False,
            description="If true, force regeneration",
        ),
        period: Optional[str] = Query(
            default=None,
            description="Override lookback period (e.g. 28d)",
        ),
        report_mode: Optional[str] = Query(
            default=None,
            description="Requested report mode (standard|deep). Tier-gated.",
        ),
    ) -> MyProfileLatestEnsureResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token is required",
            )

        user_id = await _resolve_user_id_from_token(access_token)
        uid = str(user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=401, detail="Failed to resolve user id")

        effective_period = (period or DEFAULT_LATEST_PERIOD or "28d").strip() or "28d"

        # ---- Resolve report_mode (with subscription gating; fail-closed) ----
        # Spec v2: free users cannot view MyProfile self-structure reports.
        effective_report_mode = "standard"
        try:
            from subscription import (
                SubscriptionTier,
                MyProfileMode,
                normalize_myprofile_mode,
                is_myprofile_mode_allowed,
                allowed_myprofile_modes_for_tier,
            )
            from subscription_store import get_subscription_tier_for_user

            tier = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
            if tier == SubscriptionTier.FREE:
                raise HTTPException(status_code=403, detail="MyProfile report is available for Plus/Premium users only")

            default_mode = MyProfileMode.STRUCTURAL if tier == SubscriptionTier.PREMIUM else MyProfileMode.STANDARD
            requested_mode = _subscription_mode_input(report_mode)
            mode_enum = normalize_myprofile_mode(requested_mode, default=default_mode)

            # "light" is kept only for backward-compat input; disallow for MyProfile.
            if mode_enum == MyProfileMode.LIGHT:
                raise HTTPException(status_code=403, detail="report_mode 'light' is not available")

            if not is_myprofile_mode_allowed(tier, mode_enum):
                allowed = [
                    _canonicalize_report_mode_value(m.value)
                    for m in allowed_myprofile_modes_for_tier(tier)
                    if m != MyProfileMode.LIGHT
                ]
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"report_mode '{_canonicalize_report_mode_value(mode_enum.value)}' is not allowed for tier '{tier.value}'. "
                        f"Allowed: {', '.join(allowed)}"
                    ),
                )
            effective_report_mode = _canonicalize_report_mode_value(mode_enum.value)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Failed to resolve subscription tier/report_mode (deny): %s", exc)
            raise HTTPException(status_code=403, detail="MyProfile report is not available")

        # ---- Fetch latest self-structure analysis refs (stale source-of-truth) ----
        latest_analysis_rows: Dict[str, Optional[Dict[str, Any]]] = {}
        latest_analysis_updated_at: Optional[str] = None
        try:
            latest_analysis_rows["standard"] = await _fetch_latest_self_structure_analysis_row(uid, "standard")
            if effective_report_mode == "deep":
                latest_analysis_rows["deep"] = await _fetch_latest_self_structure_analysis_row(uid, "deep")
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Failed to fetch self structure analysis refs: %s", exc)
            latest_analysis_rows = {}

        def _parse_iso(iso: Optional[str]) -> Optional[datetime]:
            if not iso:
                return None
            try:
                s = str(iso).replace("Z", "+00:00")
                return datetime.fromisoformat(s)
            except Exception:
                return None

        latest_analysis_dt: Optional[datetime] = None
        for _stage_row in latest_analysis_rows.values():
            if not isinstance(_stage_row, dict):
                continue
            cand_iso = _stage_row.get("updated_at") or _stage_row.get("created_at")
            cand_dt = _parse_iso(cand_iso)
            if cand_dt and (latest_analysis_dt is None or cand_dt > latest_analysis_dt):
                latest_analysis_dt = cand_dt
                latest_analysis_updated_at = cand_iso

        # ---- Fetch latest report row ----
        latest_row: Optional[Dict[str, Any]] = None
        latest_generated_at: Optional[str] = None
        try:
            resp = await _sb_get(
                "/rest/v1/myprofile_reports",
                params={
                    "select": "id,title,content_text,generated_at,content_json,period_start,period_end",
                    "user_id": f"eq.{uid}",
                    "report_type": "eq.latest",
                    "order": "generated_at.desc",
                    "limit": "1",
                },
            )
            if resp.status_code >= 300:
                logger.error(
                    "Supabase myprofile_reports select failed: %s %s",
                    resp.status_code,
                    resp.text[:1500],
                )
                raise HTTPException(
                    status_code=502, detail="Failed to load latest MyProfile report"
                )
            rows = resp.json()
            if isinstance(rows, list) and rows:
                latest_row = rows[0]
                latest_generated_at = latest_row.get("generated_at")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to load latest MyProfile report: %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load latest MyProfile report")

        latest_dt = _parse_iso(latest_generated_at)
        patterns_updated_at = latest_analysis_updated_at

        def _latest_response_from_row(
            row: Optional[Dict[str, Any]],
            *,
            refreshed: bool,
            reason_value: str,
            generated_at_value: Optional[str] = None,
        ) -> MyProfileLatestEnsureResponse:
            report_meta = _extract_report_content_json(row) if row else None
            period_start_value, period_end_value = _extract_report_window(row)
            generated_value = generated_at_value or (row.get("generated_at") if row else latest_generated_at)
            return MyProfileLatestEnsureResponse(
                refreshed=refreshed,
                reason=reason_value,
                report_mode=effective_report_mode,
                period=effective_period,
                patterns_updated_at=patterns_updated_at,
                latest_generated_at=(row.get("generated_at") if row else latest_generated_at),
                generated_at=generated_value,
                period_start=period_start_value,
                period_end=period_end_value,
                title=(row.get("title") if row else None),
                content_text=_sanitize_self_structure_report_text(
                    row.get("content_text") if row else None
                ),
                meta=report_meta,
                has_visible_content=_extract_saved_has_visible_content(row) if row else False,
                skip_reason=_extract_saved_skip_reason(row) if row else None,
            )

        stale = False
        reason = "up_to_date"

        required_analysis_stages = ["standard"] + (["deep"] if effective_report_mode == "deep" else [])

        if force:
            stale = True
            reason = "force"
        elif not latest_row or not str(latest_row.get("content_text") or "").strip():
            stale = True
            reason = "missing"
        elif not _row_matches_requested_mode(latest_row, effective_report_mode):
            stale = True
            reason = "mode_mismatch"
        elif not _row_uses_current_myprofile_schema(latest_row):
            stale = True
            reason = "schema_mismatch"
        else:
            analysis_missing = False
            analysis_changed = False
            for stage_key in required_analysis_stages:
                live_row = latest_analysis_rows.get(stage_key)
                if not live_row:
                    analysis_missing = True
                    continue
                saved_hash = _extract_saved_self_structure_ref_source_hash(latest_row, stage_key)
                live_hash = str(live_row.get("source_hash") or "").strip() or None
                if (not saved_hash) or saved_hash != live_hash:
                    analysis_changed = True
            if analysis_missing or analysis_changed:
                stale = True
                reason = "stale_analysis"
            elif latest_analysis_dt and latest_dt and latest_analysis_dt > (latest_dt + timedelta(seconds=1)):
                stale = True
                reason = "stale_analysis"
            elif latest_analysis_dt and not latest_dt:
                stale = True
                reason = "stale_analysis"
            elif not latest_analysis_dt:
                reason = "no_analysis"

        if ensure and stale:
            async def _refetch_latest_row() -> Optional[Dict[str, Any]]:
                try:
                    resp = await _sb_get(
                        "/rest/v1/myprofile_reports",
                        params={
                            "select": "id,title,content_text,generated_at,content_json,period_start,period_end",
                            "user_id": f"eq.{uid}",
                            "report_type": "eq.latest",
                            "order": "generated_at.desc",
                            "limit": "1",
                        },
                    )
                    if resp.status_code < 300:
                        rows = resp.json()
                        if isinstance(rows, list) and rows:
                            return rows[0]
                except Exception:
                    return None
                return None

            try:
                from astor_myprofile_report import refresh_myprofile_latest_report

                refresh_result = await refresh_myprofile_latest_report(
                    user_id=uid,
                    trigger="on_demand_myprofile_latest",
                    force=True,
                    period_override=effective_period,
                    report_mode_override=effective_report_mode,
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Failed to refresh latest MyProfile report: %s", exc)
                raise HTTPException(
                    status_code=500, detail="Failed to generate latest MyProfile report"
                )

            refresh_status = str((refresh_result or {}).get("status") or "").strip().lower()
            if refresh_status == "skipped_locked":
                waited = None
                if poll_until is not None and MYPROFILE_LATEST_LOCK_WAIT_SECONDS > 0:
                    waited = await poll_until(
                        _refetch_latest_row,
                        timeout_seconds=MYPROFILE_LATEST_LOCK_WAIT_SECONDS,
                    )
                row = waited or latest_row
                if row and (not _row_matches_requested_mode(row, effective_report_mode)):
                    row = None
                return _latest_response_from_row(
                    row,
                    refreshed=False,
                    reason_value="in_progress",
                )

            if refresh_status == "empty":
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate latest MyProfile report",
                )

            if refresh_status == "no_visible_content":
                return MyProfileLatestEnsureResponse(
                    refreshed=False,
                    reason=str((refresh_result or {}).get("skip_reason") or "no_visible_content"),
                    report_mode=effective_report_mode,
                    period=effective_period,
                    patterns_updated_at=patterns_updated_at,
                    latest_generated_at=latest_generated_at,
                    generated_at=(str((refresh_result or {}).get("generated_at") or "").strip() or None),
                    period_start=(str((refresh_result or {}).get("period_start") or "").strip() or None),
                    period_end=(str((refresh_result or {}).get("period_end") or "").strip() or None),
                    title=(str((refresh_result or {}).get("title") or "").strip() or None),
                    content_text=_sanitize_self_structure_report_text((refresh_result or {}).get("content_text")),
                    meta=((refresh_result or {}).get("meta") if isinstance((refresh_result or {}).get("meta"), dict) else None),
                    has_visible_content=False,
                    skip_reason=(str((refresh_result or {}).get("skip_reason") or "").strip() or None),
                )

            refreshed_row = await _refetch_latest_row()
            if refreshed_row and (not _row_matches_requested_mode(refreshed_row, effective_report_mode)):
                refreshed_row = None

            return _latest_response_from_row(
                refreshed_row or latest_row,
                refreshed=(refresh_status == "ok"),
                reason_value=reason,
                generated_at_value=(str((refresh_result or {}).get("generated_at") or "").strip() or None),
            )

        return _latest_response_from_row(
            latest_row,
            refreshed=False,
            reason_value=reason,
        )


    @app.post("/myprofile/monthly/ensure", response_model=MyProfileMonthlyEnsureResponse)
    async def ensure_myprofile_monthly_report(
        body: MyProfileMonthlyEnsureBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileMonthlyEnsureResponse:
        """Ensure the current month's distributed MyProfile monthly report exists.

        Design:
        - JST month boundary anchored: dist = (this month 1st 00:00 JST)
        - period_end = dist - 1ms
        - period_start = dist - <period_days> days
        - By default (force=false): if a row exists for this period, return it without regenerating.
        """
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token is required",
            )

        user_id = await _resolve_user_id_from_token(access_token)
        uid = str(user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=401, detail="Failed to resolve user id")

        # resolve params
        force = bool(body.force)
        include_secret = bool(body.include_secret)
        effective_period = (body.period or DEFAULT_MONTHLY_DISTRIBUTION_PERIOD or "28d").strip() or "28d"
        distribution_origin = bool(body.distribution_origin or str(body.trigger or "").strip() == "internal_rollover")

        # ---- Resolve report_mode (with subscription gating; fail-closed) ----
        # Spec v2: free users cannot view MyProfile self-structure reports.
        effective_report_mode = "standard"
        try:
            from subscription import (
                SubscriptionTier,
                MyProfileMode,
                normalize_myprofile_mode,
                is_myprofile_mode_allowed,
                allowed_myprofile_modes_for_tier,
            )
            from subscription_store import get_subscription_tier_for_user

            tier = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
            if tier == SubscriptionTier.FREE:
                raise HTTPException(status_code=403, detail="MyProfile report is available for Plus/Premium users only")

            default_mode = MyProfileMode.STRUCTURAL if tier == SubscriptionTier.PREMIUM else MyProfileMode.STANDARD
            requested_mode = _subscription_mode_input(body.report_mode)
            mode_enum = normalize_myprofile_mode(requested_mode, default=default_mode)

            if mode_enum == MyProfileMode.LIGHT:
                raise HTTPException(status_code=403, detail="report_mode 'light' is not available")

            if not is_myprofile_mode_allowed(tier, mode_enum):
                allowed = [
                    _canonicalize_report_mode_value(m.value)
                    for m in allowed_myprofile_modes_for_tier(tier)
                    if m != MyProfileMode.LIGHT
                ]
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"report_mode '{_canonicalize_report_mode_value(mode_enum.value)}' is not allowed for tier '{tier.value}'. "
                        f"Allowed: {', '.join(allowed)}"
                    ),
                )
            effective_report_mode = _canonicalize_report_mode_value(mode_enum.value)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Failed to resolve subscription tier/report_mode (deny): %s", exc)
            raise HTTPException(status_code=403, detail="MyProfile report is not available")

        # ---- time helpers (JST fixed) ----
        JST = timezone(timedelta(hours=9))

        def _parse_now_utc(now_iso: Optional[str]) -> datetime:
            if not now_iso:
                return datetime.now(timezone.utc)
            try:
                s = str(now_iso).strip()
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid now_iso (must be ISO datetime in UTC)",
                )

        def _to_iso_z(dt: datetime) -> str:
            dtu = dt.astimezone(timezone.utc)
            return dtu.isoformat().replace("+00:00", "Z")

        def _format_jst_md(dt_utc: datetime) -> str:
            j = dt_utc.astimezone(JST)
            return f"{j.month}/{j.day}"

        # parse period days via astor_myprofile_report (keeps behavior consistent)
        try:
            from astor_myprofile_report import parse_period_days
            period_days = parse_period_days(effective_period)
        except Exception:
            # fallback: 28 days
            period_days = 28

        now_utc = _parse_now_utc(body.now_iso)

        # distribution time: 1st 00:00 JST of current month
        now_jst = now_utc.astimezone(JST)
        dist_jst = datetime(now_jst.year, now_jst.month, 1, 0, 0, 0, 0, tzinfo=JST)
        dist_utc = dist_jst.astimezone(timezone.utc)

        period_end_utc = dist_utc - timedelta(milliseconds=1)
        period_start_utc = dist_utc - timedelta(days=max(period_days, 1))

        period_start_iso = _to_iso_z(period_start_utc)
        period_end_iso = _to_iso_z(period_end_utc)
        distribution_key = (
            _normalize_distribution_key(body.distribution_key)
            or _distribution_key_from_requested_at(body.requested_at)
            or dist_jst.date().isoformat()
        )

        title = SELF_STRUCTURE_MONTHLY_TITLE_BASE

        # ---- helper: fetch existing row for this period ----
        async def _fetch_report_for_period(ps: str, pe: str) -> Optional[Dict[str, Any]]:
            resp = await _sb_get(
                "/rest/v1/myprofile_reports",
                params={
                    "select": "id,title,content_text,content_json,generated_at,updated_at,period_start,period_end",
                    "user_id": f"eq.{uid}",
                    "report_type": "eq.monthly",
                    "period_start": f"eq.{ps}",
                    "period_end": f"eq.{pe}",
                    "limit": "1",
                },
            )
            if resp.status_code >= 300:
                logger.error(
                    "Supabase myprofile_reports(monthly) select failed: %s %s",
                    resp.status_code,
                    resp.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to query monthly MyProfile report")
            rows = resp.json()
            if isinstance(rows, list) and rows:
                return rows[0]
            return None

        async def _fetch_previous_saved_report(before_period_end_iso: str) -> Optional[Dict[str, Any]]:
            resp = await _sb_get(
                "/rest/v1/myprofile_reports",
                params={
                    "select": "id,title,content_text,content_json,generated_at,updated_at,period_start,period_end",
                    "user_id": f"eq.{uid}",
                    "report_type": "eq.monthly",
                    "period_end": f"lt.{before_period_end_iso}",
                    "order": "period_end.desc,generated_at.desc",
                    "limit": "1",
                },
            )
            if resp.status_code >= 300:
                logger.error(
                    "Supabase myprofile_reports(previous monthly) select failed: %s %s",
                    resp.status_code,
                    resp.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to query previous monthly MyProfile report")
            rows = resp.json()
            if isinstance(rows, list) and rows:
                return rows[0]
            return None

        async def _delete_report_row_if_present(row: Optional[Dict[str, Any]]) -> None:
            if not isinstance(row, dict):
                return
            row_id = row.get("id")
            if row_id is None:
                return
            resp = await _sb_delete(
                "/rest/v1/myprofile_reports",
                params={"id": f"eq.{row_id}"},
            )
            if resp.status_code not in (200, 204):
                logger.error(
                    "Supabase myprofile_reports(monthly) delete failed: %s %s",
                    resp.status_code,
                    resp.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to delete stale monthly MyProfile report")

        def _monthly_response_from_row(
            row: Optional[Dict[str, Any]],
            *,
            refreshed: bool,
            reason_value: str,
            generated_at_value: Optional[str] = None,
            history_saved: bool = False,
            has_visible_content: Optional[bool] = None,
            skip_reason_value: Optional[str] = None,
            meta_override: Optional[Dict[str, Any]] = None,
            text_override: Optional[str] = None,
            title_override: Optional[str] = None,
        ) -> MyProfileMonthlyEnsureResponse:
            report_meta = meta_override if isinstance(meta_override, dict) else _extract_report_content_json(row)
            has_visible = _extract_saved_has_visible_content(row) if has_visible_content is None else bool(has_visible_content)
            skip_reason_final = skip_reason_value if skip_reason_value is not None else _extract_saved_skip_reason(row)
            return MyProfileMonthlyEnsureResponse(
                refreshed=refreshed,
                reason=reason_value,
                report_mode=effective_report_mode,
                period=effective_period,
                period_start=period_start_iso,
                period_end=period_end_iso,
                generated_at=generated_at_value or (row.get("generated_at") if row else None) or (row.get("updated_at") if row else None),
                title=_sanitize_self_structure_monthly_title(
                    title_override or (row.get("title") if row else None) or title
                ),
                content_text=_sanitize_self_structure_report_text(
                    text_override if text_override is not None else (row.get("content_text") if row else None)
                ),
                meta=report_meta,
                history_saved=history_saved,
                has_visible_content=has_visible,
                skip_reason=skip_reason_final,
            )

        existing_row = await _fetch_report_for_period(period_start_iso, period_end_iso)
        existing_row_mode_matches = _row_matches_requested_mode(existing_row, effective_report_mode)
        existing_row_schema_matches = _row_uses_current_myprofile_schema(existing_row)
        existing_row_is_legacy = bool(existing_row and not existing_row_schema_matches)

        if existing_row and (not force) and existing_row_mode_matches and existing_row_schema_matches:
            if distribution_origin:
                await _enqueue_self_structure_monthly_distribution_candidate(
                    user_id=uid,
                    distribution_key=distribution_key,
                    report_row=existing_row,
                    period_start=period_start_iso,
                    period_end=period_end_iso,
                )
            return _monthly_response_from_row(
                existing_row,
                refreshed=False,
                reason_value="up_to_date",
                history_saved=True,
            )

        # ---- Phase10: generation lock (avoid duplicate compute) ----
        lock_key = None
        lock_owner = None
        lock_acquired = True
        if build_lock_key is not None and try_acquire_lock is not None:
            try:
                lock_key = build_lock_key(
                    namespace="myprofile",
                    user_id=uid,
                    report_type="monthly",
                    period_start=period_start_iso,
                    period_end=period_end_iso,
                )
                lock_owner = (make_owner_id("myprofile_monthly") if make_owner_id is not None else None)
                lr = await try_acquire_lock(
                    lock_key=lock_key,
                    ttl_seconds=MYPROFILE_MONTHLY_LOCK_TTL_SECONDS,
                    owner_id=lock_owner,
                    context={
                        "namespace": "myprofile",
                        "user_id": uid,
                        "report_type": "monthly",
                        "period": effective_period,
                        "report_mode": effective_report_mode,
                        "period_start": period_start_iso,
                        "period_end": period_end_iso,
                        "source": "myprofile.monthly.ensure",
                    },
                )
                lock_acquired = bool(getattr(lr, "acquired", False))
                lock_owner = getattr(lr, "owner_id", lock_owner)
            except Exception:
                lock_acquired = True

        if not lock_acquired:
            waited_row = None
            if poll_until is not None and MYPROFILE_MONTHLY_LOCK_WAIT_SECONDS > 0:
                waited_row = await poll_until(
                    lambda: _fetch_report_for_period(period_start_iso, period_end_iso),
                    timeout_seconds=MYPROFILE_MONTHLY_LOCK_WAIT_SECONDS,
                )
            row = waited_row or existing_row
            if row and (not _row_matches_requested_mode(row, effective_report_mode)):
                row = None
            if row:
                return _monthly_response_from_row(
                    row,
                    refreshed=False,
                    reason_value="in_progress",
                    history_saved=bool(row),
                )
            raise HTTPException(status_code=409, detail="Monthly report generation is in progress")

        # ---- previous saved monthly report (for diff summary / unchanged skip) ----
        prev_saved_row: Optional[Dict[str, Any]] = None
        prev_report_text: Optional[str] = None
        prev_report_json: Optional[Dict[str, Any]] = None
        try:
            prev_saved_row = await _fetch_previous_saved_report(period_end_iso)
            if prev_saved_row:
                if prev_saved_row.get("content_text"):
                    prev_report_text = str(prev_saved_row.get("content_text"))
                prev_cj = _extract_report_content_json(prev_saved_row)
                if prev_cj:
                    prev_report_json = dict(prev_cj)
        except Exception:
            prev_saved_row = None
            prev_report_text = None
            prev_report_json = None

        # ---- generate + save (server-side) ----
        try:
            try:
                from astor_myprofile_report import refresh_myprofile_monthly_report

                refresh_result = await refresh_myprofile_monthly_report(
                    user_id=uid,
                    period_override=effective_period,
                    report_mode_override=effective_report_mode,
                    include_secret=include_secret,
                    now=dist_utc,
                    prev_report_text=prev_report_text,
                    prev_report_json=prev_report_json,
                    distribution_utc=_to_iso_z(dist_utc),
                )
                report_text = str(refresh_result.get("report_text") or "")
                report_meta = refresh_result.get("report_meta") if isinstance(refresh_result, dict) else {}
            except Exception as exc:
                logger.error("Failed to build monthly MyProfile report: %s", exc)
                raise HTTPException(status_code=500, detail="Failed to generate monthly MyProfile report")

            report_text = _sanitize_self_structure_report_text(
                str(report_text or "").strip()
            )
            if not report_text:
                raise HTTPException(status_code=500, detail="Monthly MyProfile report text was empty")

            generated_at = _to_iso_z(dist_utc)
            visibility = report_meta.get("visibility") if isinstance(report_meta, dict) else {}
            history_meta = report_meta.get("history") if isinstance(report_meta, dict) else {}
            has_visible_content = bool((visibility or {}).get("has_visible_content"))
            history_fingerprint = str((history_meta or {}).get("history_fingerprint") or "").strip() or None
            prev_history_fingerprint = _extract_saved_history_fingerprint(prev_saved_row)

            content_json = {
                **(report_meta or {}),
                "source": "myprofile.monthly.ensure",
                "report_type": "monthly",
                "report_mode": effective_report_mode,
                "distribution_utc": _to_iso_z(dist_utc),
                "distribution_jst": dist_jst.isoformat(),
                "generated_at_server": _to_iso_z(datetime.now(timezone.utc)),
                "period_start": period_start_iso,
                "period_end": period_end_iso,
                "period_days": period_days,
            }

            if not has_visible_content:
                if existing_row_is_legacy:
                    await _delete_report_row_if_present(existing_row)
                return _monthly_response_from_row(
                    None,
                    refreshed=False,
                    reason_value=str((history_meta or {}).get("skip_reason") or "no_visible_content"),
                    generated_at_value=generated_at,
                    history_saved=False,
                    has_visible_content=False,
                    skip_reason_value=str((history_meta or {}).get("skip_reason") or "no_visible_content"),
                    meta_override=content_json,
                    text_override=report_text,
                    title_override=title,
                )

            if history_fingerprint and prev_history_fingerprint and history_fingerprint == prev_history_fingerprint:
                if existing_row_is_legacy:
                    await _delete_report_row_if_present(existing_row)
                return _monthly_response_from_row(
                    None,
                    refreshed=False,
                    reason_value="unchanged",
                    generated_at_value=generated_at,
                    history_saved=False,
                    has_visible_content=True,
                    skip_reason_value="unchanged",
                    meta_override=content_json,
                    text_override=report_text,
                    title_override=title,
                )

            content_json["history"] = {
                **(content_json.get("history") if isinstance(content_json.get("history"), dict) else {}),
                "archive_eligible": True,
                "history_fingerprint": history_fingerprint,
                "skip_reason": None,
                "history_saved": True,
            }

            payload = {
                "user_id": uid,
                "report_type": "monthly",
                "period_start": period_start_iso,
                "period_end": period_end_iso,
                "title": title,
                "content_text": report_text,
                "content_json": content_json,
                "generated_at": generated_at,
            }

            # upsert by unique key
            resp2 = await _sb_post(
                "/rest/v1/myprofile_reports?on_conflict=user_id,report_type,period_start,period_end",
                json=payload,
                prefer="resolution=merge-duplicates,return=representation",
            )
            if resp2.status_code not in (200, 201):
                logger.error(
                    "Supabase myprofile_reports(monthly) upsert failed: %s %s",
                    resp2.status_code,
                    resp2.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to save monthly MyProfile report")

            saved_rows = resp2.json()
            saved_row = saved_rows[0] if isinstance(saved_rows, list) and saved_rows and isinstance(saved_rows[0], dict) else payload
            if distribution_origin:
                await _enqueue_self_structure_monthly_distribution_candidate(
                    user_id=uid,
                    distribution_key=distribution_key,
                    report_row=saved_row,
                    period_start=period_start_iso,
                    period_end=period_end_iso,
                )

            reason = "force" if force else ("missing" if not existing_row else ("mode_mismatch" if not existing_row_mode_matches else ("schema_mismatch" if not existing_row_schema_matches else "force")))

            return _monthly_response_from_row(
                saved_row,
                refreshed=True,
                reason_value=reason,
                generated_at_value=generated_at,
                history_saved=True,
                has_visible_content=True,
                skip_reason_value=None,
                meta_override=content_json,
                text_override=report_text,
                title_override=title,
            )
        finally:
            if lock_key and release_lock is not None:
                await release_lock(lock_key=lock_key, owner_id=lock_owner)
