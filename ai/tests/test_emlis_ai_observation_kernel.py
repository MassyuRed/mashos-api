from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_types import (
    DerivedUserModel,
    EvidenceRef,
    GreetingDecision,
    MeaningMapEntry,
    PartnerExpectationProfile,
    ResponsePreferenceCues,
    SourceBundle,
    StyleProfile,
    WorldModel,
    WorldModelFacts,
    WorldModelHypothesis,
)


def _base_world_model():
    return WorldModel(
        facts=WorldModelFacts(
            dominant_emotion="不安",
            dominant_strength="strong",
            has_memo_input=True,
            current_categories=["仕事"],
            current_emotion_labels=["不安"],
        ),
        hypotheses=[
            WorldModelHypothesis(
                key="same_day_change",
                text="さっきから気持ちの揺れ方が少し変わっていますね。",
                evidence=[EvidenceRef(kind="emotion", ref_id="emo-prev")],
                confidence=0.72,
            ),
            WorldModelHypothesis(
                key="recovery_signal",
                text="直近の流れだけを見ると、少し落ち着く方向へ寄ってきていますね。",
                evidence=[EvidenceRef(kind="emotion", ref_id="emo-prev")],
                confidence=0.66,
            ),
        ],
    )


def test_observation_kernel_premium_uses_interpretive_frame_and_sentence_bound_evidence():
    capability = resolve_emlis_ai_capability_for_tier("premium")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-04-18T00:00:00Z",
            "emotions": ["不安"],
            "category": ["仕事"],
            "memo": "仕事の評価が不安",
            "memo_action": "",
        },
        greeting=GreetingDecision(slot_name="day", slot_key="2026-04-18:day", greeting_text="Emlisです。", first_in_slot=False),
        input_effort={"memo_char_count": 24, "memo_action_char_count": 0, "emotion_count": 1, "category_count": 1, "effort_score": 0.78},
        memory_richness={"same_day_recent_count": 2, "similar_inputs_count": 4, "model_meaning_map_count": 2, "model_open_anchor_count": 1, "history_density_score": 0.82},
    )
    working_model = DerivedUserModel(schema_version="emlis_user_model.v2", model_tier="premium")
    working_model.interpretive_frame.meaning_map = [
        MeaningMapEntry(
            trigger="仕事",
            likely_meaning="評価不安",
            confidence=0.81,
            evidence=[EvidenceRef(kind="emotion", ref_id="emo-old")],
            last_seen_at="2026-04-17T00:00:00Z",
        )
    ]
    working_model.interpretive_frame.response_preference_cues = ResponsePreferenceCues(
        prefers_receive_first=True,
        prefers_continuity_reference=True,
        evidence=[EvidenceRef(kind="emotion", ref_id="emo-old")],
    )
    working_model.interpretive_frame.partner_expectation = PartnerExpectationProfile(
        wants_continuity=True,
        wants_non_judgmental_receive=True,
        wants_precise_observation=True,
        evidence=[EvidenceRef(kind="emotion", ref_id="emo-old")],
    )

    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=_base_world_model(),
            style_profile=StyleProfile(family="sensitive", tone_reason="test"),
            working_model=working_model,
        )
    )

    assert decision.reply_length_plan is not None
    assert decision.reply_length_plan.max_lines >= 4
    assert decision.reply_lines[0].key == "receive"
    assert any(line.key == "interpretation" for line in decision.reply_lines)
    assert any(line.key == "partner_line" for line in decision.reply_lines)
    assert all(line.sentence_evidence.evidence for line in decision.reply_lines)


def test_observation_kernel_free_stays_present_only_without_model_lines():
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-04-18T00:00:00Z",
            "emotions": ["不安"],
            "category": ["仕事"],
            "memo": "",
            "memo_action": "",
        },
        input_effort={"effort_score": 0.05},
        memory_richness={"history_density_score": 0.95},
    )
    working_model = DerivedUserModel(schema_version="emlis_user_model.v2", model_tier="premium")
    working_model.interpretive_frame.meaning_map = [
        MeaningMapEntry(
            trigger="仕事",
            likely_meaning="評価不安",
            confidence=0.91,
            evidence=[EvidenceRef(kind="emotion", ref_id="emo-old")],
            last_seen_at="2026-04-17T00:00:00Z",
        )
    ]

    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=WorldModel(facts=WorldModelFacts(dominant_emotion="不安", has_memo_input=False)),
            style_profile=StyleProfile(family="accepting", tone_reason="test"),
            working_model=working_model,
        )
    )

    assert decision.reply_length_plan is not None
    assert decision.reply_length_plan.max_lines <= 3
    assert [line.key for line in decision.reply_lines] == ["receive"]
