# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from active_users_store import touch_active_user
from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token, _send_fcm_push
from astor_snapshot_enqueue import enqueue_global_snapshot_refresh
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user
from today_question_store import (
    TodayQuestionStore,
    _answer_summary,
    _history_item_public,
    invalidate_today_question_user_runtime_cache,
)
from publish_governance import history_retention_bounds_for_query
from response_microcache import build_cache_key, get_or_compute, invalidate_prefix

logger = logging.getLogger("today_question_api")
store = TodayQuestionStore()
TODAY_QUESTION_CURRENT_CACHE_TTL_SECONDS = 10.0

def _configured_today_question_cron_tokens() -> List[str]:
    values = [
        os.getenv("TODAY_QUESTION_INTERNAL_TOKEN", "").strip(),
        os.getenv("INTERNAL_ROLLOVER_TOKEN", "").strip(),
        os.getenv("CRON_INTERNAL_TOKEN", "").strip(),
        os.getenv("INTERNAL_API_TOKEN", "").strip(),
        os.getenv("MASHOS_CRON_TOKEN", "").strip(),
        os.getenv("MYMODEL_CRON_TOKEN", "").strip(),
        os.getenv("COCOLON_CRON_TOKEN", "").strip(),
    ]
    out: List[str] = []
    for value in values:
        tok = str(value or "").strip()
        if tok and tok not in out:
            out.append(tok)
    return out


TODAY_QUESTION_INTERNAL_TOKENS = _configured_today_question_cron_tokens()
TODAY_QUESTION_INTERNAL_TOKEN = TODAY_QUESTION_INTERNAL_TOKENS[0] if TODAY_QUESTION_INTERNAL_TOKENS else ""


class TodayQuestionChoiceOption(BaseModel):
    choice_id: str
    choice_key: Optional[str] = None
    label: str


class TodayQuestionCurrentQuestion(BaseModel):
    question_id: str
    question_key: Optional[str] = None
    version: int = 1
    text: str
    choice_count: int = 0
    choices: List[TodayQuestionChoiceOption] = Field(default_factory=list)
    free_text_enabled: bool = True


class TodayQuestionAnswerSummary(BaseModel):
    answer_mode: str
    label: Optional[str] = None
    text: Optional[str] = None


class TodayQuestionCurrentResponse(BaseModel):
    service_day_key: str
    question: Optional[TodayQuestionCurrentQuestion] = None
    answer_status: str = "unanswered"
    answer_summary: Optional[TodayQuestionAnswerSummary] = None
    delivery: Dict[str, Any] = Field(default_factory=dict)
    progress: Dict[str, Any] = Field(default_factory=dict)


class TodayQuestionAnswerCreateRequest(BaseModel):
    service_day_key: str
    question_id: str
    sequence_no: Optional[int] = None
    answer_mode: str = Field(..., pattern="^(choice|free_text)$")
    selected_choice_id: Optional[str] = None
    selected_choice_key: Optional[str] = None
    free_text: Optional[str] = None
    timezone_name: Optional[str] = None


class TodayQuestionAnswerWriteResponse(BaseModel):
    status: str = "ok"
    answer_id: str
    saved: bool = True
    snapshot_refresh_enqueued: bool = False
    answer_summary: Optional[TodayQuestionAnswerSummary] = None


class TodayQuestionHistoryItem(BaseModel):
    answer_id: str
    service_day_key: str
    sequence_no: Optional[int] = None
    question_id: str
    question_key: Optional[str] = None
    question_version: int = 1
    question_text: str
    answer_mode: str
    selected_choice_id: Optional[str] = None
    selected_choice_key: Optional[str] = None
    selected_choice_label: Optional[str] = None
    free_text: Optional[str] = None
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    answered_at: Optional[str] = None
    edited_at: Optional[str] = None
    edit_count: int = 0
    can_edit: bool = False


class TodayQuestionHistoryResponse(BaseModel):
    items: List[TodayQuestionHistoryItem] = Field(default_factory=list)
    limit: int = 30
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    subscription_tier: str = "free"


class TodayQuestionAnswerPatchRequest(BaseModel):
    answer_mode: str = Field(..., pattern="^(choice|free_text)$")
    selected_choice_id: Optional[str] = None
    selected_choice_key: Optional[str] = None
    free_text: Optional[str] = None


class TodayQuestionSettingsResponse(BaseModel):
    notification_enabled: bool = True
    delivery_time_local: str = "18:00"
    timezone_name: str = "Asia/Tokyo"


class TodayQuestionSettingsPatchRequest(BaseModel):
    notification_enabled: Optional[bool] = None
    delivery_time_local: Optional[str] = None
    timezone_name: Optional[str] = None


class TodayQuestionPushResponse(BaseModel):
    status: str = "ok"
    scanned: int = 0
    sent: int = 0


