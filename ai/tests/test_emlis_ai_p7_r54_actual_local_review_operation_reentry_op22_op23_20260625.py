# -*- coding: utf-8 -*-
"""R54 actual local-only review operation re-entry OP22/OP23 contract tests."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op20_op21_20260625 import (
    _op20_ready,
    _op20_ready_with_single_p8_material_candidate,
)


def _assert_bodyfree_no_question_start_or_release(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    forbidden_tokens = (
        '"raw_input"',
        '"comment_text":',
        '"returned_emlis_body"',
        '"bounded_history_surface"',
        '"reviewer_free_text":',
        '"reviewer_notes_body"',
        '"local_path":',
        '"body_hash"',
        '"body_full_packet_content"',
        '"question_text":',
        '"draft_question_text":',
        '"question_implementation_started_here": true',
        '"p8_start_allowed": true',
        '"p6_limited_human_readfeel_start_allowed": true',
        '"release_allowed": true',
    )
    for token in forbidden_tokens:
        assert token not in dumped
    assert material["body_free"] is True
    assert material["raw_body_included"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False


@lru_cache(maxsize=1)
def _cached_op21_ready_without_p8_material() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op21_p8_material_candidate_handoff(
        p6_candidate_handoff=_op20_ready()
    )
    assert op.assert_p7_r54_op21_p8_material_candidate_handoff_contract(material) is True
    return (material,)


def _op21_ready_without_p8_material() -> dict[str, object]:
    return deepcopy(_cached_op21_ready_without_p8_material()[0])


@lru_cache(maxsize=1)
def _cached_op21_ready_with_p8_material() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op21_p8_material_candidate_handoff(
        p6_candidate_handoff=_op20_ready_with_single_p8_material_candidate()
    )
    assert op.assert_p7_r54_op21_p8_material_candidate_handoff_contract(material) is True
    assert material["p8_question_design_material_candidate"] is True
    return (material,)


def _op21_ready_with_p8_material() -> dict[str, object]:
    return deepcopy(_cached_op21_ready_with_p8_material()[0])


@lru_cache(maxsize=1)
def _cached_op22_ready_without_p8_material() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_handoff=_op21_ready_without_p8_material()
    )
    assert op.assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    return (material,)


def _op22_ready_without_p8_material() -> dict[str, object]:
    return deepcopy(_cached_op22_ready_without_p8_material()[0])


@lru_cache(maxsize=1)
def _cached_op22_ready_with_p8_material() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_handoff=_op21_ready_with_p8_material()
    )
    assert op.assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    assert material["p8_question_design_material_candidate"] is True
    return (material,)


def _op22_ready_with_p8_material() -> dict[str, object]:
    return deepcopy(_cached_op22_ready_with_p8_material()[0])


def test_op22_op23_symbols_are_exported() -> None:
    expected = {
        "P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION",
        "P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION",
        "P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF",
        "P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF",
        "P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF",
        "P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF",
        "P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF",
        "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF",
        "P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF",
        "build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation",
        "assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract",
        "build_p7_r54_op23_r52_reintake_handoff",
        "assert_p7_r54_op23_r52_reintake_handoff_contract",
        "build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree",
        "build_p7_r54_operation_r52_reintake_handoff_bodyfree",
    }
    assert expected.issubset(set(op.__all__))


def test_op22_default_blocks_until_op21_ready() -> None:
    material = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation()

    assert op.assert_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation_contract(material) is True
    assert material["final_validation_status"] == op.P7_R54_OP22_FINAL_VALIDATION_BLOCKED_STATUS_REF
    assert material["final_validation_failure_class_ref"] == "op21_not_ready"
    assert material["r52_reintake_handoff_allowed_next"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == op.P7_R54_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_question_start_or_release(material)


def test_op22_ready_is_final_bodyfree_validation_only() -> None:
    material = _op22_ready_without_p8_material()

    assert material["final_validation_status"] == op.P7_R54_OP22_FINAL_VALIDATION_READY_STATUS_REF
    assert material["final_validation_ref"] == op.P7_R54_OP22_FINAL_VALIDATION_REF
    assert material["final_validation_passed"] is True
    assert material["final_validation_failure_class_ref"] == "none"
    assert material["reviewed_case_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["rating_row_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["question_observation_row_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["body_leak_violation_count"] == 0
    assert material["question_text_violation_count"] == 0
    assert material["no_touch_violation_count"] == 0
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["r52_reintake_handoff_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == op.P7_R54_OP23_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP22_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP22_NOT_YET_IMPLEMENTED_STEPS
    assert material["open_execution_blocker_ids"] == []
    _assert_bodyfree_no_question_start_or_release(material)


def test_op22_blocks_body_or_question_text_evidence_without_materializing_text() -> None:
    material = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_handoff=_op21_ready_without_p8_material(),
        body_leak_violation_refs=["body_full_packet_artifact_detected"],
        question_text_violation_refs=["question_text_artifact_detected"],
    )

    assert material["final_validation_status"] == op.P7_R54_OP22_BODY_LEAK_BLOCKED_STATUS_REF
    assert material["final_validation_failure_class_ref"] == "body_or_question_text"
    assert material["body_leak_or_question_text_violation_detected"] is True
    assert material["body_leak_violation_count"] == 1
    assert material["question_text_violation_count"] == 1
    assert material["no_body_leak_validation_passed"] is False
    assert material["no_question_text_validation_passed"] is False
    assert material["r52_reintake_handoff_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_question_start_or_release(material)


def test_op22_blocks_no_touch_validation_evidence_without_changing_contract_flags() -> None:
    material = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_handoff=_op21_ready_without_p8_material(),
        no_touch_violation_refs=["api_changed_detected"],
    )

    assert material["final_validation_status"] == op.P7_R54_OP22_NO_TOUCH_BLOCKED_STATUS_REF
    assert material["final_validation_failure_class_ref"] == "no_touch"
    assert material["no_touch_violation_detected"] is True
    assert material["no_touch_violation_count"] == 1
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is False
    assert material["api_changed"] is False
    assert material["db_changed"] is False
    assert material["rn_changed"] is False
    assert material["runtime_changed"] is False
    assert material["r52_reintake_handoff_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_question_start_or_release(material)


def test_op23_default_blocks_by_actual_review_evidence_missing() -> None:
    material = op.build_p7_r54_op23_r52_reintake_handoff()

    assert op.assert_p7_r54_op23_r52_reintake_handoff_contract(material) is True
    assert material["handoff_status"] == op.P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF
    assert material["r52_reintake_handoff_ready"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_evidence_handoff_materialized_here"] is False
    assert material["r52_reintake_required"] is False
    assert material["next_required_step"] == op.P7_R54_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    _assert_bodyfree_no_question_start_or_release(material)


def test_op23_ready_materializes_r52_reintake_handoff_bodyfree() -> None:
    material = op.build_p7_r54_op23_r52_reintake_handoff(
        final_validation=_op22_ready_without_p8_material()
    )

    assert material["handoff_status"] == op.P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    assert material["handoff_ref"] == op.P7_R54_OP23_R52_REINTAKE_HANDOFF_REF
    assert material["handoff_reason_refs"] == [op.P7_R54_OP23_READY_REASON_REF]
    assert material["r52_reintake_decision_ref"] == op.P7_R54_OP23_R52_REINTAKE_DECISION_REF
    assert material["r52_reintake_handoff_ready"] is True
    assert material["body_free_evidence_handoff_materialized_here"] is True
    assert material["r52_reintake_required"] is True
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_from_bodyfree_receipts"] is True
    assert material["rating_row_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["question_observation_row_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["rating_rows_bodyfree_handoff_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["question_observation_rows_bodyfree_handoff_count"] == op.P7_R51_REQUIRED_CASE_COUNT
    assert material["disposal_verified"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is True
    assert material["p6_candidate_only"] is True
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["r52_handoff_contains_body_full_packet"] is False
    assert material["r52_handoff_contains_question_text"] is False
    assert material["r52_handoff_contains_local_path"] is False
    assert material["r52_handoff_contains_raw_payload"] is False
    assert material["handoff_evidence_ref_count"] == len(material["handoff_evidence_refs"])
    assert material["handoff_evidence_ref_count"] > 0
    assert material["next_required_step"] == op.P7_R54_OP24_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP23_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP23_NOT_YET_IMPLEMENTED_STEPS
    assert material["open_execution_blocker_ids"] == []
    _assert_bodyfree_no_question_start_or_release(material)


def test_op23_preserves_p8_material_candidate_as_candidate_only() -> None:
    material = op.build_p7_r54_op23_r52_reintake_handoff(
        final_validation=_op22_ready_with_p8_material()
    )

    assert material["handoff_status"] == op.P7_R54_OP23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    assert material["p8_question_design_material_candidate"] is True
    assert material["p8_material_candidate_row_count"] == 1
    assert material["p8_material_candidate_only"] is True
    assert material["p8_design_material_candidate_only_not_start"] is True
    assert material["p8_start_allowed"] is False
    assert material["question_implementation_started_here"] is False
    assert material["p8_implementation_spec_finalized_here"] is False
    assert material["question_text_materialized_here"] is False
    assert material["draft_question_text_materialized_here"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    _assert_bodyfree_no_question_start_or_release(material)


def test_op23_blocks_body_leak_status_from_op22() -> None:
    op22 = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_handoff=_op21_ready_without_p8_material(),
        body_leak_violation_refs=["body_full_packet_artifact_detected"],
    )
    material = op.build_p7_r54_op23_r52_reintake_handoff(final_validation=op22)

    assert material["handoff_status"] == op.P7_R54_OP23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_evidence_handoff_materialized_here"] is False
    assert material["r52_reintake_required"] is False
    assert material["next_required_step"] == op.P7_R54_OP23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_bodyfree_no_question_start_or_release(material)


def test_op22_op23_aliases_match_primary_builders() -> None:
    op21 = _op21_ready_without_p8_material()
    primary22 = op.build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation(
        p8_material_candidate_handoff=op21
    )
    alias22 = op.build_p7_r54_operation_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
        p8_material_candidate_handoff=op21
    )
    assert primary22 == alias22

    primary23 = op.build_p7_r54_op23_r52_reintake_handoff(final_validation=primary22)
    alias23 = op.build_p7_r54_operation_r52_reintake_handoff_bodyfree(final_validation=alias22)
    assert primary23 == alias23
