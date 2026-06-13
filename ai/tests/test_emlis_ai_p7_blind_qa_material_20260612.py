# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_blind_qa_material import (
    P7_BLIND_QA_DIMENSIONS,
    P7_BLIND_QA_MATERIAL_SCHEMA_VERSION,
    P7_BLIND_QA_REVIEW_SCHEMA_VERSION,
    apply_p7_blind_qa_review_to_scorecard_row,
    assert_p7_blind_qa_candidate_contract,
    assert_p7_blind_qa_material_contract,
    assert_p7_blind_qa_review_contract,
    build_p7_blind_qa_candidate,
    build_p7_blind_qa_material,
    normalize_p7_blind_qa_review,
)
from emlis_ai_p7_event_bridge import P7_RATING_REQUIRED_DIMENSIONS, build_p7_scorecard_row
from test_emlis_ai_p7_event_bridge_20260612 import _event, _handoff

SECRET_COMMENT = "P7-6 secret comment_text body must never be serialized"
SECRET_REVIEWER_NOTE = "P7-6 reviewer free text must never be accepted"


def _row(*, family: str = "structure_question") -> dict[str, object]:
    return build_p7_scorecard_row(product_quality_event=_event(family=family), p7_handoff_summary=_handoff())


def _complete_review(candidate_id: str, *, score: float = 0.92) -> dict[str, object]:
    return {
        "review_id": f"review:{candidate_id}",
        "candidate_id": candidate_id,
        "reviewer_id_hash": "reviewer_hash_p7_6",
        "dimensions": {
            dimension: {"score": score, "reason_codes": [f"{dimension}_rated"]}
            for dimension in P7_RATING_REQUIRED_DIMENSIONS
        },
        "reason_codes": ["ratings_only_review_completed"],
    }


def test_p7_6_exports_scorecard_rows_as_body_free_ratings_only_candidates() -> None:
    material = build_p7_blind_qa_material([_row()])
    assert_p7_blind_qa_material_contract(material)

    assert material["schema_version"] == P7_BLIND_QA_MATERIAL_SCHEMA_VERSION
    assert material["candidate_count"] == 1
    assert material["review_missing_count"] == 1
    assert material["review_completed_count"] == 0
    assert material["rating_unreviewed_dimensions_status"] == "review_missing"
    assert material["machine_metrics_used_for_read_feeling"] is False
    assert material["read_feeling_auto_filled_from_machine_metrics"] is False
    assert material["reviewer_free_text_included"] is False
    assert material["release_allowed"] is False

    candidate = material["candidates"][0]
    assert_p7_blind_qa_candidate_contract(candidate)
    assert candidate["candidate_kind"] == "ratings_only_blind_qa_candidate"
    assert candidate["reviewer_payload_body_externalized"] is True
    assert candidate["reviewer_free_text_included"] is False
    assert candidate["review_status"] == "review_missing"
    assert candidate["rating_required"] is True
    assert set(candidate["missing_dimensions"]) == set(P7_BLIND_QA_DIMENSIONS)
    assert "read_feeling" in candidate["dimensions_required"]
    assert "history_connection_naturalness" in candidate["dimensions_required"]
    assert "creepy_absence" in candidate["dimensions_required"]

    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_6_review_missing_stays_hold_and_does_not_machine_fill_read_feeling() -> None:
    candidate = build_p7_blind_qa_candidate(_row())

    assert candidate["review_status"] == "review_missing"
    assert candidate["rating_required"] is True
    assert "P7-HOLD-001" in candidate["hold_refs"]
    assert "read_feeling" in candidate["missing_dimensions"]
    assert "dimension_scores" not in candidate
    assert candidate["machine_metrics_used_for_read_feeling"] is False
    assert candidate["read_feeling_auto_estimation_allowed"] is False


