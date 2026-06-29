# -*- coding: utf-8 -*-
"""Tests for R54-AHR14/AHR15 body-free question observation and consistency guard."""

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

NO_TOUCH_ALWAYS_FALSE_FLAGS = (
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
    "actual_disposal_receipt_materialized_here",
    "actual_r52_reintake_execution_confirmed",
    "actual_review_evidence_complete",
    "p5_human_blind_qa_confirmed_final",
    "p6_start_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
)


def assert_bodyfree_no_touch(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in BODY_FREE_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in NO_TOUCH_ALWAYS_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key


def assert_bodyfree_row(row: dict[str, object]) -> None:
    assert row["body_free"] is True
    for key in BODY_FREE_FALSE_FLAGS:
        if key in row:
            assert row[key] is False, key


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


def build_review_result_rows(
    operation: dict[str, object] | None = None,
    *,
    p8_candidate_index: int | None = None,
    repair_index: int | None = None,
    execution_blocker_index: int | None = None,
) -> list[dict[str, object]]:
    operation = operation or build_valid_operation()
    manifest = ahr.build_p7_r54_ahr05_24_case_manifest_freeze()
    rows: list[dict[str, object]] = []
    for index, case_row in enumerate(manifest["case_rows"], start=1):
        question_class = "no_question_needed_emlis_can_observe"
        ambiguity_refs = ["no_material_ambiguity"]
        one_fit = "not_needed"
        repair_refs = ["no_repair_required"]
        verdict = "PASS"
        readfeel_blockers: list[str] = []
        execution_blockers: list[str] = []
        reason_ids = ["record_returned_as_natural_line"]
        plan_flags = {
            "plus_single_question_candidate_later": False,
            "premium_deep_dive_candidate_later": False,
            "p8_design_material_candidate": False,
            "p8_implementation_spec_finalized_here": False,
        }
        if p8_candidate_index == index:
            question_class = "plus_single_question_candidate_later"
            ambiguity_refs = ["missing_time_scope"]
            one_fit = "fits_one_question"
            plan_flags["plus_single_question_candidate_later"] = True
            plan_flags["p8_design_material_candidate"] = True
            reason_ids = ["question_may_reduce_overread_risk_later"]
        if repair_index == index:
            question_class = "not_question_p5_surface_repair_required"
            one_fit = "repair_required_not_question"
            repair_refs = ["p5_surface_repair_required"]
            verdict = "REPAIR_REQUIRED"
            readfeel_blockers = ["history_connection_weak"]
            reason_ids = ["p5_surface_repair_required"]
        if execution_blocker_index == index:
            question_class = "insufficient_material_execution_blocker"
            one_fit = "insufficient_material"
            repair_refs = ["gate_boundary_repair_required"]
            verdict = "BLOCKED"
            execution_blockers = ["packet_missing"]
            reason_ids = ["execution_blocker_present"]
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
                "verdict": verdict,
                "sanitized_reason_ids": reason_ids,
                "readfeel_blocker_ids": readfeel_blockers,
                "execution_blocker_ids": execution_blockers,
                "question_need_primary_class": question_class,
                "ambiguity_kind_refs": ambiguity_refs,
                "one_question_fit_ref": one_fit,
                "repair_required_refs": repair_refs,
                "plan_candidate_flags": plan_flags,
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


def build_valid_ahr12_rating(
    *,
    p8_candidate_index: int | None = None,
    repair_index: int | None = None,
    execution_blocker_index: int | None = None,
) -> dict[str, object]:
    operation = build_valid_operation()
    intake = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=build_review_result_rows(
            operation,
            p8_candidate_index=p8_candidate_index,
            repair_index=repair_index,
            execution_blocker_index=execution_blocker_index,
        ),
        review_session_id=operation["review_session_id"],
    )
    return ahr.build_p7_r54_ahr12_rating_row_normalization(
        sanitized_review_result_intake=intake,
        review_session_id=operation["review_session_id"],
    )


def build_valid_ahr13_blockers(
    *,
    rating: dict[str, object] | None = None,
) -> dict[str, object]:
    rating = rating or build_valid_ahr12_rating()
    return ahr.build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=rating,
        review_session_id=rating["review_session_id"],
    )


def build_valid_ahr14_question_normalization(
    *,
    rating: dict[str, object] | None = None,
    blockers: dict[str, object] | None = None,
) -> dict[str, object]:
    rating = rating or build_valid_ahr12_rating()
    blockers = blockers or build_valid_ahr13_blockers(rating=rating)
    return ahr.build_p7_r54_ahr14_question_need_observation_normalization(
        blocker_ingestion=blockers,
        rating_row_normalization=rating,
        review_session_id=rating["review_session_id"],
    )


