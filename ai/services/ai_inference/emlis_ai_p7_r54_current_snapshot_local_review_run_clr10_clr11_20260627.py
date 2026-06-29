# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR10-CLR11 helpers.

CLR10 intakes only a body-free receipt that an external local-only human review
operation reached a selection-row state.  It does not open packets, include packet
bodies, export reviewer notes, or mark review evidence complete.

CLR11 intakes only sanitized selection rows that match the CLR10 body-free
receipt.  It does not normalize rating rows, materialize question-observation
rows, verify disposal, or promote P5/P6/P8/release state.
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr08_clr09_20260627 as clr09


P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr10_actual_human_review_local_only_operation.bodyfree.v1"
)
P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr11_sanitized_review_result_row.bodyfree.v1"
)
P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr11_sanitized_review_result_row_intake.bodyfree.v1"
)
P7_R54_CLR10_SCHEMA_VERSION: Final = P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION
P7_R54_CLR11_ROW_SCHEMA_VERSION: Final = P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
P7_R54_CLR11_SCHEMA_VERSION: Final = P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR10_STEP_REF: Final = clr03.P7_R54_CLR10_STEP_REF
P7_R54_CLR11_STEP_REF: Final = clr03.P7_R54_CLR11_STEP_REF
P7_R54_CLR12_STEP_REF: Final = clr03.P7_R54_CLR12_STEP_REF

P7_R54_CLR10_REVIEW_NOT_STARTED_STATUS_REF: Final = "NOT_STARTED"
P7_R54_CLR10_REVIEW_IN_PROGRESS_STATUS_REF: Final = "REVIEW_IN_PROGRESS_LOCAL_ONLY"
P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF: Final = "PAUSED_NO_HANDOFF_LOCAL_ONLY"
P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF: Final = "ABORTED_PURGE_REQUIRED"
P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF: Final = "EXPIRED_PURGE_REQUIRED"
P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF: Final = "LOCAL_ONLY_HUMAN_REVIEW_COMPLETED_SELECTIONS_CAPTURED"
P7_R54_CLR10_ALLOWED_REVIEW_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR10_REVIEW_NOT_STARTED_STATUS_REF,
    P7_R54_CLR10_REVIEW_IN_PROGRESS_STATUS_REF,
    P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF,
    P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF,
    P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF,
    P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
)
P7_R54_CLR10_OPERATION_RECEIPT_READY_STATUS_REF: Final = "LOCAL_ONLY_HUMAN_REVIEW_OPERATION_RECEIPT_READY_BODYFREE"
P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF: Final = "LOCAL_ONLY_HUMAN_REVIEW_OPERATION_RECEIPT_BLOCKED"
P7_R54_CLR10_ALLOWED_OPERATION_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR10_OPERATION_RECEIPT_READY_STATUS_REF,
    P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_CLR10_COMPLETION_RECEIPT_REF: Final = "r54_clr10_external_local_human_review_completion_receipt_bodyfree_20260627"
P7_R54_CLR10_OPERATION_RECEIPT_POLICY_REF: Final = "external_local_human_review_receipt_refs_counts_enums_only_no_body_no_path_no_hash"
P7_R54_CLR10_READY_REASON_REF: Final = "r54_clr10_external_local_review_completed_selection_refs_accepted_bodyfree"
P7_R54_CLR10_STATE_CAPTURE_REASON_REF: Final = "r54_clr10_external_local_review_state_captured_bodyfree_no_handoff"
P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-10_blocked_until_external_local_human_review_receipt_ready"
P7_R54_CLR10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-10_continue_pause_or_retry_before_sanitized_row_intake"
P7_R54_CLR10_REVIEWER_IDENTITY_POLICY_REF: Final = r54op.P7_R54_OP10_REVIEWER_IDENTITY_POLICY_REF

P7_R54_CLR11_INTAKE_READY_STATUS_REF: Final = "SANITIZED_REVIEW_RESULT_ROWS_INTAKEN_BODYFREE"
P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF: Final = "SANITIZED_REVIEW_RESULT_ROW_INTAKE_BLOCKED"
P7_R54_CLR11_ALLOWED_INTAKE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR11_INTAKE_READY_STATUS_REF,
    P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF,
)
P7_R54_CLR11_SANITIZED_REVIEW_RESULT_INTAKE_REF: Final = "r54_clr11_sanitized_review_result_row_intake_bodyfree_20260627"
P7_R54_CLR11_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF: Final = "sanitized_selection_rows_only_no_raw_body_no_question_text_no_paths_no_hashes_20260627"
P7_R54_CLR11_READY_REASON_REF: Final = "r54_clr11_24_sanitized_selection_rows_intaken_bodyfree"
P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-CLR-11_blocked_until_24_selection_only_rows_are_available"

P7_R54_CLR10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr09.P7_R54_CLR09_IMPLEMENTED_STEPS, P7_R54_CLR10_STEP_REF)
P7_R54_CLR10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[9:]
P7_R54_CLR11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR10_IMPLEMENTED_STEPS, P7_R54_CLR11_STEP_REF)
P7_R54_CLR11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[10:]

P7_R54_CLR11_SELECTION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_SELECTION_ROW_REQUIRED_FIELD_REFS
P7_R54_CLR11_PROHIBITED_SELECTION_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "question_text",
    "draft_question_text",
    "local_absolute_path",
    "local_path",
    "body_hash",
    "packet_content",
    "terminal_output_body",
)
P7_R54_CLR11_RATING_AXIS_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_RATING_AXIS_REFS
P7_R54_CLR11_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(clr09.P7_R54_CLR09_RATING_AXIS_TARGET_THRESHOLDS)
P7_R54_CLR11_SCORE_OPTION_REFS: Final[tuple[float, ...]] = clr09.P7_R54_CLR09_SCORE_OPTION_REFS
P7_R54_CLR11_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_VERDICT_OPTION_REFS
P7_R54_CLR11_OVERALL_READ_FEELING_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_OVERALL_READ_FEELING_OPTION_REFS
P7_R54_CLR11_READFEEL_BLOCKER_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_READFEEL_BLOCKER_OPTION_REFS
P7_R54_CLR11_EXECUTION_BLOCKER_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_EXECUTION_BLOCKER_OPTION_REFS
P7_R54_CLR11_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_QUESTION_NEED_PRIMARY_CLASS_REFS
P7_R54_CLR11_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_AMBIGUITY_KIND_OPTION_REFS
P7_R54_CLR11_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_ONE_QUESTION_FIT_OPTION_REFS
P7_R54_CLR11_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_REPAIR_REQUIRED_OPTION_REFS
P7_R54_CLR11_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = clr09.P7_R54_CLR09_PLAN_CANDIDATE_FLAG_REFS

P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_result_row_ref",
    "selection_row_ref",
    "review_session_id",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_index",
    "case_role_family_ref",
    "plan_tier_context_ref",
    "reviewer_ref",
    "reviewed_at_ref",
    "axis_scores",
    "axis_score_count",
    "overall_read_feeling_ref",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "selection_only_row",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "source_body_not_materialized_in_row",
    "question_text_not_materialized_in_row",
    "body_free",
)

