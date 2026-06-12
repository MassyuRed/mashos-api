# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_limited_visible_connection import (
    USER_LABEL_CONNECTION_P5_HUMAN_QA_BOUNDARY_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID,
    assert_user_label_connection_p5_limited_visible_connection_contract,
    user_label_connection_p5_limited_visible_connection_public_summary,
)
from test_emlis_ai_user_label_connection_p5_limited_visible_connection_20260611 import (
    _connection,
    _p5_chain,
)
from test_emlis_ai_user_label_connection_p5_product_quality_review_20260611 import _review
from test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612 import (
    _install_p5_runtime_history_context,
)

FORBIDDEN_BODY_KEYS = {
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
    "actual_appended_line",
    "body",
    "text",
}


def _contains_forbidden_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in FORBIDDEN_BODY_KEYS or _contains_forbidden_body_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_body_key(child) for child in value)
    return False


def _assert_public_boundary_is_body_free(boundary: Mapping[str, Any]) -> None:
    assert boundary["safe_summary_only"] is True
    assert boundary["input_feedback_comment_text_only_visible_body"] is True
    assert boundary["public_response_top_level_key_added"] is False
    assert boundary["public_response_key_added"] is False
    assert boundary["rn_visible_contract_changed"] is False
    assert boundary["api_route_changed"] is False
    assert boundary["request_key_changed"] is False
    assert boundary["db_schema_changed"] is False
    assert boundary["raw_input_included"] is False
    assert boundary["raw_text_included"] is False
    assert boundary["history_raw_text_included"] is False
    assert boundary["comment_text_body_included"] is False
    assert boundary["candidate_body_included"] is False
    assert boundary["surface_body_included"] is False
    assert boundary["reviewer_free_text_included"] is False
    assert boundary["actual_appended_line_included"] is False
    assert boundary["release_allowed"] is False


def test_r4_missing_human_qa_remains_hold_separate_from_runtime_evaluation_and_visible_application() -> None:
    chain = _p5_chain(run_id="p5_r4_missing_human_qa_chain")
    missing_human_review = _review(
        p5_safety_guard=chain["p5_safety_guard"],
        review_rows=[],
        run_id="p5_r4_missing_human_qa_review",
    )

    result = _connection(
        p5_visibility_boundary=chain["p5_visibility_boundary"],
        p5_eligibility_matrix=chain["p5_eligibility_matrix"],
        p5_surface_role_plan=chain["p5_surface_role_plan"],
        p5_safety_guard=chain["p5_safety_guard"],
        p5_product_quality_review=missing_human_review,
        run_id="p5_r4_missing_human_qa_boundary",
    )
    meta = result.as_meta()
    public_summary = user_label_connection_p5_limited_visible_connection_public_summary(meta)

    assert meta["runtime_evaluated"] is True
    assert meta["visible_applied"] is False
    assert meta["product_quality_confirmed"] is False
    assert meta["human_blind_qa_confirmed"] is False
    assert meta["product_quality_complete_claim_allowed"] is False
    assert meta["p5_completion_claim_allowed"] is False

    boundary = meta["p5_human_qa_boundary"]
    assert boundary["schema_version"] == USER_LABEL_CONNECTION_P5_HUMAN_QA_BOUNDARY_SCHEMA_VERSION
    assert boundary["hold_id"] == USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID
    assert boundary["human_qa_required"] is True
    assert boundary["human_qa_status"] == "not_started_or_missing"
    assert boundary["human_qa_complete"] is False
    assert boundary["human_blind_qa_confirmed"] is False
    assert boundary["runtime_evaluated"] is True
    assert boundary["visible_applied"] is False
    assert boundary["product_quality_confirmed"] is False
    assert boundary["human_qa_not_substituted_by_runtime"] is True
    assert boundary["human_qa_not_substituted_by_visible_connection"] is True
    assert boundary["product_quality_complete_claim_allowed"] is False
    assert boundary["p5_completion_claim_allowed"] is False
    assert boundary["live_runtime_review_rows_synthesized"] is False
    assert "p5_human_qa_review_rows_missing" in boundary["hold_reason_codes"]

    layers = meta["p5_completion_layers"]
    assert layers["runtime_evaluated"]["complete"] is True
    assert layers["visible_applied"]["complete"] is False
    assert layers["human_qa_product_quality"]["complete"] is False
    assert layers["human_qa_product_quality"]["hold_id"] == USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID
    assert layers["human_qa_product_quality"]["not_substituted_by_runtime"] is True
    assert layers["human_qa_product_quality"]["not_substituted_by_visible_connection"] is True

    _assert_public_boundary_is_body_free(meta["p5_public_meta_boundary"])
    assert public_summary["runtime_evaluated"] is True
    assert public_summary["visible_applied"] is False
    assert public_summary["product_quality_confirmed"] is False
    assert public_summary["human_blind_qa_confirmed"] is False
    assert public_summary["product_quality_complete_claim_allowed"] is False
    assert public_summary["p5_completion_claim_allowed"] is False
    assert _contains_forbidden_body_key(meta) is False
    assert _contains_forbidden_body_key(public_summary) is False
    assert_user_label_connection_p5_limited_visible_connection_contract(meta)


