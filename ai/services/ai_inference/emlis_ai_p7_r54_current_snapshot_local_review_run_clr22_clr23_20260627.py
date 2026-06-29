# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR22-CLR23 helpers.

CLR22 performs the final body-free validation that checks for body-full leakage,
question text materialization, and no-touch boundary violations after the P6/P8
candidate-only handoffs.  It does not export packet content, question text,
local paths, hashes, or terminal output bodies.

CLR23 materializes only a body-free R52 re-intake handoff.  It may mark the
body-free evidence envelope as ready for R52 only after CLR22 has passed, while
still keeping P5 final confirmation, P6 start, P8 start, P7 completion, and
release permission closed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_FORBIDDEN_BODY_KEYS,
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
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr14_clr15_20260627 as clr15
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr18_clr19_20260627 as clr19
import emlis_ai_p7_r54_current_snapshot_local_review_run_clr20_clr21_20260627 as clr21


P7_R54_CLR22_FINAL_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr22_final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)
P7_R54_CLR23_R52_REINTAKE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr23_r52_reintake_handoff.bodyfree.v1"
)
P7_R54_CLR22_SCHEMA_VERSION: Final = P7_R54_CLR22_FINAL_VALIDATION_SCHEMA_VERSION
P7_R54_CLR23_SCHEMA_VERSION: Final = P7_R54_CLR23_R52_REINTAKE_HANDOFF_SCHEMA_VERSION

P7_R54_CLR_STEP: Final = clr03.P7_R54_CLR_STEP
P7_R54_CLR_SCOPE: Final = clr03.P7_R54_CLR_SCOPE
P7_R54_CLR_POLICY_KIND: Final = clr03.P7_R54_CLR_POLICY_KIND
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = clr03.P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
P7_R54_CLR22_STEP_REF: Final = clr03.P7_R54_CLR22_STEP_REF
P7_R54_CLR23_STEP_REF: Final = clr03.P7_R54_CLR23_STEP_REF
P7_R54_CLR24_STEP_REF: Final = clr03.P7_R54_CLR24_STEP_REF

P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF: Final = (
    "FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY_BODYFREE_20260627"
)
P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF: Final = (
    "FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BLOCKED_20260627"
)
P7_R54_CLR22_BODY_LEAK_OR_QUESTION_TEXT_BLOCKED_STATUS_REF: Final = (
    "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
)
P7_R54_CLR22_NO_TOUCH_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_NO_TOUCH_VIOLATION"
P7_R54_CLR22_ALLOWED_FINAL_VALIDATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF,
    P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF,
    P7_R54_CLR22_BODY_LEAK_OR_QUESTION_TEXT_BLOCKED_STATUS_REF,
    P7_R54_CLR22_NO_TOUCH_BLOCKED_STATUS_REF,
)
P7_R54_CLR22_FINAL_VALIDATION_REF: Final = "R54_CLR22_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_20260627"
P7_R54_CLR22_READY_DECISION_REF: Final = "R54_CLR22_FINAL_BODYFREE_VALIDATION_READY"
P7_R54_CLR22_BLOCKED_DECISION_REF: Final = "R54_CLR22_FINAL_BODYFREE_VALIDATION_BLOCKED"
P7_R54_CLR22_READY_REASON_REF: Final = "r54_clr22_final_validation_ready_bodyfree"
P7_R54_CLR22_INPUT_BLOCKED_REASON_REF: Final = (
    "r54_clr22_blocked_until_clr21_p8_material_candidate_only_handoff_ready"
)
P7_R54_CLR22_BODY_LEAK_BLOCKED_REASON_REF: Final = (
    "r54_clr22_body_leak_or_question_text_detected_bodyfree"
)
P7_R54_CLR22_NO_TOUCH_BLOCKED_REASON_REF: Final = "r54_clr22_no_touch_boundary_violation_detected_bodyfree"
P7_R54_CLR22_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-CLR-22_blocked_until_clr21_p8_material_candidate_only_handoff_ready_before_final_validation"
)
P7_R54_CLR22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "body_leak_or_question_text_repair_before_r52_reintake_handoff"
)
P7_R54_CLR22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "no_touch_boundary_repair_before_r52_reintake_handoff"
)
P7_R54_CLR22_NEXT_WORK_AFTER_CLR21_REF: Final = (
    "r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_after_candidate_handoffs"
)
P7_R54_CLR22_NEXT_WORK_AFTER_CLR22_REF: Final = "r54_clr23_r52_reintake_handoff_after_final_validation"

P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF: Final = "R54_R52_REINTAKE_HANDOFF_READY"
P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF: Final = (
    "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
)
P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_DISPOSAL"
P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF: Final = (
    "R54_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT"
)
P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF: Final = (
    "R54_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION"
)
P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE"
P7_R54_CLR23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF,
    P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF,
    P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF,
    P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF,
    P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF,
    P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF,
)
P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF: Final = "R54_CLR23_R52_REINTAKE_HANDOFF_BODYFREE_20260627"
P7_R54_CLR23_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF: Final = (
    "R54_CLR23_BODYFREE_ACTUAL_REVIEW_EVIDENCE_READY_FOR_R52_REINTAKE_20260627"
)
P7_R54_CLR23_R52_REINTAKE_DECISION_REF: Final = "R52_REINTAKE_REQUIRED"
P7_R54_CLR23_R52_REINTAKE_REQUIRED_REF: Final = (
    "R52_REINTAKE_REQUIRED_AFTER_R54_CURRENT_SNAPSHOT_ACTUAL_LOCAL_REVIEW_BODYFREE_20260627"
)
P7_R54_CLR23_READY_REASON_REF: Final = "r54_clr23_r52_reintake_handoff_ready_bodyfree_actual_review_evidence"
P7_R54_CLR23_EVIDENCE_MISSING_REASON_REF: Final = "r54_clr23_actual_review_evidence_missing_or_incomplete"
P7_R54_CLR23_DISPOSAL_BLOCKED_REASON_REF: Final = "r54_clr23_disposal_not_verified"
P7_R54_CLR23_BODY_LEAK_BLOCKED_REASON_REF: Final = "r54_clr23_blocked_by_body_leak_or_question_text_validation"
P7_R54_CLR23_NO_TOUCH_BLOCKED_REASON_REF: Final = "r54_clr23_blocked_by_no_touch_validation"
P7_R54_CLR23_INCONCLUSIVE_REASON_REF: Final = "r54_clr23_operation_inconclusive_before_r52_reintake"
P7_R54_CLR23_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "r52_reintake_handoff_blocked_until_bodyfree_actual_review_evidence_ready"
)
P7_R54_CLR23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "disposal_receipt_repair_before_r52_reintake_handoff"
P7_R54_CLR23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "body_leak_or_question_text_repair_before_r52_reintake_handoff"
)
P7_R54_CLR23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "no_touch_boundary_repair_before_r52_reintake_handoff"
P7_R54_CLR23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "r54_operation_inconclusive_retry_or_r52_reintake_repair"
P7_R54_CLR23_NEXT_WORK_AFTER_CLR22_REF: Final = "r54_clr23_r52_reintake_handoff_after_final_validation"
P7_R54_CLR23_NEXT_WORK_AFTER_CLR23_REF: Final = (
    "r54_clr24_validation_command_matrix_documentation_output_after_r52_reintake_handoff"
)