def _extract_today_question_cron_token(request: Request) -> Optional[str]:
    try:
        x_cron_token = str(request.headers.get("x-cron-token") or "").strip()
    except Exception:
        x_cron_token = ""
    if x_cron_token:
        return x_cron_token

    try:
        x_internal_token = str(request.headers.get("x-internal-token") or "").strip()
    except Exception:
        x_internal_token = ""
    if x_internal_token:
        return x_internal_token

    authorization = request.headers.get("authorization")
    provided = _extract_bearer_token(authorization) if authorization else None
    token = str(provided or "").strip()
    return token or None


def _require_today_question_cron_auth(request: Request) -> None:
    expected = list(TODAY_QUESTION_INTERNAL_TOKENS or [])
    if not expected:
        raise HTTPException(status_code=500, detail="Today question cron token is not configured")

    provided = _extract_today_question_cron_token(request)
    if not provided or provided not in expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


async def run_today_question_push_once(*, limit: int = 200, now_utc: Optional[datetime] = None) -> TodayQuestionPushResponse:
    current_utc = now_utc or datetime.now(timezone.utc)
    candidates = await store.list_due_push_candidates(now_utc=current_utc, limit=limit)
    sent = 0
    for row in candidates:
        token = str(row.get("push_token") or "").strip()
        if not token:
            continue
        question_text = str(row.get("question_text") or "").strip()
        body = "今日の問いが届きました。Homeを開いて答えてみましょう。"
        if question_text:
            snippet = question_text[:48]
            body = f"今日の問い: {snippet}"
        try:
            await _send_fcm_push(
                tokens=[token],
                title="Cocolon",
                body=body,
                data={
                    "type": "today_question",
                    "screen": "Input",
                    "service_day_key": str(row.get("service_day_key") or ""),
                    "question_id": str(row.get("question_id") or ""),
                    "sequence_no": str(row.get("sequence_no") or ""),
                },
            )
            sent += 1
            await store.mark_push_delivered(
                user_id=str(row.get("user_id") or ""),
                service_day_key=str(row.get("service_day_key") or ""),
                timezone_name=str(row.get("timezone_name") or ""),
                delivery_time_local=str(row.get("delivery_time_local") or ""),
            )
        except Exception:
            logger.exception("today_question: push send failed")
    return TodayQuestionPushResponse(scanned=len(candidates), sent=sent)


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
        logger.exception("today_question: touch_active_user failed")
    return uid


async def _enqueue_self_structure_refresh(user_id: str, trigger: str) -> bool:
    try:
        res = await enqueue_global_snapshot_refresh(user_id=str(user_id or "").strip(), trigger=trigger)
        return bool(res)
    except Exception:
        logger.exception("today_question: snapshot enqueue failed")
        return False


async def _invalidate_today_question_caches(user_id: str) -> None:
    uid = str(user_id or "").strip()
    if not uid:
        return
    await invalidate_prefix(f"today_question:current:{uid}")
    await invalidate_today_question_user_runtime_cache(uid)


async def _require_plus_or_higher(user_id: str) -> str:
    tier = await get_subscription_tier_for_user(user_id)
    tier_value = str(getattr(tier, "value", tier) or "free").strip().lower() or "free"
    if tier_value not in (SubscriptionTier.PLUS.value, SubscriptionTier.PREMIUM.value):
        raise HTTPException(status_code=403, detail="Plus membership or higher is required")
    return tier_value


async def _subscription_tier_value(user_id: str) -> str:
    tier = await get_subscription_tier_for_user(user_id)
    return str(getattr(tier, "value", tier) or "free").strip().lower() or "free"


