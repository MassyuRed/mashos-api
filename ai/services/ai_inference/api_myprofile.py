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

import logging
import os
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

logger = logging.getLogger("myprofile_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

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


class MyProfileFollowListResponse(BaseModel):
    status: str = Field(..., description="ok")
    target_user_id: str
    tab: str = Field(..., description="following | followers")
    rows: list[MyProfileFollowListItem]






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
        description="missing | stale_patterns | force | up_to_date | no_patterns",
    )
    report_mode: str = Field(..., description="standard | structural")
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
    title: Optional[str] = Field(default=None, description="report title")
    content_text: Optional[str] = Field(default=None, description="report body")


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
        description="Requested report mode (standard|structural). Tier-gated.",
    )
    include_secret: bool = Field(
        default=True,
        description="true の場合、secret も含めて自己レポートを生成する。",
    )
    now_iso: Optional[str] = Field(
        default=None,
        description="テスト用: 現在時刻(UTC ISO)。未指定ならサーバ現在時刻。",
    )


class MyProfileMonthlyEnsureResponse(BaseModel):
    status: str = Field("ok", description="ok")
    refreshed: bool = Field(..., description="True if regenerated & saved")
    reason: str = Field(..., description="missing | force | up_to_date")
    report_mode: str = Field(..., description="standard | structural")
    period: str = Field(..., description="lookback period (e.g. 28d)")
    period_start: str = Field(..., description="period_start (ISO)")
    period_end: str = Field(..., description="period_end (ISO)")
    generated_at: Optional[str] = Field(default=None, description="generated_at of returned report")
    title: Optional[str] = Field(default=None, description="report title")
    content_text: Optional[str] = Field(default=None, description="report body")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="metadata JSON")

# ----------------------------
# Supabase helpers
# ----------------------------


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.get(url, headers=_sb_headers_json(), params=params)


