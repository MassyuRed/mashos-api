"""Authenticated, default-off Q2 development application API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from api_account_visibility import _require_user_id
from emlis_thread_config import MAX_ANSWER_CHARS, development_enabled
from emlis_thread_store import ThreadStoreError


class ThreadOperationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1, strict=True)
    idempotency_key: str = Field(min_length=1, max_length=128, strict=True)


class ThreadAnswerBody(ThreadOperationBody):
    question_id: str = Field(min_length=1, max_length=128, strict=True)
    answer_text: str = Field(min_length=1, max_length=MAX_ANSWER_CHARS, strict=True)
    authored_at: datetime | None = None

    @field_validator("answer_text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("answer_required")
        return value

    @field_validator("authored_at")
    @classmethod
    def offset_required(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("answer_time_offset_required")
        return value


class ThreadActionBody(ThreadOperationBody):
    action: Literal["skip", "stop", "continue", "retry_response"]
    question_id: str | None = Field(default=None, max_length=128)
    operation_id: UUID | None = None


def register_emlis_thread_routes(app: FastAPI, *, service=None):
    def owner():
        if service is not None:
            return service
        from emlis_thread_service import EmlisThreadService
        return EmlisThreadService()

    async def user(authorization, response):
        response.headers["Cache-Control"] = "private, no-store"
        if not development_enabled():
            raise HTTPException(404, "emlis_thread_not_enabled")
        return await _require_user_id(authorization)

    async def call(awaitable):
        try:
            return await awaitable
        except ThreadStoreError as exc:
            raise HTTPException(exc.status, exc.code, headers={"Cache-Control": "private, no-store"}) from None

    @app.get("/emlis/threads/by-input/{emotion_id}")
    async def read_thread(emotion_id: UUID, response: Response, authorization: str | None = Header(default=None)):
        me = await user(authorization, response)
        return await call(owner().get(me, str(emotion_id)))

    @app.post("/emlis/threads/{thread_id}/answers")
    async def answer(thread_id: UUID, body: ThreadAnswerBody, response: Response, authorization: str | None = Header(default=None)):
        me = await user(authorization, response)
        values = body.model_dump()
        values["authored_at"] = body.authored_at.isoformat() if body.authored_at else None
        return await call(owner().answer(me, str(thread_id), **values))

    @app.post("/emlis/threads/{thread_id}/actions")
    async def action(thread_id: UUID, body: ThreadActionBody, response: Response, authorization: str | None = Header(default=None)):
        me = await user(authorization, response)
        values = body.model_dump()
        values["operation_id"] = str(body.operation_id) if body.operation_id else None
        return await call(owner().action(me, str(thread_id), **values))
