from __future__ import annotations

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
