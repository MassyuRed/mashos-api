# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_environment_state_output_surface_contract_completion import (
    EnvironmentStateOutputSurfaceContract,
    complete_environment_state_output_scope_marker,
    environment_state_output_scoped_line,
    environment_state_output_surface_rejection_reasons,
)

SAMPLE_REALITY_ESCAPE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _connected_contract() -> EnvironmentStateOutputSurfaceContract:
    return EnvironmentStateOutputSurfaceContract(
        connected=True,
        single_record_only=True,
        scope_marker_required=True,
        required_scope_marker="今回の入力では",
        allowed_scope_markers=("今回の入力では", "今の入力では", "この入力では", "今回の記録では", "この記録では"),
    )


@pytest.mark.asyncio
async def test_phase2_current_profile_surface_candidate_receives_scope_marker_before_runtime_gate(monkeypatch) -> None:
    """Phase 2 wires the helper before candidate surface validation without relaxing later Gates."""

    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase2-scope-marker-completion-user",
        subscription_tier="free",
        current_input={
            "id": "phase2-scope-marker-completion-input",
            "created_at": "2026-05-25T00:00:00Z",
            "memo": SAMPLE_REALITY_ESCAPE_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    runtime_gate = diagnostic["runtime_surface_pre_return_gate"]
    candidate = reply.meta["multi_perspective"]["composer_candidate"]
    completion = candidate["composer_meta"]["environment_state_output_scope_marker_completion"]

    assert candidate["status"] == "generated"
    assert candidate["comment_text"]
    assert "今回の入力では" in candidate["comment_text"]
    assert "environment_state_output_scope_marker_missing" not in candidate["rejection_reasons"]
    assert completion["applied"] is True
    assert completion["target_line"] == "first_body_line"
    assert completion["display_gate_relaxed"] is False
    assert runtime_gate["environment_state_output_frame_surface_limited_use"] is True
    assert runtime_gate["environment_state_output_single_record_only"] is True
    assert runtime_gate["environment_state_output_scope_marker_required"] is True
    assert runtime_gate["environment_state_output_scope_marker_present"] is True
    assert runtime_gate["passed"] is True
    assert "environment_state_output_scope_marker_missing" not in diagnostic.get("primary_reason", "")
    # Phase 6 confirms the completed marker surface can pass public display
    # without relaxing the scope-marker or runtime gates.
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text
    assert "今回の入力では" in reply.comment_text


def test_phase1_helper_applies_marker_to_first_body_line_after_greeting() -> None:
    result = complete_environment_state_output_scope_marker(
        "Emlisです。\n外に出る余裕が少なく、画面の中で少し息をつこうとしているように見えます。",
        _connected_contract(),
    )

    lines = result.text.splitlines()
    assert result.evaluated is True
    assert result.applied is True
    assert result.target_line_index == 1
    assert result.before_marker_present is False
    assert result.after_marker_present is True
    assert lines[0] == "Emlisです。"
    assert lines[1].startswith("今回の入力では、")


def test_phase1_helper_is_idempotent_when_marker_already_exists() -> None:
    original = "今回の入力では、画面の中で少し息をつこうとしているように見えます。"
    result = complete_environment_state_output_scope_marker(original, _connected_contract())

    assert result.text == original
    assert result.applied is False
    assert result.before_marker_present is True
    assert result.after_marker_present is True
    assert result.action == "continue"
    assert result.rejection_reasons == ()


def test_phase1_line_helper_keeps_legacy_current_input_core_formatting() -> None:
    assert environment_state_output_scoped_line("今は、少し整えようとしているように見えます。") == (
        "今回の入力では、少し整えようとしているように見えます。"
    )
    assert environment_state_output_scoped_line("今回の入力では、少し整えようとしているように見えます。") == (
        "今回の入力では、少し整えようとしているように見えます。"
    )


def test_phase1_helper_does_not_repair_forbidden_surface_claims() -> None:
    result = complete_environment_state_output_scope_marker(
        "あなたは現実逃避しやすい性格です。",
        _connected_contract(),
    )

    assert result.applied is False
    assert result.action == "reject"
    assert "personality_tendency_surface" in result.rejection_reasons




@pytest.mark.parametrize(
    ("candidate_text", "expected_reason"),
    (
        ("この傾向が最近ずっと続いています。", "period_tendency_from_single_record_surface"),
        ("あなたは現実逃避しやすい性格です。", "personality_tendency_surface"),
        ("これは心理診断として不安の症状です。", "diagnosis_surface"),
        ("原因は家庭環境です。", "cause_from_category_surface"),
        ("原因は不安が強いことです。", "cause_from_emotion_strength_surface"),
        ("回復するには毎日外に出るべきです。", "recovery_prescription_surface"),
    ),
)
def test_phase3_helper_rejects_forbidden_surface_claims_before_marker_repair(
    candidate_text: str, expected_reason: str
) -> None:
    result = complete_environment_state_output_scope_marker(candidate_text, _connected_contract())

    assert result.action == "reject"
    assert result.applied is False
    assert result.before_marker_present is False
    assert result.after_marker_present is False
    assert result.text == candidate_text
    assert expected_reason in result.rejection_reasons
    assert "environment_state_output_scope_marker_missing" not in result.rejection_reasons
    assert result.display_gate_relaxed is False
    assert result.raw_input_included is False


@pytest.mark.parametrize(
    ("candidate_text", "expected_reason"),
    (
        ("今回の入力では、あなたは現実逃避しやすい性格です。", "personality_tendency_surface"),
        ("今回の入力では、これは心理診断として不安の症状です。", "diagnosis_surface"),
        ("今回の入力では、仕事が不安の原因です。", "cause_from_category_surface"),
        ("今回の入力では、原因は不安が強いことです。", "cause_from_emotion_strength_surface"),
        ("今回の入力では、回復するには毎日外に出るべきです。", "recovery_prescription_surface"),
    ),
)
def test_phase3_existing_marker_does_not_allow_forbidden_surface_claims(
    candidate_text: str, expected_reason: str
) -> None:
    result = complete_environment_state_output_scope_marker(candidate_text, _connected_contract())
    reasons = environment_state_output_surface_rejection_reasons(candidate_text, _connected_contract())

    assert result.action == "reject"
    assert result.applied is False
    assert result.before_marker_present is True
    assert result.after_marker_present is True
    assert expected_reason in result.rejection_reasons
    assert expected_reason in reasons
    assert "environment_state_output_scope_marker_missing" not in reasons
    assert result.display_gate_relaxed is False


def test_phase1_surface_rejection_reasons_remain_fail_closed_after_marker() -> None:
    reasons = environment_state_output_surface_rejection_reasons(
        "今回の入力では、仕事が不安の原因です。",
        _connected_contract(),
    )

    assert "environment_state_output_scope_marker_missing" not in reasons
    assert "cause_from_category_surface" in reasons