async def _sb_count(path: str, *, params: Dict[str, str]) -> int:
    """Return exact row count for a given REST endpoint query (PostgREST count header)."""
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(
            url,
            headers=_sb_headers_json(prefer="count=exact"),
            params=params,
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
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.post(url, headers=_sb_headers_json(prefer=prefer), json=json)


async def _sb_patch(path: str, *, params: Dict[str, str], json: Any, prefer: Optional[str] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.patch(url, headers=_sb_headers_json(prefer=prefer), params=params, json=json)


async def _sb_delete(path: str, *, params: Dict[str, str]) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.delete(url, headers=_sb_headers_json(), params=params)


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

        # 1) link table -> ordered ids
        if t == "following":
            resp = await _sb_get(
                "/rest/v1/myprofile_links",
                params={
                    "select": "owner_user_id,created_at",
                    "viewer_user_id": f"eq.{uid}",
                    "order": "created_at.desc",
                    "limit": str(int(limit)),
                },
            )
            key = "owner_user_id"
        else:
            resp = await _sb_get(
                "/rest/v1/myprofile_links",
                params={
                    "select": "viewer_user_id,created_at",
                    "owner_user_id": f"eq.{uid}",
                    "order": "created_at.desc",
                    "limit": str(int(limit)),
                },
            )
            key = "viewer_user_id"

        if resp.status_code >= 300:
            logger.error("Supabase myprofile_links list failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to load follow list")

        link_rows = resp.json()
        ids_raw: list[str] = []
        if isinstance(link_rows, list):
            for r in link_rows:
                if isinstance(r, dict):
                    v = str(r.get(key) or "").strip()
                    if v:
                        ids_raw.append(v)

        # dedupe while preserving order
        ids: list[str] = []
        seen = set()
        for x in ids_raw:
            if x not in seen:
                ids.append(x)
                seen.add(x)

        if not ids:
            return MyProfileFollowListResponse(status="ok", target_user_id=uid, tab=t, rows=[])

        # 2) profiles bulk fetch (chunked to keep URLs reasonable)
        profiles_map: Dict[str, Dict[str, Any]] = {}
        chunk_size = 200
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i : i + chunk_size]
            in_expr = ",".join(chunk)

            resp2 = await _sb_get(
                "/rest/v1/profiles",
                params={
                    "select": "id,display_name,friend_code,myprofile_code",
                    "id": f"in.({in_expr})",
                    "limit": str(len(chunk)),
                },
            )
            if resp2.status_code >= 300:
                logger.error("Supabase profiles list failed: %s %s", resp2.status_code, resp2.text[:1500])
                raise HTTPException(status_code=502, detail="Failed to load profiles")

            rows2 = resp2.json()
            if isinstance(rows2, list):
                for p in rows2:
                    if isinstance(p, dict) and p.get("id") is not None:
                        profiles_map[str(p.get("id"))] = p

        # 3) order restore
        ordered: list[MyProfileFollowListItem] = []
        for pid in ids:
            p = profiles_map.get(pid)
            if not p:
                continue
            ordered.append(
                MyProfileFollowListItem(
                    id=str(p.get("id")),
                    display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    friend_code=(p.get("friend_code") if isinstance(p.get("friend_code"), str) else None),
                    myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                )
            )

        return MyProfileFollowListResponse(
            status="ok",
            target_user_id=uid,
            tab=t,
            rows=ordered,
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
            description="Requested report mode (standard|structural). Tier-gated.",
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
            mode_enum = normalize_myprofile_mode(report_mode, default=default_mode)

            # "light" is kept only for backward-compat input; disallow for MyProfile.
            if mode_enum == MyProfileMode.LIGHT:
                raise HTTPException(status_code=403, detail="report_mode 'light' is not available")

            if not is_myprofile_mode_allowed(tier, mode_enum):
                allowed = [m.value for m in allowed_myprofile_modes_for_tier(tier) if m != MyProfileMode.LIGHT]
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"report_mode '{mode_enum.value}' is not allowed for tier '{tier.value}'. "
                        f"Allowed: {', '.join(allowed)}"
                    ),
                )
            effective_report_mode = mode_enum.value
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Failed to resolve subscription tier/report_mode (deny): %s", exc)
            raise HTTPException(status_code=403, detail="MyProfile report is not available")

        # ---- Fetch patterns updated_at (B1) ----
        patterns_updated_at: Optional[str] = None
        try:
            resp = await _sb_get(
                f"/rest/v1/{ASTOR_STRUCTURE_PATTERNS_TABLE}",
                params={
                    "select": "updated_at",
                    "user_id": f"eq.{uid}",
                    "limit": "1",
                },
            )
            if resp.status_code < 300:
                rows = resp.json()
                if isinstance(rows, list) and rows:
                    patterns_updated_at = rows[0].get("updated_at")
        except Exception as exc:
            logger.warning("Failed to fetch structure patterns updated_at: %s", exc)

        # Spec v2: MyProfile（月次/最新）は raw logs（思考/行動）を主材料にするため、
        # patterns が無い場合は emotions の最新 created_at を更新指標として使う。
        if not patterns_updated_at:
            try:
                resp = await _sb_get(
                    "/rest/v1/emotions",
                    params={
                        "select": "created_at",
                        "user_id": f"eq.{uid}",
                        "order": "created_at.desc",
                        "limit": "1",
                    },
                )
                if resp.status_code < 300:
                    rows = resp.json()
                    if isinstance(rows, list) and rows:
                        patterns_updated_at = rows[0].get("created_at")
            except Exception:
                pass

        # ---- Fetch latest report row ----
        latest_row: Optional[Dict[str, Any]] = None
        latest_generated_at: Optional[str] = None
        try:
            resp = await _sb_get(
                "/rest/v1/myprofile_reports",
                params={
                    "select": "id,title,content_text,generated_at,content_json",
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

        def _parse_iso(iso: Optional[str]) -> Optional[datetime]:
            if not iso:
                return None
            try:
                s = str(iso).replace("Z", "+00:00")
                return datetime.fromisoformat(s)
            except Exception:
                return None

        patterns_dt = _parse_iso(patterns_updated_at)
        latest_dt = _parse_iso(latest_generated_at)

        stale = False
        reason = "up_to_date"

        if force:
            stale = True
            reason = "force"
        elif not latest_row or not str(latest_row.get("content_text") or "").strip():
            stale = True
            reason = "missing"
        elif patterns_dt and latest_dt:
            if patterns_dt > (latest_dt + timedelta(seconds=1)):
                stale = True
                reason = "stale_patterns"
        elif patterns_dt and not latest_dt:
            stale = True
            reason = "stale_patterns"
        elif not patterns_dt:
            reason = "no_patterns"

        if ensure and stale:
            # ---- Phase10: generation lock (avoid duplicate compute) ----
            lock_key = None
            lock_owner = None
            lock_acquired = True

            async def _refetch_latest_row() -> Optional[Dict[str, Any]]:
                try:
                    resp = await _sb_get(
                        "/rest/v1/myprofile_reports",
                        params={
                            "select": "id,title,content_text,generated_at,content_json",
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

            if build_lock_key is not None and try_acquire_lock is not None:
                try:
                    lock_key = build_lock_key(
                        namespace="myprofile",
                        user_id=uid,
                        report_type="latest",
                        period_start=LATEST_REPORT_PERIOD_START,
                        period_end=LATEST_REPORT_PERIOD_END,
                    )
                    lock_owner = (make_owner_id("myprofile_latest") if make_owner_id is not None else None)
                    lr = await try_acquire_lock(
                        lock_key=lock_key,
                        ttl_seconds=MYPROFILE_LATEST_LOCK_TTL_SECONDS,
                        owner_id=lock_owner,
                        context={
                            "namespace": "myprofile",
                            "user_id": uid,
                            "report_type": "latest",
                            "period": effective_period,
                            "report_mode": effective_report_mode,
                            "source": "on_demand_myprofile_latest",
                        },
                    )
                    lock_acquired = bool(getattr(lr, "acquired", False))
                    lock_owner = getattr(lr, "owner_id", lock_owner)
                except Exception:
                    lock_acquired = True

            if not lock_acquired:
                waited = None
                if poll_until is not None and MYPROFILE_LATEST_LOCK_WAIT_SECONDS > 0:
                    waited = await poll_until(
                        _refetch_latest_row,
                        timeout_seconds=MYPROFILE_LATEST_LOCK_WAIT_SECONDS,
                    )
                row = waited or latest_row
                return MyProfileLatestEnsureResponse(
                    refreshed=False,
                    reason="in_progress",
                    report_mode=effective_report_mode,
                    period=effective_period,
                    patterns_updated_at=patterns_updated_at,
                    latest_generated_at=(row.get("generated_at") if row else latest_generated_at),
                    generated_at=(row.get("generated_at") if row else latest_generated_at),
                    title=(row.get("title") if row else None),
                    content_text=(row.get("content_text") if row else None),
                )

            try:
                from astor_myprofile_report import build_myprofile_monthly_report

                now = datetime.now(timezone.utc).replace(microsecond=0)
                text, meta = build_myprofile_monthly_report(
                    user_id=uid,
                    period=effective_period,
                    report_mode=effective_report_mode,
                    include_secret=True,
                    now=now,
                    prev_report_text=None,
                )
                text = str(text or "").strip()
                if not text:
                    raise RuntimeError("report text is empty")

                generated_at = now.isoformat().replace("+00:00", "Z")

                payload = {
                    "user_id": uid,
                    "report_type": "latest",
                    "period_start": LATEST_REPORT_PERIOD_START,
                    "period_end": LATEST_REPORT_PERIOD_END,
                    "title": "自己構造レポート（最新版）",
                    "content_text": text,
                    "content_json": {
                        **(meta or {}),
                        "source": "on_demand_myprofile_latest",
                        "snapshot_period": effective_period,
                        "generated_at_server": generated_at,
                    },
                    "generated_at": generated_at,
                }

                if latest_row and latest_row.get("id") is not None:
                    rid = latest_row.get("id")
                    resp2 = await _sb_patch(
                        "/rest/v1/myprofile_reports",
                        params={"id": f"eq.{rid}"},
                        json=payload,
                        prefer="return=minimal",
                    )
                    if resp2.status_code not in (200, 204):
                        logger.error(
                            "Supabase update myprofile_reports(latest) failed: %s %s",
                            resp2.status_code,
                            resp2.text[:1500],
                        )
                        raise HTTPException(
                            status_code=502,
                            detail="Failed to save latest MyProfile report",
                        )
                else:
                    resp2 = await _sb_post(
                        "/rest/v1/myprofile_reports",
                        json=payload,
                        prefer="return=minimal",
                    )
                    if resp2.status_code not in (200, 201, 204):
                        logger.error(
                            "Supabase insert myprofile_reports(latest) failed: %s %s",
                            resp2.status_code,
                            resp2.text[:1500],
                        )
                        raise HTTPException(
                            status_code=502,
                            detail="Failed to save latest MyProfile report",
                        )

                return MyProfileLatestEnsureResponse(
                    refreshed=True,
                    reason=reason,
                    report_mode=effective_report_mode,
                    period=effective_period,
                    patterns_updated_at=patterns_updated_at,
                    latest_generated_at=latest_generated_at,
                    generated_at=generated_at,
                    title="自己構造レポート（最新版）",
                    content_text=text,
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Failed to build/save latest MyProfile report: %s", exc)
                raise HTTPException(
                    status_code=500, detail="Failed to generate latest MyProfile report"
                )
            finally:
                if lock_key and release_lock is not None:
                    await release_lock(lock_key=lock_key, owner_id=lock_owner)

        return MyProfileLatestEnsureResponse(
            refreshed=False,
            reason=reason,
            report_mode=effective_report_mode,
            period=effective_period,
            patterns_updated_at=patterns_updated_at,
            latest_generated_at=latest_generated_at,
            generated_at=latest_generated_at,
            title=(latest_row.get("title") if latest_row else None),
            content_text=(latest_row.get("content_text") if latest_row else None),
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
            mode_enum = normalize_myprofile_mode(body.report_mode, default=default_mode)

            if mode_enum == MyProfileMode.LIGHT:
                raise HTTPException(status_code=403, detail="report_mode 'light' is not available")

            if not is_myprofile_mode_allowed(tier, mode_enum):
                allowed = [m.value for m in allowed_myprofile_modes_for_tier(tier) if m != MyProfileMode.LIGHT]
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"report_mode '{mode_enum.value}' is not allowed for tier '{tier.value}'. "
                        f"Allowed: {', '.join(allowed)}"
                    ),
                )
            effective_report_mode = mode_enum.value
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

        title_range = f"{_format_jst_md(period_start_utc)} ～ {_format_jst_md(period_end_utc)}"
        title = f"自己構造レポート：{title_range}（{period_days}日分）"

        # ---- helper: fetch existing row for this period ----
        async def _fetch_report_for_period(ps: str, pe: str) -> Optional[Dict[str, Any]]:
            resp = await _sb_get(
                "/rest/v1/myprofile_reports",
                params={
                    "select": "id,title,content_text,content_json,generated_at,updated_at",
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

        existing_row = await _fetch_report_for_period(period_start_iso, period_end_iso)

        if existing_row and (not force):
            return MyProfileMonthlyEnsureResponse(
                refreshed=False,
                reason="up_to_date",
                report_mode=effective_report_mode,
                period=effective_period,
                period_start=period_start_iso,
                period_end=period_end_iso,
                generated_at=existing_row.get("generated_at") or existing_row.get("updated_at"),
                title=existing_row.get("title") or title,
                content_text=existing_row.get("content_text"),
                meta=existing_row.get("content_json"),
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
            if row:
                return MyProfileMonthlyEnsureResponse(
                    refreshed=False,
                    reason="in_progress",
                    report_mode=effective_report_mode,
                    period=effective_period,
                    period_start=period_start_iso,
                    period_end=period_end_iso,
                    generated_at=row.get("generated_at") or row.get("updated_at"),
                    title=row.get("title") or title,
                    content_text=row.get("content_text"),
                    meta=row.get("content_json"),
                )
            raise HTTPException(status_code=409, detail="Monthly report generation is in progress")

        # ---- previous distributed report (for diff summary) ----
        prev_report_text: Optional[str] = None
        try:
            prev_month_end_jst = dist_jst - timedelta(days=1)
            prev_dist_jst = datetime(prev_month_end_jst.year, prev_month_end_jst.month, 1, 0, 0, 0, 0, tzinfo=JST)
            prev_dist_utc = prev_dist_jst.astimezone(timezone.utc)

            prev_period_end_utc = prev_dist_utc - timedelta(milliseconds=1)
            prev_period_start_utc = prev_dist_utc - timedelta(days=max(period_days, 1))

            prev_ps = _to_iso_z(prev_period_start_utc)
            prev_pe = _to_iso_z(prev_period_end_utc)

            prev_row = await _fetch_report_for_period(prev_ps, prev_pe)
            if prev_row and prev_row.get("content_text"):
                prev_report_text = str(prev_row.get("content_text"))
        except Exception:
            prev_report_text = None

        # ---- generate + save (server-side) ----
        try:
            try:
                from astor_myprofile_report import build_myprofile_monthly_report

                # Use dist_utc as "now" so the range is anchored to month boundary (end exclusive)
                report_text, report_meta = build_myprofile_monthly_report(
                    user_id=uid,
                    period=effective_period,
                    report_mode=effective_report_mode,
                    include_secret=include_secret,
                    now=dist_utc,
                    prev_report_text=prev_report_text,
                )
            except Exception as exc:
                logger.error("Failed to build monthly MyProfile report: %s", exc)
                raise HTTPException(status_code=500, detail="Failed to generate monthly MyProfile report")

            report_text = str(report_text or "").strip()
            if not report_text:
                raise HTTPException(status_code=500, detail="Monthly MyProfile report text was empty")

            generated_at = _to_iso_z(dist_utc)

            content_json = {
                **(report_meta or {}),
                "source": "myprofile.monthly.ensure",
                "distribution_utc": _to_iso_z(dist_utc),
                "distribution_jst": dist_jst.isoformat(),
                "generated_at_server": _to_iso_z(datetime.now(timezone.utc)),
                "period_start": period_start_iso,
                "period_end": period_end_iso,
                "period_days": period_days,
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

            reason = "force" if force else ("missing" if not existing_row else "force")

            return MyProfileMonthlyEnsureResponse(
                refreshed=True,
                reason=reason,
                report_mode=effective_report_mode,
                period=effective_period,
                period_start=period_start_iso,
                period_end=period_end_iso,
                generated_at=generated_at,
                title=title,
                content_text=report_text,
                meta=content_json,
            )
        finally:
            if lock_key and release_lock is not None:
                await release_lock(lock_key=lock_key, owner_id=lock_owner)
