# -*- coding: utf-8 -*-
"""emotion_piece_store.py

Store helpers for the new emotion-generated Reflection flow.

Design
------
- Uses the same `mymodel_reflections` table family to keep read-side reuse viable.
- Draft preview rows are stored with:
    source_type = emotion_generated
    status      = draft
    is_active   = false
- Publish promotes the same row to ready + active WITHOUT archiving sibling rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence

from piece_generation_store import (
    REFLECTIONS_TABLE,
    REFLECTIONS_READ_TABLE,
    _sb_count,
    _sb_get_json,
    _sb_patch_json,
    _sb_post_json,
)
from piece_generated_display import apply_generated_display_to_content_json
from piece_publish_entitlements import get_current_month_window_jst

EMOTION_REFLECTION_SOURCE_TYPE = "emotion_generated"
EMOTION_REFLECTION_VERSION = "emotion_reflection.v1"


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def create_preview_draft(
    *,
    user_id: str,
    question: str,
    q_key: str,
    raw_answer: str,
    category: Optional[str],
    display_result: Any,
    emotion_input: Dict[str, Any],
) -> Dict[str, Any]:
    now_iso = _now_iso_z()
    content_json: Dict[str, Any] = {
        "version": EMOTION_REFLECTION_VERSION,
        "source_type": EMOTION_REFLECTION_SOURCE_TYPE,
        "question": str(question or "").strip(),
        "answer": str(raw_answer or "").strip(),
        "q_key": str(q_key or "").strip() or None,
        "category": str(category or "").strip() or None,
        "emotion_preview": dict(emotion_input or {}),
    }
    content_json = apply_generated_display_to_content_json(
        content_json,
        result=display_result,
        display_updated_at=now_iso,
    )

    payload = {
        "owner_user_id": str(user_id or "").strip(),
        "source_type": EMOTION_REFLECTION_SOURCE_TYPE,
        "status": "draft",
        "is_active": False,
        "q_key": str(q_key or "").strip() or None,
        "category": str(category or "").strip() or None,
        "question": str(question or "").strip(),
        "answer": str(raw_answer or "").strip(),
        "content_json": content_json,
        "published_at": None,
    }

    rows = await _sb_post_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        json_body=payload,
        timeout=10.0,
        prefer="return=representation",
    )
    if not rows:
        raise RuntimeError("Failed to create emotion reflection preview draft")
    return rows[0]


async def fetch_preview_draft(*, preview_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    pid = str(preview_id or "").strip()
    uid = str(user_id or "").strip()
    if not pid or not uid:
        return None
    rows = await _sb_get_json(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("select", "*"),
            ("id", f"eq.{pid}"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", f"eq.{EMOTION_REFLECTION_SOURCE_TYPE}"),
            ("limit", "1"),
        ],
        timeout=8.0,
    )
    return rows[0] if rows else None


async def cancel_preview_draft(*, preview_id: str, user_id: str) -> Dict[str, Any]:
    pid = str(preview_id or "").strip()
    uid = str(user_id or "").strip()
    rows = await _sb_patch_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        params=[
            ("id", f"eq.{pid}"),
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", f"eq.{EMOTION_REFLECTION_SOURCE_TYPE}"),
            ("status", "eq.draft"),
        ],
        json_body={
            "status": "rejected",
            "is_active": False,
            "published_at": None,
        },
        timeout=8.0,
        prefer="return=representation",
    )
    return rows[0] if rows else {"id": pid, "status": "rejected", "is_active": False}


async def publish_preview_draft(
    *,
    preview_id: str,
    user_id: str,
    published_at: str,
    emotion_entry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row = await fetch_preview_draft(preview_id=preview_id, user_id=user_id)
    if not row:
        raise ValueError("preview draft not found")

    content_json = row.get("content_json") if isinstance(row.get("content_json"), dict) else {}
    if emotion_entry:
        content_json = {
            **content_json,
            "emotion_entry": {
                "id": emotion_entry.get("id"),
                "created_at": emotion_entry.get("created_at"),
            },
        }

    rows = await _sb_patch_json(
        f"/rest/v1/{REFLECTIONS_TABLE}",
        params=[
            ("id", f"eq.{str(preview_id).strip()}"),
            ("owner_user_id", f"eq.{str(user_id).strip()}"),
            ("source_type", f"eq.{EMOTION_REFLECTION_SOURCE_TYPE}"),
            ("status", "eq.draft"),
        ],
        json_body={
            "status": "ready",
            "is_active": True,
            "published_at": str(published_at or "").strip() or _now_iso_z(),
            "content_json": content_json,
        },
        timeout=8.0,
        prefer="return=representation",
    )
    if not rows:
        raise RuntimeError("Failed to publish emotion reflection preview draft")
    return rows[0]


async def count_published_emotion_reflections_for_month(
    *,
    user_id: str,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    month_key, start_iso, end_iso = get_current_month_window_jst(now=now)
    uid = str(user_id or "").strip()
    if not uid:
        return {
            "month_key": month_key,
            "start_iso": start_iso,
            "end_iso": end_iso,
            "published_count": 0,
        }

    published_count = await _sb_count(
        f"/rest/v1/{REFLECTIONS_READ_TABLE}",
        params=[
            ("owner_user_id", f"eq.{uid}"),
            ("source_type", f"eq.{EMOTION_REFLECTION_SOURCE_TYPE}"),
            ("published_at", f"gte.{start_iso}"),
            ("published_at", f"lt.{end_iso}"),
        ],
        timeout=8.0,
    )
    return {
        "month_key": month_key,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "published_count": int(published_count or 0),
    }


__all__ = [
    "EMOTION_REFLECTION_SOURCE_TYPE",
    "EMOTION_REFLECTION_VERSION",
    "cancel_preview_draft",
    "count_published_emotion_reflections_for_month",
    "create_preview_draft",
    "fetch_preview_draft",
    "publish_preview_draft",
]
