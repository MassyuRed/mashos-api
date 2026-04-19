from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from response_microcache import invalidate_prefix
from startup_snapshot_store import invalidate_startup_snapshot

from .command_types import HomeCacheInvalidationPlan, HomeCommandName

logger = logging.getLogger("home_gateway.cache_invalidator")


_INVALIDATION_KEYS: dict[HomeCommandName, HomeCacheInvalidationPlan] = {
    "emotion.submit": HomeCacheInvalidationPlan(
        response_keys=("input_summary", "global_summary", "home_state"),
        startup_snapshot=True,
    ),
    "today_question.answer.create": HomeCacheInvalidationPlan(
        response_keys=("today_question_current", "today_question_status", "home_state"),
        startup_snapshot=True,
    ),
    "notice.read": HomeCacheInvalidationPlan(
        response_keys=("notices_current", "home_state"),
        startup_snapshot=True,
    ),
    "notice.popup_seen": HomeCacheInvalidationPlan(
        response_keys=("notices_current", "home_state"),
        startup_snapshot=True,
    ),
    "emotion.reflection.publish": HomeCacheInvalidationPlan(
        response_keys=("input_summary", "global_summary", "emotion_reflection_quota", "home_state"),
        startup_snapshot=True,
    ),
}


def build_cache_invalidation_plan(command_name: HomeCommandName) -> HomeCacheInvalidationPlan:
    return _INVALIDATION_KEYS.get(command_name, HomeCacheInvalidationPlan())


async def execute_cache_invalidation(
    plan: HomeCacheInvalidationPlan,
    *,
    user_id: str,
    result: Optional[Mapping[str, Any]] = None,
) -> None:
    uid = str(user_id or "").strip()
    if not uid:
        return

    result_payload = dict(result or {})
    activity_date = str(result_payload.get("global_summary_activity_date") or "").strip() or None

    for response_key in plan.response_keys:
        try:
            if response_key == "input_summary":
                await invalidate_prefix(f"input_summary:{uid}")
                await invalidate_prefix(f"myweb_home_summary:{uid}")
            elif response_key == "global_summary":
                if activity_date:
                    await invalidate_prefix(f"global_summary:{activity_date}:")
                else:
                    await invalidate_prefix("global_summary:")
            elif response_key == "today_question_current":
                await invalidate_prefix(f"today_question:current:{uid}")
            elif response_key == "today_question_status":
                await invalidate_prefix(f"today_question:status:{uid}")
            elif response_key == "notices_current":
                await invalidate_prefix(f"notices:current:{uid}")
            elif response_key == "emotion_reflection_quota":
                # Currently this response is computed without response_microcache.
                continue
            elif response_key == "home_state":
                await invalidate_prefix(f"home_state:{uid}")
        except Exception:
            logger.exception(
                "home gateway cache invalidation failed: user_id=%s response_key=%s",
                uid,
                response_key,
            )

    if plan.startup_snapshot:
        try:
            await invalidate_startup_snapshot(uid)
        except Exception:
            logger.exception("home gateway startup invalidation failed: user_id=%s", uid)
