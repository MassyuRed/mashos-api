# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_readiness import (
    P5_ENTRY_DECISION_ALLOWED,
    P5_ENTRY_DECISION_BLOCKED_UNSAFE_PAYLOAD,
    P5_ENTRY_DECISION_CURRENT_ONLY_RECHECK_REQUIRED,
    P5_ENTRY_DECISION_HOLD,
    P5_ENTRY_DECISION_REGRESSION_BLOCKED,
    USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_READINESS_STEP,
    assert_user_label_connection_p5_readiness_contract,
    build_user_label_connection_p5_readiness,
    user_label_connection_p5_readiness_public_summary,
)
from fixtures.emlis_ai_product_readfeel_p4_regression_handoff_20260610 import (
    SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED,
    SCENARIO_GREEN_REGRESSION_P5_HOLD,
    SCENARIO_GREEN_REGRESSION_P5_READY,
    SCENARIO_REMAINING_BLOCKERS,
    build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610,
)

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
    "reply_text",
    "replyText",
    "surface_text",
    "surfaceText",
    "display_text",
    "displayText",
    "visible_text",
    "visibleText",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _p4_summary(scenario: str) -> dict[str, Any]:
    return build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=scenario,
        run_id=f"p5_0_readiness_{scenario}",
    )


def test_p5_0_allows_entry_only_after_p4_ready_and_green_regression_without_visible_strengthening() -> None:
    readiness = build_user_label_connection_p5_readiness(
        _p4_summary(SCENARIO_GREEN_REGRESSION_P5_READY),
        run_id="p5_0_ready_green_regression_test",
    )

    assert readiness["schema_version"] == USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION
    assert readiness["step"] == USER_LABEL_CONNECTION_P5_READINESS_STEP
    assert readiness["decision"] == P5_ENTRY_DECISION_ALLOWED
    assert readiness["p4_10_handoff_packet_seen"] is True
    assert readiness["all_required_regression_green"] is True
    assert readiness["post_p4_p5_connection_allowed"] is True
    assert readiness["post_p4_current_only_readfeel_minimum_met"] is True
    assert readiness["post_p4_main_family_readfeel_minimum_met"] is True
    assert readiness["history_line_masks_current_input_gap"] is False
    assert readiness["p5_entry_allowed"] is True
    assert readiness["p5_visible_strengthening_allowed"] is True
    assert readiness["p5_hold_continues"] is False
    assert readiness["p5_hold_reason_codes"] == []
    assert readiness["p5_visible_surface_strengthened"] is False
    assert readiness["p5_runtime_change_applied"] is False
    assert readiness["p5_visible_surface_connected"] is False
    assert readiness["p5_runtime_visible_connection_applied"] is False
    assert readiness["public_contract"]["response_shape_changed"] is False
    assert readiness["public_contract"]["public_response_key_added"] is False
    assert readiness["body_free"]["raw_input_included"] is False
    assert readiness["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(readiness) is False
    assert_user_label_connection_p5_readiness_contract(readiness)


def test_p5_0_keeps_hold_when_p4_green_regression_still_lacks_current_only_readfeel_floor() -> None:
    readiness = build_user_label_connection_p5_readiness(
        _p4_summary(SCENARIO_GREEN_REGRESSION_P5_HOLD),
        run_id="p5_0_current_only_recheck_hold_test",
    )

    assert readiness["decision"] == P5_ENTRY_DECISION_CURRENT_ONLY_RECHECK_REQUIRED
    assert readiness["all_required_regression_green"] is True
    assert readiness["post_p4_p5_connection_allowed"] is False
    assert readiness["post_p4_current_only_readfeel_minimum_met"] is False
    assert readiness["post_p4_main_family_readfeel_minimum_met"] is False
    assert readiness["p5_entry_allowed"] is False
    assert readiness["p5_visible_strengthening_allowed"] is False
    assert readiness["p5_hold_continues"] is True
    assert "current_only_readfeel_minimum_not_met" in readiness["p5_hold_reason_codes"]
    assert "main_family_readfeel_minimum_not_met" in readiness["p5_hold_reason_codes"]
    assert "p5_hold_reason_codes_present" in readiness["p5_hold_reason_codes"]
    assert "p4_hold:current_only_readfeel_below_minimum" in readiness["p5_hold_reason_codes"]
    assert readiness["p5_visible_surface_strengthened"] is False
    assert readiness["p5_runtime_change_applied"] is False
    assert_user_label_connection_p5_readiness_contract(readiness)


def test_p5_0_blocks_entry_when_required_regression_is_not_green() -> None:
    readiness = build_user_label_connection_p5_readiness(
        _p4_summary(SCENARIO_BACKEND_ONLY_RN_NOT_EXECUTED),
        run_id="p5_0_required_regression_blocked_test",
    )

    assert readiness["decision"] == P5_ENTRY_DECISION_REGRESSION_BLOCKED
    assert readiness["all_required_regression_green"] is False
    assert readiness["p5_entry_allowed"] is False
    assert readiness["p5_visible_strengthening_allowed"] is False
    assert "required_regression_not_green" in readiness["p5_hold_reason_codes"]
    assert "regression:required_regression_not_green:rn_contract" in readiness["p5_hold_reason_codes"]
    assert_user_label_connection_p5_readiness_contract(readiness)


def test_p5_0_keeps_hold_for_remaining_p4_rating_blockers() -> None:
    readiness = build_user_label_connection_p5_readiness(
        _p4_summary(SCENARIO_REMAINING_BLOCKERS),
        run_id="p5_0_remaining_p4_blockers_test",
    )

    assert readiness["decision"] == P5_ENTRY_DECISION_CURRENT_ONLY_RECHECK_REQUIRED
    assert readiness["all_required_regression_green"] is True
    assert readiness["post_p4_p5_connection_allowed"] is False
    assert readiness["p5_entry_allowed"] is False
    assert readiness["p5_visible_strengthening_allowed"] is False
    assert "post_p4_p5_connection_not_allowed" in readiness["p5_hold_reason_codes"]
    assert "current_only_readfeel_minimum_not_met" in readiness["p5_hold_reason_codes"]
    assert "p4_hold:rich_input_low_information_overroute" in readiness["p5_hold_reason_codes"]
    assert_user_label_connection_p5_readiness_contract(readiness)


def test_p5_0_rejects_missing_handoff_and_unsafe_source_payloads_without_leaking_body_text() -> None:
    missing = build_user_label_connection_p5_readiness(None, run_id="p5_0_missing_handoff_test")

    assert missing["decision"] == P5_ENTRY_DECISION_REGRESSION_BLOCKED
    assert missing["p4_10_handoff_packet_seen"] is False
    assert missing["p5_entry_allowed"] is False
    assert "p4_handoff_missing" in missing["p5_hold_reason_codes"]
    assert_user_label_connection_p5_readiness_contract(missing)

    unsafe = build_user_label_connection_p5_readiness(
        {
            "p4_10_handoff_packet_created": True,
            "all_required_regression_green": True,
            "post_p4_p5_connection_allowed": True,
            "post_p4_current_only_readfeel_minimum_met": True,
            "post_p4_main_family_readfeel_minimum_met": True,
            "comment_text": "must not be retained",
        },
        run_id="p5_0_unsafe_payload_test",
    )

    assert unsafe["decision"] == P5_ENTRY_DECISION_BLOCKED_UNSAFE_PAYLOAD
    assert unsafe["p5_entry_allowed"] is False
    assert "unsafe_text_payload_detected" in unsafe["p5_hold_reason_codes"]
    assert _contains_forbidden_raw_key(unsafe) is False
    assert_user_label_connection_p5_readiness_contract(unsafe)


def test_p5_0_public_summary_is_body_free_and_contract_stable() -> None:
    readiness = build_user_label_connection_p5_readiness(
        _p4_summary(SCENARIO_GREEN_REGRESSION_P5_READY),
        run_id="p5_0_public_summary_test",
    )
    public_summary = user_label_connection_p5_readiness_public_summary(readiness)
    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)

    assert public_summary["p5_entry_allowed"] is True
    assert public_summary["p5_visible_strengthening_allowed"] is True
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["raw_input_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert '"comment_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"history_records"' not in dumped
    assert_user_label_connection_p5_readiness_contract(public_summary, allow_partial=True)


def test_p5_0_contract_guard_rejects_body_keys_and_forbidden_true_flags() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_readiness_contract({"schema_version": USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION, "text": "body"})

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_readiness_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_READINESS_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_READINESS_STEP,
                "public_response_key_added": True,
            },
            allow_partial=True,
        )
