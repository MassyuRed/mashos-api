# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_limited_visible_connection import (
    USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP,
    assert_user_label_connection_p5_limited_visible_connection_contract,
    build_user_label_connection_p5_limited_visible_connection,
    user_label_connection_p5_limited_visible_connection_public_summary,
)
from test_emlis_ai_user_label_connection_p5_visibility_boundary_20260611 import _visibility_boundary
from test_emlis_ai_user_label_connection_p5_eligibility_matrix_20260611 import _matrix
from test_emlis_ai_user_label_connection_p5_surface_role_plan_20260611 import _plan
from test_emlis_ai_user_label_connection_p5_safety_guard_20260611 import _guard
from test_emlis_ai_user_label_connection_p5_product_quality_review_20260611 import _ratings_row, _review

BASE_COMMENT_TEXT = "今回の入力は、まず今の状態として受け取ります。"

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
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _existing_gate_reports(**overrides: Any) -> dict[str, Any]:
    reports = {
        "display_gate": {"passed": True},
        "grounding": {"passed": True},
        "template_echo": {"passed": True},
        "safety": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
    }
    reports.update(overrides)
    return reports


def _p5_chain(**overrides: Any) -> dict[str, Any]:
    visibility = overrides.get("p5_visibility_boundary") or _visibility_boundary(run_id="p5_6_visibility_source")
    matrix = overrides.get("p5_eligibility_matrix") or _matrix(
        p5_visibility_boundary=visibility,
        run_id="p5_6_eligibility_source",
    )
    plan = overrides.get("p5_surface_role_plan") or _plan(
        p5_eligibility_matrix=matrix,
        run_id="p5_6_role_plan_source",
    )
    guard = overrides.get("p5_safety_guard") or _guard(
        p5_surface_role_plan=plan,
        run_id="p5_6_safety_guard_source",
    )
    review = overrides.get("p5_product_quality_review") or _review(
        p5_safety_guard=guard,
        run_id="p5_6_product_quality_source",
    )
    return {
        "p5_visibility_boundary": visibility,
        "p5_eligibility_matrix": matrix,
        "p5_surface_role_plan": plan,
        "p5_safety_guard": guard,
        "p5_product_quality_review": review,
    }


def _connection(**overrides: Any):
    chain = _p5_chain(**{key: value for key, value in overrides.items() if key.startswith("p5_")})
    args = {
        "existing_comment_text": BASE_COMMENT_TEXT,
        "observation_status": "passed",
        **chain,
        "existing_gate_reports": _existing_gate_reports(),
        "run_id": "p5_6_limited_visible_connection",
    }
    args.update({key: value for key, value in overrides.items() if not key.startswith("p5_")})
    existing_comment_text = args.pop("existing_comment_text")
    return build_user_label_connection_p5_limited_visible_connection(existing_comment_text, **args)


def test_p5_6_applies_limited_visible_connection_only_after_p5_1_to_p5_5_pass() -> None:
    result = _connection(run_id="p5_6_green_connection_test")
    meta = result.as_meta()

    assert result.applied is True
    assert result.comment_text.startswith(BASE_COMMENT_TEXT)
    assert "Emlisから見える範囲では" in result.comment_text
    assert "ように見えます" in result.comment_text
    assert meta["schema_version"] == USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION
    assert meta["step"] == USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP
    assert meta["applied"] is True
    assert meta["limited_visible_connection_applied"] is True
    assert meta["history_line_surface_connected"] is True
    assert meta["comment_text_connected"] is True
    assert meta["existing_comment_text_present"] is True
    assert meta["observation_status_passed"] is True
    assert meta["existing_gate_reports_passed"] is True
    assert meta["p5_visibility_boundary_allowed"] is True
    assert meta["p5_eligibility_connectable"] is True
    assert meta["p5_surface_role_plan_ready"] is True
    assert meta["p5_safety_guard_allowed"] is True
    assert meta["p5_product_quality_allowed"] is True
    assert meta["rejection_reasons"] == []
    assert meta["public_contract"]["public_response_key_added"] is False
    assert meta["public_contract"]["response_shape_changed"] is False
    assert meta["public_contract"]["rn_visible_contract_changed"] is False
    assert meta["body_free"]["comment_text_body_in_meta_included"] is False
    assert meta["release_allowed"] is False
    assert meta["public_release_applied"] is False
    assert meta["product_quality_released"] is False
    assert meta["visible_connection_route"] == "p5_6_boundary_internal_phase8_connector"
    assert meta["p5_6_boundary_enforced"] is True
    assert meta["phase8_connector_scope"] == "p5_6_internal_boundary_only"
    assert meta["phase8_direct_reply_service_call_allowed"] is False
    assert meta["phase8_direct_visible_connection_from_reply_service"] is False
    assert meta["old_phase8_direct_visible_connection_replaced_by_p5_6_boundary"] is True
    assert meta["legacy_phase8_direct_call_used"] is False
    assert meta["phase8_connector_called_inside_p5_6_boundary"] is True
    assert meta["post_connection_regate_required"] is True
    assert meta["post_connection_gate_passed"] is True
    assert meta["p5_red_002_closed_by_route"] is True
    assert _contains_forbidden_raw_key(meta) is False
    assert_user_label_connection_p5_limited_visible_connection_contract(meta)


