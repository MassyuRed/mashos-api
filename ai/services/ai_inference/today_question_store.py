# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Mapping, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from response_microcache import get_or_compute, invalidate_prefix
from supabase_client import ensure_supabase_config, sb_get, sb_patch, sb_post
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user
from today_question_personal_candidate_service import (
    build_best_personal_today_question_candidate,
    list_recent_emotion_inputs_for_personal_today_question,
)
from today_question_personal_question_service import build_personal_question_insert_payload
from today_question_personal_templates import (
    QUESTION_ORIGIN_PERSONAL,
    QUESTION_ORIGIN_STATIC,
    build_source_hash,
    source_anchor_hash as build_source_anchor_hash,
)

logger = logging.getLogger("today_question_store")

TODAY_QUESTION_BANK_TABLE = (os.getenv("TODAY_QUESTION_BANK_TABLE") or "today_question_bank").strip() or "today_question_bank"
TODAY_QUESTION_CHOICES_TABLE = (os.getenv("TODAY_QUESTION_CHOICES_TABLE") or "today_question_choices").strip() or "today_question_choices"
TODAY_QUESTION_SCHEDULE_TABLE = (os.getenv("TODAY_QUESTION_SCHEDULE_TABLE") or "today_question_schedule").strip() or "today_question_schedule"
TODAY_QUESTION_SEQUENCE_TABLE = (os.getenv("TODAY_QUESTION_SEQUENCE_TABLE") or "today_question_sequence").strip() or "today_question_sequence"
TODAY_QUESTION_SETTINGS_TABLE = (os.getenv("TODAY_QUESTION_SETTINGS_TABLE") or "today_question_user_settings").strip() or "today_question_user_settings"
TODAY_QUESTION_PROGRESS_TABLE = (os.getenv("TODAY_QUESTION_PROGRESS_TABLE") or "today_question_user_progress").strip() or "today_question_user_progress"
TODAY_QUESTION_ANSWERS_TABLE = (os.getenv("TODAY_QUESTION_ANSWERS_TABLE") or "today_question_answers").strip() or "today_question_answers"
TODAY_QUESTION_REVISIONS_TABLE = (os.getenv("TODAY_QUESTION_REVISIONS_TABLE") or "today_question_answer_revisions").strip() or "today_question_answer_revisions"
TODAY_QUESTION_PUSH_DELIVERIES_TABLE = (os.getenv("TODAY_QUESTION_PUSH_DELIVERIES_TABLE") or "today_question_push_deliveries").strip() or "today_question_push_deliveries"
TODAY_QUESTION_PERSONAL_CANDIDATES_TABLE = (os.getenv("TODAY_QUESTION_PERSONAL_CANDIDATES_TABLE") or "today_question_personal_candidates").strip() or "today_question_personal_candidates"
TODAY_QUESTION_PERSONAL_QUESTIONS_TABLE = (os.getenv("TODAY_QUESTION_PERSONAL_QUESTIONS_TABLE") or "today_question_personal_questions").strip() or "today_question_personal_questions"
ACTIVE_USERS_TABLE = (os.getenv("COCOLON_ACTIVE_USERS_TABLE") or "active_users").strip() or "active_users"
TODAY_QUESTION_DEFAULT_TIMEZONE = (os.getenv("TODAY_QUESTION_DEFAULT_TIMEZONE") or "Asia/Tokyo").strip() or "Asia/Tokyo"
TODAY_QUESTION_SERVICE_DAY_TIMEZONE = (os.getenv("TODAY_QUESTION_SERVICE_DAY_TIMEZONE") or "Asia/Tokyo").strip() or "Asia/Tokyo"
TODAY_QUESTION_DEFAULT_DELIVERY_TIME = (os.getenv("TODAY_QUESTION_DEFAULT_DELIVERY_TIME") or "18:00").strip() or "18:00"
TODAY_QUESTION_DEFAULT_NOTIFICATION_ENABLED = (os.getenv("TODAY_QUESTION_DEFAULT_NOTIFICATION_ENABLED") or "true").strip().lower() in ("1", "true", "yes", "on")
TODAY_QUESTION_MAX_HISTORY_LIMIT = int(os.getenv("TODAY_QUESTION_MAX_HISTORY_LIMIT", "100") or "100")
TODAY_QUESTION_PUSH_SCAN_LIMIT = int(os.getenv("TODAY_QUESTION_PUSH_SCAN_LIMIT", "1000") or "1000")
TODAY_QUESTION_SEQUENCE_FETCH_LIMIT = int(os.getenv("TODAY_QUESTION_SEQUENCE_FETCH_LIMIT", "5000") or "5000")
TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS = float(os.getenv("TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS", "300") or "300")
TODAY_QUESTION_SETTINGS_CACHE_TTL_SECONDS = float(os.getenv("TODAY_QUESTION_SETTINGS_CACHE_TTL_SECONDS", "30") or "30")
TODAY_QUESTION_PROGRESS_CACHE_TTL_SECONDS = float(os.getenv("TODAY_QUESTION_PROGRESS_CACHE_TTL_SECONDS", "10") or "10")
TODAY_QUESTION_ANSWER_CACHE_TTL_SECONDS = float(os.getenv("TODAY_QUESTION_ANSWER_CACHE_TTL_SECONDS", "10") or "10")
TODAY_QUESTION_HISTORY_SCAN_CACHE_TTL_SECONDS = float(os.getenv("TODAY_QUESTION_HISTORY_SCAN_CACHE_TTL_SECONDS", "20") or "20")
TODAY_QUESTION_PERSONAL_FOLLOWUP_ENABLED = (os.getenv("TODAY_QUESTION_PERSONAL_FOLLOWUP_ENABLED") or "true").strip().lower() in ("1", "true", "yes", "on")
TODAY_QUESTION_PERSONAL_MIN_SCORE = int(os.getenv("TODAY_QUESTION_PERSONAL_MIN_SCORE", "72") or "72")
TODAY_QUESTION_PERSONAL_STATIC_FALLBACK_EVERY_N_DAYS = int(os.getenv("TODAY_QUESTION_PERSONAL_STATIC_FALLBACK_EVERY_N_DAYS", "4") or "4")

_HHMM_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


@dataclass
class TodayQuestionCurrentBundle:
    service_day_key: str
    question: Optional[Dict[str, Any]]
    answer: Optional[Dict[str, Any]]
    settings: Dict[str, Any]
    progress: Dict[str, Any]
    release_status: str = "released"
    release_time_local: Optional[str] = None
    question_origin: str = QUESTION_ORIGIN_STATIC
    personal_question_id: Optional[str] = None
    source_anchor: Optional[Dict[str, Any]] = None
    question_type: Optional[str] = None


@dataclass
class TodayQuestionStatusBundle:
    service_day_key: str
    question: Optional[Dict[str, Any]]
    answer: Optional[Dict[str, Any]]
    settings: Dict[str, Any]
    progress: Dict[str, Any]
    release_status: str = "released"
    release_time_local: Optional[str] = None
    question_origin: str = QUESTION_ORIGIN_STATIC
    personal_question_id: Optional[str] = None
    source_anchor: Optional[Dict[str, Any]] = None
    question_type: Optional[str] = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(dt: Optional[datetime] = None) -> str:
    return (dt or _now_utc()).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_timezone_name(raw: Any) -> str:
    s = str(raw or "").strip() or TODAY_QUESTION_DEFAULT_TIMEZONE
    try:
        ZoneInfo(s)
        return s
    except Exception:
        return TODAY_QUESTION_DEFAULT_TIMEZONE


def _normalize_delivery_time_local(raw: Any) -> str:
    s = str(raw or "").strip() or TODAY_QUESTION_DEFAULT_DELIVERY_TIME
    return s if _HHMM_RE.match(s) else TODAY_QUESTION_DEFAULT_DELIVERY_TIME


