# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
from emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization import (
    P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
)


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
    '"body_full_generation_requested_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_verified": true',
    '"existing_op06_reused_as_actual_request_basis": true',
    '"existing_op07_reused_as_actual_local_operation_basis": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_ev04_ready() -> tuple[dict[str, object]]:
    ev03 = ev.build_p7_r54_ev03_r55_hold_intake_refreeze()
    material = ev.build_p7_r54_ev04_local_only_preflight_implementation_confirmation(
        r55_hold_intake_refreeze=ev03,
        local_review_root_presence_ref=ev.P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=ev.P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=ev.P7_R54_EV04_PURGE_PLAN_READY_REF,
        retention_policy_ref=ev.P7_R54_EV04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF,
    )
    assert ev.assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material) is True
    return (material,)


def _ev04_ready() -> dict[str, object]:
    return deepcopy(_cached_ev04_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev05_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev05_24_case_manifest_refreeze(
        local_only_preflight_implementation_confirmation=_ev04_ready(),
    )
    assert ev.assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material) is True
    return (material,)


def _ev05_ready() -> dict[str, object]:
    return deepcopy(_cached_ev05_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev06_blocked() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev06_body_full_packet_generation_request_bodyfree()
    assert ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material) is True
    return (material,)


def _ev06_blocked() -> dict[str, object]:
    return deepcopy(_cached_ev06_blocked()[0])


@lru_cache(maxsize=1)
def _cached_ev06_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev06_body_full_packet_generation_request_bodyfree(
        case_manifest_refreeze=_ev05_ready(),
    )
    assert ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material) is True
    return (material,)


def _ev06_ready() -> dict[str, object]:
    return deepcopy(_cached_ev06_ready()[0])


@lru_cache(maxsize=1)
def _cached_ev07_blocked() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev07_local_operation_boundary_instruction(
        body_full_packet_generation_request_bodyfree=_ev06_blocked(),
    )
    assert ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material) is True
    return (material,)


def _ev07_blocked() -> dict[str, object]:
    return deepcopy(_cached_ev07_blocked()[0])


@lru_cache(maxsize=1)
def _cached_ev07_ready() -> tuple[dict[str, object]]:
    material = ev.build_p7_r54_ev07_local_operation_boundary_instruction(
        body_full_packet_generation_request_bodyfree=_ev06_ready(),
    )
    assert ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material) is True
    return (material,)


def _ev07_ready() -> dict[str, object]:
    return deepcopy(_cached_ev07_ready()[0])


