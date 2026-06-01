# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-13 post-final gate recovery regression tests.

These tests pin the remaining Phase20 display-reliability hole described in
``Cocolon_EmlisAI_Phase20_DisplayReliability_FinalGateRecovery``: after a
candidate has reached a displayable ``passed + comment_text`` state, the final
pre-return visible-surface recheck can still fail closed and return an empty
public observation.  Phase20-13 intentionally adds the regression coverage before
Phase20-14 implements the recovery branch, so the displayable-path tests are red
against the pre-Phase20-14 implementation.
"""

from collections.abc import Mapping
from typing import Any
import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
)
from emlis_ai_observation_eligibility_router import EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY, ResponseKind
from emlis_ai_safety_triage import EMLIS_SAFETY_TRIAGE_META_KEY, TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import GreetingDecision


_PHASE20_13_ENV_KEYS = (
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

_FORCED_FINAL_VISIBLE_GATE_REJECTION = "phase20_13_forced_final_visible_gate_rejection"
_POST_FINAL_META_KEY = "phase20_13_post_final_gate_recovery"
_PUBLIC_FORBIDDEN_EXACT_KEYS = {
    "response_kind",
    "safety_triage_kind",
    "material_quality",
    "observation_text",
    "reception_text",
    "raw_input",
    "raw_text",
    "comment_text_body",
    "comment_text",
}

_PUBLIC_FALSE_BOUNDARY_FLAGS = {
    "raw_input_included",
    "raw_text_included",
    "comment_text_body_included",
    "comment_text_included",
}

_NORMAL_INPUT = {
    "memo": "今日は仕事で予定が急に変わって、気持ちの置き場がなくなった。",
    "memo_action": "予定変更の連絡を受けて、帰ってからも考え続けていた。",
    "emotions": ["不安"],
    "category": ["仕事"],
}
_LOW_INFORMATION_INPUT = {
    "memo": "なんか今日は全部だるい。\n何もしたくない。",
    "memo_action": "",
    "emotions": ["悲しみ", "不安"],
    "category": ["生活"],
}
_LIMITED_GROUNDING_INPUT = {
    "memo": "今、不安が強い。",
    "memo_action": "",
    "emotions": ["不安"],
    "category": ["仕事"],
}
_SELF_DENIAL_INPUT = {
    "memo": "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
    "memo_action": "",
    "emotions": ["悲しみ"],
    "category": ["人生", "価値観"],
}
_EMERGENCY_INPUT = {
    "memo": "もう死にたい。自分を傷つけたい衝動がある。",
    "memo_action": "",
    "emotions": ["悲しみ"],
    "category": ["人生"],
}


@pytest.fixture(autouse=True)
def _patch_source_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="phase20-13-post-final-gate-recovery",
            slot_key="phase20-13-post-final-gate-recovery",
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
def phase20_13_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _PHASE20_13_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _public_meta(reply: Any) -> dict[str, Any]:
    return build_public_emlis_input_feedback_meta(
        _mapping(getattr(reply, "meta", {})),
        comment_text_present=bool(str(getattr(reply, "comment_text", "") or "").strip()),
        subscription_tier="free",
    )


def _internal_contract(reply: Any) -> Mapping[str, Any]:
    return _mapping(_mapping(getattr(reply, "meta", {})).get(EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY))


def _material_route(reply: Any) -> Mapping[str, Any]:
    return _mapping(_mapping(getattr(reply, "meta", {})).get(EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY))


def _safety_triage(reply: Any) -> Mapping[str, Any]:
    return _mapping(_mapping(getattr(reply, "meta", {})).get(EMLIS_SAFETY_TRIAGE_META_KEY))


def _post_final_recovery_meta(reply: Any) -> Mapping[str, Any]:
    meta = _mapping(getattr(reply, "meta", {}))
    direct = _mapping(meta.get(_POST_FINAL_META_KEY))
    if direct:
        return direct
    diagnostic = _mapping(meta.get("diagnostic_summary"))
    return _mapping(diagnostic.get(_POST_FINAL_META_KEY))


def _force_first_nonempty_visible_surface_recheck_failure(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    original = reply_service._build_visible_surface_acceptance_report_for_candidate
    state: dict[str, Any] = {
        "forced": False,
        "nonempty_candidate_seen": False,
        "forced_reasons": [],
    }

    def wrapped_visible_surface_report(**kwargs: Any) -> dict[str, Any]:
        report = dict(original(**kwargs))
        comment_text = str(kwargs.get("comment_text") or "").strip()
        if not comment_text:
            return report
        state["nonempty_candidate_seen"] = True
        if state["forced"]:
            return report
        state["forced"] = True
        state["forced_reasons"] = [_FORCED_FINAL_VISIBLE_GATE_REJECTION]
        report.update(
            {
                "evaluated": True,
                "passed": False,
                "blocked": True,
                "classification": "repair_required",
                "action": "rerender_surface",
                "rerender_recommended": True,
                "surface_repair_requested": True,
                "rejection_reasons": [_FORCED_FINAL_VISIBLE_GATE_REJECTION],
                "repair_reason_family": "phase20_13_final_pre_return_probe",
                "display_gate_relaxed": False,
                "safety_gate_relaxed": False,
                "grounding_gate_relaxed": False,
                "template_gate_relaxed": False,
                "fixed_fallback_used": False,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "public_response_key_change": False,
            }
        )
        return report

    monkeypatch.setattr(
        reply_service,
        "_build_visible_surface_acceptance_report_for_candidate",
        wrapped_visible_surface_report,
    )
    return state


def _assert_public_contract_unchanged(reply: Any) -> None:
    public_meta = _public_meta(reply)

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                assert key not in _PUBLIC_FORBIDDEN_EXACT_KEYS
                if key in _PUBLIC_FALSE_BOUNDARY_FLAGS:
                    assert item is False
                walk(item)
            return
        if isinstance(value, list):
            for item in value:
                walk(item)

    walk(public_meta)
    assert public_meta.get("observation_text") is None
    assert public_meta.get("reception_text") is None


def _assert_post_final_recovery_contract(
    reply: Any,
    *,
    expected_material_quality: str,
    expected_response_kinds: set[str],
) -> None:
    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    meta = _mapping(getattr(reply, "meta", {}))
    internal = _internal_contract(reply)
    material_route = _material_route(reply)
    post_final = _post_final_recovery_meta(reply)

    assert comment_text
    assert meta.get("observation_status") == "passed"
    assert internal.get("response_kind") in expected_response_kinds
    assert material_route.get("material_quality") == expected_material_quality
    assert should_include_public_input_feedback(comment_text, _public_meta(reply)) is True
    assert _public_meta(reply).get("observation_status") == "passed"

    assert post_final.get("schema_version") == "cocolon.emlis.post_final_gate_recovery.v1"
    assert post_final.get("source_phase") == "Phase20-13_Post_Final_Gate_Recovery"
    assert post_final.get("attempted") is True
    assert post_final.get("applied") is True
    assert post_final.get("attempt_count") == 1
    assert post_final.get("original_final_status") in {"rejected", "unavailable"}
    assert post_final.get("final_status_after_recovery") == "passed"
    assert post_final.get("from_gate") in {
        "final_pre_return_gate",
        "final_visible_surface_acceptance_gate",
    }
    assert post_final.get("display_gate_relaxed") is False
    assert post_final.get("safety_gate_relaxed") is False
    assert post_final.get("grounding_gate_relaxed") is False
    assert post_final.get("template_gate_relaxed") is False
    assert post_final.get("fixed_fallback_used") is False
    assert post_final.get("public_response_key_change") is False
    assert post_final.get("comment_text_body_included") is False
    assert post_final.get("raw_input_included") is False
    assert post_final.get("empty_comment_text_exit_allowed") is False
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_normal_observation_recovers_when_final_visible_gate_fails(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-normal-user",
        subscription_tier="free",
        current_input=dict(_NORMAL_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    _assert_post_final_recovery_contract(
        reply,
        expected_material_quality=MATERIAL_QUALITY_ELIGIBLE,
        expected_response_kinds={ResponseKind.NORMAL_OBSERVATION.value},
    )


@pytest.mark.asyncio
async def test_phase20_13_low_information_observation_recovers_when_final_visible_gate_fails(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-low-information-user",
        subscription_tier="free",
        current_input=dict(_LOW_INFORMATION_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    _assert_post_final_recovery_contract(
        reply,
        expected_material_quality=MATERIAL_QUALITY_LOW_INFORMATION,
        expected_response_kinds={ResponseKind.LOW_INFORMATION_OBSERVATION.value},
    )
    assert "何があったか" not in str(getattr(reply, "comment_text", "") or "")
    assert _LOW_INFORMATION_INPUT["memo"].split("\n", maxsplit=1)[0] not in str(getattr(reply, "comment_text", "") or "")


@pytest.mark.asyncio
async def test_phase20_13_limited_grounding_observation_recovers_by_narrowing_scope_when_final_gate_fails(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-limited-grounding-user",
        subscription_tier="free",
        current_input=dict(_LIMITED_GROUNDING_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    _assert_post_final_recovery_contract(
        reply,
        expected_material_quality=MATERIAL_QUALITY_LIMITED_GROUNDING,
        expected_response_kinds={
            ResponseKind.NORMAL_OBSERVATION.value,
            ResponseKind.LIMITED_GROUNDING_OBSERVATION.value,
        },
    )
    comment_text = str(getattr(reply, "comment_text", "") or "")
    assert "原因は" not in comment_text
    assert "あなたは" not in comment_text
    assert "診断" not in comment_text


@pytest.mark.asyncio
async def test_phase20_13_self_denial_prefers_safe_state_answer_over_generic_post_final_recovery(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-self-denial-user",
        subscription_tier="free",
        current_input=dict(_SELF_DENIAL_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    meta = _mapping(getattr(reply, "meta", {}))
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    assert comment_text
    assert meta.get("observation_status") == "passed"
    assert _internal_contract(reply).get("response_kind") == ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER.value
    assert should_include_public_input_feedback(comment_text, _public_meta(reply)) is True
    assert not post_final or post_final.get("applied") is not True
    assert "あなたが悪い" not in comment_text
    assert "事実です" not in comment_text
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_safety_emergency_does_not_run_post_final_recovery_or_become_observation(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-safety-emergency-user",
        subscription_tier="free",
        current_input=dict(_EMERGENCY_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    meta = _mapping(getattr(reply, "meta", {}))
    public_meta = _public_meta(reply)
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["forced"] is False
    assert comment_text == ""
    assert meta.get("observation_status") == "safety_blocked"
    assert _internal_contract(reply).get("response_kind") == ResponseKind.SAFETY_BLOCKED_EMERGENCY.value
    assert _safety_triage(reply).get("requires_block") is True
    assert should_include_public_input_feedback(comment_text, public_meta) is False
    assert public_meta.get("observation_status") != "passed"
    assert not post_final or post_final.get("attempted") is not True
    _assert_public_contract_unchanged(reply)
