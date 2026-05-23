from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_low_information_observation_composer import (
    LOW_INFORMATION_SPECIFICITY_PLAN_SCHEMA_VERSION,
    LOW_INFORMATION_SPECIFICITY_STEP,
    assert_low_information_observation_composer_contract,
    build_emlis_ai_low_information_observation,
    dump_low_information_observation_composition,
)
from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_observation_surface_realizer_tone import realize_low_information_observation_surface
from emlis_ai_reply_service import render_emlis_ai_reply


def _input(memo: str, *, emotions: list[str] | None = None) -> dict[str, Any]:
    labels = list(emotions or [])
    return {
        "id": f"low-info-specificity-{abs(hash((memo, tuple(labels))))}",
        "created_at": "2026-05-23T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": label, "strength": "medium"} for label in labels],
        "emotions": labels,
        "category": ["生活"],
    }


def test_step6_uses_specific_safe_anchor_for_safety_question_without_raw_long_copy() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("大丈夫かどうか不安"),
        subscription_tier="free",
    )
    meta = draft.as_meta()
    plan = meta["low_information_specificity_plan"]

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["step6_low_information_specificity_ready"] is True
    assert meta["low_information_specificity_used"] is True
    assert meta["safe_anchor_count"] == 1
    assert meta["uses_safe_anchor"] is True
    assert meta["safe_anchor_role"] == "question"
    assert meta["safe_anchor_surface_kind"] == "safety_confirmation"
    assert plan["version"] == LOW_INFORMATION_SPECIFICITY_PLAN_SCHEMA_VERSION
    assert plan["source_step"] == LOW_INFORMATION_SPECIFICITY_STEP
    assert plan["raw_input_included"] is False
    assert plan["comment_text_body_included"] is False
    assert "大丈夫かどうか" in draft.body
    assert "何について大丈夫か気になっていますか" in draft.body
    assert "大丈夫かどうか不安" not in draft.body
    assert meta["unsupported_event_assertion_present"] is False
    assert meta["user_fact_promotion_attempt"] is False
    assert_low_information_observation_composer_contract(draft, current_input=_input("大丈夫かどうか不安"))


def test_step6_uses_emotion_anchor_but_does_not_echo_short_raw_input() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("疲れた"),
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert meta["low_information_specificity_used"] is True
    assert meta["safe_anchor_count"] == 1
    assert meta["uses_safe_anchor"] is True
    assert meta["safe_anchor_role"] == "emotion"
    assert meta["safe_anchor_surface_kind"] == "fatigue_weight"
    assert "疲れの重さ" in draft.body
    assert "疲れた" not in draft.body
    assert "何がありましたか" in draft.body
    assert_low_information_observation_composer_contract(draft, current_input=_input("疲れた"))


def test_step6_keeps_fully_anchorless_low_information_abstract_and_meta_only() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("あれだけ", emotions=[]),
        subscription_tier="free",
    )
    meta = draft.as_meta()

    assert meta["low_information_specificity_used"] is False
    assert meta["safe_anchor_count"] == 0
    assert meta["uses_safe_anchor"] is False
    assert meta["safe_anchor_role"] == "none"
    assert meta["safe_anchor_surface_kind"] == "none"
    assert "言葉になる前の重さ" in draft.body
    assert "何がありましたか" in draft.body
    assert_low_information_observation_composer_contract(draft, current_input=_input("あれだけ", emotions=[]))


def test_step6_specificity_meta_and_dump_do_not_store_anchor_surface_or_body_text() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("大丈夫かな"),
        subscription_tier="free",
    )
    dumped = dump_low_information_observation_composition(draft)

    assert "大丈夫かな" not in dumped
    assert "大丈夫かどうか" not in dumped
    assert "何について大丈夫か" not in dumped
    assert "commentText" not in dumped
    assert "\"raw_input\"" not in dumped
    assert "safety_confirmation" in dumped


def test_step6_contract_rejects_positive_safe_anchor_count_without_usage() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("疲れた"),
        subscription_tier="free",
    )
    invalid = {"body": draft.body, **draft.as_meta()}
    invalid["uses_safe_anchor"] = False
    invalid["low_information_specificity_plan"] = dict(invalid["low_information_specificity_plan"])
    invalid["low_information_specificity_plan"]["uses_safe_anchor"] = False

    with pytest.raises(ValueError):
        assert_low_information_observation_composer_contract(invalid)


def test_step6_surface_realizer_preserves_anchor_specific_question_line() -> None:
    draft = build_emlis_ai_low_information_observation(
        current_input=_input("大丈夫かどうか不安"),
        subscription_tier="free",
    )
    surface = realize_low_information_observation_surface(draft, current_input=_input("大丈夫かどうか不安"))
    meta = surface.as_meta()

    assert "何について大丈夫か気になっていますか" in surface.body
    assert "よければ、何がありましたか" not in surface.body
    assert meta["source_meta"]["low_information_specificity_used"] is True
    assert meta["source_meta"]["safe_anchor_surface_kind"] == "safety_confirmation"


@pytest.mark.asyncio
async def test_step6_public_low_information_repair_keeps_specific_safe_anchor_question() -> None:
    reply = await render_emlis_ai_reply(
        user_id="step6-low-information-specificity-user",
        subscription_tier="free",
        current_input=_input("大丈夫かどうか不安"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=None,
    )

    assert reply.meta["observation_status"] == "passed"
    assert "大丈夫かどうか" in reply.comment_text
    assert "何について大丈夫か気になっていますか" in reply.comment_text
    assert "よければ、何がありましたか" not in reply.comment_text
