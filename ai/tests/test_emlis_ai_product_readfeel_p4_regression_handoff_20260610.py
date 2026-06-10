# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
    DECISION_P5_READY_AFTER_P4,
)
from emlis_ai_product_readfeel_p4_regression_handoff import (
    P4_10_REQUIRED_REGRESSION_SUITES_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610,
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610,
    build_product_readfeel_p4_regression_handoff_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_regression_handoff_20260610 import (
    SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED,
    SCENARIO_GREEN_REGRESSION_P5_HOLD,
    SCENARIO_GREEN_REGRESSION_P5_READY,
    SCENARIO_REMAINING_BLOCKERS,
    SCENARIO_TIMEOUT_LEDGER,
    build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610,
    build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610,
    dump_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_ratings_review_20260610 import (
    build_product_readfeel_p4_ratings_review_from_target_selection_20260610,
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
    "surface_text",
    "surfaceText",
    "reply_text",
    "replyText",
    "reviewer_note",
    "reviewer_notes",
    "raw_test_output",
    "test_output",
    "command_output",
    "terminal_output",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def test_p4_10_green_regression_rechecks_p5_hold_without_strengthening_p5_surface() -> None:
    handoff = build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_HOLD,
        run_id="p4_10_green_regression_p5_hold_test",
    )
    summary = handoff["summary"]

    assert handoff["schema_version"] == PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_VERSION_20260610
    assert handoff["source_step"] == PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_STEP_20260610
    assert summary["schema_version"] == PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610
    assert summary["p4_10_handoff_packet_created"] is True
    assert summary["p4_10_handoff_only"] is True
    assert summary["all_required_regression_green"] is True
    assert summary["missing_required_regression_suites"] == []
    assert summary["post_p4_p3_9_next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert summary["post_p4_p5_connection_allowed"] is False
    assert summary["p5_hold_rechecked"] is True
    assert summary["p5_hold_continues"] is True
    assert summary["p5_connection_handoff_allowed"] is False
    assert "current_only_readfeel_below_minimum" in summary["p5_hold_material"]
    assert "p4_target_subset_only_current_only_readfeel_not_full_minimum" in summary["p5_hold_material"]
    assert summary["recommended_next_action"] == "handoff_p4_results_with_p5_hold_until_full_current_only_recheck"
    assert summary["p5_visible_surface_strengthened"] is False
    assert summary["p5_runtime_change_applied"] is False
    assert summary["public_release_applied"] is False
    assert handoff["p4_runtime_tuning_applied"] is False
    assert handoff["gate_relaxed"] is False
    assert _contains_forbidden_raw_key(handoff) is False
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(handoff)


def test_p4_10_allows_p5_handoff_only_with_explicit_p4_9_ready_and_required_regression_green() -> None:
    handoff = build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_READY,
        run_id="p4_10_p5_ready_test",
    )
    summary = handoff["summary"]

    assert summary["post_p4_p3_9_next_phase_decision"] == DECISION_P5_READY_AFTER_P4
    assert summary["post_p4_p5_connection_allowed"] is True
    assert summary["all_required_regression_green"] is True
    assert summary["p5_hold_continues"] is False
    assert summary["p5_connection_handoff_allowed"] is True
    assert summary["p5_visible_surface_strengthened"] is False
    assert summary["product_gate_ready"] is False
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(handoff)


def test_p4_10_keeps_p5_hold_when_remaining_p4_9_blockers_exist() -> None:
    handoff = build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
        scenario=SCENARIO_REMAINING_BLOCKERS,
        run_id="p4_10_remaining_blockers_test",
    )
    summary = handoff["summary"]

    assert summary["all_required_regression_green"] is True
    assert summary["p5_connection_handoff_allowed"] is False
    assert summary["p5_hold_continues"] is True
    assert "rich_input_low_information_overroute" in summary["p5_hold_material"]
    assert "generic_reception_surface" in summary["p5_hold_material"]
    assert "p4_9_remaining_blockers_or_unreviewed_cases" in summary["p5_hold_material"]
    assert summary["recommended_next_action"] == "continue_p4_repair_for_remaining_ratings_or_boundary_blockers"
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(handoff)


def test_p4_10_blocks_p5_handoff_when_required_rn_contract_is_not_green() -> None:
    handoff = build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
        scenario=SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED,
        run_id="p4_10_backend_only_rn_missing_test",
    )
    summary = handoff["summary"]

    assert summary["all_required_regression_green"] is False
    assert summary["p5_connection_handoff_allowed"] is False
    assert summary["p5_hold_continues"] is True
    assert summary["handoff_requires_rn_contract_when_available"] is True
    assert "required_regression_not_green:rn_contract" in summary["required_regression_blockers"]
    assert "required_regression_not_green:rn_contract" in summary["p5_hold_material"]
    assert summary["recommended_next_action"] == "rerun_missing_or_timeout_regression_before_p5_handoff"
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(handoff)


