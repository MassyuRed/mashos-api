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
    count_published_emotion_reflections_for_month,
    create_preview_draft,
    fetch_preview_draft,
    publish_preview_draft,
)
from emotion_submit_service import (
    normalize_submission_payload,
    persist_emotion_submission,
    resolve_authenticated_user_id,
)
from reflection_publish_entitlements import (
    get_reflection_publish_policy_for_user,
    resolve_reflection_publish_limit_for_tier,
)
from subscription import SubscriptionTier, normalize_subscription_tier


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


async def _build_quota_status(user_id: str) -> Dict[str, Any]:
    policy = await get_reflection_publish_policy_for_user(user_id)
    usage = await count_published_emotion_reflections_for_month(user_id=user_id)
    tier = normalize_subscription_tier(policy.get("subscription_tier"), default=SubscriptionTier.FREE)
    publish_limit = resolve_reflection_publish_limit_for_tier(tier)
    published_count = int(usage.get("published_count") or 0)
    remaining_count = None if publish_limit is None else max(0, int(publish_limit) - published_count)
    can_publish = True if publish_limit is None else published_count < int(publish_limit)
    return {
        "status": "ok",
        "subscription_tier": tier.value,
        "month_key": usage.get("month_key"),
        "publish_limit": publish_limit,
        "published_count": published_count,
        "remaining_count": remaining_count,
        "can_publish": can_publish,
    }



def register_emotion_reflection_routes(app: FastAPI) -> None:
    @app.get("/emotion/reflection/quota", response_model=EmotionReflectionQuotaResponse)
    async def emotion_reflection_quota(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionReflectionQuotaResponse:
        user_id = await resolve_authenticated_user_id(authorization=authorization)
        quota = await _build_quota_status(user_id)
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
        quota = await _build_quota_status(user_id)
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
        draft = await fetch_preview_draft(preview_id=body.preview_id, user_id=user_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Reflection preview not found")
        if str(draft.get("status") or "").strip().lower() != "draft":
            raise HTTPException(status_code=400, detail="Reflection preview is no longer publishable")

        quota = await _build_quota_status(user_id)
        if not quota.get("can_publish"):
            raise HTTPException(status_code=403, detail="Reflection publish quota exceeded")

        content_json = draft.get("content_json") if isinstance(draft.get("content_json"), dict) else {}
        preview_input = content_json.get("emotion_preview") if isinstance(content_json.get("emotion_preview"), dict) else {}
        stored_emotions = preview_input.get("emotions") if isinstance(preview_input.get("emotions"), list) else []
        created_at = str(preview_input.get("created_at") or "").strip() or None
        notify_friends = True if preview_input.get("notify_friends") is None else bool(preview_input.get("notify_friends"))
        category = preview_input.get("category") if isinstance(preview_input.get("category"), list) else []
        memo = preview_input.get("memo")
        memo_action = preview_input.get("memo_action")

        persisted = await persist_emotion_submission(
            user_id=user_id,
            emotions=stored_emotions,
            memo=memo,
            memo_action=memo_action,
            category=category,
            created_at=created_at,
            is_secret=False,
            notify_friends=notify_friends,
        )
        published_row = await publish_preview_draft(
            preview_id=body.preview_id,
            user_id=user_id,
            published_at=str(persisted.get("created_at") or created_at or ""),
            emotion_entry=persisted.get("inserted") if isinstance(persisted.get("inserted"), dict) else None,
        )
        next_quota = await _build_quota_status(user_id)
        display_bundle = content_json.get("display") if isinstance(content_json.get("display"), dict) else {}
        reflection_text = str(
            display_bundle.get("answer_display_text")
            or content_json.get("answer_display_text")
            or published_row.get("answer")
            or ""
        )
        return EmotionReflectionPublishResponse(
            preview_id=str(body.preview_id),
            reflection_id=str(published_row.get("id") or body.preview_id),
            emotion_id=(persisted.get("inserted") or {}).get("id") if isinstance(persisted.get("inserted"), dict) else None,
            created_at=str(persisted.get("created_at") or created_at or ""),
            question=str(published_row.get("question") or draft.get("question") or ""),
            reflection_text=reflection_text,
            quota=EmotionReflectionQuotaResponse(**next_quota),
            input_feedback=(
                {
                    "comment_text": persisted.get("input_feedback_comment"),
                    "emlis_ai": persisted.get("input_feedback_meta") if isinstance(persisted.get("input_feedback_meta"), dict) else None,
                }
                if str(persisted.get("input_feedback_comment") or "").strip()
                else None
            ),
        )

    @app.post("/emotion/reflection/cancel")
    async def emotion_reflection_cancel(
        body: EmotionReflectionCancelRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        user_id = await resolve_authenticated_user_id(authorization=authorization)
        draft = await fetch_preview_draft(preview_id=body.preview_id, user_id=user_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Reflection preview not found")
        result = await cancel_preview_draft(preview_id=body.preview_id, user_id=user_id)
        return {
            "status": "ok",
            "preview_id": str(body.preview_id),
            "result": str(result.get("status") or "rejected"),
        }
