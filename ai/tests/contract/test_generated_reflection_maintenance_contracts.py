from __future__ import annotations

import asyncio
from typing import Any, Dict


def test_generated_display_uses_stored_bundle_when_source_signature_matches():
    import generated_reflection_display as display_module

    signature = display_module.compute_generated_display_source_signature(
        question="最近夢中なことは？",
        raw_answer="今日は体がだるくてずっと寝てるし、やたら お腹すいて色々食べてるだけだったけど お話練習したくて配信見に行って少しずつ コメントしてお話できたから お話。",
        category="趣味",
        focus_key="fun",
        topic_summary_text="趣味 / 配信見に行って少しずつコメントして話した / お話",
        text_candidates=[],
    )

    row: Dict[str, Any] = {
        "id": "generated-persist-1",
        "public_id": "reflection:generated-persist-1",
        "owner_user_id": "owner-persist-1",
        "source_type": "generated",
        "question": "最近夢中なことは？",
        "answer": "今日は体がだるくてずっと寝てるし、やたら お腹すいて色々食べてるだけだったけど お話練習したくて配信見に行って少しずつ コメントしてお話できたから お話。",
        "category": "趣味",
        "updated_at": "2026-04-03T07:00:00+00:00",
        "content_json": {
            "focus_key": "fun",
            "topic_summary_text": "趣味 / 配信見に行って少しずつコメントして話した / お話",
            "display": {
                "answer_display_text": "最近夢中なのは、人とやり取りしながら配信を楽しむことです。",
                "answer_display_state": "ready",
                "answer_format_version": display_module.GENERATED_REFLECTION_DISPLAY_VERSION,
                "answer_format_meta": {
                    "version": display_module.GENERATED_REFLECTION_DISPLAY_VERSION,
                    "changed": True,
                    "flags": [],
                    "actions": ["rewrite:answer_opening"],
                    "answer_norm_hash": display_module.compute_generated_answer_norm_hash(
                        "最近夢中なのは、人とやり取りしながら配信を楽しむことです。"
                    ),
                    "display_source_signature": signature,
                },
                "answer_display_updated_at": "2026-04-03T06:59:00+00:00",
                "rewritten_answer_text": "最近夢中なのは、人とやり取りしながら配信を楽しむことです。",
                "answer_norm_hash": display_module.compute_generated_answer_norm_hash(
                    "最近夢中なのは、人とやり取りしながら配信を楽しむことです。"
                ),
                "display_source_signature": signature,
            }
        },
    }

    result = display_module.resolve_generated_reflection_display(row)
    assert result.answer_display_text == "最近夢中なのは、人とやり取りしながら配信を楽しむことです。"
    assert result.display_source_signature == signature



def test_generated_maintenance_builds_backfill_plan_for_missing_display_bundle():
    import generated_reflection_maintenance as maintenance_module

    row: Dict[str, Any] = {
        "id": "generated-backfill-1",
        "public_id": "reflection:generated-backfill-1",
        "owner_user_id": "owner-backfill-1",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "question": "大切にしていることは？",
        "answer": "完全に元通りとは言えないけど、突発性難聴は治ったら終わりじゃなくて、まず一番大事なのは。",
        "category": "生活",
        "content_json": {
            "focus_key": "values",
            "topic_summary_text": "生活 / 完全に元通りとは言えないけど / 突発性難聴は治ったら終わりじゃなくて / まず一番大事なのは",
        },
    }

    plan = maintenance_module.build_generated_reflection_backfill_plan(row)
    assert plan is not None
    assert plan.reflection_id == "generated-backfill-1"
    display = plan.content_json.get("display") or {}
    assert display.get("answer_display_state") in {"ready", "masked"}
    assert display.get("display_source_signature")
    assert display.get("answer_norm_hash")



