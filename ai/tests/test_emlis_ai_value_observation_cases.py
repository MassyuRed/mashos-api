from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model


def test_emlis_world_model_and_kernel_use_value_observation_signal():
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-05-07T00:00:00Z",
            "emotions": ["自己理解"],
            "category": ["自己理解"],
            "memo": "今日は何もしていないのに疲れた。",
            "memo_action": "",
        },
        input_effort={"memo_char_count": 17, "memo_action_char_count": 0, "emotion_count": 1, "category_count": 1, "effort_score": 0.4},
        memory_richness={},
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    keys = [signal.signal_key for signal in world_model.facts.value_observation_signals]

    assert "inner_activity_fatigue_gap" in keys
    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            style_profile=build_style_profile(capability=capability, bundle=bundle, world_model=world_model),
            working_model=None,
        )
    )
    text = "\n".join(line.text for line in decision.reply_lines)
    assert "行動量" in text or "頭の中" in text or "内側" in text
    assert "精神の問題" not in text
