# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_complete_product_quality_scorecard_service import COMPLETE_PRODUCT_QUALITY_SCORECARD_VERSION
from emlis_ai_p7_body_free_leak_guard import (
    assert_p7_body_free_no_payload_leak,
    build_p7_product_quality_connection_scorecard_body_free_contract,
)

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"
_SAMPLE_INPUT_ID = "step6-product-quality-scorecard-input"


def _clear_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
    ):
        monkeypatch.delenv(name, raising=False)


def _sample_current_input(input_id: str) -> dict[str, object]:
    return {
        "id": input_id,
        "created_at": "2026-05-16T00:00:00Z",
        "memo": _SAMPLE_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


@pytest.mark.asyncio
async def test_step6_product_quality_scorecard_is_attached_to_complete_initial_reply_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step6-product-quality-scorecard-user",
        subscription_tier="free",
        current_input=_sample_current_input(_SAMPLE_INPUT_ID),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    scorecard = diagnostic["step6_product_quality_scorecard"]
    rubric = diagnostic["complete_product_quality_blind_qa_rubric"]

    assert scorecard == diagnostic["complete_product_quality_scorecard"]
    assert scorecard == reply.meta["complete_product_quality_scorecard"]
    assert scorecard == reply.meta["multi_perspective"]["complete_product_quality_scorecard"]
    assert scorecard["version"] == COMPLETE_PRODUCT_QUALITY_SCORECARD_VERSION
    assert scorecard["target_step"] == "Step6_Scorecard_Blind_QA"
    assert scorecard["product_quality_scorecard_ready"] is True
    assert scorecard["machine_metrics_ready"] is True
    assert scorecard["machine_metrics"]["machine_metrics_ready"] is True
    assert scorecard["blind_qa_required"] is True
    assert scorecard["read_feeling_requires_blind_qa"] is True
    assert scorecard["blind_qa_ready"] is False
    assert "blind_qa_missing" in scorecard["release_blockers"]
    assert scorecard["product_gate_reached"] is False
    assert scorecard["product_gate_ready"] is False
    assert scorecard["comment_text_contract"] == "passed_only"
    assert scorecard["display_gate_relaxed"] is False
    assert scorecard["grounding_gate_relaxed"] is False
    assert scorecard["template_gate_relaxed"] is False
    assert scorecard["response_shape_changed"] is False
    assert scorecard["raw_input_included"] is False
    assert scorecard["comment_text_included"] is False
    assert rubric == reply.meta["complete_product_quality_blind_qa_rubric"]
    assert set(rubric["dimensions"]) == {"read_feeling", "evidence_retention", "distance", "naturalness", "non_template"}
    assert phase_gate["step6_product_quality_scorecard_ready"] is True
    assert phase_gate["step6_product_quality_machine_metrics_ready"] is True
    assert phase_gate["step6_product_gate_ready"] is False
    assert phase_gate["step6_product_quality_response_shape_changed"] is False
    assert phase_gate["step6_product_quality_display_gate_relaxed"] is False

    body_free_contract = build_p7_product_quality_connection_scorecard_body_free_contract()
    assert_p7_body_free_no_payload_leak(
        scorecard,
        source="complete_product_quality_connection_e2e.scorecard",
        contract=body_free_contract,
        forbidden_raw_values={
            "current_input.memo": _SAMPLE_MEMO,
            "current_input.id": _SAMPLE_INPUT_ID,
        },
    )
