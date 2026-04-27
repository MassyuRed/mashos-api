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
    import api_piece_runtime as piece_runtime_module
    import piece_public_read_service as piece_read_service

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

    async def fake_fetch_reads(viewer_user_id: str, q_instance_ids):
        return set()

    async def fake_is_resonated(viewer_user_id: str, q_instance_id: str):
        return False

    monkeypatch.setattr(piece_runtime_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(piece_read_service, "resolve_generated_reflection_access", fake_resolve_generated_reflection_access)
    monkeypatch.setattr(piece_read_service, "fetch_instance_metrics", fake_fetch_instance_metrics)
    monkeypatch.setattr(piece_read_service, "fetch_reads", fake_fetch_reads)
    monkeypatch.setattr(piece_read_service, "is_resonated", fake_is_resonated)

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
    import api_piece_runtime as piece_runtime_module

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

    monkeypatch.setattr(qna_module, "resolve_generated_reflection_access", fake_resolve_generated_reflection_access)

    ctx = asyncio.run(
        piece_runtime_module._resolve_qna_context_for_reaction(
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
    import api_piece_runtime as piece_runtime_module
    import piece_public_read_service as piece_read_service

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

    monkeypatch.setattr(piece_runtime_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(piece_read_service, "resolve_generated_reflection_access", fake_resolve_generated_reflection_access)

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


def test_generated_canonicalization_is_owner_scoped_not_global_qkey():
    import api_mymodel_qna as qna_module

    owner_a_row = {
        "id": "owner-a-generated-1",
        "public_id": "reflection:owner-a-generated-1",
        "owner_user_id": "owner-a",
        "source_type": "generated",
        "question": "最近夢中なことは？",
        "answer": "配信を通して人と話すこと。",
        "updated_at": "2026-04-03T18:00:00+00:00",
    }
    owner_b_row = {
        "id": "owner-b-generated-1",
        "public_id": "reflection:owner-b-generated-1",
        "owner_user_id": "owner-b",
        "source_type": "generated",
        "question": "最近夢中なことは？",
        "answer": "写真を撮りに出かけること。",
        "updated_at": "2026-04-03T17:00:00+00:00",
    }

    canonical = qna_module._canonicalize_generated_rows_latest_by_qkey([owner_a_row, owner_b_row])

    assert len(canonical) == 2
    assert {row["public_id"] for row in canonical} == {
        "reflection:owner-a-generated-1",
        "reflection:owner-b-generated-1",
    }


def test_generated_canonicalization_keeps_latest_per_owner_qkey():
    import api_mymodel_qna as qna_module

    latest_row = {
        "id": "owner-latest-generated-1",
        "public_id": "reflection:owner-latest-generated-1",
        "owner_user_id": "owner-latest",
        "source_type": "generated",
        "question": "大切にしていることは？",
        "answer": "無理をしすぎず整えること。",
        "updated_at": "2026-04-03T18:00:00+00:00",
    }
    older_row = {
        "id": "owner-latest-generated-2",
        "public_id": "reflection:owner-latest-generated-2",
        "owner_user_id": "owner-latest",
        "source_type": "generated",
        "question": "大切にしていることは？",
        "answer": "恋愛を楽しむこと。",
        "updated_at": "2026-04-03T10:00:00+00:00",
    }

    canonical = qna_module._canonicalize_generated_rows_latest_by_qkey([older_row, latest_row])

    assert len(canonical) == 1
    assert canonical[0]["public_id"] == "reflection:owner-latest-generated-1"



def test_generated_work_concern_uses_work_specific_head():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="仕事で気にしていることは？",
        raw_answer="毎日どこがダメだったか考えてるし、反省することが多い。",
        category="仕事",
        focus_key="work",
        topic_summary_text="仕事 / 毎日どこがダメだったか考えてる / 反省することが多い",
    )

    assert result.answer_display_state in {"ready", "masked"}
    assert result.answer_display_text is not None
    assert result.answer_display_text.startswith("仕事では、")
    assert "最近気になっているのは、" not in result.answer_display_text



def test_generated_notice_and_concern_use_different_heads():
    import generated_reflection_display as display_module

    common_raw = "どこか焦ってる毎日で余裕がない気がする。"
    notice = display_module.build_generated_reflection_display(
        question="最近気づいたことは？",
        raw_answer=common_raw,
        category="生活",
        focus_key="generic",
        topic_summary_text="生活 / どこか焦ってる毎日で余裕がない",
    )
    concern = display_module.build_generated_reflection_display(
        question="最近気になることは？",
        raw_answer=common_raw,
        category="生活",
        focus_key="generic",
        topic_summary_text="生活 / どこか焦ってる毎日で余裕がない",
    )

    assert notice.answer_display_state in {"ready", "masked"}
    assert concern.answer_display_state in {"ready", "masked"}
    assert notice.answer_display_text is not None
    assert concern.answer_display_text is not None
    assert notice.answer_display_text.startswith("最近気づいたのは、")
    assert concern.answer_display_text.startswith("最近気になっているのは、")



def test_generated_stress_time_uses_time_specific_template():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="心が休まる時間は？",
        raw_answer="夜中にASMRを聞いている時間は少し落ち着く。",
        category="生活",
        focus_key="stress",
        topic_summary_text="生活 / 夜中にASMRを聞いている時間は少し落ち着く",
    )

    assert result.answer_display_state in {"ready", "masked"}
    assert result.answer_display_text is not None
    assert result.answer_display_text.startswith("心が休まるのは、")
    assert "しんどい時は、" not in result.answer_display_text


def test_generated_notice_fragment_is_normalized_or_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="最近気づいたことは？",
        raw_answer="お風呂上がりの髪の毛を猫が嗅いでいて。",
        category="生活",
        focus_key="generic",
        topic_summary_text="生活 / お風呂上がりの髪の毛を猫が嗅いでいて",
    )

    if result.answer_display_state == "ready":
        assert result.answer_display_text is not None
        assert "ていてです" not in result.answer_display_text
    else:
        assert result.answer_display_state == "blocked"


def test_generated_notice_impulse_buy_fragment_is_normalized_or_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="最近気づいたことは？",
        raw_answer="欲しいと思ったものは必ず欲しいと思って買っちゃう。",
        category="生活",
        focus_key="generic",
        topic_summary_text="生活 / 欲しいと思ったものは必ず欲しいと思って買っちゃう",
    )

    if result.answer_display_state == "ready":
        assert result.answer_display_text is not None
        assert "買っちゃうです" not in result.answer_display_text
    else:
        assert result.answer_display_state == "blocked"