def test_p4_10_records_timeout_ledger_without_treating_optional_combined_timeout_as_required_green_failure() -> None:
    handoff = build_product_readfeel_p4_regression_handoff_from_ratings_review_20260610(
        scenario=SCENARIO_TIMEOUT_LEDGER,
        run_id="p4_10_timeout_ledger_test",
    )
    summary = handoff["summary"]

    assert summary["all_required_regression_green"] is True
    assert summary["regression_suite_counts"]["timeout"] >= 3
    assert "command_timeout_recorded:p3_p4_combined_command" in summary["non_blocking_regression_notes"]
    assert "command_timeout_recorded:backend_contract_display_two_stage_combined" in summary["non_blocking_regression_notes"]
    assert "command_timeout_recorded:full_backend_suite" in summary["non_blocking_regression_notes"]
    assert summary["p5_connection_handoff_allowed"] is False
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(handoff)


def test_p4_10_public_summary_excludes_ratings_review_rows_command_packets_and_all_bodies() -> None:
    dumped = dump_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_HOLD,
        run_id="p4_10_public_summary_dump_test",
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == PRODUCT_READFEEL_P4_REGRESSION_HANDOFF_SUMMARY_VERSION_20260610
    assert parsed["p5_hold_continues"] is True
    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["candidate_body_included"] is False
    assert parsed["raw_test_output_included"] is False
    assert parsed["command_output_included"] is False
    assert '"review_rows"' not in dumped
    assert '"p4_ratings_review_summary"' not in dumped
    assert '"regression_suite_statuses"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"raw_test_output"' not in dumped
    assert '"command_output"' not in dumped
    assert "Emlisです" not in dumped
    assert_product_readfeel_p4_regression_handoff_meta_only_20260610(parsed)


def test_p4_10_guard_rejects_raw_outputs_body_keys_and_release_or_gate_mutation_flags() -> None:
    ratings_review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        run_id="p4_10_guard_rating_source"
    )
    suites = build_product_readfeel_p4_regression_handoff_green_suite_statuses_20260610()
    unsafe_suite = dict(suites[0])
    unsafe_suite["raw_test_output"] = "raw pytest output must not be retained"
    with pytest.raises(ValueError):
        build_product_readfeel_p4_regression_handoff_20260610(
            p4_ratings_review=ratings_review,
            regression_suite_statuses=[unsafe_suite],
            run_id="p4_10_guard_raw_output",
        )

    clean = build_product_readfeel_p4_regression_handoff_20260610(
        p4_ratings_review=ratings_review,
        regression_suite_statuses=suites,
        run_id="p4_10_guard_clean",
    )
    unsafe_summary = dict(clean["summary"])
    unsafe_summary["gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_regression_handoff_meta_only_20260610(unsafe_summary)

    unsafe_release = dict(clean["summary"])
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p4_regression_handoff_meta_only_20260610(unsafe_release)


def test_p4_10_required_suite_catalog_stays_explicit_and_contract_focused() -> None:
    assert list(P4_10_REQUIRED_REGRESSION_SUITES_20260610) == [
        "p4_new_tests",
        "p3_product_readfeel_regression",
        "product_readfeel_surface_guard_subset",
        "public_recovery_limited_source_unavailable_subset",
        "user_label_connection_boundary_subset",
        "backend_contract",
        "display_contract",
        "two_stage_e2e",
        "rn_contract",
    ]
