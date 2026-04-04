from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional


def test_generated_reflection_display_rewrites_broken_answer():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="大切にしていることは？",
        raw_answer="完全に元通りとは言えないけど、突発性難聴は治ったら終わりじゃなくて、まず一番大事なのは。",
        category="生活",
        focus_key="values",
        topic_summary_text="生活 / 完全に元通りとは言えないけど / 突発性難聴は治ったら終わりじゃなくて / まず一番大事なのは",
    )

    assert result.answer_display_state in {"ready", "masked"}
    assert result.answer_display_text is not None
    assert "大切にしているのは" in result.answer_display_text
    assert "まず一番大事なのは。" not in result.answer_display_text
    assert result.answer_norm_hash


def test_generated_qna_detail_uses_display_text(client, monkeypatch):
    import api_mymodel_qna as qna_module

    generated_row: Dict[str, Any] = {
        "id": "generated-row-1",
        "public_id": "reflection:test-generated-1",
        "owner_user_id": "owner-generated-1",
        "source_type": "generated",
        "topic_key": "topic-generated-1",
        "category": "趣味",
        "question": "最近夢中なことは？",
        "answer": "今日は体がだるくてずっと寝てるし、やたら お腹すいて色々食べてるだけだったけど お話練習したくて配信見に行って少しずつ コメントしてお話できたから お話。",
        "content_json": {
            "focus_key": "fun",
            "topic_summary_text": "趣味 / 配信見に行って少しずつコメントして話した / お話",
        },
    }

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "viewer-generated-1"

    async def fake_resolve_generated_reflection_access(*, viewer_user_id: str, q_instance_id: str):
        return dict(generated_row)

    async def fake_fetch_instance_metrics(_instance_ids):
        return {"reflection:test-generated-1": {"views": 3, "resonances": 2}}

    async def fake_sb_count_rows(path, *, params=None):
        return 1

    async def fake_fetch_reads(viewer_user_id: str, q_instance_ids):
        return set()

    async def fake_is_resonated(viewer_user_id: str, q_instance_id: str):
        return False

    monkeypatch.setattr(qna_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(qna_module, "_resolve_generated_reflection_access", fake_resolve_generated_reflection_access)
    monkeypatch.setattr(qna_module, "_fetch_instance_metrics", fake_fetch_instance_metrics)
    monkeypatch.setattr(qna_module, "_sb_count_rows", fake_sb_count_rows)
    monkeypatch.setattr(qna_module, "_fetch_reads", fake_fetch_reads)
    monkeypatch.setattr(qna_module, "_is_resonated", fake_is_resonated)

    response = client.get(
        "/mymodel/qna/detail?q_instance_id=reflection:test-generated-1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    body = response.json()["body"]
    assert "最近夢中なのは" in body
    assert "お話。" not in body


def test_generated_reaction_context_uses_display_text(monkeypatch):
    import api_mymodel_qna as qna_module

    generated_row: Dict[str, Any] = {
        "id": "generated-row-ctx",
        "public_id": "reflection:test-generated-ctx",
        "owner_user_id": "owner-generated-ctx",
        "source_type": "generated",
        "topic_key": "topic-generated-ctx",
        "category": "生活",
        "question": "人との関わりで大切なことは？",
        "answer": "でもずっとこのままじゃ嫌だから 耳の治療が終わって もう普通に近い生活に戻れた時 交流をもっと増やせるようになるには どうしたらいいか考えてみた まえにやってたみたいに自分がコメント側で新しい 人と会話すること ききせんでも全然ありかもしれない 少しずつはじめていこうかな。",
        "content_json": {
            "focus_key": "relationship",
            "topic_summary_text": "生活 / 交流をもっと増やしたい / コメント側で会話してみたい",
        },
    }

    async def fake_resolve_generated_reflection_access(*, viewer_user_id: str, q_instance_id: str):
        return dict(generated_row)

    monkeypatch.setattr(qna_module, "_resolve_generated_reflection_access", fake_resolve_generated_reflection_access)

    ctx = asyncio.run(
        qna_module._resolve_qna_context_for_reaction(
            viewer_user_id="viewer-generated-ctx",
            q_instance_id="reflection:test-generated-ctx",
            q_key=None,
        )
    )

    assert ctx["kind"] == "generated"
    assert ctx["context_answer"]
    assert "人との関わりでは" in ctx["context_answer"]
    assert "少しずつ交流を広げること" in ctx["context_answer"]


def test_generated_detail_hides_blocked_text(client, monkeypatch):
    import api_mymodel_qna as qna_module

    generated_row: Dict[str, Any] = {
        "id": "generated-row-blocked",
        "public_id": "reflection:test-generated-blocked",
        "owner_user_id": "owner-generated-blocked",
        "source_type": "generated",
        "topic_key": "topic-generated-blocked",
        "category": "生活",
        "question": "最近気になることは？",
        "answer": "住所を晒してやる。殺してやる。",
        "content_json": {"focus_key": "generic"},
    }

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "viewer-generated-blocked"

    async def fake_resolve_generated_reflection_access(*, viewer_user_id: str, q_instance_id: str):
        return dict(generated_row)

    monkeypatch.setattr(qna_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(qna_module, "_resolve_generated_reflection_access", fake_resolve_generated_reflection_access)

    response = client.get(
        "/mymodel/qna/detail?q_instance_id=reflection:test-generated-blocked",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 404, response.text


def test_generated_stage_skips_same_as_active(monkeypatch):
    import astor_reflection_store as store_module
    from generated_reflection_identity import compute_generated_question_q_key

    active_row: Dict[str, Any] = {
        "id": "active-generated-1",
        "public_id": "reflection:active-generated-1",
        "owner_user_id": "owner-generated-dup",
        "source_type": "generated",
        "topic_key": "topic-generated-dup",
        "category": "趣味",
        "question": "最近夢中なことは？",
        "answer": "今日は体がだるくてずっと寝てるし、やたら お腹すいて色々食べてるだけだったけど お話練習したくて配信見に行って少しずつ コメントしてお話できたから お話。",
        "content_json": {
            "focus_key": "fun",
            "topic_summary_text": "趣味 / 配信見に行って少しずつコメントして話した / お話",
        },
    }

    q_key = compute_generated_question_q_key("最近夢中なことは？")

    async def fake_fetch_active_generated_public_group_rows(*, user_id: str, q_key: str, question: str, exclude_id: Optional[str] = None):
        assert q_key == compute_generated_question_q_key(question)
        return [dict(active_row)]

    monkeypatch.setattr(store_module, "_fetch_active_generated_public_group_rows", fake_fetch_active_generated_public_group_rows)

    result = asyncio.run(
        store_module._upsert_staged_generated_row(
            user_id="owner-generated-dup",
            topic_key="topic-generated-dup",
            q_key=q_key,
            category="趣味",
            question="最近夢中なことは？",
            answer="今日は体がだるくてずっと寝てるし、やたら お腹すいて色々食べてるだけだったけど お話練習したくて配信見に行って少しずつ コメントしてお話できたから お話。",
            source_snapshot_id="snapshot-generated-dup",
            source_hash="source-hash-generated-dup",
            source_refs=[],
            topic_summary_text="趣味 / 配信見に行って少しずつコメントして話した / お話",
            topic_embedding=[],
            focus_key="fun",
            previous_reflection_id=None,
            locked=False,
            lock_note=None,
        )
    )

    assert result["_stage_action"] == "skip_same_as_active"
    assert result["id"] == "active-generated-1"


def test_generated_reflection_display_blocks_low_quality_values_fragment():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="大切にしていることは？",
        raw_answer="久々に枠とって歌った",
        category="趣味",
        focus_key="values",
        topic_summary_text="趣味 / 久々に枠とって歌った",
    )

    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None
    assert "quality:block" in result.actions


def test_generated_reflection_display_rewrites_fun_song_fragment():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="最近夢中なことは？",
        raw_answer="久々に枠とって歌った",
        category="趣味",
        focus_key="fun",
        topic_summary_text="趣味 / 久々に枠とって歌った",
    )

    assert result.answer_display_state in {"ready", "masked"}
    assert result.answer_display_text is not None
    assert "歌うこと" in result.answer_display_text
