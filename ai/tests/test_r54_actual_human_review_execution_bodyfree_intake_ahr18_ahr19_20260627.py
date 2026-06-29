# -*- coding: utf-8 -*-
"""Tests for R54-AHR18/AHR19 body-free post-review and P5 decision separation."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
from test_r54_actual_human_review_execution_bodyfree_intake_ahr14_ahr15_20260627 import (
    build_valid_ahr12_rating,
    build_valid_ahr13_blockers,
    build_valid_ahr14_question_normalization,
)
from test_r54_actual_human_review_execution_bodyfree_intake_ahr16_ahr17_20260627 import (
    build_valid_ahr16_protocol,
)


BODY_FREE_FALSE_FLAGS = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "body_full_packet_content_included",
    "packet_content_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)

NO_TOUCH_FALSE_FLAGS = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "response_shape_changed",
    "db_schema_changed",
    "db_migration_added",
    "db_physical_schema_changed",
    "rn_ui_changed",
    "rn_visible_contract_changed",
    "public_response_key_changed",
    "public_response_top_level_key_added",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_answer_persistence_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "body_full_packet_generation_started_here",
    "body_full_packet_generation_requested_here",
    "body_full_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_r52_reintake_execution_confirmed",
)

PRODUCT_PROMOTION_FALSE_FLAGS = (
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_real_device_modal_verified",
)


def assert_bodyfree_no_touch_no_final_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in BODY_FREE_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in NO_TOUCH_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in PRODUCT_PROMOTION_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key


def build_valid_ahr15_guard(
    *,
    p8_candidate_index: int | None = None,
    repair_index: int | None = None,
    execution_blocker_index: int | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    rating = build_valid_ahr12_rating(
        p8_candidate_index=p8_candidate_index,
        repair_index=repair_index,
        execution_blocker_index=execution_blocker_index,
    )
    blockers = build_valid_ahr13_blockers(rating=rating)
    question = build_valid_ahr14_question_normalization(rating=rating, blockers=blockers)
    guard = ahr.build_p7_r54_ahr15_rating_question_consistency_guard(
        question_need_observation_normalization=question,
        review_session_id=rating["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(guard) is True
    assert guard["consistency_guard_status_ref"] == ahr.P7_R54_AHR15_PASSED_STATUS_REF
    return rating, blockers, question, guard


def build_valid_ahr18_summary(
    *,
    p8_candidate_index: int | None = None,
    repair_index: int | None = None,
    execution_blocker_index: int | None = None,
    disposal_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    rating, blockers, question, guard = build_valid_ahr15_guard(
        p8_candidate_index=p8_candidate_index,
        repair_index=repair_index,
        execution_blocker_index=execution_blocker_index,
    )
    protocol = build_valid_ahr16_protocol()
    disposal = ahr.build_p7_r54_ahr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=protocol,
        **(disposal_overrides or {}),
    )
    summary = ahr.build_p7_r54_ahr18_bodyfree_post_review_summary(
        purge_disposal_receipt=disposal,
        rating_row_normalization=rating,
        readfeel_execution_blocker_ingestion=blockers,
        question_need_observation_normalization=question,
        rating_question_consistency_guard=guard,
        review_session_id=rating["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr18_bodyfree_post_review_summary_contract(summary) is True
    return summary


def test_r54_ahr18_default_blocks_without_disposal_or_rows() -> None:
    material = ahr.build_p7_r54_ahr18_bodyfree_post_review_summary()

    assert ahr.assert_p7_r54_ahr18_bodyfree_post_review_summary_contract(material) is True
    assert material["post_review_summary_status_ref"] == ahr.P7_R54_AHR18_BLOCKED_STATUS_REF
    assert "ahr17_purge_disposal_receipt_not_ready" in material["execution_blocker_ids"]
    assert material["reviewed_case_count"] == 0
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR18_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR17_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr18_summarizes_clean_bodyfree_post_review_result() -> None:
    material = build_valid_ahr18_summary()

    assert material["schema_version"] == ahr.P7_R54_AHR18_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR18_STEP_REF
    assert material["post_review_summary_status_ref"] == ahr.P7_R54_AHR18_READY_STATUS_REF
    assert material["post_review_summary_reason_refs"] == [ahr.P7_R54_AHR18_READY_REASON_REF]
    assert material["reviewed_case_count"] == 24
    assert material["sanitized_review_result_row_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["verdict_counts"] == {
        "PASS": 24,
        "YELLOW": 0,
        "REPAIR_REQUIRED": 0,
        "RED": 0,
        "BLOCKED": 0,
        "NOT_REVIEWABLE": 0,
    }
    assert material["axis_score_averages"] == {axis_ref: 1.0 for axis_ref in ahr.P7_R54_AHR05_RATING_AXIS_REFS}
    assert all(material["axis_score_average_target_passed_by_axis"].values())
    assert material["all_axis_score_averages_meet_targets"] is True
    assert material["below_target_axis_ref_count"] == 0
    assert material["open_readfeel_blocker_count"] == 0
    assert material["open_execution_blocker_count"] == 0
    assert material["p8_material_candidate_row_count"] == 0
    assert material["disposal_verified"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["p5_decision_candidate_separation_allowed_next"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR19_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR18_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "disposal_overrides,expected_reason",
    [
        ({"body_removed": False}, "ahr17_purge_disposal_receipt_not_ready"),
        ({"reviewer_notes_removed": False}, "ahr17_purge_disposal_receipt_not_ready"),
        ({"local_packet_exported": True}, "ahr17_purge_disposal_receipt_not_ready"),
    ],
)
def test_r54_ahr18_blocks_invalid_or_exported_disposal_receipts(
    disposal_overrides: dict[str, object],
    expected_reason: str,
) -> None:
    material = build_valid_ahr18_summary(disposal_overrides=disposal_overrides)

    assert material["post_review_summary_status_ref"] == ahr.P7_R54_AHR18_BLOCKED_STATUS_REF
    assert expected_reason in material["execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR18_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr18_preserves_p8_material_count_without_starting_p8() -> None:
    material = build_valid_ahr18_summary(p8_candidate_index=3)

    assert material["post_review_summary_status_ref"] == ahr.P7_R54_AHR18_READY_STATUS_REF
    assert material["p8_material_candidate_row_count"] == 1
    assert material["plus_single_question_candidate_row_count"] == 1
    assert material["premium_deep_dive_candidate_row_count"] == 0
    assert material["p8_start_allowed"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["actual_review_evidence_complete"] is True
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("raw_body_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("packet_content_included", True),
        ("actual_human_review_run_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_ahr18_rejects_body_question_path_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr18_summary()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr18_bodyfree_post_review_summary_contract(mutated)


def test_r54_ahr19_default_blocks_without_valid_summary() -> None:
    material = ahr.build_p7_r54_ahr19_p5_decision_candidate_separation()

    assert ahr.assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(material) is True
    assert material["p5_decision_candidate_separation_status_ref"] == ahr.P7_R54_AHR19_BLOCKED_STATUS_REF
    assert "ahr18_bodyfree_post_review_summary_not_ready" in material["execution_blocker_ids"]
    assert material["decision_candidate_ref"] == ahr.P7_R54_AHR19_OPERATION_INCONCLUSIVE_REF
    assert material["decision_candidate_separated_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR19_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr19_separates_clean_p5_confirmed_candidate_without_final_promotion() -> None:
    summary = build_valid_ahr18_summary()
    material = ahr.build_p7_r54_ahr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=summary,
        review_session_id=summary["review_session_id"],
    )

    assert ahr.assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR19_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR19_STEP_REF
    assert material["p5_decision_candidate_separation_status_ref"] == ahr.P7_R54_AHR19_READY_STATUS_REF
    assert material["decision_candidate_ref"] == ahr.P7_R54_AHR19_P5_CONFIRMED_CANDIDATE_REF
    assert material["decision_candidate_separated_here"] is True
    assert material["p5_confirmed_candidate_conditions_satisfied"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate_only_allowed_later"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR20_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR19_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR19_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr19_routes_readfeel_or_rating_repair_to_p5_repair_return() -> None:
    summary = build_valid_ahr18_summary(repair_index=5)
    material = ahr.build_p7_r54_ahr19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)

    assert ahr.assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(material) is True
    assert material["p5_decision_candidate_separation_status_ref"] == ahr.P7_R54_AHR19_READY_STATUS_REF
    assert material["decision_candidate_ref"] == ahr.P7_R54_AHR19_P5_REPAIR_RETURN_REF
    assert material["p5_repair_return_required"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["open_readfeel_blocker_count"] == 1
    assert material["repair_required_case_count"] == 1
    assert material["p5_repair_required_observation_row_count"] == 1
    assert material["next_required_step"] == ahr.P7_R54_AHR19_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


def test_r54_ahr19_routes_execution_blocker_to_operation_blocked_not_p5_quality() -> None:
    summary = build_valid_ahr18_summary(execution_blocker_index=7)
    material = ahr.build_p7_r54_ahr19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)

    assert ahr.assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(material) is True
    assert material["p5_decision_candidate_separation_status_ref"] == ahr.P7_R54_AHR19_READY_STATUS_REF
    assert material["decision_candidate_ref"] == ahr.P7_R54_AHR19_OPERATION_BLOCKED_PREFLIGHT_REF
    assert material["r54_operation_blocked_preflight_or_execution"] is True
    assert material["p5_repair_return_required"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["open_execution_blocker_count"] == 1
    assert material["next_required_step"] == ahr.P7_R54_AHR19_OPERATION_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_no_touch_no_final_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("raw_body_included", True),
        ("question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("actual_human_review_run_here", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
    ],
)
def test_r54_ahr19_rejects_body_question_path_or_final_promotion_mutations(field: str, bad_value: object) -> None:
    summary = build_valid_ahr18_summary()
    material = ahr.build_p7_r54_ahr19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr19_p5_decision_candidate_separation_contract(mutated)


def test_r54_ahr18_ahr19_design_aliases_point_to_canonical_helpers() -> None:
    summary = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr18_bodyfree_post_review_summary()
    decision = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=summary,
        review_session_id=summary["review_session_id"],
    )

    assert summary["post_review_summary_status_ref"] == ahr.P7_R54_AHR18_BLOCKED_STATUS_REF
    assert decision["p5_decision_candidate_separation_status_ref"] == ahr.P7_R54_AHR19_BLOCKED_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr18_bodyfree_post_review_summary_contract(summary) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr19_p5_decision_candidate_separation_contract(decision) is True
