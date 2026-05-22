from __future__ import annotations

import pytest

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_limited_release_service import (
    build_phase7_rollout_metrics,
    evaluate_limited_composer_release,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _clear_phase7_env(monkeypatch: pytest.MonkeyPatch) -> None:
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
        "COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
        "EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    ):
        monkeypatch.delenv(name, raising=False)


def _current_input(**extra):
    payload = {
        "id": "phase7-emotion",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": SAMPLE_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    payload.update(extra)
    return payload


def _scope_for(payload):
    evidence = build_evidence_ledger(payload)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    return scope


def _assert_step10_rollout_block_meta_consistent(reply) -> None:
    step10 = reply.meta.get("step10_observation_display_repair_integration") or {}
    multi = reply.meta.get("multi_perspective") or {}
    diagnostic = reply.meta.get("diagnostic_summary") or {}
    phase_gate = multi.get("phase_gate") or {}

    assert reply.comment_text == ""
    assert reply.meta["observation_status"] == "unavailable"
    assert diagnostic["observation_status"] == "unavailable"
    assert diagnostic["comment_text_allowed"] is False
    display_trace = multi["gate_trace"]["display_gate"]
    assert display_trace["comment_text_present"] is False
    assert display_trace["comment_text_allowed"] is False
    assert step10 == reply.meta.get("observation_display_repair_integration")
    assert step10 == diagnostic["step10_observation_display_repair_integration"]
    assert step10 == diagnostic["observation_display_repair_integration"]
    assert step10 == multi["step10_observation_display_repair_integration"]
    assert step10 == multi["observation_display_repair_integration"]

    assert step10["applied"] is False
    assert step10["low_information_repair_applied"] is False
    assert step10["original_observation_status"] == "unavailable"
    assert step10["final_observation_status"] == "unavailable"
    assert step10["observation_status"] == "unavailable"
    assert step10["public_observation_status"] == "unavailable"
    assert step10["comment_text_present"] is False
    assert step10["comment_text_allowed"] is False

    blocked_reasons = step10["blocked_reasons"]
    assert "step10_blocked_by_phase7_rollout" in blocked_reasons
    assert "composer_resolution_blocked_rollout" in blocked_reasons
    assert "composer_resolution_pre_connection_rollout_stop" in blocked_reasons
    assert "limited_composer_rollout_not_allowed" in blocked_reasons
    assert "phase7_rollout_gate_blocked" in blocked_reasons

    for unchanged_contract_key in (
        "public_status_extended",
        "observation_status_enum_extended",
        "rn_visible_contract_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "response_shape_changed",
        "display_gate_relaxed",
        "reader_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
    ):
        assert step10[unchanged_contract_key] is False

    for forbidden_runtime_key in (
        "fixed_fallback_used",
        "legacy_safe_fallback_used",
        "external_ai_used",
        "local_llm_used",
        "legacy_input_feedback_template_used",
    ):
        assert step10[forbidden_runtime_key] is False
    assert step10["raw_input_included"] is False
    assert step10["raw_text_included"] is False

    assert phase_gate["step10_observation_display_repair_integration_ready"] is True
    assert phase_gate["step10_low_information_display_repair_applied"] is False
    assert phase_gate["step10_display_gate_relaxed"] is False
    assert phase_gate["step10_public_status_extended"] is False


def test_step10_reply_service_runtime_block_reason_only_blocks_rollout() -> None:
    from emlis_ai_reply_service import _step10_repair_runtime_block_reason

    assert (
        _step10_repair_runtime_block_reason(
            composer_client_resolution={
                "connection_status": "blocked_rollout",
                "pre_connection_stop_stage": "rollout",
                "rejection_reasons": ["limited_composer_rollout_not_allowed"],
            },
            limited_release_decision={
                "enabled": False,
                "reason_code": "rollout_stage_not_matched",
                "rejection_reasons": ["limited_composer_rollout_not_allowed"],
            },
        )
        == "step10_blocked_by_phase7_rollout"
    )

    assert (
        _step10_repair_runtime_block_reason(
            composer_client_resolution={
                "connection_status": "blocked_feature_flag",
                "pre_connection_stop_stage": "flag",
                "rejection_reasons": ["default_limited_composer_feature_disabled"],
            },
            limited_release_decision={
                "enabled": False,
                "reason_code": "feature_flag_disabled",
                "rejection_reasons": ["default_limited_composer_feature_disabled"],
            },
        )
        == ""
    )

    assert (
        _step10_repair_runtime_block_reason(
            composer_client_resolution={
                "connection_status": "blocked_scope",
                "pre_connection_stop_stage": "scope",
                "rejection_reasons": ["limited_composer_scope_not_allowed", "scope_not_eligible"],
            },
            limited_release_decision={
                "enabled": False,
                "cohort": "blocked_scope",
                "reason_code": "scope_limited_case_not_eligible",
                "rejection_reasons": ["limited_composer_scope_not_allowed", "scope_not_eligible"],
            },
        )
        == ""
    )


def test_phase7_default_stage_allows_scope_eligible_limited_cases(monkeypatch):
    _clear_phase7_env(monkeypatch)
    scope = _scope_for(_current_input())

    decision = evaluate_limited_composer_release(
        user_id="phase7-user",
        current_input=_current_input(),
        limited_observation_scope=scope,
        feature_flag_enabled=True,
    )
    metrics = build_phase7_rollout_metrics(
        release_decision=decision,
        observation_status="passed",
        rejection_reasons=[],
    )

    assert decision.stage == "limited_cases"
    assert decision.enabled is True
    assert decision.cohort == "limited_case"
    assert decision.scope_status == "eligible"
    assert metrics["attempted"] is True
    assert metrics["passed_rate_numerator"] == 1
    assert metrics["passed_rate_denominator"] == 1


@pytest.mark.asyncio
async def test_phase7_internal_stage_blocks_non_allowlisted_default_client(monkeypatch):
    _clear_phase7_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "internal")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="not-internal-user",
        subscription_tier="free",
        current_input=_current_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    release = multi["limited_composer_release"]
    metrics = multi["phase7_rollout_metrics"]
    client_meta = multi["composer_client_resolution"]

    assert release["stage"] == "internal"
    assert release["enabled"] is False
    assert "limited_composer_rollout_not_allowed" in release["rejection_reasons"]
    assert client_meta["default_client_used"] is False
    assert client_meta["release_allowed"] is False
    assert metrics["attempted"] is False
    assert reply.comment_text == ""

    _assert_step10_rollout_block_meta_consistent(reply)


@pytest.mark.asyncio
async def test_phase7_internal_stage_allows_allowlisted_user(monkeypatch):
    _clear_phase7_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "internal")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS", "phase7-internal-user")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase7-internal-user",
        subscription_tier="free",
        current_input=_current_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    release = multi["limited_composer_release"]
    metrics = multi["phase7_rollout_metrics"]
    client_meta = multi["composer_client_resolution"]

    assert release["enabled"] is True
    assert release["cohort"] == "internal"
    assert client_meta["default_client_used"] is True
    assert metrics["attempted"] is True
    assert metrics["passed_rate_denominator"] == 1
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}


@pytest.mark.asyncio
async def test_phase7_tutorial_stage_allows_tutorial_case(monkeypatch):
    _clear_phase7_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "tutorial")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase7-tutorial-user",
        subscription_tier="free",
        current_input=_current_input(is_tutorial=True, source="tutorial"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    release = multi["limited_composer_release"]
    metrics = multi["phase7_rollout_metrics"]

    assert release["stage"] == "tutorial"
    assert release["enabled"] is True
    assert release["cohort"] == "tutorial"
    assert multi["composer_client_resolution"]["default_client_used"] is True
    assert metrics["attempted"] is True
    assert metrics["aggregation_key"] == "tutorial:tutorial"
