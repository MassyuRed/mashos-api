from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_product_readfeel_rubric import (
    PRODUCT_READFEEL_RATING_DIMENSIONS,
    PRODUCT_READFEEL_RUBRIC_STEP,
    PRODUCT_READFEEL_RUBRIC_VERSION,
    PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS,
    PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS,
    assert_product_readfeel_rubric_meta_only,
    build_product_readfeel_blind_qa_aggregate,
    build_product_readfeel_rubric,
    normalize_product_readfeel_blind_qa_review,
    normalize_product_readfeel_rubric_to_scorecard_fields,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in (
            "raw_input",
            "raw_text",
            "input_text",
            "user_input",
            "memo",
            "memo_action",
            "emotion_details",
            "comment_text",
            "reply_text",
            "surface_text",
            "display_text",
            "candidate_body",
            "accepted_surface_probe",
            "body",
            "text",
        ):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        assert payload.get("candidate_body_included") is not True
        assert payload.get("machine_metrics_used_for_read_feeling") is not True
        assert payload.get("read_feeling_auto_filled_from_machine_metrics") is not True
        assert payload.get("public_response_key_change") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _green_product_readfeel_review(family: str = "long_meaning_arc") -> dict[str, Any]:
    return {
        "review_id": f"review-{family}",
        "candidate_id": f"candidate-{family}",
        "fixture_family": family,
        "ratings": {
            "read_feeling": "green",
            "self_report_retention": "green",
            "state_structure_retention": "green",
            "emotion_temperature_retention": "green",
            "follow_depth": "green",
            "evidence_boundary": "green",
            "soft_inference_surface": "green",
            "naturalness": "green",
            "non_template": "green",
            "insight_delta": "yellow",
        },
    }


def _displayed_event(row_id: str, family: str) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "fixture_family": family,
        "coverage_group": family,
        "observation_status": "passed",
        "display_confirmed": True,
        "comment_text_present": True,
        "eligible_count": 1,
        "passed_display_count": 1,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "surface_signature_family_key": f"sig-{row_id}",
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def test_phase2_rubric_defines_product_readfeel_v1_dimensions_as_meta_only() -> None:
    rubric = build_product_readfeel_rubric()

    assert rubric["version"] == PRODUCT_READFEEL_RUBRIC_VERSION
    assert rubric["step"] == PRODUCT_READFEEL_RUBRIC_STEP
    assert rubric["machine_metrics_are_separate"] is True
    assert rubric["read_feeling_requires_blind_qa"] is True
    assert rubric["read_feeling_auto_filled_from_machine_metrics"] is False
    assert rubric["v1_required_dimensions"] == list(PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS)
    assert rubric["v2_candidate_dimensions"] == list(PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS)
    assert set(PRODUCT_READFEEL_RATING_DIMENSIONS).issubset(set(rubric["dimensions"]))
    assert rubric["dimensions"]["read_feeling"]["machine_metric_fill_forbidden"] is True
    assert "self_report_retention" in rubric["dimensions"]
    assert "state_structure_retention" in rubric["dimensions"]
    assert "emotion_temperature_retention" in rubric["dimensions"]
    assert "follow_depth" in rubric["dimensions"]
    assert "insight_delta" in rubric["dimensions"]
    _assert_meta_only(rubric)


def test_phase2_normalizes_blind_qa_review_without_retaining_raw_or_comment_text() -> None:
    review = normalize_product_readfeel_blind_qa_review(
        {
            **_green_product_readfeel_review("structure_question"),
            "raw_input": "ユーザー本文はrubric metaへ保持しない",
            "comment_text": "表示本文もrubric metaへ保持しない",
        }
    )

    assert review["version"] == "cocolon.emlis.product_readfeel.blind_qa_review.v1"
    assert review["product_readfeel_family"] == "structure_question"
    assert review["read_feeling_score"] == 1.0
    assert review["self_report_retention_score"] == 1.0
    assert review["state_structure_retention_score"] == 1.0
    assert review["emotion_temperature_retention_score"] == 1.0
    assert review["follow_depth_score"] == 1.0
    assert review["insight_delta_score"] == 0.65
    assert review["v1_verdict"] == "PASS"
    assert review["v2_verdict"] == "YELLOW"
    assert review["v2_insight_delta_release_blocker"] is False
    assert review["source_text_payload_seen"] is True
    assert review["source_text_payload_retained"] is False
    _assert_meta_only(review)


def test_phase2_aggregate_and_scorecard_fields_keep_machine_metrics_and_blind_qa_separated() -> None:
    aggregate = build_product_readfeel_blind_qa_aggregate(
        reviews=[_green_product_readfeel_review("long_meaning_arc")]
    )
    fields = normalize_product_readfeel_rubric_to_scorecard_fields(aggregate)

    assert aggregate["phase2_product_readfeel_rubric_ready"] is True
    assert aggregate["blind_qa_ready"] is True
    assert aggregate["read_feeling_score"] == 1.0
    assert aggregate["insight_delta_score"] == 0.65
    assert aggregate["read_feeling_source"] == "blind_qa_review_ratings"
    assert fields["phase2_product_readfeel_rubric_ready"] is True
    assert fields["product_readfeel_phase2_ready"] is True
    assert fields["product_readfeel_rubric_implementation_decision"] == "separate_meta_only_rubric_connected_to_scorecard"
    assert fields["product_readfeel_machine_metrics_separated_from_blind_qa"] is True
    assert fields["product_readfeel_read_feeling_requires_blind_qa"] is True
    assert fields["product_readfeel_machine_metrics_used_for_read_feeling"] is False
    assert fields["product_readfeel_read_feeling_auto_filled_from_machine_metrics"] is False
    assert fields["product_readfeel_read_feeling_score"] == 1.0
    assert fields["product_readfeel_v1_product_pass_candidate_rate"] == 1.0
    assert fields["product_readfeel_v2_structure_insight_ready_candidate_rate"] == 0.0
    _assert_meta_only(aggregate)
    _assert_meta_only(fields)


def test_phase2_complete_scorecard_exposes_rubric_candidate_without_release_or_contract_change() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[_displayed_event("phase2-structure", "structure_question")],
        blind_qa_reviews=[_green_product_readfeel_review("structure_question")],
    )

    assert scorecard["phase2_product_readfeel_rubric_ready"] is True
    assert scorecard["product_readfeel_phase2_ready"] is True
    assert scorecard["product_readfeel_rubric_version"] == PRODUCT_READFEEL_RUBRIC_VERSION
    assert scorecard["product_readfeel_rubric_implementation_decision"] == "separate_meta_only_rubric_connected_to_scorecard"
    assert "self_report_retention" in scorecard["product_readfeel_required_dimensions"]
    assert "state_structure_retention" in scorecard["product_readfeel_required_dimensions"]
    assert "emotion_temperature_retention" in scorecard["product_readfeel_required_dimensions"]
    assert "follow_depth" in scorecard["product_readfeel_required_dimensions"]
    assert "insight_delta" in scorecard["product_readfeel_optional_v2_dimensions"]
    assert scorecard["product_readfeel_read_feeling_score"] == 1.0
    assert scorecard["product_readfeel_read_feeling_source"] == "blind_qa_review_ratings"
    assert scorecard["product_readfeel_machine_metrics_separated_from_blind_qa"] is True
    assert scorecard["product_gate_ready"] is False
    assert scorecard["public_release_applied"] is False
    assert scorecard["public_response_key_change"] is False
    _assert_meta_only(scorecard["phase2_product_readfeel_rubric"])
    _assert_meta_only(scorecard["phase2_product_readfeel_blind_qa_metrics"])
    _assert_meta_only(scorecard["phase2_product_readfeel_rubric_fields"])


def test_phase2_machine_event_read_feeling_does_not_fill_product_readfeel_without_blind_qa() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            {
                **_displayed_event("phase2-machine-only", "daily_positive"),
                "read_feeling_score": 1.0,
            }
        ],
        blind_qa_reviews=[],
    )

    assert scorecard["phase2_product_readfeel_rubric_ready"] is True
    assert scorecard["product_readfeel_blind_qa_ready"] is False
    assert scorecard["product_readfeel_read_feeling_score"] is None
    assert scorecard["product_readfeel_read_feeling_source"] == "blind_qa_required_not_evaluated"
    assert scorecard["product_readfeel_machine_metrics_used_for_read_feeling"] is False
    assert scorecard["product_readfeel_read_feeling_auto_filled_from_machine_metrics"] is False
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert scorecard["read_feeling_auto_filled_from_machine_metrics"] is False


def test_phase2_meta_only_assert_rejects_text_keys_and_machine_fill() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_rubric_meta_only({"comment_text": "出してはいけない"})
    with pytest.raises(ValueError):
        assert_product_readfeel_rubric_meta_only({"read_feeling_auto_filled_from_machine_metrics": True})
