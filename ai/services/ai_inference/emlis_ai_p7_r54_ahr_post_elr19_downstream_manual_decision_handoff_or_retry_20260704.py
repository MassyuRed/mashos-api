# -*- coding: utf-8 -*-
"""Post-ELR19 downstream manual decision handoff-or-retry helpers for DHR-OP00〜OP09.

DHR is intentionally a thin Post-ELR19 boundary.  It does not reimplement DMD,
execute DMD/R52, generate body-full packets, run actual local-only human review,
create receipts/rows/disposal evidence, start P5/P6/P8, complete P7, or allow
release.

* DHR-OP00 freezes the Post-ELR19 scope, no-touch boundary, and no-promotion
  boundary after ELR-OP19.  It only fixes what DHR is allowed to do next.
* DHR-OP01 intakes the ELR-OP19 result memo validation closure as body-free
  material.  It distinguishes closed / waiting / repair / missing-or-invalid
  OP19 material, carries count-only validation summaries, scans for body-like or
  promotion leakage, and keeps ELR-OP19 closure from being promoted into actual
  review execution or downstream execution evidence.
* DHR-OP02 intakes the ELR-OP18 downstream manual-decision hold without
  executing DMD/R52 or promoting release/P8.
* DHR-OP03 extracts only the body-free ELR-OP17 DMD-compatible receipt
  candidate shape. It does not confirm actual source evidence for downstream
  handoff; that remains DHR-OP04.
* DHR-OP06 deterministically resolves repair / wait / retry-or-start / manual
  DMD-handoff-ready / unresolved-hold without executing the branch target.
* DHR-OP07 materializes the selected branch into body-free manual decision
  material for a human operator, still without DMD/R52/P8/release promotion.
* DHR-OP08 materializes a body-free DMD handoff plan candidate only for
  handoff-ready branches. It never executes DMD or fakes a DMH-OP18 finalizer.
* DHR-OP09 closes the body-free result memo with count-only target, selected
  regression, and compileall summaries while keeping actual review, DMD/R52,
  P8, P7 completion, and release unverified/not started.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd


P7_R54_AHR_POST_ELR19_DHR_PHASE: Final = "P7"
P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_ELR19_DHR_STEP: Final = (
    "R54-AHR-PostELR19_DownstreamManualDecision_HandoffOrRetry_20260704"
)
P7_R54_AHR_POST_ELR19_DHR_SCOPE: Final = (
    "p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry"
)
P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND: Final = (
    "r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_bodyfree_boundary"
)
P7_R54_AHR_POST_ELR19_DHR_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postelr19_dhr_session_20260704_current_received_282_94_267_180_v1"
)

P7_R54_AHR_POST_ELR19_DHR_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op01_elr_op19_result_memo_validation_closure_intake.bodyfree.v1"
)

P7_R54_AHR_POST_ELR19_DHR_OP00_STEP_REF: Final = (
    "DHR-OP00_scope_no_touch_no_promotion_refreeze_after_ELR_OP19"
)
P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF: Final = (
    "DHR-OP01_ELR_OP19_result_memo_validation_closure_intake"
)
P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF: Final = (
    "DHR-OP02_ELR_OP18_downstream_manual_decision_hold_intake"
)
P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF: Final = (
    "DHR-OP03_ELR_OP17_DMD_compatible_receipt_candidate_extraction"
)
P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF: Final = (
    "DHR-OP04_actual_source_claim_separation_invalid_source_classification"
)
P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF: Final = (
    "DHR-OP05_bodyfree_leak_promotion_claim_DMD_compatibility_preflight_scan"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF: Final = (
    "DHR-OP06_handoff_or_retry_deterministic_branch_resolver"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF: Final = (
    "DHR-OP07_manual_decision_materialization"
)
P7_R54_AHR_POST_ELR19_DHR_OP08_STEP_REF: Final = (
    "DHR-OP08_DMD_handoff_plan_candidate_materialization_without_execution"
)
P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF: Final = (
    "DHR-OP09_bodyfree_result_memo_target_tests_regression_closure"
)
P7_R54_AHR_POST_ELR19_DHR_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP00_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP08_STEP_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF,
)
P7_R54_AHR_POST_ELR19_DHR_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:1]
)
P7_R54_AHR_POST_ELR19_DHR_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[1:]
)
P7_R54_AHR_POST_ELR19_DHR_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:2]
)
P7_R54_AHR_POST_ELR19_DHR_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[2:]
)

P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_CLOSED_BODYFREE_REF: Final = (
    "DHR_ELR_OP19_INTAKE_CLOSED_BODYFREE"
)
P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_WAITING_FOR_MANUAL_HOLD_REF: Final = (
    "DHR_ELR_OP19_INTAKE_WAITING_FOR_MANUAL_HOLD"
)
P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_ELR_OP19_INTAKE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF: Final = (
    "DHR_ELR_OP19_INTAKE_MISSING_OR_INVALID"
)
P7_R54_AHR_POST_ELR19_DHR_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_CLOSED_BODYFREE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_WAITING_FOR_MANUAL_HOLD_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF,
)
P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_CLOSED_BODYFREE_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_CLOSED_BODYFREE_REF
)
P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_WAITING_FOR_MANUAL_HOLD_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_WAITING_FOR_MANUAL_HOLD_REF
)
P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_REPAIR_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF
)
P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_MISSING_OR_INVALID_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF
)

P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP19_CLOSURE_REF: Final = (
    "wait_for_elr_op19_closure"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF: Final = (
    "repair_post_elr19_result_memo_boundary"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP19_RESULT_MEMO_BOUNDARY_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF
)

P7_R54_AHR_POST_ELR19_DHR_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-ELR19 Downstream Manual Decision Handoff-or-Retry"
)
P7_R54_AHR_POST_ELR19_DHR_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "P8 question design",
    "P8 question implementation",
    "R52 actual execution",
    "P5 finalization",
    "P6 start",
    "P7 complete",
    "release decision",
)
P7_R54_AHR_POST_ELR19_DHR_CURRENT_HOLD_AFTER_ELR_OP19_REF: Final = (
    "downstream_non_promotion_manual_decision_required"
)
P7_R54_AHR_POST_ELR19_DHR_DEFAULT_NEXT_REQUIRED_STEP_REF: Final = (
    "decide_downstream_manual_handoff_or_retry_without_auto_promotion"
)
P7_R54_AHR_POST_ELR19_DHR_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(282).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(94).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(13).zip",
    "rn_zip_ref": "Cocolon(267).zip",
    "backend_zip_ref": "mashos-api(180).zip",
}
P7_R54_AHR_POST_ELR19_DHR_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostELR19_DownstreamManualDecision_HandoffOrRetry_PreDesignMemo_20260704.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostELR19_DownstreamManualDecision_HandoffOrRetry_DetailedDesign_ImplementationOrder_20260704.md",
    "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP19_Result_20260704.md",
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703.py",
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703.py",
)
P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "elr_op19_result_memo_bodyfree_closed_is_not_actual_review_execution",
    "elr_op19_result_memo_bodyfree_closed_is_not_downstream_manual_decision_completed",
    "elr_op18_downstream_manual_hold_is_not_dmd_execution",
    "elr_op17_dmd_compatible_receipt_candidate_is_not_actual_source_claim_confirmation",
    "helper_green_is_not_actual_human_review_complete",
    "target_green_is_not_actual_human_review_complete",
    "result_memo_green_is_not_actual_human_review_complete",
    "dmd_compatible_shape_is_not_downstream_handoff_permission",
    "p8_question_need_observation_is_not_p8_question_design",
    "release_decision_is_not_allowed_here",
)
P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_local_human_review_execution",
    "actual_operation_receipt_from_real_operation",
    "actual_sanitized_review_result_rows_from_real_operation",
    "actual_rating_rows_from_real_operation",
    "actual_question_need_observation_rows_from_real_operation",
    "actual_disposal_purge_execution",
    "dmd_execution",
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
P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "ELR-OP19 closure != actual review complete",
    "ELR-OP18 manual hold != downstream execution complete",
    "ELR-OP17 DMD-compatible receipt candidate != actual source confirmed",
    "helper green != actual human review complete",
    "DMD handoff decision must remain manual",
    "DMD direct execution is not performed in DHR",
    "R52 actual execution is not started in DHR",
    "P8 question observation != P8 start",
    "P7 target green != P7 complete",
    "P7 complete != release allowed",
)

P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "api_route_changed",
    "api_response_key_changed",
    "db_changed",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_changed",
    "runtime_generation_changed",
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
    "actual_review_execution_claimed_by_dhr_op01",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
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
P7_R54_AHR_POST_ELR19_DHR_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "input_body_included",
    "comment_text_body_included",
    "reviewer_note_body_included",
    "result_memo_body_included",
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
P7_R54_AHR_POST_ELR19_DHR_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_generation_changed",
    "p8_question_api_created",
    "p8_question_db_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "release_allowed",
)
P7_R54_AHR_POST_ELR19_DHR_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        *elr.P7_R54_AHR_POST_ALR12_ELR_FORBIDDEN_PAYLOAD_KEY_REFS,
        "raw_answer",
        "answer_text",
        "body_full_packet",
        "body_full_packet_body",
        "reviewer_note_body",
        "question_text",
        "draft_question_text",
        "absolute_path",
        "relative_path",
        "file_path",
        "local_path",
        "input_hash",
        "body_hash",
        "sha256",
        "terminal_output_body",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
    }
)
P7_R54_AHR_POST_ELR19_DHR_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "actual_local_human_review_complete",
    "actual_local_human_review_executed",
    "actual_local_human_review_executed_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_disposal_purge_executed_here",
    "helper_green_promoted_to_actual_review_complete",
    "target_green_promoted_to_actual_review_complete",
    "result_memo_green_promoted_to_actual_review_complete",
    "actual_review_execution_claimed_by_dhr_op01",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
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

P7_R54_AHR_POST_ELR19_DHR_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "current_hold_after_elr_op19_ref", "current_default_next_required_step_ref",
    "not_stage_refs", "not_stage_ref_count", "support_material_refs", "support_material_ref_count",
    "local_received_zip_refs", "local_received_zip_ref_count", "body_free", "dhr_op00_scope_confirmed",
    "dhr_op00_no_touch_boundary_confirmed", "dhr_op00_no_promotion_boundary_confirmed", "dhr_op00_does_not_intake_elr_op19_result_memo",
    "dhr_op00_does_not_intake_elr_op18_or_op17", "dhr_op00_does_not_generate_body_full_packet", "dhr_op00_does_not_run_actual_local_human_review",
    "dhr_op00_does_not_create_receipts_rows_or_disposal", "dhr_op00_does_not_execute_dmd_or_r52",
    "dhr_op00_does_not_start_p5_p6_p8_p7_or_release", "dhr_op00_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_elr19_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_ELR19_DHR_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed", "op00_no_touch_boundary_confirmed",
    "op00_no_promotion_boundary_confirmed", "op00_contract_valid", "dhr_op01_status_ref", "elr_op19_intake_status_ref",
    "dhr_op01_allowed_status_refs", "dhr_op01_allowed_status_ref_count",
    "dhr_op01_ready", "elr_op19_closed_bodyfree", "elr_op19_missing_or_invalid", "dhr_op01_reason_refs", "dhr_op01_reason_ref_count", "dhr_op01_blocker_refs", "dhr_op01_blocker_ref_count",
    "elr_op19_result_memo_present", "elr_op19_contract_valid", "elr_op19_schema_version", "elr_op19_operation_step_ref",
    "elr_op19_material_ref", "elr_op19_next_required_step", "elr_op19_result_memo_validation_closure_status_ref",
    "elr_op19_result_memo_bodyfree_closed", "elr_op19_result_memo_validation_closure_ready", "elr_op19_waiting_for_manual_hold",
    "elr_op19_repair_required", "elr_op19_op18_downstream_manual_decision_hold_ready",
    "elr_op19_op18_downstream_manual_decision_required_without_auto_execution", "target_tests_summary_bodyfree",
    "target_tests_summary_status_ref", "target_tests_passed_count", "target_tests_failed_count", "target_tests_timed_out",
    "elr_op19_target_tests_passed_count", "elr_op19_target_tests_failed_count", "elr_op19_target_tests_timed_out",
    "selected_regression_summary_bodyfree", "selected_regression_summary_status_ref", "selected_regression_passed_count",
    "selected_regression_failed_count", "selected_regression_timed_out",
    "elr_op19_selected_regression_passed_count", "elr_op19_selected_regression_failed_count", "elr_op19_selected_regression_timed_out",
    "compileall_summary_bodyfree", "compileall_summary_status_ref",
    "compileall_passed", "compileall_failed", "compileall_timed_out",
    "elr_op19_compileall_passed", "elr_op19_compileall_failed", "elr_op19_compileall_timed_out",
    "elr_op19_forbidden_payload_key_paths", "elr_op19_forbidden_payload_key_path_refs",
    "elr_op19_forbidden_payload_key_path_count", "elr_op19_body_like_value_path_refs", "elr_op19_body_like_value_path_count",
    "elr_op19_promotion_claim_refs", "elr_op19_promotion_claim_ref_count", "actual_review_execution_claimed_by_dhr_op01",
    "dhr_op01_ready_for_elr_op18_manual_hold_intake", "dhr_op01_waiting_for_elr_op19_closure", "dhr_op01_repair_required",
    "dhr_op01_does_not_intake_elr_op18_or_op17", "dhr_op01_does_not_resolve_final_branch", "dhr_op01_does_not_generate_body_full_packet",
    "dhr_op01_does_not_run_actual_local_human_review", "dhr_op01_does_not_create_receipts_rows_or_disposal",
    "dhr_op01_does_not_execute_dmd_or_r52", "dhr_op01_does_not_start_p5_p6_p8_p7_or_release",
    "dhr_op01_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_elr19_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(
        value,
        default=P7_R54_AHR_POST_ELR19_DHR_DEFAULT_REVIEW_SESSION_ID,
        max_length=220,
    )


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_ELR19_DHR_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_ELR19_DHR_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS}


def _required_fields_present(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {', '.join(missing[:8])}")


def _dedupe_clean_refs(values: Sequence[Any], *, max_length: int = 260) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        ref = _clean_ref(value, max_length=max_length)
        if ref and ref not in seen:
            seen.add(ref)
            out.append(ref)
    return out


def _scan_forbidden_payload_key_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_ELR19_DHR_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _ref_has_local_path_shape(text: str) -> bool:
    lowered = text.lower()
    if not text.strip():
        return False
    return (
        lowered.startswith("/mnt/")
        or lowered.startswith("/tmp/")
        or lowered.startswith("c:\\")
        or ":\\" in lowered
        or "file://" in lowered
    )


def _scan_body_like_value_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    suspect_key_tokens = (
        "raw_input", "comment_text", "question_text", "draft_question", "answer_text",
        "reviewer_note", "body_full_packet", "local_path", "file_path", "absolute_path",
        "hash", "terminal", "stdout", "stderr", "traceback",
    )
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            key_lower = key_text.lower()
            if isinstance(child, str):
                if any(token in key_lower for token in suspect_key_tokens) and child.strip():
                    paths.append(child_path)
                elif _ref_has_local_path_shape(child):
                    paths.append(child_path)
            elif (
                child is True
                and any(token in key_lower for token in suspect_key_tokens)
                and (key_lower.endswith("_included") or key_lower.endswith("_retained") or key_lower.endswith("_body"))
            ):
                paths.append(child_path)
            paths.extend(_scan_body_like_value_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_body_like_value_paths(child, path=f"{path}[{index}]"))
    return paths


def _promotion_claim_refs(material: Mapping[str, Any]) -> list[str]:
    return [
        field
        for field in P7_R54_AHR_POST_ELR19_DHR_PROMOTION_CLAIM_FIELD_REFS
        if material.get(field) is True
    ]


def _summary_bodyfree(op19: Mapping[str, Any], *, field: str, default_status_ref: str) -> dict[str, Any]:
    summary = op19.get(field)
    if not isinstance(summary, Mapping):
        return {
            "status_ref": default_status_ref,
            "passed_count": 0,
            "failed_count": 0,
            "timed_out": False,
            "body_free": True,
        }
    return {
        "status_ref": _clean_ref(summary.get("status_ref"), default=default_status_ref, max_length=220),
        "passed_count": max(0, int(summary.get("passed_count") or 0)) if not isinstance(summary.get("passed_count"), bool) else 0,
        "failed_count": max(0, int(summary.get("failed_count") or 0)) if not isinstance(summary.get("failed_count"), bool) else 0,
        "timed_out": bool(summary.get("timed_out") is True),
        "body_free": True,
    }


def _op19_contract_valid(op19: Mapping[str, Any] | None) -> bool:
    if not isinstance(op19, Mapping):
        return False
    try:
        return elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract(op19) is True
    except ValueError:
        return False


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_ELR19_DHR_PHASE or data.get("current_phase") != P7_R54_AHR_POST_ELR19_DHR_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_ELR19_DHR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_ELR19_DHR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim GitHub connection check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for field in P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS:
        if data.get(field) is not False:
            raise ValueError(f"{source} required false flag changed: {field}")
    if any(value is not False for value in (data.get("public_contract") or {}).values()):
        raise ValueError(f"{source} public contract mutated")
    if any(value is not False for value in (data.get("post_elr19_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract mutated")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free marker changed")
    if any(key in P7_R54_AHR_POST_ELR19_DHR_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains forbidden top-level payload key")


def build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build DHR-OP00 body-free scope / no-touch / no-promotion re-freeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_ELR19_DHR_SELECTED_STAGE_REF,
        "current_hold_after_elr_op19_ref": P7_R54_AHR_POST_ELR19_DHR_CURRENT_HOLD_AFTER_ELR_OP19_REF,
        "current_default_next_required_step_ref": P7_R54_AHR_POST_ELR19_DHR_DEFAULT_NEXT_REQUIRED_STEP_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_ELR19_DHR_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_ELR19_DHR_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "dhr_op00_scope_confirmed": True,
        "dhr_op00_no_touch_boundary_confirmed": True,
        "dhr_op00_no_promotion_boundary_confirmed": True,
        "dhr_op00_does_not_intake_elr_op19_result_memo": True,
        "dhr_op00_does_not_intake_elr_op18_or_op17": True,
        "dhr_op00_does_not_generate_body_full_packet": True,
        "dhr_op00_does_not_run_actual_local_human_review": True,
        "dhr_op00_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op00_does_not_execute_dmd_or_r52": True,
        "dhr_op00_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DHR-OP00 scope / no-touch / no-promotion re-freeze contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_ELR19_DHR_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostELR19-DHR-OP00",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_ELR19_DHR_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP00_STEP_REF,
        source="P7-R54-AHR-PostELR19-DHR-OP00",
    )
    for key in (
        "dhr_op00_scope_confirmed",
        "dhr_op00_no_touch_boundary_confirmed",
        "dhr_op00_no_promotion_boundary_confirmed",
        "dhr_op00_does_not_intake_elr_op19_result_memo",
        "dhr_op00_does_not_intake_elr_op18_or_op17",
        "dhr_op00_does_not_generate_body_full_packet",
        "dhr_op00_does_not_run_actual_local_human_review",
        "dhr_op00_does_not_create_receipts_rows_or_disposal",
        "dhr_op00_does_not_execute_dmd_or_r52",
        "dhr_op00_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op00_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP00 required true boundary changed: {key}")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("local_received_zip_refs", "local_received_zip_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if field == "local_received_zip_refs":
            expected_count = len(data.get(field) or {})
        else:
            expected_count = len(data.get(field) or [])
        if data.get(count_field) != expected_count:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP00 {count_field} changed")
    if data.get("selected_stage_ref") != P7_R54_AHR_POST_ELR19_DHR_SELECTED_STAGE_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 selected stage changed")
    if data.get("current_hold_after_elr_op19_ref") != P7_R54_AHR_POST_ELR19_DHR_CURRENT_HOLD_AFTER_ELR_OP19_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 current hold changed")
    if data.get("current_default_next_required_step_ref") != P7_R54_AHR_POST_ELR19_DHR_DEFAULT_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 current default next step changed")
    if tuple(data.get("not_stage_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_STAGE_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 not-stage refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP00 next step changed")
    return True


def _op01_status_reason_blocker_next(
    *, op19: Mapping[str, Any] | None, op19_contract_valid: bool, forbidden_paths: Sequence[str], body_like_paths: Sequence[str], promotion_claims: Sequence[str], op00_valid: bool
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    reasons: list[str] = []
    if not op00_valid:
        blockers.append("op00_contract_invalid")
    if not isinstance(op19, Mapping):
        blockers.append("elr_op19_result_memo_missing")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF,
            [],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF,
        )
    if not op19_contract_valid:
        blockers.append("elr_op19_result_memo_contract_invalid")
    if forbidden_paths:
        blockers.append("elr_op19_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("elr_op19_body_like_value_detected")
    if promotion_claims:
        blockers.append("elr_op19_promotion_claim_detected")
    op19_status_ref = _clean_ref(
        op19.get("result_memo_validation_closure_status_ref"),
        default="elr_op19_status_missing",
        max_length=240,
    )
    if blockers:
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF
            if (forbidden_paths or body_like_paths or promotion_claims)
            else P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF,
            ["dhr_op01_elr_op19_result_memo_validation_closure_cannot_be_handed_off_until_repaired"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF,
        )
    if op19_status_ref == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_CLOSED_BODYFREE_REF:
        reasons.append("dhr_op01_elr_op19_result_memo_validation_closure_closed_bodyfree_without_promotion")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_CLOSED_BODYFREE_REF,
            _dedupe_clean_refs(reasons),
            [],
            P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF,
        )
    if op19_status_ref == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_WAITING_FOR_MANUAL_HOLD_REF:
        reasons.append("dhr_op01_elr_op19_result_memo_validation_waits_for_manual_hold")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_WAITING_FOR_MANUAL_HOLD_REF,
            _dedupe_clean_refs(reasons),
            [],
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP19_CLOSURE_REF,
        )
    if op19_status_ref == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_REPAIR_REQUIRED_REF:
        blockers.append("elr_op19_result_memo_validation_closure_repair_required")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF,
            ["dhr_op01_elr_op19_result_memo_validation_closure_requires_repair"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF,
        )
    blockers.append("elr_op19_result_memo_validation_closure_status_unknown")
    return (
        P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF,
        [],
        _dedupe_clean_refs(blockers),
        P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF,
    )


def build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    elr_op19_result_memo_validation_closure: Mapping[str, Any] | None = None,
    op19_result_memo_validation_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP01 body-free ELR-OP19 result memo validation closure intake material."""

    op19 = elr_op19_result_memo_validation_closure if elr_op19_result_memo_validation_closure is not None else op19_result_memo_validation_closure
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op19.get("review_session_id") if isinstance(op19, Mapping) else None))
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19(
            review_session_id=session_id
        )
    try:
        op00_valid = assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(op00) is True
    except ValueError:
        op00_valid = False

    op19_map = op19 if isinstance(op19, Mapping) else {}
    op19_contract_valid = _op19_contract_valid(op19)
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(op19_map, path="elr_op19_result_memo_validation_closure"),
        max_length=280,
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(op19_map, path="elr_op19_result_memo_validation_closure"),
        max_length=280,
    )
    promotion_claims = _dedupe_clean_refs(
        [f"elr_op19_result_memo_validation_closure.{ref}" for ref in (_promotion_claim_refs(op19_map) if isinstance(op19_map, Mapping) else [])],
        max_length=280,
    )
    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        op19=op19,
        op19_contract_valid=op19_contract_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        op00_valid=op00_valid,
    )
    ready = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_CLOSED_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_WAITING_FOR_MANUAL_HOLD_REF
    repair = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF

    target_summary = _summary_bodyfree(op19_map, field="target_tests_summary_bodyfree", default_status_ref="target_tests_not_confirmed_by_dhr_op01")
    regression_summary = _summary_bodyfree(op19_map, field="selected_regression_summary_bodyfree", default_status_ref="selected_regression_not_confirmed_by_dhr_op01")
    compile_summary = _summary_bodyfree(op19_map, field="compileall_summary_bodyfree", default_status_ref="compileall_not_confirmed_by_dhr_op01")

    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="op00_next_required_step_missing", max_length=260),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("dhr_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("dhr_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("dhr_op00_no_promotion_boundary_confirmed") is True),
        "op00_contract_valid": op00_valid,
        "dhr_op01_status_ref": status_ref,
        "elr_op19_intake_status_ref": status_ref,
        "dhr_op01_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP01_ALLOWED_STATUS_REFS),
        "dhr_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP01_ALLOWED_STATUS_REFS),
        "dhr_op01_ready": ready,
        "dhr_op01_reason_refs": reasons,
        "dhr_op01_reason_ref_count": len(reasons),
        "dhr_op01_blocker_refs": blockers,
        "dhr_op01_blocker_ref_count": len(blockers),
        "elr_op19_result_memo_present": isinstance(op19, Mapping),
        "elr_op19_contract_valid": op19_contract_valid,
        "elr_op19_schema_version": _clean_ref(op19_map.get("schema_version"), default="elr_op19_schema_missing", max_length=260),
        "elr_op19_operation_step_ref": _clean_ref(op19_map.get("operation_step_ref"), default="elr_op19_operation_step_ref_missing", max_length=260),
        "elr_op19_material_ref": _clean_ref(op19_map.get("material_id"), default="elr_op19_material_missing", max_length=260),
        "elr_op19_next_required_step": _clean_ref(op19_map.get("next_required_step"), default="elr_op19_next_required_step_missing", max_length=260),
        "elr_op19_result_memo_validation_closure_status_ref": _clean_ref(op19_map.get("result_memo_validation_closure_status_ref"), default="elr_op19_status_missing", max_length=260),
        "elr_op19_result_memo_bodyfree_closed": bool(isinstance(op19, Mapping) and op19_map.get("result_memo_bodyfree_closed") is True),
        "elr_op19_closed_bodyfree": ready,
        "elr_op19_result_memo_validation_closure_ready": bool(isinstance(op19, Mapping) and op19_map.get("result_memo_validation_closure_ready") is True),
        "elr_op19_waiting_for_manual_hold": bool(isinstance(op19, Mapping) and op19_map.get("result_memo_validation_waiting_for_manual_hold") is True),
        "elr_op19_repair_required": bool(isinstance(op19, Mapping) and op19_map.get("result_memo_validation_repair_required") is True),
        "elr_op19_missing_or_invalid": status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF,
        "elr_op19_op18_downstream_manual_decision_hold_ready": bool(isinstance(op19, Mapping) and op19_map.get("op18_downstream_manual_decision_hold_ready") is True),
        "elr_op19_op18_downstream_manual_decision_required_without_auto_execution": bool(isinstance(op19, Mapping) and op19_map.get("op18_downstream_manual_decision_required_without_auto_execution") is True),
        "target_tests_summary_bodyfree": target_summary,
        "target_tests_summary_status_ref": target_summary["status_ref"],
        "target_tests_passed_count": target_summary["passed_count"],
        "target_tests_failed_count": target_summary["failed_count"],
        "target_tests_timed_out": target_summary["timed_out"],
        "elr_op19_target_tests_passed_count": target_summary["passed_count"],
        "elr_op19_target_tests_failed_count": target_summary["failed_count"],
        "elr_op19_target_tests_timed_out": target_summary["timed_out"],
        "selected_regression_summary_bodyfree": regression_summary,
        "selected_regression_summary_status_ref": regression_summary["status_ref"],
        "selected_regression_passed_count": regression_summary["passed_count"],
        "selected_regression_failed_count": regression_summary["failed_count"],
        "selected_regression_timed_out": regression_summary["timed_out"],
        "elr_op19_selected_regression_passed_count": regression_summary["passed_count"],
        "elr_op19_selected_regression_failed_count": regression_summary["failed_count"],
        "elr_op19_selected_regression_timed_out": regression_summary["timed_out"],
        "compileall_summary_bodyfree": compile_summary,
        "compileall_summary_status_ref": compile_summary["status_ref"],
        "compileall_passed": compile_summary["status_ref"] == "compileall_passed" and compile_summary["failed_count"] == 0 and compile_summary["timed_out"] is False,
        "compileall_failed": compile_summary["failed_count"] > 0,
        "compileall_timed_out": compile_summary["timed_out"],
        "elr_op19_compileall_passed": compile_summary["status_ref"] == "compileall_passed" and compile_summary["failed_count"] == 0 and compile_summary["timed_out"] is False,
        "elr_op19_compileall_failed": compile_summary["failed_count"] > 0,
        "elr_op19_compileall_timed_out": compile_summary["timed_out"],
        "elr_op19_forbidden_payload_key_paths": forbidden_paths,
        "elr_op19_forbidden_payload_key_path_refs": forbidden_paths,
        "elr_op19_forbidden_payload_key_path_count": len(forbidden_paths),
        "elr_op19_body_like_value_path_refs": body_like_paths,
        "elr_op19_body_like_value_path_count": len(body_like_paths),
        "elr_op19_promotion_claim_refs": promotion_claims,
        "elr_op19_promotion_claim_ref_count": len(promotion_claims),
        "actual_review_execution_claimed_by_dhr_op01": False,
        "dhr_op01_ready_for_elr_op18_manual_hold_intake": ready,
        "dhr_op01_waiting_for_elr_op19_closure": waiting,
        "dhr_op01_repair_required": status_ref in (
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF,
        ),
        "dhr_op01_does_not_intake_elr_op18_or_op17": True,
        "dhr_op01_does_not_resolve_final_branch": True,
        "dhr_op01_does_not_generate_body_full_packet": True,
        "dhr_op01_does_not_run_actual_local_human_review": True,
        "dhr_op01_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op01_does_not_execute_dmd_or_r52": True,
        "dhr_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DHR-OP01 body-free ELR-OP19 result memo validation closure intake contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_ELR19_DHR_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostELR19-DHR-OP01",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_ELR19_DHR_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF,
        source="P7-R54-AHR-PostELR19-DHR-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_ELR19_DHR_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 OP00 next step changed")
    if data.get("op00_contract_valid") is not True:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 OP00 contract must be valid")
    if data.get("elr_op19_intake_status_ref") != data.get("dhr_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 ELR-OP19 intake status alias changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "dhr_op01_does_not_intake_elr_op18_or_op17",
        "dhr_op01_does_not_resolve_final_branch",
        "dhr_op01_does_not_generate_body_full_packet",
        "dhr_op01_does_not_run_actual_local_human_review",
        "dhr_op01_does_not_create_receipts_rows_or_disposal",
        "dhr_op01_does_not_execute_dmd_or_r52",
        "dhr_op01_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op01_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP01 required true boundary changed: {key}")
    for key in (
        "actual_review_execution_claimed_by_dhr_op01",
        "dmd_execution_started_here",
        "dmd_auto_execution_allowed",
        "manual_decision_auto_executes_downstream",
        "r52_actual_execution_started_here",
        "r52_actual_execution_confirmed",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP01 downstream flag promoted: {key}")
    for field, count_field in (
        ("dhr_op01_allowed_status_refs", "dhr_op01_allowed_status_ref_count"),
        ("dhr_op01_reason_refs", "dhr_op01_reason_ref_count"),
        ("dhr_op01_blocker_refs", "dhr_op01_blocker_ref_count"),
        ("elr_op19_forbidden_payload_key_paths", "elr_op19_forbidden_payload_key_path_count"),
        ("elr_op19_forbidden_payload_key_path_refs", "elr_op19_forbidden_payload_key_path_count"),
        ("elr_op19_body_like_value_path_refs", "elr_op19_body_like_value_path_count"),
        ("elr_op19_promotion_claim_refs", "elr_op19_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP01 {count_field} changed")
    if tuple(data.get("dhr_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 allowed status refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 not-yet steps changed")

    for summary_field in (
        "target_tests_summary_bodyfree",
        "selected_regression_summary_bodyfree",
        "compileall_summary_bodyfree",
    ):
        summary = data.get(summary_field)
        if not isinstance(summary, Mapping) or summary.get("body_free") is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP01 invalid body-free summary: {summary_field}")

    status_ref = data.get("dhr_op01_status_ref")
    if status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_CLOSED_BODYFREE_REF:
        for key in (
            "dhr_op01_ready",
            "elr_op19_result_memo_present",
            "elr_op19_contract_valid",
            "elr_op19_result_memo_bodyfree_closed",
            "elr_op19_closed_bodyfree",
            "elr_op19_result_memo_validation_closure_ready",
            "dhr_op01_ready_for_elr_op18_manual_hold_intake",
            "elr_op19_op18_downstream_manual_decision_hold_ready",
            "elr_op19_op18_downstream_manual_decision_required_without_auto_execution",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP01 closed branch required true changed: {key}")
        if data.get("elr_op19_result_memo_validation_closure_status_ref") != elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_CLOSED_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 closed ELR-OP19 status changed")
        if data.get("elr_op19_forbidden_payload_key_paths") != [] or data.get("elr_op19_forbidden_payload_key_path_refs") != [] or data.get("elr_op19_body_like_value_path_refs") != [] or data.get("elr_op19_promotion_claim_refs") != [] or data.get("dhr_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 closed branch cannot carry leak/promotion/blocker refs")
        if data.get("dhr_op01_reason_refs") != ["dhr_op01_elr_op19_result_memo_validation_closure_closed_bodyfree_without_promotion"]:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 closed reason changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 closed next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_WAITING_FOR_MANUAL_HOLD_REF:
        if data.get("dhr_op01_ready") is not False or data.get("elr_op19_waiting_for_manual_hold") is not True or data.get("dhr_op01_waiting_for_elr_op19_closure") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 waiting branch flags changed")
        if data.get("elr_op19_contract_valid") is not True or data.get("elr_op19_result_memo_bodyfree_closed") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 waiting branch OP19 contract/bodyfree state changed")
        if data.get("dhr_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 waiting branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP19_CLOSURE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_REPAIR_REQUIRED_REF:
        if data.get("dhr_op01_ready") is not False or data.get("dhr_op01_repair_required") is not True or not data.get("dhr_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 repair branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP01_STATUS_MISSING_OR_INVALID_REF:
        if data.get("dhr_op01_ready") is not False or data.get("dhr_op01_repair_required") is not True or not data.get("dhr_op01_blocker_refs") or data.get("elr_op19_missing_or_invalid") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 missing/invalid branch must carry blockers")
        if data.get("elr_op19_contract_valid") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 missing/invalid branch cannot claim OP19 contract valid")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_POST_ELR19_RESULT_MEMO_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 missing/invalid next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP01 status ref is not allowed")
    return True


# Compatibility aliases with the full operation name used in the design title.
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19 = (
    build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract
)
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op01_elr_op19_result_memo_validation_closure_intake = (
    build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract
)

# Short canonical aliases used by the implementation-order design section.
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP02_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF
build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze = (
    build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19
)
assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract
)
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op00_scope_no_touch_no_promotion_refreeze = (
    build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op00_scope_no_touch_no_promotion_refreeze_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract
)


# ---------------------------------------------------------------------------
# DHR-OP02 / DHR-OP03: thin Post-ELR19 intake/extraction boundary.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_ELR19_DHR_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op02_elr_op18_downstream_manual_decision_hold_intake.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op03_elr_op17_dmd_compatible_receipt_candidate_extraction.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:3]
)
P7_R54_AHR_POST_ELR19_DHR_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[3:]
)
P7_R54_AHR_POST_ELR19_DHR_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:4]
)
P7_R54_AHR_POST_ELR19_DHR_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[4:]
)

