# -*- coding: utf-8 -*-
from __future__ import annotations

"""Greeting slot logic for EmlisAI.

v1 implementation note:
- tries Supabase table first if available
- falls back to in-process memory when the table is absent or unavailable
"""

from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from emlis_ai_types import GreetingDecision

try:
    from supabase_client import sb_get, sb_patch, sb_post
except Exception:  # pragma: no cover
    sb_get = None  # type: ignore
    sb_patch = None  # type: ignore
    sb_post = None  # type: ignore

DEFAULT_TIMEZONE = "Asia/Tokyo"
GREETING_STATE_TABLE = "emlis_ai_greeting_state"
_MEMORY_STATE: Dict[str, Dict[str, Any]] = {}


def resolve_greeting_slot(now_local: datetime) -> str:
    hour = int(now_local.hour)
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 18:
        return "day"
    return "night"


def greeting_phrase_for_slot(slot_name: str) -> str:
    if slot_name == "morning":
        return "おはようございます"
    if slot_name == "day":
        return "こんにちは"
    return "こんばんは"


def build_greeting_slot_key(*, now_local: datetime) -> str:
    slot_name = resolve_greeting_slot(now_local)
    return f"{now_local.year:04d}-{now_local.month:02d}-{now_local.day:02d}:{slot_name}"


def resolve_timezone_name(timezone_name: Optional[str]) -> str:
    raw = str(timezone_name or "").strip()
    if not raw:
        return DEFAULT_TIMEZONE
    try:
        ZoneInfo(raw)
        return raw
    except Exception:
        return DEFAULT_TIMEZONE


def _pick_rows(resp: Any) -> list[dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def load_greeting_state_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return None
    if sb_get is not None:
        try:
            resp = await sb_get(
                f"/rest/v1/{GREETING_STATE_TABLE}",
                params={
                    "select": "user_id,last_greeting_slot_key,last_greeted_at,updated_at",
                    "user_id": f"eq.{uid}",
                    "limit": "1",
                },
                timeout=4.0,
            )
            if resp.status_code < 300:
                rows = _pick_rows(resp)
                if rows:
                    row = rows[0]
                    _MEMORY_STATE[uid] = dict(row)
                    return row
        except Exception:
            pass
    return dict(_MEMORY_STATE.get(uid) or {}) or None


async def save_greeting_state_for_user(
    user_id: str,
    *,
    slot_key: str,
    greeted_at_iso: str,
) -> None:
    uid = str(user_id or "").strip()
    if not uid:
        return None
    row = {
        "user_id": uid,
        "last_greeting_slot_key": str(slot_key or "").strip(),
        "last_greeted_at": str(greeted_at_iso or "").strip(),
        "updated_at": str(greeted_at_iso or "").strip(),
    }
    _MEMORY_STATE[uid] = dict(row)
    if sb_patch is None or sb_post is None:
        return None
    try:
        resp = await sb_patch(
            f"/rest/v1/{GREETING_STATE_TABLE}",
            params={"user_id": f"eq.{uid}"},
            json=row,
            prefer="return=representation",
            timeout=4.0,
        )
        if resp.status_code < 300 and _pick_rows(resp):
            return None
        await sb_post(
            f"/rest/v1/{GREETING_STATE_TABLE}",
            json=row,
            params={"on_conflict": "user_id"},
            prefer="resolution=merge-duplicates,return=minimal",
            timeout=4.0,
        )
    except Exception:
        return None


async def decide_greeting_for_user(
    *,
    user_id: str,
    display_name: Optional[str],
    timezone_name: Optional[str],
    now_utc: Optional[datetime] = None,
) -> GreetingDecision:
    from datetime import datetime, timezone

    tz_name = resolve_timezone_name(timezone_name)
    now_utc = now_utc or datetime.now(timezone.utc)
    now_local = now_utc.astimezone(ZoneInfo(tz_name))

    slot_name = resolve_greeting_slot(now_local)
    slot_key = build_greeting_slot_key(now_local=now_local)
    prev_state = await load_greeting_state_for_user(user_id)
    prev_key = str((prev_state or {}).get("last_greeting_slot_key") or "").strip()
    first_in_slot = prev_key != slot_key

    name = str(display_name or "").strip()
    if first_in_slot:
        if name:
            greeting_text = f"{name}さん、{greeting_phrase_for_slot(slot_name)}。Emlisです。"
        else:
            greeting_text = f"{greeting_phrase_for_slot(slot_name)}。Emlisです。"
        await save_greeting_state_for_user(
            user_id,
            slot_key=slot_key,
            greeted_at_iso=now_utc.isoformat().replace("+00:00", "Z"),
        )
    else:
        greeting_text = "Emlisです。"

    return GreetingDecision(
        slot_name=slot_name,
        slot_key=slot_key,
        greeting_text=greeting_text,
        first_in_slot=first_in_slot,
    )
