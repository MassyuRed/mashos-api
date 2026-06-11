# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_readiness import build_user_label_connection_p5_readiness
from emlis_ai_user_label_connection_p5_visibility_boundary import (
    DECISION_ALLOW_LIMITED_VISIBLE,
    DECISION_BLOCK,
    DECISION_HOLD,
    DECISION_META_ONLY,
    USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP,
    assert_user_label_connection_p5_visibility_boundary_contract,
    build_user_label_connection_p5_visibility_boundary,
    user_label_connection_p5_visibility_boundary_public_summary,
)
from fixtures.emlis_ai_product_readfeel_p4_regression_handoff_20260610 import (
    SCENARIO_GREEN_REGRESSION_P5_HOLD,
    SCENARIO_GREEN_REGRESSION_P5_READY,
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


def _readiness_ready() -> dict[str, Any]:
    handoff = build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_READY,
        run_id="p5_1_ready_handoff",
    )
    return build_user_label_connection_p5_readiness(handoff, run_id="p5_1_ready")


def _readiness_hold() -> dict[str, Any]:
    handoff = build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_HOLD,
        run_id="p5_1_hold_handoff",
    )
    return build_user_label_connection_p5_readiness(handoff, run_id="p5_1_hold")


def _material_meta(**overrides: Any) -> dict[str, Any]:
    material = {
        "capability_tier": "plus",
        "source_scope": "current_input_with_owned_history",
        "record_scope": "current_input_with_owned_history",
        "history_read_allowed": True,
        "current_point_present": True,
        "current_input_included": True,
        "user_fact_grounding_boundary_passed": True,
        "material_quality": "history_connection_candidate",
        "connection_edges": [
            {
                "edge_family": "category_state_recurrence",
                "evidence_record_count": 2,
                "current_record_included": True,
            }
        ],
        "max_edge_evidence_record_count": 2,
    }
    material.update(overrides)
    return material


def _gate_meta(**overrides: Any) -> dict[str, Any]:
    gate = {
        "passed": True,
        "blocked": False,
        "source_scope": "current_input_with_owned_history",
        "evidence_contract": {
            "evidence_record_count": 2,
            "current_record_included": True,
        },
        "scope_marker_required": True,
        "soft_marker_required": True,
    }
    gate.update(overrides)
    return gate


def _surface_plan_meta(**overrides: Any) -> dict[str, Any]:
    surface = {
        "surface_plan_kind": "limited_history_line_observation",
        "source_scope": "current_input_with_owned_history",
        "evidence_contract": {
            "evidence_record_count": 2,
            "current_record_included": True,
        },
        "scope_marker_required": True,
        "soft_marker_required": True,
    }
    surface.update(overrides)
    return surface


def _existing_gate_reports(**overrides: Any) -> dict[str, Any]:
    reports = {
        "display_gate": {"passed": True},
        "grounding_gate": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
        "template_gate": {"passed": True},
    }
    reports.update(overrides)
    return reports


def _visibility_boundary(**overrides: Any) -> dict[str, Any]:
    args = {
        "p5_readiness": _readiness_ready(),
        "material_meta": _material_meta(),
        "gate_meta": _gate_meta(),
        "surface_plan_meta": _surface_plan_meta(),
        "observation_reply_meta": {"family": "structure_question", "low_information": False},
        "existing_comment_text_present": True,
        "existing_gate_reports": _existing_gate_reports(),
        "subscription_tier": "plus",
        "run_id": "p5_1_visibility_boundary",
    }
    args.update(overrides)
    return build_user_label_connection_p5_visibility_boundary(**args)


def test_p5_1_allows_limited_visible_only_for_ready_plus_owned_history_with_existing_gates() -> None:
    boundary = _visibility_boundary(run_id="p5_1_allow_limited_visible_test")

    assert boundary["schema_version"] == USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION
    assert boundary["step"] == USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP
    assert boundary["decision"] == DECISION_ALLOW_LIMITED_VISIBLE
    assert boundary["allow_limited_visible"] is True
    assert boundary["meta_only"] is False
    assert boundary["hold"] is False
    assert boundary["blocked"] is False
    assert boundary["rejection_reasons"] == []
    assert boundary["eligibility"]["subscription_history_allowed"] is True
    assert boundary["eligibility"]["owned_history_only"] is True
    assert boundary["eligibility"]["current_input_included"] is True
    assert boundary["eligibility"]["evidence_record_count"] == 2
    assert boundary["eligibility"]["minimum_evidence_record_count"] == 2
    assert boundary["eligibility"]["user_fact_grounding_boundary_passed"] is True
    assert boundary["eligibility"]["scope_marker_required"] is True
    assert boundary["eligibility"]["soft_marker_required"] is True
    assert boundary["eligibility"]["current_input_not_masked_by_history"] is True
    assert boundary["existing_comment_text_present"] is True
    assert boundary["existing_gate_reports_passed"] is True
    assert boundary["public_contract"]["public_response_key_added"] is False
    assert boundary["public_contract"]["response_shape_changed"] is False
    assert boundary["body_free"]["raw_text_included"] is False
    assert boundary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(boundary) is False
    assert_user_label_connection_p5_visibility_boundary_contract(boundary)


