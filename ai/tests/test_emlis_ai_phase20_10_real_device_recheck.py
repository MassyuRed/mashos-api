# -*- coding: utf-8 -*-
from __future__ import annotations

"""Historical Phase20-10 local public-delivery regression guards.

The local A/B/C/D names in this file belong to the earlier Phase20-10 delivery
check; they are not the current core-repair A-D semantic fixtures. This test
owns only public status, comment presence, Safety, canonical body-free metadata
and RN modal eligibility.  It is not real-device evidence and never records a
Product Read Feel result. Exact/sub-string response expectations belong to the
separate grounded semantic-quality tests.
"""

from collections.abc import Mapping
from typing import Any

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
from emlis_ai_grounded_observation_gate import GROUND_OBSERVATION_REPLY_GENERATION_PATH
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY
from emlis_ai_safety_triage import (
    EMLIS_SAFETY_TRIAGE_META_KEY,
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)
from emlis_ai_types import GreetingDecision


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
            slot_name="phase20-10-historical-local-display",
            slot_key="phase20-10-historical-local-display",
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
    grounded = _mapping(meta.get("grounded_observation"))
    public_input_feedback_included = should_include_public_input_feedback(comment_text, meta)
    return {
        "request_id": str(meta.get("observation_trace_id") or ""),
        "response_kind": str(internal.get("response_kind") or ""),
        "public_observation_status": str(meta.get("observation_status") or internal.get("public_observation_status") or ""),
        "comment_text_presence": bool(comment_text),
        "safety_triage_kind": str(safety.get("safety_triage_kind") or internal.get("safety_triage_kind") or ""),
        "material_quality": str(grounded.get("material_quality") or ""),
        "generation_path": str(grounded.get("generation_path") or ""),
        "composer_source": str(grounded.get("composer_source") or ""),
        "semantic_quality_gate": str(grounded.get("semantic_quality_gate") or ""),
        "product_readfeel_status": str(grounded.get("product_readfeel_status") or ""),
        "public_reply_path_connected": grounded.get("public_reply_path_connected") is True,
        "public_input_feedback_presence": public_input_feedback_included,
        "rn_modal_opened": bool(public_input_feedback_included and meta.get("observation_status") == "passed"),
        "evidence_scope": "historical_local_display_only",
        "actual_device_evidence": False,
    }


def _assert_current_canonical_display_meta(row: Mapping[str, Any]) -> None:
    assert row["generation_path"] == GROUND_OBSERVATION_REPLY_GENERATION_PATH
    assert row["composer_source"] == "grounded_plan_realizer"
    assert row["semantic_quality_gate"] == "passed"
    assert row["product_readfeel_status"] == "not_evaluated"
    assert row["public_reply_path_connected"] is True
    assert row["evidence_scope"] == "historical_local_display_only"
    assert row["actual_device_evidence"] is False


@pytest.mark.asyncio
async def test_phase20_10_historical_local_a_uses_current_canonical_display_meta() -> None:
    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-10-a-user",
        subscription_tier="free",
        current_input=dict(_A_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )
    row = _phase20_10_log_row(reply)
    assert row["request_id"]
    assert row["response_kind"] == "low_information_observation"
    assert row["public_observation_status"] == "passed"
    assert row["comment_text_presence"] is True
    assert row["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
    assert row["material_quality"] == "short_state_sufficient"
    assert row["public_input_feedback_presence"] is True
    assert row["rn_modal_opened"] is True
    _assert_current_canonical_display_meta(row)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case_id", "current_input", "expected_response_kind", "expected_safety_triage"),
    [
        ("B", _B_INPUT, "self_denial_safe_state_answer", TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER),
        ("C", _C_INPUT, "normal_observation", TRIAGE_SAFE_OBSERVATION),
        ("D", _D_INPUT, "normal_observation", TRIAGE_SAFE_OBSERVATION),
    ],
)
async def test_phase20_10_historical_local_bcd_remain_canonical_and_displayable(
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
    _assert_current_canonical_display_meta(row)
    for token in _FORBIDDEN_PHASE19_ROUTE_TOKENS:
        assert token not in dumped_meta
        assert token not in comment_text
