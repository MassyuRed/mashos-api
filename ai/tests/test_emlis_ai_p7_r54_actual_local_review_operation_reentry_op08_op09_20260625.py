# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import P7_R51_REQUIRED_CASE_COUNT


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"local_directory_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"body_full_packet_export_allowed": true',
    '"body_full_packet_zip_inclusion_allowed": true',
    '"reviewer_notes_export_allowed": true',
    '"local_path_included": true',
    '"question_text_included": true',
    '"draft_question_text_included": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_op04_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op04_local_only_preflight(
        local_review_root_presence_ref=op.P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=op.P7_R54_OP04_PURGE_PLAN_READY_REF,
        retention_policy_ref=op.P7_R54_OP04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=op.P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF,
    )
    assert op.assert_p7_r54_op04_local_only_preflight_contract(material) is True
    return (material,)


def _op04_ready() -> dict[str, object]:
    return deepcopy(_cached_op04_ready()[0])


@lru_cache(maxsize=1)
def _cached_op05_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op05_24_case_manifest_freeze(local_only_preflight=_op04_ready())
    assert op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material) is True
    return (material,)


def _op05_ready() -> dict[str, object]:
    return deepcopy(_cached_op05_ready()[0])


@lru_cache(maxsize=1)
def _cached_op06_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op06_local_only_body_full_packet_generation_request(case_manifest_freeze=_op05_ready())
    assert op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material) is True
    return (material,)


def _op06_ready() -> dict[str, object]:
    return deepcopy(_cached_op06_ready()[0])


@lru_cache(maxsize=1)
def _cached_op07_ready() -> tuple[dict[str, object]]:
    op06 = _op06_ready()
    material = op.build_p7_r54_op07_packet_generation_local_operation(
        body_full_packet_generation_request=op06,
        local_operation_receipt_ref=op.P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF,
        declared_generated_packet_ref_ids=op06["requested_packet_ref_ids"],
    )
    assert op.assert_p7_r54_op07_packet_generation_local_operation_contract(material) is True
    return (material,)


def _op07_ready() -> dict[str, object]:
    return deepcopy(_cached_op07_ready()[0])


@lru_cache(maxsize=1)
def _cached_op08_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation=_op07_ready()
    )
    assert op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material) is True
    return (material,)


def _op08_ready() -> dict[str, object]:
    return deepcopy(_cached_op08_ready()[0])


@lru_cache(maxsize=1)
def _cached_op09_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op09_reviewer_instruction_rating_form_freeze(
        packet_completeness_export_denylist_scan=_op08_ready()
    )
    assert op.assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material) is True
    return (material,)


def _op09_ready() -> dict[str, object]:
    return deepcopy(_cached_op09_ready()[0])


