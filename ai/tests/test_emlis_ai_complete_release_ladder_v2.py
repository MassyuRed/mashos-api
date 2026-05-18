from __future__ import annotations

from typing import Any

from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER
from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_complete_release_ladder_service import (
    COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION,
    build_complete_product_quality_release_ladder,
    build_complete_product_quality_release_ladder_criteria,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_key_written") is not True
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in {"raw_text", "raw_input", "input_text", "user_input", "comment_text", "reply_text"}:
                assert value in ("", None, [], {})
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _event(group: str, *, status: str = "passed", reason: str = "") -> dict[str, Any]:
    passed = status == "passed"
    return {
        "event_kind": "complete_product_quality_fixture_case",
        "coverage_group": group,
        "observation_status": status,
        "display_passed": passed,
        "complete_candidate_generated": True,
        "eligible_count": 1,
        "passed_display_count": 1 if passed else 0,
        "rejected_count": 0 if passed else 1,
        "binding_count": 2,
        "expected_binding_count": 2,
        "binding_supported_sentence_count": 2 if passed else 0,
        "template_major_count": 0,
        "safety_major_count": 0,
        "top_rejection_reasons": [reason] if reason else [],
        "gate_rejection_reasons": [reason] if reason else [],
        "relation_types": ["coexistence"],
    }


def _green_blind_review(group: str = "short_daily") -> dict[str, Any]:
    return {
        "run_id": "blind-run-step7",
        "fixture_set_id": "product-quality-fixtures",
        "coverage_group": group,
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def test_step7_release_ladder_criteria_are_meta_only_and_match_design_thresholds() -> None:
    criteria = build_complete_product_quality_release_ladder_criteria()

    assert criteria["version"] == "emlis.complete_product_quality_release_ladder_criteria.v1"
    assert criteria["target_step"] == "Step7_Release_ladder_connection"
    assert criteria["stage_order"] == ["internal", "limited", "broader_beta", "product_gate"]
    assert criteria["targets"]["connection_display_target"] == 0.8
    assert criteria["targets"]["product_gate_display_target"] == 0.9
    assert criteria["targets"]["binding_pass_rate"] == 0.98
    assert criteria["targets"]["broader_read_feeling_target"] == 0.85
    assert criteria["targets"]["product_gate_read_feeling_target"] == 0.9
    assert criteria["comment_text_contract"] == "passed_only"
    _assert_meta_only(criteria)


def test_step7_single_reply_scorecard_stays_internal_until_aggregate_coverage_is_ready() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_event=_event("short_daily"),
        blind_qa_reviews=[],
    )
    ladder = build_complete_product_quality_release_ladder(
        product_quality_scorecard=scorecard,
        diagnostic_summary={"gate_binding_contract_version": "emlis.gate_binding_contract.v2"},
    )

    assert ladder["version"] == COMPLETE_PRODUCT_QUALITY_RELEASE_LADDER_VERSION
    assert ladder["release_ladder_connected"] is True
    assert ladder["current_stage"] == "internal"
    assert ladder["stage_evaluations"]["internal"]["allowed"] is True
    assert ladder["stage_evaluations"]["limited"]["allowed"] is False
    assert "limited_coverage_group_count_below_minimum" in ladder["stage_evaluations"]["limited"]["blockers"]
    assert ladder["product_gate_ready"] is False
    assert ladder["product_gate_reached"] is False
    assert ladder["product_gate_public_release_applied"] is False
    assert ladder["release_judgment"]["release_allowed"] is False
    assert ladder["comment_text_contract"] == "passed_only"
    _assert_meta_only(ladder)


def test_step7_full_green_scorecard_allows_product_gate_transition_without_public_release_side_effects() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[_event(group) for group in COMPLETE_COVERAGE_GROUP_ORDER],
        blind_qa_reviews=[_green_blind_review(group) for group in COMPLETE_COVERAGE_GROUP_ORDER],
    )
    ladder = build_complete_product_quality_release_ladder(
        product_quality_scorecard=scorecard,
        diagnostic_summary={"gate_binding_contract_version": "emlis.gate_binding_contract.v2"},
    )

    assert ladder["stage_evaluations"]["internal"]["allowed"] is True
    assert ladder["stage_evaluations"]["limited"]["allowed"] is True
    assert ladder["stage_evaluations"]["broader_beta"]["allowed"] is True
    assert ladder["stage_evaluations"]["product_gate"]["allowed"] is True
    assert ladder["max_allowed_stage"] == "product_gate"
    assert ladder["product_gate_transition_allowed"] is True
    assert ladder["product_gate_ready"] is True
    assert ladder["product_gate_reached"] is False
    assert ladder["product_gate_public_release_applied"] is False
    assert ladder["release_judgment"]["release_allowed"] is False
    assert ladder["metrics"]["required_coverage_complete"] is True
    assert ladder["metrics"]["blind_qa_ready"] is True
    assert ladder["display_gate_relaxed"] is False
    assert ladder["fixed_fallback_used"] is False
    _assert_meta_only(ladder)


def test_step7_blocks_product_gate_when_gate_is_relaxed_or_fixed_fallback_is_present() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[_event(group) for group in COMPLETE_COVERAGE_GROUP_ORDER],
        blind_qa_reviews=[_green_blind_review(group) for group in COMPLETE_COVERAGE_GROUP_ORDER],
    )
    scorecard = {
        **scorecard,
        "display_gate_relaxed": True,
        "fixed_fallback_used": True,
        "raw_input_required_for_improvement": True,
    }
    ladder = build_complete_product_quality_release_ladder(
        product_quality_scorecard=scorecard,
        diagnostic_summary={"gate_binding_contract_version": "emlis.gate_binding_contract.v2"},
    )

    product_blockers = set(ladder["stage_evaluations"]["product_gate"]["blockers"])
    assert ladder["product_gate_ready"] is False
    assert "gate_relaxed" in product_blockers
    assert "raw_input_dependency" in product_blockers
    assert "fixed_fallback_or_external_generation_detected" in product_blockers
    assert ladder["stop_conditions"]["gate_relaxed"] is True
    assert ladder["stop_conditions"]["raw_input_dependency"] is True
    assert ladder["release_judgment"]["release_allowed"] is False
    _assert_meta_only(ladder)



def test_step7_release_ladder_does_not_count_coverage_group_missing_as_required_coverage() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            {**_event(group), "coverage_group": group}
            for group in COMPLETE_COVERAGE_GROUP_ORDER[:-1]
        ]
        + [{**_event(""), "coverage_group": ""}],
        blind_qa_reviews=[_green_blind_review(group) for group in COMPLETE_COVERAGE_GROUP_ORDER],
    )
    ladder = build_complete_product_quality_release_ladder(
        product_quality_scorecard=scorecard,
        diagnostic_summary={"gate_binding_contract_version": "emlis.gate_binding_contract.v2"},
    )

    assert scorecard["coverage_group_missing_count"] == 1
    assert "relationship" in scorecard["missing_coverage_groups"]
    assert ladder["metrics"]["coverage_group_count"] == len(COMPLETE_COVERAGE_GROUP_ORDER) - 1
    assert ladder["metrics"]["coverage_group_missing_count"] == 1
    assert ladder["metrics"]["required_coverage_complete"] is False
    assert "coverage_group_missing" in ladder["stage_evaluations"]["broader_beta"]["blockers"]
    assert "product_gate_coverage_groups_incomplete" in ladder["stage_evaluations"]["product_gate"]["blockers"]
    assert ladder["product_gate_ready"] is False