def test_p5_6_keeps_current_comment_primary_and_history_line_as_support() -> None:
    result = _connection(run_id="p5_6_current_primary_history_support_test")
    meta = result.as_meta()

    assert result.comment_text.index(BASE_COMMENT_TEXT) == 0
    assert "\n\nEmlisから見える範囲では" in result.comment_text
    assert "あなたはいつも" not in result.comment_text
    assert "原因は" not in result.comment_text
    assert "こうするべき" not in result.comment_text
    assert meta["connection_shape"]["existing_comment_text_primary"] is True
    assert meta["connection_shape"]["history_line_support_section"] is True
    assert meta["connection_shape"]["current_input_not_masked_by_history"] is True
    assert meta["comment_text_visible_body_owner"] == "input_feedback.comment_text"
    assert meta["input_feedback_user_label_connection_meta_kind"] == "safe_summary_only"


def test_p5_6_blocks_missing_comment_non_passed_status_and_existing_gate_failure() -> None:
    missing = _connection(existing_comment_text="", run_id="p5_6_missing_comment_test")
    assert missing.applied is False
    assert missing.comment_text == ""
    assert "existing_comment_text_missing" in missing.meta["rejection_reasons"]
    assert_user_label_connection_p5_limited_visible_connection_contract(missing.as_meta())

    non_passed = _connection(observation_status="hold", run_id="p5_6_non_passed_status_test")
    assert non_passed.applied is False
    assert non_passed.comment_text == BASE_COMMENT_TEXT
    assert "observation_status_not_passed" in non_passed.meta["rejection_reasons"]

    safety_failed = _connection(
        existing_gate_reports=_existing_gate_reports(safety={"passed": False, "primary_reason": "safety_gate_failed"}),
        run_id="p5_6_safety_gate_failed_test",
    )
    assert safety_failed.applied is False
    assert safety_failed.comment_text == BASE_COMMENT_TEXT
    assert "safety_gate_failed" in safety_failed.meta["rejection_reasons"]
    assert safety_failed.meta["existing_gate_reports"]["safety"]["passed"] is False


def test_p5_6_blocks_when_any_p5_boundary_from_p5_1_to_p5_5_is_not_ready() -> None:
    blocked_visibility = _visibility_boundary(subscription_tier="free", run_id="p5_6_free_visibility_source")
    blocked_matrix = _matrix(p5_visibility_boundary=blocked_visibility, run_id="p5_6_free_matrix_source")
    blocked_plan = _plan(p5_eligibility_matrix=blocked_matrix, run_id="p5_6_free_plan_source")
    blocked_guard = _guard(p5_surface_role_plan=blocked_plan, run_id="p5_6_free_guard_source")
    blocked_review = _review(p5_safety_guard=blocked_guard, run_id="p5_6_free_review_source")
    blocked = _connection(
        p5_visibility_boundary=blocked_visibility,
        p5_eligibility_matrix=blocked_matrix,
        p5_surface_role_plan=blocked_plan,
        p5_safety_guard=blocked_guard,
        p5_product_quality_review=blocked_review,
        run_id="p5_6_upstream_boundary_block_test",
    )

    assert blocked.applied is False
    assert "p5_visibility_boundary_not_allowed" in blocked.meta["rejection_reasons"]
    assert "p5_eligibility_not_connectable" in blocked.meta["rejection_reasons"]
    assert "p5_surface_role_plan_not_ready" in blocked.meta["rejection_reasons"]
    assert "p5_safety_guard_not_allowed" in blocked.meta["rejection_reasons"]

    clean_chain = _p5_chain()
    risky_guard = _guard(
        p5_surface_role_plan=clean_chain["p5_surface_role_plan"],
        guard_signal_meta={"creepy_risk": True},
        run_id="p5_6_risky_guard_source",
    )
    risky_review = _review(p5_safety_guard=risky_guard, run_id="p5_6_risky_review_source")
    risky = _connection(
        p5_visibility_boundary=clean_chain["p5_visibility_boundary"],
        p5_eligibility_matrix=clean_chain["p5_eligibility_matrix"],
        p5_surface_role_plan=clean_chain["p5_surface_role_plan"],
        p5_safety_guard=risky_guard,
        p5_product_quality_review=risky_review,
        run_id="p5_6_safety_guard_block_test",
    )

    assert risky.applied is False
    assert "p5_safety_guard_not_allowed" in risky.meta["rejection_reasons"]
    assert "p5_product_quality_review_not_allowed" in risky.meta["rejection_reasons"]


