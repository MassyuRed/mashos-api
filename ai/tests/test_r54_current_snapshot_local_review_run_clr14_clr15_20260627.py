# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR14-CLR15 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr11
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr12_clr13_20260627 as clr13
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr


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
    material = clr.build_p7_r54_clr14_question_need_observation_normalization(
        readfeel_blocker_execution_blocker_ingestion=_ready_clr13(rows),
    )
    assert clr.assert_p7_r54_clr14_question_need_observation_normalization_contract(material) is True
    return material


def test_r54_clr00_to_clr13_are_present_before_clr14_clr15() -> None:
    material = _ready_clr13()

    assert tuple(material["implemented_steps"]) == clr13.P7_R54_CLR13_IMPLEMENTED_STEPS
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 0
    assert material["question_need_observation_normalization_allowed_next"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR14_STEP_REF


def test_r54_clr14_default_blocks_without_ready_clr13() -> None:
    material = clr.build_p7_r54_clr14_question_need_observation_normalization()

    assert set(material) == set(clr.P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR14_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR14_STEP_REF
    assert material["question_observation_normalization_status"] == clr.P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF
    assert "clr13_readfeel_blocker_execution_blocker_ingestion_not_ready_for_question_observation_normalization" in material["execution_blocker_ids"]
    assert material["question_observation_rows"] == []
    assert material["question_observation_row_count"] == 0
    assert material["rating_question_consistency_guard_allowed_next"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR14_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr14_question_need_observation_normalization_contract(material) is True


def test_r54_clr14_question_need_observation_normalization_ready_bodyfree() -> None:
    material = _ready_clr14()

    assert set(material) == set(clr.P7_R54_CLR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["question_observation_normalization_status"] == clr.P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    assert material["question_observation_normalization_ref"] == clr.P7_R54_CLR14_QUESTION_OBSERVATION_NORMALIZATION_REF
    assert material["question_observation_normalization_reason_refs"] == [clr.P7_R54_CLR14_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["question_observation_row_ref_count"] == 24
    assert material["case_ref_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert material["p8_material_candidate_allowed_row_count"] == 0
    assert material["not_question_repair_required_count"] == 0
    assert material["insufficient_material_execution_blocker_count"] == 0
    assert material["question_text_absent_for_all_rows"] is True
    assert material["draft_question_text_absent_for_all_rows"] is True
    assert material["question_text_or_draft_text_saved_here"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR15_STEP_REF
    for row in material["question_observation_rows"]:
        assert set(row) == set(clr.P7_R54_CLR14_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
        assert row["question_observation_row_is_bodyfree"] is True
        assert row["question_text_included"] is False
        assert row["draft_question_text_included"] is False
        assert row["p8_implementation_spec_finalized_here"] is False
        assert row["body_free"] is True
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        },
    )
    assert clr.assert_p7_r54_clr14_question_need_observation_normalization_contract(material) is True


def test_r54_clr14_counts_p8_material_candidate_as_material_only_not_implementation() -> None:
    rows = _ready_rows()
    rows[0]["question_need_primary_class"] = "question_may_reduce_overread_risk"
    rows[0]["one_question_fit_ref"] = "fits_one_question"
    rows[0]["ambiguity_kind_refs"] = ["missing_target"]
    rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True

    material = _ready_clr14(rows)
    row = material["question_observation_rows"][0]

    assert row["p8_material_candidate_requested"] is True
    assert row["p8_material_candidate_allowed"] is True
    assert row["p8_material_candidate_safe_for_handoff"] is True
    assert row["p8_implementation_spec_finalized_here"] is False
    assert material["p8_material_candidate_requested_row_count"] == 1
    assert material["p8_material_candidate_allowed_row_count"] == 1
    assert material["question_text_or_draft_text_saved_here"] is False
    assert material["question_trigger_logic_implemented"] is False
    assert material["p8_start_allowed"] is False
    assert clr.assert_p7_r54_clr14_question_need_observation_normalization_contract(material) is True


def test_r54_clr14_rejects_question_text_payload_from_prior_material() -> None:
    material = _ready_clr13()
    mutated = deepcopy(material)
    mutated["rating_rows"][0]["question_text"] = "forbidden"

    with pytest.raises(ValueError):
        clr.build_p7_r54_clr14_question_need_observation_normalization(
            readfeel_blocker_execution_blocker_ingestion=mutated,
        )


def test_r54_clr14_rejects_p8_implementation_spec_finalization_flag() -> None:
    material = _ready_clr13()
    mutated = deepcopy(material)
    mutated["rating_rows"][0]["plan_candidate_flags"] = dict(mutated["rating_rows"][0]["plan_candidate_flags"])
    mutated["rating_rows"][0]["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] = True

    with pytest.raises(ValueError):
        clr.build_p7_r54_clr14_question_need_observation_normalization(
            readfeel_blocker_execution_blocker_ingestion=mutated,
        )


def test_r54_clr15_default_blocks_without_ready_clr14() -> None:
    material = clr.build_p7_r54_clr15_rating_question_consistency_guard()

    assert set(material) == set(clr.P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR15_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR15_STEP_REF
    assert material["rating_question_consistency_guard_status"] == clr.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert "clr14_question_need_observation_normalization_not_ready_for_consistency_guard" in material["execution_blocker_ids"]
    assert material["rating_question_consistency_issue_rows"] == []
    assert material["consistency_issue_count"] == 0
    assert material["ready_for_pause_abort_expiration_protocol"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR15_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr15_rating_question_consistency_guard_contract(material) is True


def test_r54_clr15_consistency_guard_ready_bodyfree() -> None:
    material = clr.build_p7_r54_clr15_rating_question_consistency_guard(
        question_need_observation_normalization=_ready_clr14(),
    )

    assert set(material) == set(clr.P7_R54_CLR15_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["rating_question_consistency_guard_status"] == clr.P7_R54_CLR15_CONSISTENCY_GUARD_READY_STATUS_REF
    assert material["rating_question_consistency_guard_ref"] == clr.P7_R54_CLR15_CONSISTENCY_GUARD_REF
    assert material["rating_question_consistency_guard_reason_refs"] == [clr.P7_R54_CLR15_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["rating_question_case_ref_sets_match"] is True
    assert material["all_required_rating_and_question_rows_present"] is True
    assert material["rating_question_consistency_issue_rows"] == []
    assert material["consistency_issue_count"] == 0
    assert material["p5_confirmed_candidate_blocked_by_consistency_issues"] is False
    assert material["p5_decision_candidate_not_materialized_here"] is True
    assert material["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    assert material["question_text_absent"] is True
    assert material["ready_for_pause_abort_expiration_protocol"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR16_STEP_REF
    _assert_bodyfree_no_touch(
        material,
        allowed_true_false_flags={
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
        },
    )
    assert clr.assert_p7_r54_clr15_rating_question_consistency_guard_contract(material) is True


def test_r54_clr15_blocks_non_pass_below_target_and_readfeel_blocker_from_p5_confirmed_candidate() -> None:
    rows = _ready_rows()
    rows[0]["verdict"] = "YELLOW"
    rows[0]["overall_read_feeling_ref"] = "felt_generic_or_shallow"
    rows[0]["readfeel_blocker_ids"] = ["p5_history_connection_too_generic"]
    rows[0]["axis_scores"] = dict(rows[0]["axis_scores"])
    rows[0]["axis_scores"]["history_connection_naturalness"] = 0.75

    guard = clr.build_p7_r54_clr15_rating_question_consistency_guard(
        question_need_observation_normalization=_ready_clr14(rows),
    )
    issue_ids = {row["issue_id"] for row in guard["rating_question_consistency_issue_rows"]}

    assert guard["rating_question_consistency_guard_status"] == clr.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert "r54_clr15_yellow_red_repair_or_below_target_blocks_p5_confirmed_candidate" in issue_ids
    assert "r54_clr15_readfeel_blocker_blocks_p5_confirmed_candidate" in issue_ids
    assert guard["yellow_red_repair_or_below_target_block_count"] >= 1
    assert guard["readfeel_blocker_block_count"] == 1
    assert guard["p5_confirmed_candidate_blocked_by_consistency_issues"] is True
    assert guard["ready_for_pause_abort_expiration_protocol"] is False
    assert guard["p5_human_blind_qa_confirmed_final"] is False
    assert guard["release_allowed"] is False
    assert clr.assert_p7_r54_clr15_rating_question_consistency_guard_contract(guard) is True


def test_r54_clr15_blocks_not_question_repair_from_becoming_p8_material() -> None:
    rows = _ready_rows()
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    rows[0]["plan_candidate_flags"] = dict(rows[0]["plan_candidate_flags"])
    rows[0]["plan_candidate_flags"]["p8_design_material_candidate"] = True

    guard = clr.build_p7_r54_clr15_rating_question_consistency_guard(
        question_need_observation_normalization=_ready_clr14(rows),
    )
    issue_ids = {row["issue_id"] for row in guard["rating_question_consistency_issue_rows"]}

    assert guard["rating_question_consistency_guard_status"] == clr.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert "r54_clr15_not_question_repair_not_p8_material" in issue_ids
    assert guard["not_question_repair_not_p8_material_count"] == 1
    assert guard["p5_repair_required_not_reclassified_as_p8_material"] is False
    assert guard["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    assert guard["p8_start_allowed"] is False
    assert clr.assert_p7_r54_clr15_rating_question_consistency_guard_contract(guard) is True


def test_r54_clr15_blocks_insufficient_material_pass() -> None:
    rows = _ready_rows()
    rows[0]["question_need_primary_class"] = "insufficient_material_execution_blocker"
    rows[0]["one_question_fit_ref"] = "insufficient_material"

    guard = clr.build_p7_r54_clr15_rating_question_consistency_guard(
        question_need_observation_normalization=_ready_clr14(rows),
    )
    issue_ids = {row["issue_id"] for row in guard["rating_question_consistency_issue_rows"]}

    assert guard["rating_question_consistency_guard_status"] == clr.P7_R54_CLR15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert "r54_clr15_insufficient_material_with_pass_or_no_execution_blocker" in issue_ids
    assert guard["insufficient_material_with_pass_or_no_execution_blocker_count"] == 1
    assert guard["ready_for_pause_abort_expiration_protocol"] is False
    assert guard["actual_review_evidence_complete"] is False
    assert clr.assert_p7_r54_clr15_rating_question_consistency_guard_contract(guard) is True