def test_generated_maintenance_plans_cleanup_and_reports_remaining_multi_answer_groups():
    import generated_reflection_maintenance as maintenance_module

    duplicate_active_new = {
        "id": "dup-active-new",
        "public_id": "reflection:dup-active-new",
        "owner_user_id": "owner-cleanup-1",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "question": "人との関わりで大切なことは？",
        "answer": "安心して話せる関係を大切にしたい。",
        "category": "生活",
        "updated_at": "2026-04-03T07:10:00+00:00",
        "content_json": {"focus_key": "relationship", "topic_summary_text": "生活 / 安心して話せる関係"},
    }
    duplicate_active_old = {
        "id": "dup-active-old",
        "public_id": "reflection:dup-active-old",
        "owner_user_id": "owner-cleanup-1",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "question": "人との関わりで大切なことは？",
        "answer": "安心して話せる関係を大切にしたい。",
        "category": "生活",
        "updated_at": "2026-04-03T07:00:00+00:00",
        "content_json": {"focus_key": "relationship", "topic_summary_text": "生活 / 安心して話せる関係"},
    }
    duplicate_archived = {
        "id": "dup-archived-1",
        "public_id": "reflection:dup-archived-1",
        "owner_user_id": "owner-cleanup-1",
        "source_type": "generated",
        "status": "archived",
        "is_active": False,
        "question": "人との関わりで大切なことは？",
        "answer": "安心して話せる関係を大切にしたい。",
        "category": "生活",
        "updated_at": "2026-04-03T06:55:00+00:00",
        "content_json": {"focus_key": "relationship", "topic_summary_text": "生活 / 安心して話せる関係"},
    }
    different_answer_same_question = {
        "id": "different-answer-1",
        "public_id": "reflection:different-answer-1",
        "owner_user_id": "owner-cleanup-1",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "question": "人との関わりで大切なことは？",
        "answer": "少しずつ交流を広げていきたい。",
        "category": "生活",
        "updated_at": "2026-04-03T07:05:00+00:00",
        "content_json": {"focus_key": "relationship", "topic_summary_text": "生活 / 少しずつ交流を広げたい"},
    }

    actions = maintenance_module.plan_generated_reflection_duplicate_cleanup(
        [duplicate_active_new, duplicate_active_old, duplicate_archived, different_answer_same_question]
    )
    action_map = {item.reflection_id: item.action for item in actions}

    assert action_map["dup-active-new"] == "keep"
    assert action_map["dup-active-old"] == "archive"
    assert action_map["dup-archived-1"] == "delete"

    simulated_rows = maintenance_module.simulate_cleanup_actions(
        [duplicate_active_new, duplicate_active_old, duplicate_archived, different_answer_same_question],
        actions,
    )
    unresolved = maintenance_module.summarize_unresolved_question_multi_answer_groups(simulated_rows)
    assert unresolved
    assert unresolved[0]["question"] == "人との関わりで大切なことは？"
    assert unresolved[0]["unique_answer_count"] == 2



def test_generated_maintenance_archives_noncanonical_active_same_qkey():
    import generated_reflection_maintenance as maintenance_module

    latest_row = {
        "id": "latest-qkey-row",
        "public_id": "reflection:latest-qkey-row",
        "owner_user_id": "owner-qkey-1",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "q_key": "generated:q:test-same-question",
        "question": "大切にしていることは？",
        "answer": "無理をしすぎず心と体を整えることを大切にしたい。",
        "category": "生活",
        "updated_at": "2026-04-03T17:56:32+00:00",
        "content_json": {"focus_key": "values", "topic_summary_text": "生活 / 無理をしすぎず整える"},
    }
    older_row = {
        "id": "older-qkey-row",
        "public_id": "reflection:older-qkey-row",
        "owner_user_id": "owner-qkey-1",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "q_key": "generated:q:test-same-question",
        "question": "大切にしていることは？",
        "answer": "恋愛を楽しみたい。",
        "category": "生活",
        "updated_at": "2026-04-03T10:50:00+00:00",
        "content_json": {"focus_key": "values", "topic_summary_text": "生活 / 恋愛を楽しみたい"},
    }

    actions = maintenance_module.plan_generated_reflection_latest_qkey_cleanup([latest_row, older_row])
    action_map = {item.reflection_id: item.action for item in actions}

    assert action_map["latest-qkey-row"] == "keep"
    assert action_map["older-qkey-row"] == "archive"