def test_p7_6_normalizes_ratings_only_review_and_applies_scores_without_release() -> None:
    candidate = build_p7_blind_qa_candidate(_row())
    review = normalize_p7_blind_qa_review(_complete_review(candidate["candidate_id"]))
    assert_p7_blind_qa_review_contract(review)

    assert review["schema_version"] == P7_BLIND_QA_REVIEW_SCHEMA_VERSION
    assert review["missing_dimensions"] == []
    assert review["verdict"] == "PRODUCT_PASS"
    assert review["reviewer_free_text_included"] is False
    assert review["ratings_only_payload"] is True
    assert review["release_allowed"] is False
    assert review["dimension_scores"]["read_feeling"] == 0.92

    updated_row = apply_p7_blind_qa_review_to_scorecard_row(_row(), review)
    assert updated_row["ratings"]["blind_qa_completed"] is True
    assert updated_row["ratings"]["rating_required"] is False
    assert updated_row["ratings"]["missing_dimensions"] == []
    assert updated_row["ratings"]["review_verdict"] == "PRODUCT_PASS"
    assert updated_row["ratings"]["dimension_scores"]["read_feeling"] == 0.92
    assert updated_row["release_allowed"] is False

    material = build_p7_blind_qa_material([_row()], reviews=[_complete_review(candidate["candidate_id"])])
    assert material["review_completed_count"] == 1
    assert material["review_missing_count"] == 0
    assert material["rating_unreviewed_dimensions_status"] == "review_completed"
    assert material["release_allowed"] is False

    material_from_rated_row = build_p7_blind_qa_material([updated_row])
    assert material_from_rated_row["review_completed_count"] == 1
    assert material_from_rated_row["review_missing_count"] == 0
    assert material_from_rated_row["summary"]["blind_qa_completed"] is True
    assert material_from_rated_row["candidates"][0]["dimension_scores"]["read_feeling"] == 0.92


def test_p7_6_partial_review_remains_review_partial_and_yellow() -> None:
    candidate = build_p7_blind_qa_candidate(_row())
    review = normalize_p7_blind_qa_review(
        {
            "review_id": "partial_review",
            "candidate_id": candidate["candidate_id"],
            "reviewer_id_hash": "reviewer_hash_partial",
            "dimensions": {
                "read_feeling": {"score": 0.8, "reason_codes": ["readable"]},
                "naturalness": {"score": 0.75, "reason_codes": ["natural"]},
            },
        }
    )

    assert review["verdict"] == "YELLOW"
    assert "history_connection_naturalness" in review["missing_dimensions"]
    updated_row = apply_p7_blind_qa_review_to_scorecard_row(_row(), review)
    assert updated_row["ratings"]["blind_qa_completed"] is False
    assert updated_row["ratings"]["rating_required"] is True
    assert updated_row["ratings"]["review_verdict"] == "YELLOW"

    material = build_p7_blind_qa_material([_row()], reviews=[review])
    assert material["review_completed_count"] == 0
    assert material["review_missing_count"] == 1
    assert material["candidates"][0]["review_status"] == "review_partial"


def test_p7_6_contract_rejects_body_payload_reviewer_free_text_and_release_promotion() -> None:
    candidate = build_p7_blind_qa_candidate(_row())

    with pytest.raises(ValueError):
        normalize_p7_blind_qa_review(
            {
                "candidate_id": candidate["candidate_id"],
                "reviewer_id_hash": "reviewer_hash_bad",
                "reviewer_free_text": SECRET_REVIEWER_NOTE,
                "dimensions": {},
            }
        )

    unsafe_candidate = dict(candidate)
    unsafe_candidate["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_blind_qa_candidate_contract(unsafe_candidate)

    unsafe_candidate = dict(candidate)
    unsafe_candidate["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_p7_blind_qa_candidate_contract(unsafe_candidate)

    material = build_p7_blind_qa_material([_row()])
    unsafe_material = dict(material)
    unsafe_material["public_contract"] = dict(material["public_contract"])
    unsafe_material["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_blind_qa_material_contract(unsafe_material)