def test_generated_api_suppresses_overlapping_recent_notice_and_concern():
    import api_mymodel_qna as qna_module

    notice_row = {
        "id": "notice-row-1",
        "public_id": "reflection:notice-row-1",
        "owner_user_id": "owner-suppress-1",
        "source_type": "generated",
        "question": "最近気づいたことは？",
        "answer": "焦っていて余裕が少ない。",
        "updated_at": "2026-04-04T07:39:13+00:00",
        "content_json": {
            "display": {
                "answer_display_state": "ready",
                "answer_display_text": "最近気づいたのは、どこか焦っていて余裕が少ないことです。 毎日を慌ただしく感じることがあります。",
                "answer_format_meta": {
                    "sibling_cluster": "recent_notice_vs_concern",
                    "semantic_signature": "recent_notice_vs_concern|どこか焦っていて余裕が少ないこと|毎日を慌ただしく感じることがあります",
                },
            }
        },
    }
    concern_row = {
        "id": "concern-row-1",
        "public_id": "reflection:concern-row-1",
        "owner_user_id": "owner-suppress-1",
        "source_type": "generated",
        "question": "最近気になることは？",
        "answer": "焦っていて余裕が少ない。",
        "updated_at": "2026-04-04T07:39:12+00:00",
        "content_json": {
            "display": {
                "answer_display_state": "ready",
                "answer_display_text": "最近気になっているのは、どこか焦っていて余裕が少ないことです。 毎日を慌ただしく感じることがあります。",
                "answer_format_meta": {
                    "sibling_cluster": "recent_notice_vs_concern",
                    "semantic_signature": "recent_notice_vs_concern|どこか焦っていて余裕が少ないこと|毎日を慌ただしく感じることがあります",
                },
            }
        },
    }

    visible = qna_module._suppress_overlapping_generated_rows([notice_row, concern_row])

    assert len(visible) == 1
    assert visible[0]["public_id"] == "reflection:concern-row-1"


