# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_product_quality_review import (
    DIMENSION_TARGETS,
    REQUIRED_DIMENSIONS,
    USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP,
    assert_user_label_connection_p5_product_quality_review_contract,
    build_user_label_connection_p5_product_quality_review,
    user_label_connection_p5_product_quality_review_public_summary,
)
from test_emlis_ai_user_label_connection_p5_safety_guard_20260611 import _guard

FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "history_context",
    "historyContext",
    "history_records",
    "historyRecords",
    "history_raw_text",
    "historyRawText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "reply_text",
    "replyText",
    "display_text",
    "displayText",
    "reviewer_note",
    "reviewer_notes",
    "review_notes",
    "free_text_note",
    "reviewer_free_text",
    "blind_qa_free_text",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _ratings_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "case_ref": "p5-quality-case-001",
        "ratings": {
            "history_connection_naturalness": 0.94,
            "creepy_absence": 0.98,
            "overclaim_absence": 0.97,
            "self_blame_non_amplification": 0.97,
            "current_input_not_masked_by_history": 0.98,
            "non_template": 0.96,
            "self_information_organized": 0.93,
            "wants_more_input_or_accumulation": 0.9,
            "subscription_boundary_correctness": 1.0,
            "no_raw_text_meta": 1.0,
        },
        "ratings_only": True,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "reviewer_free_text_included": False,
    }
    row.update(overrides)
    return row


def _review(**overrides: Any) -> dict[str, Any]:
    args = {
        "p5_safety_guard": _guard(run_id="p5_5_safety_guard_source"),
        "review_rows": [_ratings_row(), _ratings_row(case_ref="p5-quality-case-002")],
        "run_id": "p5_5_product_quality_review",
    }
    args.update(overrides)
    return build_user_label_connection_p5_product_quality_review(**args)


def test_p5_5_builds_ratings_only_review_and_allows_limited_visible_candidate_without_release() -> None:
    review = _review(run_id="p5_5_green_ratings_only_test")

    assert review["schema_version"] == USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION
    assert review["step"] == USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP
    assert review["ratings_only"] is True
    assert review["review_count"] == 2
    assert review["blocker_reason_codes"] == []
    assert review["p5_limited_visible_allowed"] is True
    assert review["p5_safety_guard_allowed"] is True
    assert set(review["dimension_averages"]) == set(REQUIRED_DIMENSIONS)
    assert review["dimension_averages"]["history_connection_naturalness"] == 0.94
    assert review["dimension_averages"]["wants_more_input_or_accumulation"] == 0.9
    assert review["dimension_targets"] == DIMENSION_TARGETS
    assert review["machine_metrics_used_for_read_feeling"] is False
    assert review["read_feeling_auto_filled_from_machine_metrics"] is False
    assert review["public_release_applied"] is False
    assert review["product_quality_released"] is False
    assert review["release_allowed"] is False
    assert review["public_contract"]["release_allowed"] is False
    assert review["public_contract"]["public_release_applied"] is False
    assert review["public_contract"]["product_quality_released"] is False
    assert review["body_free"]["raw_text_included"] is False
    assert review["body_free"]["comment_text_body_included"] is False
    assert review["body_free"]["reviewer_free_text_included"] is False
    assert _contains_forbidden_raw_key(review) is False
    assert_user_label_connection_p5_product_quality_review_contract(review)


def test_p5_5_blocks_low_dimension_scores_including_wants_more_input_or_accumulation() -> None:
    low = _ratings_row(
        ratings={
            "history_connection_naturalness": 0.89,
            "creepy_absence": 0.94,
            "overclaim_absence": 0.94,
            "self_blame_non_amplification": 0.94,
            "current_input_not_masked_by_history": 0.94,
            "non_template": 0.89,
            "self_information_organized": 0.89,
            "wants_more_input_or_accumulation": 0.84,
            "subscription_boundary_correctness": 1.0,
            "no_raw_text_meta": 1.0,
        }
    )
    review = _review(review_rows=[low], run_id="p5_5_low_dimension_block_test")

    assert review["p5_limited_visible_allowed"] is False
    assert "dimension_below_target:history_connection_naturalness" in review["blocker_reason_codes"]
    assert "dimension_below_target:creepy_absence" in review["blocker_reason_codes"]
    assert "dimension_below_target:overclaim_absence" in review["blocker_reason_codes"]
    assert "dimension_below_target:self_blame_non_amplification" in review["blocker_reason_codes"]
    assert "dimension_below_target:current_input_not_masked_by_history" in review["blocker_reason_codes"]
    assert "dimension_below_target:wants_more_input_or_accumulation" in review["blocker_reason_codes"]
    assert_user_label_connection_p5_product_quality_review_contract(review)


def test_p5_5_blocks_missing_dimensions_and_missing_review_rows() -> None:
    partial = _ratings_row(ratings={"history_connection_naturalness": 1.0})
    review = _review(review_rows=[partial], run_id="p5_5_missing_dimensions_test")

    assert review["p5_limited_visible_allowed"] is False
    assert "dimension_rating_missing:creepy_absence" in review["blocker_reason_codes"]
    assert "dimension_rating_missing:wants_more_input_or_accumulation" in review["blocker_reason_codes"]

    missing = _review(review_rows=[], run_id="p5_5_no_review_rows_test")
    assert missing["review_count"] == 0
    assert missing["p5_limited_visible_allowed"] is False
    assert "ratings_only_review_rows_missing" in missing["blocker_reason_codes"]
    assert_user_label_connection_p5_product_quality_review_contract(missing)


