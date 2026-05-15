from __future__ import annotations

import pytest

from emlis_ai_rollout_metrics_service import (
    STEP16_ROLLOUT_METRIC_EVENT_VERSION,
    STEP16_ROLLOUT_METRICS_AGGREGATE_VERSION,
    STEP16_ROLLOUT_METRICS_VERSION,
    aggregate_emlis_rollout_metrics,
    build_emlis_rollout_metric_event,
)


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _clear_limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
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
        "id": "step16-emotion",
        "created_at": "2026-05-14T00:00:00Z",
        "memo": SAMPLE_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    payload.update(extra)
    return payload


def _record(status: str, reason: str, group: str, *, attempted: bool = True, stage: str = "limited_cases"):
    cohort = {
        "internal": "internal",
        "tutorial": "tutorial",
        "limited_cases": "limited_case",
        "all": "all",
    }.get(stage, "limited_case") if attempted else "blocked"
    return build_emlis_rollout_metric_event(
        release_meta={
            "stage": stage,
            "cohort": cohort,
            "enabled": attempted,
            "attempted": attempted,
            "reason_code": "scope_limited_case_allowed" if attempted else "feature_flag_disabled",
        },
        phase7_rollout_metrics={
            "attempted": attempted,
            "observation_status": status,
            "stage": stage,
            "cohort": cohort,
        },
        diagnostic_summary={
            "version": "emlis.diagnostic_summary.v1",
            "observation_status": status,
            "stage": "display" if status == "passed" else "composer",
            "primary_reason": reason,
            "secondary_reasons": [] if reason == "passed" else [reason],
            "coverage_primary_group": group,
            "coverage_groups": [group],
            "coverage_scope": "partial_observation",
            "coverage_next_steps": ["Step16_rollout_metrics"],
            "composer_model": "cocolon_limited_composer.v1" if attempted else "",
            "composer_status": "generated" if attempted else "not_attempted",
        },
    )


def test_step16_rollout_metric_record_keeps_required_decision_fields() -> None:
    metrics = _record("rejected", "unsupported_sentence", "gate_quality")

    assert metrics["version"] == STEP16_ROLLOUT_METRIC_EVENT_VERSION
    assert metrics["phase"] == "B-R1"
    assert metrics["step"] == "Step16_rollout_metrics"
    assert metrics["attempted"] is True
    assert metrics["rejected"] is True
    assert metrics["primary_reason"] == "unsupported_sentence"
    assert metrics["coverage_group"] == "gate_quality"
    assert metrics["composer_model"] == "cocolon_limited_composer.v1"
    assert metrics["aggregation_dimensions"]["primary_reason"] == "unsupported_sentence"
    assert set(("attempted", "primary_reason", "coverage_group", "composer_model")).issubset(metrics["metric_fields"])


def test_step16_rollout_metric_aggregate_counts_status_reason_group_and_model() -> None:
    records = [
        _record("passed", "passed", "positive_recovery", stage="internal"),
        _record("passed", "passed", "relationship", stage="tutorial"),
        _record("rejected", "unsupported_sentence", "gate_quality", stage="limited_cases"),
        _record("unavailable", "default_limited_composer_feature_disabled", "connection_rollout", attempted=False),
        _record("safety_blocked", "safety_boundary", "safety_boundary", attempted=False, stage="all"),
    ]

    aggregate = aggregate_emlis_rollout_metrics(records)

    assert aggregate["version"] == STEP16_ROLLOUT_METRICS_AGGREGATE_VERSION
    assert aggregate["event_count"] == 5
    assert aggregate["attempted"] == 3
    assert aggregate["passed"] == 2
    assert aggregate["rejected"] == 1
    assert aggregate["unavailable"] == 1
    assert aggregate["safety_blocked"] == 1
    assert aggregate["passed_rate_numerator"] == 2
    assert aggregate["passed_rate_denominator"] == 3
    assert aggregate["by_primary_reason"]["unsupported_sentence"] == 1
    assert aggregate["by_coverage_group"]["gate_quality"] == 1
    assert aggregate["by_composer_model"]["cocolon_limited_composer.v1"] == 3
    assert aggregate["by_stage"]["internal"]["passed"] == 1
    assert aggregate["by_stage"]["tutorial"]["passed"] == 1
    assert aggregate["by_stage"]["limited_cases"]["rejected"] == 1
    assert aggregate["by_stage"]["all"]["safety_blocked"] == 1
    assert aggregate["ap0_judgement"]["do_not_promote_from_passed_only"] is True


@pytest.mark.asyncio
async def test_step16_rollout_metrics_are_added_to_render_meta_for_limited_cases(monkeypatch) -> None:
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "limited_cases")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step16-limited-user",
        subscription_tier="free",
        current_input=_current_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    metrics = multi["step16_rollout_metrics"]
    summary = reply.meta["diagnostic_summary"]
    phase_gate = multi["phase_gate"]

    assert metrics == reply.meta["step16_rollout_metrics"]
    assert summary["step16_rollout_metrics"] == metrics
    assert multi["rollout_metrics"] == metrics
    assert metrics["version"] == STEP16_ROLLOUT_METRICS_VERSION
    assert metrics["phase"] == "B-R1"
    assert metrics["stage"] == "limited_cases"
    assert metrics["attempted"] is True
    assert metrics["observation_status"] == reply.meta["observation_status"]
    assert metrics["primary_reason"] == summary["primary_reason"]
    assert metrics["coverage_group"] == summary["coverage_primary_group"]
    assert metrics["composer_model"] == summary["composer_model"]
    assert metrics["passed_rate_denominator"] == 1
    assert metrics["internal_qa_aggregate"]["event_count"] == 1
    assert phase_gate["step16_rollout_metrics_ready"] is True
    assert phase_gate["step16_rollout_metrics_aggregation_ready"] is True
    assert "primary_reason" in phase_gate["step16_rollout_metric_fields"]


@pytest.mark.asyncio
async def test_step16_rollout_metrics_classify_not_attempted_before_composer(monkeypatch) -> None:
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step16-disabled-user",
        subscription_tier="free",
        current_input=_current_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    metrics = reply.meta["multi_perspective"]["step16_rollout_metrics"]
    summary = reply.meta["diagnostic_summary"]

    assert metrics["attempted"] is False
    assert metrics["passed_rate_denominator"] == 0
    assert metrics["observation_status"] == "unavailable"
    assert metrics["primary_reason"] == "default_limited_composer_feature_disabled"
    assert metrics["composer_model"] == "not_connected"
    assert metrics["aggregation_dimensions"]["primary_reason"] == summary["primary_reason"]
    assert reply.comment_text == ""
