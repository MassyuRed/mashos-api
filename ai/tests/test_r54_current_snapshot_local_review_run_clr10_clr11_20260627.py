# -*- coding: utf-8 -*-
"""R54 current snapshot local review run CLR10-CLR11 contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr10_clr11_20260627 as clr


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


def _assert_bodyfree_no_touch(material: dict[str, Any]) -> None:
    assert material["body_free"] is True
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        assert material[key] is False, key
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["r54_clr_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _ready_clr09() -> dict[str, Any]:
    form = clr09.build_p7_r54_clr09_reviewer_selection_form_freeze()
    assert clr09.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form) is True
    assert form["reviewer_selection_form_status"] == clr09.P7_R54_CLR09_FORM_READY_STATUS_REF
    assert form["actual_human_review_operation_allowed_next"] is True
    assert form["actual_human_review_operation_state_capture_allowed_next"] is True
    assert form["next_required_step"] == clr.P7_R54_CLR10_STEP_REF
    return form


def _completed_receipt(form: dict[str, Any] | None = None) -> dict[str, Any]:
    return clr.build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form(
        reviewer_selection_form_freeze=form or _ready_clr09(),
        reviewer_ref_ids=["r54-local-reviewer-bodyfree-ref-001"],
    )


def _completed_clr10() -> dict[str, Any]:
    form = _ready_clr09()
    receipt = _completed_receipt(form)
    material = clr.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=form,
        local_human_review_operation_receipt=receipt,
    )
    assert clr.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True
    return material


def _ready_rows(op10: dict[str, Any]) -> list[dict[str, Any]]:
    return clr.build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion(op10)


def _ready_clr11() -> dict[str, Any]:
    op10 = _completed_clr10()
    rows = _ready_rows(op10)
    material = clr.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=rows,
    )
    assert clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True
    return material


def test_r54_clr00_to_clr09_are_present_before_clr10_clr11() -> None:
    form = _ready_clr09()

    assert tuple(form["implemented_steps"]) == clr09.P7_R54_CLR09_IMPLEMENTED_STEPS
    assert form["reviewer_selection_form_status"] == clr09.P7_R54_CLR09_FORM_READY_STATUS_REF
    assert form["selection_only_form"] is True
    assert form["actual_human_review_operation_allowed_next"] is True
    assert form["actual_human_review_run_here"] is False
    assert form["rating_row_count"] == 0
    assert form["question_observation_row_count"] == 0
    assert form["disposal_verified"] is False
    assert form["next_required_step"] == clr.P7_R54_CLR10_STEP_REF


def test_r54_clr10_without_external_receipt_is_blocked_bodyfree() -> None:
    material = clr.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=_ready_clr09()
    )

    assert set(material) == set(clr.P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR10_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR10_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR10_STEP_REF
    assert material["review_operation_receipt_status"] == clr.P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF
    assert material["review_operation_status"] == clr.P7_R54_CLR10_REVIEW_NOT_STARTED_STATUS_REF
    assert "local_human_review_operation_receipt_missing" in material["execution_blocker_ids"]
    assert material["reviewer_ref_count"] == 0
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["review_completed_packet_ref_count"] == 0
    assert material["review_completed_selection_row_count"] == 0
    assert material["external_local_human_review_completion_receipt_accepted"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_operation_performed_by_helper"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert tuple(material["implemented_steps"]) == clr09.P7_R54_CLR09_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True


@pytest.mark.parametrize(
    "status_ref,declared_field",
    [
        (clr.P7_R54_CLR10_REVIEW_IN_PROGRESS_STATUS_REF, "review_started_state_declared"),
        (clr.P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF, "review_paused_state_declared"),
        (clr.P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF, "review_aborted_state_declared"),
        (clr.P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF, "review_expired_state_declared"),
    ],
)
def test_r54_clr10_non_completed_operation_states_do_not_allow_intake(status_ref: str, declared_field: str) -> None:
    receipt = _completed_receipt(_ready_clr09())
    receipt["review_operation_status"] = status_ref
    # Non-completed states must not declare completed packet/selection evidence.
    receipt["review_completed_packet_ref_ids"] = []
    receipt["review_completed_selection_row_refs"] = []
    receipt["review_completion_receipt_ref"] = "review_completion_receipt_not_available_bodyfree"

    material = clr.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=_ready_clr09(),
        local_human_review_operation_receipt=receipt,
    )

    assert material["review_operation_receipt_status"] == clr.P7_R54_CLR10_OPERATION_RECEIPT_READY_STATUS_REF
    assert material["review_operation_status"] == status_ref
    assert material[declared_field] is True
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True


def test_r54_clr10_completed_external_receipt_allows_clr11_without_bodyfull_claim() -> None:
    material = _completed_clr10()

    assert material["review_operation_receipt_status"] == clr.P7_R54_CLR10_OPERATION_RECEIPT_READY_STATUS_REF
    assert material["review_operation_status"] == clr.P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
    assert material["review_operation_reason_refs"] == [clr.P7_R54_CLR10_READY_REASON_REF]
    assert material["review_completed_state_declared"] is True
    assert material["review_completed_packet_ref_count"] == 24
    assert material["review_completed_selection_row_count"] == 24
    assert material["review_completed_packet_ref_ids_unique"] is True
    assert material["review_completed_selection_row_refs_unique"] is True
    assert material["reviewer_ref_count"] == 1
    assert material["external_local_human_review_completion_receipt_accepted"] is True
    assert material["external_local_human_review_selection_refs_only"] is True
    assert material["external_local_human_review_body_not_materialized_here"] is True
    assert material["sanitized_review_result_row_intake_allowed_next"] is True
    assert material["next_required_step"] == clr.P7_R54_CLR11_STEP_REF
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_operation_performed_by_helper"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR10_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_touch(material)


def test_r54_clr10_blocks_when_clr09_form_not_ready() -> None:
    blocked_scan = clr09.build_p7_r54_clr08_packet_completeness_export_denylist_scan(
        body_full_packet_export_candidate_refs=["p7r48-p5-packet-r54clr-001"]
    )
    blocked_form = clr09.build_p7_r54_clr09_reviewer_selection_form_freeze(
        packet_completeness_export_denylist_scan=blocked_scan
    )
    receipt = _completed_receipt(_ready_clr09())

    material = clr.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=blocked_form,
        local_human_review_operation_receipt=receipt,
    )

    assert material["review_operation_receipt_status"] == clr.P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF
    assert "r54_clr10_blocked_until_clr09_reviewer_selection_form_ready" in material["execution_blocker_ids"]
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True


def test_r54_clr10_blocks_completed_receipt_with_export_candidate() -> None:
    receipt = _completed_receipt(_ready_clr09())
    receipt["export_candidate_count"] = 1

    material = clr.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=_ready_clr09(),
        local_human_review_operation_receipt=receipt,
    )

    assert material["review_operation_receipt_status"] == clr.P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF
    assert "review_operation_export_candidate_count_must_be_zero" in material["execution_blocker_ids"]
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(material) is True


def test_r54_clr11_default_blocks_without_completed_clr10() -> None:
    op10 = clr.build_p7_r54_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=_ready_clr09()
    )
    material = clr.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10
    )

    assert material["sanitized_review_result_intake_status"] == clr.P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF
    assert "r54_clr11_blocked_until_clr10_completed_state_ready" in material["execution_blocker_ids"]
    assert material["submitted_selection_row_count"] == 0
    assert material["sanitized_review_result_row_count"] == 0
    assert material["reviewed_case_count"] == 0
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True


def test_r54_clr11_sanitized_review_result_row_intake_ready_bodyfree() -> None:
    material = _ready_clr11()

    assert set(material) == set(clr.P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == clr.P7_R54_CLR11_SCHEMA_VERSION
    assert material["policy_section"] == clr.P7_R54_CLR11_STEP_REF
    assert material["operation_step_ref"] == clr.P7_R54_CLR11_STEP_REF
    assert material["sanitized_review_result_intake_status"] == clr.P7_R54_CLR11_INTAKE_READY_STATUS_REF
    assert material["sanitized_review_result_intake_ref"] == clr.P7_R54_CLR11_SANITIZED_REVIEW_RESULT_INTAKE_REF
    assert material["sanitized_review_result_intake_reason_refs"] == [clr.P7_R54_CLR11_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["clr10_review_operation_status"] == clr.P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
    assert material["clr10_sanitized_review_result_row_intake_allowed_next"] is True
    assert material["submitted_selection_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["case_ref_count"] == 24
    assert material["blind_case_id_count"] == 24
    assert material["selection_row_ref_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["selection_row_refs_unique"] is True
    assert material["reviewer_ref_count"] == 1
    assert material["selection_rows_are_bodyfree_only"] is True
    assert material["sanitized_review_result_rows_materialized_here"] is True
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["case_role_family_counts"]["p5_history_line_review"] == 20
    assert material["case_role_family_counts"]["current_only_boundary_case"] == 4
    assert material["actual_human_review_run_here"] is False
    assert material["actual_human_review_run_by_helper"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == clr.P7_R54_CLR11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == clr.P7_R54_CLR11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == clr.P7_R54_CLR12_STEP_REF

    for row in material["sanitized_review_result_rows"]:
        assert set(row) == set(clr.P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS)
        assert tuple(row["axis_scores"].keys()) == clr.P7_R54_CLR11_RATING_AXIS_REFS
        assert "overall_read_feeling_ref" not in row["axis_scores"]
        assert row["selection_only_row"] is True
        assert row["body_free"] is True
        assert row["source_body_not_materialized_in_row"] is True
        assert row["question_text_not_materialized_in_row"] is True
        for false_key in (
            "reviewer_free_text_included",
            "reviewer_note_included",
            "reviewer_notes_included",
            "raw_body_included",
            "returned_emlis_body_included",
            "history_surface_included",
            "question_text_included",
            "draft_question_text_included",
            "local_path_included",
            "local_absolute_path_included",
            "body_hash_included",
            "packet_content_included",
            "terminal_output_body_included",
        ):
            assert row[false_key] is False
        for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
            assert forbidden_key not in row
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True


def test_r54_clr11_blocks_incomplete_rows() -> None:
    op10 = _completed_clr10()
    rows = _ready_rows(op10)[:-1]

    material = clr.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=rows,
    )

    assert material["sanitized_review_result_intake_status"] == clr.P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF
    assert material["submitted_selection_row_count"] == 23
    assert "sanitized_review_result_row_count_must_be_24" in material["execution_blocker_ids"]
    assert material["sanitized_review_result_row_count"] == 0
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == clr.P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True


def test_r54_clr11_blocks_packet_ref_mismatch() -> None:
    op10 = _completed_clr10()
    rows = _ready_rows(op10)
    rows[0]["packet_ref_id"] = "p7r54-clr11-wrong-packet-ref"

    material = clr.build_p7_r54_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=rows,
    )

    assert material["sanitized_review_result_intake_status"] == clr.P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF
    assert "sanitized_review_packet_refs_must_match_clr10_completion_refs" in material["execution_blocker_ids"]
    assert material["sanitized_review_result_row_count"] == 0
    assert material["next_required_step"] == clr.P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch(material)
    assert clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(material) is True


def test_r54_clr11_rejects_forbidden_payload_or_question_key() -> None:
    op10 = _completed_clr10()
    rows = _ready_rows(op10)
    rows[0]["question_text"] = "forbidden_marker_payload"

    with pytest.raises(ValueError):
        clr.build_p7_r54_clr11_sanitized_review_result_row_intake(
            actual_human_review_local_only_operation=op10,
            reviewer_selection_rows=rows,
        )


def test_r54_clr10_clr11_contract_rejects_mutations() -> None:
    op10 = _completed_clr10()
    mutated_op10 = deepcopy(op10)
    mutated_op10["actual_human_review_run_here"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(mutated_op10)

    intake = _ready_clr11()
    mutated_intake = deepcopy(intake)
    mutated_intake["release_allowed"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(mutated_intake)

    mutated_row_intake = deepcopy(intake)
    mutated_row_intake["sanitized_review_result_rows"][0]["packet_content_included"] = True
    with pytest.raises(ValueError):
        clr.assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(mutated_row_intake)


def test_r54_clr10_clr11_aliases_remain_available() -> None:
    op10 = clr.build_p7_r54_current_snapshot_local_run_clr10_actual_human_review_local_only_operation(
        reviewer_selection_form_freeze=_ready_clr09(),
        local_human_review_operation_receipt=_completed_receipt(_ready_clr09()),
    )
    assert clr.assert_p7_r54_current_snapshot_local_run_clr10_actual_human_review_local_only_operation_contract(op10) is True
    assert clr.assert_p7_r54_current_snapshot_actual_human_review_local_only_operation_bodyfree_contract(op10) is True
    assert clr.assert_clr10_actual_human_review_local_only_operation_contract(op10) is True

    intake = clr.build_p7_r54_current_snapshot_local_run_clr11_sanitized_review_result_row_intake(
        actual_human_review_local_only_operation=op10,
        reviewer_selection_rows=_ready_rows(op10),
    )
    assert clr.assert_p7_r54_current_snapshot_local_run_clr11_sanitized_review_result_row_intake_contract(intake) is True
    assert clr.assert_p7_r54_current_snapshot_sanitized_review_result_row_intake_bodyfree_contract(intake) is True
    assert clr.assert_clr11_sanitized_review_result_row_intake_contract(intake) is True