P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_ACCEPTED_BODYFREE_REF: Final = (
    "DHR_ELR_OP18_MANUAL_HOLD_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_WAITING_FOR_HANDOFF_REF: Final = (
    "DHR_ELR_OP18_MANUAL_HOLD_WAITING_FOR_HANDOFF"
)
P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_ELR_OP18_MANUAL_HOLD_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF: Final = (
    "DHR_ELR_OP18_MANUAL_HOLD_MISSING_OR_INVALID"
)
P7_R54_AHR_POST_ELR19_DHR_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_WAITING_FOR_HANDOFF_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF,
)
P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_ACCEPTED_BODYFREE_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_ACCEPTED_BODYFREE_REF
P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_WAITING_FOR_HANDOFF_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_WAITING_FOR_HANDOFF_REF
P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_REPAIR_REQUIRED_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF
P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_MISSING_OR_INVALID_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF

P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF: Final = (
    "DHR_ELR_OP17_RECEIPT_CANDIDATE_SHAPE_VALID_BODYFREE"
)
P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF: Final = (
    "DHR_ELR_OP17_RECEIPT_CANDIDATE_WAITING_FOR_COMPLETE_EVIDENCE"
)
P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_ELR_OP17_RECEIPT_CANDIDATE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF: Final = (
    "DHR_ELR_OP17_RECEIPT_CANDIDATE_MISSING_OR_INVALID"
)
P7_R54_AHR_POST_ELR19_DHR_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF,
)
P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_SHAPE_VALID_BODYFREE_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF
P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_WAITING_FOR_COMPLETE_EVIDENCE_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF
P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_REPAIR_REQUIRED_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF
P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_MISSING_OR_INVALID_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF

