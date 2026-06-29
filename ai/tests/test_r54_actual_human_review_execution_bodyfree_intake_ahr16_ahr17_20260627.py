# -*- coding: utf-8 -*-
"""Tests for R54-AHR16/AHR17 body-free pause/disposal boundaries."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as ahr
from test_r54_actual_human_review_execution_bodyfree_intake_ahr14_ahr15_20260627 import (
    build_valid_ahr14_question_normalization,
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

PROMOTION_FALSE_FLAGS = (
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "actual_r52_reintake_execution_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
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
    "rn_ui_changed",
    "rn_visible_contract_changed",
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
)


def assert_bodyfree_and_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in BODY_FREE_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in PROMOTION_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key
    for key in NO_TOUCH_FALSE_FLAGS:
        if key in material:
            assert material[key] is False, key


def build_valid_ahr15_guard() -> dict[str, object]:
    question_material = build_valid_ahr14_question_normalization()
    guard = ahr.build_p7_r54_ahr15_rating_question_consistency_guard(
        question_need_observation_normalization=question_material,
        review_session_id=question_material["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr15_rating_question_consistency_guard_contract(guard) is True
    assert guard["consistency_guard_status_ref"] == ahr.P7_R54_AHR15_PASSED_STATUS_REF
    return guard


def build_valid_ahr16_protocol(
    *,
    review_lifecycle_status_ref: str = ahr.P7_R54_AHR16_DEFAULT_REVIEW_LIFECYCLE_STATUS_REF,
    purge_plan_present: bool = True,
) -> dict[str, object]:
    guard = build_valid_ahr15_guard()
    protocol = ahr.build_p7_r54_ahr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=guard,
        review_lifecycle_status_ref=review_lifecycle_status_ref,
        purge_plan_present=purge_plan_present,
        review_session_id=guard["review_session_id"],
    )
    assert ahr.assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract(protocol) is True
    return protocol


def test_r54_ahr16_default_blocks_without_passed_ahr15_guard() -> None:
    material = ahr.build_p7_r54_ahr16_pause_abort_expiration_protocol()

    assert ahr.assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract(material) is True
    assert material["pause_abort_expiration_protocol_status_ref"] == ahr.P7_R54_AHR16_PROTOCOL_BLOCKED_STATUS_REF
    assert "ahr15_pause_abort_expiration_protocol_not_allowed" in material["execution_blocker_ids"]
    assert material["purge_disposal_receipt_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR16_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR15_IMPLEMENTED_STEPS
    assert_bodyfree_and_no_promotion(material)


def test_r54_ahr16_freezes_completed_purge_required_fail_closed_protocol() -> None:
    material = build_valid_ahr16_protocol()

    assert material["schema_version"] == ahr.P7_R54_AHR16_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR16_STEP_REF
    assert material["pause_abort_expiration_protocol_status_ref"] == ahr.P7_R54_AHR16_PROTOCOL_READY_STATUS_REF
    assert material["review_lifecycle_status_ref"] == "COMPLETED_PURGE_REQUIRED"
    assert material["purge_plan_required_for_current_status"] is True
    assert material["purge_plan_present"] is True
    assert material["fail_closed_on_pause_abort_expiration"] is True
    assert material["body_full_packet_must_not_remain_unhandled"] is True
    assert material["body_full_packet_disposal_required_next"] is True
    assert material["reviewer_local_notes_disposal_required_next"] is True
    assert material["temporary_form_disposal_required_next"] is True
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["actual_human_review_executed_by_person"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_receipt_materialized_here"] is False
    assert material["purge_disposal_receipt_allowed_next"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR17_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR16_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_and_no_promotion(material)


@pytest.mark.parametrize(
    "status_ref",
    [
        "PAUSED_LOCAL_ONLY",
        "ABORTED_PURGE_REQUIRED",
        "EXPIRED_PURGE_REQUIRED",
        "COMPLETED_PURGE_REQUIRED",
    ],
)
def test_r54_ahr16_pause_abort_expiration_statuses_require_and_allow_purge(status_ref: str) -> None:
    material = build_valid_ahr16_protocol(review_lifecycle_status_ref=status_ref)

    assert material["review_lifecycle_status_ref"] == status_ref
    assert material["purge_plan_required_for_current_status"] is True
    assert material["purge_plan_present"] is True
    assert material["purge_disposal_receipt_allowed_next"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR17_STEP_REF
    assert_bodyfree_and_no_promotion(material)


def test_r54_ahr16_running_status_waits_without_disposal_receipt_claim() -> None:
    material = build_valid_ahr16_protocol(review_lifecycle_status_ref="RUNNING")

    assert material["pause_abort_expiration_protocol_status_ref"] == ahr.P7_R54_AHR16_PROTOCOL_READY_STATUS_REF
    assert material["purge_plan_required_for_current_status"] is False
    assert material["purge_disposal_receipt_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR16_WAITING_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_and_no_promotion(material)


def test_r54_ahr16_blocks_pause_without_purge_plan() -> None:
    material = build_valid_ahr16_protocol(review_lifecycle_status_ref="PAUSED_LOCAL_ONLY", purge_plan_present=False)

    assert material["pause_abort_expiration_protocol_status_ref"] == ahr.P7_R54_AHR16_PROTOCOL_BLOCKED_STATUS_REF
    assert "purge_plan_missing_for_pause_abort_expiration_status" in material["execution_blocker_ids"]
    assert material["purge_disposal_receipt_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR16_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR15_IMPLEMENTED_STEPS
    assert_bodyfree_and_no_promotion(material)


def test_r54_ahr17_default_blocks_without_valid_ahr16_protocol() -> None:
    material = ahr.build_p7_r54_ahr17_purge_disposal_receipt()

    assert ahr.assert_p7_r54_ahr17_purge_disposal_receipt_contract(material) is True
    assert material["purge_disposal_receipt_status_ref"] == ahr.P7_R54_AHR17_DISPOSAL_BLOCKED_STATUS_REF
    assert "ahr16_purge_disposal_receipt_not_allowed" in material["execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["body_free_post_review_summary_allowed_next"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR16_IMPLEMENTED_STEPS
    assert_bodyfree_and_no_promotion(material)


def test_r54_ahr17_intakes_bodyfree_disposal_verified_receipt() -> None:
    protocol = build_valid_ahr16_protocol()
    material = ahr.build_p7_r54_ahr17_purge_disposal_receipt(pause_abort_expiration_protocol=protocol)

    assert ahr.assert_p7_r54_ahr17_purge_disposal_receipt_contract(material) is True
    assert material["schema_version"] == ahr.P7_R54_AHR17_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert material["operation_step_ref"] == ahr.P7_R54_AHR17_STEP_REF
    assert material["purge_disposal_receipt_status_ref"] == ahr.P7_R54_AHR17_DISPOSAL_READY_STATUS_REF
    assert material["disposal_status_ref"] == "DISPOSAL_VERIFIED"
    assert material["disposal_verified"] is True
    assert material["disposal_receipt_intaken_here"] is True
    assert material["disposal_receipt_bodyfree_only"] is True
    assert material["body_removed"] is True
    assert material["body_full_packet_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["temporary_form_removed"] is True
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_post_review_summary_allowed_next"] is True
    assert material["next_required_step"] == ahr.P7_R54_AHR18_STEP_REF
    assert tuple(material["implemented_steps"]) == ahr.P7_R54_AHR17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ahr.P7_R54_AHR17_NOT_YET_IMPLEMENTED_STEPS
    assert_bodyfree_and_no_promotion(material)


def test_r54_ahr17_allows_expired_purged_receipt_without_p8_or_release_promotion() -> None:
    protocol = build_valid_ahr16_protocol(review_lifecycle_status_ref="EXPIRED_PURGE_REQUIRED")
    material = ahr.build_p7_r54_ahr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=protocol,
        disposal_status_ref="EXPIRED_PURGED",
    )

    assert ahr.assert_p7_r54_ahr17_purge_disposal_receipt_contract(material) is True
    assert material["purge_disposal_receipt_status_ref"] == ahr.P7_R54_AHR17_DISPOSAL_READY_STATUS_REF
    assert material["disposal_status_ref"] == "EXPIRED_PURGED"
    assert material["disposal_verified"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert_bodyfree_and_no_promotion(material)


@pytest.mark.parametrize(
    "kwargs,expected_blocker",
    [
        ({"body_removed": False}, "body_removed_false"),
        ({"reviewer_notes_removed": False}, "reviewer_notes_removed_false"),
        ({"temporary_form_removed": False}, "temporary_form_removed_false"),
        ({"disposal_status_ref": "DISPOSAL_UNKNOWN"}, "disposal_status_not_allowed"),
        ({"local_packet_exported": True}, "local_packet_exported_true"),
        ({"content_hash_of_body_stored": True}, "content_hash_of_body_stored_true"),
    ],
)
def test_r54_ahr17_blocks_invalid_disposal_receipts_bodyfree(kwargs: dict[str, object], expected_blocker: str) -> None:
    protocol = build_valid_ahr16_protocol()
    material = ahr.build_p7_r54_ahr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=protocol,
        **kwargs,
    )

    assert ahr.assert_p7_r54_ahr17_purge_disposal_receipt_contract(material) is True
    assert material["purge_disposal_receipt_status_ref"] == ahr.P7_R54_AHR17_DISPOSAL_BLOCKED_STATUS_REF
    assert expected_blocker in material["execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["body_free_post_review_summary_allowed_next"] is False
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["next_required_step"] == ahr.P7_R54_AHR17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_bodyfree_and_no_promotion(material)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_review_evidence_complete", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("local_packet_exported", True),
        ("body_full_packet_content_included", True),
    ],
)
def test_r54_ahr16_rejects_premature_completion_or_bodyfull_mutations(field: str, bad_value: object) -> None:
    material = build_valid_ahr16_protocol()
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr16_pause_abort_expiration_protocol_contract(mutated)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("actual_review_evidence_complete", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("raw_body_included", True),
        ("question_text_included", True),
        ("local_absolute_path_included", True),
    ],
)
def test_r54_ahr17_rejects_completion_promotion_or_body_leak_mutations(field: str, bad_value: object) -> None:
    protocol = build_valid_ahr16_protocol()
    material = ahr.build_p7_r54_ahr17_purge_disposal_receipt(pause_abort_expiration_protocol=protocol)
    mutated = deepcopy(material)
    mutated[field] = bad_value

    with pytest.raises(ValueError):
        ahr.assert_p7_r54_ahr17_purge_disposal_receipt_contract(mutated)


def test_r54_ahr16_ahr17_design_aliases_point_to_canonical_helpers() -> None:
    guard = build_valid_ahr15_guard()
    protocol = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=guard,
        review_session_id=guard["review_session_id"],
    )
    disposal = ahr.build_p7_r54_actual_human_review_execution_bodyfree_intake_ahr17_purge_disposal_receipt(
        pause_abort_expiration_protocol=protocol,
        review_session_id=protocol["review_session_id"],
    )

    assert protocol["pause_abort_expiration_protocol_status_ref"] == ahr.P7_R54_AHR16_PROTOCOL_READY_STATUS_REF
    assert disposal["purge_disposal_receipt_status_ref"] == ahr.P7_R54_AHR17_DISPOSAL_READY_STATUS_REF
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr16_pause_abort_expiration_protocol_contract(protocol) is True
    assert ahr.assert_p7_r54_actual_human_review_execution_bodyfree_intake_ahr17_purge_disposal_receipt_contract(disposal) is True
