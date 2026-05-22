from __future__ import annotations

import pytest

from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_reply_service import render_emlis_ai_reply

_LOW_INFORMATION_ENV_KEYS = (
    "COCOLON_EMLIS_OBSERVATION_ROUTER_ENABLED",
    "COCOLON_EMLIS_LOW_INFORMATION_OBSERVATION_ENABLED",
    "COCOLON_EMLIS_USER_FACT_GROUNDING_BOUNDARY_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_SENTENCE_ROLES_ENABLED",
)


def _input(memo: str) -> dict:
    return {
        "id": f"low-info-red-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def _clear_low_information_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _LOW_INFORMATION_ENV_KEYS:
        monkeypatch.delenv(name, raising=False)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "memo",
    [
        "疲れた",
        "なんか無理",
        "あれがまたこうなって、結局だめだった。もう無理かもしれない。",
    ],
)
async def test_low_information_inputs_should_eventually_return_passed_low_information_observation(
    monkeypatch: pytest.MonkeyPatch,
    memo: str,
) -> None:
    _clear_low_information_flags(monkeypatch)

    reply = await render_emlis_ai_reply(
        user_id="low-information-red-user",
        subscription_tier="free",
        current_input=_input(memo),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=None,
    )

    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()

    diagnostic = reply.meta.get("diagnostic_summary") or {}
    observation_reply_meta = (
        diagnostic.get("observation_reply_meta")
        or reply.meta.get("observation_reply_meta")
        or diagnostic.get("observation_reply_contract")
        or {}
    )
    assert observation_reply_meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert observation_reply_meta["eligible_for_full_observation"] is False
    assert observation_reply_meta["question_required"] is True
    assert observation_reply_meta["user_fact_may_promote_to_eligible"] is False

    step10 = reply.meta.get("step10_observation_display_repair_integration") or {}
    assert step10["applied"] is True
    assert step10["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert step10["final_observation_status"] == "passed"
    assert step10["display_gate_relaxed"] is False
    assert step10["public_status_extended"] is False
    assert step10["rn_visible_contract_changed"] is False
    assert step10["fixed_fallback_used"] is False
    assert step10["external_ai_used"] is False