P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_HANDOFF_CANDIDATE_REF: Final = (
    "wait_for_elr_handoff_candidate"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF: Final = (
    "repair_elr_op18_manual_hold"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP17_RECEIPT_CANDIDATE_REF: Final = (
    "wait_for_elr_op17_dmd_compatible_receipt_candidate"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP17_RECEIPT_CANDIDATE_REF: Final = (
    "repair_elr_op17_dmd_compatible_receipt_candidate"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP03_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP04_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF

P7_R54_AHR_POST_ELR19_DHR_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_next_required_step", "op01_elr_op19_intake_status_ref",
    "op01_ready_for_elr_op18_manual_hold_intake", "op01_contract_valid", "dhr_op02_status_ref",
    "elr_op18_manual_hold_intake_status_ref", "dhr_op02_allowed_status_refs", "dhr_op02_allowed_status_ref_count",
    "dhr_op02_ready", "dhr_op02_reason_refs", "dhr_op02_reason_ref_count", "dhr_op02_blocker_refs",
    "dhr_op02_blocker_ref_count", "elr_op18_manual_hold_present", "elr_op18_contract_valid",
    "elr_op18_schema_version", "elr_op18_operation_step_ref", "elr_op18_material_ref", "elr_op18_next_required_step",
    "elr_op18_downstream_manual_decision_hold_status_ref", "elr_op18_downstream_manual_decision_hold_ready",
    "elr_op18_downstream_manual_decision_hold_waiting_for_handoff", "elr_op18_downstream_manual_decision_hold_repair_required",
    "elr_op18_downstream_manual_decision_required", "elr_op18_downstream_manual_decision_required_without_auto_execution",
    "elr_op18_complete_candidate_held_without_downstream_execution", "elr_op18_manual_decision_auto_executes_downstream",
    "elr_op18_dmd_reexecution_started_here", "elr_op18_r52_actual_execution_started_here", "elr_op18_p8_start_allowed",
    "elr_op18_release_allowed", "elr_op18_forbidden_payload_key_path_refs", "elr_op18_forbidden_payload_key_path_count",
    "elr_op18_body_like_value_path_refs", "elr_op18_body_like_value_path_count", "elr_op18_promotion_claim_refs",
    "elr_op18_promotion_claim_ref_count", "actual_review_execution_claimed_by_dhr_op02",
    "dhr_op02_ready_for_elr_op17_receipt_candidate_extraction", "dhr_op02_waiting_for_elr_handoff_candidate",
    "dhr_op02_repair_required", "dhr_op02_does_not_confirm_actual_source_claim", "dhr_op02_does_not_intake_elr_op17",
    "dhr_op02_does_not_resolve_final_branch", "dhr_op02_does_not_generate_body_full_packet",
    "dhr_op02_does_not_run_actual_local_human_review", "dhr_op02_does_not_create_receipts_rows_or_disposal",
    "dhr_op02_does_not_execute_dmd_or_r52", "dhr_op02_does_not_start_p5_p6_p8_p7_or_release",
    "dhr_op02_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_elr19_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_ELR19_DHR_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_next_required_step", "op02_elr_op18_manual_hold_intake_status_ref",
    "op02_ready_for_elr_op17_receipt_candidate_extraction", "op02_contract_valid", "dhr_op03_status_ref",
    "elr_op17_receipt_candidate_extraction_status_ref", "dhr_op03_allowed_status_refs", "dhr_op03_allowed_status_ref_count",
    "dhr_op03_ready", "dhr_op03_reason_refs", "dhr_op03_reason_ref_count", "dhr_op03_blocker_refs",
    "dhr_op03_blocker_ref_count", "elr_op17_receipt_candidate_present", "elr_op17_contract_valid",
    "elr_op17_schema_version", "elr_op17_operation_step_ref", "elr_op17_material_ref", "elr_op17_next_required_step",
    "elr_op17_dmd_compatible_receipt_adapter_status_ref", "elr_op17_dmd_compatible_receipt_adapter_ready",
    "elr_op17_dmd_compatible_receipt_handoff_candidate_ready", "receipt_shape_valid", "receipt_schema_version",
    "receipt_schema_version_matches_dmd", "receipt_source_kind_ref", "receipt_source_kind_valid", "receipt_count_fields_are_24",
    "receipt_required_true_fields_passed", "receipt_body_free", "receipt_required_true_field_refs",
    "receipt_required_true_field_ref_count", "receipt_count_field_refs", "receipt_count_field_ref_count",
    "receipt_count_summary_bodyfree", "receipt_forbidden_payload_key_path_refs", "receipt_forbidden_payload_key_path_count",
    "receipt_body_like_value_path_refs", "receipt_body_like_value_path_count", "receipt_promotion_claim_refs",
    "receipt_promotion_claim_ref_count", "dmd_compatible_actual_operation_evidence_receipt_bodyfree",
    "dmd_compatible_actual_operation_evidence_receipt_bodyfree_key_refs",
    "dmd_compatible_actual_operation_evidence_receipt_bodyfree_key_ref_count", "receipt_claimed_as_actual_execution_by_dhr_op03",
    "actual_source_claim_confirmed_for_downstream_handoff", "dhr_op03_ready_for_actual_source_claim_separation",
    "dhr_op03_waiting_for_complete_evidence", "dhr_op03_repair_required", "dhr_op03_does_not_confirm_actual_source_claim",
    "dhr_op03_does_not_resolve_final_branch", "dhr_op03_does_not_generate_body_full_packet",
    "dhr_op03_does_not_run_actual_local_human_review", "dhr_op03_does_not_create_receipts_rows_or_disposal",
    "dhr_op03_does_not_execute_dmd_or_r52", "dhr_op03_does_not_start_p5_p6_p8_p7_or_release",
    "dhr_op03_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_elr19_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op18_contract_valid(op18: Mapping[str, Any] | None) -> bool:
    if not isinstance(op18, Mapping):
        return False
    try:
        return elr.assert_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold_contract(op18) is True
    except ValueError:
        return False


def _op17_contract_valid(op17: Mapping[str, Any] | None) -> bool:
    if not isinstance(op17, Mapping):
        return False
    try:
        return elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(op17) is True
    except ValueError:
        return False


def _receipt_count_summary(receipt: Mapping[str, Any]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS:
        value = receipt.get(field)
        summary[field] = int(value) if isinstance(value, int) and not isinstance(value, bool) else 0
    return summary


def _receipt_required_true_fields_passed(receipt: Mapping[str, Any]) -> bool:
    return all(receipt.get(field) is True for field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS)


def _receipt_count_fields_are_expected(receipt: Mapping[str, Any]) -> bool:
    return all(
        receipt.get(field) == dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT
        for field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS
    )


def _op02_status_reason_blocker_next(
    *,
    op01: Mapping[str, Any] | None,
    op01_valid: bool,
    op18: Mapping[str, Any] | None,
    op18_contract_valid: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    reasons: list[str] = []
    op01_ready = bool(op01_valid and isinstance(op01, Mapping) and op01.get("dhr_op01_ready_for_elr_op18_manual_hold_intake") is True)
    if not op01_ready:
        blockers.append("dhr_op02_op01_elr_op19_closure_intake_not_ready")
    if not isinstance(op18, Mapping):
        blockers.append("elr_op18_downstream_manual_decision_hold_missing")
        return (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF, [], _dedupe_clean_refs(blockers), P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF)
    if not op18_contract_valid:
        blockers.append("elr_op18_downstream_manual_decision_hold_contract_invalid")
    if forbidden_paths:
        blockers.append("elr_op18_manual_hold_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("elr_op18_manual_hold_body_like_value_detected")
    if promotion_claims:
        blockers.append("elr_op18_manual_hold_promotion_claim_detected")
    status = _clean_ref(op18.get("downstream_manual_decision_hold_status_ref"), default="elr_op18_status_missing", max_length=260)
    if blockers:
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF if (op18_contract_valid or forbidden_paths or body_like_paths or promotion_claims) else P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF,
            ["dhr_op02_elr_op18_manual_hold_cannot_continue_until_repaired"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF,
        )
    if status == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_HELD_BODYFREE_REF:
        reasons.append("dhr_op02_elr_op18_downstream_manual_decision_hold_accepted_bodyfree_without_execution")
        return (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_ACCEPTED_BODYFREE_REF, _dedupe_clean_refs(reasons), [], P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF)
    if status == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_WAITING_FOR_HANDOFF_REF:
        reasons.append("dhr_op02_elr_op18_manual_hold_waits_for_dmd_compatible_handoff_candidate")
        return (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_WAITING_FOR_HANDOFF_REF, _dedupe_clean_refs(reasons), [], P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_HANDOFF_CANDIDATE_REF)
    if status == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_REPAIR_REQUIRED_REF:
        blockers.append("elr_op18_downstream_manual_decision_hold_repair_required")
        return (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF, ["dhr_op02_elr_op18_manual_hold_requires_repair"], _dedupe_clean_refs(blockers), P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF)
    blockers.append("elr_op18_downstream_manual_decision_hold_status_unknown")
    return (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF, [], _dedupe_clean_refs(blockers), P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF)


def build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
    *,
    elr_op19_result_memo_validation_closure_intake: Mapping[str, Any] | None = None,
    op01_elr_op19_result_memo_validation_closure_intake: Mapping[str, Any] | None = None,
    elr_op18_downstream_manual_decision_hold: Mapping[str, Any] | None = None,
    op18_downstream_manual_decision_hold: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP02 body-free ELR-OP18 downstream manual-decision hold intake."""
    op01 = elr_op19_result_memo_validation_closure_intake if elr_op19_result_memo_validation_closure_intake is not None else op01_elr_op19_result_memo_validation_closure_intake
    op18 = elr_op18_downstream_manual_decision_hold if elr_op18_downstream_manual_decision_hold is not None else op18_downstream_manual_decision_hold
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op18.get("review_session_id") if isinstance(op18, Mapping) else (op01.get("review_session_id") if isinstance(op01, Mapping) else None)))
    if op01 is None:
        op01 = build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(review_session_id=session_id)
    try:
        op01_valid = assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(op01) is True
    except ValueError:
        op01_valid = False
    op18_map = op18 if isinstance(op18, Mapping) else {}
    op18_contract_valid = _op18_contract_valid(op18)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op18_map, path="elr_op18_downstream_manual_decision_hold"), max_length=280)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op18_map, path="elr_op18_downstream_manual_decision_hold"), max_length=280)
    promotion_claims = _dedupe_clean_refs([f"elr_op18_downstream_manual_decision_hold.{ref}" for ref in (_promotion_claim_refs(op18_map) if isinstance(op18_map, Mapping) else [])], max_length=280)
    status_ref, reasons, blockers, next_required_step = _op02_status_reason_blocker_next(
        op01=op01,
        op01_valid=op01_valid,
        op18=op18,
        op18_contract_valid=op18_contract_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_ACCEPTED_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_WAITING_FOR_HANDOFF_REF
    repair = status_ref in (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF)
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else "", default="op01_schema_missing", max_length=260),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else "", default="op01_material_missing", max_length=260),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else "", default="op01_next_required_step_missing", max_length=260),
        "op01_elr_op19_intake_status_ref": _clean_ref(op01.get("elr_op19_intake_status_ref") if isinstance(op01, Mapping) else "", default="op01_intake_status_missing", max_length=260),
        "op01_ready_for_elr_op18_manual_hold_intake": bool(isinstance(op01, Mapping) and op01.get("dhr_op01_ready_for_elr_op18_manual_hold_intake") is True),
        "op01_contract_valid": op01_valid,
        "dhr_op02_status_ref": status_ref,
        "elr_op18_manual_hold_intake_status_ref": status_ref,
        "dhr_op02_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP02_ALLOWED_STATUS_REFS),
        "dhr_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP02_ALLOWED_STATUS_REFS),
        "dhr_op02_ready": ready,
        "dhr_op02_reason_refs": reasons,
        "dhr_op02_reason_ref_count": len(reasons),
        "dhr_op02_blocker_refs": blockers,
        "dhr_op02_blocker_ref_count": len(blockers),
        "elr_op18_manual_hold_present": isinstance(op18, Mapping),
        "elr_op18_contract_valid": op18_contract_valid,
        "elr_op18_schema_version": _clean_ref(op18_map.get("schema_version"), default="elr_op18_schema_missing", max_length=260),
        "elr_op18_operation_step_ref": _clean_ref(op18_map.get("operation_step_ref"), default="elr_op18_operation_step_ref_missing", max_length=260),
        "elr_op18_material_ref": _clean_ref(op18_map.get("material_id"), default="elr_op18_material_missing", max_length=260),
        "elr_op18_next_required_step": _clean_ref(op18_map.get("next_required_step"), default="elr_op18_next_required_step_missing", max_length=260),
        "elr_op18_downstream_manual_decision_hold_status_ref": _clean_ref(op18_map.get("downstream_manual_decision_hold_status_ref"), default="elr_op18_status_missing", max_length=260),
        "elr_op18_downstream_manual_decision_hold_ready": bool(isinstance(op18, Mapping) and op18_map.get("downstream_manual_decision_hold_ready") is True),
        "elr_op18_downstream_manual_decision_hold_waiting_for_handoff": bool(isinstance(op18, Mapping) and op18_map.get("downstream_manual_decision_hold_waiting_for_handoff") is True),
        "elr_op18_downstream_manual_decision_hold_repair_required": bool(isinstance(op18, Mapping) and op18_map.get("downstream_manual_decision_hold_repair_required") is True),
        "elr_op18_downstream_manual_decision_required": bool(isinstance(op18, Mapping) and op18_map.get("downstream_manual_decision_required") is True),
        "elr_op18_downstream_manual_decision_required_without_auto_execution": bool(isinstance(op18, Mapping) and op18_map.get("downstream_manual_decision_required_without_auto_execution") is True),
        "elr_op18_complete_candidate_held_without_downstream_execution": bool(isinstance(op18, Mapping) and op18_map.get("complete_candidate_held_without_downstream_execution") is True),
        "elr_op18_manual_decision_auto_executes_downstream": False,
        "elr_op18_dmd_reexecution_started_here": False,
        "elr_op18_r52_actual_execution_started_here": False,
        "elr_op18_p8_start_allowed": False,
        "elr_op18_release_allowed": False,
        "elr_op18_forbidden_payload_key_path_refs": forbidden_paths,
        "elr_op18_forbidden_payload_key_path_count": len(forbidden_paths),
        "elr_op18_body_like_value_path_refs": body_like_paths,
        "elr_op18_body_like_value_path_count": len(body_like_paths),
        "elr_op18_promotion_claim_refs": promotion_claims,
        "elr_op18_promotion_claim_ref_count": len(promotion_claims),
        "actual_review_execution_claimed_by_dhr_op02": False,
        "dhr_op02_ready_for_elr_op17_receipt_candidate_extraction": ready,
        "dhr_op02_waiting_for_elr_handoff_candidate": waiting,
        "dhr_op02_repair_required": repair,
        "dhr_op02_does_not_confirm_actual_source_claim": True,
        "dhr_op02_does_not_intake_elr_op17": True,
        "dhr_op02_does_not_resolve_final_branch": True,
        "dhr_op02_does_not_generate_body_full_packet": True,
        "dhr_op02_does_not_run_actual_local_human_review": True,
        "dhr_op02_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op02_does_not_execute_dmd_or_r52": True,
        "dhr_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP02")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP02_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP02")
    if data.get("op01_schema_version") != P7_R54_AHR_POST_ELR19_DHR_OP01_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 OP01 schema version changed")
    if data.get("op01_next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 OP01 next step changed")
    if data.get("elr_op18_manual_hold_intake_status_ref") != data.get("dhr_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 status alias changed")
    for key in ("dhr_op02_does_not_confirm_actual_source_claim", "dhr_op02_does_not_intake_elr_op17", "dhr_op02_does_not_resolve_final_branch", "dhr_op02_does_not_generate_body_full_packet", "dhr_op02_does_not_run_actual_local_human_review", "dhr_op02_does_not_create_receipts_rows_or_disposal", "dhr_op02_does_not_execute_dmd_or_r52", "dhr_op02_does_not_start_p5_p6_p8_p7_or_release", "dhr_op02_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP02 required true boundary changed: {key}")
    for key in ("actual_review_execution_claimed_by_dhr_op02", "elr_op18_manual_decision_auto_executes_downstream", "elr_op18_dmd_reexecution_started_here", "elr_op18_r52_actual_execution_started_here", "elr_op18_p8_start_allowed", "elr_op18_release_allowed", "dmd_execution_started_here", "dmd_auto_execution_allowed", "manual_decision_auto_executes_downstream", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP02 downstream flag promoted: {key}")
    for field, count_field in (("dhr_op02_allowed_status_refs", "dhr_op02_allowed_status_ref_count"), ("dhr_op02_reason_refs", "dhr_op02_reason_ref_count"), ("dhr_op02_blocker_refs", "dhr_op02_blocker_ref_count"), ("elr_op18_forbidden_payload_key_path_refs", "elr_op18_forbidden_payload_key_path_count"), ("elr_op18_body_like_value_path_refs", "elr_op18_body_like_value_path_count"), ("elr_op18_promotion_claim_refs", "elr_op18_promotion_claim_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP02 {count_field} changed")
    if tuple(data.get("dhr_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 allowed status refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 not-yet steps changed")
    status_ref = data.get("dhr_op02_status_ref")
    if status_ref == P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_ACCEPTED_BODYFREE_REF:
        for key in ("op01_ready_for_elr_op18_manual_hold_intake", "op01_contract_valid", "dhr_op02_ready", "elr_op18_manual_hold_present", "elr_op18_contract_valid", "elr_op18_downstream_manual_decision_hold_ready", "elr_op18_downstream_manual_decision_required", "elr_op18_downstream_manual_decision_required_without_auto_execution", "elr_op18_complete_candidate_held_without_downstream_execution", "dhr_op02_ready_for_elr_op17_receipt_candidate_extraction"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP02 accepted branch required true changed: {key}")
        if data.get("elr_op18_downstream_manual_decision_hold_status_ref") != elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_HELD_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 accepted ELR-OP18 status changed")
        if data.get("dhr_op02_blocker_refs") != [] or data.get("elr_op18_forbidden_payload_key_path_refs") != [] or data.get("elr_op18_body_like_value_path_refs") != [] or data.get("elr_op18_promotion_claim_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 accepted branch cannot carry leak/promotion/blocker refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 accepted next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_WAITING_FOR_HANDOFF_REF:
        if data.get("dhr_op02_ready") is not False or data.get("dhr_op02_waiting_for_elr_handoff_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 waiting branch flags changed")
        if data.get("elr_op18_contract_valid") is not True or data.get("elr_op18_downstream_manual_decision_hold_waiting_for_handoff") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 waiting ELR-OP18 state changed")
        if data.get("dhr_op02_blocker_refs") != [] or data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_HANDOFF_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 waiting branch changed")
    elif status_ref in (P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_ELR19_DHR_OP02_STATUS_MISSING_OR_INVALID_REF):
        if data.get("dhr_op02_ready") is not False or data.get("dhr_op02_repair_required") is not True or not data.get("dhr_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 repair/missing branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 repair/missing next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP02 status ref is not allowed")
    return True


def _op03_status_reason_blocker_next(
    *,
    op02: Mapping[str, Any] | None,
    op02_valid: bool,
    op17: Mapping[str, Any] | None,
    op17_contract_valid: bool,
    receipt: Mapping[str, Any],
    schema_ok: bool,
    source_ok: bool,
    counts_ok: bool,
    true_ok: bool,
    body_free_ok: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    reasons: list[str] = []
    op02_ready = bool(op02_valid and isinstance(op02, Mapping) and op02.get("dhr_op02_ready_for_elr_op17_receipt_candidate_extraction") is True)
    if not op02_ready:
        blockers.append("dhr_op03_op02_elr_op18_manual_hold_intake_not_ready")
    if not isinstance(op17, Mapping):
        blockers.append("elr_op17_dmd_compatible_receipt_candidate_missing")
        return (P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF, [], _dedupe_clean_refs(blockers), P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP17_RECEIPT_CANDIDATE_REF)
    status = _clean_ref(op17.get("dmd_compatible_receipt_adapter_status_ref"), default="elr_op17_status_missing", max_length=260)
    if forbidden_paths:
        blockers.append("elr_op17_receipt_candidate_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("elr_op17_receipt_candidate_body_like_value_detected")
    if promotion_claims:
        blockers.append("elr_op17_receipt_candidate_promotion_claim_detected")
    if not op17_contract_valid:
        blockers.append("elr_op17_dmd_compatible_receipt_candidate_contract_invalid")
    if status == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF and not blockers:
        reasons.append("dhr_op03_elr_op17_receipt_candidate_waits_for_complete_evidence")
        return (P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF, _dedupe_clean_refs(reasons), [], P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP17_RECEIPT_CANDIDATE_REF)
    if status == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_REPAIR_REQUIRED_REF:
        blockers.append("elr_op17_dmd_compatible_receipt_candidate_repair_required")
    if not receipt and status != elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF:
        blockers.append("elr_op17_dmd_compatible_receipt_candidate_bodyfree_receipt_empty")
    if receipt:
        if not schema_ok:
            blockers.append("elr_op17_receipt_schema_version_mismatch")
        if not source_ok:
            blockers.append("elr_op17_receipt_source_kind_invalid")
        if not counts_ok:
            blockers.append("elr_op17_receipt_count_fields_not_24")
        if not true_ok:
            blockers.append("elr_op17_receipt_required_true_fields_incomplete")
        if not body_free_ok:
            blockers.append("elr_op17_receipt_body_free_flag_missing_or_false")
    if blockers:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF if "elr_op17_dmd_compatible_receipt_candidate_missing" in blockers else P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF
        return (status_ref, ["dhr_op03_elr_op17_receipt_candidate_cannot_continue_until_repaired"], _dedupe_clean_refs(blockers), P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP17_RECEIPT_CANDIDATE_REF)
    if status == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_READY_BODYFREE_REF and receipt and schema_ok and source_ok and counts_ok and true_ok and body_free_ok:
        reasons.append("dhr_op03_elr_op17_dmd_compatible_receipt_candidate_shape_valid_bodyfree_without_actual_source_confirmation")
        return (P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF, _dedupe_clean_refs(reasons), [], P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF)
    return (P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF, ["dhr_op03_elr_op17_receipt_candidate_waits_for_complete_evidence"], [], P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP17_RECEIPT_CANDIDATE_REF)


def build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
    *,
    elr_op18_downstream_manual_decision_hold_intake: Mapping[str, Any] | None = None,
    op02_elr_op18_downstream_manual_decision_hold_intake: Mapping[str, Any] | None = None,
    elr_op17_dmd_compatible_receipt_candidate: Mapping[str, Any] | None = None,
    op17_dmd_compatible_receipt_candidate: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP03 body-free ELR-OP17 DMD-compatible receipt candidate extraction material."""
    op02 = elr_op18_downstream_manual_decision_hold_intake if elr_op18_downstream_manual_decision_hold_intake is not None else op02_elr_op18_downstream_manual_decision_hold_intake
    op17 = elr_op17_dmd_compatible_receipt_candidate if elr_op17_dmd_compatible_receipt_candidate is not None else op17_dmd_compatible_receipt_candidate
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op17.get("review_session_id") if isinstance(op17, Mapping) else (op02.get("review_session_id") if isinstance(op02, Mapping) else None)))
    if op02 is None:
        op02 = build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(review_session_id=session_id)
    try:
        op02_valid = assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(op02) is True
    except ValueError:
        op02_valid = False
    op17_map = op17 if isinstance(op17, Mapping) else {}
    op17_contract_valid = _op17_contract_valid(op17)
    receipt_value = op17_map.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree")
    receipt = receipt_value if isinstance(receipt_value, Mapping) else {}
    schema_ok = bool(receipt and receipt.get("schema_version") == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION)
    source_kind_ref = _clean_ref(receipt.get("source_kind_ref") if receipt else "", default="source_kind_missing", max_length=180)
    source_ok = source_kind_ref == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
    counts_ok = bool(receipt and _receipt_count_fields_are_expected(receipt))
    true_ok = bool(receipt and _receipt_required_true_fields_passed(receipt))
    body_free_ok = bool(receipt and receipt.get("body_free") is True)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(receipt, path="dmd_compatible_actual_operation_evidence_receipt"), max_length=280)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(receipt, path="dmd_compatible_actual_operation_evidence_receipt"), max_length=280)
    promotion_claims = _dedupe_clean_refs([f"dmd_compatible_actual_operation_evidence_receipt.{ref}" for ref in (_promotion_claim_refs(receipt) if isinstance(receipt, Mapping) else [])], max_length=280)
    status_ref, reasons, blockers, next_required_step = _op03_status_reason_blocker_next(
        op02=op02,
        op02_valid=op02_valid,
        op17=op17,
        op17_contract_valid=op17_contract_valid,
        receipt=receipt,
        schema_ok=schema_ok,
        source_ok=source_ok,
        counts_ok=counts_ok,
        true_ok=true_ok,
        body_free_ok=body_free_ok,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF
    repair = status_ref in (P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF)
    safe_receipt = {str(key): value for key, value in receipt.items()} if ready else {}
    receipt_keys = list(safe_receipt.keys())
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else "", default="op02_schema_missing", max_length=260),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else "", default="op02_material_missing", max_length=260),
        "op02_next_required_step": _clean_ref(op02.get("next_required_step") if isinstance(op02, Mapping) else "", default="op02_next_required_step_missing", max_length=260),
        "op02_elr_op18_manual_hold_intake_status_ref": _clean_ref(op02.get("elr_op18_manual_hold_intake_status_ref") if isinstance(op02, Mapping) else "", default="op02_status_missing", max_length=260),
        "op02_ready_for_elr_op17_receipt_candidate_extraction": bool(isinstance(op02, Mapping) and op02.get("dhr_op02_ready_for_elr_op17_receipt_candidate_extraction") is True),
        "op02_contract_valid": op02_valid,
        "dhr_op03_status_ref": status_ref,
        "elr_op17_receipt_candidate_extraction_status_ref": status_ref,
        "dhr_op03_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP03_ALLOWED_STATUS_REFS),
        "dhr_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP03_ALLOWED_STATUS_REFS),
        "dhr_op03_ready": ready,
        "dhr_op03_reason_refs": reasons,
        "dhr_op03_reason_ref_count": len(reasons),
        "dhr_op03_blocker_refs": blockers,
        "dhr_op03_blocker_ref_count": len(blockers),
        "elr_op17_receipt_candidate_present": isinstance(op17, Mapping),
        "elr_op17_contract_valid": op17_contract_valid,
        "elr_op17_schema_version": _clean_ref(op17_map.get("schema_version"), default="elr_op17_schema_missing", max_length=260),
        "elr_op17_operation_step_ref": _clean_ref(op17_map.get("operation_step_ref"), default="elr_op17_operation_step_ref_missing", max_length=260),
        "elr_op17_material_ref": _clean_ref(op17_map.get("material_id"), default="elr_op17_material_missing", max_length=260),
        "elr_op17_next_required_step": _clean_ref(op17_map.get("next_required_step"), default="elr_op17_next_required_step_missing", max_length=260),
        "elr_op17_dmd_compatible_receipt_adapter_status_ref": _clean_ref(op17_map.get("dmd_compatible_receipt_adapter_status_ref"), default="elr_op17_status_missing", max_length=260),
        "elr_op17_dmd_compatible_receipt_adapter_ready": bool(isinstance(op17, Mapping) and op17_map.get("dmd_compatible_receipt_adapter_ready") is True),
        "elr_op17_dmd_compatible_receipt_handoff_candidate_ready": bool(isinstance(op17, Mapping) and op17_map.get("dmd_compatible_receipt_handoff_candidate_ready") is True),
        "receipt_shape_valid": ready,
        "receipt_schema_version": _clean_ref(receipt.get("schema_version") if receipt else "", default="receipt_schema_missing", max_length=260),
        "receipt_schema_version_matches_dmd": schema_ok,
        "receipt_source_kind_ref": source_kind_ref,
        "receipt_source_kind_valid": source_ok,
        "receipt_count_fields_are_24": counts_ok,
        "receipt_required_true_fields_passed": true_ok,
        "receipt_body_free": body_free_ok,
        "receipt_required_true_field_refs": list(dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS),
        "receipt_required_true_field_ref_count": len(dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS),
        "receipt_count_field_refs": list(dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS),
        "receipt_count_field_ref_count": len(dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS),
        "receipt_count_summary_bodyfree": _receipt_count_summary(receipt),
        "receipt_forbidden_payload_key_path_refs": forbidden_paths,
        "receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "receipt_body_like_value_path_refs": body_like_paths,
        "receipt_body_like_value_path_count": len(body_like_paths),
        "receipt_promotion_claim_refs": promotion_claims,
        "receipt_promotion_claim_ref_count": len(promotion_claims),
        "dmd_compatible_actual_operation_evidence_receipt_bodyfree": safe_receipt,
        "dmd_compatible_actual_operation_evidence_receipt_bodyfree_key_refs": receipt_keys,
        "dmd_compatible_actual_operation_evidence_receipt_bodyfree_key_ref_count": len(receipt_keys),
        "receipt_claimed_as_actual_execution_by_dhr_op03": False,
        "actual_source_claim_confirmed_for_downstream_handoff": False,
        "dhr_op03_ready_for_actual_source_claim_separation": ready,
        "dhr_op03_waiting_for_complete_evidence": waiting,
        "dhr_op03_repair_required": repair,
        "dhr_op03_does_not_confirm_actual_source_claim": True,
        "dhr_op03_does_not_resolve_final_branch": True,
        "dhr_op03_does_not_generate_body_full_packet": True,
        "dhr_op03_does_not_run_actual_local_human_review": True,
        "dhr_op03_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op03_does_not_execute_dmd_or_r52": True,
        "dhr_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP03")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP03_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP03")
    if data.get("op02_schema_version") != P7_R54_AHR_POST_ELR19_DHR_OP02_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 OP02 schema version changed")
    if data.get("op02_next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 OP02 next step changed")
    if data.get("elr_op17_receipt_candidate_extraction_status_ref") != data.get("dhr_op03_status_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 status alias changed")
    for key in ("dhr_op03_does_not_confirm_actual_source_claim", "dhr_op03_does_not_resolve_final_branch", "dhr_op03_does_not_generate_body_full_packet", "dhr_op03_does_not_run_actual_local_human_review", "dhr_op03_does_not_create_receipts_rows_or_disposal", "dhr_op03_does_not_execute_dmd_or_r52", "dhr_op03_does_not_start_p5_p6_p8_p7_or_release", "dhr_op03_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP03 required true boundary changed: {key}")
    for key in ("receipt_claimed_as_actual_execution_by_dhr_op03", "actual_source_claim_confirmed_for_downstream_handoff", "dmd_execution_started_here", "dmd_auto_execution_allowed", "manual_decision_auto_executes_downstream", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP03 downstream or actual-source flag promoted: {key}")
    for field, count_field in (("dhr_op03_allowed_status_refs", "dhr_op03_allowed_status_ref_count"), ("dhr_op03_reason_refs", "dhr_op03_reason_ref_count"), ("dhr_op03_blocker_refs", "dhr_op03_blocker_ref_count"), ("receipt_required_true_field_refs", "receipt_required_true_field_ref_count"), ("receipt_count_field_refs", "receipt_count_field_ref_count"), ("receipt_forbidden_payload_key_path_refs", "receipt_forbidden_payload_key_path_count"), ("receipt_body_like_value_path_refs", "receipt_body_like_value_path_count"), ("receipt_promotion_claim_refs", "receipt_promotion_claim_ref_count"), ("dmd_compatible_actual_operation_evidence_receipt_bodyfree_key_refs", "dmd_compatible_actual_operation_evidence_receipt_bodyfree_key_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP03 {count_field} changed")
    if tuple(data.get("dhr_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 allowed status refs changed")
    if tuple(data.get("receipt_required_true_field_refs") or ()) != dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 receipt true refs changed")
    if tuple(data.get("receipt_count_field_refs") or ()) != dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 receipt count refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 not-yet steps changed")
    status_ref = data.get("dhr_op03_status_ref")
    if status_ref == P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF:
        for key in ("op02_ready_for_elr_op17_receipt_candidate_extraction", "op02_contract_valid", "dhr_op03_ready", "elr_op17_receipt_candidate_present", "elr_op17_contract_valid", "elr_op17_dmd_compatible_receipt_adapter_ready", "elr_op17_dmd_compatible_receipt_handoff_candidate_ready", "receipt_shape_valid", "receipt_schema_version_matches_dmd", "receipt_source_kind_valid", "receipt_count_fields_are_24", "receipt_required_true_fields_passed", "receipt_body_free", "dhr_op03_ready_for_actual_source_claim_separation"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP03 shape-valid branch required true changed: {key}")
        if data.get("elr_op17_dmd_compatible_receipt_adapter_status_ref") != elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_READY_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 ready ELR-OP17 status changed")
        if data.get("receipt_schema_version") != dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 receipt schema changed")
        if data.get("receipt_source_kind_ref") != dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 receipt source kind changed")
        receipt = data.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree")
        if not isinstance(receipt, Mapping) or receipt == {}:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 shape-valid branch must carry safe receipt")
        for field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS:
            if receipt.get(field) != dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP03 receipt count changed: {field}")
        for field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS:
            if receipt.get(field) is not True:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP03 receipt true field changed: {field}")
        if data.get("receipt_forbidden_payload_key_path_refs") != [] or data.get("receipt_body_like_value_path_refs") != [] or data.get("receipt_promotion_claim_refs") != [] or data.get("dhr_op03_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 shape-valid branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 shape-valid next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF:
        if data.get("dhr_op03_ready") is not False or data.get("dhr_op03_waiting_for_complete_evidence") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 waiting branch flags changed")
        if data.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree") != {} or data.get("dhr_op03_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 waiting branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP17_RECEIPT_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 waiting next step changed")
    elif status_ref in (P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF):
        if data.get("dhr_op03_ready") is not False or data.get("dhr_op03_repair_required") is not True or not data.get("dhr_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 repair/missing branch must carry blockers")
        if data.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree") != {}:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 repair/missing branch must not carry receipt")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP17_RECEIPT_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 repair/missing next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP03 status ref is not allowed")
    return True


build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_elr_op18_downstream_manual_decision_hold_intake = (
    build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract
)
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction = (
    build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract
)



# ---------------------------------------------------------------------------
# DHR-OP04 / DHR-OP05: actual source separation and preflight scan.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op04_actual_source_claim_separation_invalid_source_classification.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:5]
)
P7_R54_AHR_POST_ELR19_DHR_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[5:]
)
P7_R54_AHR_POST_ELR19_DHR_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:6]
)
P7_R54_AHR_POST_ELR19_DHR_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[6:]
)

