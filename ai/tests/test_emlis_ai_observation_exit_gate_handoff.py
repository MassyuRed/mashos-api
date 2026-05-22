from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_observation_exit_gate_handoff import (
    OBSERVATION_EXIT_GATE_HANDOFF_STEP,
    OBSERVATION_EXIT_GATE_HANDOFF_VERSION,
    ROLLBACK_CONDITION_IDS,
    assert_observation_exit_gate_handoff_meta_only,
    build_observation_exit_gate_handoff,
    build_observation_exit_gate_rollback_conditions,
    dump_observation_exit_gate_handoff,
)
from emlis_ai_observation_regression_fixture_coverage import (
    FIXTURE_GROUP_SHORT_LOW_INFORMATION,
    build_observation_regression_fixture_coverage,
    build_observation_regression_fixture_scorecard_events,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
)
from emlis_ai_observation_scorecard_blind_qa import build_observation_scorecard_blind_qa


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in ("raw_input", "raw_text", "input_text", "user_input", "comment_text", "reply_text", "body", "text"):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _green_review() -> dict[str, Any]:
    return {
        "review_id": "step14-blind-green",
        "ratings": {
            # Observation Reply Step12 dimensions.
            "read_feeling": "green",
            "input_arrangement": "green",
            "state_verbalization": "green",
            "low_info_question_quality": "green",
            "user_fact_boundary": "green",
            "overclaim_absence": "green",
            "non_template": "green",
            # Existing Product Quality dimensions, for scorecard integration.
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
        },
    }


def test_step14_exit_gate_ready_when_scorecard_and_regression_coverage_meet_thresholds() -> None:
    events = build_observation_regression_fixture_scorecard_events()
    scorecard = build_observation_scorecard_blind_qa(
        scorecard_events=events,
        blind_qa_reviews=[_green_review()],
        run_id="step14-ready",
    )
    gate = build_observation_exit_gate_handoff(scorecard=scorecard, run_id="step14-ready")

    assert gate["version"] == OBSERVATION_EXIT_GATE_HANDOFF_VERSION
    assert gate["step"] == OBSERVATION_EXIT_GATE_HANDOFF_STEP
    assert gate["observation_exit_gate_handoff_ready"] is True
    assert gate["step14_observation_exit_gate_handoff_ready"] is True
    assert gate["handoff_only"] is True
    assert gate["release_blockers"] == []
    assert gate["rollback_required"] is False
    assert gate["rollback_triggered_conditions"] == []
    assert gate["metrics"]["always_display_rate"] == 1.0
    assert gate["metrics"]["eligible_observation_rate"] >= 0.9
    assert gate["metrics"]["low_info_observation_rate"] == 1.0
    assert gate["metrics"]["false_eligible_count"] == 0
    assert gate["metrics"]["free_user_fact_violation_count"] == 0
    assert gate["metrics"]["blind_qa_fatal_count"] == 0
    assert gate["regression_fixture_coverage"]["ready"] is True
    assert gate["public_contract_unchanged"] is True
    assert gate["product_gate_ready"] is False
    assert gate["product_gate_achieved"] is False
    assert gate["public_release_applied"] is False
    assert gate["release_judgment"]["release_allowed"] is False
    assert {item["condition_id"] for item in gate["rollback_conditions"]} == set(ROLLBACK_CONDITION_IDS)
    _assert_meta_only(gate)


