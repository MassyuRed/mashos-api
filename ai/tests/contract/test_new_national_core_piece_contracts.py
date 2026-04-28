from __future__ import annotations

import asyncio

import pytest


def test_core_contract_registry_fixes_three_new_national_cores():
    import core_contract_registry as registry

    core_ids = set(registry.core_ids())
    assert core_ids == {"emlis_ai", "analysis", "piece"}
    assert len(registry.core_contract_ids()) == len(set(registry.core_contract_ids()))

    piece = registry.get_core_contract("piece")
    assert piece is not None
    assert piece.publish_policy == "preview_ready_to_published_status_only"
    assert "preview" in piece.primary_route
    assert "publish" in piece.primary_route


def test_emotion_piece_preview_contract_adds_piece_text_and_core_meta():
    from api_emotion_piece import EmotionPiecePreviewResponse, EmotionPieceQuotaResponse

    quota = EmotionPieceQuotaResponse(
        subscription_tier="free",
        month_key="2026-04",
        publish_limit=3,
        published_count=0,
        remaining_count=3,
        can_publish=True,
    )
    response = EmotionPiecePreviewResponse(
        preview_id="preview-1",
        question="最近気になることは？",
        reflection_text="最近気になっているのは、疲れが残っていることです。",
        piece_text="最近気になっているのは、疲れが残っていることです。",
        answer_display_state="ready",
        visibility_status="preview_ready",
        generation_status="fallback_generated",
        transform_mode="low_info",
        safety_level="needs_transform",
        safety_flags=["low_info"],
        quota=quota,
        meta={"source_input_scope": "current_input_only"},
    )

    body = response.dict()
    assert body["piece_text"] == body["reflection_text"]
    assert body["visibility_status"] == "preview_ready"
    assert body["generation_status"] == "fallback_generated"
    assert body["transform_mode"] == "low_info"
    assert body["safety_level"] == "needs_transform"
    assert body["safety_flags"] == ["low_info"]


def test_piece_generation_policy_removes_url_before_preview():
    from emotion_piece_generation_service import generate_emotion_reflection_preview

    preview = generate_emotion_reflection_preview(
        emotion_details=[{"type": "怒り", "strength": "strong"}],
        memo="このサイト見て https://example.com",
        memo_action=None,
        categories=[],
    )

    text = preview["answer_display_text"]
    policy = preview["piece_policy"].as_storage_meta()
    assert "http" not in text
    assert "example.com" not in text
    assert policy["transform_mode"] == "abstracted"
    assert policy["safety_level"] == "high_risk_transformed"
    assert "url_removed" in policy["safety_flags"]
    assert "external_redirect_removed" in policy["safety_flags"]


def test_piece_generation_policy_abstracts_attack_target_before_preview():
    from emotion_piece_generation_service import generate_emotion_reflection_preview

    preview = generate_emotion_reflection_preview(
        emotion_details=[{"type": "怒り", "strength": "strong"}],
        memo="〇〇がムカつく。消えてほしい。",
        memo_action=None,
        categories=[],
    )

    text = preview["answer_display_text"]
    policy = preview["piece_policy"].as_storage_meta()
    assert "〇〇" not in text
    assert "ムカつく" not in text
    assert "消えてほしい" not in text
    assert policy["transform_mode"] == "abstracted"
    assert policy["safety_level"] == "high_risk_transformed"
    assert "target_removed" in policy["safety_flags"]
    assert "attack_removed" in policy["safety_flags"]


def test_piece_generation_policy_keeps_low_info_piece_publishable():
    from emotion_piece_generation_service import generate_emotion_reflection_preview

    preview = generate_emotion_reflection_preview(
        emotion_details=[{"type": "悲しみ", "strength": "strong"}],
        memo="疲れた",
        memo_action=None,
        categories=[],
    )

    text = preview["answer_display_text"]
    policy = preview["piece_policy"].as_storage_meta()
    assert text
    assert policy["generation_status"] == "fallback_generated"
    assert policy["transform_mode"] == "low_info"
    assert "low_info" in policy["safety_flags"]
    assert policy["piece_text_hash"]


