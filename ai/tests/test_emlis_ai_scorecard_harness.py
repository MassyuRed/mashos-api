from __future__ import annotations

import pytest

from emlis_ai_coverage_matrix_service import (
    aggregate_emlis_limited_composer_scorecard_events,
    build_emlis_limited_composer_scorecard_event,
    build_emlis_limited_composer_scorecard_harness,
)


def _summary(*, status: str, group: str, reason: str, binding_count: int = 0, expected: int = 0, relation_types=None):
    return {
        "observation_status": status,
        "stage": "grounding" if status == "rejected" else "display",
        "failed_stage": "grounding" if status == "rejected" else "",
        "primary_reason": reason,
        "secondary_reasons": [reason],
        "coverage_group": group,
        "coverage_primary_group": group,
        "coverage_groups": [group],
        "composer_status": "generated",
        "composer_model": "limited_composer.test",
        "binding_present": binding_count > 0,
        "binding_missing": expected > binding_count,
        "binding_count": binding_count,
        "expected_binding_count": expected,
        "binding_diagnostic": {
            "binding_required": expected > 0,
            "binding_present": binding_count > 0,
            "binding_missing": expected > binding_count,
            "binding_count": binding_count,
            "expected_binding_count": expected,
            "relation_types": list(relation_types or []),
        },
    }


def test_step9_scorecard_event_keeps_status_coverage_group_and_binding_contract() -> None:
    event = build_emlis_limited_composer_scorecard_event(
        diagnostic_summary=_summary(
            status="rejected",
            group="anxiety",
            reason="unsupported_sentence",
            binding_count=1,
            expected=2,
            relation_types=["pressure"],
        )
    )

    assert event["version"] == "emlis.limited_composer_scorecard_event.v1"
    assert event["step"] == "9_scorecard_harness"
    assert event["coverage_group"] == "anxiety"
    assert event["observation_status"] == "rejected"
    assert event["binding_present"] is True
    assert event["binding_missing"] is True
    assert event["binding_coverage_denominator"] == 2
    assert event["binding_coverage_numerator"] == 1
    assert event["raw_text_included"] is False


def test_step9_scorecard_aggregates_passed_rejected_unavailable_by_coverage_group() -> None:
    aggregate = aggregate_emlis_limited_composer_scorecard_events(
        [
            _summary(status="passed", group="anxiety", reason="passed", binding_count=2, expected=2, relation_types=["coexistence"]),
            _summary(status="rejected", group="anxiety", reason="unsupported_sentence", binding_count=1, expected=2, relation_types=["pressure"]),
            _summary(status="unavailable", group="relationship", reason="composer_client_not_connected", binding_count=0, expected=0),
        ]
    )

    assert aggregate["version"] == "emlis.limited_composer_scorecard_aggregate.v1"
    assert aggregate["record_count"] == 3
    anxiety = aggregate["by_coverage_group"]["anxiety"]
    relationship = aggregate["by_coverage_group"]["relationship"]
    assert anxiety["passed_count"] == 1
    assert anxiety["rejected_count"] == 1
    assert anxiety["unavailable_count"] == 0
    assert anxiety["binding_expected_count"] == 2
    assert anxiety["binding_present_count"] == 2
    assert anxiety["binding_missing_count"] == 1
    assert anxiety["binding_sentence_expected_total"] == 4
    assert anxiety["binding_sentence_present_total"] == 3
    assert anxiety["binding_sentence_coverage_rate"] == 0.75
    assert relationship["unavailable_count"] == 1
    assert "anxiety" in aggregate["groups_needing_attention"]
    assert "relationship" in aggregate["groups_needing_attention"]
    assert aggregate["raw_input_included"] is False
    assert aggregate["display_gate_relaxed"] is False


def test_step9_scorecard_harness_exposes_current_group_scorecard() -> None:
    summary = _summary(status="passed", group="positive_recovery", reason="passed", binding_count=2, expected=2, relation_types=["recovery"])
    harness = build_emlis_limited_composer_scorecard_harness(diagnostic_summary=summary)

    assert harness["version"] == "emlis.limited_composer_scorecard_harness.v1"
    assert harness["target_step"] == "9_scorecard_harness"
    assert harness["coverage_group"] == "positive_recovery"
    assert harness["coverage_group_scorecard"]["passed_count"] == 1
    assert harness["binding_coverage"]["binding_sentence_coverage_rate"] == 1.0
    assert harness["next_tasks_visible"] is True
    assert harness["raw_input_included"] is False
    assert harness["input_specific_template_added"] is False


def _clear_limited_composer_env(monkeypatch):
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
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.asyncio
async def test_step9_scorecard_harness_is_attached_to_reply_meta(monkeypatch):
    import pytest
    pytest.importorskip("pytest_asyncio")
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step9-scorecard-user",
        subscription_tier="free",
        current_input={
            "id": "step9-scorecard-input",
            "memo": "不安が残っていて、少し休みたい。",
            "emotions": ["不安"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    scorecard = summary["step9_scorecard_harness"]
    assert scorecard["step"] == "9_scorecard_harness"
    assert scorecard["coverage_group"]
    assert scorecard["aggregate"]["record_count"] == 1
    assert scorecard["raw_text_included"] is False
    assert reply.meta["step9_scorecard_harness"] == scorecard
    assert reply.meta["multi_perspective"]["step9_scorecard_harness"] == scorecard