def test_generated_cleanup_apply_skips_delete_by_default(monkeypatch):
    import generated_reflection_maintenance as maintenance_module

    archived_calls = []
    deleted_calls = []

    async def fake_patch_json(path, *, params=None, json_body=None, timeout=None, prefer=None):
        archived_calls.append({
            "path": path,
            "params": params,
            "json_body": json_body,
            "timeout": timeout,
            "prefer": prefer,
        })
        return []

    async def fake_delete(path, *, params=None, timeout=None, prefer=None):
        deleted_calls.append({
            "path": path,
            "params": params,
            "timeout": timeout,
            "prefer": prefer,
        })

    monkeypatch.setattr(maintenance_module, "_sb_patch_json", fake_patch_json)
    monkeypatch.setattr(maintenance_module, "_sb_delete", fake_delete)

    actions = [
        maintenance_module.GeneratedCleanupAction(
            action="archive",
            reflection_id="archive-me",
            reason="archive_noncanonical_latest_qkey",
            owner_user_id="owner-cleanup-2",
            q_key="generated:q:archive-me",
            question="大切にしていることは？",
            answer_norm_hash="hash-archive",
            is_active=True,
            public_id="reflection:archive-me",
        ),
        maintenance_module.GeneratedCleanupAction(
            action="delete",
            reflection_id="delete-me",
            reason="delete_inactive_duplicate_clone",
            owner_user_id="owner-cleanup-2",
            q_key="generated:q:archive-me",
            question="大切にしていることは？",
            answer_norm_hash="hash-delete",
            is_active=False,
            public_id="reflection:delete-me",
        ),
    ]

    result = asyncio.run(maintenance_module.apply_generated_cleanup_actions(actions))

    assert result == {"archived_ids": ["archive-me"], "deleted_ids": []}
    assert len(archived_calls) == 1
    assert archived_calls[0]["json_body"]["status"] == "archived"
    assert deleted_calls == []


def test_generated_maintenance_canonicalize_active_only_skips_duplicate_delete_planning(monkeypatch):
    import generated_reflection_maintenance as maintenance_module

    latest_ready = {
        "id": "canonical-active-new",
        "public_id": "reflection:canonical-active-new",
        "owner_user_id": "owner-cleanup-3",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "q_key": "generated:q:canonical-values",
        "question": "大切にしていることは？",
        "answer": "無理をしすぎず心と体を整えることを大切にしたい。",
        "category": "生活",
        "updated_at": "2026-04-03T18:00:00+00:00",
        "content_json": {"focus_key": "values", "topic_summary_text": "生活 / 無理をしすぎず整える"},
    }
    older_ready = {
        "id": "canonical-active-old",
        "public_id": "reflection:canonical-active-old",
        "owner_user_id": "owner-cleanup-3",
        "source_type": "generated",
        "status": "ready",
        "is_active": True,
        "q_key": "generated:q:canonical-values",
        "question": "大切にしていることは？",
        "answer": "恋愛を楽しみたい。",
        "category": "生活",
        "updated_at": "2026-04-03T10:00:00+00:00",
        "content_json": {"focus_key": "values", "topic_summary_text": "生活 / 恋愛を楽しみたい"},
    }
    inactive_exact_clone = {
        "id": "canonical-inactive-dup",
        "public_id": "reflection:canonical-inactive-dup",
        "owner_user_id": "owner-cleanup-3",
        "source_type": "generated",
        "status": "archived",
        "is_active": False,
        "q_key": "generated:q:canonical-values",
        "question": "大切にしていることは？",
        "answer": "無理をしすぎず心と体を整えることを大切にしたい。",
        "category": "生活",
        "updated_at": "2026-04-03T09:00:00+00:00",
        "content_json": {"focus_key": "values", "topic_summary_text": "生活 / 無理をしすぎず整える"},
    }

    async def fake_fetch_generated_reflection_rows(*, user_id=None, batch_size=500, max_rows=None):
        return [latest_ready, older_ready, inactive_exact_clone]

    monkeypatch.setattr(maintenance_module, "fetch_generated_reflection_rows", fake_fetch_generated_reflection_rows)

    summary = asyncio.run(
        maintenance_module.run_generated_reflection_backfill_cleanup(
            do_backfill=False,
            do_cleanup=True,
            canonicalize_active_only=True,
            allow_delete=False,
            apply=False,
        )
    )

    assert summary["cleanup"]["counts"]["delete"] == 0
    assert summary["cleanup"]["counts"]["archive"] == 1
    assert summary["cleanup"]["canonicalized_qkey_group_count"] == 1
    assert summary["cleanup"]["planned_action_count"] == 1



