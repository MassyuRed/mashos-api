# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_regression_handoff import (
    DECISION_P4_RETURN,
    DECISION_P5_CONTINUE,
    DECISION_P6_HOLD,
    DECISION_P6_READY,
    P5_7_REQUIRED_REGRESSION_SUITES,
    USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP,
    USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION,
    assert_user_label_connection_p5_regression_handoff_contract,
    build_user_label_connection_p5_regression_handoff,
    dump_user_label_connection_p5_regression_handoff_public_summary,
    normalize_user_label_connection_p5_regression_suite_status,
    user_label_connection_p5_regression_handoff_public_summary,
)
from test_emlis_ai_user_label_connection_p5_limited_visible_connection_20260611 import _connection, _p5_chain
from test_emlis_ai_user_label_connection_p5_product_quality_review_20260611 import _ratings_row, _review

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
    "reviewer_free_text",
    "raw_test_output",
    "test_output",
    "command_output",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _green_suites(**overrides: Any) -> list[dict[str, Any]]:
    suites = [
        {
            "suite_id": suite_id,
            "status": "passed",
            "required": True,
            "passed_count": 10,
            "failed_count": 0,
            "warning_count": 0,
        }
        for suite_id in P5_7_REQUIRED_REGRESSION_SUITES
    ]
    by_id = {item["suite_id"]: item for item in suites}
    for suite_id, patch in overrides.items():
        by_id[suite_id].update(patch)
    return list(by_id.values())


def _p4_handoff(**overrides: Any) -> dict[str, Any]:
    summary = {
        "schema_version": "cocolon.emlis.product_readfeel.p4.regression_handoff_summary.20260610.v1",
        "post_p4_current_only_readfeel_minimum_met": True,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "comment_text_body_included": False,
        "raw_text_included": False,
        "public_release_applied": False,
        "release_allowed": False,
    }
    summary.update(overrides)
    return {"summary": summary}


def _green_sources() -> dict[str, Any]:
    chain = _p5_chain()
    connection = _connection(
        p5_visibility_boundary=chain["p5_visibility_boundary"],
        p5_eligibility_matrix=chain["p5_eligibility_matrix"],
        p5_surface_role_plan=chain["p5_surface_role_plan"],
        p5_safety_guard=chain["p5_safety_guard"],
        p5_product_quality_review=chain["p5_product_quality_review"],
        run_id="p5_7_limited_visible_source",
    )
    return {
        **chain,
        "p5_limited_visible_connection": connection,
    }


def _handoff(**overrides: Any) -> dict[str, Any]:
    sources = _green_sources()
    args = {
        "p5_limited_visible_connection": sources["p5_limited_visible_connection"],
        "p5_product_quality_review": sources["p5_product_quality_review"],
        "p5_safety_guard": sources["p5_safety_guard"],
        "p4_regression_handoff": _p4_handoff(),
        "regression_suite_statuses": _green_suites(),
        "p6_candidate_families": ["structure_question", "long_meaning_arc", "self_understanding_follow"],
        "run_id": "p5_7_regression_handoff",
    }
    args.update(overrides)
    return build_user_label_connection_p5_regression_handoff(**args)


