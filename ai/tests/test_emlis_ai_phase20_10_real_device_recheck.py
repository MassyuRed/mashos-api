# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-10 real-device recheck guards.

The uploaded real-device screenshots showed B/C/D opening the Emlis modal, but
A stayed silent.  This test keeps the recheck focused on public behavior and on
log fields requested by the Phase20-10 design: response_kind, public status,
comment presence, safety triage, material quality, material slots, recovery
attempts, public input_feedback eligibility, and RN modal eligibility.
"""

from collections.abc import Mapping
from typing import Any

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
from emlis_ai_input_material_bundle import MATERIAL_QUALITY_LOW_INFORMATION
from emlis_ai_observation_eligibility_router import EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY
from emlis_ai_safety_triage import (
    EMLIS_SAFETY_TRIAGE_META_KEY,
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)
from emlis_ai_types import GreetingDecision


_PHASE20_10_ENV = {
    # This flag reproduces the production-like path from the real-device A log:
    # a composer/scope stop happens before a generated candidate owns the
    # surface.  Phase20 low-information observation must still recover through
    # its own material-bundle branch without relaxing gates.
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
}
_PHASE20_10_ENV_KEYS = (
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
)
_FORBIDDEN_PHASE19_ROUTE_TOKENS = (
    "relationship_gratitude_recovery",
    "self_understanding_learning_shift",
    "phase19_real_device_C_self_understanding_learning_shift",
    "phase19_real_device_D_relationship_gratitude_recovery",
)


@pytest.fixture(autouse=True)
def _patch_source_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="phase20-10-real-device-recheck",
            slot_key="phase20-10-real-device-recheck",
            greeting_text="Emlisです。",
            first_in_slot=False,
        )

    async def empty_dict(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {}

    async def empty_list(*_args: Any, **_kwargs: Any) -> list[Any]:
        return []

    async def none_value(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(context_service, "_resolve_display_name_for_user", fake_display_name)
    monkeypatch.setattr(context_service, "_resolve_timezone_name_for_user", fake_timezone)
    monkeypatch.setattr(context_service, "decide_greeting_for_user", fake_greeting)
    for name, replacement in {
        "_get_input_summary_for_user": empty_dict,
        "_get_myweb_home_summary_for_user": empty_dict,
        "_get_latest_today_question_answer_for_user": empty_dict,
        "_list_recent_today_question_answers_for_user": empty_list,
        "get_last_input_for_user": none_value,
        "list_same_day_recent_inputs": empty_list,
        "search_similar_inputs": empty_list,
        "load_emlis_ai_user_model_for_user": none_value,
        "get_cross_core_context_for_emlis_ai": empty_list,
    }.items():
        if hasattr(context_service, name):
            monkeypatch.setattr(context_service, name, replacement)


@pytest.fixture()
def phase20_10_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _PHASE20_10_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in _PHASE20_10_ENV.items():
        monkeypatch.setenv(key, value)


_A_INPUT = {
    "memo": "なんか今日は全部だるい。\n何もしたくない。",
    "memo_action": "",
    "emotions": ["悲しみ", "不安"],
    "category": ["生活"],
}
_B_INPUT = {
    "memo": "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
    "memo_action": "",
    "emotions": ["悲しみ"],
    "category": ["人生", "価値観"],
}
_C_INPUT = {
    "memo": (
        "今までは、人に対して何故？と考えていたけど、疑問の対象が物になったことで、人について考えすぎる事が減った気がする。\n"
        "何故それを聞くの？とか聞く意味があるの？と考えてしまってうまくコミュニケーションが取れなくてもやもやしていたけど、物を見ることで人への興味が薄れた。\n"
        "私にとってはとても良い変化になった。\n"
        "そして学校、バイト、趣味で一人の時間が無くなったけど、人との話し方を思い出してきてる。やろう、言おうと思ったときにすぐに行動する勇気が出せるようになった。\n"
        "少しずつだけど進歩してる。大丈夫。"
    ),
    "memo_action": (
        "創作をする時にリアルさを求めるなら日常に隠れている汚れや傷の意味を知れ。という授業があった。\n"
        "意味のない場所に傷や汚れは作れない、作ったとしても違和感になる。と、それから外に出る度に色んな場所を見て、今まで気にしなかった場所も見るようになった。\n"
        "傷や汚れの場所、自分のこうかな？という憶測をメモしていった。"
    ),
    "emotions": ["自己理解"],
    "category": ["学習"],
}
_D_INPUT = {
    "memo": (
        "悲しい気持ちばかりで身の回りにある優しさを見逃してしまいそうになるが、"
        "ちゃんと優しさに触れてそれを実感出来ていることが嬉しい。"
        "そして私のために怒ってくれる存在に感謝の気持ちが溢れてくる。"
        "1つの関係の終わりが、もうひとつの友達という関係を強くしてくれたと考えれば、"
        "少し自分の中で区切りがついて成長出来るように感じる。"
        "そしてその優しさを今回受け止めて別の形で必ず返していきたい。"
    ),
    "memo_action": "彼氏と別れたが、友達が変わらず今も優しくしてくれている。そして私のために怒ってくれている。",
    "emotions": ["喜び"],
    "category": ["恋愛", "人間関係", "価値観"],
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _phase20_10_log_row(reply: Any) -> dict[str, Any]:
    meta = _mapping(getattr(reply, "meta", {}))
    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    internal = _mapping(meta.get(EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY))
    safety = _mapping(meta.get(EMLIS_SAFETY_TRIAGE_META_KEY))
    material_route = _mapping(meta.get(EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY))
    gate = _mapping(meta.get("phase20_5_gate_recovery_loop") or meta.get("gate_recovery_loop"))
    public_input_feedback_included = should_include_public_input_feedback(comment_text, meta)
    return {
        "request_id": str(meta.get("observation_trace_id") or ""),
        "response_kind": str(internal.get("response_kind") or ""),
        "public_observation_status": str(meta.get("observation_status") or internal.get("public_observation_status") or ""),
        "comment_text_presence": bool(comment_text),
        "safety_triage_kind": str(safety.get("safety_triage_kind") or internal.get("safety_triage_kind") or ""),
        "material_quality": str(material_route.get("material_quality") or ""),
        "visible_material_slots": list(material_route.get("visible_material_slots") or []),
        "unknown_slots": list(material_route.get("unknown_slots") or []),
        "gate_recovery_attempts": list(internal.get("repair_attempts") or gate.get("internal_response_repair_attempts") or []),
        "public_input_feedback_presence": public_input_feedback_included,
        "rn_modal_opened": bool(public_input_feedback_included and meta.get("observation_status") == "passed"),
    }


@pytest.mark.asyncio
async def test_phase20_10_real_device_a_low_information_reappears_when_limited_composer_scope_stops(
    phase20_10_env: None,
) -> None:
    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-10-a-user",
        subscription_tier="free",
        current_input=dict(_A_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )
    row = _phase20_10_log_row(reply)
    comment_text = str(getattr(reply, "comment_text", "") or "")

    assert row["request_id"]
    assert row["response_kind"] == "low_information_observation"
    assert row["public_observation_status"] == "passed"
    assert row["comment_text_presence"] is True
    assert row["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
    assert row["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert row["visible_material_slots"]
    assert row["unknown_slots"]
    assert row["gate_recovery_attempts"]
    assert row["public_input_feedback_presence"] is True
    assert row["rn_modal_opened"] is True
    assert "何があったか" in comment_text
    assert "なんか今日は全部だるい" not in comment_text
    assert "前から同じことで疲れている" not in comment_text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case_id", "current_input", "expected_response_kind", "expected_safety_triage"),
    [
        ("B", _B_INPUT, "self_denial_safe_state_answer", TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER),
        ("C", _C_INPUT, "normal_observation", TRIAGE_SAFE_OBSERVATION),
        ("D", _D_INPUT, "normal_observation", TRIAGE_SAFE_OBSERVATION),
    ],
)
async def test_phase20_10_real_device_bcd_remain_displayable_without_phase19_runtime_routes(
    phase20_10_env: None,
    case_id: str,
    current_input: Mapping[str, Any],
    expected_response_kind: str,
    expected_safety_triage: str,
) -> None:
    reply = await reply_service.render_emlis_ai_reply(
        user_id=f"phase20-10-{case_id.lower()}-user",
        subscription_tier="free",
        current_input=dict(current_input),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )
    row = _phase20_10_log_row(reply)
    dumped_meta = str(getattr(reply, "meta", {}) or {})
    comment_text = str(getattr(reply, "comment_text", "") or "")

    assert row["response_kind"] == expected_response_kind
    assert row["public_observation_status"] == "passed"
    assert row["comment_text_presence"] is True
    assert row["safety_triage_kind"] == expected_safety_triage
    assert row["public_input_feedback_presence"] is True
    assert row["rn_modal_opened"] is True
    for token in _FORBIDDEN_PHASE19_ROUTE_TOKENS:
        assert token not in dumped_meta
        assert token not in comment_text
    if case_id == "B":
        assert "事実として確定" in comment_text
    else:
        assert "見えたこと：" in comment_text
        assert "Emlisから：" in comment_text
