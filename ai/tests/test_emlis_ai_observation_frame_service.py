from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_reply_service import _build_reply_plan_from_decision, _naturalize_reply_text, _render_comment_text_from_reply_lines
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import SourceBundle
from emlis_ai_user_address_service import build_emlis_observation_greeting
from emlis_ai_world_model_service import build_emlis_ai_world_model


_SAMPLE_MEMO = """ずっと家にいて、リラックスできて自分のことを
優先して色々整えたりお家のことも出来るから
嬉しいんだけど、ふって気が抜けたときに現実と
向き合うことがあるからその時にダメージでかい
あぁ、今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に
生活したい。でもそうしたらもっと悪化する
そんなの分かってる。たまに逃げ出したくなる"""


def test_observation_frame_reconstructs_relation_and_uses_display_name():
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-observation-sample",
            "created_at": "2026-05-09T00:00:00Z",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "category": ["生活"],
            "memo": _SAMPLE_MEMO,
            "memo_action": "",
        },
        input_effort={"memo_char_count": len(_SAMPLE_MEMO), "memo_action_char_count": 0, "effort_score": 0.78},
        memory_richness={"history_density_score": 0.0},
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
        _render_comment_text_from_reply_lines(
            plan.reply_lines,
            greeting_text=build_emlis_observation_greeting(display_name=bundle.display_name, greeting_text="Emlisです。"),
        )
    )

    assert text.startswith("Mashさん、Emlisです。")
    assert "あなたは" not in text
    assert "あなたの" not in text
    assert "今の生活にある良さ" in text
    assert "現実の不便さ" in text
    assert "普通に生活したい願い" in text
    assert "悪化すると分かっている現実" in text
    assert "逃げ出したくなる気持ちは、弱さではなく" in text
    assert "強さ" in text
    assert "一緒に見ていきます" in text
