# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR24 helper.

CLR24 materializes only a body-free validation command matrix and documentation
output for the 2026-06-27 current snapshot local run.  It records what was run,
what was not run, and which green claims are allowed, without converting helper
or selected-regression green into full product readiness.

This helper does not execute commands, store terminal output, export packet
content, create question text, mutate API/DB/RN/runtime contracts, mark P5 final,
start P6/P8, complete P7, or allow release.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_p7_no_body_payload_or_contract_mutation,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r54_current_snapshot_local_review_run_20260627 as clr03
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr22_clr23_20260627 as clr23


P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr24_validation_command_matrix_row.bodyfree.v1"
)
P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr24_validation_command_matrix_documentation_output.bodyfree.v1"
)
P7_R54_CLR24_SCHEMA_VERSION: Final = P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR23_STEP_REF: Final = clr03.P7_R54_CLR23_STEP_REF
P7_R54_CLR24_STEP_REF: Final = clr03.P7_R54_CLR24_STEP_REF

P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF: Final = (
    "CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_READY_BODYFREE_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF: Final = (
    "CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLR23_STATUS_REF: Final = (
    "CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_R52_REINTAKE_HANDOFF_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF: Final = (
    "CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF: Final = (
    "CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_GREEN_CLAIM_OVERREACH_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_STATUS_REF: Final = (
    "CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_R52_HANDOFF_STATUS_REF: Final = (
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLR23_STATUS_REF
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_VIOLATION_STATUS_REF: Final = (
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_STATUS_REF
)
P7_R54_CLR24_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF,
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF,
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLR23_STATUS_REF,
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF,
    P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_STATUS_REF,
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_REF: Final = (
    "R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BODYFREE_20260627"
)
P7_R54_CLR24_DOCUMENTATION_OUTPUT_FILE_REF: Final = "R54_CLR24_Result_20260627.md"
P7_R54_CLR24_READY_REASON_REF: Final = "r54_clr24_validation_command_matrix_documentation_output_ready_bodyfree"
P7_R54_CLR24_BLOCKED_BY_CLR23_REASON_REF: Final = "r54_clr24_blocked_until_r52_reintake_handoff_ready"
P7_R54_CLR24_COMMAND_MATRIX_MISSING_REASON_REF: Final = "r54_clr24_validation_command_matrix_rows_missing"
P7_R54_CLR24_COMMAND_MATRIX_NO_EXECUTED_ROWS_REASON_REF: Final = (
    "r54_clr24_validation_command_matrix_has_no_executed_rows"
)
P7_R54_CLR24_COMMAND_MATRIX_FAILED_REASON_REF: Final = "r54_clr24_validation_command_matrix_has_failed_result_refs"
P7_R54_CLR24_COMMAND_MATRIX_PRECONDITION_BLOCKED_REASON_REF: Final = (
    "r54_clr24_validation_command_matrix_has_blocked_by_precondition_result_refs"
)
P7_R54_CLR24_GREEN_CLAIM_OVERREACH_REASON_REF: Final = (
    "r54_clr24_green_claim_scope_overreach_detected_bodyfree"
)
P7_R54_CLR24_BODYFREE_LEAK_REASON_REF: Final = "r54_clr24_command_matrix_bodyfree_leak_detected"
P7_R54_CLR24_NEXT_WORK_AFTER_CLR24_REF: Final = (
    "r52_reintake_consumes_r54_bodyfree_evidence_after_validation_documentation_output"
)
P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "validation_command_matrix_documentation_output_repair_before_r52_reintake_consumption"
)

P7_R54_CLR24_COMMAND_RESULT_PASSED_REF: Final = "PASSED"
P7_R54_CLR24_COMMAND_RESULT_FAILED_REF: Final = "FAILED"
P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF: Final = "NOT_EXECUTED"
P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF: Final = "COLLECTED_ONLY_NOT_FULL_SUITE_GREEN"
P7_R54_CLR24_COMMAND_RESULT_BLOCKED_BY_PRECONDITION_REF: Final = "BLOCKED_BY_PRECONDITION"
P7_R54_CLR24_ALLOWED_COMMAND_RESULT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
    P7_R54_CLR24_COMMAND_RESULT_FAILED_REF,
    P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF,
    P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF,
    P7_R54_CLR24_COMMAND_RESULT_BLOCKED_BY_PRECONDITION_REF,
)

