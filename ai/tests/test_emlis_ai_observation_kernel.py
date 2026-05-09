from __future__ import annotations

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_world_model_service import build_emlis_ai_world_model
from emlis_ai_types import (
    DerivedUserModel,
    EmotionDisplayItem,
    EvidenceRef,
    GreetingDecision,
    MeaningMapEntry,
    PartnerExpectationProfile,
    ResponsePreferenceCues,
    SourceBundle,
    StyleProfile,
    UserWordAnchor,
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
    assert decision.reply_length_plan.max_lines <= 8
    assert decision.reply_length_plan.history_usable is False
    assert decision.reply_length_plan.interpretive_frame_usable is False
    assert decision.reply_lines[0].key == "receive"
    assert decision.reply_lines[-1].key == "receiving_close"
    assert not any(line.key in {"interpretation", "partner_line", "continuity", "topic_anchor"} for line in decision.reply_lines)


def test_observation_kernel_free_reflects_user_words_and_selected_emotions():
    capability = resolve_emlis_ai_capability_for_tier("free")
    current_ref = EvidenceRef(kind="emotion", ref_id="emo-cur")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="Mash",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-04-18T00:00:00Z",
            "emotions": ["不安", "悲しみ"],
            "category": ["恋愛"],
            "memo": "恋人と喧嘩した。連絡の頻度ですれ違った。わかり合えなくてとても悲しかった。",
            "memo_action": "",
        },
        input_effort={"memo_char_count": 48, "emotion_count": 2, "effort_score": 0.62},
        memory_richness={"history_density_score": 0.0},
    )
    world_model = WorldModel(
        facts=WorldModelFacts(
            dominant_emotion="不安",
            dominant_strength="medium",
            has_memo_input=True,
            selected_emotions=[
                EmotionDisplayItem(type="不安", strength="medium", strength_label="中", role="dominant"),
                EmotionDisplayItem(type="悲しみ", strength="weak", strength_label="弱", role="secondary"),
            ],
            secondary_emotions=[
                EmotionDisplayItem(type="悲しみ", strength="weak", strength_label="弱", role="secondary"),
            ],
            current_categories=["恋愛"],
            current_emotion_labels=["不安", "悲しみ"],
            user_word_anchors=[
                UserWordAnchor(anchor_key="a1", text="恋人と喧嘩した", source_field="memo", role="event", evidence=[current_ref]),
                UserWordAnchor(anchor_key="a2", text="連絡の頻度ですれ違った", source_field="memo", role="mismatch", evidence=[current_ref]),
                UserWordAnchor(anchor_key="a3", text="わかり合えなくてとても悲しかった", source_field="memo", role="explicit_emotion", evidence=[current_ref]),
            ],
            response_mode="comfort",
            memo_richness="medium",
        )
    )

    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            style_profile=StyleProfile(family="accepting", tone_reason="test"),
        )
    )

    text = "\n".join(line.text for line in decision.reply_lines)
    assert "恋人と喧嘩" in text
    assert "連絡の頻度" in text
    assert "わかり合えなくてとても悲しかった" in text
    assert "悲しみ" in text
    assert decision.reply_lines[-1].text == "ここに置いてくれた言葉を、Emlisは軽く扱いません。"


def test_observation_kernel_verbalizes_self_awareness_conflict_without_receive_loop():
    capability = resolve_emlis_ai_capability_for_tier("free")
    bundle = SourceBundle(
        user_id="user-1",
        display_name="User",
        current_input={
            "id": "emo-cur",
            "created_at": "2026-05-05T00:00:00Z",
            "emotions": ["悲しみ", "不安"],
            "emotion_details": [
                {"type": "悲しみ", "strength": "medium"},
                {"type": "不安", "strength": "medium"},
            ],
            "category": ["人間関係"],
            "memo": "きっと怒ると知っていながらパーソナルスペースに触れてしまった。女の子との絡みがあったからという理由を掲げて自分の非を見たくない自分が嫌われてしまいそうで悲しくて不安な気持ち。",
            "memo_action": "人のパーソナルスペースに入ってしまった。",
        },
        input_effort={
            "memo_char_count": 93,
            "memo_action_char_count": 20,
            "emotion_count": 2,
            "category_count": 1,
            "effort_score": 0.9,
        },
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

    text = "\n".join(line.text for line in decision.reply_lines)
    assert "パーソナルスペース" in text
    assert "怒ると知っていながら" in text
    assert "自分の非" in text
    assert "見たくない" in text
    assert "嫌われ" in text
    assert "悲しみ" in text and "不安" in text
    assert "あなたは" not in text
    assert any(word in text for word in ("だけでなく", "同じ流れ", "状態として", "見ています"))
    assert text.count("受け取") <= 1
    assert "入力として受け取ります" not in text
    assert "理解しました" not in text
    assert world_model.facts.understanding_patterns
    assert "justification_vs_fault" in world_model.facts.understanding_patterns
