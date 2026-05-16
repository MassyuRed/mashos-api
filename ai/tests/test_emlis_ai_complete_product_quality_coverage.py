from __future__ import annotations

from emlis_ai_complete_scorecard_service import (
    COMPLETE_COVERAGE_GROUP_ORDER,
    COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION,
    aggregate_complete_scorecard_events,
    build_complete_initial_fixture_suite,
    normalize_complete_scorecard_event,
)


def _event(group: str, *, displayed: bool, relation: str, reason: str = "") -> dict[str, object]:
    return {
        "version": "emlis.complete_scorecard_event.v1",
        "event_kind": "complete_composer_initial_reply_attempt",
        "complete_candidate_seen": True,
        "complete_candidate_generated": True,
        "complete_candidate_displayed": displayed,
        "eligible_count": 1,
        "passed_display_count": 1 if displayed else 0,
        "candidate_generated_count": 1,
        "observation_status": "passed" if displayed else "rejected",
        "coverage_group": group,
        "coverage_scope": group,
        "binding_pass": displayed,
        "binding_count": 2 if displayed else 1,
        "relation_types": [relation],
        "gate_rejection_reasons": [reason] if reason else [],
        "top_rejection_reasons": [reason] if reason else [],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def test_product_quality_coverage_suite_defines_required_structural_groups_without_raw_text() -> None:
    suite = build_complete_initial_fixture_suite()
    expected_groups = (
        "short_daily",
        "long_meaning_arc",
        "conflict",
        "recovery",
        "pressure",
        "desire_fear",
        "relationship",
    )

    assert tuple(COMPLETE_COVERAGE_GROUP_ORDER) == expected_groups
    assert suite["product_quality_coverage_suite_version"] == COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION
    assert tuple(suite["coverage_groups"]) == expected_groups
    assert suite["missing_coverage_groups"] == []
    assert suite["fixture_suite_ready"] is True
    assert set(suite["coverage_taxonomy"]) == set(expected_groups)

    desire_case = next(case for case in suite["fixtures"] if case["coverage_group"] == "desire_fear")
    assert "approach_avoidance" in desire_case["target_relations"]
    assert "desire_and_fear_coexist" in desire_case["eligible_conditions"]
    assert "advice_like" in desire_case["expected_primary_reasons"]

    for case in suite["fixtures"]:
        assert case["coverage_suite_version"] == COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION
        assert case["coverage_group"] in expected_groups
        assert case["eligible_conditions"]
        assert case["ng_conditions"]
        assert case["expected_primary_reasons"]
        assert case["raw_input_included"] is False
        assert case["raw_text_included"] is False
        assert "raw_text" not in case


def test_product_quality_coverage_normalizes_desire_fear_from_approach_avoidance_relation() -> None:
    normalized = normalize_complete_scorecard_event(
        _event("", displayed=False, relation="approach_avoidance", reason="relation_missing")
    )

    assert normalized["coverage_group"] == "desire_fear"
    assert normalized["top_rejection_reasons"] == ["relation_missing"]
    assert normalized["raw_input_included"] is False
    assert normalized["comment_text_included"] is False


def test_product_quality_coverage_report_aggregates_group_reasons() -> None:
    events = [
        _event("short_daily", displayed=True, relation="residue"),
        _event("long_meaning_arc", displayed=False, relation="residue", reason="focus_drift"),
        _event("conflict", displayed=False, relation="contrast", reason="relation_not_expressed"),
        _event("recovery", displayed=True, relation="recovery"),
        _event("pressure", displayed=False, relation="pressure", reason="diagnostic_tone"),
        _event("desire_fear", displayed=False, relation="approach_avoidance", reason="advice_like"),
        _event("relationship", displayed=False, relation="coexistence", reason="personality_claim"),
    ]
    aggregate = aggregate_complete_scorecard_events(events)

    assert aggregate["missing_fixture_groups"] == []
    assert aggregate["fixture_coverage_rate"] == 1.0
    assert aggregate["by_coverage_group"]["desire_fear"]["reason_counts"]["advice_like"] == 1
    assert aggregate["by_coverage_group"]["relationship"]["reason_counts"]["personality_claim"] >= 1
    assert aggregate["raw_input_included"] is False
    assert aggregate["display_gate_relaxed"] is False
