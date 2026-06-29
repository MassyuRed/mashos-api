# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR16-CLR17 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr16_clr17_20260627 as clr


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "local_path",
    "local_absolute_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)


def _assert_bodyfree_no_touch(material: dict[str, Any], *, allowed_true_false_flags: set[str] | None = None) -> None:
    allowed = allowed_true_false_flags or set()
    assert material["body_free"] is True
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if key in allowed:
            assert material[key] is True, key
        else:
            assert material[key] is False, key
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_clr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _ready_clr09() -> dict[str, Any]:
    form = clr09.build_p7_r54_clr09_reviewer_selection_form_freeze()
    assert clr09.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form) is True
    return form


def _completed_clr10() -> dict[str, Any]:
    form = _ready_clr09()
    receipt = clr11.build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form(
        reviewer_selection_form_freeze=form,
        reviewer_ref_ids=["r54-local-reviewer-bodyfree-ref-001"],
    )
    material = clr11.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=form,
        local_human_review_operation_receipt=receipt,
    )
    assert clr11.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True
    return material


def _ready_rows(op10: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return clr11.build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion(op10 or _completed_clr10())


def _ready_clr11(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    op10 = _completed_clr10()
    material = clr11.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=rows or _ready_rows(op10),
    )
    assert clr11.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True
    return material


def _ready_clr12(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr13.build_p7_r54_clr12_rating_row_normalization(
        sanitized_review_result_row_intake=_ready_clr11(rows),
    )
    assert clr13.assert_p7_r54_clr12_rating_row_normalization_contract(material) is True
    return material


def _ready_clr13(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr13.build_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=_ready_clr12(rows),
    )
    assert clr13.assert_p7_r54_clr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True
    return material


def _ready_clr14(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr15.build_p7_r54_clr14_question_need_observation_normalization(
        readfeel_blocker_execution_blocker_ingestion=_ready_clr13(rows),
    )
    assert clr15.assert_p7_r54_clr14_question_need_observation_normalization_contract(material) is True
    return material


def _ready_clr15(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr15.build_p7_r54_clr15_rating_question_consistency_guard(
        question_need_observation_normalization=_ready_clr14(rows),
    )
    assert clr15.assert_p7_r54_clr15_rating_question_consistency_guard_contract(material) is True
    return material


def _ready_clr16(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_ready_clr15(rows),
    )
    assert clr.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True
    return material


def _verified_receipt(op16: dict[str, Any]) -> dict[str, Any]:
    return clr.build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol(op16)


def test_r54_clr00_to_clr15_are_present_before_clr16_clr17() -> None:
    material = _ready_clr15()

    assert tuple(material["implemented_steps"]) == clr15.P7_R54_CLR15_IMPLEMENTED_STEPS
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["ready_for_pause_abort_expiration_protocol"] is True
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR16_STEP_REF


def test_r54_clr16_default_blocks_without_ready_clr15() -> None:
    material = clr.build_p7_r54_clr16_pause_abort_expiration_protocol()

    assert set(material) == set(clr.P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR16_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR16_STEP_REF
    assert material["pause_abort_expiration_protocol_status"] == clr.P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF
    assert "clr15_consistency_guard_not_ready_for_pause_abort_expiration_protocol" in material["execution_blocker_ids"]
    assert material["ready_for_purge_disposal_receipt"] is False
    assert material["purge_disposal_receipt_allowed_next"] is False
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR16_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True


def test_r54_clr16_ready_routes_to_disposal_receipt_bodyfree() -> None:
    material = _ready_clr16()

    assert set(material) == set(clr.P7_R54_CLR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert material["pause_abort_expiration_protocol_status"] == clr.P7_R54_CLR16_PROTOCOL_READY_STATUS_REF
    assert material["pause_abort_expiration_protocol_ref"] == clr.P7_R54_CLR16_PROTOCOL_REF
    assert material["pause_abort_expiration_protocol_reason_refs"] == [clr.P7_R54_CLR16_READY_REASON_REF]
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["ready_for_purge_disposal_receipt"] is True
    assert material["purge_disposal_receipt_allowed_next"] is True
    assert material["handoff_allowed_before_purge"] is False
    assert material["r52_reintake_handoff_allowed_before_purge"] is False
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR16_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR17_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        },
    )
    assert clr.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True


def test_r54_clr16_paused_keeps_no_handoff_and_no_disposal_next() -> None:
    material = clr.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_ready_clr15(),
        review_operation_status_ref=clr11.P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF,
    )

    assert material["pause_abort_expiration_protocol_status"] == clr.P7_R54_CLR16_PROTOCOL_PAUSED_STATUS_REF
    assert material["review_paused_without_handoff"] is True
    assert material["ready_for_purge_disposal_receipt"] is False
    assert material["purge_disposal_receipt_allowed_next"] is False
    assert material["handoff_allowed_before_purge"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR16_PAUSED_NEXT_REQUIRED_STEP_REF
    assert clr.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True


def test_r54_clr16_aborted_expired_and_incomplete_route_to_disposal_receipt() -> None:
    for status_ref, expected_status in (
        (clr11.P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF, clr.P7_R54_CLR16_PROTOCOL_ABORTED_STATUS_REF),
        (clr11.P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF, clr.P7_R54_CLR16_PROTOCOL_EXPIRED_STATUS_REF),
        ("rating_incomplete_purge_required", clr.P7_R54_CLR16_PROTOCOL_RATING_INCOMPLETE_STATUS_REF),
    ):
        material = clr.build_p7_r54_clr16_pause_abort_expiration_protocol(
            rating_question_consistency_guard=_ready_clr15(),
            review_operation_status_ref=status_ref,
        )
        assert material["pause_abort_expiration_protocol_status"] == expected_status
        assert material["ready_for_purge_disposal_receipt"] is True
        assert material["p5_inconclusive_direction_only_not_decision_materialized"] is True
        assert material["p5_decision_materialized_here"] is False
        assert material["next_required_step"] == clr.P7_R54_CLR17_STEP_REF
        assert clr.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True


def test_r54_clr16_consistency_guard_blocked_with_rows_still_routes_to_purge_not_p8() -> None:
    rows = _ready_rows()
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True
    guard = _ready_clr15(rows)
    assert guard["rating_question_consistency_guard_status"] == clr15.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF

    material = clr.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=guard,
    )

    assert material["pause_abort_expiration_protocol_status"] == clr.P7_R54_CLR16_PROTOCOL_BLOCKED_STATUS_REF
    assert material["blocked_by_consistency_guard_requires_purge"] is True
    assert material["ready_for_purge_disposal_receipt"] is True
    assert material["p5_decision_direction_ref"] == "p5_or_emlis_repair_required_later_not_p8_material"
    assert "r54_clr15_not_question_repair_not_p8_material" in material["upstream_consistency_issue_ids"]
    assert material["next_required_step"] == clr.P7_R54_CLR17_STEP_REF
    assert clr.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True


def test_r54_clr17_default_blocks_without_ready_clr16() -> None:
    material = clr.build_p7_r54_clr17_purge_disposal_receipt()

    assert set(material) == set(clr.P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR17_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR17_STEP_REF
    assert material["purge_disposal_receipt_status"] == clr.P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF
    assert "pause_abort_expiration_protocol_not_ready_for_disposal_receipt" in material["execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["body_free_post_review_summary_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR17_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True


def test_r54_clr17_verified_receipt_allows_bodyfree_summary_next() -> None:
    op16 = _ready_clr16()
    receipt = _verified_receipt(op16)
    material = clr.build_p7_r54_clr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        disposal_receipt=receipt,
    )

    assert set(material) == set(clr.P7_R54_CLR17_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["purge_disposal_receipt_status"] == clr.P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF
    assert material["purge_disposal_receipt_ref"] == clr.P7_R54_CLR17_DISPOSAL_RECEIPT_REF
    assert material["purge_disposal_receipt_reason_refs"] == [clr.P7_R54_CLR17_READY_REASON_REF]
    assert material["received_receipt_has_only_allowed_fields"] is True
    assert material["body_full_packet_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["temporary_form_removed"] is True
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["disposal_verified"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["actual_disposal_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_post_review_summary_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR17_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR18_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
        },
    )
    assert clr.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True


def test_r54_clr17_blocks_missing_targets_export_and_body_hash_storage() -> None:
    op16 = _ready_clr16()
    material = clr.build_p7_r54_clr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        body_full_packet_removed=True,
        reviewer_notes_removed=False,
        temporary_form_removed=True,
        local_packet_exported=True,
        content_hash_of_body_stored=True,
        disposal_verified=True,
        disposal_operation_ref=clr.P7_R54_CLR17_DISPOSAL_RECEIPT_REF,
        disposal_verified_at_ref="r54_clr17_disposal_verified_at_bodyfree_ref_20260627",
    )

    assert material["purge_disposal_receipt_status"] == clr.P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF
    assert "reviewer_notes_not_removed" in material["disposal_execution_blocker_ids"]
    assert "local_packet_exported_during_disposal" in material["disposal_execution_blocker_ids"]
    assert "content_hash_of_body_stored_during_disposal" in material["disposal_execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["body_free_post_review_summary_allowed_next"] is False
    assert clr.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True


def test_r54_clr17_rejects_forbidden_body_fields_in_receipt() -> None:
    op16 = _ready_clr16()
    receipt = _verified_receipt(op16)
    receipt["local_path"] = "path_like/forbidden"

    with pytest.raises(ValueError):
        clr.build_p7_r54_clr17_purge_disposal_receipt(
            pause_abort_expiration_protocol=op16,
            disposal_receipt=receipt,
        )


def test_r54_clr17_does_not_echo_path_like_or_hash_like_receipt_values() -> None:
    op16 = _ready_clr16()
    material = clr.build_p7_r54_clr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        body_full_packet_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        disposal_verified=True,
        disposal_operation_ref="path_like/disposal_ref",
        disposal_verified_at_ref="a" * 64,
    )

    assert material["purge_disposal_receipt_status"] == clr.P7_R54_CLR17_DISPOSAL_BLOCKED_STATUS_REF
    assert material["disposal_operation_ref"] == ""
    assert material["disposal_verified_at_ref"] == ""
    assert "path_like/disposal_ref" not in str(material)
    assert "a" * 64 not in str(material)
    assert clr.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True
