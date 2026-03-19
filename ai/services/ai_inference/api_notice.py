# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from active_users_store import touch_active_user
from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from client_compat import extract_client_meta
from notice_store import NoticeStore

logger = logging.getLogger("notice_api")
store = NoticeStore()


class NoticeItem(BaseModel):
    notice_id: str
    notice_key: Optional[str] = None
    version: int = 1
    title: str
    body: str
    body_format: str = "plain_text"
    category: str = "other"
    priority: str = "normal"
    published_at: Optional[str] = None
    is_read: bool = False
    read_at: Optional[str] = None
    popup_seen_at: Optional[str] = None
    cta: Dict[str, Any] = Field(default_factory=dict)


class NoticeCurrentResponse(BaseModel):
    feature_enabled: bool = True
    unread_count: int = 0
    has_unread: bool = False
    badge: Dict[str, Any] = Field(default_factory=dict)
    popup_notice: Optional[NoticeItem] = None


class NoticeHistoryResponse(BaseModel):
    feature_enabled: bool = True
    items: List[NoticeItem] = Field(default_factory=list)
    limit: int = 30
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    unread_count: int = 0


class NoticeReadRequest(BaseModel):
    notice_ids: List[str] = Field(default_factory=list)


class NoticeReadResponse(BaseModel):
    status: str = "ok"
    updated_count: int = 0
    unread_count: int = 0


class NoticePopupSeenRequest(BaseModel):
    notice_id: str


class NoticePopupSeenResponse(BaseModel):
    status: str = "ok"
    popup_seen: bool = True


async def _require_user_id(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    uid = await _resolve_user_id_from_token(token)
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        await touch_active_user(uid)
    except Exception:
        logger.exception("notice: touch_active_user failed")
    return uid


def register_notice_routes(app: FastAPI) -> None:
    @app.get("/notices/current", response_model=NoticeCurrentResponse)
    async def notices_current(
        request: Request,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NoticeCurrentResponse:
        uid = await _require_user_id(authorization)
        bundle = await store.fetch_current_notice_bundle(uid, extract_client_meta(request.headers))
        return NoticeCurrentResponse(**bundle)

    @app.get("/notices/history", response_model=NoticeHistoryResponse)
    async def notices_history(
        request: Request,
        limit: int = Query(default=30, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NoticeHistoryResponse:
        uid = await _require_user_id(authorization)
        bundle = await store.list_notice_history(
            uid,
            extract_client_meta(request.headers),
            limit=limit,
            offset=offset,
        )
        return NoticeHistoryResponse(**bundle)

    @app.post("/notices/read", response_model=NoticeReadResponse)
    async def notices_read(
        request: Request,
        body: NoticeReadRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NoticeReadResponse:
        uid = await _require_user_id(authorization)
        updated_count = await store.mark_notices_read(uid, body.notice_ids)
        current = await store.fetch_current_notice_bundle(uid, extract_client_meta(request.headers))
        return NoticeReadResponse(
            updated_count=updated_count,
            unread_count=int(current.get("unread_count") or 0),
        )

    @app.post("/notices/popup-seen", response_model=NoticePopupSeenResponse)
    async def notices_popup_seen(
        body: NoticePopupSeenRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NoticePopupSeenResponse:
        uid = await _require_user_id(authorization)
        popup_seen = await store.mark_notice_popup_seen(uid, body.notice_id)
        return NoticePopupSeenResponse(popup_seen=bool(popup_seen))