def test_r4_body_free_human_ratings_can_confirm_product_quality_without_claiming_p5_completion_or_release() -> None:
    result = _connection(run_id="p5_r4_human_ratings_confirmed_boundary")
    meta = result.as_meta()
    public_summary = user_label_connection_p5_limited_visible_connection_public_summary(meta)

    assert meta["runtime_evaluated"] is True
    assert meta["visible_applied"] is True
    assert meta["product_quality_confirmed"] is True
    assert meta["human_blind_qa_confirmed"] is True
    assert meta["product_quality_complete_claim_allowed"] is False
    assert meta["p5_completion_claim_allowed"] is False
    assert meta["release_allowed"] is False
    assert meta["public_release_applied"] is False

    boundary = meta["p5_human_qa_boundary"]
    assert boundary["human_qa_status"] == "confirmed_by_human_blind_qa"
    assert boundary["human_qa_review_rows_present"] is True
    assert boundary["human_qa_complete"] is True
    assert boundary["product_quality_confirmed"] is True
    assert boundary["product_quality_confirmed_by"] == "human_blind_qa_ratings"
    assert boundary["product_quality_complete_claim_allowed"] is False
    assert boundary["p5_completion_claim_allowed"] is False
    assert boundary["machine_metrics_used_as_human_qa"] is False
    assert boundary["reviewer_free_text_included"] is False

    layers = meta["p5_completion_layers"]
    assert layers["runtime_evaluated"]["complete"] is True
    assert layers["visible_applied"]["complete"] is True
    assert layers["human_qa_product_quality"]["complete"] is True
    assert layers["human_qa_product_quality"]["not_substituted_by_runtime"] is True
    assert layers["human_qa_product_quality"]["not_substituted_by_visible_connection"] is True

    _assert_public_boundary_is_body_free(meta["p5_public_meta_boundary"])
    assert public_summary["product_quality_confirmed"] is True
    assert public_summary["human_blind_qa_confirmed"] is True
    assert public_summary["product_quality_complete_claim_allowed"] is False
    assert public_summary["p5_completion_claim_allowed"] is False
    assert public_summary["release_allowed"] is False
    assert _contains_forbidden_body_key(public_summary) is False
    assert_user_label_connection_p5_limited_visible_connection_contract(meta)


@pytest.mark.asyncio
async def test_r4_actual_reply_runtime_summary_keeps_human_qa_pending_and_public_contract_static(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_p5_runtime_history_context(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="p5-r4-runtime-user",
        subscription_tier="plus",
        current_input={
            "id": "p5-r4-runtime-current-001",
            "created_at": "2026-06-12T00:00:00Z",
            "memo": "また仕事の判断で言い切れなくなっている。前も同じところで詰まった気がする。",
            "memo_action": "考え込んでいる。",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "emotions": ["不安"],
            "category": ["仕事"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta.get("diagnostic_summary") if isinstance(reply.meta.get("diagnostic_summary"), dict) else {}
    bridge = (
        reply.meta.get("user_label_connection_p5_runtime_bridge")
        or diagnostic.get("user_label_connection_p5_runtime_bridge")
        or reply.meta.get("p5_runtime_bridge")
    )

    assert isinstance(bridge, dict)
    assert bridge["schema_version"] == "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1"
    assert bridge["step"] == "P5_RuntimeBridge_Repair_R4_20260612"
    assert bridge["r4_boundary_step"] == "P5_RuntimeBridge_PublicMetaHumanQABoundary_R4_20260612"
    assert bridge["runtime_evaluated"] is True
    assert bridge["product_quality_confirmed"] is False
    assert bridge["human_qa_required"] is True
    assert bridge["human_qa_completed"] is False
    assert bridge["human_qa_pending"] is True
    assert bridge["p5_hold_001_human_qa_unconfirmed"] is True
    assert "P5-HOLD-001" in bridge["human_qa_hold_reason_codes"]
    assert bridge["runtime_evaluated_is_not_product_quality_confirmed"] is True
    assert bridge["product_quality_complete_claim_allowed"] is False
    assert bridge["p5_completion_claim_allowed"] is False
    assert bridge["release_allowed"] is False
    assert bridge["public_contract"]["public_response_key_added"] is False
    assert bridge["public_contract"]["rn_visible_contract_changed"] is False
    assert bridge["public_contract"]["api_route_changed"] is False
    assert bridge["public_contract"]["db_schema_changed"] is False
    assert bridge["body_free"]["raw_input_included"] is False
    assert bridge["body_free"]["raw_text_included"] is False
    assert bridge["body_free"]["history_raw_text_included"] is False
    assert bridge["body_free"]["comment_text_body_included"] is False
    assert bridge["body_free"]["candidate_body_included"] is False
    assert bridge["body_free"]["surface_body_included"] is False
    assert bridge["body_free"]["reviewer_free_text_included"] is False

    phase_gate = reply.meta.get("phase_gate") if isinstance(reply.meta.get("phase_gate"), dict) else {}
    if phase_gate:
        assert phase_gate["p5_runtime_bridge_r4_human_qa_required"] is True
        assert phase_gate["p5_runtime_bridge_r4_human_qa_completed"] is False
        assert phase_gate["p5_runtime_bridge_r4_human_qa_pending"] is True
        assert phase_gate["p5_runtime_bridge_r4_release_allowed"] is False
        assert phase_gate["p5_runtime_bridge_r4_public_response_key_added"] is False
        assert phase_gate["p5_runtime_bridge_r4_comment_text_body_included"] is False
        assert phase_gate["p5_runtime_bridge_r4_candidate_body_included"] is False
        assert phase_gate["p5_runtime_bridge_r4_surface_body_included"] is False
        assert phase_gate["p5_runtime_bridge_r4_reviewer_free_text_included"] is False