def test_publish_preview_draft_promotes_same_preview_hash(monkeypatch):
    import emotion_piece_store as store
    from piece_generation_policy import build_piece_generation_policy, compute_piece_text_hash

    preview_text = "最近気になっているのは、疲れが残っていることです。"
    policy = build_piece_generation_policy(
        piece_text=preview_text,
        raw_answer="疲れた",
        source_texts=["疲れた"],
    ).as_storage_meta()
    content_json = {
        "display": {"answer_display_text": preview_text},
        "answer_display_text": preview_text,
        "display_answer": preview_text,
        "national_core": policy,
        "piece_core": policy,
        "piece_text_hash": policy["piece_text_hash"],
    }
    row = {
        "id": "preview-1",
        "owner_user_id": "user-1",
        "source_type": store.EMOTION_REFLECTION_SOURCE_TYPE,
        "status": "draft",
        "question": "最近気になることは？",
        "answer": "疲れた",
        "content_json": content_json,
    }
    captured = {}

    async def fake_fetch_preview_draft(*, preview_id: str, user_id: str):
        assert preview_id == "preview-1"
        assert user_id == "user-1"
        return dict(row)

    async def fake_sb_patch_json(*args, **kwargs):
        captured["json_body"] = kwargs["json_body"]
        return [
            {
                **row,
                "status": "ready",
                "is_active": True,
                "published_at": kwargs["json_body"]["published_at"],
                "content_json": kwargs["json_body"]["content_json"],
            }
        ]

    monkeypatch.setattr(store, "fetch_preview_draft", fake_fetch_preview_draft)
    monkeypatch.setattr(store, "_sb_patch_json", fake_sb_patch_json)

    published = asyncio.run(
        store.publish_preview_draft(
            preview_id="preview-1",
            user_id="user-1",
            published_at="2026-04-27T00:00:00Z",
            emotion_entry={"id": "emotion-1", "created_at": "2026-04-27T00:00:00Z"},
        )
    )

    national_core = published["content_json"]["national_core"]
    assert national_core["visibility_status"] == "published"
    assert national_core["piece_text_hash"] == compute_piece_text_hash(preview_text)
    assert national_core["published_text_hash"] == national_core["piece_text_hash"]
    assert published["content_json"]["display_answer"] == preview_text
    assert captured["json_body"]["status"] == "ready"
    assert captured["json_body"]["is_active"] is True


def test_publish_preview_draft_rejects_preview_text_hash_mismatch(monkeypatch):
    import emotion_piece_store as store
    from piece_generation_policy import build_piece_generation_policy

    preview_text = "最近気になっているのは、疲れが残っていることです。"
    other_policy = build_piece_generation_policy(
        piece_text="別の本文です。",
        raw_answer="疲れた",
        source_texts=["疲れた"],
    ).as_storage_meta()
    row = {
        "id": "preview-1",
        "owner_user_id": "user-1",
        "source_type": store.EMOTION_REFLECTION_SOURCE_TYPE,
        "status": "draft",
        "question": "最近気になることは？",
        "answer": "疲れた",
        "content_json": {
            "display": {"answer_display_text": preview_text},
            "answer_display_text": preview_text,
            "display_answer": preview_text,
            "national_core": other_policy,
            "piece_core": other_policy,
            "piece_text_hash": other_policy["piece_text_hash"],
        },
    }

    async def fake_fetch_preview_draft(*, preview_id: str, user_id: str):
        return dict(row)

    monkeypatch.setattr(store, "fetch_preview_draft", fake_fetch_preview_draft)

    with pytest.raises(RuntimeError, match="hash mismatch"):
        asyncio.run(
            store.publish_preview_draft(
                preview_id="preview-1",
                user_id="user-1",
                published_at="2026-04-27T00:00:00Z",
            )
        )
