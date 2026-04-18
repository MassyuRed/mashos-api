# -*- coding: utf-8 -*-
from __future__ import annotations

"""Context collection for EmlisAI."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from emlis_ai_greeting_state_store import decide_greeting_for_user
from emlis_ai_types import EmlisAICapabilityConfig, SourceBundle
from emotion_history_search_service import (
    get_last_input_for_user,
    list_same_day_recent_inputs,
    search_similar_inputs,
)
from supabase_client import sb_get
from today_question_store import TodayQuestionStore, _history_item_public, _settings_public

_PROFILES_TABLE = "profiles"
_TQ_STORE = TodayQuestionStore()


def _pick_rows(resp: Any) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def _get_input_summary_for_user(user_id: str) -> Dict[str, Any]:
    try:
        from api_input_summary import get_input_summary_payload_for_user
        return await get_input_summary_payload_for_user(user_id)
    except Exception:
        return {}


async def _get_myweb_home_summary_for_user(user_id: str) -> Dict[str, Any]:
    try:
        from api_myweb_reads import get_myweb_home_summary_payload_for_user
        return await get_myweb_home_summary_payload_for_user(user_id)
    except Exception:
        return {}


async def _get_latest_today_question_answer_for_user(user_id: str) -> Dict[str, Any]:
    try:
        rows = await _TQ_STORE.list_history(user_id, limit=1, offset=0)
        return rows[0] if rows else {}
    except Exception:
        return {}


async def _list_recent_today_question_answers_for_user(user_id: str, *, limit: int) -> List[Dict[str, Any]]:
    try:
        rows = await _TQ_STORE.list_history(user_id, limit=limit, offset=0)
        return rows or []
    except Exception:
        return []


async def _resolve_display_name_for_user(user_id: str) -> Optional[str]:
    uid = str(user_id or "").strip()
    if not uid:
        return None
    try:
        resp = await sb_get(
            f"/rest/v1/{_PROFILES_TABLE}",
            params={"select": "display_name", "id": f"eq.{uid}", "limit": "1"},
            timeout=4.0,
        )
        if resp.status_code >= 300:
            return None
        rows = _pick_rows(resp)
        if not rows:
            return None
        display_name = str(rows[0].get("display_name") or "").strip()
        return display_name or None
    except Exception:
        return None


async def _resolve_timezone_name_for_user(user_id: str, *, fallback: Optional[str] = None) -> str:
    raw_fallback = str(fallback or "").strip()
    if raw_fallback:
        return raw_fallback
    try:
        settings = await _TQ_STORE.get_or_create_user_settings(user_id)
        public_settings = _settings_public(settings) if isinstance(settings, dict) else {}
        timezone_name = str(public_settings.get("timezone_name") or "").strip()
        return timezone_name or "Asia/Tokyo"
    except Exception:
        return "Asia/Tokyo"


async def build_emlis_ai_source_bundle(
    *,
    user_id: str,
    current_input: Dict[str, Any],
    capability: EmlisAICapabilityConfig,
    display_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
    now_utc: Optional[datetime] = None,
) -> SourceBundle:
    now_utc = now_utc or datetime.now(timezone.utc)
    resolved_name = display_name if str(display_name or "").strip() else await _resolve_display_name_for_user(user_id)
    resolved_timezone_name = await _resolve_timezone_name_for_user(user_id, fallback=timezone_name)

    greeting = await decide_greeting_for_user(
        user_id=user_id,
        display_name=resolved_name,
        timezone_name=resolved_timezone_name,
        now_utc=now_utc,
    )

    bundle = SourceBundle(
        user_id=user_id,
        display_name=resolved_name,
        current_input=current_input,
        greeting=greeting,
        debug={"tier": capability.tier, "history_mode": capability.history_mode},
    )

    if capability.include_input_summary:
        bundle.input_summary = await _get_input_summary_for_user(user_id)

    if capability.include_myweb_summary:
        bundle.myweb_home_summary = await _get_myweb_home_summary_for_user(user_id)

    if capability.include_today_question_history:
        bundle.latest_today_question_answer = await _get_latest_today_question_answer_for_user(user_id)
        bundle.recent_today_question_answers = await _list_recent_today_question_answers_for_user(user_id, limit=3)

    if capability.history_mode != "none":
        created_at = str(current_input.get("created_at") or "").strip()
        current_emotion_id = current_input.get("id")
        bundle.last_input = await get_last_input_for_user(
            user_id,
            include_secret=True,
            exclude_emotion_id=current_emotion_id,
        )
        if created_at:
            bundle.same_day_recent_inputs = await list_same_day_recent_inputs(
                user_id,
                created_at=created_at,
                include_secret=True,
                limit=capability.max_same_day_inputs,
                exclude_emotion_id=current_emotion_id,
            )
        bundle.similar_inputs = await search_similar_inputs(
            user_id,
            memo=str(current_input.get("memo") or "").strip() or None,
            memo_action=str(current_input.get("memo_action") or "").strip() or None,
            category=current_input.get("category") if isinstance(current_input.get("category"), list) else [],
            emotion_details=current_input.get("emotion_details") if isinstance(current_input.get("emotion_details"), list) else [],
            include_secret=True,
            window_days=capability.retrieval_window_days,
            limit=capability.max_similar_inputs,
            exclude_emotion_id=current_emotion_id,
        )

    return bundle
