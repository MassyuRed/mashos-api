# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_regression_handoff import (
    DECISION_P4_RETURN,
    DECISION_P5_RETURN,
    DECISION_P6_CONTINUE,
    DECISION_P7_HOLD,
    DECISION_P7_READY,
    REASON_LONG_RUN_SEQUENCE_NOT_EVALUATED,
    REASON_MANUAL_READ_FEEL_NOT_CONFIRMED,
    REASON_NO_CONNECT_FAMILY_REGRESSION_NOT_GREEN,
    REASON_P6_PRODUCT_QA_UNSAFE_CANDIDATE_PRESENT,
    REASON_PUBLIC_CONTRACT_MUTATION_DETECTED,
    REASON_RAW_TEXT_PAYLOAD_DETECTED,
    STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_STEP,
    assert_structure_insight_p6_regression_handoff_contract,
    build_structure_insight_p6_regression_handoff,
    dump_structure_insight_p6_regression_handoff_public_summary,
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
    "reviewer_note",
    "reviewer_notes",
    "reviewer_free_text",
    "blind_qa_free_text",
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


def _green_statuses() -> list[dict[str, Any]]:
    return [
        {"suite_id": "p6_new_tests", "status": "passed", "passed": True},
        {"suite_id": "structure_insight_existing_tests", "status": "passed", "passed": True},
        {"suite_id": "p5_regression_handoff_tests", "status": "passed", "passed": True},
        {"suite_id": "p5_limited_visible_connection_tests", "status": "passed", "passed": True},
        {"suite_id": "p5_product_quality_review_tests", "status": "passed", "passed": True},
        {"suite_id": "p4_regression_handoff_tests", "status": "passed", "passed": True},
        {"suite_id": "product_readfeel_p4_tests", "status": "passed", "passed": True},
        {"suite_id": "public_feedback_meta_tests", "status": "passed", "passed": True},
        {"suite_id": "display_contract_tests", "status": "passed", "passed": True},
        {"suite_id": "two_stage_reception_e2e", "status": "passed", "passed": True},
        {"suite_id": "rn_contract_tests", "status": "passed", "passed": True},
        {"suite_id": "free_tier_boundary_tests", "status": "passed", "passed": True},
        {"suite_id": "low_information_boundary_tests", "status": "passed", "passed": True},
        {"suite_id": "no_raw_text_meta_tests", "status": "passed", "passed": True},
        {"suite_id": "no_connect_family_regression", "status": "passed", "passed": True},
    ]


def _entry() -> dict[str, Any]:
    return {
        "summary": {
            "p6_entry_allowed": True,
            "p6_entry_hold": False,
            "p5_return_required": False,
            "p4_return_required": False,
            "p4_current_only_readfeel_preserved": True,
            "p5_limited_visible_connection_ready": True,
            "current_input_not_masked_by_history": True,
            "creepy_overclaim_self_blame_risk_not_increased": True,
            "p5_deep_insight_substitute_used": False,
            "decision_reason_codes": [],
        }
    }


def _family_boundary() -> dict[str, Any]:
    return {"summary": {"decision": "allow_limited_surface", "allow_limited_surface": True, "block": False, "hold": False}}


def _relation_policy() -> dict[str, Any]:
    return {
        "summary": {
            "visibility_decision": "allow_initial_visible",
            "allow_initial_visible": True,
            "blocked": False,
            "decision_reason_codes": [],
        }
    }


def _gate() -> dict[str, Any]:
    return {"summary": {"passed": True, "blocked": False, "decision_reason_codes": []}}


def _surface_plan() -> dict[str, Any]:
    return {
        "summary": {
            "surface_plan_kind": "limited_structure_insight_seed",
            "limited_surface_candidate": True,
            "gate_passed": True,
            "planned_insight_seed_count": 1,
            "decision_reason_codes": [],
        }
    }


def _family_review(family: str = "long_meaning_arc") -> dict[str, Any]:
    return {"summary": {"family": family, "family_review_classification": "allow", "decision_reason_codes": []}}


def _product_quality_ready() -> dict[str, Any]:
    return {
        "summary": {
            "review_count": 2,
            "structure_insight_ready_candidate_count": 1,
            "unsafe_candidate_count": 0,
            "weak_candidate_count": 0,
            "p7_long_run_field_candidate_count": 1,
            "p7_long_run_field_candidates": [
                {
                    "case_id": "ready-structure-question",
                    "family": "structure_question",
                    "relation_family": "desire_blockage_conflict",
                    "surface_role": "observation_insight_seed",
                    "verdict": "STRUCTURE_INSIGHT_READY",
                    "qa_bucket": "ready",
                    "rating_numbers": {"read_feeling": 0.94, "insight_delta": 0.9},
                    "safe_reason_codes": [],
                    "body_free": {"comment_text_body_included": False},
                    "public_contract": {"public_response_key_added": False},
                }
            ],
            "blocker_reason_codes": [],
            "release_allowed": False,
        }
    }


def _base_kwargs() -> dict[str, Any]:
    return {
        "p6_entry_freeze": _entry(),
        "p6_family_boundary": _family_boundary(),
        "p6_relation_policy": _relation_policy(),
        "p6_gate_hardening": _gate(),
        "p6_surface_role_plan": _surface_plan(),
        "p6_family_review": _family_review(),
        "p6_product_quality_review": _product_quality_ready(),
        "regression_statuses": _green_statuses(),
        "p7_review_meta": {
            "long_meaning_arc_reviewed": True,
            "self_understanding_follow_reviewed": True,
            "long_run_sequence_evaluated": True,
            "manual_read_feel_confirmed": True,
        },
    }


