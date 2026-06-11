# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_eligibility_matrix import (
    DECISION_REVIEW_REQUIRED,
)
from emlis_ai_user_label_connection_p5_surface_role_plan import (
    SURFACE_PLAN_KIND_BLOCKED,
    SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
    SURFACE_PLAN_KIND_META_ONLY,
    USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP,
    assert_user_label_connection_p5_surface_role_plan_contract,
    build_user_label_connection_p5_surface_role_plan,
    user_label_connection_p5_surface_role_plan_public_summary,
)
from test_emlis_ai_user_label_connection_p5_eligibility_matrix_20260611 import _matrix

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
    "fixed_sentence",
    "template_text",
    "sentence_template",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _plan(**overrides: Any) -> dict[str, Any]:
    args = {
        "p5_eligibility_matrix": _matrix(run_id="p5_3_eligibility_source"),
        "run_id": "p5_3_surface_role_plan",
    }
    args.update(overrides)
    return build_user_label_connection_p5_surface_role_plan(**args)


def test_p5_3_builds_role_driven_plan_without_fixed_sentence_or_visible_body() -> None:
    plan = _plan(run_id="p5_3_ready_structure_question_test")

    assert plan["schema_version"] == USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION
    assert plan["step"] == USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP
    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    assert plan["role_plan_ready"] is True
    assert plan["meta_only"] is False
    assert plan["blocked"] is False
    assert plan["connectable_family"] == "structure_question"
    assert plan["source_connectable_family"] == "structure_question"
    assert plan["edge_family"] == "category_state_recurrence"
    assert plan["section_order"] == ["current_observation", "history_support_line", "not_personality_boundary"]
    assert plan["surface_shape"]["existing_visible_body_is_primary"] is True
    assert plan["surface_shape"]["current_observation_first"] is True
    assert plan["surface_shape"]["history_line_is_support"] is True
    assert plan["fixed_sentence_template_added"] is False
    assert plan["comment_text_generated_by_this_layer"] is False
    assert plan["visible_text_generated"] is False
    assert plan["visible_surface_connected"] is False
    assert plan["runtime_change_applied"] is False
    assert plan["public_contract"]["fixed_sentence_template_added"] is False
    assert plan["public_contract"]["public_response_key_added"] is False
    assert plan["body_free"]["surface_body_included"] is False
    assert plan["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(plan) is False
    assert_user_label_connection_p5_surface_role_plan_contract(plan)


def test_p5_3_preserves_existing_roles_and_adds_p5_support_line_roles() -> None:
    plan = _plan(run_id="p5_3_role_set_test")
    roles = set(plan["must_include_roles"])
    forbidden = set(plan["must_not_include_roles"])

    assert {
        "scope_marker",
        "current_input_anchor",
        "history_line_marker",
        "soft_observation",
        "not_personality_disclaimer",
        "self_understanding_support",
    }.issubset(roles)
    assert {
        "current_observation_first",
        "history_as_support_line",
        "evidence_count_boundary",
        "same_label_overlap",
        "time_scope_limited",
        "do_not_generalize_marker",
        "not_cause_marker",
        "not_advice_marker",
    }.issubset(roles)
    assert {
        "advice",
        "diagnosis",
        "personality_claim",
        "future_prediction",
        "always_claim",
        "should_statement",
        "cause_claim",
        "opponent_intent_claim",
        "self_blame_amplification",
    }.issubset(forbidden)
    assert roles.isdisjoint(forbidden)


def test_p5_3_maps_label_route_edge_and_long_meaning_family_to_expected_roles() -> None:
    eligibility = _matrix(
        connectable_family="long_meaning_arc",
        edge_meta={
            "edge_family": "label_route_current_alignment",
            "evidence_record_count": 2,
            "current_record_included": True,
            "evidence_point_ids": ["current:present", "history:owned:001"],
        },
        run_id="p5_3_long_meaning_label_route_source",
    )
    plan = _plan(
        p5_eligibility_matrix=eligibility,
        run_id="p5_3_long_meaning_label_route_test",
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    assert plan["connectable_family"] == "long_meaning_arc"
    assert plan["edge_family"] == "label_route_current_alignment"
    assert set(plan["role_family_mapping"]["roles"]) >= {"time_scope_limited", "evidence_count_boundary"}
    assert set(plan["edge_family_mapping"]["roles"]) >= {"same_label_overlap", "not_advice_marker"}
    assert_user_label_connection_p5_surface_role_plan_contract(plan)


def test_p5_3_keeps_review_required_and_meta_only_eligibility_invisible() -> None:
    review_eligibility = _matrix(
        edge_meta={
            "edge_family": "state_output_attachment",
            "evidence_record_count": 2,
            "current_record_included": True,
            "evidence_point_ids": ["current:present", "history:owned:001"],
        },
        run_id="p5_3_review_required_source",
    )
    assert review_eligibility["decision"] == DECISION_REVIEW_REQUIRED

    review_plan = _plan(
        p5_eligibility_matrix=review_eligibility,
        run_id="p5_3_review_required_plan_test",
    )
    assert review_plan["surface_plan_kind"] == SURFACE_PLAN_KIND_META_ONLY
    assert review_plan["role_plan_ready"] is False
    assert review_plan["review_required"] is True
    assert "p5_eligibility_not_connectable" in review_plan["rejection_reasons"]

    meta_eligibility = _matrix(
        connectable_family="daily_unpleasant",
        run_id="p5_3_meta_only_source",
    )
    meta_plan = _plan(
        p5_eligibility_matrix=meta_eligibility,
        run_id="p5_3_meta_only_plan_test",
    )
    assert meta_plan["surface_plan_kind"] == SURFACE_PLAN_KIND_META_ONLY
    assert meta_plan["role_plan_ready"] is False
    assert meta_plan["meta_only"] is True
    assert "p5_eligibility_not_connectable" in meta_plan["rejection_reasons"]


def test_p5_3_blocks_forbidden_requested_roles_even_when_p5_2_is_connectable() -> None:
    plan = _plan(
        requested_roles=["scope_marker", "advice", "cause_claim"],
        run_id="p5_3_forbidden_requested_roles_test",
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_KIND_BLOCKED
    assert plan["role_plan_ready"] is False
    assert plan["blocked"] is True
    assert "forbidden_role_detected" in plan["rejection_reasons"]
    assert "forbidden_role:advice" in plan["rejection_reasons"]
    assert "forbidden_role:cause_claim" in plan["rejection_reasons"]
    assert_user_label_connection_p5_surface_role_plan_contract(plan)


def test_p5_3_blocks_raw_payload_or_fixed_sentence_template_attempts() -> None:
    raw = _plan(
        role_overrides={"template_text": "fixed sentence body must not be accepted"},
        run_id="p5_3_raw_template_text_block_test",
    )
    assert raw["surface_plan_kind"] == SURFACE_PLAN_KIND_BLOCKED
    assert "raw_text_payload_detected" in raw["rejection_reasons"]
    assert _contains_forbidden_raw_key(raw) is False
    assert_user_label_connection_p5_surface_role_plan_contract(raw)

    fixed = _plan(
        role_overrides={"fixed_sentence_template_added": True},
        run_id="p5_3_fixed_sentence_template_block_test",
    )
    assert fixed["surface_plan_kind"] == SURFACE_PLAN_KIND_BLOCKED
    assert "contract_mutation_detected" in fixed["rejection_reasons"]
    assert "fixed_sentence_template_detected" in fixed["rejection_reasons"]
    assert_user_label_connection_p5_surface_role_plan_contract(fixed)


def test_p5_3_public_summary_is_body_free_and_contract_stable() -> None:
    plan = _plan(run_id="p5_3_public_summary_source")
    public_summary = user_label_connection_p5_surface_role_plan_public_summary(plan)
    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)

    assert public_summary["surface_plan_kind"] == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    assert public_summary["role_plan_ready"] is True
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["raw_text_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["history_raw_text_included"] is False
    assert '"comment_text"' not in dumped
    assert '"surface_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"history_records"' not in dumped
    assert_user_label_connection_p5_surface_role_plan_contract(public_summary, allow_partial=True)


def test_p5_3_contract_guard_rejects_body_keys_forbidden_true_flags_and_forbidden_roles() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_surface_role_plan_contract(
            {"schema_version": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION, "text": "body"}
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_surface_role_plan_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP,
                "public_response_key_added": True,
            },
            allow_partial=True,
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_surface_role_plan_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP,
                "surface_plan_kind": SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
                "role_plan_ready": True,
                "must_include_roles": ["scope_marker", "advice"],
                "must_not_include_roles": [
                    "advice",
                    "diagnosis",
                    "personality_claim",
                    "future_prediction",
                    "always_claim",
                    "should_statement",
                    "cause_claim",
                    "opponent_intent_claim",
                    "self_blame_amplification",
                ],
                "section_order": ["current_observation", "history_support_line", "not_personality_boundary"],
                "public_contract": {
                    "rn_visible_contract_changed": False,
                    "public_response_key_added": False,
                    "response_shape_changed": False,
                    "db_schema_changed": False,
                    "fixed_sentence_template_added": False,
                },
                "body_free": {
                    "raw_text_included": False,
                    "comment_text_body_included": False,
                    "candidate_body_included": False,
                    "surface_body_included": False,
                    "history_raw_text_included": False,
                },
            }
        )
