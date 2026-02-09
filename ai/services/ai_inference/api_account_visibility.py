# -*- coding: utf-8 -*-
"""api_account_visibility.py

Account Visibility / Privacy Settings API (Cocolon / MashOS / FastAPI)
--------------------------------------------------------------------

Endpoints
- GET   /account/visibility/me
- PATCH /account/visibility/me
- GET   /account/profile?target_user_id=<uuid>

Notes
- Requires Authorization: Bearer <supabase_access_token>
- Uses Supabase PostgREST (service role) to read/write:
  - account_visibility_settings
  - profiles

Friend code visibility
- friend_code itself is a friend request flow requiring approval (handled elsewhere).
- This setting controls whether friend_code is *shown* to other users on the account page.
- Self can always view their own friend_code.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)

logger = logging.getLogger("account_visibility_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


# ----------------------------
# Models
# ----------------------------


class AccountVisibilityResponse(BaseModel):
    user_id: str
    is_friend_code_public: bool = True
    is_recommendation_enabled: bool = True
    is_ranking_visible: bool = True
    is_private_account: bool = False
    updated_at: Optional[str] = None


class AccountVisibilityUpdateBody(BaseModel):
    is_friend_code_public: Optional[bool] = None
    is_recommendation_enabled: Optional[bool] = None
    is_ranking_visible: Optional[bool] = None
    is_private_account: Optional[bool] = None


class FriendCodeVisibilityInfo(BaseModel):
    can_view: bool
    reason: str


class AccountProfileResponse(BaseModel):
    target_user_id: str
    display_name: Optional[str] = None
    myprofile_code: Optional[str] = None
    friend_code: Optional[str] = None
    friend_code_visibility: FriendCodeVisibilityInfo


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


async def _sb_patch(
    path: str, *, params: Dict[str, str], json: Any, prefer: Optional[str] = None
) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.patch(url, headers=_sb_headers_json(prefer=prefer), params=params, json=json)


# ----------------------------
# Internal helpers
# ----------------------------


async def _require_user_id(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return str(await _resolve_user_id_from_token(token))


def _pick_row(resp: httpx.Response) -> Dict[str, Any]:
    try:
        data = resp.json()
    except Exception:
        return {}
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    if isinstance(data, dict):
        return data
    return {}


async def _get_or_create_settings(user_id: str) -> Dict[str, Any]:
    resp = await _sb_get(
        "/rest/v1/account_visibility_settings",
        params={
            "select": "user_id,is_friend_code_public,is_recommendation_enabled,is_ranking_visible,is_private_account,updated_at",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase fetch account_visibility_settings failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to load visibility settings")

    row = _pick_row(resp)
    if row:
        return row

    # Should not happen if DB triggers/backfill are in place, but keep it safe.
    ins = await _sb_post(
        "/rest/v1/account_visibility_settings",
        json={"user_id": user_id},
        prefer="return=representation",
    )
    if ins.status_code not in (200, 201):
        logger.error(
            "Supabase insert account_visibility_settings failed: %s %s",
            ins.status_code,
            ins.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to initialize visibility settings")

    return _pick_row(ins)


async def _get_profile_row(user_id: str) -> Optional[Dict[str, Any]]:
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,myprofile_code,friend_code",
            "id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase profiles fetch failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to load profile")

    row = _pick_row(resp)
    return row if row else None


# ----------------------------
# Route registration
# ----------------------------


def register_account_visibility_routes(app: FastAPI) -> None:
    """Register /account/visibility/* and /account/profile endpoints."""

    @app.get("/account/visibility/me", response_model=AccountVisibilityResponse)
    async def get_my_visibility(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountVisibilityResponse:
        me = await _require_user_id(authorization)
        row = await _get_or_create_settings(me)

        return AccountVisibilityResponse(
            user_id=str(row.get("user_id") or me),
            is_friend_code_public=bool(
                row.get("is_friend_code_public") if row.get("is_friend_code_public") is not None else True
            ),
            is_recommendation_enabled=bool(
                row.get("is_recommendation_enabled") if row.get("is_recommendation_enabled") is not None else True
            ),
            is_ranking_visible=bool(
                row.get("is_ranking_visible") if row.get("is_ranking_visible") is not None else True
            ),
            is_private_account=bool(
                row.get("is_private_account") if row.get("is_private_account") is not None else False
            ),
            updated_at=(str(row.get("updated_at")) if row.get("updated_at") is not None else None),
        )

    @app.patch("/account/visibility/me", response_model=AccountVisibilityResponse)
    async def patch_my_visibility(
        body: AccountVisibilityUpdateBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        me = await _require_user_id(authorization)

        payload: Dict[str, Any] = {}
        if body.is_friend_code_public is not None:
            payload["is_friend_code_public"] = bool(body.is_friend_code_public)
        if body.is_recommendation_enabled is not None:
            payload["is_recommendation_enabled"] = bool(body.is_recommendation_enabled)
        if body.is_ranking_visible is not None:
            payload["is_ranking_visible"] = bool(body.is_ranking_visible)
        if body.is_private_account is not None:
            payload["is_private_account"] = bool(body.is_private_account)

        if not payload:
            return JSONResponse(
                status_code=400,
                content={"detail": "更新項目がありません", "code": "no_fields"},
            )

        resp = await _sb_patch(
            "/rest/v1/account_visibility_settings",
            params={"user_id": f"eq.{me}"},
            json=payload,
            prefer="return=representation",
        )
        if resp.status_code >= 300:
            logger.error(
                "Supabase update account_visibility_settings failed: %s %s",
                resp.status_code,
                resp.text[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to update visibility settings")

        row = _pick_row(resp)
        if not row:
            # Defensive: read again / create
            row = await _get_or_create_settings(me)

        return AccountVisibilityResponse(
            user_id=str(row.get("user_id") or me),
            is_friend_code_public=bool(
                row.get("is_friend_code_public") if row.get("is_friend_code_public") is not None else True
            ),
            is_recommendation_enabled=bool(
                row.get("is_recommendation_enabled") if row.get("is_recommendation_enabled") is not None else True
            ),
            is_ranking_visible=bool(
                row.get("is_ranking_visible") if row.get("is_ranking_visible") is not None else True
            ),
            is_private_account=bool(
                row.get("is_private_account") if row.get("is_private_account") is not None else False
            ),
            updated_at=(str(row.get("updated_at")) if row.get("updated_at") is not None else None),
        )

    @app.get("/account/profile", response_model=AccountProfileResponse)
    async def get_account_profile(
        target_user_id: str = Query(..., description="Target user UUID"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountProfileResponse:
        viewer = await _require_user_id(authorization)

        tgt = str(target_user_id or "").strip()
        if not tgt:
            return JSONResponse(
                status_code=400,
                content={"detail": "target_user_id が不正です", "code": "invalid_target_user_id"},
            )

        prof = await _get_profile_row(tgt)
        if not prof:
            raise HTTPException(status_code=404, detail="User not found")

        # Determine friend_code visibility
        if str(viewer) == str(tgt):
            can_view = True
            reason = "self"
        else:
            srow = await _get_or_create_settings(tgt)
            is_public = bool(
                srow.get("is_friend_code_public") if srow.get("is_friend_code_public") is not None else True
            )
            can_view = bool(is_public)
            reason = "public" if can_view else "hidden_by_user_setting"

        friend_code: Optional[str] = None
        raw_fc = prof.get("friend_code")
        if can_view and isinstance(raw_fc, str) and raw_fc.strip():
            friend_code = raw_fc.strip()

        return AccountProfileResponse(
            target_user_id=str(tgt),
            display_name=(prof.get("display_name") if isinstance(prof.get("display_name"), str) else None),
            myprofile_code=(prof.get("myprofile_code") if isinstance(prof.get("myprofile_code"), str) else None),
            friend_code=friend_code,
            friend_code_visibility=FriendCodeVisibilityInfo(can_view=can_view, reason=reason),
        )