def test_r54_op08_default_scan_fails_closed_when_local_operation_is_not_ready() -> None:
    material = op.build_p7_r54_op08_packet_completeness_export_denylist_scan()

    assert material["schema_version"] == op.P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP08_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP08_STEP_REF
    assert material["op07_local_operation_ready"] is False
    assert material["packet_scan_status"] == op.P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF
    assert material["packet_scan_ref"] == "packet_scan_not_ready_bodyfree"
    assert material["packet_scan_rows"] == []
    assert material["packet_scan_row_count"] == 0
    assert material["total_case_count"] == 0
    assert material["packet_present_count"] == 0
    assert material["required_fields_present_count"] == 0
    assert material["packet_completeness_ready"] is False
    assert material["reviewer_instruction_rating_form_freeze_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op08_scan_ready_counts_twenty_four_packet_refs_without_exporting_content() -> None:
    material = _op08_ready()
    op07 = _op07_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert material["op07_schema_version"] == op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION
    assert material["op07_next_required_step"] == op.P7_R54_OP08_STEP_REF
    assert material["op07_local_operation_status"] == op.P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF
    assert material["op07_local_operation_ready"] is True
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["required_case_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["packet_scan_status"] == op.P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF
    assert material["packet_scan_ref"] == op.P7_R54_OP08_PACKET_SCAN_REF
    assert material["packet_scan_reason_refs"] == [op.P7_R54_OP08_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["expected_packet_ref_ids"] == op07["expected_packet_ref_ids"]
    assert material["declared_packet_ref_ids"] == op07["declared_generated_packet_ref_ids"]
    assert material["expected_packet_ref_count"] == 24
    assert material["declared_packet_ref_count"] == 24
    assert material["declared_packet_ref_ids_unique"] is True
    assert material["packet_ref_ids_match_local_operation"] is True
    assert material["packet_scan_row_count"] == 24
    assert len(material["packet_scan_rows"]) == 24
    assert material["total_case_count"] == 24
    assert material["packet_present_count"] == 24
    assert material["required_fields_present_count"] == 24
    assert material["required_packet_field_refs"] == list(op.P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS)
    assert material["required_packet_field_ref_count"] == len(op.P7_R54_OP08_REQUIRED_PACKET_FIELD_REFS)
    assert material["packet_completeness_ready"] is True
    assert material["export_denylist_violation_refs"] == []
    assert material["export_denylist_violation_count"] == 0
    assert material["body_full_packet_export_candidate_refs"] == []
    assert material["body_full_packet_export_candidate_count"] == 0
    assert material["packet_scan_is_bodyfree_only"] is True
    assert material["packet_scan_contains_packet_content"] is False
    assert material["packet_scan_contains_local_path"] is False
    assert material["packet_scan_contains_question_text"] is False
    assert material["reviewer_instruction_rating_form_freeze_allowed_next"] is True
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_body_full_packet_generated_here"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP08_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP08_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP09_STEP_REF
    assert material["packet_scan_rows"][0]["packet_ref_id"] == op07["declared_generated_packet_ref_ids"][0]
    assert material["packet_scan_rows"][0]["packet_content_included"] is False
    assert material["packet_scan_rows"][0]["local_path_included"] is False
    assert material["packet_scan_rows"][0]["question_text_included"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op08_blocks_on_export_denylist_or_question_text_leak_without_advancing() -> None:
    material = op.build_p7_r54_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation=_op07_ready(),
        export_denylist_violation_refs=["body_full_packets.local_only/"],
        body_full_packet_export_candidate_refs=["r54_packet_export_candidate_detected_bodyfree"],
        question_text_detected_in_export=True,
    )

    assert material["packet_scan_status"] == op.P7_R54_OP08_PACKET_SCAN_BLOCKED_BY_LEAK_STATUS_REF
    assert material["reviewer_instruction_rating_form_freeze_allowed_next"] is False
    assert material["export_denylist_violation_count"] == 1
    assert material["body_full_packet_export_candidate_count"] == 1
    assert material["question_text_detected_in_export"] is True
    assert "export_denylist_violation_detected" in material["execution_blocker_ids"]
    assert "body_full_packet_export_candidate_detected" in material["execution_blocker_ids"]
    assert "question_text_detected_in_export" in material["execution_blocker_ids"]
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op07_local_operation_ready", False),
        ("op07_local_operation_status", op.P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF),
        ("declared_packet_ref_count", 23),
        ("declared_packet_ref_ids_unique", False),
        ("packet_ref_ids_match_local_operation", False),
        ("packet_scan_row_count", 23),
        ("packet_present_count", 23),
        ("required_fields_present_count", 23),
        ("required_packet_field_ref_count", 6),
        ("packet_completeness_ready", False),
        ("export_denylist_violation_count", 1),
        ("body_full_packet_export_candidate_count", 1),
        ("body_full_packet_content_detected_in_export", True),
        ("question_text_detected_in_export", True),
        ("local_path_detected_in_export", True),
        ("packet_scan_is_bodyfree_only", False),
        ("packet_scan_contains_packet_content", True),
        ("packet_scan_contains_local_path", True),
        ("packet_scan_contains_question_text", True),
        ("reviewer_instruction_rating_form_freeze_allowed_next", False),
        ("body_full_packet_content_included", True),
        ("body_full_packet_generated_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("local_review_root_path_included", True),
        ("local_packet_directory_path_included", True),
        ("local_packet_exported", True),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("p5_actual_review_still_not_run", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op08_rejects_scan_boundary_body_leak_review_claim_or_promotion_mutation(
    key: str,
    value: object,
) -> None:
    material = _op08_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material)


def test_r54_op08_rejects_scan_row_removal_or_body_boundary_mutation() -> None:
    material = _op08_ready()
    material["packet_scan_rows"] = material["packet_scan_rows"][:23]
    material["packet_scan_row_count"] = 23
    with pytest.raises(ValueError):
        op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material)

    material = _op08_ready()
    material["packet_scan_rows"][0]["packet_content_included"] = True
    with pytest.raises(ValueError):
        op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material)

    material = _op08_ready()
    material["declared_packet_ref_ids"][0] = "different-packet-ref"
    with pytest.raises(ValueError):
        op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material)


def test_r54_op09_default_form_fails_closed_when_packet_scan_is_not_ready() -> None:
    material = op.build_p7_r54_op09_reviewer_instruction_rating_form_freeze()

    assert material["schema_version"] == op.P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP09_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP09_STEP_REF
    assert material["op08_packet_scan_ready"] is False
    assert material["reviewer_instruction_status"] == op.P7_R54_OP09_FORM_BLOCKED_STATUS_REF
    assert material["reviewer_instruction_ref"] == "reviewer_instruction_not_frozen_until_packet_scan_ready"
    assert material["rating_form_ref"] == "rating_form_not_frozen_until_packet_scan_ready"
    assert material["rating_axis_refs"] == []
    assert material["rating_axis_count"] == 0
    assert material["rating_axis_target_thresholds"] == {}
    assert material["score_option_refs"] == []
    assert material["verdict_option_refs"] == []
    assert material["selection_only_form"] is False
    assert material["reviewer_instruction_materialized_here"] is False
    assert material["rating_form_materialized_here"] is False
    assert material["actual_human_review_operation_state_capture_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op09_freezes_selection_only_reviewer_instruction_and_rating_form() -> None:
    material = _op09_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert material["op08_schema_version"] == op.P7_R54_OPERATION_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert material["op08_next_required_step"] == op.P7_R54_OP09_STEP_REF
    assert material["op08_packet_scan_status"] == op.P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF
    assert material["op08_packet_scan_ready"] is True
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["required_case_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["packet_scan_row_count"] == 24
    assert material["packet_present_count"] == 24
    assert material["required_fields_present_count"] == 24
    assert material["reviewer_instruction_status"] == op.P7_R54_OP09_FORM_READY_STATUS_REF
    assert material["reviewer_instruction_ref"] == op.P7_R54_OP09_REVIEWER_INSTRUCTION_REF
    assert material["reviewer_instruction_policy_ref"] == "selection_only_no_free_text_no_question_text_no_raw_body_copy"
    assert material["rating_form_ref"] == op.P7_R54_OP09_RATING_FORM_REF
    assert material["rating_form_reason_refs"] == [op.P7_R54_OP09_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["rating_axis_refs"] == list(op.P7_R54_OP09_RATING_AXIS_REFS)
    assert material["rating_axis_count"] == 6
    assert material["rating_axis_target_thresholds"] == op.P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS
    assert material["score_option_refs"] == list(op.P7_R54_OP09_SCORE_OPTION_REFS)
    assert material["verdict_option_refs"] == list(op.P7_R54_OP09_VERDICT_OPTION_REFS)
    assert material["blocker_id_option_refs"] == list(op.P7_R54_OP09_BLOCKER_ID_OPTION_REFS)
    assert material["question_need_primary_class_options"] == list(op.P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS)
    assert material["ambiguity_kind_option_refs"] == list(op.P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS)
    assert material["one_question_fit_option_refs"] == list(op.P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS)
    assert material["repair_required_option_refs"] == list(op.P7_R54_OP09_REPAIR_REQUIRED_OPTION_REFS)
    assert material["plan_candidate_flag_refs"] == list(op.P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS)
    assert material["selection_only_form"] is True
    assert material["reviewer_free_text_field_present"] is False
    assert material["reviewer_free_text_export_allowed"] is False
    assert material["raw_body_copy_field_present"] is False
    assert material["question_text_field_present"] is False
    assert material["draft_question_text_field_present"] is False
    assert material["local_path_field_present"] is False
    assert material["body_hash_field_present"] is False
    assert material["packet_content_field_present"] is False
    assert material["actual_human_review_operation_state_capture_allowed_next"] is True
    assert material["reviewer_instruction_materialized_here"] is True
    assert material["rating_form_materialized_here"] is True
    assert material["actual_human_review_started_here"] is False
    assert material["actual_human_review_run_here"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP09_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP09_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP10_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op09_blocks_after_op08_body_leak_scan_without_exposing_form_options() -> None:
    op08 = op.build_p7_r54_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation=_op07_ready(),
        body_full_packet_content_detected_in_export=True,
    )
    material = op.build_p7_r54_op09_reviewer_instruction_rating_form_freeze(
        packet_completeness_export_denylist_scan=op08
    )

    assert material["reviewer_instruction_status"] == op.P7_R54_OP09_FORM_BLOCKED_STATUS_REF
    assert material["rating_axis_refs"] == []
    assert material["rating_axis_count"] == 0
    assert material["score_option_refs"] == []
    assert material["verdict_option_refs"] == []
    assert material["question_need_primary_class_options"] == []
    assert material["selection_only_form"] is False
    assert material["reviewer_instruction_materialized_here"] is False
    assert material["rating_form_materialized_here"] is False
    assert material["next_required_step"] == op.P7_R54_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert "body_full_packet_content_detected_in_export" in material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op08_packet_scan_ready", False),
        ("op08_packet_scan_status", op.P7_R54_OP08_PACKET_SCAN_BLOCKED_STATUS_REF),
        ("packet_scan_row_count", 23),
        ("packet_present_count", 23),
        ("required_fields_present_count", 23),
        ("reviewer_instruction_ref", "different_instruction"),
        ("reviewer_instruction_policy_ref", "allows_free_text"),
        ("rating_form_ref", "different_rating_form"),
        ("rating_axis_count", 5),
        ("selection_only_form", False),
        ("reviewer_free_text_field_present", True),
        ("reviewer_free_text_export_allowed", True),
        ("raw_body_copy_field_present", True),
        ("question_text_field_present", True),
        ("draft_question_text_field_present", True),
        ("local_path_field_present", True),
        ("body_hash_field_present", True),
        ("packet_content_field_present", True),
        ("rating_form_contains_question_text", True),
        ("rating_form_contains_raw_body_copy", True),
        ("rating_form_contains_local_path", True),
        ("rating_form_contains_body_hash", True),
        ("rating_form_contains_reviewer_free_text_export", True),
        ("actual_human_review_operation_state_capture_allowed_next", False),
        ("reviewer_instruction_materialized_here", False),
        ("rating_form_materialized_here", False),
        ("actual_human_review_started_here", True),
        ("actual_human_review_run_here", True),
        ("p5_actual_review_still_not_run", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op09_rejects_form_boundary_review_claim_or_promotion_mutation(
    key: str,
    value: object,
) -> None:
    material = _op09_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material)


def test_r54_op09_rejects_option_set_mutations() -> None:
    material = _op09_ready()
    material["rating_axis_refs"] = material["rating_axis_refs"][:-1]
    with pytest.raises(ValueError):
        op.assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material)

    material = _op09_ready()
    material["question_need_primary_class_options"] = material["question_need_primary_class_options"][:-1]
    with pytest.raises(ValueError):
        op.assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material)

    material = _op09_ready()
    material["plan_candidate_flag_refs"][-1] = "p8_implementation_spec_finalized_here_true"
    with pytest.raises(ValueError):
        op.assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material)


def test_r54_op08_op09_bodyfree_aliases_match_primary_builders() -> None:
    op08 = op.build_p7_r54_operation_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_local_operation=_op07_ready()
    )
    assert op.assert_p7_r54_operation_packet_completeness_export_denylist_scan_bodyfree_contract(op08) is True
    assert op08["packet_scan_status"] == op.P7_R54_OP08_PACKET_SCAN_READY_STATUS_REF

    op09 = op.build_p7_r54_operation_reviewer_instruction_rating_form_freeze_bodyfree(
        packet_completeness_export_denylist_scan=op08
    )
    assert op.assert_p7_r54_operation_reviewer_instruction_rating_form_freeze_bodyfree_contract(op09) is True
    assert op09["reviewer_instruction_status"] == op.P7_R54_OP09_FORM_READY_STATUS_REF
    _assert_body_free_no_promotion(op09)
