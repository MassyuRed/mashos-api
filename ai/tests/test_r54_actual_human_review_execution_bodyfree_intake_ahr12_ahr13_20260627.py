# -*- coding: utf-8 -*-
"""Tests for R54-AHR12/AHR13 body-free rating and blocker intake."""

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
    "actual_question_need_observation_rows_materialized_here",
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


def build_valid_ahr11_intake(*, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    operation = build_valid_operation()
    return ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows or build_valid_review_result_rows(operation),
        review_session_id=operation["review_session_id"],
    )


def build_valid_ahr12_rating() -> dict[str, object]:
    intake = build_valid_ahr11_intake()
    return ahr.build_p7_r54_ahr12_rating_row_normalization(
        sanitized_review_result_intake=intake,
        review_session_id=intake["review_session_id"],
    )


def test_r54_ahr12_default_blocks_without_sanitized_review_result_intake() -> None:
    material = ahr.build_p7_r54_ahr12_rating_row_normalization()

    assert ahr.assert_p7_r54_ahr12_rating_row_normalization_contract(material) is True
    assert material["rating_row_normalization_status_ref"] == ahr.P7_R54_AHR12_BLOCKED_STATUS_REF
    assert "ahr11_sanitized_review_result_row_intake_not_ready" in material["execution_blocker_ids"]
    assert material["rating_row_count"] == 0
    assert material["rating_rows"] == []
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_ingestion_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR11_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr12_normalizes_24_bodyfree_rating_rows_from_sanitized_results() -> None:
    intake = build_valid_ahr11_intake()
    material = ahr.build_p7_r54_ahr12_rating_row_normalization(
        sanitized_review_result_intake=intake,
        review_session_id=intake["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr12_rating_row_normalization_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR12_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR12_STEP_REF
    assert material["rating_row_normalization_status_ref"] == ahr.P7_R54_AHR12_NORMALIZED_STATUS_REF
    assert material["rating_row_normalization_reason_refs"] == [ahr.P7_R54_AHR12_READY_REASON_REF]
    assert material["sanitized_review_result_rows_ready_for_rating_normalization"] is True
    assert material["rating_row_count"] == 24
    assert material["rating_row_ref_count"] == 24
    assert material["source_review_result_row_ref_count"] == 24
    assert material["case_ref_id_count"] == 24
    assert material["case_ref_ids_unique"] is True
    assert material["axis_refs"] == list(ahr.P7_R54_AHR05_RATING_AXIS_REFS)
    assert material["axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == dict(ahr.P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS)
    assert material["rating_rows_bodyfree_only"] is True
    assert material["rating_rows_have_required_axis_scores"] is True
    assert material["rating_scores_in_range"] is True
    assert material["rating_rows_have_allowed_verdict_refs"] is True
    assert material["rating_rows_normalized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["readfeel_blocker_ingestion_allowed_next"] is True
    assert material["question_need_observation_rows_materialized_here"] is False
    assert material["r52_reintake_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR13_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR12_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)
    for row in material["rating_rows"]:
        assert row["schema_version"] == ahr.P7_R54_AHR12_RATING_ROW_SCHEMA_VERSION
        assert set(row["axis_scores"]) == set(ahr.P7_R54_AHR05_RATING_AXIS_REFS)
        assert row["axis_score_count"] == 6
        assert row["axis_targets"] == dict(ahr.P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS)
        assert row["verdict"] == "PASS"
        assert_bodyfree_row(row)


@pytest.mark.parametrize(
    "mutator,expected_blocker",
    [
        (
            lambda intake: dict(intake, review_result_rows=intake["review_result_rows"][:-1]),
            "source_sanitized_review_result_row_count_not_24",
        ),
        (
            lambda intake: dict(
                intake,
                review_result_rows=[
                    dict(row, axis_scores={k: v for k, v in row["axis_scores"].items() if k != ahr.P7_R54_AHR05_RATING_AXIS_REFS[0]})
                    if i == 0
                    else row
                    for i, row in enumerate(intake["review_result_rows"])
                ],
            ),
            "rating_source_row_01_axis_refs_mismatch",
        ),
        (
            lambda intake: dict(
                intake,
                review_result_rows=[
                    dict(row, axis_scores={**row["axis_scores"], ahr.P7_R54_AHR05_RATING_AXIS_REFS[0]: 1.5})
                    if i == 0
                    else row
                    for i, row in enumerate(intake["review_result_rows"])
                ],
            ),
            f"rating_source_row_01_{ahr.P7_R54_AHR05_RATING_AXIS_REFS[0]}_score_out_of_range",
        ),
        (
            lambda intake: dict(
                intake,
                review_result_rows=[dict(row, verdict="UNKNOWN") if i == 0 else row for i, row in enumerate(intake["review_result_rows"])],
            ),
            "rating_source_row_01_verdict_not_allowed",
        ),
        (
            lambda intake: dict(
                intake,
                review_result_rows=[dict(row, question_text="not allowed") if i == 0 else row for i, row in enumerate(intake["review_result_rows"])],
            ),
            "rating_source_row_01_contains_forbidden_body_question_path_hash_key",
        ),
    ],
)

def test_r54_ahr12_blocks_invalid_rating_source_rows(mutator, expected_blocker: str) -> None:
    intake = mutator(build_valid_ahr11_intake())
    material = ahr.build_p7_r54_ahr12_rating_row_normalization(
        sanitized_review_result_intake=intake,
        review_session_id=intake["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr12_rating_row_normalization_contract(material) is True
    assert material["rating_row_normalization_status_ref"] == ahr.P7_R54_AHR12_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["rating_row_count"] == 0
    assert material["rating_rows"] == []
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_ingestion_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


def test_r54_ahr13_default_blocks_without_rating_row_normalization() -> None:
    material = ahr.build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion()

    assert ahr.assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True
    assert material["blocker_ingestion_status_ref"] == ahr.P7_R54_AHR13_BLOCKED_STATUS_REF
    assert "ahr12_rating_row_normalization_not_ready" in material["execution_blocker_ids"]
    assert material["rating_row_count"] == 0
    assert material["blocker_row_count"] == 0
    assert material["blocker_rows"] == []
    assert material["question_need_observation_normalization_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR13_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR12_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)


def test_r54_ahr13_ingests_readfeel_and_execution_blockers_separately() -> None:
    operation = build_valid_operation()
    rows = build_valid_review_result_rows(operation)
    rows[0]["verdict"] = "REPAIR_REQUIRED"
    rows[0]["readfeel_blocker_ids"] = ["history_connection_weak"]
    rows[0]["sanitized_reason_ids"] = ["history_line_weak_or_generic"]
    rows[0]["repair_required_refs"] = ["p5_surface_repair_required"]
    rows[1]["verdict"] = "BLOCKED"
    rows[1]["execution_blocker_ids"] = ["packet_missing"]
    rows[1]["sanitized_reason_ids"] = ["execution_blocker_present"]
    intake = ahr.build_p7_r54_ahr11_sanitized_review_result_row_intake(
        actual_human_review_operation=operation,
        review_result_rows=rows,
        review_session_id=operation["review_session_id"],
    )
    rating = ahr.build_p7_r54_ahr12_rating_row_normalization(
        sanitized_review_result_intake=intake,
        review_session_id=operation["review_session_id"],
    )
    material = ahr.build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=rating,
        review_session_id=operation["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True
    assert material["blocker_ingestion_status_ref"] == ahr.P7_R54_AHR13_INGESTED_STATUS_REF
    assert material["blocker_ingestion_reason_refs"] == [ahr.P7_R54_AHR13_READY_REASON_REF]
    assert material["rating_rows_ready_for_blocker_ingestion"] is True
    assert material["rating_row_count"] == 24
    assert material["blocker_row_count"] == 2
    assert material["readfeel_blocker_row_count"] == 1
    assert material["execution_blocker_row_count"] == 1
    assert material["observed_readfeel_blocker_ids"] == ["history_connection_weak"]
    assert material["observed_execution_blocker_ids"] == ["packet_missing"]
    assert material["readfeel_execution_blockers_separated"] is True
    assert material["readfeel_blockers_routed_to_p5_repair"] is True
    assert material["readfeel_blockers_not_routed_to_p8_material"] is True
    assert material["execution_blockers_routed_to_operation_blocked"] is True
    assert material["execution_blockers_not_mixed_into_p5_quality"] is True
    assert material["readfeel_blockers_routed_to_p8_material"] is False
    assert material["execution_blockers_mixed_into_p5_quality"] is False
    assert material["question_need_observation_normalization_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR14_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR13_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch(material)

    readfeel_row = material["readfeel_blocker_rows"][0]
    execution_row = material["execution_blocker_rows"][0]
    assert readfeel_row["blocker_kind"] == ahr.P7_R54_AHR13_READFEEL_BLOCKER_KIND_REF
    assert readfeel_row["routes_to"] == ahr.P7_R54_AHR13_READFEEL_ROUTE_REF
    assert execution_row["blocker_kind"] == ahr.P7_R54_AHR13_EXECUTION_BLOCKER_KIND_REF
    assert execution_row["routes_to"] == ahr.P7_R54_AHR13_EXECUTION_ROUTE_REF
    assert_bodyfree_row(readfeel_row)
    assert_bodyfree_row(execution_row)


def test_r54_ahr13_blocks_free_text_blocker_key_in_rating_row() -> None:
    rating = build_valid_ahr12_rating()
    mutated_rating = deepcopy(rating)
    mutated_rating["rating_rows"][0]["blocker_free_text"] = "free text must not be exported"
    material = ahr.build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=mutated_rating,
        review_session_id=mutated_rating["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True
    assert material["blocker_ingestion_status_ref"] == ahr.P7_R54_AHR13_BLOCKED_STATUS_REF
    assert "rating_row_01_contains_free_text_blocker_key" in material["execution_blocker_ids"]
    assert material["blocker_rows"] == []
    assert material["blocker_row_count"] == 0
    assert material["question_need_observation_normalization_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR13_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_review_evidence_complete", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr12_rejects_premature_completion_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr12_rating()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr12_rating_row_normalization_contract(mutated)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_review_evidence_complete", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("readfeel_blockers_routed_to_p8_material", True),
        ("execution_blockers_mixed_into_p5_quality", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr13_rejects_premature_completion_or_boundary_mutations(field: str, bad_value: object) -> None:
    material = ahr.build_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=build_valid_ahr12_rating()
    )
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr13_readfeel_blocker_execution_blocker_ingestion_contract(mutated)


def test_r54_ahr12_ahr13_design_aliases_point_to_canonical_helpers() -> None:
    intake = build_valid_ahr11_intake()
    rating = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr12_rating_row_normalization(
        sanitized_review_result_intake=intake,
        review_session_id=intake["review_session_id"],
    )
    blockers = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr13_readfeel_blocker_execution_blocker_ingestion(
        rating_row_normalization=rating,
        review_session_id=rating["review_session_id"],
    )

    assert rating["rating_row_normalization_status_ref"] == ahr.P7_R54_AHR12_NORMALIZED_STATUS_REF
    assert blockers["blocker_ingestion_status_ref"] == ahr.P7_R54_AHR13_INGESTED_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr12_rating_row_normalization_contract(rating) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr13_readfeel_blocker_execution_blocker_ingestion_contract(blockers) is True
