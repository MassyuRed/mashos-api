from __future__ import annotations

from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER
from emlis_ai_complete_product_quality_scorecard_service import (
    build_complete_product_quality_blind_qa_rubric,
    build_complete_product_quality_scorecard,
    normalize_complete_product_quality_blind_qa_review,
)


def _event(group: str, *, displayed: bool = True, reason: str = "") -> dict[str, object]:
    return {
        "version": "emlis.complete_scorecard_event.v1",
        "source_step": "Step6_Scorecard_Blind_QA",
        "event_kind": "complete_composer_initial_reply_attempt",
        "coverage_group": group,
        "coverage_scope": group,
        "eligible_count": 1,
        "passed_display_count": 1 if displayed else 0,
        "candidate_generated_count": 1,
        "observation_status": "passed" if displayed else "rejected",
        "binding_count": 2,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "used_evidence_span_count": 2,
        "used_phrase_unit_count": 2,
        "used_relation_count": 1,
        "relation_types": ["coexistence"],
        "read_feeling_score": 0.9 if displayed else None,
        "top_rejection_reasons": [reason] if reason else [],
        "gate_rejection_reasons": [reason] if reason else [],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def _green_review(group: str = "short_daily") -> dict[str, object]:
    return {
        "review_id": "qa_1",
        "coverage_group": group,
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def test_step6_product_quality_blind_qa_rubric_separates_read_feeling_from_machine_metrics() -> None:
    rubric = build_complete_product_quality_blind_qa_rubric()

    assert rubric["version"] == "emlis.complete_product_quality_blind_qa_rubric.v1"
    assert rubric["target_step"] == "Step6_Scorecard_Blind_QA"
    assert set(rubric["dimensions"]) == {
        "read_feeling",
        "evidence_retention",
        "distance",
        "naturalness",
        "non_template",
    }
    assert rubric["read_feeling_connection_target"] == 0.85
    assert rubric["read_feeling_product_gate_target"] == 0.9
    assert rubric["machine_metrics_are_separate"] is True
    assert rubric["exact_comment_text_locked"] is False
    assert rubric["raw_input_included"] is False
    assert rubric["comment_text_included"] is False


def test_step6_normalizes_blind_qa_review_without_raw_or_comment_text() -> None:
    review = normalize_complete_product_quality_blind_qa_review(
        {
            **_green_review("pressure"),
            "raw_input": "should not leak",
            "comment_text": "should not leak",
        }
    )

    assert review["version"] == "emlis.complete_product_quality_blind_qa_review.v1"
    assert review["coverage_group"] == "pressure"
    assert review["read_feeling_score"] == 1.0
    assert review["passed"] is True
    assert review["raw_input_included"] is False
    assert review["comment_text_included"] is False
    assert "raw_input" not in review
    assert "comment_text" not in review


def test_step6_product_quality_scorecard_combines_machine_metrics_and_blind_qa() -> None:
    events = [_event(group) for group in COMPLETE_COVERAGE_GROUP_ORDER]
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=[_green_review("short_daily"), _green_review("relationship")],
    )

    assert scorecard["version"] == "emlis.complete_product_quality_scorecard.v1"
    assert scorecard["step"] == "Step6_Scorecard_Blind_QA"
    assert scorecard["machine_metrics_separated_from_blind_qa"] is True
    assert scorecard["eligible_count"] == len(COMPLETE_COVERAGE_GROUP_ORDER)
    assert scorecard["passed_display_count"] == len(COMPLETE_COVERAGE_GROUP_ORDER)
    assert scorecard["display_reach_rate"] == 1.0
    assert scorecard["binding_pass_rate"] == 1.0
    assert scorecard["read_feeling_score"] == 1.0
    assert scorecard["blind_qa_metrics"]["review_count"] == 2
    assert scorecard["reason_coverage_rate"] == 1.0
    assert scorecard["safety_major_count"] == 0
    assert scorecard["template_major_count"] == 0
    assert scorecard["release_blockers"] == []
    assert scorecard["product_gate_reached"] is False
    assert scorecard["product_gate_decision"] == "not_released_step6_scorecard_only"
    assert scorecard["raw_input_included"] is False
    assert scorecard["comment_text_included"] is False
    assert scorecard["display_gate_relaxed"] is False


def test_step6_product_quality_scorecard_requires_rejection_reason_coverage() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            {
                **_event("conflict", displayed=False),
                "top_rejection_reasons": [],
                "gate_rejection_reasons": [],
            }
        ],
        blind_qa_reviews=[],
    )

    assert scorecard["reason_required_count"] == 1
    assert scorecard["reason_covered_count"] == 0
    assert scorecard["reason_coverage_rate"] == 0.0
    assert "reason_coverage_missing" in scorecard["release_blockers"]
    assert scorecard["product_gate_reached"] is False


def test_step6_machine_metrics_do_not_fill_read_feeling_score_without_blind_qa() -> None:
    event = {
        **_event("short_daily"),
        "read_feeling_score": 1.0,
    }
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[event],
        blind_qa_reviews=[],
    )

    assert scorecard["blind_qa_required"] is True
    assert scorecard["read_feeling_requires_blind_qa"] is True
    assert scorecard["blind_qa_ready"] is False
    assert scorecard["read_feeling_score"] is None
    assert scorecard["read_feeling_source"] == "blind_qa_required_not_evaluated"
    assert scorecard["machine_metrics"]["read_feeling_score"] is None
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert scorecard["read_feeling_auto_filled_from_machine_metrics"] is False
    assert "blind_qa_missing" in scorecard["release_blockers"]
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_response_key_change"] is False
