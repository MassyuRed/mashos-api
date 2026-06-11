# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_family_review import (
    DECISION_ALLOW_REVIEW_CANDIDATE,
    DECISION_BLOCK_REVIEW_CANDIDATE,
    DECISION_HOLD_FOR_MANUAL_REVIEW,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_REVIEW_ALLOW,
    FAMILY_REVIEW_BLOCK,
    FAMILY_REVIEW_HOLD,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
    REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW,
    REASON_LONG_MEANING_ARC_SUMMARY_ONLY_BLOCKED,
    REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED,
    REASON_SELF_DENIAL_IDENTITY_NOT_INITIAL_AUTO_VISIBLE,
    REASON_STRUCTURE_QUESTION_SURFACE_PLAN_REUSE_BLOCKED,
    REASON_TARGET_JUDGEMENT_RISK_BLOCKED,
    STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_STEP,
    assert_structure_insight_p6_family_review_contract,
    build_structure_insight_p6_family_review,
    dump_structure_insight_p6_family_review_public_summary,
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
    "candidate_comment_text",
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
    "observation_text",
    "reception_text",
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


def test_p6_7_allows_long_meaning_arc_review_without_summary_only_shortcut() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=3,
        long_arc_summary_only=False,
        long_arc_relation_flow_present=True,
        run_id="p6_family_review_long_arc_allow",
    )

    assert review["schema_version"] == STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SCHEMA_VERSION
    assert review["step"] == STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_STEP
    assert review["family_review_classification"] == FAMILY_REVIEW_ALLOW
    assert review["decision"] == DECISION_ALLOW_REVIEW_CANDIDATE
    assert review["initial_auto_visible_allowed"] is False
    assert review["summary"]["long_meaning_arc_not_summary_only_enforced"] is True
    assert review["summary"]["long_arc_core_count"] == 3
    assert _contains_forbidden_raw_key(review) is False
    assert_structure_insight_p6_family_review_contract(review)


def test_p6_7_blocks_long_meaning_arc_when_it_is_summary_only() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=3,
        long_arc_summary_only=True,
        long_arc_relation_flow_present=True,
    )

    assert review["family_review_classification"] == FAMILY_REVIEW_BLOCK
    assert review["decision"] == DECISION_BLOCK_REVIEW_CANDIDATE
    assert REASON_LONG_MEANING_ARC_SUMMARY_ONLY_BLOCKED in review["decision_reason_codes"]


def test_p6_7_holds_long_arc_when_multiple_core_or_relation_flow_is_missing() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=1,
        long_arc_summary_only=False,
        long_arc_relation_flow_present=False,
    )

    assert review["family_review_classification"] == FAMILY_REVIEW_HOLD
    assert review["decision"] == DECISION_HOLD_FOR_MANUAL_REVIEW
    assert "long_meaning_arc_multiple_core_missing" in review["decision_reason_codes"]
    assert "long_meaning_arc_relation_flow_missing" in review["decision_reason_codes"]


def test_p6_7_allows_self_understanding_follow_when_observation_intent_is_safe() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        relation_family="uncertainty_effort_pair",
        self_understanding_observation_intent=True,
        self_understanding_uncertainty_boundary=True,
    )

    assert review["family_review_classification"] == FAMILY_REVIEW_ALLOW
    assert review["decision"] == DECISION_ALLOW_REVIEW_CANDIDATE
    assert review["initial_auto_visible_allowed"] is False
    assert review["summary"]["self_understanding_observation_intent_present"] is True


def test_p6_7_holds_self_denial_identity_split_and_blocks_identity_fact() -> None:
    held = build_structure_insight_p6_family_review(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        relation_family="self_denial_identity_split",
        self_understanding_observation_intent=True,
        self_understanding_uncertainty_boundary=True,
    )

    assert held["family_review_classification"] == FAMILY_REVIEW_HOLD
    assert held["summary"]["initial_auto_visible_allowed"] is False
    assert held["summary"]["self_denial_identity_split_not_initial_auto_visible"] is True
    assert REASON_SELF_DENIAL_IDENTITY_NOT_INITIAL_AUTO_VISIBLE in held["decision_reason_codes"]
    assert REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW in held["decision_reason_codes"]

    blocked = build_structure_insight_p6_family_review(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        relation_family="self_denial_identity_split",
        self_understanding_observation_intent=True,
        self_understanding_uncertainty_boundary=True,
        self_denial_identity_fact_required=True,
    )
    assert blocked["family_review_classification"] == FAMILY_REVIEW_BLOCK
    assert REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED in blocked["decision_reason_codes"]


def test_p6_7_blocks_target_judgement_risk() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        relation_family="value_line_crossed",
        self_understanding_observation_intent=True,
        self_understanding_uncertainty_boundary=True,
        target_judgement_risk=True,
    )

    assert review["family_review_classification"] == FAMILY_REVIEW_BLOCK
    assert REASON_TARGET_JUDGEMENT_RISK_BLOCKED in review["decision_reason_codes"]


def test_p6_7_blocks_structure_question_surface_plan_reuse() -> None:
    structure_question_plan = {
        "summary": {
            "family": "structure_question",
            "surface_plan_kind": "limited_structure_insight_seed",
            "limited_surface_candidate": True,
            "body_free": {"surface_body_included": False},
        }
    }
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=3,
        long_arc_summary_only=False,
        long_arc_relation_flow_present=True,
        p6_surface_role_plan=structure_question_plan,
    )

    assert review["family_review_classification"] == FAMILY_REVIEW_BLOCK
    assert review["summary"]["structure_question_surface_plan_reuse_blocked"] is True
    assert REASON_STRUCTURE_QUESTION_SURFACE_PLAN_REUSE_BLOCKED in review["decision_reason_codes"]


def test_p6_7_blocks_body_public_contract_or_template_meta() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=3,
        long_arc_summary_only=False,
        long_arc_relation_flow_present=True,
        family_review_meta={
            "comment_text": "body must not be present",
            "public_response_key_added": True,
            "fixed_sentence_template_added": True,
        },
    )

    assert review["family_review_classification"] == FAMILY_REVIEW_BLOCK
    assert "comment_text_body_detected" in review["decision_reason_codes"]
    assert "public_contract_mutation_detected" in review["decision_reason_codes"]
    assert "fixed_sentence_template_detected" in review["decision_reason_codes"]


def test_p6_7_public_summary_stays_body_free() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=3,
        long_arc_summary_only=False,
        long_arc_relation_flow_present=True,
    )
    dumped = dump_structure_insight_p6_family_review_public_summary(review)
    loaded = json.loads(dumped)

    assert loaded["family_review_classification"] == FAMILY_REVIEW_ALLOW
    assert loaded["initial_auto_visible_allowed"] is False
    assert loaded["public_contract"]["public_response_key_added"] is False
    assert _contains_forbidden_raw_key(loaded) is False


def test_p6_7_contract_rejects_body_or_release_flags() -> None:
    review = build_structure_insight_p6_family_review(
        family=FAMILY_LONG_MEANING_ARC,
        relation_family="long_arc_multiple_core",
        long_arc_core_count=3,
        long_arc_summary_only=False,
        long_arc_relation_flow_present=True,
    )
    leaked = dict(review)
    leaked["surface_text"] = "leak"
    with pytest.raises(ValueError):
        assert_structure_insight_p6_family_review_contract(leaked)

    released = dict(review)
    released["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_structure_insight_p6_family_review_contract(released)