P7_R54_CLR22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*clr21.P7_R54_CLR21_IMPLEMENTED_STEPS, P7_R54_CLR22_STEP_REF)
P7_R54_CLR22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[21:]
P7_R54_CLR23_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_CLR22_IMPLEMENTED_STEPS, P7_R54_CLR23_STEP_REF)
P7_R54_CLR23_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = clr03.P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[22:]

P7_R54_CLR22_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_candidate",
        "p8_question_design_material_candidate",
    }
)
P7_R54_CLR23_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        *P7_R54_CLR22_ALLOWED_TRUE_FALSE_FLAG_REFS,
        "actual_review_evidence_complete",
    }
)

P7_R54_CLR22_FINAL_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr21_schema_version",
    "clr21_material_ref",
    "clr21_next_required_step",
    "clr21_p8_material_candidate_handoff_status",
    "clr21_p8_question_design_material_candidate",
    "clr21_p8_start_allowed",
    "existing_op22_helper_ref",
    "existing_op22_schema_version",
    "existing_op22_operation_current_refs",
    "existing_op22_current_refs_are_historical_here",
    "existing_op22_reused_as_actual_final_validation_basis",
    "existing_op22_structural_contract_reused",
    "existing_ev20_helper_ref",
    "existing_ev20_schema_version",
    "existing_ev20_current_refs",
    "existing_ev20_current_refs_are_historical_here",
    "existing_ev20_reused_as_actual_final_validation_basis",
    "existing_ev20_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "question_need_observation_rows_aggregated_count",
    "disposal_verified",
    "p5_decision_candidate_ref",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate_ref",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_material_candidate_only_ref",
    "p8_question_design_material_candidate_ref",
    "p8_question_design_material_candidate",
    "p8_material_candidate_row_count",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "release_allowed",
    "validation_evidence_ref",
    "validation_evidence_bodyfree_only",
    "final_validation_status",
    "final_validation_ref",
    "final_validation_decision_ref",
    "final_validation_reason_refs",
    "final_validation_issue_refs",
    "final_validation_issue_count",
    "final_validation_failure_class_ref",
    "body_leak_violation_refs",
    "body_leak_violation_count",
    "question_text_violation_refs",
    "question_text_violation_count",
    "no_touch_violation_refs",
    "no_touch_violation_count",
    "body_leak_or_question_text_violation_detected",
    "no_touch_violation_detected",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "final_validation_passed",
    "r52_reintake_handoff_allowed_next",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "raw_body_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR23_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *clr03.P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr22_schema_version",
    "clr22_material_ref",
    "clr22_next_required_step",
    "clr22_final_validation_status",
    "clr22_r52_reintake_handoff_allowed_next",
    *clr03.P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "actual_review_basis_refs",
    "existing_op23_helper_ref",
    "existing_op23_schema_version",
    "existing_op23_operation_current_refs",
    "existing_op23_current_refs_are_historical_here",
    "existing_op23_reused_as_actual_r52_handoff_basis",
    "existing_op23_structural_contract_reused",
    "existing_ev21_helper_ref",
    "existing_ev21_schema_version",
    "existing_ev21_current_refs",
    "existing_ev21_current_refs_are_historical_here",
    "existing_ev21_reused_as_actual_r52_handoff_basis",
    "existing_ev21_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "handoff_status",
    "handoff_ref",
    "handoff_reason_refs",
    "r52_reintake_decision_ref",
    "r52_reintake_handoff_ready",
    "r52_reintake_handoff_status",
    "r52_reintake_handoff_ref",
    "r52_reintake_handoff_reason_refs",
    "r52_reintake_required_ref",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_bodyfree_receipts",
    "r52_bodyfree_actual_review_evidence_complete",
    "r52_bodyfree_evidence_handoff_ready",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "rating_rows_bodyfree_handoff_count",
    "question_observation_rows_bodyfree_handoff_count",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "final_validation_status",
    "p5_decision_candidate",
    "p5_decision_candidate_ref",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_candidate_only",
    "p6_candidate_only_ref",
    "p6_limited_human_readfeel_candidate_ref",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_material_candidate_only",
    "p8_material_candidate_only_ref",
    "p8_question_design_material_candidate_ref",
    "p8_question_design_material_candidate",
    "p8_material_candidate_row_count",
    "p8_design_material_candidate_only_not_start",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_trigger_logic_implemented",
    "question_answer_persistence_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_plan_guard_implemented",
    "question_storage_schema_implemented",
    "question_text_included",
    "draft_question_text_included",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "release_allowed",
    "p7_complete",
    "body_free_evidence_handoff_materialized_here",
    "r52_reintake_required",
    "body_free_actual_review_evidence_ref",
    "body_free_result_handoff_ref",
    "handoff_evidence_refs",
    "handoff_evidence_ref_count",
    "r52_handoff_preserves_candidate_only_boundaries",
    "r52_handoff_contains_body_full_packet",
    "r52_handoff_contains_question_text",
    "r52_handoff_contains_local_path",
    "r52_handoff_contains_payload_hash",
    "r52_handoff_contains_reviewer_free_text",
    "r52_handoff_contains_raw_payload",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    *clr03.P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    "body_free",
    "raw_body_included",
    "local_path_included",
    *clr03.P7_R54_CLR_FALSE_FLAG_REFS,
)

_BODY_LEAK_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_body_included",
        "returned_emlis_body_included",
        "history_surface_included",
        "reviewer_free_text_included",
        "reviewer_note_included",
        "reviewer_notes_included",
        "reviewer_notes_body_included",
        "local_path_included",
        "local_absolute_path_included",
        "body_hash_included",
        "packet_content_included",
        "terminal_output_body_included",
        "body_full_packet_export_candidate",
        "body_full_packet_generated_here",
        "body_full_packet_generation_started_here",
        "body_full_generation_requested_here",
        "body_full_packet_generation_requested_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
    }
)
_QUESTION_TEXT_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "question_text_included",
        "draft_question_text_included",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "question_implementation_started_here",
        "question_trigger_logic_implemented",
        "question_answer_persistence_implemented",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_plan_guard_implemented",
        "question_storage_schema_implemented",
        "p8_implementation_spec_finalized_here",
        "p8_question_implementation_spec_finalized_here",
    }
)
_NO_TOUCH_FLAG_REFS: Final[frozenset[str]] = frozenset(
    {
        "api_changed",
        "db_changed",
        "rn_changed",
        "runtime_changed",
        "api_route_changed",
        "request_key_changed",
        "response_key_changed",
        "response_shape_changed",
        "db_schema_changed",
        "db_migration_changed",
        "db_migration_added",
        "db_physical_schema_changed",
        "rn_ui_changed",
        "rn_visible_contract_changed",
        "public_response_top_level_key_added",
        "public_response_key_changed",
        "runtime_gate_threshold_changed",
        "user_label_connection_runtime_changed",
        "emlis_visible_output_generation_changed",
        "subscription_or_plan_access_policy_changed",
        "api_db_rn_response_key_changed_here",
        "runtime_changed_here",
    }
)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=180)


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    required_set = set(required)
    missing = [field for field in required if field not in data]
    extra = [field for field in data if field not in required_set]
    if missing or extra:
        raise ValueError(f"{source} field mismatch missing={missing[:10]} extra={extra[:10]}")


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


