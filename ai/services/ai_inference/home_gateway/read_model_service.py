from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Optional

from response_microcache import build_cache_key, get_or_compute, invalidate_exact

logger = logging.getLogger("home_gateway.read_model_service")

JST = timezone(timedelta(hours=9))
HOME_STATE_SCHEMA_VERSION = "home_state.v1"
HOME_STATE_CACHE_TTL_SECONDS = 15.0
HOME_STATE_SECTION_TIMEOUT_SECONDS = 10.0
HOME_STATE_SOURCE_VERSIONS: Dict[str, str] = {
    "schema": HOME_STATE_SCHEMA_VERSION,
    "input_summary": "input.summary.v1",
    "global_summary": "global_summary.ready_first.v1",
    "notices_current": "notice.current.v1",
    "today_question_current": "today_question.current.v1",
    "emotion_reflection_quota": "emotion.reflection.quota.v1",
}


def _iso_utc(dt: Optional[datetime] = None) -> str:
    return (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today_jst_date_iso() -> str:
    return datetime.now(JST).date().isoformat()


def _normalize_client_meta(client_meta: Optional[Mapping[str, Any]]) -> Dict[str, Optional[str]]:
    meta = client_meta or {}

    def _pick(key: str) -> Optional[str]:
        value = meta.get(key) if isinstance(meta, Mapping) else None
        s = str(value or "").strip()
        return s or None

    return {
        "platform": _pick("platform"),
        "app_version": _pick("app_version"),
        "app_build": _pick("app_build"),
    }


def _home_state_cache_key(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
) -> str:
    uid = str(user_id or "").strip()
    meta = _normalize_client_meta(client_meta)
    return build_cache_key(
        f"home_state:{uid}",
        {
            "platform": meta.get("platform"),
            "app_version": meta.get("app_version"),
            "app_build": meta.get("app_build"),
            "timezone_name": str(timezone_name or "").strip() or None,
        },
    )


async def _safe_section(name: str, coro, default: Mapping[str, Any]) -> tuple[str, Dict[str, Any], Optional[str]]:
    try:
        payload = await asyncio.wait_for(coro, timeout=max(1.0, float(HOME_STATE_SECTION_TIMEOUT_SECONDS or 0.0)))
        if not isinstance(payload, Mapping):
            return name, dict(default), None
        return name, dict(payload), None
    except Exception as exc:
        logger.warning("home state section fallback: section=%s err=%r", name, exc)
        return name, dict(default), str(exc)


async def _build_home_state_payload(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    normalized_meta = _normalize_client_meta(client_meta)
    if not uid:
        return {
            "status": "ok",
            "user_id": "",
            "generated_at": _iso_utc(),
            "service_day_key": _today_jst_date_iso(),
            "source_versions": dict(HOME_STATE_SOURCE_VERSIONS),
            "popup_candidates": [],
            "notice_popup_notice_id": None,
            "sections": {
                "input_summary": {
                    "status": "ok",
                    "user_id": "",
                    "today_count": 0,
                    "week_count": 0,
                    "month_count": 0,
                    "streak_days": 0,
                    "last_input_at": None,
                },
                "global_summary": {
                    "date": _today_jst_date_iso(),
                    "tz": "+09:00",
                    "emotion_users": 0,
                    "reflection_views": 0,
                    "echo_count": 0,
                    "discovery_count": 0,
                    "updated_at": None,
                },
                "notices_current": {
                    "feature_enabled": True,
                    "unread_count": 0,
                    "has_unread": False,
                    "badge": {"show": False, "count": 0},
                    "popup_notice": None,
                },
                "today_question_current": {
                    "service_day_key": _today_jst_date_iso(),
                    "question": None,
                    "answer_status": "unanswered",
                    "answer_summary": None,
                    "delivery": {},
                    "progress": {},
                },
                "emotion_reflection_quota": {
                    "status": "ok",
                    "subscription_tier": "free",
                    "month_key": _today_jst_date_iso()[:7],
                    "publish_limit": 0,
                    "published_count": 0,
                    "remaining_count": 0,
                    "can_publish": False,
                },
            },
            "errors": {"user_id": "missing"},
        }

    from api_global_summary import get_global_summary_payload
    from api_input_summary import get_input_summary_payload_for_user
    from api_notice import get_notice_current_payload_for_user
    from api_today_question import get_today_question_current_payload_for_user
    from home_gateway.emotion_reflection_publish_service import build_emotion_reflection_quota_status

    defaults: Dict[str, Dict[str, Any]] = {
        "input_summary": {
            "status": "ok",
            "user_id": uid,
            "today_count": 0,
            "week_count": 0,
            "month_count": 0,
            "streak_days": 0,
            "last_input_at": None,
        },
        "global_summary": {
            "date": _today_jst_date_iso(),
            "tz": "+09:00",
            "emotion_users": 0,
            "reflection_views": 0,
            "echo_count": 0,
            "discovery_count": 0,
            "updated_at": None,
        },
        "notices_current": {
            "feature_enabled": True,
            "unread_count": 0,
            "has_unread": False,
            "badge": {"show": False, "count": 0},
            "popup_notice": None,
        },
        "today_question_current": {
            "service_day_key": _today_jst_date_iso(),
            "question": None,
            "answer_status": "unanswered",
            "answer_summary": None,
            "delivery": {},
            "progress": {},
        },
        "emotion_reflection_quota": {
            "status": "ok",
            "subscription_tier": "free",
            "month_key": _today_jst_date_iso()[:7],
            "publish_limit": 0,
            "published_count": 0,
            "remaining_count": 0,
            "can_publish": False,
        },
    }

    section_results = await asyncio.gather(
        _safe_section("input_summary", get_input_summary_payload_for_user(uid), defaults["input_summary"]),
        _safe_section("global_summary", get_global_summary_payload(mode="ready_first"), defaults["global_summary"]),
        _safe_section("notices_current", get_notice_current_payload_for_user(uid, normalized_meta), defaults["notices_current"]),
        _safe_section(
            "today_question_current",
            get_today_question_current_payload_for_user(uid, timezone_name=timezone_name),
            defaults["today_question_current"],
        ),
        _safe_section("emotion_reflection_quota", build_emotion_reflection_quota_status(uid), defaults["emotion_reflection_quota"]),
    )

    sections: Dict[str, Dict[str, Any]] = {}
    errors: Dict[str, str] = {}
    for name, payload, error in section_results:
        sections[name] = payload if isinstance(payload, dict) else dict(defaults[name])
        if error:
            errors[name] = error

    notices_current = sections.get("notices_current") if isinstance(sections.get("notices_current"), dict) else {}
    today_question_current = sections.get("today_question_current") if isinstance(sections.get("today_question_current"), dict) else {}
    popup_notice = notices_current.get("popup_notice") if isinstance(notices_current.get("popup_notice"), Mapping) else None
    popup_notice_id = str((popup_notice or {}).get("notice_id") or "").strip() or None
    question = today_question_current.get("question") if isinstance(today_question_current.get("question"), Mapping) else None

    popup_candidates = []
    if popup_notice_id:
        popup_candidates.append({
            "kind": "notice",
            "notice_id": popup_notice_id,
        })
    if question and str(today_question_current.get("answer_status") or "unanswered") != "answered":
        popup_candidates.append({
            "kind": "today_question",
            "service_day_key": str(today_question_current.get("service_day_key") or _today_jst_date_iso()),
            "question_id": str(question.get("question_id") or "").strip() or None,
        })

    return {
        "status": "ok",
        "user_id": uid,
        "generated_at": _iso_utc(),
        "service_day_key": str(today_question_current.get("service_day_key") or _today_jst_date_iso()),
        "source_versions": dict(HOME_STATE_SOURCE_VERSIONS),
        "popup_candidates": popup_candidates,
        "notice_popup_notice_id": popup_notice_id,
        "sections": sections,
        "errors": errors,
    }


async def get_home_state(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return await _build_home_state_payload(uid, client_meta=client_meta, timezone_name=timezone_name)

    cache_key = _home_state_cache_key(uid, client_meta=client_meta, timezone_name=timezone_name)
    if force_refresh:
        try:
            await invalidate_exact(cache_key)
        except Exception:
            logger.exception("home state exact invalidate failed")

    async def _producer() -> Dict[str, Any]:
        return await _build_home_state_payload(uid, client_meta=client_meta, timezone_name=timezone_name)

    return await get_or_compute(cache_key, HOME_STATE_CACHE_TTL_SECONDS, _producer)


__all__ = [
    "HOME_STATE_SCHEMA_VERSION",
    "HOME_STATE_SOURCE_VERSIONS",
    "get_home_state",
]
