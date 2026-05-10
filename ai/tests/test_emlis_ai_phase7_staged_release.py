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