def test_p5_7_marks_p6_ready_only_when_p5_connection_regressions_and_p6_family_scope_are_green() -> None:
    handoff = _handoff(run_id="p5_7_p6_ready_test")
    summary = handoff["summary"]

    assert handoff["schema_version"] == USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SCHEMA_VERSION
    assert handoff["step"] == USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_STEP
    assert summary["schema_version"] == USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION
    assert summary["handoff_decision"] == DECISION_P6_READY
    assert summary["p6_ready"] is True
    assert summary["p6_hold"] is False
    assert summary["p5_continue"] is False
    assert summary["p4_return"] is False
    assert summary["decision_reason_codes"] == []
    assert summary["all_required_regression_green"] is True
    assert summary["missing_required_regression_suites"] == []
    assert summary["p5_limited_visible_connection_ready"] is True
    assert summary["current_input_not_masked_by_history"] is True
    assert summary["creepy_overclaim_self_blame_risk_not_increased"] is True
    assert summary["p5_deep_insight_substitute_used"] is False
    assert summary["p6_target_family_scope_limited"] is True
    assert summary["p4_current_only_readfeel_preserved"] is True
    assert summary["release_allowed"] is False
    assert handoff["release_allowed"] is False
    assert summary["public_contract"]["public_response_key_added"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(handoff) is False
    assert_user_label_connection_p5_regression_handoff_contract(handoff)


def test_p5_7_holds_p6_when_p5_is_green_but_p6_family_scope_or_late_regression_is_not_ready() -> None:
    no_family = _handoff(p6_candidate_families=[], run_id="p5_7_p6_family_missing_test")
    summary = no_family["summary"]
    assert summary["handoff_decision"] == DECISION_P6_HOLD
    assert summary["p6_hold"] is True
    assert "p6_target_family_missing" in summary["p6_hold_material"]

    rn_hold = _handoff(
        regression_suite_statuses=_green_suites(
            rn_contract_tests={"status": "not_executed", "passed_count": 0, "failed_count": 0}
        ),
        run_id="p5_7_rn_contract_hold_test",
    )
    assert rn_hold["summary"]["handoff_decision"] == DECISION_P6_HOLD
    assert "required_regression_not_green:rn_contract_tests" in rn_hold["summary"]["p6_hold_material"]

    out_of_scope = _handoff(
        p6_candidate_families=["structure_question", "relationship_future_prediction"],
        run_id="p5_7_p6_family_out_of_scope_test",
    )
    assert out_of_scope["summary"]["handoff_decision"] == DECISION_P6_HOLD
    assert "p6_target_family_out_of_scope:relationship_future_prediction" in out_of_scope["summary"]["p6_hold_material"]


def test_p5_7_continues_p5_when_limited_visible_connection_or_risk_quality_is_not_green() -> None:
    blocked_connection = _connection(observation_status="hold", run_id="p5_7_blocked_connection_source")
    blocked = _handoff(
        p5_limited_visible_connection=blocked_connection,
        run_id="p5_7_p5_continue_connection_block_test",
    )

    assert blocked["summary"]["handoff_decision"] == DECISION_P5_CONTINUE
    assert blocked["summary"]["p5_continue"] is True
    assert "p5_limited_visible_connection_not_ready" in blocked["summary"]["p5_continue_material"]
    assert "p5_limited_visible:observation_status_not_passed" in blocked["summary"]["p5_continue_material"]

    sources = _green_sources()
    low_quality = _review(
        p5_safety_guard=sources["p5_safety_guard"],
        review_rows=[
            _ratings_row(
                ratings={
                    "history_connection_naturalness": 0.94,
                    "creepy_absence": 0.94,
                    "overclaim_absence": 0.97,
                    "self_blame_non_amplification": 0.97,
                    "current_input_not_masked_by_history": 0.98,
                    "non_template": 0.96,
                    "self_information_organized": 0.93,
                    "wants_more_input_or_accumulation": 0.9,
                    "subscription_boundary_correctness": 1.0,
                    "no_raw_text_meta": 1.0,
                }
            )
        ],
        run_id="p5_7_low_quality_source",
    )
    risk = _handoff(
        p5_limited_visible_connection=sources["p5_limited_visible_connection"],
        p5_product_quality_review=low_quality,
        p5_safety_guard=sources["p5_safety_guard"],
        run_id="p5_7_p5_continue_quality_risk_test",
    )

    assert risk["summary"]["handoff_decision"] == DECISION_P5_CONTINUE
    assert "creepy_overclaim_self_blame_risk_increased" in risk["summary"]["p5_continue_material"]


def test_p5_7_returns_to_p4_when_current_only_regression_or_p4_suites_are_not_preserved() -> None:
    p4_regressed = _handoff(
        p4_regression_handoff=_p4_handoff(post_p4_current_only_readfeel_minimum_met=False),
        run_id="p5_7_p4_current_only_regressed_test",
    )
    assert p4_regressed["summary"]["handoff_decision"] == DECISION_P4_RETURN
    assert p4_regressed["summary"]["p4_return"] is True
    assert "p4_current_only_regression_not_preserved" in p4_regressed["summary"]["p4_return_material"]

    p4_suite_failed = _handoff(
        regression_suite_statuses=_green_suites(
            product_readfeel_p4_tests={"status": "failed", "failed_count": 1}
        ),
        run_id="p5_7_p4_suite_failed_test",
    )
    assert p4_suite_failed["summary"]["handoff_decision"] == DECISION_P4_RETURN
    assert "required_regression_not_green:product_readfeel_p4_tests" in p4_suite_failed["summary"]["p4_return_material"]


def test_p5_7_public_summary_is_body_free_and_does_not_expose_suite_packets_or_release() -> None:
    dumped = dump_user_label_connection_p5_regression_handoff_public_summary(
        _handoff(run_id="p5_7_public_summary_source")
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == USER_LABEL_CONNECTION_P5_REGRESSION_HANDOFF_SUMMARY_SCHEMA_VERSION
    assert parsed["handoff_decision"] == DECISION_P6_READY
    assert parsed["public_response_key_added"] is False
    assert parsed["response_shape_changed"] is False
    assert parsed["raw_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["history_raw_text_included"] is False
    assert parsed["raw_test_output_included"] is False
    assert parsed["command_output_included"] is False
    assert parsed["release_allowed"] is False
    assert '"regression_suite_statuses"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_test_output"' not in dumped
    assert _contains_forbidden_raw_key(parsed) is False
    assert_user_label_connection_p5_regression_handoff_contract(parsed, allow_partial=True)


def test_p5_7_rejects_raw_test_output_and_release_or_contract_mutation() -> None:
    unsafe_suite = dict(_green_suites()[0])
    unsafe_suite["raw_test_output"] = "must not be retained"
    with pytest.raises(ValueError):
        normalize_user_label_connection_p5_regression_suite_status(unsafe_suite)

    clean = _handoff(run_id="p5_7_contract_source")
    release = dict(clean)
    release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_regression_handoff_contract(release)

    summary_release = dict(clean)
    summary_release["summary"] = dict(clean["summary"], release_allowed=True)
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_regression_handoff_contract(summary_release)

    contract = dict(clean)
    contract["summary"] = {
        **clean["summary"],
        "public_contract": dict(clean["summary"]["public_contract"], response_shape_changed=True),
    }
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_regression_handoff_contract(contract)


def test_p5_7_required_regression_suite_catalog_matches_design_boundary() -> None:
    assert list(P5_7_REQUIRED_REGRESSION_SUITES) == [
        "user_label_connection_existing_tests",
        "p5_new_tests",
        "p4_regression_handoff_tests",
        "product_readfeel_p4_tests",
        "public_feedback_meta_tests",
        "display_contract_tests",
        "two_stage_reception_e2e",
        "rn_contract_tests",
        "free_tier_boundary_tests",
        "low_information_boundary_tests",
        "no_raw_text_meta_tests",
    ]
