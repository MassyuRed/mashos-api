# -*- coding: utf-8 -*-
"""emotion_submit_service.py

Shared helpers for emotion persistence flows.

Purpose
-------
- Keep `/emotion/submit` semantics unchanged.
- Allow new routes such as `/emotion/reflection/publish` to reuse the same
  normalization / insert / cache invalidation / background task pipeline
  without HTTP self-calls.

Notes
-----
- This module intentionally reuses the existing private helpers from
  `api_emotion_submit.py` to minimize blast radius for the current release.
- The public API here is small and additive.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence, Union

from fastapi import HTTPException

from api_emotion_submit import (
    ALLOW_LEGACY_USER_ID,
    EmotionItem,
    _build_input_feedback_comment,
    _extract_bearer_token,
    _global_summary_activity_date_from_created_at,
    _insert_emotion_row,
    _normalize_categories,
    _normalize_emotions,
    _resolve_user_id_from_token,
    _start_post_submit_background_tasks,
)
from emlis_ai_reply_service import render_emlis_ai_reply
from response_microcache import invalidate_prefix
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user


async def resolve_authenticated_user_id(
    *,
    authorization: Optional[str],
    legacy_user_id: Optional[str] = None,
) -> str:
    """Resolve authenticated user id with the same policy as `/emotion/submit`."""
    access_token = _extract_bearer_token(authorization)
    if access_token:
        return await _resolve_user_id_from_token(access_token)

    if ALLOW_LEGACY_USER_ID and legacy_user_id:
        return str(legacy_user_id)

    raise HTTPException(
        status_code=401,
        detail="Authorization header with Bearer token is required",
    )


def normalize_submission_payload(
    *,
    emotions: Sequence[Union[EmotionItem, str]],
    memo: Optional[str],
    memo_action: Optional[str],
    category: Optional[Sequence[str]],
) -> Dict[str, Any]:
    """Normalize emotion submit payload into storage-ready values."""
    emotions_tags, emotion_details, avg_strength = _normalize_emotions(emotions)
    if not emotions_tags:
        raise HTTPException(status_code=400, detail="At least one emotion is required")

    normalized_categories = _normalize_categories(category)
    has_memo_input = bool(str(memo or "").strip() or str(memo_action or "").strip())
    if not has_memo_input:
        normalized_categories = []

    return {
        "emotions_tags": emotions_tags,
        "emotion_details": emotion_details,
        "emotion_strength_avg": avg_strength,
        "category": normalized_categories,
        "has_memo_input": has_memo_input,
    }


async def persist_emotion_submission(
    *,
    user_id: str,
    emotions: Sequence[Union[EmotionItem, str]],
    memo: Optional[str],
    memo_action: Optional[str],
    category: Optional[Sequence[str]],
    created_at: Optional[str] = None,
    is_secret: bool = False,
    notify_friends: bool = True,
) -> Dict[str, Any]:
    """Persist one emotion submission and trigger the existing post-submit flow."""
    normalized = normalize_submission_payload(
        emotions=emotions,
        memo=memo,
        memo_action=memo_action,
        category=category,
    )

    effective_created_at = str(created_at or "").strip() or datetime.now(timezone.utc).isoformat()
    inserted = await _insert_emotion_row(
        user_id=str(user_id or "").strip(),
        emotions=normalized["emotions_tags"],
        emotion_details=normalized["emotion_details"],
        emotion_strength_avg=normalized["emotion_strength_avg"],
        memo=memo,
        memo_action=memo_action,
        category=normalized["category"],
        created_at=effective_created_at,
        is_secret=bool(is_secret),
    )

    try:
        await invalidate_prefix(f"input_summary:{user_id}")
    except Exception:
        pass

    try:
        await invalidate_prefix(f"myweb_home_summary:{user_id}")
    except Exception:
        pass

    try:
        activity_date = _global_summary_activity_date_from_created_at(
            inserted.get("created_at", effective_created_at)
        )
        await invalidate_prefix(f"global_summary:{activity_date}:")
    except Exception:
        pass

    _start_post_submit_background_tasks(
        user_id=str(user_id or "").strip(),
        emotion_details=normalized["emotion_details"],
        created_at=effective_created_at,
        avg_strength=normalized["emotion_strength_avg"],
        memo=memo,
        is_secret=bool(is_secret),
        notify_friends=bool(notify_friends),
    )

    input_feedback_seed = (
        f"{inserted.get('id') or ''}|{inserted.get('created_at', effective_created_at) or effective_created_at}"
    )

    current_input = {
        "id": inserted.get("id"),
        "created_at": inserted.get("created_at", effective_created_at),
        "emotions": normalized["emotions_tags"],
        "emotion_details": normalized["emotion_details"],
        "memo": memo,
        "memo_action": memo_action,
        "category": normalized["category"],
        "is_secret": bool(is_secret),
        "selection_seed": input_feedback_seed,
    }

    input_feedback_comment = ""
    input_feedback_meta: Dict[str, Any] = {}
    try:
        subscription_tier = await get_subscription_tier_for_user(
            str(user_id or "").strip(),
            default=SubscriptionTier.FREE,
        )
    except Exception:
        subscription_tier = SubscriptionTier.FREE

    try:
        reply = await render_emlis_ai_reply(
            user_id=str(user_id or "").strip(),
            subscription_tier=subscription_tier,
            current_input=current_input,
        )
        input_feedback_comment = str(reply.comment_text or "").strip()
        input_feedback_meta = reply.meta if isinstance(reply.meta, dict) else {}
    except Exception:
        input_feedback_comment = _build_input_feedback_comment(
            emotion_details=normalized["emotion_details"],
            memo=memo,
            memo_action=memo_action,
            category=normalized["category"],
            selection_seed=input_feedback_seed,
        )
        input_feedback_meta = {
            "version": "emlis_ai_v2",
            "kernel_version": "observation_kernel.v2",
            "tier": str(getattr(subscription_tier, "value", subscription_tier) or "free"),
            "capability": {
                "history_mode": "none",
                "continuity_mode": "off",
                "style_mode": "base",
                "partner_mode": "off",
                "model_mode": "off",
                "interpretation_mode": "current_only",
            },
            "used_sources": ["current_input"],
            "used_memory_layers": ["canonical_history"],
            "reply_length_mode": "short_present_only",
            "evidence_count": 0,
            "evidence_by_line": {},
            "rejected_candidate_count": 0,
            "fallback_used": True,
            "model_revision": None,
            "world_model_debug": {},
        }

    return {
        "inserted": inserted,
        "created_at": inserted.get("created_at", effective_created_at),
        "input_feedback_comment": input_feedback_comment,
        "input_feedback_meta": input_feedback_meta,
        "normalized": normalized,
    }


__all__ = [
    "normalize_submission_payload",
    "persist_emotion_submission",
    "resolve_authenticated_user_id",
]