P7_R54_CLR24_CLAIM_BOUNDARY_GUARD_REFS: Final[tuple[str, ...]] = (
    "collect_only_not_full_suite_green",
    "selected_regression_not_full_backend_suite_green",
    "rn_contract_not_real_device_modal_verification",
    "r54_helper_green_not_actual_human_review_complete",
    "r52_handoff_ready_not_p5_final_confirmation",
    "validation_matrix_not_release_permission",
)
P7_R54_CLR24_DEFAULT_NOT_EXECUTED_VALIDATION_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_not_executed_in_clr24",
    "rn_contract_not_executed_in_clr24",
    "rn_real_device_modal_not_executed_in_clr24",
    "actual_body_full_packet_content_generation_not_executed_by_clr24_helper",
    "actual_local_only_human_review_execution_not_executed_by_clr24_helper",
    "actual_r52_reintake_processing_not_executed_by_clr24_helper",
    "release_validation_not_executed_in_clr24",
)
P7_R54_CLR24_BLOCKED_GREEN_CLAIM_TOKEN_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green",
    "full_suite_green",
    "real_device_modal_verified",
    "actual_human_review_complete",
    "actual_local_only_human_review_complete",
    "p5_final_confirmation",
    "p6_start_allowed",
    "p8_start_allowed",
    "release_allowed",
)
P7_R54_CLR24_FORBIDDEN_DOCUMENTATION_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_body",
        "returned_emlis_body",
        "returned_body",
        "history_surface",
        "history_body",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "payload_hash",
        "packet_content",
        "terminal_output",
        "terminal_output_body",
        "stdout",
        "stderr",
        "traceback",
    }
)

P7_R54_CLR24_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *clr23.P7_R54_CLR23_IMPLEMENTED_STEPS,
    P7_R54_CLR24_STEP_REF,
)
P7_R54_CLR24_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple()

P7_R54_CLR24_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_candidate",
        "p8_question_design_material_candidate",
    }
)

P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "validation_command_row_ref",
    "review_session_id",
    "command_ref",
    "command_group_ref",
    "command_kind_ref",
    "result_status_ref",
    "result_scope_ref",
    "passed_count",
    "collected_count",
    "warning_count",
    "failure_count",
    "green_claim_allowed",
    "collection_only_claim_allowed",
    "full_suite_claim_allowed",
    "real_device_claim_allowed",
    "actual_human_review_claim_allowed",
    "release_claim_allowed",
    "result_summary_ref",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "command_string_included",
    "body_free",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
)
P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr23_schema_version",
    "clr23_material_ref",
    "clr23_next_required_step",
    "clr23_handoff_status",
    "clr23_r52_reintake_handoff_ready",
    "clr23_actual_review_evidence_complete",
    "existing_op24_helper_ref",
    "existing_op24_schema_version",
    "existing_op24_operation_current_refs",
    "existing_op24_current_refs_are_historical_here",
    "existing_op24_reused_as_actual_documentation_output_basis",
    "existing_op24_structural_contract_reused",
    "existing_ev22_helper_ref",
    "existing_ev22_schema_version",
    "existing_ev22_current_refs",
    "existing_ev22_current_refs_are_historical_here",
    "existing_ev22_reused_as_actual_documentation_output_basis",
    "existing_ev22_structural_contract_reused",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "actual_review_basis_refs",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "actual_review_evidence_complete",
    "body_free_evidence_handoff_materialized_here",
    "r52_reintake_handoff_ready",
    "r52_reintake_required",
    "p5_decision_candidate_ref",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "p7_complete",
    "release_allowed",
    "documentation_output_status",
    "documentation_output_ref",
    "documentation_output_file_ref",
    "documentation_output_file_bodyfree",
    "documentation_output_file_contains_terminal_output_body",
    "documentation_output_reason_refs",
    "documentation_output_issue_refs",
    "documentation_output_issue_count",
    "documentation_output_materialized_here",
    "validation_command_result_refs",
    "validation_command_row_schema_version",
    "validation_command_row_required_field_refs",
    "validation_command_rows",
    "validation_command_row_count",
    "executed_validation_command_refs",
    "executed_validation_command_count",
    "passed_validation_command_count",
    "collected_only_validation_command_count",
    "failed_validation_command_count",
    "blocked_by_precondition_validation_command_count",
    "not_executed_validation_command_count",
    "not_executed_validation_refs",
    "not_executed_validation_ref_count",
    "green_claim_scope_refs",
    "green_claim_scope_count",
    "collection_only_scope_refs",
    "collection_only_scope_count",
    "blocked_green_claim_refs",
    "blocked_green_claim_count",
    "claim_boundary_guard_refs",
    "claim_boundary_guard_count",
    "bodyfree_leak_violation_refs",
    "bodyfree_leak_violation_count",
    "collect_only_claimed_as_full_suite_green",
    "rn_contract_claimed_as_real_device_modal_verified",
    "r54_helper_green_claimed_as_actual_human_review_complete",
    "r52_handoff_ready_claimed_as_p5_final_confirmation",
    "validation_matrix_claimed_as_release_permission",
    "full_backend_suite_green_confirmed",
    "real_device_modal_verified",
    "actual_human_review_complete_claimed_by_helper",
    "release_claimed_from_validation_matrix",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "command_string_included",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")


def _false_flags_except(*allowed_true_refs: str) -> dict[str, bool]:
    allowed = set(allowed_true_refs)
    return {key: False for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if key not in allowed}


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "public_response_key_changed": False,
        "public_response_top_level_key_added": False,
        "runtime_gate_threshold_changed": False,
        "user_label_connection_runtime_changed": False,
        "emlis_visible_output_generation_changed": False,
        "subscription_or_plan_access_policy_changed": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_trigger_logic_implemented": False,
    }


def _body_free_markers() -> dict[str, bool]:
    return {
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
    }