def test_p6_9_all_green_ready_material_goes_to_p7_without_release_flag() -> None:
    report = build_structure_insight_p6_regression_handoff(**_base_kwargs(), run_id="p6_9_ready")
    summary = report["summary"]

    assert report["schema_version"] == STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_SCHEMA_VERSION
    assert report["step"] == STRUCTURE_INSIGHT_P6_REGRESSION_HANDOFF_STEP
    assert report["decision"] == DECISION_P7_READY
    assert summary["p7_ready"] is True
    assert summary["p7_handoff_ready"] is True
    assert summary["release_allowed"] is False
    assert summary["public_contract"]["public_response_key_added"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(report) is False
    assert_structure_insight_p6_regression_handoff_contract(report)


def test_p6_9_holds_p7_when_manual_or_long_run_review_is_missing() -> None:
    kwargs = _base_kwargs()
    kwargs["p7_review_meta"] = {
        "long_meaning_arc_reviewed": True,
        "self_understanding_follow_reviewed": True,
        "long_run_sequence_evaluated": False,
        "manual_read_feel_confirmed": False,
    }
    report = build_structure_insight_p6_regression_handoff(**kwargs)

    assert report["decision"] == DECISION_P7_HOLD
    assert REASON_LONG_RUN_SEQUENCE_NOT_EVALUATED in report["summary"]["p7_hold_material"]
    assert REASON_MANUAL_READ_FEEL_NOT_CONFIRMED in report["summary"]["p7_hold_material"]
    assert report["summary"]["release_allowed"] is False


def test_p6_9_continues_p6_when_product_quality_has_unsafe_candidate() -> None:
    kwargs = _base_kwargs()
    kwargs["p6_product_quality_review"] = {
        "summary": {
            "review_count": 1,
            "structure_insight_ready_candidate_count": 0,
            "unsafe_candidate_count": 1,
            "weak_candidate_count": 0,
            "p7_long_run_field_candidate_count": 0,
            "blocker_reason_codes": ["self_denial_identity_fact_blocked"],
            "release_allowed": False,
        }
    }
    report = build_structure_insight_p6_regression_handoff(**kwargs)

    assert report["decision"] == DECISION_P6_CONTINUE
    assert REASON_P6_PRODUCT_QA_UNSAFE_CANDIDATE_PRESENT in report["summary"]["p6_continue_material"]
    assert report["summary"]["p7_ready"] is False


def test_p6_9_returns_to_p5_when_current_input_is_masked_or_body_leaks() -> None:
    kwargs = _base_kwargs()
    entry = _entry()
    entry["summary"]["current_input_not_masked_by_history"] = False
    kwargs["p6_entry_freeze"] = entry
    kwargs["p6_product_quality_review"] = {**_product_quality_ready(), "raw_text": "must not be retained"}
    report = build_structure_insight_p6_regression_handoff(**kwargs)

    assert report["decision"] == DECISION_P5_RETURN
    assert REASON_RAW_TEXT_PAYLOAD_DETECTED in report["summary"]["p5_return_material"]
    assert "must not be retained" not in json.dumps(report, ensure_ascii=False)


def test_p6_9_returns_to_p5_on_public_contract_mutation() -> None:
    kwargs = _base_kwargs()
    kwargs["p6_surface_role_plan"] = {**_surface_plan(), "public_response_key_added": True}
    report = build_structure_insight_p6_regression_handoff(**kwargs)

    assert report["decision"] == DECISION_P5_RETURN
    assert REASON_PUBLIC_CONTRACT_MUTATION_DETECTED in report["summary"]["p5_return_material"]


def test_p6_9_returns_to_p4_when_no_connect_regression_fails() -> None:
    kwargs = _base_kwargs()
    statuses = _green_statuses()
    for row in statuses:
        if row["suite_id"] == "no_connect_family_regression":
            row["status"] = "failed"
            row["passed"] = False
            row["failed_count"] = 1
    kwargs["regression_statuses"] = statuses
    report = build_structure_insight_p6_regression_handoff(**kwargs)

    assert report["decision"] == DECISION_P4_RETURN
    assert REASON_NO_CONNECT_FAMILY_REGRESSION_NOT_GREEN in report["summary"]["p4_return_material"]


def test_p6_9_public_summary_stays_body_free() -> None:
    report = build_structure_insight_p6_regression_handoff(**_base_kwargs())
    dumped = dump_structure_insight_p6_regression_handoff_public_summary(report)
    loaded = json.loads(dumped)

    assert loaded["decision"] == DECISION_P7_READY
    assert loaded["release_allowed"] is False
    assert _contains_forbidden_raw_key(loaded) is False


def test_p6_9_contract_rejects_body_and_release_flags() -> None:
    report = build_structure_insight_p6_regression_handoff(**_base_kwargs())
    leaked = dict(report)
    leaked["surface_text"] = "leak"
    with pytest.raises(ValueError):
        assert_structure_insight_p6_regression_handoff_contract(leaked)

    released = dict(report)
    released["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_structure_insight_p6_regression_handoff_contract(released)