P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF: Final = (
    "DHR_ACTUAL_SOURCE_CLAIM_CONFIRMED_BODYFREE"
)
P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF: Final = (
    "DHR_ACTUAL_SOURCE_CLAIM_NOT_CONFIRMED_RETRY_OR_START_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = (
    "DHR_ACTUAL_SOURCE_INVALID_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF: Final = (
    "DHR_ACTUAL_SOURCE_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM"
)
P7_R54_AHR_POST_ELR19_DHR_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF,
)
P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_CLAIM_CONFIRMED_BODYFREE_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
)
P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_CLAIM_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
)
P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_INVALID_REPAIR_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF
)
P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
)

P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF: Final = (
    "DHR_PREFLIGHT_SCAN_CLEAR_BODYFREE"
)
P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF: Final = (
    "DHR_PREFLIGHT_SCAN_WAITING_OR_INCOMPLETE"
)
P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF,
)
P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_CLEAR_BODYFREE_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF
)
P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF
)
P7_R54_AHR_POST_ELR19_DHR_PREFLIGHT_SCAN_WAITING_OR_INCOMPLETE_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF
)

P7_R54_AHR_POST_ELR19_DHR_INVALID_SOURCE_KIND_REFS: Final[tuple[str, ...]] = (
    "unit_test_fixture",
    "helper_green",
    "target_green",
    "result_memo_green",
    "synthetic",
    "historical_reuse_only",
    "unknown",
    "candidate_shape_only",
)
P7_R54_AHR_POST_ELR19_DHR_EXTERNAL_ACTUAL_SOURCE_ORIGIN_REF: Final = (
    "external_local_only_human_review_receipt_or_manual_evidence_confirmation"
)
P7_R54_AHR_POST_ELR19_DHR_CANDIDATE_SHAPE_ONLY_EXCLUSION_REF: Final = "candidate_shape_only"
P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF: Final = (
    "existing_dmd_op01_requires_dmh_op18_finalizer_contract"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF: Final = (
    "retry_or_start_actual_local_only_human_review_operation_with_explicit_local_only_allow"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF: Final = (
    "stop_and_repair_post_elr19_bodyfree_evidence_boundary"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_EXTERNAL_BODYFREE_ACTUAL_SOURCE_CLAIM_REF: Final = (
    "wait_for_external_bodyfree_actual_source_claim"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP05_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP06_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF

P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_PROMOTION_FIELD_REFS: Final[tuple[str, ...]] = (
    "helper_green_promoted_to_actual_source",
    "target_green_promoted_to_actual_source",
    "result_memo_green_promoted_to_actual_source",
    "fixture_promoted_to_actual_source",
    "historical_reuse_promoted_to_actual_source",
    "candidate_shape_promoted_to_actual_source",
    "actual_operation_receipt_created_by_helper_here",
    "actual_rows_created_by_helper_here",
)

P7_R54_AHR_POST_ELR19_DHR_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_schema_version", "op03_material_ref", "op03_next_required_step", "op03_receipt_candidate_extraction_status_ref",
    "op03_ready_for_actual_source_claim_separation", "op03_contract_valid", "dhr_op04_status_ref",
    "actual_source_claim_separation_status_ref", "dhr_op04_allowed_status_refs", "dhr_op04_allowed_status_ref_count",
    "dhr_op04_ready", "dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan", "dhr_op04_reason_refs",
    "dhr_op04_reason_ref_count", "dhr_op04_blocker_refs", "dhr_op04_blocker_ref_count", "receipt_shape_valid",
    "receipt_source_kind_ref", "receipt_count_fields_are_24", "receipt_required_true_fields_passed", "receipt_body_free",
    "receipt_candidate_bodyfree_present", "receipt_candidate_source_kind_ref", "receipt_candidate_shape_carried_only",
    "candidate_shape_promoted_to_actual_source", "external_actual_operation_evidence_claim_optional_present",
    "external_actual_operation_evidence_claim_source_kind_ref", "external_actual_operation_evidence_claim_source_kind_valid",
    "external_actual_operation_evidence_claim_bodyfree", "external_actual_operation_evidence_claim_origin_ref",
    "external_actual_operation_evidence_claim_forbidden_payload_key_path_refs",
    "external_actual_operation_evidence_claim_forbidden_payload_key_path_count",
    "external_actual_operation_evidence_claim_body_like_value_path_refs",
    "external_actual_operation_evidence_claim_body_like_value_path_count",
    "external_actual_operation_evidence_claim_promotion_claim_refs",
    "external_actual_operation_evidence_claim_promotion_claim_ref_count",
    "actual_source_claim_status_ref", "actual_source_claim_confirmed_for_downstream_handoff",
    "actual_source_claim_bodyfree", "actual_source_claim_origin_ref", "actual_local_only_human_review_by_person_confirmed",
    "actual_source_claim_requires_external_bodyfree_evidence", "actual_source_claim_missing_or_not_confirmed",
    "actual_source_invalid_repair_required", "actual_source_waiting_for_external_bodyfree_claim", "actual_source_exclusion_refs",
    "actual_source_exclusion_ref_count", "invalid_source_kind_refs", "invalid_source_kind_ref_count",
    "helper_green_promoted_to_actual_source", "target_green_promoted_to_actual_source",
    "result_memo_green_promoted_to_actual_source", "fixture_promoted_to_actual_source",
    "historical_reuse_promoted_to_actual_source", "actual_operation_receipt_created_by_helper_here",
    "actual_rows_created_by_helper_here", "dhr_op04_does_not_resolve_final_branch",
    "dhr_op04_does_not_generate_body_full_packet", "dhr_op04_does_not_run_actual_local_human_review",
    "dhr_op04_does_not_create_receipts_rows_or_disposal", "dhr_op04_does_not_execute_dmd_or_r52",
    "dhr_op04_does_not_start_p5_p6_p8_p7_or_release", "dhr_op04_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_elr19_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_ELR19_DHR_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_schema_version", "op04_material_ref", "op04_next_required_step", "op04_actual_source_claim_status_ref",
    "op04_actual_source_claim_confirmed_for_downstream_handoff", "op04_invalid_source_kind_ref_count", "op04_ready_for_preflight_scan",
    "op04_contract_valid", "dhr_op05_status_ref", "preflight_scan_status_ref", "dhr_op05_allowed_status_refs",
    "dhr_op05_allowed_status_ref_count", "dhr_op05_ready", "dhr_op05_ready_for_branch_resolver", "dhr_op05_reason_refs",
    "dhr_op05_reason_ref_count", "dhr_op05_blocker_refs", "dhr_op05_blocker_ref_count", "scanned_material_ref_count",
    "forbidden_payload_key_path_refs", "forbidden_payload_key_path_count", "body_like_value_path_refs", "body_like_value_path_count",
    "promotion_claim_refs", "promotion_claim_ref_count", "invalid_source_kind_refs", "invalid_source_kind_ref_count",
    "bodyfree_leak_promotion_source_scan_passed", "preflight_scan_passed", "preflight_repair_required",
    "preflight_waiting_or_incomplete", "actual_source_claim_confirmed_for_downstream_handoff",
    "evidence_incomplete_or_source_not_confirmed", "dmd_direct_call_safe_without_adapter", "dmd_direct_call_blocker_refs",
    "dmd_direct_call_blocker_ref_count", "dmd_direct_call_reason_ref", "dmh_op18_finalizer_fake_generation_allowed",
    "dmd_handoff_plan_candidate_allowed", "dmd_handoff_plan_candidate_blocker_refs",
    "dmd_handoff_plan_candidate_blocker_ref_count", "dmd_alternate_post_elr19_intake_may_be_required",
    "dhr_op05_does_not_resolve_final_branch", "dhr_op05_does_not_generate_body_full_packet",
    "dhr_op05_does_not_run_actual_local_human_review", "dhr_op05_does_not_create_receipts_rows_or_disposal",
    "dhr_op05_does_not_execute_dmd_or_r52", "dhr_op05_does_not_start_p5_p6_p8_p7_or_release",
    "dhr_op05_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_elr19_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _external_claim_source_kind_ref(claim: Mapping[str, Any] | None) -> str:
    if not isinstance(claim, Mapping):
        return "external_actual_operation_evidence_claim_missing"
    for key in (
        "source_kind_ref",
        "actual_source_kind_ref",
        "actual_source_claim_source_kind_ref",
        "external_actual_operation_evidence_claim_source_kind_ref",
    ):
        value = claim.get(key)
        if value not in (None, ""):
            return _clean_ref(value, default="external_actual_operation_evidence_claim_source_kind_missing", max_length=180)
    return "external_actual_operation_evidence_claim_source_kind_missing"


def _external_claim_origin_ref(claim: Mapping[str, Any] | None) -> str:
    if not isinstance(claim, Mapping):
        return "actual_source_claim_origin_missing_or_not_confirmed"
    for key in (
        "actual_source_claim_origin_ref",
        "external_actual_operation_evidence_claim_origin_ref",
        "origin_ref",
    ):
        value = claim.get(key)
        if value not in (None, ""):
            return _clean_ref(value, default="actual_source_claim_origin_missing_or_not_confirmed", max_length=220)
    return "actual_source_claim_origin_missing_or_not_confirmed"


def _external_claim_bodyfree(claim: Mapping[str, Any] | None) -> bool:
    if not isinstance(claim, Mapping):
        return False
    return claim.get("actual_source_claim_bodyfree") is True or claim.get("body_free") is True


def _external_claim_human_confirmed(claim: Mapping[str, Any] | None) -> bool:
    if not isinstance(claim, Mapping):
        return False
    return (
        claim.get("actual_local_only_human_review_by_person_confirmed") is True
        or claim.get("actual_human_review_executed_by_person") is True
    )


def _external_claim_promotion_refs(claim: Mapping[str, Any] | None, *, path: str) -> list[str]:
    if not isinstance(claim, Mapping):
        return []
    refs = [f"{path}.{field}" for field in P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_PROMOTION_FIELD_REFS if claim.get(field) is True]
    refs.extend(f"{path}.{field}" for field in _promotion_claim_refs(claim))
    return _dedupe_clean_refs(refs, max_length=280)


def _scan_invalid_source_kind_ref_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if "source_kind" in key_text.lower() and isinstance(child, str) and child in P7_R54_AHR_POST_ELR19_DHR_INVALID_SOURCE_KIND_REFS:
                paths.append(f"{child_path}:{child}")
            paths.extend(_scan_invalid_source_kind_ref_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_invalid_source_kind_ref_paths(child, path=f"{path}[{index}]"))
    return paths


def _op04_status_reason_blocker_next(
    *,
    op03: Mapping[str, Any] | None,
    op03_valid: bool,
    external_claim: Mapping[str, Any] | None,
    source_kind_ref: str,
    source_kind_valid: bool,
    claim_bodyfree: bool,
    origin_ref: str,
    human_confirmed: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str, list[str], list[str]]:
    blockers: list[str] = []
    reasons: list[str] = []
    exclusions: list[str] = []
    invalid_sources: list[str] = []
    op03_ready = bool(op03_valid and isinstance(op03, Mapping) and op03.get("dhr_op03_ready_for_actual_source_claim_separation") is True)
    op03_waiting = bool(isinstance(op03, Mapping) and op03.get("dhr_op03_waiting_for_complete_evidence") is True)
    if not isinstance(op03, Mapping) or not op03_valid:
        blockers.append("dhr_op04_op03_receipt_candidate_extraction_invalid_or_missing")
    if isinstance(op03, Mapping) and op03.get("dhr_op03_repair_required") is True:
        blockers.append("dhr_op04_op03_receipt_candidate_extraction_repair_required")
    if op03_waiting and not blockers:
        reasons.append("dhr_op04_waits_because_op03_receipt_candidate_is_waiting")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF,
            _dedupe_clean_refs(reasons),
            [],
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_EXTERNAL_BODYFREE_ACTUAL_SOURCE_CLAIM_REF,
            [P7_R54_AHR_POST_ELR19_DHR_CANDIDATE_SHAPE_ONLY_EXCLUSION_REF],
            [],
        )
    if not op03_ready:
        blockers.append("dhr_op04_op03_not_ready_for_actual_source_claim_separation")
    if forbidden_paths:
        blockers.append("dhr_op04_external_actual_source_claim_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("dhr_op04_external_actual_source_claim_body_like_value_detected")
    if promotion_claims:
        blockers.append("dhr_op04_external_actual_source_claim_promotion_attempt_detected")
    if isinstance(external_claim, Mapping):
        if source_kind_ref in P7_R54_AHR_POST_ELR19_DHR_INVALID_SOURCE_KIND_REFS:
            invalid_sources.append(source_kind_ref)
            blockers.append("dhr_op04_external_actual_source_claim_invalid_source_kind_detected")
        elif not source_kind_valid:
            blockers.append("dhr_op04_external_actual_source_claim_source_kind_missing_or_not_actual")
        if not claim_bodyfree:
            blockers.append("dhr_op04_external_actual_source_claim_not_bodyfree")
        if origin_ref == "actual_source_claim_origin_missing_or_not_confirmed":
            blockers.append("dhr_op04_external_actual_source_claim_origin_missing")
    if blockers:
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF,
            ["dhr_op04_actual_source_claim_boundary_requires_repair_before_handoff_or_retry_decision"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF,
            _dedupe_clean_refs(exclusions),
            _dedupe_clean_refs(invalid_sources),
        )
    if not isinstance(external_claim, Mapping):
        reasons.append("dhr_op04_receipt_candidate_shape_is_not_actual_source_confirmation")
        exclusions.append(P7_R54_AHR_POST_ELR19_DHR_CANDIDATE_SHAPE_ONLY_EXCLUSION_REF)
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF,
            _dedupe_clean_refs(reasons),
            [],
            P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
            _dedupe_clean_refs(exclusions),
            [],
        )
    if source_kind_valid and claim_bodyfree and human_confirmed and origin_ref == P7_R54_AHR_POST_ELR19_DHR_EXTERNAL_ACTUAL_SOURCE_ORIGIN_REF:
        reasons.append("dhr_op04_external_actual_source_claim_confirmed_bodyfree_without_helper_created_receipts_or_rows")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF,
            _dedupe_clean_refs(reasons),
            [],
            P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
            [],
            [],
        )
    reasons.append("dhr_op04_external_actual_source_claim_not_sufficient_for_downstream_handoff")
    if not human_confirmed:
        exclusions.append("actual_local_only_human_review_by_person_not_confirmed")
    if origin_ref != P7_R54_AHR_POST_ELR19_DHR_EXTERNAL_ACTUAL_SOURCE_ORIGIN_REF:
        exclusions.append("external_actual_source_origin_not_confirmed")
    return (
        P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF,
        _dedupe_clean_refs(reasons),
        [],
        P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
        _dedupe_clean_refs(exclusions),
        [],
    )


def build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
    *,
    elr_op17_dmd_compatible_receipt_candidate_extraction: Mapping[str, Any] | None = None,
    op03_elr_op17_dmd_compatible_receipt_candidate_extraction: Mapping[str, Any] | None = None,
    external_actual_operation_evidence_claim_bodyfree_optional: Mapping[str, Any] | None = None,
    external_actual_operation_evidence_claim_optional: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP04 actual source claim separation material without promoting receipt shape."""

    op03 = elr_op17_dmd_compatible_receipt_candidate_extraction if elr_op17_dmd_compatible_receipt_candidate_extraction is not None else op03_elr_op17_dmd_compatible_receipt_candidate_extraction
    external_claim = external_actual_operation_evidence_claim_bodyfree_optional if external_actual_operation_evidence_claim_bodyfree_optional is not None else external_actual_operation_evidence_claim_optional
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op03.get("review_session_id") if isinstance(op03, Mapping) else None))
    if op03 is None:
        op03 = build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(review_session_id=session_id)
    try:
        op03_valid = assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(op03) is True
    except ValueError:
        op03_valid = False
    op03_map = op03 if isinstance(op03, Mapping) else {}
    claim_map = external_claim if isinstance(external_claim, Mapping) else None
    source_kind_ref = _external_claim_source_kind_ref(claim_map)
    source_kind_valid = source_kind_ref == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
    claim_bodyfree = _external_claim_bodyfree(claim_map)
    origin_ref = _external_claim_origin_ref(claim_map)
    human_confirmed = _external_claim_human_confirmed(claim_map)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(claim_map or {}, path="external_actual_operation_evidence_claim"), max_length=280)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(claim_map or {}, path="external_actual_operation_evidence_claim"), max_length=280)
    promotion_claims = _external_claim_promotion_refs(claim_map, path="external_actual_operation_evidence_claim")
    status_ref, reasons, blockers, next_required_step, exclusions, invalid_sources = _op04_status_reason_blocker_next(
        op03=op03,
        op03_valid=op03_valid,
        external_claim=claim_map,
        source_kind_ref=source_kind_ref,
        source_kind_valid=source_kind_valid,
        claim_bodyfree=claim_bodyfree,
        origin_ref=origin_ref,
        human_confirmed=human_confirmed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    confirmed = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    not_confirmed = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF
    waiting = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    repair = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF
    ready_for_scan = status_ref in (
        P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF,
        P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF,
    )
    receipt_candidate = op03_map.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree") if isinstance(op03_map.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree"), Mapping) else {}
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": _clean_ref(op03_map.get("schema_version"), default="op03_schema_missing", max_length=260),
        "op03_material_ref": _clean_ref(op03_map.get("material_id"), default="op03_material_missing", max_length=260),
        "op03_next_required_step": _clean_ref(op03_map.get("next_required_step"), default="op03_next_required_step_missing", max_length=260),
        "op03_receipt_candidate_extraction_status_ref": _clean_ref(op03_map.get("dhr_op03_status_ref"), default="op03_status_missing", max_length=260),
        "op03_ready_for_actual_source_claim_separation": bool(op03_map.get("dhr_op03_ready_for_actual_source_claim_separation") is True),
        "op03_contract_valid": op03_valid,
        "dhr_op04_status_ref": status_ref,
        "actual_source_claim_separation_status_ref": status_ref,
        "dhr_op04_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP04_ALLOWED_STATUS_REFS),
        "dhr_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP04_ALLOWED_STATUS_REFS),
        "dhr_op04_ready": ready_for_scan,
        "dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan": ready_for_scan,
        "dhr_op04_reason_refs": reasons,
        "dhr_op04_reason_ref_count": len(reasons),
        "dhr_op04_blocker_refs": blockers,
        "dhr_op04_blocker_ref_count": len(blockers),
        "receipt_shape_valid": bool(op03_map.get("receipt_shape_valid") is True),
        "receipt_source_kind_ref": _clean_ref(op03_map.get("receipt_source_kind_ref"), default="receipt_source_kind_missing", max_length=180),
        "receipt_count_fields_are_24": bool(op03_map.get("receipt_count_fields_are_24") is True),
        "receipt_required_true_fields_passed": bool(op03_map.get("receipt_required_true_fields_passed") is True),
        "receipt_body_free": bool(op03_map.get("receipt_body_free") is True),
        "receipt_candidate_bodyfree_present": bool(receipt_candidate),
        "receipt_candidate_source_kind_ref": _clean_ref(receipt_candidate.get("source_kind_ref") if isinstance(receipt_candidate, Mapping) else "", default="receipt_candidate_source_kind_missing", max_length=180),
        "receipt_candidate_shape_carried_only": True,
        "candidate_shape_promoted_to_actual_source": False,
        "external_actual_operation_evidence_claim_optional_present": isinstance(claim_map, Mapping),
        "external_actual_operation_evidence_claim_source_kind_ref": source_kind_ref,
        "external_actual_operation_evidence_claim_source_kind_valid": source_kind_valid,
        "external_actual_operation_evidence_claim_bodyfree": claim_bodyfree,
        "external_actual_operation_evidence_claim_origin_ref": origin_ref,
        "external_actual_operation_evidence_claim_forbidden_payload_key_path_refs": forbidden_paths,
        "external_actual_operation_evidence_claim_forbidden_payload_key_path_count": len(forbidden_paths),
        "external_actual_operation_evidence_claim_body_like_value_path_refs": body_like_paths,
        "external_actual_operation_evidence_claim_body_like_value_path_count": len(body_like_paths),
        "external_actual_operation_evidence_claim_promotion_claim_refs": promotion_claims,
        "external_actual_operation_evidence_claim_promotion_claim_ref_count": len(promotion_claims),
        "actual_source_claim_status_ref": status_ref,
        "actual_source_claim_confirmed_for_downstream_handoff": confirmed,
        "actual_source_claim_bodyfree": bool(confirmed and claim_bodyfree),
        "actual_source_claim_origin_ref": origin_ref if confirmed else "actual_source_claim_origin_missing_or_not_confirmed",
        "actual_local_only_human_review_by_person_confirmed": bool(confirmed and human_confirmed),
        "actual_source_claim_requires_external_bodyfree_evidence": not confirmed,
        "actual_source_claim_missing_or_not_confirmed": not_confirmed,
        "actual_source_invalid_repair_required": repair,
        "actual_source_waiting_for_external_bodyfree_claim": waiting,
        "actual_source_exclusion_refs": exclusions,
        "actual_source_exclusion_ref_count": len(exclusions),
        "invalid_source_kind_refs": invalid_sources,
        "invalid_source_kind_ref_count": len(invalid_sources),
        "helper_green_promoted_to_actual_source": False,
        "target_green_promoted_to_actual_source": False,
        "result_memo_green_promoted_to_actual_source": False,
        "fixture_promoted_to_actual_source": False,
        "historical_reuse_promoted_to_actual_source": False,
        "actual_operation_receipt_created_by_helper_here": False,
        "actual_rows_created_by_helper_here": False,
        "dhr_op04_does_not_resolve_final_branch": True,
        "dhr_op04_does_not_generate_body_full_packet": True,
        "dhr_op04_does_not_run_actual_local_human_review": True,
        "dhr_op04_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op04_does_not_execute_dmd_or_r52": True,
        "dhr_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHR-OP04 actual-source claim separation and invalid-source classification contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP04")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP04")
    if data.get("op03_schema_version") != P7_R54_AHR_POST_ELR19_DHR_OP03_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 OP03 schema version changed")
    if data.get("actual_source_claim_separation_status_ref") != data.get("dhr_op04_status_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 status alias changed")
    if tuple(data.get("dhr_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 allowed status refs changed")
    for field, count_field in (
        ("dhr_op04_allowed_status_refs", "dhr_op04_allowed_status_ref_count"),
        ("dhr_op04_reason_refs", "dhr_op04_reason_ref_count"),
        ("dhr_op04_blocker_refs", "dhr_op04_blocker_ref_count"),
        ("external_actual_operation_evidence_claim_forbidden_payload_key_path_refs", "external_actual_operation_evidence_claim_forbidden_payload_key_path_count"),
        ("external_actual_operation_evidence_claim_body_like_value_path_refs", "external_actual_operation_evidence_claim_body_like_value_path_count"),
        ("external_actual_operation_evidence_claim_promotion_claim_refs", "external_actual_operation_evidence_claim_promotion_claim_ref_count"),
        ("actual_source_exclusion_refs", "actual_source_exclusion_ref_count"),
        ("invalid_source_kind_refs", "invalid_source_kind_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP04 {count_field} changed")
    for key in (
        "dhr_op04_does_not_resolve_final_branch",
        "dhr_op04_does_not_generate_body_full_packet",
        "dhr_op04_does_not_run_actual_local_human_review",
        "dhr_op04_does_not_create_receipts_rows_or_disposal",
        "dhr_op04_does_not_execute_dmd_or_r52",
        "dhr_op04_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op04_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
        "receipt_candidate_shape_carried_only",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP04 required true boundary changed: {key}")
    for key in (
        "candidate_shape_promoted_to_actual_source",
        "helper_green_promoted_to_actual_source",
        "target_green_promoted_to_actual_source",
        "result_memo_green_promoted_to_actual_source",
        "fixture_promoted_to_actual_source",
        "historical_reuse_promoted_to_actual_source",
        "actual_operation_receipt_created_by_helper_here",
        "actual_rows_created_by_helper_here",
        "dmd_execution_started_here",
        "dmd_auto_execution_allowed",
        "manual_decision_auto_executes_downstream",
        "r52_actual_execution_started_here",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP04 source or downstream flag promoted: {key}")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP04_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-yet steps changed")
    status_ref = data.get("dhr_op04_status_ref")
    if status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF:
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 confirmed status must confirm actual source")
        for key in (
            "op03_contract_valid",
            "op03_ready_for_actual_source_claim_separation",
            "receipt_shape_valid",
            "receipt_candidate_bodyfree_present",
            "external_actual_operation_evidence_claim_optional_present",
            "external_actual_operation_evidence_claim_source_kind_valid",
            "external_actual_operation_evidence_claim_bodyfree",
            "actual_source_claim_bodyfree",
            "actual_local_only_human_review_by_person_confirmed",
            "dhr_op04_ready",
            "dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP04 confirmed branch required true changed: {key}")
        if data.get("actual_source_claim_origin_ref") != P7_R54_AHR_POST_ELR19_DHR_EXTERNAL_ACTUAL_SOURCE_ORIGIN_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 confirmed origin changed")
        if data.get("invalid_source_kind_refs") != [] or data.get("dhr_op04_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 confirmed branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 confirmed next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF:
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not False or data.get("actual_source_claim_missing_or_not_confirmed") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-confirmed branch flags changed")
        if data.get("dhr_op04_ready") is not True or data.get("dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-confirmed branch must continue to preflight scan")
        if data.get("dhr_op04_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-confirmed branch cannot carry repair blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 not-confirmed next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF:
        if data.get("dhr_op04_ready") is not False or data.get("actual_source_waiting_for_external_bodyfree_claim") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 waiting branch flags changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_EXTERNAL_BODYFREE_ACTUAL_SOURCE_CLAIM_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("dhr_op04_ready") is not False or data.get("actual_source_invalid_repair_required") is not True or not data.get("dhr_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 repair branch must carry blockers")
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 repair branch cannot confirm actual source")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 repair next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP04 status ref is not allowed")
    return True


def _op05_scan_materials(op04: Mapping[str, Any] | None, additional_materials: Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    materials: list[Mapping[str, Any]] = []
    if isinstance(op04, Mapping):
        materials.append(op04)
    if additional_materials:
        for material in additional_materials:
            if isinstance(material, Mapping):
                materials.append(material)
    return materials


def _scan_materials_forbidden_paths(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    paths: list[str] = []
    for index, material in enumerate(materials):
        paths.extend(_scan_forbidden_payload_key_paths(material, path=f"preflight_material[{index}]"))
    return _dedupe_clean_refs(paths, max_length=280)


def _scan_materials_body_like_paths(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    paths: list[str] = []
    for index, material in enumerate(materials):
        paths.extend(_scan_body_like_value_paths(material, path=f"preflight_material[{index}]"))
    return _dedupe_clean_refs(paths, max_length=280)


def _scan_materials_promotion_claim_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for index, material in enumerate(materials):
        refs.extend(f"preflight_material[{index}].{ref}" for ref in _promotion_claim_refs(material))
        refs.extend(f"preflight_material[{index}].{field}" for field in P7_R54_AHR_POST_ELR19_DHR_ACTUAL_SOURCE_PROMOTION_FIELD_REFS if material.get(field) is True)
    return _dedupe_clean_refs(refs, max_length=280)


def _scan_materials_invalid_source_kind_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    refs: list[str] = []
    for index, material in enumerate(materials):
        refs.extend(_scan_invalid_source_kind_ref_paths(material, path=f"preflight_material[{index}]"))
    return _dedupe_clean_refs(refs, max_length=280)


def _op05_status_reason_blocker_next(
    *,
    op04: Mapping[str, Any] | None,
    op04_valid: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    invalid_sources: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    reasons: list[str] = []
    if not isinstance(op04, Mapping) or not op04_valid:
        blockers.append("dhr_op05_op04_actual_source_claim_separation_invalid_or_missing")
    if isinstance(op04, Mapping) and op04.get("actual_source_invalid_repair_required") is True:
        blockers.append("dhr_op05_actual_source_repair_carried_from_op04")
    if forbidden_paths:
        blockers.append("dhr_op05_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("dhr_op05_body_like_value_detected")
    if promotion_claims:
        blockers.append("dhr_op05_promotion_claim_detected")
    if invalid_sources:
        blockers.append("dhr_op05_invalid_source_kind_detected")
    if blockers:
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF,
            ["dhr_op05_preflight_scan_requires_repair_before_branch_resolution"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF,
        )
    if not bool(isinstance(op04, Mapping) and op04.get("actual_source_claim_confirmed_for_downstream_handoff") is True):
        reasons.append("dhr_op05_scan_clear_but_actual_source_claim_not_confirmed_for_downstream_handoff")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF,
            _dedupe_clean_refs(reasons),
            [],
            P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF,
        )
    reasons.append("dhr_op05_preflight_scan_clear_with_manual_dmd_handoff_plan_candidate_allowed")
    return (
        P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF,
        _dedupe_clean_refs(reasons),
        [],
        P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF,
    )


def build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(
    *,
    actual_source_claim_separation: Mapping[str, Any] | None = None,
    op04_actual_source_claim_separation: Mapping[str, Any] | None = None,
    additional_bodyfree_materials: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP05 body-free leak / promotion / DMD compatibility preflight scan."""

    op04 = actual_source_claim_separation if actual_source_claim_separation is not None else op04_actual_source_claim_separation
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op04.get("review_session_id") if isinstance(op04, Mapping) else None))
    if op04 is None:
        op04 = build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(review_session_id=session_id)
    try:
        op04_valid = assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(op04) is True
    except ValueError:
        op04_valid = False
    materials = _op05_scan_materials(op04 if isinstance(op04, Mapping) else None, additional_bodyfree_materials)
    forbidden_paths = _scan_materials_forbidden_paths(materials)
    body_like_paths = _scan_materials_body_like_paths(materials)
    promotion_claims = _scan_materials_promotion_claim_refs(materials)
    invalid_sources = _scan_materials_invalid_source_kind_refs(materials)
    status_ref, reasons, blockers, next_required_step = _op05_status_reason_blocker_next(
        op04=op04,
        op04_valid=op04_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        invalid_sources=invalid_sources,
    )
    confirmed = bool(isinstance(op04, Mapping) and op04.get("actual_source_claim_confirmed_for_downstream_handoff") is True)
    repair = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF
    clear = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF
    waiting_or_incomplete = status_ref == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF
    handoff_allowed = bool(clear and confirmed)
    handoff_blockers: list[str] = []
    if not handoff_allowed:
        if repair:
            handoff_blockers.append("dhr_op05_repair_required_before_dmd_handoff_plan_candidate")
        if not confirmed:
            handoff_blockers.append("dhr_op05_actual_source_claim_not_confirmed_for_dmd_handoff_plan_candidate")
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": _clean_ref(op04.get("schema_version") if isinstance(op04, Mapping) else "", default="op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id") if isinstance(op04, Mapping) else "", default="op04_material_missing", max_length=260),
        "op04_next_required_step": _clean_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else "", default="op04_next_required_step_missing", max_length=260),
        "op04_actual_source_claim_status_ref": _clean_ref(op04.get("actual_source_claim_status_ref") if isinstance(op04, Mapping) else "", default="op04_actual_source_status_missing", max_length=260),
        "op04_actual_source_claim_confirmed_for_downstream_handoff": confirmed,
        "op04_invalid_source_kind_ref_count": int(op04.get("invalid_source_kind_ref_count") or 0) if isinstance(op04, Mapping) and not isinstance(op04.get("invalid_source_kind_ref_count"), bool) else 0,
        "op04_ready_for_preflight_scan": bool(isinstance(op04, Mapping) and op04.get("dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan") is True),
        "op04_contract_valid": op04_valid,
        "dhr_op05_status_ref": status_ref,
        "preflight_scan_status_ref": status_ref,
        "dhr_op05_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS),
        "dhr_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS),
        "dhr_op05_ready": not repair,
        "dhr_op05_ready_for_branch_resolver": not repair,
        "dhr_op05_reason_refs": reasons,
        "dhr_op05_reason_ref_count": len(reasons),
        "dhr_op05_blocker_refs": blockers,
        "dhr_op05_blocker_ref_count": len(blockers),
        "scanned_material_ref_count": len(materials),
        "forbidden_payload_key_path_refs": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "body_like_value_path_refs": body_like_paths,
        "body_like_value_path_count": len(body_like_paths),
        "promotion_claim_refs": promotion_claims,
        "promotion_claim_ref_count": len(promotion_claims),
        "invalid_source_kind_refs": invalid_sources,
        "invalid_source_kind_ref_count": len(invalid_sources),
        "bodyfree_leak_promotion_source_scan_passed": not repair,
        "preflight_scan_passed": clear,
        "preflight_repair_required": repair,
        "preflight_waiting_or_incomplete": waiting_or_incomplete,
        "actual_source_claim_confirmed_for_downstream_handoff": confirmed,
        "evidence_incomplete_or_source_not_confirmed": not confirmed and not repair,
        "dmd_direct_call_safe_without_adapter": False,
        "dmd_direct_call_blocker_refs": [P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF],
        "dmd_direct_call_blocker_ref_count": 1,
        "dmd_direct_call_reason_ref": P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF,
        "dmh_op18_finalizer_fake_generation_allowed": False,
        "dmd_handoff_plan_candidate_allowed": handoff_allowed,
        "dmd_handoff_plan_candidate_blocker_refs": _dedupe_clean_refs(handoff_blockers, max_length=260),
        "dmd_handoff_plan_candidate_blocker_ref_count": len(_dedupe_clean_refs(handoff_blockers, max_length=260)),
        "dmd_alternate_post_elr19_intake_may_be_required": handoff_allowed,
        "dhr_op05_does_not_resolve_final_branch": True,
        "dhr_op05_does_not_generate_body_full_packet": True,
        "dhr_op05_does_not_run_actual_local_human_review": True,
        "dhr_op05_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op05_does_not_execute_dmd_or_r52": True,
        "dhr_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHR-OP05 preflight scan contract without executing DMD or generating a fake DMH finalizer."""

    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP05")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP05")
    if data.get("op04_schema_version") != P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 OP04 schema version changed")
    if data.get("preflight_scan_status_ref") != data.get("dhr_op05_status_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 status alias changed")
    if tuple(data.get("dhr_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 allowed status refs changed")
    for field, count_field in (
        ("dhr_op05_allowed_status_refs", "dhr_op05_allowed_status_ref_count"),
        ("dhr_op05_reason_refs", "dhr_op05_reason_ref_count"),
        ("dhr_op05_blocker_refs", "dhr_op05_blocker_ref_count"),
        ("forbidden_payload_key_path_refs", "forbidden_payload_key_path_count"),
        ("body_like_value_path_refs", "body_like_value_path_count"),
        ("promotion_claim_refs", "promotion_claim_ref_count"),
        ("invalid_source_kind_refs", "invalid_source_kind_ref_count"),
        ("dmd_direct_call_blocker_refs", "dmd_direct_call_blocker_ref_count"),
        ("dmd_handoff_plan_candidate_blocker_refs", "dmd_handoff_plan_candidate_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP05 {count_field} changed")
    for key in (
        "dhr_op05_does_not_resolve_final_branch",
        "dhr_op05_does_not_generate_body_full_packet",
        "dhr_op05_does_not_run_actual_local_human_review",
        "dhr_op05_does_not_create_receipts_rows_or_disposal",
        "dhr_op05_does_not_execute_dmd_or_r52",
        "dhr_op05_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op05_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP05 required true boundary changed: {key}")
    for key in (
        "dmd_direct_call_safe_without_adapter",
        "dmh_op18_finalizer_fake_generation_allowed",
        "dmd_execution_started_here",
        "dmd_auto_execution_allowed",
        "manual_decision_auto_executes_downstream",
        "r52_actual_execution_started_here",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP05 direct execution or promotion flag changed: {key}")
    if data.get("dmd_direct_call_blocker_refs") != [P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF]:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 direct DMD call blocker changed")
    if data.get("dmd_direct_call_reason_ref") != P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_BLOCKER_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 direct DMD call reason changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP05_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 not-yet steps changed")
    status_ref = data.get("dhr_op05_status_ref")
    if status_ref == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF:
        if data.get("dhr_op05_ready") is not True or data.get("dhr_op05_ready_for_branch_resolver") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 clear status must be ready for branch resolver")
        if data.get("preflight_scan_passed") is not True or data.get("bodyfree_leak_promotion_source_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 clear status scan flags changed")
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not True or data.get("dmd_handoff_plan_candidate_allowed") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 clear status requires confirmed source and handoff candidate allowance")
        if data.get("preflight_repair_required") is not False or data.get("preflight_waiting_or_incomplete") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 clear status repair/wait flags changed")
        if any(data.get(field) for field in ("forbidden_payload_key_path_refs", "body_like_value_path_refs", "promotion_claim_refs", "invalid_source_kind_refs", "dhr_op05_blocker_refs")):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 clear status cannot carry scan blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 clear next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF:
        if data.get("dhr_op05_ready") is not True or data.get("dhr_op05_ready_for_branch_resolver") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 waiting/incomplete status still proceeds to branch resolver")
        if data.get("preflight_waiting_or_incomplete") is not True or data.get("evidence_incomplete_or_source_not_confirmed") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 waiting/incomplete flags changed")
        if data.get("preflight_repair_required") is not False or data.get("dmd_handoff_plan_candidate_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 waiting/incomplete cannot allow handoff candidate")
        if data.get("dhr_op05_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 waiting/incomplete cannot carry repair blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 waiting/incomplete next step changed")
    elif status_ref == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF:
        if data.get("dhr_op05_ready") is not False or data.get("dhr_op05_ready_for_branch_resolver") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 repair status cannot proceed")
        if data.get("preflight_repair_required") is not True or not data.get("dhr_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 repair status must carry blockers")
        if data.get("dmd_handoff_plan_candidate_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 repair status cannot allow handoff candidate")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 repair next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP05 status ref is not allowed")
    return True


build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_actual_source_claim_separation_invalid_source_classification = (
    build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract
)
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan = (
    build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract
)


# ---------------------------------------------------------------------------
# DHR-OP06 / DHR-OP07: deterministic branch resolver and manual material.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_ELR19_DHR_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op06_handoff_or_retry_deterministic_branch_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op07_manual_decision_materialization.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:7]
)
P7_R54_AHR_POST_ELR19_DHR_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[7:]
)
P7_R54_AHR_POST_ELR19_DHR_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:8]
)
P7_R54_AHR_POST_ELR19_DHR_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[8:]
)

