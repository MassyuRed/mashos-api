# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR22-CLR23 contract tests."""

from __future__ import annotations

from typing import Any

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr16_clr17_20260627 as clr17
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr18_clr19_20260627 as clr19
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr20_clr21_20260627 as clr21
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr22_clr23_20260627 as clr


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


def _ready_clr17(rows: list[dict[str, Any]] | None = None, *, clr15_material: dict[str, Any] | None = None) -> dict[str, Any]:
    op16 = clr17.build_p7_r54_clr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=clr15_material or _ready_clr15(rows),
    )
    assert clr17.assert_p7_r54_clr16_pause_abort_expiration_protocol_contract(op16) is True
    receipt = clr17.build_p7_r54_clr17_bodyfree_verified_disposal_receipt_from_protocol(op16)
    material = clr17.build_p7_r54_clr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=op16,
        disposal_receipt=receipt,
    )
    assert clr17.assert_p7_r54_clr17_purge_disposal_receipt_contract(material) is True
    return material


def _ready_clr18(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    guard = _ready_clr15(rows)
    material = clr19.build_p7_r54_clr18_bodyfree_post_review_summary(
        purge_disposal_receipt=_ready_clr17(clr15_material=guard),
        rating_question_consistency_guard=guard,
    )
    assert clr19.assert_p7_r54_clr18_bodyfree_post_review_summary_contract(material) is True
    return material


def _ready_clr19(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr19.build_p7_r54_clr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_ready_clr18(rows),
    )
    assert clr19.assert_p7_r54_clr19_p5_decision_candidate_separation_contract(material) is True
    return material


def _ready_clr20(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr21.build_p7_r54_clr20_p6_candidate_only_handoff(
        p5_decision_candidate_separation=_ready_clr19(rows),
    )
    assert clr21.assert_p7_r54_clr20_p6_candidate_only_handoff_contract(material) is True
    return material


def _ready_clr21(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr21.build_p7_r54_clr21_p8_material_candidate_only_handoff(
        p6_candidate_only_handoff=_ready_clr20(rows),
    )
    assert clr21.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(material) is True
    return material


def _ready_clr22(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    material = clr.build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=_ready_clr21(rows),
    )
    assert clr.assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    return material


def test_r54_clr00_to_clr21_are_present_before_clr22_clr23() -> None:
    material = _ready_clr21()

    assert tuple(material["implemented_steps"]) == clr21.P7_R54_CLR21_IMPLEMENTED_STEPS
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR22_STEP_REF


def test_r54_clr22_default_blocks_without_ready_clr21() -> None:
    material = clr.build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation()

    assert set(material) == set(clr.P7_R54_CLR22_FINAL_VALIDATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR22_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR22_STEP_REF
    assert material["final_validation_status"] == clr.P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF
    assert material["final_validation_passed"] is False
    assert material["r52_reintake_handoff_allowed_next"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR22_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_r54_clr22_ready_final_validation_does_not_promote_p5_p6_p8_release() -> None:
    material = _ready_clr22()

    assert set(material) == set(clr.P7_R54_CLR22_FINAL_VALIDATION_REQUIRED_FIELD_REFS)
    assert material["final_validation_status"] == clr.P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF
    assert material["final_validation_passed"] is True
    assert material["r52_reintake_handoff_allowed_next"] is True
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR23_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={key for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if material.get(key) is True},
    )
    assert clr.assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_r54_clr22_blocks_body_or_question_leak_evidence_without_exporting_body() -> None:
    material = clr.build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=_ready_clr21(),
        validation_evidence={"raw_input": "do-not-export", "question_text_included": True},
    )

    assert material["final_validation_status"] == clr.P7_R54_CLR22_BODY_LEAK_OR_QUESTION_TEXT_BLOCKED_STATUS_REF
    assert material["body_leak_or_question_text_violation_detected"] is True
    assert material["body_leak_violation_count"] >= 1
    assert material["question_text_violation_count"] >= 1
    assert material["r52_reintake_handoff_allowed_next"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "raw_input" not in material
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_r54_clr22_blocks_no_touch_violation() -> None:
    material = clr.build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=_ready_clr21(),
        validation_evidence={"api_changed": True},
    )

    assert material["final_validation_status"] == clr.P7_R54_CLR22_NO_TOUCH_BLOCKED_STATUS_REF
    assert material["no_touch_violation_detected"] is True
    assert material["no_touch_violation_count"] >= 1
    assert material["final_validation_passed"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True


def test_r54_clr23_default_blocks_without_ready_clr22() -> None:
    material = clr.build_p7_r54_clr23_r52_reintake_handoff()

    assert set(material) == set(clr.P7_R54_CLR23_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR23_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR23_STEP_REF
    assert material["handoff_status"] == clr.P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_evidence_handoff_materialized_here"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR23_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr23_r52_reintake_handoff_contract(material) is True


def test_r54_clr23_ready_r52_reintake_handoff_is_bodyfree_and_not_release() -> None:
    material = clr.build_p7_r54_clr23_r52_reintake_handoff(final_validation=_ready_clr22())

    assert set(material) == set(clr.P7_R54_CLR23_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS)
    assert material["handoff_status"] == clr.P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_bodyfree_receipts"] is True
    assert material["body_free_evidence_handoff_materialized_here"] is True
    assert material["handoff_evidence_ref_count"] == len(material["handoff_evidence_refs"])
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_candidate_only"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_design_material_candidate_only_not_start"] is True
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["p7_complete"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_manual_review_run_here"] is False
    assert material["r52_handoff_contains_body_full_packet"] is False
    assert material["r52_handoff_contains_question_text"] is False
    assert material["r52_handoff_contains_local_path"] is False
    assert material["r52_handoff_contains_payload_hash"] is False
    assert material["r52_handoff_contains_reviewer_free_text"] is False
    assert material["r52_handoff_contains_raw_payload"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR24_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={key for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if material.get(key) is True},
    )
    assert clr.assert_p7_r54_clr23_r52_reintake_handoff_contract(material) is True


def test_r54_clr23_blocks_when_clr22_reports_body_leak() -> None:
    bad_final_validation = clr.build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_only_handoff=_ready_clr21(),
        validation_evidence={"packet_content_included": True},
    )
    material = clr.build_p7_r54_clr23_r52_reintake_handoff(final_validation=bad_final_validation)

    assert material["handoff_status"] == clr.P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_evidence_handoff_materialized_here"] is False
    assert material["r52_reintake_handoff_ready"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr23_r52_reintake_handoff_contract(material) is True


def test_r54_clr23_keeps_historical_helper_refs_separate_from_current_basis() -> None:
    material = clr.build_p7_r54_clr23_r52_reintake_handoff(final_validation=_ready_clr22())

    assert material["actual_review_basis_refs"] == clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["operation_current_refs"] == clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["existing_op23_current_refs_are_historical_here"] is True
    assert material["existing_ev21_current_refs_are_historical_here"] is True
    assert material["existing_op23_reused_as_actual_r52_handoff_basis"] is False
    assert material["existing_ev21_reused_as_actual_r52_handoff_basis"] is False
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["operation_current_refs_used_as_actual_review_basis"] is True
