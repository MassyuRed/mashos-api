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
def _cached_op06_blocked() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op06_local_only_body_full_packet_generation_request()
    assert op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material) is True
    return (material,)


def _op06_blocked() -> dict[str, object]:
    return deepcopy(_cached_op06_blocked()[0])


@lru_cache(maxsize=1)
def _cached_op07_blocked() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op07_packet_generation_local_operation(
        body_full_packet_generation_request=_op06_ready()
    )
    assert op.assert_p7_r54_op07_packet_generation_local_operation_contract(material) is True
    return (material,)


def _op07_blocked() -> dict[str, object]:
    return deepcopy(_cached_op07_blocked()[0])


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


def test_r54_op06_default_request_fails_closed_when_manifest_is_not_ready() -> None:
    material = _op06_blocked()

    assert material["schema_version"] == op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP06_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP06_STEP_REF
    assert material["op05_manifest_status"] == op.P7_R54_OP05_MANIFEST_BLOCKED_STATUS_REF
    assert material["op05_manifest_ready"] is False
    assert material["packet_generation_request_status"] == op.P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF
    assert material["packet_generation_request_ref"] == "not_requested_until_manifest_ready"
    assert material["requested_case_count"] == 0
    assert material["requested_packet_count"] == 0
    assert material["requested_packet_ref_ids"] == []
    assert material["packet_generation_request_rows"] == []
    assert material["packet_generation_request_materialized_here"] is False
    assert material["body_full_packet_generation_local_operation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == op.P7_R54_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op06_materializes_only_bodyfree_request_refs_after_ready_manifest() -> None:
    material = _op06_ready()
    op05 = _op05_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS)
    assert material["op05_schema_version"] == op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert material["op05_next_required_step"] == op.P7_R54_OP06_STEP_REF
    assert material["op05_manifest_status"] == op.P7_R54_OP05_MANIFEST_READY_STATUS_REF
    assert material["op05_manifest_ready"] is True
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["required_case_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["op05_case_count"] == 24
    assert material["op05_controller_manifest_row_count"] == 24
    assert material["op05_reviewer_facing_row_count"] == 24
    assert material["packet_generation_request_status"] == op.P7_R54_OP06_REQUEST_READY_STATUS_REF
    assert material["packet_generation_request_ref"] == op.P7_R54_OP06_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_request_policy_ref"] == op.P7_R54_OP06_PACKET_GENERATION_REQUEST_POLICY_REF
    assert material["packet_generation_request_reason_refs"] == [op.P7_R54_OP06_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["requested_case_count"] == 24
    assert material["requested_packet_count"] == 24
    assert material["requested_packet_ref_count"] == 24
    assert material["requested_packet_ref_ids_unique"] is True
    assert material["requested_packet_ref_ids"] == [row["packet_ref_id"] for row in op05["case_rows"]]
    assert material["packet_generation_request_row_count"] == 24
    assert len(material["packet_generation_request_rows"]) == 24
    assert material["packet_generation_request_rows"][0]["packet_ref_id"] == op05["case_rows"][0]["packet_ref_id"]
    assert material["packet_generation_request_rows"][0]["packet_generation_requested"] is True
    assert material["packet_generation_request_rows"][0]["request_is_bodyfree_only"] is True
    assert material["packet_generation_request_rows"][0]["packet_content_included"] is False
    assert material["request_is_bodyfree_only"] is True
    assert material["request_contains_packet_content"] is False
    assert material["request_contains_local_path"] is False
    assert material["request_contains_question_text"] is False
    assert material["local_review_root_path_included"] is False
    assert material["local_packet_directory_path_included"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_generation_local_operation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["packet_generation_request_materialized_here"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP07_STEP_REF
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op05_manifest_ready", False),
        ("packet_generation_request_ref", "different_request"),
        ("requested_packet_ref_ids_unique", False),
        ("request_is_bodyfree_only", False),
        ("request_contains_packet_content", True),
        ("request_contains_local_path", True),
        ("request_contains_question_text", True),
        ("local_review_root_path_included", True),
        ("local_packet_directory_path_included", True),
        ("body_full_packet_content_included", True),
        ("body_full_packet_generation_local_operation_started_here", True),
        ("body_full_packet_generated_here", True),
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
def test_r54_op06_rejects_request_boundary_review_claim_or_promotion_mutation(key: str, value: object) -> None:
    material = _op06_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material)


def test_r54_op06_rejects_request_row_removal_or_packet_ref_mismatch() -> None:
    material = _op06_ready()
    material["packet_generation_request_rows"] = material["packet_generation_request_rows"][:23]
    material["packet_generation_request_row_count"] = 23
    with pytest.raises(ValueError):
        op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material)

    material = _op06_ready()
    material["packet_generation_request_rows"][0]["packet_ref_id"] = "different-packet-ref"
    with pytest.raises(ValueError):
        op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material)

    material = _op06_ready()
    material["packet_generation_request_rows"][0]["packet_content_included"] = True
    with pytest.raises(ValueError):
        op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material)