P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF: Final = (
    "DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION"
)
P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF: Final = (
    "DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF"
)
P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF: Final = (
    "DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF: Final = (
    "DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD"
)
P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF: Final = (
    "DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED"
)
P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF,
    P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF,
    P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF,
    P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF,
)
P7_R54_AHR_POST_ELR19_DHR_BRANCH_RESOLVER_PRIORITY_REFS: Final[tuple[str, ...]] = (
    "repair_required",
    "elr_op19_not_closed_or_elr_op18_or_op17_waiting",
    "actual_source_claim_not_confirmed_or_evidence_incomplete",
    "dmd_handoff_ready_manual_decision_required",
    "unresolved_manual_hold",
)

P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_OP06_BRANCH_RESOLVED_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_WAITING_REF: Final = (
    "DHR_OP06_BRANCH_RESOLVED_WAITING"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_RETRY_OR_START_REQUIRED_REF: Final = (
    "DHR_OP06_BRANCH_RESOLVED_RETRY_OR_START_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF: Final = (
    "DHR_OP06_BRANCH_RESOLVED_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    "DHR_OP06_BRANCH_RESOLVED_MANUAL_HOLD_UNRESOLVED"
)
P7_R54_AHR_POST_ELR19_DHR_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_WAITING_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_RETRY_OR_START_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_MANUAL_HOLD_UNRESOLVED_REF,
)
P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_OP07_MANUAL_DECISION_MATERIALIZED_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_WAITING_REF: Final = (
    "DHR_OP07_MANUAL_DECISION_MATERIALIZED_WAITING"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_RETRY_OR_START_REQUIRED_REF: Final = (
    "DHR_OP07_MANUAL_DECISION_MATERIALIZED_RETRY_OR_START_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF: Final = (
    "DHR_OP07_MANUAL_DECISION_MATERIALIZED_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    "DHR_OP07_MANUAL_DECISION_MATERIALIZED_MANUAL_HOLD_UNRESOLVED"
)
P7_R54_AHR_POST_ELR19_DHR_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_WAITING_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_RETRY_OR_START_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_MANUAL_HOLD_UNRESOLVED_REF,
)

