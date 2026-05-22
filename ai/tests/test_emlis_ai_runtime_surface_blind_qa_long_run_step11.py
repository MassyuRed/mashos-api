from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
)
from emlis_ai_complete_product_quality_scorecard_service import (
    build_complete_product_quality_scorecard,
)
from emlis_ai_runtime_surface_blind_qa_long_run import (
    RUNTIME_SURFACE_BLIND_QA_CANDIDATE_VERSION,
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP,
    RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION,
    assert_runtime_surface_blind_qa_long_run_meta_only,
    build_runtime_surface_blind_qa_candidates,
    build_runtime_surface_blind_qa_long_run_summary,
    normalize_runtime_surface_blind_qa_review,
)
from emlis_ai_long_term_quality_service import (
    build_runtime_surface_long_run_signature_report,
)


def _event(row_id: str, coverage_group: str, signature: str, *, displayed: bool = True) -> dict[str, object]:
    return {
        "row_id": row_id,
        "run_id": "run-step11",
        "trace_id": f"trace-{row_id}",
        "emotion_log_id": f"emotion-{row_id}",
        "coverage_group": coverage_group,
        "measurement_classification": "passed_displayed" if displayed else "rejected",
        "classification": "passed_displayed" if displayed else "rejected",
        "observation_status": "passed" if displayed else "rejected",
        "backend_public_passed": displayed,
        "public_passed": displayed,
        "display_confirmed": displayed,
        "passed_display_count": 1 if displayed else 0,
        "eligible_count": 1,
        "candidate_generated_count": 1,
        "binding_count": 2,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "surface_signature_id": f"sig:{signature}",
        "surface_signature_family_key": signature,
        "surface_major_reasons": [],
        "grammar_warning_codes": [],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def _review(candidate_id: str, *, read: object = "green") -> dict[str, object]:
    return {
        "review_id": f"review-{candidate_id}",
        "candidate_id": candidate_id,
        "coverage_group": "short_daily",
        "ratings": {
            "read_feeling": read,
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
        "raw_input": "this text must be stripped",
        "comment_text": "this observation body must be stripped",
    }


def test_step11_builds_blind_qa_candidates_from_row_coverage_classification_only() -> None:
    candidates = build_runtime_surface_blind_qa_candidates([
        _event("row-1", "short_daily", "sig-a"),
        _event("row-2", "relationship", "sig-b"),
    ])

    assert len(candidates) == 2
    assert candidates[0]["version"] == RUNTIME_SURFACE_BLIND_QA_CANDIDATE_VERSION
    assert candidates[0]["source_step"] == RUNTIME_SURFACE_BLIND_QA_LONG_RUN_STEP
    assert candidates[0]["candidate_id"] == "row-1"
    assert candidates[0]["coverage_group"] == "short_daily"
    assert candidates[0]["classification"] == "passed_displayed"
    assert candidates[0]["reviewable_for_blind_qa"] is True
    assert candidates[0]["ratings_required"] == [
        "read_feeling",
        "evidence_retention",
        "distance",
        "naturalness",
        "non_template",
    ]
    assert candidates[0]["read_feeling_score"] is None
    assert candidates[0]["machine_metrics_used_for_read_feeling"] is False
    assert candidates[0]["comment_text_body_included"] is False
    assert "this text must be stripped" not in json.dumps(candidates, ensure_ascii=False)


def test_step11_normalizes_ratings_only_blind_qa_review_and_strips_text_payload() -> None:
    review = normalize_runtime_surface_blind_qa_review(_review("row-1"))
    dumped = json.dumps(review, ensure_ascii=False)

    assert review["candidate_id"] == "row-1"
    assert review["read_feeling_score"] == 1.0
    assert review["passed"] is True
    assert review["ratings_only_payload"] is True
    assert review["machine_metrics_used_for_read_feeling"] is False
    assert review["comment_text_body_included"] is False
    assert "this observation body must be stripped" not in dumped
    assert "this text must be stripped" not in dumped
    assert "comment_text" not in review
    assert "raw_input" not in review


def test_step11_summary_requires_blind_qa_and_long_run_signature_diversity() -> None:
    events = [
        _event("row-1", "short_daily", "sig-a"),
        _event("row-2", "short_daily", "sig-b"),
    ]
    summary = build_runtime_surface_blind_qa_long_run_summary(
        events=events,
        blind_qa_reviews=[_review("row-1"), _review("row-2")],
        run_id="run-step11",
    )

    assert summary["version"] == RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION
    assert summary["step11_blind_qa_long_run_ready"] is True
    assert summary["runtime_surface_blind_qa_long_run_ready"] is True
    assert summary["blind_qa_ready"] is True
    assert summary["read_feeling_score"] == 1.0
    assert summary["machine_metrics_used_for_read_feeling"] is False
    assert summary["long_run_surface_signature_diversity_ready"] is True
    assert summary["long_run_surface_signature_diversity_rate"] == 1.0
    assert summary["long_run_surface_signature_repeat_detected"] is False
    assert summary["step11_release_blockers"] == []
    assert summary["product_gate_candidate_material_ready"] is True
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False


def test_step11_read_feeling_below_product_target_remains_blocker() -> None:
    summary = build_runtime_surface_blind_qa_long_run_summary(
        events=[
            _event("row-1", "relationship", "sig-a"),
            _event("row-2", "relationship", "sig-b"),
        ],
        blind_qa_reviews=[_review("row-1", read="yellow"), _review("row-2", read="yellow")],
    )

    assert summary["read_feeling_score"] == 0.65
    assert summary["step11_blind_qa_long_run_ready"] is False
    assert "read_feeling_score_below_product_gate_target" in summary["step11_release_blockers"]
    assert summary["machine_metrics_used_for_read_feeling"] is False


def test_step11_long_run_detects_same_coverage_signature_repeat_without_comment_text() -> None:
    long_run = build_runtime_surface_long_run_signature_report(
        events=[
            _event("row-1", "conflict", "same-sig"),
            _event("row-2", "conflict", "same-sig"),
        ]
    )

    assert long_run["long_run_ready"] is False
    assert long_run["surface_signature_repeat_count"] == 1
    assert "long_run_surface_signature_repeat" in long_run["product_gate_candidate_blockers"]
    assert long_run["comment_text_body_included"] is False
    assert_runtime_surface_blind_qa_long_run_meta_only({
        "comment_text_body_included": False,
        "raw_input_included": False,
        "public_release_applied": False,
    })


def test_step11_connects_to_scorecard_and_measurement_report_without_changing_public_release() -> None:
    events = [
        _event("row-1", "short_daily", "sig-a"),
        _event("row-2", "short_daily", "sig-b"),
    ]
    reviews = [_review("row-1"), _review("row-2")]

    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=events,
        blind_qa_reviews=reviews,
    )
    assert scorecard["runtime_surface_blind_qa_long_run_version"] == RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION
    assert scorecard["step11_blind_qa_long_run_ready"] is True
    assert scorecard["long_run_surface_signature_diversity_rate"] == 1.0
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert scorecard["product_gate_ready"] is False

    measurement_reviews = [
        {k: v for k, v in review.items() if k not in {"raw_input", "comment_text"}}
        for review in reviews
    ]
    measurement = build_complete_product_quality_measurement_connection(
        rows=events,
        blind_qa_reviews=measurement_reviews,
        run_id="run-step11",
    )
    assert measurement["runtime_surface_blind_qa_long_run_version"] == RUNTIME_SURFACE_BLIND_QA_LONG_RUN_VERSION
    assert measurement["step11_blind_qa_long_run_ready"] is True
    assert measurement["long_run_surface_signature_diversity_rate"] == 1.0
    assert measurement["machine_metrics_used_for_read_feeling"] is False
    assert measurement["product_gate_ready"] is False
    assert measurement["public_release_applied"] is False


def test_step11_meta_only_assert_rejects_text_keys_and_contract_relaxation() -> None:
    with pytest.raises(ValueError):
        assert_runtime_surface_blind_qa_long_run_meta_only({"comment_text": "must not be kept"})
    with pytest.raises(ValueError):
        assert_runtime_surface_blind_qa_long_run_meta_only({"display_gate_relaxed": True})