def test_r54_ahr14_default_blocks_without_ahr13_and_rating_rows() -> None:
    material = ahr.build_p7_r54_ahr14_question_need_observation_normalization()

    assert ahr.assert_p7_r54_ahr14_question_need_observation_normalization_contract(material) is True
    assert material["question_need_observation_normalization_status_ref"] == ahr.P7_R54_AHR14_BLOCKED_STATUS_REF
    assert "ahr13_blocker_ingestion_not_ready" in material["execution_blocker_ids"]
    assert "ahr12_rating_row_normalization_not_ready_for_question_observation" in material["execution_blocker_ids"]
    assert material["question_need_observation_row_count"] == 0
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR13_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr14_normalizes_24_bodyfree_question_observation_rows() -> None:
    rating = build_valid_ahr12_rating(p8_candidate_index=3, repair_index=5, execution_blocker_index=7)
    blockers = build_valid_ahr13_blockers(rating=rating)
    material = build_valid_ahr14_question_normalization(rating=rating, blockers=blockers)

    assert ahr.assert_p7_r54_ahr14_question_need_observation_normalization_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR14_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR14_STEP_REF
    assert material["question_need_observation_normalization_status_ref"] == ahr.P7_R54_AHR14_NORMALIZED_STATUS_REF
    assert material["question_need_observation_normalization_reason_refs"] == [ahr.P7_R54_AHR14_READY_REASON_REF]
    assert material["question_need_observation_row_count"] == 24
    assert material["actual_question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_ref_count"] == 24
    assert material["source_rating_row_ref_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["question_observation_rows_bodyfree_only"] is True
    assert material["question_observation_rows_from_actual_review_only"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["p8_material_candidate_row_count"] == 1
    assert material["plus_single_question_candidate_row_count"] == 1
    assert material["p5_repair_required_observation_row_count"] == 1
    assert material["execution_blocker_observation_row_count"] == 1
    assert material["question_need_observation_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR15_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR14_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)

    p8_rows = [row for row in material["question_need_observation_rows"] if row["p8_design_material_candidate"] is True]
    assert len(p8_rows) == 1
    assert p8_rows[0]["question_need_primary_class"] == "plus_single_question_candidate_later"
    assert p8_rows[0]["one_question_fit_ref"] == "fits_one_question"
    assert p8_rows[0]["p8_implementation_spec_finalized_here"] is False
    for row in material["question_need_observation_rows"]:
        assert row["schema_version"] == ahr.P7_R54_AHR14_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
        assert_bodyfree_row(row)


def test_r54_ahr14_blocks_rating_rows_with_body_or_question_key() -> None:
    rating = build_valid_ahr12_rating()
    mutated_rating = deepcopy(rating)
    mutated_rating["rating_rows"][0]["question_text"] = "should never enter body-free evidence"
    blockers = build_valid_ahr13_blockers(rating=rating)
    material = ahr.build_p7_r54_ahr14_question_need_observation_normalization(
        blocker_ingestion=blockers,
        rating_row_normalization=mutated_rating,
        review_session_id=rating["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr14_question_need_observation_normalization_contract(material) is True
    assert material["question_need_observation_normalization_status_ref"] == ahr.P7_R54_AHR14_BLOCKED_STATUS_REF
    assert "question_observation_source_rating_row_01_contains_forbidden_body_question_path_hash_key" in material["execution_blocker_ids"]
    assert material["question_need_observation_rows"] == []
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


def test_r54_ahr15_default_blocks_without_ahr14_question_observations() -> None:
    material = ahr.build_p7_r54_ahr15_rating_question_consistency_guard()

    assert ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(material) is True
    assert material["consistency_guard_status_ref"] == ahr.P7_R54_AHR15_BLOCKED_STATUS_REF
    assert "ahr14_question_need_observation_normalization_not_ready" in material["execution_blocker_ids"]
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["pause_abort_expiration_protocol_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR15_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR14_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr15_passes_clean_rating_question_consistency_guard() -> None:
    question_material = build_valid_ahr14_question_normalization(
        rating=build_valid_ahr12_rating(p8_candidate_index=3, repair_index=5, execution_blocker_index=7)
    )
    material = ahr.build_p7_r54_ahr15_rating_question_consistency_guard(
        question_need_observation_normalization=question_material,
        review_session_id=question_material["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR15_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR15_STEP_REF
    assert material["consistency_guard_status_ref"] == ahr.P7_R54_AHR15_PASSED_STATUS_REF
    assert material["consistency_guard_reason_refs"] == [ahr.P7_R54_AHR15_READY_REASON_REF]
    assert material["question_need_observation_row_count"] == 24
    assert material["question_need_observation_row_ref_count"] == 24
    assert material["consistency_issue_rows"] == []
    assert material["consistency_issue_row_count"] == 0
    assert material["open_consistency_issue_count"] == 0
    assert material["rating_question_consistency_guard_passed"] is True
    assert material["question_text_absent"] is True
    assert material["draft_question_text_absent"] is True
    assert material["p8_implementation_spec_not_finalized_here"] is True
    assert material["p5_repair_rows_excluded_from_p8_material"] is True
    assert material["execution_blocker_rows_excluded_from_p8_material"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["pause_abort_expiration_protocol_allowed_next"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR16_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR15_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


@pytest.mark.parametrize(
    "mutator,expected_issue",
    [
        (
            lambda rows: [dict(row, question_text_included=True) if i == 0 else row for i, row in enumerate(rows)],
            "question_or_draft_text_included",
        ),
        (
            lambda rows: [dict(row, p8_implementation_spec_finalized_here=True) if i == 0 else row for i, row in enumerate(rows)],
            "p8_implementation_spec_finalized_here",
        ),
        (
            lambda rows: [
                dict(
                    row,
                    p8_design_material_candidate=True,
                    p5_repair_required=True,
                    repair_required_refs=["p5_surface_repair_required"],
                )
                if i == 0
                else row
                for i, row in enumerate(rows)
            ],
            "repair_required_row_routed_to_p8_material",
        ),
        (
            lambda rows: [
                dict(row, p8_design_material_candidate=True, execution_blocker_present=True, execution_blocker_ids=["packet_missing"])
                if i == 0
                else row
                for i, row in enumerate(rows)
            ],
            "execution_blocker_routed_to_p8_material",
        ),
        (
            lambda rows: [
                dict(row, p8_design_material_candidate=True, verdict="REPAIR_REQUIRED") if i == 0 else row
                for i, row in enumerate(rows)
            ],
            "red_repair_or_blocked_verdict_routed_to_p8_material",
        ),
        (
            lambda rows: [
                dict(row, readfeel_blocker_present=True, plus_single_question_candidate_later=True, readfeel_blocker_ids=["history_connection_weak"])
                if i == 0
                else row
                for i, row in enumerate(rows)
            ],
            "readfeel_blocker_routed_to_question_candidate",
        ),
        (
            lambda rows: [
                dict(row, question_need_primary_class="no_question_needed_emlis_can_observe", repair_required_refs=["p5_surface_repair_required"])
                if i == 0
                else row
                for i, row in enumerate(rows)
            ],
            "p5_surface_repair_required_misclassified_as_no_question_needed",
        ),
    ],
)
def test_r54_ahr15_blocks_rating_question_consistency_issues(mutator, expected_issue: str) -> None:
    question_material = build_valid_ahr14_question_normalization()
    mutated = deepcopy(question_material)
    mutated["question_need_observation_rows"] = mutator(mutated["question_need_observation_rows"])
    material = ahr.build_p7_r54_ahr15_rating_question_consistency_guard(
        question_need_observation_normalization=mutated,
        review_session_id=mutated["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(material) is True
    assert material["consistency_guard_status_ref"] == ahr.P7_R54_AHR15_BLOCKED_STATUS_REF
    assert expected_issue in material["consistency_issue_ids"]
    assert expected_issue in material["execution_blocker_ids"]
    assert material["consistency_issue_row_count"] >= 1
    assert material["rating_question_consistency_guard_passed"] is False
    assert material["pause_abort_expiration_protocol_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR15_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)
    for row in material["consistency_issue_rows"]:
        assert row["schema_version"] == ahr.P7_R54_AHR15_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION
        assert row["routes_to"] == ahr.P7_R54_AHR15_CONSISTENCY_ROUTE_REF
        assert_bodyfree_row(row)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_review_evidence_complete", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("p8_implementation_spec_finalized_here", True),
    ],
)
def test_r54_ahr14_rejects_premature_completion_promotion_or_question_text_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr14_question_normalization()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr14_question_need_observation_normalization_contract(mutated)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_review_evidence_complete", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr15_rejects_premature_completion_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = ahr.build_p7_r54_ahr15_rating_question_consistency_guard(
        question_need_observation_normalization=build_valid_ahr14_question_normalization()
    )
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(mutated)


def test_r54_ahr14_ahr15_design_aliases_point_to_canonical_helpers() -> None:
    rating = build_valid_ahr12_rating(p8_candidate_index=4)
    blockers = build_valid_ahr13_blockers(rating=rating)
    question_material = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr14_question_need_observation_normalization(
        blocker_ingestion=blockers,
        rating_row_normalization=rating,
        review_session_id=rating["review_session_id"],
    )
    guard = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr15_rating_question_consistency_guard(
        question_need_observation_normalization=question_material,
        review_session_id=question_material["review_session_id"],
    )

    assert question_material["question_need_observation_normalization_status_ref"] == ahr.P7_R54_AHR14_NORMALIZED_STATUS_REF
    assert guard["consistency_guard_status_ref"] == ahr.P7_R54_AHR15_PASSED_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr14_question_need_observation_normalization_contract(question_material) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr15_rating_question_consistency_guard_contract(guard) is True
