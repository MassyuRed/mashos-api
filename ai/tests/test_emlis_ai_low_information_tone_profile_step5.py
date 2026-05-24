from __future__ import annotations

from typing import Any

from emlis_ai_low_information_observation_composer import (
    LOW_INFORMATION_TONE_PROFILE_MIXED,
    LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY,
    LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT,
    QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY,
    assert_low_information_observation_composer_contract,
    compose_low_information_observation,
)
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_observation_reply_contract import UNKNOWN_SLOT_RELATION, UNKNOWN_SLOT_TARGET
from emlis_ai_observation_surface_realizer_tone import realize_low_information_observation_surface
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report


_BURDEN_DEFAULT_MARKERS = (
    "不安の重さ",
    "疲れの重さ",
    "言葉になる前の重さ",
    "軽く流せるものではなさそう",
    "無理かもしれない",
    "負荷",
    "どのあたりが重くなっているか",
)


def _input(memo: str, emotions: list[str]) -> dict[str, Any]:
    return {
        "id": f"low-info-tone-step5-{abs(hash((memo, tuple(emotions))))}",
        "created_at": "2026-05-24T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": emotion, "strength": "medium"} for emotion in emotions],
        "emotions": list(emotions),
        "category": ["生活"],
    }


def test_step5_positive_only_low_information_avoids_default_burden_surface_and_heavy_question() -> None:
    current_input = _input("いい感じ", ["平穏", "喜び"])
    draft = compose_low_information_observation(current_input=current_input, subscription_tier="free")
    meta = draft.as_meta()

    assert meta["step5_low_information_tone_profile_ready"] is True
    assert meta["low_information_tone_profile"] == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY
    assert meta["negative_text_anchor_present"] is False
    assert meta["burden_surface_default_allowed"] is False
    assert meta["positive_burden_surface_default_blocked"] is True
    assert "positive_feeling" in meta["observed_scope"]
    assert "unspecified_burden" not in meta["observed_scope"]
    assert "burden_before_words" not in meta["selected_material_entry_ids"]
    assert meta["question_surface_kind"] != QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
    assert not any(marker in draft.body for marker in _BURDEN_DEFAULT_MARKERS)
    assert "よければ、何がありましたか" not in draft.body
    visible_report = build_visible_surface_acceptance_gate_report(
        comment_text=draft.body,
        selected_emotions=current_input["emotion_details"],
        current_input=current_input,
    )
    assert visible_report["passed"] is True
    assert visible_report["rejection_reasons"] == []
    assert_low_information_observation_composer_contract(draft, current_input=current_input)


def test_step5_positive_only_target_relation_slots_do_not_force_heavy_question() -> None:
    current_input = _input("穏やかだった", ["平穏"])
    eligibility = route_observation_eligibility(current_input=current_input, subscription_tier="free")
    eligibility_meta = dict(eligibility.as_meta())
    eligibility_meta["unknown_slots"] = [UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION]
    eligibility_meta["observation_reply_meta"] = dict(eligibility_meta["observation_reply_meta"])
    eligibility_meta["observation_reply_meta"]["unknown_slots"] = [UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION]

    draft = compose_low_information_observation(
        current_input=current_input,
        eligibility_decision=eligibility_meta,
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert meta["low_information_tone_profile"] == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY
    assert meta["question_surface_kind"] != QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
    assert "どのあたりが重くなっているか" not in draft.body
    assert not any(marker in draft.body for marker in _BURDEN_DEFAULT_MARKERS)
    assert_low_information_observation_composer_contract(draft, current_input=current_input)


def test_step5_positive_selection_with_negative_text_anchor_becomes_mixed_and_bridged() -> None:
    current_input = _input("なんか不安", ["平穏", "喜び"])
    draft = compose_low_information_observation(current_input=current_input, subscription_tier="free")
    meta = draft.as_meta()

    assert meta["low_information_tone_profile"] == LOW_INFORMATION_TONE_PROFILE_MIXED
    assert meta["negative_text_anchor_present"] is True
    assert meta["burden_surface_default_allowed"] is True
    assert meta["mixed_requires_bridge_between_emotions"] is True
    assert "coexisting_emotions" in meta["observed_scope"]
    assert "だけではなく" in draft.body
    assert "近くにある" in draft.body
    assert_low_information_observation_composer_contract(draft, current_input=current_input)


def test_step5_self_insight_profile_uses_unformed_understanding_surface_without_diagnosis() -> None:
    current_input = _input("なんとなく分かった気がする", ["自己理解"])
    draft = compose_low_information_observation(current_input=current_input, subscription_tier="free")
    meta = draft.as_meta()

    assert meta["low_information_tone_profile"] == LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT
    assert "unformed_self_insight" in meta["observed_scope"]
    assert "自分について見えかけているもの" in draft.body
    assert "診断" not in draft.body
    assert "性格" not in draft.body
    assert_low_information_observation_composer_contract(draft, current_input=current_input)


def test_step5_tone_profile_meta_reaches_low_information_surface_realizer_source_meta() -> None:
    current_input = _input("いい感じ", ["平穏", "喜び"])
    draft = compose_low_information_observation(current_input=current_input, subscription_tier="free")
    surface = realize_low_information_observation_surface(draft, current_input=current_input)
    source_meta = surface.as_meta()["source_meta"]

    assert source_meta["step5_low_information_tone_profile_ready"] is True
    assert source_meta["low_information_tone_profile"] == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY
    assert source_meta["positive_burden_surface_default_blocked"] is True
    assert not any(marker in surface.body for marker in _BURDEN_DEFAULT_MARKERS)
