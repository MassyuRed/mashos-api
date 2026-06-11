# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_entry_freeze import (
    DECISION_P4_RETURN_REQUIRED,
    DECISION_P5_RETURN_REQUIRED,
    DECISION_P6_ENTRY_ALLOWED,
    DECISION_P6_ENTRY_HOLD,
    STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP,
    STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION,
    assert_structure_insight_p6_entry_freeze_contract,
    build_structure_insight_p6_entry_freeze,
    dump_structure_insight_p6_entry_freeze_public_summary,
)
from emlis_ai_structure_insight_p6_inventory import build_structure_insight_p6_inventory


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


def _p5_7_handoff(**overrides: Any) -> dict[str, Any]:
    summary = {
        "schema_version": "cocolon.emlis.user_label_connection.p5_regression_handoff_summary.v1",
        "version": "cocolon.emlis.user_label_connection.p5_regression_handoff_summary.v1",
        "source": "test_p5_7_handoff",
        "step": "P5-7_Regression_P6HoldDecision",
        "run_id": "p5_7_summary",
        "p5_regression_handoff_created": True,
        "handoff_decision": "p6_ready",
        "p6_ready": True,
        "p6_hold": False,
        "p5_continue": False,
        "p4_return": False,
        "decision_reason_codes": [],
        "all_required_regression_green": True,
        "missing_required_regression_suites": [],
        "required_regression_blockers": [],
        "p5_limited_visible_connection_ready": True,
        "current_input_not_masked_by_history": True,
        "creepy_overclaim_self_blame_risk_not_increased": True,
        "p5_deep_insight_substitute_used": False,
        "p6_target_families": ["structure_question", "long_meaning_arc", "self_understanding_follow"],
        "p6_target_family_scope_limited": True,
        "p4_current_only_readfeel_preserved": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "public_release_applied": False,
        "release_allowed": False,
    }
    summary.update(overrides)
    return {"summary": summary}


def _inventory() -> dict[str, Any]:
    return build_structure_insight_p6_inventory(run_id="p6_entry_inventory_source")


def test_p6_0_allows_entry_only_when_p5_7_inventory_family_and_regressions_are_confirmed_body_free() -> None:
    freeze = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(),
        structure_insight_inventory=_inventory(),
        run_id="p6_entry_allowed_test",
    )
    summary = freeze["summary"]

    assert freeze["schema_version"] == STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SCHEMA_VERSION
    assert freeze["step"] == STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_STEP
    assert summary["schema_version"] == STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION
    assert summary["handoff_decision"] == DECISION_P6_ENTRY_ALLOWED
    assert summary["p6_entry_allowed"] is True
    assert summary["p6_entry_hold"] is False
    assert summary["p5_return_required"] is False
    assert summary["p4_return_required"] is False
    assert summary["p5_7_handoff_decision"] == "p6_ready"
    assert summary["all_required_regression_green"] is True
    assert summary["p5_limited_visible_connection_ready"] is True
    assert summary["current_input_not_masked_by_history"] is True
    assert summary["creepy_overclaim_self_blame_risk_not_increased"] is True
    assert summary["p5_deep_insight_substitute_used"] is False
    assert summary["p6_target_family_scope_limited"] is True
    assert summary["structure_insight_inventory_confirmed"] is True
    assert summary["release_allowed"] is False
    assert summary["public_contract"]["public_response_key_added"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(freeze) is False
    assert_structure_insight_p6_entry_freeze_contract(freeze)


def test_p6_0_holds_entry_when_inventory_or_family_scope_is_not_confirmed() -> None:
    no_inventory = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(),
        run_id="p6_entry_no_inventory_hold_test",
    )
    assert no_inventory["summary"]["handoff_decision"] == DECISION_P6_ENTRY_HOLD
    assert no_inventory["summary"]["p6_entry_hold"] is True
    assert "structure_insight_inventory_not_confirmed" in no_inventory["summary"]["p6_hold_material"]

    out_of_scope = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(),
        structure_insight_inventory=_inventory(),
        p6_candidate_families=["structure_question", "future_prediction"],
        run_id="p6_entry_family_hold_test",
    )
    assert out_of_scope["summary"]["handoff_decision"] == DECISION_P6_ENTRY_HOLD
    assert "p6_target_family_out_of_scope:future_prediction" in out_of_scope["summary"]["p6_hold_material"]


