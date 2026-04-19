# -*- coding: utf-8 -*-
"""api_emotion_reflection.py

New Reflection flow driven by the current emotion input only.

Endpoints
---------
- POST /emotion/reflection/preview
- POST /emotion/reflection/publish
- POST /emotion/reflection/cancel
- GET  /emotion/reflection/quota
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except Exception:  # pragma: no cover
    ConfigDict = None  # type: ignore

from api_emotion_submit import EmotionItem
from client_compat import extract_client_meta
from emotion_reflection_generation_service import generate_emotion_reflection_preview
from emotion_reflection_store import (
    cancel_preview_draft,
    create_preview_draft,
    fetch_preview_draft,
    publish_preview_draft,
)
from home_gateway.command_gateway import execute_home_command
from home_gateway.emotion_reflection_publish_service import (
    build_emotion_reflection_quota_status,
)
from home_gateway.emotion_submit_service import (
    normalize_submission_payload,
    persist_emotion_submission,
    resolve_authenticated_user_id,
)


_build_quota_status = build_emotion_reflection_quota_status


class EmotionReflectionPreviewRequest(BaseModel):
    user_id: Optional[str] = Field(default=None)
    emotions: List[Union[EmotionItem, str]] = Field(...)
    memo: Optional[str] = Field(default=None)
    memo_action: Optional[str] = Field(default=None, alias="memoAction")
    category: Optional[List[str]] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    notify_friends: Optional[bool] = Field(default=True, alias="send_friend_notification")

    if ConfigDict is not None:  # pragma: no cover
        model_config = ConfigDict(populate_by_name=True)
    else:  # pragma: no cover
        class Config:
            allow_population_by_field_name = True


class EmotionReflectionPublishRequest(BaseModel):
    preview_id: str = Field(..., min_length=1)


class EmotionReflectionCancelRequest(BaseModel):
    preview_id: str = Field(..., min_length=1)


class EmotionReflectionQuotaResponse(BaseModel):
    status: str = Field(default="ok")
    subscription_tier: str
    month_key: str
    publish_limit: Optional[int] = None
    published_count: int
    remaining_count: Optional[int] = None
    can_publish: bool


class EmotionReflectionPreviewResponse(BaseModel):
    status: str = Field(default="ok")
    preview_id: str
    question: str
    reflection_text: str
    answer_display_state: str
    quota: EmotionReflectionQuotaResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


class EmotionReflectionPublishResponse(BaseModel):
    status: str = Field(default="ok")
    preview_id: str
    reflection_id: str
    emotion_id: Optional[Any] = None
    created_at: str
    question: str
    reflection_text: str
    quota: EmotionReflectionQuotaResponse
    input_feedback: Optional[Dict[str, Any]] = None


class EmotionReflectionCancelResponse(BaseModel):
    status: str = Field(default="ok")
    preview_id: str
    result: str




def register_emotion_reflection_routes(app: FastAPI) -> None:
    @app.get("/emotion/reflection/quota", response_model=EmotionReflectionQuotaResponse)
    async def emotion_reflection_quota(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionReflectionQuotaResponse:
        user_id = await resolve_authenticated_user_id(authorization=authorization)
        quota = await build_emotion_reflection_quota_status(user_id)
        return EmotionReflectionQuotaResponse(**quota)

    @app.post("/emotion/reflection/preview", response_model=EmotionReflectionPreviewResponse)
    async def emotion_reflection_preview(
        request: Request,
        payload: EmotionReflectionPreviewRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionReflectionPreviewResponse:
        user_id = await resolve_authenticated_user_id(
            authorization=authorization,
            legacy_user_id=payload.user_id,
        )
        _ = extract_client_meta(request.headers)

        normalized = normalize_submission_payload(
            emotions=payload.emotions,
            memo=payload.memo,
            memo_action=payload.memo_action,
            category=payload.category,
        )
        preview = generate_emotion_reflection_preview(
            emotion_details=normalized["emotion_details"],
            memo=payload.memo,
            memo_action=payload.memo_action,
            categories=normalized["category"],
        )
        draft = await create_preview_draft(
            user_id=user_id,
            question=preview["question"],
            q_key=preview["q_key"],
            raw_answer=preview["raw_answer"],
            category=preview.get("category"),
            display_result=preview["display_result"],
            emotion_input={
                "emotions": normalized["emotion_details"],
                "memo": str(payload.memo or ""),
                "memo_action": str(payload.memo_action or ""),
                "category": list(normalized["category"] or []),
                "created_at": str(payload.created_at or "").strip() or None,
                "notify_friends": True if payload.notify_friends is None else bool(payload.notify_friends),
            },
        )
        quota = await build_emotion_reflection_quota_status(user_id)
        return EmotionReflectionPreviewResponse(
            preview_id=str(draft.get("id") or ""),
            question=str(preview["question"]),
            reflection_text=str(preview["answer_display_text"] or ""),
            answer_display_state=str(preview["answer_display_state"] or "ready"),
            quota=EmotionReflectionQuotaResponse(**quota),
            meta={
                "q_key": str(preview["q_key"]),
                "category": preview.get("category"),
            },
        )

    @app.post("/emotion/reflection/publish", response_model=EmotionReflectionPublishResponse)
    async def emotion_reflection_publish(
        body: EmotionReflectionPublishRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionReflectionPublishResponse:
        user_id = await resolve_authenticated_user_id(authorization=authorization)
        execution = await execute_home_command(
            "emotion.reflection.publish",
            payload={"preview_id": body.preview_id},
            user_id=user_id,
            source="emotion.reflection.publish.route",
        )
        result = execution.result.data
        return EmotionReflectionPublishResponse(
            preview_id=str(result.get("preview_id") or body.preview_id),
            reflection_id=str(result.get("reflection_id") or body.preview_id),
            emotion_id=result.get("emotion_id"),
            created_at=str(result.get("created_at") or ""),
            question=str(result.get("question") or ""),
            reflection_text=str(result.get("reflection_text") or ""),
            quota=EmotionReflectionQuotaResponse(**(result.get("quota") if isinstance(result.get("quota"), dict) else {})),
            input_feedback=result.get("input_feedback") if isinstance(result.get("input_feedback"), dict) else None,
        )


    @app.post("/emotion/reflection/cancel", response_model=EmotionReflectionCancelResponse)
    async def emotion_reflection_cancel(
        body: EmotionReflectionCancelRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionReflectionCancelResponse:
        user_id = await resolve_authenticated_user_id(authorization=authorization)
        draft = await fetch_preview_draft(preview_id=body.preview_id, user_id=user_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Reflection preview not found")
        result = await cancel_preview_draft(preview_id=body.preview_id, user_id=user_id)
        return EmotionReflectionCancelResponse(
            status="ok",
            preview_id=str(body.preview_id),
            result=str(result.get("status") or "rejected"),
        )