def _false_flags_except(*allowed_true_refs: str) -> dict[str, bool]:
    allowed = set(allowed_true_refs)
    return {key: False for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS if key not in allowed}


def _assert_all_false(mapping: Mapping[str, Any], *, source: str) -> None:
    if not isinstance(mapping, Mapping):
        raise ValueError(f"{source} must be a mapping")
    true_keys = [str(key) for key, value in mapping.items() if value is True]
    if true_keys:
        raise ValueError(f"{source} must keep all markers false: {true_keys[:8]}")


def _assert_common_base(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, source: str, allowed_true_false_flags: frozenset[str]
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("step") != P7_R54_CLR_STEP:
        raise ValueError(f"{source} P7 phase/step changed")
    if data.get("scope") != P7_R54_CLR_SCOPE or data.get("policy_kind") != P7_R54_CLR_POLICY_KIND:
        raise ValueError(f"{source} scope/policy changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != policy_section:
        raise ValueError(f"{source} policy section changed")
    if data.get("source_mode") != P7_SOURCE_MODE or data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} source mode/git boundary changed")
    for key in clr03.P7_R54_CLR_FALSE_FLAG_REFS:
        value = data.get(key)
        if key in allowed_true_false_flags:
            if not isinstance(value, bool):
                raise ValueError(f"{source} {key} must remain boolean")
        elif value is not False:
            raise ValueError(f"{source} must keep {key}=False")
    for key in (
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
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    _assert_all_false(safe_mapping(data.get("public_contract")), source=f"{source}.public_contract")
    _assert_all_false(safe_mapping(data.get("r54_clr_no_touch_contract")), source=f"{source}.r54_clr_no_touch_contract")
    _assert_all_false(safe_mapping(data.get("body_free_markers")), source=f"{source}.body_free_markers")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body_free")
    if safe_mapping(data.get("operation_current_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current snapshot refs changed")
    if data.get("operation_current_refs_are_actual_review_basis") is not True or data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError(f"{source} current snapshot must be actual review basis")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _collect_probe_refs(value: Any) -> tuple[list[str], list[str], list[str]]:
    body_refs: list[str] = []
    question_refs: list[str] = []
    no_touch_refs: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            for raw_key, child in node.items():
                key = str(raw_key)
                clean_key = clean_identifier(key, default="unknown_marker", max_length=120)
                if key in P7_FORBIDDEN_BODY_KEYS:
                    body_refs.append(f"forbidden_body_payload_key_detected__{clean_key}")
                if key in _BODY_LEAK_FLAG_REFS and child is True:
                    body_refs.append(f"{clean_key}_true")
                if key in _QUESTION_TEXT_FLAG_REFS and child is True:
                    question_refs.append(f"{clean_key}_true")
                if key in _NO_TOUCH_FLAG_REFS and child is True:
                    no_touch_refs.append(f"{clean_key}_true")
                if isinstance(child, (Mapping, list, tuple, set)):
                    walk(child)
        elif isinstance(node, (list, tuple, set)):
            for child in node:
                if isinstance(child, (Mapping, list, tuple, set)):
                    walk(child)

    walk(value)
    return (
        dedupe_identifiers(body_refs, limit=120, max_length=180),
        dedupe_identifiers(question_refs, limit=120, max_length=180),
        dedupe_identifiers(no_touch_refs, limit=120, max_length=180),
    )


def _mapping_true_refs(mapping: Any, *, prefix: str) -> list[str]:
    return dedupe_identifiers(
        [f"{prefix}_{clean_identifier(key, default='marker', max_length=120)}_true" for key, value in safe_mapping(mapping).items() if value is True],
        limit=120,
        max_length=180,
    )


def _clr22_prior_refs(prior: Mapping[str, Any]) -> tuple[list[str], list[str], list[str], list[str]]:
    prior_refs: list[str] = []
    body_refs: list[str] = []
    question_refs: list[str] = []
    no_touch_refs: list[str] = []
    if prior.get("p8_material_candidate_handoff_status") != clr21.P7_R54_CLR21_P8_MATERIAL_HANDOFF_READY_STATUS_REF:
        prior_refs.append(P7_R54_CLR22_INPUT_BLOCKED_REASON_REF)
    if prior.get("next_required_step") != P7_R54_CLR22_STEP_REF:
        prior_refs.append("clr21_next_required_step_not_clr22_final_validation")
    prior_refs.extend(dedupe_identifiers(prior.get("open_execution_blocker_ids") or [], limit=120, max_length=180))
    for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
        if int(prior.get(count_key) or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            prior_refs.append(f"{count_key}_not_24_for_clr22_final_validation")
    if prior.get("disposal_verified") is not True:
        prior_refs.append("disposal_not_verified_for_clr22_final_validation")
    for key in ("raw_body_included", "returned_emlis_body_included", "history_surface_included", "reviewer_free_text_included", "local_path_included", "body_hash_included", "packet_content_included", "terminal_output_body_included"):
        if prior.get(key) is True:
            body_refs.append(f"clr21_{key}_true")
    for key in ("question_text_included", "draft_question_text_included", "question_text_materialized_here", "draft_question_text_materialized_here"):
        if prior.get(key) is True:
            question_refs.append(f"clr21_{key}_true")
    no_touch_refs.extend(_mapping_true_refs(prior.get("public_contract"), prefix="clr21_public_contract"))
    no_touch_refs.extend(_mapping_true_refs(prior.get("r54_clr_no_touch_contract"), prefix="clr21_no_touch_contract"))
    for key in (
        "api_changed",
        "db_changed",
        "rn_changed",
        "runtime_changed",
        "api_db_rn_response_key_changed_here",
        "runtime_changed_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_trigger_logic_implemented",
        "question_answer_persistence_implemented",
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "p8_start_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "release_allowed",
        "p7_complete",
    ):
        if prior.get(key) is True:
            no_touch_refs.append(f"clr21_{key}_must_remain_false")
    return (
        dedupe_identifiers(prior_refs, limit=120, max_length=180),
        dedupe_identifiers(body_refs, limit=120, max_length=180),
        dedupe_identifiers(question_refs, limit=120, max_length=180),
        dedupe_identifiers(no_touch_refs, limit=120, max_length=180),
    )


def _clr22_status_next_reason(
    prior_refs: Sequence[str], body_refs: Sequence[str], question_refs: Sequence[str], no_touch_refs: Sequence[str]
) -> tuple[str, str, str, list[str]]:
    if body_refs or question_refs:
        return (
            P7_R54_CLR22_BODY_LEAK_OR_QUESTION_TEXT_BLOCKED_STATUS_REF,
            P7_R54_CLR22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF,
            "body_or_question_text",
            dedupe_identifiers([P7_R54_CLR22_BODY_LEAK_BLOCKED_REASON_REF, *body_refs, *question_refs], limit=120, max_length=180),
        )
    if no_touch_refs:
        return (
            P7_R54_CLR22_NO_TOUCH_BLOCKED_STATUS_REF,
            P7_R54_CLR22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF,
            "no_touch",
            dedupe_identifiers([P7_R54_CLR22_NO_TOUCH_BLOCKED_REASON_REF, *no_touch_refs], limit=120, max_length=180),
        )
    if prior_refs:
        return (
            P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF,
            P7_R54_CLR22_BLOCKED_NEXT_REQUIRED_STEP_REF,
            "clr21_not_ready",
            dedupe_identifiers([P7_R54_CLR22_INPUT_BLOCKED_REASON_REF, *prior_refs], limit=120, max_length=180),
        )
    return (P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF, P7_R54_CLR23_STEP_REF, "none", [P7_R54_CLR22_READY_REASON_REF])


def build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation(
    *,
    p8_material_candidate_only_handoff: Mapping[str, Any] | None = None,
    validation_evidence: Mapping[str, Any] | None = None,
    validation_evidence_ref: Any = "r54_clr22_final_validation_bodyfree_evidence_ref",
    material_id: Any = "p7_r54_clr22_final_validation",
) -> dict[str, Any]:
    """Build CLR22 final body-free validation without exporting body/question material."""
    prior = safe_mapping(p8_material_candidate_only_handoff) if p8_material_candidate_only_handoff is not None else clr21.build_p7_r54_clr21_p8_material_candidate_only_handoff()
    clr21.assert_p7_r54_clr21_p8_material_candidate_only_handoff_contract(prior)
    prior_refs, prior_body_refs, prior_question_refs, prior_no_touch_refs = _clr22_prior_refs(prior)
    probe_body_refs, probe_question_refs, probe_no_touch_refs = _collect_probe_refs(validation_evidence or {})
    body_refs = dedupe_identifiers([*prior_body_refs, *probe_body_refs], limit=120, max_length=180)
    question_refs = dedupe_identifiers([*prior_question_refs, *probe_question_refs], limit=120, max_length=180)
    no_touch_refs = dedupe_identifiers([*prior_no_touch_refs, *probe_no_touch_refs], limit=120, max_length=180)
    status, next_step, failure_class, reason_refs = _clr22_status_next_reason(prior_refs, body_refs, question_refs, no_touch_refs)
    ready = status == P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF
    issue_refs = dedupe_identifiers([*prior_refs, *body_refs, *question_refs, *no_touch_refs], limit=120, max_length=180)
    blockers = [] if ready else dedupe_identifiers([*reason_refs, *issue_refs], limit=120, max_length=180)
    p8_candidate = prior.get("p8_question_design_material_candidate") is True and ready
    material = {
        "schema_version": P7_R54_CLR22_FINAL_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR22_STEP_REF,
        "operation_step_ref": P7_R54_CLR22_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr22_final_validation", max_length=220),
        "review_session_id": _safe_review_session_id(prior.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr21_schema_version": clr21.P7_R54_CLR21_SCHEMA_VERSION,
        "clr21_material_ref": clean_identifier(prior.get("material_id"), default="p7_r54_clr21_p8_material_candidate_only_handoff", max_length=220),
        "clr21_next_required_step": clean_identifier(prior.get("next_required_step"), default="", max_length=220),
        "clr21_p8_material_candidate_handoff_status": clean_identifier(prior.get("p8_material_candidate_handoff_status"), default=clr21.P7_R54_CLR21_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF, max_length=180),
        "clr21_p8_question_design_material_candidate": prior.get("p8_question_design_material_candidate") is True,
        "clr21_p8_start_allowed": prior.get("p8_start_allowed") is True,
        "existing_op22_helper_ref": "build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation",
        "existing_op22_schema_version": r54op.P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "existing_op22_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op22_current_refs_are_historical_here": True,
        "existing_op22_reused_as_actual_final_validation_basis": False,
        "existing_op22_structural_contract_reused": True,
        "existing_ev20_helper_ref": "build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation",
        "existing_ev20_schema_version": r54ev.P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "existing_ev20_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev20_current_refs_are_historical_here": True,
        "existing_ev20_reused_as_actual_final_validation_basis": False,
        "existing_ev20_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(prior.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(prior.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(prior.get("question_observation_row_count") or 0) if ready else 0,
        "question_need_observation_rows_aggregated_count": int(prior.get("question_need_observation_rows_aggregated_count") or 0) if ready else 0,
        "disposal_verified": prior.get("disposal_verified") is True and ready,
        "p5_decision_candidate_ref": clr19.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF if prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready else clr19.P7_R54_CLR19_INCONCLUSIVE_REF,
        "p5_human_blind_qa_confirmed_candidate": prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate_ref": clean_identifier(prior.get("p6_limited_human_readfeel_candidate_ref"), default=clr21.P7_R54_CLR20_P6_CANDIDATE_REF, max_length=220) if prior.get("p6_limited_human_readfeel_candidate") is True and ready else "",
        "p6_limited_human_readfeel_candidate": prior.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_material_candidate_only_ref": clean_identifier(prior.get("p8_material_candidate_handoff_ref"), default=clr21.P7_R54_CLR21_P8_MATERIAL_HANDOFF_REF, max_length=220) if ready else "",
        "p8_question_design_material_candidate_ref": clean_identifier(prior.get("p8_question_design_material_candidate_ref"), default=clr21.P7_R54_CLR21_P8_MATERIAL_CANDIDATE_REF, max_length=220) if p8_candidate else "",
        "p8_question_design_material_candidate": p8_candidate,
        "p8_material_candidate_row_count": int(prior.get("p8_material_candidate_row_count") or 0) if ready else 0,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "release_allowed": False,
        "validation_evidence_ref": clean_identifier(validation_evidence_ref, default="r54_clr22_final_validation_bodyfree_evidence_ref", max_length=220),
        "validation_evidence_bodyfree_only": True,
        "final_validation_status": status,
        "final_validation_ref": P7_R54_CLR22_FINAL_VALIDATION_REF if ready else "r54_clr22_final_validation_not_ready_bodyfree_20260627",
        "final_validation_decision_ref": P7_R54_CLR22_READY_DECISION_REF if ready else P7_R54_CLR22_BLOCKED_DECISION_REF,
        "final_validation_reason_refs": reason_refs,
        "final_validation_issue_refs": issue_refs,
        "final_validation_issue_count": len(issue_refs),
        "final_validation_failure_class_ref": failure_class,
        "body_leak_violation_refs": body_refs,
        "body_leak_violation_count": len(body_refs),
        "question_text_violation_refs": question_refs,
        "question_text_violation_count": len(question_refs),
        "no_touch_violation_refs": no_touch_refs,
        "no_touch_violation_count": len(no_touch_refs),
        "body_leak_or_question_text_violation_detected": bool(body_refs or question_refs),
        "no_touch_violation_detected": bool(no_touch_refs),
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "final_validation_passed": ready,
        "r52_reintake_handoff_allowed_next": ready,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_rating_rows_materialized_here": prior.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_blocker_rows_materialized_here": prior.get("actual_blocker_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": prior.get("actual_question_need_observation_rows_materialized_here") is True and ready,
        "actual_disposal_receipt_materialized_here": prior.get("actual_disposal_receipt_materialized_here") is True and ready,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        **_current_ref_fields(),
        "implemented_steps": list(P7_R54_CLR22_IMPLEMENTED_STEPS if ready else tuple(prior.get("implemented_steps") or clr21.P7_R54_CLR21_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_CLR22_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(prior.get("not_yet_implemented_steps") or clr21.P7_R54_CLR21_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_CLR22_NEXT_WORK_AFTER_CLR22_REF if ready else P7_R54_CLR22_NEXT_WORK_AFTER_CLR21_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": clr15._no_touch_contract(),  # type: ignore[attr-defined]
        "body_free_markers": clr15._body_free_markers(),  # type: ignore[attr-defined]
        "body_free": True,
        "raw_body_included": False,
        "local_path_included": False,
        **_false_flags_except(
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p8_question_design_material_candidate",
        ),
    }
    material["actual_rating_rows_materialized_here"] = prior.get("actual_rating_rows_materialized_here") is True and ready
    material["actual_blocker_rows_materialized_here"] = prior.get("actual_blocker_rows_materialized_here") is True and ready
    material["actual_question_need_observation_rows_materialized_here"] = prior.get("actual_question_need_observation_rows_materialized_here") is True and ready
    material["actual_disposal_receipt_materialized_here"] = prior.get("actual_disposal_receipt_materialized_here") is True and ready
    material["disposal_verified"] = prior.get("disposal_verified") is True and ready
    material["p5_human_blind_qa_confirmed_candidate"] = prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready
    material["p6_limited_human_readfeel_candidate"] = prior.get("p6_limited_human_readfeel_candidate") is True and ready
    material["p8_question_design_material_candidate"] = p8_candidate
    material["question_text_included"] = False
    material["draft_question_text_included"] = False
    material["returned_emlis_body_included"] = False
    material["history_surface_included"] = False
    material["reviewer_free_text_included"] = False
    material["reviewer_note_included"] = False
    material["reviewer_notes_included"] = False
    material["reviewer_notes_body_included"] = False
    material["local_absolute_path_included"] = False
    material["body_hash_included"] = False
    material["packet_content_included"] = False
    material["terminal_output_body_included"] = False
    assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(material)
    return material


def assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR22_FINAL_VALIDATION_REQUIRED_FIELD_REFS, source="P7-R54-CLR22")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR22_FINAL_VALIDATION_SCHEMA_VERSION,
        policy_section=P7_R54_CLR22_STEP_REF,
        source="P7-R54-CLR22",
        allowed_true_false_flags=P7_R54_CLR22_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("existing_op22_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR22 existing OP22 refs changed")
    if safe_mapping(material.get("existing_ev20_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR22 existing EV20 refs changed")
    for key in (
        "existing_op22_current_refs_are_historical_here",
        "existing_op22_structural_contract_reused",
        "existing_ev20_current_refs_are_historical_here",
        "existing_ev20_structural_contract_reused",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "validation_evidence_bodyfree_only",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR22 must keep {key}=True")
    for key in (
        "existing_op22_reused_as_actual_final_validation_basis",
        "existing_ev20_reused_as_actual_final_validation_basis",
        "actual_review_evidence_complete",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "release_allowed",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR22 must keep {key}=False")
    if material.get("final_validation_status") not in P7_R54_CLR22_ALLOWED_FINAL_VALIDATION_STATUS_REFS:
        raise ValueError("P7-R54-CLR22 final validation status outside allowed refs")
    ready = material.get("final_validation_status") == P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF
    if material.get("final_validation_passed") is not ready or material.get("r52_reintake_handoff_allowed_next") is not ready:
        raise ValueError("P7-R54-CLR22 readiness flags must match status")
    if material.get("body_leak_or_question_text_violation_detected") is not bool(material.get("body_leak_violation_refs") or material.get("question_text_violation_refs")):
        raise ValueError("P7-R54-CLR22 body/question violation flag mismatch")
    if material.get("no_touch_violation_detected") is not bool(material.get("no_touch_violation_refs")):
        raise ValueError("P7-R54-CLR22 no-touch violation flag mismatch")
    for count_key, refs_key in (
        ("body_leak_violation_count", "body_leak_violation_refs"),
        ("question_text_violation_count", "question_text_violation_refs"),
        ("no_touch_violation_count", "no_touch_violation_refs"),
        ("final_validation_issue_count", "final_validation_issue_refs"),
    ):
        if material.get(count_key) != len(material.get(refs_key) or []):
            raise ValueError(f"P7-R54-CLR22 {count_key} mismatch")
    if ready:
        if material.get("final_validation_ref") != P7_R54_CLR22_FINAL_VALIDATION_REF:
            raise ValueError("P7-R54-CLR22 ready validation ref changed")
        if material.get("final_validation_reason_refs") != [P7_R54_CLR22_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR22 ready reason refs changed")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count", "question_need_observation_rows_aggregated_count"):
            if material.get(count_key) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-CLR22 ready must preserve 24 {count_key}")
        if material.get("disposal_verified") is not True or material.get("p5_human_blind_qa_confirmed_candidate") is not True or material.get("p6_limited_human_readfeel_candidate") is not True:
            raise ValueError("P7-R54-CLR22 ready must preserve body-free candidate evidence")
        if material.get("open_execution_blocker_ids") or material.get("final_validation_issue_refs"):
            raise ValueError("P7-R54-CLR22 ready must not carry blockers or issues")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR22_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR22 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR22_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR22 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR23_STEP_REF:
            raise ValueError("P7-R54-CLR22 ready must point to CLR23")
    else:
        if not material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR22 blocked must carry blockers")
        if material.get("next_required_step") not in {
            P7_R54_CLR22_BLOCKED_NEXT_REQUIRED_STEP_REF,
            P7_R54_CLR22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF,
            P7_R54_CLR22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF,
        }:
            raise ValueError("P7-R54-CLR22 blocked next step changed")
    return True


def _clr23_status_next_reason(final_validation: Mapping[str, Any]) -> tuple[str, str, list[str]]:
    if (
        final_validation.get("final_validation_status") == P7_R54_CLR22_BODY_LEAK_OR_QUESTION_TEXT_BLOCKED_STATUS_REF
        or final_validation.get("body_leak_or_question_text_violation_detected") is True
    ):
        return (
            P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF,
            P7_R54_CLR23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR23_BODY_LEAK_BLOCKED_REASON_REF],
        )
    if (
        final_validation.get("final_validation_status") == P7_R54_CLR22_NO_TOUCH_BLOCKED_STATUS_REF
        or final_validation.get("no_touch_violation_detected") is True
    ):
        return (
            P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF,
            P7_R54_CLR23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR23_NO_TOUCH_BLOCKED_REASON_REF],
        )
    if (
        final_validation.get("final_validation_status") != P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF
        or final_validation.get("r52_reintake_handoff_allowed_next") is not True
        or final_validation.get("next_required_step") != P7_R54_CLR23_STEP_REF
    ):
        return (
            P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF,
            P7_R54_CLR23_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR23_EVIDENCE_MISSING_REASON_REF],
        )
    if final_validation.get("disposal_verified") is not True:
        return (
            P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF,
            P7_R54_CLR23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR23_DISPOSAL_BLOCKED_REASON_REF],
        )
    for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
        if int(final_validation.get(count_key) or 0) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            return (
                P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF,
                P7_R54_CLR23_BLOCKED_NEXT_REQUIRED_STEP_REF,
                [P7_R54_CLR23_EVIDENCE_MISSING_REASON_REF],
            )
    for evidence_key in (
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
    ):
        if final_validation.get(evidence_key) is not True:
            return (
                P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF,
                P7_R54_CLR23_BLOCKED_NEXT_REQUIRED_STEP_REF,
                [P7_R54_CLR23_EVIDENCE_MISSING_REASON_REF],
            )
    if final_validation.get("p5_decision_candidate_ref") != clr19.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF:
        return (
            P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF,
            P7_R54_CLR23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF,
            [P7_R54_CLR23_INCONCLUSIVE_REASON_REF],
        )
    return (P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF, P7_R54_CLR24_STEP_REF, [P7_R54_CLR23_READY_REASON_REF])


def build_p7_r54_clr23_r52_reintake_handoff(
    *,
    final_validation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_clr23_r52_reintake_handoff",
) -> dict[str, Any]:
    """Build CLR23 body-free R52 re-intake handoff without starting P5/P6/P8/release."""
    prior = safe_mapping(final_validation) if final_validation is not None else build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation()
    assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract(prior)
    status, next_step, reason_refs = _clr23_status_next_reason(prior)
    ready = status == P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    blockers = [] if ready else dedupe_identifiers([*reason_refs, *(prior.get("open_execution_blocker_ids") or [])], limit=120, max_length=180)
    p5_candidate_ref = clean_identifier(prior.get("p5_decision_candidate_ref"), default=clr19.P7_R54_CLR19_INCONCLUSIVE_REF, max_length=180)
    p6_candidate_ref = clean_identifier(prior.get("p6_limited_human_readfeel_candidate_ref"), default=clr21.P7_R54_CLR20_P6_CANDIDATE_REF, max_length=220)
    p8_material_ref = clean_identifier(prior.get("p8_material_candidate_only_ref"), default=clr21.P7_R54_CLR21_P8_MATERIAL_HANDOFF_REF, max_length=220)
    p8_question_candidate_ref = clean_identifier(prior.get("p8_question_design_material_candidate_ref"), default="", max_length=220)
    handoff_refs = (
        "clr12_rating_rows_bodyfree",
        "clr13_blocker_rows_bodyfree",
        "clr14_question_observation_rows_bodyfree",
        "clr17_disposal_receipt_bodyfree",
        "clr18_post_review_summary_bodyfree",
        "clr19_p5_decision_candidate_bodyfree",
        "clr20_p6_candidate_only_handoff_bodyfree",
        "clr21_p8_material_candidate_only_handoff_bodyfree",
        "clr22_final_validation_bodyfree",
    )
    material = {
        "schema_version": P7_R54_CLR23_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR23_STEP_REF,
        "operation_step_ref": P7_R54_CLR23_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_clr23_r52_reintake_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(prior.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr22_schema_version": P7_R54_CLR22_FINAL_VALIDATION_SCHEMA_VERSION,
        "clr22_material_ref": clean_identifier(prior.get("material_id"), default="p7_r54_clr22_final_validation", max_length=220),
        "clr22_next_required_step": clean_identifier(prior.get("next_required_step"), default="", max_length=220),
        "clr22_final_validation_status": clean_identifier(prior.get("final_validation_status"), default=P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF, max_length=180),
        "clr22_r52_reintake_handoff_allowed_next": prior.get("r52_reintake_handoff_allowed_next") is True,
        **_current_ref_fields(),
        "actual_review_basis_refs": dict(clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_op23_helper_ref": "build_p7_r54_op23_r52_reintake_handoff",
        "existing_op23_schema_version": r54op.P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "existing_op23_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op23_current_refs_are_historical_here": True,
        "existing_op23_reused_as_actual_r52_handoff_basis": False,
        "existing_op23_structural_contract_reused": True,
        "existing_ev21_helper_ref": "build_p7_r54_ev21_r52_reintake_handoff",
        "existing_ev21_schema_version": r54ev.P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "existing_ev21_current_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_ev21_current_refs_are_historical_here": True,
        "existing_ev21_reused_as_actual_r52_handoff_basis": False,
        "existing_ev21_structural_contract_reused": True,
        "required_case_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(prior.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(prior.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(prior.get("question_observation_row_count") or 0) if ready else 0,
        "handoff_status": status,
        "handoff_ref": P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF if ready else "r52_reintake_handoff_not_ready_bodyfree_20260627",
        "handoff_reason_refs": reason_refs if ready else blockers,
        "r52_reintake_decision_ref": P7_R54_CLR23_R52_REINTAKE_DECISION_REF if ready else "R52_REINTAKE_HELD",
        "r52_reintake_handoff_ready": ready,
        "r52_reintake_handoff_status": status,
        "r52_reintake_handoff_ref": P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF if ready else "r52_reintake_handoff_not_ready_bodyfree_20260627",
        "r52_reintake_handoff_reason_refs": reason_refs if ready else blockers,
        "r52_reintake_required_ref": P7_R54_CLR23_R52_REINTAKE_REQUIRED_REF if ready else "R52_REINTAKE_HELD",
        "actual_review_evidence_complete": ready,
        "actual_review_evidence_complete_from_bodyfree_receipts": ready,
        "r52_bodyfree_actual_review_evidence_complete": ready,
        "r52_bodyfree_evidence_handoff_ready": ready,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "rating_rows_bodyfree_handoff_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if ready else 0,
        "question_observation_rows_bodyfree_handoff_count": clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if ready else 0,
        "disposal_verified": prior.get("disposal_verified") is True and ready,
        "no_body_leak_validation_passed": prior.get("no_body_leak_validation_passed") is True and ready,
        "no_question_text_validation_passed": prior.get("no_question_text_validation_passed") is True and ready,
        "no_touch_validation_passed": prior.get("no_touch_validation_passed") is True and ready,
        "final_validation_status": clean_identifier(prior.get("final_validation_status"), default=P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF, max_length=180),
        "p5_decision_candidate": p5_candidate_ref if ready else clr19.P7_R54_CLR19_INCONCLUSIVE_REF,
        "p5_decision_candidate_ref": p5_candidate_ref if ready else clr19.P7_R54_CLR19_INCONCLUSIVE_REF,
        "p5_human_blind_qa_confirmed_candidate": prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_candidate_only": prior.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_candidate_only_ref": p6_candidate_ref if ready else "",
        "p6_limited_human_readfeel_candidate_ref": p6_candidate_ref if prior.get("p6_limited_human_readfeel_candidate") is True and ready else "",
        "p6_limited_human_readfeel_candidate": prior.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_material_candidate_only": ready,
        "p8_material_candidate_only_ref": p8_material_ref if ready else "",
        "p8_question_design_material_candidate_ref": p8_question_candidate_ref if prior.get("p8_question_design_material_candidate") is True and ready else "",
        "p8_question_design_material_candidate": prior.get("p8_question_design_material_candidate") is True and ready,
        "p8_material_candidate_row_count": int(prior.get("p8_material_candidate_row_count") or 0) if ready else 0,
        "p8_design_material_candidate_only_not_start": True,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_trigger_logic_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_plan_guard_implemented": False,
        "question_storage_schema_implemented": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "api_db_rn_response_key_changed_here": False,
        "runtime_changed_here": False,
        "release_allowed": False,
        "p7_complete": False,
        "body_free_evidence_handoff_materialized_here": ready,
        "r52_reintake_required": ready,
        "body_free_actual_review_evidence_ref": P7_R54_CLR23_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF if ready else "bodyfree_actual_review_evidence_not_ready_20260627",
        "body_free_result_handoff_ref": P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF if ready else "bodyfree_result_handoff_not_ready_20260627",
        "handoff_evidence_refs": list(handoff_refs) if ready else [],
        "handoff_evidence_ref_count": len(handoff_refs) if ready else 0,
        "r52_handoff_preserves_candidate_only_boundaries": True,
        "r52_handoff_contains_body_full_packet": False,
        "r52_handoff_contains_question_text": False,
        "r52_handoff_contains_local_path": False,
        "r52_handoff_contains_payload_hash": False,
        "r52_handoff_contains_reviewer_free_text": False,
        "r52_handoff_contains_raw_payload": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_rating_rows_materialized_here": prior.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_blocker_rows_materialized_here": prior.get("actual_blocker_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": prior.get("actual_question_need_observation_rows_materialized_here") is True and ready,
        "actual_disposal_receipt_materialized_here": prior.get("actual_disposal_receipt_materialized_here") is True and ready,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R54_CLR23_IMPLEMENTED_STEPS if ready else tuple(prior.get("implemented_steps") or P7_R54_CLR22_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_CLR23_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(prior.get("not_yet_implemented_steps") or P7_R54_CLR22_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_CLR23_NEXT_WORK_AFTER_CLR23_REF if ready else P7_R54_CLR23_NEXT_WORK_AFTER_CLR22_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": clr15._no_touch_contract(),  # type: ignore[attr-defined]
        "body_free_markers": clr15._body_free_markers(),  # type: ignore[attr-defined]
        "body_free": True,
        "raw_body_included": False,
        "local_path_included": False,
        **_false_flags_except(
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "actual_review_evidence_complete",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p8_question_design_material_candidate",
        ),
    }
    material["actual_review_evidence_complete"] = ready
    material["actual_rating_rows_materialized_here"] = prior.get("actual_rating_rows_materialized_here") is True and ready
    material["actual_blocker_rows_materialized_here"] = prior.get("actual_blocker_rows_materialized_here") is True and ready
    material["actual_question_need_observation_rows_materialized_here"] = prior.get("actual_question_need_observation_rows_materialized_here") is True and ready
    material["actual_disposal_receipt_materialized_here"] = prior.get("actual_disposal_receipt_materialized_here") is True and ready
    material["disposal_verified"] = prior.get("disposal_verified") is True and ready
    material["p5_human_blind_qa_confirmed_candidate"] = prior.get("p5_human_blind_qa_confirmed_candidate") is True and ready
    material["p6_limited_human_readfeel_candidate"] = prior.get("p6_limited_human_readfeel_candidate") is True and ready
    material["p8_question_design_material_candidate"] = prior.get("p8_question_design_material_candidate") is True and ready
    material["returned_emlis_body_included"] = False
    material["history_surface_included"] = False
    material["reviewer_free_text_included"] = False
    material["reviewer_note_included"] = False
    material["reviewer_notes_included"] = False
    material["reviewer_notes_body_included"] = False
    material["local_absolute_path_included"] = False
    material["body_hash_included"] = False
    material["packet_content_included"] = False
    material["terminal_output_body_included"] = False
    assert_p7_r54_clr23_r52_reintake_handoff_contract(material)
    return material


def assert_p7_r54_clr23_r52_reintake_handoff_contract(data: Mapping[str, Any]) -> bool:
    material = safe_mapping(data)
    _assert_required_fields(material, required=P7_R54_CLR23_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS, source="P7-R54-CLR23")
    _assert_common_base(
        material,
        schema_version=P7_R54_CLR23_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_CLR23_STEP_REF,
        source="P7-R54-CLR23",
        allowed_true_false_flags=P7_R54_CLR23_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if safe_mapping(material.get("actual_review_basis_refs")) != clr03.P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR23 actual review basis refs changed")
    if safe_mapping(material.get("existing_op23_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("P7-R54-CLR23 existing OP23 refs changed")
    if safe_mapping(material.get("existing_ev21_current_refs")) != r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR23 existing EV21 refs changed")
    for key in (
        "existing_op23_current_refs_are_historical_here",
        "existing_op23_structural_contract_reused",
        "existing_ev21_current_refs_are_historical_here",
        "existing_ev21_structural_contract_reused",
        "p8_design_material_candidate_only_not_start",
        "r52_handoff_preserves_candidate_only_boundaries",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if material.get(key) is not True:
            raise ValueError(f"P7-R54-CLR23 must keep {key}=True")
    for key in (
        "existing_op23_reused_as_actual_r52_handoff_basis",
        "existing_ev21_reused_as_actual_r52_handoff_basis",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "p7_complete",
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "question_trigger_logic_implemented",
        "question_answer_persistence_implemented",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_plan_guard_implemented",
        "question_storage_schema_implemented",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "question_text_included",
        "draft_question_text_included",
        "r52_handoff_contains_body_full_packet",
        "r52_handoff_contains_question_text",
        "r52_handoff_contains_local_path",
        "r52_handoff_contains_payload_hash",
        "r52_handoff_contains_reviewer_free_text",
        "r52_handoff_contains_raw_payload",
    ):
        if material.get(key) is not False:
            raise ValueError(f"P7-R54-CLR23 must keep {key}=False")
    if material.get("handoff_status") != material.get("r52_reintake_handoff_status"):
        raise ValueError("P7-R54-CLR23 status aliases changed")
    if material.get("handoff_status") not in P7_R54_CLR23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS:
        raise ValueError("P7-R54-CLR23 handoff status outside allowed refs")
    ready = material.get("handoff_status") == P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    for ready_key in (
        "actual_review_evidence_complete",
        "actual_review_evidence_complete_from_bodyfree_receipts",
        "r52_bodyfree_actual_review_evidence_complete",
        "r52_bodyfree_evidence_handoff_ready",
        "r52_reintake_handoff_ready",
        "body_free_evidence_handoff_materialized_here",
        "r52_reintake_required",
    ):
        if material.get(ready_key) is not ready:
            raise ValueError(f"P7-R54-CLR23 {ready_key} must match handoff readiness")
    if ready:
        if material.get("handoff_ref") != P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF:
            raise ValueError("P7-R54-CLR23 ready handoff ref changed")
        if material.get("r52_reintake_handoff_ref") != P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF:
            raise ValueError("P7-R54-CLR23 ready R52 handoff ref changed")
        if material.get("handoff_reason_refs") != [P7_R54_CLR23_READY_REASON_REF]:
            raise ValueError("P7-R54-CLR23 ready reason refs changed")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count", "rating_rows_bodyfree_handoff_count", "question_observation_rows_bodyfree_handoff_count"):
            if material.get(count_key) != clr03.P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-CLR23 ready must preserve 24 {count_key}")
        if material.get("p5_decision_candidate_ref") != clr19.P7_R54_CLR19_P5_CONFIRMED_CANDIDATE_REF:
            raise ValueError("P7-R54-CLR23 ready must preserve P5 confirmed candidate ref")
        if material.get("p5_human_blind_qa_confirmed_candidate") is not True or material.get("p6_candidate_only") is not True:
            raise ValueError("P7-R54-CLR23 ready must preserve P5/P6 candidate-only evidence")
        if material.get("open_execution_blocker_ids") or material.get("handoff_evidence_ref_count") != len(material.get("handoff_evidence_refs") or []):
            raise ValueError("P7-R54-CLR23 ready evidence refs or blockers changed")
        if tuple(material.get("implemented_steps") or ()) != P7_R54_CLR23_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR23 implemented steps changed")
        if tuple(material.get("not_yet_implemented_steps") or ()) != P7_R54_CLR23_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-CLR23 not-yet steps changed")
        if material.get("next_required_step") != P7_R54_CLR24_STEP_REF:
            raise ValueError("P7-R54-CLR23 ready must point to CLR24")
    else:
        if material.get("body_free_evidence_handoff_materialized_here") is not False or material.get("r52_reintake_required") is not False:
            raise ValueError("P7-R54-CLR23 blocked must not materialize evidence")
        if not material.get("open_execution_blocker_ids"):
            raise ValueError("P7-R54-CLR23 blocked must carry blockers")
        if material.get("next_required_step") not in {
            P7_R54_CLR23_BLOCKED_NEXT_REQUIRED_STEP_REF,
            P7_R54_CLR23_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF,
            P7_R54_CLR23_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF,
            P7_R54_CLR23_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF,
            P7_R54_CLR23_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF,
        }:
            raise ValueError("P7-R54-CLR23 blocked next step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr22_final_validation = build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_current_snapshot_local_run_clr22_final_validation_contract = assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_current_snapshot_final_no_body_leak_no_question_text_no_touch_validation_bodyfree = build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_current_snapshot_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract = assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_current_snapshot_local_run_clr23_r52_reintake_handoff = build_p7_r54_clr23_r52_reintake_handoff
assert_p7_r54_current_snapshot_local_run_clr23_r52_reintake_handoff_contract = assert_p7_r54_clr23_r52_reintake_handoff_contract
build_p7_r54_current_snapshot_r52_reintake_handoff_bodyfree = build_p7_r54_clr23_r52_reintake_handoff
assert_p7_r54_current_snapshot_r52_reintake_handoff_bodyfree_contract = assert_p7_r54_clr23_r52_reintake_handoff_contract

build_clr22_final_validation = build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation
assert_clr22_final_validation_contract = assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract
build_clr23_r52_reintake_handoff = build_p7_r54_clr23_r52_reintake_handoff
assert_clr23_r52_reintake_handoff_contract = assert_p7_r54_clr23_r52_reintake_handoff_contract

__all__ = (
    "P7_R54_CLR22_FINAL_VALIDATION_SCHEMA_VERSION",
    "P7_R54_CLR23_R52_REINTAKE_HANDOFF_SCHEMA_VERSION",
    "P7_R54_CLR22_SCHEMA_VERSION",
    "P7_R54_CLR23_SCHEMA_VERSION",
    "P7_R54_CLR22_STEP_REF",
    "P7_R54_CLR23_STEP_REF",
    "P7_R54_CLR24_STEP_REF",
    "P7_R54_CLR22_FINAL_VALIDATION_READY_STATUS_REF",
    "P7_R54_CLR22_FINAL_VALIDATION_BLOCKED_STATUS_REF",
    "P7_R54_CLR22_BODY_LEAK_OR_QUESTION_TEXT_BLOCKED_STATUS_REF",
    "P7_R54_CLR22_NO_TOUCH_BLOCKED_STATUS_REF",
    "P7_R54_CLR22_ALLOWED_FINAL_VALIDATION_STATUS_REFS",
    "P7_R54_CLR22_FINAL_VALIDATION_REF",
    "P7_R54_CLR22_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR22_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR22_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_CLR23_R52_REINTAKE_HANDOFF_READY_STATUS_REF",
    "P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF",
    "P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF",
    "P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF",
    "P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF",
    "P7_R54_CLR23_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF",
    "P7_R54_CLR23_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS",
    "P7_R54_CLR23_R52_REINTAKE_HANDOFF_REF",
    "P7_R54_CLR23_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF",
    "P7_R54_CLR23_R52_REINTAKE_REQUIRED_REF",
    "P7_R54_CLR22_IMPLEMENTED_STEPS",
    "P7_R54_CLR22_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR23_IMPLEMENTED_STEPS",
    "P7_R54_CLR23_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_CLR22_FINAL_VALIDATION_REQUIRED_FIELD_REFS",
    "P7_R54_CLR23_R52_REINTAKE_HANDOFF_REQUIRED_FIELD_REFS",
    "build_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation",
    "assert_p7_r54_clr22_final_no_body_leak_no_question_text_no_touch_validation_contract",
    "build_p7_r54_clr23_r52_reintake_handoff",
    "assert_p7_r54_clr23_r52_reintake_handoff_contract",
    "build_p7_r54_current_snapshot_local_run_clr22_final_validation",
    "assert_p7_r54_current_snapshot_local_run_clr22_final_validation_contract",
    "build_p7_r54_current_snapshot_final_no_body_leak_no_question_text_no_touch_validation_bodyfree",
    "assert_p7_r54_current_snapshot_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract",
    "build_p7_r54_current_snapshot_local_run_clr23_r52_reintake_handoff",
    "assert_p7_r54_current_snapshot_local_run_clr23_r52_reintake_handoff_contract",
    "build_p7_r54_current_snapshot_r52_reintake_handoff_bodyfree",
    "assert_p7_r54_current_snapshot_r52_reintake_handoff_bodyfree_contract",
    "build_clr22_final_validation",
    "assert_clr22_final_validation_contract",
    "build_clr23_r52_reintake_handoff",
    "assert_clr23_r52_reintake_handoff_contract",
)
