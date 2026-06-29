# -*- coding: utf-8 -*-
"""P7-R55 R54 evidence reconcile / R52 re-intake decision helpers.

R55-0 refreezes the *current received* local snapshot for this work session.
R55-1 reconciles the prior R52/R53/R54 helper source refs against that current
snapshot so older helper refs remain historical regression context only.
R55-2 reconciles validation evidence claim levels without treating split green,
collect-only, one-shot timeout, or RN contract checks as product readiness.
R55-3 intakes the R54 default R52 re-intake handoff as a body-free blocked
actual-review-evidence-missing state.
R55-4 scans R55 intake/intermediate materials for forbidden body or question
payloads without storing the scanned bodies.
R55-5 assesses the current actual-review-evidence gap as missing without
promoting P5/P6/P8/release readiness.
R55-6 materializes the R55-owned R52 re-intake decision while keeping the R52
existing decision equivalent separate.
R55-7 separates P5 candidate/final, P6 start, P8 material/start, P7 completion,
and release readiness so none are promoted by the R55 evidence material.
R55-8 validates the final no-touch boundary for API/DB/RN/runtime/public response
keys and P8 question implementation surfaces.
R55-9 materializes the validation command matrix / documentation output as
body-free command refs and green-claim rules, without terminal output or local
paths.
R55-10 summarizes the R55 result as body-free decision material for the next
work decision, while keeping P6/P8/P7/release held.

This module intentionally implements only R55-0 through R55-10.  It does not run
an actual human review, generate body-full packets, create rating/question rows,
write schema files, change API/DB/RN/public response contracts, start P6/P8,
complete P7, or claim release readiness.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate import (
    P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R52_POLICY_KIND,
    P7_R52_SCOPE,
    P7_R52_STEP,
)
from emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization import (
    P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R53_POLICY_KIND,
    P7_R53_SCOPE,
    P7_R53_STEP,
)
from emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff import (
    P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R54_POLICY_KIND,
    P7_R54_R22_STEP_REF,
    P7_R54_R23_STEP_REF,
    P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
    P7_R54_R52_REINTAKE_HANDOFF_STATUS_REFS,
    P7_R54_SCOPE,
    P7_R54_STEP,
    P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
    P7_R54_VALIDATION_DOCUMENTATION_STATUS_REFS,
    assert_p7_r54_r52_reintake_handoff_bodyfree_contract,
    assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract,
    build_p7_r54_r52_reintake_handoff_bodyfree,
    build_p7_r54_validation_command_matrix_documentation_output_bodyfree,
)


P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.current_received_snapshot_refreeze.bodyfree.v1"
)
P7_R55_PRIOR_HELPER_SOURCE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.prior_helper_source_row.bodyfree.v1"
)
P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.prior_helper_source_reconcile.bodyfree.v1"
)
P7_R55_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.validation_evidence_row.bodyfree.v1"
)
P7_R55_VALIDATION_EVIDENCE_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.validation_evidence_reconcile.bodyfree.v1"
)
P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.r54_handoff_intake.bodyfree.v1"
)
P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.bodyfree_forbidden_payload_scan.bodyfree.v1"
)
P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.actual_review_evidence_gap_assessment.bodyfree.v1"
)

P7_R55_STEP: Final = "R55_R54EvidenceReconcile_R52ReintakeDecisionMaterialization_20260623"
P7_R55_SCOPE: Final = "r54_evidence_reconcile_current_snapshot_refreeze_r52_reintake_decision"
P7_R55_POLICY_KIND: Final = "bodyfree_evidence_reconcile_decision_materialization"
P7_R55_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r55_r54_evidence_reconcile_r52_reintake_session"
P7_R55_FIRST_NEXT_WORK_REF: Final = "r54_evidence_reconcile_without_p6_p8_or_release_promotion"

P7_R55_R0_NEXT_REQUIRED_STEP_REF: Final = "R55-1_prior_helper_source_reconcile"
P7_R55_R1_NEXT_REQUIRED_STEP_REF: Final = "R55-2_validation_evidence_reconcile"
P7_R55_R2_NEXT_REQUIRED_STEP_REF: Final = "R55-3_r54_default_handoff_intake"
P7_R55_R3_NEXT_REQUIRED_STEP_REF: Final = "R55-4_bodyfree_forbidden_payload_scan"
P7_R55_R4_NEXT_REQUIRED_STEP_REF: Final = "R55-5_actual_review_evidence_gap_assessment"
P7_R55_R5_NEXT_REQUIRED_STEP_REF: Final = "R55-6_r52_reintake_decision_materialization"

P7_R55_R2_STEP_REF: Final = "R55-2_validation_evidence_reconcile"
P7_R55_R3_STEP_REF: Final = "R55-3_r54_default_handoff_intake"
P7_R55_R4_STEP_REF: Final = "R55-4_bodyfree_forbidden_payload_scan"
P7_R55_R5_STEP_REF: Final = "R55-5_actual_review_evidence_gap_assessment"
P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF: Final = (
    "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
)
P7_R55_R54_DEFAULT_VALIDATION_DOCUMENTATION_STATUS_REF: Final = (
    "VALIDATION_DOCUMENTATION_BLOCKED_BY_R54_22_R52_REINTAKE_HANDOFF"
)
P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF: Final = "not_started"
P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF: Final = "P5_NOT_REVIEWED"
P7_R55_FORBIDDEN_PAYLOAD_SCAN_CLEAR_REF: Final = "R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_CLEAR"
P7_R55_BODYFREE_BOUNDARY_RISK_CLEAR_REF: Final = "NO_BODYFREE_BOUNDARY_RISK_DETECTED"
P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF: Final = "ACTUAL_REVIEW_EVIDENCE_MISSING"
P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF: Final = "R55_P5_NOT_REVIEWED_EVIDENCE_MISSING"
P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT: Final = 24
P7_R55_DEFAULT_MISSING_EVIDENCE_REFS: Final[tuple[str, ...]] = (
    "p5_actual_human_blind_qa_review_result_rows_missing",
    "reviewer_rating_actual_rows_missing",
    "question_need_observation_actual_rows_missing",
    "actual_disposal_receipt_missing",
    "r54_default_handoff_blocked_by_actual_review_evidence_missing",
)

P7_R55_ACTUAL_REVIEW_BASIS_REF: Final = "R55_CURRENT_RECEIVED_SNAPSHOT_20260623"
P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_received_snapshot_only"
P7_R55_PRIOR_HELPER_CLASSIFICATION_REF: Final = "historical_regression_context"
P7_R55_PRIOR_HELPER_COMPARISON_STATUS_REF: Final = "OLDER_THAN_R55_CURRENT_RECEIVED_SNAPSHOT"

P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(248).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(77).zip",
    "rn_zip_ref": "Cocolon(250).zip",
    "backend_zip_ref": "mashos-api(163).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(9).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R55Candidate_R54EvidenceReconcile_R52ReintakeDecision_PreDesignMemo_20260623.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R55_R54EvidenceReconcile_R52ReintakeDecisionMaterialization_DetailedDesign_ImplementationOrder_20260623.md",
}

P7_R55_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R55-0_scope_current_received_snapshot_refreeze",
)
P7_R55_FUTURE_STEPS_AFTER_R1: Final[tuple[str, ...]] = (
    "R55-2_validation_evidence_reconcile",
    "R55-3_r54_default_handoff_intake",
    "R55-4_bodyfree_forbidden_payload_scan",
    "R55-5_actual_review_evidence_gap_assessment",
    "R55-6_r52_reintake_decision_materialization",
    "R55-7_p5_p6_p8_release_separation",
    "R55-8_final_no_touch_boundary_validation",
    "R55-9_validation_command_matrix_documentation_output",
    "R55-10_final_summary",
)
P7_R55_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R55-1_prior_helper_source_reconcile",
    *P7_R55_FUTURE_STEPS_AFTER_R1,
)
P7_R55_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R0_IMPLEMENTED_STEPS,
    "R55-1_prior_helper_source_reconcile",
)
P7_R55_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R55_FUTURE_STEPS_AFTER_R1
P7_R55_FUTURE_STEPS_AFTER_R3: Final[tuple[str, ...]] = (
    "R55-4_bodyfree_forbidden_payload_scan",
    "R55-5_actual_review_evidence_gap_assessment",
    "R55-6_r52_reintake_decision_materialization",
    "R55-7_p5_p6_p8_release_separation",
    "R55-8_final_no_touch_boundary_validation",
    "R55-9_validation_command_matrix_documentation_output",
    "R55-10_final_summary",
)
P7_R55_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_IMPLEMENTED_STEPS,
    P7_R55_R2_STEP_REF,
)
P7_R55_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R55_R3_STEP_REF,
    *P7_R55_FUTURE_STEPS_AFTER_R3,
)
P7_R55_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R2_IMPLEMENTED_STEPS,
    P7_R55_R3_STEP_REF,
)
P7_R55_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R55_FUTURE_STEPS_AFTER_R3
P7_R55_FUTURE_STEPS_AFTER_R5: Final[tuple[str, ...]] = (
    "R55-6_r52_reintake_decision_materialization",
    "R55-7_p5_p6_p8_release_separation",
    "R55-8_final_no_touch_boundary_validation",
    "R55-9_validation_command_matrix_documentation_output",
    "R55-10_final_summary",
)
P7_R55_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R3_IMPLEMENTED_STEPS,
    P7_R55_R4_STEP_REF,
)
P7_R55_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R55_R5_STEP_REF,
    *P7_R55_FUTURE_STEPS_AFTER_R5,
)
P7_R55_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R4_IMPLEMENTED_STEPS,
    P7_R55_R5_STEP_REF,
)
P7_R55_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R55_FUTURE_STEPS_AFTER_R5

P7_R55_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_implementation_started_here",
)
P7_R55_REVIEW_RELEASE_CLOSED_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "actual_review_evidence_complete",
    "actual_review_evidence_claimed",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
)
P7_R55_SCHEMA_MUTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
    "public_response_key_changed_here",
    "gate_threshold_changed_here",
    "user_label_connection_runtime_changed_here",
    "emlis_runtime_changed_here",
)
P7_R55_BODY_FREE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "history_body_included",
    "reviewer_free_text_included",
    "reviewer_notes_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "packet_content_hash_included",
    "terminal_output_included",
    "command_full_output_included",
    "body_full_packet_zip_inclusion_allowed",
)
P7_R55_FORBIDDEN_SCAN_DETECTION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "forbidden_payload_detected",
    "body_full_payload_detected",
    "raw_input_detected",
    "returned_surface_detected",
    "comment_text_detected",
    "history_body_detected",
    "reviewer_free_text_detected",
    "question_text_detected",
    "draft_question_text_detected",
    "local_absolute_path_detected",
    "body_content_hash_detected",
    "packet_content_hash_detected",
    "terminal_output_detected",
)
P7_R55_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R55_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
    *P7_R55_REVIEW_RELEASE_CLOSED_KEY_REFS,
    *P7_R55_SCHEMA_MUTATION_FALSE_KEY_REFS,
    *P7_R55_BODY_FREE_FALSE_KEY_REFS,
)

P7_R55_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "raw_answer",
        "comment_text",
        "comment_text_body",
        "returned_emlis_surface",
        "current_input_review_surface",
        "bounded_owned_history_review_surface",
        "history_body",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "question_text",
        "draft_question_text",
        "question_body",
        "answer_text",
        "local_absolute_path",
        "body_content_hash",
        "packet_content_hash",
        "terminal_output",
        "command_full_output",
        "stdout",
        "stderr",
        "traceback",
    }
)

P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "current_snapshot_refrozen_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "prior_helper_refs_used_as_actual_review_basis",
    "current_received_snapshot_used_as_actual_review_basis",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

P7_R55_PRIOR_HELPER_SOURCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "helper_ref",
    "helper_step_ref",
    "helper_scope_ref",
    "helper_policy_kind_ref",
    "helper_snapshot_ref_group",
    "helper_snapshot_refs",
    "helper_snapshot_ref_count",
    "current_snapshot_ref_group",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "comparison_to_current_ref",
    "comparison_status_ref",
    "refs_match_current_received_snapshot",
    "classification_ref",
    "used_as_actual_review_basis",
    "used_as_regression_context_only",
    "current_snapshot_used_as_actual_review_basis",
    "source_delta_reason_refs",
    "body_free",
)

P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r0_refreeze_schema_version",
    "r0_refreeze_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "prior_helper_ref_keys",
    "prior_helper_source_rows",
    "prior_helper_source_row_count",
    "all_prior_helper_refs_classified",
    "prior_helper_refs_used_as_actual_review_basis",
    "prior_helper_refs_used_as_regression_context_only",
    "current_received_snapshot_used_as_actual_review_basis",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)


P7_R55_VALIDATION_CLAIM_LEVEL_REFS: Final[tuple[str, ...]] = (
    "PASSED_TARGET",
    "PASSED_SPLIT_TARGET",
    "COLLECT_ONLY",
    "TIMEOUT_ONE_SHOT",
    "NOT_RUN",
    "UNCONFIRMED",
)
P7_R55_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "rn_contract",
    "r52_target",
    "r53_target_split",
    "r53_one_shot_timeout",
    "r54_collect_only",
    "r54_target_split",
    "r54_one_shot_timeout",
    "full_backend_suite",
)
P7_R55_VALIDATION_GREEN_ALLOWED_CLAIM_LEVEL_REFS: Final[frozenset[str]] = frozenset(
    {"PASSED_TARGET", "PASSED_SPLIT_TARGET"}
)
P7_R55_VALIDATION_NOT_GREEN_CLAIM_LEVEL_REFS: Final[frozenset[str]] = frozenset(
    {"COLLECT_ONLY", "TIMEOUT_ONE_SHOT", "NOT_RUN", "UNCONFIRMED"}
)

P7_R55_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "evidence_group_ref",
    "command_ref",
    "command_scope_ref",
    "claim_level_ref",
    "passed_count",
    "collected_count",
    "warning_count",
    "timeout_observed",
    "one_shot_attempted",
    "collect_only",
    "green_claim_allowed",
    "evidence_source_ref",
    "green_claim_scope_ref",
    "p5_actual_review_completion_claimed",
    "p6_p8_start_allowed_claim",
    "p7_complete_claimed",
    "release_allowed_claimed",
    "full_backend_suite_green_claimed",
    "rn_real_device_modal_readfeel_claimed",
    "collect_only_claimed_as_green",
    "one_shot_timeout_claimed_as_green",
    "body_free",
)

P7_R55_VALIDATION_EVIDENCE_RECONCILE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r1_prior_helper_source_reconcile_schema_version",
    "r1_prior_helper_source_reconcile_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "validation_evidence_rows",
    "validation_evidence_row_count",
    "validation_evidence_group_refs",
    "claim_level_refs_present",
    "passed_target_row_count",
    "passed_split_target_row_count",
    "collect_only_row_count",
    "timeout_one_shot_row_count",
    "not_run_or_unconfirmed_row_count",
    "green_allowed_row_count",
    "green_claim_allowed_passed_count_total",
    "one_shot_timeout_claimed_as_green",
    "collect_only_claimed_as_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "full_backend_suite_green_confirmed",
    "split_green_claimed_as_actual_human_review_complete",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

P7_R55_R54_HANDOFF_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r2_validation_evidence_reconcile_schema_version",
    "r2_validation_evidence_reconcile_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "current_received_snapshot_used_as_actual_review_basis",
    "r54_handoff_current_snapshot_used_as_actual_review_basis",
    "r54_handoff_schema_version",
    "r54_handoff_material_ref",
    "r54_handoff_policy_section_ref",
    "r54_handoff_current_received_snapshot_refs",
    "r54_handoff_current_received_snapshot_ref_count",
    "r54_handoff_status",
    "r54_handoff_reason_refs",
    "r54_review_operation_state_ref",
    "r54_p5_decision_candidate_ref",
    "r54_actual_review_evidence_complete",
    "r54_r52_reintake_ready",
    "r54_r52_reintake_materialized_here",
    "r54_validation_documentation_schema_version",
    "r54_validation_documentation_material_ref",
    "r54_validation_documentation_policy_section_ref",
    "r54_validation_documentation_status",
    "r54_validation_documentation_materialized_here",
    "forbidden_payload_detected",
    "question_text_detected",
    "no_touch_violation_detected",
    "no_touch_touched_refs",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r3_r54_handoff_intake_schema_version",
    "r3_r54_handoff_intake_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "scan_scope_ref",
    "scan_target_material_refs",
    "scan_target_schema_versions",
    "scan_target_policy_sections",
    "scan_target_material_count",
    "forbidden_payload_key_refs",
    "forbidden_payload_true_flag_refs",
    "forbidden_payload_key_ref_count",
    "forbidden_payload_true_flag_ref_count",
    "scan_result_ref",
    "bodyfree_boundary_risk_ref",
    "blocked_by_body_free_boundary_risk",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "r55_4_bodyfree_forbidden_payload_scan_done",
    "r55_5_actual_review_evidence_gap_assessed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_FORBIDDEN_SCAN_DETECTION_FALSE_KEY_REFS,
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r4_bodyfree_forbidden_payload_scan_schema_version",
    "r4_bodyfree_forbidden_payload_scan_material_ref",
    "r3_r54_handoff_intake_schema_version",
    "r3_r54_handoff_intake_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "actual_review_evidence_source_ref",
    "r54_handoff_status",
    "r54_review_operation_state_ref",
    "r54_p5_decision_candidate_ref",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "missing_evidence_refs",
    "missing_evidence_ref_count",
    "gap_status_ref",
    "p5_decision_status_ref",
    "p5_decision_candidate_ref",
    "evidence_missing_classified_as_p5_repair_required",
    "evidence_missing_classified_as_p8_material_candidate",
    "bodyfree_forbidden_payload_scan_clear",
    "blocked_by_body_free_boundary_risk",
    "blocked_by_no_touch_violation",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "r55_4_bodyfree_forbidden_payload_scan_done",
    "r55_5_actual_review_evidence_gap_assessed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R55_R0_R1_FALSE_KEY_REFS}


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R55_DEFAULT_REVIEW_SESSION_ID, max_length=140)


def _snapshot_refs(base: Mapping[str, str], overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    refs = dict(base)
    for key, value in safe_mapping(overrides).items():
        if key in refs:
            refs[key] = clean_identifier(value, default=refs[key], max_length=320)
    return refs


def _current_received_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS, overrides)


def _body_free_markers() -> dict[str, bool]:
    markers = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    markers.update(
        {
            "returned_surface_included": False,
            "history_body_included": False,
            "reviewer_notes_included": False,
            "question_text_included": False,
            "draft_question_text_included": False,
            "local_absolute_path_included": False,
            "body_content_hash_included": False,
            "packet_content_hash_included": False,
            "command_full_output_included": False,
        }
    )
    return markers


def _public_no_touch_contract() -> dict[str, bool]:
    return {
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "rn_visible_contract_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "public_response_key_changed_here": False,
        "runtime_changed_here": False,
        "gate_threshold_changed_here": False,
        "question_implementation_changed_here": False,
        "release_material_changed_here": False,
    }


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R55_FORBIDDEN_PAYLOAD_KEY_REFS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_payload_key(child) for child in value)
    return False


def _forbidden_payload_key_refs(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            if key_ref in P7_R55_FORBIDDEN_PAYLOAD_KEY_REFS:
                found.append(key_ref)
            found.extend(_forbidden_payload_key_refs(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_forbidden_payload_key_refs(child))
    return dedupe_identifiers(found, limit=80, max_length=120)


def _forbidden_true_flag_refs(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            if key_ref in P7_R55_R0_R1_FALSE_KEY_REFS and child is True:
                found.append(key_ref)
            if key_ref in P7_R55_FORBIDDEN_SCAN_DETECTION_FALSE_KEY_REFS and child is True:
                found.append(key_ref)
            found.extend(_forbidden_true_flag_refs(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_forbidden_true_flag_refs(child))
    return dedupe_identifiers(found, limit=80, max_length=120)


def _material_id_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    return [clean_identifier(material.get("material_id"), default="r55_material", max_length=220) for material in materials]


def _material_schema_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    return [clean_identifier(material.get("schema_version"), default="r55_schema", max_length=220) for material in materials]


def _material_policy_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    return [clean_identifier(material.get("policy_section"), default="r55_policy_section", max_length=220) for material in materials]


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:6]}")
    extra = sorted(set(data) - set(required))
    if extra:
        raise ValueError(f"{source} has unexpected fields: {extra[:6]}")


def _assert_body_free_common(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R55_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R55_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r55_public_no_touch_contract") or {}, source=f"{source}.r55_public_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for false_key in P7_R55_R0_R1_FALSE_KEY_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    if _contains_forbidden_payload_key(data):
        raise ValueError(f"{source} contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    current_refs = safe_mapping(data.get("current_received_snapshot_refs"))
    if current_refs != P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current received snapshot refs changed")
    if data.get("current_received_snapshot_ref_count") != len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} current received snapshot ref count changed")
    if data.get("actual_review_basis_ref") != P7_R55_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} must allow only R55 current received snapshot as review basis")


def _prior_helper_definitions() -> tuple[dict[str, Any], ...]:
    return (
        {
            "helper_ref": "R52",
            "helper_step_ref": P7_R52_STEP,
            "helper_scope_ref": P7_R52_SCOPE,
            "helper_policy_kind_ref": P7_R52_POLICY_KIND,
            "helper_snapshot_ref_group": "p7_r52_current_received_snapshot_refs",
            "helper_snapshot_refs": dict(P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS),
        },
        {
            "helper_ref": "R53",
            "helper_step_ref": P7_R53_STEP,
            "helper_scope_ref": P7_R53_SCOPE,
            "helper_policy_kind_ref": P7_R53_POLICY_KIND,
            "helper_snapshot_ref_group": "p7_r53_current_received_snapshot_refs",
            "helper_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        },
        {
            "helper_ref": "R54",
            "helper_step_ref": P7_R54_STEP,
            "helper_scope_ref": P7_R54_SCOPE,
            "helper_policy_kind_ref": P7_R54_POLICY_KIND,
            "helper_snapshot_ref_group": "p7_r54_current_received_snapshot_refs",
            "helper_snapshot_refs": dict(P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        },
    )


def _expected_prior_helper_refs(helper_ref: str) -> Mapping[str, str]:
    expected = {
        "R52": P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS,
        "R53": P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
        "R54": P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS,
    }
    return expected.get(helper_ref, {})


def _source_delta_reason_refs(helper_ref: str) -> list[str]:
    safe_ref = clean_identifier(helper_ref, default="RXX", max_length=12).lower()
    return [
        f"{safe_ref}_helper_refs_are_prior_historical_context_only",
        "r55_current_received_snapshot_refreeze_required_before_r52_reintake",
        "prior_helper_refs_must_not_be_reused_as_actual_review_basis",
    ]


def _prior_helper_source_row(helper: Mapping[str, Any]) -> dict[str, Any]:
    helper_ref = clean_identifier(helper.get("helper_ref"), default="RXX", max_length=12)
    helper_refs = safe_mapping(helper.get("helper_snapshot_refs"))
    refs_match = helper_refs == P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    row = {
        "schema_version": P7_R55_PRIOR_HELPER_SOURCE_ROW_SCHEMA_VERSION,
        "helper_ref": helper_ref,
        "helper_step_ref": clean_identifier(helper.get("helper_step_ref"), default="helper_step", max_length=220),
        "helper_scope_ref": clean_identifier(helper.get("helper_scope_ref"), default="helper_scope", max_length=220),
        "helper_policy_kind_ref": clean_identifier(helper.get("helper_policy_kind_ref"), default="helper_policy", max_length=220),
        "helper_snapshot_ref_group": clean_identifier(helper.get("helper_snapshot_ref_group"), default="helper_snapshot_refs", max_length=160),
        "helper_snapshot_refs": dict(helper_refs),
        "helper_snapshot_ref_count": len(helper_refs),
        "current_snapshot_ref_group": "p7_r55_current_received_snapshot_refs",
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "comparison_to_current_ref": f"{helper_ref}_refs_to_R55_current_received_snapshot_refs",
        "comparison_status_ref": P7_R55_PRIOR_HELPER_COMPARISON_STATUS_REF,
        "refs_match_current_received_snapshot": refs_match,
        "classification_ref": P7_R55_PRIOR_HELPER_CLASSIFICATION_REF,
        "used_as_actual_review_basis": False,
        "used_as_regression_context_only": True,
        "current_snapshot_used_as_actual_review_basis": True,
        "source_delta_reason_refs": _source_delta_reason_refs(helper_ref),
        "body_free": True,
    }
    assert_p7_r55_prior_helper_source_row_contract(row)
    return row


def assert_p7_r55_prior_helper_source_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R55_PRIOR_HELPER_SOURCE_ROW_REQUIRED_FIELD_REFS,
        source="p7_r55_r1_prior_helper_source_row",
    )
    if data.get("schema_version") != P7_R55_PRIOR_HELPER_SOURCE_ROW_SCHEMA_VERSION:
        raise ValueError("R55 prior helper source row schema version changed")
    helper_ref = clean_identifier(data.get("helper_ref"), default="", max_length=12)
    if helper_ref not in {"R52", "R53", "R54"}:
        raise ValueError("R55 prior helper source row helper ref changed")
    if safe_mapping(data.get("helper_snapshot_refs")) != dict(_expected_prior_helper_refs(helper_ref)):
        raise ValueError("R55 prior helper source row helper refs changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R55 prior helper source row current refs changed")
    if data.get("helper_snapshot_ref_count") != len(_expected_prior_helper_refs(helper_ref)):
        raise ValueError("R55 prior helper source row helper ref count changed")
    if data.get("current_received_snapshot_ref_count") != len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("R55 prior helper source row current ref count changed")
    if data.get("refs_match_current_received_snapshot") is not False:
        raise ValueError("R55 prior helper source row must keep prior/current mismatch visible")
    if data.get("comparison_status_ref") != P7_R55_PRIOR_HELPER_COMPARISON_STATUS_REF:
        raise ValueError("R55 prior helper source row comparison status changed")
    if data.get("classification_ref") != P7_R55_PRIOR_HELPER_CLASSIFICATION_REF:
        raise ValueError("R55 prior helper source row classification changed")
    for false_key in ("used_as_actual_review_basis",):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 prior helper source row must keep {false_key}=False")
    for true_key in ("used_as_regression_context_only", "current_snapshot_used_as_actual_review_basis"):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 prior helper source row must keep {true_key}=True")
    if data.get("body_free") is not True:
        raise ValueError("R55 prior helper source row must be body-free")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 prior helper source row contains a forbidden payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r1_prior_helper_source_row")
    return True


def build_p7_r55_current_received_snapshot_refreeze(
    *,
    current_received_snapshot_refs: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_current_received_snapshot_refreeze",
    review_session_id: Any = P7_R55_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Build R55-0 body-free current received snapshot refreeze material."""

    refs = _current_received_snapshot_refs(current_received_snapshot_refs)
    refreeze = {
        "schema_version": P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": "R55-0_scope_current_received_snapshot_refreeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_current_received_snapshot_refreeze", max_length=220),
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "current_received_snapshot_refs": refs,
        "current_received_snapshot_ref_count": len(refs),
        "current_snapshot_refrozen_here": True,
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "prior_helper_refs_used_as_actual_review_basis": False,
        "current_received_snapshot_used_as_actual_review_basis": True,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": False,
        "implemented_steps": list(P7_R55_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R0_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r55_current_received_snapshot_refreeze_contract(refreeze)
    return refreeze


def assert_p7_r55_current_received_snapshot_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r55_r0_current_received_snapshot_refreeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        source="p7_r55_r0_current_received_snapshot_refreeze",
    )
    if data.get("policy_section") != "R55-0_scope_current_received_snapshot_refreeze":
        raise ValueError("R55 R0 policy section changed")
    _assert_current_refs(data, source="p7_r55_r0_current_received_snapshot_refreeze")
    if data.get("current_snapshot_refrozen_here") is not True:
        raise ValueError("R55 R0 must mark current snapshot refrozen")
    if data.get("prior_helper_refs_used_as_actual_review_basis") is not False:
        raise ValueError("R55 R0 must not use prior helper refs as actual review basis")
    if data.get("current_received_snapshot_used_as_actual_review_basis") is not True:
        raise ValueError("R55 R0 must use the R55 current received snapshot as actual review basis")
    if data.get("r55_0_scope_current_received_snapshot_refrozen") is not True:
        raise ValueError("R55 R0 must mark R55-0 refrozen")
    if data.get("r55_1_prior_helper_source_reconciled") is not False:
        raise ValueError("R55 R0 must not claim R55-1")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R0_IMPLEMENTED_STEPS:
        raise ValueError("R55 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R0 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R0 must point to R55-1")
    return True


def build_p7_r55_prior_helper_source_reconcile_bodyfree(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    prior_helper_row_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r55_prior_helper_source_reconcile",
) -> dict[str, Any]:
    """Build R55-1 body-free prior helper source reconcile material."""

    r0 = (
        safe_mapping(current_received_snapshot_refreeze)
        if current_received_snapshot_refreeze is not None
        else build_p7_r55_current_received_snapshot_refreeze()
    )
    assert_p7_r55_current_received_snapshot_refreeze_contract(r0)
    rows: list[dict[str, Any]] = []
    overrides = safe_mapping(prior_helper_row_overrides)
    for helper in _prior_helper_definitions():
        row = _prior_helper_source_row(helper)
        patch = safe_mapping(overrides.get(str(row["helper_ref"])))
        if patch:
            row.update(patch)
            assert_p7_r55_prior_helper_source_row_contract(row)
        rows.append(row)
    reconcile = {
        "schema_version": P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": "R55-1_prior_helper_source_reconcile",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_prior_helper_source_reconcile", max_length=220),
        "review_session_id": _safe_review_session_id(r0.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r0_refreeze_schema_version": P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "r0_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r55_current_received_snapshot_refreeze", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "prior_helper_ref_keys": ["R52", "R53", "R54"],
        "prior_helper_source_rows": rows,
        "prior_helper_source_row_count": len(rows),
        "all_prior_helper_refs_classified": True,
        "prior_helper_refs_used_as_actual_review_basis": False,
        "prior_helper_refs_used_as_regression_context_only": True,
        "current_received_snapshot_used_as_actual_review_basis": True,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "implemented_steps": list(P7_R55_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R1_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract(reconcile)
    return reconcile


def assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract(reconcile: Mapping[str, Any]) -> bool:
    data = safe_mapping(reconcile)
    _assert_required_fields(
        data,
        required=P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_REQUIRED_FIELD_REFS,
        source="p7_r55_r1_prior_helper_source_reconcile",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_SCHEMA_VERSION,
        source="p7_r55_r1_prior_helper_source_reconcile",
    )
    if data.get("policy_section") != "R55-1_prior_helper_source_reconcile":
        raise ValueError("R55 R1 policy section changed")
    if data.get("r0_refreeze_schema_version") != P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R55 R1 R0 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r1_prior_helper_source_reconcile")
    rows = data.get("prior_helper_source_rows")
    expected_refs = ["R52", "R53", "R54"]
    if data.get("prior_helper_ref_keys") != expected_refs:
        raise ValueError("R55 R1 prior helper ref keys changed")
    if not isinstance(rows, list) or len(rows) != len(expected_refs):
        raise ValueError("R55 R1 prior helper source rows changed")
    if data.get("prior_helper_source_row_count") != len(expected_refs):
        raise ValueError("R55 R1 prior helper source row count changed")
    row_refs = [safe_mapping(row).get("helper_ref") for row in rows]
    if row_refs != expected_refs:
        raise ValueError("R55 R1 prior helper row order changed")
    for row in rows:
        assert_p7_r55_prior_helper_source_row_contract(safe_mapping(row))
    for false_key in ("prior_helper_refs_used_as_actual_review_basis",):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R1 must keep {false_key}=False")
    for true_key in (
        "all_prior_helper_refs_classified",
        "prior_helper_refs_used_as_regression_context_only",
        "current_received_snapshot_used_as_actual_review_basis",
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R1 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_IMPLEMENTED_STEPS:
        raise ValueError("R55 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R1 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R1 must point to R55-2")
    return True


# ---------------------------------------------------------------------------
# R55-2 validation evidence reconcile
# ---------------------------------------------------------------------------


def _int_count(value: Any, *, default: int = 0, minimum: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _validation_evidence_row(
    *,
    evidence_group_ref: str,
    command_ref: str,
    command_scope_ref: str,
    claim_level_ref: str,
    passed_count: int = 0,
    collected_count: int = 0,
    warning_count: int = 0,
    timeout_observed: bool = False,
    one_shot_attempted: bool = False,
    collect_only: bool = False,
    green_claim_allowed: bool = False,
    evidence_source_ref: str,
    green_claim_scope_ref: str,
) -> dict[str, Any]:
    row = {
        "schema_version": P7_R55_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION,
        "evidence_group_ref": clean_identifier(evidence_group_ref, default="validation_evidence", max_length=120),
        "command_ref": clean_identifier(command_ref, default="validation_command_ref", max_length=180),
        "command_scope_ref": clean_identifier(command_scope_ref, default="targeted_validation_only", max_length=180),
        "claim_level_ref": clean_identifier(claim_level_ref, default="UNCONFIRMED", max_length=60),
        "passed_count": _int_count(passed_count),
        "collected_count": _int_count(collected_count),
        "warning_count": _int_count(warning_count),
        "timeout_observed": bool(timeout_observed),
        "one_shot_attempted": bool(one_shot_attempted),
        "collect_only": bool(collect_only),
        "green_claim_allowed": bool(green_claim_allowed),
        "evidence_source_ref": clean_identifier(evidence_source_ref, default="r55_validation_evidence_source", max_length=220),
        "green_claim_scope_ref": clean_identifier(green_claim_scope_ref, default="not_product_readiness", max_length=220),
        "p5_actual_review_completion_claimed": False,
        "p6_p8_start_allowed_claim": False,
        "p7_complete_claimed": False,
        "release_allowed_claimed": False,
        "full_backend_suite_green_claimed": False,
        "rn_real_device_modal_readfeel_claimed": False,
        "collect_only_claimed_as_green": False,
        "one_shot_timeout_claimed_as_green": False,
        "body_free": True,
    }
    assert_p7_r55_validation_evidence_row_bodyfree_contract(row)
    return row


def _default_validation_evidence_rows() -> list[dict[str, Any]]:
    return [
        _validation_evidence_row(
            evidence_group_ref="rn_contract",
            command_ref="npm_run_test_rn_screens_silent",
            command_scope_ref="rn_contract_only_not_real_device_modal_readfeel",
            claim_level_ref="PASSED_TARGET",
            passed_count=36,
            collected_count=36,
            green_claim_allowed=True,
            one_shot_attempted=True,
            evidence_source_ref="r55_pre_design_memo_rn_contract_current_zip",
            green_claim_scope_ref="rn_visible_contract_only",
        ),
        _validation_evidence_row(
            evidence_group_ref="r52_target",
            command_ref="pytest_r52_target",
            command_scope_ref="r52_decision_gate_target_only_not_p6_p8_start",
            claim_level_ref="PASSED_TARGET",
            passed_count=219,
            collected_count=219,
            green_claim_allowed=True,
            one_shot_attempted=True,
            evidence_source_ref="r55_pre_design_memo_r52_target_current_zip",
            green_claim_scope_ref="r52_contract_target_only",
        ),
        _validation_evidence_row(
            evidence_group_ref="r53_target_split",
            command_ref="pytest_r53_target_split_total",
            command_scope_ref="r53_split_target_only_not_one_shot_green",
            claim_level_ref="PASSED_SPLIT_TARGET",
            passed_count=291,
            collected_count=291,
            timeout_observed=False,
            one_shot_attempted=False,
            green_claim_allowed=True,
            evidence_source_ref="r55_pre_design_memo_r53_split_target_current_zip",
            green_claim_scope_ref="r53_split_target_contract_only",
        ),
        _validation_evidence_row(
            evidence_group_ref="r53_one_shot_timeout",
            command_ref="pytest_r53_target_one_shot_attempt",
            command_scope_ref="r53_one_shot_timeout_not_green",
            claim_level_ref="TIMEOUT_ONE_SHOT",
            timeout_observed=True,
            one_shot_attempted=True,
            green_claim_allowed=False,
            evidence_source_ref="r55_pre_design_memo_r53_one_shot_timeout",
            green_claim_scope_ref="timeout_not_green",
        ),
        _validation_evidence_row(
            evidence_group_ref="r54_collect_only",
            command_ref="pytest_r54_target_collect_only",
            command_scope_ref="r54_collect_only_not_execution_green",
            claim_level_ref="COLLECT_ONLY",
            collected_count=309,
            collect_only=True,
            green_claim_allowed=False,
            evidence_source_ref="r55_pre_design_memo_r54_collect_only",
            green_claim_scope_ref="collect_only_not_green",
        ),
        _validation_evidence_row(
            evidence_group_ref="r54_target_split",
            command_ref="pytest_r54_target_split_total",
            command_scope_ref="r54_split_target_only_not_actual_human_review",
            claim_level_ref="PASSED_SPLIT_TARGET",
            passed_count=309,
            collected_count=309,
            timeout_observed=False,
            one_shot_attempted=False,
            green_claim_allowed=True,
            evidence_source_ref="r55_pre_design_memo_r54_split_target_current_zip",
            green_claim_scope_ref="r54_split_target_contract_only",
        ),
        _validation_evidence_row(
            evidence_group_ref="r54_one_shot_timeout",
            command_ref="pytest_r54_target_one_shot_attempt",
            command_scope_ref="r54_one_shot_timeout_not_green",
            claim_level_ref="TIMEOUT_ONE_SHOT",
            timeout_observed=True,
            one_shot_attempted=True,
            green_claim_allowed=False,
            evidence_source_ref="r55_pre_design_memo_r54_one_shot_timeout",
            green_claim_scope_ref="timeout_not_green",
        ),
        _validation_evidence_row(
            evidence_group_ref="full_backend_suite",
            command_ref="pytest_full_backend_suite",
            command_scope_ref="full_backend_suite_not_run_or_unconfirmed",
            claim_level_ref="NOT_RUN",
            green_claim_allowed=False,
            evidence_source_ref="r55_pre_design_memo_full_backend_suite_unconfirmed",
            green_claim_scope_ref="full_backend_suite_green_not_confirmed",
        ),
    ]


def assert_p7_r55_validation_evidence_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R55_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS,
        source="p7_r55_r2_validation_evidence_row",
    )
    if data.get("schema_version") != P7_R55_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION:
        raise ValueError("R55 validation evidence row schema version changed")
    if data.get("evidence_group_ref") not in P7_R55_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R55 validation evidence row group ref changed")
    claim_level = clean_identifier(data.get("claim_level_ref"), default="", max_length=60)
    if claim_level not in P7_R55_VALIDATION_CLAIM_LEVEL_REFS:
        raise ValueError("R55 validation evidence row claim level changed")
    if data.get("body_free") is not True:
        raise ValueError("R55 validation evidence row must be body-free")
    if claim_level in P7_R55_VALIDATION_GREEN_ALLOWED_CLAIM_LEVEL_REFS:
        if data.get("green_claim_allowed") is not True:
            raise ValueError("R55 passed target evidence row must allow only local target green claim")
    if claim_level in P7_R55_VALIDATION_NOT_GREEN_CLAIM_LEVEL_REFS:
        if data.get("green_claim_allowed") is not False:
            raise ValueError("R55 collect-only/timeout/not-run evidence row must not be green")
    if claim_level == "COLLECT_ONLY":
        if data.get("collect_only") is not True or data.get("passed_count") != 0:
            raise ValueError("R55 collect-only row must not be execution green")
    if claim_level == "TIMEOUT_ONE_SHOT":
        if data.get("timeout_observed") is not True or data.get("one_shot_attempted") is not True:
            raise ValueError("R55 timeout row must keep timeout evidence explicit")
    for false_key in (
        "p5_actual_review_completion_claimed",
        "p6_p8_start_allowed_claim",
        "p7_complete_claimed",
        "release_allowed_claimed",
        "full_backend_suite_green_claimed",
        "rn_real_device_modal_readfeel_claimed",
        "collect_only_claimed_as_green",
        "one_shot_timeout_claimed_as_green",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 validation evidence row must keep {false_key}=False")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 validation evidence row contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r2_validation_evidence_row")
    return True


def build_p7_r55_validation_evidence_reconcile_bodyfree(
    *,
    prior_helper_source_reconcile: Mapping[str, Any] | None = None,
    validation_evidence_rows: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r55_validation_evidence_reconcile",
) -> dict[str, Any]:
    """Build R55-2 body-free validation evidence claim-level reconcile material."""

    r1 = (
        safe_mapping(prior_helper_source_reconcile)
        if prior_helper_source_reconcile is not None
        else build_p7_r55_prior_helper_source_reconcile_bodyfree()
    )
    assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract(r1)
    rows = [safe_mapping(row) for row in validation_evidence_rows] if validation_evidence_rows is not None else _default_validation_evidence_rows()
    for row in rows:
        assert_p7_r55_validation_evidence_row_bodyfree_contract(row)
    claim_levels = [str(row.get("claim_level_ref")) for row in rows]
    row_groups = [str(row.get("evidence_group_ref")) for row in rows]
    material = {
        "schema_version": P7_R55_VALIDATION_EVIDENCE_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R2_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_validation_evidence_reconcile", max_length=220),
        "review_session_id": _safe_review_session_id(r1.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r1_prior_helper_source_reconcile_schema_version": P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_SCHEMA_VERSION,
        "r1_prior_helper_source_reconcile_material_ref": clean_identifier(r1.get("material_id"), default="p7_r55_prior_helper_source_reconcile", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "validation_evidence_rows": rows,
        "validation_evidence_row_count": len(rows),
        "validation_evidence_group_refs": row_groups,
        "claim_level_refs_present": all(claim in P7_R55_VALIDATION_CLAIM_LEVEL_REFS for claim in claim_levels),
        "passed_target_row_count": sum(1 for claim in claim_levels if claim == "PASSED_TARGET"),
        "passed_split_target_row_count": sum(1 for claim in claim_levels if claim == "PASSED_SPLIT_TARGET"),
        "collect_only_row_count": sum(1 for claim in claim_levels if claim == "COLLECT_ONLY"),
        "timeout_one_shot_row_count": sum(1 for claim in claim_levels if claim == "TIMEOUT_ONE_SHOT"),
        "not_run_or_unconfirmed_row_count": sum(1 for claim in claim_levels if claim in {"NOT_RUN", "UNCONFIRMED"}),
        "green_allowed_row_count": sum(1 for row in rows if row.get("green_claim_allowed") is True),
        "green_claim_allowed_passed_count_total": sum(_int_count(row.get("passed_count")) for row in rows if row.get("green_claim_allowed") is True),
        "one_shot_timeout_claimed_as_green": False,
        "collect_only_claimed_as_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "full_backend_suite_green_confirmed": False,
        "split_green_claimed_as_actual_human_review_complete": False,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": False,
        "implemented_steps": list(P7_R55_R2_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R2_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R2_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(material)
    return material


def assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(reconcile: Mapping[str, Any]) -> bool:
    data = safe_mapping(reconcile)
    _assert_required_fields(
        data,
        required=P7_R55_VALIDATION_EVIDENCE_RECONCILE_REQUIRED_FIELD_REFS,
        source="p7_r55_r2_validation_evidence_reconcile",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_VALIDATION_EVIDENCE_RECONCILE_SCHEMA_VERSION,
        source="p7_r55_r2_validation_evidence_reconcile",
    )
    if data.get("policy_section") != P7_R55_R2_STEP_REF:
        raise ValueError("R55 R2 policy section changed")
    if data.get("r1_prior_helper_source_reconcile_schema_version") != P7_R55_PRIOR_HELPER_SOURCE_RECONCILE_SCHEMA_VERSION:
        raise ValueError("R55 R2 R1 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r2_validation_evidence_reconcile")
    rows = data.get("validation_evidence_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R55_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R55 R2 validation evidence rows changed")
    if data.get("validation_evidence_row_count") != len(rows):
        raise ValueError("R55 R2 validation evidence row count changed")
    row_groups = [safe_mapping(row).get("evidence_group_ref") for row in rows]
    if tuple(row_groups) != P7_R55_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R55 R2 validation evidence row order changed")
    for row in rows:
        assert_p7_r55_validation_evidence_row_bodyfree_contract(safe_mapping(row))
    if data.get("claim_level_refs_present") is not True:
        raise ValueError("R55 R2 must classify every validation evidence row by claim level")
    expected_counts = {
        "passed_target_row_count": 2,
        "passed_split_target_row_count": 2,
        "collect_only_row_count": 1,
        "timeout_one_shot_row_count": 2,
        "not_run_or_unconfirmed_row_count": 1,
        "green_allowed_row_count": 4,
        "green_claim_allowed_passed_count_total": 855,
    }
    for key, expected in expected_counts.items():
        if data.get(key) != expected:
            raise ValueError(f"R55 R2 {key} changed")
    for false_key in (
        "one_shot_timeout_claimed_as_green",
        "collect_only_claimed_as_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "full_backend_suite_green_confirmed",
        "split_green_claimed_as_actual_human_review_complete",
        "r55_3_r54_default_handoff_intake_done",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R2 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R2 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R2_IMPLEMENTED_STEPS:
        raise ValueError("R55 R2 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R2_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R2 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R2_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R2 must point to R55-3")
    return True


# ---------------------------------------------------------------------------
# R55-3 R54 default handoff intake
# ---------------------------------------------------------------------------


def build_p7_r55_r54_handoff_intake_bodyfree(
    *,
    validation_evidence_reconcile: Mapping[str, Any] | None = None,
    r54_r52_reintake_handoff: Mapping[str, Any] | None = None,
    r54_validation_documentation_output: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_r54_default_handoff_intake",
) -> dict[str, Any]:
    """Build R55-3 body-free intake of the R54 default blocked handoff."""

    r2 = (
        safe_mapping(validation_evidence_reconcile)
        if validation_evidence_reconcile is not None
        else build_p7_r55_validation_evidence_reconcile_bodyfree()
    )
    assert_p7_r55_validation_evidence_reconcile_bodyfree_contract(r2)
    r54_handoff = (
        safe_mapping(r54_r52_reintake_handoff)
        if r54_r52_reintake_handoff is not None
        else build_p7_r54_r52_reintake_handoff_bodyfree()
    )
    assert_p7_r54_r52_reintake_handoff_bodyfree_contract(r54_handoff)
    r54_documentation = (
        safe_mapping(r54_validation_documentation_output)
        if r54_validation_documentation_output is not None
        else build_p7_r54_validation_command_matrix_documentation_output_bodyfree(
            r52_reintake_handoff=r54_handoff
        )
    )
    assert_p7_r54_validation_command_matrix_documentation_output_bodyfree_contract(r54_documentation)

    actual_review_complete = r54_handoff.get("actual_review_evidence_complete") is True
    status = clean_identifier(
        r54_handoff.get("r52_reintake_handoff_status"),
        default=P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF,
        max_length=180,
    )
    validation_status = clean_identifier(
        r54_documentation.get("validation_documentation_status"),
        default=P7_R55_R54_DEFAULT_VALIDATION_DOCUMENTATION_STATUS_REF,
        max_length=180,
    )
    material = {
        "schema_version": P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R3_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_r54_default_handoff_intake", max_length=220),
        "review_session_id": _safe_review_session_id(r2.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r2_validation_evidence_reconcile_schema_version": P7_R55_VALIDATION_EVIDENCE_RECONCILE_SCHEMA_VERSION,
        "r2_validation_evidence_reconcile_material_ref": clean_identifier(r2.get("material_id"), default="p7_r55_validation_evidence_reconcile", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_received_snapshot_used_as_actual_review_basis": True,
        "r54_handoff_current_snapshot_used_as_actual_review_basis": False,
        "r54_handoff_schema_version": clean_identifier(r54_handoff.get("schema_version"), default=P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, max_length=180),
        "r54_handoff_material_ref": clean_identifier(r54_handoff.get("material_id"), default="p7_r54_r52_reintake_handoff_bodyfree", max_length=180),
        "r54_handoff_policy_section_ref": clean_identifier(r54_handoff.get("policy_section"), default=P7_R54_R22_STEP_REF, max_length=180),
        "r54_handoff_current_received_snapshot_refs": dict(safe_mapping(r54_handoff.get("current_received_snapshot_refs"))),
        "r54_handoff_current_received_snapshot_ref_count": _int_count(r54_handoff.get("current_received_snapshot_ref_count")),
        "r54_handoff_status": status,
        "r54_handoff_reason_refs": dedupe_identifiers(r54_handoff.get("r52_reintake_handoff_reason_refs"), limit=20, max_length=140),
        "r54_review_operation_state_ref": P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF if not actual_review_complete else "actual_review_evidence_complete_not_expected_in_r55_r3_default_intake",
        "r54_p5_decision_candidate_ref": clean_identifier(r54_handoff.get("p5_decision_candidate_ref"), default=P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF, max_length=180),
        "r54_actual_review_evidence_complete": actual_review_complete,
        "r54_r52_reintake_ready": r54_handoff.get("r52_reintake_ready") is True,
        "r54_r52_reintake_materialized_here": r54_handoff.get("r52_reintake_handoff_materialized_here") is True,
        "r54_validation_documentation_schema_version": clean_identifier(r54_documentation.get("schema_version"), default=P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION, max_length=180),
        "r54_validation_documentation_material_ref": clean_identifier(r54_documentation.get("material_id"), default="p7_r54_validation_command_matrix_documentation_output_bodyfree", max_length=180),
        "r54_validation_documentation_policy_section_ref": clean_identifier(r54_documentation.get("policy_section"), default=P7_R54_R23_STEP_REF, max_length=180),
        "r54_validation_documentation_status": validation_status,
        "r54_validation_documentation_materialized_here": r54_documentation.get("documentation_output_materialized_here") is True,
        "forbidden_payload_detected": False,
        "question_text_detected": r54_handoff.get("question_text_detected") is True,
        "no_touch_violation_detected": r54_handoff.get("no_touch_violation_detected") is True,
        "no_touch_touched_refs": dedupe_identifiers(r54_handoff.get("no_touch_touched_refs"), limit=20, max_length=140),
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "implemented_steps": list(P7_R55_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R3_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r55_r54_handoff_intake_bodyfree_contract(material)
    return material


def assert_p7_r55_r54_handoff_intake_bodyfree_contract(intake: Mapping[str, Any]) -> bool:
    data = safe_mapping(intake)
    _assert_required_fields(
        data,
        required=P7_R55_R54_HANDOFF_INTAKE_REQUIRED_FIELD_REFS,
        source="p7_r55_r3_r54_handoff_intake",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION,
        source="p7_r55_r3_r54_handoff_intake",
    )
    if data.get("policy_section") != P7_R55_R3_STEP_REF:
        raise ValueError("R55 R3 policy section changed")
    if data.get("r2_validation_evidence_reconcile_schema_version") != P7_R55_VALIDATION_EVIDENCE_RECONCILE_SCHEMA_VERSION:
        raise ValueError("R55 R3 R2 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r3_r54_handoff_intake")
    if data.get("current_received_snapshot_used_as_actual_review_basis") is not True:
        raise ValueError("R55 R3 must keep R55 current snapshot as actual review basis")
    if data.get("r54_handoff_current_snapshot_used_as_actual_review_basis") is not False:
        raise ValueError("R55 R3 must not reuse R54 helper snapshot as actual review basis")
    if data.get("r54_handoff_schema_version") != P7_R54_R52_REINTAKE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("R55 R3 R54 handoff schema version changed")
    if data.get("r54_validation_documentation_schema_version") != P7_R54_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION:
        raise ValueError("R55 R3 R54 validation documentation schema version changed")
    if data.get("r54_handoff_status") not in P7_R54_R52_REINTAKE_HANDOFF_STATUS_REFS:
        raise ValueError("R55 R3 unknown R54 handoff status")
    if data.get("r54_validation_documentation_status") not in P7_R54_VALIDATION_DOCUMENTATION_STATUS_REFS:
        raise ValueError("R55 R3 unknown R54 validation documentation status")
    if data.get("r54_handoff_status") != P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF:
        raise ValueError("R55 R3 must intake the default R54 actual-review-evidence-missing handoff")
    if data.get("r54_validation_documentation_status") != P7_R55_R54_DEFAULT_VALIDATION_DOCUMENTATION_STATUS_REF:
        raise ValueError("R55 R3 must keep R54 validation documentation blocked by R54-22")
    if data.get("r54_review_operation_state_ref") != P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("R55 R3 default review operation state must remain not_started")
    if data.get("r54_p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R55 R3 default P5 decision candidate must remain P5_NOT_REVIEWED")
    for false_key in (
        "r54_actual_review_evidence_complete",
        "r54_r52_reintake_ready",
        "r54_r52_reintake_materialized_here",
        "r54_validation_documentation_materialized_here",
        "forbidden_payload_detected",
        "question_text_detected",
        "no_touch_violation_detected",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R3 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R3 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R3_IMPLEMENTED_STEPS:
        raise ValueError("R55 R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R3 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R3_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R3 must point to R55-4")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 R3 contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r3_r54_handoff_intake")
    return True
 

# ---------------------------------------------------------------------------
# R55-4 body-free forbidden payload scan
# ---------------------------------------------------------------------------


def _default_r55_scan_materials(r54_handoff_intake: Mapping[str, Any]) -> list[dict[str, Any]]:
    r0 = build_p7_r55_current_received_snapshot_refreeze()
    r1 = build_p7_r55_prior_helper_source_reconcile_bodyfree(current_received_snapshot_refreeze=r0)
    r2 = build_p7_r55_validation_evidence_reconcile_bodyfree(prior_helper_source_reconcile=r1)
    r3 = safe_mapping(r54_handoff_intake)
    assert_p7_r55_r54_handoff_intake_bodyfree_contract(r3)
    return [r0, r1, r2, dict(r3)]


def build_p7_r55_bodyfree_forbidden_payload_scan_bodyfree(
    *,
    r54_handoff_intake: Mapping[str, Any] | None = None,
    scan_target_materials: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r55_bodyfree_forbidden_payload_scan",
) -> dict[str, Any]:
    """Build R55-4 body-free scan material without storing scanned body payloads."""

    r3 = (
        safe_mapping(r54_handoff_intake)
        if r54_handoff_intake is not None
        else build_p7_r55_r54_handoff_intake_bodyfree()
    )
    assert_p7_r55_r54_handoff_intake_bodyfree_contract(r3)
    scan_materials = (
        [safe_mapping(material) for material in scan_target_materials]
        if scan_target_materials is not None
        else _default_r55_scan_materials(r3)
    )
    if not scan_materials:
        raise ValueError("R55 R4 requires at least one body-free material to scan")
    forbidden_keys: list[str] = []
    forbidden_flags: list[str] = []
    for material in scan_materials:
        forbidden_keys.extend(_forbidden_payload_key_refs(material))
        forbidden_flags.extend(_forbidden_true_flag_refs(material))
        assert_p7_no_body_payload_or_contract_mutation(material, source="p7_r55_r4_scan_target_material")
    forbidden_keys = dedupe_identifiers(forbidden_keys, limit=80, max_length=120)
    forbidden_flags = dedupe_identifiers(forbidden_flags, limit=80, max_length=120)
    if forbidden_keys or forbidden_flags:
        raise ValueError("R55 R4 detected forbidden body/question payload or true promotion flags")

    material = {
        "schema_version": P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R4_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_bodyfree_forbidden_payload_scan", max_length=220),
        "review_session_id": _safe_review_session_id(r3.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r3_r54_handoff_intake_schema_version": P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION,
        "r3_r54_handoff_intake_material_ref": clean_identifier(r3.get("material_id"), default="p7_r55_r54_default_handoff_intake", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "scan_scope_ref": "r55_intake_intermediate_material_bodyfree_forbidden_payload_scan",
        "scan_target_material_refs": _material_id_refs(scan_materials),
        "scan_target_schema_versions": _material_schema_refs(scan_materials),
        "scan_target_policy_sections": _material_policy_refs(scan_materials),
        "scan_target_material_count": len(scan_materials),
        "forbidden_payload_key_refs": [],
        "forbidden_payload_true_flag_refs": [],
        "forbidden_payload_key_ref_count": 0,
        "forbidden_payload_true_flag_ref_count": 0,
        "scan_result_ref": P7_R55_FORBIDDEN_PAYLOAD_SCAN_CLEAR_REF,
        "bodyfree_boundary_risk_ref": P7_R55_BODYFREE_BOUNDARY_RISK_CLEAR_REF,
        "blocked_by_body_free_boundary_risk": False,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": False,
        "implemented_steps": list(P7_R55_R4_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R4_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R4_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **{key: False for key in P7_R55_FORBIDDEN_SCAN_DETECTION_FALSE_KEY_REFS},
        **_false_flags(),
    }
    assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(material)
    return material


def assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(scan: Mapping[str, Any]) -> bool:
    data = safe_mapping(scan)
    _assert_required_fields(
        data,
        required=P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_REQUIRED_FIELD_REFS,
        source="p7_r55_r4_bodyfree_forbidden_payload_scan",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION,
        source="p7_r55_r4_bodyfree_forbidden_payload_scan",
    )
    if data.get("policy_section") != P7_R55_R4_STEP_REF:
        raise ValueError("R55 R4 policy section changed")
    if data.get("r3_r54_handoff_intake_schema_version") != P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION:
        raise ValueError("R55 R4 R3 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r4_bodyfree_forbidden_payload_scan")
    target_refs = data.get("scan_target_material_refs")
    schema_refs = data.get("scan_target_schema_versions")
    policy_refs = data.get("scan_target_policy_sections")
    if not isinstance(target_refs, list) or not target_refs:
        raise ValueError("R55 R4 scan target refs must be present")
    if not isinstance(schema_refs, list) or len(schema_refs) != len(target_refs):
        raise ValueError("R55 R4 scan target schema refs changed")
    if not isinstance(policy_refs, list) or len(policy_refs) != len(target_refs):
        raise ValueError("R55 R4 scan target policy refs changed")
    if data.get("scan_target_material_count") != len(target_refs):
        raise ValueError("R55 R4 scan target count changed")
    if data.get("forbidden_payload_key_refs") != [] or data.get("forbidden_payload_true_flag_refs") != []:
        raise ValueError("R55 R4 must not retain forbidden payload key or true flag refs")
    if data.get("forbidden_payload_key_ref_count") != 0 or data.get("forbidden_payload_true_flag_ref_count") != 0:
        raise ValueError("R55 R4 forbidden payload counts must stay zero")
    if data.get("scan_result_ref") != P7_R55_FORBIDDEN_PAYLOAD_SCAN_CLEAR_REF:
        raise ValueError("R55 R4 scan result changed")
    if data.get("bodyfree_boundary_risk_ref") != P7_R55_BODYFREE_BOUNDARY_RISK_CLEAR_REF:
        raise ValueError("R55 R4 body-free boundary risk ref changed")
    for false_key in (*P7_R55_FORBIDDEN_SCAN_DETECTION_FALSE_KEY_REFS, "blocked_by_body_free_boundary_risk", "r55_5_actual_review_evidence_gap_assessed"):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R4 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R4 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R4_IMPLEMENTED_STEPS:
        raise ValueError("R55 R4 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R4_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R4 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R4_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R4 must point to R55-5")
    return True


# ---------------------------------------------------------------------------
# R55-5 actual review evidence gap assessment
# ---------------------------------------------------------------------------


def build_p7_r55_actual_review_evidence_gap_assessment_bodyfree(
    *,
    bodyfree_forbidden_payload_scan: Mapping[str, Any] | None = None,
    r54_handoff_intake: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_actual_review_evidence_gap_assessment",
) -> dict[str, Any]:
    """Build R55-5 body-free current default actual-review-evidence gap material."""

    r3 = (
        safe_mapping(r54_handoff_intake)
        if r54_handoff_intake is not None
        else build_p7_r55_r54_handoff_intake_bodyfree()
    )
    assert_p7_r55_r54_handoff_intake_bodyfree_contract(r3)
    r4 = (
        safe_mapping(bodyfree_forbidden_payload_scan)
        if bodyfree_forbidden_payload_scan is not None
        else build_p7_r55_bodyfree_forbidden_payload_scan_bodyfree(r54_handoff_intake=r3)
    )
    assert_p7_r55_bodyfree_forbidden_payload_scan_bodyfree_contract(r4)
    if r4.get("blocked_by_body_free_boundary_risk") is not False:
        raise ValueError("R55 R5 cannot assess actual review gap when R55-4 body-free scan is blocked")
    if r3.get("no_touch_violation_detected") is not False:
        raise ValueError("R55 R5 cannot assess actual review gap when R55-3 no-touch violation is detected")

    material = {
        "schema_version": P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R5_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_actual_review_evidence_gap_assessment", max_length=220),
        "review_session_id": _safe_review_session_id(r3.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r4_bodyfree_forbidden_payload_scan_schema_version": P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION,
        "r4_bodyfree_forbidden_payload_scan_material_ref": clean_identifier(r4.get("material_id"), default="p7_r55_bodyfree_forbidden_payload_scan", max_length=220),
        "r3_r54_handoff_intake_schema_version": P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION,
        "r3_r54_handoff_intake_material_ref": clean_identifier(r3.get("material_id"), default="p7_r55_r54_default_handoff_intake", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "actual_review_evidence_source_ref": "r54_default_handoff_intake_actual_review_evidence_missing",
        "r54_handoff_status": clean_identifier(r3.get("r54_handoff_status"), default=P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF, max_length=180),
        "r54_review_operation_state_ref": clean_identifier(r3.get("r54_review_operation_state_ref"), default=P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF, max_length=180),
        "r54_p5_decision_candidate_ref": clean_identifier(r3.get("r54_p5_decision_candidate_ref"), default=P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF, max_length=180),
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "missing_evidence_refs": list(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "gap_status_ref": P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF,
        "p5_decision_status_ref": P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
        "p5_decision_candidate_ref": P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
        "evidence_missing_classified_as_p5_repair_required": False,
        "evidence_missing_classified_as_p8_material_candidate": False,
        "bodyfree_forbidden_payload_scan_clear": True,
        "blocked_by_body_free_boundary_risk": False,
        "blocked_by_no_touch_violation": False,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": True,
        "implemented_steps": list(P7_R55_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R5_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(material)
    return material


def assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(assessment: Mapping[str, Any]) -> bool:
    data = safe_mapping(assessment)
    _assert_required_fields(
        data,
        required=P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_REQUIRED_FIELD_REFS,
        source="p7_r55_r5_actual_review_evidence_gap_assessment",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION,
        source="p7_r55_r5_actual_review_evidence_gap_assessment",
    )
    if data.get("policy_section") != P7_R55_R5_STEP_REF:
        raise ValueError("R55 R5 policy section changed")
    if data.get("r4_bodyfree_forbidden_payload_scan_schema_version") != P7_R55_BODYFREE_FORBIDDEN_PAYLOAD_SCAN_SCHEMA_VERSION:
        raise ValueError("R55 R5 R4 schema reference changed")
    if data.get("r3_r54_handoff_intake_schema_version") != P7_R55_R54_HANDOFF_INTAKE_SCHEMA_VERSION:
        raise ValueError("R55 R5 R3 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r5_actual_review_evidence_gap_assessment")
    if data.get("actual_review_evidence_source_ref") != "r54_default_handoff_intake_actual_review_evidence_missing":
        raise ValueError("R55 R5 actual review evidence source ref changed")
    if data.get("r54_handoff_status") != P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF:
        raise ValueError("R55 R5 must remain based on R54 actual-review-evidence-missing handoff")
    if data.get("r54_review_operation_state_ref") != P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("R55 R5 default review operation state must remain not_started")
    if data.get("r54_p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R55 R5 R54 P5 candidate must remain P5_NOT_REVIEWED")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R55 R5 required case count changed")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R55 R5 current default must not materialize actual review rows")
    if data.get("disposal_verified") is not False:
        raise ValueError("R55 R5 current default must not verify disposal")
    if tuple(data.get("missing_evidence_refs") or ()) != P7_R55_DEFAULT_MISSING_EVIDENCE_REFS:
        raise ValueError("R55 R5 missing evidence refs changed")
    if data.get("missing_evidence_ref_count") != len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS):
        raise ValueError("R55 R5 missing evidence ref count changed")
    if data.get("gap_status_ref") != P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF:
        raise ValueError("R55 R5 gap status must remain actual review evidence missing")
    if data.get("p5_decision_status_ref") != P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("R55 R5 P5 decision status changed")
    if data.get("p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R55 R5 P5 decision candidate must remain P5_NOT_REVIEWED")
    for false_key in (
        "evidence_missing_classified_as_p5_repair_required",
        "evidence_missing_classified_as_p8_material_candidate",
        "blocked_by_body_free_boundary_risk",
        "blocked_by_no_touch_violation",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R5 must keep {false_key}=False")
    if data.get("bodyfree_forbidden_payload_scan_clear") is not True:
        raise ValueError("R55 R5 requires R55-4 body-free scan clear")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R5 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R5_IMPLEMENTED_STEPS:
        raise ValueError("R55 R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R5 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R5_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R5 must point to R55-6")
    return True



# ---------------------------------------------------------------------------
# R55-6 / R55-7 decision materialization and release separation
# ---------------------------------------------------------------------------

P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.r52_reintake_decision_materialization.bodyfree.v1"
)
P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.p5_p6_p8_release_separation.bodyfree.v1"
)

P7_R55_R6_STEP_REF: Final = "R55-6_r52_reintake_decision_materialization"
P7_R55_R7_STEP_REF: Final = "R55-7_p5_p6_p8_release_separation"
P7_R55_R6_NEXT_IMPLEMENTATION_STEP_REF: Final = P7_R55_R7_STEP_REF
P7_R55_R7_NEXT_IMPLEMENTATION_STEP_REF: Final = "R55-8_final_no_touch_boundary_validation"
P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF: Final = (
    "R54_actual_local_only_human_review_operation_required_before_R52_reintake"
)

P7_R55_R52_REINTAKE_DECISION_REFS: Final[tuple[str, ...]] = (
    "R55_R52_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED",
    "R55_R52_RETURN_TO_P5_REPAIR_REQUIRED",
    "R55_R52_P5_CONFIRMED_CANDIDATE_ONLY",
    "R55_R52_INCONCLUSIVE",
    "R55_BLOCKED_BY_BODY_FREE_BOUNDARY_RISK",
    "R55_BLOCKED_BY_NO_TOUCH_VIOLATION",
    "R55_BLOCKED_BY_CURRENT_SNAPSHOT_UNCLASSIFIED",
    "R55_BLOCKED_BY_VALIDATION_EVIDENCE_INCOMPLETE",
    "R55_BLOCKED_BY_DISPOSAL_SAFETY",
    "R55_R52_NO_GO_P6_P8_START",
)
P7_R55_R52_EXISTING_DECISION_EQUIVALENT_REFS: Final[tuple[str, ...]] = (
    "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED",
    "R52_BLOCKED_BY_R51_EVIDENCE_MISSING",
    "R52_RETURN_TO_P5_REPAIR_REQUIRED",
    "R52_BLOCKED_BY_R51_BODY_FREE_BOUNDARY_RISK",
    "R52_BLOCKED_BY_DISPOSAL_NOT_VERIFIED",
    "R52_BLOCKED_BY_EXECUTION_BLOCKER_OPEN",
    "R52_BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY",
    "R52_INCONCLUSIVE_RETURN_TO_R51_REVIEW_OR_RECHECK",
    "R52_GO_P5_CONFIRMED_CANDIDATE_REVIEWED_BUT_NOT_RELEASE",
    "R52_NO_GO_P6_P8_START",
)
P7_R55_DECISION_STATUS_REFS: Final[tuple[str, ...]] = (
    "NO_GO",
    "BLOCKED",
    "CANDIDATE_ONLY",
    "INCONCLUSIVE",
)
P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF: Final = "R55_R52_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED"
P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF: Final = "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
P7_R55_DEFAULT_R52_EQUIVALENT_REASON_REF: Final = (
    "actual_review_evidence_missing_before_p6_p8_start_decision"
)
P7_R55_DEFAULT_DECISION_STATUS_REF: Final = "NO_GO"
P7_R55_DEFAULT_DECISION_REASON_REFS: Final[tuple[str, ...]] = (
    "r54_r52_reintake_blocked_by_actual_review_evidence_missing",
    "r54_review_operation_state_not_started",
    "p5_actual_human_blind_qa_review_not_completed",
    "question_need_observation_actual_rows_missing",
    "p8_start_hold_by_p7_p8_bridge",
)
P7_R55_P5_P6_P8_RELEASE_SEPARATION_STATUS_REF: Final = (
    "P5_P6_P8_RELEASE_HELD_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
)
P7_R55_CANDIDATE_ONLY_POLICY_REF: Final = (
    "p5_confirmed_candidate_only_does_not_finalize_or_start_p6_p8_or_release_in_r55"
)
P7_R55_P8_MATERIAL_ESCAPE_BLOCKED_REF: Final = (
    "p5_not_reviewed_or_repair_required_must_not_escape_to_p8_question_material"
)

P7_R55_FUTURE_STEPS_AFTER_R7: Final[tuple[str, ...]] = (
    "R55-8_final_no_touch_boundary_validation",
    "R55-9_validation_command_matrix_documentation_output",
    "R55-10_final_summary",
)
P7_R55_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R5_IMPLEMENTED_STEPS,
    P7_R55_R6_STEP_REF,
)
P7_R55_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R55_R7_STEP_REF,
    *P7_R55_FUTURE_STEPS_AFTER_R7,
)
P7_R55_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R6_IMPLEMENTED_STEPS,
    P7_R55_R7_STEP_REF,
)
P7_R55_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R55_FUTURE_STEPS_AFTER_R7

P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "r52_existing_decision_enum_changed_here",
    "r52_existing_decision_enum_extended_here",
    "r52_decision_written_here",
    "r52_reintake_ready_claimed",
    "p5_not_reviewed_reclassified_as_p5_repair_required",
    "p5_not_reviewed_reclassified_as_p5_confirmed_candidate",
    "p5_not_reviewed_reclassified_as_p8_question_material",
    "p5_repair_required_escaped_to_p8_question_material",
    "decision_material_claimed_as_actual_review_completion",
)
P7_R55_P5_P6_P8_RELEASE_SEPARATION_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "p5_candidate_auto_finalization_allowed",
    "p5_candidate_auto_p6_start_allowed",
    "p5_candidate_auto_p8_start_allowed",
    "p5_candidate_auto_release_allowed",
    "actual_review_complete_candidate_only_auto_finalization_allowed",
    "actual_review_complete_candidate_only_auto_p6_p8_start_allowed",
    "actual_review_complete_candidate_only_auto_release_allowed",
    "p5_repair_required_escaped_to_p8_question_material",
    "p5_not_reviewed_escaped_to_p8_question_material",
    "p8_question_design_material_allowed_from_missing_evidence",
    "p8_question_design_material_allowed_from_p5_repair_required",
    "p6_start_allowed_from_target_green_only",
    "release_allowed_from_target_green_only",
)

P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r5_actual_review_evidence_gap_assessment_schema_version",
    "r5_actual_review_evidence_gap_assessment_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "actual_review_evidence_gap_status_ref",
    "r54_handoff_status",
    "r54_review_operation_state_ref",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "missing_evidence_refs",
    "missing_evidence_ref_count",
    "r55_decision_ref",
    "r52_existing_decision_equivalent",
    "r52_equivalent_reason_ref",
    "decision_status",
    "decision_reason_refs",
    "decision_reason_ref_count",
    "next_required_step",
    "r55_next_implementation_step_ref",
    "p5_decision_status_ref",
    "p5_decision_candidate_ref",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "r55_4_bodyfree_forbidden_payload_scan_done",
    "r55_5_actual_review_evidence_gap_assessed",
    "r55_6_r52_reintake_decision_materialized",
    "r55_7_p5_p6_p8_release_separated",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_FALSE_FIELD_REFS,
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

P7_R55_P5_P6_P8_RELEASE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r6_r52_reintake_decision_schema_version",
    "r6_r52_reintake_decision_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "r55_decision_ref",
    "r52_existing_decision_equivalent",
    "decision_status",
    "decision_reason_refs",
    "decision_next_required_step",
    "separation_status_ref",
    "candidate_only_policy_ref",
    "p8_material_escape_blocked_ref",
    "actual_review_evidence_complete",
    "p5_decision_status_ref",
    "p5_decision_candidate_ref",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p5_repair_return_candidate",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "r55_4_bodyfree_forbidden_payload_scan_done",
    "r55_5_actual_review_evidence_gap_assessed",
    "r55_6_r52_reintake_decision_materialized",
    "r55_7_p5_p6_p8_release_separated",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r55_next_implementation_step_ref",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_P5_P6_P8_RELEASE_SEPARATION_FALSE_FIELD_REFS,
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)


def build_p7_r55_r52_reintake_decision_materialization_bodyfree(
    *,
    actual_review_evidence_gap_assessment: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_r52_reintake_decision_materialization_current_default",
) -> dict[str, Any]:
    """Build R55-6 body-free R52 re-intake decision material."""

    r5 = (
        safe_mapping(actual_review_evidence_gap_assessment)
        if actual_review_evidence_gap_assessment is not None
        else build_p7_r55_actual_review_evidence_gap_assessment_bodyfree()
    )
    assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(r5)
    if r5.get("gap_status_ref") != P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF:
        raise ValueError("R55 R6 current default expects actual review evidence missing from R55-5")
    if r5.get("actual_review_evidence_complete") is not False:
        raise ValueError("R55 R6 must not materialize a decision from completed actual review in current default")
    if r5.get("blocked_by_body_free_boundary_risk") is not False or r5.get("blocked_by_no_touch_violation") is not False:
        raise ValueError("R55 R6 cannot materialize R52 re-intake decision from blocked R55-5 material")

    material = {
        "schema_version": P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R6_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_r52_reintake_decision_materialization_current_default", max_length=220),
        "review_session_id": _safe_review_session_id(r5.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r5_actual_review_evidence_gap_assessment_schema_version": P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION,
        "r5_actual_review_evidence_gap_assessment_material_ref": clean_identifier(r5.get("material_id"), default="p7_r55_actual_review_evidence_gap_assessment", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "actual_review_evidence_gap_status_ref": clean_identifier(r5.get("gap_status_ref"), default=P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF, max_length=180),
        "r54_handoff_status": clean_identifier(r5.get("r54_handoff_status"), default=P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF, max_length=180),
        "r54_review_operation_state_ref": clean_identifier(r5.get("r54_review_operation_state_ref"), default=P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF, max_length=180),
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": _int_count(r5.get("rating_row_count")),
        "question_observation_row_count": _int_count(r5.get("question_observation_row_count")),
        "disposal_verified": r5.get("disposal_verified") is True,
        "missing_evidence_refs": list(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "r55_decision_ref": P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF,
        "r52_existing_decision_equivalent": P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF,
        "r52_equivalent_reason_ref": P7_R55_DEFAULT_R52_EQUIVALENT_REASON_REF,
        "decision_status": P7_R55_DEFAULT_DECISION_STATUS_REF,
        "decision_reason_refs": list(P7_R55_DEFAULT_DECISION_REASON_REFS),
        "decision_reason_ref_count": len(P7_R55_DEFAULT_DECISION_REASON_REFS),
        "next_required_step": P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "r55_next_implementation_step_ref": P7_R55_R6_NEXT_IMPLEMENTATION_STEP_REF,
        "p5_decision_status_ref": P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
        "p5_decision_candidate_ref": P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": True,
        "r55_6_r52_reintake_decision_materialized": True,
        "r55_7_p5_p6_p8_release_separated": False,
        "implemented_steps": list(P7_R55_R6_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R6_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **{key: False for key in P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_FALSE_FIELD_REFS},
        **_false_flags(),
    }
    assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(material)
    return material


def assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(decision: Mapping[str, Any]) -> bool:
    data = safe_mapping(decision)
    _assert_required_fields(
        data,
        required=P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_REQUIRED_FIELD_REFS,
        source="p7_r55_r6_r52_reintake_decision_materialization",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
        source="p7_r55_r6_r52_reintake_decision_materialization",
    )
    if data.get("policy_section") != P7_R55_R6_STEP_REF:
        raise ValueError("R55 R6 policy section changed")
    if data.get("r5_actual_review_evidence_gap_assessment_schema_version") != P7_R55_ACTUAL_REVIEW_EVIDENCE_GAP_ASSESSMENT_SCHEMA_VERSION:
        raise ValueError("R55 R6 R5 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r6_r52_reintake_decision_materialization")
    if data.get("actual_review_evidence_gap_status_ref") != P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF:
        raise ValueError("R55 R6 must remain based on actual review evidence missing")
    if data.get("r54_handoff_status") != P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF:
        raise ValueError("R55 R6 R54 handoff status changed")
    if data.get("r54_review_operation_state_ref") != P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("R55 R6 review operation state must remain not_started")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R55 R6 required case count changed")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R55 R6 must not materialize rating or question observation rows")
    if data.get("disposal_verified") is not False:
        raise ValueError("R55 R6 must not verify disposal")
    if tuple(data.get("missing_evidence_refs") or ()) != P7_R55_DEFAULT_MISSING_EVIDENCE_REFS:
        raise ValueError("R55 R6 missing evidence refs changed")
    if data.get("missing_evidence_ref_count") != len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS):
        raise ValueError("R55 R6 missing evidence ref count changed")
    if data.get("r55_decision_ref") != P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("R55 R6 default decision must return to R54 actual review")
    if data.get("r55_decision_ref") not in P7_R55_R52_REINTAKE_DECISION_REFS:
        raise ValueError("R55 R6 unknown R55 decision ref")
    if data.get("r52_existing_decision_equivalent") != P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF:
        raise ValueError("R55 R6 R52 equivalent decision changed")
    if data.get("r52_existing_decision_equivalent") not in P7_R55_R52_EXISTING_DECISION_EQUIVALENT_REFS:
        raise ValueError("R55 R6 unknown R52 existing decision equivalent")
    if data.get("r52_equivalent_reason_ref") != P7_R55_DEFAULT_R52_EQUIVALENT_REASON_REF:
        raise ValueError("R55 R6 R52 equivalent reason changed")
    if data.get("decision_status") != P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("R55 R6 decision status must remain NO_GO")
    if data.get("decision_status") not in P7_R55_DECISION_STATUS_REFS:
        raise ValueError("R55 R6 unknown decision status")
    if tuple(data.get("decision_reason_refs") or ()) != P7_R55_DEFAULT_DECISION_REASON_REFS:
        raise ValueError("R55 R6 decision reason refs changed")
    if data.get("decision_reason_ref_count") != len(P7_R55_DEFAULT_DECISION_REASON_REFS):
        raise ValueError("R55 R6 decision reason count changed")
    if data.get("next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R6 must point the product decision back to R54 actual review")
    if data.get("r55_next_implementation_step_ref") != P7_R55_R6_NEXT_IMPLEMENTATION_STEP_REF:
        raise ValueError("R55 R6 next implementation step must remain R55-7")
    if data.get("p5_decision_status_ref") != P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("R55 R6 P5 decision status changed")
    if data.get("p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R55 R6 P5 candidate must remain P5_NOT_REVIEWED")
    for false_key in P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_FALSE_FIELD_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R6 must keep {false_key}=False")
    for false_key in (
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "r55_7_p5_p6_p8_release_separated",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R6 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
        "r55_6_r52_reintake_decision_materialized",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R6 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R6_IMPLEMENTED_STEPS:
        raise ValueError("R55 R6 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R6_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R6 not-yet steps changed")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 R6 contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r6_r52_reintake_decision_materialization")
    return True


def build_p7_r55_p5_p6_p8_release_separation_bodyfree(
    *,
    r52_reintake_decision_materialization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_p5_p6_p8_release_separation_current_default",
) -> dict[str, Any]:
    """Build R55-7 body-free P5/P6/P8/release separation material."""

    r6 = (
        safe_mapping(r52_reintake_decision_materialization)
        if r52_reintake_decision_materialization is not None
        else build_p7_r55_r52_reintake_decision_materialization_bodyfree()
    )
    assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(r6)
    if r6.get("r55_decision_ref") != P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("R55 R7 current default expects R55 return-to-R54 decision material")

    material = {
        "schema_version": P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R7_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_p5_p6_p8_release_separation_current_default", max_length=220),
        "review_session_id": _safe_review_session_id(r6.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r6_r52_reintake_decision_schema_version": P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
        "r6_r52_reintake_decision_material_ref": clean_identifier(r6.get("material_id"), default="p7_r55_r52_reintake_decision_materialization_current_default", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "r55_decision_ref": clean_identifier(r6.get("r55_decision_ref"), default=P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF, max_length=180),
        "r52_existing_decision_equivalent": clean_identifier(r6.get("r52_existing_decision_equivalent"), default=P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF, max_length=180),
        "decision_status": clean_identifier(r6.get("decision_status"), default=P7_R55_DEFAULT_DECISION_STATUS_REF, max_length=60),
        "decision_reason_refs": list(P7_R55_DEFAULT_DECISION_REASON_REFS),
        "decision_next_required_step": P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "separation_status_ref": P7_R55_P5_P6_P8_RELEASE_SEPARATION_STATUS_REF,
        "candidate_only_policy_ref": P7_R55_CANDIDATE_ONLY_POLICY_REF,
        "p8_material_escape_blocked_ref": P7_R55_P8_MATERIAL_ESCAPE_BLOCKED_REF,
        "actual_review_evidence_complete": False,
        "p5_decision_status_ref": P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
        "p5_decision_candidate_ref": P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_repair_return_candidate": False,
        "p6_limited_human_readfeel_candidate": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": True,
        "r55_6_r52_reintake_decision_materialized": True,
        "r55_7_p5_p6_p8_release_separated": True,
        "implemented_steps": list(P7_R55_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R7_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "r55_next_implementation_step_ref": P7_R55_R7_NEXT_IMPLEMENTATION_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **{key: False for key in P7_R55_P5_P6_P8_RELEASE_SEPARATION_FALSE_FIELD_REFS},
        **_false_flags(),
    }
    # Keep explicitly duplicated separation fields at their intended values after _false_flags().
    material["r55_7_p5_p6_p8_release_separated"] = True
    material["actual_review_evidence_complete"] = False
    material["p5_human_blind_qa_confirmed_candidate"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_repair_return_candidate"] = False
    material["p6_limited_human_readfeel_candidate"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p8_question_design_material_candidate"] = False
    material["p8_start_allowed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(material)
    return material


def assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(separation: Mapping[str, Any]) -> bool:
    data = safe_mapping(separation)
    _assert_required_fields(
        data,
        required=P7_R55_P5_P6_P8_RELEASE_SEPARATION_REQUIRED_FIELD_REFS,
        source="p7_r55_r7_p5_p6_p8_release_separation",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION,
        source="p7_r55_r7_p5_p6_p8_release_separation",
    )
    if data.get("policy_section") != P7_R55_R7_STEP_REF:
        raise ValueError("R55 R7 policy section changed")
    if data.get("r6_r52_reintake_decision_schema_version") != P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION:
        raise ValueError("R55 R7 R6 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r7_p5_p6_p8_release_separation")
    if data.get("r55_decision_ref") != P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("R55 R7 must remain tied to return-to-R54 actual review decision")
    if data.get("r52_existing_decision_equivalent") != P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF:
        raise ValueError("R55 R7 R52 equivalent decision changed")
    if data.get("decision_status") != P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("R55 R7 decision status must remain NO_GO")
    if tuple(data.get("decision_reason_refs") or ()) != P7_R55_DEFAULT_DECISION_REASON_REFS:
        raise ValueError("R55 R7 decision reason refs changed")
    if data.get("decision_next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R7 decision next step must return to R54 actual review")
    if data.get("separation_status_ref") != P7_R55_P5_P6_P8_RELEASE_SEPARATION_STATUS_REF:
        raise ValueError("R55 R7 separation status changed")
    if data.get("candidate_only_policy_ref") != P7_R55_CANDIDATE_ONLY_POLICY_REF:
        raise ValueError("R55 R7 candidate-only policy ref changed")
    if data.get("p8_material_escape_blocked_ref") != P7_R55_P8_MATERIAL_ESCAPE_BLOCKED_REF:
        raise ValueError("R55 R7 P8 material escape blocker changed")
    if data.get("p5_decision_status_ref") != P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("R55 R7 P5 decision status changed")
    if data.get("p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R55 R7 P5 decision candidate must remain P5_NOT_REVIEWED")
    for false_key in P7_R55_P5_P6_P8_RELEASE_SEPARATION_FALSE_FIELD_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R7 must keep {false_key}=False")
    for false_key in (
        "actual_review_evidence_complete",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_human_blind_qa_confirmed_final",
        "p5_repair_return_candidate",
        "p6_limited_human_readfeel_candidate",
        "p6_limited_human_readfeel_start_allowed",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R7 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
        "r55_6_r52_reintake_decision_materialized",
        "r55_7_p5_p6_p8_release_separated",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R7 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R7_IMPLEMENTED_STEPS:
        raise ValueError("R55 R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R7 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R7 product decision next step must remain R54 actual review")
    if data.get("r55_next_implementation_step_ref") != P7_R55_R7_NEXT_IMPLEMENTATION_STEP_REF:
        raise ValueError("R55 R7 next implementation step must remain R55-8")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 R7 contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r7_p5_p6_p8_release_separation")
    return True



# ---------------------------------------------------------------------------
# R55-8 / R55-9 final no-touch validation and command documentation
# ---------------------------------------------------------------------------

P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.final_no_touch_boundary_validation.bodyfree.v1"
)
P7_R55_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.validation_command_matrix_row.bodyfree.v1"
)
P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r55.validation_command_matrix_documentation_output.bodyfree.v1"
)

P7_R55_R8_STEP_REF: Final = "R55-8_final_no_touch_boundary_validation"
P7_R55_R9_STEP_REF: Final = "R55-9_validation_command_matrix_documentation_output"
P7_R55_R10_STEP_REF: Final = "R55-10_final_summary"
P7_R55_R8_NEXT_IMPLEMENTATION_STEP_REF: Final = P7_R55_R9_STEP_REF
P7_R55_R9_NEXT_IMPLEMENTATION_STEP_REF: Final = P7_R55_R10_STEP_REF
P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF: Final = "R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATED"
P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF: Final = "NO_API_DB_RN_RUNTIME_PUBLIC_KEY_OR_QUESTION_TOUCH"
P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF: Final = "R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_BODYFREE"
P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF: Final = "COMMAND_MATRIX_DOCUMENTATION_ONLY_NOT_RESULT_EVIDENCE"
P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF: Final = "R55_GREEN_CLAIM_RULES_KEEP_TARGET_GREEN_SEPARATE_FROM_PRODUCT_READINESS"
P7_R55_R55_TARGET_GREEN_SCOPE_REF: Final = "r55_target_contract_only_not_actual_review_p8_or_release"

P7_R55_FUTURE_STEPS_AFTER_R9: Final[tuple[str, ...]] = (P7_R55_R10_STEP_REF,)
P7_R55_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R7_IMPLEMENTED_STEPS,
    P7_R55_R8_STEP_REF,
)
P7_R55_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R55_R9_STEP_REF,
    *P7_R55_FUTURE_STEPS_AFTER_R9,
)
P7_R55_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R55_R8_IMPLEMENTED_STEPS,
    P7_R55_R9_STEP_REF,
)
P7_R55_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R55_FUTURE_STEPS_AFTER_R9

P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_route_changed_here",
    "request_key_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "db_write_path_changed_here",
    "subscription_boundary_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
    "public_response_key_changed_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "emlis_runtime_changed_here",
    "user_label_connection_runtime_changed_here",
    "gate_threshold_changed_here",
    "public_meta_sanitizer_relaxed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_question_implementation_spec_finalized_here",
)
P7_R55_VALIDATION_COMMAND_MATRIX_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "command_full_text_included",
    "local_absolute_path_included",
    "terminal_output_included",
    "command_full_output_included",
    "timeout_one_shot_claimed_as_green",
    "collect_only_claimed_as_green",
    "rn_contract_green_claimed_as_real_device_modal_readfeel",
    "r55_target_green_claimed_as_actual_review_completion",
    "r55_target_green_claimed_as_p8_start_allowed",
    "r55_target_green_claimed_as_release_allowed",
    "full_backend_suite_green_claimed_here",
    "actual_review_execution_claimed_here",
    "p5_actual_review_completion_claimed_here",
    "p8_start_allowed_claimed_here",
    "release_allowed_claimed_here",
)
P7_R55_COMMAND_MATRIX_GROUP_REFS: Final[tuple[str, ...]] = (
    "r55_helper_py_compile",
    "r55_r0_r3_target_split",
    "r55_r4_r7_target_split",
    "r55_r8_r9_target",
    "r54_regression_split",
    "r52_r53_targeted_regression",
    "rn_no_touch_contract",
)
P7_R55_COMMAND_MATRIX_KIND_REFS: Final[tuple[str, ...]] = (
    "PY_COMPILE",
    "PYTEST_TARGET_SPLIT",
    "PYTEST_TARGET_REGRESSION",
    "RN_CONTRACT",
)
P7_R55_COMMAND_MATRIX_REQUIRED_CLAIM_LEVEL_REFS: Final[tuple[str, ...]] = (
    "PASSED_TARGET",
    "PASSED_SPLIT_TARGET",
)

P7_R55_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "command_group_ref",
    "command_ref",
    "command_kind_ref",
    "command_scope_ref",
    "working_directory_ref",
    "target_file_refs",
    "target_file_ref_count",
    "expected_claim_level_when_passed_ref",
    "green_claim_allowed_if_passed",
    "result_evidence_status_ref",
    "green_claim_scope_ref",
    "command_full_text_included",
    "local_absolute_path_included",
    "terminal_output_included",
    "command_full_output_included",
    "timeout_one_shot_claimed_as_green",
    "collect_only_claimed_as_green",
    "rn_contract_green_claimed_as_real_device_modal_readfeel",
    "r55_target_green_claimed_as_actual_review_completion",
    "r55_target_green_claimed_as_p8_start_allowed",
    "r55_target_green_claimed_as_release_allowed",
    "actual_review_execution_claimed_here",
    "p8_start_allowed_claimed_here",
    "release_allowed_claimed_here",
    "body_free",
)

P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r7_p5_p6_p8_release_separation_schema_version",
    "r7_p5_p6_p8_release_separation_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "r55_decision_ref",
    "r52_existing_decision_equivalent",
    "decision_status",
    "decision_next_required_step",
    "no_touch_boundary_status_ref",
    "no_touch_touched_refs",
    "no_touch_touched_ref_count",
    "no_touch_touched_refs_empty_ref",
    "question_implementation_status_ref",
    "p8_hold_reason_ref",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "r55_4_bodyfree_forbidden_payload_scan_done",
    "r55_5_actual_review_evidence_gap_assessed",
    "r55_6_r52_reintake_decision_materialized",
    "r55_7_p5_p6_p8_release_separated",
    "r55_8_final_no_touch_boundary_validated",
    "r55_9_validation_command_matrix_documented",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r55_next_implementation_step_ref",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS,
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)

P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r8_final_no_touch_boundary_validation_schema_version",
    "r8_final_no_touch_boundary_validation_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "documentation_status_ref",
    "result_evidence_status_ref",
    "green_claim_rule_ref",
    "validation_command_rows",
    "validation_command_row_count",
    "validation_command_group_refs",
    "all_required_command_groups_documented",
    "command_full_text_included",
    "local_absolute_path_included",
    "terminal_output_included",
    "command_full_output_included",
    "timeout_one_shot_claimed_as_green",
    "collect_only_claimed_as_green",
    "rn_contract_green_claimed_as_real_device_modal_readfeel",
    "r55_target_green_claimed_as_actual_review_completion",
    "r55_target_green_claimed_as_p8_start_allowed",
    "r55_target_green_claimed_as_release_allowed",
    "full_backend_suite_green_claimed_here",
    "actual_review_execution_claimed_here",
    "p5_actual_review_completion_claimed_here",
    "p8_start_allowed_claimed_here",
    "release_allowed_claimed_here",
    "r55_0_scope_current_received_snapshot_refrozen",
    "r55_1_prior_helper_source_reconciled",
    "r55_2_validation_evidence_reconciled",
    "r55_3_r54_default_handoff_intake_done",
    "r55_4_bodyfree_forbidden_payload_scan_done",
    "r55_5_actual_review_evidence_gap_assessed",
    "r55_6_r52_reintake_decision_materialized",
    "r55_7_p5_p6_p8_release_separated",
    "r55_8_final_no_touch_boundary_validated",
    "r55_9_validation_command_matrix_documented",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "r55_next_implementation_step_ref",
    "public_contract",
    "r55_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R55_R0_R1_FALSE_KEY_REFS,
)


def _command_matrix_row(
    *,
    command_group_ref: str,
    command_ref: str,
    command_kind_ref: str,
    command_scope_ref: str,
    working_directory_ref: str,
    target_file_refs: Sequence[Any],
    expected_claim_level_when_passed_ref: str,
    green_claim_allowed_if_passed: bool,
    green_claim_scope_ref: str,
) -> dict[str, Any]:
    target_refs = dedupe_identifiers(target_file_refs, limit=20, max_length=240)
    row = {
        "schema_version": P7_R55_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "command_group_ref": clean_identifier(command_group_ref, default="r55_validation_command_group", max_length=120),
        "command_ref": clean_identifier(command_ref, default="r55_validation_command", max_length=220),
        "command_kind_ref": clean_identifier(command_kind_ref, default="PYTEST_TARGET_SPLIT", max_length=80),
        "command_scope_ref": clean_identifier(command_scope_ref, default="target_contract_only", max_length=220),
        "working_directory_ref": clean_identifier(working_directory_ref, default="mashos_api_ai_root", max_length=160),
        "target_file_refs": target_refs,
        "target_file_ref_count": len(target_refs),
        "expected_claim_level_when_passed_ref": clean_identifier(expected_claim_level_when_passed_ref, default="PASSED_TARGET", max_length=80),
        "green_claim_allowed_if_passed": bool(green_claim_allowed_if_passed),
        "result_evidence_status_ref": P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF,
        "green_claim_scope_ref": clean_identifier(green_claim_scope_ref, default=P7_R55_R55_TARGET_GREEN_SCOPE_REF, max_length=220),
        "command_full_text_included": False,
        "local_absolute_path_included": False,
        "terminal_output_included": False,
        "command_full_output_included": False,
        "timeout_one_shot_claimed_as_green": False,
        "collect_only_claimed_as_green": False,
        "rn_contract_green_claimed_as_real_device_modal_readfeel": False,
        "r55_target_green_claimed_as_actual_review_completion": False,
        "r55_target_green_claimed_as_p8_start_allowed": False,
        "r55_target_green_claimed_as_release_allowed": False,
        "actual_review_execution_claimed_here": False,
        "p8_start_allowed_claimed_here": False,
        "release_allowed_claimed_here": False,
        "body_free": True,
    }
    assert_p7_r55_validation_command_matrix_row_bodyfree_contract(row)
    return row


def _default_validation_command_matrix_rows() -> list[dict[str, Any]]:
    return [
        _command_matrix_row(
            command_group_ref="r55_helper_py_compile",
            command_ref="py_compile_r55_helper",
            command_kind_ref="PY_COMPILE",
            command_scope_ref="r55_helper_syntax_import_only",
            working_directory_ref="mashos_api_ai_root",
            target_file_refs=(
                "services/ai_inference/emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization.py",
            ),
            expected_claim_level_when_passed_ref="PASSED_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="helper_syntax_import_only",
        ),
        _command_matrix_row(
            command_group_ref="r55_r0_r3_target_split",
            command_ref="pytest_r55_r0_r1_r2_r3_target_split",
            command_kind_ref="PYTEST_TARGET_SPLIT",
            command_scope_ref="r55_r0_to_r3_target_contract_only",
            working_directory_ref="mashos_api_ai_root",
            target_file_refs=(
                "tests/test_emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization_r0_r1_20260623.py",
                "tests/test_emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization_r2_r3_20260623.py",
            ),
            expected_claim_level_when_passed_ref="PASSED_SPLIT_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="r55_target_contract_only_not_actual_review_completion",
        ),
        _command_matrix_row(
            command_group_ref="r55_r4_r7_target_split",
            command_ref="pytest_r55_r4_r5_r6_r7_target_split",
            command_kind_ref="PYTEST_TARGET_SPLIT",
            command_scope_ref="r55_r4_to_r7_target_contract_only",
            working_directory_ref="mashos_api_ai_root",
            target_file_refs=(
                "tests/test_emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization_r4_r5_20260623.py",
                "tests/test_emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization_r6_r7_20260623.py",
            ),
            expected_claim_level_when_passed_ref="PASSED_SPLIT_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="r55_target_contract_only_not_p8_or_release",
        ),
        _command_matrix_row(
            command_group_ref="r55_r8_r9_target",
            command_ref="pytest_r55_r8_r9_target",
            command_kind_ref="PYTEST_TARGET_SPLIT",
            command_scope_ref="r55_r8_r9_target_contract_only",
            working_directory_ref="mashos_api_ai_root",
            target_file_refs=(
                "tests/test_emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization_r8_r9_20260623.py",
            ),
            expected_claim_level_when_passed_ref="PASSED_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="r55_r8_r9_target_contract_only_not_actual_review_completion",
        ),
        _command_matrix_row(
            command_group_ref="r54_regression_split",
            command_ref="pytest_r54_result_handoff_regression_split",
            command_kind_ref="PYTEST_TARGET_REGRESSION",
            command_scope_ref="r54_regression_contract_only_not_p5_actual_review_completion",
            working_directory_ref="mashos_api_ai_root",
            target_file_refs=(
                "tests/test_emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff_*.py",
            ),
            expected_claim_level_when_passed_ref="PASSED_SPLIT_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="r54_regression_only_not_actual_review_completion",
        ),
        _command_matrix_row(
            command_group_ref="r52_r53_targeted_regression",
            command_ref="pytest_r52_r53_targeted_regression",
            command_kind_ref="PYTEST_TARGET_REGRESSION",
            command_scope_ref="r52_r53_regression_contract_only_not_p6_p8_start",
            working_directory_ref="mashos_api_ai_root",
            target_file_refs=(
                "tests/test_emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate_*.py",
                "tests/test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_*.py",
            ),
            expected_claim_level_when_passed_ref="PASSED_SPLIT_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="r52_r53_regression_only_not_p6_p8_start",
        ),
        _command_matrix_row(
            command_group_ref="rn_no_touch_contract",
            command_ref="npm_run_test_rn_screens_silent",
            command_kind_ref="RN_CONTRACT",
            command_scope_ref="rn_visible_contract_only_not_real_device_modal_readfeel",
            working_directory_ref="cocolon_rn_root",
            target_file_refs=(
                "Cocolon/tests/rn-screen-contracts.test.js",
            ),
            expected_claim_level_when_passed_ref="PASSED_TARGET",
            green_claim_allowed_if_passed=True,
            green_claim_scope_ref="rn_visible_contract_only_not_real_device_modal_readfeel",
        ),
    ]


def assert_p7_r55_validation_command_matrix_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R55_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS,
        source="p7_r55_r9_validation_command_matrix_row",
    )
    if data.get("schema_version") != P7_R55_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION:
        raise ValueError("R55 R9 command matrix row schema version changed")
    if data.get("command_group_ref") not in P7_R55_COMMAND_MATRIX_GROUP_REFS:
        raise ValueError("R55 R9 command matrix row group ref changed")
    if data.get("command_kind_ref") not in P7_R55_COMMAND_MATRIX_KIND_REFS:
        raise ValueError("R55 R9 command matrix row kind changed")
    if data.get("expected_claim_level_when_passed_ref") not in P7_R55_COMMAND_MATRIX_REQUIRED_CLAIM_LEVEL_REFS:
        raise ValueError("R55 R9 command matrix row claim level changed")
    if data.get("result_evidence_status_ref") != P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF:
        raise ValueError("R55 R9 command matrix row must remain documentation-only, not result evidence")
    if data.get("body_free") is not True:
        raise ValueError("R55 R9 command matrix row must be body-free")
    if not data.get("target_file_refs") or data.get("target_file_ref_count") != len(data.get("target_file_refs") or ()):  # type: ignore[arg-type]
        raise ValueError("R55 R9 command matrix row target refs changed")
    for false_key in (
        "command_full_text_included",
        "local_absolute_path_included",
        "terminal_output_included",
        "command_full_output_included",
        "timeout_one_shot_claimed_as_green",
        "collect_only_claimed_as_green",
        "rn_contract_green_claimed_as_real_device_modal_readfeel",
        "r55_target_green_claimed_as_actual_review_completion",
        "r55_target_green_claimed_as_p8_start_allowed",
        "r55_target_green_claimed_as_release_allowed",
        "actual_review_execution_claimed_here",
        "p8_start_allowed_claimed_here",
        "release_allowed_claimed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R9 command matrix row must keep {false_key}=False")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 R9 command matrix row contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r9_validation_command_matrix_row")
    return True


def build_p7_r55_final_no_touch_boundary_validation_bodyfree(
    *,
    p5_p6_p8_release_separation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_final_no_touch_boundary_validation",
) -> dict[str, Any]:
    """Build R55-8 body-free final no-touch boundary validation material."""

    r7 = (
        safe_mapping(p5_p6_p8_release_separation)
        if p5_p6_p8_release_separation is not None
        else build_p7_r55_p5_p6_p8_release_separation_bodyfree()
    )
    assert_p7_r55_p5_p6_p8_release_separation_bodyfree_contract(r7)
    if r7.get("r55_next_implementation_step_ref") != P7_R55_R8_STEP_REF:
        raise ValueError("R55 R8 expects R55-7 material to point to final no-touch boundary validation")

    material = {
        "schema_version": P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R8_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_final_no_touch_boundary_validation", max_length=220),
        "review_session_id": _safe_review_session_id(r7.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r7_p5_p6_p8_release_separation_schema_version": P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION,
        "r7_p5_p6_p8_release_separation_material_ref": clean_identifier(r7.get("material_id"), default="p7_r55_p5_p6_p8_release_separation_current_default", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "r55_decision_ref": clean_identifier(r7.get("r55_decision_ref"), default=P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF, max_length=180),
        "r52_existing_decision_equivalent": clean_identifier(r7.get("r52_existing_decision_equivalent"), default=P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF, max_length=180),
        "decision_status": clean_identifier(r7.get("decision_status"), default=P7_R55_DEFAULT_DECISION_STATUS_REF, max_length=60),
        "decision_next_required_step": clean_identifier(r7.get("decision_next_required_step"), default=P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF, max_length=220),
        "no_touch_boundary_status_ref": P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF,
        "no_touch_touched_refs": [],
        "no_touch_touched_ref_count": 0,
        "no_touch_touched_refs_empty_ref": P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF,
        "question_implementation_status_ref": "P8_QUESTION_IMPLEMENTATION_NOT_STARTED_IN_R55",
        "p8_hold_reason_ref": "P8_HOLD_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_AND_P7_P8_BRIDGE",
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": True,
        "r55_6_r52_reintake_decision_materialized": True,
        "r55_7_p5_p6_p8_release_separated": True,
        "r55_8_final_no_touch_boundary_validated": True,
        "r55_9_validation_command_matrix_documented": False,
        "implemented_steps": list(P7_R55_R8_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R8_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "r55_next_implementation_step_ref": P7_R55_R8_NEXT_IMPLEMENTATION_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **{key: False for key in P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS},
        **_false_flags(),
    }
    material["r55_8_final_no_touch_boundary_validated"] = True
    material["r55_9_validation_command_matrix_documented"] = False
    assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(material)
    return material


def assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(validation: Mapping[str, Any]) -> bool:
    data = safe_mapping(validation)
    _assert_required_fields(
        data,
        required=P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_REQUIRED_FIELD_REFS,
        source="p7_r55_r8_final_no_touch_boundary_validation",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        source="p7_r55_r8_final_no_touch_boundary_validation",
    )
    if data.get("policy_section") != P7_R55_R8_STEP_REF:
        raise ValueError("R55 R8 policy section changed")
    if data.get("r7_p5_p6_p8_release_separation_schema_version") != P7_R55_P5_P6_P8_RELEASE_SEPARATION_SCHEMA_VERSION:
        raise ValueError("R55 R8 R7 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r8_final_no_touch_boundary_validation")
    if data.get("r55_decision_ref") != P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("R55 R8 must remain tied to return-to-R54 actual review decision")
    if data.get("r52_existing_decision_equivalent") != P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF:
        raise ValueError("R55 R8 R52 equivalent changed")
    if data.get("decision_status") != P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("R55 R8 decision status must remain NO_GO")
    if data.get("decision_next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R8 decision next step must stay R54 actual review")
    if data.get("no_touch_boundary_status_ref") != P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF:
        raise ValueError("R55 R8 no-touch status changed")
    if data.get("no_touch_touched_refs") != [] or data.get("no_touch_touched_ref_count") != 0:
        raise ValueError("R55 R8 must keep touched refs empty")
    if data.get("no_touch_touched_refs_empty_ref") != P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF:
        raise ValueError("R55 R8 touched refs empty marker changed")
    if data.get("question_implementation_status_ref") != "P8_QUESTION_IMPLEMENTATION_NOT_STARTED_IN_R55":
        raise ValueError("R55 R8 question implementation status changed")
    if data.get("p8_hold_reason_ref") != "P8_HOLD_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_AND_P7_P8_BRIDGE":
        raise ValueError("R55 R8 P8 hold reason changed")
    for false_key in P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R8 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
        "r55_6_r52_reintake_decision_materialized",
        "r55_7_p5_p6_p8_release_separated",
        "r55_8_final_no_touch_boundary_validated",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R8 must keep {true_key}=True")
    if data.get("r55_9_validation_command_matrix_documented") is not False:
        raise ValueError("R55 R8 must not claim R55-9")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R8_IMPLEMENTED_STEPS:
        raise ValueError("R55 R8 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R8_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R8 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R8 product next step must remain R54 actual review")
    if data.get("r55_next_implementation_step_ref") != P7_R55_R8_NEXT_IMPLEMENTATION_STEP_REF:
        raise ValueError("R55 R8 next implementation step must remain R55-9")
    return True


def build_p7_r55_validation_command_matrix_bodyfree(
    *,
    final_no_touch_boundary_validation: Mapping[str, Any] | None = None,
    validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    material_id: Any = "p7_r55_validation_command_matrix_documentation_output",
) -> dict[str, Any]:
    """Build R55-9 body-free validation command matrix / documentation output."""

    r8 = (
        safe_mapping(final_no_touch_boundary_validation)
        if final_no_touch_boundary_validation is not None
        else build_p7_r55_final_no_touch_boundary_validation_bodyfree()
    )
    assert_p7_r55_final_no_touch_boundary_validation_bodyfree_contract(r8)
    rows = [safe_mapping(row) for row in validation_command_rows] if validation_command_rows is not None else _default_validation_command_matrix_rows()
    for row in rows:
        assert_p7_r55_validation_command_matrix_row_bodyfree_contract(row)
    row_groups = [str(row.get("command_group_ref")) for row in rows]
    material = {
        "schema_version": P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R9_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_validation_command_matrix_documentation_output", max_length=220),
        "review_session_id": _safe_review_session_id(r8.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r8_final_no_touch_boundary_validation_schema_version": P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        "r8_final_no_touch_boundary_validation_material_ref": clean_identifier(r8.get("material_id"), default="p7_r55_final_no_touch_boundary_validation", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "documentation_status_ref": P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF,
        "result_evidence_status_ref": P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF,
        "green_claim_rule_ref": P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF,
        "validation_command_rows": rows,
        "validation_command_row_count": len(rows),
        "validation_command_group_refs": list(P7_R55_COMMAND_MATRIX_GROUP_REFS),
        "all_required_command_groups_documented": tuple(row_groups) == P7_R55_COMMAND_MATRIX_GROUP_REFS,
        "command_full_text_included": False,
        "local_absolute_path_included": False,
        "terminal_output_included": False,
        "command_full_output_included": False,
        "timeout_one_shot_claimed_as_green": False,
        "collect_only_claimed_as_green": False,
        "rn_contract_green_claimed_as_real_device_modal_readfeel": False,
        "r55_target_green_claimed_as_actual_review_completion": False,
        "r55_target_green_claimed_as_p8_start_allowed": False,
        "r55_target_green_claimed_as_release_allowed": False,
        "full_backend_suite_green_claimed_here": False,
        "actual_review_execution_claimed_here": False,
        "p5_actual_review_completion_claimed_here": False,
        "p8_start_allowed_claimed_here": False,
        "release_allowed_claimed_here": False,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": True,
        "r55_6_r52_reintake_decision_materialized": True,
        "r55_7_p5_p6_p8_release_separated": True,
        "r55_8_final_no_touch_boundary_validated": True,
        "r55_9_validation_command_matrix_documented": True,
        "implemented_steps": list(P7_R55_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "r55_next_implementation_step_ref": P7_R55_R9_NEXT_IMPLEMENTATION_STEP_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    material["r55_8_final_no_touch_boundary_validated"] = True
    material["r55_9_validation_command_matrix_documented"] = True
    assert_p7_r55_validation_command_matrix_bodyfree_contract(material)
    return material


def assert_p7_r55_validation_command_matrix_bodyfree_contract(matrix: Mapping[str, Any]) -> bool:
    data = safe_mapping(matrix)
    _assert_required_fields(
        data,
        required=P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS,
        source="p7_r55_r9_validation_command_matrix_documentation_output",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        source="p7_r55_r9_validation_command_matrix_documentation_output",
    )
    if data.get("policy_section") != P7_R55_R9_STEP_REF:
        raise ValueError("R55 R9 policy section changed")
    if data.get("r8_final_no_touch_boundary_validation_schema_version") != P7_R55_FINAL_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION:
        raise ValueError("R55 R9 R8 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r9_validation_command_matrix_documentation_output")
    if data.get("documentation_status_ref") != P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF:
        raise ValueError("R55 R9 documentation status changed")
    if data.get("result_evidence_status_ref") != P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF:
        raise ValueError("R55 R9 must not treat command matrix as run result evidence")
    if data.get("green_claim_rule_ref") != P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF:
        raise ValueError("R55 R9 green claim rule changed")
    rows = [safe_mapping(row) for row in data.get("validation_command_rows") or ()]
    for row in rows:
        assert_p7_r55_validation_command_matrix_row_bodyfree_contract(row)
    if data.get("validation_command_row_count") != len(rows):
        raise ValueError("R55 R9 command row count changed")
    if tuple(data.get("validation_command_group_refs") or ()) != P7_R55_COMMAND_MATRIX_GROUP_REFS:
        raise ValueError("R55 R9 command group refs changed")
    if tuple(row.get("command_group_ref") for row in rows) != P7_R55_COMMAND_MATRIX_GROUP_REFS:
        raise ValueError("R55 R9 command rows must document every required group in order")
    if data.get("all_required_command_groups_documented") is not True:
        raise ValueError("R55 R9 must document all required command groups")
    for false_key in P7_R55_VALIDATION_COMMAND_MATRIX_FALSE_FIELD_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R9 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
        "r55_6_r52_reintake_decision_materialized",
        "r55_7_p5_p6_p8_release_separated",
        "r55_8_final_no_touch_boundary_validated",
        "r55_9_validation_command_matrix_documented",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R9 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R9_IMPLEMENTED_STEPS:
        raise ValueError("R55 R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R9 not-yet steps changed")
    if data.get("next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R55 R9 product next step must remain R54 actual review")
    if data.get("r55_next_implementation_step_ref") != P7_R55_R9_NEXT_IMPLEMENTATION_STEP_REF:
        raise ValueError("R55 R9 next implementation step must remain R55-10")
    return True


# ---------------------------------------------------------------------------
# R55-10 final summary
# ---------------------------------------------------------------------------

P7_R55_FINAL_SUMMARY_SCHEMA_VERSION: Final = "cocolon.emlis.p7_r55.final_summary.bodyfree.v1"
P7_R55_FINAL_SUMMARY_READY_REF: Final = "R55_FINAL_SUMMARY_READY"
P7_R55_FINAL_SUMMARY_STATUS_REF: Final = P7_R55_FINAL_SUMMARY_READY_REF
P7_R55_FINAL_SUMMARY_SCOPE_REF: Final = "r55_bodyfree_decision_summary_only"
P7_R55_R10_NEXT_IMPLEMENTATION_STEP_REF: Final = "R55_IMPLEMENTATION_COMPLETE_NO_NEXT_R55_STEP"
P7_R55_FINAL_SUMMARY_NEXT_IMPLEMENTATION_STEP_REF: Final = P7_R55_R10_NEXT_IMPLEMENTATION_STEP_REF
P7_R55_FINAL_DECISION_SUMMARY_REF: Final = "R55_FINAL_DECISION_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED"
P7_R55_FINAL_NO_PROMOTION_POLICY_REF: Final = "R55_FINAL_SUMMARY_BODYFREE_NO_PRODUCT_PROMOTION"
P7_R55_FINAL_P6_HOLD_REASON_REF: Final = "P6_HOLD_BY_P5_ACTUAL_REVIEW_EVIDENCE_MISSING"
P7_R55_FINAL_P8_HOLD_REASON_REF: Final = "P8_HOLD_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_AND_P7_P8_BRIDGE"
P7_R55_FINAL_RELEASE_HOLD_REASON_REF: Final = "RELEASE_HOLD_BY_P5_P6_P8_AND_FULL_BACKEND_UNCONFIRMED"
P7_R55_FINAL_QUESTION_IMPLEMENTATION_STATUS_REF: Final = "P8_QUESTION_IMPLEMENTATION_NOT_STARTED_IN_R55"

P7_R55_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R55_R9_IMPLEMENTED_STEPS, P7_R55_R10_STEP_REF)
P7_R55_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R55_FINAL_SUMMARY_REASON_REFS: Final[tuple[str, ...]] = (
    "current_received_snapshot_refrozen_as_r55_work_basis",
    "prior_helper_refs_classified_as_historical_regression_context",
    "validation_evidence_claim_levels_reconciled_without_product_promotion",
    "r54_default_handoff_intaken_as_actual_review_evidence_missing",
    "bodyfree_forbidden_payload_scan_clear",
    "actual_review_evidence_gap_assessed_as_missing",
    "r52_reintake_decision_materialized_as_return_to_r54_actual_review_required",
    "p5_p6_p8_release_separation_preserved",
    "final_no_touch_boundary_validated",
    "validation_command_matrix_documented_without_run_result_claim",
)
P7_R55_FINAL_SUMMARY_HOLD_REASON_REFS: Final[tuple[str, ...]] = (
    P7_R55_FINAL_P6_HOLD_REASON_REF,
    P7_R55_FINAL_P8_HOLD_REASON_REF,
    P7_R55_FINAL_RELEASE_HOLD_REASON_REF,
)
P7_R55_FINAL_SUMMARY_VALIDATION_LIMITATION_REFS: Final[tuple[str, ...]] = (
    "r55_target_green_is_contract_only_not_actual_review_completion",
    "command_matrix_is_documentation_only_not_result_evidence",
    "full_backend_suite_green_not_confirmed_here",
    "rn_contract_green_is_not_real_device_modal_readfeel",
    "p5_actual_human_blind_qa_review_not_executed_here",
    "question_need_observation_actual_rows_missing",
)
P7_R55_FINAL_SUMMARY_RECOMMENDED_NEXT_WORK_REFS: Final[tuple[str, ...]] = (
    "run_R54_actual_local_only_human_review_operation_before_R52_reintake",
    "keep_P6_limited_human_readfeel_start_on_hold",
    "keep_P8_question_design_on_hold_until_question_need_observation_rows_exist",
    "keep_release_and_P7_completion_closed",
)

P7_R55_FINAL_SUMMARY_FALSE_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *P7_R55_FINAL_NO_TOUCH_BOUNDARY_FLAG_REFS,
            *P7_R55_VALIDATION_COMMAND_MATRIX_FALSE_FIELD_REFS,
            *P7_R55_R0_R1_FALSE_KEY_REFS,
            "full_backend_suite_green_confirmed",
            "full_backend_suite_green_claimed_here",
            "rn_real_device_modal_readfeel_confirmed",
            "p5_actual_human_blind_qa_review_completed",
            "p8_question_design_started_here",
            "p8_question_design_material_ready",
            "release_ready_claimed_here",
            "final_summary_claimed_as_actual_review_completion",
            "final_summary_claimed_as_p5_confirmed_final",
            "final_summary_claimed_as_p6_start_allowed",
            "final_summary_claimed_as_p8_start_allowed",
            "final_summary_claimed_as_p7_complete",
            "final_summary_claimed_as_release_allowed",
        )
    )
)

P7_R55_FINAL_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            "schema_version",
            "phase",
            "step",
            "scope",
            "policy_kind",
            "policy_section",
            "current_phase",
            "material_id",
            "review_session_id",
            "source_mode",
            "git_connection_required",
            "git_checked",
            "r9_validation_command_matrix_schema_version",
            "r9_validation_command_matrix_material_ref",
            "current_received_snapshot_refs",
            "current_received_snapshot_ref_count",
            "actual_review_basis_ref",
            "actual_review_basis_allowed",
            "final_status",
            "final_status_ref",
            "final_summary_scope_ref",
            "final_decision_summary_ref",
            "final_no_promotion_policy_ref",
            "r55_decision_ref",
            "r52_existing_decision_equivalent",
            "r52_equivalent_reason_ref",
            "decision_status",
            "decision_reason_refs",
            "decision_reason_ref_count",
            "next_required_step",
            "r55_next_implementation_step_ref",
            "recommended_next_work_refs",
            "recommended_next_work_ref_count",
            "hold_reason_refs",
            "hold_reason_ref_count",
            "summary_reason_refs",
            "summary_reason_ref_count",
            "validation_limitation_refs",
            "validation_limitation_ref_count",
            "actual_review_evidence_complete",
            "actual_review_evidence_gap_status_ref",
            "required_case_count",
            "rating_row_count",
            "question_observation_row_count",
            "disposal_verified",
            "missing_evidence_refs",
            "missing_evidence_ref_count",
            "p5_decision_status_ref",
            "p5_decision_candidate_ref",
            "p5_human_blind_qa_confirmed_final",
            "p6_hold",
            "p6_hold_reason_ref",
            "p6_limited_human_readfeel_start_allowed",
            "p8_hold",
            "p8_hold_reason_ref",
            "p8_question_design_material_candidate",
            "p8_start_allowed",
            "release_hold",
            "release_hold_reason_ref",
            "p7_complete",
            "release_allowed",
            "validation_documentation_status_ref",
            "validation_result_evidence_status_ref",
            "green_claim_rule_ref",
            "validation_command_row_count",
            "full_backend_suite_green_confirmed",
            "rn_real_device_modal_readfeel_confirmed",
            "question_implementation_status_ref",
            "no_touch_boundary_status_ref",
            "no_touch_touched_refs",
            "no_touch_touched_ref_count",
            "no_touch_touched_refs_empty_ref",
            "r55_0_scope_current_received_snapshot_refrozen",
            "r55_1_prior_helper_source_reconciled",
            "r55_2_validation_evidence_reconciled",
            "r55_3_r54_default_handoff_intake_done",
            "r55_4_bodyfree_forbidden_payload_scan_done",
            "r55_5_actual_review_evidence_gap_assessed",
            "r55_6_r52_reintake_decision_materialized",
            "r55_7_p5_p6_p8_release_separated",
            "r55_8_final_no_touch_boundary_validated",
            "r55_9_validation_command_matrix_documented",
            "r55_10_final_summary_ready",
            "implemented_steps",
            "not_yet_implemented_steps",
            "first_next_work_ref",
            "public_contract",
            "r55_public_no_touch_contract",
            "body_free_markers",
            "body_free",
            *P7_R55_FINAL_SUMMARY_FALSE_FIELD_REFS,
        )
    )
)


def build_p7_r55_final_summary_bodyfree(
    *,
    validation_command_matrix: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r55_final_summary_current_default",
) -> dict[str, Any]:
    """Build R55-10 body-free final summary material for next-step judgment."""

    r9 = safe_mapping(validation_command_matrix) if validation_command_matrix is not None else build_p7_r55_validation_command_matrix_bodyfree()
    assert_p7_r55_validation_command_matrix_bodyfree_contract(r9)
    if r9.get("r55_next_implementation_step_ref") != P7_R55_R10_STEP_REF:
        raise ValueError("R55 R10 expects R55-9 material to point to final summary")

    material = {
        "schema_version": P7_R55_FINAL_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R55_STEP,
        "scope": P7_R55_SCOPE,
        "policy_kind": P7_R55_POLICY_KIND,
        "policy_section": P7_R55_R10_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r55_final_summary_current_default", max_length=220),
        "review_session_id": _safe_review_session_id(r9.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r9_validation_command_matrix_schema_version": P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "r9_validation_command_matrix_material_ref": clean_identifier(r9.get("material_id"), default="p7_r55_validation_command_matrix_documentation_output", max_length=220),
        "current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "final_status": P7_R55_FINAL_SUMMARY_READY_REF,
        "final_status_ref": P7_R55_FINAL_SUMMARY_STATUS_REF,
        "final_summary_scope_ref": P7_R55_FINAL_SUMMARY_SCOPE_REF,
        "final_decision_summary_ref": P7_R55_FINAL_DECISION_SUMMARY_REF,
        "final_no_promotion_policy_ref": P7_R55_FINAL_NO_PROMOTION_POLICY_REF,
        "r55_decision_ref": P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF,
        "r52_existing_decision_equivalent": P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF,
        "r52_equivalent_reason_ref": P7_R55_DEFAULT_R52_EQUIVALENT_REASON_REF,
        "decision_status": P7_R55_DEFAULT_DECISION_STATUS_REF,
        "decision_reason_refs": list(P7_R55_DEFAULT_DECISION_REASON_REFS),
        "decision_reason_ref_count": len(P7_R55_DEFAULT_DECISION_REASON_REFS),
        "next_required_step": P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
        "r55_next_implementation_step_ref": P7_R55_R10_NEXT_IMPLEMENTATION_STEP_REF,
        "recommended_next_work_refs": list(P7_R55_FINAL_SUMMARY_RECOMMENDED_NEXT_WORK_REFS),
        "recommended_next_work_ref_count": len(P7_R55_FINAL_SUMMARY_RECOMMENDED_NEXT_WORK_REFS),
        "hold_reason_refs": list(P7_R55_FINAL_SUMMARY_HOLD_REASON_REFS),
        "hold_reason_ref_count": len(P7_R55_FINAL_SUMMARY_HOLD_REASON_REFS),
        "summary_reason_refs": list(P7_R55_FINAL_SUMMARY_REASON_REFS),
        "summary_reason_ref_count": len(P7_R55_FINAL_SUMMARY_REASON_REFS),
        "validation_limitation_refs": list(P7_R55_FINAL_SUMMARY_VALIDATION_LIMITATION_REFS),
        "validation_limitation_ref_count": len(P7_R55_FINAL_SUMMARY_VALIDATION_LIMITATION_REFS),
        "actual_review_evidence_complete": False,
        "actual_review_evidence_gap_status_ref": P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "missing_evidence_refs": list(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "p5_decision_status_ref": P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
        "p5_decision_candidate_ref": P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_hold": True,
        "p6_hold_reason_ref": P7_R55_FINAL_P6_HOLD_REASON_REF,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_hold": True,
        "p8_hold_reason_ref": P7_R55_FINAL_P8_HOLD_REASON_REF,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "release_hold": True,
        "release_hold_reason_ref": P7_R55_FINAL_RELEASE_HOLD_REASON_REF,
        "p7_complete": False,
        "release_allowed": False,
        "validation_documentation_status_ref": P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF,
        "validation_result_evidence_status_ref": P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF,
        "green_claim_rule_ref": P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF,
        "validation_command_row_count": int(r9.get("validation_command_row_count") or 0),
        "full_backend_suite_green_confirmed": False,
        "rn_real_device_modal_readfeel_confirmed": False,
        "question_implementation_status_ref": P7_R55_FINAL_QUESTION_IMPLEMENTATION_STATUS_REF,
        "no_touch_boundary_status_ref": P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF,
        "no_touch_touched_refs": [],
        "no_touch_touched_ref_count": 0,
        "no_touch_touched_refs_empty_ref": P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF,
        "r55_0_scope_current_received_snapshot_refrozen": True,
        "r55_1_prior_helper_source_reconciled": True,
        "r55_2_validation_evidence_reconciled": True,
        "r55_3_r54_default_handoff_intake_done": True,
        "r55_4_bodyfree_forbidden_payload_scan_done": True,
        "r55_5_actual_review_evidence_gap_assessed": True,
        "r55_6_r52_reintake_decision_materialized": True,
        "r55_7_p5_p6_p8_release_separated": True,
        "r55_8_final_no_touch_boundary_validated": True,
        "r55_9_validation_command_matrix_documented": True,
        "r55_10_final_summary_ready": True,
        "implemented_steps": list(P7_R55_R10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R55_R10_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R55_FIRST_NEXT_WORK_REF,
        "public_contract": public_contract_flags(),
        "r55_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **{key: False for key in P7_R55_FINAL_SUMMARY_FALSE_FIELD_REFS},
    }
    # Preserve explicit true summary/hold markers after false-field expansion.
    material["p6_hold"] = True
    material["p8_hold"] = True
    material["release_hold"] = True
    material["r55_10_final_summary_ready"] = True
    assert_p7_r55_final_summary_bodyfree_contract(material)
    return material


def assert_p7_r55_final_summary_bodyfree_contract(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    _assert_required_fields(data, required=P7_R55_FINAL_SUMMARY_REQUIRED_FIELD_REFS, source="p7_r55_r10_final_summary")
    _assert_body_free_common(data, schema_version=P7_R55_FINAL_SUMMARY_SCHEMA_VERSION, source="p7_r55_r10_final_summary")
    if data.get("policy_section") != P7_R55_R10_STEP_REF:
        raise ValueError("R55 R10 policy section changed")
    if data.get("r9_validation_command_matrix_schema_version") != P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION:
        raise ValueError("R55 R10 R9 schema reference changed")
    _assert_current_refs(data, source="p7_r55_r10_final_summary")
    expected_pairs = (
        ("final_status", P7_R55_FINAL_SUMMARY_READY_REF),
        ("final_status_ref", P7_R55_FINAL_SUMMARY_STATUS_REF),
        ("final_summary_scope_ref", P7_R55_FINAL_SUMMARY_SCOPE_REF),
        ("final_decision_summary_ref", P7_R55_FINAL_DECISION_SUMMARY_REF),
        ("final_no_promotion_policy_ref", P7_R55_FINAL_NO_PROMOTION_POLICY_REF),
        ("r55_decision_ref", P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF),
        ("r52_existing_decision_equivalent", P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF),
        ("r52_equivalent_reason_ref", P7_R55_DEFAULT_R52_EQUIVALENT_REASON_REF),
        ("decision_status", P7_R55_DEFAULT_DECISION_STATUS_REF),
        ("next_required_step", P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF),
        ("r55_next_implementation_step_ref", P7_R55_R10_NEXT_IMPLEMENTATION_STEP_REF),
        ("actual_review_evidence_gap_status_ref", P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF),
        ("p5_decision_status_ref", P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF),
        ("p5_decision_candidate_ref", P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF),
        ("validation_documentation_status_ref", P7_R55_VALIDATION_COMMAND_MATRIX_DOCUMENTED_REF),
        ("validation_result_evidence_status_ref", P7_R55_COMMAND_MATRIX_RESULT_EVIDENCE_STATUS_REF),
        ("green_claim_rule_ref", P7_R55_COMMAND_MATRIX_GREEN_CLAIM_RULE_REF),
        ("question_implementation_status_ref", P7_R55_FINAL_QUESTION_IMPLEMENTATION_STATUS_REF),
        ("no_touch_boundary_status_ref", P7_R55_NO_TOUCH_BOUNDARY_VALIDATED_REF),
        ("no_touch_touched_refs_empty_ref", P7_R55_NO_TOUCH_TOUCHED_REFS_EMPTY_REF),
    )
    for key, expected in expected_pairs:
        if data.get(key) != expected:
            raise ValueError(f"R55 R10 {key} changed")
    sequence_expectations = (
        ("decision_reason_refs", P7_R55_DEFAULT_DECISION_REASON_REFS, "decision_reason_ref_count"),
        ("recommended_next_work_refs", P7_R55_FINAL_SUMMARY_RECOMMENDED_NEXT_WORK_REFS, "recommended_next_work_ref_count"),
        ("hold_reason_refs", P7_R55_FINAL_SUMMARY_HOLD_REASON_REFS, "hold_reason_ref_count"),
        ("summary_reason_refs", P7_R55_FINAL_SUMMARY_REASON_REFS, "summary_reason_ref_count"),
        ("validation_limitation_refs", P7_R55_FINAL_SUMMARY_VALIDATION_LIMITATION_REFS, "validation_limitation_ref_count"),
        ("missing_evidence_refs", P7_R55_DEFAULT_MISSING_EVIDENCE_REFS, "missing_evidence_ref_count"),
    )
    for key, expected, count_key in sequence_expectations:
        if tuple(data.get(key) or ()) != expected:
            raise ValueError(f"R55 R10 {key} changed")
        if data.get(count_key) != len(expected):
            raise ValueError(f"R55 R10 {count_key} changed")
    for key, expected in (
        ("actual_review_evidence_complete", False),
        ("required_case_count", P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT),
        ("rating_row_count", 0),
        ("question_observation_row_count", 0),
        ("disposal_verified", False),
        ("p5_human_blind_qa_confirmed_final", False),
        ("p6_limited_human_readfeel_start_allowed", False),
        ("p8_question_design_material_candidate", False),
        ("p8_start_allowed", False),
        ("p7_complete", False),
        ("release_allowed", False),
        ("validation_command_row_count", len(P7_R55_COMMAND_MATRIX_GROUP_REFS)),
        ("full_backend_suite_green_confirmed", False),
        ("rn_real_device_modal_readfeel_confirmed", False),
        ("no_touch_touched_refs", []),
        ("no_touch_touched_ref_count", 0),
    ):
        if data.get(key) != expected:
            raise ValueError(f"R55 R10 must keep {key}={expected!r}")
    for hold_key, reason_key, reason_ref in (
        ("p6_hold", "p6_hold_reason_ref", P7_R55_FINAL_P6_HOLD_REASON_REF),
        ("p8_hold", "p8_hold_reason_ref", P7_R55_FINAL_P8_HOLD_REASON_REF),
        ("release_hold", "release_hold_reason_ref", P7_R55_FINAL_RELEASE_HOLD_REASON_REF),
    ):
        if data.get(hold_key) is not True:
            raise ValueError(f"R55 R10 must keep {hold_key}=True")
        if data.get(reason_key) != reason_ref:
            raise ValueError(f"R55 R10 {reason_key} changed")
    for false_key in P7_R55_FINAL_SUMMARY_FALSE_FIELD_REFS:
        if data.get(false_key) is not False:
            raise ValueError(f"R55 R10 must keep {false_key}=False")
    for true_key in (
        "r55_0_scope_current_received_snapshot_refrozen",
        "r55_1_prior_helper_source_reconciled",
        "r55_2_validation_evidence_reconciled",
        "r55_3_r54_default_handoff_intake_done",
        "r55_4_bodyfree_forbidden_payload_scan_done",
        "r55_5_actual_review_evidence_gap_assessed",
        "r55_6_r52_reintake_decision_materialized",
        "r55_7_p5_p6_p8_release_separated",
        "r55_8_final_no_touch_boundary_validated",
        "r55_9_validation_command_matrix_documented",
        "r55_10_final_summary_ready",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R55 R10 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R55_R10_IMPLEMENTED_STEPS:
        raise ValueError("R55 R10 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R55_R10_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R55 R10 not-yet steps must be empty")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R55 R10 contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r55_r10_final_summary")
    return True

# Compatibility alias for the final summary design wording.
build_p7_r55_final_summary = build_p7_r55_final_summary_bodyfree
assert_p7_r55_final_summary_contract = assert_p7_r55_final_summary_bodyfree_contract

# Compatibility alias for the longer design wording.
build_p7_r55_validation_command_matrix_documentation_output_bodyfree = build_p7_r55_validation_command_matrix_bodyfree
assert_p7_r55_validation_command_matrix_documentation_output_bodyfree_contract = assert_p7_r55_validation_command_matrix_bodyfree_contract

# Compatibility alias for the shorter design wording.
build_p7_r55_prior_helper_source_reconcile = build_p7_r55_prior_helper_source_reconcile_bodyfree
assert_p7_r55_prior_helper_source_reconcile_contract = assert_p7_r55_prior_helper_source_reconcile_bodyfree_contract
