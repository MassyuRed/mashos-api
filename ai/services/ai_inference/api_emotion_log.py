# -*- coding: utf-8 -*-
"""Current EmotionLog API entrypoint.

This module now owns the current-vocabulary EmotionLog feed / unread route
definitions. Legacy aggregate entrypoints may still delegate here during the
rename-safe / split-safe phase.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException

from api_follow import (
    FriendUnreadMarkReadBody,
    FriendUnreadMarkReadResponse,
    FriendUnreadStatusResponse,
    _build_friend_feed_response_items,
    _emotion_log_feed_head_created_at_for_viewer,
    _extract_bearer_token,
    _fetch_last_read_at,
    _fetch_live_emotion_log_feed_rows,
    _has_newer_iso,
    _invalidate_friend_api_caches,
    _parse_iso_utc,
    _resolve_user_id_from_token,
    _upsert_last_read_at,
    fetch_latest_ready_emotion_log_feed_summary,
    get_friend_unread_status_payload_for_user,
    logger,
    select_emotion_log_feed_items,
)

EmotionLogUnreadStatusResponse = FriendUnreadStatusResponse
EmotionLogFeedMarkReadBody = FriendUnreadMarkReadBody
EmotionLogFeedMarkReadResponse = FriendUnreadMarkReadResponse
get_emotion_log_unread_status_payload_for_user = get_friend_unread_status_payload_for_user


def register_emotion_log_routes(app: FastAPI) -> None:
    """Register current EmotionLog feed / unread routes on the given FastAPI app."""

    @app.get("/emotion-log/feed")
    async def get_emotion_log_feed(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        summary = None
        try:
            summary = await fetch_latest_ready_emotion_log_feed_summary(me)
        except Exception as exc:
            logger.warning("Failed to fetch ready emotion log feed summary: %s", exc)
            summary = None

        if summary:
            items = _build_friend_feed_response_items(select_emotion_log_feed_items(summary))
            return {"status": "ok", "items": items}

        try:
            live_rows = await _fetch_live_emotion_log_feed_rows(me, limit=20)
            return {"status": "ok", "items": _build_friend_feed_response_items(live_rows)}
        except HTTPException:
            raise

    @app.get("/emotion-log/unread-status", response_model=FriendUnreadStatusResponse)
    async def get_friend_unread_status(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendUnreadStatusResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        payload = await get_friend_unread_status_payload_for_user(me)
        return FriendUnreadStatusResponse(**payload)

    @app.post("/emotion-log/unread/read-feed", response_model=FriendUnreadMarkReadResponse)
    async def post_emotion_log_feed_mark_read(
        body: Optional[FriendUnreadMarkReadBody] = None,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendUnreadMarkReadResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        requested_last_read_at = str((body.last_seen_created_at if body else "") or "").strip() or None
        if requested_last_read_at and _parse_iso_utc(requested_last_read_at) is None:
            requested_last_read_at = None

        current_last_read_at_task = _fetch_last_read_at("friend_feed_reads", me)
        latest_feed_created_at_task = (
            _emotion_log_feed_head_created_at_for_viewer(me)
            if not requested_last_read_at
            else asyncio.sleep(0, result=None)
        )
        current_last_read_at, latest_feed_created_at = await asyncio.gather(
            current_last_read_at_task,
            latest_feed_created_at_task,
        )

        candidate_last_read_at = (
            requested_last_read_at
            or latest_feed_created_at
            or datetime.now(timezone.utc).isoformat()
        )
        last_read_at = (
            current_last_read_at
            if _has_newer_iso(current_last_read_at, candidate_last_read_at)
            else candidate_last_read_at
        )

        ok = await _upsert_last_read_at("friend_feed_reads", me, last_read_at)
        if not ok:
            raise HTTPException(status_code=502, detail="Failed to mark friend feed as read")

        await _invalidate_friend_api_caches(me)
        return FriendUnreadMarkReadResponse(last_read_at=last_read_at)


__all__ = [
    "EmotionLogUnreadStatusResponse",
    "EmotionLogFeedMarkReadBody",
    "EmotionLogFeedMarkReadResponse",
    "get_emotion_log_unread_status_payload_for_user",
    "register_emotion_log_routes",
]
