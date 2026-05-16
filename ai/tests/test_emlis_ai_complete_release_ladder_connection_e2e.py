# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_complete_release_ladder_service import COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"


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
async def test_step7_release_ladder_is_attached_to_complete_initial_reply_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step7-release-ladder-user",
        subscription_tier="free",
        current_input=_sample_current_input("step7-release-ladder-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    ladder = diagnostic["step7_product_quality_release_ladder"]

    assert ladder == diagnostic["complete_product_quality_release_ladder"]
    assert ladder == reply.meta["complete_product_quality_release_ladder"]
    assert ladder == reply.meta["multi_perspective"]["complete_product_quality_release_ladder"]
    assert ladder["version"] == COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION
    assert ladder["target_step"] == "Step7_Release_ladder_connection"
    assert ladder["release_ladder_connected"] is True
    assert ladder["release_ladder_guard_ready"] is True
    assert ladder["product_gate_reached"] is False
    assert ladder["product_gate_public_release_applied"] is False
    assert ladder["release_judgment"]["release_allowed"] is False
    assert ladder["comment_text_contract"] == "passed_only"
    assert ladder["comment_text_written_by_step7_release_ladder"] is False
    assert ladder["display_gate_relaxed"] is False
    assert ladder["grounding_gate_relaxed"] is False
    assert ladder["template_gate_relaxed"] is False
    assert ladder["response_shape_changed"] is False
    assert ladder["raw_input_included"] is False
    assert ladder["comment_text_included"] is False
    assert phase_gate["step7_product_quality_release_ladder_connected"] is True
    assert phase_gate["step7_product_quality_product_gate_reached"] is False
    assert phase_gate["step7_product_quality_public_release_applied"] is False
    assert phase_gate["step7_product_quality_response_shape_changed"] is False
    assert phase_gate["step7_product_quality_display_gate_relaxed"] is False

    serialized = json.dumps(ladder, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized
    assert "memo_action" not in serialized
    assert "current_input" not in serialized
    assert "source_text" not in serialized
