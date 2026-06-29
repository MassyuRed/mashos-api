# -*- coding: utf-8 -*-
"""R48 R10/R11 body-free disposal receipt and P5 review handoff contracts."""

from __future__ import annotations

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48


def _r8_r9_freeze() -> dict:
    freeze = r48.build_p7_r48_r8_r9_rating_blocker_rows_freeze()
    assert r48.assert_p7_r48_r8_r9_rating_blocker_rows_freeze_contract(freeze)
    return freeze


def _case_rows() -> list[dict]:
    # Use a fresh matrix from the established R6/R7 path so the test does not depend on body-full material.
    r6_r7_freeze = r48.build_p7_r48_r6_r7_materialization_notes_policy_freeze()
    p5_matrix = r6_r7_freeze["r4_r5_reviewer_packet_schema_freeze"]["r2_r3_local_storage_case_matrix_freeze"]["p5_case_matrix"]
    rows: list[dict] = []
    for row in p5_matrix["case_rows"]:
        merged = dict(row)
        merged["review_session_id"] = p5_matrix["review_session_id"]
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
    rows = []
    for case_row in _case_rows():
        rows.append(
            r48.normalize_p7_r48_p5_rating_row_bodyfree(
                review_result=_passing_result(),
                case_row=case_row,
                reviewer_ref="local_reviewer_a",
                reviewed_at="2026-06-19T00-00-00Z",
                body_removed=body_removed,
            )
        )
    return rows


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


def test_r0_to_r9_existing_freeze_is_present_before_r10_r11() -> None:
    freeze = _r8_r9_freeze()

    assert freeze["rating_row_normalizer_ready"] is True
    assert freeze["blocker_row_builder_ready"] is True
    assert freeze["execution_blocker_row_builder_ready"] is True
    assert freeze["next_required_step"] == "R10_disposal_receipt_builder"
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False


def test_r10_disposal_receipt_policy_is_bodyfree_and_points_to_r11() -> None:
    policy = r48.build_p7_r48_disposal_receipt_builder_policy(r8_r9_freeze=_r8_r9_freeze())

    assert r48.assert_p7_r48_disposal_receipt_builder_policy_contract(policy)
    assert policy["disposal_receipt_builder_ready"] is True
    assert policy["body_free_disposal_receipt_required_before_p5_confirmed"] is True
    assert policy["body_hash_allowed"] is False
    assert policy["local_absolute_path_included"] is False
    assert policy["deleted_body_preview_allowed"] is False
    assert policy["actual_disposal_run_here"] is False
    assert policy["actual_disposal_receipt_materialized_here"] is False
    assert policy["next_required_step"] == "R11_p5_review_handoff_summary_builder"
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["hold004_close_allowed"] is False


