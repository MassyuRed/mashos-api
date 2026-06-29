# -*- coding: utf-8 -*-
"""Tests for R54-AHR10/AHR11 body-free actual review receipt intake."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr


BODY_FREE_FALSE_FLAGS = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "body_full_packet_content_included",
    "packet_content_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
)

NO_TOUCH_FALSE_FLAGS = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "db_schema_changed",
    "db_migration_added",
    "rn_ui_changed",
    "public_response_key_changed",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_answer_persistence_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_r52_reintake_execution_confirmed",
    "actual_review_evidence_complete",
    "p5_human_blind_qa_confirmed_final",
    "p6_start_allowed",
    "p8_start_allowed",
    "release_allowed",
)


def assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in BODY_FREE_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in NO_TOUCH_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key


def build_valid_operation() -> dict[str, object]:
    form = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze()
    return ahr.build_p7_r54_ahr10_actual_human_review_local_only_operation(
        reviewer_selection_form=form,
        operation_receipt_ref=ahr.P7_R54_AHR10_OPERATION_RECEIPT_REF,
        reviewer_ref=ahr.P7_R54_AHR10_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_executed_by_person=True,
        review_started_at_ref=ahr.P7_R54_AHR10_REVIEW_STARTED_AT_REF_DEFAULT,
        review_completed_at_ref=ahr.P7_R54_AHR10_REVIEW_COMPLETED_AT_REF_DEFAULT,
        reviewed_case_count=ahr.P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        selection_row_count=ahr.P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    )


def build_valid_review_result_rows(operation: dict[str, object] | None = None) -> list[dict[str, object]]:
    operation = operation or build_valid_operation()
    manifest = ahr.build_p7_r54_ahr05_24_case_manifest_freeze()
    rows: list[dict[str, object]] = []
    for index, case_row in enumerate(manifest["case_rows"], start=1):
        rows.append(
            {
                "schema_version": ahr.P7_R54_AHR11_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_result_row_ref": f"review_result_row_{index:03d}",
                "review_session_id": operation["review_session_id"],
                "case_ref_id": case_row["case_ref_id"],
                "blind_case_id": case_row["blind_case_id"],
                "packet_ref_id": case_row["packet_ref_id"],
                "family": case_row["family"],
                "case_role": case_row["case_role"],
                "reviewer_ref": operation["reviewer_ref"],
                "reviewed_at_ref": "reviewed_at_bucket_ref",
                "axis_scores": {axis_ref: 1.0 for axis_ref in ahr.P7_R54_AHR05_RATING_AXIS_REFS},
                "axis_score_count": len(ahr.P7_R54_AHR05_RATING_AXIS_REFS),
                "verdict": "PASS",
                "sanitized_reason_ids": ["record_returned_as_natural_line"],
                "readfeel_blocker_ids": [],
                "execution_blocker_ids": [],
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "plan_candidate_flags": {
                    "plus_single_question_candidate_later": False,
                    "premium_deep_dive_candidate_later": False,
                    "p8_design_material_candidate": False,
                    "p8_implementation_spec_finalized_here": False,
                },
                "selection_only_row": True,
                "reviewer_free_text_included": False,
                "raw_body_included": False,
                "returned_emlis_body_included": False,
                "history_surface_included": False,
                "comment_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
                "body_free": True,
            }
        )
    return rows


def test_r54_ahr10_default_blocks_without_actual_person_receipt() -> None:
    material = ahr.build_p7_r54_ahr10_actual_human_review_local_only_operation()

    assert ahr.assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract(material) is True
    assert material["operation_status_ref"] == ahr.P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF
    assert "operation_receipt_ref_missing" in material["execution_blocker_ids"]
    assert "actual_human_review_executed_by_person_not_confirmed" in material["execution_blocker_ids"]
    assert material["actual_human_review_executed_by_person"] is False
    assert material["actual_human_review_operation_receipt_intaken_here"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR09_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr10_intakes_valid_bodyfree_actual_review_operation_receipt() -> None:
    material = build_valid_operation()

    assert ahr.assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR10_STEP_REF
    assert material["operation_status_ref"] == ahr.P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    assert material["operation_receipt_status_ref"] == material["operation_status_ref"]
    assert material["operation_receipt_reason_refs"] == [ahr.P7_R54_AHR10_READY_REASON_REF]
    assert material["reviewer_selection_form_ready_for_actual_review_operation"] is True
    assert material["operation_receipt_ref_present"] is True
    assert material["operation_receipt_bodyfree_only"] is True
    assert material["reviewer_is_person"] is True
    assert material["reviewer_person_confirmed"] is True
    assert material["reviewer_local_only_read_receipt_present"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["reviewed_case_count"] == 24
    assert material["selection_row_count"] == 24
    assert material["actual_human_review_operation_complete"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is True
    assert material["rating_rows_materialized_here"] is False
    assert material["question_need_observation_rows_materialized_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR11_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR10_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"reviewer_is_person": False}, "reviewer_is_not_person"),
        ({"reviewer_person_confirmed": False}, "reviewer_person_not_confirmed"),
        ({"reviewer_local_only_read_receipt_present": False}, "reviewer_local_only_read_receipt_missing"),
        ({"reviewed_case_count": 23}, "reviewed_case_count_not_24"),
        ({"selection_row_count": 23}, "selection_row_count_not_24"),
        ({"local_only": False}, "local_only_not_confirmed"),
        ({"must_not_export": False}, "must_not_export_not_confirmed"),
        ({"selection_only": False}, "selection_only_not_confirmed"),
        ({"question_text_included": True}, "question_text_included"),
        ({"packet_content_included": True}, "packet_content_included"),
    ],
)
def test_r54_ahr10_blocks_incomplete_or_unsafe_actual_review_receipts(
    kwargs: dict[str, object], expected_blocker: str
) -> None:
    base = dict(
        reviewer_selection_form=ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze(),
        operation_receipt_ref=ahr.P7_R54_AHR10_OPERATION_RECEIPT_REF,
        reviewer_ref=ahr.P7_R54_AHR10_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_executed_by_person=True,
        review_started_at_ref=ahr.P7_R54_AHR10_REVIEW_STARTED_AT_REF_DEFAULT,
        review_completed_at_ref=ahr.P7_R54_AHR10_REVIEW_COMPLETED_AT_REF_DEFAULT,
        reviewed_case_count=24,
        selection_row_count=24,
    )
    base.update(kwargs)
    material = ahr.build_p7_r54_ahr10_actual_human_review_local_only_operation(**base)

    assert ahr.assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract(material) is True
    assert material["operation_status_ref"] == ahr.P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["actual_human_review_operation_complete"] is False
    assert material["sanitized_review_result_row_intake_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


def test_r54_ahr10_blocks_when_reviewer_form_is_not_frozen() -> None:
    blocked_form = ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze(question_text_input_allowed=True)
    material = ahr.build_p7_r54_ahr10_actual_human_review_local_only_operation(
        reviewer_selection_form=blocked_form,
        operation_receipt_ref=ahr.P7_R54_AHR10_OPERATION_RECEIPT_REF,
        reviewer_ref=ahr.P7_R54_AHR10_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_executed_by_person=True,
        review_started_at_ref=ahr.P7_R54_AHR10_REVIEW_STARTED_AT_REF_DEFAULT,
        review_completed_at_ref=ahr.P7_R54_AHR10_REVIEW_COMPLETED_AT_REF_DEFAULT,
        reviewed_case_count=24,
        selection_row_count=24,
    )

    assert material["operation_status_ref"] == ahr.P7_R54_AHR10_OPERATION_BLOCKED_STATUS_REF
    assert "ahr09_reviewer_selection_form_not_frozen" in material["execution_blocker_ids"]
    assert "ahr09_next_step_not_actual_review_operation" in material["execution_blocker_ids"]
    assert ahr.assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract(material) is True


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("raw_input_included", True),
        ("returned_emlis_body_included", True),
        ("history_surface_included", True),
        ("reviewer_free_text_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("packet_content_included", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr10_rejects_body_leak_question_leak_or_premature_promotion_mutations(
    field: str, bad_value: object
) -> None:
    material = build_valid_operation()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr10_actual_human_review_local_only_operation_contract(mutated)


def test_r54_ahr11_default_blocks_without_operation_or_review_rows() -> None:
    material = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake()

    assert ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(material) is True
    assert material["sanitized_review_result_row_intake_status_ref"] == ahr.P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF
    assert "ahr10_actual_human_review_operation_not_ready" in material["execution_blocker_ids"]
    assert "review_result_row_count_not_24" in material["execution_blocker_ids"]
    assert material["sanitized_review_result_row_count"] == 0
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


def test_r54_ahr11_intakes_24_selection_only_sanitized_review_rows() -> None:
    operation = build_valid_operation()
    rows = build_valid_review_result_rows(operation)
    material = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows,
        review_session_id=operation["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR11_STEP_REF
    assert material["sanitized_review_result_row_intake_status_ref"] == ahr.P7_R54_AHR11_INTAKE_READY_STATUS_REF
    assert material["sanitized_review_result_row_intake_reason_refs"] == [ahr.P7_R54_AHR11_READY_REASON_REF]
    assert material["operation_ready_for_sanitized_result_intake"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["review_result_row_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["review_result_row_ref_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["packet_ref_ids_unique"] is True
    assert material["rows_match_24_case_manifest"] is True
    assert material["rows_bodyfree_only"] is True
    assert material["rows_selection_only"] is True
    assert material["rows_have_no_body_or_question_or_path_or_hash"] is True
    assert material["sanitized_review_result_rows_intaken_here"] is True
    assert material["actual_sanitized_review_result_rows_intaken_here"] is True
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_rows_materialized_here"] is False
    assert material["question_need_observation_rows_materialized_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR12_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR11_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


@pytest.mark.parametrize(
    "mutator,expected_blocker",
    [
        (lambda rows: rows[:-1], "review_result_row_count_not_24"),
        (lambda rows: [dict(row, axis_score_count=5) if i == 0 else row for i, row in enumerate(rows)], "review_result_row_01_axis_score_count_not_6"),
        (lambda rows: [dict(row, verdict="UNKNOWN") if i == 0 else row for i, row in enumerate(rows)], "review_result_row_01_verdict_not_allowed"),
        (lambda rows: [dict(row, question_text="body leak") if i == 0 else row for i, row in enumerate(rows)], "review_result_row_01_contains_forbidden_body_question_path_hash_key"),
        (lambda rows: [dict(row, packet_content_included=True) if i == 0 else row for i, row in enumerate(rows)], "review_result_row_01_packet_content_included_not_false"),
    ],
)
def test_r54_ahr11_blocks_invalid_or_unsafe_sanitized_review_rows(mutator, expected_blocker: str) -> None:
    operation = build_valid_operation()
    rows = mutator(build_valid_review_result_rows(operation))
    material = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows,
        review_session_id=operation["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(material) is True
    assert material["sanitized_review_result_row_intake_status_ref"] == ahr.P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["review_result_rows"] == []
    assert material["sanitized_review_result_row_count"] == 0
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


def test_r54_ahr11_blocks_when_ahr10_operation_is_not_ready() -> None:
    blocked_operation = ahr.build_p7_r54_ahr10_actual_human_review_local_only_operation()
    material = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=blocked_operation,
        review_result_rows=build_valid_review_result_rows(build_valid_operation()),
    )

    assert material["sanitized_review_result_row_intake_status_ref"] == ahr.P7_R54_AHR11_INTAKE_BLOCKED_STATUS_REF
    assert "ahr10_actual_human_review_operation_not_ready" in material["execution_blocker_ids"]
    assert ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(material) is True


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_human_review_run_here", True),
        ("actual_review_evidence_complete", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr11_rejects_premature_completion_or_promotion_mutations(field: str, bad_value: object) -> None:
    operation = build_valid_operation()
    rows = build_valid_review_result_rows(operation)
    material = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows,
        review_session_id=operation["review_session_id"],
    )
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(mutated)


def test_r54_ahr11_rejects_row_body_or_p8_implementation_mutation() -> None:
    operation = build_valid_operation()
    rows = build_valid_review_result_rows(operation)
    material = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows,
        review_session_id=operation["review_session_id"],
    )
    mutated = deepcopy(material)
    mutated["review_result_rows"][0]["question_text_included"] = True

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(mutated)

    mutated = deepcopy(material)
    mutated["review_result_rows"][0]["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] = True
    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr11_sanitized_review_result_row_intake_contract(mutated)


def test_r54_ahr10_ahr11_design_aliases_point_to_canonical_helpers() -> None:
    operation = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr10_actual_human_review_local_only_operation(
        reviewer_selection_form=ahr.build_p7_r54_ahr09_reviewer_selection_form_freeze(),
        operation_receipt_ref=ahr.P7_R54_AHR10_OPERATION_RECEIPT_REF,
        reviewer_ref=ahr.P7_R54_AHR10_REVIEWER_PERSON_REF_DEFAULT,
        reviewer_is_person=True,
        reviewer_person_confirmed=True,
        reviewer_local_only_read_receipt_present=True,
        actual_human_review_executed_by_person=True,
        review_started_at_ref=ahr.P7_R54_AHR10_REVIEW_STARTED_AT_REF_DEFAULT,
        review_completed_at_ref=ahr.P7_R54_AHR10_REVIEW_COMPLETED_AT_REF_DEFAULT,
        reviewed_case_count=24,
        selection_row_count=24,
    )
    rows = build_valid_review_result_rows(operation)
    intake = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows,
        review_session_id=operation["review_session_id"],
    )

    assert operation["operation_status_ref"] == ahr.P7_R54_AHR10_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    assert intake["sanitized_review_result_row_intake_status_ref"] == ahr.P7_R54_AHR11_INTAKE_READY_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr10_actual_human_review_local_only_operation_contract(operation) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr11_sanitized_review_result_row_intake_contract(intake) is True
