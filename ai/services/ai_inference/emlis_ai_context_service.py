# -*- coding: utf-8 -*-
from __future__ import annotations

"""Context collection for EmlisAI."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from emlis_ai_readers import (
    get_input_summary_for_emlis_ai,
    get_myweb_home_summary_for_emlis_ai,
)
from emlis_ai_greeting_state_store import decide_greeting_for_user
from emlis_ai_types import DerivedUserModel, EmlisAICapabilityConfig, SourceBundle
from emlis_ai_user_model_store import load_emlis_ai_user_model_for_user
from emotion_history_search_service import (
    get_last_input_for_user,
    list_same_day_recent_inputs,
    search_similar_inputs,
)
from supabase_client import sb_get
from today_question_store import TodayQuestionStore, _settings_public

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
    return await get_input_summary_for_emlis_ai(user_id)


async def _get_myweb_home_summary_for_user(user_id: str) -> Dict[str, Any]:
    return await get_myweb_home_summary_for_emlis_ai(user_id)


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


def _count_chars(*values: Any) -> int:
    total = 0
    for value in values:
        total += len(str(value or "").strip())
    return total


def _has_today_question_link(current_input: Dict[str, Any], latest_answer: Dict[str, Any]) -> bool:
    memo = str(current_input.get("memo") or "").strip()
    memo_action = str(current_input.get("memo_action") or "").strip()
    latest_text = str(latest_answer.get("free_text") or latest_answer.get("selected_choice_label") or "").strip()
    if not latest_text:
        return False
    return bool(latest_text and (latest_text in memo or latest_text in memo_action))


def build_input_effort_signals(
    current_input: Dict[str, Any],
    *,
    latest_today_question_answer: Optional[Dict[str, Any]] = None,
    same_day_recent_inputs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    memo_char_count = _count_chars(current_input.get("memo"))
    memo_action_char_count = _count_chars(current_input.get("memo_action"))
    emotion_count = len(current_input.get("emotion_details") or []) if isinstance(current_input.get("emotion_details"), list) else len(current_input.get("emotions") or []) if isinstance(current_input.get("emotions"), list) else 0
    category_count = len(current_input.get("category") or []) if isinstance(current_input.get("category"), list) else 0
    has_today_question_link = _has_today_question_link(current_input, latest_today_question_answer or {})
    same_day_continuation = bool(same_day_recent_inputs or [])

    effort_score = 0.0
    effort_score += min(1.0, (memo_char_count + memo_action_char_count) / 220.0) * 0.55
    effort_score += min(1.0, float(emotion_count) / 3.0) * 0.15
    effort_score += min(1.0, float(category_count) / 2.0) * 0.10
    effort_score += 0.10 if has_today_question_link else 0.0
    effort_score += 0.10 if same_day_continuation else 0.0
    effort_score = max(0.0, min(1.0, effort_score))

    return {
        "memo_char_count": memo_char_count,
        "memo_action_char_count": memo_action_char_count,
        "emotion_count": emotion_count,
        "category_count": category_count,
        "has_today_question_link": has_today_question_link,
        "same_day_continuation": same_day_continuation,
        "effort_score": effort_score,
    }


def _derived_model_size(model: Optional[DerivedUserModel]) -> Dict[str, int]:
    if model is None:
        return {
            "model_meaning_map_count": 0,
            "model_open_anchor_count": 0,
            "model_recovery_anchor_count": 0,
            "model_hypothesis_count": 0,
        }
    return {
        "model_meaning_map_count": len(model.interpretive_frame.meaning_map),
        "model_open_anchor_count": len(model.open_topic_anchors),
        "model_recovery_anchor_count": len(model.recovery_anchors),
        "model_hypothesis_count": len(model.hypotheses),
    }


def build_memory_richness_signals(
    *,
    capability: EmlisAICapabilityConfig,
    same_day_recent_inputs: List[Dict[str, Any]],
    similar_inputs: List[Dict[str, Any]],
    derived_user_model: Optional[DerivedUserModel],
) -> Dict[str, Any]:
    model_stats = _derived_model_size(derived_user_model)
    history_density_score = 0.0
    history_density_score += min(1.0, float(len(same_day_recent_inputs)) / max(1.0, float(capability.max_same_day_inputs or 1))) * 0.30
    history_density_score += min(1.0, float(len(similar_inputs)) / max(1.0, float(capability.max_similar_inputs or 1))) * 0.30
    history_density_score += min(1.0, float(model_stats["model_meaning_map_count"]) / 6.0) * 0.20
    history_density_score += min(1.0, float(model_stats["model_open_anchor_count"]) / 4.0) * 0.10
    history_density_score += min(1.0, float(model_stats["model_hypothesis_count"]) / 6.0) * 0.10
    history_density_score = max(0.0, min(1.0, history_density_score))

    return {
        "same_day_recent_count": len(same_day_recent_inputs),
        "similar_inputs_count": len(similar_inputs),
        **model_stats,
        "history_density_score": history_density_score,
    }


async def build_emlis_ai_source_bundle(
    *,
    user_id: str,
    current_input: Dict[str, Any],
    capability: EmlisAICapabilityConfig,
    display_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
    now_utc: Optional[datetime] = None,
    load_derived_model: Optional[bool] = None,
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

    should_load_model = capability.model_read_enabled and capability.include_derived_user_model
    if load_derived_model is not None:
        should_load_model = bool(load_derived_model)
    if should_load_model:
        bundle.derived_user_model = await load_emlis_ai_user_model_for_user(
            user_id=user_id,
            expected_tier=capability.tier,
        )

    bundle.side_state = {
        "greeting_slot_key": bundle.greeting.slot_key if bundle.greeting else None,
        "greeting_first_in_slot": bool(bundle.greeting.first_in_slot) if bundle.greeting else False,
    }
    bundle.input_effort = build_input_effort_signals(
        current_input,
        latest_today_question_answer=bundle.latest_today_question_answer,
        same_day_recent_inputs=bundle.same_day_recent_inputs,
    )
    bundle.memory_richness = build_memory_richness_signals(
        capability=capability,
        same_day_recent_inputs=bundle.same_day_recent_inputs,
        similar_inputs=bundle.similar_inputs,
        derived_user_model=bundle.derived_user_model,
    )
    bundle.debug.update(
        {
            "derived_model_loaded": bool(bundle.derived_user_model is not None),
            "input_effort_score": float(bundle.input_effort.get("effort_score") or 0.0),
            "history_density_score": float(bundle.memory_richness.get("history_density_score") or 0.0),
        }
    )
    return bundle
