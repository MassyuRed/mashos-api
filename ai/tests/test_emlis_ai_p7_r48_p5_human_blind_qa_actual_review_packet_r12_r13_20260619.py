# -*- coding: utf-8 -*-
"""R48 R12/R13 P5 confirmed-candidate gate and no body-free leak guard."""

from __future__ import annotations

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48


def _r10_r11_freeze() -> dict:
    freeze = r48.build_p7_r48_r10_r11_disposal_handoff_summary_freeze()
    assert r48.assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(freeze)
    return freeze


def _case_rows() -> list[dict]:
    r6_r7_freeze = r48.build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    matrix = r6_r7_freeze["r4_r5_reviewer_packet_schema_freeze"]["r2_r3_local_storage_case_matrix_freeze"]["p5_case_matrix"]
    rows: list[dict] = []
    for row in matrix["case_rows"]:
        merged = dict(row)
        merged["review_session_id"] = matrix["review_session_id"]
        rows.append(merged)
    assert len(rows) == 24
    return rows


def _passing_result() -> dict:
    return {
        "axis_scores": {axis: 1.0 for axis in r48.P5_HUMAN_BLIND_QA_RATING_AXES},
        "verdict": "PASS",
        "sanitized_reason_ids": [],
        "blocker_ids": [],
        "reviewer_free_text_included": False,
    }


def _passing_rating_rows(*, body_removed: bool = True) -> list[dict]:
    return [
        r48.normalize_p7_r48_p5_rating_row_bodyfree(
            review_result=_passing_result(),
            case_row=case_row,
            reviewer_ref="local_reviewer_a",
            reviewed_at="2026-06-19T00-00-00Z",
            body_removed=body_removed,
        )
        for case_row in _case_rows()
    ]


def _verified_receipt() -> dict:
    return r48.build_p7_r48_p5_disposal_receipt_bodyfree(
        case_count=24,
        deleted_file_count=48,
        disposal_status="DISPOSAL_VERIFIED",
        body_removed=True,
        reviewer_notes_removed=True,
        purge_started_at="2026-06-19T00-00-00Z",
        purge_completed_at="2026-06-19T00-01-00Z",
    )


def _passing_summary() -> dict:
    summary = r48.build_p7_r48_p5_review_handoff_summary_bodyfree(
        rating_rows=_passing_rating_rows(body_removed=True),
        blocker_rows=[],
        execution_blocker_rows=[],
        disposal_receipt=_verified_receipt(),
        review_session_status="FINALIZED",
        case_count=24,
    )
    assert summary["p5_human_blind_qa_confirmed_candidate"] is True
    return summary


