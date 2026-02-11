# -*- coding: utf-8 -*-
"""Friends API for Cocolon (MashOS / FastAPI)

Implements the minimum endpoints required for the MVP:

- POST /friends/request
    Body: {"friend_code": "XXXXXXXXXX"}
    Creates a pending friend request.

- POST /friends/requests/{id}/accept
    The receiver accepts a pending request. Creates friendships (both directions).

- POST /friends/requests/{id}/reject
    The receiver rejects a pending request.

Notes
-----
* The caller must pass Supabase Auth access token via:
    Authorization: Bearer <access_token>
  We resolve the user_id by calling Supabase Auth `/auth/v1/user`.
* DB writes are performed via Supabase PostgREST using the service role key.
* We do NOT expose secret memo content anywhere.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Path
from pydantic import BaseModel, Field

# Reuse auth helpers & config checks from emotion submit module
from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
    _fetch_profile_display_name,
    _fetch_push_tokens_for_users,
    _send_fcm_push,
)

logger = logging.getLogger("friends_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


# ----------------------------
# Pydantic models
# ----------------------------


class FriendRequestCreateBody(BaseModel):
    friend_code: str = Field(..., min_length=4, max_length=64, description="Target user's friend_code")


class FriendRequestCreateResponse(BaseModel):
    status: str = Field(..., description="ok | already_friends | already_pending")
    request_id: Optional[int] = None
    requested_user_id: Optional[str] = None
    requested_display_name: Optional[str] = None


class FriendRequestActionResponse(BaseModel):
    status: str = Field(..., description="ok")
    request_id: int


class FriendRemoveBody(BaseModel):
    friend_user_id: str = Field(..., min_length=1, max_length=128, description="Target user's user id")


class FriendRemoveResponse(BaseModel):
    status: str = Field(..., description="ok")
    friend_user_id: str




class FriendNotificationSettingUpsertBody(BaseModel):
    is_enabled: bool = Field(..., description="true: receive notifications from this friend, false: mute")


class FriendNotificationSettingItem(BaseModel):
    friend_user_id: str = Field(..., description="Friend (owner) user id")
    is_enabled: bool = Field(..., description="Whether notifications are enabled for this friend")


class FriendNotificationSettingResponse(BaseModel):
    status: str = Field(..., description="ok")
    friend_user_id: str
    is_enabled: bool


class FriendNotificationSettingsResponse(BaseModel):
    status: str = Field(..., description="ok")
    settings: List[FriendNotificationSettingItem]

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

async def _sb_delete(path: str, *, params: Dict[str, str], prefer: Optional[str] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.delete(url, headers=_sb_headers_json(prefer=prefer), params=params)



async def _lookup_profile_by_friend_code(friend_code: str) -> Optional[Dict[str, Any]]:
    """Return {id, display_name} or None"""
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,friend_code",
            "friend_code": f"eq.{friend_code}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase profiles lookup failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to look up friend code")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _are_already_friends(user_id: str, friend_user_id: str) -> bool:
    resp = await _sb_get(
        "/rest/v1/friendships",
        params={
            "select": "user_id",
            "user_id": f"eq.{user_id}",
            "friend_user_id": f"eq.{friend_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friendships select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to check friendship")
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def _find_existing_pending_request(user_a: str, user_b: str) -> Optional[Dict[str, Any]]:
    """Return a pending request for the pair in either direction."""
    # PostgREST OR syntax
    or_expr = (
        f"and(requester_user_id.eq.{user_a},requested_user_id.eq.{user_b}),"
        f"and(requester_user_id.eq.{user_b},requested_user_id.eq.{user_a})"
    )
    resp = await _sb_get(
        "/rest/v1/friend_requests",
        params={
            "select": "id,requester_user_id,requested_user_id,status,created_at",
            "status": "eq.pending",
            "or": f"({or_expr})",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friend_requests select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friend requests")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _get_friend_request_by_id(req_id: int) -> Dict[str, Any]:
    resp = await _sb_get(
        "/rest/v1/friend_requests",
        params={
            "select": "id,requester_user_id,requested_user_id,status,created_at,responded_at",
            "id": f"eq.{req_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friend_requests get failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friend request")
    rows = resp.json()
    if not (isinstance(rows, list) and rows):
        raise HTTPException(status_code=404, detail="Friend request not found")
    return rows[0]


async def _insert_friendships_bidirectional(user_a: str, user_b: str) -> None:
    payload = [
        {"user_id": user_a, "friend_user_id": user_b},
        {"user_id": user_b, "friend_user_id": user_a},
    ]
    resp = await _sb_post(
        "/rest/v1/friendships",
        json=payload,
        prefer="return=minimal",
    )

    # 201/204 ok. 409 can happen if already exists; treat as ok.
    if resp.status_code in (200, 201, 204):
        return
    if resp.status_code == 409:
        logger.info("friendships already exist for %s<->%s", user_a, user_b)
        return
    logger.error("Supabase insert friendships failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to create friendship")


async def _delete_friendships_bidirectional(user_a: str, user_b: str) -> None:
    """Delete friendships rows in both directions (idempotent)."""
    for u, f in ((user_a, user_b), (user_b, user_a)):
        resp = await _sb_delete(
            "/rest/v1/friendships",
            params={
                "user_id": f"eq.{u}",
                "friend_user_id": f"eq.{f}",
            },
            prefer="return=minimal",
        )
        # 204 No Content even when nothing deleted; treat as ok
        if resp.status_code in (200, 204):
            continue
        # Some PostgREST setups may return 404; treat as idempotent ok
        if resp.status_code == 404:
            continue
        logger.error("Supabase delete friendships failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to remove friendship")


# ----------------------------
# Route registration
# ----------------------------


def register_friend_routes(app: FastAPI) -> None:
    """Register friend request endpoints on the given FastAPI app."""

    @app.post("/friends/request", response_model=FriendRequestCreateResponse)
    async def create_friend_request(
        body: FriendRequestCreateBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestCreateResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        requester_user_id = await _resolve_user_id_from_token(access_token)
        friend_code = body.friend_code.strip()
        if not friend_code:
            raise HTTPException(status_code=400, detail="friend_code is required")

        target_profile = await _lookup_profile_by_friend_code(friend_code)
        if not target_profile:
            raise HTTPException(status_code=404, detail="User not found for the given friend_code")

        requested_user_id = str(target_profile.get("id") or "")
        requested_display_name = target_profile.get("display_name") or None

        if not requested_user_id:
            raise HTTPException(status_code=404, detail="User not found for the given friend_code")

        if requested_user_id == requester_user_id:
            raise HTTPException(status_code=400, detail="You cannot send a friend request to yourself")

        # If already friends -> idempotent ok
        if await _are_already_friends(requester_user_id, requested_user_id):
            return FriendRequestCreateResponse(
                status="already_friends",
                request_id=None,
                requested_user_id=requested_user_id,
                requested_display_name=requested_display_name,
            )

        # If pending already exists (either direction) -> return that
        existing = await _find_existing_pending_request(requester_user_id, requested_user_id)
        if existing:
            return FriendRequestCreateResponse(
                status="already_pending",
                request_id=int(existing.get("id")),
                requested_user_id=requested_user_id,
                requested_display_name=requested_display_name,
            )

        # Create request
        payload = {
            "requester_user_id": requester_user_id,
            "requested_user_id": requested_user_id,
            "status": "pending",
        }
        resp = await _sb_post(
            "/rest/v1/friend_requests",
            json=payload,
            prefer="return=representation",
        )
        if resp.status_code not in (200, 201):
            # Unique pending pair index may fire -> try to return existing pending
            if resp.status_code == 409:
                existing2 = await _find_existing_pending_request(requester_user_id, requested_user_id)
                if existing2:
                    return FriendRequestCreateResponse(
                        status="already_pending",
                        request_id=int(existing2.get("id")),
                        requested_user_id=requested_user_id,
                        requested_display_name=requested_display_name,
                    )
            logger.error("Supabase insert friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to create friend request")

        data = resp.json()
        row = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
        request_id = int(row.get("id")) if row.get("id") is not None else None

        # Push通知（best-effort）：申請先ユーザーへ通知
        try:
            token_map = await _fetch_push_tokens_for_users([requested_user_id])
            tokens = list(token_map.values())
            if tokens:
                requester_name = await _fetch_profile_display_name(requester_user_id)
                requester_label = (requester_name or "").strip() or "フレンド"
                if requester_label == "Friend":
                    requester_label = "フレンド"

                body_text = f"{requester_label}さんからフレンド通知が届きました"
                data_payload: Dict[str, str] = {"type": "friend_request"}
                if request_id is not None:
                    data_payload["request_id"] = str(request_id)

                await _send_fcm_push(tokens=tokens, title="Cocolon", body=body_text, data=data_payload)
        except Exception as exc:
            logger.warning("Failed to send friend request push: %s", exc)

        return FriendRequestCreateResponse(
            status="ok",
            request_id=request_id,
            requested_user_id=requested_user_id,
            requested_display_name=requested_display_name,
        )

    @app.post("/friends/requests/{request_id}/accept", response_model=FriendRequestActionResponse)
    async def accept_friend_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_friend_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        requested_user_id = str(req.get("requested_user_id"))
        requester_user_id = str(req.get("requester_user_id"))
        if requested_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to accept this request")

        now = datetime.now(timezone.utc).isoformat()
        # Update request status
        resp = await _sb_patch(
            "/rest/v1/friend_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "accepted", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase update friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to accept friend request")

        # Create friendships (both directions)
        await _insert_friendships_bidirectional(requester_user_id, requested_user_id)
        return FriendRequestActionResponse(status="ok", request_id=request_id)

    @app.post("/friends/requests/{request_id}/reject", response_model=FriendRequestActionResponse)
    async def reject_friend_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_friend_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        requested_user_id = str(req.get("requested_user_id"))
        if requested_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to reject this request")

        now = datetime.now(timezone.utc).isoformat()
        resp = await _sb_patch(
            "/rest/v1/friend_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "rejected", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase update friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to reject friend request")

        return FriendRequestActionResponse(status="ok", request_id=request_id)



    @app.post("/friends/requests/{request_id}/cancel", response_model=FriendRequestActionResponse)
    async def cancel_friend_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestActionResponse:
        """Requester cancels (withdraws) a pending friend request.

        Behavior:
        - Only requester_user_id can cancel.
        - Only pending requests can be canceled.
        - Implementation deletes the pending row (robust against status enum/constraints).
        """
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_friend_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        requester_user_id = str(req.get("requester_user_id"))
        if requester_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to cancel this request")

        # Delete request row (idempotent best-effort)
        resp = await _sb_delete(
            "/rest/v1/friend_requests",
            params={"id": f"eq.{request_id}"},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            if resp.status_code == 404:
                return FriendRequestActionResponse(status="ok", request_id=request_id)
            logger.error("Supabase delete friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to cancel friend request")

        return FriendRequestActionResponse(status="ok", request_id=request_id)

    @app.post("/friends/remove", response_model=FriendRemoveResponse)
    async def remove_friend(
        body: FriendRemoveBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRemoveResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        friend_user_id = (body.friend_user_id or "").strip()
        if not friend_user_id:
            raise HTTPException(status_code=400, detail="friend_user_id is required")
        if friend_user_id == me:
            raise HTTPException(status_code=400, detail="You cannot remove yourself from friends")

        await _delete_friendships_bidirectional(me, friend_user_id)
        return FriendRemoveResponse(status="ok", friend_user_id=friend_user_id)


    @app.get("/friends/notification-settings", response_model=FriendNotificationSettingsResponse)
    async def list_friend_notification_settings(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendNotificationSettingsResponse:
        """List per-friend notification settings for the caller (viewer).

        Note:
        - Missing rows should be treated as enabled (true) by the client.
        - This endpoint returns only explicitly saved settings rows.
        """
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            "/rest/v1/friend_notification_settings",
            params={
                "select": "owner_user_id,is_enabled",
                "viewer_user_id": f"eq.{me}",
                "order": "owner_user_id.asc",
            },
        )

        # If the table isn't provisioned yet, tell the client explicitly.
        if resp.status_code == 404:
            raise HTTPException(status_code=501, detail="friend_notification_settings table is not configured")

        if resp.status_code >= 300:
            logger.error(
                "Supabase select friend_notification_settings failed: %s %s",
                resp.status_code,
                resp.text[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to query notification settings")

        rows = resp.json()
        settings: List[FriendNotificationSettingItem] = []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                fid = r.get("owner_user_id")
                enabled = r.get("is_enabled")
                if isinstance(fid, str) and fid:
                    settings.append(
                        FriendNotificationSettingItem(
                            friend_user_id=fid,
                            is_enabled=(True if enabled is None else bool(enabled)),
                        )
                    )

        return FriendNotificationSettingsResponse(status="ok", settings=settings)

    @app.post("/friends/notification-settings/{friend_user_id}", response_model=FriendNotificationSettingResponse)
    async def set_friend_notification_setting(
        body: FriendNotificationSettingUpsertBody,
        friend_user_id: str = Path(..., min_length=1, max_length=128),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendNotificationSettingResponse:
        """Upsert per-friend notification setting (viewer -> owner)."""
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        owner_user_id = (friend_user_id or "").strip()
        if not owner_user_id:
            raise HTTPException(status_code=400, detail="friend_user_id is required")
        if owner_user_id == me:
            raise HTTPException(status_code=400, detail="You cannot set notification setting for yourself")

        is_enabled = bool(body.is_enabled)
        now = datetime.now(timezone.utc).isoformat()

        # 1) Check existing row
        resp_get = await _sb_get(
            "/rest/v1/friend_notification_settings",
            params={
                "select": "viewer_user_id,owner_user_id,is_enabled",
                "viewer_user_id": f"eq.{me}",
                "owner_user_id": f"eq.{owner_user_id}",
                "limit": "1",
            },
        )

        if resp_get.status_code == 404:
            raise HTTPException(status_code=501, detail="friend_notification_settings table is not configured")
        if resp_get.status_code >= 300:
            logger.error(
                "Supabase get friend_notification_settings failed: %s %s",
                resp_get.status_code,
                resp_get.text[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to query notification settings")

        rows = resp_get.json()
        exists = bool(isinstance(rows, list) and rows)

        if exists:
            resp_upd = await _sb_patch(
                "/rest/v1/friend_notification_settings",
                params={
                    "viewer_user_id": f"eq.{me}",
                    "owner_user_id": f"eq.{owner_user_id}",
                },
                json={"is_enabled": is_enabled, "updated_at": now},
                prefer="return=minimal",
            )
            if resp_upd.status_code not in (200, 204):
                logger.error(
                    "Supabase update friend_notification_settings failed: %s %s",
                    resp_upd.status_code,
                    resp_upd.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to update notification setting")
        else:
            resp_ins = await _sb_post(
                "/rest/v1/friend_notification_settings",
                json={
                    "viewer_user_id": me,
                    "owner_user_id": owner_user_id,
                    "is_enabled": is_enabled,
                    "updated_at": now,
                },
                prefer="return=minimal",
            )
            if resp_ins.status_code not in (200, 201, 204):
                logger.error(
                    "Supabase insert friend_notification_settings failed: %s %s",
                    resp_ins.status_code,
                    resp_ins.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to save notification setting")

        return FriendNotificationSettingResponse(
            status="ok",
            friend_user_id=owner_user_id,
            is_enabled=is_enabled,
        )

