from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from .cache_invalidator import build_cache_invalidation_plan, execute_cache_invalidation
from .command_types import (
    HomeCommand,
    HomeCommandContext,
    HomeCommandName,
    HomeCommandResult,
    HomeGatewayExecution,
    HomeGatewayPlan,
)
from .dispatch_planner import build_dispatch_plan


@dataclass(slots=True)
class HomeCommandGateway:
    """Phase 2 gateway for Home-origin write commands.

    Public routes remain unchanged. They resolve authentication and validation,
    then delegate canonical write execution to this internal gateway.
    """

    default_source: str = "home"

    def plan(self, command: HomeCommand) -> HomeGatewayPlan:
        return HomeGatewayPlan(
            command=command,
            dispatch=build_dispatch_plan(command),
            cache_invalidation=build_cache_invalidation_plan(command.name),
        )

    async def execute(self, command: HomeCommand) -> HomeGatewayExecution:
        plan = self.plan(command)
        result = await _execute_home_command_impl(command)
        user_id = command.context.user_id if command.context else ""
        await execute_cache_invalidation(
            plan.cache_invalidation,
            user_id=user_id,
            result=result,
        )
        return HomeGatewayExecution(plan=plan, result=HomeCommandResult(data=result))


async def _execute_home_command_impl(command: HomeCommand) -> Dict[str, Any]:
    payload: Mapping[str, Any] = command.payload or {}
    user_id = command.context.user_id if command.context else ""

    if command.name == "emotion.submit":
        from .emotion_submit_service import persist_emotion_submission

        return await persist_emotion_submission(
            user_id=user_id,
            emotions=payload.get("emotions") or [],
            memo=payload.get("memo"),
            memo_action=payload.get("memo_action"),
            category=payload.get("category"),
            created_at=payload.get("created_at"),
            is_secret=bool(payload.get("is_secret")),
            notify_friends=True if payload.get("notify_friends") is None else bool(payload.get("notify_friends")),
        )

    if command.name == "today_question.answer.create":
        from .today_question_command_service import create_today_question_answer

        return await create_today_question_answer(
            user_id=user_id,
            service_day_key=str(payload.get("service_day_key") or ""),
            question_id=str(payload.get("question_id") or ""),
            sequence_no=payload.get("sequence_no"),
            answer_mode=str(payload.get("answer_mode") or ""),
            selected_choice_id=payload.get("selected_choice_id"),
            selected_choice_key=payload.get("selected_choice_key"),
            free_text=payload.get("free_text"),
            timezone_name=payload.get("timezone_name"),
        )

    if command.name == "notice.read":
        from .notice_command_service import mark_notices_read

        return await mark_notices_read(
            user_id=user_id,
            notice_ids=payload.get("notice_ids") or [],
            client_meta=payload.get("client_meta") if isinstance(payload.get("client_meta"), Mapping) else None,
        )

    if command.name == "notice.popup_seen":
        from .notice_command_service import mark_notice_popup_seen

        return await mark_notice_popup_seen(
            user_id=user_id,
            notice_id=str(payload.get("notice_id") or ""),
        )

    if command.name == "emotion.reflection.publish":
        from .emotion_reflection_publish_service import publish_emotion_reflection_preview

        return await publish_emotion_reflection_preview(
            user_id=user_id,
            preview_id=str(payload.get("preview_id") or ""),
        )

    raise ValueError(f"Unsupported home command: {command.name}")


def _build_command(
    name: HomeCommandName,
    *,
    payload: Dict[str, Any] | None,
    user_id: str,
    requested_at: str | None,
    source: str,
) -> HomeCommand:
    return HomeCommand(
        name=name,
        payload=payload or {},
        context=HomeCommandContext(
            user_id=user_id,
            source=source or "home",
            requested_at=requested_at,
        ),
    )


def plan_home_command(
    name: HomeCommandName,
    *,
    payload: Dict[str, Any] | None = None,
    user_id: str,
    requested_at: str | None = None,
    source: str = "home",
) -> HomeGatewayPlan:
    gateway = HomeCommandGateway(default_source=source)
    command = _build_command(
        name,
        payload=payload,
        user_id=user_id,
        requested_at=requested_at,
        source=source,
    )
    return gateway.plan(command)


async def execute_home_command(
    name: HomeCommandName,
    *,
    payload: Dict[str, Any] | None = None,
    user_id: str,
    requested_at: str | None = None,
    source: str = "home",
) -> HomeGatewayExecution:
    gateway = HomeCommandGateway(default_source=source)
    command = _build_command(
        name,
        payload=payload,
        user_id=user_id,
        requested_at=requested_at,
        source=source,
    )
    return await gateway.execute(command)