def _contains_blocked_claim_ref(value: Any) -> bool:
    lowered = clean_identifier(value, default="", max_length=260).lower()
    return any(token in lowered for token in P7_R54_CLR24_BLOCKED_GREEN_CLAIM_TOKEN_REFS)


def _forbidden_field_refs(value: Any, *, prefix: str = "payload") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_prefix = f"{prefix}.{key_text}"
            if key_text in P7_R54_CLR24_FORBIDDEN_DOCUMENTATION_FIELD_REFS:
                refs.append(child_prefix)
            refs.extend(_forbidden_field_refs(child, prefix=child_prefix))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_forbidden_field_refs(child, prefix=f"{prefix}[{index}]"))
    return refs


def build_p7_r54_clr24_validation_command_matrix_row(
    *,
    command_ref: Any,
    command_group_ref: Any = "r54_clr24_validation",
    command_kind_ref: Any = "pytest_target",
    result_status_ref: Any = P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
    result_scope_ref: Any = "selected_target_only",
    passed_count: Any = 0,
    collected_count: Any = 0,
    warning_count: Any = 0,
    failure_count: Any = 0,
    result_summary_ref: Any = "bodyfree_result_summary_ref",
    review_session_id: Any = None,
) -> dict[str, Any]:
    status = clean_identifier(result_status_ref, default=P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF, max_length=120)
    if status not in P7_R54_CLR24_ALLOWED_COMMAND_RESULT_STATUS_REFS:
        status = P7_R54_CLR24_COMMAND_RESULT_FAILED_REF
    command_id = clean_identifier(command_ref, default="validation_command_ref_missing", max_length=220)
    scope_ref = clean_identifier(result_scope_ref, default="selected_target_only", max_length=220)
    passed = max(0, int(passed_count or 0))
    collected = max(0, int(collected_count or 0))
    warnings = max(0, int(warning_count or 0))
    failures = max(0, int(failure_count or 0))
    if status == P7_R54_CLR24_COMMAND_RESULT_FAILED_REF and failures <= 0:
        failures = 1
    if status != P7_R54_CLR24_COMMAND_RESULT_FAILED_REF:
        failures = 0
    green_claim_allowed = status == P7_R54_CLR24_COMMAND_RESULT_PASSED_REF and not _contains_blocked_claim_ref(scope_ref)
    full_suite_claim_allowed = green_claim_allowed and "full_backend_suite" in scope_ref.lower() and "not_full" not in scope_ref.lower()
    real_device_claim_allowed = green_claim_allowed and "real_device_modal" in scope_ref.lower()
    actual_review_claim_allowed = green_claim_allowed and "actual_human_review" in scope_ref.lower() and "complete" not in scope_ref.lower()
    material = {
        "schema_version": P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "validation_command_row_ref": f"r54_clr24_validation_command_row__{command_id}"[:260],
        "review_session_id": clean_identifier(review_session_id, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=160),
        "command_ref": command_id,
        "command_group_ref": clean_identifier(command_group_ref, default="r54_clr24_validation", max_length=160),
        "command_kind_ref": clean_identifier(command_kind_ref, default="pytest_target", max_length=160),
        "result_status_ref": status,
        "result_scope_ref": scope_ref,
        "passed_count": passed if status == P7_R54_CLR24_COMMAND_RESULT_PASSED_REF else 0,
        "collected_count": collected if status == P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF else 0,
        "warning_count": warnings,
        "failure_count": failures,
        "green_claim_allowed": green_claim_allowed,
        "collection_only_claim_allowed": status == P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF,
        "full_suite_claim_allowed": full_suite_claim_allowed,
        "real_device_claim_allowed": real_device_claim_allowed,
        "actual_human_review_claim_allowed": actual_review_claim_allowed,
        "release_claim_allowed": False,
        "result_summary_ref": clean_identifier(result_summary_ref, default="bodyfree_result_summary_ref", max_length=220),
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "command_string_included": False,
        "body_free": True,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
    }
    assert_p7_r54_clr24_validation_command_matrix_row_contract(material)
    return material


def assert_p7_r54_clr24_validation_command_matrix_row_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(
        material,
        required=P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR24 command row",
    )
    if material.get("schema_version") != P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR24 command row schema version changed")
    if material.get("result_status_ref") not in P7_R54_CLR24_ALLOWED_COMMAND_RESULT_STATUS_REFS:
        raise ValueError("P7-R54-CLR24 command row result status outside allowed refs")
    if material.get("body_free") is not True:
        raise ValueError("P7-R54-CLR24 command row must remain body-free")
    for false_key in (
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "command_string_included",
        "raw_body_included",
        "returned_emlis_body_included",
        "history_surface_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "local_absolute_path_included",
        "body_hash_included",
        "packet_content_included",
        "terminal_output_body_included",
        "release_claim_allowed",
    ):
        if material.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR24 command row must keep {false_key}=False")
    if material.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF:
        if material.get("collection_only_claim_allowed") is not True or material.get("green_claim_allowed") is not False:
            raise ValueError("P7-R54-CLR24 collect-only row must not become a green claim")
    if material.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_FAILED_REF and int(material.get("failure_count") or 0) <= 0:
        raise ValueError("P7-R54-CLR24 failed row must carry failure_count")
    if material.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_PASSED_REF and int(material.get("failure_count") or 0) != 0:
        raise ValueError("P7-R54-CLR24 passed row must not carry failure_count")
    return True