def test_p5_1_keeps_hold_when_p5_0_entry_is_not_allowed() -> None:
    boundary = _visibility_boundary(
        p5_readiness=_readiness_hold(),
        run_id="p5_1_p5_0_hold_test",
    )

    assert boundary["decision"] == DECISION_HOLD
    assert boundary["allow_limited_visible"] is False
    assert boundary["hold"] is True
    assert boundary["blocked"] is False
    assert "p5_entry_not_allowed" in boundary["rejection_reasons"]
    assert "p5_hold:current_only_readfeel_minimum_not_met" in boundary["rejection_reasons"]
    assert_user_label_connection_p5_visibility_boundary_contract(boundary)


def test_p5_1_blocks_free_tier_history_connection_even_when_other_material_is_present() -> None:
    boundary = _visibility_boundary(
        material_meta=_material_meta(capability_tier="free"),
        subscription_tier="free",
        run_id="p5_1_free_tier_block_test",
    )

    assert boundary["decision"] == DECISION_BLOCK
    assert boundary["allow_limited_visible"] is False
    assert boundary["blocked"] is True
    assert boundary["eligibility"]["subscription_history_allowed"] is False
    assert "free_tier_history_blocked" in boundary["rejection_reasons"]
    assert_user_label_connection_p5_visibility_boundary_contract(boundary)


def test_p5_1_blocks_missing_current_input_and_insufficient_evidence() -> None:
    boundary = _visibility_boundary(
        material_meta=_material_meta(
            current_point_present=False,
            current_input_included=False,
            max_edge_evidence_record_count=1,
            connection_edges=[
                {
                    "edge_family": "category_state_recurrence",
                    "evidence_record_count": 1,
                    "current_record_included": False,
                }
            ],
        ),
        gate_meta=_gate_meta(evidence_contract={"evidence_record_count": 1, "current_record_included": False}),
        surface_plan_meta=_surface_plan_meta(evidence_contract={"evidence_record_count": 1, "current_record_included": False}),
        run_id="p5_1_current_and_evidence_block_test",
    )

    assert boundary["decision"] == DECISION_BLOCK
    assert boundary["eligibility"]["current_input_included"] is False
    assert boundary["eligibility"]["evidence_record_count"] == 1
    assert "current_input_missing" in boundary["rejection_reasons"]
    assert "history_record_count_insufficient" in boundary["rejection_reasons"]
    assert_user_label_connection_p5_visibility_boundary_contract(boundary)


def test_p5_1_blocks_low_information_safety_self_denial_and_target_judgement_markers() -> None:
    low_information = _visibility_boundary(
        material_meta=_material_meta(material_quality="low_information_protected"),
        observation_reply_meta={"family": "low_information_short"},
        run_id="p5_1_low_information_block_test",
    )
    assert low_information["decision"] == DECISION_BLOCK
    assert "low_information_history_promotion_blocked" in low_information["rejection_reasons"]

    safety = _visibility_boundary(
        observation_reply_meta={"family": "safety_adjacent"},
        run_id="p5_1_safety_block_test",
    )
    assert safety["decision"] == DECISION_BLOCK
    assert "safety_adjacent_history_connection_blocked" in safety["rejection_reasons"]

    self_denial = _visibility_boundary(
        observation_reply_meta={"family": "self_denial"},
        run_id="p5_1_self_denial_block_test",
    )
    assert self_denial["decision"] == DECISION_BLOCK
    assert "self_denial_history_connection_blocked" in self_denial["rejection_reasons"]

    target_judgement = _visibility_boundary(
        observation_reply_meta={"family": "anger_or_boundary", "context_marker": "opponent_intent_claim"},
        run_id="p5_1_target_judgement_block_test",
    )
    assert target_judgement["decision"] == DECISION_BLOCK
    assert "target_judgement_history_connection_blocked" in target_judgement["rejection_reasons"]


