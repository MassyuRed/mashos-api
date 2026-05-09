from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model
from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, run_multi_perspective_case


def test_emlis_world_model_keeps_value_signal_but_observation_uses_new_pipeline():
    memo = "今日は何もしていないのに疲れた。頭の中だけずっと動いていて、内側が休まっていない感じがする。"
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-05-07T00:00:00Z",
            "emotions": ["自己理解"],
            "category": ["自己理解"],
            "memo": memo,
            "memo_action": "",
        },
        input_effort={"memo_char_count": len(memo), "memo_action_char_count": 0, "emotion_count": 1, "category_count": 1, "effort_score": 0.4},
        memory_richness={},
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    keys = [signal.signal_key for signal in world_model.facts.value_observation_signals]

    assert "inner_activity_fatigue_gap" in keys
    result = run_multi_perspective_case(memo, display_name="Mash", emotion="自己理解", category="自己理解")
    assert result.decision.observation_status == "passed"
    assert "疲れ" in result.text or "頭の中" in result.text or "内側" in result.text
    assert_no_legacy_observation_text(result.text)
