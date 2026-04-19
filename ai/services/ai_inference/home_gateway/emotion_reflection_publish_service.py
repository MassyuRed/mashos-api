from __future__ import annotations

import sys

from typing import Any, Dict

from fastapi import HTTPException

from api_emotion_submit import EmotionItem
from emotion_reflection_store import (
    count_published_emotion_reflections_for_month,
    fetch_preview_draft,
    publish_preview_draft,
)
from reflection_publish_entitlements import (
    get_reflection_publish_policy_for_user,
    resolve_reflection_publish_limit_for_tier,
)
from subscription import SubscriptionTier, normalize_subscription_tier

from .emotion_submit_service import persist_emotion_submission


def _reflection_module_override(name: str, default: Any) -> Any:
    module = sys.modules.get("api_emotion_reflection")
    if module is None:
        return None
    candidate = getattr(module, name, None)
    if not callable(candidate) or candidate is default:
        return None
    return candidate


async def _call_fetch_preview_draft(*, preview_id: str, user_id: str) -> Dict[str, Any] | None:
    override = _reflection_module_override("fetch_preview_draft", fetch_preview_draft)
    if override is not None:
        return await override(preview_id=preview_id, user_id=user_id)
    return await fetch_preview_draft(preview_id=preview_id, user_id=user_id)


async def _call_build_quota_status(user_id: str) -> Dict[str, Any]:
    override = _reflection_module_override("_build_quota_status", build_emotion_reflection_quota_status)
    if override is not None:
        return await override(user_id)
    return await build_emotion_reflection_quota_status(user_id)


async def _call_persist_emotion_submission(**kwargs: Any) -> Dict[str, Any]:
    override = _reflection_module_override("persist_emotion_submission", persist_emotion_submission)
    if override is not None:
        return await override(**kwargs)
    return await persist_emotion_submission(**kwargs)


async def _call_publish_preview_draft(**kwargs: Any) -> Dict[str, Any]:
    override = _reflection_module_override("publish_preview_draft", publish_preview_draft)
    if override is not None:
        return await override(**kwargs)
    return await publish_preview_draft(**kwargs)


def _coerce_stored_emotions(raw_items: Any) -> list[Any]:
    if not isinstance(raw_items, list):
        return []
    out: list[Any] = []
    for item in raw_items:
        if isinstance(item, EmotionItem):
            out.append(item)
            continue
        if isinstance(item, dict):
            emotion_type = str(item.get("type") or "").strip()
            strength = str(item.get("strength") or "medium").strip().lower() or "medium"
            if not emotion_type:
                continue
            try:
                out.append(EmotionItem(type=emotion_type, strength=strength))
                continue
            except Exception:
                out.append(emotion_type)
                continue
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


async def build_emotion_reflection_quota_status(user_id: str) -> Dict[str, Any]:
    policy = await get_reflection_publish_policy_for_user(user_id)
    usage = await count_published_emotion_reflections_for_month(user_id=user_id)
    tier = normalize_subscription_tier(policy.get("subscription_tier"), default=SubscriptionTier.FREE)
    publish_limit = resolve_reflection_publish_limit_for_tier(tier)
    published_count = int(usage.get("published_count") or 0)
    remaining_count = None if publish_limit is None else max(0, int(publish_limit) - published_count)
    can_publish = True if publish_limit is None else published_count < int(publish_limit)
    return {
        "status": "ok",
        "subscription_tier": tier.value,
        "month_key": usage.get("month_key"),
        "publish_limit": publish_limit,
        "published_count": published_count,
        "remaining_count": remaining_count,
        "can_publish": can_publish,
    }


async def publish_emotion_reflection_preview(*, user_id: str, preview_id: str) -> Dict[str, Any]:
    draft = await _call_fetch_preview_draft(preview_id=preview_id, user_id=user_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Reflection preview not found")
    if str(draft.get("status") or "").strip().lower() != "draft":
        raise HTTPException(status_code=400, detail="Reflection preview is no longer publishable")

    quota = await _call_build_quota_status(user_id)
    if not quota.get("can_publish"):
        raise HTTPException(status_code=403, detail="Reflection publish quota exceeded")

    content_json = draft.get("content_json") if isinstance(draft.get("content_json"), dict) else {}
    preview_input = content_json.get("emotion_preview") if isinstance(content_json.get("emotion_preview"), dict) else {}
    stored_emotions = _coerce_stored_emotions(preview_input.get("emotions"))
    created_at = str(preview_input.get("created_at") or "").strip() or None
    notify_friends = True if preview_input.get("notify_friends") is None else bool(preview_input.get("notify_friends"))
    category = preview_input.get("category") if isinstance(preview_input.get("category"), list) else []
    memo = preview_input.get("memo")
    memo_action = preview_input.get("memo_action")

    persisted = await _call_persist_emotion_submission(
        user_id=user_id,
        emotions=stored_emotions,
        memo=memo,
        memo_action=memo_action,
        category=category,
        created_at=created_at,
        is_secret=False,
        notify_friends=notify_friends,
    )
    published_row = await _call_publish_preview_draft(
        preview_id=preview_id,
        user_id=user_id,
        published_at=str(persisted.get("created_at") or created_at or ""),
        emotion_entry=persisted.get("inserted") if isinstance(persisted.get("inserted"), dict) else None,
    )
    next_quota = await _call_build_quota_status(user_id)
    display_bundle = content_json.get("display") if isinstance(content_json.get("display"), dict) else {}
    reflection_text = str(
        display_bundle.get("answer_display_text")
        or content_json.get("answer_display_text")
        or published_row.get("answer")
        or ""
    )
    input_feedback = None
    if str(persisted.get("input_feedback_comment") or "").strip():
        input_feedback = {
            "comment_text": persisted.get("input_feedback_comment"),
            "emlis_ai": persisted.get("input_feedback_meta") if isinstance(persisted.get("input_feedback_meta"), dict) else None,
        }
    return {
        "status": "ok",
        "preview_id": str(preview_id),
        "reflection_id": str(published_row.get("id") or preview_id),
        "emotion_id": (persisted.get("inserted") or {}).get("id") if isinstance(persisted.get("inserted"), dict) else None,
        "created_at": str(persisted.get("created_at") or created_at or ""),
        "question": str(published_row.get("question") or draft.get("question") or ""),
        "reflection_text": reflection_text,
        "quota": next_quota,
        "input_feedback": input_feedback,
        "global_summary_activity_date": persisted.get("global_summary_activity_date"),
    }