def test_r10_disposal_receipt_requires_body_removed_notes_removed_and_no_hash_or_export() -> None:
    receipt = _verified_receipt()

    assert r48.assert_p7_r48_p5_disposal_receipt_bodyfree_contract(receipt)
    assert set(receipt) == set(r48.P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert receipt["schema_version"] == r48.P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert receipt["disposal_status"] == "DISPOSAL_VERIFIED"
    assert receipt["body_removed"] is True
    assert receipt["reviewer_notes_removed"] is True
    assert receipt["local_packet_exported"] is False
    assert receipt["content_hash_of_body_stored"] is False
    assert receipt["p7_material_body_free"] is True
    assert receipt["body_free"] is True

    with pytest.raises(ValueError, match="requires body and reviewer notes removed"):
        r48.build_p7_r48_p5_disposal_receipt_bodyfree(
            case_count=24,
            deleted_file_count=1,
            disposal_status="DISPOSAL_VERIFIED",
            body_removed=True,
            reviewer_notes_removed=False,
        )


def test_r10_disposal_receipt_rejects_body_hash_local_path_and_deleted_preview() -> None:
    base = dict(_verified_receipt())
    for forbidden_key in ("body_content_hash", "local_absolute_path", "deleted_body_preview", "raw_input"):
        payload = dict(base)
        payload[forbidden_key] = "must_not_survive"
        with pytest.raises(ValueError, match="body hash|local path|deleted preview|body payload"):
            r48.build_p7_r48_p5_disposal_receipt_bodyfree(disposal_result=payload)


def test_r11_handoff_summary_policy_is_bodyfree_and_does_not_open_release() -> None:
    policy = r48.build_p7_r48_p5_review_handoff_summary_builder_policy()

    assert r48.assert_p7_r48_p5_review_handoff_summary_builder_policy_contract(policy)
    assert policy["case_coverage_aggregated"] is True
    assert policy["axis_averages_aggregated"] is True
    assert policy["open_blockers_aggregated"] is True
    assert policy["disposal_status_checked"] is True
    assert policy["p5_human_blind_qa_confirmed_candidate_calculated"] is True
    assert policy["p6_limited_human_readfeel_start_allowed_candidate_calculated"] is True
    assert policy["rating_only_confirmation_allowed"] is False
    assert policy["actual_human_review_run_here"] is False
    assert policy["actual_review_handoff_summary_materialized_here"] is False
    assert policy["release_allowed"] is False
    assert policy["p7_complete"] is False
    assert policy["p8_start_allowed"] is False
    assert policy["next_required_step"] == "R12_p5_confirmed_candidate_gate"


def test_r11_handoff_summary_defaults_to_not_confirmed_without_review_rows() -> None:
    summary = r48.build_p7_r48_p5_review_handoff_summary_bodyfree(
        disposal_receipt=_verified_receipt(),
        review_session_status="FINALIZED",
    )

    assert r48.assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(summary)
    assert set(summary) == set(r48.P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS)
    assert summary["reviewed_case_count"] == 0
    assert summary["family_coverage_satisfied"] is False
    assert summary["axis_targets_satisfied"] is False
    assert summary["p5_human_blind_qa_confirmed_candidate"] is False
    assert summary["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert summary["release_allowed"] is False
    assert all(value is None for value in summary["axis_averages"].values())


def test_r11_handoff_summary_can_calculate_p5_candidate_only_after_coverage_ratings_and_disposal() -> None:
    summary = r48.build_p7_r48_p5_review_handoff_summary_bodyfree(
        rating_rows=_passing_rating_rows(body_removed=True),
        blocker_rows=[],
        execution_blocker_rows=[],
        disposal_receipt=_verified_receipt(),
        review_session_status="FINALIZED",
        case_count=24,
    )

    assert r48.assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(summary)
    assert summary["reviewed_case_count"] == 24
    assert summary["family_coverage_satisfied"] is True
    assert summary["axis_targets_satisfied"] is True
    assert summary["open_blocker_ids"] == []
    assert summary["open_execution_blocker_ids"] == []
    assert summary["boundary_violation_blocker_ids"] == []
    assert summary["disposal_verified_for_candidate"] is True
    assert summary["p5_human_blind_qa_confirmed_candidate"] is True
    assert summary["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert summary["release_allowed"] is False
    assert summary["p7_complete"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["hold004_close_allowed"] is False


def test_r11_handoff_summary_keeps_open_blocker_and_execution_blocker_separate_from_candidate() -> None:
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

    assert r48.assert_p7_r48_p5_review_handoff_summary_bodyfree_contract(summary)
    assert summary["p5_human_blind_qa_confirmed_candidate"] is False
    assert "p5_free_tier_history_boundary_violation" in summary["open_blocker_ids"]
    assert "review_timeout_unclassified" in summary["open_execution_blocker_ids"]
    assert "p5_free_tier_history_boundary_violation" in summary["boundary_violation_blocker_ids"]
    assert summary["release_allowed"] is False


def test_r10_r11_combined_freeze_keeps_review_closed_and_points_to_r12() -> None:
    freeze = r48.build_p7_r48_r10_r11_disposal_handoff_summary_freeze(r8_r9_freeze=_r8_r9_freeze())

    assert r48.assert_p7_r48_r10_r11_disposal_handoff_summary_freeze_contract(freeze)
    assert freeze["disposal_receipt_builder_ready"] is True
    assert freeze["p5_review_handoff_summary_builder_ready"] is True
    assert freeze["r10_disposal_receipt_schema_fixed"] is True
    assert freeze["r11_handoff_summary_schema_fixed"] is True
    assert freeze["next_required_step"] == "R12_p5_confirmed_candidate_gate"
    assert freeze["actual_disposal_run_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False
    assert freeze["actual_review_handoff_summary_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["p5_human_blind_qa_confirmed_candidate"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
