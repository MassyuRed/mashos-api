from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, run_multi_perspective_case
from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_frame_service import build_emlis_observation_frame
from emlis_ai_types import EvidenceRef, SourceBundle
from emlis_ai_world_model_service import build_emlis_ai_world_model


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def test_observation_frame_keeps_structure_without_user_facing_templates():
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-observation-sample",
            "created_at": "2026-05-09T00:00:00Z",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "category": ["生活"],
            "memo": SAMPLE_MEMO,
            "memo_action": "",
        },
        input_effort={"memo_char_count": len(SAMPLE_MEMO), "memo_action_char_count": 0, "effort_score": 0.78},
        memory_richness={"history_density_score": 0.0},
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    frame = build_emlis_observation_frame(
        meaning_blocks=world_model.facts.meaning_blocks,
        whole_input_meaning_arc=world_model.facts.whole_input_meaning_arc,
        evidence=EvidenceRef(kind="emotion", ref_id="emo-observation-sample"),
    )

    assert frame is not None
    assert frame.primary_state
    assert frame.evidence_terms
    assert frame.evidence
    serialized = "\n".join(
        [
            frame.primary_state,
            frame.escape_or_limit_signal,
            frame.self_awareness_signal,
            frame.strength_signal,
            frame.companion_close,
            *frame.pressure_sources,
            *frame.evidence_terms,
        ]
    )
    assert_no_legacy_observation_text(serialized)


def test_multi_perspective_case_passes_without_sample_phrase_expectation():
    result = run_multi_perspective_case(SAMPLE_MEMO, display_name="Mash")

    assert result.decision.observation_status == "passed"
    assert result.graph.core_tensions
    assert result.graph.pressure_sources
    assert result.graph.limit_signals
    assert result.graph.self_awareness
    assert result.text.startswith("Mashさん、Emlisです。")
    assert_no_legacy_observation_text(result.text)
