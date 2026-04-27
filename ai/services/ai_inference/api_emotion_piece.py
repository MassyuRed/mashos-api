# -*- coding: utf-8 -*-
"""Current Emotion->Piece write API owner.

This module owns the Emotion input -> Piece preview / publish routes. Legacy
``api_emotion_reflection`` remains only as a compatibility import path.
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
from emotion_piece_generation_service import generate_emotion_reflection_preview
from emotion_piece_store import (
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


class EmotionPiecePreviewRequest(BaseModel):
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


class EmotionPiecePublishRequest(BaseModel):
    preview_id: str = Field(..., min_length=1)


class EmotionPieceCancelRequest(BaseModel):
    preview_id: str = Field(..., min_length=1)


class EmotionPieceQuotaResponse(BaseModel):
    status: str = Field(default="ok")
    subscription_tier: str
    month_key: str
    publish_limit: Optional[int] = None
    published_count: int
    remaining_count: Optional[int] = None
    can_publish: bool


class EmotionPiecePreviewResponse(BaseModel):
    status: str = Field(default="ok")
    preview_id: str
    question: str
    reflection_text: str
    answer_display_state: str
    quota: EmotionPieceQuotaResponse
    meta: Dict[str, Any] = Field(default_factory=dict)


class EmotionPiecePublishResponse(BaseModel):
    status: str = Field(default="ok")
    preview_id: str
    reflection_id: str
    emotion_id: Optional[Any] = None
    created_at: str
    question: str
    reflection_text: str
    quota: EmotionPieceQuotaResponse
    input_feedback: Optional[Dict[str, Any]] = None


class EmotionPieceCancelResponse(BaseModel):
    status: str = Field(default="ok")
    preview_id: str
    result: str


# Legacy contract aliases kept for compat routes and older tests/import paths.
EmotionReflectionPreviewRequest = EmotionPiecePreviewRequest
EmotionReflectionPublishRequest = EmotionPiecePublishRequest
EmotionReflectionCancelRequest = EmotionPieceCancelRequest
EmotionReflectionQuotaResponse = EmotionPieceQuotaResponse
EmotionReflectionPreviewResponse = EmotionPiecePreviewResponse
EmotionReflectionPublishResponse = EmotionPiecePublishResponse
EmotionReflectionCancelResponse = EmotionPieceCancelResponse

# Current helper aliases with legacy function names kept because DB/wire contracts still use them.
BuildEmotionPieceQuotaStatus = build_emotion_reflection_quota_status
GenerateEmotionPiecePreview = generate_emotion_reflection_preview
CreateEmotionPiecePreviewDraft = create_preview_draft
FetchEmotionPiecePreviewDraft = fetch_preview_draft
CancelEmotionPiecePreviewDraft = cancel_preview_draft
ExecuteEmotionPieceHomeCommand = execute_home_command
NormalizeEmotionPieceSubmissionPayload = normalize_submission_payload
ResolveEmotionPieceAuthenticatedUserId = resolve_authenticated_user_id
ExtractEmotionPieceClientMeta = extract_client_meta


def register_emotion_piece_routes(app: FastAPI) -> None:
    """Register current Emotion->Piece write routes on the given FastAPI app."""

    @app.get("/emotion/piece/quota", response_model=EmotionPieceQuotaResponse)
    async def emotion_piece_quota(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionPieceQuotaResponse:
        user_id = await ResolveEmotionPieceAuthenticatedUserId(authorization=authorization)
        quota = await BuildEmotionPieceQuotaStatus(user_id)
        return EmotionPieceQuotaResponse(**quota)

    @app.post("/emotion/piece/preview", response_model=EmotionPiecePreviewResponse)
    async def emotion_piece_preview(
        request: Request,
        payload: EmotionPiecePreviewRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionPiecePreviewResponse:
        user_id = await ResolveEmotionPieceAuthenticatedUserId(
            authorization=authorization,
            legacy_user_id=payload.user_id,
        )
        _ = ExtractEmotionPieceClientMeta(request.headers)

        normalized = NormalizeEmotionPieceSubmissionPayload(
            emotions=payload.emotions,
            memo=payload.memo,
            memo_action=payload.memo_action,
            category=payload.category,
        )
        preview = GenerateEmotionPiecePreview(
            emotion_details=normalized["emotion_details"],
            memo=payload.memo,
            memo_action=payload.memo_action,
            categories=normalized["category"],
        )
        draft = await CreateEmotionPiecePreviewDraft(
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
        quota = await BuildEmotionPieceQuotaStatus(user_id)
        return EmotionPiecePreviewResponse(
            preview_id=str(draft.get("id") or ""),
            question=str(preview["question"]),
            reflection_text=str(preview["answer_display_text"] or ""),
            answer_display_state=str(preview["answer_display_state"] or "ready"),
            quota=EmotionPieceQuotaResponse(**quota),
            meta={
                "q_key": str(preview["q_key"]),
                "category": preview.get("category"),
            },
        )

    @app.post("/emotion/piece/publish", response_model=EmotionPiecePublishResponse)
    async def emotion_piece_publish(
        body: EmotionPiecePublishRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionPiecePublishResponse:
        user_id = await ResolveEmotionPieceAuthenticatedUserId(authorization=authorization)
        execution = await ExecuteEmotionPieceHomeCommand(
            "emotion.reflection.publish",
            payload={"preview_id": body.preview_id},
            user_id=user_id,
            source="emotion.piece.publish.route",
        )
        result = execution.result.data
        return EmotionPiecePublishResponse(
            preview_id=str(result.get("preview_id") or body.preview_id),
            reflection_id=str(result.get("reflection_id") or body.preview_id),
            emotion_id=result.get("emotion_id"),
            created_at=str(result.get("created_at") or ""),
            question=str(result.get("question") or ""),
            reflection_text=str(result.get("reflection_text") or ""),
            quota=EmotionPieceQuotaResponse(**(result.get("quota") if isinstance(result.get("quota"), dict) else {})),
            input_feedback=result.get("input_feedback") if isinstance(result.get("input_feedback"), dict) else None,
        )

    @app.post("/emotion/piece/cancel", response_model=EmotionPieceCancelResponse)
    async def emotion_piece_cancel(
        body: EmotionPieceCancelRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionPieceCancelResponse:
        user_id = await ResolveEmotionPieceAuthenticatedUserId(authorization=authorization)
        draft = await FetchEmotionPiecePreviewDraft(preview_id=body.preview_id, user_id=user_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Reflection preview not found")
        result = await CancelEmotionPiecePreviewDraft(preview_id=body.preview_id, user_id=user_id)
        return EmotionPieceCancelResponse(
            status="ok",
            preview_id=str(body.preview_id),
            result=str(result.get("status") or "rejected"),
        )


def register_emotion_reflection_routes(app: FastAPI) -> None:
    """Legacy entrypoint name; current routes are still owned by this module."""
    return register_emotion_piece_routes(app)


__all__ = [
    "EmotionPiecePreviewRequest",
    "EmotionPiecePublishRequest",
    "EmotionPieceCancelRequest",
    "EmotionPieceQuotaResponse",
    "EmotionPiecePreviewResponse",
    "EmotionPiecePublishResponse",
    "EmotionPieceCancelResponse",
    "EmotionReflectionPreviewRequest",
    "EmotionReflectionPublishRequest",
    "EmotionReflectionCancelRequest",
    "EmotionReflectionQuotaResponse",
    "EmotionReflectionPreviewResponse",
    "EmotionReflectionPublishResponse",
    "EmotionReflectionCancelResponse",
    "BuildEmotionPieceQuotaStatus",
    "GenerateEmotionPiecePreview",
    "CreateEmotionPiecePreviewDraft",
    "FetchEmotionPiecePreviewDraft",
    "CancelEmotionPiecePreviewDraft",
    "ExecuteEmotionPieceHomeCommand",
    "NormalizeEmotionPieceSubmissionPayload",
    "ResolveEmotionPieceAuthenticatedUserId",
    "ExtractEmotionPieceClientMeta",
    "_build_quota_status",
    "build_emotion_reflection_quota_status",
    "cancel_preview_draft",
    "create_preview_draft",
    "execute_home_command",
    "extract_client_meta",
    "fetch_preview_draft",
    "generate_emotion_reflection_preview",
    "normalize_submission_payload",
    "persist_emotion_submission",
    "publish_preview_draft",
    "resolve_authenticated_user_id",
    "register_emotion_piece_routes",
    "register_emotion_reflection_routes",
    "HTTPException",
]
