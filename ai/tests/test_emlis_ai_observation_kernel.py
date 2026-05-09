from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model
from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, run_multi_perspective_case


SAMPLE_MEMO = """
誰かと繋がっていたい気持ちもあるけど、ひとりで静かに過ごしたい気持ちもある。
人と関わると気を使いすぎて疲れるし、でも完全に離れると寂しくなる。
自分でもどうしたいのか分からなくなる。
"""


def test_retired_kernel_delegates_to_multi_perspective_adapter_without_templates():
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-05-09T00:00:00Z",
            "emotions": ["自己理解"],
            "category": ["人間関係"],
            "memo": SAMPLE_MEMO,
            "memo_action": "",
        },
        input_effort={"memo_char_count": len(SAMPLE_MEMO), "emotion_count": 1, "effort_score": 0.72},
        memory_richness={"history_density_score": 0.0},
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            style_profile=build_style_profile(capability=capability, bundle=bundle, world_model=world_model),
        )
    )

    assert decision.debug["kernel_version"] == "multi_perspective_adapter.v1"
    assert decision.reply_length_plan is not None
    assert decision.reply_lines
    text = "\n".join(line.text for line in decision.reply_lines)
    assert "繋がっていたい" in text or "静かに過ごしたい" in text
    assert_no_legacy_observation_text(text)
    assert all(line.sentence_evidence.evidence for line in decision.reply_lines)


def test_multi_perspective_observers_replace_model_line_expectations():
    result = run_multi_perspective_case(SAMPLE_MEMO, display_name="Mash", emotion="自己理解", category="人間関係")

    assert {report.observer_id for report in result.reports} >= {
        "explicit_content",
        "emotion_state",
        "conflict_coexistence",
        "pressure_constraint",
        "limit_signal",
        "self_awareness",
        "value_strength",
        "addressee_model",
        "safety_boundary",
    }
    assert result.graph.core_tensions
    assert result.decision.observation_status == "passed"
    assert_no_legacy_observation_text(result.text)
