from __future__ import annotations

from .command_types import HomeCommand, HomeDispatchAction, HomeDispatchPlan


def _emotion_submit_actions(command: HomeCommand) -> tuple[HomeDispatchAction, ...]:
    requested_at = command.context.requested_at if command.context else None
    user_id = command.context.user_id if command.context else None
    base_payload = {
        "requested_at": requested_at,
        "user_id": user_id,
        "source": command.context.source if command.context else "home",
    }
    return (
        HomeDispatchAction("notifications", "emotion_log.notify", dict(base_payload)),
        HomeDispatchAction("snapshot", "snapshot.generate", dict(base_payload, scope="global")),
        HomeDispatchAction("self_structure", "myprofile.latest_refresh", dict(base_payload)),
        HomeDispatchAction("ranking", "ranking.refresh", dict(base_payload)),
        HomeDispatchAction("account_status", "account_status.refresh", dict(base_payload)),
        HomeDispatchAction("friend_feed", "friend_feed.refresh", dict(base_payload)),
        HomeDispatchAction("reply", "emlis_ai.reply", dict(base_payload)),
    )


def _today_question_actions(command: HomeCommand) -> tuple[HomeDispatchAction, ...]:
    requested_at = command.context.requested_at if command.context else None
    user_id = command.context.user_id if command.context else None
    payload = {
        "requested_at": requested_at,
        "user_id": user_id,
        "source": command.context.source if command.context else "home",
    }
    return (
        HomeDispatchAction("startup", "startup.invalidate", dict(payload)),
        HomeDispatchAction("snapshot", "snapshot.generate", dict(payload, scope="global")),
    )


def _notice_actions(command: HomeCommand) -> tuple[HomeDispatchAction, ...]:
    requested_at = command.context.requested_at if command.context else None
    user_id = command.context.user_id if command.context else None
    payload = {
        "requested_at": requested_at,
        "user_id": user_id,
        "source": command.context.source if command.context else "home",
    }
    return (HomeDispatchAction("startup", "startup.invalidate", dict(payload)),)


def _reflection_publish_actions(command: HomeCommand) -> tuple[HomeDispatchAction, ...]:
    return _emotion_submit_actions(command)


_DISPATCHERS = {
    "emotion.submit": _emotion_submit_actions,
    "today_question.answer.create": _today_question_actions,
    "notice.read": _notice_actions,
    "notice.popup_seen": _notice_actions,
    "emotion.reflection.publish": _reflection_publish_actions,
}


def build_dispatch_plan(command: HomeCommand) -> HomeDispatchPlan:
    builder = _DISPATCHERS.get(command.name)
    actions = builder(command) if builder is not None else ()
    return HomeDispatchPlan(command_name=command.name, actions=actions)