def test_p5_5_blocks_when_p5_safety_guard_is_not_allowed() -> None:
    blocked_guard = _guard(
        guard_signal_meta={"creepy_risk": True},
        run_id="p5_5_blocked_safety_guard_source",
    )
    review = _review(
        p5_safety_guard=blocked_guard,
        run_id="p5_5_safety_guard_not_allowed_test",
    )

    assert blocked_guard["blocked"] is True
    assert review["p5_safety_guard_allowed"] is False
    assert review["p5_limited_visible_allowed"] is False
    assert "p5_safety_guard_not_allowed" in review["blocker_reason_codes"]
    assert "p5_safety_guard:creepy_risk_detected" in review["blocker_reason_codes"]
    assert_user_label_connection_p5_product_quality_review_contract(review)


def test_p5_5_rejects_raw_text_reviewer_free_text_contract_mutation_and_machine_metric_autofill() -> None:
    raw = _review(
        review_rows=[_ratings_row(reviewer_free_text="must not be retained")],
        run_id="p5_5_reviewer_free_text_block_test",
    )
    assert raw["p5_limited_visible_allowed"] is False
    assert "raw_text_payload_detected" in raw["blocker_reason_codes"]
    assert "reviewer_free_text_detected" in raw["blocker_reason_codes"]
    assert _contains_forbidden_raw_key(raw) is False
    assert_user_label_connection_p5_product_quality_review_contract(raw)

    mutation = _review(
        review_rows=[_ratings_row(public_response_key_added=True)],
        run_id="p5_5_contract_mutation_block_test",
    )
    assert mutation["p5_limited_visible_allowed"] is False
    assert "contract_mutation_detected" in mutation["blocker_reason_codes"]

    machine = _review(
        review_rows=[_ratings_row(machine_metrics_used_for_read_feeling=True)],
        run_id="p5_5_machine_metric_autofill_block_test",
    )
    assert machine["p5_limited_visible_allowed"] is False
    assert "machine_metric_autofill_detected" in machine["blocker_reason_codes"]
    assert "contract_mutation_detected" in machine["blocker_reason_codes"]


def test_p5_5_accepts_verdict_alias_scores_but_still_ratings_only() -> None:
    row = _ratings_row(
        ratings={
            "history_naturalness": "pass",
            "not_creepy": "pass",
            "no_overclaim": "pass",
            "self_blame_absence": "pass",
            "current_not_masked": "pass",
            "not_template": "pass",
            "self_info_organized": "pass",
            "accumulation_motivation": "pass",
            "subscription_boundary": "pass",
            "raw_text_meta_absence": "pass",
        }
    )
    review = _review(review_rows=[row], run_id="p5_5_alias_scores_test")

    assert review["p5_limited_visible_allowed"] is True
    assert review["dimension_averages"]["wants_more_input_or_accumulation"] == 1.0
    assert review["ratings_only"] is True
    assert_user_label_connection_p5_product_quality_review_contract(review)


def test_p5_5_public_summary_is_body_free_and_does_not_expose_release_ready() -> None:
    review = _review(run_id="p5_5_public_summary_source")
    public_summary = user_label_connection_p5_product_quality_review_public_summary(review)
    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)

    assert public_summary["ratings_only"] is True
    assert public_summary["review_count"] == 2
    assert public_summary["p5_limited_visible_allowed"] is True
    assert public_summary["release_allowed"] is False
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["raw_text_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["history_raw_text_included"] is False
    assert public_summary["reviewer_free_text_included"] is False
    assert '"comment_text"' not in dumped
    assert '"reviewer_free_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"history_records"' not in dumped
    assert_user_label_connection_p5_product_quality_review_contract(public_summary, allow_partial=True)


def test_p5_5_contract_guard_rejects_body_keys_forbidden_true_flags_and_non_ratings_only() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_product_quality_review_contract(
            {"schema_version": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION, "text": "body"}
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_product_quality_review_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP,
                "public_response_key_added": True,
            },
            allow_partial=True,
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_product_quality_review_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_PRODUCT_QUALITY_REVIEW_STEP,
                "ratings_only": False,
                "dimension_averages": {dimension: 1.0 for dimension in REQUIRED_DIMENSIONS},
                "public_contract": {
                    "rn_visible_contract_changed": False,
                    "public_response_key_added": False,
                    "response_shape_changed": False,
                    "db_schema_changed": False,
                    "release_allowed": False,
                    "public_release_applied": False,
                    "product_quality_released": False,
                },
                "body_free": {
                    "raw_text_included": False,
                    "comment_text_body_included": False,
                    "candidate_body_included": False,
                    "surface_body_included": False,
                    "history_raw_text_included": False,
                    "reviewer_free_text_included": False,
                },
            }
        )
