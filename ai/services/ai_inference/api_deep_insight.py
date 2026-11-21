"""Normal authenticated routes for DeepInsight and its private 4B request."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime
import json
import logging
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from cocolon_meaning_experience_engine.deep_insight_question import (
    generate_question, prepare_question_material,
)
from emlis_thread_config import MAX_ANSWER_CHARS, natural_reply_provider_settings
from generation_lock import build_lock_key, release_lock, try_acquire_lock
from response_microcache import get_or_compute
from supabase_client import sb_post_rpc


logger = logging.getLogger(__name__)
Lane = Literal["records", "theme"]
QuestionStatus = Literal["issued", "existing", "no_question", "daily_limit"]
_GENERATION_BUDGET_SECONDS = 96
_NO_MERIT_CACHE_SECONDS = 15 * 60


class Question(BaseModel):
    id: UUID
    lane: Lane
    theme: str | None
    question_text: str
    issued_on: date
    answer_text: str | None
    answered_at: datetime | None


class DeepInsightState(BaseModel):
    can_use_theme: bool
    records: Question | None
    theme: Question | None
    record_available_today: bool
    theme_available_today: bool
    history: list[Question]


class _StoredState(DeepInsightState):
    day: date


class QuestionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lane: Lane
    theme: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def require_theme_only_in_theme_lane(self):
        if self.lane == "theme":
            if not self.theme or not self.theme.strip() or any(c in self.theme for c in "\n\r\x00"):
                raise ValueError("deep_insight_theme_required")
            self.theme = self.theme.strip()
        elif self.theme is not None:
            raise ValueError("deep_insight_theme_not_expected")
        return self


class QuestionResult(BaseModel):
    status: QuestionStatus
    question: Question | None = None


@dataclass(frozen=True)
class _Attempt:
    disposition: str
    result: QuestionResult | None = None
    error: tuple[int, str, dict[str, str] | None] | None = None


class AnswerCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: UUID
    answer_text: str = Field(min_length=1, max_length=MAX_ANSWER_CHARS)

    @field_validator("answer_text")
    @classmethod
    def require_answer(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("deep_insight_answer_required")
        return value


class AnswerResult(BaseModel):
    question: Question


class _StoredAnswer(AnswerResult):
    inserted: bool


async def _owner(authorization: str | None = Header(default=None)) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(401, "deep_insight_auth_required", headers={"WWW-Authenticate": "Bearer"})
    resolved = await _resolve_user_id_from_token(token)
    try:
        return str(UUID(resolved))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(401, "deep_insight_auth_required") from None


async def _rpc(name, payload):
    try:
        response = await sb_post_rpc(name, payload, timeout=8.0)
        result = response.json()
    except (httpx.HTTPError, TypeError, ValueError, RuntimeError):
        raise HTTPException(503, "deep_insight_storage_unavailable") from None
    if response.status_code >= 300:
        code = result.get("code") if isinstance(result, dict) else None
        error = {
            "P0002": (404, "deep_insight_question_unavailable"),
            "23505": (409, "deep_insight_answer_conflict"),
            "42501": (403, "deep_insight_theme_locked"),
            "22023": (422, "deep_insight_request_invalid"),
        }.get(code, (503, "deep_insight_storage_unavailable"))
        raise HTTPException(*error)
    if not isinstance(result, dict):
        raise HTTPException(503, "deep_insight_storage_unavailable")
    return result


def _stored(model, result):
    try:
        return model.model_validate(result)
    except ValidationError:
        raise HTTPException(503, "deep_insight_storage_unavailable") from None


async def _generate_candidate(system: str, material: dict) -> str:
    # The existing normal Emlis recipient author serves OpenAI-compatible
    # system/user messages. This is a separate request and never uses its
    # recipient reply as a question or as evidence.
    settings = natural_reply_provider_settings()
    endpoint, model, key = (settings[name].strip() for name in ("endpoint", "model", "api_key"))
    try:
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or not parsed.path.endswith("/chat/completions")
                or not model or not key):
            raise ValueError
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(material, ensure_ascii=False, separators=(",", ":"))},
        ]
        async with asyncio.timeout(32):
            async with httpx.AsyncClient(follow_redirects=False,
                    timeout=httpx.Timeout(30.0, connect=5.0)) as client:
                async with client.stream("POST", endpoint, headers={"Authorization": "Bearer " + key}, json={
                    "model": model, "messages": messages, "temperature": 0, "max_tokens": 2048,
                    "stream": False, "chat_template_kwargs": {"enable_thinking": False},
                }) as response:
                    response.raise_for_status()
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > 32768:
                            raise ValueError
        result = json.loads(body)
        if result["model"] != model or len(result["choices"]) != 1:
            raise ValueError
        choice = result["choices"][0]
        message = choice["message"]
        if (choice["finish_reason"] != "stop" or message["role"] != "assistant"
                or message.get("tool_calls") or message.get("function_call") or message.get("reasoning_content")
                or not isinstance(message["content"], str)):
            raise ValueError
        return message["content"]
    except (httpx.HTTPError, TimeoutError, TypeError, ValueError, KeyError, IndexError, AttributeError):
        raise HTTPException(503, "deep_insight_question_unavailable") from None


async def _issue_state(owner: str, lane: Lane):
    state = _stored(_StoredState, await _rpc("deep_insight_state", {"p_user_id": owner}))
    if lane == "theme" and not state.can_use_theme:
        raise HTTPException(403, "deep_insight_theme_locked")
    question = state.records if lane == "records" else state.theme
    if question is not None:
        return state, QuestionResult(status="existing", question=question)
    available = state.record_available_today if lane == "records" else state.theme_available_today
    return state, None if available else QuestionResult(status="daily_limit")


async def _issue_from_material(owner, command, day, guard, material, prepared, sources):
    # A different theme still uses the same owner's single theme slot.
    lock_key = build_lock_key(namespace="deep-insight", user_id=owner, report_type=command.lane,
                              period_start=day, period_end=guard)
    try:
        lease = await try_acquire_lock(lock_key=lock_key, ttl_seconds=120)
    except (HTTPException, httpx.HTTPError, RuntimeError, ValueError):
        raise HTTPException(503, "deep_insight_question_unavailable") from None
    if not lease.acquired:
        _, result = await _issue_state(owner, command.lane)
        if result is not None:
            return _Attempt(result.status, result)
        raise HTTPException(503, "deep_insight_question_unavailable", headers={"Retry-After": "3"})

    try:
        state, result = await _issue_state(owner, command.lane)
        if result is not None:
            return _Attempt(result.status, result)
        if state.day.isoformat() != day:
            return _Attempt("source_changed", QuestionResult(status="no_question"))

        try:
            async with asyncio.timeout(_GENERATION_BUDGET_SECONDS):
                run = await generate_question(prepared, sources, material=material, generate=_generate_candidate)
        except TimeoutError:
            raise HTTPException(503, "deep_insight_question_unavailable") from None
        candidate = run.candidate
        if candidate is None:
            return _Attempt(run.disposition, QuestionResult(status="no_question"))

        saved = await _rpc("deep_insight_issue_grounded", {
            "p_user_id": owner, "p_day": day, "p_lane": command.lane, "p_theme": command.theme,
            "p_question_text": candidate.text, "p_question_key": candidate.question_key,
            "p_text_key": candidate.text_key, "p_material_guard": guard,
            "p_grounding_receipt": candidate.receipt,
        })
        result = _stored(QuestionResult, saved)
        return _Attempt("source_changed_or_duplicate" if result.status == "no_question" else result.status, result)
    finally:
        await release_lock(lock_key=lease.lock_key, owner_id=lease.owner_id)


def register_deep_insight_routes(app: FastAPI) -> None:
    router = APIRouter(prefix="/deep-insight")

    @router.get("", response_model=DeepInsightState)
    async def read_deep_insight(response: Response, owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        return _stored(_StoredState, await _rpc("deep_insight_state", {"p_user_id": owner}))

    @router.post("/questions", response_model=QuestionResult)
    async def issue_deep_insight_question(command: QuestionCommand, response: Response, owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        state, previous = await _issue_state(owner, command.lane)
        if previous is not None:
            return previous

        context = await _rpc("deep_insight_candidate_context", {"p_user_id": owner})
        try:
            material = context["material"]
            guard = context["guard"]
            if not isinstance(guard, str) or not guard:
                raise ValueError
            prepared, sources = prepare_question_material(material, lane=command.lane, theme=command.theme)
        except (ValueError, KeyError, TypeError):
            raise HTTPException(503, "deep_insight_storage_unavailable") from None
        if command.lane == "records" and not sources:
            return QuestionResult(status="no_question")

        day = state.day.isoformat()
        cache_key = build_lock_key(namespace="deep-insight-v2", user_id=owner, report_type=command.lane,
                                   period_start=day, period_end=guard + ":" + (command.theme or ""))

        async def attempt():
            try:
                return await _issue_from_material(owner, command, day, guard, material, prepared, sources)
            except HTTPException as exc:
                # Failed requests remain retryable. Use the status only, never source text, in telemetry.
                return _Attempt("unavailable", error=(exc.status_code, exc.detail, exc.headers))

        outcome = await get_or_compute(cache_key, 0, attempt,
            ttl_resolver=lambda row: _NO_MERIT_CACHE_SECONDS if row.disposition == "no_merit" else 0)
        logger.info("DeepInsight generation %s %s", command.lane, outcome.disposition)
        if outcome.error is not None:
            raise HTTPException(*outcome.error)
        return outcome.result

    @router.post("/answers", response_model=AnswerResult)
    async def answer_deep_insight_question(command: AnswerCommand, response: Response, owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        saved = _stored(_StoredAnswer, await _rpc("deep_insight_answer", {
            "p_user_id": owner, "p_question_id": str(command.question_id), "p_answer_text": command.answer_text,
        }))
        from analysis_cumulative_service import request_map_refresh
        try:
            # A replay can recover a lost write response without disturbing a
            # refresh already queued for that original answer.
            await request_map_refresh(owner, trigger="deep_insight_answer" if saved.inserted else "map_view")
        except Exception:
            logger.warning("DeepInsight answer saved; map refresh enqueue unavailable")
        return saved

    app.include_router(router)
