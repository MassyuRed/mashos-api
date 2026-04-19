from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from astor_snapshot_enqueue import enqueue_global_snapshot_refresh
from today_question_store import TodayQuestionStore, _answer_summary

logger = logging.getLogger("home_gateway.today_question_command_service")
store = TodayQuestionStore()


async def _enqueue_self_structure_refresh(user_id: str, trigger: str) -> bool:
    try:
        res = await enqueue_global_snapshot_refresh(
            user_id=str(user_id or "").strip(),
            trigger=trigger,
        )
        return bool(res)
    except Exception:
        logger.exception("today_question: snapshot enqueue failed")
        return False


async def create_today_question_answer(
    *,
    user_id: str,
    service_day_key: str,
    question_id: str,
    answer_mode: str,
    selected_choice_id: Optional[str] = None,
    selected_choice_key: Optional[str] = None,
    free_text: Optional[str] = None,
    sequence_no: Optional[int] = None,
    timezone_name: Optional[str] = None,
) -> Dict[str, Any]:
    row = await store.create_answer(
        str(user_id or "").strip(),
        service_day_key=service_day_key,
        question_id=question_id,
        sequence_no=sequence_no,
        answer_mode=answer_mode,
        selected_choice_id=selected_choice_id,
        selected_choice_key=selected_choice_key,
        free_text=free_text,
        timezone_name=timezone_name,
    )
    enqueued = await _enqueue_self_structure_refresh(str(user_id or "").strip(), trigger="today_question_answer")
    return {
        "status": "ok",
        "answer_id": str(row.get("id") or ""),
        "saved": True,
        "snapshot_refresh_enqueued": enqueued,
        "answer_summary": _answer_summary(row),
    }