def test_r54_ev06_blocks_without_ready_ev05_manifest_and_keeps_packet_request_absent() -> None:
    material = _ev06_blocked()

    assert material["schema_version"] == ev.P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV06_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV06_STEP_REF
    assert material["source_mode"] == "local_snapshot"
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True

    assert material["ev05_manifest_ready"] is False
    assert material["packet_generation_request_status"] == ev.P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF
    assert material["packet_generation_request_ref"] == "not_requested_until_ev05_manifest_ready"
    assert material["packet_request_count"] == 0
    assert material["packet_ref_ids"] == []
    assert material["packet_generation_request_rows"] == []
    assert material["body_full_packet_generation_request_materialized_here"] is False
    assert material["local_operation_boundary_instruction_allowed_next"] is False
    assert material["execution_blocker_ids"] == material["open_execution_blocker_ids"]
    assert "r54_ev06_blocked_until_24_case_manifest_ready" in material["execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV06_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["existing_op06_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op06_operation_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_op06_current_refs_are_historical_here"] is True
    assert material["existing_op06_reused_as_actual_request_basis"] is False
    assert material["existing_op06_structural_contract_reused"] is True

    assert material["request_is_bodyfree_only"] is True
    assert material["request_contains_packet_content"] is False
    assert material["request_contains_local_path"] is False
    assert material["request_contains_body_hash"] is False
    assert material["request_contains_raw_input"] is False
    assert material["request_contains_returned_body"] is False
    assert material["request_contains_history_surface"] is False
    assert material["request_contains_reviewer_free_text"] is False
    assert material["request_contains_question_text"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev06_ready_materializes_only_bodyfree_packet_request_refs_for_24_cases() -> None:
    material = _ev06_ready()

    assert material["packet_generation_request_status"] == ev.P7_R54_EV06_REQUEST_READY_STATUS_REF
    assert material["packet_generation_request_status_ref"] == ev.P7_R54_EV06_REQUEST_STATUS_REF
    assert material["packet_generation_request_ref"] == ev.P7_R54_EV06_PACKET_GENERATION_REQUEST_REF
    assert material["packet_generation_request_policy_ref"] == ev.P7_R54_EV06_PACKET_GENERATION_REQUEST_POLICY_REF
    assert material["packet_generation_request_reason_refs"] == [ev.P7_R54_EV06_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["ev05_manifest_ready"] is True
    assert material["ev05_next_required_step"] == ev.P7_R54_EV06_STEP_REF
    assert material["ev05_case_count"] == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT == 24
    assert material["ev05_controller_manifest_row_count"] == 24
    assert material["ev05_reviewer_facing_row_count"] == 24

    assert material["packet_request_count"] == 24
    assert material["packet_ref_count"] == 24
    assert material["packet_ref_ids_unique"] is True
    assert len(material["packet_ref_ids"]) == 24
    assert material["packet_generation_request_row_count"] == 24
    assert len(material["packet_generation_request_rows"]) == 24
    assert [row["packet_ref_id"] for row in material["packet_generation_request_rows"]] == material["packet_ref_ids"]
    assert material["allowed_output_ref"] == ev.P7_R54_EV06_ALLOWED_OUTPUT_REF
    assert tuple(material["forbidden_output_refs"]) == ev.P7_R54_EV06_FORBIDDEN_OUTPUT_REFS
    assert material["forbidden_output_ref_count"] == len(ev.P7_R54_EV06_FORBIDDEN_OUTPUT_REFS)
    assert material["export_denylist_policy_ref"] == ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF
    assert tuple(material["export_denylist_patterns"]) == r54op.P7_R47_EXPORT_DENYLIST_PATTERNS

    assert material["body_full_packet_generation_request_materialized_here"] is True
    assert material["body_full_packet_generation_local_operation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["local_operation_boundary_instruction_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV06_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV06_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV07_STEP_REF

    for row in material["packet_generation_request_rows"]:
        assert row["packet_generation_requested"] is True
        assert row["request_is_bodyfree_only"] is True
        assert row["allowed_output_ref"] == ev.P7_R54_EV06_ALLOWED_OUTPUT_REF
        assert tuple(row["forbidden_output_refs"]) == ev.P7_R54_EV06_FORBIDDEN_OUTPUT_REFS
        assert row["packet_content_included"] is False
        assert row["raw_body_included"] is False
        assert row["returned_body_included"] is False
        assert row["history_surface_included"] is False
        assert row["reviewer_free_text_included"] is False
        assert row["local_path_included"] is False
        assert row["body_hash_included"] is False
        assert row["question_text_included"] is False
        assert row["body_free"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev07_blocks_without_ready_ev06_request_and_keeps_local_operation_absent() -> None:
    material = _ev07_blocked()

    assert material["schema_version"] == ev.P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV07_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV07_STEP_REF
    assert material["body_free"] is True
    assert material["ev06_request_ready"] is False
    assert material["local_operation_boundary_instruction_status"] == ev.P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF
    assert material["packet_ref_ids_for_local_operation"] == []
    assert material["local_operation_instruction_rows"] == []
    assert material["body_full_packet_generation_may_be_run_after_this_instruction"] is False
    assert material["body_full_packet_generation_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["local_operation_receipt_required_after_external_run"] is False
    assert material["external_local_body_full_packet_generation_required_before_actual_review"] is False
    assert material["body_full_packet_generation_not_performed_by_helper"] is True
    assert material["execution_blocker_ids"] == material["open_execution_blocker_ids"]
    assert "r54_ev07_blocked_until_ev06_bodyfree_packet_generation_request_ready" in material["execution_blocker_ids"]
    assert material["next_required_step"] == ev.P7_R54_EV07_BLOCKED_NEXT_REQUIRED_STEP_REF
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


def test_r54_ev07_ready_freezes_local_operation_instruction_without_generating_packets() -> None:
    material = _ev07_ready()

    assert material["local_operation_boundary_instruction_status"] == ev.P7_R54_EV07_INSTRUCTION_READY_STATUS_REF
    assert material["local_operation_boundary_status_ref"] == ev.P7_R54_EV07_BOUNDARY_STATUS_REF
    assert material["local_operation_boundary_instruction_ref"] == ev.P7_R54_EV07_INSTRUCTION_REF
    assert material["local_operation_boundary_instruction_policy_ref"] == ev.P7_R54_EV07_INSTRUCTION_POLICY_REF
    assert material["local_operation_boundary_instruction_reason_refs"] == [ev.P7_R54_EV07_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["ev06_request_ready"] is True
    assert material["ev06_next_required_step"] == ev.P7_R54_EV07_STEP_REF
    assert material["ev06_packet_generation_request_status"] == ev.P7_R54_EV06_REQUEST_READY_STATUS_REF

    assert material["operation_current_refs"] == ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert material["existing_op07_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op07_operation_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["existing_op07_current_refs_are_historical_here"] is True
    assert material["existing_op07_reused_as_actual_local_operation_basis"] is False
    assert material["existing_op07_structural_contract_reused"] is True

    assert material["packet_ref_count_for_local_operation"] == 24
    assert material["packet_ref_ids_for_local_operation_unique"] is True
    assert len(material["packet_ref_ids_for_local_operation"]) == 24
    assert material["local_operation_instruction_row_count"] == 24
    assert len(material["local_operation_instruction_rows"]) == 24
    assert [row["packet_ref_id"] for row in material["local_operation_instruction_rows"]] == material["packet_ref_ids_for_local_operation"]
    assert tuple(material["allowed_local_operation_scope_refs"]) == ev.P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS
    assert tuple(material["forbidden_local_operation_refs"]) == ev.P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS
    assert tuple(material["forbidden_output_refs"]) == ev.P7_R54_EV06_FORBIDDEN_OUTPUT_REFS
    assert material["local_review_root_env_var"] == r54op.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR
    assert material["local_review_root_path_included"] is False
    assert material["local_review_root_path_materialized_here"] is False
    assert material["local_packet_directory_path_included"] is False
    assert material["local_packet_directory_path_materialized_here"] is False
    assert material["export_denylist_policy_ref"] == ev.P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF
    assert tuple(material["export_denylist_patterns"]) == r54op.P7_R47_EXPORT_DENYLIST_PATTERNS
    assert material["retention_policy_ref"] == ev.P7_R54_EV04_RETENTION_POLICY_READY_REF
    assert material["body_full_packet_retention_max_hours"] == r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS
    assert material["reviewer_notes_retention_after_rating_finalized_max_hours"] == r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    assert tuple(material["delete_trigger_refs"]) == r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS

    assert material["body_full_packet_generation_may_be_run_after_this_instruction"] is True
    assert material["body_full_packet_generation_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_body_full_packet_generated_here"] is False
    assert material["local_reviewer_payload_materialized_here"] is False
    assert material["local_operation_receipt_materialized_here"] is False
    assert material["local_operation_receipt_required_after_external_run"] is True
    assert material["local_operation_receipt_body_stored_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["external_local_body_full_packet_generation_required_before_actual_review"] is True
    assert material["body_full_packet_generation_not_performed_by_helper"] is True
    assert material["p5_actual_review_still_not_run"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV07_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV07_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ev.P7_R54_EV08_NEXT_REQUIRED_STEP_REF

    for row in material["local_operation_instruction_rows"]:
        assert row["local_operation_scope_ref"] == "external_local_only_body_full_packet_generation"
        assert row["packet_generation_may_be_run_after_instruction"] is True
        assert row["packet_generation_run_here"] is False
        assert row["packet_content_included"] is False
        assert row["local_path_included"] is False
        assert row["body_hash_included"] is False
        assert row["question_text_included"] is False
        assert row["body_free"] is True
    for key in ev.P7_R54_EV_FALSE_FLAG_REFS:
        assert material[key] is False
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op06_current_refs_are_historical_here", False),
        ("existing_op06_reused_as_actual_request_basis", True),
        ("existing_op06_structural_contract_reused", False),
        ("required_case_count", 23),
        ("packet_generation_request_status", ev.P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF),
        ("packet_request_count", 23),
        ("packet_ref_count", 23),
        ("packet_ref_ids_unique", False),
        ("packet_generation_request_row_count", 23),
        ("allowed_output_ref", "artifact_zip"),
        ("request_is_bodyfree_only", False),
        ("request_contains_packet_content", True),
        ("request_contains_local_path", True),
        ("request_contains_body_hash", True),
        ("request_contains_raw_input", True),
        ("request_contains_returned_body", True),
        ("request_contains_history_surface", True),
        ("request_contains_reviewer_free_text", True),
        ("request_contains_question_text", True),
        ("body_full_packet_generation_request_materialized_here", False),
        ("body_full_packet_generation_local_operation_started_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("local_operation_boundary_instruction_allowed_next", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev06_rejects_request_boundary_mutations(key: str, value: object) -> None:
    material = _ev06_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material)


def test_r54_ev06_rejects_tampered_rows_old_refs_or_body_leak_keys() -> None:
    material = _ev06_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material)

    material = _ev06_ready()
    material["packet_generation_request_rows"] = material["packet_generation_request_rows"][:-1]
    material["packet_generation_request_row_count"] = 23
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material)

    material = _ev06_ready()
    material["packet_generation_request_rows"][0]["packet_content_included"] = True
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material)

    material = _ev06_ready()
    material["raw_input"] = "body must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op07_current_refs_are_historical_here", False),
        ("existing_op07_reused_as_actual_local_operation_basis", True),
        ("existing_op07_structural_contract_reused", False),
        ("required_case_count", 23),
        ("local_operation_boundary_instruction_status", ev.P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF),
        ("packet_ref_count_for_local_operation", 23),
        ("packet_ref_ids_for_local_operation_unique", False),
        ("local_operation_instruction_row_count", 23),
        ("local_review_root_path_included", True),
        ("local_review_root_path_materialized_here", True),
        ("local_packet_directory_path_included", True),
        ("local_packet_directory_path_materialized_here", True),
        ("body_full_packet_generation_may_be_run_after_this_instruction", False),
        ("body_full_packet_generation_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("local_reviewer_payload_materialized_here", True),
        ("local_operation_receipt_materialized_here", True),
        ("local_operation_receipt_required_after_external_run", False),
        ("local_operation_receipt_body_stored_here", True),
        ("body_full_packet_content_included", True),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("external_local_body_full_packet_generation_required_before_actual_review", False),
        ("body_full_packet_generation_not_performed_by_helper", False),
        ("p5_actual_review_still_not_run", False),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev07_rejects_instruction_boundary_mutations(key: str, value: object) -> None:
    material = _ev07_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material)


def test_r54_ev07_rejects_tampered_instruction_rows_old_refs_or_body_leak_keys() -> None:
    material = _ev07_ready()
    material["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material)

    material = _ev07_ready()
    material["local_operation_instruction_rows"] = material["local_operation_instruction_rows"][:-1]
    material["local_operation_instruction_row_count"] = 23
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material)

    material = _ev07_ready()
    material["local_operation_instruction_rows"][0]["packet_generation_run_here"] = True
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material)

    material = _ev07_ready()
    material["reviewer_free_text"] = "free text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material)