def test_step14_detects_threshold_failures_contract_changes_and_rollback_triggers() -> None:
    event = build_observation_regression_fixture_scorecard_events()[0]
    bad_event = dict(event)
    bad_event["observation_reply_meta"] = {
        **dict(event["observation_reply_meta"]),
        "observation_reply_kind": OBSERVATION_REPLY_KIND_ELIGIBLE,
        "eligibility_status": OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        "eligible_for_full_observation": True,
    }
    bad_event["expected_observation_reply_kind"] = "low_information_observation"
    bad_event["expected_eligibility_status"] = "low_information"
    bad_event["user_fact_grounding_mode"] = "explicit_reference"
    bad_event["facts_used"] = [{"fact_id": "fact-leak"}]
    bad_event["free_user_fact_violation"] = True

    scorecard = build_observation_scorecard_blind_qa(
        scorecard_events=[bad_event],
        blind_qa_reviews=[_green_review()],
        run_id="step14-blocked",
    )
    gate = build_observation_exit_gate_handoff(
        scorecard=scorecard,
        contract_observations={"api_route_changed": True, "rn_visible_contract_changed": True},
        run_id="step14-blocked",
    )

    assert gate["observation_exit_gate_handoff_ready"] is False
    assert gate["rollback_required"] is True
    assert "false_eligible_detected" in gate["rollback_triggered_conditions"]
    assert "free_user_fact_violation_detected" in gate["rollback_triggered_conditions"]
    assert "api_route_changed" in gate["rollback_triggered_conditions"]
    assert "rn_public_contract_changed" in gate["rollback_triggered_conditions"]
    assert "low_info_observation_rate_below_100_percent" in gate["rollback_triggered_conditions"]
    assert "false_eligible_zero" in gate["exit_gate_blockers"]
    assert any(item.startswith("public_contract_changed:api_route_changed") for item in gate["release_blockers"])
    assert gate["api_route_changed"] is False
    assert gate["rn_visible_contract_changed"] is False
    assert gate["product_gate_ready"] is False
    _assert_meta_only(gate)


def test_step14_uses_step13_fixture_coverage_and_fails_missing_groups() -> None:
    events = [event for event in build_observation_regression_fixture_scorecard_events() if event["fixture_group"] == FIXTURE_GROUP_SHORT_LOW_INFORMATION]
    coverage = build_observation_regression_fixture_coverage(scorecard_events=events)
    scorecard = build_observation_scorecard_blind_qa(
        scorecard_events=events,
        blind_qa_reviews=[_green_review()],
    )
    gate = build_observation_exit_gate_handoff(scorecard=scorecard, regression_fixture_coverage=coverage)

    assert gate["observation_exit_gate_handoff_ready"] is False
    assert gate["regression_fixture_coverage"]["ready"] is False
    assert "step13_regression_fixture_coverage_ready" in gate["exit_gate_blockers"]
    assert gate["regression_fixture_coverage"]["missing_fixture_groups"]
    _assert_meta_only(gate)


def test_step14_dump_and_meta_only_contract_reject_text_and_public_release_side_effects() -> None:
    with pytest.raises(ValueError):
        build_observation_exit_gate_handoff(contract_observations={"comment_text": "must not leak"})
    with pytest.raises(ValueError):
        assert_observation_exit_gate_handoff_meta_only({"product_gate_ready": True})
    with pytest.raises(ValueError):
        assert_observation_exit_gate_handoff_meta_only({"public_release_applied": True})

    gate = build_observation_exit_gate_handoff(
        scorecard=build_observation_scorecard_blind_qa(
            scorecard_events=build_observation_regression_fixture_scorecard_events(),
            blind_qa_reviews=[_green_review()],
        )
    )
    dumped = dump_observation_exit_gate_handoff(gate)
    parsed = json.loads(dumped)
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert '"comment_text"' not in dumped
    assert "must not leak" not in dumped


def test_step14_connects_to_product_quality_scorecard_as_handoff_only() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=build_observation_regression_fixture_scorecard_events(),
        blind_qa_reviews=[_green_review()],
    )

    assert scorecard["observation_exit_gate_handoff_version"] == OBSERVATION_EXIT_GATE_HANDOFF_VERSION
    assert scorecard["observation_exit_gate_handoff_step"] == OBSERVATION_EXIT_GATE_HANDOFF_STEP
    assert scorecard["step14_observation_exit_gate_handoff_ready"] is True
    assert scorecard["observation_exit_gate_handoff_ready"] is True
    assert scorecard["observation_exit_gate_release_blockers"] == []
    assert scorecard["observation_exit_gate_rollback_required"] is False
    assert scorecard["observation_exit_gate_handoff"]["release_judgment"]["release_allowed"] is False
    assert scorecard["observation_exit_gate_handoff"]["public_release_applied"] is False
    _assert_meta_only(scorecard["observation_exit_gate_handoff"])


def test_step14_rollback_catalog_is_fixed_and_meta_only() -> None:
    catalog = build_observation_exit_gate_rollback_conditions()

    assert [item["condition_id"] for item in catalog] == list(ROLLBACK_CONDITION_IDS)
    assert any(item["rollback_target"] == "Step3_User_Fact_Grounding_Boundary" for item in catalog)
    _assert_meta_only(catalog)