async def get_today_question_current_payload_for_user(
    user_id: str,
    *,
    timezone_name: Optional[str] = None,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    cache_key = build_cache_key(
        f"today_question:current:{uid}",
        {"timezone_name": str(timezone_name or "")},
    )

    async def _build_payload() -> Dict[str, Any]:
        bundle = await store.fetch_current_bundle(uid, timezone_name=timezone_name)
        answer_summary = _answer_summary(bundle.answer)
        response = TodayQuestionCurrentResponse(
            service_day_key=bundle.service_day_key,
            question=bundle.question,
            answer_status="answered" if bundle.answer else "unanswered",
            answer_summary=answer_summary,
            delivery=bundle.settings,
            progress=bundle.progress,
        )
        return jsonable_encoder(response)

    return await get_or_compute(cache_key, TODAY_QUESTION_CURRENT_CACHE_TTL_SECONDS, _build_payload)


def register_today_question_routes(app: FastAPI) -> None:
    @app.get("/today-question/current", response_model=TodayQuestionCurrentResponse)
    async def today_question_current(
        timezone_name: Optional[str] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> TodayQuestionCurrentResponse:
        uid = await _require_user_id(authorization)
        payload = await get_today_question_current_payload_for_user(uid, timezone_name=timezone_name)
        return TodayQuestionCurrentResponse(**payload)

    @app.post("/today-question/answers", response_model=TodayQuestionAnswerWriteResponse)
    async def today_question_answers_create(
        body: TodayQuestionAnswerCreateRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> TodayQuestionAnswerWriteResponse:
        uid = await _require_user_id(authorization)
        row = await store.create_answer(
            uid,
            service_day_key=body.service_day_key,
            question_id=body.question_id,
            sequence_no=body.sequence_no,
            answer_mode=body.answer_mode,
            selected_choice_id=body.selected_choice_id,
            selected_choice_key=body.selected_choice_key,
            free_text=body.free_text,
            timezone_name=body.timezone_name,
        )
        await _invalidate_today_question_caches(uid)
        enqueued = await _enqueue_self_structure_refresh(uid, trigger="today_question_answer")
        return TodayQuestionAnswerWriteResponse(
            answer_id=str(row.get("id") or ""),
            saved=True,
            snapshot_refresh_enqueued=enqueued,
            answer_summary=_answer_summary(row),
        )

    @app.get("/today-question/history", response_model=TodayQuestionHistoryResponse)
    async def today_question_history(
        limit: int = Query(default=30, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> TodayQuestionHistoryResponse:
        uid = await _require_user_id(authorization)
        tier = await _subscription_tier_value(uid)
        now_utc = datetime.now(timezone.utc)
        retention = history_retention_bounds_for_query(tier, now_utc=now_utc)
        can_edit = tier in (SubscriptionTier.PLUS.value, SubscriptionTier.PREMIUM.value)
        raw_rows = await store.list_history(
            uid,
            limit=int(limit or 30) + 1,
            offset=offset,
            answered_at_gte=retention.get("gte_iso"),
            answered_at_lt=retention.get("lt_iso"),
        )
        has_more = len(raw_rows) > int(limit or 30)
        rows = raw_rows[: int(limit or 30)]
        items: List[TodayQuestionHistoryItem] = []
        for row in rows:
            item = _history_item_public(row)
            item["can_edit"] = can_edit
            items.append(TodayQuestionHistoryItem(**item))
        next_offset = (int(offset or 0) + int(limit or 30)) if has_more else None
        return TodayQuestionHistoryResponse(
            items=items,
            limit=int(limit or 30),
            offset=int(offset or 0),
            has_more=bool(has_more),
            next_offset=next_offset,
            subscription_tier=tier,
        )

    @app.patch("/today-question/history/{answer_id}", response_model=TodayQuestionAnswerWriteResponse)
    async def today_question_history_patch(
        answer_id: str,
        body: TodayQuestionAnswerPatchRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> TodayQuestionAnswerWriteResponse:
        uid = await _require_user_id(authorization)
        await _require_plus_or_higher(uid)
        row = await store.patch_answer(
            uid,
            answer_id,
            answer_mode=body.answer_mode,
            selected_choice_id=body.selected_choice_id,
            selected_choice_key=body.selected_choice_key,
            free_text=body.free_text,
        )
        await _invalidate_today_question_caches(uid)
        enqueued = await _enqueue_self_structure_refresh(uid, trigger="today_question_edit")
        return TodayQuestionAnswerWriteResponse(
            answer_id=str(row.get("id") or answer_id),
            saved=True,
            snapshot_refresh_enqueued=enqueued,
            answer_summary=_answer_summary(row),
        )

    @app.get("/today-question/settings", response_model=TodayQuestionSettingsResponse)
    async def today_question_settings_read(
        timezone_name: Optional[str] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> TodayQuestionSettingsResponse:
        uid = await _require_user_id(authorization)
        settings = await store.get_or_create_user_settings(uid, timezone_name=timezone_name)
        return TodayQuestionSettingsResponse(**settings)

    @app.patch("/today-question/settings", response_model=TodayQuestionSettingsResponse)
    async def today_question_settings_patch(
        body: TodayQuestionSettingsPatchRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> TodayQuestionSettingsResponse:
        uid = await _require_user_id(authorization)
        settings = await store.patch_user_settings(
            uid,
            notification_enabled=body.notification_enabled,
            delivery_time_local=body.delivery_time_local,
            timezone_name=body.timezone_name,
        )
        await _invalidate_today_question_caches(uid)
        return TodayQuestionSettingsResponse(**settings)

    @app.post("/cron/today-question/push", response_model=TodayQuestionPushResponse)
    async def today_question_push_cron(
        request: Request,
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> TodayQuestionPushResponse:
        _require_today_question_cron_auth(request)
        return await run_today_question_push_once(limit=limit)