def test_p5_1_existing_comment_text_missing_or_marker_missing_stays_meta_only() -> None:
    missing_comment = _visibility_boundary(
        existing_comment_text_present=False,
        run_id="p5_1_existing_comment_missing_meta_only_test",
    )
    assert missing_comment["decision"] == DECISION_META_ONLY
    assert missing_comment["meta_only"] is True
    assert "existing_comment_text_missing" in missing_comment["rejection_reasons"]

    marker_missing = _visibility_boundary(
        surface_plan_meta=_surface_plan_meta(scope_marker_required=False, soft_marker_required=False),
        run_id="p5_1_marker_missing_meta_only_test",
    )
    assert marker_missing["decision"] == DECISION_META_ONLY
    assert "scope_marker_missing" in marker_missing["rejection_reasons"]
    assert "soft_marker_missing" in marker_missing["rejection_reasons"]


def test_p5_1_existing_gate_block_or_history_masking_blocks_visible_connection() -> None:
    gate_blocked = _visibility_boundary(
        existing_gate_reports=_existing_gate_reports(grounding_gate={"passed": False}),
        run_id="p5_1_existing_gate_blocked_test",
    )
    assert gate_blocked["decision"] == DECISION_BLOCK
    assert "existing_gate_blocked" in gate_blocked["rejection_reasons"]
    assert "existing_gate_blocked:grounding_gate" in gate_blocked["rejection_reasons"]

    history_masked = _visibility_boundary(
        p5_readiness=dict(_readiness_ready(), history_line_masks_current_input_gap=True),
        run_id="p5_1_history_masks_current_input_test",
    )
    assert history_masked["decision"] == DECISION_BLOCK
    assert "current_input_masked_by_history" in history_masked["rejection_reasons"]


def test_p5_1_detects_raw_payload_and_contract_mutation_without_leaking_bodies() -> None:
    raw_payload = _visibility_boundary(
        material_meta=_material_meta(memo="raw memo must not be carried"),
        run_id="p5_1_raw_payload_block_test",
    )
    assert raw_payload["decision"] == DECISION_BLOCK
    assert "raw_text_payload_detected" in raw_payload["rejection_reasons"]
    assert _contains_forbidden_raw_key(raw_payload) is False
    assert_user_label_connection_p5_visibility_boundary_contract(raw_payload)

    raw_payload_while_p5_hold = _visibility_boundary(
        p5_readiness=_readiness_hold(),
        material_meta=_material_meta(memo="raw memo must not be carried"),
        run_id="p5_1_raw_payload_still_blocks_when_p5_0_hold_test",
    )
    assert raw_payload_while_p5_hold["decision"] == DECISION_BLOCK
    assert "p5_entry_not_allowed" in raw_payload_while_p5_hold["rejection_reasons"]
    assert "raw_text_payload_detected" in raw_payload_while_p5_hold["rejection_reasons"]

    mutation = _visibility_boundary(
        surface_plan_meta=_surface_plan_meta(public_response_key_added=True),
        run_id="p5_1_contract_mutation_block_test",
    )
    assert mutation["decision"] == DECISION_BLOCK
    assert "contract_mutation_detected" in mutation["rejection_reasons"]
    assert_user_label_connection_p5_visibility_boundary_contract(mutation)


def test_p5_1_public_summary_is_body_free_and_keeps_response_contract_closed() -> None:
    boundary = _visibility_boundary(run_id="p5_1_public_summary_test")
    public_summary = user_label_connection_p5_visibility_boundary_public_summary(boundary)
    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)

    assert public_summary["decision"] == DECISION_ALLOW_LIMITED_VISIBLE
    assert public_summary["allow_limited_visible"] is True
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["raw_text_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["history_raw_text_included"] is False
    assert '"comment_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"history_records"' not in dumped
    assert_user_label_connection_p5_visibility_boundary_contract(public_summary, allow_partial=True)


def test_p5_1_contract_guard_rejects_body_keys_and_forbidden_true_flags() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_visibility_boundary_contract({"schema_version": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION, "body": "raw"})

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_visibility_boundary_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_VISIBILITY_BOUNDARY_STEP,
                "public_response_key_added": True,
            },
            allow_partial=True,
        )
