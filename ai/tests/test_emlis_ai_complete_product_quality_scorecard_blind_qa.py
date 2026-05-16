from __future__ import annotations

from typing import Any

from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER
from emlis_ai_complete_product_quality_scorecard_service import (
    build_complete_product_quality_blind_qa_rubric,
    build_complete_product_quality_scorecard,
    build_complete_product_quality_scorecard_event_schema,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in {"raw_text", "raw_input", "input_text", "user_input", "comment_text", "reply_text"}:
                assert value in ("", None, [], {})
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _event(group: str, *, status: str = "passed", reasons: list[str] | None = None, safety: int = 0, template: int = 0) -> dict[str, Any]:
    passed = status == "passed"
    return {
        "event_kind": "complete_product_quality_fixture_case",
        "coverage_group": group,
        "observation_status": status,
        "display_passed": passed,
        "complete_candidate_generated": True,
        "eligible_count": 1,
        "binding_pass": passed,
        "binding_count": 2 if passed else 0,
        "expected_binding_count": 2,
        "binding_supported_sentence_count": 2 if passed else 0,
        "repair_attempted": False,
        "repair_success": False,
        "template_major_count": template,
        "safety_major_count": safety,
        "top_rejection_reasons": list(reasons or []),
        "relation_types": ["coexistence"],
    }


def _green_blind_review() -> dict[str, Any]:
    return {
        "run_id": "blind-run-step6",
        "fixture_set_id": "product-quality-fixtures",
        "coverage_group": "short_daily",
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def test_step6_event_schema_and_blind_qa_rubric_are_meta_only() -> None:
    schema = build_complete_product_quality_scorecard_event_schema()
    expected_fields = {
        "run_id",
        "fixture_set_id",
        "coverage_group",
        "eligible_count",
        "passed_display_count",
        "rejected_count",
        "unavailable_count",
        "binding_pass_rate",
        "repair_success_rate",
        "read_feeling_score",
        "safety_major_count",
        "template_major_count",
        "top_rejection_reasons",
    }
    assert expected_fields.issubset(set(schema["required_fields"]))
    assert schema["machine_metrics_and_blind_qa_separated"] is True

    rubric = build_complete_product_quality_blind_qa_rubric()
    assert rubric["machine_metrics_are_separate"] is True
    assert rubric["exact_comment_text_locked"] is False
    assert set(rubric["dimensions"]) == {
        "read_feeling",
        "evidence_retention",
        "distance",
        "naturalness",
        "non_template",
    }
    _assert_meta_only(schema)
    _assert_meta_only(rubric)


def test_step6_product_quality_scorecard_combines_machine_metrics_and_blind_qa_without_release_claim() -> None:
    events = [_event(group) for group in COMPLETE_COVERAGE_GROUP_ORDER]
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=[_green_blind_review()],
    )

    assert scorecard["product_quality_scorecard_ready"] is True
    assert scorecard["machine_metrics_separated_from_blind_qa"] is True
    assert scorecard["machine_metrics"]["display_reach_rate"] == 1.0
    assert scorecard["machine_metrics"]["binding_pass_rate"] == 1.0
    assert scorecard["machine_metrics"]["reason_coverage_rate"] == 1.0
    assert scorecard["blind_qa_metrics"]["read_feeling_score"] == 1.0
    assert scorecard["safety_major_count"] == 0
    assert scorecard["template_major_count"] == 0
    assert scorecard["product_gate_thresholds_met"] is True
    assert scorecard["product_gate_ready"] is False
    assert scorecard["product_gate_reached"] is False
    assert scorecard["release_judgment"]["release_allowed"] is False
    assert scorecard["display_gate_relaxed"] is False
    assert scorecard["fixed_fallback_used"] is False
    _assert_meta_only(scorecard)


def test_step6_product_quality_scorecard_keeps_fail_closed_reasons_and_blockers() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            _event("short_daily", status="rejected"),
            _event("relationship", status="rejected", reasons=["raw_echo"], safety=1, template=1),
        ]
    )

    blockers = set(scorecard["release_blockers"])
    assert scorecard["product_gate_ready"] is False
    assert "blind_qa_not_evaluated" in blockers
    assert "binding_pass_rate_below_target" in blockers
    assert "reason_coverage_incomplete" in blockers
    assert "safety_major_detected" in blockers
    assert "template_major_detected" in blockers
    assert scorecard["machine_metrics"]["reason_required_count"] == 2
    assert scorecard["machine_metrics"]["reason_covered_count"] == 1
    _assert_meta_only(scorecard)


def test_step6_product_quality_scorecard_accepts_draft_rubric_aliases_without_using_raw_payload() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_event=_event("pressure"),
        blind_qa_reviews=[{
            "ratings": {
                "input_specific_structure_reflected": "green",
                "relation_kept": "green",
                "evidence_bound": "green",
                "tone_distance_stable": "green",
                "natural_but_not_template": "green",
            },
            "raw_input": "should not leak",
            "comment_text": "should not leak",
        }],
    )

    assert scorecard["blind_qa_metrics"]["read_feeling_score"] == 1.0
    assert scorecard["read_feeling_source"] == "blind_qa"
    _assert_meta_only(scorecard)
