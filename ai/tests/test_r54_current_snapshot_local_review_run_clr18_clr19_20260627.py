# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR18-CLR19 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr16_clr17_20260627 as clr17
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr18_clr19_20260627 as clr


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
    material = clr17.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_ready_clr15(rows),
    )
    assert clr17.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(material) is True
    return material


def _ready_clr17(rows: list[dict[str, Any]] | None = None, *, clr15_material: dict[str, Any] | None = None) -> dict[str, Any]:
    op16 = clr17.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=clr15_material or _ready_clr15(rows),
    )
    receipt = clr17.build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol(op16)
    material = clr17.build_p7_r54_clr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        disposal_receipt=receipt,
    )
    assert clr17.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True
    return material


def _ready_clr18(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    guard = _ready_clr15(rows)
    material = clr.build_p7_r54_clr18_bodyfree_post_review_summary(
        purge_disposal_receipt=_ready_clr17(clr15_material=guard),
        rating_question_consistency_guard=guard,
    )
    assert clr.assert_p7_r54_clr18_bodyfree_post_review_summary_contract(material) is True
    return material


def test_r54_clr00_to_clr17_are_present_before_clr18_clr19() -> None:
    material = _ready_clr17()

    assert tuple(material["implemented_steps"]) == clr17.P7_R54_CLR17_IMPLEMENTED_STEPS
    assert material["purge_disposal_receipt_status"] == clr17.P7_R54_CLR17_DISPOSAL_VERIFIED_STATUS_REF
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["body_free_post_review_summary_allowed_next"] is True
    assert material["next_required_step"] == clr.P7_R54_CLR18_STEP_REF


def test_r54_clr18_default_blocks_without_ready_inputs() -> None:
    material = clr.build_p7_r54_clr18_bodyfree_post_review_summary()

    assert set(material) == set(clr.P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR18_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR18_STEP_REF
    assert material["bodyfree_post_review_summary_status"] == clr.P7_R54_CLR18_SUMMARY_BLOCKED_STATUS_REF
    assert "clr17_disposal_receipt_missing_for_bodyfree_summary" in material["summary_blocker_ids"]
    assert "clr15_rating_question_consistency_guard_missing_for_bodyfree_summary" in material["summary_blocker_ids"]
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR18_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr18_bodyfree_post_review_summary_contract(material) is True


def test_r54_clr18_ready_summarizes_rating_question_disposal_bodyfree() -> None:
    material = _ready_clr18()

    assert set(material) == set(clr.P7_R54_CLR18_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS)
    assert material["bodyfree_post_review_summary_status"] == clr.P7_R54_CLR18_SUMMARY_READY_STATUS_REF
    assert material["bodyfree_post_review_summary_ref"] == clr.P7_R54_CLR18_SUMMARY_REF
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["verdict_counts"] == {"PASS": 24}
    assert material["overall_read_feeling_counts"] == {"felt_record_returned_as_line": 24}
    assert material["below_target_axis_count"] == 0
    assert material["open_readfeel_blocker_count"] == 0
    assert material["open_execution_blocker_count"] == 0
    assert material["primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert material["disposal_verified"] is True
    assert material["body_removed"] is True
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["p5_decision_candidate_separation_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR19_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
        },
    )
    assert clr.assert_p7_r54_clr18_bodyfree_post_review_summary_contract(material) is True


def test_r54_clr19_confirmed_candidate_is_candidate_only_not_final_or_release() -> None:
    material = clr.build_p7_r54_clr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_ready_clr18(),
    )

    assert set(material) == set(clr.P7_R54_CLR19_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS)
    assert material["decision_candidate_separation_status"] == clr.P7_R54_CLR19_DECISION_SEPARATION_READY_STATUS_REF
    assert material["p5_decision_candidate_ref"] == clr.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR20_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
        },
    )
    assert clr.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True


def test_r54_clr19_p5_repair_return_uses_classified_summary_not_p8_escape() -> None:
    rows = _ready_rows()
    rows[0]["verdict"] = "YELLOW"
    rows[0]["overall_read_feeling_ref"] = "felt_generic_or_shallow"
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["axis_scores"] = dict(rows[0]["axis_scores"])
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.75
    guard = _ready_clr15(rows)
    receipt = _ready_clr17(clr15_material=guard)
    summary = clr.build_p7_r54_clr18_bodyfree_post_review_summary(
        purge_disposal_receipt=receipt,
        rating_question_consistency_guard=guard,
    )
    material = clr.build_p7_r54_clr19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)

    assert summary["bodyfree_post_review_summary_status"] == clr.P7_R54_CLR18_SUMMARY_READY_STATUS_REF
    assert summary["p5_decision_candidate_separation_allowed_next"] is True
    assert summary["verdict_counts"]["YELLOW"] == 1
    assert summary["below_target_axis_count"] == 1
    assert summary["open_readfeel_blocker_count"] == 1
    assert material["p5_decision_candidate_ref"] == clr.P7_R54_CLR19_P5_REPAIR_RETURN_REF
    assert material["p5_repair_return_required"] is True
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    assert any(ref.startswith("yellow_verdict_present") for ref in material["p5_decision_repair_reason_refs"])
    assert clr.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True


def test_r54_clr19_not_question_repair_stays_p5_repair_return() -> None:
    rows = _ready_rows()
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    guard = _ready_clr15(rows)
    receipt = _ready_clr17(clr15_material=guard)
    summary = clr.build_p7_r54_clr18_bodyfree_post_review_summary(
        purge_disposal_receipt=receipt,
        rating_question_consistency_guard=guard,
    )
    material = clr.build_p7_r54_clr19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)

    assert summary["not_question_repair_required_count"] == 1
    assert summary["p8_material_candidate_row_count"] == 0
    assert material["p5_decision_candidate_ref"] == clr.P7_R54_CLR19_P5_REPAIR_RETURN_REF
    assert material["p5_repair_return_required"] is True
    assert material["p8_start_allowed"] is False
    assert clr.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True


def test_r54_clr19_explicit_current_only_issue_routes_to_p4_r12_not_p5_confirmed() -> None:
    material = clr.build_p7_r54_clr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_ready_clr18(),
        p4_current_only_surface_issue_refs=["p4_current_surface_repair_required"],
    )

    assert material["p5_decision_candidate_ref"] == clr.P7_R54_CLR19_P4_R12_TARGETED_REPAIR_REF
    assert material["p4_r12_targeted_current_only_surface_repair_required"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR19_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF
    assert clr.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True


def test_r54_clr18_rejects_question_text_payload_from_clr15_input() -> None:
    guard = _ready_clr15()
    mutated = deepcopy(guard)
    mutated["question_observation_rows"][0]["question_text"] = "forbidden"

    with pytest.raises(ValueError):
        clr.build_p7_r54_clr18_bodyfree_post_review_summary(
            purge_disposal_receipt=_ready_clr17(clr15_material=guard),
            rating_question_consistency_guard=mutated,
        )


def test_r54_clr19_default_blocks_without_clr18_summary() -> None:
    material = clr.build_p7_r54_clr19_p5_decision_candidate_separation()

    assert material["decision_candidate_separation_status"] == clr.P7_R54_CLR19_DECISION_SEPARATION_BLOCKED_STATUS_REF
    assert material["p5_decision_candidate_ref"] == clr.P7_R54_CLR19_INCONCLUSIVE_REF
    assert material["p5_decision_candidate_materialized_here"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True
