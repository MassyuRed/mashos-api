# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_next_decision_handoff_ledger import (
    BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT,
    BRANCH_B_DISPLAY_GREEN_LINEAGE_YELLOW,
    BRANCH_C_DISPLAY_RED_BODY_FREE_LEAK_REPAIR_RETURN,
    BRANCH_D_DISPLAY_RED_GATE_RELAXATION_REPAIR_RETURN,
    BRANCH_E_DISPLAY_RED_TEST_STALE_ONLY_RUNTIME_PUBLIC_META_CONSISTENT,
    P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION,
    assert_p7_r46_next_decision_handoff_ledger_contract,
    build_p7_r46_next_decision_handoff_ledger,
)

SECRET_INPUT = "R14 secret raw input must never enter next-decision ledger"
SECRET_SURFACE = "R14 secret returned surface must never enter next-decision ledger"
SECRET_REVIEWER = "R14 reviewer prose must never enter next-decision ledger"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_r14_branch_a_returns_to_p5_entry_without_release_or_p8_promotion() -> None:
    ledger = build_p7_r46_next_decision_handoff_ledger()
    assert_p7_r46_next_decision_handoff_ledger_contract(ledger)
    summary = ledger["next_decision_summary"]

    assert ledger["schema_version"] == P7_R46_NEXT_DECISION_HANDOFF_LEDGER_SCHEMA_VERSION
    assert ledger["current_phase"] == "P7"
    assert ledger["active_decision_branch"] == BRANCH_A_DISPLAY_GREEN_LINEAGE_CONSISTENT
    assert summary["display_decision_status"]["display_contract_green"] is True
    assert summary["display_decision_status"]["public_lineage_consistency_passed"] is True
    assert summary["display_decision_status"]["body_leak_detected"] is False
    assert summary["p5_return_status"]["formal_review_start_allowed"] is True
    assert summary["p6_return_status"]["formal_review_start_allowed"] is False
    assert ledger["ledger_entries"][0]["status"] == "READY"
    assert ledger["ledger_entries"][1]["status"] == "READY_AFTER_P5"
    assert ledger["actual_human_review_run_here"] is False
    assert ledger["actual_real_device_review_run_here"] is False
    assert summary["next_recommended_work_refs"][0] == "local_review_packet_storage_generation_disposal_policy"
    assert ledger["release_allowed"] is False
    assert ledger["p7_complete"] is False
    assert ledger["p8_start_allowed"] is False
    assert ledger["hold004_close_allowed"] is False
    assert "P7-HOLD-001" in ledger["unresolved_hold_refs"]
    assert "P7-HOLD-002" in ledger["unresolved_hold_refs"]
    assert "P7-HOLD-003" in ledger["unresolved_hold_refs"]
    assert "P7-HOLD-004" in ledger["unresolved_hold_refs"]
    assert "HOLD-DC-005" in ledger["unresolved_hold_refs"]
    assert ledger["body_free"] is True

    dumped = _dumped(ledger)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()


@pytest.mark.parametrize(
    ("display_status", "expected_branch", "expected_first_next"),
    [
        (
            {"display_contract_green": True, "public_lineage_consistent": False},
            BRANCH_B_DISPLAY_GREEN_LINEAGE_YELLOW,
            "public_meta_final_source_consistency_repair_before_human_review",
        ),
        (
            {"display_contract_green": False, "body_leak_detected": True},
            BRANCH_C_DISPLAY_RED_BODY_FREE_LEAK_REPAIR_RETURN,
            "body_free_leak_guard_repair_before_p5_p6_return",
        ),
        (
            {"display_contract_green": False, "gate_relaxation_detected": True},
            BRANCH_D_DISPLAY_RED_GATE_RELAXATION_REPAIR_RETURN,
            "gate_relaxation_repair_before_p5_p6_return",
        ),
        (
            {
                "display_contract_green": False,
                "test_expectation_stale_only": True,
                "runtime_public_meta_consistent": True,
            },
            BRANCH_E_DISPLAY_RED_TEST_STALE_ONLY_RUNTIME_PUBLIC_META_CONSISTENT,
            "display_contract_semantic_test_update",
        ),
    ],
)
def test_r14_branch_matrix_blocks_or_sequences_next_work_without_body_payload(
    display_status: dict[str, object], expected_branch: str, expected_first_next: str
) -> None:
    ledger = build_p7_r46_next_decision_handoff_ledger(display_contract_status=display_status)
    assert_p7_r46_next_decision_handoff_ledger_contract(ledger)
    summary = ledger["next_decision_summary"]

    assert ledger["active_decision_branch"] == expected_branch
    assert summary["next_recommended_work_refs"][0] == expected_first_next
    assert ledger["release_allowed"] is False
    assert ledger["p7_complete"] is False
    assert ledger["p8_start_allowed"] is False
    assert ledger["hold004_close_allowed"] is False
    assert ledger["actual_human_review_run_here"] is False
    assert ledger["actual_real_device_review_run_here"] is False
    if expected_branch in {
        BRANCH_B_DISPLAY_GREEN_LINEAGE_YELLOW,
        BRANCH_C_DISPLAY_RED_BODY_FREE_LEAK_REPAIR_RETURN,
        BRANCH_D_DISPLAY_RED_GATE_RELAXATION_REPAIR_RETURN,
    }:
        assert summary["p5_return_status"]["formal_review_start_allowed"] is False
        assert summary["p6_return_status"]["formal_review_start_allowed"] is False
        assert ledger["ledger_entries"][0]["status"] == "BLOCKED"

    dumped = _dumped(ledger)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"gate_relaxed": true' not in dumped.lower()


def test_r14_builders_reject_body_payload_or_contract_mutation_inputs() -> None:
    with pytest.raises(ValueError):
        build_p7_r46_next_decision_handoff_ledger(
            display_contract_status={
                "display_contract_green": True,
                "raw_input": SECRET_INPUT,
                "comment_text": SECRET_SURFACE,
                "reviewer_free_text": SECRET_REVIEWER,
            }
        )

    with pytest.raises(ValueError):
        build_p7_r46_next_decision_handoff_ledger(
            display_contract_status={
                "display_contract_green": True,
                "public_response_key_added": True,
            }
        )


def test_r14_contract_rejects_false_completion_or_release_promotion() -> None:
    ledger = build_p7_r46_next_decision_handoff_ledger()
    ledger["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r46_next_decision_handoff_ledger_contract(ledger)

    ledger = build_p7_r46_next_decision_handoff_ledger()
    ledger["active_decision_branch"] = BRANCH_B_DISPLAY_GREEN_LINEAGE_YELLOW
    with pytest.raises(ValueError):
        assert_p7_r46_next_decision_handoff_ledger_contract(ledger)
