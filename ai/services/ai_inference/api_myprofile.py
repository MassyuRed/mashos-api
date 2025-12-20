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
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Path
from pydantic import BaseModel, Field

# Reuse auth helpers & config checks from emotion submit module
from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)

logger = logging.getLogger("myprofile_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


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
