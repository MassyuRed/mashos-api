# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
from emlis_ai_structure_insight_p6_relation_policy import (
    P6_BLOCKED_RELATION_FAMILIES,
    P6_HIGH_RISK_RELATION_FAMILIES,
    P6_LOW_RISK_RELATION_FAMILIES,
    P6_MEDIUM_RISK_RELATION_FAMILIES,
    P6_META_ONLY_RELATION_FAMILIES,
    RISK_LEVEL_BLOCKED,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
    STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP,
    STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION,
    VISIBILITY_ALLOW_INITIAL_VISIBLE,
    VISIBILITY_BLOCKED,
    VISIBILITY_META_ONLY,
    VISIBILITY_REVIEW_REQUIRED,
    assert_structure_insight_p6_relation_policy_contract,
    build_structure_insight_p6_relation_policy,
    dump_structure_insight_p6_relation_policy_public_summary,
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


def _family_boundary() -> dict[str, Any]:
    return build_structure_insight_p6_family_boundary(
        family="structure_question",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        run_id="p6_relation_policy_family_boundary_source",
    )


def test_p6_3_low_risk_relations_are_initial_visible_candidates_after_family_boundary() -> None:
    for relation in P6_LOW_RISK_RELATION_FAMILIES:
        policy = build_structure_insight_p6_relation_policy(
            relation_family=relation,
            p6_family_boundary=_family_boundary(),
            run_id=f"p6_relation_low_{relation}",
        )
        summary = policy["summary"]

        assert policy["schema_version"] == STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION
        assert policy["step"] == STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP
        assert summary["schema_version"] == STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION
        assert policy["relation_family"] == relation
        assert policy["risk_level"] == RISK_LEVEL_LOW
        assert policy["visibility_decision"] == VISIBILITY_ALLOW_INITIAL_VISIBLE
        assert summary["allow_initial_visible"] is True
        assert summary["auto_visible_allowed"] is True
        assert summary["review_required"] is False
        assert summary["blocked"] is False
        assert "evidence_boundary_gate" in summary["gate_required"]
        assert "soft_inference_surface_gate" in summary["gate_required"]
        assert "diagnosis" in summary["forbidden_claims"]
        assert summary["release_allowed"] is False
        assert summary["public_contract"]["public_response_key_added"] is False
        assert summary["body_free"]["candidate_body_included"] is False
        assert _contains_forbidden_raw_key(policy) is False
        assert_structure_insight_p6_relation_policy_contract(policy)


def test_p6_3_medium_risk_relations_require_review_and_do_not_auto_visible() -> None:
    for relation in P6_MEDIUM_RISK_RELATION_FAMILIES:
        policy = build_structure_insight_p6_relation_policy(relation_family=relation)
        summary = policy["summary"]

        assert policy["risk_level"] == RISK_LEVEL_MEDIUM
        assert policy["visibility_decision"] == VISIBILITY_REVIEW_REQUIRED
        assert summary["review_required"] is True
        assert summary["auto_visible_allowed"] is False
        assert "p6_relation_policy_review_gate" in summary["gate_required"]
        assert any(reason.startswith("medium_risk_relation_review_required") for reason in summary["decision_reason_codes"])


def test_p6_3_high_risk_relations_require_review_and_block_auto_visible() -> None:
    for relation in P6_HIGH_RISK_RELATION_FAMILIES:
        policy = build_structure_insight_p6_relation_policy(relation_family=relation)
        summary = policy["summary"]

        assert policy["risk_level"] == RISK_LEVEL_HIGH
        assert policy["visibility_decision"] == VISIBILITY_REVIEW_REQUIRED
        assert summary["review_required"] is True
        assert summary["auto_visible_allowed"] is False
        assert summary["high_risk_auto_visible_blocked"] is True
        assert "high_risk_relation_auto_visible_blocked" in summary["decision_reason_codes"]

    self_denial = build_structure_insight_p6_relation_policy(relation_family="self_denial_identity_split")
    assert self_denial["summary"]["self_denial_identity_review_required"] is True
    assert "self_denial_identity_review_required" in self_denial["summary"]["decision_reason_codes"]


def test_p6_3_blocked_relations_do_not_become_p6_visible_and_keep_separate_reasons() -> None:
    for relation in P6_BLOCKED_RELATION_FAMILIES:
        policy = build_structure_insight_p6_relation_policy(relation_family=relation)
        summary = policy["summary"]

        assert policy["risk_level"] == RISK_LEVEL_BLOCKED
        assert policy["visibility_decision"] == VISIBILITY_BLOCKED
        assert summary["blocked"] is True
        assert summary["auto_visible_allowed"] is False
        assert any(reason.startswith("blocked_relation_family") for reason in summary["decision_reason_codes"])

    low_info = build_structure_insight_p6_relation_policy(relation_family="low_information_unspecified_weight")
    assert low_info["summary"]["low_information_visible_blocked"] is True
    assert "low_information_visible_blocked" in low_info["summary"]["decision_reason_codes"]

    target = build_structure_insight_p6_relation_policy(relation_family="target_judgement_agreement")
    assert target["summary"]["target_judgement_blocked"] is True
    assert "target_judgement_blocked" in target["summary"]["decision_reason_codes"]

    period = build_structure_insight_p6_relation_policy(relation_family="period_tendency_from_single_record")
    assert period["summary"]["period_tendency_single_record_blocked"] is True

    dictionary = build_structure_insight_p6_relation_policy(relation_family="user_dictionary_fact_claim")
    assert dictionary["summary"]["user_dictionary_fact_claim_blocked"] is True


def test_p6_3_history_fact_relation_is_meta_only_not_initial_visible() -> None:
    for relation in P6_META_ONLY_RELATION_FAMILIES:
        policy = build_structure_insight_p6_relation_policy(relation_family=relation)
        summary = policy["summary"]

        assert policy["visibility_decision"] == VISIBILITY_META_ONLY
        assert summary["meta_only"] is True
        assert summary["auto_visible_allowed"] is False
        assert summary["history_fact_line_meta_only"] is True
        assert "history_fact_line_as_insight_meta_only" in summary["decision_reason_codes"]


def test_p6_3_unknown_or_missing_relation_stays_meta_only_without_expanding_initial_set() -> None:
    missing = build_structure_insight_p6_relation_policy()
    assert missing["summary"]["visibility_decision"] == VISIBILITY_META_ONLY
    assert "relation_family_missing" in missing["summary"]["decision_reason_codes"]

    unknown = build_structure_insight_p6_relation_policy(relation_family="new_unreviewed_relation")
    assert unknown["summary"]["visibility_decision"] == VISIBILITY_META_ONLY
    assert "relation_family_not_in_initial_p6_set:new_unreviewed_relation" in unknown["summary"]["decision_reason_codes"]


def test_p6_3_family_boundary_can_demote_low_risk_relation_to_meta_only() -> None:
    no_connect_boundary = build_structure_insight_p6_family_boundary(
        family="low_information",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
    )
    policy = build_structure_insight_p6_relation_policy(
        relation_family="desire_blockage_conflict",
        p6_family_boundary=no_connect_boundary,
    )

    assert policy["summary"]["visibility_decision"] == VISIBILITY_META_ONLY
    assert policy["summary"]["auto_visible_allowed"] is False
    assert "p6_family_boundary_not_allowing_surface" in policy["summary"]["decision_reason_codes"]


def test_p6_3_blocks_low_info_overread_self_denial_fact_gate_bypass_and_pre_gate_body_generation() -> None:
    policy = build_structure_insight_p6_relation_policy(
        relation_family="desire_blockage_conflict",
        low_information_overread_risk=True,
        target_judgement_required=True,
        self_denial_identity_fact_required=True,
        period_tendency_required=True,
        user_dictionary_fact_claim_required=True,
        gate_required_bypassed=True,
        pre_gate_body_generated=True,
    )
    reasons = policy["summary"]["decision_reason_codes"]

    assert policy["summary"]["visibility_decision"] == VISIBILITY_BLOCKED
    assert "low_information_overread_blocked" in reasons
    assert "target_judgement_blocked" in reasons
    assert "self_denial_identity_fact_blocked" in reasons
    assert "period_tendency_from_single_record_blocked" in reasons
    assert "user_dictionary_fact_claim_blocked" in reasons
    assert "gate_required_bypassed" in reasons
    assert "body_generated_before_gate" in reasons


def test_p6_3_public_summary_is_body_free_and_does_not_expose_source_packets_or_release() -> None:
    dumped = dump_structure_insight_p6_relation_policy_public_summary(
        build_structure_insight_p6_relation_policy(relation_family="desire_blockage_conflict")
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION
    assert parsed["risk_level"] == RISK_LEVEL_LOW
    assert parsed["visibility_decision"] == VISIBILITY_ALLOW_INITIAL_VISIBLE
    assert parsed["public_response_key_added"] is False
    assert parsed["response_shape_changed"] is False
    assert parsed["raw_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["candidate_body_included"] is False
    assert parsed["release_allowed"] is False
    assert '"relation_meta"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_test_output"' not in dumped
    assert _contains_forbidden_raw_key(parsed) is False
    assert_structure_insight_p6_relation_policy_contract(parsed, allow_partial=True)


def test_p6_3_contract_rejects_raw_payload_keys_release_and_public_contract_mutation() -> None:
    with pytest.raises(ValueError):
        assert_structure_insight_p6_relation_policy_contract({"comment_text": "must not leak"}, allow_partial=True)
    with pytest.raises(ValueError):
        assert_structure_insight_p6_relation_policy_contract({"release_allowed": True}, allow_partial=True)

    clean = build_structure_insight_p6_relation_policy(relation_family="desire_blockage_conflict")
    contract = dict(clean)
    contract["summary"] = {
        **clean["summary"],
        "public_contract": dict(clean["summary"]["public_contract"], response_shape_changed=True),
    }
    with pytest.raises(ValueError):
        assert_structure_insight_p6_relation_policy_contract(contract)
