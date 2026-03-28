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
    import api_mymodel_create as create_module

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
        "/mymodel/create/answers",
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

    answer_rows: Dict[int, Dict[str, Any]] = {
        1: {
            "question_id": 1,
            "answer_text": "foo@example.com",
            "updated_at": "2026-03-28T00:00:00Z",
            "is_secret": False,
            "reflection_display_text": "[メールアドレス]",
            "reflection_display_state": "masked",
            "reflection_format_version": "reflection.display.v1",
            "reflection_format_meta": {"version": "reflection.display.v1", "changed": True},
        }
    }

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "owner-1"

    async def fake_resolve_tiers(*, viewer_user_id: str, target_user_id: str):
        return ("free", "light", "light", "light")

    async def fake_fetch_create_questions(*, build_tier: str):
        return [{"id": 1, "question_text": "Question 1"}]

    async def fake_fetch_create_answers(*, user_id: str, question_ids=None):
        return dict(answer_rows)

    async def fake_fetch_instance_metrics(_instance_ids):
        return {"owner-1:1": {"views": 0, "resonances": 0}}

    async def fake_sb_count_rows(path, *, params=None):
        return 0

    async def fake_fetch_reads(viewer_user_id: str, q_instance_ids):
        return set()

    async def fake_is_resonated(viewer_user_id: str, q_instance_id: str):
        return False

    monkeypatch.setattr(qna_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(qna_module, "_resolve_tiers", fake_resolve_tiers)
    monkeypatch.setattr(qna_module, "_fetch_create_questions", fake_fetch_create_questions)
    monkeypatch.setattr(qna_module, "_fetch_create_answers", fake_fetch_create_answers)
    monkeypatch.setattr(qna_module, "_fetch_instance_metrics", fake_fetch_instance_metrics)
    monkeypatch.setattr(qna_module, "_sb_count_rows", fake_sb_count_rows)
    monkeypatch.setattr(qna_module, "_fetch_reads", fake_fetch_reads)
    monkeypatch.setattr(qna_module, "_is_resonated", fake_is_resonated)

    response = client.get(
        "/mymodel/qna/detail?q_instance_id=owner-1:1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["body"] == "[メールアドレス]"

    answer_rows[1] = {
        "question_id": 1,
        "answer_text": "住所を晒してやる。殺してやる。",
        "updated_at": "2026-03-28T00:00:00Z",
        "is_secret": False,
        "reflection_display_text": None,
        "reflection_display_state": "blocked",
        "reflection_format_version": "reflection.display.v1",
        "reflection_format_meta": {"version": "reflection.display.v1", "changed": True},
    }

    blocked_response = client.get(
        "/mymodel/qna/detail?q_instance_id=owner-1:1",
        headers={"Authorization": "Bearer test-token"},
    )
    assert blocked_response.status_code == 404, blocked_response.text


def test_qna_reaction_context_uses_display_text(monkeypatch):
    import api_mymodel_qna as qna_module

    async def fake_resolve_tiers(*, viewer_user_id: str, target_user_id: str):
        return ("free", "light", "light", "light")

    async def fake_fetch_create_questions(*, build_tier: str):
        return [{"id": 3, "question_text": "Question 3"}]

    async def fake_fetch_create_answers(*, user_id: str, question_ids=None):
        return {
            3: {
                "question_id": 3,
                "answer_text": "foo@example.com",
                "updated_at": "2026-03-28T00:00:00Z",
                "is_secret": False,
                "reflection_display_text": "[メールアドレス]",
                "reflection_display_state": "masked",
                "reflection_format_version": "reflection.display.v1",
                "reflection_format_meta": {"version": "reflection.display.v1", "changed": True},
            }
        }

    monkeypatch.setattr(qna_module, "_resolve_tiers", fake_resolve_tiers)
    monkeypatch.setattr(qna_module, "_fetch_create_questions", fake_fetch_create_questions)
    monkeypatch.setattr(qna_module, "_fetch_create_answers", fake_fetch_create_answers)

    ctx = asyncio.run(
        qna_module._resolve_qna_context_for_reaction(
            viewer_user_id="owner-ctx",
            q_instance_id="owner-ctx:3",
            q_key=None,
        )
    )

    assert ctx["kind"] == "create"
    assert ctx["context_answer"] == "[メールアドレス]"


def test_public_snapshot_uses_display_text_and_excludes_blocked(monkeypatch):
    import astor_material_snapshots as snapshots_module

    async def fake_fetch_optional_rows_by_user(*, table: str, user_id: str, user_id_column: str = "user_id", include_secret: bool = True, page_size: int = 1000, max_rows: int = 20000):
        return [
            {
                "id": "row-1",
                "user_id": user_id,
                "answer_text": "連絡先は foo@example.com です。",
                "updated_at": "2026-03-28T00:00:00Z",
                "created_at": "2026-03-27T00:00:00Z",
                "is_secret": False,
            },
            {
                "id": "row-2",
                "user_id": user_id,
                "answer_text": "住所を晒してやる。殺してやる。",
                "updated_at": "2026-03-28T00:00:00Z",
                "created_at": "2026-03-27T00:00:00Z",
                "is_secret": False,
            },
        ]

    monkeypatch.setattr(snapshots_module, "_fetch_optional_rows_by_user", fake_fetch_optional_rows_by_user)

    rows = asyncio.run(
        snapshots_module.fetch_mymodel_create_rows_for_self_structure(
            "snapshot-user",
            include_secret=False,
        )
    )

    assert len(rows) == 1
    assert rows[0]["answer_text"] == "連絡先は [メールアドレス] です。"
    assert rows[0]["reflection_display_state"] == "masked"
