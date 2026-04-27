from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> Any:
        return self._payload


def test_reflection_formatter_masks_pii_and_lightly_normalizes():
    import reflection_text_formatter as formatter

    result = formatter.format_reflection_text(
        "  連絡は foo@example.com と 090-1234-5678 へ！！！\r\n\r\nよろしく。  "
    )

    assert result.display_state == formatter.STATE_MASKED
    assert result.display_text is not None
    assert "[メールアドレス]" in result.display_text
    assert "[電話番号]" in result.display_text
    assert "！！！" not in result.display_text
    assert result.changed is True


def test_reflection_formatter_blocks_severe_text():
    import reflection_text_formatter as formatter

    result = formatter.format_reflection_text("住所を晒してやる。殺してやる。")

    assert result.display_state == formatter.STATE_BLOCKED
    assert result.display_text is None
    assert "block:severe" in result.actions


def test_mymodel_create_answers_persists_reflection_display_columns(client, monkeypatch):
    import api_profile_create as create_module

    saved_batches = []

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-formatter"

    async def fake_touch_active_user(_user_id: str, activity: Optional[str] = None):
        return None

    async def fake_get_subscription_tier_for_user(_user_id: str):
        return create_module.SubscriptionTier.PLUS

    async def fake_fetch_questions_all_active():
        return [
            {"id": 1, "question_text": "Question 1", "sort_order": 1, "tier": "light", "is_active": True},
        ]

    async def fake_fetch_answers(*, user_id: str, question_ids=None):
        return {}

    async def fake_sb_post(path, *, params=None, json=None, prefer=None):
        saved_batches.extend(list(json or []))
        return _FakeResponse(201, [])

    async def fake_sb_delete(path, *, params=None):
        return _FakeResponse(204, [])

    async def fake_enqueue_global_snapshot_refresh(*args, **kwargs):
        return None

    async def fake_enqueue_account_status_refresh(*args, **kwargs):
        return None

    monkeypatch.setattr(create_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(create_module, "touch_active_user", fake_touch_active_user)
    monkeypatch.setattr(create_module, "get_subscription_tier_for_user", fake_get_subscription_tier_for_user)
    monkeypatch.setattr(create_module, "_fetch_questions_all_active", fake_fetch_questions_all_active)
    monkeypatch.setattr(create_module, "_fetch_answers", fake_fetch_answers)
    monkeypatch.setattr(create_module, "_sb_post", fake_sb_post)
    monkeypatch.setattr(create_module, "_sb_delete", fake_sb_delete)
    monkeypatch.setattr(create_module, "enqueue_global_snapshot_refresh", fake_enqueue_global_snapshot_refresh)
    monkeypatch.setattr(create_module, "enqueue_account_status_refresh", fake_enqueue_account_status_refresh)

    response = client.post(
        "/profile-create/answers",
        headers={"Authorization": "Bearer test-token"},
        json={
            "answers": [
                {
                    "question_id": 1,
                    "answer_text": "連絡先は foo@example.com と 090-1234-5678 です。",
                    "is_secret": False,
                }
            ]
        },
    )

    assert response.status_code == 200, response.text
    assert saved_batches, "expected at least one upsert payload"
    row = saved_batches[0]
    assert row["reflection_display_state"] == "masked"
    assert row["reflection_display_text"] == "連絡先は [メールアドレス] と [電話番号] です。"
    assert row["reflection_format_version"]
    assert isinstance(row["reflection_format_meta"], dict)
    assert response.json()["meta"]["reflection_formatting"]["masked_count"] == 1


def test_qna_detail_uses_public_display_text_and_hides_blocked_rows(client, monkeypatch):
    import api_mymodel_qna as qna_module
    import api_piece_runtime as piece_runtime_module
    import piece_public_read_service as piece_read_service

    reflection_row: Dict[str, Any] = {
        "id": "reflection-row-1",
        "public_id": "reflection:test-1",
        "owner_user_id": "owner-1",
        "question": "Question 1",
        "source_type": qna_module.EMOTION_GENERATED_SOURCE_TYPE,
    }
    current_body = {"value": "[メールアドレス]"}

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "owner-1"

    async def fake_resolve_generated_reflection_access(*, viewer_user_id: str, q_instance_id: str):
        assert viewer_user_id == "owner-1"
        assert q_instance_id == "reflection:test-1"
        return dict(reflection_row)

    def fake_get_public_generated_reflection_text(row):
        assert row.get("id") == "reflection-row-1"
        return current_body["value"]

    async def fake_fetch_instance_metrics(_instance_ids):
        return {"reflection:test-1": {"views": 0, "resonances": 0}}

    async def fake_fetch_reads(_viewer_user_id: str, _q_instance_ids):
        return set()

    async def fake_is_resonated(_viewer_user_id: str, _q_instance_id: str):
        return False

    def fake_build_generated_q_key(_row):
        return "generated:test"

    monkeypatch.setattr(piece_runtime_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(piece_read_service, "resolve_generated_reflection_access", fake_resolve_generated_reflection_access)
    monkeypatch.setattr(piece_read_service, "get_public_generated_reflection_text", fake_get_public_generated_reflection_text)
    monkeypatch.setattr(piece_read_service, "fetch_instance_metrics", fake_fetch_instance_metrics)
    monkeypatch.setattr(piece_read_service, "fetch_reads", fake_fetch_reads)
    monkeypatch.setattr(piece_read_service, "is_resonated", fake_is_resonated)
    monkeypatch.setattr(piece_read_service, "build_generated_q_key", fake_build_generated_q_key)

    response = client.get(
        "/mymodel/qna/detail?q_instance_id=reflection:test-1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["body"] == "[メールアドレス]"

    current_body["value"] = None

    blocked_response = client.get(
        "/mymodel/qna/detail?q_instance_id=reflection:test-1",
        headers={"Authorization": "Bearer test-token"},
    )
    assert blocked_response.status_code == 404, blocked_response.text


def test_qna_reaction_context_uses_display_text(monkeypatch):
    import api_mymodel_qna as qna_module
    import api_piece_runtime as piece_runtime_module

    async def fake_resolve_generated_reflection_access(*, viewer_user_id: str, q_instance_id: str):
        assert viewer_user_id == "owner-ctx"
        assert q_instance_id == "reflection:test-ctx"
        return {
            "id": "reflection-row-ctx",
            "owner_user_id": "owner-ctx",
            "question": "Question 3",
            "source_type": qna_module.EMOTION_GENERATED_SOURCE_TYPE,
        }

    def fake_get_public_generated_reflection_text(row):
        assert row.get("id") == "reflection-row-ctx"
        return "[メールアドレス]"

    monkeypatch.setattr(qna_module, "resolve_generated_reflection_access", fake_resolve_generated_reflection_access)
    monkeypatch.setattr(qna_module, "get_public_generated_reflection_text", fake_get_public_generated_reflection_text)

    ctx = asyncio.run(
        piece_runtime_module._resolve_qna_context_for_reaction(
            viewer_user_id="owner-ctx",
            q_instance_id="reflection:test-ctx",
            q_key="generated:test",
        )
    )

    assert ctx["kind"] == qna_module.EMOTION_GENERATED_SOURCE_TYPE
    assert ctx["context_answer"] == "[メールアドレス]"


def test_legacy_profilecreate_discovery_routes_are_removed(client):
    trending = client.get("/mymodel/qna/trending?limit=5&mode=overall")
    assert trending.status_code == 404, trending.text

    holders = client.get("/mymodel/qna/holders?question_id=7")
    assert holders.status_code == 404, holders.text
