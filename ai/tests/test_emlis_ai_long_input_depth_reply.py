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


LONG_SELF_UNDERSTANDING_MEMO = """
体も心もボロボロになってきてるなって、自分でもちゃんと分かってる
それくらいここまで頑張ってきたんだと思うし、無理してきた時間もちゃんと積み重なってる

それでも、もう少し頑張りたいって気持ちが残ってるのも本音で
投げ出したいわけじゃないし、ここで終わりにしたくないって思ってる自分もいる

でも同時に、しんどいっていう感覚もちゃんとあって
体が重かったり、気持ちがついてこなかったりして
このまま無理したら崩れてしまいそうな不安もある

だからこそ、どっちかを無理やり選ぶんじゃなくて
頑張りたい気持ちもしんどい気持ちも、どっちもちゃんと抱えたまま進んでいきたい

頑張れる日は少しだけ前に進んで
しんどい日は立ち止まってもいいって、自分に許しながら
無理に削るんじゃなくて、ちゃんと整えながら進んでいきたい

今の自分は弱いわけじゃなくて
ちゃんと限界に気づけてる状態なんだと思う
"""


def _build_long_reply_text():
    current_input = {
        "id": "emo-long",
        "created_at": "2026-05-05T03:00:00Z",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["仕事"],
        "memo": LONG_SELF_UNDERSTANDING_MEMO,
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
    text = _naturalize_reply_text(
        _render_comment_text_from_reply_lines(plan.reply_lines, greeting_text="Emlisです。")
    )
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


def test_long_clear_input_reply_covers_multiple_meaning_blocks_and_passes_gate():
    text, review, meta, capability = _build_long_reply_text()

    assert "体も心" in text or "ボロボロ" in text
    assert "ここまで頑張ってきた" in text or "無理してきた時間" in text
    assert "もう少し頑張りたい" in text
    assert "投げ出したいわけ" in text or "ここで終わりにしたいわけ" in text
    assert "体が重" in text or "気持ちがついてこ" in text or "崩れてしまいそう" in text
    assert "頑張りたい気持ちもしんどい気持ち" in text or "両方抱えたまま" in text
    assert "しんどい日は立ち止" in text or "整えながら" in text
    assert "弱いのではなく" in text or "限界に気づけている" in text
    assert "どれかひとつに削らず" in text or "大切に" in text
    assert len([line for line in text.splitlines() if line.strip()]) >= 7
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
    assert gate.meaning_coverage_ok is True
    assert gate.long_input_depth_ok is True