P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr09_schema_version",
    "clr09_material_ref",
    "clr09_next_required_step",
    "clr09_reviewer_selection_form_status",
    "clr09_form_ready",
    "clr09_actual_human_review_operation_allowed_next",
    "existing_op10_helper_ref",
    "existing_op10_schema_version",
    "existing_op10_operation_current_refs",
    "existing_op10_current_refs_are_historical_here",
    "existing_op10_reused_as_actual_review_basis",
    "existing_op10_structural_contract_reused",
    "required_case_count",
    "review_operation_receipt_status",
    "review_operation_status",
    "review_operation_receipt_ref",
    "review_operation_receipt_policy_ref",
    "review_operation_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "reviewer_assignment_ref",
    "reviewer_ref_ids",
    "reviewer_ref_count",
    "reviewer_identity_policy_ref",
    "reviewer_identity_personal_info_included",
    "reviewer_name_included",
    "reviewer_email_included",
    "reviewer_account_included",
    "review_started_state_declared",
    "review_paused_state_declared",
    "review_aborted_state_declared",
    "review_expired_state_declared",
    "review_completed_state_declared",
    "review_completion_receipt_ref",
    "review_completed_packet_ref_ids",
    "review_completed_packet_ref_count",
    "review_completed_packet_ref_ids_unique",
    "review_completed_selection_row_refs",
    "review_completed_selection_row_count",
    "review_completed_selection_row_refs_unique",
    "review_completed_selection_rows_expected_count",
    "external_local_human_review_completion_receipt_accepted",
    "external_local_human_review_selection_refs_only",
    "external_local_human_review_body_not_materialized_here",
    "review_operation_receipt_contains_raw_body",
    "review_operation_receipt_contains_returned_body",
    "review_operation_receipt_contains_history_surface",
    "review_operation_receipt_contains_reviewer_free_text",
    "review_operation_receipt_contains_question_text",
    "review_operation_receipt_contains_local_path",
    "review_operation_receipt_contains_body_hash",
    "review_operation_receipt_contains_packet_content",
    "review_operation_receipt_contains_terminal_output_body",
    "sanitized_review_result_row_intake_allowed_next",
    "actual_human_review_started_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_review_operation_performed_by_helper",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified_before_intake",
    "disposal_verified",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr10_schema_version",
    "clr10_material_ref",
    "clr10_next_required_step",
    "clr10_review_operation_status",
    "clr10_review_operation_receipt_status",
    "clr10_sanitized_review_result_row_intake_allowed_next",
    "existing_op11_helper_ref",
    "existing_op11_schema_version",
    "existing_op11_operation_current_refs",
    "existing_op11_current_refs_are_historical_here",
    "existing_op11_reused_as_actual_intake_basis",
    "existing_op11_structural_contract_reused",
    "required_case_count",
    "expected_packet_ref_ids",
    "expected_packet_ref_count",
    "expected_selection_row_refs",
    "expected_selection_row_ref_count",
    "submitted_selection_row_count",
    "sanitized_review_result_intake_status",
    "sanitized_review_result_intake_ref",
    "sanitized_review_result_intake_policy_ref",
    "sanitized_review_result_intake_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "sanitized_review_result_rows",
    "sanitized_review_result_row_count",
    "reviewed_case_count",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "case_ref_ids",
    "case_ref_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "selection_row_refs",
    "selection_row_ref_count",
    "selection_row_refs_unique",
    "reviewer_ref_ids",
    "reviewer_ref_count",
    "case_role_family_counts",
    "plan_tier_context_counts",
    "selection_rows_are_bodyfree_only",
    "sanitized_rows_contain_reviewer_free_text",
    "sanitized_rows_contain_reviewer_note",
    "sanitized_rows_contain_reviewer_notes",
    "sanitized_rows_contain_raw_body",
    "sanitized_rows_contain_returned_body",
    "sanitized_rows_contain_history_surface",
    "sanitized_rows_contain_question_text",
    "sanitized_rows_contain_local_path",
    "sanitized_rows_contain_local_absolute_path",
    "sanitized_rows_contain_body_hash",
    "sanitized_rows_contain_packet_content",
    "sanitized_rows_contain_terminal_output_body",
    "sanitized_review_result_rows_materialized_here",
    "rating_row_normalization_allowed_next",
    "actual_human_review_run_by_helper",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "history_raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_note_included": False,
        "reviewer_notes_included": False,
        "terminal_output_included": False,
    }


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_key_changed": False,
        "db_migration_changed": False,
        "rn_visible_contract_changed": False,
        "public_response_key_changed": False,
        "runtime_gate_threshold_changed": False,
        "user_label_connection_runtime_changed": False,
        "emlis_visible_output_generation_changed": False,
        "subscription_or_plan_access_policy_changed": False,
        "p8_question_trigger_logic_changed": False,
        "p8_question_text_created": False,
        "release_decision_changed": False,
    }


