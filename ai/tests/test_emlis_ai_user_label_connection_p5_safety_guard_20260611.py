# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_safety_guard import (
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_WARN,
    USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP,
    assert_user_label_connection_p5_safety_guard_contract,
    build_user_label_connection_p5_safety_guard,
    user_label_connection_p5_safety_guard_public_summary,
)
from test_emlis_ai_user_label_connection_p5_surface_role_plan_20260611 import _plan

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


def _guard(**overrides: Any) -> dict[str, Any]:
    args = {
        "p5_surface_role_plan": _plan(run_id="p5_4_role_plan_source"),
        "guard_signal_meta": {},
        "run_id": "p5_4_safety_guard",
    }
    args.update(overrides)
    return build_user_label_connection_p5_safety_guard(**args)


def test_p5_4_allows_only_clean_ready_p5_3_role_plan_without_generating_visible_body() -> None:
    guard = _guard(run_id="p5_4_allow_clean_role_plan_test")

    assert guard["schema_version"] == USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION
    assert guard["step"] == USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP
    assert guard["decision"] == DECISION_ALLOW
    assert guard["allow_limited_visible_candidate"] is True
    assert guard["hold_for_product_quality_qa"] is False
    assert guard["blocked"] is False
    assert guard["rejection_reasons"] == []
    assert guard["risk_summary"] == {
        "creepy_risk_detected": False,
        "overclaim_risk_detected": False,
        "self_blame_amplification_detected": False,
        "period_tendency_from_single_record_detected": False,
        "always_claim_detected": False,
        "cause_claim_detected": False,
        "personality_or_diagnosis_claim_detected": False,
        "future_prediction_detected": False,
        "advice_or_should_statement_detected": False,
        "target_judgement_agreement_detected": False,
        "history_masks_current_input_gap": False,
        "safety_or_self_denial_context_detected": False,
    }
    assert guard["role_plan"]["surface_plan_kind"] == "limited_history_line_observation"
    assert guard["role_plan"]["role_plan_ready"] is True
    assert guard["guard_contract"]["wording_repair_allowed"] is False
    assert guard["guard_contract"]["gate_relaxation_allowed"] is False
    assert guard["fixed_sentence_template_added"] is False
    assert guard["comment_text_generated_by_this_layer"] is False
    assert guard["visible_text_generated"] is False
    assert guard["visible_surface_connected"] is False
    assert guard["runtime_change_applied"] is False
    assert guard["public_contract"]["response_shape_changed"] is False
    assert guard["public_contract"]["public_response_key_added"] is False
    assert guard["body_free"]["raw_text_included"] is False
    assert guard["body_free"]["surface_body_included"] is False
    assert _contains_forbidden_raw_key(guard) is False
    assert_user_label_connection_p5_safety_guard_contract(guard)


def test_p5_4_warns_when_p5_3_is_meta_only_or_review_required_without_hard_risk() -> None:
    review_plan = _plan(
        p5_eligibility_matrix=__import__(
            "test_emlis_ai_user_label_connection_p5_eligibility_matrix_20260611"
        )._matrix(
            edge_meta={
                "edge_family": "state_output_attachment",
                "evidence_record_count": 2,
                "current_record_included": True,
                "evidence_point_ids": ["current:present", "history:owned:001"],
            },
            run_id="p5_4_review_required_eligibility_source",
        ),
        run_id="p5_4_review_required_role_plan_source",
    )
    guard = _guard(
        p5_surface_role_plan=review_plan,
        run_id="p5_4_review_required_warn_test",
    )

    assert guard["decision"] == DECISION_WARN
    assert guard["allow_limited_visible_candidate"] is False
    assert guard["hold_for_product_quality_qa"] is True
    assert guard["blocked"] is False
    assert "p5_surface_role_plan_not_ready" in guard["rejection_reasons"]
    assert_user_label_connection_p5_safety_guard_contract(guard)


def test_p5_4_blocks_if_p5_3_role_plan_is_blocked() -> None:
    blocked_plan = _plan(
        requested_roles=["advice"],
        run_id="p5_4_blocked_role_plan_source",
    )
    guard = _guard(
        p5_surface_role_plan=blocked_plan,
        run_id="p5_4_blocked_role_plan_test",
    )

    assert guard["decision"] == DECISION_BLOCK
    assert guard["blocked"] is True
    assert "p5_surface_role_plan_blocked" in guard["rejection_reasons"]
    assert "p5_surface_role_plan_not_ready" in guard["rejection_reasons"]
    assert "p5_surface_role_plan:forbidden_role_detected" in guard["rejection_reasons"]
    assert_user_label_connection_p5_safety_guard_contract(guard)