def _zoneinfo(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(_normalize_timezone_name(name))
    except Exception:
        return ZoneInfo(TODAY_QUESTION_DEFAULT_TIMEZONE)


def _local_day_key(now_utc: Optional[datetime], timezone_name: str) -> str:
    dt = (now_utc or _now_utc()).astimezone(_zoneinfo(timezone_name))
    return dt.date().isoformat()


def _service_day_key(now_utc: Optional[datetime]) -> str:
    return _local_day_key(now_utc, TODAY_QUESTION_SERVICE_DAY_TIMEZONE)


def _local_hhmm(now_utc: Optional[datetime], timezone_name: str) -> str:
    dt = (now_utc or _now_utc()).astimezone(_zoneinfo(timezone_name))
    return dt.strftime("%H:%M")


def _local_minutes_since_midnight(now_utc: Optional[datetime], timezone_name: str) -> int:
    dt = (now_utc or _now_utc()).astimezone(_zoneinfo(timezone_name))
    return int(dt.hour) * 60 + int(dt.minute)


def _delivery_time_minutes(delivery_time_local: Any) -> int:
    hhmm = _normalize_delivery_time_local(delivery_time_local)
    try:
        hh_str, mm_str = hhmm.split(":", 1)
        return int(hh_str) * 60 + int(mm_str)
    except Exception:
        fallback_hh, fallback_mm = TODAY_QUESTION_DEFAULT_DELIVERY_TIME.split(":", 1)
        return int(fallback_hh) * 60 + int(fallback_mm)


def _is_delivery_time_due(now_utc: Optional[datetime], timezone_name: str, delivery_time_local: Any) -> bool:
    return _local_minutes_since_midnight(now_utc, timezone_name) >= _delivery_time_minutes(delivery_time_local)


def _is_today_question_released_for_settings(now_utc: Optional[datetime], settings: Mapping[str, Any]) -> bool:
    """Return True only after the user's configured Today Question delivery time.

    The service day still switches at the global service-day boundary, but the
    question body itself must stay hidden until the user's notification time so
    users cannot answer it before the push window.
    """
    settings_map = settings if isinstance(settings, Mapping) else {}
    return _is_delivery_time_due(
        now_utc,
        _normalize_timezone_name(settings_map.get("timezone_name")),
        _normalize_delivery_time_local(settings_map.get("delivery_time_local")),
    )


def _hidden_until_delivery_progress(*, total_count: int, progress_row: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Build a non-mutating progress payload while the question is hidden."""
    row = progress_row if isinstance(progress_row, Mapping) else {}
    return _progress_public(
        sequence_no=_safe_int(row.get("current_sequence_no"), 0) or None,
        total_count=max(_safe_int(total_count, 0), 0),
        current_presented_local_date=str(row.get("current_presented_local_date") or "").strip() or None,
    )


def _delivery_time_from_settings(settings: Mapping[str, Any]) -> str:
    settings_map = settings if isinstance(settings, Mapping) else {}
    return _normalize_delivery_time_local(settings_map.get("delivery_time_local"))


def _hidden_release_time_from_settings(settings: Mapping[str, Any]) -> str:
    return _delivery_time_from_settings(settings)


def _parse_jsonish(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        try:
            return json.loads(s)
        except Exception:
            return default
    return default


def _in_filter(ids: List[str]) -> str:
    quoted = []
    for raw in ids or []:
        s = str(raw or "").strip()
        if not s:
            continue
        quoted.append('"' + s.replace('"', '') + '"')
    return f"in.({','.join(quoted)})"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _today_question_settings_cache_prefix(user_id: str) -> str:
    return f"today_question:user_settings:{str(user_id or '').strip()}"


def _today_question_progress_cache_prefix(user_id: str) -> str:
    return f"today_question:user_progress:{str(user_id or '').strip()}"


def _today_question_answer_day_cache_prefix(user_id: str) -> str:
    return f"today_question:answer_day:{str(user_id or '').strip()}"


def _today_question_answer_sequence_cache_prefix(user_id: str) -> str:
    return f"today_question:answer_sequence:{str(user_id or '').strip()}"


def _today_question_answer_scan_cache_prefix(user_id: str) -> str:
    return f"today_question:answer_scan:{str(user_id or '').strip()}"


async def invalidate_today_question_user_runtime_cache(user_id: str) -> None:
    uid = str(user_id or "").strip()
    if not uid:
        return
    await invalidate_prefix(_today_question_settings_cache_prefix(uid))
    await invalidate_prefix(_today_question_progress_cache_prefix(uid))
    await invalidate_prefix(_today_question_answer_day_cache_prefix(uid))
    await invalidate_prefix(_today_question_answer_sequence_cache_prefix(uid))
    await invalidate_prefix(_today_question_answer_scan_cache_prefix(uid))


def _raise_http_from_supabase(resp, default_detail: str) -> None:
    detail = default_detail
    try:
        js = resp.json()
        if isinstance(js, dict):
            detail = str(js.get("message") or js.get("hint") or js.get("details") or js.get("detail") or default_detail)
        elif js:
            detail = str(js)
    except Exception:
        txt = (getattr(resp, "text", "") or "").strip()
        if txt:
            detail = txt[:500]
    raise HTTPException(status_code=502, detail=detail)


def _hidden_meta_from_choice_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    meta = _parse_jsonish(row.get("hidden_meta_json"), {})
    if not isinstance(meta, dict):
        meta = {}
    analysis_tags = meta.get("analysis_tags")
    if not isinstance(analysis_tags, list):
        analysis_tags = []
    return {
        "role_hint": meta.get("role_hint"),
        "target_hint": meta.get("target_hint"),
        "world_kind_hint": meta.get("world_kind_hint"),
        "analysis_tags": analysis_tags,
    }


def _choice_snapshot(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "choice_id": str(row.get("id") or ""),
        "choice_key": str(row.get("choice_key") or ""),
        "label": str(row.get("choice_label") or ""),
        "sort_order": int(row.get("sort_order") or 0),
        "hidden_meta": _hidden_meta_from_choice_row(row),
    }


def _choice_public(row: Mapping[str, Any]) -> Dict[str, Any]:
    snap = _choice_snapshot(row)
    return {
        "choice_id": snap["choice_id"],
        "choice_key": snap["choice_key"],
        "label": snap["label"],
    }


def _choice_public_from_snapshot(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "choice_id": str(row.get("choice_id") or row.get("id") or ""),
        "choice_key": str(row.get("choice_key") or "") or None,
        "label": str(row.get("label") or row.get("choice_label") or ""),
    }


def _answer_summary(answer_row: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(answer_row, Mapping):
        return None
    mode = str(answer_row.get("answer_mode") or "").strip()
    if mode == "choice":
        label = str(answer_row.get("selected_choice_label_snapshot") or answer_row.get("selected_choice_label") or "").strip()
        if not label:
            label = str(answer_row.get("selected_choice_key") or "").strip()
        return {
            "answer_mode": "choice",
            "label": label or None,
            "text": str(answer_row.get("free_text") or "").strip() or None,
        }
    text = str(answer_row.get("free_text") or "").strip()
    return {
        "answer_mode": "free_text",
        "label": None,
        "text": text or None,
    }


def _settings_public(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "notification_enabled": bool(row.get("notification_enabled", TODAY_QUESTION_DEFAULT_NOTIFICATION_ENABLED)),
        "delivery_time_local": _normalize_delivery_time_local(row.get("delivery_time_local")),
        "timezone_name": _normalize_timezone_name(row.get("timezone_name")),
    }


def _question_origin_from_row(row: Mapping[str, Any]) -> str:
    origin = str(row.get("question_origin") or "").strip()
    if origin in (QUESTION_ORIGIN_STATIC, QUESTION_ORIGIN_PERSONAL):
        return origin
    return QUESTION_ORIGIN_PERSONAL if str(row.get("personal_question_id") or "").strip() else QUESTION_ORIGIN_STATIC


def _source_anchor_public(value: Any) -> Optional[Dict[str, Any]]:
    raw = _parse_jsonish(value, {})
    if not isinstance(raw, Mapping):
        return None
    anchor_text = str(raw.get("anchor_text") or "").strip()
    source_id = str(raw.get("source_id") or "").strip()
    source_field = str(raw.get("source_field") or "").strip()
    question_type = str(raw.get("question_type") or "").strip()
    if not anchor_text or not source_id or not source_field:
        return None
    return {
        "source_type": str(raw.get("source_type") or "emotion_input").strip() or "emotion_input",
        "source_id": source_id,
        "source_field": source_field,
        "anchor_text": anchor_text,
        "anchor_start": raw.get("anchor_start"),
        "anchor_end": raw.get("anchor_end"),
        "question_type": question_type or None,
        "source_hash": str(raw.get("source_hash") or "").strip() or None,
    }


def _source_anchor_public_from_answer_row(row: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    from_snapshot = _source_anchor_public(row.get("source_anchor_snapshot_json"))
    if from_snapshot:
        return from_snapshot
    anchor_text = str(row.get("anchor_text") or "").strip()
    source_id = str(row.get("source_id") or "").strip()
    source_field = str(row.get("source_field") or "").strip()
    question_type = str(row.get("question_type") or "").strip()
    if not anchor_text or not source_id or not source_field:
        return None
    return {
        "source_type": str(row.get("source_type") or "emotion_input").strip() or "emotion_input",
        "source_id": source_id,
        "source_field": source_field,
        "anchor_text": anchor_text,
        "anchor_start": None,
        "anchor_end": None,
        "question_type": question_type or None,
        "source_hash": build_source_hash(
            source_id=source_id,
            source_field=source_field,
            anchor_text=anchor_text,
            question_type=question_type,
        ),
    }


def _source_anchor_summary(source_anchor: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(source_anchor, Mapping):
        return None
    anchor_text = str(source_anchor.get("anchor_text") or "").strip()
    if not anchor_text:
        return None
    return {
        "source_type": str(source_anchor.get("source_type") or "emotion_input").strip() or "emotion_input",
        "source_field": str(source_anchor.get("source_field") or "").strip() or None,
        "anchor_text": anchor_text,
        "question_type": str(source_anchor.get("question_type") or "").strip() or None,
    }


def _question_public(question_row: Mapping[str, Any], choice_rows: List[Mapping[str, Any]]) -> Dict[str, Any]:
    choices_sorted = sorted(choice_rows or [], key=lambda x: int(x.get("sort_order") or 0))
    choice_count = int(question_row.get("choice_count") or len(choices_sorted) or 0)
    return {
        "question_id": str(question_row.get("id") or ""),
        "question_key": str(question_row.get("question_key") or ""),
        "version": int(question_row.get("version") or 1),
        "text": str(question_row.get("question_text") or "").strip(),
        "choice_count": choice_count,
        "choices": [_choice_public(r) for r in choices_sorted],
        "free_text_enabled": bool(question_row.get("free_text_enabled", True)),
        "optional_free_text_enabled": False,
        "question_origin": QUESTION_ORIGIN_STATIC,
    }


def _question_public_from_personal_row(question_row: Mapping[str, Any]) -> Dict[str, Any]:
    raw_choices = _parse_jsonish(question_row.get("choices_snapshot_json"), [])
    if not isinstance(raw_choices, list):
        raw_choices = []
    choices_sorted = sorted(
        [r for r in raw_choices if isinstance(r, Mapping)],
        key=lambda x: _safe_int(x.get("sort_order"), 0),
    )
    qid = str(question_row.get("id") or "").strip()
    qtype = str(question_row.get("question_type") or "").strip()
    return {
        "question_id": qid,
        "question_key": f"personal_{qtype}" if qtype else "personal_followup",
        "version": 1,
        "text": str(question_row.get("question_text") or "").strip(),
        "choice_count": len(choices_sorted),
        "choices": [_choice_public_from_snapshot(r) for r in choices_sorted],
        "free_text_enabled": True,
        "optional_free_text_enabled": True,
        "question_origin": QUESTION_ORIGIN_PERSONAL,
        "personal_question_id": qid or None,
        "question_type": qtype or None,
        "source_anchor": _source_anchor_public(question_row.get("source_anchor_json")),
    }


def _question_public_from_answer_row(answer_row: Mapping[str, Any]) -> Dict[str, Any]:
    raw_choices = _parse_jsonish(answer_row.get("choices_snapshot_json"), [])
    if not isinstance(raw_choices, list):
        raw_choices = []
    choices_sorted = sorted(
        [r for r in raw_choices if isinstance(r, Mapping)],
        key=lambda x: _safe_int(x.get("sort_order"), 0),
    )
    origin = _question_origin_from_row(answer_row)
    personal_question_id = str(answer_row.get("personal_question_id") or "").strip() or None
    question_id = str(answer_row.get("question_id") or "").strip() or personal_question_id or ""
    source_anchor = _source_anchor_public_from_answer_row(answer_row)
    return {
        "question_id": question_id,
        "question_key": str(answer_row.get("question_key") or ""),
        "version": int(answer_row.get("question_version") or 1),
        "text": str(answer_row.get("question_text_snapshot") or "").strip(),
        "choice_count": len(choices_sorted),
        "choices": [_choice_public_from_snapshot(r) for r in choices_sorted],
        "free_text_enabled": True,
        "optional_free_text_enabled": origin == QUESTION_ORIGIN_PERSONAL,
        "question_origin": origin,
        "personal_question_id": personal_question_id,
        "question_type": str(answer_row.get("question_type") or "").strip() or None,
        "source_anchor": source_anchor,
    }


def _question_status_public(question_row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "question_id": str(question_row.get("id") or question_row.get("question_id") or ""),
        "question_key": str(question_row.get("question_key") or "") or None,
        "version": int(question_row.get("version") or question_row.get("question_version") or 1),
        "choice_count": int(question_row.get("choice_count") or 0),
        "free_text_enabled": bool(question_row.get("free_text_enabled", True)),
        "optional_free_text_enabled": False,
        "question_origin": QUESTION_ORIGIN_STATIC,
    }


def _question_status_public_from_personal_row(question_row: Mapping[str, Any]) -> Dict[str, Any]:
    raw_choices = _parse_jsonish(question_row.get("choices_snapshot_json"), [])
    if not isinstance(raw_choices, list):
        raw_choices = []
    qid = str(question_row.get("id") or "").strip()
    qtype = str(question_row.get("question_type") or "").strip()
    return {
        "question_id": qid,
        "question_key": f"personal_{qtype}" if qtype else "personal_followup",
        "version": 1,
        "choice_count": len([r for r in raw_choices if isinstance(r, Mapping)]),
        "free_text_enabled": True,
        "optional_free_text_enabled": True,
        "question_origin": QUESTION_ORIGIN_PERSONAL,
        "personal_question_id": qid or None,
        "question_type": qtype or None,
        "source_anchor": _source_anchor_public(question_row.get("source_anchor_json")),
    }


def _question_status_public_from_answer_row(answer_row: Mapping[str, Any]) -> Dict[str, Any]:
    origin = _question_origin_from_row(answer_row)
    personal_question_id = str(answer_row.get("personal_question_id") or "").strip() or None
    question_id = str(answer_row.get("question_id") or "").strip() or personal_question_id or ""
    return {
        "question_id": question_id,
        "question_key": str(answer_row.get("question_key") or "") or None,
        "version": int(answer_row.get("question_version") or 1),
        "choice_count": int(answer_row.get("choice_count") or 0),
        "free_text_enabled": bool(answer_row.get("free_text_enabled", True)),
        "optional_free_text_enabled": origin == QUESTION_ORIGIN_PERSONAL,
        "question_origin": origin,
        "personal_question_id": personal_question_id,
        "question_type": str(answer_row.get("question_type") or "").strip() or None,
        "source_anchor": _source_anchor_public_from_answer_row(answer_row),
    }


def _progress_public(
    *,
    sequence_no: Optional[int],
    total_count: int,
    current_presented_local_date: Optional[str],
) -> Dict[str, Any]:
    seq = _safe_int(sequence_no, 0) or None
    total = max(_safe_int(total_count, 0), 0)
    presented = str(current_presented_local_date or "").strip() or None
    return {
        "sequence_no": seq,
        "total_count": total,
        "current_presented_local_date": presented,
        "mode": "user_sequence_v1",
    }


def _history_item_public(row: Mapping[str, Any]) -> Dict[str, Any]:
    choices_snapshot = _parse_jsonish(row.get("choices_snapshot_json"), [])
    if not isinstance(choices_snapshot, list):
        choices_snapshot = []
    origin = _question_origin_from_row(row)
    personal_question_id = str(row.get("personal_question_id") or "").strip() or None
    source_anchor = _source_anchor_public_from_answer_row(row)
    return {
        "answer_id": str(row.get("id") or ""),
        "service_day_key": str(row.get("service_day_key") or ""),
        "sequence_no": _safe_int(row.get("sequence_no"), 0) or None,
        "question_id": str(row.get("question_id") or "").strip() or personal_question_id or "",
        "question_key": str(row.get("question_key") or ""),
        "question_version": int(row.get("question_version") or 1),
        "question_text": str(row.get("question_text_snapshot") or "").strip(),
        "answer_mode": str(row.get("answer_mode") or ""),
        "selected_choice_id": str(row.get("selected_choice_id") or "") or None,
        "selected_choice_key": str(row.get("selected_choice_key") or "") or None,
        "selected_choice_label": str(row.get("selected_choice_label_snapshot") or "") or None,
        "free_text": str(row.get("free_text") or "") or None,
        "choices": choices_snapshot,
        "answered_at": str(row.get("answered_at") or row.get("created_at") or "") or None,
        "edited_at": str(row.get("edited_at") or "") or None,
        "edit_count": int(row.get("edit_count") or 0),
        "question_origin": origin,
        "personal_question_id": personal_question_id,
        "question_type": str(row.get("question_type") or "").strip() or None,
        "source_anchor_summary": _source_anchor_summary(source_anchor),
    }


class TodayQuestionStore:
    async def _select_rows(self, table: str, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
        ensure_supabase_config()
        resp = await sb_get(f"/rest/v1/{table}", params=params, timeout=10.0)
        if resp.status_code not in (200, 206):
            _raise_http_from_supabase(resp, f"Failed to query {table}")
        data = resp.json()
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    async def _insert_rows(self, table: str, *, json_body: Any, prefer: str = "return=representation") -> List[Dict[str, Any]]:
        ensure_supabase_config()
        resp = await sb_post(f"/rest/v1/{table}", json=json_body, prefer=prefer, timeout=10.0)
        if resp.status_code >= 300:
            if resp.status_code == 409:
                raise HTTPException(status_code=409, detail="Already exists")
            _raise_http_from_supabase(resp, f"Failed to insert {table}")
        if resp.status_code == 204:
            return []
        text = (getattr(resp, "text", "") or "").strip()
        if not text:
            return []
        data = resp.json()
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    async def _patch_rows(self, table: str, *, params: Dict[str, str], json_body: Any, prefer: str = "return=representation") -> List[Dict[str, Any]]:
        ensure_supabase_config()
        resp = await sb_patch(f"/rest/v1/{table}", params=params, json=json_body, prefer=prefer, timeout=10.0)
        if resp.status_code >= 300:
            _raise_http_from_supabase(resp, f"Failed to patch {table}")
        if resp.status_code == 204:
            return []
        data = resp.json()
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    async def get_or_create_user_settings(self, user_id: str, *, timezone_name: Optional[str] = None) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=401, detail="Unauthorized")

        cache_key = f"{_today_question_settings_cache_prefix(uid)}:{str(timezone_name or '').strip() or 'default'}"

        async def _producer() -> Dict[str, Any]:
            rows = await self._select_rows(
                TODAY_QUESTION_SETTINGS_TABLE,
                params={
                    "select": "notification_enabled,delivery_time_local,timezone_name",
                    "user_id": f"eq.{uid}",
                    "limit": "1",
                },
            )
            if rows:
                return _settings_public(rows[0])

            created = {
                "user_id": uid,
                "notification_enabled": TODAY_QUESTION_DEFAULT_NOTIFICATION_ENABLED,
                "delivery_time_local": TODAY_QUESTION_DEFAULT_DELIVERY_TIME,
                "timezone_name": _normalize_timezone_name(timezone_name),
            }
            rows = await self._insert_rows(
                TODAY_QUESTION_SETTINGS_TABLE,
                json_body=created,
                prefer="resolution=merge-duplicates,return=representation",
            )
            return _settings_public(rows[0] if rows else created)

        return await get_or_compute(cache_key, TODAY_QUESTION_SETTINGS_CACHE_TTL_SECONDS, _producer)

    async def patch_user_settings(
        self,
        user_id: str,
        *,
        notification_enabled: Optional[bool] = None,
        delivery_time_local: Optional[str] = None,
        timezone_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        current = await self.get_or_create_user_settings(uid, timezone_name=timezone_name)
        body = {
            "user_id": uid,
            "notification_enabled": current["notification_enabled"] if notification_enabled is None else bool(notification_enabled),
            "delivery_time_local": current["delivery_time_local"] if delivery_time_local is None else _normalize_delivery_time_local(delivery_time_local),
            "timezone_name": current["timezone_name"] if timezone_name is None else _normalize_timezone_name(timezone_name),
            "updated_at": _iso_utc(),
        }
        rows = await self._insert_rows(
            TODAY_QUESTION_SETTINGS_TABLE,
            json_body=body,
            prefer="resolution=merge-duplicates,return=representation",
        )
        await invalidate_today_question_user_runtime_cache(uid)
        return _settings_public(rows[0] if rows else body)

    async def _fetch_schedule_row(self, service_day_key: str) -> Optional[Dict[str, Any]]:
        rows = await self._select_rows(
            TODAY_QUESTION_SCHEDULE_TABLE,
            params={
                "select": "*",
                "service_day_key": f"eq.{service_day_key}",
                "order": "published_at_utc.desc",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    async def _fetch_sequence_rows(self, *, limit: int = TODAY_QUESTION_SEQUENCE_FETCH_LIMIT) -> List[Dict[str, Any]]:
        lim = max(1, min(int(limit or TODAY_QUESTION_SEQUENCE_FETCH_LIMIT), TODAY_QUESTION_SEQUENCE_FETCH_LIMIT))
        cache_key = f"today_question:static:sequence_rows:{lim}"

        async def _producer() -> List[Dict[str, Any]]:
            return await self._select_rows(
                TODAY_QUESTION_SEQUENCE_TABLE,
                params={
                    "select": "id,sequence_no,question_id",
                    "order": "sequence_no.asc",
                    "limit": str(lim),
                },
            )

        return await get_or_compute(cache_key, TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS, _producer)

    async def _fetch_sequence_row(self, sequence_no: int) -> Optional[Dict[str, Any]]:
        seq = _safe_int(sequence_no, 0)
        if seq < 1:
            return None
        cache_key = f"today_question:static:sequence:{seq}"

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_SEQUENCE_TABLE,
                params={
                    "select": "id,sequence_no,question_id",
                    "sequence_no": f"eq.{seq}",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS, _producer)

    async def _fetch_sequence_row_by_id(self, sequence_id: str) -> Optional[Dict[str, Any]]:
        sid = str(sequence_id or "").strip()
        if not sid:
            return None
        rows = await self._select_rows(
            TODAY_QUESTION_SEQUENCE_TABLE,
            params={
                "select": "*",
                "id": f"eq.{sid}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    async def _fetch_total_sequence_count(self) -> int:
        async def _producer() -> int:
            rows = await self._select_rows(
                TODAY_QUESTION_SEQUENCE_TABLE,
                params={
                    "select": "sequence_no",
                    "order": "sequence_no.desc",
                    "limit": "1",
                },
            )
            if not rows:
                return 0
            return max(_safe_int(rows[0].get("sequence_no"), 0), 0)

        return await get_or_compute("today_question:static:sequence_total", TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS, _producer)

    async def _fetch_user_progress_row(self, user_id: str) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        if not uid:
            return None
        cache_key = _today_question_progress_cache_prefix(uid)

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_PROGRESS_TABLE,
                params={
                    "select": "user_id,last_completed_sequence_no,current_sequence_id,current_sequence_no,current_presented_local_date,updated_at",
                    "user_id": f"eq.{uid}",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_PROGRESS_CACHE_TTL_SECONDS, _producer)

    async def _upsert_user_progress(
        self,
        user_id: str,
        *,
        last_completed_sequence_no: int,
        current_sequence_id: Optional[str],
        current_sequence_no: Optional[int],
        current_presented_local_date: Optional[str],
    ) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=401, detail="Unauthorized")
        now_iso = _iso_utc()
        body = {
            "user_id": uid,
            "last_completed_sequence_no": max(_safe_int(last_completed_sequence_no, 0), 0),
            "current_sequence_id": str(current_sequence_id or "").strip() or None,
            "current_sequence_no": (_safe_int(current_sequence_no, 0) or None),
            "current_presented_local_date": str(current_presented_local_date or "").strip() or None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        rows = await self._insert_rows(
            TODAY_QUESTION_PROGRESS_TABLE,
            json_body=body,
            prefer="resolution=merge-duplicates,return=representation",
        )
        await invalidate_prefix(_today_question_progress_cache_prefix(uid))
        return rows[0] if rows else body

    async def _fetch_question_row(self, question_id: str) -> Optional[Dict[str, Any]]:
        qid = str(question_id or "").strip()
        if not qid:
            return None
        cache_key = f"today_question:static:question:{qid}"

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_BANK_TABLE,
                params={
                    "select": "id,question_key,version,question_text,choice_count,free_text_enabled",
                    "id": f"eq.{qid}",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS, _producer)

    async def _fetch_question_meta_row(self, question_id: str) -> Optional[Dict[str, Any]]:
        qid = str(question_id or "").strip()
        if not qid:
            return None
        cache_key = f"today_question:static:question_meta:{qid}"

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_BANK_TABLE,
                params={
                    "select": "id,question_key,version,choice_count,free_text_enabled",
                    "id": f"eq.{qid}",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS, _producer)

    async def _fetch_choice_rows(self, question_id: str) -> List[Dict[str, Any]]:
        qid = str(question_id or "").strip()
        if not qid:
            return []
        cache_key = f"today_question:static:choices:{qid}"

        async def _producer() -> List[Dict[str, Any]]:
            return await self._select_rows(
                TODAY_QUESTION_CHOICES_TABLE,
                params={
                    "select": "id,question_id,choice_key,choice_label,sort_order,hidden_meta_json",
                    "question_id": f"eq.{qid}",
                    "order": "sort_order.asc",
                    "limit": "10",
                },
            )

        return await get_or_compute(cache_key, TODAY_QUESTION_STATIC_CACHE_TTL_SECONDS, _producer)

    async def _fetch_answer_row_for_day(self, user_id: str, service_day_key: str) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        day = str(service_day_key or "").strip()
        if not uid or not day:
            return None
        cache_key = f"{_today_question_answer_day_cache_prefix(uid)}:{day}"

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_ANSWERS_TABLE,
                params={
                    "select": "id,service_day_key,sequence_id,sequence_no,presented_local_date,local_answer_date,question_id,question_key,question_version,question_text_snapshot,choices_snapshot_json,answer_mode,selected_choice_id,selected_choice_key,selected_choice_label_snapshot,free_text,answered_at,created_at,question_origin,personal_question_id,source_type,source_id,source_field,anchor_text,question_type,source_anchor_snapshot_json",
                    "user_id": f"eq.{uid}",
                    "service_day_key": f"eq.{day}",
                    "order": "answered_at.desc,id.desc",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_ANSWER_CACHE_TTL_SECONDS, _producer)

    async def _fetch_answer_status_row_for_day(self, user_id: str, service_day_key: str) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        day = str(service_day_key or "").strip()
        if not uid or not day:
            return None
        cache_key = f"{_today_question_answer_day_cache_prefix(uid)}:{day}:status"

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_ANSWERS_TABLE,
                params={
                    "select": "id,service_day_key,sequence_id,sequence_no,presented_local_date,local_answer_date,question_id,question_key,question_version,answer_mode,selected_choice_id,selected_choice_key,selected_choice_label_snapshot,free_text,answered_at,created_at,question_origin,personal_question_id,source_type,source_id,source_field,anchor_text,question_type,source_anchor_snapshot_json",
                    "user_id": f"eq.{uid}",
                    "service_day_key": f"eq.{day}",
                    "order": "answered_at.desc,id.desc",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_ANSWER_CACHE_TTL_SECONDS, _producer)

    async def _fetch_answer_row_for_sequence(self, user_id: str, sequence_no: int) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        seq = _safe_int(sequence_no, 0)
        if not uid or seq < 1:
            return None
        cache_key = f"{_today_question_answer_sequence_cache_prefix(uid)}:{seq}"

        async def _producer() -> Optional[Dict[str, Any]]:
            rows = await self._select_rows(
                TODAY_QUESTION_ANSWERS_TABLE,
                params={
                    "select": "id,sequence_no,service_day_key,answered_at",
                    "user_id": f"eq.{uid}",
                    "sequence_no": f"eq.{seq}",
                    "order": "answered_at.desc,id.desc",
                    "limit": "1",
                },
            )
            return rows[0] if rows else None

        return await get_or_compute(cache_key, TODAY_QUESTION_ANSWER_CACHE_TTL_SECONDS, _producer)

    async def _fetch_answer_rows_for_user(self, user_id: str, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        if not uid:
            return []
        total_count = await self._fetch_total_sequence_count()
        lim = limit if limit is not None else max(total_count + 20, 500)
        lim = max(1, min(int(lim or 500), TODAY_QUESTION_SEQUENCE_FETCH_LIMIT))
        cache_key = f"{_today_question_answer_scan_cache_prefix(uid)}:{lim}"

        async def _producer() -> List[Dict[str, Any]]:
            return await self._select_rows(
                TODAY_QUESTION_ANSWERS_TABLE,
                params={
                    "select": "sequence_no",
                    "user_id": f"eq.{uid}",
                    "sequence_no": "not.is.null",
                    "order": "sequence_no.asc,answered_at.asc",
                    "limit": str(lim),
                },
            )

        return await get_or_compute(cache_key, TODAY_QUESTION_HISTORY_SCAN_CACHE_TTL_SECONDS, _producer)

    async def _compute_first_unanswered_sequence_no(self, user_id: str) -> Optional[int]:
        sequence_rows = await self._fetch_sequence_rows()
        if not sequence_rows:
            return None
        answer_rows = await self._fetch_answer_rows_for_user(user_id, limit=max(len(sequence_rows) + 20, 500))
        answered_sequence_nos = {
            _safe_int(r.get("sequence_no"), 0)
            for r in answer_rows
            if _safe_int(r.get("sequence_no"), 0) > 0
        }
        for row in sequence_rows:
            seq_no = _safe_int(row.get("sequence_no"), 0)
            if seq_no < 1:
                continue
            if seq_no not in answered_sequence_nos:
                return seq_no
        return None

    async def _resolve_pending_progress(
        self,
        user_id: str,
        *,
        service_day_key: str,
        total_count: Optional[int] = None,
        progress_row: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        total = max(_safe_int(total_count, 0), 0) if total_count is not None else await self._fetch_total_sequence_count()
        progress_row = progress_row or await self._fetch_user_progress_row(user_id)

        desired_sequence_row: Optional[Dict[str, Any]] = None
        desired_sequence_no: Optional[int] = None
        last_completed_sequence_no = max(_safe_int((progress_row or {}).get("last_completed_sequence_no"), 0), 0)
        current_progress_sequence_no = _safe_int((progress_row or {}).get("current_sequence_no"), 0) or None
        current_progress_sequence_id = str((progress_row or {}).get("current_sequence_id") or "").strip() or None
        current_progress_presented_local_date = str((progress_row or {}).get("current_presented_local_date") or "").strip() or None
        presented_local_date: Optional[str] = None

        if total <= 0:
            desired_sequence_row = None
            desired_sequence_no = None
            last_completed_sequence_no = 0
            presented_local_date = None
        else:
            if current_progress_sequence_no and current_progress_sequence_no <= total:
                candidate_row = await self._fetch_sequence_row(current_progress_sequence_no)
                candidate_row_id = str((candidate_row or {}).get("id") or "").strip() or None
                if candidate_row and (not current_progress_sequence_id or current_progress_sequence_id == candidate_row_id):
                    candidate_answer = await self._fetch_answer_row_for_sequence(user_id, current_progress_sequence_no)
                    if not candidate_answer:
                        desired_sequence_row = candidate_row
                        desired_sequence_no = current_progress_sequence_no
                        last_completed_sequence_no = max(desired_sequence_no - 1, 0)
                        presented_local_date = current_progress_presented_local_date or service_day_key

            if desired_sequence_row is None:
                if last_completed_sequence_no >= total:
                    desired_sequence_row = None
                    desired_sequence_no = None
                    last_completed_sequence_no = total
                    presented_local_date = None
                else:
                    next_sequence_no = max(last_completed_sequence_no, 0) + 1
                    if next_sequence_no <= total:
                        next_sequence_answer = await self._fetch_answer_row_for_sequence(user_id, next_sequence_no)
                        if not next_sequence_answer:
                            candidate_row = await self._fetch_sequence_row(next_sequence_no)
                            if candidate_row:
                                desired_sequence_row = candidate_row
                                desired_sequence_no = next_sequence_no
                                last_completed_sequence_no = max(next_sequence_no - 1, 0)
                                if current_progress_sequence_no == next_sequence_no and current_progress_presented_local_date:
                                    presented_local_date = current_progress_presented_local_date
                                else:
                                    presented_local_date = service_day_key

            if desired_sequence_row is None and desired_sequence_no is None and last_completed_sequence_no < total:
                first_unanswered = await self._compute_first_unanswered_sequence_no(user_id)
                if first_unanswered is None:
                    desired_sequence_row = None
                    desired_sequence_no = None
                    last_completed_sequence_no = total
                    presented_local_date = None
                else:
                    desired_sequence_row = await self._fetch_sequence_row(first_unanswered)
                    desired_sequence_no = _safe_int(desired_sequence_row.get("sequence_no"), 0) if desired_sequence_row else None
                    if not desired_sequence_row or not desired_sequence_no:
                        logger.warning("today_question: sequence row missing for sequence_no=%s", first_unanswered)
                        desired_sequence_row = None
                        desired_sequence_no = None
                        last_completed_sequence_no = total
                        presented_local_date = None
                    else:
                        last_completed_sequence_no = max(desired_sequence_no - 1, 0)
                        if current_progress_sequence_no == desired_sequence_no and current_progress_presented_local_date:
                            presented_local_date = current_progress_presented_local_date
                        else:
                            presented_local_date = service_day_key

        existing_last_completed = _safe_int((progress_row or {}).get("last_completed_sequence_no"), 0)
        existing_current_sequence_id = current_progress_sequence_id
        existing_current_sequence_no = current_progress_sequence_no
        existing_presented_local_date = str((progress_row or {}).get("current_presented_local_date") or "").strip() or None
        desired_current_sequence_id = str((desired_sequence_row or {}).get("id") or "").strip() or None

        if (
            progress_row is None
            or existing_last_completed != last_completed_sequence_no
            or existing_current_sequence_id != desired_current_sequence_id
            or existing_current_sequence_no != desired_sequence_no
            or existing_presented_local_date != presented_local_date
        ):
            progress_row = await self._upsert_user_progress(
                user_id,
                last_completed_sequence_no=last_completed_sequence_no,
                current_sequence_id=desired_current_sequence_id,
                current_sequence_no=desired_sequence_no,
                current_presented_local_date=presented_local_date,
            )

        return {
            "row": progress_row,
            "sequence_row": desired_sequence_row,
            "public": _progress_public(
                sequence_no=desired_sequence_no,
                total_count=total,
                current_presented_local_date=presented_local_date,
            ),
        }

    async def _resolve_subscription_tier_value(self, user_id: str) -> str:
        uid = str(user_id or "").strip()
        if not uid:
            return SubscriptionTier.FREE.value
        try:
            tier = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
            return str(getattr(tier, "value", tier) or SubscriptionTier.FREE.value).strip().lower() or SubscriptionTier.FREE.value
        except Exception:
            logger.exception("today_question: subscription tier lookup failed")
            return SubscriptionTier.FREE.value

    def _is_personal_followup_allowed(self, tier_value: str) -> bool:
        if not TODAY_QUESTION_PERSONAL_FOLLOWUP_ENABLED:
            return False
        return str(tier_value or "").strip().lower() == SubscriptionTier.PREMIUM.value

    def _should_reserve_static_slot(self, *, user_id: str, service_day_key: str) -> bool:
        every = int(TODAY_QUESTION_PERSONAL_STATIC_FALLBACK_EVERY_N_DAYS or 0)
        if every <= 0:
            return False
        try:
            ordinal = date.fromisoformat(str(service_day_key or "").strip()).toordinal()
        except Exception:
            ordinal = 0
        seed = sum(ord(ch) for ch in str(user_id or ""))
        return ((ordinal + seed) % every) == 0

    async def _fetch_personal_question_row_for_day(self, user_id: str, service_day_key: str) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        day = str(service_day_key or "").strip()
        if not uid or not day:
            return None
        rows = await self._select_rows(
            TODAY_QUESTION_PERSONAL_QUESTIONS_TABLE,
            params={
                "select": "*",
                "user_id": f"eq.{uid}",
                "presented_local_date": f"eq.{day}",
                "status": "in.(ready,answered)",
                "order": "created_at.desc,id.desc",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    async def _fetch_personal_question_row_by_id(self, user_id: str, personal_question_id: str) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        qid = str(personal_question_id or "").strip()
        if not uid or not qid:
            return None
        rows = await self._select_rows(
            TODAY_QUESTION_PERSONAL_QUESTIONS_TABLE,
            params={
                "select": "*",
                "id": f"eq.{qid}",
                "user_id": f"eq.{uid}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    async def _fetch_seen_personal_anchor_keys(self, user_id: str) -> set[tuple[str, str, str]]:
        uid = str(user_id or "").strip()
        if not uid:
            return set()
        seen: set[tuple[str, str, str]] = set()
        try:
            rows = await self._select_rows(
                TODAY_QUESTION_ANSWERS_TABLE,
                params={
                    "select": "source_id,anchor_text,question_type",
                    "user_id": f"eq.{uid}",
                    "question_origin": f"eq.{QUESTION_ORIGIN_PERSONAL}",
                    "order": "answered_at.desc,id.desc",
                    "limit": "80",
                },
            )
            for row in rows:
                source_id = str(row.get("source_id") or "").strip()
                anchor_text = str(row.get("anchor_text") or "").strip()
                question_type = str(row.get("question_type") or "").strip()
                if source_id and anchor_text and question_type:
                    seen.add((source_id, anchor_text, question_type))
        except Exception:
            logger.exception("today_question: failed to scan personal answer anchors")
        try:
            rows = await self._select_rows(
                TODAY_QUESTION_PERSONAL_CANDIDATES_TABLE,
                params={
                    "select": "source_id,anchor_text,question_type",
                    "user_id": f"eq.{uid}",
                    "status": "in.(used,rejected)",
                    "order": "created_at.desc,id.desc",
                    "limit": "120",
                },
            )
            for row in rows:
                source_id = str(row.get("source_id") or "").strip()
                anchor_text = str(row.get("anchor_text") or "").strip()
                question_type = str(row.get("question_type") or "").strip()
                if source_id and anchor_text and question_type:
                    seen.add((source_id, anchor_text, question_type))
        except Exception:
            logger.exception("today_question: failed to scan personal candidate anchors")
        return seen

    async def _insert_personal_candidate(self, user_id: str, candidate: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        if not uid or not isinstance(candidate, Mapping):
            return None
        source_id = str(candidate.get("source_id") or "").strip()
        source_field = str(candidate.get("source_field") or "").strip()
        anchor_text = str(candidate.get("anchor_text") or "").strip()
        question_type = str(candidate.get("question_type") or "").strip()
        if not source_id or not source_field or not anchor_text or not question_type:
            return None
        existing = await self._select_rows(
            TODAY_QUESTION_PERSONAL_CANDIDATES_TABLE,
            params={
                "select": "*",
                "user_id": f"eq.{uid}",
                "source_type": f"eq.{str(candidate.get('source_type') or 'emotion_input')}",
                "source_id": f"eq.{source_id}",
                "source_field": f"eq.{source_field}",
                "anchor_text": f"eq.{anchor_text}",
                "question_type": f"eq.{question_type}",
                "limit": "1",
            },
        )
        if existing:
            return existing[0]
        now_iso = _iso_utc()
        body = {
            "user_id": uid,
            "source_type": str(candidate.get("source_type") or "emotion_input").strip() or "emotion_input",
            "source_id": source_id,
            "source_field": source_field,
            "anchor_text": anchor_text,
            "anchor_start": candidate.get("anchor_start"),
            "anchor_end": candidate.get("anchor_end"),
            "question_type": question_type,
            "score": int(candidate.get("score") or 0),
            "source_hash": str(candidate.get("source_hash") or "").strip() or None,
            "status": "ready",
            "reason_json": candidate.get("reason_json") if isinstance(candidate.get("reason_json"), Mapping) else {},
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        rows = await self._insert_rows(
            TODAY_QUESTION_PERSONAL_CANDIDATES_TABLE,
            json_body=body,
            prefer="return=representation",
        )
        return rows[0] if rows else body

    async def _create_personal_question_from_candidate(
        self,
        *,
        user_id: str,
        service_day_key: str,
        candidate_row: Mapping[str, Any],
    ) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        cid = str(candidate_row.get("id") or "").strip()
        if not uid or not cid:
            return None
        payload = build_personal_question_insert_payload(
            user_id=uid,
            candidate_id=cid,
            candidate=candidate_row,
            service_day_key=service_day_key,
        )
        if not payload:
            return None
        now_iso = _iso_utc()
        payload["created_at"] = now_iso
        payload["updated_at"] = now_iso
        rows = await self._insert_rows(
            TODAY_QUESTION_PERSONAL_QUESTIONS_TABLE,
            json_body=payload,
            prefer="return=representation",
        )
        question_row = rows[0] if rows else payload
        try:
            await self._patch_rows(
                TODAY_QUESTION_PERSONAL_CANDIDATES_TABLE,
                params={"id": f"eq.{cid}", "user_id": f"eq.{uid}"},
                json_body={"status": "used", "updated_at": now_iso},
                prefer="return=minimal",
            )
        except Exception:
            logger.exception("today_question: failed to mark personal candidate used")
        return question_row

    async def _resolve_personal_followup_for_day(
        self,
        user_id: str,
        *,
        service_day_key: str,
        tier_value: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        day = str(service_day_key or "").strip()
        if not uid or not day:
            return None
        tier = str(tier_value or "").strip().lower() or await self._resolve_subscription_tier_value(uid)
        if not self._is_personal_followup_allowed(tier):
            return None

        existing = await self._fetch_personal_question_row_for_day(uid, day)
        if existing:
            return existing

        if self._should_reserve_static_slot(user_id=uid, service_day_key=day):
            return None

        try:
            rows = await list_recent_emotion_inputs_for_personal_today_question(uid)
            seen_keys = await self._fetch_seen_personal_anchor_keys(uid)
            candidate = build_best_personal_today_question_candidate(rows, seen_keys=seen_keys)
            if not candidate:
                return None
            if int(candidate.get("score") or 0) < int(TODAY_QUESTION_PERSONAL_MIN_SCORE or 0):
                return None
            candidate_row = await self._insert_personal_candidate(uid, candidate)
            if not candidate_row:
                return None
            return await self._create_personal_question_from_candidate(
                user_id=uid,
                service_day_key=day,
                candidate_row=candidate_row,
            )
        except Exception:
            logger.exception("today_question: personal followup resolution failed")
            return None

    async def refresh_personal_followup_candidates(self, *, limit: int = 200, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        now = now_utc or _now_utc()
        day = _service_day_key(now)
        rows = await self._select_rows(
            ACTIVE_USERS_TABLE,
            params={
                "select": "user_id,subscription_tier,last_active_at",
                "subscription_tier": f"eq.{SubscriptionTier.PREMIUM.value}",
                "order": "last_active_at.desc",
                "limit": str(max(1, min(int(limit or 200), 1000))),
            },
        )
        scanned = 0
        created = 0
        for row in rows:
            uid = str(row.get("user_id") or "").strip()
            if not uid:
                continue
            scanned += 1
            before = await self._fetch_personal_question_row_for_day(uid, day)
            question_row = await self._resolve_personal_followup_for_day(
                uid,
                service_day_key=day,
                tier_value=SubscriptionTier.PREMIUM.value,
            )
            if question_row and not before:
                created += 1
        return {"status": "ok", "service_day_key": day, "scanned": scanned, "created": created}

    def _resolve_choice_from_input(
        self,
        choice_rows: List[Mapping[str, Any]],
        *,
        selected_choice_id: Optional[str],
        selected_choice_key: Optional[str],
    ) -> Dict[str, Any]:
        cid = str(selected_choice_id or "").strip()
        ckey = str(selected_choice_key or "").strip()
        for row in choice_rows or []:
            if cid and str(row.get("id") or "").strip() == cid:
                return _choice_snapshot(row)
            if ckey and str(row.get("choice_key") or "").strip() == ckey:
                return _choice_snapshot(row)
        raise HTTPException(status_code=422, detail="Selected choice is invalid")

    def _resolve_choice_from_snapshot(
        self,
        choices_snapshot: List[Mapping[str, Any]],
        *,
        selected_choice_id: Optional[str],
        selected_choice_key: Optional[str],
    ) -> Dict[str, Any]:
        cid = str(selected_choice_id or "").strip()
        ckey = str(selected_choice_key or "").strip()
        for row in choices_snapshot or []:
            if cid and str(row.get("choice_id") or "").strip() == cid:
                return dict(row)
            if ckey and str(row.get("choice_key") or "").strip() == ckey:
                return dict(row)
        raise HTTPException(status_code=422, detail="Selected choice is invalid")

    async def fetch_current_bundle(
        self,
        user_id: str,
        *,
        timezone_name: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> TodayQuestionCurrentBundle:
        uid = str(user_id or "").strip()
        now = now_utc or _now_utc()
        # service-day 自体は従来通り固定基準で切り替える。
        # ただし、質問本文の表示と回答受付はユーザーの通知時刻以降に限定する。
        service_day_key = _service_day_key(now)
        settings_task = asyncio.create_task(self.get_or_create_user_settings(uid, timezone_name=timezone_name))
        total_count_task = asyncio.create_task(self._fetch_total_sequence_count())
        today_answer_task = asyncio.create_task(self._fetch_answer_row_for_day(uid, service_day_key))
        progress_task = asyncio.create_task(self._fetch_user_progress_row(uid))

        settings, total_count, today_answer, progress_row = await asyncio.gather(
            settings_task,
            total_count_task,
            today_answer_task,
            progress_task,
        )

        if not _is_today_question_released_for_settings(now, settings):
            return TodayQuestionCurrentBundle(
                service_day_key=service_day_key,
                question=None,
                answer=None,
                settings=settings,
                progress=_hidden_until_delivery_progress(total_count=total_count, progress_row=progress_row),
                release_status="locked_until_delivery",
                release_time_local=_hidden_release_time_from_settings(settings),
            )

        if today_answer:
            answer_sequence_no = _safe_int(today_answer.get("sequence_no"), 0) or None
            if not progress_row and answer_sequence_no:
                progress_row = await self._upsert_user_progress(
                    uid,
                    last_completed_sequence_no=answer_sequence_no,
                    current_sequence_id=str(today_answer.get("sequence_id") or "").strip() or None,
                    current_sequence_no=answer_sequence_no,
                    current_presented_local_date=str(today_answer.get("presented_local_date") or today_answer.get("local_answer_date") or service_day_key),
                )
            progress_public = _progress_public(
                sequence_no=answer_sequence_no or _safe_int((progress_row or {}).get("current_sequence_no"), 0) or None,
                total_count=total_count,
                current_presented_local_date=(
                    str(today_answer.get("presented_local_date") or "").strip()
                    or str((progress_row or {}).get("current_presented_local_date") or "").strip()
                    or service_day_key
                ),
            )
            origin = _question_origin_from_row(today_answer)
            source_anchor = _source_anchor_public_from_answer_row(today_answer)
            personal_question_id = str(today_answer.get("personal_question_id") or "").strip() or None
            return TodayQuestionCurrentBundle(
                service_day_key=service_day_key,
                question=_question_public_from_answer_row(today_answer),
                answer=today_answer,
                settings=settings,
                progress=progress_public,
                question_origin=origin,
                personal_question_id=personal_question_id,
                source_anchor=source_anchor,
                question_type=str(today_answer.get("question_type") or "").strip() or None,
            )

        tier_value = await self._resolve_subscription_tier_value(uid)
        personal_question_row = await self._resolve_personal_followup_for_day(
            uid,
            service_day_key=service_day_key,
            tier_value=tier_value,
        )
        if personal_question_row:
            source_anchor = _source_anchor_public(personal_question_row.get("source_anchor_json"))
            return TodayQuestionCurrentBundle(
                service_day_key=service_day_key,
                question=_question_public_from_personal_row(personal_question_row),
                answer=None,
                settings=settings,
                progress={**_progress_public(
                    sequence_no=None,
                    total_count=total_count,
                    current_presented_local_date=service_day_key,
                ), "mode": QUESTION_ORIGIN_PERSONAL},
                question_origin=QUESTION_ORIGIN_PERSONAL,
                personal_question_id=str(personal_question_row.get("id") or "").strip() or None,
                source_anchor=source_anchor,
                question_type=str(personal_question_row.get("question_type") or "").strip() or None,
            )

        resolved = await self._resolve_pending_progress(
            uid,
            service_day_key=service_day_key,
            total_count=total_count,
            progress_row=progress_row,
        )
        sequence_row = resolved["sequence_row"]
        if not sequence_row:
            return TodayQuestionCurrentBundle(
                service_day_key=service_day_key,
                question=None,
                answer=None,
                settings=settings,
                progress=resolved["public"],
            )

        question_row = await self._fetch_question_row(str(sequence_row.get("question_id") or ""))
        if not question_row:
            logger.warning(
                "today_question: question row missing for sequence_no=%s question_id=%s",
                sequence_row.get("sequence_no"),
                sequence_row.get("question_id"),
            )
            return TodayQuestionCurrentBundle(
                service_day_key=service_day_key,
                question=None,
                answer=None,
                settings=settings,
                progress=resolved["public"],
            )
        choice_rows = await self._fetch_choice_rows(str(question_row.get("id") or ""))
        return TodayQuestionCurrentBundle(
            service_day_key=service_day_key,
            question=_question_public(question_row, choice_rows),
            answer=None,
            settings=settings,
            progress=resolved["public"],
        )

    async def fetch_status_bundle(
        self,
        user_id: str,
        *,
        timezone_name: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> TodayQuestionStatusBundle:
        uid = str(user_id or "").strip()
        now = now_utc or _now_utc()
        service_day_key = _service_day_key(now)
        settings_task = asyncio.create_task(self.get_or_create_user_settings(uid, timezone_name=timezone_name))
        total_count_task = asyncio.create_task(self._fetch_total_sequence_count())
        today_answer_task = asyncio.create_task(self._fetch_answer_status_row_for_day(uid, service_day_key))
        progress_task = asyncio.create_task(self._fetch_user_progress_row(uid))

        settings, total_count, today_answer, progress_row = await asyncio.gather(
            settings_task,
            total_count_task,
            today_answer_task,
            progress_task,
        )

        if not _is_today_question_released_for_settings(now, settings):
            return TodayQuestionStatusBundle(
                service_day_key=service_day_key,
                question=None,
                answer=None,
                settings=settings,
                progress=_hidden_until_delivery_progress(total_count=total_count, progress_row=progress_row),
                release_status="locked_until_delivery",
                release_time_local=_hidden_release_time_from_settings(settings),
            )

        if today_answer:
            answer_sequence_no = _safe_int(today_answer.get("sequence_no"), 0) or None
            if not progress_row and answer_sequence_no:
                progress_row = await self._upsert_user_progress(
                    uid,
                    last_completed_sequence_no=answer_sequence_no,
                    current_sequence_id=str(today_answer.get("sequence_id") or "").strip() or None,
                    current_sequence_no=answer_sequence_no,
                    current_presented_local_date=str(today_answer.get("presented_local_date") or today_answer.get("local_answer_date") or service_day_key),
                )
            progress_public = _progress_public(
                sequence_no=answer_sequence_no or _safe_int((progress_row or {}).get("current_sequence_no"), 0) or None,
                total_count=total_count,
                current_presented_local_date=(
                    str(today_answer.get("presented_local_date") or "").strip()
                    or str((progress_row or {}).get("current_presented_local_date") or "").strip()
                    or service_day_key
                ),
            )
            question_meta = _question_status_public_from_answer_row(today_answer)
            question_id = str(today_answer.get("question_id") or "").strip()
            if question_id:
                meta_row = await self._fetch_question_meta_row(question_id)
                if meta_row:
                    question_meta = _question_status_public(meta_row)
            origin = _question_origin_from_row(today_answer)
            source_anchor = _source_anchor_public_from_answer_row(today_answer)
            personal_question_id = str(today_answer.get("personal_question_id") or "").strip() or None
            return TodayQuestionStatusBundle(
                service_day_key=service_day_key,
                question=question_meta,
                answer=today_answer,
                settings=settings,
                progress=progress_public,
                question_origin=origin,
                personal_question_id=personal_question_id,
                source_anchor=source_anchor,
                question_type=str(today_answer.get("question_type") or "").strip() or None,
            )

        tier_value = await self._resolve_subscription_tier_value(uid)
        personal_question_row = await self._resolve_personal_followup_for_day(
            uid,
            service_day_key=service_day_key,
            tier_value=tier_value,
        )
        if personal_question_row:
            source_anchor = _source_anchor_public(personal_question_row.get("source_anchor_json"))
            return TodayQuestionStatusBundle(
                service_day_key=service_day_key,
                question=_question_status_public_from_personal_row(personal_question_row),
                answer=None,
                settings=settings,
                progress={**_progress_public(
                    sequence_no=None,
                    total_count=total_count,
                    current_presented_local_date=service_day_key,
                ), "mode": QUESTION_ORIGIN_PERSONAL},
                question_origin=QUESTION_ORIGIN_PERSONAL,
                personal_question_id=str(personal_question_row.get("id") or "").strip() or None,
                source_anchor=source_anchor,
                question_type=str(personal_question_row.get("question_type") or "").strip() or None,
            )

        resolved = await self._resolve_pending_progress(
            uid,
            service_day_key=service_day_key,
            total_count=total_count,
            progress_row=progress_row,
        )
        sequence_row = resolved["sequence_row"]
        if not sequence_row:
            return TodayQuestionStatusBundle(
                service_day_key=service_day_key,
                question=None,
                answer=None,
                settings=settings,
                progress=resolved["public"],
            )

        question_id = str(sequence_row.get("question_id") or "").strip()
        question_row = await self._fetch_question_meta_row(question_id)
        if not question_row:
            logger.warning(
                "today_question: status meta row missing for sequence_no=%s question_id=%s",
                sequence_row.get("sequence_no"),
                sequence_row.get("question_id"),
            )
            return TodayQuestionStatusBundle(
                service_day_key=service_day_key,
                question=None,
                answer=None,
                settings=settings,
                progress=resolved["public"],
            )

        return TodayQuestionStatusBundle(
            service_day_key=service_day_key,
            question=_question_status_public(question_row),
            answer=None,
            settings=settings,
            progress=resolved["public"],
        )

    async def create_answer(
        self,
        user_id: str,
        *,
        service_day_key: str,
        question_id: str,
        answer_mode: str,
        selected_choice_id: Optional[str] = None,
        selected_choice_key: Optional[str] = None,
        free_text: Optional[str] = None,
        sequence_no: Optional[int] = None,
        timezone_name: Optional[str] = None,
        question_origin: Optional[str] = None,
        personal_question_id: Optional[str] = None,
        source_anchor_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        mode = str(answer_mode or "").strip()
        if mode not in ("choice", "free_text"):
            raise HTTPException(status_code=422, detail="answer_mode must be choice or free_text")

        bundle = await self.fetch_current_bundle(uid, timezone_name=timezone_name)
        if str(bundle.service_day_key) != str(service_day_key or "").strip():
            raise HTTPException(status_code=409, detail="Question day has changed. Please reload.")
        if not bundle.question:
            raise HTTPException(status_code=404, detail="No today question is available")
        if str(bundle.question.get("question_id") or "") != str(question_id or "").strip():
            raise HTTPException(status_code=409, detail="Question has changed. Please reload.")
        if bundle.answer:
            raise HTTPException(status_code=409, detail="Today question has already been answered")

        current_origin = str(getattr(bundle, "question_origin", None) or (bundle.question or {}).get("question_origin") or QUESTION_ORIGIN_STATIC).strip() or QUESTION_ORIGIN_STATIC
        expected_origin = str(question_origin or current_origin).strip() or current_origin
        if expected_origin != current_origin:
            raise HTTPException(status_code=409, detail="Question has changed. Please reload.")

        current_sequence_no = _safe_int((bundle.progress or {}).get("sequence_no"), 0) or None
        if current_origin != QUESTION_ORIGIN_PERSONAL and sequence_no is not None and current_sequence_no and _safe_int(sequence_no, 0) != current_sequence_no:
            raise HTTPException(status_code=409, detail="Question sequence has changed. Please reload.")

        if current_origin == QUESTION_ORIGIN_PERSONAL:
            current_personal_question_id = str(getattr(bundle, "personal_question_id", None) or (bundle.question or {}).get("personal_question_id") or "").strip()
            provided_personal_question_id = str(personal_question_id or "").strip()
            if provided_personal_question_id and provided_personal_question_id != current_personal_question_id:
                raise HTTPException(status_code=409, detail="Question has changed. Please reload.")
            anchor = getattr(bundle, "source_anchor", None)
            if source_anchor_hash and isinstance(anchor, Mapping):
                expected_hash = build_source_anchor_hash(anchor)
                if str(source_anchor_hash or "").strip() != expected_hash:
                    raise HTTPException(status_code=409, detail="Question source has changed. Please reload.")

        existing_today_answer = await self._fetch_answer_row_for_day(uid, bundle.service_day_key)
        if existing_today_answer:
            raise HTTPException(status_code=409, detail="Today question has already been answered")

        if current_origin != QUESTION_ORIGIN_PERSONAL and current_sequence_no:
            existing_sequence_answer = await self._fetch_answer_row_for_sequence(uid, current_sequence_no)
            if existing_sequence_answer:
                raise HTTPException(status_code=409, detail="This question has already been answered")

        question = bundle.question
        if current_origin == QUESTION_ORIGIN_PERSONAL:
            choice_rows = []
            choices_snapshot = _parse_jsonish(question.get("choices"), []) if isinstance(question, Mapping) else []
            if not isinstance(choices_snapshot, list):
                choices_snapshot = []
            choices_snapshot = [dict(r) for r in choices_snapshot if isinstance(r, Mapping)]
            personal_row = await self._fetch_personal_question_row_by_id(
                uid,
                str(getattr(bundle, "personal_question_id", None) or question.get("personal_question_id") or question.get("question_id") or ""),
            )
            if personal_row:
                raw_personal_choices = _parse_jsonish(personal_row.get("choices_snapshot_json"), [])
                if isinstance(raw_personal_choices, list):
                    choices_snapshot = [dict(r) for r in raw_personal_choices if isinstance(r, Mapping)]
        else:
            choice_rows = await self._fetch_choice_rows(question["question_id"])
            choices_snapshot = [_choice_snapshot(r) for r in choice_rows]

        free_text_clean = str(free_text or "").strip()
        selected_snapshot: Optional[Dict[str, Any]] = None
        if mode == "choice":
            if current_origin == QUESTION_ORIGIN_PERSONAL:
                selected_snapshot = self._resolve_choice_from_snapshot(
                    choices_snapshot,
                    selected_choice_id=selected_choice_id,
                    selected_choice_key=selected_choice_key,
                )
            else:
                selected_snapshot = self._resolve_choice_from_input(
                    choice_rows,
                    selected_choice_id=selected_choice_id,
                    selected_choice_key=selected_choice_key,
                )
            if free_text_clean and len(free_text_clean) > 1000:
                raise HTTPException(status_code=422, detail="free_text is too long")
        else:
            if not free_text_clean:
                raise HTTPException(status_code=422, detail="free_text is required")
            if len(free_text_clean) > 1000:
                raise HTTPException(status_code=422, detail="free_text is too long")

        now_iso = _iso_utc()
        sequence_row = await self._fetch_sequence_row(current_sequence_no or 0) if (current_origin != QUESTION_ORIGIN_PERSONAL and current_sequence_no) else None
        presented_local_date = str((bundle.progress or {}).get("current_presented_local_date") or bundle.service_day_key or "").strip() or bundle.service_day_key
        personal_question_id_value = str(getattr(bundle, "personal_question_id", None) or question.get("personal_question_id") or "").strip() or None
        source_anchor_value = getattr(bundle, "source_anchor", None) if isinstance(getattr(bundle, "source_anchor", None), Mapping) else None
        question_type_value = str(getattr(bundle, "question_type", None) or question.get("question_type") or "").strip() or None
        row = {
            "user_id": uid,
            "service_day_key": bundle.service_day_key,
            "local_answer_date": bundle.service_day_key,
            "sequence_id": str((sequence_row or {}).get("id") or "").strip() or None,
            "sequence_no": current_sequence_no if current_origin != QUESTION_ORIGIN_PERSONAL else None,
            "presented_local_date": presented_local_date,
            "question_id": question["question_id"] if current_origin != QUESTION_ORIGIN_PERSONAL else None,
            "question_key": question.get("question_key"),
            "question_version": int(question.get("version") or 1),
            "question_origin": current_origin,
            "personal_question_id": personal_question_id_value if current_origin == QUESTION_ORIGIN_PERSONAL else None,
            "source_type": (str(source_anchor_value.get("source_type") or "").strip() if source_anchor_value else None),
            "source_id": (str(source_anchor_value.get("source_id") or "").strip() if source_anchor_value else None),
            "source_field": (str(source_anchor_value.get("source_field") or "").strip() if source_anchor_value else None),
            "anchor_text": (str(source_anchor_value.get("anchor_text") or "").strip() if source_anchor_value else None),
            "question_type": question_type_value,
            "source_anchor_snapshot_json": dict(source_anchor_value) if source_anchor_value else None,
            "answer_mode": mode,
            "selected_choice_id": (selected_snapshot.get("choice_id") if selected_snapshot and current_origin != QUESTION_ORIGIN_PERSONAL else None),
            "selected_choice_key": selected_snapshot.get("choice_key") if selected_snapshot else None,
            "free_text": free_text_clean or None,
            "answered_at": now_iso,
            "edited_at": None,
            "edit_count": 0,
            "question_text_snapshot": question.get("text"),
            "choices_snapshot_json": choices_snapshot,
            "selected_choice_label_snapshot": selected_snapshot.get("label") if selected_snapshot else None,
            "selected_choice_hidden_meta_snapshot_json": (selected_snapshot.get("hidden_meta") if selected_snapshot else None),
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        rows = await self._insert_rows(
            TODAY_QUESTION_ANSWERS_TABLE,
            json_body=row,
            prefer="return=representation",
        )

        if current_origin != QUESTION_ORIGIN_PERSONAL and current_sequence_no:
            await self._upsert_user_progress(
                uid,
                last_completed_sequence_no=current_sequence_no,
                current_sequence_id=str((sequence_row or {}).get("id") or "").strip() or None,
                current_sequence_no=current_sequence_no,
                current_presented_local_date=presented_local_date,
            )
        elif current_origin == QUESTION_ORIGIN_PERSONAL and personal_question_id_value:
            try:
                await self._patch_rows(
                    TODAY_QUESTION_PERSONAL_QUESTIONS_TABLE,
                    params={"id": f"eq.{personal_question_id_value}", "user_id": f"eq.{uid}"},
                    json_body={"status": "answered", "answered_at": now_iso, "updated_at": now_iso},
                    prefer="return=minimal",
                )
            except Exception:
                logger.exception("today_question: failed to mark personal question answered")

        await invalidate_today_question_user_runtime_cache(uid)

        return rows[0] if rows else row

    async def list_history(
        self,
        user_id: str,
        *,
        limit: int = 30,
        offset: int = 0,
        answered_at_gte: Optional[str] = None,
        answered_at_lt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        lim = max(1, min(int(limit or 30), TODAY_QUESTION_MAX_HISTORY_LIMIT))
        off = max(0, int(offset or 0))
        params = {
            "select": "*",
            "user_id": f"eq.{uid}",
            "order": "answered_at.desc,id.desc",
            "limit": str(lim),
            "offset": str(off),
        }
        gte_iso = str(answered_at_gte or "").strip()
        lt_iso = str(answered_at_lt or "").strip()
        if gte_iso and lt_iso:
            params["and"] = f"(answered_at.gte.{gte_iso},answered_at.lt.{lt_iso})"
        elif gte_iso:
            params["answered_at"] = f"gte.{gte_iso}"
        elif lt_iso:
            params["answered_at"] = f"lt.{lt_iso}"
        rows = await self._select_rows(
            TODAY_QUESTION_ANSWERS_TABLE,
            params=params,
        )
        return rows

    async def get_history_answer(self, user_id: str, answer_id: str) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        aid = str(answer_id or "").strip()
        rows = await self._select_rows(
            TODAY_QUESTION_ANSWERS_TABLE,
            params={
                "select": "*",
                "id": f"eq.{aid}",
                "user_id": f"eq.{uid}",
                "limit": "1",
            },
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Answer not found")
        return rows[0]

    async def patch_answer(
        self,
        user_id: str,
        answer_id: str,
        *,
        answer_mode: str,
        selected_choice_id: Optional[str] = None,
        selected_choice_key: Optional[str] = None,
        free_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        current = await self.get_history_answer(user_id, answer_id)
        mode = str(answer_mode or "").strip()
        if mode not in ("choice", "free_text"):
            raise HTTPException(status_code=422, detail="answer_mode must be choice or free_text")

        choices_snapshot = _parse_jsonish(current.get("choices_snapshot_json"), [])
        if not isinstance(choices_snapshot, list):
            choices_snapshot = []

        selected_snapshot: Optional[Dict[str, Any]] = None
        free_text_clean = str(free_text or "").strip()
        if mode == "choice":
            selected_snapshot = self._resolve_choice_from_snapshot(
                choices_snapshot,
                selected_choice_id=selected_choice_id,
                selected_choice_key=selected_choice_key,
            )
            if free_text is None:
                free_text_clean = str(current.get("free_text") or "").strip()
            if free_text_clean and len(free_text_clean) > 1000:
                raise HTTPException(status_code=422, detail="free_text is too long")
        else:
            if not free_text_clean:
                raise HTTPException(status_code=422, detail="free_text is required")
            if len(free_text_clean) > 1000:
                raise HTTPException(status_code=422, detail="free_text is too long")

        prev_snapshot = dict(current)
        revision = {
            "answer_id": str(current.get("id") or answer_id),
            "version_no": int(current.get("edit_count") or 0) + 1,
            "snapshot_json": prev_snapshot,
            "edited_at": _iso_utc(),
            "created_at": _iso_utc(),
        }
        try:
            await self._insert_rows(TODAY_QUESTION_REVISIONS_TABLE, json_body=revision, prefer="return=minimal")
        except Exception:
            logger.exception("today_question: failed to save revision")

        origin = _question_origin_from_row(current)
        patch_body = {
            "answer_mode": mode,
            "selected_choice_id": (selected_snapshot.get("choice_id") if selected_snapshot and origin != QUESTION_ORIGIN_PERSONAL else None),
            "selected_choice_key": selected_snapshot.get("choice_key") if selected_snapshot else None,
            "free_text": free_text_clean or None,
            "selected_choice_label_snapshot": selected_snapshot.get("label") if selected_snapshot else None,
            "selected_choice_hidden_meta_snapshot_json": selected_snapshot.get("hidden_meta") if selected_snapshot else None,
            "edited_at": _iso_utc(),
            "updated_at": _iso_utc(),
            "edit_count": int(current.get("edit_count") or 0) + 1,
        }
        rows = await self._patch_rows(
            TODAY_QUESTION_ANSWERS_TABLE,
            params={
                "id": f"eq.{str(current.get('id') or answer_id)}",
                "user_id": f"eq.{str(user_id or '').strip()}",
            },
            json_body=patch_body,
            prefer="return=representation",
        )
        await invalidate_today_question_user_runtime_cache(str(user_id or "").strip())
        if rows:
            return rows[0]
        return await self.get_history_answer(user_id, answer_id)

    async def _fetch_profiles_for_push_scan(self, limit: int) -> List[Dict[str, Any]]:
        rows = await self._select_rows(
            "profiles",
            params={
                "select": "id,push_token,push_enabled",
                "push_enabled": "eq.true",
                "push_token": "not.is.null",
                "limit": str(max(1, min(limit, TODAY_QUESTION_PUSH_SCAN_LIMIT))),
            },
        )
        return rows

    async def _fetch_settings_map_for_users(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        ids = [str(x or "").strip() for x in user_ids if str(x or "").strip()]
        if not ids:
            return {}
        rows = await self._select_rows(
            TODAY_QUESTION_SETTINGS_TABLE,
            params={
                "select": "*",
                "user_id": _in_filter(ids),
                "limit": str(len(ids)),
            },
        )
        return {str(r.get("user_id") or ""): r for r in rows if isinstance(r, dict)}

    async def _fetch_delivery_map(self, user_ids: List[str], service_day_key: str) -> Dict[str, Dict[str, Any]]:
        ids = [str(x or "").strip() for x in user_ids if str(x or "").strip()]
        if not ids:
            return {}
        rows = await self._select_rows(
            TODAY_QUESTION_PUSH_DELIVERIES_TABLE,
            params={
                "select": "*",
                "user_id": _in_filter(ids),
                "service_day_key": f"eq.{service_day_key}",
                "limit": str(len(ids)),
            },
        )
        return {str(r.get("user_id") or ""): r for r in rows if isinstance(r, dict)}

    async def _fetch_answer_map(self, user_ids: List[str], service_day_key: str) -> Dict[str, Dict[str, Any]]:
        ids = [str(x or "").strip() for x in user_ids if str(x or "").strip()]
        if not ids:
            return {}
        rows = await self._select_rows(
            TODAY_QUESTION_ANSWERS_TABLE,
            params={
                "select": "id,user_id,service_day_key",
                "user_id": _in_filter(ids),
                "service_day_key": f"eq.{service_day_key}",
                "limit": str(len(ids)),
            },
        )
        return {str(r.get("user_id") or ""): r for r in rows if isinstance(r, dict)}

    async def list_due_push_candidates(self, *, now_utc: Optional[datetime] = None, limit: int = 200) -> List[Dict[str, Any]]:
        now = now_utc or _now_utc()
        profiles = await self._fetch_profiles_for_push_scan(limit=max(limit * 3, limit))
        user_ids = [str(r.get("id") or "").strip() for r in profiles if str(r.get("id") or "").strip()]
        settings_map = await self._fetch_settings_map_for_users(user_ids)

        due_by_day: Dict[str, List[Dict[str, Any]]] = {}
        for profile in profiles:
            uid = str(profile.get("id") or "").strip()
            if not uid:
                continue
            settings_row = settings_map.get(uid) or {
                "notification_enabled": TODAY_QUESTION_DEFAULT_NOTIFICATION_ENABLED,
                "delivery_time_local": TODAY_QUESTION_DEFAULT_DELIVERY_TIME,
                "timezone_name": TODAY_QUESTION_DEFAULT_TIMEZONE,
            }
            settings = _settings_public(settings_row)
            if not settings["notification_enabled"]:
                continue
            if not _is_delivery_time_due(now, settings["timezone_name"], settings["delivery_time_local"]):
                continue
            # 通知は user settings の local time を見るが、対象 question/day 自体は service-day 基準で固定する。
            day_key = _service_day_key(now)
            due_by_day.setdefault(day_key, []).append({
                "user_id": uid,
                "push_token": str(profile.get("push_token") or "").strip(),
                "timezone_name": settings["timezone_name"],
                "delivery_time_local": settings["delivery_time_local"],
                "service_day_key": day_key,
            })

        out: List[Dict[str, Any]] = []
        for day_key, rows in due_by_day.items():
            user_ids_for_day = [str(r.get("user_id") or "").strip() for r in rows]
            delivered_map = await self._fetch_delivery_map(user_ids_for_day, day_key)
            answered_map = await self._fetch_answer_map(user_ids_for_day, day_key)
            for row in rows:
                uid = str(row.get("user_id") or "").strip()
                if uid in delivered_map or uid in answered_map:
                    continue
                if not row.get("push_token"):
                    continue
                bundle = await self.fetch_current_bundle(
                    uid,
                    timezone_name=str(row.get("timezone_name") or "").strip() or None,
                    now_utc=now,
                )
                if not bundle.question or bundle.answer:
                    continue
                out.append({
                    **row,
                    "question_id": str(bundle.question.get("question_id") or ""),
                    "question_text": str(bundle.question.get("text") or "").strip(),
                    "sequence_no": _safe_int((bundle.progress or {}).get("sequence_no"), 0) or None,
                    "question_origin": str(getattr(bundle, "question_origin", None) or (bundle.question or {}).get("question_origin") or QUESTION_ORIGIN_STATIC),
                    "personal_question_id": str(getattr(bundle, "personal_question_id", None) or (bundle.question or {}).get("personal_question_id") or ""),
                })
                if len(out) >= limit:
                    return out
        return out

    async def mark_push_delivered(self, *, user_id: str, service_day_key: str, timezone_name: str, delivery_time_local: str) -> None:
        row = {
            "user_id": str(user_id or "").strip(),
            "service_day_key": str(service_day_key or "").strip(),
            "timezone_name": _normalize_timezone_name(timezone_name),
            "delivery_time_local": _normalize_delivery_time_local(delivery_time_local),
            "delivered_at": _iso_utc(),
            "created_at": _iso_utc(),
        }
        try:
            await self._insert_rows(TODAY_QUESTION_PUSH_DELIVERIES_TABLE, json_body=row, prefer="resolution=ignore-duplicates,return=minimal")
        except Exception:
            logger.exception("today_question: failed to mark push delivery")


__all__ = [
    "TodayQuestionStore",
    "TodayQuestionCurrentBundle",
    "_answer_summary",
    "_history_item_public",
    "_settings_public",
    "_normalize_timezone_name",
    "_normalize_delivery_time_local",
    "QUESTION_ORIGIN_STATIC",
    "QUESTION_ORIGIN_PERSONAL",
]