def test_r0_to_r11_existing_freeze_is_present_before_r12_r13() -> None:
    freeze = _r10_r11_freeze()

    assert freeze["disposal_receipt_builder_ready"] is True
    assert freeze["p5_review_handoff_summary_builder_ready"] is True
    assert freeze["next_required_step"] == "R12_p5_confirmed_candidate_gate"
    assert freeze["actual_review_handoff_summary_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False


def test_r12_confirmed_candidate_gate_policy_requires_coverage_blocker_and_disposal() -> None:
    policy = r48.build_p7_r48_p5_confirmed_candidate_gate_policy(r10_r11_freeze=_r10_r11_freeze())

    assert r48.assert_p7_r48_p5_confirmed_candidate_gate_policy_contract(policy)
    assert policy["p5_confirmed_candidate_gate_ready"] is True
    assert policy["rating_only_confirmation_allowed"] is False
    assert policy["body_removed_required"] is True
    assert policy["reviewer_notes_removed_required"] is True
    assert policy["disposal_verified_required"] is True
    assert policy["red_or_repair_open_allowed"] is False
    assert policy["boundary_violation_allowed"] is False
    assert policy["open_execution_blocker_allowed"] is False
    assert policy["body_hash_allowed"] is False
    assert policy["actual_p5_confirmed_candidate_gate_materialized_here"] is False
    assert policy["next_required_step"] == "R13_r47_regression_no_body_free_leak_guard"
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False


def test_r12_gate_passes_only_as_candidate_and_keeps_actual_release_closed() -> None:
    gate = r48.build_p7_r48_p5_confirmed_candidate_gate_bodyfree(handoff_summary=_passing_summary())

    assert r48.assert_p7_r48_p5_confirmed_candidate_gate_bodyfree_contract(gate)
    assert set(gate) == set(r48.P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS)
    assert gate["p5_confirmed_candidate_gate_passed"] is True
    assert gate["p5_human_blind_qa_confirmed_candidate"] is True
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert gate["missing_requirement_refs"] == []
    assert gate["failed_requirement_count"] == 0
    assert gate["p5_human_blind_qa_confirmed"] is False
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert gate["actual_human_review_run_here"] is False
    assert gate["actual_body_full_packet_generated_here"] is False
    assert gate["release_allowed"] is False
    assert gate["p7_complete"] is False
    assert gate["p8_start_allowed"] is False
    assert gate["hold004_close_allowed"] is False


def test_r12_gate_rejects_body_not_removed_and_missing_disposal_from_candidate() -> None:
    receipt = r48.build_p7_r48_p5_disposal_receipt_bodyfree(
        case_count=24,
        deleted_file_count=0,
        disposal_status="RATINGS_EXTRACTED",
        body_removed=False,
        reviewer_notes_removed=False,
    )
    summary = r48.build_p7_r48_p5_review_handoff_summary_bodyfree(
        rating_rows=_passing_rating_rows(body_removed=False),
        blocker_rows=[],
        execution_blocker_rows=[],
        disposal_receipt=receipt,
        review_session_status="FINALIZED",
        case_count=24,
    )

    gate = r48.build_p7_r48_p5_confirmed_candidate_gate_bodyfree(handoff_summary=summary)

    assert gate["p5_confirmed_candidate_gate_passed"] is False
    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert "body_removed" in gate["missing_requirement_refs"]
    assert "reviewer_notes_removed" in gate["missing_requirement_refs"]
    assert "disposal_verified_for_candidate" in gate["missing_requirement_refs"]
    assert gate["p5_human_blind_qa_confirmed"] is False
    assert gate["release_allowed"] is False


def test_r12_gate_rejects_red_repair_boundary_and_execution_blockers() -> None:
    case_row = _case_rows()[0]
    blocker = r48.build_p7_r48_p5_blocker_row_bodyfree(
        case_row=case_row,
        blocker_id="p5_free_tier_history_boundary_violation",
        blocker_kind="READFEEL_RED",
        blocker_status="OPEN",
        sanitized_reason_ids=["reason_id_other_local_note_purged"],
        body_removed=True,
    )
    execution_blocker = r48.build_p7_r48_p5_execution_blocker_row_bodyfree(
        case_row=case_row,
        execution_blocker_id="review_timeout_unclassified",
        execution_blocker_status="OPEN",
    )
    summary = r48.build_p7_r48_p5_review_handoff_summary_bodyfree(
        rating_rows=_passing_rating_rows(body_removed=True),
        blocker_rows=[blocker],
        execution_blocker_rows=[execution_blocker],
        disposal_receipt=_verified_receipt(),
        review_session_status="FINALIZED",
        case_count=24,
    )

    gate = r48.build_p7_r48_p5_confirmed_candidate_gate_bodyfree(handoff_summary=summary)

    assert gate["p5_confirmed_candidate_gate_passed"] is False
    assert "open_readfeel_blockers_zero" in gate["missing_requirement_refs"]
    assert "open_execution_blockers_zero" in gate["missing_requirement_refs"]
    assert "boundary_violation_blockers_zero" in gate["missing_requirement_refs"]
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False


def test_r13_policy_requires_r47_regression_without_claiming_execution() -> None:
    r12 = r48.build_p7_r48_p5_confirmed_candidate_gate_policy()
    policy = r48.build_p7_r48_r47_regression_no_body_free_leak_guard(r12_policy=r12)

    assert r48.assert_p7_r48_r47_regression_no_body_free_leak_guard_contract(policy)
    assert policy["r47_policy_ready_required"] is True
    assert policy["r47_target_regression_required"] is True
    assert tuple(policy["r47_target_regression_test_refs"]) == r48.P7_R48_R47_TARGET_REGRESSION_TEST_REFS
    assert policy["r47_target_regression_executed_here"] is False
    assert policy["no_body_free_leak_guard_ready"] is True
    assert policy["reviewer_packet_payload_bodyfree_allowed"] is False
    assert policy["reviewer_notes_bodyfree_allowed"] is False
    assert policy["body_hash_bodyfree_allowed"] is False
    assert policy["local_absolute_path_bodyfree_allowed"] is False
    assert policy["next_required_step"] == "R14_r46_handoff_regression"


def test_r13_no_body_free_leak_guard_accepts_summary_and_rejects_body_surface_keys() -> None:
    summary = _passing_summary()
    assert r48.assert_p7_r48_no_body_free_leak_guard_bodyfree_material(summary, source="passing_summary")

    leaked = dict(summary)
    leaked["returned_emlis_surface"] = "body payload must not be retained"
    with pytest.raises(ValueError, match="local-only reviewer packet|body payload|body hash|local path"):
        r48.assert_p7_r48_no_body_free_leak_guard_bodyfree_material(leaked, source="leaked_summary")


def test_r13_no_body_free_leak_guard_rejects_reviewer_packet_payload_even_without_raw_body() -> None:
    with pytest.raises(ValueError, match="local-only reviewer packet|body payload"):
        r48.assert_p7_r48_no_body_free_leak_guard_bodyfree_material(
            {
                "body_free": True,
                "reviewer_packet": {
                    "blind_case_id": "p7r48-p5-bqa-s000-001",
                    "local_only": True,
                    "must_not_export": True,
                },
            },
            source="bodyfree_with_reviewer_packet",
        )


def test_r12_r13_combined_freeze_keeps_review_p5_p6_release_closed_and_points_to_r14() -> None:
    freeze = r48.build_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze(r10_r11_freeze=_r10_r11_freeze())

    assert r48.assert_p7_r48_r12_r13_confirmed_gate_leak_guard_freeze_contract(freeze)
    assert freeze["p5_confirmed_candidate_gate_ready"] is True
    assert freeze["no_body_free_leak_guard_ready"] is True
    assert freeze["r47_target_regression_required"] is True
    assert freeze["r47_target_regression_executed_here"] is False
    assert freeze["actual_no_body_free_leak_scan_executed_here"] is False
    assert freeze["next_required_step"] == "R14_r46_handoff_regression"
    assert freeze["p5_human_blind_qa_confirmed_candidate"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