def build_p7_r54_clr24_default_bodyfree_validation_command_rows(
    *,
    review_session_id: Any = None,
) -> list[dict[str, Any]]:
    return [
        build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="backend_compileall_services_ai_inference_tests",
            command_group_ref="backend_compileall",
            command_kind_ref="compileall",
            result_status_ref=P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            result_scope_ref="syntax_import_target_compileall_only_no_full_suite_claim",
            passed_count=1,
            result_summary_ref="compileall_passed_bodyfree",
            review_session_id=review_session_id,
        ),
        build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="clr00_to_clr23_split_chain",
            command_group_ref="clr_contract_chain_split",
            command_kind_ref="pytest_selected_target",
            result_status_ref=P7_R54_CLR24_COMMAND_RESULT_PASSED_REF,
            result_scope_ref="clr00_to_clr23_split_chain_selected_target_green_claim_limited",
            passed_count=247,
            result_summary_ref="clr00_to_clr23_split_chain_passed_bodyfree",
            review_session_id=review_session_id,
        ),
        build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="selected_regression_split",
            command_group_ref="selected_regression",
            command_kind_ref="pytest_selected_regression",
            result_status_ref=P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF,
            result_scope_ref="selected_regression_collected_only_no_full_suite_claim",
            collected_count=1696,
            result_summary_ref="selected_regression_collected_only_bodyfree",
            review_session_id=review_session_id,
        ),
        build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="full_backend_suite",
            command_group_ref="full_backend_suite",
            command_kind_ref="pytest_full_suite",
            result_status_ref=P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF,
            result_scope_ref="not_executed_no_full_suite_claim",
            result_summary_ref="full_backend_suite_not_executed_bodyfree",
            review_session_id=review_session_id,
        ),
        build_p7_r54_clr24_validation_command_matrix_row(
            command_ref="rn_real_device_modal",
            command_group_ref="rn_real_device_modal",
            command_kind_ref="manual_real_device_check",
            result_status_ref=P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF,
            result_scope_ref="not_executed_no_real_device_modal_verified_claim",
            result_summary_ref="rn_real_device_modal_not_executed_bodyfree",
            review_session_id=review_session_id,
        ),
    ]


def _sanitize_command_rows(command_rows: Sequence[Mapping[str, Any]] | None, *, review_session_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    leak_refs: list[str] = []
    for index, row in enumerate(command_rows or ()):  # type: ignore[arg-type]
        row_map = safe_mapping(row)
        leak_refs.extend(_forbidden_field_refs(row_map, prefix=f"validation_command_rows[{index}]")[:20])
        if row_map.get("schema_version") == P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION:
            sanitized = build_p7_r54_clr24_validation_command_matrix_row(
                command_ref=row_map.get("command_ref"),
                command_group_ref=row_map.get("command_group_ref", "r54_clr24_validation"),
                command_kind_ref=row_map.get("command_kind_ref", "pytest_target"),
                result_status_ref=row_map.get("result_status_ref"),
                result_scope_ref=row_map.get("result_scope_ref"),
                passed_count=row_map.get("passed_count", 0),
                collected_count=row_map.get("collected_count", 0),
                warning_count=row_map.get("warning_count", 0),
                failure_count=row_map.get("failure_count", 0),
                result_summary_ref=row_map.get("result_summary_ref", "bodyfree_result_summary_ref"),
                review_session_id=review_session_id,
            )
        else:
            sanitized = build_p7_r54_clr24_validation_command_matrix_row(
                command_ref=row_map.get("command_ref", f"validation_command_row_{index + 1}"),
                command_group_ref=row_map.get("command_group_ref", "r54_clr24_validation"),
                command_kind_ref=row_map.get("command_kind_ref", "pytest_target"),
                result_status_ref=row_map.get("result_status_ref", row_map.get("result_ref", P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF)),
                result_scope_ref=row_map.get("result_scope_ref", "selected_target_only"),
                passed_count=row_map.get("passed_count", 0),
                collected_count=row_map.get("collected_count", 0),
                warning_count=row_map.get("warning_count", 0),
                failure_count=row_map.get("failure_count", 0),
                result_summary_ref=row_map.get("result_summary_ref", "bodyfree_result_summary_ref"),
                review_session_id=review_session_id,
            )
        rows.append(sanitized)
    return rows, dedupe_identifiers(leak_refs, limit=80, max_length=240)


def _decide_documentation_status(
    *,
    handoff: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    leak_refs: Sequence[str],
) -> tuple[str, str, list[str]]:
    if handoff.get("handoff_status") != clr23.P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF or handoff.get("next_required_step") != P7_R54_CLR24_STEP_REF:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLR23_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_CLR24_BLOCKED_BY_CLR23_REASON_REF, *(handoff.get("open_execution_blocker_ids") or [])], limit=120, max_length=220),
        )
    if leak_refs:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_CLR24_BODYFREE_LEAK_REASON_REF, *leak_refs], limit=120, max_length=220),
        )
    if not rows:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR24_COMMAND_MATRIX_MISSING_REASON_REF],
        )
    executed_rows = [row for row in rows if row.get("result_status_ref") != P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF]
    if not executed_rows:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR24_COMMAND_MATRIX_NO_EXECUTED_ROWS_REASON_REF],
        )
    failed_rows = [clean_identifier(row.get("command_ref"), default="validation_command_failed", max_length=220) for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_FAILED_REF]
    if failed_rows:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_CLR24_COMMAND_MATRIX_FAILED_REASON_REF, *failed_rows], limit=120, max_length=220),
        )
    precondition_rows = [clean_identifier(row.get("command_ref"), default="validation_command_blocked_by_precondition", max_length=220) for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_BLOCKED_BY_PRECONDITION_REF]
    if precondition_rows:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_CLR24_COMMAND_MATRIX_PRECONDITION_BLOCKED_REASON_REF, *precondition_rows], limit=120, max_length=220),
        )
    blocked_claim_refs = [
        clean_identifier(row.get("command_ref"), default="blocked_green_claim", max_length=220)
        for row in rows
        if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_PASSED_REF and _contains_blocked_claim_ref(row.get("result_scope_ref"))
    ]
    if blocked_claim_refs:
        return (
            P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF,
            P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_CLR24_GREEN_CLAIM_OVERREACH_REASON_REF, *blocked_claim_refs], limit=120, max_length=220),
        )
    return (P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF, P7_R54_CLR24_NEXT_WORK_AFTER_CLR24_REF, [P7_R54_CLR24_READY_REASON_REF])