def test_generated_generation_plan_prefers_latest_state_signals_for_same_question():
    import astor_reflection_engine as engine_module

    premium_reflection_view = {
        "version": "premium_reflection_view.v1",
        "items": [
            {
                "source_type": "emotion_input",
                "source_id": "old-1",
                "timestamp": "2026-01-01T09:00:00+00:00",
                "category": "健康",
                "text_primary": "夜更かしすること",
                "text_secondary": "",
                "source_weight": 1.0,
            },
            {
                "source_type": "emotion_input",
                "source_id": "new-1",
                "timestamp": "2026-04-03T18:00:00+00:00",
                "category": "健康",
                "text_primary": "無理をしすぎず休むこと",
                "text_secondary": "",
                "source_weight": 1.0,
            },
        ],
    }

    plan = engine_module.build_generation_plan(
        user_id="owner-latest-1",
        snapshot_id="snapshot-latest-1",
        source_hash="source-hash-latest-1",
        premium_reflection_view=premium_reflection_view,
        existing_dynamic_reflections=[],
    )

    assert len(plan["creates"]) == 1
    answer = str(plan["creates"][0]["answer"] or "")
    assert "無理をしすぎず休むこと" in answer
    assert "夜更かし" not in answer


def test_generated_display_recomputes_stored_bundle_that_now_fails_quality_gate():
    import generated_reflection_display as display_module

    signature = display_module.compute_generated_display_source_signature(
        question="大切にしていることは？",
        raw_answer="久々に枠とって歌った",
        category="趣味",
        focus_key="values",
        topic_summary_text="趣味 / 久々に枠とって歌った",
        text_candidates=[],
    )

    row: Dict[str, Any] = {
        "id": "generated-persist-low-quality-1",
        "public_id": "reflection:generated-persist-low-quality-1",
        "owner_user_id": "owner-persist-low-quality-1",
        "source_type": "generated",
        "question": "大切にしていることは？",
        "answer": "久々に枠とって歌った",
        "category": "趣味",
        "updated_at": "2026-04-03T07:00:00+00:00",
        "content_json": {
            "focus_key": "values",
            "topic_summary_text": "趣味 / 久々に枠とって歌った",
            "display": {
                "answer_display_text": "大切にしているのは、久々に枠とって歌ったです。",
                "answer_display_state": "ready",
                "answer_format_version": display_module.GENERATED_REFLECTION_DISPLAY_VERSION,
                "answer_format_meta": {
                    "version": display_module.GENERATED_REFLECTION_DISPLAY_VERSION,
                    "changed": True,
                    "flags": [],
                    "actions": ["rewrite:question_aware"],
                    "answer_norm_hash": display_module.compute_generated_answer_norm_hash(
                        "大切にしているのは、久々に枠とって歌ったです。"
                    ),
                    "display_source_signature": signature,
                },
                "answer_display_updated_at": "2026-04-03T06:59:00+00:00",
                "rewritten_answer_text": "大切にしているのは、久々に枠とって歌ったです。",
                "answer_norm_hash": display_module.compute_generated_answer_norm_hash(
                    "大切にしているのは、久々に枠とって歌ったです。"
                ),
                "display_source_signature": signature,
            }
        },
    }

    result = display_module.resolve_generated_reflection_display(row)
    assert result.answer_display_state == "blocked"
    assert result.answer_display_text is None
