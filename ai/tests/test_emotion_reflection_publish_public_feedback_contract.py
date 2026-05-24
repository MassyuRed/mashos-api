from __future__ import annotations

import pytest

from home_gateway import emotion_reflection_publish_service as service


async def _fake_fetch_preview_draft(*, preview_id: str, user_id: str):
    assert preview_id == "preview-1"
    assert user_id == "user-1"
    return {
        "id": "preview-1",
        "status": "draft",
        "question": "今日の気持ちは？",
        "content_json": {
            "emotion_preview": {
                "emotions": [{"type": "不安", "strength": "medium"}],
                "created_at": "2026-05-23T00:00:00Z",
                "category": ["daily"],
                "memo": "入力本文",
                "memo_action": None,
                "notify_friends": False,
            },
            "display": {"answer_display_text": "published reflection"},
        },
    }


async def _fake_build_quota_status(_user_id: str):
    return {
        "status": "ok",
        "subscription_tier": "free",
        "month_key": "2026-05",
        "publish_limit": 3,
        "published_count": 1,
        "remaining_count": 2,
        "can_publish": True,
    }


async def _fake_publish_preview_draft(**_kwargs):
    return {
        "id": "reflection-1",
        "question": "今日の気持ちは？",
        "answer": "published reflection",
        "content_json": {
            "display": {"answer_display_text": "published reflection"},
            "piece_text_hash": "hash-1",
        },
    }


def _patch_publish_baseline(monkeypatch, *, persisted):
    async def fake_persist_emotion_submission(**_kwargs):
        return persisted

    monkeypatch.setattr(service, "_call_fetch_preview_draft", _fake_fetch_preview_draft)
    monkeypatch.setattr(service, "_call_build_quota_status", _fake_build_quota_status)
    monkeypatch.setattr(service, "_call_persist_emotion_submission", fake_persist_emotion_submission)
    monkeypatch.setattr(service, "_call_publish_preview_draft", _fake_publish_preview_draft)
    monkeypatch.setattr(
        service,
        "public_piece_contract_from_content_json",
        lambda *_args, **_kwargs: {
            "visibility_status": "published",
            "generation_status": "generated",
            "transform_mode": "normalized",
            "safety_level": "safe",
            "safety_flags": [],
        },
    )


@pytest.mark.asyncio
async def test_reflection_publish_includes_input_feedback_only_for_passed_public_meta(monkeypatch) -> None:
    _patch_publish_baseline(
        monkeypatch,
        persisted={
            "inserted": {"id": "emo-1"},
            "created_at": "2026-05-23T00:00:00Z",
            "input_feedback_comment": "Emlisの観測本文です。",
            "input_feedback_meta": {
                "schema_version": "emlis.public_input_feedback_meta.v1",
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "public_feedback_meta_boundary": {
                    "version": "emlis.public_feedback_meta_boundary.v1",
                    "sanitized": True,
                    "max_bytes": 12288,
                    "trimmed": False,
                    "internal_meta_returned": False,
                    "raw_input_included": False,
                    "comment_text_included": False,
                },
            },
        },
    )

    result = await service.publish_emotion_reflection_preview(user_id="user-1", preview_id="preview-1")

    assert result["input_feedback"]["comment_text"] == "Emlisの観測本文です。"
    assert result["input_feedback"]["emlis_ai"]["observation_status"] == "passed"


@pytest.mark.asyncio
async def test_reflection_publish_omits_meta_only_unavailable_input_feedback(monkeypatch) -> None:
    _patch_publish_baseline(
        monkeypatch,
        persisted={
            "inserted": {"id": "emo-1"},
            "created_at": "2026-05-23T00:00:00Z",
            "input_feedback_comment": "",
            "input_feedback_meta": {
                "schema_version": "emlis.public_input_feedback_meta.v1",
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "unavailable",
                "rejection_reasons": ["render_timeout"],
                "public_feedback_meta_boundary": {
                    "version": "emlis.public_feedback_meta_boundary.v1",
                    "sanitized": True,
                    "max_bytes": 12288,
                    "trimmed": True,
                    "internal_meta_returned": False,
                    "raw_input_included": False,
                    "comment_text_included": False,
                },
            },
        },
    )

    result = await service.publish_emotion_reflection_preview(user_id="user-1", preview_id="preview-1")

    assert result["input_feedback"] is None
