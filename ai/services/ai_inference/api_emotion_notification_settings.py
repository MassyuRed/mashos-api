# -*- coding: utf-8 -*-
"""Current EmotionNotification settings API entrypoint.

This module now owns the current-vocabulary EmotionNotification settings route
definitions. Legacy aggregate entrypoints may still delegate here during the
rename-safe / split-safe phase.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Path

from api_follow import (
    FriendNotificationSettingItem,
    FriendNotificationSettingResponse,
    FriendNotificationSettingsResponse,
    FriendNotificationSettingUpsertBody,
    _extract_bearer_token,
    _invalidate_friend_api_caches,
    _resolve_user_id_from_token,
    _sb_get,
    _sb_patch,
    _sb_post,
    logger,
)

EmotionNotificationSettingUpsertBody = FriendNotificationSettingUpsertBody
EmotionNotificationSettingItem = FriendNotificationSettingItem
EmotionNotificationSettingResponse = FriendNotificationSettingResponse
EmotionNotificationSettingsResponse = FriendNotificationSettingsResponse

# Current bridge view is backend read-only. Keep write/update/insert paths on
# public.friend_notification_settings and use this table only for SELECT-only reads.
EMOTION_NOTIFICATION_SETTINGS_READ_TABLE = (
    os.getenv("COCOLON_EMOTION_NOTIFICATION_SETTINGS_READ_TABLE")
    or os.getenv("COCOLON_FRIEND_NOTIFICATION_SETTINGS_READ_TABLE")
    or "emotion_notification_settings"
).strip() or "emotion_notification_settings"


def register_emotion_notification_settings_routes(app: FastAPI) -> None:
    """Register current EmotionNotification settings routes on the given FastAPI app."""

    @app.get("/emotion-notifications/settings", response_model=FriendNotificationSettingsResponse)
    async def list_emotion_notification_settings(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendNotificationSettingsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            f"/rest/v1/{EMOTION_NOTIFICATION_SETTINGS_READ_TABLE}",
            params={
                "select": "owner_user_id,is_enabled",
                "viewer_user_id": f"eq.{me}",
                "order": "owner_user_id.asc",
            },
        )

        if resp.status_code == 404:
            raise HTTPException(status_code=501, detail=f"{EMOTION_NOTIFICATION_SETTINGS_READ_TABLE} table is not configured")

        if resp.status_code >= 300:
            logger.error(
                "Supabase select %s failed: %s %s",
                EMOTION_NOTIFICATION_SETTINGS_READ_TABLE,
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
                            owner_user_id=fid,
                            friend_user_id=fid,
                            is_enabled=(True if enabled is None else bool(enabled)),
                        )
                    )

        return FriendNotificationSettingsResponse(status="ok", settings=settings)

    @app.post("/emotion-notifications/settings/{friend_user_id}", response_model=FriendNotificationSettingResponse)
    async def set_emotion_notification_setting(
        body: FriendNotificationSettingUpsertBody,
        friend_user_id: str = Path(..., min_length=1, max_length=128),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendNotificationSettingResponse:
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

        await _invalidate_friend_api_caches(me)
        return FriendNotificationSettingResponse(
            status="ok",
            owner_user_id=owner_user_id,
            friend_user_id=owner_user_id,
            is_enabled=is_enabled,
        )


__all__ = [
    "EmotionNotificationSettingUpsertBody",
    "EmotionNotificationSettingItem",
    "EmotionNotificationSettingResponse",
    "EmotionNotificationSettingsResponse",
    "register_emotion_notification_settings_routes",
]