P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF: Final = (
    "manual_decision_execute_or_decline_dmd_handoff_without_auto_promotion"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF: Final = (
    "wait_for_elr_complete_evidence_or_manual_hold_material"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_KEEP_DOWNSTREAM_MANUAL_DECISION_HOLD_WITHOUT_PROMOTION_REF: Final = (
    "keep_downstream_manual_decision_hold_without_promotion"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP07_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF

P7_R54_AHR_POST_ELR19_DHR_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_contract_valid", "op05_ready",
    "op05_ready_for_branch_resolver", "op05_next_required_step", "op05_preflight_scan_passed", "op05_preflight_repair_required",
    "op05_preflight_waiting_or_incomplete", "op05_actual_source_claim_status_ref", "op05_actual_source_claim_confirmed_for_downstream_handoff",
    "op05_evidence_incomplete_or_source_not_confirmed", "op05_dmd_handoff_plan_candidate_allowed",
    "op05_dmd_handoff_plan_candidate_blocker_refs", "op05_dmd_handoff_plan_candidate_blocker_ref_count",
    "op05_dmd_direct_call_safe_without_adapter", "op05_dmh_op18_finalizer_fake_generation_allowed",
    "op05_forbidden_payload_key_path_count", "op05_body_like_value_path_count", "op05_promotion_claim_ref_count",
    "op05_invalid_source_kind_ref_count", "op05_dhr_op05_blocker_refs", "op05_dhr_op05_blocker_ref_count",
    "dhr_op06_status_ref", "branch_resolution_status_ref", "dhr_op06_allowed_status_refs", "dhr_op06_allowed_status_ref_count",
    "dhr_op06_ready", "branch_resolver_ready", "dhr_op06_branch_resolved", "resolver_priority_refs", "resolver_priority_ref_count",
    "repair_precedence_applied", "wait_precedence_applied", "retry_or_start_precedence_applied",
    "handoff_ready_selected_after_no_repair_no_wait_no_retry", "unresolved_manual_hold_selected",
    "branch_ref", "selected_branch_ref", "branch_reason_refs", "branch_reason_ref_count", "branch_blocker_refs", "branch_blocker_ref_count",
    "next_required_step", "next_dhr_step_ref", "bodyfree_evidence_boundary_repair_required", "elr_complete_evidence_or_manual_hold_waiting_required",
    "retry_or_start_actual_local_only_human_review_required", "dmd_handoff_ready_manual_decision_required_no_auto_execution",
    "manual_decision_hold_continues_unresolved", "dmd_handoff_allowed_as_manual_decision_candidate",
    "manual_decision_required_without_auto_execution", "dhr_op06_does_not_materialize_manual_decision",
    "dhr_op06_does_not_generate_body_full_packet", "dhr_op06_does_not_run_actual_local_human_review",
    "dhr_op06_does_not_create_receipts_rows_or_disposal", "dhr_op06_does_not_execute_dmd_or_r52",
    "dhr_op06_does_not_start_p5_p6_p8_p7_or_release", "dhr_op06_does_not_change_api_db_rn_runtime_response_key",
    "dmd_direct_call_safe_without_adapter", "dmh_op18_finalizer_fake_generation_allowed", "dmd_execution_started_here",
    "r52_actual_execution_started_here", "p8_start_allowed", "release_allowed", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "public_contract",
    "post_elr19_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_ELR19_DHR_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_contract_valid", "op06_ready",
    "op06_branch_ref", "op06_next_required_step", "dhr_op07_status_ref", "dhr_op07_allowed_status_refs",
    "dhr_op07_allowed_status_ref_count", "dhr_op07_ready", "manual_decision_materialized",
    "manual_decision_materialized_bodyfree", "manual_decision_required", "manual_decision_required_without_auto_execution",
    "manual_decision_auto_executes_downstream", "manual_decision_materialization_from_branch_resolver",
    "selected_branch_ref", "recommended_next_step_ref", "next_required_step", "operator_action_required",
    "dmd_handoff_allowed_as_manual_decision_candidate", "retry_or_start_required", "repair_required", "waiting_required",
    "hold_continues", "branch_reason_refs", "branch_reason_ref_count", "branch_blocker_refs", "branch_blocker_ref_count",
    "auto_executes_dmd", "auto_executes_r52", "auto_starts_actual_review", "auto_starts_p8", "release_allowed",
    "dhr_op07_does_not_generate_body_full_packet", "dhr_op07_does_not_run_actual_local_human_review",
    "dhr_op07_does_not_create_receipts_rows_or_disposal", "dhr_op07_does_not_execute_dmd_or_r52",
    "dhr_op07_does_not_start_p5_p6_p8_p7_or_release", "dhr_op07_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "public_contract", "post_elr19_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op06_status_branch_next(
    op05: Mapping[str, Any] | None,
    *,
    op05_valid: bool,
) -> tuple[str, str, str, bool, bool, bool, bool, bool, list[str], list[str]]:
    """Resolve DHR-OP06 branch using repair > wait > retry > handoff > unresolved precedence."""

    reasons: list[str] = []
    blockers: list[str] = []
    op05_status = _clean_ref(op05.get("dhr_op05_status_ref") if isinstance(op05, Mapping) else "", default="op05_status_missing", max_length=220)
    op04_source_status = _clean_ref(op05.get("op04_actual_source_claim_status_ref") if isinstance(op05, Mapping) else "", default="op04_actual_source_status_missing", max_length=260)
    op05_blockers = [
        _clean_ref(ref, max_length=220)
        for ref in (op05.get("dhr_op05_blocker_refs") if isinstance(op05, Mapping) else []) or []
    ]
    repair = (
        not isinstance(op05, Mapping)
        or not op05_valid
        or op05_status == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF
        or bool(isinstance(op05, Mapping) and op05.get("preflight_repair_required") is True)
        or bool(op05_blockers)
    )
    if repair:
        blockers.extend(op05_blockers or ["dhr_op06_op05_preflight_scan_invalid_or_repair_required"])
        reasons.append("dhr_op06_repair_precedence_selected_before_wait_retry_or_handoff")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF,
            True,
            False,
            False,
            False,
            False,
            _dedupe_clean_refs(reasons),
            _dedupe_clean_refs(blockers),
        )

    waiting = op04_source_status == P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF
    if waiting:
        reasons.append("dhr_op06_wait_precedence_selected_for_elr_complete_evidence_or_manual_hold_material")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_WAITING_REF,
            P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF,
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF,
            False,
            True,
            False,
            False,
            False,
            _dedupe_clean_refs(reasons),
            [],
        )

    actual_source_confirmed = bool(
        isinstance(op05, Mapping)
        and op05.get("actual_source_claim_confirmed_for_downstream_handoff") is True
    )
    evidence_incomplete = (
        op05_status == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF
        or bool(isinstance(op05, Mapping) and op05.get("evidence_incomplete_or_source_not_confirmed") is True)
        or not actual_source_confirmed
    )
    if evidence_incomplete:
        reasons.append("dhr_op06_retry_or_start_selected_because_actual_source_claim_is_not_confirmed_for_downstream_handoff")
        blockers.append("dhr_op06_actual_source_claim_not_confirmed_or_evidence_incomplete")
        if isinstance(op05, Mapping) and op05.get("dmd_handoff_plan_candidate_allowed") is False:
            blockers.append("dhr_op06_dmd_handoff_plan_candidate_not_allowed_by_preflight")
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_RETRY_OR_START_REQUIRED_REF,
            P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF,
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF,
            False,
            False,
            True,
            False,
            False,
            _dedupe_clean_refs(reasons),
            _dedupe_clean_refs(blockers),
        )

    handoff_ready = (
        op05_status == P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF
        and bool(isinstance(op05, Mapping) and op05.get("preflight_scan_passed") is True)
        and bool(isinstance(op05, Mapping) and op05.get("dmd_handoff_plan_candidate_allowed") is True)
        and actual_source_confirmed
    )
    if handoff_ready:
        reasons.extend(
            [
                "dhr_op06_handoff_ready_selected_after_no_repair_no_wait_and_actual_source_confirmed",
                "dhr_op06_dmd_handoff_remains_manual_and_no_auto_execution",
            ]
        )
        return (
            P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF,
            P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF,
            P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF,
            False,
            False,
            False,
            True,
            False,
            _dedupe_clean_refs(reasons),
            [],
        )

    reasons.append("dhr_op06_manual_decision_hold_continues_because_branch_inputs_are_unresolved")
    blockers.append("dhr_op06_unresolved_manual_hold_after_preflight")
    return (
        P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_MANUAL_HOLD_UNRESOLVED_REF,
        P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF,
        P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_KEEP_DOWNSTREAM_MANUAL_DECISION_HOLD_WITHOUT_PROMOTION_REF,
        False,
        False,
        False,
        False,
        True,
        _dedupe_clean_refs(reasons),
        _dedupe_clean_refs(blockers),
    )


def build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(
    *,
    bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan: Mapping[str, Any] | None = None,
    op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP06 branch resolver without executing any selected branch."""

    op05 = bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan if bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan is not None else op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op05.get("review_session_id") if isinstance(op05, Mapping) else None))
    if op05 is None:
        op05 = build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan(review_session_id=session_id)
    try:
        op05_valid = assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(op05) is True
    except ValueError:
        op05_valid = False

    status_ref, branch_ref, next_required_step, repair_branch, wait_branch, retry_branch, handoff_branch, unresolved_branch, reasons, blockers = _op06_status_branch_next(
        op05 if isinstance(op05, Mapping) else None,
        op05_valid=op05_valid,
    )
    op05_map = op05 if isinstance(op05, Mapping) else {}
    candidate_blockers = _dedupe_clean_refs(op05_map.get("dmd_handoff_plan_candidate_blocker_refs") or [], max_length=260)
    op05_blockers = _dedupe_clean_refs(op05_map.get("dhr_op05_blocker_refs") or [], max_length=260)
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": _clean_ref(op05_map.get("schema_version"), default="op05_schema_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05_map.get("material_id"), default="op05_material_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05_map.get("dhr_op05_status_ref"), default="op05_status_missing", max_length=260),
        "op05_contract_valid": op05_valid,
        "op05_ready": bool(isinstance(op05, Mapping) and op05_map.get("dhr_op05_ready") is True),
        "op05_ready_for_branch_resolver": bool(isinstance(op05, Mapping) and op05_map.get("dhr_op05_ready_for_branch_resolver") is True),
        "op05_next_required_step": _clean_ref(op05_map.get("next_required_step"), default="op05_next_required_step_missing", max_length=260),
        "op05_preflight_scan_passed": bool(isinstance(op05, Mapping) and op05_map.get("preflight_scan_passed") is True),
        "op05_preflight_repair_required": bool(isinstance(op05, Mapping) and op05_map.get("preflight_repair_required") is True),
        "op05_preflight_waiting_or_incomplete": bool(isinstance(op05, Mapping) and op05_map.get("preflight_waiting_or_incomplete") is True),
        "op05_actual_source_claim_status_ref": _clean_ref(op05_map.get("op04_actual_source_claim_status_ref"), default="op04_actual_source_status_missing", max_length=260),
        "op05_actual_source_claim_confirmed_for_downstream_handoff": bool(isinstance(op05, Mapping) and op05_map.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
        "op05_evidence_incomplete_or_source_not_confirmed": bool(isinstance(op05, Mapping) and op05_map.get("evidence_incomplete_or_source_not_confirmed") is True),
        "op05_dmd_handoff_plan_candidate_allowed": bool(isinstance(op05, Mapping) and op05_map.get("dmd_handoff_plan_candidate_allowed") is True),
        "op05_dmd_handoff_plan_candidate_blocker_refs": candidate_blockers,
        "op05_dmd_handoff_plan_candidate_blocker_ref_count": len(candidate_blockers),
        "op05_dmd_direct_call_safe_without_adapter": bool(isinstance(op05, Mapping) and op05_map.get("dmd_direct_call_safe_without_adapter") is True),
        "op05_dmh_op18_finalizer_fake_generation_allowed": bool(isinstance(op05, Mapping) and op05_map.get("dmh_op18_finalizer_fake_generation_allowed") is True),
        "op05_forbidden_payload_key_path_count": int(op05_map.get("forbidden_payload_key_path_count") or 0) if not isinstance(op05_map.get("forbidden_payload_key_path_count"), bool) else 0,
        "op05_body_like_value_path_count": int(op05_map.get("body_like_value_path_count") or 0) if not isinstance(op05_map.get("body_like_value_path_count"), bool) else 0,
        "op05_promotion_claim_ref_count": int(op05_map.get("promotion_claim_ref_count") or 0) if not isinstance(op05_map.get("promotion_claim_ref_count"), bool) else 0,
        "op05_invalid_source_kind_ref_count": int(op05_map.get("invalid_source_kind_ref_count") or 0) if not isinstance(op05_map.get("invalid_source_kind_ref_count"), bool) else 0,
        "op05_dhr_op05_blocker_refs": op05_blockers,
        "op05_dhr_op05_blocker_ref_count": len(op05_blockers),
        "dhr_op06_status_ref": status_ref,
        "branch_resolution_status_ref": status_ref,
        "dhr_op06_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP06_ALLOWED_STATUS_REFS),
        "dhr_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP06_ALLOWED_STATUS_REFS),
        "dhr_op06_ready": True,
        "branch_resolver_ready": True,
        "dhr_op06_branch_resolved": True,
        "resolver_priority_refs": list(P7_R54_AHR_POST_ELR19_DHR_BRANCH_RESOLVER_PRIORITY_REFS),
        "resolver_priority_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_BRANCH_RESOLVER_PRIORITY_REFS),
        "repair_precedence_applied": repair_branch,
        "wait_precedence_applied": wait_branch,
        "retry_or_start_precedence_applied": retry_branch,
        "handoff_ready_selected_after_no_repair_no_wait_no_retry": handoff_branch,
        "unresolved_manual_hold_selected": unresolved_branch,
        "branch_ref": branch_ref,
        "selected_branch_ref": branch_ref,
        "branch_reason_refs": reasons,
        "branch_reason_ref_count": len(reasons),
        "branch_blocker_refs": blockers,
        "branch_blocker_ref_count": len(blockers),
        "next_required_step": next_required_step,
        "next_dhr_step_ref": P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP07_REF,
        "bodyfree_evidence_boundary_repair_required": repair_branch,
        "elr_complete_evidence_or_manual_hold_waiting_required": wait_branch,
        "retry_or_start_actual_local_only_human_review_required": retry_branch,
        "dmd_handoff_ready_manual_decision_required_no_auto_execution": handoff_branch,
        "manual_decision_hold_continues_unresolved": unresolved_branch,
        "dmd_handoff_allowed_as_manual_decision_candidate": handoff_branch,
        "manual_decision_required_without_auto_execution": True,
        "dhr_op06_does_not_materialize_manual_decision": True,
        "dhr_op06_does_not_generate_body_full_packet": True,
        "dhr_op06_does_not_run_actual_local_human_review": True,
        "dhr_op06_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op06_does_not_execute_dmd_or_r52": True,
        "dhr_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "dmd_direct_call_safe_without_adapter": False,
        "dmh_op18_finalizer_fake_generation_allowed": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHR-OP06 branch resolver contract without executing branch targets."""

    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP06")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP06_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP06")
    if data.get("branch_resolution_status_ref") != data.get("dhr_op06_status_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 status alias changed")
    if tuple(data.get("dhr_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 allowed status refs changed")
    if tuple(data.get("resolver_priority_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_BRANCH_RESOLVER_PRIORITY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 resolver priority changed")
    for field, count_field in (
        ("dhr_op06_allowed_status_refs", "dhr_op06_allowed_status_ref_count"),
        ("resolver_priority_refs", "resolver_priority_ref_count"),
        ("branch_reason_refs", "branch_reason_ref_count"),
        ("branch_blocker_refs", "branch_blocker_ref_count"),
        ("op05_dmd_handoff_plan_candidate_blocker_refs", "op05_dmd_handoff_plan_candidate_blocker_ref_count"),
        ("op05_dhr_op05_blocker_refs", "op05_dhr_op05_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP06 {count_field} changed")
    for key in (
        "dhr_op06_ready",
        "branch_resolver_ready",
        "dhr_op06_branch_resolved",
        "dhr_op06_does_not_materialize_manual_decision",
        "dhr_op06_does_not_generate_body_full_packet",
        "dhr_op06_does_not_run_actual_local_human_review",
        "dhr_op06_does_not_create_receipts_rows_or_disposal",
        "dhr_op06_does_not_execute_dmd_or_r52",
        "dhr_op06_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op06_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP06 required true boundary changed: {key}")
    for key in (
        "dmd_direct_call_safe_without_adapter",
        "dmh_op18_finalizer_fake_generation_allowed",
        "dmd_execution_started_here",
        "dmd_auto_execution_allowed",
        "manual_decision_auto_executes_downstream",
        "r52_actual_execution_started_here",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP06 direct execution or promotion flag changed: {key}")
    if data.get("selected_branch_ref") != data.get("branch_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 selected branch alias changed")
    if data.get("branch_ref") not in P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 branch ref is not allowed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP06_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 not-yet steps changed")
    branch_flags = (
        data.get("bodyfree_evidence_boundary_repair_required"),
        data.get("elr_complete_evidence_or_manual_hold_waiting_required"),
        data.get("retry_or_start_actual_local_only_human_review_required"),
        data.get("dmd_handoff_ready_manual_decision_required_no_auto_execution"),
        data.get("manual_decision_hold_continues_unresolved"),
    )
    if branch_flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 must resolve exactly one branch")
    branch_ref = data.get("branch_ref")
    status_ref = data.get("dhr_op06_status_ref")
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 repair status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF or not data.get("branch_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 repair branch changed")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_WAITING_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 wait status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 wait next step changed")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_RETRY_OR_START_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 retry/start status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 retry/start next step changed")
        if data.get("dmd_handoff_allowed_as_manual_decision_candidate") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 retry/start cannot allow DMD handoff candidate")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 handoff status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 handoff next step changed")
        if data.get("dmd_handoff_allowed_as_manual_decision_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 handoff branch must allow manual DMD handoff candidate")
        if data.get("op05_dmd_direct_call_safe_without_adapter") is not False or data.get("op05_dmh_op18_finalizer_fake_generation_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 handoff branch cannot claim direct DMD call or fake finalizer")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP06_STATUS_MANUAL_HOLD_UNRESOLVED_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 unresolved hold status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_KEEP_DOWNSTREAM_MANUAL_DECISION_HOLD_WITHOUT_PROMOTION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 unresolved next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP06 unknown branch ref")
    return True


def _op07_status_from_branch(branch_ref: str) -> str:
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF:
        return P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_REPAIR_REQUIRED_REF
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF:
        return P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_WAITING_REF
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF:
        return P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF:
        return P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_MANUAL_HOLD_UNRESOLVED_REF
    return P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_RETRY_OR_START_REQUIRED_REF


def build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(
    *,
    handoff_or_retry_deterministic_branch_resolver: Mapping[str, Any] | None = None,
    op06_handoff_or_retry_deterministic_branch_resolver: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP07 body-free manual decision material without auto-execution."""

    op06 = handoff_or_retry_deterministic_branch_resolver if handoff_or_retry_deterministic_branch_resolver is not None else op06_handoff_or_retry_deterministic_branch_resolver
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op06.get("review_session_id") if isinstance(op06, Mapping) else None))
    if op06 is None:
        op06 = build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver(review_session_id=session_id)
    try:
        op06_valid = assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract(op06) is True
    except ValueError:
        op06_valid = False
    op06_map = op06 if isinstance(op06, Mapping) else {}
    branch_ref = _clean_ref(op06_map.get("branch_ref"), default=P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF, max_length=260)
    if not op06_valid or branch_ref not in P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS:
        branch_ref = P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF
    status_ref = _op07_status_from_branch(branch_ref)
    repair_required = branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF
    waiting_required = branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF
    retry_required = branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
    handoff_allowed = branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    hold_continues = branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF
    branch_reasons = _dedupe_clean_refs(op06_map.get("branch_reason_refs") or [], max_length=260)
    branch_blockers = _dedupe_clean_refs(op06_map.get("branch_blocker_refs") or [], max_length=260)
    if repair_required and not branch_blockers:
        branch_blockers = ["dhr_op07_branch_resolver_invalid_or_repair_required"]
    recommended_next_step = _clean_ref(op06_map.get("next_required_step"), default=P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF, max_length=260)
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": _clean_ref(op06_map.get("schema_version"), default="op06_schema_missing", max_length=260),
        "op06_material_ref": _clean_ref(op06_map.get("material_id"), default="op06_material_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06_map.get("dhr_op06_status_ref"), default="op06_status_missing", max_length=260),
        "op06_contract_valid": op06_valid,
        "op06_ready": bool(op06_valid and op06_map.get("dhr_op06_ready") is True),
        "op06_branch_ref": _clean_ref(op06_map.get("branch_ref"), default="op06_branch_missing", max_length=260),
        "op06_next_required_step": _clean_ref(op06_map.get("next_required_step"), default="op06_next_required_step_missing", max_length=260),
        "dhr_op07_status_ref": status_ref,
        "dhr_op07_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP07_ALLOWED_STATUS_REFS),
        "dhr_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP07_ALLOWED_STATUS_REFS),
        "dhr_op07_ready": True,
        "manual_decision_materialized": True,
        "manual_decision_materialized_bodyfree": True,
        "manual_decision_required": True,
        "manual_decision_required_without_auto_execution": True,
        "manual_decision_auto_executes_downstream": False,
        "manual_decision_materialization_from_branch_resolver": op06_valid,
        "selected_branch_ref": branch_ref,
        "recommended_next_step_ref": recommended_next_step,
        "next_required_step": recommended_next_step,
        "operator_action_required": True,
        "dmd_handoff_allowed_as_manual_decision_candidate": handoff_allowed,
        "retry_or_start_required": retry_required,
        "repair_required": repair_required,
        "waiting_required": waiting_required,
        "hold_continues": hold_continues,
        "branch_reason_refs": branch_reasons,
        "branch_reason_ref_count": len(branch_reasons),
        "branch_blocker_refs": branch_blockers,
        "branch_blocker_ref_count": len(branch_blockers),
        "auto_executes_dmd": False,
        "auto_executes_r52": False,
        "auto_starts_actual_review": False,
        "auto_starts_p8": False,
        "release_allowed": False,
        "dhr_op07_does_not_generate_body_full_packet": True,
        "dhr_op07_does_not_run_actual_local_human_review": True,
        "dhr_op07_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op07_does_not_execute_dmd_or_r52": True,
        "dhr_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHR-OP07 manual decision materialization contract without auto-execution."""

    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP07")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP07_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP07")
    if tuple(data.get("dhr_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 allowed status refs changed")
    for field, count_field in (
        ("dhr_op07_allowed_status_refs", "dhr_op07_allowed_status_ref_count"),
        ("branch_reason_refs", "branch_reason_ref_count"),
        ("branch_blocker_refs", "branch_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP07 {count_field} changed")
    for key in (
        "dhr_op07_ready",
        "manual_decision_materialized",
        "manual_decision_materialized_bodyfree",
        "manual_decision_required",
        "manual_decision_required_without_auto_execution",
        "operator_action_required",
        "dhr_op07_does_not_generate_body_full_packet",
        "dhr_op07_does_not_run_actual_local_human_review",
        "dhr_op07_does_not_create_receipts_rows_or_disposal",
        "dhr_op07_does_not_execute_dmd_or_r52",
        "dhr_op07_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op07_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP07 required true boundary changed: {key}")
    for key in (
        "manual_decision_auto_executes_downstream",
        "auto_executes_dmd",
        "auto_executes_r52",
        "auto_starts_actual_review",
        "auto_starts_p8",
        "dmd_execution_started_here",
        "dmd_auto_execution_allowed",
        "r52_actual_execution_started_here",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP07 auto execution or promotion flag changed: {key}")
    branch_ref = data.get("selected_branch_ref")
    if branch_ref not in P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 selected branch ref is not allowed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP07_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 not-yet steps changed")
    branch_flags = (
        data.get("repair_required"),
        data.get("waiting_required"),
        data.get("retry_or_start_required"),
        data.get("dmd_handoff_allowed_as_manual_decision_candidate"),
        data.get("hold_continues"),
    )
    if branch_flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 must materialize exactly one branch flag")
    status_ref = data.get("dhr_op07_status_ref")
    next_step = data.get("recommended_next_step_ref")
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_REPAIR_REQUIRED_REF or next_step != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 repair material changed")
        if not data.get("branch_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 repair material must carry blockers")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_WAITING_REF or next_step != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 waiting material changed")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_RETRY_OR_START_REQUIRED_REF or next_step != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 retry/start material changed")
        if data.get("auto_starts_actual_review") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 retry/start branch cannot auto-start actual review")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_REF or next_step != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 DMD handoff material changed")
        if data.get("dmd_handoff_allowed_as_manual_decision_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 DMD handoff branch must expose manual candidate")
        if data.get("auto_executes_dmd") is not False:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 DMD handoff branch cannot execute DMD")
    elif branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF:
        if status_ref != P7_R54_AHR_POST_ELR19_DHR_OP07_STATUS_MANUAL_HOLD_UNRESOLVED_REF or next_step != P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_KEEP_DOWNSTREAM_MANUAL_DECISION_HOLD_WITHOUT_PROMOTION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 unresolved hold material changed")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 unknown branch ref")
    if data.get("next_required_step") != data.get("recommended_next_step_ref"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP07 next step alias changed")
    return True


build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_handoff_or_retry_deterministic_branch_resolver = (
    build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract
)
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op07_manual_decision_materialization = (
    build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op07_manual_decision_materialization_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract
)


# ---------------------------------------------------------------------------
# DHR-OP08 / DHR-OP09: DMD handoff plan candidate and result memo closure.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_ELR19_DHR_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op08_dmd_handoff_plan_candidate_materialization_without_execution.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP09_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr."
    "op09_bodyfree_result_memo_target_tests_regression_closure.bodyfree.v1"
)
P7_R54_AHR_POST_ELR19_DHR_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[:9]
P7_R54_AHR_POST_ELR19_DHR_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_ELR19_DHR_STEP_REFS[9:]
P7_R54_AHR_POST_ELR19_DHR_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_ELR19_DHR_STEP_REFS
P7_R54_AHR_POST_ELR19_DHR_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_MATERIALIZED_BODYFREE_NO_EXECUTION_REF: Final = (
    "DHR_OP08_DMD_HANDOFF_PLAN_MATERIALIZED_BODYFREE_NO_EXECUTION"
)
P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_NOT_MATERIALIZED_BRANCH_NOT_READY_REF: Final = (
    "DHR_OP08_DMD_HANDOFF_PLAN_NOT_MATERIALIZED_BRANCH_NOT_HANDOFF_READY"
)
P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_OP08_DMD_HANDOFF_PLAN_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_MATERIALIZED_BODYFREE_NO_EXECUTION_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_NOT_MATERIALIZED_BRANCH_NOT_READY_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_ELR19_DHR_DMD_HANDOFF_PLAN_MATERIALIZED_BODYFREE_NO_EXECUTION_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_MATERIALIZED_BODYFREE_NO_EXECUTION_REF
)
P7_R54_AHR_POST_ELR19_DHR_DMD_HANDOFF_PLAN_NOT_MATERIALIZED_BRANCH_NOT_READY_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_NOT_MATERIALIZED_BRANCH_NOT_READY_REF
)
P7_R54_AHR_POST_ELR19_DHR_DMD_HANDOFF_PLAN_REPAIR_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF
)

