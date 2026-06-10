# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
    DECISION_P5_READY_AFTER_P4,
)
from emlis_ai_product_readfeel_p4_ratings_review import (
    P4_9_STATUS_IMPROVED,
    P4_9_STATUS_NOT_EVALUATED,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_ROW_VERSION_20260610,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610,
    assert_product_readfeel_p4_ratings_review_meta_only_20260610,
    build_product_readfeel_p4_ratings_review_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_ratings_review_20260610 import (
    SCENARIO_MISSING_READ_FEELING,
    SCENARIO_P5_READY,
    SCENARIO_REMAINING_BLOCKERS,
    build_product_readfeel_p4_ratings_review_fixture_reviews_20260610,
    build_product_readfeel_p4_ratings_review_from_target_selection_20260610,
    dump_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
)

_FORBIDDEN_RAW_KEYS = {
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
    "surface_text",
    "surfaceText",
    "reply_text",
    "replyText",
    "reviewer_note",
    "reviewer_notes",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def test_p4_9_builds_body_free_ratings_only_review_and_rejudges_p3_9_with_p5_hold() -> None:
    review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        run_id="p4_9_ratings_only_review_hold_test"
    )
    summary = review["summary"]
    p3_9_summary = review["post_p4_p3_9_redecision"]["summary"]

    assert review["schema_version"] == PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610
    assert review["source_step"] == PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610
    assert summary["schema_version"] == PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610
    assert summary["target_case_count"] == 23
    assert summary["review_count"] == 23
    assert summary["target_subset_review_complete"] is True
    assert summary["improved_count"] == 23
    assert summary["worsened_count"] == 0
    assert summary["not_evaluated_count"] == 0
    assert summary["p4_target_subset_floor_met"] is True
    assert summary["rich_input_low_information_overroute_count"] == 0
    assert summary["generic_reception_surface_count"] == 0
    assert summary["identity_claim_as_fact_count"] == 0
    assert summary["boundary_regression_count"] == 0
    assert summary["read_feeling_auto_filled_from_machine_metrics"] is False
    assert summary["machine_metrics_used_for_read_feeling"] is False
    assert summary["post_p4_p3_9_next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert summary["post_p4_p5_connection_allowed"] is False
    assert summary["p5_hold_continues"] is True
    assert "current_only_readfeel_below_minimum" in summary["post_p4_p5_hold_reason_codes"]
    assert p3_9_summary["p5_visible_surface_strengthened"] is False
    assert p3_9_summary["p5_runtime_change_applied"] is False
    assert review["p4_runtime_tuning_applied"] is False
    assert review["p5_visible_surface_strengthened"] is False
    assert review["public_response_key_change"] is False
    assert review["api_route_changed"] is False
    assert review["db_physical_name_changed"] is False
    assert review["rn_visible_contract_changed"] is False
    assert review["gate_relaxed"] is False
    assert _contains_forbidden_raw_key(review) is False
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(review)

    for row in review["review_rows"]:
        assert row["schema_version"] == PRODUCT_READFEEL_P4_RATINGS_REVIEW_ROW_VERSION_20260610
        assert row["ratings_only_payload"] is True
        assert row["improvement_status"] == P4_9_STATUS_IMPROVED
        assert row["comment_text_body_included"] is False
        assert row["raw_input_included"] is False
        assert row["candidate_body_included"] is False
        assert row["read_feeling_auto_filled_from_machine_metrics"] is False


def test_p4_9_public_summary_dump_excludes_review_rows_and_all_bodies() -> None:
    dumped = dump_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610(
        run_id="p4_9_public_summary_dump_test"
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610
    assert parsed["review_count"] == 23
    assert parsed["post_p4_p5_connection_allowed"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["raw_input_included"] is False
    assert parsed["candidate_body_included"] is False
    assert parsed["read_feeling_auto_filled_from_machine_metrics"] is False
    assert '"review_rows"' not in dumped
    assert '"connection_evidence"' not in dumped
    assert '"post_p4_p3_9_redecision"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"memo"' not in dumped
    assert "会議で軽く流された" not in dumped
    assert "Emlisです" not in dumped
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(parsed)


def test_p4_9_keeps_read_feeling_unfilled_when_ratings_omit_it() -> None:
    review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        scenario=SCENARIO_MISSING_READ_FEELING,
        run_id="p4_9_missing_read_feeling_test",
    )
    summary = review["summary"]
    missing = next(row for row in review["review_rows"] if row["improvement_status"] == P4_9_STATUS_NOT_EVALUATED)

    assert summary["not_evaluated_count"] == 1
    assert summary["p4_target_subset_floor_met"] is False
    assert summary["post_p4_p5_connection_allowed"] is False
    assert missing["read_feeling_auto_filled_from_machine_metrics"] is False
    assert missing["machine_metrics_used_for_read_feeling"] is False
    assert "read_feeling_not_evaluated" in missing["unresolved_reason_codes"]
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(review)


def test_p4_9_detects_remaining_family_blockers_and_keeps_p5_hold_codes() -> None:
    review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        scenario=SCENARIO_REMAINING_BLOCKERS,
        run_id="p4_9_remaining_blockers_test",
    )
    summary = review["summary"]
    p3_9_summary = review["post_p4_p3_9_redecision"]["summary"]

    assert summary["rich_input_low_information_overroute_count"] == 1
    assert summary["generic_reception_surface_count"] == 1
    assert summary["question_only_surface_count"] == 1
    assert summary["comfort_only_surface_count"] == 1
    assert summary["identity_claim_as_fact_count"] == 1
    assert summary["p4_target_subset_floor_met"] is False
    assert summary["post_p4_p3_9_next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert summary["post_p4_p5_connection_allowed"] is False
    assert "rich_input_low_information_overroute" in summary["post_p4_p5_hold_reason_codes"]
    assert "generic_reception_surface" in summary["post_p4_p5_hold_reason_codes"]
    assert "p5_hold_reason_codes_present" in p3_9_summary["p5_hold_reasons"]
    assert p3_9_summary["p5_visible_surface_strengthened"] is False
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(review)


def test_p4_9_can_rejudge_p5_ready_only_when_explicit_full_current_only_evidence_is_clean() -> None:
    review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        scenario=SCENARIO_P5_READY,
        run_id="p4_9_p5_ready_redecision_test",
    )
    summary = review["summary"]
    p3_9_summary = review["post_p4_p3_9_redecision"]["summary"]

    assert summary["p4_target_subset_floor_met"] is True
    assert summary["post_p4_p3_9_next_phase_decision"] == DECISION_P5_READY_AFTER_P4
    assert summary["post_p4_p5_connection_allowed"] is True
    assert summary["p5_hold_continues"] is False
    assert summary["post_p4_p5_hold_reason_codes"] == []
    assert p3_9_summary["current_only_readfeel_minimum_met"] is True
    assert p3_9_summary["main_family_readfeel_minimum_met"] is True
    assert p3_9_summary["history_line_masks_current_input_gap"] is False
    assert p3_9_summary["p5_visible_surface_strengthened"] is False
    assert p3_9_summary["public_response_key_change"] is False
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(review)


def test_p4_9_guard_rejects_body_keys_forbidden_flags_and_machine_autofill() -> None:
    selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id="p4_9_guard_selection_test"
    )
    reviews = build_product_readfeel_p4_ratings_review_fixture_reviews_20260610(
        p4_target_case_selection=selection
    )

    unsafe_body = dict(reviews[0])
    unsafe_body["comment_text"] = "rendered body must not enter P4-9 ratings"
    with pytest.raises(ValueError):
        build_product_readfeel_p4_ratings_review_20260610(
            p4_target_case_selection=selection,
            p4_ratings_reviews=[unsafe_body],
            run_id="p4_9_guard_body_test",
        )

    review = build_product_readfeel_p4_ratings_review_20260610(
        p4_target_case_selection=selection,
        p4_ratings_reviews=reviews,
        run_id="p4_9_guard_clean_test",
    )
    unsafe_summary = dict(review["summary"])
    unsafe_summary["gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_ratings_review_meta_only_20260610(unsafe_summary)

    unsafe_machine = dict(review["summary"])
    unsafe_machine["read_feeling_auto_filled_from_machine_metrics"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_ratings_review_meta_only_20260610(unsafe_machine)
