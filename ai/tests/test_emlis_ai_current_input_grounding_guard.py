from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model


def test_explicit_previous_input_leak_is_blocked():
    memo = "しんどい時に誰かに話したり頼ったりすることも必要だと思う。"
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="User",
        current_input={"id": "emo-ground", "emotions": ["悲しみ"], "memo": memo, "memo_action": ""},
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    review = review_emlis_ai_reply_text(
        comment_text=(
            "Emlisです。\n"
            "しんどい時に頼ることも必要だと気づいている状態として見ています。\n"
            "前回入力の内容を踏まえて、別の入力の気持ちもここにあります。\n"
            "ここに置いてくれた言葉を、Emlisは軽く扱いません。"
        ),
        world_model=world_model,
    )
    codes = {issue.code for issue in review.issues}
    assert "stale_meaning_block_leak" in codes or "stale_meaning_block_leak_remaining" in codes
    assert "second_person_pronoun" not in codes
    assert review.passed is False
    assert review.repaired_text is None
