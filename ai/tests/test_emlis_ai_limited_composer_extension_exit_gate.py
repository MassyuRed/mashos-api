from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "ai_inference"))

from emlis_ai_limited_composer_extension_exit_gate import build_limited_composer_extension_e2e_exit_gate


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""

_LIMITED_COMPOSER_ENV_KEYS = (
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
    "COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    "EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
)


def _clear_limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _LIMITED_COMPOSER_ENV_KEYS:
        monkeypatch.delenv(name, raising=False)


def _enable_limited_composer(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "1")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "limited")


def _input(memo: str = SAMPLE_MEMO) -> dict:
    return {
        "id": "step11-e2e-input",
        "created_at": "2026-05-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _body_lines(text: str) -> list[str]:
    return [line.strip() for line in str(text or "").splitlines()[1:] if line.strip()]


def _assert_step11_attached(reply, *, expected_status: str) -> dict:
    summary = reply.meta["diagnostic_summary"]
    step11 = summary["step11_e2e_exit_gate"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]

    assert step11["version"] == "emlis.limited_composer_extension_e2e_exit_gate.v1"
    assert step11["step"] == "11_E2E_test_fixed"
    assert step11["exit_gate_name"] == "limited_composer_extension_exit_gate"
    assert step11["observation_status"] == expected_status
    assert step11 == summary["step11_e2e_test_fixed"]
    assert step11 == summary["limited_composer_extension_exit_gate"]
    assert step11 == summary["limited_composer_extension_exit_gate_e2e"]
    assert step11 == reply.meta["step11_e2e_exit_gate"]
    assert step11 == reply.meta["step11_e2e_test_fixed"]
    assert step11 == reply.meta["limited_composer_extension_exit_gate"]
    assert step11 == reply.meta["limited_composer_extension_exit_gate_e2e"]
    assert step11 == reply.meta["multi_perspective"]["step11_e2e_exit_gate"]
    assert step11 == reply.meta["multi_perspective"]["limited_composer_extension_exit_gate"]

    assert phase_gate["step11_e2e_contract_passed"] is True
    assert phase_gate["step11_previous_steps_missing"] == step11["previous_steps_missing"]
    assert phase_gate["step11_e2e_release_blockers"] == step11["release_blockers"]
    assert step11["passed_only_display_contract_preserved"] is True
    assert step11["step10_display_contract_passed"] is True
    assert step11["raw_input_included"] is False
    assert step11["raw_input_required_for_debug"] is False
    assert step11["input_specific_template_added"] is False
    assert step11["fixed_completion_template_added"] is False
    assert step11["role_completion_template_added"] is False
    assert step11["display_gate_relaxed"] is False
    assert step11["reader_grounding_template_relaxed"] is False
    assert step11["db_api_rename_performed"] is False
    assert step11["response_key_rename_performed"] is False

    for step_name in (
        "step0_baseline",
        "step1_connection_visibility",
        "step2_diagnostic_summary_extension",
        "step3_sentence_binding",
        "step6_binding_aware_grounding",
        "step7_gate_binding_reflection",
        "step9_scorecard_harness",
        "step10_e2e_display_contract",
    ):
        assert step11["previous_step_presence"][step_name] is True

    return step11


def test_step11_exit_gate_marks_step10_display_contract_blocker() -> None:
    step11 = build_limited_composer_extension_e2e_exit_gate(
        diagnostic_summary={
            "observation_status": "passed",
            "primary_reason": "passed",
            "failed_stage": "display",
            "coverage_group": "anxiety",
            "gate_results": {
                "reader": {"passed": True, "binding_present": True},
                "grounding": {"passed": True, "binding_present": True},
                "template_echo": {"passed": True, "binding_present": True},
                "display": {"passed": True, "binding_present": True},
            },
            "binding_diagnostic": {"binding_present": True, "binding_count": 1, "expected_binding_count": 1},
            "step9_scorecard_harness": {"ready": True, "next_tasks_visible": True},
            "step10_e2e_display_contract": {"contract_passed": False, "release_blockers": ["non_passed_comment_text_exposed"]},
        }
    )

    assert step11["contract_passed"] is False
    assert "step10_display_contract_not_passed" in step11["release_blockers"]
    assert "non_passed_comment_text_exposed" in step11["release_blockers"]
    assert step11["display_gate_relaxed"] is False
    assert step11["raw_input_included"] is False


@pytest.mark.asyncio
async def test_step11_e2e_exit_gate_ready_after_limited_composer_passed_fixture(monkeypatch):
    _enable_limited_composer(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step11-e2e-passed-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    step11 = _assert_step11_attached(reply, expected_status="passed")
    summary = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    body_lines = _body_lines(reply.comment_text)

    assert reply.comment_text.strip()
    assert summary["primary_reason"] == "passed"
    assert step11["release_blockers"] == []
    assert step11["previous_steps_missing"] == []
    assert step11["all_previous_step_meta_present"] is True
    assert step11["required_gate_results_present"] is True
    assert step11["gate_binding_trace_present"] is True
    assert step11["binding_present"] is True
    assert step11["binding_missing"] is False
    assert step11["binding_count"] == len(body_lines)
    assert step11["expected_binding_count"] == len(body_lines)
    assert step11["all_body_sentences_bound"] is True
    assert step11["relation_taxonomy_present"] is True
    assert step11["relation_not_expressed_traceable"] is True
    assert step11["scorecard_ready"] is True
    assert step11["scorecard_next_tasks_visible"] is True
    assert step11["limited_extension_exit_gate_ready"] is True
    assert step11["limited_composer_extension_complete"] is True
    assert step11["ready_for_complete_composer_initial"] is True
    assert phase_gate["step11_e2e_exit_gate_ready"] is True
    assert phase_gate["limited_composer_extension_exit_gate_ready"] is True
    assert phase_gate["ready_for_complete_composer_initial"] is True


@pytest.mark.asyncio
async def test_step11_e2e_unavailable_fixture_preserves_fail_closed_contract(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step11-e2e-unavailable-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    step11 = _assert_step11_attached(reply, expected_status="unavailable")
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]

    assert reply.comment_text == ""
    assert step11["contract_passed"] is True
    assert step11["limited_extension_exit_gate_ready"] is False
    assert step11["ready_for_complete_composer_initial"] is False
    assert step11["release_blockers"] == []
    assert step11["previous_steps_missing"] == []
    assert "not_a_passed_exit_candidate" in step11["non_blocking_reasons"]
    assert "fail_closed_contract_preserved" in step11["non_blocking_reasons"]
    assert phase_gate["step11_e2e_exit_gate_ready"] is False
    assert phase_gate["step11_e2e_contract_passed"] is True
