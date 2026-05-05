from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_quality_gate import evaluate_emlis_ai_quality_gate
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_reply_service import (
    _build_meta,
    _build_reply_plan_from_decision,
    _naturalize_reply_text,
    _render_comment_text_from_reply_lines,
)
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model

SELF_SACRIFICE_MEMO = """
どこかで私が我慢していれば、誰にも心配かけないし負担もかけないからこれでいいって思ってた
自分が少し我慢すれば全部丸く収まるって考えてたし
それが一番楽なやり方だと思ってた

でもそれを続けていくと、しんどい気持ちをずっと一人で
抱え込むことになるし、気づいたら余裕がなくなってることもある

本当はしんどい時にちゃんと誰かに話したり
頼ったりすることも必要で、それができる方が無理せず
続けていけるんだと思う

それに、自分を守るために距離を取ったり
無理しない選択をすることもちゃんと必要なことなんだよね
我慢することだけが正しいわけじゃなくて
自分の状態を見ながらどう動くかを考えていくことも
大切なんだと思う
"""


def _render_self_sacrifice_reply():
    current_input = {
        "id": "emo-composition-self-sacrifice",
        "created_at": "2026-05-05T07:16:00Z",
        "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
        "emotions": ["悲しみ"],
        "category": ["自己理解"],
        "memo": SELF_SACRIFICE_MEMO,
        "memo_action": "",
    }
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="User",
        current_input=current_input,
        input_effort={"score": 0.9},
        memory_richness={"score": 0.0},
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    style_profile = build_style_profile(capability=capability, bundle=bundle, world_model=world_model)
    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            style_profile=style_profile,
        )
    )
    plan = _build_reply_plan_from_decision(decision)
    text = _naturalize_reply_text(_render_comment_text_from_reply_lines(plan.reply_lines, greeting_text="Emlisです。"))
    review = review_emlis_ai_reply_text(comment_text=text, world_model=world_model)
    if review.repaired_text:
        text = _naturalize_reply_text(review.repaired_text)
        review = review_emlis_ai_reply_text(comment_text=text, world_model=world_model)
    meta = _build_meta(
        capability=capability,
        bundle=bundle,
        world_model=world_model,
        plan=plan,
        fallback_used=False,
        working_model=None,
    )
    return text, review, meta, capability


def test_self_sacrifice_reply_has_opening_thesis_and_composed_flow():
    text, review, meta, capability = _render_self_sacrifice_reply()
    lines = [line for line in text.splitlines() if line.strip()]

    assert lines[0] == "Emlisです。"
    assert not lines[1].startswith(("ただ同時に", "それでも", "だからこそ"))
    assert "我慢" in text and ("収ま" in text or "心配" in text)
    assert "心配" in text and "負担" in text
    assert "一人で抱え込" in text
    assert "余裕がなく" in text
    assert "話したり頼ったり" in text or "頼る" in text
    assert "距離を取" in text
    assert "無理しない選択" in text
    assert "我慢" in text and "正しい" in text
    assert "自分の状態" in text
    assert "体が重" not in text
    assert "崩れてしまいそう" not in text
    assert "大切に扱います" in text
    assert review.passed is True

    gate = evaluate_emlis_ai_quality_gate(
        comment_text=text,
        capability=capability,
        used_sources=meta.get("used_sources"),
        evidence_by_line=meta.get("evidence_by_line"),
        fallback_used=False,
        allowed_line_count=meta.get("reply_depth", {}).get("max_lines"),
        sample_user_word_anchors=meta.get("anchor_summary", {}).get("sample_user_word_anchors"),
        user_word_anchor_count=meta.get("anchor_summary", {}).get("user_word_anchor_count", 0),
        understanding_patterns=meta.get("understanding", {}).get("patterns"),
        final_reader_passed=review.passed,
        pre_return_blocking_enabled=True,
        meaning_coverage=meta.get("meaning_coverage"),
        composition=meta.get("composition"),
    )
    assert gate.passed is True
    assert gate.response_composition_ok is True
    assert gate.opening_thesis_present is True
    assert gate.first_content_line_not_midstream is True
    assert gate.current_input_grounding_ok is True
