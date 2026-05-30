# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest


_COMPLETE_INITIAL_ENV = {
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
    "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_initial",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE": "all",
}

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


def _enable_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)


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
async def test_phase18_3_complete_initial_generates_candidate_before_display_gate_without_public_body_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_complete_initial(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase18-3-complete-initial-candidate-path-user",
        subscription_tier="free",
        current_input=_sample_current_input("phase18-3-complete-initial-candidate-path-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    runtime = diagnostic["complete_initial_runtime"]
    step6 = diagnostic["step6_final_ap0_scorecard_connection"]

    assert step5["phase18_candidate_path_contract_version"] == "cocolon.emlis.complete_initial.candidate_path.v2"
    assert step5["candidate_generation_attempted"] is True
    assert step5["complete_composer_client_generate_called"] is True
    assert step5["candidate_generated"] is True
    assert step5["candidate_generated_before_display_gate"] is True
    assert step5["candidate_status"] == "generated"
    assert step5["candidate_status_before_display_gate"] == "generated"
    assert step5["candidate_comment_text_present"] is True
    assert step5["complete_initial_candidate_generation_display_gate_separated"] is True

    assert runtime["candidate_generated"] is True
    assert runtime["candidate_generated_before_display_gate"] is True
    assert runtime["candidate_status_before_display_gate"] == "generated"
    assert runtime["candidate_comment_text_present"] is True
    assert runtime["sentence_binding_count"] >= 1
    assert runtime["used_evidence_span_count"] >= 1
    assert runtime["used_phrase_unit_count"] >= 1
    assert runtime["complete_initial_candidate_generation_display_gate_separated"] is True

    # Phase18-3 restores generation visibility only. The public passed-only
    # display contract remains owned by Reader/Grounding/Template/Display gates.
    assert step5["display_gate_relaxed"] is False
    assert step5["grounding_gate_relaxed"] is False
    assert step5["public_comment_text_present"] is False
    assert step5["non_passed_comment_text_empty"] is True
    assert step5["passed_only_comment_text_contract_preserved"] is True
    assert reply.comment_text == ""
    assert step6["scorecard_candidate_generated"] is True
    assert step6["passed_only_comment_text_contract_preserved"] is True

    serialized = json.dumps({"step5": step5, "runtime": runtime, "step6": step6}, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized
    assert "memo_action" not in serialized
    assert "comment_text" not in runtime
    assert step5["raw_input_included"] is False
    assert step5["generated_candidate_text_included"] is False
