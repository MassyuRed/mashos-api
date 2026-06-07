# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 true low-information reception-required surface tests."""

import pytest

from emlis_ai_low_information_observation_composer import (
    assert_low_information_observation_composer_contract,
    compose_low_information_observation,
    low_information_reception_required_shape_summary,
)
from emlis_ai_observation_surface_realizer_tone import realize_low_information_observation_surface


_TRUE_LOW_INFORMATION_INPUT = {
    "memo": "なんか無理",
    "memo_action": "",
    "emotions": ["疲れ"],
    "emotion_details": [{"type": "疲れ", "strength": "medium"}],
    "category": ["生活"],
}


def _assert_reception_required_surface(text: str) -> None:
    summary = low_information_reception_required_shape_summary(text)
    assert text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in text
    assert summary["passed"] is True
    assert summary["observation_section_present"] is True
    assert summary["reception_section_present"] is True
    assert summary["question_after_reception"] is True
    assert summary["question_before_reception"] is False
    assert summary["question_dominant_surface"] is False
    assert text.index("詳しく残せそうなら") > text.index("Emlisから：")


def test_p5_true_low_information_composer_uses_reception_required_shape() -> None:
    draft = compose_low_information_observation(
        current_input=dict(_TRUE_LOW_INFORMATION_INPUT),
        subscription_tier="free",
    )

    _assert_reception_required_surface(draft.body)
    meta = draft.as_meta()
    assert meta["observation_reply_kind"] == "low_information_observation"
    assert meta["eligibility_status"] == "low_information"
    assert meta["eligible_for_full_observation"] is False
    assert meta["low_information_reception_required"] is True
    assert meta["low_information_reception_shape_valid"] is True
    assert meta["reception_section_present"] is True
    assert meta["question_after_reception"] is True
    assert meta["question_dominant_surface"] is False
    assert meta["must_not_promote_low_info_to_eligible"] is True
    assert meta["must_not_assert_current_event_from_user_fact"] is True
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False


def test_p5_low_information_surface_realizer_preserves_reception_required_body() -> None:
    draft = compose_low_information_observation(
        current_input=dict(_TRUE_LOW_INFORMATION_INPUT),
        subscription_tier="free",
    )
    realized = realize_low_information_observation_surface(
        draft,
        current_input=dict(_TRUE_LOW_INFORMATION_INPUT),
    )

    assert realized.body == draft.body
    _assert_reception_required_surface(realized.body)
    meta = realized.as_meta()
    assert meta["source_meta"]["low_information_reception_required"] is True
    assert meta["source_meta"]["low_information_reception_shape_valid"] is True
    assert meta["source_meta"]["question_after_reception"] is True
    assert meta["raw_input_included"] is False


def test_p5_contract_rejects_legacy_low_information_question_surface_without_reception() -> None:
    draft = compose_low_information_observation(
        current_input=dict(_TRUE_LOW_INFORMATION_INPUT),
        subscription_tier="free",
    )
    invalid = {**draft.as_meta(), "body": "今は、疲れの重さが先に出ているように見えます。詳しく残せそうなら、何があったか残してみませんか。"}

    with pytest.raises(ValueError):
        assert_low_information_observation_composer_contract(invalid)
