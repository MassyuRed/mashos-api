from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Optional

from response_microcache import build_cache_key, get_or_compute, invalidate_exact, invalidate_prefix

logger = logging.getLogger("startup_snapshot_store")


STARTUP_SNAPSHOT_ENABLED = (os.getenv("STARTUP_SNAPSHOT_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"}
try:
    STARTUP_SNAPSHOT_CACHE_TTL_SECONDS = float(os.getenv("STARTUP_SNAPSHOT_CACHE_TTL_SECONDS", "25") or "25")
except Exception:
    STARTUP_SNAPSHOT_CACHE_TTL_SECONDS = 25.0
try:
    STARTUP_SNAPSHOT_REFRESH_THROTTLE_SECONDS = float(os.getenv("STARTUP_SNAPSHOT_REFRESH_THROTTLE_SECONDS", "20") or "20")
except Exception:
    STARTUP_SNAPSHOT_REFRESH_THROTTLE_SECONDS = 20.0
try:
    STARTUP_SNAPSHOT_SECTION_TIMEOUT_SECONDS = float(os.getenv("STARTUP_SNAPSHOT_SECTION_TIMEOUT_SECONDS", "12") or "12")
except Exception:
    STARTUP_SNAPSHOT_SECTION_TIMEOUT_SECONDS = 12.0

JST = timezone(timedelta(hours=9))
STARTUP_SNAPSHOT_SCHEMA_VERSION = "startup_snapshot.v1"
STARTUP_SNAPSHOT_SOURCE_VERSIONS: Dict[str, str] = {
    "schema": STARTUP_SNAPSHOT_SCHEMA_VERSION,
    "friends_unread": "friends.unread.v1",
    "myweb_unread": "report_reads.myweb_unread.v1",
    "notices_current": "notices.current.v1",
    "today_question_light": "today_question.current.light.v1",
    "input_summary": "input.summary.v1",
    "global_summary": "global_summary.ready_first.v1",
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


def _snapshot_cache_key(user_id: str, *, client_meta: Optional[Mapping[str, Any]] = None, timezone_name: Optional[str] = None) -> str:
    uid = str(user_id or "").strip()
    meta = _normalize_client_meta(client_meta)
    return build_cache_key(
        f"startup_snapshot:{uid}",
        {
            "platform": meta.get("platform"),
            "app_version": meta.get("app_version"),
            "app_build": meta.get("app_build"),
            "timezone_name": str(timezone_name or "").strip() or None,
        },
    )


def _refresh_throttle_key(user_id: str, *, client_meta: Optional[Mapping[str, Any]] = None, timezone_name: Optional[str] = None, force_refresh: bool = False) -> str:
    uid = str(user_id or "").strip()
    meta = _normalize_client_meta(client_meta)
    return build_cache_key(
        f"startup_snapshot:refresh:{uid}",
        {
            "platform": meta.get("platform"),
            "app_version": meta.get("app_version"),
            "app_build": meta.get("app_build"),
            "timezone_name": str(timezone_name or "").strip() or None,
            "force_refresh": bool(force_refresh),
        },
    )


async def _safe_section(name: str, coro, default: Any) -> tuple[str, Any, Optional[str]]:
    try:
        payload = await asyncio.wait_for(coro, timeout=max(1.0, float(STARTUP_SNAPSHOT_SECTION_TIMEOUT_SECONDS or 0.0)))
        if payload is None:
            return name, default, None
        return name, payload, None
    except Exception as exc:
        logger.warning("startup snapshot section fallback: section=%s err=%r", name, exc)
        return name, default, str(exc)


def _light_today_question_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    question_raw = payload.get("question") if isinstance(payload, Mapping) else None
    question: Optional[Dict[str, Any]] = None
    if isinstance(question_raw, Mapping):
        question = {
            "question_id": str(question_raw.get("question_id") or "").strip() or None,
            "question_key": str(question_raw.get("question_key") or "").strip() or None,
            "version": int(question_raw.get("version") or 1),
            "text": str(question_raw.get("text") or "").strip() or None,
            "choice_count": int(question_raw.get("choice_count") or 0),
            "free_text_enabled": bool(question_raw.get("free_text_enabled", True)),
        }
    return {
        "service_day_key": str(payload.get("service_day_key") or _today_jst_date_iso()),
        "answer_status": str(payload.get("answer_status") or "unanswered"),
        "answer_summary": payload.get("answer_summary") if isinstance(payload.get("answer_summary"), Mapping) else None,
        "question": question,
        "delivery": payload.get("delivery") if isinstance(payload.get("delivery"), Mapping) else {},
        "progress": payload.get("progress") if isinstance(payload.get("progress"), Mapping) else {},
    }


async def _build_startup_snapshot_payload(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        return {
            "schema_version": STARTUP_SNAPSHOT_SCHEMA_VERSION,
            "user_id": "",
            "client_meta": _normalize_client_meta(client_meta),
            "generated_at": _iso_utc(),
            "source_versions": dict(STARTUP_SNAPSHOT_SOURCE_VERSIONS),
            "sections": {},
            "errors": {"user_id": "missing"},
        }

    # Lazy imports keep startup light and avoid circular imports during app boot.
    from api_friends import get_friend_unread_status_payload_for_user
    from api_global_summary import get_global_summary_payload
    from api_input_summary import get_input_summary_payload_for_user
    from api_notice import get_notice_current_payload_for_user
    from api_report_reads import get_myweb_unread_status_payload_for_user
    from api_today_question import get_today_question_current_payload_for_user

    normalized_meta = _normalize_client_meta(client_meta)

    defaults: Dict[str, Any] = {
        "friends_unread": {
            "status": "ok",
            "feed_unread": False,
            "requests_unread": False,
            "incoming_pending_count": 0,
            "feed_last_read_at": None,
            "requests_last_read_at": None,
        },
        "myweb_unread": {
            "status": "ok",
            "viewer_tier": "free",
            "ids_by_type": {
                "daily": [],
                "weekly": [],
                "monthly": [],
                "selfStructure": [],
            },
            "read_ids": [],
            "unread_by_type": {
                "daily": False,
                "weekly": False,
                "monthly": False,
                "selfStructure": False,
            },
        },
        "notices_current": {
            "feature_enabled": True,
            "unread_count": 0,
            "has_unread": False,
            "badge": {"show": False, "count": 0},
            "popup_notice": None,
        },
        "today_question": {
            "service_day_key": _today_jst_date_iso(),
            "answer_status": "unanswered",
            "answer_summary": None,
            "question": None,
            "delivery": {},
            "progress": {},
        },
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
    }

    section_results = await asyncio.gather(
        _safe_section("friends_unread", get_friend_unread_status_payload_for_user(uid), defaults["friends_unread"]),
        _safe_section(
            "myweb_unread",
            get_myweb_unread_status_payload_for_user(uid, limit=1, include_self_structure=True),
            defaults["myweb_unread"],
        ),
        _safe_section("notices_current", get_notice_current_payload_for_user(uid, normalized_meta), defaults["notices_current"]),
        _safe_section(
            "today_question",
            get_today_question_current_payload_for_user(uid, timezone_name=timezone_name),
            defaults["today_question"],
        ),
        _safe_section("input_summary", get_input_summary_payload_for_user(uid), defaults["input_summary"]),
        _safe_section("global_summary", get_global_summary_payload(), defaults["global_summary"]),
    )

    sections: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    for name, payload, error in section_results:
        if name == "today_question":
            payload = _light_today_question_payload(payload if isinstance(payload, Mapping) else defaults[name])
        sections[name] = payload
        if error:
            errors[name] = error

    friends_unread = sections.get("friends_unread") if isinstance(sections.get("friends_unread"), Mapping) else {}
    myweb_unread = sections.get("myweb_unread") if isinstance(sections.get("myweb_unread"), Mapping) else {}
    notices_current = sections.get("notices_current") if isinstance(sections.get("notices_current"), Mapping) else {}
    today_question = sections.get("today_question") if isinstance(sections.get("today_question"), Mapping) else {}

    unread_by_type = myweb_unread.get("unread_by_type") if isinstance(myweb_unread.get("unread_by_type"), Mapping) else {}
    startup_flags = {
        "has_any_friends_unread": bool(friends_unread.get("feed_unread") or friends_unread.get("requests_unread")),
        "has_any_myweb_unread": any(bool(unread_by_type.get(k)) for k in ("daily", "weekly", "monthly", "selfStructure")),
        "has_popup_notice": bool(notices_current.get("popup_notice")),
        "today_question_answered": str(today_question.get("answer_status") or "unanswered") == "answered",
    }

    payload = {
        "schema_version": STARTUP_SNAPSHOT_SCHEMA_VERSION,
        "user_id": uid,
        "client_meta": normalized_meta,
        "generated_at": _iso_utc(),
        "source_versions": dict(STARTUP_SNAPSHOT_SOURCE_VERSIONS),
        "flags": startup_flags,
        "sections": sections,
        "errors": errors,
    }
    return payload


async def get_startup_snapshot(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not STARTUP_SNAPSHOT_ENABLED or not uid:
        return await _build_startup_snapshot_payload(uid, client_meta=client_meta, timezone_name=timezone_name)

    cache_key = _snapshot_cache_key(uid, client_meta=client_meta, timezone_name=timezone_name)
    if force_refresh:
        try:
            await invalidate_exact(cache_key)
        except Exception:
            logger.exception("startup snapshot exact invalidate failed")

    async def _producer() -> Dict[str, Any]:
        return await _build_startup_snapshot_payload(uid, client_meta=client_meta, timezone_name=timezone_name)

    return await get_or_compute(cache_key, STARTUP_SNAPSHOT_CACHE_TTL_SECONDS, _producer)


async def refresh_startup_snapshot_if_due(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
    reason: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    if not STARTUP_SNAPSHOT_ENABLED or not uid:
        return {}

    throttle_key = _refresh_throttle_key(
        uid,
        client_meta=client_meta,
        timezone_name=timezone_name,
        force_refresh=force_refresh,
    )

    async def _producer() -> Dict[str, Any]:
        snapshot = await get_startup_snapshot(
            uid,
            client_meta=client_meta,
            timezone_name=timezone_name,
            force_refresh=force_refresh,
        )
        return {
            "status": "ok",
            "reason": str(reason or "middleware"),
            "generated_at": str(snapshot.get("generated_at") or _iso_utc()),
        }

    return await get_or_compute(throttle_key, STARTUP_SNAPSHOT_REFRESH_THROTTLE_SECONDS, _producer)


async def invalidate_startup_snapshot(user_id: str) -> int:
    uid = str(user_id or "").strip()
    if not uid:
        return 0
    return await invalidate_prefix(f"startup_snapshot:{uid}")


def schedule_startup_snapshot_refresh(
    user_id: str,
    *,
    client_meta: Optional[Mapping[str, Any]] = None,
    timezone_name: Optional[str] = None,
    reason: Optional[str] = None,
    force_refresh: bool = False,
) -> bool:
    uid = str(user_id or "").strip()
    if not STARTUP_SNAPSHOT_ENABLED or not uid:
        return False
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return False
    try:
        loop.create_task(
            refresh_startup_snapshot_if_due(
                uid,
                client_meta=client_meta,
                timezone_name=timezone_name,
                reason=reason,
                force_refresh=force_refresh,
            )
        )
        return True
    except Exception:
        logger.exception("startup snapshot schedule failed")
        return False


__all__ = [
    "STARTUP_SNAPSHOT_ENABLED",
    "STARTUP_SNAPSHOT_SCHEMA_VERSION",
    "get_startup_snapshot",
    "refresh_startup_snapshot_if_due",
    "invalidate_startup_snapshot",
    "schedule_startup_snapshot_refresh",
]