def test_p6_0_returns_to_p5_when_p5_limited_connection_or_risk_boundary_is_not_green() -> None:
    freeze = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(
            p5_limited_visible_connection_ready=False,
            current_input_not_masked_by_history=False,
            creepy_overclaim_self_blame_risk_not_increased=False,
            p5_deep_insight_substitute_used=True,
        ),
        structure_insight_inventory=_inventory(),
        run_id="p6_entry_p5_return_test",
    )
    summary = freeze["summary"]

    assert summary["handoff_decision"] == DECISION_P5_RETURN_REQUIRED
    assert summary["p5_return_required"] is True
    assert "p5_limited_visible_connection_not_ready" in summary["p5_return_material"]
    assert "current_input_masked_by_history" in summary["p5_return_material"]
    assert "creepy_overclaim_self_blame_risk_increased" in summary["p5_return_material"]
    assert "p5_deep_insight_substitute_risk" in summary["p5_return_material"]


def test_p6_0_returns_to_p4_when_current_only_readfeel_regression_is_not_preserved() -> None:
    freeze = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(
            handoff_decision="p4_return",
            p6_ready=False,
            p4_return=True,
            p4_current_only_readfeel_preserved=False,
        ),
        structure_insight_inventory=_inventory(),
        run_id="p6_entry_p4_return_test",
    )

    assert freeze["summary"]["handoff_decision"] == DECISION_P4_RETURN_REQUIRED
    assert freeze["summary"]["p4_return_required"] is True
    assert "p4_current_only_regression_not_preserved" in freeze["summary"]["p4_return_material"]


def test_p6_0_public_summary_is_body_free_and_does_not_expose_inventory_records_or_release() -> None:
    dumped = dump_structure_insight_p6_entry_freeze_public_summary(
        build_structure_insight_p6_entry_freeze(
            p5_7_regression_handoff=_p5_7_handoff(),
            structure_insight_inventory=_inventory(),
            run_id="p6_entry_public_summary_source",
        )
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == STRUCTURE_INSIGHT_P6_ENTRY_FREEZE_SUMMARY_SCHEMA_VERSION
    assert parsed["handoff_decision"] == DECISION_P6_ENTRY_ALLOWED
    assert parsed["public_response_key_added"] is False
    assert parsed["response_shape_changed"] is False
    assert parsed["raw_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["release_allowed"] is False
    assert '"module_records"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_test_output"' not in dumped
    assert _contains_forbidden_raw_key(parsed) is False
    assert_structure_insight_p6_entry_freeze_contract(parsed, allow_partial=True)


def test_p6_0_contract_rejects_raw_payload_keys_release_and_public_contract_mutation() -> None:
    with pytest.raises(ValueError):
        assert_structure_insight_p6_entry_freeze_contract({"comment_text": "must not leak"}, allow_partial=True)
    with pytest.raises(ValueError):
        assert_structure_insight_p6_entry_freeze_contract({"release_allowed": True}, allow_partial=True)

    clean = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(),
        structure_insight_inventory=_inventory(),
        run_id="p6_entry_contract_source",
    )
    contract = dict(clean)
    contract["summary"] = {
        **clean["summary"],
        "public_contract": dict(clean["summary"]["public_contract"], response_shape_changed=True),
    }
    with pytest.raises(ValueError):
        assert_structure_insight_p6_entry_freeze_contract(contract)


def test_p6_0_relation_policy_can_explicitly_hold_later_p6_steps_without_returning_to_p5_or_p4() -> None:
    freeze = build_structure_insight_p6_entry_freeze(
        p5_7_regression_handoff=_p5_7_handoff(),
        structure_insight_inventory=_inventory(),
        p6_relation_policy_fixed=False,
        run_id="p6_entry_relation_policy_hold_test",
    )

    assert freeze["summary"]["handoff_decision"] == DECISION_P6_ENTRY_HOLD
    assert freeze["summary"]["p6_entry_hold"] is True
    assert freeze["summary"]["p5_return_required"] is False
    assert freeze["summary"]["p4_return_required"] is False
    assert "p6_relation_policy_not_fixed" in freeze["summary"]["p6_hold_material"]