P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF: Final = (
    "DHR_OP09_BODYFREE_RESULT_MEMO_TARGET_TESTS_REGRESSION_CLOSED"
)
P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_INCOMPLETE_OR_UNVERIFIED_REF: Final = (
    "DHR_OP09_RESULT_MEMO_TARGET_TESTS_REGRESSION_INCOMPLETE_OR_UNVERIFIED"
)
P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_REPAIR_REQUIRED_REF: Final = (
    "DHR_OP09_BODYFREE_RESULT_MEMO_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_ELR19_DHR_OP09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_INCOMPLETE_OR_UNVERIFIED_REF,
    P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_ELR19_DHR_OP09_PASS_STATUS_REFS: Final[frozenset[str]] = frozenset(
    {"passed", "passed_bodyfree_count_only", "ok"}
)

P7_R54_AHR_POST_ELR19_DHR_DMD_TARGET_HELPER_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703"
)
P7_R54_AHR_POST_ELR19_DHR_DMD_RECEIPT_SCHEMA_VERSION: Final = (
    dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
)
P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_REASON_REF: Final = (
    "existing_dmd_op01_requires_dmh_op18_finalizer_contract"
)
P7_R54_AHR_POST_ELR19_DHR_DMD_ALTERNATE_POST_ELR19_INTAKE_DECISION_REF: Final = (
    "implementation_time_decision_dmd_alternate_post_elr19_intake_may_be_required"
)
P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP09_REF: Final = P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF
P7_R54_AHR_POST_ELR19_DHR_OP09_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostELR19_DownstreamManualDecision_HandoffOrRetry_DHR_OP00_OP09_Result_20260704.md"
)

P7_R54_AHR_POST_ELR19_DHR_OP09_UNVERIFIED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
    "actual_body_full_packet_generation",
    "actual_local_only_human_review_execution",
    "actual_operation_receipt_real_creation",
    "sanitized_review_result_rows_real_creation",
    "rating_rows_real_creation",
    "question_need_observation_rows_real_creation",
    "disposal_purge_real_execution",
    "dmd_execution",
    "r52_actual_execution",
    "p8_question_design_or_implementation",
    "release_readiness",
)
P7_R54_AHR_POST_ELR19_DHR_OP09_CHANGED_FILE_REFS: Final[dict[str, tuple[str, ...]]] = {
    "modified": (
        "mashos-api/ai/services/ai_inference/"
        "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    ),
    "new": (
        "mashos-api/ai/tests/"
        "test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op08_op09_result_20260704.py",
        "mashos-api/ai/tests/"
        "R54_AHR_PostELR19_DownstreamManualDecision_HandoffOrRetry_DHR_OP00_OP09_Result_20260704.md",
    ),
    "deleted": (),
}

P7_R54_AHR_POST_ELR19_DHR_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_contract_valid", "op07_ready",
    "op07_selected_branch_ref", "op07_recommended_next_step_ref", "op07_dmd_handoff_allowed_as_manual_decision_candidate",
    "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_contract_valid", "op03_receipt_shape_valid",
    "dhr_op08_status_ref", "dmd_handoff_plan_status_ref", "dhr_op08_allowed_status_refs", "dhr_op08_allowed_status_ref_count",
    "dhr_op08_ready", "dhr_op08_ready_for_result_memo_closure", "dhr_op08_reason_refs", "dhr_op08_reason_ref_count",
    "dhr_op08_blocker_refs", "dhr_op08_blocker_ref_count", "selected_branch_ref", "recommended_next_step_ref",
    "next_required_step", "next_dhr_step_ref", "dmd_handoff_plan_materialized", "dmd_handoff_plan_bodyfree",
    "dmd_handoff_ready_manual_decision_required", "dmd_handoff_plan_candidate_allowed_from_op07",
    "dmd_handoff_plan_candidate_allowed_by_safe_receipt", "dmd_target_helper_ref", "dmd_receipt_schema_version",
    "dmd_direct_call_safe_without_adapter", "dmd_direct_call_reason_ref", "dmd_alternate_post_elr19_intake_may_be_required",
    "dmd_alternate_post_elr19_intake_decision_ref", "dmh_op18_finalizer_fake_generation_allowed", "dmd_auto_execution_allowed",
    "dmd_execution_started_here", "manual_operator_must_confirm_dmd_handoff", "manual_decision_required_without_auto_execution",
    "manual_decision_auto_executes_downstream", "actual_operation_evidence_receipt_bodyfree",
    "actual_operation_evidence_receipt_bodyfree_present", "actual_operation_evidence_receipt_bodyfree_key_refs",
    "actual_operation_evidence_receipt_bodyfree_key_ref_count", "receipt_schema_version", "receipt_schema_version_matches_dmd",
    "receipt_source_kind_ref", "receipt_source_kind_valid", "receipt_count_fields_are_24", "receipt_required_true_fields_passed",
    "receipt_body_free", "receipt_forbidden_payload_key_path_refs", "receipt_forbidden_payload_key_path_count",
    "receipt_body_like_value_path_refs", "receipt_body_like_value_path_count", "receipt_promotion_claim_refs", "receipt_promotion_claim_ref_count",
    "actual_source_claim_confirmed_for_downstream_handoff", "dhr_op08_does_not_generate_dmh_op18_finalizer",
    "dhr_op08_does_not_generate_body_full_packet", "dhr_op08_does_not_run_actual_local_human_review",
    "dhr_op08_does_not_create_receipts_rows_or_disposal", "dhr_op08_does_not_execute_dmd_or_r52",
    "dhr_op08_does_not_start_p5_p6_p8_p7_or_release", "dhr_op08_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps",
    "public_contract", "post_elr19_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_ELR19_DHR_OP09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op08_schema_version", "op08_material_ref", "op08_status_ref", "op08_contract_valid", "op08_ready",
    "op08_selected_branch_ref", "op08_dmd_handoff_plan_materialized", "op08_next_required_step",
    "dhr_op09_status_ref", "result_memo_status_ref", "dhr_op09_allowed_status_refs", "dhr_op09_allowed_status_ref_count",
    "result_memo_ref", "result_memo_bodyfree_closed", "selected_branch_ref", "dmd_handoff_plan_materialized",
    "dmd_handoff_plan_bodyfree", "dmd_handoff_ready_manual_decision_required", "dmd_target_helper_ref", "dmd_receipt_schema_version",
    "dmd_execution_started_here", "dmd_auto_execution_allowed", "r52_actual_execution_started_here",
    "target_tests_summary_bodyfree", "target_tests_summary_status_ref", "target_tests_passed_count", "target_tests_failed_count", "target_tests_timed_out",
    "selected_regression_summary_bodyfree", "selected_regression_summary_status_ref", "selected_regression_passed_count", "selected_regression_failed_count", "selected_regression_timed_out",
    "compileall_summary_bodyfree", "compileall_summary_status_ref", "compileall_passed", "compileall_failed", "compileall_timed_out",
    "result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count",
    "result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count", "result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count",
    "actual_local_human_review_execution_verified_here", "actual_rows_created_verified_here", "actual_disposal_purge_execution_verified_here", "actual_body_full_packet_generation_verified_here",
    "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed",
    "unverified_boundary_refs", "unverified_boundary_ref_count", "changed_file_refs", "modified_file_refs", "new_file_refs", "deleted_file_refs",
    "next_required_step", "dhr_op09_does_not_generate_body_full_packet", "dhr_op09_does_not_run_actual_local_human_review",
    "dhr_op09_does_not_create_receipts_rows_or_disposal", "dhr_op09_does_not_execute_dmd_or_r52",
    "dhr_op09_does_not_start_p5_p6_p8_p7_or_release", "dhr_op09_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "manual_decision_auto_executes_downstream",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps",
    "public_contract", "post_elr19_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _dhr_op08_pick_receipt(op03: Mapping[str, Any] | None) -> dict[str, Any]:
    receipt = op03.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree") if isinstance(op03, Mapping) else None
    return {str(key): value for key, value in receipt.items()} if isinstance(receipt, Mapping) else {}


def _dhr_op08_receipt_flags(receipt: Mapping[str, Any], op03: Mapping[str, Any] | None, *, op03_valid: bool) -> dict[str, Any]:
    present = bool(receipt)
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(receipt, path="actual_operation_evidence_receipt_bodyfree"), max_length=280)
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(receipt, path="actual_operation_evidence_receipt_bodyfree"), max_length=280)
    promotion = _dedupe_clean_refs(_promotion_claim_refs(receipt), max_length=240)
    source_kind = _clean_ref(receipt.get("source_kind_ref") if present else "", default="actual_operation_evidence_receipt_source_kind_missing", max_length=180)
    schema_version = _clean_ref(receipt.get("schema_version") if present else "", default="actual_operation_evidence_receipt_schema_missing", max_length=260)
    count_fields_are_24 = bool(isinstance(op03, Mapping) and op03.get("receipt_count_fields_are_24") is True)
    true_fields_passed = bool(isinstance(op03, Mapping) and op03.get("receipt_required_true_fields_passed") is True)
    body_free = bool(receipt.get("body_free") is True) if present else False
    return {
        "receipt_schema_version": schema_version,
        "receipt_schema_version_matches_dmd": bool(schema_version == P7_R54_AHR_POST_ELR19_DHR_DMD_RECEIPT_SCHEMA_VERSION),
        "receipt_source_kind_ref": source_kind,
        "receipt_source_kind_valid": bool(source_kind == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF),
        "receipt_count_fields_are_24": count_fields_are_24,
        "receipt_required_true_fields_passed": true_fields_passed,
        "receipt_body_free": body_free,
        "receipt_forbidden_payload_key_path_refs": forbidden,
        "receipt_forbidden_payload_key_path_count": len(forbidden),
        "receipt_body_like_value_path_refs": body_like,
        "receipt_body_like_value_path_count": len(body_like),
        "receipt_promotion_claim_refs": promotion,
        "receipt_promotion_claim_ref_count": len(promotion),
        "receipt_safe_for_handoff_plan": bool(
            op03_valid
            and present
            and schema_version == P7_R54_AHR_POST_ELR19_DHR_DMD_RECEIPT_SCHEMA_VERSION
            and source_kind == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
            and count_fields_are_24
            and true_fields_passed
            and body_free
            and not forbidden
            and not body_like
            and not promotion
        ),
    }


def _dhr_branch_next_required_step(branch_ref: str) -> str:
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF:
        return P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_MANUAL_DECISION_EXECUTE_OR_DECLINE_DMD_HANDOFF_WITHOUT_AUTO_PROMOTION_REF
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF:
        return P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF:
        return P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    if branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF:
        return P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_MATERIAL_REF
    return P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_KEEP_DOWNSTREAM_MANUAL_DECISION_HOLD_WITHOUT_PROMOTION_REF


