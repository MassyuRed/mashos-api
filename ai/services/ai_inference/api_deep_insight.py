"""Normal authenticated routes for DeepInsight and its private 4B request."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import json
import logging
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, field_validator, model_validator

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from cocolon_meaning_experience_engine.deep_insight_question import (
    QuestionPlanRejectionReason, QuestionRejectionStage, generate_question, prepare_question_material,
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
    can_use_records: bool = True
    records: Question | None
    theme: Question | None
    record_available_today: bool
    theme_available_today: bool
    theme_next_available_at: datetime | None = None
    theme_notification_enabled: bool = False
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
    theme_next_available_at: datetime | None = None


@dataclass(frozen=True)
class _Attempt:
    disposition: str
    result: QuestionResult | None = None
    error: tuple[int, str, dict[str, str] | None] | None = None
    rejection_stage: QuestionRejectionStage | None = None
    plan_rejection_reason: QuestionPlanRejectionReason | None = None


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


class ThemeNotification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: StrictBool


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
        if code == "42501" and result.get("message") == "deep_insight_records_locked":
            raise HTTPException(403, "deep_insight_records_locked")
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
        # The shared provider can finish a Map phase before it accepts this request.
        # Keep the issuance deadline across all phases, including time spent queued.
        async with asyncio.timeout(_GENERATION_BUDGET_SECONDS):
            async with httpx.AsyncClient(follow_redirects=False,
                    timeout=httpx.Timeout(float(_GENERATION_BUDGET_SECONDS), connect=5.0)) as client:
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
    next_available = state.theme_next_available_at if lane == "theme" else None
    if question is not None:
        return state, QuestionResult(status="existing", question=question, theme_next_available_at=next_available)
    if lane == "records" and not state.can_use_records:
        raise HTTPException(403, "deep_insight_records_locked")
    available = state.record_available_today if lane == "records" else state.theme_available_today
    return state, None if available else QuestionResult(status="daily_limit", theme_next_available_at=next_available)


async def _issue_from_material(owner, command, day, guard, material, prepared, sources):
    # Foreground and background callers share each owner's daily lane slot.
    lock_key = build_lock_key(namespace="deep-insight", user_id=owner, report_type=command.lane,
                              period_start=day, period_end=f"{command.lane}-slot")
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

        run = await generate_question(prepared, sources, material=material, generate=_generate_candidate)
        candidate = run.candidate
        if candidate is None:
            return _Attempt(run.disposition, QuestionResult(status="no_question"),
                            rejection_stage=run.rejection_stage, plan_rejection_reason=run.plan_rejection_reason)

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


async def _candidate_context(owner, command):
    if command.lane == "theme":
        context = await _rpc("deep_insight_theme_candidate_context", {
            "p_user_id": owner, "p_theme": command.theme,
        })
    else:
        context = await _rpc("deep_insight_candidate_context", {"p_user_id": owner})
    try:
        guard, material = context["guard"], context["material"]
        if not isinstance(guard, str) or not guard:
            raise ValueError
        return guard, material
    except (ValueError, KeyError, TypeError):
        raise HTTPException(503, "deep_insight_storage_unavailable") from None


async def _try_issue(owner, command, day, guard, material, deadline):
    try:
        prepared, sources = prepare_question_material(material, lane=command.lane, theme=command.theme)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(503, "deep_insight_storage_unavailable") from None
    if command.lane == "records" and not sources:
        return _Attempt("no_material", QuestionResult(status="no_question"))

    cache_key = build_lock_key(namespace="deep-insight-v2", user_id=owner, report_type=command.lane,
                               period_start=day, period_end=guard + ":" + (command.theme or ""))

    async def attempt():
        try:
            async with asyncio.timeout_at(deadline):
                return await _issue_from_material(owner, command, day, guard, material, prepared, sources)
        except TimeoutError:
            return _Attempt("unavailable", error=(503, "deep_insight_question_unavailable", None))
        except HTTPException as exc:
            return _Attempt("unavailable", error=(exc.status_code, exc.detail, exc.headers))

    # A caller timing out must not cancel a shared microcache result. The
    # producer has its own timeout at the same absolute deadline.
    return await asyncio.shield(get_or_compute(cache_key, 0, attempt,
        ttl_resolver=lambda row: _NO_MERIT_CACHE_SECONDS if row.disposition == "no_merit" else 0))


def _map_source_matches(material, expected_version):
    if expected_version is None:
        return True
    reference = material.get("map") if isinstance(material, dict) else None
    return isinstance(reference, dict) and reference.get("source_version") == expected_version


async def _issue_question(owner, command, deadline, *, expected_map_version=None):
    state, previous = await _issue_state(owner, command.lane)
    if previous is not None:
        return _Attempt(previous.status, previous)

    day = state.day.isoformat()
    guard, material = await _candidate_context(owner, command)
    if not _map_source_matches(material, expected_map_version):
        return _Attempt("stale_map", QuestionResult(status="no_question"))
    outcome = await _try_issue(owner, command, day, guard, material, deadline)
    if outcome.disposition != "source_changed_or_duplicate":
        return outcome

    # Re-read eligibility and the lane's own material after a conflicting write.
    refreshed_state, previous = await _issue_state(owner, command.lane)
    if refreshed_state.day != state.day:
        return _Attempt("source_changed", outcome.result)
    if previous is not None:
        return _Attempt(previous.status, previous)

    refreshed_guard, refreshed_material = await _candidate_context(owner, command)
    if not _map_source_matches(refreshed_material, expected_map_version):
        return _Attempt("stale_map", QuestionResult(status="no_question"))
    if refreshed_guard == guard:
        return outcome
    return await _try_issue(owner, command, day, refreshed_guard, refreshed_material, deadline)


async def _issue_with_deadline(owner, command, *, expected_map_version=None):
    deadline = asyncio.get_running_loop().time() + _GENERATION_BUDGET_SECONDS
    try:
        async with asyncio.timeout_at(deadline):
            return await _issue_question(owner, command, deadline, expected_map_version=expected_map_version)
    except TimeoutError:
        return _Attempt("unavailable", error=(503, "deep_insight_question_unavailable", None))


async def assess_deep_insight_records(owner, source_guard):
    """Run the same issuance policy after a current map became available."""
    expected_version = sha256(source_guard.encode()).hexdigest()
    try:
        outcome = await _issue_with_deadline(owner, QuestionCommand(lane="records"),
                                             expected_map_version=expected_version)
        if outcome.error is not None:
            raise HTTPException(*outcome.error)
    except HTTPException as exc:
        if exc.status_code == 403 and exc.detail == "deep_insight_records_locked":
            return "records_locked"
        raise RuntimeError("deep_insight_record_assessment_unavailable") from None
    return outcome.disposition


def register_deep_insight_routes(app: FastAPI) -> None:
    router = APIRouter(prefix="/deep-insight")

    @router.get("", response_model=DeepInsightState)
    async def read_deep_insight(response: Response, owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        return _stored(_StoredState, await _rpc("deep_insight_state", {"p_user_id": owner}))

    @router.get("/questions/{question_id}", response_model=Question)
    async def read_deep_insight_question(question_id: UUID, response: Response, owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        return _stored(Question, await _rpc("deep_insight_question_by_id", {
            "p_user_id": owner, "p_question_id": str(question_id),
        }))

    @router.patch("/theme-notification", response_model=ThemeNotification)
    async def update_deep_insight_theme_notification(command: ThemeNotification, response: Response,
                                                     owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        saved = await _rpc("deep_insight_theme_notification_write", {
            "p_user_id": owner, "p_enabled": command.enabled,
        })
        return _stored(ThemeNotification, saved)

    @router.post("/questions", response_model=QuestionResult)
    async def issue_deep_insight_question(command: QuestionCommand, response: Response, owner: str = Depends(_owner)):
        response.headers["Cache-Control"] = "no-store"
        outcome = await _issue_with_deadline(owner, command)
        if outcome.plan_rejection_reason is not None:
            logger.info("DeepInsight generation %s %s stage=%s reason=%s", command.lane,
                        outcome.disposition, outcome.rejection_stage, outcome.plan_rejection_reason)
        elif outcome.rejection_stage is None:
            logger.info("DeepInsight generation %s %s", command.lane, outcome.disposition)
        else:
            logger.info("DeepInsight generation %s %s stage=%s",
                        command.lane, outcome.disposition, outcome.rejection_stage)
        if outcome.error is not None:
            raise HTTPException(*outcome.error)
        return outcome.result

    @router.post("/answers", response_model=AnswerResult)
    async def answer_deep_insight_question(command: AnswerCommand, response: Response, owner: str = Depends(_owner)):
        from analysis_cumulative_service import _map_refresh_queue_enabled

        response.headers["Cache-Control"] = "no-store"
        return _stored(_StoredAnswer, await _rpc("deep_insight_answer_and_refresh", {
            "p_user_id": owner, "p_question_id": str(command.question_id), "p_answer_text": command.answer_text,
            "p_enqueue_map": _map_refresh_queue_enabled(),
        }))

    app.include_router(router)