def test_p5_4_blocks_creepy_overclaim_self_blame_and_quality_absence_risks() -> None:
    cases = [
        ({"creepy_risk": True}, "creepy_risk_detected", "creepy_risk_detected"),
        ({"overclaim_risk": True}, "overclaim_risk_detected", "overclaim_risk_detected"),
        ({"self_blame_amplification": True}, "self_blame_amplification_detected", "self_blame_amplification_detected"),
        ({"creepy_absence": 0.94}, "creepy_risk_detected", "creepy_risk_detected"),
        ({"overclaim_absence": 0.9}, "overclaim_risk_detected", "overclaim_risk_detected"),
        ({"self_blame_non_amplification": 0.8}, "self_blame_amplification_detected", "self_blame_amplification_detected"),
    ]
    for signal, reason, risk_key in cases:
        guard = _guard(guard_signal_meta=signal, run_id=f"p5_4_risk_{reason}")

        assert guard["decision"] == DECISION_BLOCK
        assert guard["blocked"] is True
        assert reason in guard["rejection_reasons"]
        assert guard["risk_summary"][risk_key] is True
        assert_user_label_connection_p5_safety_guard_contract(guard)


def test_p5_4_blocks_claims_history_masking_safety_and_target_judgement() -> None:
    cases = [
        ({"period_tendency_from_single_record": True}, "period_tendency_from_single_record"),
        ({"always_claim": True}, "always_claim_detected"),
        ({"cause_claim": True}, "cause_claim_detected"),
        ({"diagnosis_claim": True}, "personality_or_diagnosis_claim_detected"),
        ({"personality_claim": True}, "personality_or_diagnosis_claim_detected"),
        ({"future_prediction": True}, "future_prediction_detected"),
        ({"advice_claim": True}, "advice_or_should_statement_detected"),
        ({"should_statement": True}, "advice_or_should_statement_detected"),
        ({"target_judgement_agreement": True}, "target_judgement_agreement_detected"),
        ({"opponent_intent_claim": True}, "target_judgement_agreement_detected"),
        ({"history_line_masks_current_input_gap": True}, "history_masks_current_input_gap"),
        ({"safety_adjacent": True}, "safety_or_self_denial_context_detected"),
        ({"self_denial_context": True}, "safety_or_self_denial_context_detected"),
    ]
    for signal, reason in cases:
        guard = _guard(guard_signal_meta=signal, run_id=f"p5_4_claim_{reason}")

        assert guard["decision"] == DECISION_BLOCK
        assert guard["blocked"] is True
        assert reason in guard["rejection_reasons"]
        assert_user_label_connection_p5_safety_guard_contract(guard)


def test_p5_4_does_not_treat_policy_forbidden_role_list_as_detected_claims() -> None:
    plan = _plan(run_id="p5_4_policy_list_role_plan_source")
    guard = _guard(p5_surface_role_plan=plan, run_id="p5_4_policy_list_no_false_positive_test")

    assert "advice" in plan["must_not_include_roles"]
    assert "always_claim" in plan["must_not_include_roles"]
    assert guard["decision"] == DECISION_ALLOW
    assert guard["risk_summary"]["advice_or_should_statement_detected"] is False
    assert guard["risk_summary"]["always_claim_detected"] is False


def test_p5_4_detects_raw_payload_and_contract_mutation_without_leaking_bodies() -> None:
    raw = _guard(
        guard_signal_meta={"memo": "raw memo must not be retained"},
        run_id="p5_4_raw_payload_block_test",
    )
    assert raw["decision"] == DECISION_BLOCK
    assert "raw_text_payload_detected" in raw["rejection_reasons"]
    assert _contains_forbidden_raw_key(raw) is False
    assert_user_label_connection_p5_safety_guard_contract(raw)

    mutation = _guard(
        guard_signal_meta={"public_response_key_added": True},
        run_id="p5_4_contract_mutation_block_test",
    )
    assert mutation["decision"] == DECISION_BLOCK
    assert "contract_mutation_detected" in mutation["rejection_reasons"]
    assert_user_label_connection_p5_safety_guard_contract(mutation)


def test_p5_4_public_summary_is_body_free_and_contract_stable() -> None:
    guard = _guard(run_id="p5_4_public_summary_source")
    public_summary = user_label_connection_p5_safety_guard_public_summary(guard)
    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)

    assert public_summary["decision"] == DECISION_ALLOW
    assert public_summary["allow_limited_visible_candidate"] is True
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["raw_text_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["history_raw_text_included"] is False
    assert '"comment_text"' not in dumped
    assert '"surface_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"history_records"' not in dumped
    assert_user_label_connection_p5_safety_guard_contract(public_summary, allow_partial=True)


def test_p5_4_contract_guard_rejects_body_keys_and_forbidden_true_flags() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_safety_guard_contract(
            {"schema_version": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION, "text": "body"}
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_safety_guard_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP,
                "public_response_key_added": True,
            },
            allow_partial=True,
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_safety_guard_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP,
                "decision": DECISION_ALLOW,
                "allow_limited_visible_candidate": True,
                "risk_summary": {"creepy_risk_detected": True},
                "public_contract": {
                    "rn_visible_contract_changed": False,
                    "public_response_key_added": False,
                    "response_shape_changed": False,
                    "db_schema_changed": False,
                    "fixed_sentence_template_added": False,
                    "gate_relaxed": False,
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
