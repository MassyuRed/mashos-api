# -*- coding: utf-8 -*-
"""R54-AHR-CS14/CS15 current snapshot actual review re-entry contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

import emlis_ai_p7_r54_ahr_current_snapshot_actual_review_reentry_20260628 as cs
from test_r54_ahr_current_snapshot_actual_review_reentry_cs12_cs13_20260628 import _build_ready_cs13


FORBIDDEN_BODY_OR_QUESTION_KEYS = (
    "raw_input", "raw_body", "returned_emlis_body", "history_surface",
    "comment_text", "comment_text_body", "reviewer_free_text", "reviewer_note",
    "reviewer_notes", "reviewer_notes_body", "question_text", "draft_question_text",
    "raw_question_answer", "body_full_packet_content", "packet_content",
    "local_absolute_path", "local_file_path", "body_hash", "terminal_output_body",
    "stdout_body", "stderr_body", "traceback_body",
)


def _assert_bodyfree_no_touch_allowing(material: dict[str, Any], allowed_true_flags: tuple[str, ...]) -> None:
    assert material["body_free"] is True
    for key in cs.P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key in allowed_true_flags:
            continue
        assert material[key] is False, key
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        assert material[flag_map_key]
        assert all(value is False for value in material[flag_map_key].values()), flag_map_key
    for forbidden_key in FORBIDDEN_BODY_OR_QUESTION_KEYS:
        assert forbidden_key not in material


def _ready_cs14_kwargs() -> dict[str, Any]:
    return {
        "rating_question_consistency_guard": _build_ready_cs13(),
        "disposal_receipt_ref": cs.P7_R54_AHR_CS14_DISPOSAL_RECEIPT_REF_DEFAULT,
        "disposal_receipt_present": True,
        "disposal_verified": True,
        "body_full_packet_deleted_or_purged_ref": True,
        "reviewer_notes_deleted_or_not_created_ref": True,
        "packet_lifecycle_closed_bodyfree": True,
    }


def _build_ready_cs14() -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt(**_ready_cs14_kwargs())
    assert cs.assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract(material) is True
    return material


def _build_ready_cs15() -> dict[str, Any]:
    material = cs.build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete(
        pause_abort_expiration_disposal_receipt=_build_ready_cs14()
    )
    assert cs.assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract(material) is True
    return material


def test_cs00_to_cs13_ready_path_is_present_before_cs14_cs15() -> None:
    cs13 = _build_ready_cs13()
    assert cs13["consistency_guard_status_ref"] == cs.P7_R54_AHR_CS13_PASSED_STATUS_REF
    assert cs13["question_need_observation_row_count"] == cs.P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    assert cs13["rating_question_consistency_guard_passed"] is True
    assert cs13["pause_abort_expiration_disposal_receipt_allowed_next"] is True
    assert cs13["actual_review_evidence_complete"] is False
    assert cs13["next_required_step"] == cs.P7_R54_AHR_CS14_STEP_REF
    assert cs.assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(cs13) is True


def test_cs14_default_is_fail_closed_without_ready_cs13_or_disposal_receipt() -> None:
    material = cs.build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt()
    assert material["disposal_receipt_status_ref"] == cs.P7_R54_AHR_CS14_BLOCKED_STATUS_REF
    for blocker in (
        "cs13_rating_question_consistency_guard_not_ready_for_disposal_receipt",
        "disposal_receipt_present_not_true",
        "disposal_verified_not_true",
        "body_full_packet_deleted_or_purged_ref_not_true",
        "reviewer_notes_deleted_or_not_created_ref_not_true",
        "packet_lifecycle_closed_bodyfree_not_true",
    ):
        assert blocker in material["execution_blocker_ids"]
    assert material["packet_lifecycle_closed_bodyfree"] is False
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["bodyfree_post_review_summary_allowed_next"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS14_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract(material) is True


def test_cs14_ready_closes_packet_lifecycle_without_completing_evidence() -> None:
    material = _build_ready_cs14()
    assert set(material) == set(cs.P7_R54_AHR_CS14_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS14_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS14_STEP_REF
    assert material["cs13_next_required_step"] == cs.P7_R54_AHR_CS14_STEP_REF
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["disposal_receipt_status_ref"] == cs.P7_R54_AHR_CS14_VERIFIED_STATUS_REF
    assert material["disposal_receipt_reason_refs"] == [cs.P7_R54_AHR_CS14_READY_REASON_REF]
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["rating_question_consistency_guard_ready_for_disposal"] is True
    assert material["packet_lifecycle_closed_bodyfree"] is True
    assert material["packet_lifecycle_status_ref"] == cs.P7_R54_AHR_CS14_PACKET_LIFECYCLE_STATUS_CLOSED_REF
    assert material["disposal_receipt_present"] is True
    assert material["disposal_verified"] is True
    assert material["body_full_packet_deleted_or_purged_ref"] is True
    assert material["reviewer_notes_deleted_or_not_created_ref"] is True
    assert material["disposal_receipt_bodyfree_only"] is True
    assert material["disposal_receipt_refs_only"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["bodyfree_post_review_summary_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS15_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS14_ALLOWED_TRUE_FALSE_FLAG_REFS)


@pytest.mark.parametrize(
    "field, blocker",
    (
        ("disposal_receipt_present", "disposal_receipt_present_not_true"),
        ("disposal_verified", "disposal_verified_not_true"),
        ("body_full_packet_deleted_or_purged_ref", "body_full_packet_deleted_or_purged_ref_not_true"),
        ("reviewer_notes_deleted_or_not_created_ref", "reviewer_notes_deleted_or_not_created_ref_not_true"),
        ("packet_lifecycle_closed_bodyfree", "packet_lifecycle_closed_bodyfree_not_true"),
    ),
)
def test_cs14_blocks_each_required_disposal_true_field_when_missing(field: str, blocker: str) -> None:
    kwargs = _ready_cs14_kwargs()
    kwargs[field] = False
    material = cs.build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt(**kwargs)
    assert material["disposal_receipt_status_ref"] == cs.P7_R54_AHR_CS14_BLOCKED_STATUS_REF
    assert blocker in material["execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["bodyfree_post_review_summary_allowed_next"] is False
    assert cs.assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract(material) is True


@pytest.mark.parametrize(
    "leak_field, blocker",
    (
        ("body_full_packet_content_included", "body_full_packet_content_included_must_remain_false"),
        ("reviewer_notes_body_included", "reviewer_notes_body_included_must_remain_false"),
        ("local_path_included", "local_path_included_must_remain_false"),
        ("local_absolute_path_included", "local_absolute_path_included_must_remain_false"),
        ("body_hash_included", "body_hash_included_must_remain_false"),
        ("terminal_output_body_included", "terminal_output_body_included_must_remain_false"),
        ("stdout_body_included", "stdout_body_included_must_remain_false"),
        ("stderr_body_included", "stderr_body_included_must_remain_false"),
        ("traceback_body_included", "traceback_body_included_must_remain_false"),
    ),
)
def test_cs14_blocks_leak_flags_but_does_not_copy_body_values(leak_field: str, blocker: str) -> None:
    kwargs = _ready_cs14_kwargs()
    kwargs[leak_field] = True
    material = cs.build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt(**kwargs)
    assert material["disposal_receipt_status_ref"] == cs.P7_R54_AHR_CS14_BLOCKED_STATUS_REF
    assert blocker in material["execution_blocker_ids"]
    assert material[leak_field] is False
    assert cs.assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract(material) is True


def test_cs14_rejects_mutated_evidence_complete_flag() -> None:
    material = _build_ready_cs14()
    mutated = deepcopy(material)
    mutated["actual_review_evidence_complete"] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract(mutated)


def test_cs14_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs14()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_disposal_receipt_bodyfree(**_ready_cs14_kwargs())
    assert alias == primary
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_disposal_receipt_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs14_disposal_contract(alias) is True


def test_cs15_default_is_fail_closed_without_verified_cs14() -> None:
    material = cs.build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete()
    assert material["post_review_summary_status_ref"] == cs.P7_R54_AHR_CS15_INCOMPLETE_STATUS_REF
    for blocker in (
        "cs14_disposal_receipt_not_verified_for_post_review_summary",
        "reviewed_case_count_not_24",
        "rating_row_count_not_24",
        "question_observation_row_count_not_24",
    ):
        assert blocker in material["execution_blocker_ids"]
    assert material["reviewed_case_count"] == 0
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["no_body_leak_validation_passed"] is False
    assert material["no_question_text_validation_passed"] is False
    assert material["no_touch_validation_passed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert material["next_required_step"] == cs.P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, ())
    assert cs.assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract(material) is True


def test_cs15_ready_marks_bodyfree_evidence_complete_but_not_later_phase() -> None:
    material = _build_ready_cs15()
    assert set(material) == set(cs.P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == cs.P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_SCHEMA_VERSION
    assert material["policy_section"] == cs.P7_R54_AHR_CS15_STEP_REF
    assert material["operation_step_ref"] == cs.P7_R54_AHR_CS15_STEP_REF
    assert material["cs14_next_required_step"] == cs.P7_R54_AHR_CS15_STEP_REF
    assert material["current_basis_ref"] == cs.P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF
    assert material["historical_basis_ref"] == cs.P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
    assert material["post_review_summary_status_ref"] == cs.P7_R54_AHR_CS15_COMPLETE_STATUS_REF
    assert material["post_review_summary_reason_refs"] == [cs.P7_R54_AHR_CS15_COMPLETE_REASON_REF]
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["review_counts_complete"] is True
    assert material["rating_counts_complete"] is True
    assert material["question_observation_counts_complete"] is True
    assert material["disposal_evidence_complete"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_human_review_complete"] is False
    assert material["actual_r52_reintake_execution_confirmed"] is False
    assert material["r52_reintake_handoff_ready_here"] is False
    assert material["p5_confirmed_candidate_not_finalized_here"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["p5_decision_candidate_separation_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == cs.P7_R54_AHR_CS15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == cs.P7_R54_AHR_CS15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == cs.P7_R54_AHR_CS16_STEP_REF
    _assert_bodyfree_no_touch_allowing(material, cs.P7_R54_AHR_CS15_ALLOWED_TRUE_FALSE_FLAG_REFS)


@pytest.mark.parametrize(
    "promotion_flag",
    (
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_handoff_ready_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ),
)
def test_cs15_never_promotes_later_phase_or_release_flags(promotion_flag: str) -> None:
    material = _build_ready_cs15()
    assert material[promotion_flag] is False


@pytest.mark.parametrize(
    "mutation_key",
    (
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_handoff_ready_here",
        "p5_human_blind_qa_confirmed_final",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ),
)
def test_cs15_rejects_mutated_later_phase_flags(mutation_key: str) -> None:
    material = _build_ready_cs15()
    mutated = deepcopy(material)
    mutated[mutation_key] = True
    with pytest.raises(ValueError):
        cs.assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract(mutated)


def test_cs15_blocks_when_cs14_disposal_receipt_is_not_verified() -> None:
    cs14 = _build_ready_cs14()
    cs14["disposal_receipt_status_ref"] = cs.P7_R54_AHR_CS14_BLOCKED_STATUS_REF
    material = cs.build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete(
        pause_abort_expiration_disposal_receipt=cs14
    )
    assert material["post_review_summary_status_ref"] == cs.P7_R54_AHR_CS15_INCOMPLETE_STATUS_REF
    assert material["actual_review_evidence_complete"] is False
    assert "cs14_disposal_receipt_not_verified_for_post_review_summary" in material["execution_blocker_ids"]
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert cs.assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract(material) is True


def test_cs15_aliases_match_primary_builder_and_contract() -> None:
    primary = _build_ready_cs15()
    alias = cs.build_p7_r54_ahr_current_snapshot_actual_review_reentry_post_review_summary_bodyfree(
        pause_abort_expiration_disposal_receipt=_build_ready_cs14()
    )
    assert alias == primary
    assert cs.assert_p7_r54_ahr_current_snapshot_actual_review_reentry_post_review_summary_bodyfree_contract(alias) is True
    assert cs.assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_contract(alias) is True