def test_p5_6_blocks_product_quality_review_with_low_ratings() -> None:
    chain = _p5_chain()
    low_review = _review(
        p5_safety_guard=chain["p5_safety_guard"],
        review_rows=[
            _ratings_row(
                ratings={
                    "history_connection_naturalness": 0.89,
                    "creepy_absence": 0.98,
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
        run_id="p5_6_low_quality_review_source",
    )
    result = _connection(
        p5_visibility_boundary=chain["p5_visibility_boundary"],
        p5_eligibility_matrix=chain["p5_eligibility_matrix"],
        p5_surface_role_plan=chain["p5_surface_role_plan"],
        p5_safety_guard=chain["p5_safety_guard"],
        p5_product_quality_review=low_review,
        run_id="p5_6_low_quality_review_block_test",
    )

    assert result.applied is False
    assert result.comment_text == BASE_COMMENT_TEXT
    assert "p5_product_quality_review_not_allowed" in result.meta["rejection_reasons"]
    assert "p5_product_quality:dimension_below_target:history_connection_naturalness" in result.meta["rejection_reasons"]
    assert result.meta["p5_product_quality_allowed"] is False


def test_p5_6_public_summary_is_safe_and_does_not_expose_comment_text_body_or_release() -> None:
    result = _connection(run_id="p5_6_public_summary_source")
    summary = user_label_connection_p5_limited_visible_connection_public_summary(result)

    assert summary["public_meta_summary_only"] is True
    assert summary["applied"] is True
    assert summary["limited_visible_connection_applied"] is True
    assert summary["public_response_key_added"] is False
    assert summary["response_shape_changed"] is False
    assert summary["rn_visible_contract_changed"] is False
    assert summary["raw_text_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["history_raw_text_included"] is False
    assert summary["release_allowed"] is False
    assert summary["visible_connection_route"] == "p5_6_boundary_internal_phase8_connector"
    assert summary["p5_6_boundary_enforced"] is True
    assert summary["phase8_connector_scope"] == "p5_6_internal_boundary_only"
    assert summary["phase8_direct_reply_service_call_allowed"] is False
    assert summary["phase8_direct_visible_connection_from_reply_service"] is False
    assert summary["old_phase8_direct_visible_connection_replaced_by_p5_6_boundary"] is True
    assert summary["legacy_phase8_direct_call_used"] is False
    assert summary["phase8_connector_called_inside_p5_6_boundary"] is True
    assert summary["post_connection_regate_required"] is True
    assert summary["post_connection_gate_passed"] is True
    assert summary["p5_red_002_closed_by_route"] is True
    assert _contains_forbidden_raw_key(summary) is False
    assert_user_label_connection_p5_limited_visible_connection_contract(summary, allow_partial=True)


def test_p5_6_contract_rejects_raw_meta_and_release_or_contract_mutation() -> None:
    result = _connection(run_id="p5_6_contract_source")
    meta = result.as_meta()

    raw = dict(meta)
    raw["comment_text"] = "must not be in meta"
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_limited_visible_connection_contract(raw)

    release = dict(meta)
    release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_limited_visible_connection_contract(release)

    contract = dict(meta)
    contract["public_contract"] = dict(meta["public_contract"], response_shape_changed=True)
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_limited_visible_connection_contract(contract)

    body_free = dict(meta)
    body_free["body_free"] = dict(meta["body_free"], history_raw_text_included=True)
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_limited_visible_connection_contract(body_free)
