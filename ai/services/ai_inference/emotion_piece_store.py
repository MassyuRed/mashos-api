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
from piece_generation_policy import (
    VISIBILITY_PREVIEW_READY,
    VISIBILITY_PUBLISHED,
    compute_piece_text_hash,
    piece_policy_from_content_json,
    with_piece_policy_visibility,
)
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
    piece_policy: Any = None,
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
    answer_display_text = str(content_json.get("answer_display_text") or "").strip()
    policy = piece_policy
    if policy is None:
        from piece_generation_policy import build_piece_generation_policy

        policy = build_piece_generation_policy(
            piece_text=answer_display_text,
            raw_answer=raw_answer,
            display_result=display_result,
            emotion_input=emotion_input,
        )
    policy = with_piece_policy_visibility(
        policy,
        visibility_status=VISIBILITY_PREVIEW_READY,
        piece_text=answer_display_text,
    )
    piece_core = policy.as_storage_meta()
    content_json = {
        **content_json,
        "display_question": str(question or "").strip(),
        "display_answer": answer_display_text,
        "piece_text_hash": piece_core.get("piece_text_hash"),
        "national_core": piece_core,
        "piece_core": piece_core,
        "previewed_at": now_iso,
    }

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
    display_bundle = content_json.get("display") if isinstance(content_json.get("display"), dict) else {}
    preview_text = str(
        display_bundle.get("answer_display_text")
        or content_json.get("answer_display_text")
        or content_json.get("display_answer")
        or row.get("answer")
        or ""
    ).strip()
    current_hash = compute_piece_text_hash(preview_text)
    policy = piece_policy_from_content_json(content_json)
    stored_hash = str(policy.piece_text_hash or content_json.get("piece_text_hash") or "").strip()
    if stored_hash and current_hash and stored_hash != current_hash:
        raise RuntimeError("Emotion Piece preview text hash mismatch")

    published_policy = with_piece_policy_visibility(
        policy,
        visibility_status=VISIBILITY_PUBLISHED,
        piece_text=preview_text,
    )
    piece_core = {
        **published_policy.as_storage_meta(),
        "published_text_hash": current_hash or stored_hash,
    }
    content_json = {
        **content_json,
        "display_answer": preview_text,
        "piece_text_hash": current_hash or stored_hash,
        "national_core": piece_core,
        "piece_core": piece_core,
    }
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
