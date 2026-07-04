# -*- coding: utf-8 -*-
"""Post-DMH18 downstream manual decision triage helpers for DMD-OP00-OP08.

DMD-OP00 and DMD-OP01 intentionally add only the first thin, body-free
Post-DMH18 manual decision layer:

* DMD-OP00 freezes the Post-DMH18 scope, no-touch boundary, and no-promotion
  boundary after the DMH-OP18 finalizer.  It does not intake OP18 yet, does not
  generate a body-full packet, does not run actual local-only human review, does
  not create receipts/rows, does not execute PostCR22 re-entry/R52, does not
  start P5/P6/P8, does not complete P7, and does not allow release.
* DMD-OP01 intakes a DMH-OP18 finalizer as body-free material.  It distinguishes
  missing / invalid-or-repair-required / accepted-bodyfree OP18 material, records
  OP18 ready/blocked/repair status, and keeps the OP18 ready-path candidate from
  being promoted into real-operation actual review evidence.

DMD-OP02 separates candidate support from real-operation evidence claim, and
DMD-OP03 inventories the optional actual evidence receipt with body-free source,
count, and guard fields.

DMD-OP04 scans body-free leak / invalid-source boundaries without echoing
source values. DMD-OP05 scans downstream promotion claims and keeps all
downstream execution flags false. DMD-OP06 resolves the deterministic branch,
and DMD-OP07 materializes that branch as a body-free manual-decision material.
DMD-OP08 closes the body-free result memo / target-test / selected-regression
summary boundary without running validation commands or downstream execution
inside the helper. No downstream execution is requested or allowed here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh


P7_R54_AHR_POST_DMH18_DMD_PHASE: Final = "P7"
P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_DMH18_DMD_STEP: Final = (
    "R54-AHR-PostDMH18_DownstreamManualDecision_ActualEvidenceStatusTriage_20260703"
)
P7_R54_AHR_POST_DMH18_DMD_SCOPE: Final = (
    "p7_r54_ahr_post_dmh18_downstream_manual_decision_actual_evidence_status_triage"
)
P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND: Final = (
    "r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_triage_boundary"
)
P7_R54_AHR_POST_DMH18_DMD_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postdmh18_dmd_session_20260703_current_received_264_91_177_v1"
)

P7_R54_AHR_POST_DMH18_DMD_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op01_op18_finalizer_bodyfree_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op02_candidate_vs_real_operation_evidence_claim_separation.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op03_actual_evidence_receipt_completeness_inventory.bodyfree.v1"
)

P7_R54_AHR_POST_DMH18_DMD_OP00_STEP_REF: Final = (
    "DMD-OP00_scope_no_touch_no_promotion_re_freeze_after_DMH_OP18"
)
P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF: Final = (
    "DMD-OP01_OP18_finalizer_bodyfree_intake"
)
P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF: Final = (
    "DMD-OP02_candidate_vs_real_operation_evidence_claim_separation"
)
P7_R54_AHR_POST_DMH18_DMD_OP03_STEP_REF: Final = (
    "DMD-OP03_actual_evidence_receipt_completeness_inventory"
)
P7_R54_AHR_POST_DMH18_DMD_OP04_STEP_REF: Final = (
    "DMD-OP04_bodyfree_leak_invalid_source_scan"
)
P7_R54_AHR_POST_DMH18_DMD_OP05_STEP_REF: Final = (
    "DMD-OP05_downstream_promotion_claim_scan"
)
P7_R54_AHR_POST_DMH18_DMD_OP06_STEP_REF: Final = (
    "DMD-OP06_deterministic_branch_resolver"
)
P7_R54_AHR_POST_DMH18_DMD_OP07_STEP_REF: Final = (
    "DMD-OP07_manual_decision_materialization"
)
P7_R54_AHR_POST_DMH18_DMD_OP08_STEP_REF: Final = (
    "DMD-OP08_bodyfree_result_memo_target_tests_regression_closure"
)
P7_R54_AHR_POST_DMH18_DMD_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP00_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP03_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP04_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP05_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP06_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP07_STEP_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DMH18_DMD_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:1]
P7_R54_AHR_POST_DMH18_DMD_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[1:]
P7_R54_AHR_POST_DMH18_DMD_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:2]
P7_R54_AHR_POST_DMH18_DMD_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[2:]
P7_R54_AHR_POST_DMH18_DMD_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:3]
P7_R54_AHR_POST_DMH18_DMD_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[3:]
P7_R54_AHR_POST_DMH18_DMD_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:4]
P7_R54_AHR_POST_DMH18_DMD_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[4:]

P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF: Final = "DMD_OP18_FINALIZER_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF: Final = "DMD_OP18_FINALIZER_MISSING"
P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF: Final = (
    "DMD_OP18_FINALIZER_INVALID_OR_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMH18_DMD_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF,
)

P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF: Final = (
    "continue_or_retry_actual_local_only_human_review_operation_before_downstream_decision"
)
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF: Final = (
    "stop_and_repair_bodyfree_evidence_boundary"
)
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP02_REF: Final = P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP03_REF: Final = P7_R54_AHR_POST_DMH18_DMD_OP03_STEP_REF
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP04_REF: Final = P7_R54_AHR_POST_DMH18_DMD_OP04_STEP_REF

P7_R54_AHR_POST_DMH18_DMD_BRANCH_CANDIDATE_OP18_ACCEPTED_REF: Final = (
    "DMD_OP18_CANDIDATE_SUPPORTED_REQUIRES_DMD_OP02_REAL_OPERATION_CLAIM_SEPARATION"
)
P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF: Final = (
    "DMD_BRANCH_EVIDENCE_INCOMPLETE_OR_NOT_CLAIMED_FROM_REAL_OPERATION"
)
P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF: Final = (
    "DMD_BRANCH_BODYFREE_BOUNDARY_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF: Final = (
    "DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION"
)

P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_CANDIDATE_ONLY_REF: Final = (
    "DMD_OP02_CANDIDATE_SUPPORTED_REAL_OPERATION_NOT_CLAIMED"
)
P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF: Final = (
    "DMD_OP02_REAL_OPERATION_CLAIM_SUPPORTED_BY_EXTERNAL_BODYFREE_RECEIPT"
)
P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_INCOMPLETE_REF: Final = (
    "DMD_OP02_PRIOR_INTAKE_MISSING_OR_EVIDENCE_INCOMPLETE"
)
P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DMD_OP02_CLAIM_SEPARATION_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMH18_DMD_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_CANDIDATE_ONLY_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF,
)

P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF: Final = "DMD_OP03_ACTUAL_EVIDENCE_RECEIPT_MISSING"
P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF: Final = "DMD_OP03_ACTUAL_EVIDENCE_RECEIPT_INCOMPLETE"
P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DMD_OP03_ACTUAL_EVIDENCE_RECEIPT_INVALID_OR_BODYFREE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF: Final = (
    "DMD_OP03_ACTUAL_EVIDENCE_RECEIPT_COMPLETE_BODYFREE_CANDIDATE"
)
P7_R54_AHR_POST_DMH18_DMD_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF,
)

P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.actual_operation_evidence_receipt.bodyfree.optional.v1"
)
P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF: Final = (
    "actual_local_only_human_review_by_person"
)
P7_R54_AHR_POST_DMH18_DMD_INVALID_SOURCE_KIND_REFS: Final[tuple[str, ...]] = (
    "unit_test_fixture",
    "helper_green",
    "synthetic",
    "historical_reuse_only",
    "unknown",
)
P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT: Final = dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT
P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewed_case_count",
    "selection_row_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_need_observation_row_count",
)
P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS: Final[tuple[str, ...]] = (
    "created_from_real_operation",
    "actual_source_guard_passed",
    "actual_human_review_executed_by_person",
    "disposal_purge_receipt_accepted",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_path_hash_validation_passed",
    "no_terminal_output_body_validation_passed",
    "no_touch_validation_passed",
    "body_free",
)
P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REPAIR_GUARD_FIELD_REFS: Final[tuple[str, ...]] = (
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_path_hash_validation_passed",
    "no_terminal_output_body_validation_passed",
    "no_touch_validation_passed",
)
P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_INCOMPLETE_REF: Final = (
    "actual_evidence_incomplete_or_not_claimed_from_real_operation"
)
P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_REPAIR_REQUIRED_REF: Final = (
    "bodyfree_evidence_boundary_repair_required"
)
P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_COMPLETE_CANDIDATE_REF: Final = (
    "actual_evidence_complete_from_real_operation_bodyfree_candidate_ready"
)

P7_R54_AHR_POST_DMH18_DMD_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-DMH-OP18 Downstream Manual Decision / Actual Evidence Status Triage"
)
P7_R54_AHR_POST_DMH18_DMD_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "P8 question design",
    "P8 question implementation",
    "P6 limited human readfeel start",
    "R52 actual execution",
    "P5 finalization",
    "P7 complete",
    "release decision",
)
P7_R54_AHR_POST_DMH18_DMD_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(276).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(91).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(10).zip",
    "rn_zip_ref": "Cocolon(264).zip",
    "backend_zip_ref": "mashos-api(177).zip",
}
P7_R54_AHR_POST_DMH18_DMD_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostDMH18_DownstreamManualDecision_PreDesignMemo_20260703.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostDMH18_DownstreamManualDecision_ActualEvidenceStatusTriage_DetailedDesign_ImplementationOrder_20260703.md",
    "R54_AHR_PostPMN23_DownstreamManualDecisionHold_EvidenceIntake_DMH_OP18_Result_20260702.md",
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701.py",
)
P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dmh_op18_ready_path_is_not_real_operation_actual_review_completion",
    "actual_review_evidence_candidate_is_not_actual_review_evidence_claimed_from_real_operation",
    "helper_green_is_not_actual_human_review_complete",
    "target_green_is_not_actual_human_review_complete",
    "result_memo_bodyfree_closed_is_not_body_full_packet_generation",
    "postcr22_ex07_ex18_reentry_ready_candidate_is_not_reentry_execution",
    "r52_handoff_candidate_is_not_r52_actual_execution",
    "p5_confirmed_candidate_is_not_p5_final",
    "p6_candidate_only_is_not_p6_start",
    "p8_material_candidate_only_is_not_p8_start",
    "p7_target_green_is_not_p7_complete",
    "release_decision_is_not_allowed_here",
)
P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_local_human_review_execution",
    "actual_operation_receipt_from_real_operation",
    "actual_sanitized_review_result_rows_from_real_operation",
    "actual_rating_rows_from_real_operation",
    "actual_question_need_observation_rows_from_real_operation",
    "actual_disposal_purge_execution",
    "actual_review_evidence_complete_from_real_operation",
    "postcr22_ex07_ex18_reentry_executed_here",
    "r52_actual_execution",
    "p5_final",
    "p6_start",
    "p8_start",
    "p8_question_design",
    "p8_question_implementation",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "helper green != actual human review complete",
    "OP18 ready-path fixture != live operation evidence",
    "actual evidence candidate != downstream execution allowed",
    "P5 confirmed candidate != P5 final",
    "P6 candidate-only != P6 start",
    "P8 material candidate-only != P8 start",
    "R52 handoff candidate != R52 actual execution",
    "PostCR22 reentry ready candidate != actual reentry executed",
    "P7 target green != P7 complete",
    "P7 complete != release allowed",
)
P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "body_full_packet_generated_here",
    "body_full_packet_generation_run_here",
    "actual_local_human_review_executed_here",
    "actual_human_review_run_here",
    "actual_rows_created_here",
    "actual_operation_receipt_created_here",
    "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_purge_executed_here",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "manual_decision_auto_executes_downstream",
    "postcr22_ex07_ex18_reentry_executed_here",
    "postcr22_ex07_ex18_reentry_execution_requested_here",
    "r52_actual_execution_started_here",
    "r52_actual_execution_confirmed",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DMH18_DMD_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "input_body_included",
    "comment_text_body_included",
    "reviewer_note_body_included",
    "question_text_included",
    "draft_question_text_included",
    "answer_text_included",
    "body_full_packet_body_included",
    "local_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_POST_DMH18_DMD_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_changed",
    "p8_question_api_created",
    "p8_question_db_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "postcr22_ex07_ex18_reentry_executed_here",
    "r52_actual_execution_started_here",
    "release_allowed",
)
P7_R54_AHR_POST_DMH18_DMD_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        *dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS,
        "raw_answer",
        "answer_text",
        "body_full_packet",
        "body_full_packet_body",
        "absolute_path",
        "relative_path",
        "file_path",
        "input_hash",
        "sha256",
        "terminal_output_body",
        "stdout",
        "stderr",
    }
)
P7_R54_AHR_POST_DMH18_DMD_OP18_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "manual_decision_auto_executes_downstream",
    "postcr22_ex07_ex18_reentry_executed_here",
    "postcr22_ex07_ex18_reentry_execution_requested_here",
    "r52_actual_execution_started_here",
    "r52_actual_execution_confirmed",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)

P7_R54_AHR_POST_DMH18_DMD_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "not_stage_refs", "not_stage_ref_count", "support_material_refs", "support_material_ref_count",
    "local_received_zip_refs", "local_received_zip_ref_count", "body_free", "dmd_op00_scope_confirmed",
    "dmd_op00_no_touch_boundary_confirmed", "dmd_op00_no_promotion_boundary_confirmed",
    "dmd_op00_does_not_intake_op18_finalizer", "dmd_op00_does_not_generate_body_full_packet",
    "dmd_op00_does_not_run_actual_local_human_review", "dmd_op00_does_not_create_receipts_rows_or_disposal",
    "dmd_op00_does_not_start_p8_p6_r52_or_release", "dmd_op00_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dmh18_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_DMH18_DMD_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed",
    "op00_no_touch_boundary_confirmed", "op00_no_promotion_boundary_confirmed", "dmd_op01_status_ref",
    "dmd_op01_allowed_status_refs", "dmd_op01_ready", "dmd_op01_reason_refs", "dmd_op01_reason_ref_count",
    "dmd_op01_blocker_refs", "dmd_op01_blocker_ref_count", "op18_finalizer_present", "op18_contract_valid",
    "op18_schema_version", "op18_operation_step_ref", "op18_material_ref", "op18_result_memo_ref",
    "op18_dmh_op18_status_ref", "op18_dmh_op18_ready", "op18_next_required_step", "op18_result_memo_bodyfree_closed",
    "op18_downstream_manual_decision_hold_finalized", "op18_manual_downstream_decision_required",
    "op18_actual_review_evidence_complete_candidate_from_real_review", "op18_actual_review_evidence_complete_from_real_review",
    "op18_candidate_supported", "op18_real_operation_claim_detected", "op18_bodyfree_evidence_boundary_repair_required",
    "op18_evidence_incomplete_continue_or_retry_required", "op18_postcr22_ex07_ex18_reentry_ready_candidate",
    "op18_postcr22_ex07_ex18_reentry_executed_here", "op18_r52_actual_execution_started_here", "op18_r52_actual_execution_confirmed",
    "op18_p5_final_allowed", "op18_p6_start_allowed", "op18_p8_start_allowed", "op18_p7_complete", "op18_release_allowed",
    "op18_forbidden_payload_key_paths", "op18_forbidden_payload_key_path_count", "op18_promotion_claim_refs",
    "op18_promotion_claim_ref_count", "op18_intake_branch_candidate_ref", "op18_ready_path_not_promoted_to_real_operation_claim",
    "candidate_supported_not_promoted_to_claimed_from_real_operation", "actual_review_evidence_complete_from_real_operation_claimed_by_dmd_op01",
    "dmd_op01_does_not_resolve_final_branch", "dmd_op01_does_not_generate_body_full_packet", "dmd_op01_does_not_run_actual_local_human_review",
    "dmd_op01_does_not_create_receipts_rows_or_disposal", "dmd_op01_does_not_execute_postcr22_ex_reentry_or_r52",
    "dmd_op01_does_not_start_p5_p6_p8_p7_or_release", "dmd_op01_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dmh18_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DMH18_DMD_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_status_ref", "op01_ready", "op01_next_required_step",
    "op01_intake_branch_candidate_ref", "dmd_op02_status_ref", "dmd_op02_allowed_status_refs", "dmd_op02_ready",
    "dmd_op02_reason_refs", "dmd_op02_reason_ref_count", "dmd_op02_blocker_refs", "dmd_op02_blocker_ref_count",
    "candidate_supported", "candidate_supported_source_refs", "candidate_supported_source_ref_count",
    "op18_candidate_supported", "op18_actual_review_evidence_complete_from_real_review", "op18_ready_path_not_promoted_to_real_operation_claim",
    "helper_green_not_promoted_to_real_operation_claim", "candidate_supported_not_auto_promoted_to_claimed_from_real_operation",
    "external_actual_operation_evidence_receipt_present", "external_actual_operation_evidence_receipt_schema_version",
    "external_actual_operation_evidence_receipt_ref", "external_actual_operation_evidence_receipt_source_kind_ref",
    "external_actual_operation_evidence_receipt_source_kind_valid", "external_actual_operation_evidence_receipt_created_from_real_operation",
    "external_actual_operation_evidence_receipt_actual_source_guard_passed", "external_actual_operation_evidence_receipt_actual_human_review_executed_by_person",
    "external_actual_operation_evidence_receipt_counts_and_guards_passed", "external_actual_operation_evidence_receipt_forbidden_payload_key_paths",
    "external_actual_operation_evidence_receipt_forbidden_payload_key_path_count", "claimed_from_real_operation",
    "claimed_from_real_operation_reason_refs", "claimed_from_real_operation_reason_ref_count", "claimed_from_real_operation_blocker_refs",
    "claimed_from_real_operation_blocker_ref_count", "actual_review_evidence_complete_from_real_operation_claimed_here_by_dmd_op02",
    "dmd_op02_does_not_inventory_final_completeness", "dmd_op02_does_not_resolve_final_branch", "dmd_op02_does_not_generate_body_full_packet",
    "dmd_op02_does_not_run_actual_local_human_review", "dmd_op02_does_not_create_receipts_rows_or_disposal",
    "dmd_op02_does_not_execute_postcr22_ex_reentry_or_r52", "dmd_op02_does_not_start_p5_p6_p8_p7_or_release",
    "dmd_op02_does_not_change_api_db_rn_runtime_response_key", "branch_candidate_ref", "next_required_step",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "public_contract", "post_dmh18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMH18_DMD_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_ready", "op02_claimed_from_real_operation",
    "op02_branch_candidate_ref", "op02_next_required_step", "dmd_op03_status_ref", "dmd_op03_allowed_status_refs", "dmd_op03_ready",
    "actual_evidence_status_ref", "actual_evidence_receipt_present", "actual_evidence_receipt_schema_version", "actual_evidence_receipt_ref",
    "actual_evidence_receipt_source_kind_ref", "actual_evidence_receipt_source_kind_valid", "actual_evidence_receipt_invalid_source_detected",
    "actual_evidence_receipt_forbidden_payload_key_paths", "actual_evidence_receipt_forbidden_payload_key_path_count",
    "actual_operation_receipt_present", "created_from_real_operation", "actual_source_guard_passed", "actual_human_review_executed_by_person",
    "reviewed_case_count", "selection_row_count", "sanitized_review_result_row_count", "rating_row_count", "question_need_observation_row_count",
    "reviewed_case_count_is_24", "selection_row_count_is_24", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24",
    "question_need_observation_row_count_is_24", "disposal_purge_receipt_accepted", "no_body_leak_validation_passed",
    "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_terminal_output_body_validation_passed", "no_touch_validation_passed",
    "review_session_id_consistent", "operation_receipt_ref_consistent", "actual_evidence_receipt_count_complete",
    "actual_evidence_receipt_guard_complete", "actual_evidence_receipt_complete", "actual_evidence_receipt_missing_or_incomplete",
    "bodyfree_evidence_boundary_repair_required", "evidence_incomplete_continue_or_retry_required", "complete_candidate_for_manual_decision_branch",
    "downstream_manual_decision_required_without_auto_execution", "dmd_op03_reason_refs", "dmd_op03_reason_ref_count",
    "dmd_op03_blocker_refs", "dmd_op03_blocker_ref_count", "branch_candidate_ref", "next_required_step",
    "dmd_op03_does_not_resolve_final_branch", "dmd_op03_does_not_generate_body_full_packet", "dmd_op03_does_not_run_actual_local_human_review",
    "dmd_op03_does_not_create_receipts_rows_or_disposal", "dmd_op03_does_not_execute_postcr22_ex_reentry_or_r52",
    "dmd_op03_does_not_start_p5_p6_p8_p7_or_release", "dmd_op03_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps",
    "public_contract", "post_dmh18_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(
        value,
        default=P7_R54_AHR_POST_DMH18_DMD_DEFAULT_REVIEW_SESSION_ID,
        max_length=220,
    )


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMH18_DMD_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMH18_DMD_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS}


def _required_fields_present(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {', '.join(missing[:8])}")


def _scan_forbidden_payload_key_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_DMH18_DMD_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _op18_promotion_claim_refs(op18_finalizer: Mapping[str, Any]) -> list[str]:
    return [field for field in P7_R54_AHR_POST_DMH18_DMD_OP18_PROMOTION_CLAIM_FIELD_REFS if op18_finalizer.get(field) is True]


def _op18_contract_valid(op18_finalizer: Mapping[str, Any] | None) -> bool:
    if not isinstance(op18_finalizer, Mapping):
        return False
    try:
        return (
            dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(
                op18_finalizer
            )
            is True
        )
    except ValueError:
        return False


def _op18_branch_candidate_ref(op18_finalizer: Mapping[str, Any] | None, *, status_ref: str) -> str:
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF:
        return P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF:
        return P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    if not isinstance(op18_finalizer, Mapping):
        return P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    if op18_finalizer.get("bodyfree_evidence_boundary_repair_required") is True:
        return P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    if op18_finalizer.get("evidence_incomplete_continue_or_retry_required") is True or op18_finalizer.get("dmh_op18_ready") is not True:
        return P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    return P7_R54_AHR_POST_DMH18_DMD_BRANCH_CANDIDATE_OP18_ACCEPTED_REF


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_DMH18_DMD_PHASE or data.get("current_phase") != P7_R54_AHR_POST_DMH18_DMD_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_DMH18_DMD_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_DMH18_DMD_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim GitHub connection check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for field in P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS:
        if data.get(field) is not False:
            raise ValueError(f"{source} required false flag changed: {field}")
    if any(value is not False for value in (data.get("public_contract") or {}).values()):
        raise ValueError(f"{source} public contract mutated")
    if any(value is not False for value in (data.get("post_dmh18_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract mutated")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free marker changed")
    if any(key in P7_R54_AHR_POST_DMH18_DMD_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains forbidden top-level payload key")


def build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build DMD-OP00 body-free scope / no-touch / no-promotion re-freeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_DMH18_DMD_SELECTED_STAGE_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_DMH18_DMD_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_DMH18_DMD_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "dmd_op00_scope_confirmed": True,
        "dmd_op00_no_touch_boundary_confirmed": True,
        "dmd_op00_no_promotion_boundary_confirmed": True,
        "dmd_op00_does_not_intake_op18_finalizer": True,
        "dmd_op00_does_not_generate_body_full_packet": True,
        "dmd_op00_does_not_run_actual_local_human_review": True,
        "dmd_op00_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op00_does_not_start_p8_p6_r52_or_release": True,
        "dmd_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMD-OP00 scope / no-touch / no-promotion re-freeze contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DMH18_DMD_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDMH18-DMD-OP00",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMH18_DMD_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP00_STEP_REF,
        source="P7-R54-AHR-PostDMH18-DMD-OP00",
    )
    for key in (
        "dmd_op00_scope_confirmed",
        "dmd_op00_no_touch_boundary_confirmed",
        "dmd_op00_no_promotion_boundary_confirmed",
        "dmd_op00_does_not_intake_op18_finalizer",
        "dmd_op00_does_not_generate_body_full_packet",
        "dmd_op00_does_not_run_actual_local_human_review",
        "dmd_op00_does_not_create_receipts_rows_or_disposal",
        "dmd_op00_does_not_start_p8_p6_r52_or_release",
        "dmd_op00_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP00 required true boundary changed: {key}")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("local_received_zip_refs", "local_received_zip_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP00 {count_field} changed")
    if tuple(data.get("not_stage_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_STAGE_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 not-stage refs changed")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 support material refs changed")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_DMH18_DMD_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 local received zip refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 fixed non-promotion refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP00 next required step changed")
    return True


def _op01_status_and_blockers(op18_finalizer: Mapping[str, Any] | None) -> tuple[str, list[str]]:
    if not isinstance(op18_finalizer, Mapping):
        return P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF, ["dmd_op01_op18_finalizer_missing"]

    blockers: list[str] = []
    if _scan_forbidden_payload_key_paths(op18_finalizer, path="op18_finalizer"):
        blockers.append("dmd_op01_op18_finalizer_forbidden_payload_key_detected")
    if not _op18_contract_valid(op18_finalizer):
        blockers.append("dmd_op01_op18_finalizer_contract_invalid")
    if _op18_promotion_claim_refs(op18_finalizer):
        blockers.append("dmd_op01_op18_finalizer_promotion_or_real_operation_claim_detected")

    if blockers:
        return P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF, list(dict.fromkeys(blockers))
    return P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF, []


def build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    op18_result_memo_downstream_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP01 body-free OP18 finalizer intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze(
            review_session_id=session_id
        )
    op00_valid = False
    try:
        op00_valid = assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract(op00) is True
    except ValueError:
        op00_valid = False

    op18 = op18_result_memo_downstream_manual_decision_hold_finalizer if isinstance(op18_result_memo_downstream_manual_decision_hold_finalizer, Mapping) else {}
    status_ref, blockers = _op01_status_and_blockers(op18_result_memo_downstream_manual_decision_hold_finalizer)
    if not op00_valid:
        blockers = [*blockers, "dmd_op01_op00_scope_no_touch_no_promotion_refreeze_invalid"]
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    blockers = list(dict.fromkeys(blockers))
    ready = status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF
    op18_forbidden_paths = _scan_forbidden_payload_key_paths(op18, path="op18_finalizer")
    op18_promotion_claims = _op18_promotion_claim_refs(op18)
    op18_contract_valid = _op18_contract_valid(op18_result_memo_downstream_manual_decision_hold_finalizer)
    branch_candidate_ref = _op18_branch_candidate_ref(op18_result_memo_downstream_manual_decision_hold_finalizer, status_ref=status_ref)
    if ready:
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP02_REF
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF:
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    else:
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF

    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="op00_schema_missing", max_length=220),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="op00_next_required_step_missing", max_length=220),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("dmd_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("dmd_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("dmd_op00_no_promotion_boundary_confirmed") is True),
        "dmd_op01_status_ref": status_ref,
        "dmd_op01_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP01_ALLOWED_STATUS_REFS),
        "dmd_op01_ready": ready,
        "dmd_op01_reason_refs": ["dmd_op01_op18_finalizer_accepted_bodyfree_without_real_operation_promotion"] if ready else [],
        "dmd_op01_reason_ref_count": 1 if ready else 0,
        "dmd_op01_blocker_refs": blockers,
        "dmd_op01_blocker_ref_count": len(blockers),
        "op18_finalizer_present": isinstance(op18_result_memo_downstream_manual_decision_hold_finalizer, Mapping),
        "op18_contract_valid": op18_contract_valid,
        "op18_schema_version": _clean_ref(op18.get("schema_version"), default="op18_schema_missing", max_length=260),
        "op18_operation_step_ref": _clean_ref(op18.get("operation_step_ref"), default="op18_operation_step_ref_missing", max_length=260),
        "op18_material_ref": _clean_ref(op18.get("material_id"), default="op18_material_missing", max_length=260),
        "op18_result_memo_ref": _clean_ref(op18.get("result_memo_ref"), default="op18_result_memo_ref_missing", max_length=260),
        "op18_dmh_op18_status_ref": _clean_ref(op18.get("dmh_op18_status_ref"), default="op18_status_missing", max_length=260),
        "op18_dmh_op18_ready": op18.get("dmh_op18_ready") is True,
        "op18_next_required_step": _clean_ref(op18.get("next_required_step"), default="op18_next_required_step_missing", max_length=260),
        "op18_result_memo_bodyfree_closed": op18.get("result_memo_bodyfree_closed") is True,
        "op18_downstream_manual_decision_hold_finalized": op18.get("downstream_manual_decision_hold_finalized") is True,
        "op18_manual_downstream_decision_required": op18.get("manual_downstream_decision_required") is True,
        "op18_actual_review_evidence_complete_candidate_from_real_review": op18.get("actual_review_evidence_complete_candidate_from_real_review") is True,
        "op18_actual_review_evidence_complete_from_real_review": op18.get("actual_review_evidence_complete_from_real_review") is True,
        "op18_candidate_supported": op18.get("actual_review_evidence_complete_candidate_from_real_review") is True or op18.get("actual_review_evidence_complete_from_real_review") is True,
        "op18_real_operation_claim_detected": op18.get("actual_review_evidence_complete_from_real_operation_claimed_here") is True,
        "op18_bodyfree_evidence_boundary_repair_required": op18.get("bodyfree_evidence_boundary_repair_required") is True,
        "op18_evidence_incomplete_continue_or_retry_required": op18.get("evidence_incomplete_continue_or_retry_required") is True,
        "op18_postcr22_ex07_ex18_reentry_ready_candidate": op18.get("postcr22_ex07_ex18_reentry_ready_candidate") is True,
        "op18_postcr22_ex07_ex18_reentry_executed_here": False,
        "op18_r52_actual_execution_started_here": False,
        "op18_r52_actual_execution_confirmed": False,
        "op18_p5_final_allowed": False,
        "op18_p6_start_allowed": False,
        "op18_p8_start_allowed": False,
        "op18_p7_complete": False,
        "op18_release_allowed": False,
        "op18_forbidden_payload_key_paths": [_clean_ref(path, max_length=260) for path in op18_forbidden_paths],
        "op18_forbidden_payload_key_path_count": len(op18_forbidden_paths),
        "op18_promotion_claim_refs": [_clean_ref(ref, max_length=220) for ref in op18_promotion_claims],
        "op18_promotion_claim_ref_count": len(op18_promotion_claims),
        "op18_intake_branch_candidate_ref": branch_candidate_ref,
        "op18_ready_path_not_promoted_to_real_operation_claim": True,
        "candidate_supported_not_promoted_to_claimed_from_real_operation": True,
        "actual_review_evidence_complete_from_real_operation_claimed_by_dmd_op01": False,
        "dmd_op01_does_not_resolve_final_branch": True,
        "dmd_op01_does_not_generate_body_full_packet": True,
        "dmd_op01_does_not_run_actual_local_human_review": True,
        "dmd_op01_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op01_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP01_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_DMH18_DMD_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP01_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_DMH18_DMD_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMD-OP01 body-free OP18 finalizer intake contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DMH18_DMD_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDMH18-DMD-OP01",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMH18_DMD_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF,
        source="P7-R54-AHR-PostDMH18-DMD-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_DMH18_DMD_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 OP00 next step changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "op18_ready_path_not_promoted_to_real_operation_claim",
        "candidate_supported_not_promoted_to_claimed_from_real_operation",
        "dmd_op01_does_not_resolve_final_branch",
        "dmd_op01_does_not_generate_body_full_packet",
        "dmd_op01_does_not_run_actual_local_human_review",
        "dmd_op01_does_not_create_receipts_rows_or_disposal",
        "dmd_op01_does_not_execute_postcr22_ex_reentry_or_r52",
        "dmd_op01_does_not_start_p5_p6_p8_p7_or_release",
        "dmd_op01_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP01 required true boundary changed: {key}")
    for key in (
        "actual_review_evidence_complete_from_real_operation_claimed_by_dmd_op01",
        "op18_postcr22_ex07_ex18_reentry_executed_here",
        "op18_r52_actual_execution_started_here",
        "op18_r52_actual_execution_confirmed",
        "op18_p5_final_allowed",
        "op18_p6_start_allowed",
        "op18_p8_start_allowed",
        "op18_p7_complete",
        "op18_release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP01 downstream flag promoted: {key}")
    if tuple(data.get("dmd_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 allowed status refs changed")
    for field, count_field in (
        ("dmd_op01_reason_refs", "dmd_op01_reason_ref_count"),
        ("dmd_op01_blocker_refs", "dmd_op01_blocker_ref_count"),
        ("op18_forbidden_payload_key_paths", "op18_forbidden_payload_key_path_count"),
        ("op18_promotion_claim_refs", "op18_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP01 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 fixed non-promotion refs changed")

    status_ref = data.get("dmd_op01_status_ref")
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF:
        if data.get("dmd_op01_ready") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted material must be ready")
        if data.get("dmd_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted material cannot carry blockers")
        if data.get("dmd_op01_reason_refs") != ["dmd_op01_op18_finalizer_accepted_bodyfree_without_real_operation_promotion"]:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted reason changed")
        if data.get("op18_finalizer_present") is not True or data.get("op18_contract_valid") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted material requires valid OP18 finalizer")
        if data.get("op18_schema_version") != dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_FINALIZER_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 OP18 schema version changed")
        if data.get("op18_operation_step_ref") != dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 OP18 step ref changed")
        if data.get("op18_result_memo_ref") != dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 OP18 result memo ref changed")
        if data.get("op18_forbidden_payload_key_paths") != [] or data.get("op18_promotion_claim_refs") != []:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted material cannot carry OP18 leak/promotion claims")
        if data.get("op18_real_operation_claim_detected") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 cannot accept real-operation claim")
        if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP01_IMPLEMENTED_STEPS):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted implemented steps changed")
        if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP01_NOT_YET_IMPLEMENTED_STEPS):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP02_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 accepted next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF:
        if data.get("dmd_op01_ready") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 missing material cannot be ready")
        if data.get("op18_finalizer_present") is not False or data.get("op18_contract_valid") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 missing material cannot claim OP18 finalizer")
        if "dmd_op01_op18_finalizer_missing" not in (data.get("dmd_op01_blocker_refs") or []):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 missing blocker absent")
        if data.get("op18_intake_branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 missing branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 missing next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF:
        if data.get("dmd_op01_ready") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 invalid material cannot be ready")
        if not data.get("dmd_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 invalid material must carry blockers")
        if data.get("op18_intake_branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 invalid branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 invalid next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP01 unknown status ref")
    return True




def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _receipt_count_values(receipt: Mapping[str, Any] | None) -> dict[str, int]:
    if not isinstance(receipt, Mapping):
        return {field: 0 for field in P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS}
    return {field: _safe_int(receipt.get(field)) for field in P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS}


def _receipt_count_pass_refs(receipt: Mapping[str, Any] | None) -> dict[str, bool]:
    counts = _receipt_count_values(receipt)
    return {f"{field}_is_24": count == P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT for field, count in counts.items()}


def _receipt_source_kind_ref(receipt: Mapping[str, Any] | None) -> str:
    if not isinstance(receipt, Mapping):
        return "actual_operation_evidence_receipt_source_kind_missing"
    return _clean_ref(receipt.get("source_kind_ref"), default="actual_operation_evidence_receipt_source_kind_missing", max_length=180)


def _receipt_ref(receipt: Mapping[str, Any] | None) -> str:
    if not isinstance(receipt, Mapping):
        return "actual_operation_evidence_receipt_missing"
    return _clean_ref(receipt.get("operation_receipt_ref"), default="actual_operation_evidence_receipt_ref_missing", max_length=220)


def _receipt_schema_version(receipt: Mapping[str, Any] | None) -> str:
    if not isinstance(receipt, Mapping):
        return "actual_operation_evidence_receipt_schema_missing"
    return _clean_ref(receipt.get("schema_version"), default="actual_operation_evidence_receipt_schema_missing", max_length=260)


def _receipt_has_expected_schema(receipt: Mapping[str, Any] | None) -> bool:
    return isinstance(receipt, Mapping) and receipt.get("schema_version") == P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION


def _receipt_source_kind_valid(receipt: Mapping[str, Any] | None) -> bool:
    return _receipt_source_kind_ref(receipt) == P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF


def _receipt_required_true_fields_pass(receipt: Mapping[str, Any] | None) -> bool:
    return isinstance(receipt, Mapping) and all(receipt.get(field) is True for field in P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS)


def _receipt_count_fields_pass(receipt: Mapping[str, Any] | None) -> bool:
    return all(_receipt_count_pass_refs(receipt).values())


def _receipt_core_real_operation_claim_supported(receipt: Mapping[str, Any] | None) -> bool:
    if not isinstance(receipt, Mapping):
        return False
    return (
        _receipt_has_expected_schema(receipt)
        and _receipt_source_kind_valid(receipt)
        and _receipt_required_true_fields_pass(receipt)
        and _receipt_count_fields_pass(receipt)
        and not _scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree_optional")
    )


def _op02_status_and_blockers(
    op01: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    claim_blockers: list[str] = []
    op01_valid = False
    if isinstance(op01, Mapping):
        try:
            op01_valid = assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(op01) is True
        except ValueError:
            op01_valid = False
    if not op01_valid:
        blockers.append("dmd_op02_op01_intake_invalid_or_missing")
        return P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF, blockers, claim_blockers
    if op01.get("dmd_op01_status_ref") == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF:
        blockers.append("dmd_op02_op01_intake_repair_required")
        return P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF, blockers, claim_blockers
    if op01.get("dmd_op01_status_ref") == P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF:
        claim_blockers.append("dmd_op02_op18_finalizer_missing_real_operation_claim_unavailable")
        return P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_INCOMPLETE_REF, blockers, claim_blockers
    receipt_forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree_optional") if isinstance(receipt, Mapping) else []
    if receipt_forbidden_paths:
        blockers.append("dmd_op02_external_receipt_forbidden_payload_key_detected")
        return P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF, blockers, claim_blockers
    if _receipt_core_real_operation_claim_supported(receipt):
        return P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF, blockers, claim_blockers
    if not isinstance(receipt, Mapping):
        claim_blockers.append("dmd_op02_external_actual_operation_evidence_receipt_missing")
    elif not _receipt_has_expected_schema(receipt):
        claim_blockers.append("dmd_op02_external_actual_operation_evidence_receipt_schema_missing_or_invalid")
    elif not _receipt_source_kind_valid(receipt):
        claim_blockers.append("dmd_op02_external_actual_operation_evidence_receipt_source_kind_not_real_operation")
    elif not _receipt_count_fields_pass(receipt):
        claim_blockers.append("dmd_op02_external_actual_operation_evidence_receipt_count_incomplete")
    elif not _receipt_required_true_fields_pass(receipt):
        claim_blockers.append("dmd_op02_external_actual_operation_evidence_receipt_guard_incomplete")
    return P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_CANDIDATE_ONLY_REF, blockers, claim_blockers


def build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
    *,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP02 candidate-vs-real-operation claim separation material."""

    session_id = _safe_review_session_id(review_session_id)
    op01 = op18_finalizer_bodyfree_intake
    if op01 is None:
        op01 = build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(review_session_id=session_id)
    receipt = actual_operation_evidence_receipt_bodyfree_optional if isinstance(actual_operation_evidence_receipt_bodyfree_optional, Mapping) else None
    status_ref, blockers, claim_blockers = _op02_status_and_blockers(op01 if isinstance(op01, Mapping) else None, receipt)
    claimed_from_real_operation = status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF
    candidate_supported = bool(isinstance(op01, Mapping) and op01.get("op18_candidate_supported") is True)
    candidate_sources = []
    if candidate_supported:
        candidate_sources.append("op18_actual_review_evidence_complete_candidate_from_real_review")
    if isinstance(op01, Mapping) and op01.get("op18_actual_review_evidence_complete_from_real_review") is True:
        candidate_sources.append("op18_actual_review_evidence_complete_from_real_review")
    candidate_sources = list(dict.fromkeys(candidate_sources))
    reason_refs: list[str] = []
    if candidate_supported:
        reason_refs.append("dmd_op02_op18_candidate_supported_but_not_auto_promoted")
    if claimed_from_real_operation:
        reason_refs.append("dmd_op02_external_bodyfree_actual_operation_receipt_supports_real_operation_claim")
    branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF:
        branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_INCOMPLETE_REF:
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    else:
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP03_REF
        if claimed_from_real_operation:
            branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_claim_separation_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else "", default="op01_schema_missing", max_length=260),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else "", default="op01_material_missing", max_length=260),
        "op01_status_ref": _clean_ref(op01.get("dmd_op01_status_ref") if isinstance(op01, Mapping) else "", default="op01_status_missing", max_length=220),
        "op01_ready": bool(isinstance(op01, Mapping) and op01.get("dmd_op01_ready") is True),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else "", default="op01_next_required_step_missing", max_length=220),
        "op01_intake_branch_candidate_ref": _clean_ref(op01.get("op18_intake_branch_candidate_ref") if isinstance(op01, Mapping) else "", default="op01_branch_candidate_missing", max_length=220),
        "dmd_op02_status_ref": status_ref,
        "dmd_op02_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP02_ALLOWED_STATUS_REFS),
        "dmd_op02_ready": status_ref in (
            P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_CANDIDATE_ONLY_REF,
            P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF,
        ),
        "dmd_op02_reason_refs": reason_refs,
        "dmd_op02_reason_ref_count": len(reason_refs),
        "dmd_op02_blocker_refs": blockers,
        "dmd_op02_blocker_ref_count": len(blockers),
        "candidate_supported": candidate_supported,
        "candidate_supported_source_refs": candidate_sources,
        "candidate_supported_source_ref_count": len(candidate_sources),
        "op18_candidate_supported": candidate_supported,
        "op18_actual_review_evidence_complete_from_real_review": bool(isinstance(op01, Mapping) and op01.get("op18_actual_review_evidence_complete_from_real_review") is True),
        "op18_ready_path_not_promoted_to_real_operation_claim": True,
        "helper_green_not_promoted_to_real_operation_claim": True,
        "candidate_supported_not_auto_promoted_to_claimed_from_real_operation": True,
        "external_actual_operation_evidence_receipt_present": isinstance(receipt, Mapping),
        "external_actual_operation_evidence_receipt_schema_version": _receipt_schema_version(receipt),
        "external_actual_operation_evidence_receipt_ref": _receipt_ref(receipt),
        "external_actual_operation_evidence_receipt_source_kind_ref": _receipt_source_kind_ref(receipt),
        "external_actual_operation_evidence_receipt_source_kind_valid": _receipt_source_kind_valid(receipt),
        "external_actual_operation_evidence_receipt_created_from_real_operation": bool(isinstance(receipt, Mapping) and receipt.get("created_from_real_operation") is True),
        "external_actual_operation_evidence_receipt_actual_source_guard_passed": bool(isinstance(receipt, Mapping) and receipt.get("actual_source_guard_passed") is True),
        "external_actual_operation_evidence_receipt_actual_human_review_executed_by_person": bool(isinstance(receipt, Mapping) and receipt.get("actual_human_review_executed_by_person") is True),
        "external_actual_operation_evidence_receipt_counts_and_guards_passed": _receipt_core_real_operation_claim_supported(receipt),
        "external_actual_operation_evidence_receipt_forbidden_payload_key_paths": [
            _clean_ref(path, max_length=260) for path in (_scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree_optional") if isinstance(receipt, Mapping) else [])
        ],
        "external_actual_operation_evidence_receipt_forbidden_payload_key_path_count": len(_scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree_optional") if isinstance(receipt, Mapping) else []),
        "claimed_from_real_operation": claimed_from_real_operation,
        "claimed_from_real_operation_reason_refs": ["external_actual_operation_evidence_receipt_bodyfree_complete"] if claimed_from_real_operation else [],
        "claimed_from_real_operation_reason_ref_count": 1 if claimed_from_real_operation else 0,
        "claimed_from_real_operation_blocker_refs": claim_blockers,
        "claimed_from_real_operation_blocker_ref_count": len(claim_blockers),
        "actual_review_evidence_complete_from_real_operation_claimed_here_by_dmd_op02": False,
        "dmd_op02_does_not_inventory_final_completeness": True,
        "dmd_op02_does_not_resolve_final_branch": True,
        "dmd_op02_does_not_generate_body_full_packet": True,
        "dmd_op02_does_not_run_actual_local_human_review": True,
        "dmd_op02_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op02_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "branch_candidate_ref": branch_candidate_ref,
        "next_required_step": next_required_step,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMD-OP02 body-free candidate vs real-operation claim separation contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DMH18_DMD_OP02_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDMH18-DMD-OP02",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMH18_DMD_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF,
        source="P7-R54-AHR-PostDMH18-DMD-OP02",
    )
    for key in (
        "op18_ready_path_not_promoted_to_real_operation_claim",
        "helper_green_not_promoted_to_real_operation_claim",
        "candidate_supported_not_auto_promoted_to_claimed_from_real_operation",
        "dmd_op02_does_not_inventory_final_completeness",
        "dmd_op02_does_not_resolve_final_branch",
        "dmd_op02_does_not_generate_body_full_packet",
        "dmd_op02_does_not_run_actual_local_human_review",
        "dmd_op02_does_not_create_receipts_rows_or_disposal",
        "dmd_op02_does_not_execute_postcr22_ex_reentry_or_r52",
        "dmd_op02_does_not_start_p5_p6_p8_p7_or_release",
        "dmd_op02_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP02 required true boundary changed: {key}")
    for key in ("actual_review_evidence_complete_from_real_operation_claimed_here_by_dmd_op02",):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP02 claimed-here boundary changed: {key}")
    if tuple(data.get("dmd_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 allowed status refs changed")
    for field, count_field in (
        ("dmd_op02_reason_refs", "dmd_op02_reason_ref_count"),
        ("dmd_op02_blocker_refs", "dmd_op02_blocker_ref_count"),
        ("candidate_supported_source_refs", "candidate_supported_source_ref_count"),
        ("external_actual_operation_evidence_receipt_forbidden_payload_key_paths", "external_actual_operation_evidence_receipt_forbidden_payload_key_path_count"),
        ("claimed_from_real_operation_reason_refs", "claimed_from_real_operation_reason_ref_count"),
        ("claimed_from_real_operation_blocker_refs", "claimed_from_real_operation_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP02 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 not-yet steps changed")
    status_ref = data.get("dmd_op02_status_ref")
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REAL_OPERATION_CLAIM_SUPPORTED_REF:
        if data.get("claimed_from_real_operation") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 supported claim must mark claimed_from_real_operation")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 supported claim branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP03_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 supported claim next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_CANDIDATE_ONLY_REF:
        if data.get("claimed_from_real_operation") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 candidate-only cannot claim real operation")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 candidate-only branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP03_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 candidate-only next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_INCOMPLETE_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 incomplete next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP02_STATUS_REPAIR_REQUIRED_REF:
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 repair branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 repair next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP02 unknown status ref")
    return True


def _op03_status_and_blockers(op02: Mapping[str, Any] | None, receipt: Mapping[str, Any] | None, session_id: str) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    reasons: list[str] = []
    op02_valid = False
    if isinstance(op02, Mapping):
        try:
            op02_valid = assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract(op02) is True
        except ValueError:
            op02_valid = False
    if not op02_valid:
        blockers.append("dmd_op03_op02_claim_separation_invalid_or_missing")
        return P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF, blockers, reasons
    if not isinstance(receipt, Mapping):
        blockers.append("dmd_op03_actual_operation_evidence_receipt_missing")
        return P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF, blockers, reasons
    if _scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree_optional"):
        blockers.append("dmd_op03_actual_operation_evidence_receipt_forbidden_payload_key_detected")
    if not _receipt_source_kind_valid(receipt):
        blockers.append("dmd_op03_actual_operation_evidence_receipt_invalid_source_kind")
    if any(receipt.get(field) is False for field in P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REPAIR_GUARD_FIELD_REFS):
        blockers.append("dmd_op03_actual_operation_evidence_receipt_bodyfree_guard_failed")
    if blockers:
        return P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF, list(dict.fromkeys(blockers)), reasons
    incomplete: list[str] = []
    if not _receipt_has_expected_schema(receipt):
        incomplete.append("dmd_op03_actual_operation_evidence_receipt_schema_missing_or_invalid")
    for field, passed in _receipt_count_pass_refs(receipt).items():
        if not passed:
            incomplete.append(f"dmd_op03_{field}_incomplete")
    for field in (
        "created_from_real_operation",
        "actual_source_guard_passed",
        "actual_human_review_executed_by_person",
        "disposal_purge_receipt_accepted",
        "body_free",
    ):
        if receipt.get(field) is not True:
            incomplete.append(f"dmd_op03_{field}_missing_or_false")
    if _clean_ref(receipt.get("review_session_id"), default="receipt_review_session_missing", max_length=220) != session_id:
        incomplete.append("dmd_op03_review_session_id_inconsistent")
    if _receipt_ref(receipt) == "actual_operation_evidence_receipt_ref_missing":
        incomplete.append("dmd_op03_operation_receipt_ref_missing")
    if incomplete:
        return P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF, list(dict.fromkeys(incomplete)), reasons
    reasons.append("dmd_op03_actual_operation_evidence_receipt_complete_by_counts_and_guards")
    return P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF, [], reasons


def build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
    *,
    candidate_vs_real_operation_evidence_claim_separation: Mapping[str, Any] | None = None,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP03 body-free actual evidence receipt completeness inventory."""

    session_id = _safe_review_session_id(review_session_id)
    receipt = actual_operation_evidence_receipt_bodyfree_optional if isinstance(actual_operation_evidence_receipt_bodyfree_optional, Mapping) else None
    op02 = candidate_vs_real_operation_evidence_claim_separation
    if op02 is None:
        op02 = build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            actual_operation_evidence_receipt_bodyfree_optional=receipt,
            review_session_id=session_id,
        )
    status_ref, blockers, reasons = _op03_status_and_blockers(op02 if isinstance(op02, Mapping) else None, receipt, session_id)
    count_values = _receipt_count_values(receipt)
    count_pass = _receipt_count_pass_refs(receipt)
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree_optional") if isinstance(receipt, Mapping) else []
    repair_required = status_ref == P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF
    missing_or_incomplete = status_ref in (
        P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF,
        P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF,
    )
    complete = status_ref == P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF
    if repair_required:
        actual_status_ref = P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_REPAIR_REQUIRED_REF
        branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    elif complete:
        actual_status_ref = P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_COMPLETE_CANDIDATE_REF
        branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP04_REF
    else:
        actual_status_ref = P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_INCOMPLETE_REF
        branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    operation_receipt_ref = _receipt_ref(receipt)
    review_session_ref = _clean_ref(receipt.get("review_session_id") if isinstance(receipt, Mapping) else "", default="receipt_review_session_missing", max_length=220)
    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else "", default="op02_schema_missing", max_length=260),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else "", default="op02_material_missing", max_length=260),
        "op02_status_ref": _clean_ref(op02.get("dmd_op02_status_ref") if isinstance(op02, Mapping) else "", default="op02_status_missing", max_length=220),
        "op02_ready": bool(isinstance(op02, Mapping) and op02.get("dmd_op02_ready") is True),
        "op02_claimed_from_real_operation": bool(isinstance(op02, Mapping) and op02.get("claimed_from_real_operation") is True),
        "op02_branch_candidate_ref": _clean_ref(op02.get("branch_candidate_ref") if isinstance(op02, Mapping) else "", default="op02_branch_candidate_missing", max_length=220),
        "op02_next_required_step": _clean_ref(op02.get("next_required_step") if isinstance(op02, Mapping) else "", default="op02_next_required_step_missing", max_length=220),
        "dmd_op03_status_ref": status_ref,
        "dmd_op03_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP03_ALLOWED_STATUS_REFS),
        "dmd_op03_ready": complete,
        "actual_evidence_status_ref": actual_status_ref,
        "actual_evidence_receipt_present": isinstance(receipt, Mapping),
        "actual_evidence_receipt_schema_version": _receipt_schema_version(receipt),
        "actual_evidence_receipt_ref": operation_receipt_ref,
        "actual_evidence_receipt_source_kind_ref": _receipt_source_kind_ref(receipt),
        "actual_evidence_receipt_source_kind_valid": _receipt_source_kind_valid(receipt),
        "actual_evidence_receipt_invalid_source_detected": isinstance(receipt, Mapping) and not _receipt_source_kind_valid(receipt),
        "actual_evidence_receipt_forbidden_payload_key_paths": [_clean_ref(path, max_length=260) for path in forbidden_paths],
        "actual_evidence_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "actual_operation_receipt_present": isinstance(receipt, Mapping),
        "created_from_real_operation": bool(isinstance(receipt, Mapping) and receipt.get("created_from_real_operation") is True),
        "actual_source_guard_passed": bool(isinstance(receipt, Mapping) and receipt.get("actual_source_guard_passed") is True),
        "actual_human_review_executed_by_person": bool(isinstance(receipt, Mapping) and receipt.get("actual_human_review_executed_by_person") is True),
        "reviewed_case_count": count_values["reviewed_case_count"],
        "selection_row_count": count_values["selection_row_count"],
        "sanitized_review_result_row_count": count_values["sanitized_review_result_row_count"],
        "rating_row_count": count_values["rating_row_count"],
        "question_need_observation_row_count": count_values["question_need_observation_row_count"],
        "reviewed_case_count_is_24": count_pass["reviewed_case_count_is_24"],
        "selection_row_count_is_24": count_pass["selection_row_count_is_24"],
        "sanitized_review_result_row_count_is_24": count_pass["sanitized_review_result_row_count_is_24"],
        "rating_row_count_is_24": count_pass["rating_row_count_is_24"],
        "question_need_observation_row_count_is_24": count_pass["question_need_observation_row_count_is_24"],
        "disposal_purge_receipt_accepted": bool(isinstance(receipt, Mapping) and receipt.get("disposal_purge_receipt_accepted") is True),
        "no_body_leak_validation_passed": bool(isinstance(receipt, Mapping) and receipt.get("no_body_leak_validation_passed") is True),
        "no_question_text_validation_passed": bool(isinstance(receipt, Mapping) and receipt.get("no_question_text_validation_passed") is True),
        "no_path_hash_validation_passed": bool(isinstance(receipt, Mapping) and receipt.get("no_path_hash_validation_passed") is True),
        "no_terminal_output_body_validation_passed": bool(isinstance(receipt, Mapping) and receipt.get("no_terminal_output_body_validation_passed") is True),
        "no_touch_validation_passed": bool(isinstance(receipt, Mapping) and receipt.get("no_touch_validation_passed") is True),
        "review_session_id_consistent": review_session_ref == session_id,
        "operation_receipt_ref_consistent": operation_receipt_ref != "actual_operation_evidence_receipt_ref_missing",
        "actual_evidence_receipt_count_complete": all(count_pass.values()),
        "actual_evidence_receipt_guard_complete": _receipt_required_true_fields_pass(receipt),
        "actual_evidence_receipt_complete": complete,
        "actual_evidence_receipt_missing_or_incomplete": missing_or_incomplete,
        "bodyfree_evidence_boundary_repair_required": repair_required,
        "evidence_incomplete_continue_or_retry_required": missing_or_incomplete,
        "complete_candidate_for_manual_decision_branch": complete,
        "downstream_manual_decision_required_without_auto_execution": False,
        "dmd_op03_reason_refs": reasons,
        "dmd_op03_reason_ref_count": len(reasons),
        "dmd_op03_blocker_refs": blockers,
        "dmd_op03_blocker_ref_count": len(blockers),
        "branch_candidate_ref": branch_candidate_ref,
        "next_required_step": next_required_step,
        "dmd_op03_does_not_resolve_final_branch": True,
        "dmd_op03_does_not_generate_body_full_packet": True,
        "dmd_op03_does_not_run_actual_local_human_review": True,
        "dmd_op03_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op03_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMD-OP03 body-free actual evidence receipt completeness inventory contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DMH18_DMD_OP03_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDMH18-DMD-OP03",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMH18_DMD_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP03_STEP_REF,
        source="P7-R54-AHR-PostDMH18-DMD-OP03",
    )
    for key in (
        "dmd_op03_does_not_resolve_final_branch",
        "dmd_op03_does_not_generate_body_full_packet",
        "dmd_op03_does_not_run_actual_local_human_review",
        "dmd_op03_does_not_create_receipts_rows_or_disposal",
        "dmd_op03_does_not_execute_postcr22_ex_reentry_or_r52",
        "dmd_op03_does_not_start_p5_p6_p8_p7_or_release",
        "dmd_op03_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP03 required true boundary changed: {key}")
    if data.get("downstream_manual_decision_required_without_auto_execution") is not False:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 cannot claim final downstream manual decision")
    if tuple(data.get("dmd_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 allowed status refs changed")
    for field, count_field in (
        ("actual_evidence_receipt_forbidden_payload_key_paths", "actual_evidence_receipt_forbidden_payload_key_path_count"),
        ("dmd_op03_reason_refs", "dmd_op03_reason_ref_count"),
        ("dmd_op03_blocker_refs", "dmd_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP03 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 not-yet steps changed")
    for field in P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS:
        expected_key = f"{field}_is_24"
        if data.get(expected_key) is not (data.get(field) == P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP03 count flag mismatch: {expected_key}")
    status_ref = data.get("dmd_op03_status_ref")
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF:
        if data.get("actual_evidence_receipt_complete") is not True or data.get("dmd_op03_ready") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 complete status changed")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 complete branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP04_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 complete next step changed")
        for key in (
            "actual_evidence_receipt_present",
            "actual_evidence_receipt_source_kind_valid",
            "created_from_real_operation",
            "actual_source_guard_passed",
            "actual_human_review_executed_by_person",
            "disposal_purge_receipt_accepted",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_path_hash_validation_passed",
            "no_terminal_output_body_validation_passed",
            "no_touch_validation_passed",
            "review_session_id_consistent",
            "operation_receipt_ref_consistent",
            "actual_evidence_receipt_count_complete",
            "actual_evidence_receipt_guard_complete",
            "complete_candidate_for_manual_decision_branch",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP03 complete required true changed: {key}")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_REPAIR_REQUIRED_REF:
        if data.get("bodyfree_evidence_boundary_repair_required") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 repair flag changed")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 repair branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 repair next step changed")
    elif status_ref in (P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF, P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF):
        if data.get("evidence_incomplete_continue_or_retry_required") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 incomplete flag changed")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 incomplete branch candidate changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 incomplete next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP03 unknown status ref")
    return True



# DMD-OP04 / DMD-OP05 are intentionally appended after the OP00-OP03 helper
# layer. This keeps the previous implementation surface untouched while adding
# the next two body-free triage scans.
P7_R54_AHR_POST_DMH18_DMD_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op04_bodyfree_leak_invalid_source_scan.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op05_downstream_promotion_claim_scan.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:5]
P7_R54_AHR_POST_DMH18_DMD_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[5:]
P7_R54_AHR_POST_DMH18_DMD_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:6]
P7_R54_AHR_POST_DMH18_DMD_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[6:]
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP05_REF: Final = P7_R54_AHR_POST_DMH18_DMD_OP05_STEP_REF
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP06_REF: Final = P7_R54_AHR_POST_DMH18_DMD_OP06_STEP_REF
P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_SCAN_CLEAR_REF: Final = "DMD_OP04_BODYFREE_LEAK_INVALID_SOURCE_SCAN_CLEAR"
P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_REPAIR_REQUIRED_REF: Final = "DMD_OP04_BODYFREE_LEAK_OR_INVALID_SOURCE_REPAIR_REQUIRED"
P7_R54_AHR_POST_DMH18_DMD_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_SCAN_CLEAR_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_SCAN_CLEAR_REF: Final = "DMD_OP05_DOWNSTREAM_PROMOTION_CLAIM_SCAN_CLEAR"
P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_REPAIR_REQUIRED_REF: Final = "DMD_OP05_DOWNSTREAM_PROMOTION_CLAIM_REPAIR_REQUIRED"
P7_R54_AHR_POST_DMH18_DMD_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_SCAN_CLEAR_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMH18_DMD_BODYFREE_SAFE_REF_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "material_id",
        "review_session_id",
        "operation_receipt_ref",
        "actual_evidence_receipt_ref",
        "external_actual_operation_evidence_receipt_ref",
        "source_kind_ref",
        "actual_evidence_receipt_source_kind_ref",
        "external_actual_operation_evidence_receipt_source_kind_ref",
        "op18_material_ref",
        "op18_result_memo_ref",
        "op03_material_ref",
        "op04_material_ref",
    }
)
P7_R54_AHR_POST_DMH18_DMD_PROMOTION_SCAN_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS,
        *P7_R54_AHR_POST_DMH18_DMD_OP18_PROMOTION_CLAIM_FIELD_REFS,
    }
)
P7_R54_AHR_POST_DMH18_DMD_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_ready", "op03_actual_evidence_status_ref",
    "op03_branch_candidate_ref", "op03_next_required_step", "dmd_op04_status_ref", "dmd_op04_allowed_status_refs",
    "dmd_op04_ready", "bodyfree_leak_invalid_source_scan_passed", "bodyfree_leak_or_invalid_source_detected",
    "forbidden_payload_key_paths", "forbidden_payload_key_path_count", "safe_ref_shape_violation_paths",
    "safe_ref_shape_violation_path_count", "invalid_source_kind_refs", "invalid_source_kind_ref_count",
    "invalid_source_detected", "body_text_or_question_text_shape_detected", "path_hash_or_terminal_output_shape_detected",
    "actual_evidence_receipt_complete_candidate_carried_from_op03", "evidence_incomplete_carried_from_op03",
    "bodyfree_evidence_boundary_repair_required", "evidence_incomplete_continue_or_retry_required",
    "complete_candidate_for_manual_decision_branch", "downstream_manual_decision_required_without_auto_execution",
    "dmd_op04_reason_refs", "dmd_op04_reason_ref_count", "dmd_op04_blocker_refs", "dmd_op04_blocker_ref_count",
    "branch_candidate_ref", "next_required_step", "dmd_op04_does_not_resolve_final_branch",
    "dmd_op04_does_not_generate_body_full_packet", "dmd_op04_does_not_run_actual_local_human_review",
    "dmd_op04_does_not_create_receipts_rows_or_disposal", "dmd_op04_does_not_execute_postcr22_ex_reentry_or_r52",
    "dmd_op04_does_not_start_p5_p6_p8_p7_or_release", "dmd_op04_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "public_contract", "post_dmh18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMH18_DMD_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_ready", "op04_branch_candidate_ref",
    "op04_next_required_step", "dmd_op05_status_ref", "dmd_op05_allowed_status_refs", "dmd_op05_ready",
    "downstream_promotion_claim_scan_passed", "downstream_promotion_claim_detected", "downstream_promotion_claim_paths",
    "downstream_promotion_claim_path_count", "promotion_claim_repair_required", "bodyfree_scan_repair_carried_from_op04",
    "bodyfree_evidence_boundary_repair_required", "evidence_incomplete_continue_or_retry_required",
    "complete_candidate_for_manual_decision_branch", "downstream_manual_decision_required_without_auto_execution",
    "dmd_op05_reason_refs", "dmd_op05_reason_ref_count", "dmd_op05_blocker_refs", "dmd_op05_blocker_ref_count",
    "branch_candidate_ref", "next_required_step", "dmd_op05_does_not_resolve_final_branch",
    "dmd_op05_does_not_generate_body_full_packet", "dmd_op05_does_not_run_actual_local_human_review",
    "dmd_op05_does_not_create_receipts_rows_or_disposal", "dmd_op05_does_not_execute_postcr22_ex_reentry_or_r52",
    "dmd_op05_does_not_start_p5_p6_p8_p7_or_release", "dmd_op05_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "public_contract", "post_dmh18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _path_key_ref(path: str) -> str:
    key = path.rsplit(".", 1)[-1]
    if "[" in key:
        key = key.split("[", 1)[0]
    return key


def _safe_ref_field_path(path: str) -> bool:
    key = _path_key_ref(path)
    return key in P7_R54_AHR_POST_DMH18_DMD_BODYFREE_SAFE_REF_FIELD_REFS or key.endswith("_ref") or key.endswith("_id")


def _looks_like_local_path(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith(("/", "~/", "./", "../", "file://")):
        return True
    if "\\" in stripped:
        return True
    return len(stripped) >= 3 and stripped[1:3] == ":\\" and stripped[0].isalpha()


def _looks_like_raw_hash(value: str) -> bool:
    compact = value.strip()
    return len(compact) in {32, 40, 64, 128} and all(ch in "0123456789abcdefABCDEF" for ch in compact)


def _looks_like_terminal_output(value: str) -> bool:
    markers = (
        "Traceback (most recent call last)",
        "===== FAILURES =====",
        "==== FAILURES ====",
        "Captured stdout",
        "Captured stderr",
        "File \"",
    )
    return any(marker in value for marker in markers)


def _looks_like_body_text_in_safe_ref(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    if "\n" in stripped and len(stripped) > 40:
        return True
    if len(stripped) > 120 and len(stripped.split()) >= 10:
        return True
    sentence_markers = ("。", "、", "？", "！", "です", "ます")
    return any(marker in stripped for marker in sentence_markers)


def _scan_bodyfree_safe_ref_shape_violation_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            paths.extend(_scan_bodyfree_safe_ref_shape_violation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_bodyfree_safe_ref_shape_violation_paths(child, path=f"{path}[{index}]"))
    elif isinstance(value, str) and _safe_ref_field_path(path):
        if (
            _looks_like_local_path(value)
            or _looks_like_raw_hash(value)
            or _looks_like_terminal_output(value)
            or _looks_like_body_text_in_safe_ref(value)
        ):
            paths.append(path)
    return paths


def _scan_invalid_source_kind_refs(
    *,
    actual_evidence_receipt_completeness_inventory: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
) -> list[str]:
    invalid_refs: list[str] = []
    if isinstance(actual_evidence_receipt_completeness_inventory, Mapping):
        source_ref = actual_evidence_receipt_completeness_inventory.get("actual_evidence_receipt_source_kind_ref")
        if source_ref in P7_R54_AHR_POST_DMH18_DMD_INVALID_SOURCE_KIND_REFS:
            invalid_refs.append(_clean_ref(source_ref, max_length=180))
    if isinstance(actual_operation_evidence_receipt_bodyfree_optional, Mapping):
        source_ref = actual_operation_evidence_receipt_bodyfree_optional.get("source_kind_ref")
        if source_ref in P7_R54_AHR_POST_DMH18_DMD_INVALID_SOURCE_KIND_REFS:
            invalid_refs.append(_clean_ref(source_ref, max_length=180))
    return list(dict.fromkeys(invalid_refs))


def _promotion_claim_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_DMH18_DMD_PROMOTION_SCAN_FIELD_REFS and child is True:
                paths.append(child_path)
            paths.extend(_promotion_claim_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_promotion_claim_paths(child, path=f"{path}[{index}]"))
    return paths


def _dedupe_clean_paths(paths: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(_clean_ref(path, max_length=260) for path in paths))


def build_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan(
    *,
    actual_evidence_receipt_completeness_inventory: Mapping[str, Any] | None = None,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    op18_result_memo_downstream_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP04 body-free leak / invalid source scan material."""

    session_id = _safe_review_session_id(review_session_id)
    receipt = actual_operation_evidence_receipt_bodyfree_optional if isinstance(actual_operation_evidence_receipt_bodyfree_optional, Mapping) else None
    op03 = actual_evidence_receipt_completeness_inventory
    if op03 is None:
        op03 = build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            actual_operation_evidence_receipt_bodyfree_optional=receipt,
            review_session_id=session_id,
        )
    op03_valid = False
    if isinstance(op03, Mapping):
        try:
            op03_valid = assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract(op03) is True
        except ValueError:
            op03_valid = False

    scan_sources: list[tuple[str, Any]] = [("actual_evidence_receipt_completeness_inventory", op03)]
    if isinstance(op18_finalizer_bodyfree_intake, Mapping):
        scan_sources.append(("op18_finalizer_bodyfree_intake", op18_finalizer_bodyfree_intake))
    if isinstance(op18_result_memo_downstream_manual_decision_hold_finalizer, Mapping):
        scan_sources.append(("op18_result_memo_downstream_manual_decision_hold_finalizer", op18_result_memo_downstream_manual_decision_hold_finalizer))
    if isinstance(receipt, Mapping):
        scan_sources.append(("actual_operation_evidence_receipt_bodyfree_optional", receipt))

    forbidden_paths: list[str] = []
    safe_ref_paths: list[str] = []
    for source_ref, source_payload in scan_sources:
        forbidden_paths.extend(_scan_forbidden_payload_key_paths(source_payload, path=source_ref))
        safe_ref_paths.extend(_scan_bodyfree_safe_ref_shape_violation_paths(source_payload, path=source_ref))
    forbidden_paths = _dedupe_clean_paths(forbidden_paths)
    safe_ref_paths = _dedupe_clean_paths(safe_ref_paths)
    invalid_source_refs = _scan_invalid_source_kind_refs(
        actual_evidence_receipt_completeness_inventory=op03 if isinstance(op03, Mapping) else None,
        actual_operation_evidence_receipt_bodyfree_optional=receipt,
    )

    blockers: list[str] = []
    if not op03_valid:
        blockers.append("dmd_op04_op03_inventory_invalid_or_missing")
    if isinstance(op03, Mapping) and op03.get("bodyfree_evidence_boundary_repair_required") is True:
        blockers.append("dmd_op04_prior_inventory_repair_required")
    if forbidden_paths:
        blockers.append("dmd_op04_forbidden_payload_key_detected")
    if safe_ref_paths:
        blockers.append("dmd_op04_safe_ref_path_hash_terminal_or_body_text_shape_detected")
    if invalid_source_refs:
        blockers.append("dmd_op04_invalid_source_kind_detected")
    blockers = list(dict.fromkeys(blockers))

    repair_required = bool(blockers)
    op03_branch_candidate_ref = _clean_ref(
        op03.get("branch_candidate_ref") if isinstance(op03, Mapping) else "",
        default=P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF,
        max_length=220,
    )
    if repair_required:
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_REPAIR_REQUIRED_REF
        branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    else:
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_SCAN_CLEAR_REF
        branch_candidate_ref = op03_branch_candidate_ref
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP05_REF

    op03_status_ref = _clean_ref(op03.get("dmd_op03_status_ref") if isinstance(op03, Mapping) else "", default="op03_status_missing", max_length=220)
    complete_candidate = op03_status_ref == P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_COMPLETE_REF and not repair_required
    incomplete_carried = op03_status_ref in (
        P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_MISSING_REF,
        P7_R54_AHR_POST_DMH18_DMD_OP03_STATUS_INCOMPLETE_REF,
    ) and not repair_required
    reason_refs: list[str] = []
    if not repair_required:
        reason_refs.append("dmd_op04_bodyfree_leak_invalid_source_scan_clear")
    if complete_candidate:
        reason_refs.append("dmd_op04_complete_candidate_carried_without_downstream_execution")
    if incomplete_carried:
        reason_refs.append("dmd_op04_incomplete_evidence_carried_without_promotion")

    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": _clean_ref(op03.get("schema_version") if isinstance(op03, Mapping) else "", default="op03_schema_missing", max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id") if isinstance(op03, Mapping) else "", default="op03_material_missing", max_length=260),
        "op03_status_ref": op03_status_ref,
        "op03_ready": bool(isinstance(op03, Mapping) and op03.get("dmd_op03_ready") is True),
        "op03_actual_evidence_status_ref": _clean_ref(op03.get("actual_evidence_status_ref") if isinstance(op03, Mapping) else "", default="op03_actual_evidence_status_missing", max_length=220),
        "op03_branch_candidate_ref": op03_branch_candidate_ref,
        "op03_next_required_step": _clean_ref(op03.get("next_required_step") if isinstance(op03, Mapping) else "", default="op03_next_required_step_missing", max_length=220),
        "dmd_op04_status_ref": status_ref,
        "dmd_op04_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP04_ALLOWED_STATUS_REFS),
        "dmd_op04_ready": not repair_required,
        "bodyfree_leak_invalid_source_scan_passed": not repair_required,
        "bodyfree_leak_or_invalid_source_detected": repair_required,
        "forbidden_payload_key_paths": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "safe_ref_shape_violation_paths": safe_ref_paths,
        "safe_ref_shape_violation_path_count": len(safe_ref_paths),
        "invalid_source_kind_refs": invalid_source_refs,
        "invalid_source_kind_ref_count": len(invalid_source_refs),
        "invalid_source_detected": bool(invalid_source_refs),
        "body_text_or_question_text_shape_detected": bool(safe_ref_paths),
        "path_hash_or_terminal_output_shape_detected": bool(safe_ref_paths),
        "actual_evidence_receipt_complete_candidate_carried_from_op03": complete_candidate,
        "evidence_incomplete_carried_from_op03": incomplete_carried,
        "bodyfree_evidence_boundary_repair_required": repair_required,
        "evidence_incomplete_continue_or_retry_required": incomplete_carried,
        "complete_candidate_for_manual_decision_branch": complete_candidate,
        "downstream_manual_decision_required_without_auto_execution": False,
        "dmd_op04_reason_refs": reason_refs,
        "dmd_op04_reason_ref_count": len(reason_refs),
        "dmd_op04_blocker_refs": blockers,
        "dmd_op04_blocker_ref_count": len(blockers),
        "branch_candidate_ref": branch_candidate_ref,
        "next_required_step": next_required_step,
        "dmd_op04_does_not_resolve_final_branch": True,
        "dmd_op04_does_not_generate_body_full_packet": True,
        "dmd_op04_does_not_run_actual_local_human_review": True,
        "dmd_op04_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op04_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan_contract(data: Mapping[str, Any]) -> bool:
    """Assert DMD-OP04 body-free leak / invalid source scan contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DMH18_DMD_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMH18-DMD-OP04")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMH18_DMD_OP04_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP04_STEP_REF, source="P7-R54-AHR-PostDMH18-DMD-OP04")
    for key in ("dmd_op04_does_not_resolve_final_branch", "dmd_op04_does_not_generate_body_full_packet", "dmd_op04_does_not_run_actual_local_human_review", "dmd_op04_does_not_create_receipts_rows_or_disposal", "dmd_op04_does_not_execute_postcr22_ex_reentry_or_r52", "dmd_op04_does_not_start_p5_p6_p8_p7_or_release", "dmd_op04_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP04 required true boundary changed: {key}")
    if data.get("downstream_manual_decision_required_without_auto_execution") is not False:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 cannot claim downstream manual decision")
    if tuple(data.get("dmd_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 allowed status refs changed")
    for field, count_field in (("forbidden_payload_key_paths", "forbidden_payload_key_path_count"), ("safe_ref_shape_violation_paths", "safe_ref_shape_violation_path_count"), ("invalid_source_kind_refs", "invalid_source_kind_ref_count"), ("dmd_op04_reason_refs", "dmd_op04_reason_ref_count"), ("dmd_op04_blocker_refs", "dmd_op04_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP04 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP04_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 not-yet steps changed")
    status_ref = data.get("dmd_op04_status_ref")
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_SCAN_CLEAR_REF:
        if data.get("dmd_op04_ready") is not True or data.get("bodyfree_leak_invalid_source_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 clear status must be ready")
        if data.get("bodyfree_leak_or_invalid_source_detected") is not False or data.get("bodyfree_evidence_boundary_repair_required") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 clear status cannot carry repair")
        if data.get("dmd_op04_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 clear status cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP05_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 clear next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP04_STATUS_REPAIR_REQUIRED_REF:
        if data.get("dmd_op04_ready") is not False or data.get("bodyfree_leak_invalid_source_scan_passed") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 repair status cannot be ready")
        if data.get("bodyfree_leak_or_invalid_source_detected") is not True or data.get("bodyfree_evidence_boundary_repair_required") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 repair flag changed")
        if not data.get("dmd_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 repair status must carry blockers")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 repair next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP04 unknown status ref")
    return True


def build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan(
    *,
    bodyfree_leak_invalid_source_scan: Mapping[str, Any] | None = None,
    actual_evidence_receipt_completeness_inventory: Mapping[str, Any] | None = None,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    op18_result_memo_downstream_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    downstream_manual_decision_material_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP05 downstream promotion claim scan material."""

    session_id = _safe_review_session_id(review_session_id)
    op04 = bodyfree_leak_invalid_source_scan
    if op04 is None:
        op04 = build_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan(
            actual_evidence_receipt_completeness_inventory=actual_evidence_receipt_completeness_inventory,
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            op18_result_memo_downstream_manual_decision_hold_finalizer=op18_result_memo_downstream_manual_decision_hold_finalizer,
            actual_operation_evidence_receipt_bodyfree_optional=actual_operation_evidence_receipt_bodyfree_optional,
            review_session_id=session_id,
        )
    op04_valid = False
    if isinstance(op04, Mapping):
        try:
            op04_valid = assert_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan_contract(op04) is True
        except ValueError:
            op04_valid = False

    scan_sources: list[tuple[str, Any]] = [("bodyfree_leak_invalid_source_scan", op04)]
    if isinstance(op18_finalizer_bodyfree_intake, Mapping):
        scan_sources.append(("op18_finalizer_bodyfree_intake", op18_finalizer_bodyfree_intake))
    if isinstance(op18_result_memo_downstream_manual_decision_hold_finalizer, Mapping):
        scan_sources.append(("op18_result_memo_downstream_manual_decision_hold_finalizer", op18_result_memo_downstream_manual_decision_hold_finalizer))
    if isinstance(actual_operation_evidence_receipt_bodyfree_optional, Mapping):
        scan_sources.append(("actual_operation_evidence_receipt_bodyfree_optional", actual_operation_evidence_receipt_bodyfree_optional))
    if isinstance(downstream_manual_decision_material_optional, Mapping):
        scan_sources.append(("downstream_manual_decision_material_optional", downstream_manual_decision_material_optional))

    promotion_paths: list[str] = []
    for source_ref, source_payload in scan_sources:
        promotion_paths.extend(_promotion_claim_paths(source_payload, path=source_ref))
    promotion_paths = _dedupe_clean_paths(promotion_paths)

    blockers: list[str] = []
    if not op04_valid:
        blockers.append("dmd_op05_op04_scan_invalid_or_missing")
    if isinstance(op04, Mapping) and op04.get("bodyfree_evidence_boundary_repair_required") is True:
        blockers.append("dmd_op05_prior_bodyfree_scan_repair_required")
    if promotion_paths:
        blockers.append("dmd_op05_downstream_promotion_claim_detected")
    blockers = list(dict.fromkeys(blockers))

    repair_required = bool(blockers)
    op04_branch_candidate_ref = _clean_ref(op04.get("branch_candidate_ref") if isinstance(op04, Mapping) else "", default=P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF, max_length=220)
    if repair_required:
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_REPAIR_REQUIRED_REF
        branch_candidate_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    else:
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_SCAN_CLEAR_REF
        branch_candidate_ref = op04_branch_candidate_ref
        next_required_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP06_REF

    complete_candidate = branch_candidate_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF and not repair_required
    incomplete_carried = branch_candidate_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF and not repair_required
    reason_refs: list[str] = []
    if not repair_required:
        reason_refs.append("dmd_op05_downstream_promotion_claim_scan_clear")
    if complete_candidate:
        reason_refs.append("dmd_op05_complete_candidate_carried_to_branch_resolver_without_auto_execution")
    if incomplete_carried:
        reason_refs.append("dmd_op05_incomplete_evidence_carried_to_branch_resolver_without_promotion")

    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": _clean_ref(op04.get("schema_version") if isinstance(op04, Mapping) else "", default="op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id") if isinstance(op04, Mapping) else "", default="op04_material_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("dmd_op04_status_ref") if isinstance(op04, Mapping) else "", default="op04_status_missing", max_length=220),
        "op04_ready": bool(isinstance(op04, Mapping) and op04.get("dmd_op04_ready") is True),
        "op04_branch_candidate_ref": op04_branch_candidate_ref,
        "op04_next_required_step": _clean_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else "", default="op04_next_required_step_missing", max_length=220),
        "dmd_op05_status_ref": status_ref,
        "dmd_op05_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP05_ALLOWED_STATUS_REFS),
        "dmd_op05_ready": not repair_required,
        "downstream_promotion_claim_scan_passed": not repair_required,
        "downstream_promotion_claim_detected": bool(promotion_paths),
        "downstream_promotion_claim_paths": promotion_paths,
        "downstream_promotion_claim_path_count": len(promotion_paths),
        "promotion_claim_repair_required": bool(promotion_paths),
        "bodyfree_scan_repair_carried_from_op04": isinstance(op04, Mapping) and op04.get("bodyfree_evidence_boundary_repair_required") is True,
        "bodyfree_evidence_boundary_repair_required": repair_required,
        "evidence_incomplete_continue_or_retry_required": incomplete_carried,
        "complete_candidate_for_manual_decision_branch": complete_candidate,
        "downstream_manual_decision_required_without_auto_execution": False,
        "dmd_op05_reason_refs": reason_refs,
        "dmd_op05_reason_ref_count": len(reason_refs),
        "dmd_op05_blocker_refs": blockers,
        "dmd_op05_blocker_ref_count": len(blockers),
        "branch_candidate_ref": branch_candidate_ref,
        "next_required_step": next_required_step,
        "dmd_op05_does_not_resolve_final_branch": True,
        "dmd_op05_does_not_generate_body_full_packet": True,
        "dmd_op05_does_not_run_actual_local_human_review": True,
        "dmd_op05_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op05_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan_contract(data: Mapping[str, Any]) -> bool:
    """Assert DMD-OP05 downstream promotion claim scan contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DMH18_DMD_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMH18-DMD-OP05")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMH18_DMD_OP05_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP05_STEP_REF, source="P7-R54-AHR-PostDMH18-DMD-OP05")
    for key in ("dmd_op05_does_not_resolve_final_branch", "dmd_op05_does_not_generate_body_full_packet", "dmd_op05_does_not_run_actual_local_human_review", "dmd_op05_does_not_create_receipts_rows_or_disposal", "dmd_op05_does_not_execute_postcr22_ex_reentry_or_r52", "dmd_op05_does_not_start_p5_p6_p8_p7_or_release", "dmd_op05_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP05 required true boundary changed: {key}")
    if data.get("downstream_manual_decision_required_without_auto_execution") is not False:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 cannot claim downstream manual decision")
    if tuple(data.get("dmd_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 allowed status refs changed")
    for field, count_field in (("downstream_promotion_claim_paths", "downstream_promotion_claim_path_count"), ("dmd_op05_reason_refs", "dmd_op05_reason_ref_count"), ("dmd_op05_blocker_refs", "dmd_op05_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP05 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP05_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 not-yet steps changed")
    status_ref = data.get("dmd_op05_status_ref")
    if status_ref == P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_SCAN_CLEAR_REF:
        if data.get("dmd_op05_ready") is not True or data.get("downstream_promotion_claim_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 clear status must be ready")
        if data.get("downstream_promotion_claim_detected") is not False or data.get("promotion_claim_repair_required") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 clear status cannot carry promotion claim")
        if data.get("dmd_op05_blocker_refs") != [] or data.get("downstream_promotion_claim_paths") != []:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 clear status cannot carry blockers or paths")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP06_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 clear next step changed")
    elif status_ref == P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_REPAIR_REQUIRED_REF:
        if data.get("dmd_op05_ready") is not False or data.get("downstream_promotion_claim_scan_passed") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 repair status cannot be ready")
        if data.get("bodyfree_evidence_boundary_repair_required") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 repair flag changed")
        if not data.get("dmd_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 repair status must carry blockers")
        if data.get("branch_candidate_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 repair next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP05 unknown status ref")
    return True



# DMD-OP06 / DMD-OP07 are intentionally appended after the OP04/OP05 scan
# layer. OP06 resolves exactly one branch with repair precedence, and OP07
# materializes that already-resolved branch without executing downstream work.
P7_R54_AHR_POST_DMH18_DMD_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op06_deterministic_branch_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op07_manual_decision_materialization.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:7]
P7_R54_AHR_POST_DMH18_DMD_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[7:]
P7_R54_AHR_POST_DMH18_DMD_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[:8]
P7_R54_AHR_POST_DMH18_DMD_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS[8:]
P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF: Final = (
    "downstream_manual_decision_required_without_auto_execution"
)

P7_R54_AHR_POST_DMH18_DMD_BRANCH_RESOLVER_PRIORITY_REFS: Final[tuple[str, ...]] = (
    "repair_required",
    "evidence_incomplete_or_not_claimed_from_real_operation",
    "evidence_complete_manual_decision_required_no_auto_execution",
)
P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_REPAIR_REQUIRED_REF: Final = "DMD_OP06_BRANCH_RESOLVED_BODYFREE_BOUNDARY_REPAIR_REQUIRED"
P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_INCOMPLETE_REF: Final = (
    "DMD_OP06_BRANCH_RESOLVED_EVIDENCE_INCOMPLETE_OR_NOT_CLAIMED_FROM_REAL_OPERATION"
)
P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_COMPLETE_REF: Final = (
    "DMD_OP06_BRANCH_RESOLVED_EVIDENCE_COMPLETE_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION"
)
P7_R54_AHR_POST_DMH18_DMD_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_COMPLETE_REF,
)
P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_REPAIR_REQUIRED_REF: Final = "DMD_OP07_MANUAL_DECISION_MATERIALIZED_BODYFREE_BOUNDARY_REPAIR_REQUIRED"
P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_INCOMPLETE_REF: Final = (
    "DMD_OP07_MANUAL_DECISION_MATERIALIZED_EVIDENCE_INCOMPLETE_OR_NOT_CLAIMED_FROM_REAL_OPERATION"
)
P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_COMPLETE_REF: Final = (
    "DMD_OP07_MANUAL_DECISION_MATERIALIZED_DOWNSTREAM_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION"
)
P7_R54_AHR_POST_DMH18_DMD_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_COMPLETE_REF,
)

P7_R54_AHR_POST_DMH18_DMD_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_candidate_supported", "op02_claimed_from_real_operation",
    "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_actual_evidence_status_ref", "op03_complete_candidate_for_manual_decision_branch",
    "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_ready", "op04_branch_candidate_ref", "op04_next_required_step",
    "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_ready", "op05_branch_candidate_ref", "op05_next_required_step",
    "op05_downstream_promotion_claim_scan_passed", "op05_bodyfree_evidence_boundary_repair_required", "op05_evidence_incomplete_continue_or_retry_required",
    "op05_complete_candidate_for_manual_decision_branch", "op18_intake_status_ref", "dmd_op06_status_ref", "dmd_op06_allowed_status_refs",
    "dmd_op06_ready", "dmd_op06_branch_resolved", "resolver_priority_refs", "resolver_priority_ref_count", "repair_precedence_applied",
    "incomplete_precedence_applied", "complete_branch_selected_after_no_repair_no_incomplete", "candidate_supported", "claimed_from_real_operation",
    "actual_evidence_status_ref", "branch_ref", "branch_reason_refs", "branch_reason_ref_count", "branch_blocker_refs", "branch_blocker_ref_count",
    "next_required_step", "bodyfree_evidence_boundary_repair_required", "evidence_incomplete_continue_or_retry_required",
    "downstream_manual_decision_required_without_auto_execution", "dmd_op06_does_not_materialize_manual_decision", "dmd_op06_does_not_generate_body_full_packet",
    "dmd_op06_does_not_run_actual_local_human_review", "dmd_op06_does_not_create_receipts_rows_or_disposal", "dmd_op06_does_not_execute_postcr22_ex_reentry_or_r52",
    "dmd_op06_does_not_start_p5_p6_p8_p7_or_release", "dmd_op06_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "public_contract", "post_dmh18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMH18_DMD_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_ready", "op06_branch_ref", "op06_next_required_step",
    "op18_intake_status_ref", "dmd_op07_status_ref", "dmd_op07_allowed_status_refs", "dmd_op07_ready",
    "manual_decision_materialized", "manual_decision_materialization_bodyfree_closed", "manual_decision_materialization_from_branch_resolver",
    "manual_decision_materialization_does_not_auto_execute_downstream", "candidate_supported", "claimed_from_real_operation", "actual_evidence_status_ref",
    "branch_ref", "branch_reason_refs", "branch_reason_ref_count", "branch_blocker_refs", "branch_blocker_ref_count", "next_required_step",
    "bodyfree_evidence_boundary_repair_required", "evidence_incomplete_continue_or_retry_required", "downstream_manual_decision_required_without_auto_execution",
    "postcr22_ex07_ex18_reentry_ready_candidate_carried_without_execution", "r52_handoff_candidate_carried_without_execution",
    "dmd_op07_does_not_generate_body_full_packet", "dmd_op07_does_not_run_actual_local_human_review", "dmd_op07_does_not_create_receipts_rows_or_disposal",
    "dmd_op07_does_not_execute_postcr22_ex_reentry_or_r52", "dmd_op07_does_not_start_p5_p6_p8_p7_or_release",
    "dmd_op07_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "public_contract", "post_dmh18_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _op06_build_lower_materials(
    *,
    downstream_promotion_claim_scan: Mapping[str, Any] | None = None,
    bodyfree_leak_invalid_source_scan: Mapping[str, Any] | None = None,
    actual_evidence_receipt_completeness_inventory: Mapping[str, Any] | None = None,
    candidate_vs_real_operation_evidence_claim_separation: Mapping[str, Any] | None = None,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    op18_result_memo_downstream_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    downstream_manual_decision_material_optional: Mapping[str, Any] | None = None,
    review_session_id: str,
) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None, Mapping[str, Any] | None, Mapping[str, Any] | None]:
    """Build missing lower body-free materials needed for OP06 without downstream execution."""

    receipt = actual_operation_evidence_receipt_bodyfree_optional if isinstance(actual_operation_evidence_receipt_bodyfree_optional, Mapping) else None
    op02 = candidate_vs_real_operation_evidence_claim_separation
    if op02 is None:
        op02 = build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation(
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            actual_operation_evidence_receipt_bodyfree_optional=receipt,
            review_session_id=review_session_id,
        )
    op03 = actual_evidence_receipt_completeness_inventory
    if op03 is None:
        op03 = build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory(
            candidate_vs_real_operation_evidence_claim_separation=op02 if isinstance(op02, Mapping) else None,
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            actual_operation_evidence_receipt_bodyfree_optional=receipt,
            review_session_id=review_session_id,
        )
    op04 = bodyfree_leak_invalid_source_scan
    if op04 is None:
        op04 = build_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan(
            actual_evidence_receipt_completeness_inventory=op03 if isinstance(op03, Mapping) else None,
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            op18_result_memo_downstream_manual_decision_hold_finalizer=op18_result_memo_downstream_manual_decision_hold_finalizer,
            actual_operation_evidence_receipt_bodyfree_optional=receipt,
            review_session_id=review_session_id,
        )
    op05 = downstream_promotion_claim_scan
    if op05 is None:
        op05 = build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan(
            bodyfree_leak_invalid_source_scan=op04 if isinstance(op04, Mapping) else None,
            actual_evidence_receipt_completeness_inventory=op03 if isinstance(op03, Mapping) else None,
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            op18_result_memo_downstream_manual_decision_hold_finalizer=op18_result_memo_downstream_manual_decision_hold_finalizer,
            actual_operation_evidence_receipt_bodyfree_optional=receipt,
            downstream_manual_decision_material_optional=downstream_manual_decision_material_optional,
            review_session_id=review_session_id,
        )
    return op02, op03, op04, op05


def _op06_status_and_branch(
    op05: Mapping[str, Any] | None,
    *,
    op05_valid: bool,
) -> tuple[str, str, str, bool, bool, bool, list[str], list[str]]:
    """Return status, branch, next step, branch flags, reasons, blockers for OP06."""

    blockers: list[str] = []
    reasons: list[str] = []
    if not op05_valid:
        blockers.append("dmd_op06_op05_promotion_scan_invalid_or_missing")
    op05_branch = _clean_ref(
        op05.get("branch_candidate_ref") if isinstance(op05, Mapping) else "",
        default=P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF,
        max_length=220,
    )
    op05_blockers = [
        _clean_ref(ref, max_length=180)
        for ref in (op05.get("dmd_op05_blocker_refs") if isinstance(op05, Mapping) else []) or []
    ]
    repair_required = (
        bool(blockers)
        or op05_branch == P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        or bool(isinstance(op05, Mapping) and op05.get("bodyfree_evidence_boundary_repair_required") is True)
        or bool(isinstance(op05, Mapping) and op05.get("dmd_op05_status_ref") == P7_R54_AHR_POST_DMH18_DMD_OP05_STATUS_REPAIR_REQUIRED_REF)
    )
    if repair_required:
        blockers.extend(op05_blockers or ["dmd_op06_bodyfree_or_promotion_repair_required_by_prior_scan"])
        blockers = list(dict.fromkeys(blockers))
        reasons.append("dmd_op06_repair_precedence_selected_before_incomplete_or_complete_branch")
        return (
            P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF,
            True,
            False,
            False,
            reasons,
            blockers,
        )

    incomplete = (
        op05_branch == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
        or bool(isinstance(op05, Mapping) and op05.get("evidence_incomplete_continue_or_retry_required") is True)
        or not bool(isinstance(op05, Mapping) and op05.get("complete_candidate_for_manual_decision_branch") is True)
    )
    if incomplete:
        blockers.append("dmd_op06_actual_evidence_incomplete_or_not_claimed_from_real_operation")
        if isinstance(op05, Mapping) and op05.get("evidence_incomplete_continue_or_retry_required") is True:
            blockers.append("dmd_op06_incomplete_evidence_carried_from_op05")
        blockers = list(dict.fromkeys(blockers))
        reasons.append("dmd_op06_incomplete_precedence_selected_after_no_repair")
        return (
            P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_INCOMPLETE_REF,
            P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF,
            P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF,
            False,
            True,
            False,
            reasons,
            blockers,
        )

    reasons.extend(
        [
            "dmd_op06_complete_candidate_survived_bodyfree_and_promotion_scans",
            "dmd_op06_downstream_manual_decision_required_without_auto_execution",
        ]
    )
    return (
        P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_COMPLETE_REF,
        P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF,
        P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
        False,
        False,
        True,
        reasons,
        [],
    )


def build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
    *,
    downstream_promotion_claim_scan: Mapping[str, Any] | None = None,
    bodyfree_leak_invalid_source_scan: Mapping[str, Any] | None = None,
    actual_evidence_receipt_completeness_inventory: Mapping[str, Any] | None = None,
    candidate_vs_real_operation_evidence_claim_separation: Mapping[str, Any] | None = None,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    op18_result_memo_downstream_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    downstream_manual_decision_material_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP06 deterministic branch resolver material."""

    session_id = _safe_review_session_id(review_session_id)
    op02, op03, op04, op05 = _op06_build_lower_materials(
        downstream_promotion_claim_scan=downstream_promotion_claim_scan,
        bodyfree_leak_invalid_source_scan=bodyfree_leak_invalid_source_scan,
        actual_evidence_receipt_completeness_inventory=actual_evidence_receipt_completeness_inventory,
        candidate_vs_real_operation_evidence_claim_separation=candidate_vs_real_operation_evidence_claim_separation,
        op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
        op18_result_memo_downstream_manual_decision_hold_finalizer=op18_result_memo_downstream_manual_decision_hold_finalizer,
        actual_operation_evidence_receipt_bodyfree_optional=actual_operation_evidence_receipt_bodyfree_optional,
        downstream_manual_decision_material_optional=downstream_manual_decision_material_optional,
        review_session_id=session_id,
    )
    op05_valid = False
    if isinstance(op05, Mapping):
        try:
            op05_valid = assert_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan_contract(op05) is True
        except ValueError:
            op05_valid = False

    status_ref, branch_ref, next_required_step, repair_branch, incomplete_branch, complete_branch, reasons, blockers = _op06_status_and_branch(
        op05 if isinstance(op05, Mapping) else None,
        op05_valid=op05_valid,
    )
    op05_complete_candidate = bool(isinstance(op05, Mapping) and op05.get("complete_candidate_for_manual_decision_branch") is True)
    candidate_supported = bool(isinstance(op02, Mapping) and op02.get("candidate_supported") is True) or op05_complete_candidate
    claimed_from_real_operation = bool(isinstance(op02, Mapping) and op02.get("claimed_from_real_operation") is True) or op05_complete_candidate
    if incomplete_branch and not claimed_from_real_operation:
        blockers = list(dict.fromkeys([*blockers, "dmd_op06_real_operation_evidence_claim_not_present"]))
    actual_status_ref = (
        P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_REPAIR_REQUIRED_REF
        if repair_branch
        else P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_INCOMPLETE_REF
        if incomplete_branch
        else P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_COMPLETE_CANDIDATE_REF
    )
    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else "", default="op02_schema_missing", max_length=260),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else "", default="op02_material_missing", max_length=260),
        "op02_status_ref": _clean_ref(op02.get("dmd_op02_status_ref") if isinstance(op02, Mapping) else "", default="op02_status_missing", max_length=220),
        "op02_candidate_supported": bool(isinstance(op02, Mapping) and op02.get("candidate_supported") is True),
        "op02_claimed_from_real_operation": bool(isinstance(op02, Mapping) and op02.get("claimed_from_real_operation") is True),
        "op03_schema_version": _clean_ref(op03.get("schema_version") if isinstance(op03, Mapping) else "", default="op03_schema_missing", max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id") if isinstance(op03, Mapping) else "", default="op03_material_missing", max_length=260),
        "op03_status_ref": _clean_ref(op03.get("dmd_op03_status_ref") if isinstance(op03, Mapping) else "", default="op03_status_missing", max_length=220),
        "op03_actual_evidence_status_ref": _clean_ref(op03.get("actual_evidence_status_ref") if isinstance(op03, Mapping) else "", default="op03_actual_evidence_status_missing", max_length=220),
        "op03_complete_candidate_for_manual_decision_branch": bool(isinstance(op03, Mapping) and op03.get("complete_candidate_for_manual_decision_branch") is True),
        "op04_schema_version": _clean_ref(op04.get("schema_version") if isinstance(op04, Mapping) else "", default="op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id") if isinstance(op04, Mapping) else "", default="op04_material_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("dmd_op04_status_ref") if isinstance(op04, Mapping) else "", default="op04_status_missing", max_length=220),
        "op04_ready": bool(isinstance(op04, Mapping) and op04.get("dmd_op04_ready") is True),
        "op04_branch_candidate_ref": _clean_ref(op04.get("branch_candidate_ref") if isinstance(op04, Mapping) else "", default="op04_branch_candidate_missing", max_length=220),
        "op04_next_required_step": _clean_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else "", default="op04_next_required_step_missing", max_length=220),
        "op05_schema_version": _clean_ref(op05.get("schema_version") if isinstance(op05, Mapping) else "", default="op05_schema_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id") if isinstance(op05, Mapping) else "", default="op05_material_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("dmd_op05_status_ref") if isinstance(op05, Mapping) else "", default="op05_status_missing", max_length=220),
        "op05_ready": bool(isinstance(op05, Mapping) and op05.get("dmd_op05_ready") is True),
        "op05_branch_candidate_ref": _clean_ref(op05.get("branch_candidate_ref") if isinstance(op05, Mapping) else "", default="op05_branch_candidate_missing", max_length=220),
        "op05_next_required_step": _clean_ref(op05.get("next_required_step") if isinstance(op05, Mapping) else "", default="op05_next_required_step_missing", max_length=220),
        "op05_downstream_promotion_claim_scan_passed": bool(isinstance(op05, Mapping) and op05.get("downstream_promotion_claim_scan_passed") is True),
        "op05_bodyfree_evidence_boundary_repair_required": bool(isinstance(op05, Mapping) and op05.get("bodyfree_evidence_boundary_repair_required") is True),
        "op05_evidence_incomplete_continue_or_retry_required": bool(isinstance(op05, Mapping) and op05.get("evidence_incomplete_continue_or_retry_required") is True),
        "op05_complete_candidate_for_manual_decision_branch": op05_complete_candidate,
        "op18_intake_status_ref": _clean_ref(op02.get("op01_status_ref") if isinstance(op02, Mapping) else "", default="op18_intake_status_missing", max_length=220),
        "dmd_op06_status_ref": status_ref,
        "dmd_op06_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP06_ALLOWED_STATUS_REFS),
        "dmd_op06_ready": True,
        "dmd_op06_branch_resolved": True,
        "resolver_priority_refs": list(P7_R54_AHR_POST_DMH18_DMD_BRANCH_RESOLVER_PRIORITY_REFS),
        "resolver_priority_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_BRANCH_RESOLVER_PRIORITY_REFS),
        "repair_precedence_applied": repair_branch,
        "incomplete_precedence_applied": incomplete_branch,
        "complete_branch_selected_after_no_repair_no_incomplete": complete_branch,
        "candidate_supported": candidate_supported,
        "claimed_from_real_operation": claimed_from_real_operation,
        "actual_evidence_status_ref": actual_status_ref,
        "branch_ref": branch_ref,
        "branch_reason_refs": reasons,
        "branch_reason_ref_count": len(reasons),
        "branch_blocker_refs": blockers,
        "branch_blocker_ref_count": len(blockers),
        "next_required_step": next_required_step,
        "bodyfree_evidence_boundary_repair_required": repair_branch,
        "evidence_incomplete_continue_or_retry_required": incomplete_branch,
        "downstream_manual_decision_required_without_auto_execution": complete_branch,
        "dmd_op06_does_not_materialize_manual_decision": True,
        "dmd_op06_does_not_generate_body_full_packet": True,
        "dmd_op06_does_not_run_actual_local_human_review": True,
        "dmd_op06_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op06_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract(data: Mapping[str, Any]) -> bool:
    """Assert DMD-OP06 deterministic branch resolver contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DMH18_DMD_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMH18-DMD-OP06")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMH18_DMD_OP06_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP06_STEP_REF, source="P7-R54-AHR-PostDMH18-DMD-OP06")
    for key in (
        "dmd_op06_does_not_materialize_manual_decision",
        "dmd_op06_does_not_generate_body_full_packet",
        "dmd_op06_does_not_run_actual_local_human_review",
        "dmd_op06_does_not_create_receipts_rows_or_disposal",
        "dmd_op06_does_not_execute_postcr22_ex_reentry_or_r52",
        "dmd_op06_does_not_start_p5_p6_p8_p7_or_release",
        "dmd_op06_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP06 required true boundary changed: {key}")
    if data.get("dmd_op06_ready") is not True or data.get("dmd_op06_branch_resolved") is not True:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 must resolve one branch")
    if tuple(data.get("dmd_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 allowed status refs changed")
    if tuple(data.get("resolver_priority_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_BRANCH_RESOLVER_PRIORITY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 resolver priority refs changed")
    for field, count_field in (("resolver_priority_refs", "resolver_priority_ref_count"), ("branch_reason_refs", "branch_reason_ref_count"), ("branch_blocker_refs", "branch_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP06 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP06_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 not-yet steps changed")
    flags = (data.get("bodyfree_evidence_boundary_repair_required"), data.get("evidence_incomplete_continue_or_retry_required"), data.get("downstream_manual_decision_required_without_auto_execution"))
    if flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 must select exactly one branch flag")
    branch_ref = data.get("branch_ref")
    status_ref = data.get("dmd_op06_status_ref")
    if branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
        if status_ref != P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_REPAIR_REQUIRED_REF or data.get("repair_precedence_applied") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 repair precedence changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF or not data.get("branch_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 repair branch changed")
    elif branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
        if status_ref != P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_INCOMPLETE_REF or data.get("incomplete_precedence_applied") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 incomplete precedence changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 incomplete next step changed")
    elif branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
        if status_ref != P7_R54_AHR_POST_DMH18_DMD_OP06_STATUS_EVIDENCE_COMPLETE_REF or data.get("complete_branch_selected_after_no_repair_no_incomplete") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 complete branch changed")
        if data.get("candidate_supported") is not True or data.get("claimed_from_real_operation") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 complete branch must have real-operation claim support")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 complete next step changed")
        if data.get("branch_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 complete branch cannot carry blockers")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP06 unknown branch ref")
    return True


def _op07_status_from_branch(branch_ref: str) -> str:
    if branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
        return P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_REPAIR_REQUIRED_REF
    if branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
        return P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_COMPLETE_REF
    return P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_INCOMPLETE_REF


def build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(
    *,
    deterministic_branch_resolver: Mapping[str, Any] | None = None,
    downstream_promotion_claim_scan: Mapping[str, Any] | None = None,
    bodyfree_leak_invalid_source_scan: Mapping[str, Any] | None = None,
    actual_evidence_receipt_completeness_inventory: Mapping[str, Any] | None = None,
    candidate_vs_real_operation_evidence_claim_separation: Mapping[str, Any] | None = None,
    op18_finalizer_bodyfree_intake: Mapping[str, Any] | None = None,
    op18_result_memo_downstream_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    actual_operation_evidence_receipt_bodyfree_optional: Mapping[str, Any] | None = None,
    downstream_manual_decision_material_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP07 body-free manual decision materialization."""

    session_id = _safe_review_session_id(review_session_id)
    op06 = deterministic_branch_resolver
    if op06 is None:
        op06 = build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver(
            downstream_promotion_claim_scan=downstream_promotion_claim_scan,
            bodyfree_leak_invalid_source_scan=bodyfree_leak_invalid_source_scan,
            actual_evidence_receipt_completeness_inventory=actual_evidence_receipt_completeness_inventory,
            candidate_vs_real_operation_evidence_claim_separation=candidate_vs_real_operation_evidence_claim_separation,
            op18_finalizer_bodyfree_intake=op18_finalizer_bodyfree_intake,
            op18_result_memo_downstream_manual_decision_hold_finalizer=op18_result_memo_downstream_manual_decision_hold_finalizer,
            actual_operation_evidence_receipt_bodyfree_optional=actual_operation_evidence_receipt_bodyfree_optional,
            downstream_manual_decision_material_optional=downstream_manual_decision_material_optional,
            review_session_id=session_id,
        )
    op06_valid = False
    if isinstance(op06, Mapping):
        try:
            op06_valid = assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract(op06) is True
        except ValueError:
            op06_valid = False
    branch_ref = _clean_ref(op06.get("branch_ref") if isinstance(op06, Mapping) else "", default=P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF, max_length=220)
    if not op06_valid:
        branch_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    repair_branch = branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    incomplete_branch = branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    complete_branch = branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF
    status_ref = _op07_status_from_branch(branch_ref)
    branch_reason_refs = [_clean_ref(ref, max_length=180) for ref in (op06.get("branch_reason_refs") if isinstance(op06, Mapping) else []) or []]
    branch_blocker_refs = [_clean_ref(ref, max_length=180) for ref in (op06.get("branch_blocker_refs") if isinstance(op06, Mapping) else []) or []]
    if not op06_valid:
        branch_blocker_refs = list(dict.fromkeys([*branch_blocker_refs, "dmd_op07_op06_branch_resolver_invalid_or_missing"]))
    next_required_step = (
        P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
        if repair_branch
        else P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
        if incomplete_branch
        else P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF
    )
    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": "p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": _clean_ref(op06.get("schema_version") if isinstance(op06, Mapping) else "", default="op06_schema_missing", max_length=260),
        "op06_material_ref": _clean_ref(op06.get("material_id") if isinstance(op06, Mapping) else "", default="op06_material_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06.get("dmd_op06_status_ref") if isinstance(op06, Mapping) else "", default="op06_status_missing", max_length=220),
        "op06_ready": bool(op06_valid and isinstance(op06, Mapping) and op06.get("dmd_op06_ready") is True),
        "op06_branch_ref": _clean_ref(op06.get("branch_ref") if isinstance(op06, Mapping) else "", default="op06_branch_missing", max_length=220),
        "op06_next_required_step": _clean_ref(op06.get("next_required_step") if isinstance(op06, Mapping) else "", default="op06_next_required_step_missing", max_length=220),
        "op18_intake_status_ref": _clean_ref(op06.get("op18_intake_status_ref") if isinstance(op06, Mapping) else "", default="op18_intake_status_missing", max_length=220),
        "dmd_op07_status_ref": status_ref,
        "dmd_op07_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP07_ALLOWED_STATUS_REFS),
        "dmd_op07_ready": True,
        "manual_decision_materialized": True,
        "manual_decision_materialization_bodyfree_closed": True,
        "manual_decision_materialization_from_branch_resolver": op06_valid,
        "manual_decision_materialization_does_not_auto_execute_downstream": True,
        "candidate_supported": bool(isinstance(op06, Mapping) and op06.get("candidate_supported") is True),
        "claimed_from_real_operation": bool(isinstance(op06, Mapping) and op06.get("claimed_from_real_operation") is True),
        "actual_evidence_status_ref": (
            P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_REPAIR_REQUIRED_REF
            if repair_branch
            else P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_INCOMPLETE_REF
            if incomplete_branch
            else P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_COMPLETE_CANDIDATE_REF
        ),
        "branch_ref": branch_ref,
        "branch_reason_refs": branch_reason_refs,
        "branch_reason_ref_count": len(branch_reason_refs),
        "branch_blocker_refs": branch_blocker_refs,
        "branch_blocker_ref_count": len(branch_blocker_refs),
        "next_required_step": next_required_step,
        "bodyfree_evidence_boundary_repair_required": repair_branch,
        "evidence_incomplete_continue_or_retry_required": incomplete_branch,
        "downstream_manual_decision_required_without_auto_execution": complete_branch,
        "postcr22_ex07_ex18_reentry_ready_candidate_carried_without_execution": complete_branch,
        "r52_handoff_candidate_carried_without_execution": complete_branch,
        "dmd_op07_does_not_generate_body_full_packet": True,
        "dmd_op07_does_not_run_actual_local_human_review": True,
        "dmd_op07_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op07_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(data: Mapping[str, Any]) -> bool:
    """Assert DMD-OP07 body-free manual decision materialization contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DMH18_DMD_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMH18-DMD-OP07")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMH18_DMD_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP07_STEP_REF, source="P7-R54-AHR-PostDMH18-DMD-OP07")
    for key in (
        "manual_decision_materialized",
        "manual_decision_materialization_bodyfree_closed",
        "manual_decision_materialization_does_not_auto_execute_downstream",
        "dmd_op07_does_not_generate_body_full_packet",
        "dmd_op07_does_not_run_actual_local_human_review",
        "dmd_op07_does_not_create_receipts_rows_or_disposal",
        "dmd_op07_does_not_execute_postcr22_ex_reentry_or_r52",
        "dmd_op07_does_not_start_p5_p6_p8_p7_or_release",
        "dmd_op07_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP07 required true boundary changed: {key}")
    if tuple(data.get("dmd_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 allowed status refs changed")
    for field, count_field in (("branch_reason_refs", "branch_reason_ref_count"), ("branch_blocker_refs", "branch_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP07 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP07_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMH18_DMD_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 not-yet steps changed")
    flags = (data.get("bodyfree_evidence_boundary_repair_required"), data.get("evidence_incomplete_continue_or_retry_required"), data.get("downstream_manual_decision_required_without_auto_execution"))
    if flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 must materialize exactly one branch flag")
    branch_ref = data.get("branch_ref")
    status_ref = data.get("dmd_op07_status_ref")
    if branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
        if status_ref != P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 repair status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF or not data.get("branch_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 repair branch changed")
    elif branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
        if status_ref != P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_INCOMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 incomplete status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 incomplete next step changed")
    elif branch_ref == P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
        if status_ref != P7_R54_AHR_POST_DMH18_DMD_OP07_STATUS_EVIDENCE_COMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 complete status changed")
        if data.get("candidate_supported") is not True or data.get("claimed_from_real_operation") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 complete branch must keep real-operation claim support")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 complete next step changed")
        if data.get("postcr22_ex07_ex18_reentry_executed_here") is not False or data.get("r52_actual_execution_started_here") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 complete branch cannot execute downstream")
        if data.get("p5_final_allowed") is not False or data.get("p6_start_allowed") is not False or data.get("p8_start_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 complete branch cannot promote P5/P6/P8")
    else:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP07 unknown branch ref")
    return True

build_p7_r54_ahr_post_dmh18_downstream_manual_decision_scope_no_touch_no_promotion_refreeze_bodyfree = (
    build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_scope_no_touch_no_promotion_refreeze_bodyfree_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_op18_finalizer_bodyfree_intake = (
    build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_op18_finalizer_bodyfree_intake_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_candidate_vs_real_operation_evidence_claim_separation = (
    build_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_candidate_vs_real_operation_evidence_claim_separation_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op02_candidate_vs_real_operation_evidence_claim_separation_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_actual_evidence_receipt_completeness_inventory = (
    build_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_actual_evidence_receipt_completeness_inventory_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op03_actual_evidence_receipt_completeness_inventory_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_leak_invalid_source_scan = (
    build_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_leak_invalid_source_scan_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op04_bodyfree_leak_invalid_source_scan_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_downstream_promotion_claim_scan = (
    build_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_downstream_promotion_claim_scan_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op05_downstream_promotion_claim_scan_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_deterministic_branch_resolver = (
    build_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_deterministic_branch_resolver_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op06_deterministic_branch_resolver_contract
)
build_p7_r54_ahr_post_dmh18_downstream_manual_decision_manual_decision_materialization = (
    build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_manual_decision_materialization_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract
)

# DMD-OP08 closes the Post-DMH18 manual decision triage result as a body-free
# memo/test/regression summary.  It records only supplied body-free validation
# summaries.  It does not run pytest, compileall, actual review, packet
# generation, row materialization, PostCR22 re-entry, R52, P5/P6/P8/P7, or release.
P7_R54_AHR_POST_DMH18_DMD_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmh18.downstream_manual_decision."
    "dmd_op08_bodyfree_result_memo_target_tests_regression_closure.bodyfree.v1"
)
P7_R54_AHR_POST_DMH18_DMD_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMH18_DMD_STEP_REFS
P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_CLOSED_REF: Final = "DMD_OP08_BODYFREE_RESULT_MEMO_TARGET_TESTS_REGRESSION_CLOSED"
P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_INCOMPLETE_OR_UNVERIFIED_REF: Final = (
    "DMD_OP08_RESULT_MEMO_TARGET_TESTS_REGRESSION_INCOMPLETE_OR_UNVERIFIED"
)
P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_REPAIR_REQUIRED_REF: Final = "DMD_OP08_BODYFREE_RESULT_MEMO_REPAIR_REQUIRED"
P7_R54_AHR_POST_DMH18_DMD_OP08_INCOMPLETE_NEXT_STEP_REF: Final = (
    "record_external_target_tests_selected_regression_and_compileall_status_before_result_memo_closure"
)
P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF: Final = "passed_bodyfree_count_only"
P7_R54_AHR_POST_DMH18_DMD_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_CLOSED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_INCOMPLETE_OR_UNVERIFIED_REF,
    P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostDMH18_DownstreamManualDecision_ActualEvidenceStatusTriage_DMD_OP00_OP08_Result_20260703.md"
)
P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS: Final[tuple[str, ...]] = (
    "implementation_scope",
    "changed_files",
    "target_tests",
    "selected_regression",
    "compileall",
    "op18_intake_status",
    "candidate_vs_real_operation_claim_status",
    "actual_evidence_receipt_inventory_status",
    "bodyfree_leak_invalid_source_scan_status",
    "promotion_claim_scan_status",
    "branch_decision_status",
    "next_required_step",
    "not_claimed_boundary",
    "not_executed_boundary",
    "unverified_boundary",
)
P7_R54_AHR_POST_DMH18_DMD_OP08_CHANGED_FILE_REFS: Final[dict[str, tuple[str, ...]]] = {
    "modified": (
        "post_dmh18_dmd_service_helper_op08_modified",
    ),
    "new": (
        "post_dmh18_dmd_op08_result_target_test_added",
        "post_dmh18_dmd_op00_op08_bodyfree_result_memo_added",
    ),
    "deleted": (),
}
P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS: Final[tuple[str, ...]] = (
    "dmd_op00_op01_target",
    "dmd_op02_op03_target",
    "dmd_op04_op05_target",
    "dmd_op06_op07_target",
    "dmd_op08_target",
)
P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS: Final[tuple[str, ...]] = (
    "dmh_op18_selected_regression",
    "dmh_op16_op17_selected_regression",
    "pmn_op22_op23_selected_regression",
)
P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_EXECUTED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_generation",
    "actual_local_human_review_execution",
    "actual_operation_receipt_creation",
    "actual_rows_creation",
    "actual_disposal_purge_execution",
    "postcr22_ex07_ex18_reentry_execution",
    "r52_actual_execution",
    "p5_finalization",
    "p6_start",
    "p8_start",
    "p8_question_design",
    "p8_question_implementation",
    "p7_complete",
    "release_decision",
)
P7_R54_AHR_POST_DMH18_DMD_OP08_UNVERIFIED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REFS: Final[frozenset[str]] = frozenset(
    {"passed", P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF}
)
P7_R54_AHR_POST_DMH18_DMD_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_contract_valid", "op07_branch_ref",
    "op07_next_required_step", "op18_intake_status_ref", "dmd_op08_status_ref", "dmd_op08_allowed_status_refs",
    "dmd_op08_ready", "result_memo_ref", "result_memo_bodyfree_closed", "result_memo_sections_fixed",
    "result_memo_section_refs", "result_memo_section_ref_count", "implementation_scope", "changed_files", "target_tests",
    "selected_regression", "compileall", "op18_intake_status", "candidate_vs_real_operation_claim_status",
    "actual_evidence_receipt_inventory_status", "bodyfree_leak_invalid_source_scan_status", "promotion_claim_scan_status",
    "branch_decision_status", "next_required_step", "not_executed_boundary_refs", "not_executed_boundary_ref_count",
    "not_executed_boundary", "unverified_boundary_refs", "unverified_boundary_ref_count", "unverified_boundary",
    "target_test_group_refs", "target_test_group_ref_count", "target_test_result_status_refs", "target_test_result_status_ref_count",
    "target_test_result_count_refs", "target_test_result_count_ref_count", "target_tests_summary_bodyfree_recorded",
    "target_tests_closed_by_external_status_summary", "target_tests_closed", "selected_regression_group_refs", "selected_regression_group_ref_count",
    "selected_regression_result_status_refs", "selected_regression_result_status_ref_count", "selected_regression_result_count_refs",
    "selected_regression_result_count_ref_count", "selected_regression_summary_bodyfree_recorded",
    "selected_regression_closed_by_external_status_summary", "selected_regression_closed", "compileall_result_status_ref", "compileall_result_count_ref",
    "compileall_summary_bodyfree_recorded", "compileall_closed_by_external_status_summary", "compileall_closed", "candidate_supported",
    "claimed_from_real_operation", "actual_evidence_status_ref", "branch_ref", "branch_reason_refs", "branch_reason_ref_count",
    "branch_blocker_refs", "branch_blocker_ref_count", "bodyfree_evidence_boundary_repair_required",
    "evidence_incomplete_continue_or_retry_required", "downstream_manual_decision_required_without_auto_execution",
    "dmd_op08_helper_does_not_run_pytest_or_compileall", "dmd_op08_does_not_generate_body_full_packet",
    "dmd_op08_does_not_run_actual_local_human_review", "dmd_op08_does_not_create_receipts_rows_or_disposal",
    "dmd_op08_does_not_execute_postcr22_ex_reentry_or_r52", "dmd_op08_does_not_start_p5_p6_p8_p7_or_release",
    "dmd_op08_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "public_contract",
    "post_dmh18_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _op08_clean_status_map(
    supplied: Mapping[str, Any] | None,
    *,
    required_keys: Sequence[str],
    default_status_ref: str = "not_run_by_helper",
) -> dict[str, str]:
    source = supplied if isinstance(supplied, Mapping) else {}
    result: dict[str, str] = {}
    for key in required_keys:
        clean_key = _clean_ref(key, max_length=180)
        result[clean_key] = _clean_ref(source.get(key, default_status_ref), default=default_status_ref, max_length=180)
    return result


def _op08_clean_count_map(
    supplied: Mapping[str, Any] | None,
    *,
    required_keys: Sequence[str],
) -> dict[str, int]:
    source = supplied if isinstance(supplied, Mapping) else {}
    result: dict[str, int] = {}
    for key in required_keys:
        clean_key = _clean_ref(key, max_length=180)
        try:
            value = int(source.get(key, 0))
        except (TypeError, ValueError):
            value = 0
        result[clean_key] = max(0, value)
    return result


def _op08_all_passed(status_map: Mapping[str, str]) -> bool:
    return bool(status_map) and all(value in P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REFS for value in status_map.values())


def _op08_changed_files_summary() -> dict[str, Any]:
    modified = tuple(P7_R54_AHR_POST_DMH18_DMD_OP08_CHANGED_FILE_REFS["modified"])
    new = tuple(P7_R54_AHR_POST_DMH18_DMD_OP08_CHANGED_FILE_REFS["new"])
    deleted = tuple(P7_R54_AHR_POST_DMH18_DMD_OP08_CHANGED_FILE_REFS["deleted"])
    return {
        "modified_file_refs": list(modified),
        "modified_file_ref_count": len(modified),
        "new_file_refs": list(new),
        "new_file_ref_count": len(new),
        "deleted_file_refs": list(deleted),
        "deleted_file_ref_count": len(deleted),
    }


def _op08_false_boundary(refs: Sequence[str]) -> dict[str, bool]:
    return {ref: False for ref in refs}


def _op08_contract_valid(op07: Mapping[str, Any] | None) -> bool:
    if not isinstance(op07, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization_contract(op07) is True
    except ValueError:
        return False


def build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
    *,
    manual_decision_materialization: Mapping[str, Any] | None = None,
    target_test_result_status_refs: Mapping[str, Any] | None = None,
    target_test_result_count_refs: Mapping[str, Any] | None = None,
    selected_regression_result_status_refs: Mapping[str, Any] | None = None,
    selected_regression_result_count_refs: Mapping[str, Any] | None = None,
    compileall_result_status_ref: Any = None,
    compileall_result_count_ref: Any = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMD-OP08 body-free result memo / target-test / regression closure material."""

    session_id = _safe_review_session_id(review_session_id)
    op07 = manual_decision_materialization if isinstance(manual_decision_materialization, Mapping) else None
    if op07 is None:
        op07 = build_p7_r54_ahr_post_dmh18_dmd_op07_manual_decision_materialization(review_session_id=session_id)
    op07_valid = _op08_contract_valid(op07)
    forbidden_paths = _scan_forbidden_payload_key_paths(op07, path="op07_material") if isinstance(op07, Mapping) else []

    target_status_map = _op08_clean_status_map(
        target_test_result_status_refs,
        required_keys=P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS,
    )
    target_count_map = _op08_clean_count_map(
        target_test_result_count_refs,
        required_keys=P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS,
    )
    regression_status_map = _op08_clean_status_map(
        selected_regression_result_status_refs,
        required_keys=P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS,
    )
    regression_count_map = _op08_clean_count_map(
        selected_regression_result_count_refs,
        required_keys=P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS,
    )
    compile_status = _clean_ref(compileall_result_status_ref, default="not_run_by_helper", max_length=180)
    compile_count = _clean_ref(compileall_result_count_ref, default="not_applicable", max_length=180)

    target_closed = _op08_all_passed(target_status_map)
    regression_closed = _op08_all_passed(regression_status_map)
    compile_closed = compile_status in P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REFS
    repair_required = not op07_valid or bool(forbidden_paths)
    all_validation_closed = target_closed and regression_closed and compile_closed

    if repair_required:
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_REPAIR_REQUIRED_REF
        ready = False
        branch_ref = P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
        branch_reason_refs = ["dmd_op08_requires_valid_bodyfree_op07_material_before_result_memo_closure"]
        branch_blocker_refs = ["dmd_op08_op07_manual_decision_material_missing_or_invalid"]
        if forbidden_paths:
            branch_blocker_refs.append("dmd_op08_op07_forbidden_payload_key_detected")
        candidate_supported = bool(op07.get("candidate_supported")) if isinstance(op07, Mapping) else False
        claimed_from_real_operation = False
        actual_evidence_status_ref = P7_R54_AHR_POST_DMH18_DMD_ACTUAL_EVIDENCE_STATUS_REPAIR_REQUIRED_REF
        bodyfree_repair = True
        evidence_incomplete = False
        downstream_manual = False
        op18_status_ref = _clean_ref(op07.get("op18_intake_status_ref") if isinstance(op07, Mapping) else None, default="unknown_op18_intake_status")
    else:
        assert isinstance(op07, Mapping)
        status_ref = P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_CLOSED_REF if all_validation_closed else P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
        ready = all_validation_closed
        branch_ref = _clean_ref(op07.get("branch_ref"), max_length=220)
        next_step = _clean_ref(op07.get("next_required_step"), max_length=220)
        branch_reason_refs = list(op07.get("branch_reason_refs") or [])
        if all_validation_closed:
            branch_reason_refs.append("dmd_op08_bodyfree_result_memo_target_tests_regression_closure_recorded")
        else:
            branch_reason_refs.append("dmd_op08_waits_for_external_target_tests_regression_compileall_status")
        branch_blocker_refs = list(op07.get("branch_blocker_refs") or [])
        if not all_validation_closed:
            branch_blocker_refs.append("dmd_op08_external_validation_status_not_closed")
        candidate_supported = op07.get("candidate_supported") is True
        claimed_from_real_operation = op07.get("claimed_from_real_operation") is True
        actual_evidence_status_ref = _clean_ref(op07.get("actual_evidence_status_ref"), max_length=220)
        bodyfree_repair = op07.get("bodyfree_evidence_boundary_repair_required") is True
        evidence_incomplete = op07.get("evidence_incomplete_continue_or_retry_required") is True
        downstream_manual = op07.get("downstream_manual_decision_required_without_auto_execution") is True
        op18_status_ref = _clean_ref(op07.get("op18_intake_status_ref"), max_length=220)

    branch_reason_refs = list(dict.fromkeys(_clean_ref(ref, max_length=220) for ref in branch_reason_refs))
    branch_blocker_refs = list(dict.fromkeys(_clean_ref(ref, max_length=220) for ref in branch_blocker_refs))

    return {
        "schema_version": P7_R54_AHR_POST_DMH18_DMD_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "step": P7_R54_AHR_POST_DMH18_DMD_STEP,
        "scope": P7_R54_AHR_POST_DMH18_DMD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMH18_DMD_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMH18_DMD_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMH18_DMD_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMH18_DMD_PHASE,
        "material_id": f"p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_schema_version": _clean_ref(op07.get("schema_version") if isinstance(op07, Mapping) else None, default="missing_op07_schema_version", max_length=260),
        "op07_material_ref": _clean_ref(op07.get("material_id") if isinstance(op07, Mapping) else None, default="missing_op07_material", max_length=260),
        "op07_status_ref": _clean_ref(op07.get("dmd_op07_status_ref") if isinstance(op07, Mapping) else None, default="missing_op07_status", max_length=220),
        "op07_contract_valid": op07_valid,
        "op07_branch_ref": _clean_ref(op07.get("branch_ref") if isinstance(op07, Mapping) else None, default="missing_op07_branch", max_length=220),
        "op07_next_required_step": _clean_ref(op07.get("next_required_step") if isinstance(op07, Mapping) else None, default="missing_op07_next_step", max_length=220),
        "op18_intake_status_ref": op18_status_ref,
        "dmd_op08_status_ref": status_ref,
        "dmd_op08_allowed_status_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_ALLOWED_STATUS_REFS),
        "dmd_op08_ready": ready,
        "result_memo_ref": P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_REF,
        "result_memo_bodyfree_closed": all_validation_closed,
        "result_memo_sections_fixed": True,
        "result_memo_section_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS),
        "result_memo_section_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS),
        "implementation_scope": {
            "dmd_op00_to_op08_only": True,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "r52_actual_execution_started_here": False,
            "p5_p6_p7_release_promoted": False,
        },
        "changed_files": _op08_changed_files_summary(),
        "target_tests": {
            "target_test_group_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS),
            "target_test_result_status_refs": dict(target_status_map),
            "target_test_result_count_refs": dict(target_count_map),
            "pytest_execution_run_by_helper": False,
        },
        "selected_regression": {
            "selected_regression_group_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS),
            "selected_regression_result_status_refs": dict(regression_status_map),
            "selected_regression_result_count_refs": dict(regression_count_map),
            "pytest_execution_run_by_helper": False,
        },
        "compileall": {
            "compileall_result_status_ref": compile_status,
            "compileall_result_count_ref": compile_count,
            "compileall_execution_run_by_helper": False,
            "terminal_output_body_included": False,
        },
        "op18_intake_status": {
            "op18_intake_status_ref": op18_status_ref,
            "op18_ready_path_not_promoted_to_real_operation_claim": True,
        },
        "candidate_vs_real_operation_claim_status": {
            "candidate_supported": candidate_supported,
            "claimed_from_real_operation": claimed_from_real_operation,
            "candidate_supported_not_promoted_to_claimed_from_real_operation": True,
        },
        "actual_evidence_receipt_inventory_status": {
            "actual_evidence_status_ref": actual_evidence_status_ref,
            "actual_review_evidence_complete_from_real_operation_claimed_here": False,
        },
        "bodyfree_leak_invalid_source_scan_status": {
            "bodyfree_evidence_boundary_repair_required": bodyfree_repair,
            "body_free_markers": _body_free_markers(),
        },
        "promotion_claim_scan_status": {
            "manual_decision_auto_executes_downstream": False,
            "postcr22_ex07_ex18_reentry_executed_here": False,
            "r52_actual_execution_started_here": False,
            "p5_final_allowed": False,
            "p6_start_allowed": False,
            "p8_start_allowed": False,
            "p7_complete": False,
            "release_allowed": False,
        },
        "branch_decision_status": {
            "branch_ref": branch_ref,
            "branch_reason_refs": branch_reason_refs,
            "branch_reason_ref_count": len(branch_reason_refs),
            "branch_blocker_refs": branch_blocker_refs,
            "branch_blocker_ref_count": len(branch_blocker_refs),
            "next_required_step": next_step,
        },
        "next_required_step": next_step,
        "not_executed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_EXECUTED_BOUNDARY_REFS),
        "not_executed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_EXECUTED_BOUNDARY_REFS),
        "not_executed_boundary": _op08_false_boundary(P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_EXECUTED_BOUNDARY_REFS),
        "unverified_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_OP08_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary": _op08_false_boundary(P7_R54_AHR_POST_DMH18_DMD_OP08_UNVERIFIED_BOUNDARY_REFS),
        "target_test_group_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS),
        "target_test_group_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS),
        "target_test_result_status_refs": dict(target_status_map),
        "target_test_result_status_ref_count": len(target_status_map),
        "target_test_result_count_refs": dict(target_count_map),
        "target_test_result_count_ref_count": len(target_count_map),
        "target_tests_summary_bodyfree_recorded": True,
        "target_tests_closed_by_external_status_summary": target_closed,
        "target_tests_closed": target_closed,
        "selected_regression_group_refs": list(P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS),
        "selected_regression_group_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS),
        "selected_regression_result_status_refs": dict(regression_status_map),
        "selected_regression_result_status_ref_count": len(regression_status_map),
        "selected_regression_result_count_refs": dict(regression_count_map),
        "selected_regression_result_count_ref_count": len(regression_count_map),
        "selected_regression_summary_bodyfree_recorded": True,
        "selected_regression_closed_by_external_status_summary": regression_closed,
        "selected_regression_closed": regression_closed,
        "compileall_result_status_ref": compile_status,
        "compileall_result_count_ref": compile_count,
        "compileall_summary_bodyfree_recorded": True,
        "compileall_closed_by_external_status_summary": compile_closed,
        "compileall_closed": compile_closed,
        "candidate_supported": candidate_supported,
        "claimed_from_real_operation": claimed_from_real_operation,
        "actual_evidence_status_ref": actual_evidence_status_ref,
        "branch_ref": branch_ref,
        "branch_reason_refs": branch_reason_refs,
        "branch_reason_ref_count": len(branch_reason_refs),
        "branch_blocker_refs": branch_blocker_refs,
        "branch_blocker_ref_count": len(branch_blocker_refs),
        "bodyfree_evidence_boundary_repair_required": bodyfree_repair,
        "evidence_incomplete_continue_or_retry_required": evidence_incomplete,
        "downstream_manual_decision_required_without_auto_execution": downstream_manual,
        "dmd_op08_helper_does_not_run_pytest_or_compileall": True,
        "dmd_op08_does_not_generate_body_full_packet": True,
        "dmd_op08_does_not_run_actual_local_human_review": True,
        "dmd_op08_does_not_create_receipts_rows_or_disposal": True,
        "dmd_op08_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "dmd_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "dmd_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_dmh18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMD-OP08 body-free result memo / target-test / regression closure contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DMH18_DMD_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMH18-DMD-OP08")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMH18_DMD_OP08_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMH18_DMD_OP08_STEP_REF,
        source="P7-R54-AHR-PostDMH18-DMD-OP08",
    )
    for key in (
        "result_memo_sections_fixed",
        "target_tests_summary_bodyfree_recorded",
        "selected_regression_summary_bodyfree_recorded",
        "compileall_summary_bodyfree_recorded",
        "dmd_op08_helper_does_not_run_pytest_or_compileall",
        "dmd_op08_does_not_generate_body_full_packet",
        "dmd_op08_does_not_run_actual_local_human_review",
        "dmd_op08_does_not_create_receipts_rows_or_disposal",
        "dmd_op08_does_not_execute_postcr22_ex_reentry_or_r52",
        "dmd_op08_does_not_start_p5_p6_p8_p7_or_release",
        "dmd_op08_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP08 required true boundary changed: {key}")
    if data.get("dmd_op08_status_ref") not in P7_R54_AHR_POST_DMH18_DMD_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 status ref changed")
    if tuple(data.get("dmd_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 allowed status refs changed")
    if tuple(data.get("result_memo_section_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 result memo section refs changed")
    if data.get("result_memo_section_ref_count") != len(P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 result memo section count changed")
    for section_ref in P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_SECTION_REFS:
        if section_ref not in data:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP08 missing section: {section_ref}")
    for field, count_field in (
        ("target_test_group_refs", "target_test_group_ref_count"),
        ("target_test_result_status_refs", "target_test_result_status_ref_count"),
        ("target_test_result_count_refs", "target_test_result_count_ref_count"),
        ("selected_regression_group_refs", "selected_regression_group_ref_count"),
        ("selected_regression_result_status_refs", "selected_regression_result_status_ref_count"),
        ("selected_regression_result_count_refs", "selected_regression_result_count_ref_count"),
        ("not_executed_boundary_refs", "not_executed_boundary_ref_count"),
        ("unverified_boundary_refs", "unverified_boundary_ref_count"),
        ("branch_reason_refs", "branch_reason_ref_count"),
        ("branch_blocker_refs", "branch_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        value = data.get(field) or []
        if isinstance(value, Mapping):
            length = len(value)
        else:
            length = len(value)
        if data.get(count_field) != length:
            raise ValueError(f"P7-R54-AHR-PostDMH18-DMD-OP08 {count_field} changed")
    if tuple(data.get("target_test_group_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 target test group refs changed")
    if tuple(data.get("selected_regression_group_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 selected regression group refs changed")
    if tuple(data.get("not_executed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_EXECUTED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 not-executed refs changed")
    if tuple(data.get("unverified_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_UNVERIFIED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 unverified refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 not-claimed refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 fixed non-promotion refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 not-claimed boundary must stay false")
    if any(value is not False for value in (data.get("not_executed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 not-executed boundary must stay false")
    if any(value is not False for value in (data.get("unverified_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 unverified boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMH18_DMD_OP08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 not-yet steps changed")
    if _scan_forbidden_payload_key_paths(data, path="dmd_op08"):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 forbidden payload key detected")
    if _scan_bodyfree_safe_ref_shape_violation_paths(data, path="dmd_op08"):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 unsafe body-free ref shape detected")
    flags = (
        data.get("bodyfree_evidence_boundary_repair_required"),
        data.get("evidence_incomplete_continue_or_retry_required"),
        data.get("downstream_manual_decision_required_without_auto_execution"),
    )
    if flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 must preserve exactly one branch flag")
    if data.get("target_tests_closed") != data.get("target_tests_closed_by_external_status_summary"):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 target test closure alias changed")
    if data.get("selected_regression_closed") != data.get("selected_regression_closed_by_external_status_summary"):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 selected regression closure alias changed")
    if data.get("compileall_closed") != data.get("compileall_closed_by_external_status_summary"):
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 compileall closure alias changed")
    if data.get("dmd_op08_status_ref") == P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_CLOSED_REF:
        if data.get("dmd_op08_ready") is not True or data.get("result_memo_bodyfree_closed") is not True:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 closed status must be ready and closed")
        if not (data.get("target_tests_closed_by_external_status_summary") and data.get("selected_regression_closed_by_external_status_summary") and data.get("compileall_closed_by_external_status_summary")):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 closed status requires external validation summaries")
    if data.get("dmd_op08_status_ref") == P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_INCOMPLETE_OR_UNVERIFIED_REF:
        if data.get("dmd_op08_ready") is not False or data.get("result_memo_bodyfree_closed") is not False:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 incomplete status must stay unclosed")
        if data.get("next_required_step") not in (
            P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF,
            P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF,
            P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
        ):
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 incomplete next step must preserve OP07 branch")
    if data.get("dmd_op08_status_ref") == P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_REPAIR_REQUIRED_REF:
        if data.get("branch_ref") != P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 repair status must use repair branch")
    if data.get("manual_decision_auto_executes_downstream") is not False:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 cannot auto-execute downstream")
    if data.get("p5_final_allowed") is not False or data.get("p6_start_allowed") is not False or data.get("p8_start_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostDMH18-DMD-OP08 cannot promote P5/P6/P8")
    return True


build_p7_r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_result_memo_target_tests_regression_closure = (
    build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure
)
assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_bodyfree_result_memo_target_tests_regression_closure_contract = (
    assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract
)