def test_generated_api_suppresses_overlapping_stress_time_rows():
    import api_mymodel_qna as qna_module

    relax_row = {
        "id": "relax-row-1",
        "public_id": "reflection:relax-row-1",
        "owner_user_id": "owner-suppress-2",
        "source_type": "generated",
        "question": "心が休まる時間は？",
        "answer": "落ち着ける時間。",
        "updated_at": "2026-04-04T07:39:13+00:00",
        "content_json": {
            "display": {
                "answer_display_state": "ready",
                "answer_display_text": "心が休まるのは、無理をせず落ち着ける時間です。 そういう時間があると、少し落ち着けます。",
                "answer_format_meta": {
                    "sibling_cluster": "stress_time_pair",
                    "semantic_signature": "stress_time_pair|無理をせず落ち着ける時間|そういう時間があると少し落ち着けます",
                },
            }
        },
    }
    loosen_row = {
        "id": "loosen-row-1",
        "public_id": "reflection:loosen-row-1",
        "owner_user_id": "owner-suppress-2",
        "source_type": "generated",
        "question": "心がほどける時間は？",
        "answer": "落ち着ける時間。",
        "updated_at": "2026-04-04T07:39:14+00:00",
        "content_json": {
            "display": {
                "answer_display_state": "ready",
                "answer_display_text": "心がほどけるのは、無理をせず落ち着ける時間です。 そういう時間があると、少し落ち着けます。",
                "answer_format_meta": {
                    "sibling_cluster": "stress_time_pair",
                    "semantic_signature": "stress_time_pair|無理をせず落ち着ける時間|そういう時間があると少し落ち着けます",
                },
            }
        },
    }

    visible = qna_module._suppress_overlapping_generated_rows([relax_row, loosen_row])

    assert len(visible) == 1
    assert visible[0]["public_id"] == "reflection:relax-row-1"



def test_generated_growth_time_only_fragment_is_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="伸ばしたいことは？",
        raw_answer="誕生日前日。",
        category="生活",
        focus_key="generic",
        topic_summary_text="生活 / 誕生日前日",
    )

    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None



def test_generated_value_incomplete_clause_fragment_is_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="大切にしていることは？",
        raw_answer="自分について考えていたら。",
        category="生活",
        focus_key="values",
        topic_summary_text="生活 / 自分について考えていたら",
    )

    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None



def test_generated_fun_recent_broken_fragment_is_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="最近の楽しみは？",
        raw_answer="出かけた先でまさかの。",
        category="生活",
        focus_key="fun",
        topic_summary_text="生活 / 出かけた先でまさかの",
    )

    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None



def test_generated_notice_colloquial_fragment_is_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="最近気づいたことは？",
        raw_answer="何も解決せず問題を後回しにしてしまったや。",
        category="生活",
        focus_key="generic",
        topic_summary_text="生活 / 何も解決せず問題を後回しにしてしまったや",
    )

    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None



def test_generated_work_concern_long_raw_fragment_is_blocked():
    import generated_reflection_display as display_module

    result = display_module.build_generated_reflection_display(
        question="仕事で気にしていることは？",
        raw_answer="天気が悪い日は気分も落ち込みやすい 仕事の時に 集中力が落ちたて支障が出たりしたらまずい。",
        category="仕事",
        focus_key="work",
        topic_summary_text="仕事 / 天気が悪い日は気分も落ち込みやすい / 仕事の時に 集中力が落ちたて支障が出たりしたらまずい",
    )

    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None



def test_generated_api_suppresses_overlapping_stress_method_rows():
    import api_mymodel_qna as qna_module

    body = "心と体を整えるために、体調を大事にしながら生活を整えることを大事にしています。 今の状態を見ながら、焦らず整えています。"
    method_row = {
        "id": "method-row-1",
        "public_id": "reflection:method-row-1",
        "owner_user_id": "owner-suppress-3",
        "source_type": "generated",
        "question": "心と体を整える方法は？",
        "answer": "体調を大事にしながら生活を整える。",
        "updated_at": "2026-04-04T10:20:00+00:00",
        "content_json": {
            "display": {
                "answer_display_state": "ready",
                "answer_display_text": body,
                "answer_format_meta": {
                    "sibling_cluster": "stress_method_pair",
                    "semantic_signature": "stress_method_pair|体調を大事にしながら生活を整えること|今の状態を見ながら焦らず整えています",
                },
            }
        },
    }
    feeling_row = {
        "id": "feeling-row-1",
        "public_id": "reflection:feeling-row-1",
        "owner_user_id": "owner-suppress-3",
        "source_type": "generated",
        "question": "気持ちを整える方法は？",
        "answer": "体調を大事にしながら生活を整える。",
        "updated_at": "2026-04-04T10:20:01+00:00",
        "content_json": {
            "display": {
                "answer_display_state": "ready",
                "answer_display_text": body,
                "answer_format_meta": {
                    "sibling_cluster": "stress_method_pair",
                    "semantic_signature": "stress_method_pair|体調を大事にしながら生活を整えること|今の状態を見ながら焦らず整えています",
                },
            }
        },
    }

    visible = qna_module._suppress_overlapping_generated_rows([method_row, feeling_row])

    assert len(visible) == 1
    assert visible[0]["public_id"] == "reflection:method-row-1"