def test_r54_op07_blocks_without_bodyfree_local_generation_receipt() -> None:
    material = _op07_blocked()

    assert material["schema_version"] == op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP07_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP07_STEP_REF
    assert material["op06_schema_version"] == op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION
    assert material["op06_next_required_step"] == op.P7_R54_OP07_STEP_REF
    assert material["op06_packet_generation_request_status"] == op.P7_R54_OP06_REQUEST_READY_STATUS_REF
    assert material["op06_packet_generation_request_ref"] == op.P7_R54_OP06_PACKET_GENERATION_REQUEST_REF
    assert material["op06_request_ready"] is True
    assert material["expected_packet_ref_count"] == 24
    assert material["local_operation_status"] == op.P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF
    assert material["local_operation_receipt_ref"] == "missing_local_operation_receipt_ref"
    assert material["packet_generation_local_operation_declared_complete"] is False
    assert material["packet_generation_local_operation_unverified_by_artifact"] is False
    assert material["local_operation_executed_outside_artifact_boundary"] is False
    assert material["local_operation_receipt_materialized_here"] is False
    assert material["local_operation_receipt_body_stored_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_body_full_packet_generated_here"] is False
    assert material["local_reviewer_payload_materialized_here"] is False
    assert material["local_review_root_path_included"] is False
    assert material["local_packet_directory_path_included"] is False
    assert material["local_packet_exported"] is False
    assert material["local_packet_export_candidate_count"] == 0
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["packet_completeness_scan_required_next"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == op.P7_R54_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP06_NOT_YET_IMPLEMENTED_STEPS
    _assert_body_free_no_promotion(material)


def test_r54_op07_accepts_bodyfree_receipt_only_without_exporting_packet_content() -> None:
    material = _op07_ready()
    op06 = _op06_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_REQUIRED_FIELD_REFS)
    assert material["op06_next_required_step"] == op.P7_R54_OP07_STEP_REF
    assert material["op06_packet_generation_request_status"] == op.P7_R54_OP06_REQUEST_READY_STATUS_REF
    assert material["op06_packet_generation_request_ref"] == op.P7_R54_OP06_PACKET_GENERATION_REQUEST_REF
    assert material["op06_request_ready"] is True
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["operation_current_refs_are_actual_review_basis"] is True
    assert material["required_case_count"] == P7_R51_REQUIRED_CASE_COUNT
    assert material["expected_packet_ref_ids"] == op06["requested_packet_ref_ids"]
    assert material["expected_packet_ref_count"] == 24
    assert material["local_operation_status"] == op.P7_R54_OP07_LOCAL_OPERATION_READY_STATUS_REF
    assert material["local_operation_receipt_ref"] == op.P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF
    assert material["local_operation_receipt_policy_ref"] == op.P7_R54_OP07_LOCAL_OPERATION_RECEIPT_POLICY_REF
    assert material["local_operation_reason_refs"] == [op.P7_R54_OP07_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["declared_generated_packet_ref_ids"] == op06["requested_packet_ref_ids"]
    assert material["declared_generated_packet_ref_count"] == 24
    assert material["declared_generated_packet_ref_ids_unique"] is True
    assert material["packet_ref_ids_match_request"] is True
    assert material["packet_generation_local_operation_declared_complete"] is True
    assert material["packet_generation_local_operation_unverified_by_artifact"] is True
    assert material["local_operation_executed_outside_artifact_boundary"] is True
    assert material["local_operation_receipt_materialized_here"] is True
    assert material["local_operation_receipt_body_stored_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_body_full_packet_generated_here"] is False
    assert material["local_reviewer_payload_materialized_here"] is False
    assert material["local_review_root_path_included"] is False
    assert material["local_packet_directory_path_included"] is False
    assert material["local_packet_exported"] is False
    assert material["local_packet_export_candidate_count"] == 0
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["export_denylist_violation_refs"] == []
    assert material["export_denylist_violation_count"] == 0
    assert material["packet_completeness_scan_required_next"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP08_STEP_REF
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op06_request_ready", False),
        ("op06_packet_generation_request_status", op.P7_R54_OP06_REQUEST_BLOCKED_STATUS_REF),
        ("local_operation_receipt_ref", "different_receipt"),
        ("local_operation_receipt_policy_ref", "different_policy"),
        ("declared_generated_packet_ref_count", 23),
        ("declared_generated_packet_ref_ids_unique", False),
        ("packet_ref_ids_match_request", False),
        ("packet_generation_local_operation_declared_complete", False),
        ("packet_generation_local_operation_unverified_by_artifact", False),
        ("local_operation_executed_outside_artifact_boundary", False),
        ("local_operation_receipt_materialized_here", False),
        ("local_operation_receipt_body_stored_here", True),
        ("body_full_packet_content_included", True),
        ("body_full_packet_generated_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("local_reviewer_payload_materialized_here", True),
        ("local_review_root_path_included", True),
        ("local_packet_directory_path_included", True),
        ("local_packet_exported", True),
        ("local_packet_export_candidate_count", 1),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("packet_completeness_scan_required_next", False),
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
def test_r54_op07_rejects_local_operation_receipt_boundary_review_claim_or_promotion_mutation(
    key: str,
    value: object,
) -> None:
    material = _op07_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op07_packet_generation_local_operation_contract(material)


def test_r54_op07_rejects_packet_ref_mismatch_or_export_denylist_violation() -> None:
    material = _op07_ready()
    material["declared_generated_packet_ref_ids"] = material["declared_generated_packet_ref_ids"][:23]
    material["declared_generated_packet_ref_count"] = 23
    with pytest.raises(ValueError):
        op.assert_p7_r54_op07_packet_generation_local_operation_contract(material)

    material = _op07_ready()
    material["declared_generated_packet_ref_ids"][0] = "different-packet-ref"
    with pytest.raises(ValueError):
        op.assert_p7_r54_op07_packet_generation_local_operation_contract(material)

    material = op.build_p7_r54_op07_packet_generation_local_operation(
        body_full_packet_generation_request=_op06_ready(),
        local_operation_receipt_ref=op.P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF,
        declared_generated_packet_ref_ids=_op06_ready()["requested_packet_ref_ids"],
        export_denylist_violation_refs=["body_full_packets.local_only/"],
    )
    assert material["local_operation_status"] == op.P7_R54_OP07_LOCAL_OPERATION_BLOCKED_STATUS_REF
    assert "export_denylist_violation_detected" in material["execution_blocker_ids"]
    assert material["packet_completeness_scan_required_next"] is False
    _assert_body_free_no_promotion(material)
