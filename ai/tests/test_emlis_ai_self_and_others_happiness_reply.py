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


SELF_AND_OTHERS_HAPPINESS_MEMO = """
誰かの役に立てればそれでいい
私は私自身頑張ることも楽しむことも中途半端だから
自分のことは好きになれないけど
他の人たちが幸せに笑ってくれてて
その人たちの役に立てるなら1番それが幸せかな
自分のこと 今後のこと まだ諦めたくないけれど
諦めてる自分もいる もう期待して裏切られたくないから
そう思う中でも私も幸せになりたいって思う自分もいる
それは諦めたくない時だと思う
前に考えた、もう既に幸せなことはあるって事
それ以上に求めてるんだよねきっと
好きなことをもっとしたい
納得いくまで十分にたのしみたい
素敵なパートナーと出会って幸せになりたい
手の届かい所にある願い
でもその願いに届くように、今頑張れることを大切にしたい
"""


def test_emlis_reply_reacts_to_whole_self_and_others_happiness_input():
    current_input = {
        "id": "emo-self-happy",
        "created_at": "2026-05-05T04:37:00Z",
        "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
        "emotions": ["悲しみ"],
        "category": ["人間関係"],
        "memo": SELF_AND_OTHERS_HAPPINESS_MEMO,
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

    assert "誰かの役に立" in text
    assert "中途半端" in text and "好きになれない" in text
    assert "諦めたくない" in text
    assert "諦めている自分" in text
    assert "裏切られたくない" in text or "裏切られるのが怖" in text
    assert "幸せになりたい" in text
    assert "好きなこと" in text
    assert "パートナー" in text
    assert "手の届かない" in text
    assert "今頑張れること" in text
    assert "小さく扱いません" in text
    assert "中途半端だ気持ち" not in text
    assert len([line for line in text.splitlines() if line.strip()]) >= 8
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
    )
    assert gate.passed is True
    assert gate.major_meaning_retention_ok is True
    assert gate.broken_noun_phrase_blocked is True