def _current_ref_fields() -> dict[str, Any]:
    refs = dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS)
    return {
        "operation_current_refs": refs,
        "operation_current_ref_count": len(refs),
        "operation_current_ref_keys": list(refs.keys()),
        "operation_current_ref_key_count": len(refs),
        "required_current_snapshot_ref_keys": list(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
    }


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=180)


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    missing = [field for field in required if field not in data]
    extra = [field for field in data if field not in required]
    if missing or extra:
        raise ValueError(f"{source} field mismatch missing={missing[:8]} extra={extra[:8]}")


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_CLR11_PROHIBITED_SELECTION_FIELD_REFS:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _assert_base(data: Mapping[str, Any], *, schema_version: str, policy_section: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != "P7":
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_CLR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_CLR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_CLR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != policy_section:
        raise ValueError(f"{source} policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git flags must stay false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    for nested_key in ("public_contract", "r54_clr_no_touch_contract", "body_free_markers"):
        nested = safe_mapping(data.get(nested_key))
        if not nested or any(value is True for value in nested.values()):
            raise ValueError(f"{source} {nested_key} must contain only false markers")
    for false_key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    if _contains_forbidden_key(data):
        raise ValueError(f"{source} contains forbidden body/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    if safe_mapping(data.get("operation_current_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current refs changed")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError(f"{source} must use current refs as actual review basis")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError(f"{source} must mark current refs used as basis")
    if data.get("actual_review_basis_ref") != clr03.P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis changed")
    if data.get("all_required_current_refs_present") is not True:
        raise ValueError(f"{source} must keep all current refs present")


def _default_packet_refs() -> list[str]:
    scan = clr09.build_p7_r54_clr08_packet_completeness_export_denylist_scan()
    clr09.assert_p7_r54_clr08_packet_completeness_export_denylist_scan_contract(scan)
    return [clean_identifier(item, max_length=180) for item in (scan.get("expected_packet_ref_ids") or [])]


def _review_status(value: Any) -> str:
    status = clean_identifier(value, default=P7_R54_CLR10_REVIEW_NOT_STARTED_STATUS_REF, max_length=140)
    return status if status in P7_R54_CLR10_ALLOWED_REVIEW_OPERATION_STATUS_REFS else "invalid_review_operation_status_ref"


def _clean_refs(values: Sequence[Any] | None, *, limit: int = 24, max_length: int = 180) -> list[str]:
    return dedupe_identifiers(values or [], limit=limit + 1, max_length=max_length)


def _unique_non_empty(values: Sequence[str], *, required_count: int) -> bool:
    return len(values) == required_count and len(set(values)) == required_count and all(bool(item) for item in values)


def _receipt_map(receipt: Mapping[str, Any] | None) -> dict[str, Any]:
    return safe_mapping(receipt) if receipt is not None else {}


def build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form(
    reviewer_selection_form_freeze: Mapping[str, Any] | None = None,
    *,
    reviewer_ref_ids: Sequence[Any] | None = None,
    reviewer_assignment_ref: Any = "r54_clr10_local_reviewer_assignment_bodyfree",
    review_completion_receipt_ref: Any = P7_R54_CLR10_COMPLETION_RECEIPT_REF,
) -> dict[str, Any]:
    """Return a body-free external local-review completion receipt for tests/manual intake.

    The receipt contains only refs, counts, enums, and blockers.  It never
    contains body-full packet content or reviewer free text.
    """
    form = safe_mapping(reviewer_selection_form_freeze) if reviewer_selection_form_freeze is not None else clr09.build_p7_r54_clr09_reviewer_selection_form_freeze()
    clr09.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form)
    packet_refs = _default_packet_refs()
    selection_row_refs = [f"r54-clr11-selection-row-{index:03d}" for index in range(1, len(packet_refs) + 1)]
    reviewers = dedupe_identifiers(reviewer_ref_ids or ["r54-local-reviewer-bodyfree-ref-001"], limit=8, max_length=120)
    return {
        "review_operation_receipt_ref": clean_identifier(review_completion_receipt_ref, default=P7_R54_CLR10_COMPLETION_RECEIPT_REF, max_length=220),
        "review_operation_status": P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
        "reviewer_assignment_ref": clean_identifier(reviewer_assignment_ref, default="r54_clr10_local_reviewer_assignment_bodyfree", max_length=220),
        "reviewer_ref_ids": reviewers,
        "review_completion_receipt_ref": clean_identifier(review_completion_receipt_ref, default=P7_R54_CLR10_COMPLETION_RECEIPT_REF, max_length=220),
        "review_completed_packet_ref_ids": packet_refs,
        "review_completed_selection_row_refs": selection_row_refs,
        "export_candidate_count": 0,
        "execution_blocker_ids": [],
        "body_free": True,
    }


def build_p7_r54_clr10_actual_human_review_local_only_operation(
    *,
    reviewer_selection_form_freeze: Mapping[str, Any] | None = None,
    local_human_review_operation_receipt: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr10_actual_human_review_local_only_operation",
) -> dict[str, Any]:
    """Intake a body-free local human-review operation receipt for CLR10.

    The helper never performs the review itself.  A completed state means only
    that a body-free external-local receipt with 24 packet refs and 24 selection
    row refs was supplied.
    """
    form = safe_mapping(reviewer_selection_form_freeze) if reviewer_selection_form_freeze is not None else clr09.build_p7_r54_clr09_reviewer_selection_form_freeze()
    clr09.assert_p7_r54_clr09_reviewer_selection_form_freeze_contract(form)
    form_ready = bool(
        form.get("reviewer_selection_form_status") == clr09.P7_R54_CLR09_REVIEWER_SELECTION_FORM_READY_STATUS_REF
        and form.get("actual_human_review_operation_allowed_next") is True
        and form.get("next_required_step") == P7_R54_CLR10_STEP_REF
    )
    receipt = _receipt_map(local_human_review_operation_receipt)
    if receipt:
        if _contains_forbidden_key(receipt):
            raise ValueError("p7_r54_clr10_local_human_review_operation_receipt contains forbidden body/question/path/hash key")
        assert_p7_no_body_payload_or_contract_mutation(receipt, source="p7_r54_clr10_local_human_review_operation_receipt")
    review_session_id = _safe_review_session_id(form.get("review_session_id"))
    requested_status = _review_status(receipt.get("review_operation_status"))
    reviewer_refs = dedupe_identifiers(receipt.get("reviewer_ref_ids") or [], limit=8, max_length=120)
    packet_refs = _clean_refs(receipt.get("review_completed_packet_ref_ids"), limit=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT, max_length=180)
    selection_row_refs = _clean_refs(receipt.get("review_completed_selection_row_refs"), limit=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT, max_length=180)
    completion_receipt = clean_identifier(receipt.get("review_completion_receipt_ref"), default="review_completion_receipt_not_available_bodyfree", max_length=220)
    operation_receipt_ref = clean_identifier(receipt.get("review_operation_receipt_ref"), default="local_human_review_operation_receipt_not_available_bodyfree", max_length=220)
    assignment_ref = clean_identifier(receipt.get("reviewer_assignment_ref"), default="reviewer_assignment_not_started_bodyfree", max_length=220)
    export_candidate_count = int(receipt.get("export_candidate_count") or 0) if not isinstance(receipt.get("export_candidate_count"), bool) else 0
    completed_requested = requested_status == P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
    active_requested = requested_status in (
        P7_R54_CLR10_REVIEW_IN_PROGRESS_STATUS_REF,
        P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF,
        P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    )
    completion_payload_ready = bool(
        completed_requested
        and completion_receipt != "review_completion_receipt_not_available_bodyfree"
        and operation_receipt_ref != "local_human_review_operation_receipt_not_available_bodyfree"
        and reviewer_refs
        and _unique_non_empty(packet_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT)
        and _unique_non_empty(selection_row_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT)
        and export_candidate_count == 0
    )
    blocker_seed: list[str] = []
    if not form_ready:
        blocker_seed.append("r54_clr10_blocked_until_clr09_reviewer_selection_form_ready")
    if not receipt:
        blocker_seed.append("local_human_review_operation_receipt_missing")
    if requested_status == "invalid_review_operation_status_ref":
        blocker_seed.append("invalid_review_operation_status_ref")
    if active_requested and not reviewer_refs:
        blocker_seed.append("reviewer_ref_required_for_active_or_completed_review_state")
    if completed_requested and completion_receipt == "review_completion_receipt_not_available_bodyfree":
        blocker_seed.append("review_completion_receipt_ref_required")
    if completed_requested and operation_receipt_ref == "local_human_review_operation_receipt_not_available_bodyfree":
        blocker_seed.append("review_operation_receipt_ref_required")
    if completed_requested and len(packet_refs) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blocker_seed.append("review_completed_packet_ref_count_must_be_24")
    if completed_requested and not _unique_non_empty(packet_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT):
        blocker_seed.append("review_completed_packet_refs_must_be_unique")
    if completed_requested and len(selection_row_refs) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blocker_seed.append("review_completed_selection_row_ref_count_must_be_24")
    if completed_requested and not _unique_non_empty(selection_row_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT):
        blocker_seed.append("review_completed_selection_row_refs_must_be_unique")
    if export_candidate_count:
        blocker_seed.append("review_operation_export_candidate_count_must_be_zero")
    external_blockers = dedupe_identifiers(receipt.get("execution_blocker_ids") or [], limit=80, max_length=180)
    execution_blockers = [] if form_ready and receipt and requested_status != "invalid_review_operation_status_ref" and (not completed_requested or completion_payload_ready) and (not active_requested or reviewer_refs) and not external_blockers else dedupe_identifiers(
        [*blocker_seed, *external_blockers, *(form.get("open_execution_blocker_ids") or [])],
        limit=100,
        max_length=180,
    )
    receipt_ready = bool(form_ready and receipt and requested_status != "invalid_review_operation_status_ref" and not execution_blockers)
    reason_refs = (
        [P7_R54_CLR10_READY_REASON_REF if completion_payload_ready else P7_R54_CLR10_STATE_CAPTURE_REASON_REF]
        if receipt_ready
        else dedupe_identifiers([P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF, *execution_blockers], limit=100, max_length=180)
    )
    sanitized_allowed_next = bool(receipt_ready and completion_payload_ready)
    material = {
        "schema_version": P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR10_STEP_REF,
        "operation_step_ref": P7_R54_CLR10_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr10_actual_human_review_local_only_operation", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr09_schema_version": clr09.P7_R54_CLR09_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        "clr09_material_ref": clean_identifier(form.get("material_id"), default="p7_r54_clr09_reviewer_selection_form_freeze", max_length=220),
        "clr09_next_required_step": clean_identifier(form.get("next_required_step"), default=clr09.P7_R54_CLR09_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr09_reviewer_selection_form_status": clean_identifier(form.get("reviewer_selection_form_status"), default=clr09.P7_R54_CLR09_REVIEWER_SELECTION_FORM_BLOCKED_STATUS_REF, max_length=180),
        "clr09_form_ready": form_ready,
        "clr09_actual_human_review_operation_allowed_next": bool(form.get("actual_human_review_operation_allowed_next") is True),
        "existing_op10_helper_ref": "build_p7_r54_op10_actual_human_review_operation_state_capture",
        "existing_op10_schema_version": r54op.P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION,
        "existing_op10_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op10_current_refs_are_historical_here": True,
        "existing_op10_reused_as_actual_review_basis": False,
        "existing_op10_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "review_operation_receipt_status": P7_R54_CLR10_OPERATION_RECEIPT_READY_STATUS_REF if receipt_ready else P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF,
        "review_operation_status": requested_status if requested_status != "invalid_review_operation_status_ref" else P7_R54_CLR10_REVIEW_NOT_STARTED_STATUS_REF,
        "review_operation_receipt_ref": operation_receipt_ref if receipt else "local_human_review_operation_receipt_not_available_bodyfree",
        "review_operation_receipt_policy_ref": P7_R54_CLR10_OPERATION_RECEIPT_POLICY_REF,
        "review_operation_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "reviewer_assignment_ref": assignment_ref if form_ready else "reviewer_assignment_blocked_until_form_ready_bodyfree",
        "reviewer_ref_ids": reviewer_refs if form_ready else [],
        "reviewer_ref_count": len(reviewer_refs) if form_ready else 0,
        "reviewer_identity_policy_ref": P7_R54_CLR10_REVIEWER_IDENTITY_POLICY_REF,
        "reviewer_identity_personal_info_included": False,
        "reviewer_name_included": False,
        "reviewer_email_included": False,
        "reviewer_account_included": False,
        "review_started_state_declared": requested_status == P7_R54_CLR10_REVIEW_IN_PROGRESS_STATUS_REF and form_ready,
        "review_paused_state_declared": requested_status == P7_R54_CLR10_REVIEW_PAUSED_STATUS_REF and form_ready,
        "review_aborted_state_declared": requested_status == P7_R54_CLR10_REVIEW_ABORTED_STATUS_REF and form_ready,
        "review_expired_state_declared": requested_status == P7_R54_CLR10_REVIEW_EXPIRED_STATUS_REF and form_ready,
        "review_completed_state_declared": completed_requested and form_ready,
        "review_completion_receipt_ref": completion_receipt if completed_requested and form_ready else "review_completion_receipt_not_available_bodyfree",
        "review_completed_packet_ref_ids": packet_refs if completed_requested and form_ready else [],
        "review_completed_packet_ref_count": len(packet_refs) if completed_requested and form_ready else 0,
        "review_completed_packet_ref_ids_unique": _unique_non_empty(packet_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if completed_requested and form_ready else False,
        "review_completed_selection_row_refs": selection_row_refs if completed_requested and form_ready else [],
        "review_completed_selection_row_count": len(selection_row_refs) if completed_requested and form_ready else 0,
        "review_completed_selection_row_refs_unique": _unique_non_empty(selection_row_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if completed_requested and form_ready else False,
        "review_completed_selection_rows_expected_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if completed_requested and form_ready else 0,
        "external_local_human_review_completion_receipt_accepted": completion_payload_ready,
        "external_local_human_review_selection_refs_only": completion_payload_ready,
        "external_local_human_review_body_not_materialized_here": True,
        "review_operation_receipt_contains_raw_body": False,
        "review_operation_receipt_contains_returned_body": False,
        "review_operation_receipt_contains_history_surface": False,
        "review_operation_receipt_contains_reviewer_free_text": False,
        "review_operation_receipt_contains_question_text": False,
        "review_operation_receipt_contains_local_path": False,
        "review_operation_receipt_contains_body_hash": False,
        "review_operation_receipt_contains_packet_content": False,
        "review_operation_receipt_contains_terminal_output_body": False,
        "sanitized_review_result_row_intake_allowed_next": sanitized_allowed_next,
        "actual_human_review_started_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "actual_review_operation_performed_by_helper": False,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified_before_intake": False,
        "disposal_verified": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR10_IMPLEMENTED_STEPS if receipt_ready else (form.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR10_NOT_YET_IMPLEMENTED_STEPS if receipt_ready else (form.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR11_STEP_REF if sanitized_allowed_next else (P7_R54_CLR10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF if receipt_ready else P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(data, required=P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_REQUIRED_FIELD_REFS, source="P7-R54-CLR10")
    _assert_base(data, schema_version=P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION, policy_section=P7_R54_CLR10_STEP_REF, source="P7-R54-CLR10")
    _assert_current_refs(data, source="P7-R54-CLR10")
    if safe_mapping(data.get("existing_op10_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR10 OP10 refs changed")
    if data.get("existing_op10_current_refs_are_historical_here") is not True or data.get("existing_op10_reused_as_actual_review_basis") is not False:
        raise ValueError("P7-R54-CLR10 historical OP10 boundary changed")
    if data.get("existing_op10_structural_contract_reused") is not True:
        raise ValueError("P7-R54-CLR10 must reuse OP10 only structurally")
    if data.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR10 required case count changed")
    if data.get("review_operation_receipt_status") not in P7_R54_CLR10_ALLOWED_OPERATION_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-CLR10 receipt status changed")
    if data.get("review_operation_status") not in P7_R54_CLR10_ALLOWED_REVIEW_OPERATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR10 review operation status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR10 blockers mismatch")
    for false_key in (
        "reviewer_identity_personal_info_included", "reviewer_name_included", "reviewer_email_included", "reviewer_account_included",
        "review_operation_receipt_contains_raw_body", "review_operation_receipt_contains_returned_body", "review_operation_receipt_contains_history_surface",
        "review_operation_receipt_contains_reviewer_free_text", "review_operation_receipt_contains_question_text", "review_operation_receipt_contains_local_path",
        "review_operation_receipt_contains_body_hash", "review_operation_receipt_contains_packet_content", "review_operation_receipt_contains_terminal_output_body",
        "actual_human_review_started_here", "actual_human_review_run_here", "actual_manual_review_run_here", "actual_review_operation_performed_by_helper",
        "actual_review_evidence_complete", "disposal_verified_before_intake", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR10 must keep {false_key}=False")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("P7-R54-CLR10 must not materialize rating/question rows")
    if data.get("actual_human_review_completion_claim_blocked_here") is not True or data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("P7-R54-CLR10 must block review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True or data.get("p5_finalization_blocked_here") is not True:
        raise ValueError("P7-R54-CLR10 must block promotion/finalization")
    ready = data.get("review_operation_receipt_status") == P7_R54_CLR10_OPERATION_RECEIPT_READY_STATUS_REF
    if ready:
        if data.get("clr09_form_ready") is not True or data.get("clr09_next_required_step") != P7_R54_CLR10_STEP_REF:
            raise ValueError("P7-R54-CLR10 ready receipt requires ready CLR09 form")
        if blockers:
            raise ValueError("P7-R54-CLR10 ready receipt must not carry blockers")
        if data.get("review_operation_receipt_policy_ref") != P7_R54_CLR10_OPERATION_RECEIPT_POLICY_REF:
            raise ValueError("P7-R54-CLR10 receipt policy changed")
        if data.get("review_operation_status") == P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF:
            if data.get("sanitized_review_result_row_intake_allowed_next") is not True:
                raise ValueError("P7-R54-CLR10 completed receipt must allow CLR11")
            if data.get("review_completed_packet_ref_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError("P7-R54-CLR10 completed packet count must be 24")
            if data.get("review_completed_selection_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError("P7-R54-CLR10 completed selection row count must be 24")
            if data.get("review_completed_packet_ref_ids_unique") is not True or data.get("review_completed_selection_row_refs_unique") is not True:
                raise ValueError("P7-R54-CLR10 completed refs must be unique")
            if data.get("reviewer_ref_count", 0) < 1:
                raise ValueError("P7-R54-CLR10 completed receipt requires reviewer refs")
            if data.get("external_local_human_review_completion_receipt_accepted") is not True or data.get("external_local_human_review_selection_refs_only") is not True:
                raise ValueError("P7-R54-CLR10 completed receipt must be accepted as refs-only")
            if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR10_IMPLEMENTED_STEPS:
                raise ValueError("P7-R54-CLR10 implemented steps changed")
            if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR10_NOT_YET_IMPLEMENTED_STEPS:
                raise ValueError("P7-R54-CLR10 not-yet steps changed")
            if data.get("next_required_step") != P7_R54_CLR11_STEP_REF:
                raise ValueError("P7-R54-CLR10 completed receipt must point to CLR11")
        else:
            if data.get("sanitized_review_result_row_intake_allowed_next") is not False:
                raise ValueError("P7-R54-CLR10 non-completed receipt must not allow CLR11")
            if data.get("next_required_step") != P7_R54_CLR10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF:
                raise ValueError("P7-R54-CLR10 non-completed next step changed")
    else:
        if data.get("sanitized_review_result_row_intake_allowed_next") is not False:
            raise ValueError("P7-R54-CLR10 blocked receipt must not allow CLR11")
        if not blockers:
            raise ValueError("P7-R54-CLR10 blocked receipt must carry blockers")
        if P7_R54_CLR10_STEP_REF in tuple(data.get("implemented_steps") or ()):
            raise ValueError("P7-R54-CLR10 blocked receipt must not mark CLR10 implemented")
        if data.get("next_required_step") != P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR10 blocked next step changed")
    return True


def _case_refs(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [clean_identifier(row.get(key), max_length=180) for row in rows]


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(row.get(key), default="unknown", max_length=160)
        out[value] = out.get(value, 0) + 1
    return out


def _axis_scores(value: Any) -> dict[str, float]:
    mapping = safe_mapping(value)
    scores: dict[str, float] = {}
    for axis in P7_R54_CLR11_RATING_AXIS_REFS:
        raw = mapping.get(axis)
        if isinstance(raw, bool):
            continue
        try:
            score = float(raw)
        except (TypeError, ValueError):
            continue
        scores[axis] = score
    return scores


def _plan_candidate_flags(value: Any) -> dict[str, bool]:
    mapping = safe_mapping(value)
    flags: dict[str, bool] = {}
    for key in P7_R54_CLR11_PLAN_CANDIDATE_FLAG_REFS:
        flags[key] = False if key == "p8_implementation_spec_finalized_here" else bool(mapping.get(key, False))
    return flags


def _normalized_sanitized_review_rows(rows: Sequence[Any], *, review_session_id: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        assert_p7_no_body_payload_or_contract_mutation(source, source="p7_r54_clr11_input_selection_row")
        if _contains_forbidden_key(source):
            raise ValueError("p7_r54_clr11_input_selection_row contains forbidden selection field")
        scores = _axis_scores(source.get("axis_scores"))
        normalized.append(
            {
                "schema_version": P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_result_row_ref": clean_identifier(source.get("review_result_row_ref"), default=f"r54clr11-sanitized-review-row-{index:03d}", max_length=180),
                "selection_row_ref": clean_identifier(source.get("selection_row_ref"), default=f"r54-clr11-selection-row-{index:03d}", max_length=180),
                "review_session_id": review_session_id,
                "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
                "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
                "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
                "case_index": int(source.get("case_index") or index) if not isinstance(source.get("case_index"), bool) else index,
                "case_role_family_ref": clean_identifier(source.get("case_role_family_ref"), default="p5_history_line_review", max_length=180),
                "plan_tier_context_ref": clean_identifier(source.get("plan_tier_context_ref"), default="plan_tier_context_bodyfree", max_length=180),
                "reviewer_ref": clean_identifier(source.get("reviewer_ref"), max_length=120),
                "reviewed_at_ref": clean_identifier(source.get("reviewed_at_ref"), default="coarse_reviewed_at_ref_20260627", max_length=160),
                "axis_scores": scores,
                "axis_score_count": len(scores),
                "overall_read_feeling_ref": clean_identifier(source.get("overall_read_feeling_ref"), max_length=160),
                "verdict": clean_identifier(source.get("verdict"), max_length=80),
                "sanitized_reason_ids": dedupe_identifiers(source.get("sanitized_reason_ids") or [], limit=20, max_length=160),
                "readfeel_blocker_ids": dedupe_identifiers(source.get("readfeel_blocker_ids") or [], limit=20, max_length=160),
                "execution_blocker_ids": dedupe_identifiers(source.get("execution_blocker_ids") or [], limit=20, max_length=160),
                "question_need_primary_class": clean_identifier(source.get("question_need_primary_class"), max_length=160),
                "ambiguity_kind_refs": dedupe_identifiers(source.get("ambiguity_kind_refs") or [], limit=20, max_length=160),
                "one_question_fit_ref": clean_identifier(source.get("one_question_fit_ref"), max_length=160),
                "repair_required_refs": dedupe_identifiers(source.get("repair_required_refs") or [], limit=20, max_length=160),
                "plan_candidate_flags": _plan_candidate_flags(source.get("plan_candidate_flags")),
                "selection_only_row": True,
                "reviewer_free_text_included": False,
                "reviewer_note_included": False,
                "reviewer_notes_included": False,
                "raw_body_included": False,
                "returned_emlis_body_included": False,
                "history_surface_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_path_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
                "terminal_output_body_included": False,
                "source_body_not_materialized_in_row": True,
                "question_text_not_materialized_in_row": True,
                "body_free": True,
            }
        )
    return normalized


def _assert_sanitized_review_result_row(row: Mapping[str, Any], *, reviewer_refs: Sequence[str]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS, source="P7-R54-CLR11-row")
    if data.get("schema_version") != P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR11 row schema changed")
    if data.get("selection_only_row") is not True or data.get("body_free") is not True:
        raise ValueError("P7-R54-CLR11 row must stay selection-only body-free")
    for field in ("review_result_row_ref", "selection_row_ref", "case_ref_id", "blind_case_id", "packet_ref_id", "case_role_family_ref", "plan_tier_context_ref", "reviewer_ref", "reviewed_at_ref"):
        if not clean_identifier(data.get(field), max_length=180):
            raise ValueError(f"P7-R54-CLR11 row missing {field}")
    if data.get("reviewer_ref") not in set(reviewer_refs):
        raise ValueError("P7-R54-CLR11 row reviewer must match CLR10 reviewer refs")
    scores = safe_mapping(data.get("axis_scores"))
    if tuple(scores.keys()) != P7_R54_CLR11_RATING_AXIS_REFS:
        raise ValueError("P7-R54-CLR11 row axis score keys changed")
    if data.get("axis_score_count") != len(P7_R54_CLR11_RATING_AXIS_REFS):
        raise ValueError("P7-R54-CLR11 row axis score count changed")
    for axis in P7_R54_CLR11_RATING_AXIS_REFS:
        score = scores.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError("P7-R54-CLR11 row score type invalid")
        if float(score) not in P7_R54_CLR11_SCORE_OPTION_REFS:
            raise ValueError("P7-R54-CLR11 row score outside frozen options")
    if data.get("overall_read_feeling_ref") not in P7_R54_CLR11_OVERALL_READ_FEELING_OPTION_REFS:
        raise ValueError("P7-R54-CLR11 row overall read feeling outside frozen options")
    if data.get("verdict") not in P7_R54_CLR11_VERDICT_OPTION_REFS:
        raise ValueError("P7-R54-CLR11 row verdict outside frozen options")
    if not set(data.get("readfeel_blocker_ids") or []).issubset(set(P7_R54_CLR11_READFEEL_BLOCKER_OPTION_REFS)):
        raise ValueError("P7-R54-CLR11 row readfeel blocker outside frozen options")
    if not set(data.get("execution_blocker_ids") or []).issubset(set(P7_R54_CLR11_EXECUTION_BLOCKER_OPTION_REFS)):
        raise ValueError("P7-R54-CLR11 row execution blocker outside frozen options")
    if data.get("question_need_primary_class") not in P7_R54_CLR11_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-CLR11 row question class outside frozen options")
    if not set(data.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_CLR11_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("P7-R54-CLR11 row ambiguity refs outside frozen options")
    if data.get("one_question_fit_ref") not in P7_R54_CLR11_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("P7-R54-CLR11 row one-question-fit outside frozen options")
    repair_refs = data.get("repair_required_refs") or []
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_CLR11_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("P7-R54-CLR11 row repair refs outside frozen options")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if tuple(flags.keys()) != P7_R54_CLR11_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("P7-R54-CLR11 row plan candidate flags changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("P7-R54-CLR11 row must not finalize P8")
    for false_key in (
        "reviewer_free_text_included", "reviewer_note_included", "reviewer_notes_included", "raw_body_included", "returned_emlis_body_included",
        "history_surface_included", "question_text_included", "draft_question_text_included", "local_path_included", "local_absolute_path_included",
        "body_hash_included", "packet_content_included", "terminal_output_body_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR11 row must keep {false_key}=False")
    if data.get("source_body_not_materialized_in_row") is not True or data.get("question_text_not_materialized_in_row") is not True:
        raise ValueError("P7-R54-CLR11 row must not materialize body/question text")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_clr11_sanitized_review_result_row")


def _rows_ready(rows: Sequence[Mapping[str, Any]], *, clr10_material: Mapping[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    required_count = clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    if len(rows) != required_count:
        blockers.append("sanitized_review_result_row_count_must_be_24")
    packet_refs = _case_refs(rows, "packet_ref_id")
    case_refs = _case_refs(rows, "case_ref_id")
    blind_ids = _case_refs(rows, "blind_case_id")
    row_refs = _case_refs(rows, "review_result_row_ref")
    selection_refs = _case_refs(rows, "selection_row_ref")
    expected_packet_refs = [clean_identifier(item, max_length=180) for item in (clr10_material.get("review_completed_packet_ref_ids") or [])]
    expected_selection_refs = [clean_identifier(item, max_length=180) for item in (clr10_material.get("review_completed_selection_row_refs") or [])]
    if packet_refs != expected_packet_refs:
        blockers.append("sanitized_review_packet_refs_must_match_clr10_completion_refs")
    if selection_refs != expected_selection_refs:
        blockers.append("sanitized_review_selection_row_refs_must_match_clr10_completion_refs")
    if not _unique_non_empty(packet_refs, required_count=required_count):
        blockers.append("sanitized_review_packet_refs_must_be_unique")
    if not _unique_non_empty(case_refs, required_count=required_count):
        blockers.append("sanitized_review_case_refs_must_be_unique")
    if not _unique_non_empty(blind_ids, required_count=required_count):
        blockers.append("sanitized_review_blind_case_ids_must_be_unique")
    if not _unique_non_empty(row_refs, required_count=required_count):
        blockers.append("sanitized_review_row_refs_must_be_unique")
    if not _unique_non_empty(selection_refs, required_count=required_count):
        blockers.append("sanitized_review_selection_row_refs_must_be_unique")
    reviewer_refs = [clean_identifier(item, max_length=120) for item in (clr10_material.get("reviewer_ref_ids") or [])]
    try:
        for row in rows:
            _assert_sanitized_review_result_row(row, reviewer_refs=reviewer_refs)
    except ValueError as exc:
        blockers.append(clean_identifier(str(exc), default="sanitized_review_result_row_contract_failed", max_length=180))
    return not blockers, dedupe_identifiers(blockers, limit=100, max_length=180)


def build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion(
    actual_human_review_local_only_operation: Mapping[str, Any] | None = None,
    *,
    verdict: str = "PASS",
    overall_read_feeling_ref: str = "felt_record_returned_as_line",
) -> list[dict[str, Any]]:
    """Build body-free selection rows that match a completed CLR10 receipt."""
    clr10 = safe_mapping(actual_human_review_local_only_operation) if actual_human_review_local_only_operation is not None else build_p7_r54_clr10_actual_human_review_local_only_operation(
        local_human_review_operation_receipt=build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form()
    )
    assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(clr10)
    packet_refs = [clean_identifier(item, max_length=180) for item in (clr10.get("review_completed_packet_ref_ids") or [])]
    selection_refs = [clean_identifier(item, max_length=180) for item in (clr10.get("review_completed_selection_row_refs") or [])]
    reviewer_ref = clean_identifier((clr10.get("reviewer_ref_ids") or ["r54-local-reviewer-bodyfree-ref-001"])[0], default="r54-local-reviewer-bodyfree-ref-001", max_length=120)
    scores = {axis: 1.0 for axis in P7_R54_CLR11_RATING_AXIS_REFS}
    rows: list[dict[str, Any]] = []
    for index, packet_ref in enumerate(packet_refs, start=1):
        family = "p5_history_line_review" if index <= 20 else "current_only_boundary_case"
        rows.append(
            {
                "review_result_row_ref": f"r54clr11-sanitized-review-row-{index:03d}",
                "selection_row_ref": selection_refs[index - 1],
                "case_ref_id": f"r54-clr-case-ref-{index:03d}",
                "blind_case_id": f"p7r48-p5-bqa-r54clr-{index:03d}",
                "packet_ref_id": packet_ref,
                "case_index": index,
                "case_role_family_ref": family,
                "plan_tier_context_ref": "plan_tier_current_snapshot_bodyfree",
                "reviewer_ref": reviewer_ref,
                "reviewed_at_ref": "coarse_reviewed_at_ref_20260627",
                "axis_scores": dict(scores),
                "overall_read_feeling_ref": overall_read_feeling_ref,
                "verdict": verdict,
                "sanitized_reason_ids": [],
                "readfeel_blocker_ids": [],
                "execution_blocker_ids": [],
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "plan_candidate_flags": {key: False for key in P7_R54_CLR11_PLAN_CANDIDATE_FLAG_REFS},
            }
        )
    return rows


def build_p7_r54_clr11_sanitized_review_result_row_intake(
    *,
    actual_human_review_local_only_operation: Mapping[str, Any] | None = None,
    reviewer_selection_rows: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_clr11_sanitized_review_result_row_intake",
) -> dict[str, Any]:
    """Intake sanitized body-free reviewer selection rows for CLR11."""
    clr10 = safe_mapping(actual_human_review_local_only_operation) if actual_human_review_local_only_operation is not None else build_p7_r54_clr10_actual_human_review_local_only_operation()
    assert_p7_r54_clr10_actual_human_review_local_only_operation_contract(clr10)
    allows_next = bool(
        clr10.get("review_operation_status") == P7_R54_CLR10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
        and clr10.get("sanitized_review_result_row_intake_allowed_next") is True
        and clr10.get("next_required_step") == P7_R54_CLR11_STEP_REF
    )
    review_session_id = _safe_review_session_id(clr10.get("review_session_id"))
    submitted_count = len(list(reviewer_selection_rows or [])) if allows_next else 0
    normalized_rows = _normalized_sanitized_review_rows(reviewer_selection_rows or [], review_session_id=review_session_id) if allows_next else []
    rows_ready, row_blockers = _rows_ready(normalized_rows, clr10_material=clr10) if allows_next else (False, ["r54_clr11_blocked_until_clr10_completed_state_ready"])
    intake_ready = bool(allows_next and rows_ready)
    rows = normalized_rows if intake_ready else []
    packet_refs = _case_refs(rows, "packet_ref_id")
    case_refs = _case_refs(rows, "case_ref_id")
    blind_ids = _case_refs(rows, "blind_case_id")
    selection_refs = _case_refs(rows, "selection_row_ref")
    reviewer_refs = _case_refs(rows, "reviewer_ref")
    execution_blockers = [] if intake_ready else dedupe_identifiers([*row_blockers, *(clr10.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    reason_refs = [P7_R54_CLR11_READY_REASON_REF] if intake_ready else dedupe_identifiers([P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF, *execution_blockers], limit=100, max_length=180)
    material = {
        "schema_version": P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR11_STEP_REF,
        "operation_step_ref": P7_R54_CLR11_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr11_sanitized_review_result_row_intake", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr10_schema_version": P7_R54_CLR10_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_SCHEMA_VERSION,
        "clr10_material_ref": clean_identifier(clr10.get("material_id"), default="p7_r54_clr10_actual_human_review_local_only_operation", max_length=220),
        "clr10_next_required_step": clean_identifier(clr10.get("next_required_step"), default=P7_R54_CLR10_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "clr10_review_operation_status": clean_identifier(clr10.get("review_operation_status"), default=P7_R54_CLR10_REVIEW_NOT_STARTED_STATUS_REF, max_length=180),
        "clr10_review_operation_receipt_status": clean_identifier(clr10.get("review_operation_receipt_status"), default=P7_R54_CLR10_OPERATION_RECEIPT_BLOCKED_STATUS_REF, max_length=180),
        "clr10_sanitized_review_result_row_intake_allowed_next": bool(clr10.get("sanitized_review_result_row_intake_allowed_next") is True),
        "existing_op11_helper_ref": "build_p7_r54_op11_sanitized_review_result_capture",
        "existing_op11_schema_version": r54op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "existing_op11_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op11_current_refs_are_historical_here": True,
        "existing_op11_reused_as_actual_intake_basis": False,
        "existing_op11_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_packet_ref_ids": list(clr10.get("review_completed_packet_ref_ids") or []) if allows_next else [],
        "expected_packet_ref_count": int(clr10.get("review_completed_packet_ref_count") or 0) if allows_next else 0,
        "expected_selection_row_refs": list(clr10.get("review_completed_selection_row_refs") or []) if allows_next else [],
        "expected_selection_row_ref_count": int(clr10.get("review_completed_selection_row_count") or 0) if allows_next else 0,
        "submitted_selection_row_count": submitted_count,
        "sanitized_review_result_intake_status": P7_R54_CLR11_INTAKE_READY_STATUS_REF if intake_ready else P7_R54_CLR11_INTAKE_BLOCKED_STATUS_REF,
        "sanitized_review_result_intake_ref": P7_R54_CLR11_SANITIZED_REVIEW_RESULT_INTAKE_REF if intake_ready else "sanitized_review_result_row_intake_not_ready_bodyfree",
        "sanitized_review_result_intake_policy_ref": P7_R54_CLR11_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF,
        "sanitized_review_result_intake_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "sanitized_review_result_rows": rows,
        "sanitized_review_result_row_count": len(rows),
        "reviewed_case_count": len(rows),
        "packet_ref_ids": packet_refs,
        "packet_ref_count": len(packet_refs),
        "packet_ref_ids_unique": _unique_non_empty(packet_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if intake_ready else False,
        "case_ref_ids": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_ids_unique": _unique_non_empty(case_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if intake_ready else False,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _unique_non_empty(blind_ids, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if intake_ready else False,
        "selection_row_refs": selection_refs,
        "selection_row_ref_count": len(selection_refs),
        "selection_row_refs_unique": _unique_non_empty(selection_refs, required_count=clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT) if intake_ready else False,
        "reviewer_ref_ids": dedupe_identifiers(reviewer_refs, limit=8, max_length=120),
        "reviewer_ref_count": len(dedupe_identifiers(reviewer_refs, limit=8, max_length=120)),
        "case_role_family_counts": _count_by(rows, "case_role_family_ref") if intake_ready else {},
        "plan_tier_context_counts": _count_by(rows, "plan_tier_context_ref") if intake_ready else {},
        "selection_rows_are_bodyfree_only": intake_ready,
        "sanitized_rows_contain_reviewer_free_text": False,
        "sanitized_rows_contain_reviewer_note": False,
        "sanitized_rows_contain_reviewer_notes": False,
        "sanitized_rows_contain_raw_body": False,
        "sanitized_rows_contain_returned_body": False,
        "sanitized_rows_contain_history_surface": False,
        "sanitized_rows_contain_question_text": False,
        "sanitized_rows_contain_local_path": False,
        "sanitized_rows_contain_local_absolute_path": False,
        "sanitized_rows_contain_body_hash": False,
        "sanitized_rows_contain_packet_content": False,
        "sanitized_rows_contain_terminal_output_body": False,
        "sanitized_review_result_rows_materialized_here": intake_ready,
        "rating_row_normalization_allowed_next": intake_ready,
        "actual_human_review_run_by_helper": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR11_IMPLEMENTED_STEPS if intake_ready else (clr10.get("implemented_steps") or [])),
        "not_yet_implemented_steps": list(P7_R54_CLR11_NOT_YET_IMPLEMENTED_STEPS if intake_ready else (clr10.get("not_yet_implemented_steps") or [])),
        "next_required_step": P7_R54_CLR12_STEP_REF if intake_ready else P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr11_sanitized_review_result_row_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(data, required=P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS, source="P7-R54-CLR11")
    _assert_base(data, schema_version=P7_R54_CLR11_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION, policy_section=P7_R54_CLR11_STEP_REF, source="P7-R54-CLR11")
    _assert_current_refs(data, source="P7-R54-CLR11")
    if safe_mapping(data.get("existing_op11_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR11 OP11 refs changed")
    if data.get("existing_op11_current_refs_are_historical_here") is not True or data.get("existing_op11_reused_as_actual_intake_basis") is not False:
        raise ValueError("P7-R54-CLR11 historical OP11 boundary changed")
    if data.get("existing_op11_structural_contract_reused") is not True:
        raise ValueError("P7-R54-CLR11 must reuse OP11 only structurally")
    if data.get("required_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR11 required case count changed")
    if data.get("sanitized_review_result_intake_status") not in P7_R54_CLR11_ALLOWED_INTAKE_STATUS_REFS:
        raise ValueError("P7-R54-CLR11 intake status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-CLR11 blockers mismatch")
    for false_key in (
        "sanitized_rows_contain_reviewer_free_text", "sanitized_rows_contain_reviewer_note", "sanitized_rows_contain_reviewer_notes", "sanitized_rows_contain_raw_body",
        "sanitized_rows_contain_returned_body", "sanitized_rows_contain_history_surface", "sanitized_rows_contain_question_text", "sanitized_rows_contain_local_path",
        "sanitized_rows_contain_local_absolute_path", "sanitized_rows_contain_body_hash", "sanitized_rows_contain_packet_content", "sanitized_rows_contain_terminal_output_body",
        "actual_human_review_run_by_helper", "actual_human_review_run_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete", "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"P7-R54-CLR11 must keep {false_key}=False")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("P7-R54-CLR11 must not materialize rating/question normalized rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("P7-R54-CLR11 must block review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True or data.get("p5_finalization_blocked_here") is not True:
        raise ValueError("P7-R54-CLR11 must block promotion/finalization")
    ready = data.get("sanitized_review_result_intake_status") == P7_R54_CLR11_INTAKE_READY_STATUS_REF
    if ready:
        if data.get("clr10_sanitized_review_result_row_intake_allowed_next") is not True or data.get("clr10_next_required_step") != P7_R54_CLR11_STEP_REF:
            raise ValueError("P7-R54-CLR11 ready intake requires completed CLR10")
        if blockers:
            raise ValueError("P7-R54-CLR11 ready intake must not carry blockers")
        rows = [safe_mapping(row) for row in (data.get("sanitized_review_result_rows") or [])]
        if len(rows) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR11 ready intake must contain 24 rows")
        if data.get("sanitized_review_result_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("reviewed_case_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR11 ready intake count changed")
        if data.get("expected_packet_ref_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("expected_selection_row_ref_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR11 expected ref counts changed")
        if data.get("submitted_selection_row_count") != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-CLR11 submitted row count changed")
        if data.get("packet_ref_ids") != data.get("expected_packet_ref_ids"):
            raise ValueError("P7-R54-CLR11 packet refs must match CLR10 expected refs")
        if data.get("selection_row_refs") != data.get("expected_selection_row_refs"):
            raise ValueError("P7-R54-CLR11 selection refs must match CLR10 expected refs")
        for key in ("packet_ref_ids_unique", "case_ref_ids_unique", "blind_case_ids_unique", "selection_row_refs_unique", "selection_rows_are_bodyfree_only", "sanitized_review_result_rows_materialized_here", "rating_row_normalization_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-CLR11 ready intake must keep {key}=True")
        if data.get("reviewer_ref_count", 0) < 1:
            raise ValueError("P7-R54-CLR11 ready intake requires reviewer refs")
        for row in rows:
            _assert_sanitized_review_result_row(row, reviewer_refs=data.get("reviewer_ref_ids") or [])
        if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_CLR12_STEP_REF:
            raise ValueError("P7-R54-CLR11 ready intake must point to CLR12")
    else:
        if data.get("sanitized_review_result_rows") != [] or data.get("sanitized_review_result_row_count") != 0:
            raise ValueError("P7-R54-CLR11 blocked intake must not materialize rows")
        if data.get("selection_rows_are_bodyfree_only") is not False or data.get("rating_row_normalization_allowed_next") is not False:
            raise ValueError("P7-R54-CLR11 blocked intake must not allow rating normalization")
        if data.get("sanitized_review_result_rows_materialized_here") is not False:
            raise ValueError("P7-R54-CLR11 blocked intake must not materialize rows")
        if not blockers:
            raise ValueError("P7-R54-CLR11 blocked intake must carry blockers")
        if data.get("next_required_step") != P7_R54_CLR11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-CLR11 blocked next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr10_actual_human_review_local_only_operation = build_p7_r54_clr10_actual_human_review_local_only_operation
assert_p7_r54_current_snapshot_local_run_clr10_actual_human_review_local_only_operation_contract = assert_p7_r54_clr10_actual_human_review_local_only_operation_contract
build_p7_r54_current_snapshot_actual_human_review_local_only_operation_bodyfree = build_p7_r54_clr10_actual_human_review_local_only_operation
assert_p7_r54_current_snapshot_actual_human_review_local_only_operation_bodyfree_contract = assert_p7_r54_clr10_actual_human_review_local_only_operation_contract

build_p7_r54_current_snapshot_local_run_clr10_bodyfree_completed_review_operation_receipt_from_form = build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form
build_p7_r54_current_snapshot_actual_human_review_completion_receipt_bodyfree = build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form

build_p7_r54_current_snapshot_local_run_clr11_bodyfree_selection_rows_from_clr10_completion = build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion
build_p7_r54_current_snapshot_sanitized_selection_rows_bodyfree = build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion
build_p7_r54_current_snapshot_local_run_clr11_sanitized_review_result_row_intake = build_p7_r54_clr11_sanitized_review_result_row_intake
assert_p7_r54_current_snapshot_local_run_clr11_sanitized_review_result_row_intake_contract = assert_p7_r54_clr11_sanitized_review_result_row_intake_contract
build_p7_r54_current_snapshot_sanitized_review_result_row_intake_bodyfree = build_p7_r54_clr11_sanitized_review_result_row_intake
assert_p7_r54_current_snapshot_sanitized_review_result_row_intake_bodyfree_contract = assert_p7_r54_clr11_sanitized_review_result_row_intake_contract

build_clr10_bodyfree_completed_review_operation_receipt_from_form = build_p7_r54_clr10_bodyfree_completed_review_operation_receipt_from_form
build_clr10_actual_human_review_local_only_operation = build_p7_r54_clr10_actual_human_review_local_only_operation
assert_clr10_actual_human_review_local_only_operation_contract = assert_p7_r54_clr10_actual_human_review_local_only_operation_contract
build_clr11_bodyfree_selection_rows_from_clr10_completion = build_p7_r54_clr11_bodyfree_selection_rows_from_clr10_completion
build_clr11_sanitized_review_result_row_intake = build_p7_r54_clr11_sanitized_review_result_row_intake
assert_clr11_sanitized_review_result_row_intake_contract = assert_p7_r54_clr11_sanitized_review_result_row_intake_contract
