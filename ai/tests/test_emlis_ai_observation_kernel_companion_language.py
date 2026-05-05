from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_reply_service import _naturalize_reply_text, _render_comment_text_from_reply_lines
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model


def test_observation_kernel_shapes_screenshot_input_into_companion_reply():
    current_input = {
        "id": "emo-cur",
        "created_at": "2026-05-05T00:00:00Z",
        "emotions": ["悲しみ", "怒り"],
        "emotion_details": [
            {"type": "悲しみ", "strength": "medium"},
            {"type": "怒り", "strength": "medium"},
        ],
        "category": ["仕事"],
        "memo": """
たまに泣きそうになるくらい嫌になる時あるけどそれだと
悔しいしもったいない気がするむかつくけどさ 
好きな先輩以外の時はミスしても知らねーよって
気持ちでいる だって教えてくんないんだもん
どう頑張ればいいのって思う
それに最近めっちゃイライラする
それらを忘れたい時チャット系でお話してると
癒される
""",
        "memo_action": "",
    }
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="User",
        current_input=current_input,
        input_effort={"memo_char_count": len(current_input["memo"]), "memo_action_char_count": 0, "emotion_count": 2, "effort_score": 0.9},
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

    text = _naturalize_reply_text(_render_comment_text_from_reply_lines(decision.reply_lines, greeting_text="Emlisです。"))
    review = review_emlis_ai_reply_text(comment_text=text, world_model=world_model)
    if review.repaired_text:
        text = _naturalize_reply_text(review.repaired_text)

    assert "それだとこと" not in text
    assert "けどこと" not in text
    assert "ことが、今回大きく残っていたのですね" not in text
    assert text.count("のですね") <= 2
    assert "泣きそうになるくらい嫌になる時がある" in text
    assert "どう頑張ればいい" in text or "教えて" in text
    assert "イライラ" in text or "むかつく" in text
    assert "チャット" in text and "癒し" in text
    assert "雑に扱いません" in text or "軽く扱いません" in text
    assert "最近の履歴の中でも、近いテーマ" not in text
    assert review.passed is True