def build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(
    *,
    manual_decision_materialization: Mapping[str, Any] | None = None,
    op07_manual_decision_materialization: Mapping[str, Any] | None = None,
    elr_op17_dmd_compatible_receipt_candidate_extraction: Mapping[str, Any] | None = None,
    op03_elr_op17_dmd_compatible_receipt_candidate_extraction: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP08 DMD handoff plan candidate without DMD execution."""

    op07 = manual_decision_materialization if manual_decision_materialization is not None else op07_manual_decision_materialization
    op03 = elr_op17_dmd_compatible_receipt_candidate_extraction if elr_op17_dmd_compatible_receipt_candidate_extraction is not None else op03_elr_op17_dmd_compatible_receipt_candidate_extraction
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op07.get("review_session_id") if isinstance(op07, Mapping) else None))
    if op07 is None:
        op07 = build_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization(review_session_id=session_id)
    try:
        op07_valid = assert_p7_r54_ahr_post_elr19_dhr_op07_manual_decision_materialization_contract(op07) is True
    except ValueError:
        op07_valid = False
    try:
        op03_valid = assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(op03) is True if isinstance(op03, Mapping) else False
    except ValueError:
        op03_valid = False
    op07_map = op07 if isinstance(op07, Mapping) else {}
    op03_map = op03 if isinstance(op03, Mapping) else {}
    branch_ref = _clean_ref(op07_map.get("selected_branch_ref"), default="op07_selected_branch_missing", max_length=260)
    handoff_branch = branch_ref == P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
    receipt_candidate = _dhr_op08_pick_receipt(op03_map)
    receipt_flags = _dhr_op08_receipt_flags(receipt_candidate, op03_map, op03_valid=op03_valid)
    safe_receipt = bool(receipt_flags["receipt_safe_for_handoff_plan"])
    blockers: list[str] = []
    reasons: list[str] = []
    if not op07_valid:
        blockers.append("dhr_op08_op07_manual_decision_material_invalid_or_missing")
    if handoff_branch and not safe_receipt:
        blockers.append("dhr_op08_handoff_ready_branch_missing_or_invalid_safe_bodyfree_receipt_candidate")
    if blockers:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF
        plan_materialized = False
        plan_receipt: dict[str, Any] = {}
    elif handoff_branch:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_MATERIALIZED_BODYFREE_NO_EXECUTION_REF
        plan_materialized = True
        plan_receipt = receipt_candidate
        reasons.append("dhr_op08_handoff_ready_branch_with_safe_bodyfree_receipt_candidate")
    else:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_NOT_MATERIALIZED_BRANCH_NOT_READY_REF
        plan_materialized = False
        plan_receipt = {}
        reasons.append("dhr_op08_selected_branch_is_not_dmd_handoff_ready")
    reason_refs = _dedupe_clean_refs(reasons, max_length=260)
    blocker_refs = _dedupe_clean_refs(blockers, max_length=260)
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_schema_version": _clean_ref(op07_map.get("schema_version"), default="op07_schema_missing", max_length=260),
        "op07_material_ref": _clean_ref(op07_map.get("material_id"), default="op07_material_missing", max_length=260),
        "op07_status_ref": _clean_ref(op07_map.get("dhr_op07_status_ref"), default="op07_status_missing", max_length=260),
        "op07_contract_valid": op07_valid,
        "op07_ready": bool(op07_valid and op07_map.get("dhr_op07_ready") is True),
        "op07_selected_branch_ref": branch_ref,
        "op07_recommended_next_step_ref": _clean_ref(op07_map.get("recommended_next_step_ref"), default="op07_recommended_next_step_missing", max_length=260),
        "op07_dmd_handoff_allowed_as_manual_decision_candidate": bool(op07_map.get("dmd_handoff_allowed_as_manual_decision_candidate") is True),
        "op03_schema_version": _clean_ref(op03_map.get("schema_version"), default="op03_schema_missing", max_length=260),
        "op03_material_ref": _clean_ref(op03_map.get("material_id"), default="op03_material_missing", max_length=260),
        "op03_status_ref": _clean_ref(op03_map.get("dhr_op03_status_ref"), default="op03_status_missing", max_length=260),
        "op03_contract_valid": op03_valid,
        "op03_receipt_shape_valid": bool(op03_map.get("receipt_shape_valid") is True),
        "dhr_op08_status_ref": status_ref,
        "dmd_handoff_plan_status_ref": status_ref,
        "dhr_op08_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP08_ALLOWED_STATUS_REFS),
        "dhr_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP08_ALLOWED_STATUS_REFS),
        "dhr_op08_ready": bool(status_ref != P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF),
        "dhr_op08_ready_for_result_memo_closure": bool(status_ref != P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF),
        "dhr_op08_reason_refs": reason_refs,
        "dhr_op08_reason_ref_count": len(reason_refs),
        "dhr_op08_blocker_refs": blocker_refs,
        "dhr_op08_blocker_ref_count": len(blocker_refs),
        "selected_branch_ref": branch_ref,
        "recommended_next_step_ref": _dhr_branch_next_required_step(branch_ref),
        "next_required_step": P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_DHR_OP09_REF,
        "next_dhr_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF,
        "dmd_handoff_plan_materialized": plan_materialized,
        "dmd_handoff_plan_bodyfree": True,
        "dmd_handoff_ready_manual_decision_required": plan_materialized,
        "dmd_handoff_plan_candidate_allowed_from_op07": bool(handoff_branch and op07_map.get("dmd_handoff_allowed_as_manual_decision_candidate") is True),
        "dmd_handoff_plan_candidate_allowed_by_safe_receipt": safe_receipt,
        "dmd_target_helper_ref": P7_R54_AHR_POST_ELR19_DHR_DMD_TARGET_HELPER_REF,
        "dmd_receipt_schema_version": P7_R54_AHR_POST_ELR19_DHR_DMD_RECEIPT_SCHEMA_VERSION,
        "dmd_direct_call_safe_without_adapter": False,
        "dmd_direct_call_reason_ref": P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_REASON_REF,
        "dmd_alternate_post_elr19_intake_may_be_required": plan_materialized,
        "dmd_alternate_post_elr19_intake_decision_ref": P7_R54_AHR_POST_ELR19_DHR_DMD_ALTERNATE_POST_ELR19_INTAKE_DECISION_REF,
        "dmh_op18_finalizer_fake_generation_allowed": False,
        "dmd_auto_execution_allowed": False,
        "dmd_execution_started_here": False,
        "manual_operator_must_confirm_dmd_handoff": True,
        "manual_decision_required_without_auto_execution": True,
        "manual_decision_auto_executes_downstream": False,
        "actual_operation_evidence_receipt_bodyfree": plan_receipt,
        "actual_operation_evidence_receipt_bodyfree_present": bool(plan_receipt),
        "actual_operation_evidence_receipt_bodyfree_key_refs": list(plan_receipt.keys()),
        "actual_operation_evidence_receipt_bodyfree_key_ref_count": len(plan_receipt),
        "receipt_schema_version": receipt_flags["receipt_schema_version"],
        "receipt_schema_version_matches_dmd": receipt_flags["receipt_schema_version_matches_dmd"],
        "receipt_source_kind_ref": receipt_flags["receipt_source_kind_ref"],
        "receipt_source_kind_valid": receipt_flags["receipt_source_kind_valid"],
        "receipt_count_fields_are_24": receipt_flags["receipt_count_fields_are_24"],
        "receipt_required_true_fields_passed": receipt_flags["receipt_required_true_fields_passed"],
        "receipt_body_free": receipt_flags["receipt_body_free"],
        "receipt_forbidden_payload_key_path_refs": receipt_flags["receipt_forbidden_payload_key_path_refs"],
        "receipt_forbidden_payload_key_path_count": receipt_flags["receipt_forbidden_payload_key_path_count"],
        "receipt_body_like_value_path_refs": receipt_flags["receipt_body_like_value_path_refs"],
        "receipt_body_like_value_path_count": receipt_flags["receipt_body_like_value_path_count"],
        "receipt_promotion_claim_refs": receipt_flags["receipt_promotion_claim_refs"],
        "receipt_promotion_claim_ref_count": receipt_flags["receipt_promotion_claim_ref_count"],
        "actual_source_claim_confirmed_for_downstream_handoff": plan_materialized,
        "dhr_op08_does_not_generate_dmh_op18_finalizer": True,
        "dhr_op08_does_not_generate_body_full_packet": True,
        "dhr_op08_does_not_run_actual_local_human_review": True,
        "dhr_op08_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op08_does_not_execute_dmd_or_r52": True,
        "dhr_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHR-OP08 does not execute DMD while materializing only safe candidates."""

    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP08")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP08_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP08_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP08")
    if set(data) != set(P7_R54_AHR_POST_ELR19_DHR_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 field set changed")
    if tuple(data.get("dhr_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 allowed status refs changed")
    for field, count_field in (
        ("dhr_op08_allowed_status_refs", "dhr_op08_allowed_status_ref_count"),
        ("dhr_op08_reason_refs", "dhr_op08_reason_ref_count"),
        ("dhr_op08_blocker_refs", "dhr_op08_blocker_ref_count"),
        ("actual_operation_evidence_receipt_bodyfree_key_refs", "actual_operation_evidence_receipt_bodyfree_key_ref_count"),
        ("receipt_forbidden_payload_key_path_refs", "receipt_forbidden_payload_key_path_count"),
        ("receipt_body_like_value_path_refs", "receipt_body_like_value_path_count"),
        ("receipt_promotion_claim_refs", "receipt_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP08 {count_field} changed")
    for key in (
        "dmd_direct_call_safe_without_adapter", "dmh_op18_finalizer_fake_generation_allowed", "dmd_auto_execution_allowed",
        "dmd_execution_started_here", "manual_decision_auto_executes_downstream", "r52_actual_execution_started_here",
        "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started",
        "p7_complete", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP08 execution/promotion flag changed: {key}")
    for key in (
        "dmd_handoff_plan_bodyfree", "manual_operator_must_confirm_dmd_handoff", "manual_decision_required_without_auto_execution",
        "dhr_op08_does_not_generate_dmh_op18_finalizer", "dhr_op08_does_not_generate_body_full_packet",
        "dhr_op08_does_not_run_actual_local_human_review", "dhr_op08_does_not_create_receipts_rows_or_disposal",
        "dhr_op08_does_not_execute_dmd_or_r52", "dhr_op08_does_not_start_p5_p6_p8_p7_or_release",
        "dhr_op08_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP08 required true boundary changed: {key}")
    if data.get("dmd_target_helper_ref") != P7_R54_AHR_POST_ELR19_DHR_DMD_TARGET_HELPER_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 DMD target helper changed")
    if data.get("dmd_receipt_schema_version") != P7_R54_AHR_POST_ELR19_DHR_DMD_RECEIPT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 DMD receipt schema changed")
    if data.get("dmd_direct_call_reason_ref") != P7_R54_AHR_POST_ELR19_DHR_DMD_DIRECT_CALL_REASON_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 direct call reason changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS or tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS or tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP08_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 implemented/not-yet steps changed")
    status = data.get("dhr_op08_status_ref")
    branch_ref = data.get("selected_branch_ref")
    if branch_ref not in P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 selected branch ref is not allowed")
    if status == P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_MATERIALIZED_BODYFREE_NO_EXECUTION_REF:
        if branch_ref != P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 materialized plan requires handoff-ready branch")
        for key in ("dmd_handoff_plan_materialized", "dmd_handoff_ready_manual_decision_required", "actual_operation_evidence_receipt_bodyfree_present", "dmd_handoff_plan_candidate_allowed_by_safe_receipt", "actual_source_claim_confirmed_for_downstream_handoff", "dmd_alternate_post_elr19_intake_may_be_required"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP08 materialized true flag changed: {key}")
        if not isinstance(data.get("actual_operation_evidence_receipt_bodyfree"), Mapping) or not data.get("actual_operation_evidence_receipt_bodyfree"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 materialized plan needs body-free receipt")
        if data.get("dhr_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 materialized plan cannot carry blockers")
        if data.get("receipt_forbidden_payload_key_path_refs") or data.get("receipt_body_like_value_path_refs") or data.get("receipt_promotion_claim_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 materialized receipt must stay body-free and non-promotional")
    elif status == P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_NOT_MATERIALIZED_BRANCH_NOT_READY_REF:
        if data.get("dmd_handoff_plan_materialized") is not False or data.get("actual_operation_evidence_receipt_bodyfree") != {}:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 non-handoff branch must not materialize a plan")
        if not data.get("dhr_op08_reason_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 non-handoff branch needs body-free reason")
    elif status == P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF:
        if data.get("dhr_op08_ready") is not False or not data.get("dhr_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 repair branch must be blocked")
        if data.get("dmd_handoff_plan_materialized") is not False or data.get("actual_operation_evidence_receipt_bodyfree") != {}:
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 repair branch cannot materialize a plan")
    else:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 status ref is not allowed")
    if data.get("next_required_step") != P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF or data.get("next_dhr_step_ref") != P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP08 next step changed")
    return True


def _dhr_op09_summary(value: Mapping[str, Any] | None, *, default_status_ref: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"status_ref": default_status_ref, "passed_count": 0, "failed_count": 0, "timed_out": False, "body_free": True}
    passed = value.get("passed_count")
    failed = value.get("failed_count")
    return {
        "status_ref": _clean_ref(value.get("status_ref"), default=default_status_ref, max_length=220),
        "passed_count": max(0, int(passed or 0)) if not isinstance(passed, bool) else 0,
        "failed_count": max(0, int(failed or 0)) if not isinstance(failed, bool) else 0,
        "timed_out": bool(value.get("timed_out") is True),
        "body_free": True,
    }


def _dhr_op09_summary_passed(summary: Mapping[str, Any]) -> bool:
    return bool(
        summary.get("status_ref") in P7_R54_AHR_POST_ELR19_DHR_OP09_PASS_STATUS_REFS
        and int(summary.get("passed_count") or 0) > 0
        and int(summary.get("failed_count") or 0) == 0
        and summary.get("timed_out") is False
        and summary.get("body_free") is True
    )


def _dhr_op09_next_step(branch_ref: str, op08_status_ref: str) -> str:
    if op08_status_ref == P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF:
        return P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_STOP_AND_REPAIR_POST_ELR19_BODYFREE_EVIDENCE_BOUNDARY_REF
    return _dhr_branch_next_required_step(branch_ref)


def build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure(
    *,
    dmd_handoff_plan_candidate_materialization: Mapping[str, Any] | None = None,
    op08_dmd_handoff_plan_candidate_materialization: Mapping[str, Any] | None = None,
    target_tests_summary_bodyfree: Mapping[str, Any] | None = None,
    selected_regression_summary_bodyfree: Mapping[str, Any] | None = None,
    compileall_summary_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DHR-OP09 body-free result memo closure with count-only verification summaries."""

    op08 = dmd_handoff_plan_candidate_materialization if dmd_handoff_plan_candidate_materialization is not None else op08_dmd_handoff_plan_candidate_materialization
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op08.get("review_session_id") if isinstance(op08, Mapping) else None))
    if op08 is None:
        op08 = build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution(review_session_id=session_id)
    try:
        op08_valid = assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract(op08) is True
    except ValueError:
        op08_valid = False
    op08_map = op08 if isinstance(op08, Mapping) else {}
    target_summary = _dhr_op09_summary(target_tests_summary_bodyfree, default_status_ref="target_tests_unverified")
    regression_summary = _dhr_op09_summary(selected_regression_summary_bodyfree, default_status_ref="selected_regression_unverified")
    compile_summary = _dhr_op09_summary(compileall_summary_bodyfree, default_status_ref="compileall_unverified")
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op08_map, path="dhr_op08_material"), max_length=280)
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(op08_map, path="dhr_op08_material"), max_length=280)
    promotion = _dedupe_clean_refs([f"dhr_op08_material.{ref}" for ref in _promotion_claim_refs(op08_map)], max_length=280)
    target_passed = _dhr_op09_summary_passed(target_summary)
    regression_passed = _dhr_op09_summary_passed(regression_summary)
    compile_passed = _dhr_op09_summary_passed(compile_summary)
    if forbidden or body_like or promotion or op08_map.get("dhr_op08_status_ref") == P7_R54_AHR_POST_ELR19_DHR_OP08_STATUS_REPAIR_REQUIRED_REF:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_REPAIR_REQUIRED_REF
    elif op08_valid and target_passed and regression_passed and compile_passed:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF
    else:
        status_ref = P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
    branch_ref = _clean_ref(op08_map.get("selected_branch_ref"), default=P7_R54_AHR_POST_ELR19_DHR_BRANCH_BODYFREE_EVIDENCE_REPAIR_REQUIRED_REF, max_length=260)
    changed_file_refs = P7_R54_AHR_POST_ELR19_DHR_OP09_CHANGED_FILE_REFS
    return {
        "schema_version": P7_R54_AHR_POST_ELR19_DHR_OP09_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "step": P7_R54_AHR_POST_ELR19_DHR_STEP,
        "scope": P7_R54_AHR_POST_ELR19_DHR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_ELR19_DHR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF,
        "current_phase": P7_R54_AHR_POST_ELR19_DHR_PHASE,
        "material_id": "p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_schema_version": _clean_ref(op08_map.get("schema_version"), default="op08_schema_missing", max_length=260),
        "op08_material_ref": _clean_ref(op08_map.get("material_id"), default="op08_material_missing", max_length=260),
        "op08_status_ref": _clean_ref(op08_map.get("dhr_op08_status_ref"), default="op08_status_missing", max_length=260),
        "op08_contract_valid": op08_valid,
        "op08_ready": bool(op08_map.get("dhr_op08_ready") is True),
        "op08_selected_branch_ref": branch_ref,
        "op08_dmd_handoff_plan_materialized": bool(op08_map.get("dmd_handoff_plan_materialized") is True),
        "op08_next_required_step": _clean_ref(op08_map.get("next_required_step"), default=P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF, max_length=260),
        "dhr_op09_status_ref": status_ref,
        "result_memo_status_ref": status_ref,
        "dhr_op09_allowed_status_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP09_ALLOWED_STATUS_REFS),
        "dhr_op09_allowed_status_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP09_ALLOWED_STATUS_REFS),
        "result_memo_ref": P7_R54_AHR_POST_ELR19_DHR_OP09_RESULT_MEMO_REF,
        "result_memo_bodyfree_closed": True,
        "selected_branch_ref": branch_ref,
        "dmd_handoff_plan_materialized": bool(op08_map.get("dmd_handoff_plan_materialized") is True),
        "dmd_handoff_plan_bodyfree": bool(op08_map.get("dmd_handoff_plan_bodyfree") is True),
        "dmd_handoff_ready_manual_decision_required": bool(op08_map.get("dmd_handoff_ready_manual_decision_required") is True),
        "dmd_target_helper_ref": P7_R54_AHR_POST_ELR19_DHR_DMD_TARGET_HELPER_REF,
        "dmd_receipt_schema_version": P7_R54_AHR_POST_ELR19_DHR_DMD_RECEIPT_SCHEMA_VERSION,
        "dmd_execution_started_here": False,
        "dmd_auto_execution_allowed": False,
        "r52_actual_execution_started_here": False,
        "target_tests_summary_bodyfree": target_summary,
        "target_tests_summary_status_ref": target_summary["status_ref"],
        "target_tests_passed_count": target_summary["passed_count"],
        "target_tests_failed_count": target_summary["failed_count"],
        "target_tests_timed_out": target_summary["timed_out"],
        "selected_regression_summary_bodyfree": regression_summary,
        "selected_regression_summary_status_ref": regression_summary["status_ref"],
        "selected_regression_passed_count": regression_summary["passed_count"],
        "selected_regression_failed_count": regression_summary["failed_count"],
        "selected_regression_timed_out": regression_summary["timed_out"],
        "compileall_summary_bodyfree": compile_summary,
        "compileall_summary_status_ref": compile_summary["status_ref"],
        "compileall_passed": compile_passed,
        "compileall_failed": bool(compile_summary["failed_count"] > 0),
        "compileall_timed_out": compile_summary["timed_out"],
        "result_memo_forbidden_payload_key_path_refs": forbidden,
        "result_memo_forbidden_payload_key_path_count": len(forbidden),
        "result_memo_body_like_value_path_refs": body_like,
        "result_memo_body_like_value_path_count": len(body_like),
        "result_memo_promotion_claim_refs": promotion,
        "result_memo_promotion_claim_ref_count": len(promotion),
        "actual_local_human_review_execution_verified_here": False,
        "actual_rows_created_verified_here": False,
        "actual_disposal_purge_execution_verified_here": False,
        "actual_body_full_packet_generation_verified_here": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "p7_complete": False,
        "release_allowed": False,
        "unverified_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_OP09_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_OP09_UNVERIFIED_BOUNDARY_REFS),
        "changed_file_refs": changed_file_refs,
        "modified_file_refs": list(changed_file_refs["modified"]),
        "new_file_refs": list(changed_file_refs["new"]),
        "deleted_file_refs": list(changed_file_refs["deleted"]),
        "next_required_step": _dhr_op09_next_step(branch_ref, _clean_ref(op08_map.get("dhr_op08_status_ref"), default="op08_status_missing", max_length=260)),
        "dhr_op09_does_not_generate_body_full_packet": True,
        "dhr_op09_does_not_run_actual_local_human_review": True,
        "dhr_op09_does_not_create_receipts_rows_or_disposal": True,
        "dhr_op09_does_not_execute_dmd_or_r52": True,
        "dhr_op09_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op09_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "manual_decision_auto_executes_downstream": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_ELR19_DHR_OP09_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_elr19_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHR-OP09 body-free result memo closure contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_ELR19_DHR_OP09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostELR19-DHR-OP09")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_ELR19_DHR_OP09_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_ELR19_DHR_OP09_STEP_REF, source="P7-R54-AHR-PostELR19-DHR-OP09")
    if set(data) != set(P7_R54_AHR_POST_ELR19_DHR_OP09_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 field set changed")
    if tuple(data.get("dhr_op09_allowed_status_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP09_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 allowed status refs changed")
    for field, count_field in (
        ("dhr_op09_allowed_status_refs", "dhr_op09_allowed_status_ref_count"),
        ("result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count"),
        ("result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count"),
        ("result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count"),
        ("unverified_boundary_refs", "unverified_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP09 {count_field} changed")
    for key in (
        "result_memo_bodyfree_closed", "dhr_op09_does_not_generate_body_full_packet", "dhr_op09_does_not_run_actual_local_human_review",
        "dhr_op09_does_not_create_receipts_rows_or_disposal", "dhr_op09_does_not_execute_dmd_or_r52",
        "dhr_op09_does_not_start_p5_p6_p8_p7_or_release", "dhr_op09_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP09 required true boundary changed: {key}")
    for key in (
        "actual_local_human_review_execution_verified_here", "actual_rows_created_verified_here", "actual_disposal_purge_execution_verified_here",
        "actual_body_full_packet_generation_verified_here", "dmd_execution_started_here", "dmd_auto_execution_allowed",
        "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed",
        "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed",
        "manual_decision_auto_executes_downstream",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostELR19-DHR-OP09 execution/verification/promotion flag changed: {key}")
    if data.get("result_memo_forbidden_payload_key_path_refs") or data.get("result_memo_body_like_value_path_refs") or data.get("result_memo_promotion_claim_refs"):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 result memo must stay body-free and non-promotional")
    if tuple(data.get("unverified_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_OP09_UNVERIFIED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 unverified boundary refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS or tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS or tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_ELR19_DHR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_ELR19_DHR_OP09_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != []:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 implemented/not-yet steps changed")
    if data.get("changed_file_refs") != P7_R54_AHR_POST_ELR19_DHR_OP09_CHANGED_FILE_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 changed-file refs changed")
    branch_ref = data.get("selected_branch_ref")
    if branch_ref not in P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 selected branch ref is not allowed")
    if data.get("next_required_step") != _dhr_op09_next_step(branch_ref, data.get("op08_status_ref")):
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 branch-dependent next step changed")
    if data.get("dmd_handoff_plan_materialized") is True and branch_ref != P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF:
        raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 plan materialized outside handoff branch")
    if data.get("result_memo_status_ref") == P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF:
        if not (_dhr_op09_summary_passed(data.get("target_tests_summary_bodyfree") or {}) and _dhr_op09_summary_passed(data.get("selected_regression_summary_bodyfree") or {}) and data.get("compileall_passed") is True):
            raise ValueError("P7-R54-AHR-PostELR19-DHR-OP09 closed result memo requires passing count-only summaries")
    return True


build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution = (
    build_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op08_dmd_handoff_plan_candidate_materialization_without_execution_contract
)
build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op09_bodyfree_result_memo_target_tests_regression_closure = (
    build_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure
)
assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract = (
    assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract
)