def build_p7_r54_clr24_validation_command_matrix_documentation_output(
    *,
    r52_reintake_handoff: Mapping[str, Any] | None = None,
    validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    green_claim_scope_refs: Sequence[Any] | None = None,
    not_executed_validation_refs: Sequence[Any] | None = None,
    documentation_evidence: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    session_id = clean_identifier(review_session_id, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=160)
    handoff = safe_mapping(r52_reintake_handoff)
    rows, row_leak_refs = _sanitize_command_rows(validation_command_rows, review_session_id=session_id)
    evidence_leak_refs = _forbidden_field_refs(safe_mapping(documentation_evidence), prefix="documentation_evidence")
    leak_refs = dedupe_identifiers([*row_leak_refs, *evidence_leak_refs], limit=120, max_length=240)
    supplied_green_claim_refs = [clean_identifier(ref, default="", max_length=220) for ref in (green_claim_scope_refs or ())]
    supplied_green_claim_refs = [ref for ref in supplied_green_claim_refs if ref]
    supplied_blocked_claim_refs = [ref for ref in supplied_green_claim_refs if _contains_blocked_claim_ref(ref)]
    supplied_safe_green_claim_refs = [ref for ref in supplied_green_claim_refs if not _contains_blocked_claim_ref(ref)]
    status, next_step, reason_refs = _decide_documentation_status(handoff=handoff, rows=rows, leak_refs=leak_refs)
    if status == P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF and supplied_blocked_claim_refs:
        status = P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF
        next_step = P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF
        reason_refs = dedupe_identifiers(
            [P7_R54_CLR24_GREEN_CLAIM_OVERREACH_REASON_REF, *supplied_blocked_claim_refs],
            limit=120,
            max_length=220,
        )
    ready = status == P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    failed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_FAILED_REF)
    blocked_by_precondition_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_BLOCKED_BY_PRECONDITION_REF)
    collected_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF)
    passed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_PASSED_REF)
    not_executed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF)
    executed_rows = [row for row in rows if row.get("result_status_ref") != P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF]
    not_executed_refs = dedupe_identifiers(
        not_executed_validation_refs or P7_R54_CLR24_DEFAULT_NOT_EXECUTED_VALIDATION_REFS,
        limit=80,
        max_length=220,
    )
    green_claim_refs = dedupe_identifiers(
        [
            item
            for row in rows
            if row.get("green_claim_allowed") is True
            for item in (
                clean_identifier(row.get("command_ref"), default="green_claim_command", max_length=220),
                clean_identifier(row.get("result_scope_ref"), default="green_claim_scope", max_length=220),
            )
        ]
        + supplied_safe_green_claim_refs,
        limit=120,
        max_length=220,
    )
    collection_only_refs = dedupe_identifiers(
        [
            item
            for row in rows
            if row.get("collection_only_claim_allowed") is True
            for item in (
                clean_identifier(row.get("command_ref"), default="collection_only_command", max_length=220),
                clean_identifier(row.get("result_scope_ref"), default="collection_only_scope", max_length=220),
            )
        ],
        limit=120,
        max_length=220,
    )
    blocked_claim_refs = dedupe_identifiers(
        [
            clean_identifier(row.get("command_ref"), default="blocked_green_claim", max_length=220)
            for row in rows
            if row.get("result_status_ref") == P7_R54_CLR24_COMMAND_RESULT_PASSED_REF and _contains_blocked_claim_ref(row.get("result_scope_ref"))
        ]
        + supplied_blocked_claim_refs,
        limit=120,
        max_length=220,
    )
    issue_refs = [] if ready else dedupe_identifiers(reason_refs, limit=120, max_length=220)
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR24_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR24_STEP_REF,
        "operation_step_ref": P7_R54_CLR24_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_20260627",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr23_schema_version": handoff.get("schema_version", clr23.P7_R54_CLR23_SCHEMA_VERSION),
        "clr23_material_ref": handoff.get("material_id", "clr23_r52_reintake_handoff_missing"),
        "clr23_next_required_step": handoff.get("next_required_step", "clr23_not_ready"),
        "clr23_handoff_status": handoff.get("handoff_status", "R54_R52_REINTAKE_HANDOFF_MISSING"),
        "clr23_r52_reintake_handoff_ready": handoff.get("r52_reintake_handoff_ready") is True,
        "clr23_actual_review_evidence_complete": handoff.get("actual_review_evidence_complete") is True,
        "existing_op24_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.OP24",
        "existing_op24_schema_version": r54op.P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "existing_op24_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op24_current_refs_are_historical_here": True,
        "existing_op24_reused_as_actual_documentation_output_basis": False,
        "existing_op24_structural_contract_reused": True,
        "existing_ev22_helper_ref": "emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626.EV22",
        "existing_ev22_schema_version": r54ev.P7_R54_EV_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "existing_ev22_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev22_current_refs_are_historical_here": True,
        "existing_ev22_reused_as_actual_documentation_output_basis": False,
        "existing_ev22_structural_contract_reused": True,
        "operation_current_refs": dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_keys": list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "operation_current_ref_key_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_keys": list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "actual_review_basis_refs": dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(handoff.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(handoff.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(handoff.get("question_observation_row_count") or 0) if ready else 0,
        "disposal_verified": handoff.get("disposal_verified") is True and ready,
        "actual_review_evidence_complete": handoff.get("actual_review_evidence_complete") is True and ready,
        "body_free_evidence_handoff_materialized_here": handoff.get("body_free_evidence_handoff_materialized_here") is True and ready,
        "r52_reintake_handoff_ready": handoff.get("r52_reintake_handoff_ready") is True and ready,
        "r52_reintake_required": handoff.get("r52_reintake_required") is True and ready,
        "p5_decision_candidate_ref": handoff.get("p5_decision_candidate_ref", "P5_NOT_READY") if ready else "P5_NOT_READY",
        "p5_human_blind_qa_confirmed_candidate": handoff.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": handoff.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": handoff.get("p8_question_design_material_candidate") is True and ready,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "documentation_output_status": status,
        "documentation_output_ref": P7_R54_CLR24_DOCUMENTATION_OUTPUT_REF if ready else "clr24_validation_command_matrix_documentation_output_not_ready_bodyfree_20260627",
        "documentation_output_file_ref": P7_R54_CLR24_DOCUMENTATION_OUTPUT_FILE_REF if ready else "R54_CLR24_Result_NotReady_20260627.md",
        "documentation_output_file_bodyfree": True,
        "documentation_output_file_contains_terminal_output_body": False,
        "documentation_output_reason_refs": reason_refs,
        "documentation_output_issue_refs": issue_refs,
        "documentation_output_issue_count": len(issue_refs),
        "documentation_output_materialized_here": ready,
        "validation_command_result_refs": list(P7_R54_CLR24_ALLOWED_COMMAND_RESULT_STATUS_REFS),
        "validation_command_row_schema_version": P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "validation_command_row_required_field_refs": list(P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS),
        "validation_command_rows": rows,
        "validation_command_row_count": len(rows),
        "executed_validation_command_refs": [clean_identifier(row.get("command_ref"), default="validation_command", max_length=220) for row in executed_rows] if ready else [],
        "executed_validation_command_count": len(executed_rows) if ready else 0,
        "passed_validation_command_count": passed_count if ready else 0,
        "collected_only_validation_command_count": collected_count if ready else 0,
        "failed_validation_command_count": failed_count,
        "blocked_by_precondition_validation_command_count": blocked_by_precondition_count,
        "not_executed_validation_command_count": not_executed_count,
        "not_executed_validation_refs": not_executed_refs,
        "not_executed_validation_ref_count": len(not_executed_refs),
        "green_claim_scope_refs": green_claim_refs if ready else [],
        "green_claim_scope_count": len(green_claim_refs) if ready else 0,
        "collection_only_scope_refs": collection_only_refs if ready else [],
        "collection_only_scope_count": len(collection_only_refs) if ready else 0,
        "blocked_green_claim_refs": blocked_claim_refs,
        "blocked_green_claim_count": len(blocked_claim_refs),
        "claim_boundary_guard_refs": list(P7_R54_CLR24_CLAIM_BOUNDARY_GUARD_REFS),
        "claim_boundary_guard_count": len(P7_R54_CLR24_CLAIM_BOUNDARY_GUARD_REFS),
        "bodyfree_leak_violation_refs": leak_refs,
        "bodyfree_leak_violation_count": len(leak_refs),
        "collect_only_claimed_as_full_suite_green": False,
        "rn_contract_claimed_as_real_device_modal_verified": False,
        "r54_helper_green_claimed_as_actual_human_review_complete": False,
        "r52_handoff_ready_claimed_as_p5_final_confirmation": False,
        "validation_matrix_claimed_as_release_permission": False,
        "full_backend_suite_green_confirmed": False,
        "real_device_modal_verified": False,
        "actual_human_review_complete_claimed_by_helper": False,
        "release_claimed_from_validation_matrix": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "command_string_included": False,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "execution_blocker_ids": issue_refs,
        "open_execution_blocker_ids": issue_refs,
        "implemented_steps": list(P7_R54_CLR24_IMPLEMENTED_STEPS if ready else tuple(handoff.get("implemented_steps") or ())),
        "not_yet_implemented_steps": list(P7_R54_CLR24_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(handoff.get("not_yet_implemented_steps") or ())),
        "first_next_work_ref": P7_R54_CLR24_NEXT_WORK_AFTER_CLR24_REF if ready else clr23.P7_R54_CLR23_NEXT_WORK_AFTER_CLR22_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "terminal_output_body_included": False,
        **_false_flags_except(
            "actual_review_evidence_complete",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p8_question_design_material_candidate",
        ),
    }
    material["actual_review_evidence_complete"] = handoff.get("actual_review_evidence_complete") is True and ready
    material["disposal_verified"] = handoff.get("disposal_verified") is True and ready
    material["p5_human_blind_qa_confirmed_candidate"] = handoff.get("p5_human_blind_qa_confirmed_candidate") is True and ready
    material["p6_limited_human_readfeel_candidate"] = handoff.get("p6_limited_human_readfeel_candidate") is True and ready
    material["p8_question_design_material_candidate"] = handoff.get("p8_question_design_material_candidate") is True and ready
    material["actual_rating_rows_materialized_here"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(material)
    return material


def assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(
        material,
        required=P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR24 documentation output",
    )
    if material.get("schema_version") != P7_R54_CLR24_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR24 documentation schema version changed")
    if material.get("policy_section") != P7_R54_CLR24_STEP_REF or material.get("operation_step_ref") != P7_R54_CLR24_STEP_REF:
        raise ValueError("P7-R54-CLR24 policy section changed")
    if safe_mapping(material.get("operation_current_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR24 current snapshot refs changed")
    if safe_mapping(material.get("actual_review_basis_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR24 actual review basis refs changed")
    if safe_mapping(material.get("existing_op24_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR24 existing OP24 refs changed")
    if safe_mapping(material.get("existing_ev22_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR24 existing EV22 refs changed")
    for key in (
        "existing_op24_current_refs_are_historical_here",
        "existing_op24_structural_contract_reused",
        "existing_ev22_current_refs_are_historical_here",
        "existing_ev22_structural_contract_reused",
        "operation_current_refs_are_actual_review_basis",
        "operation_current_refs_used_as_actual_review_basis",
        "human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "documentation_output_file_bodyfree",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR24 must keep {key}=True")
    for key in (
        "existing_op24_reused_as_actual_documentation_output_basis",
        "existing_ev22_reused_as_actual_documentation_output_basis",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "p8_question_implementation_spec_finalized_here",
        "p7_complete",
        "release_allowed",
        "collect_only_claimed_as_full_suite_green",
        "rn_contract_claimed_as_real_device_modal_verified",
        "r54_helper_green_claimed_as_actual_human_review_complete",
        "r52_handoff_ready_claimed_as_p5_final_confirmation",
        "validation_matrix_claimed_as_release_permission",
        "full_backend_suite_green_confirmed",
        "real_device_modal_verified",
        "actual_human_review_complete_claimed_by_helper",
        "release_claimed_from_validation_matrix",
        "documentation_output_file_contains_terminal_output_body",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "command_string_included",
        "raw_body_included",
        "returned_emlis_body_included",
        "history_surface_included",
        "reviewer_free_text_included",
        "reviewer_note_included",
        "reviewer_notes_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "local_absolute_path_included",
        "body_hash_included",
        "packet_content_included",
        "terminal_output_body_included",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR24 must keep {key}=False")
    if material.get("documentation_output_status") not in P7_R54_CLR24_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS:
        raise ValueError("P7-R54-CLR24 documentation output status outside allowed refs")
    ready = material.get("documentation_output_status") == P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    if material.get("documentation_output_materialized_here") is not ready:
        raise ValueError("P7-R54-CLR24 materialization flag must match status")
    for row in material.get("validation_command_rows") or ():
        assert_p7_r54_clr24_validation_command_matrix_row_contract(row)
    if material.get("documentation_output_issue_count") != len(material.get("documentation_output_issue_refs") or ()):
        raise ValueError("P7-R54-CLR24 issue count changed")
    if material.get("blocked_green_claim_count") != len(material.get("blocked_green_claim_refs") or ()):
        raise ValueError("P7-R54-CLR24 blocked green claim count changed")
    if material.get("collection_only_scope_count") != len(material.get("collection_only_scope_refs") or ()):
        raise ValueError("P7-R54-CLR24 collection-only scope count changed")
    if material.get("green_claim_scope_count") != len(material.get("green_claim_scope_refs") or ()):
        raise ValueError("P7-R54-CLR24 green claim scope count changed")
    if material.get("not_executed_validation_ref_count") != len(material.get("not_executed_validation_refs") or ()):
        raise ValueError("P7-R54-CLR24 not executed refs count changed")
    if material.get("bodyfree_leak_violation_count") != len(material.get("bodyfree_leak_violation_refs") or ()):
        raise ValueError("P7-R54-CLR24 bodyfree leak count changed")
    if ready:
        if material.get("clr23_handoff_status") != clr23.P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF:
            raise ValueError("P7-R54-CLR24 ready must be based on CLR23 handoff ready")
        if material.get("actual_review_evidence_complete") is not True or material.get("r52_reintake_handoff_ready") is not True:
            raise ValueError("P7-R54-CLR24 ready must preserve CLR23 body-free evidence completion")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if material.get(count_key) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-CLR24 ready must preserve 24 {count_key}")
        if material.get("validation_command_row_count") <= 0 or material.get("executed_validation_command_count") <= 0:
            raise ValueError("P7-R54-CLR24 ready requires executed validation rows")
        if material.get("failed_validation_command_count") != 0 or material.get("blocked_by_precondition_validation_command_count") != 0:
            raise ValueError("P7-R54-CLR24 ready must not contain failed/precondition-blocked rows")
        if material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR24 ready must not carry open blockers")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR24_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR24 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR24_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR24 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR24_NEXT_WORK_AFTER_CLR24_REF:
            raise ValueError("P7-R54-CLR24 ready next step changed")
    else:
        if material.get("actual_review_evidence_complete") is not False or material.get("r52_reintake_handoff_ready") is not False:
            raise ValueError("P7-R54-CLR24 blocked must not expose evidence completion")
        if not material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR24 blocked must carry blocker refs")
        if material.get("next_required_step") != P7_R54_CLR24_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR24 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(material, source="P7-R54-CLR24")
    return True


build_p7_r54_current_snapshot_local_run_clr24_validation_command_matrix_documentation_output = build_p7_r54_clr24_validation_command_matrix_documentation_output
assert_p7_r54_current_snapshot_local_run_clr24_validation_command_matrix_documentation_output_contract = assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract
build_p7_r54_current_snapshot_validation_command_matrix_documentation_output_bodyfree = build_p7_r54_clr24_validation_command_matrix_documentation_output
assert_p7_r54_current_snapshot_validation_command_matrix_documentation_output_bodyfree_contract = assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract
build_clr24_validation_command_matrix_documentation_output = build_p7_r54_clr24_validation_command_matrix_documentation_output
assert_clr24_validation_command_matrix_documentation_output_contract = assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract

__all__ = (
    "P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION",
    "P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION",
    "P7_R54_CLR24_SCHEMA_VERSION",
    "P7_R54_CLR24_STEP_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_READY_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLR23_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_R52_HANDOFF_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_LEAK_STATUS_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_BLOCKED_BY_BODYFREE_VIOLATION_STATUS_REF",
    "P7_R54_CLR24_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_REF",
    "P7_R54_CLR24_DOCUMENTATION_OUTPUT_FILE_REF",
    "P7_R54_CLR24_COMMAND_RESULT_PASSED_REF",
    "P7_R54_CLR24_COMMAND_RESULT_FAILED_REF",
    "P7_R54_CLR24_COMMAND_RESULT_NOT_EXECUTED_REF",
    "P7_R54_CLR24_COMMAND_RESULT_COLLECTED_ONLY_REF",
    "P7_R54_CLR24_COMMAND_RESULT_BLOCKED_BY_PRECONDITION_REF",
    "P7_R54_CLR24_ALLOWED_COMMAND_RESULT_STATUS_REFS",
    "P7_R54_CLR24_CLAIM_BOUNDARY_GUARD_REFS",
    "P7_R54_CLR24_DEFAULT_NOT_EXECUTED_VALIDATION_REFS",
    "P7_R54_CLR24_IMPLEMENTED_STEPS",
    "P7_R54_CLR24_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_CLR24_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr24_validation_command_matrix_row",
    "assert_p7_r54_clr24_validation_command_matrix_row_contract",
    "build_p7_r54_clr24_default_bodyfree_validation_command_rows",
    "build_p7_r54_clr24_validation_command_matrix_documentation_output",
    "assert_p7_r54_clr24_validation_command_matrix_documentation_output_contract",
    "build_p7_r54_current_snapshot_local_run_clr24_validation_command_matrix_documentation_output",
    "assert_p7_r54_current_snapshot_local_run_clr24_validation_command_matrix_documentation_output_contract",
    "build_p7_r54_current_snapshot_validation_command_matrix_documentation_output_bodyfree",
    "assert_p7_r54_current_snapshot_validation_command_matrix_documentation_output_bodyfree_contract",
    "build_clr24_validation_command_matrix_documentation_output",
    "assert_clr24_validation_command_matrix_documentation_output_contract",
)
