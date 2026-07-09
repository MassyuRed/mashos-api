# -*- coding: utf-8 -*-
"""Post-MRB08 / DHR-OP04 result manual decision boundary helpers.

RDB is intentionally a thin, body-free, backend-internal boundary after the
already-closed MRB-OP08 result memo.  This implementation currently covers
RDB-OP00 through RDB-OP08.

* RDB-OP00 refreezes scope / no-touch / no-promotion after MRB-OP08.  It does
  not intake the MRB-OP08 result memo yet and never recalls DHR-OP04 or calls
  DHR-OP05.
* RDB-OP01 intakes the MRB-OP08 body-free result memo closure, verifies the
  existing MRB-OP08 contract, records only safe refs, and stops at material
  readiness for RDB-OP02.
* RDB-OP02 checks MRB selected branch / DHR-OP04 status consistency and stops before materializing branch-specific manual decision material.
* RDB-OP03 resolves exactly one manual decision lane and stops before OP04 materialization.
* RDB-OP04 materializes branch-specific manual decision material without executing downstream work.
* RDB-OP05 wraps the selected next-stage candidate in a body-free envelope and still never calls DHR-OP05, DHR-OP06, DMD, R52, P8, or release.
* RDB-OP06 guards OP00-OP05 material for body-free / no-touch / no-promotion / no-auto-execution before OP07.
* RDB-OP07 records selected regression and compileall validation plan refs without executing tests or claiming full backend/RN green.
* RDB-OP08 closes the body-free result manual decision memo, records the selected next-stage candidate without execution, and still does not claim DHR-OP05/P8/release permission.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


P7_R54_AHR_POST_MRB08_RDB_PHASE: Final = "P7"
P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_MRB08_RDB_STEP: Final = (
    "R54-AHR-PostMRB08_DHROP04ResultManualDecision_20260705"
)
P7_R54_AHR_POST_MRB08_RDB_SCOPE: Final = (
    "p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_boundary"
)
P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND: Final = (
    "r54_ahr_post_mrb08_dhr_op04_result_manual_decision_bodyfree_boundary"
)
P7_R54_AHR_POST_MRB08_RDB_DEFAULT_REVIEW_SESSION_ID: Final = (
    mrb.P7_R54_AHR_POST_DRI_MRB_DEFAULT_REVIEW_SESSION_ID
)

P7_R54_AHR_POST_MRB08_RDB_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op00_scope_no_touch_no_promotion_refreeze_after_mrb08.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op01_mrb08_result_memo_closure_intake.bodyfree.v1"
)

P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF: Final = (
    "RDB-OP00_scope_no_touch_no_promotion_refreeze_after_MRB_OP08"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF: Final = (
    "RDB-OP01_MRB_OP08_result_memo_closure_intake"
)
P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF: Final = (
    "RDB-OP02_MRB_selected_branch_DHR_OP04_result_status_consistency_check"
)
P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF: Final = (
    "RDB-OP03_DHR_OP04_result_manual_decision_lane_resolver"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF: Final = (
    "RDB-OP04_branch_specific_manual_decision_materialization"
)
P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF: Final = (
    "RDB-OP05_next_stage_candidate_envelope_without_execution"
)
P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF: Final = (
    "RDB-OP06_bodyfree_no_touch_no_promotion_guard"
)
P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF: Final = (
    "RDB-OP07_selected_regression_compileall_validation_plan"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF: Final = (
    "RDB-OP08_bodyfree_result_manual_decision_memo_closure"
)
P7_R54_AHR_POST_MRB08_RDB_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF,
)
P7_R54_AHR_POST_MRB08_RDB_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF,
)
P7_R54_AHR_POST_MRB08_RDB_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[1:]
)
P7_R54_AHR_POST_MRB08_RDB_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:2]
)
P7_R54_AHR_POST_MRB08_RDB_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[2:]
)

P7_R54_AHR_POST_MRB08_RDB_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-MRB08 DHR-OP04 Result Manual Decision Boundary"
)
P7_R54_AHR_POST_MRB08_RDB_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-MRB08 DHR-OP04 Result Manual Decision Boundary"
)
P7_R54_AHR_POST_MRB08_RDB_BOUNDARY_PREFIX_REF: Final = "RDB"
P7_R54_AHR_POST_MRB08_RDB_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "Result Decision Boundary"
)
P7_R54_AHR_POST_MRB08_RDB_EXPECTED_FROM_MRB08_REF: Final = (
    "MRB-OP08 body-free result memo closure is DHR-OP04 result evidence only; "
    "it is not DHR-OP05/P8/release permission"
)
P7_R54_AHR_POST_MRB08_RDB_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_rdb_op01_mrb_op08_result_memo_closure_intake_without_dhr_op05_call"
)

P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_FOR_MRB08_CLOSURE_REF: Final = (
    "wait_for_mrb08_closure_or_validation_refs_before_result_manual_decision"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_MRB08_INTAKE_REF: Final = (
    "repair_dhr_op04_result_or_mrb08_boundary_without_downstream_promotion"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_MRB08_INTAKE_REF: Final = (
    "blocked_post_mrb08_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_REF: Final = (
    "manual_hold_unresolved_post_mrb08_without_promotion"
)

P7_R54_AHR_POST_MRB08_RDB_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(290).zip",
    "implemented_docs": "EmlisAIの実装済み資料(98).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(17).zip",
    "cocolon_app": "Cocolon(271).zip",
    "backend": "mashos-api(184).zip",
}
P7_R54_AHR_POST_MRB08_RDB_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/07_latest_snapshot_diff.md",
    "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/14_cocolon_joint_development_and_karen_thought_boundary.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/15_trust_based_joint_development_boundary_2026_06_05.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostMRB08_DHROP04ResultManualDecision_PreDesignMemo_20260705.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostMRB08_DHROP04ResultManualDecision_DetailedDesign_ImplementationOrder_20260705.md",
    "EmlisAIの実装済み資料/Cocolon_EmlisAI_P7_R54AHR_PostDRI_DHR_OP04ManualReintake_DetailedDesign_ImplementationOrder_20260705.md",
)
P7_R54_AHR_POST_MRB08_RDB_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "DHR-OP04 recall",
    "DHR-OP05 call",
    "DHR-OP06 call",
    "DHR-OP07 materialization",
    "DMD execution",
    "R52 actual execution",
    "actual body-full packet generation",
    "actual local-only human review execution",
    "actual operation receipt creation",
    "actual rows creation",
    "actual disposal / purge execution",
    "P5 finalization",
    "P6 start",
    "P8 start",
    "P8 question design",
    "P8 question implementation",
    "P7 completion",
    "release decision",
    "API / DB / RN / runtime / response key change",
)
P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "MRB-OP08 closure is only body-free result memo closure",
    "MRB-OP08 closure is not DHR-OP05 permission",
    "DHR-OP04 confirmed body-free is only a later manual handoff candidate source",
    "DHR-OP04 not_confirmed/waiting/invalid must not be substituted by P8 question design",
    "RDB-OP01 reads MRB-OP08 refs only and does not classify branch/status consistency yet",
    "RDB-OP01 does not call DHR-OP05 or later",
    "RDB-OP01 does not start P8 question design",
)
P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "mrb_op08_promoted_to_dhr_op05",
    "dhr_op04_recalled_here",
    "dhr_op05_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_mrb_op08_to_dhr_op05_promotion",
    "no_dhr_op04_recall",
    "no_dhr_op05_call",
    "no_dhr_op06_call",
    "no_dmd_execution",
    "no_r52_actual_execution",
    "no_p5_finalization",
    "no_p6_start",
    "no_p8_start",
    "no_p8_question_design_or_implementation",
    "no_p7_complete",
    "no_release_allowed",
)
P7_R54_AHR_POST_MRB08_RDB_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_generation_changed",
    "runtime_prompt_changed",
    "p8_question_surface_changed",
    "question_schema_changed",
    "question_trigger_changed",
    "question_answer_storage_changed",
)
P7_R54_AHR_POST_MRB08_RDB_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "input_body_included",
    "comment_text_body_included",
    "returned_surface_body_included",
    "reviewer_free_text_included",
    "reviewer_note_body_included",
    "result_memo_body_included",
    "question_text_included",
    "draft_question_text_included",
    "answer_text_included",
    "body_full_packet_body_included",
    "private_user_dictionary_text_included",
    "local_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_POST_MRB08_RDB_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "input_body",
    "comment_text",
    "comment_text_body",
    "returned_surface_body",
    "body_full_packet",
    "body_full_packet_body",
    "reviewer_free_text",
    "reviewer_note_body",
    "question_text",
    "draft_question_text",
    "answer_text",
    "private_user_dictionary_text",
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
)
P7_R54_AHR_POST_MRB08_RDB_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "mrb_op08_promoted_to_dhr_op05",
    "manual_decision_auto_executes_downstream",
    "dhr_op04_recalled_here",
    "dhr_op05_called_here",
    "dhr_op05_auto_call_allowed",
    "dhr_op06_called_here",
    "dhr_op06_auto_call_allowed",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
    "r52_actual_execution_started_here",
    "r52_actual_execution_confirmed",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_spec_created",
    "p8_question_design_started_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "mrb_op08_promoted_to_dhr_op05",
    "dhr_op04_recalled_here",
    "dhr_op05_called_here",
    "dhr_op05_auto_call_allowed",
    "dhr_op06_called_here",
    "dhr_op06_auto_call_allowed",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "downstream_auto_execution_allowed",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)

P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF: Final = (
    "RDB_OP01_MRB_OP08_RESULT_CLOSURE_READY_FOR_OP02_NO_DHR_OP05_CALL"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF: Final = (
    "RDB_OP01_WAITING_FOR_MRB_OP08_RESULT_MEMO_CLOSURE"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF: Final = (
    "RDB_OP01_REPAIR_MRB_OP08_RESULT_MEMO_CLOSURE_INTAKE"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "RDB_OP01_BLOCKED_MRB_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_MANUAL_HOLD_REF: Final = (
    "RDB_OP01_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_MRB08_RDB_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_MANUAL_HOLD_REF,
)

P7_R54_AHR_POST_MRB08_RDB_MRB08_RESULT_BRANCH_REFS: Final[tuple[str, ...]] = (
    mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
    mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
    mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
    mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
)
P7_R54_AHR_POST_MRB08_RDB_DHR_OP04_RESULT_STATUS_REFS: Final[tuple[str, ...]] = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF,
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF,
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF,
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF,
)

P7_R54_AHR_POST_MRB08_RDB_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "boundary_prefix_ref", "boundary_prefix_meaning_ref",
    "expected_from_mrb08_ref", "expected_next_required_step_ref", "not_stage_refs", "not_stage_ref_count",
    "support_material_refs", "support_material_ref_count", "local_received_zip_refs", "local_received_zip_ref_count",
    "body_free", "rdb_op00_scope_confirmed", "rdb_op00_no_touch_boundary_confirmed", "rdb_op00_no_promotion_boundary_confirmed",
    "source_mode_local_received_zip_only_confirmed", "github_connection_check_not_required_by_mash_instruction", "github_connection_check_performed",
    "rdb_op00_does_not_intake_mrb_op08_result_memo", "rdb_op00_does_not_recall_dhr_op04", "rdb_op00_does_not_call_dhr_op05",
    "rdb_op00_does_not_call_dhr_op06", "rdb_op00_does_not_execute_dmd_r52_or_release", "rdb_op00_does_not_run_actual_local_human_review",
    "rdb_op00_does_not_create_receipts_rows_or_disposal", "rdb_op00_does_not_start_p5_p6_p8_p7_or_release", "rdb_op00_does_not_change_api_db_rn_runtime_response_key",
    "rdb_op00_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_MRB08_RDB_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed", "op00_no_touch_boundary_confirmed", "op00_no_promotion_boundary_confirmed", "op00_contract_valid",
    "mrb_op08_result_memo_present", "mrb_op08_contract_valid", "mrb_op08_schema_version", "mrb_op08_operation_step_ref", "mrb_op08_material_ref",
    "mrb_op08_status_ref", "bodyfree_result_memo_closure_status_ref", "mrb_op08_closed_bodyfree_stopped", "mrb_op08_waiting_for_op06_op07_or_validation", "mrb_op08_repair_required", "mrb_op08_bodyfree_leak_promotion_or_autorun_blocked",
    "mrb_selected_branch_ref", "dhr_op04_manual_call_performed_by_mrb", "dhr_op04_result_status_ref", "actual_source_claim_confirmed_for_downstream_handoff",
    "op06_mrb_selected_branch_ref", "op06_mrb_next_required_step", "op06_dhr_op04_result_captured", "op06_dhr_op04_status_ref",
    "validation_summary_bodyfree_accepted", "result_memo_bodyfree_accepted", "combined_run_status_ref", "full_backend_suite_green_confirmed", "combined_mrb_dri_dhr_green_confirmed",
    "mrb_op08_closure_is_not_dhr_op05_call", "mrb_op08_closure_is_not_dhr_op06_call", "mrb_op08_closure_is_not_dmd_or_r52_execution", "mrb_op08_closure_is_not_p8_start", "mrb_op08_closure_is_not_p7_complete", "mrb_op08_closure_is_not_release_ready",
    "mrb_op08_dhr_op05_not_called", "mrb_op08_dhr_op06_not_called", "mrb_op08_dmd_r52_not_executed", "mrb_op08_p5_p6_p8_p7_release_not_started", "mrb_op08_p8_question_design_not_started", "mrb_op08_p8_question_implementation_not_started",
    "mrb_op08_input_forbidden_payload_key_path_refs", "mrb_op08_input_forbidden_payload_key_path_count", "mrb_op08_input_body_like_value_path_refs", "mrb_op08_input_body_like_value_path_count", "mrb_op08_input_promotion_claim_refs", "mrb_op08_input_promotion_claim_ref_count",
    "rdb_op01_status_ref", "mrb08_result_memo_closure_intake_status_ref", "rdb_op01_allowed_status_refs", "rdb_op01_allowed_status_ref_count",
    "rdb_op01_ready_for_rdb_op02", "rdb_op01_waiting_for_mrb08_closure", "rdb_op01_repair_required", "rdb_op01_bodyfree_leak_promotion_or_autorun_blocked", "rdb_op01_manual_hold_unresolved_no_promotion",
    "rdb_op01_reason_refs", "rdb_op01_reason_ref_count", "rdb_op01_blocker_refs", "rdb_op01_blocker_ref_count",
    "rdb_op01_does_not_classify_branch_status_consistency", "rdb_op01_does_not_materialize_branch_specific_manual_decision", "rdb_op01_does_not_materialize_next_stage_candidate_envelope",
    "rdb_op01_does_not_recall_dhr_op04", "rdb_op01_does_not_call_dhr_op05", "rdb_op01_does_not_call_dhr_op06", "rdb_op01_does_not_execute_dmd_r52_or_release", "rdb_op01_does_not_start_p5_p6_p8_p7_or_release", "rdb_op01_does_not_change_api_db_rn_runtime_response_key", "rdb_op01_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_MRB08_RDB_DEFAULT_REVIEW_SESSION_ID,
        max_length=160,
    )


def _clean_ref(value: Any, *, default: str = "missing", max_length: int = 260) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _dedupe_clean_refs(values: Sequence[Any] | None, *, max_length: int = 260) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        text = _clean_ref(value, default="", max_length=max_length)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MRB08_RDB_NO_TOUCH_CONTRACT_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MRB08_RDB_BODY_FREE_MARKER_REFS}


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS}


def _required_fields_present(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:6]}")


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


def _scan_forbidden_payload_key_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_MRB08_RDB_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_body_like_value_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    suspect_key_tokens = (
        "raw_input", "input_body", "comment_text", "returned_surface_body", "question_text",
        "draft_question_text", "answer_text", "reviewer_note", "reviewer_free_text", "body_full_packet",
        "private_user_dictionary_text", "local_path", "file_path", "absolute_path", "relative_path",
        "input_hash", "body_hash", "sha256", "terminal_output", "stdout", "stderr", "traceback",
    )
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
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


def _scan_promotion_claim_refs(value: Any, *, path: str = "artifact") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_MRB08_RDB_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _assert_false_mapping(data: Mapping[str, Any], *, field: str, source: str) -> None:
    mapping = data.get(field)
    if not isinstance(mapping, Mapping):
        raise ValueError(f"{source} {field} must be a mapping")
    true_keys = [str(key) for key, value in mapping.items() if value is True]
    if true_keys:
        raise ValueError(f"{source} {field} must keep false markers: {true_keys[:6]}")


def _assert_public_contract_false(data: Mapping[str, Any], *, source: str) -> None:
    if data.get("public_contract") != public_contract_flags():
        raise ValueError(f"{source} public contract changed")


def _assert_base_bodyfree_boundary(data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_MRB08_RDB_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_MRB08_RDB_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_MRB08_RDB_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref or data.get("policy_section") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git connection flags changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must stay body-free")
    _assert_public_contract_false(data, source=source)
    _assert_false_mapping(data, field="rdb_no_touch_contract", source=source)
    _assert_false_mapping(data, field="body_free_markers", source=source)
    for key in P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")
    if any(key in P7_R54_AHR_POST_MRB08_RDB_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")


def _op00_contract_valid(op00: Mapping[str, Any] | None) -> bool:
    if not isinstance(op00, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract(op00) is True
    except ValueError:
        return False


def _mrb_op08_contract_valid(op08: Mapping[str, Any] | None) -> bool:
    if not isinstance(op08, Mapping):
        return False
    try:
        return mrb.assert_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure_contract(op08) is True
    except ValueError:
        return False


def _op01_status_reason_blocker_next(
    *,
    op00_valid: bool,
    op08_present: bool,
    op08_contract_valid: bool,
    op08_status_ref: str,
    op08_closed: bool,
    op08_waiting: bool,
    op08_repair: bool,
    op08_blocked: bool,
    validation_accepted: bool,
    result_memo_accepted: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("mrb_op08_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("mrb_op08_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("mrb_op08_input_promotion_or_autorun_claim_detected")
    if op08_blocked or op08_status_ref == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("mrb_op08_status_bodyfree_leak_promotion_or_autorun_blocked")
    if blockers:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["mrb_op08_result_memo_failed_bodyfree_no_promotion_boundary_before_rdb_op02"],
            _dedupe_clean_refs(blockers, max_length=300),
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_MRB08_INTAKE_REF,
        )
    if not op00_valid:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF,
            ["rdb_op00_contract_invalid_before_mrb_op08_intake"],
            ["rdb_op00_contract_invalid"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_MRB08_INTAKE_REF,
        )
    if not op08_present:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF,
            ["mrb_op08_result_memo_closure_not_provided_yet"],
            ["mrb_op08_result_memo_closure_missing"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_FOR_MRB08_CLOSURE_REF,
        )
    if not op08_contract_valid:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF,
            ["mrb_op08_result_memo_closure_contract_repair_required_before_rdb_op02"],
            ["mrb_op08_result_memo_closure_contract_invalid"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_MRB08_INTAKE_REF,
        )
    if op08_waiting or op08_status_ref == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_WAITING_FOR_OP06_OP07_OR_VALIDATION_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF,
            ["mrb_op08_result_memo_closure_waiting_before_result_manual_decision"],
            ["mrb_op08_waiting_for_op06_op07_or_validation"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_FOR_MRB08_CLOSURE_REF,
        )
    if op08_repair or op08_status_ref == mrb.P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF,
            ["mrb_op08_result_memo_closure_repair_required_before_rdb_op02"],
            ["mrb_op08_repair_required"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_MRB08_INTAKE_REF,
        )
    if op08_closed and validation_accepted and result_memo_accepted:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF,
            ["mrb_op08_closed_bodyfree_result_memo_ready_for_rdb_op02_consistency_check"],
            [],
            P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_MANUAL_HOLD_REF,
        ["mrb_op08_result_memo_closure_unresolved_without_promotion"],
        ["mrb_op08_result_memo_closure_unresolved"],
        P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_REF,
    )


def build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build RDB-OP00 body-free scope / no-touch / no-promotion refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb08_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_MRB08_RDB_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_MRB08_RDB_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_MRB08_RDB_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_MRB08_RDB_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_mrb08_ref": P7_R54_AHR_POST_MRB08_RDB_EXPECTED_FROM_MRB08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_MRB08_RDB_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_MRB08_RDB_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_MRB08_RDB_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "rdb_op00_scope_confirmed": True,
        "rdb_op00_no_touch_boundary_confirmed": True,
        "rdb_op00_no_promotion_boundary_confirmed": True,
        "source_mode_local_received_zip_only_confirmed": True,
        "github_connection_check_not_required_by_mash_instruction": True,
        "github_connection_check_performed": False,
        "rdb_op00_does_not_intake_mrb_op08_result_memo": True,
        "rdb_op00_does_not_recall_dhr_op04": True,
        "rdb_op00_does_not_call_dhr_op05": True,
        "rdb_op00_does_not_call_dhr_op06": True,
        "rdb_op00_does_not_execute_dmd_r52_or_release": True,
        "rdb_op00_does_not_run_actual_local_human_review": True,
        "rdb_op00_does_not_create_receipts_rows_or_disposal": True,
        "rdb_op00_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op00_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RDB-OP00 scope / no-touch / no-promotion refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP00_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP00")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MRB08_RDB_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP00_STEP_REF,
        source="P7-R54-AHR-PostMRB08-RDB-OP00",
    )
    for key in (
        "rdb_op00_scope_confirmed",
        "rdb_op00_no_touch_boundary_confirmed",
        "rdb_op00_no_promotion_boundary_confirmed",
        "source_mode_local_received_zip_only_confirmed",
        "github_connection_check_not_required_by_mash_instruction",
        "rdb_op00_does_not_intake_mrb_op08_result_memo",
        "rdb_op00_does_not_recall_dhr_op04",
        "rdb_op00_does_not_call_dhr_op05",
        "rdb_op00_does_not_call_dhr_op06",
        "rdb_op00_does_not_execute_dmd_r52_or_release",
        "rdb_op00_does_not_run_actual_local_human_review",
        "rdb_op00_does_not_create_receipts_rows_or_disposal",
        "rdb_op00_does_not_start_p5_p6_p8_p7_or_release",
        "rdb_op00_does_not_change_api_db_rn_runtime_response_key",
        "rdb_op00_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP00 required true boundary changed: {key}")
    if data.get("github_connection_check_performed") is not False:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 git check must stay unperformed")
    if data.get("boundary_prefix_ref") != P7_R54_AHR_POST_MRB08_RDB_BOUNDARY_PREFIX_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 boundary prefix changed")
    if data.get("boundary_prefix_meaning_ref") != P7_R54_AHR_POST_MRB08_RDB_BOUNDARY_PREFIX_MEANING_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 boundary prefix meaning changed")
    if data.get("expected_next_required_step_ref") != P7_R54_AHR_POST_MRB08_RDB_EXPECTED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 expected next step changed")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP00 {count_field} changed")
    if data.get("local_received_zip_ref_count") != len(data.get("local_received_zip_refs") or {}):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 local zip count changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP00 next step changed")
    return True


def build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
    *,
    scope_no_touch_no_promotion_refreeze_after_mrb_op08: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP01 body-free MRB-OP08 result memo closure intake material."""

    op00 = (
        scope_no_touch_no_promotion_refreeze_after_mrb_op08
        if isinstance(scope_no_touch_no_promotion_refreeze_after_mrb_op08, Mapping)
        else build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08(review_session_id=review_session_id)
    )
    op08_map = mrb_op08_result_memo_closure if isinstance(mrb_op08_result_memo_closure, Mapping) else {}
    op00_valid = _op00_contract_valid(op00)
    op08_present = isinstance(mrb_op08_result_memo_closure, Mapping)
    op08_contract_valid = _mrb_op08_contract_valid(op08_map if op08_present else None)

    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(op08_map, path="mrb_op08_result_memo_closure"),
        max_length=320,
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(op08_map, path="mrb_op08_result_memo_closure"),
        max_length=320,
    )
    promotion_claims = _dedupe_clean_refs(
        _scan_promotion_claim_refs(op08_map, path="mrb_op08_result_memo_closure"),
        max_length=320,
    )

    op08_status_ref = _clean_ref(op08_map.get("mrb_op08_status_ref"), default="mrb_op08_status_missing", max_length=320)
    op08_closed = bool(op08_map.get("mrb_op08_closed_bodyfree_stopped") is True)
    op08_waiting = bool(op08_map.get("mrb_op08_waiting_for_op06_op07_or_validation") is True)
    op08_repair = bool(op08_map.get("mrb_op08_repair_required") is True)
    op08_blocked = bool(op08_map.get("mrb_op08_bodyfree_leak_promotion_or_autorun_blocked") is True)
    validation_accepted = bool(op08_map.get("validation_summary_bodyfree_accepted") is True)
    result_memo_accepted = bool(op08_map.get("result_memo_bodyfree_accepted") is True)

    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        op00_valid=op00_valid,
        op08_present=op08_present,
        op08_contract_valid=op08_contract_valid,
        op08_status_ref=op08_status_ref,
        op08_closed=op08_closed,
        op08_waiting=op08_waiting,
        op08_repair=op08_repair,
        op08_blocked=op08_blocked,
        validation_accepted=validation_accepted,
        result_memo_accepted=result_memo_accepted,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF
    waiting = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_WAITING_FOR_MRB08_CLOSURE_REF
    repair = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_REPAIR_MRB08_INTAKE_REF
    blocked = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    manual_hold = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_MANUAL_HOLD_REF

    session_id = _safe_review_session_id(review_session_id or op00.get("review_session_id") or op08_map.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op01_mrb08_result_memo_closure_intake_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version"), default="rdb_op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id"), default="rdb_op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step"), default="rdb_op00_next_step_missing", max_length=260),
        "op00_scope_confirmed": bool(op00.get("rdb_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(op00.get("rdb_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(op00.get("rdb_op00_no_promotion_boundary_confirmed") is True),
        "op00_contract_valid": op00_valid,
        "mrb_op08_result_memo_present": op08_present,
        "mrb_op08_contract_valid": op08_contract_valid,
        "mrb_op08_schema_version": _clean_ref(op08_map.get("schema_version"), default="mrb_op08_schema_missing", max_length=260),
        "mrb_op08_operation_step_ref": _clean_ref(op08_map.get("operation_step_ref"), default="mrb_op08_operation_step_missing", max_length=260),
        "mrb_op08_material_ref": _clean_ref(op08_map.get("material_id"), default="mrb_op08_material_missing", max_length=260),
        "mrb_op08_status_ref": op08_status_ref,
        "bodyfree_result_memo_closure_status_ref": _clean_ref(op08_map.get("bodyfree_result_memo_closure_status_ref"), default="bodyfree_result_memo_closure_status_missing", max_length=320),
        "mrb_op08_closed_bodyfree_stopped": op08_closed,
        "mrb_op08_waiting_for_op06_op07_or_validation": op08_waiting,
        "mrb_op08_repair_required": op08_repair,
        "mrb_op08_bodyfree_leak_promotion_or_autorun_blocked": op08_blocked,
        "mrb_selected_branch_ref": _clean_ref(op08_map.get("mrb_selected_branch_ref"), default="mrb_selected_branch_missing", max_length=320),
        "dhr_op04_manual_call_performed_by_mrb": bool(op08_map.get("dhr_op04_manual_call_performed_by_mrb") is True),
        "dhr_op04_result_status_ref": _clean_ref(op08_map.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=320),
        "actual_source_claim_confirmed_for_downstream_handoff": bool(op08_map.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
        "op06_mrb_selected_branch_ref": _clean_ref(op08_map.get("op06_mrb_selected_branch_ref"), default="op06_mrb_selected_branch_missing", max_length=320),
        "op06_mrb_next_required_step": _clean_ref(op08_map.get("op06_mrb_next_required_step"), default="op06_mrb_next_step_missing", max_length=320),
        "op06_dhr_op04_result_captured": bool(op08_map.get("op06_dhr_op04_result_captured") is True),
        "op06_dhr_op04_status_ref": _clean_ref(op08_map.get("op06_dhr_op04_status_ref"), default="op06_dhr_op04_status_missing", max_length=320),
        "validation_summary_bodyfree_accepted": validation_accepted,
        "result_memo_bodyfree_accepted": result_memo_accepted,
        "combined_run_status_ref": _clean_ref(op08_map.get("combined_run_status_ref"), default="not_run", max_length=120),
        "full_backend_suite_green_confirmed": bool(op08_map.get("full_backend_suite_green_confirmed") is True),
        "combined_mrb_dri_dhr_green_confirmed": bool(op08_map.get("combined_mrb_dri_dhr_green_confirmed") is True),
        "mrb_op08_closure_is_not_dhr_op05_call": True,
        "mrb_op08_closure_is_not_dhr_op06_call": True,
        "mrb_op08_closure_is_not_dmd_or_r52_execution": True,
        "mrb_op08_closure_is_not_p8_start": True,
        "mrb_op08_closure_is_not_p7_complete": True,
        "mrb_op08_closure_is_not_release_ready": True,
        "mrb_op08_dhr_op05_not_called": bool(op08_map.get("dhr_op05_not_called") is True),
        "mrb_op08_dhr_op06_not_called": bool(op08_map.get("dhr_op06_not_called") is True),
        "mrb_op08_dmd_r52_not_executed": bool(op08_map.get("dmd_r52_not_executed") is True),
        "mrb_op08_p5_p6_p8_p7_release_not_started": bool(op08_map.get("p5_p6_p8_p7_release_not_started") is True),
        "mrb_op08_p8_question_design_not_started": bool(op08_map.get("p8_question_design_not_started") is True),
        "mrb_op08_p8_question_implementation_not_started": bool(op08_map.get("p8_question_implementation_not_started") is True),
        "mrb_op08_input_forbidden_payload_key_path_refs": forbidden_paths,
        "mrb_op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "mrb_op08_input_body_like_value_path_refs": body_like_paths,
        "mrb_op08_input_body_like_value_path_count": len(body_like_paths),
        "mrb_op08_input_promotion_claim_refs": promotion_claims,
        "mrb_op08_input_promotion_claim_ref_count": len(promotion_claims),
        "rdb_op01_status_ref": status_ref,
        "mrb08_result_memo_closure_intake_status_ref": status_ref,
        "rdb_op01_allowed_status_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP01_ALLOWED_STATUS_REFS),
        "rdb_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP01_ALLOWED_STATUS_REFS),
        "rdb_op01_ready_for_rdb_op02": ready,
        "rdb_op01_waiting_for_mrb08_closure": waiting,
        "rdb_op01_repair_required": repair,
        "rdb_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "rdb_op01_manual_hold_unresolved_no_promotion": manual_hold,
        "rdb_op01_reason_refs": reasons,
        "rdb_op01_reason_ref_count": len(reasons),
        "rdb_op01_blocker_refs": blockers,
        "rdb_op01_blocker_ref_count": len(blockers),
        "rdb_op01_does_not_classify_branch_status_consistency": True,
        "rdb_op01_does_not_materialize_branch_specific_manual_decision": True,
        "rdb_op01_does_not_materialize_next_stage_candidate_envelope": True,
        "rdb_op01_does_not_recall_dhr_op04": True,
        "rdb_op01_does_not_call_dhr_op05": True,
        "rdb_op01_does_not_call_dhr_op06": True,
        "rdb_op01_does_not_execute_dmd_r52_or_release": True,
        "rdb_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op01_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RDB-OP01 MRB-OP08 result memo closure intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP01_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP01")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MRB08_RDB_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF,
        source="P7-R54-AHR-PostMRB08-RDB-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_MRB08_RDB_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 OP00 next step changed")
    if data.get("mrb08_result_memo_closure_intake_status_ref") != data.get("rdb_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 status alias changed")
    for key in (
        "mrb_op08_closure_is_not_dhr_op05_call",
        "mrb_op08_closure_is_not_dhr_op06_call",
        "mrb_op08_closure_is_not_dmd_or_r52_execution",
        "mrb_op08_closure_is_not_p8_start",
        "mrb_op08_closure_is_not_p7_complete",
        "mrb_op08_closure_is_not_release_ready",
        "rdb_op01_does_not_classify_branch_status_consistency",
        "rdb_op01_does_not_materialize_branch_specific_manual_decision",
        "rdb_op01_does_not_materialize_next_stage_candidate_envelope",
        "rdb_op01_does_not_recall_dhr_op04",
        "rdb_op01_does_not_call_dhr_op05",
        "rdb_op01_does_not_call_dhr_op06",
        "rdb_op01_does_not_execute_dmd_r52_or_release",
        "rdb_op01_does_not_start_p5_p6_p8_p7_or_release",
        "rdb_op01_does_not_change_api_db_rn_runtime_response_key",
        "rdb_op01_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP01 required true boundary changed: {key}")
    for field, count_field in (
        ("mrb_op08_input_forbidden_payload_key_path_refs", "mrb_op08_input_forbidden_payload_key_path_count"),
        ("mrb_op08_input_body_like_value_path_refs", "mrb_op08_input_body_like_value_path_count"),
        ("mrb_op08_input_promotion_claim_refs", "mrb_op08_input_promotion_claim_ref_count"),
        ("rdb_op01_reason_refs", "rdb_op01_reason_ref_count"),
        ("rdb_op01_blocker_refs", "rdb_op01_blocker_ref_count"),
        ("rdb_op01_allowed_status_refs", "rdb_op01_allowed_status_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP01 {count_field} changed")
    if tuple(data.get("rdb_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 allowed status refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 not-yet steps changed")
    status_ref = data.get("rdb_op01_status_ref")
    flags = [
        data.get("rdb_op01_ready_for_rdb_op02") is True,
        data.get("rdb_op01_waiting_for_mrb08_closure") is True,
        data.get("rdb_op01_repair_required") is True,
        data.get("rdb_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("rdb_op01_manual_hold_unresolved_no_promotion") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_MRB08_RDB_OP01_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 exactly one status branch must be selected")
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_OP01_STATUS_READY_FOR_OP02_REF:
        if data.get("mrb_op08_contract_valid") is not True or data.get("mrb_op08_closed_bodyfree_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 ready branch requires valid closed MRB-OP08")
        if data.get("validation_summary_bodyfree_accepted") is not True or data.get("result_memo_bodyfree_accepted") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 ready branch requires accepted validation/result memo")
        if data.get("rdb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 ready next step changed")
    else:
        if not data.get("rdb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 non-ready branch must carry blockers")
        if data.get("next_required_step") == P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 non-ready branch cannot continue to OP02")
    if data.get("actual_source_claim_confirmed_for_downstream_handoff") is True:
        if data.get("mrb_selected_branch_ref") != mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 confirmed handoff mirror must come from MRB confirmed branch")
        if data.get("dhr_op04_result_status_ref") != dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 confirmed handoff mirror must come from DHR confirmed status")
    if data.get("full_backend_suite_green_confirmed") is True and data.get("combined_run_status_ref") != "passed":
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP01 cannot claim full backend green when not passed")
    return True

P7_R54_AHR_POST_MRB08_RDB_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op02_mrb_selected_branch_dhr_op04_result_status_consistency_check.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op03_dhr_op04_result_manual_decision_lane_resolver.bodyfree.v1"
)

P7_R54_AHR_POST_MRB08_RDB_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:3]
)
P7_R54_AHR_POST_MRB08_RDB_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[3:]
)
P7_R54_AHR_POST_MRB08_RDB_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:4]
)
P7_R54_AHR_POST_MRB08_RDB_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[4:]
)

P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF: Final = (
    "RDB_OP02_MRB_BRANCH_DHR_STATUS_CONSISTENT_READY_FOR_OP03"
)
P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_WAITING_FOR_MRB08_CLOSURE_REF: Final = (
    "RDB_OP02_WAITING_FOR_MRB08_CLOSURE_OR_VALIDATION_REFS"
)
P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF: Final = (
    "RDB_OP02_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH"
)
P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "RDB_OP02_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF: Final = (
    "RDB_OP02_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_MRB08_RDB_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_WAITING_FOR_MRB08_CLOSURE_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
)

P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF: Final = (
    "RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF: Final = (
    "RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF: Final = (
    "RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF: Final = (
    "RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF: Final = (
    "RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF: Final = (
    "RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF: Final = (
    "RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH"
)
P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
    P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
)

P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF: Final = (
    "prepare_dhr_op05_manual_handoff_decision_without_call"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF: Final = (
    "prepare_retry_or_start_actual_local_only_human_review_operation_decision_without_p8_question"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: Final = (
    "wait_for_external_bodyfree_actual_source_claim_without_raw_evidence"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF: Final = (
    "repair_dhr_op04_result_or_mrb08_boundary_without_downstream_promotion"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    "manual_hold_unresolved_post_mrb08_without_promotion"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_MRB08_CLOSURE_REF: Final = (
    "wait_for_mrb08_closure_or_validation_refs_before_result_manual_decision"
)
P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF: Final = (
    "blocked_post_mrb08_bodyfree_leak_promotion_or_autorun"
)

P7_R54_AHR_POST_MRB08_RDB_DHR_STATUS_TO_MRB_BRANCH_REF_MAP: Final[Mapping[str, str]] = {
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF:
        mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF:
        mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF:
        mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF:
        mrb.P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
}
P7_R54_AHR_POST_MRB08_RDB_MRB_BRANCH_TO_DHR_STATUS_REF_MAP: Final[Mapping[str, str]] = {
    value: key for key, value in P7_R54_AHR_POST_MRB08_RDB_DHR_STATUS_TO_MRB_BRANCH_REF_MAP.items()
}
P7_R54_AHR_POST_MRB08_RDB_BRANCH_STATUS_MAPPING_REFS: Final[tuple[str, ...]] = tuple(
    f"{dhr_status}<->{mrb_branch}"
    for dhr_status, mrb_branch in P7_R54_AHR_POST_MRB08_RDB_DHR_STATUS_TO_MRB_BRANCH_REF_MAP.items()
)
P7_R54_AHR_POST_MRB08_RDB_OP03_BRANCH_PRIORITY_REFS: Final[tuple[str, ...]] = (
    "priority_1_bodyfree_leak_promotion_or_autorun_blocked",
    "priority_2_op02_contract_or_mrb08_schema_repair_required",
    "priority_3_mrb08_waiting_for_closure_or_validation",
    "priority_4_mrb08_branch_status_mismatch_repair_required",
    "priority_5_dhr_op04_confirmed_bodyfree",
    "priority_6_dhr_op04_not_confirmed_retry_or_start_required",
    "priority_7_dhr_op04_waiting_external_bodyfree_claim",
    "priority_8_dhr_op04_invalid_repair_required",
    "fallback_incomplete_unresolved_manual_hold",
)

P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_CONFIRMED_DHR_OP05_HANDOFF_CANDIDATE_REF: Final = (
    "dhr_op05_manual_handoff_candidate"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_RETRY_OR_START_REF: Final = (
    "retry_or_start_actual_local_only_human_review_operation"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_EXTERNAL_CLAIM_REF: Final = (
    "wait_for_external_bodyfree_actual_source_claim"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_RESULT_OR_MRB08_REF: Final = (
    "repair_dhr_op04_result_or_mrb08_boundary"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    "manual_hold_unresolved_post_mrb08"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_MRB08_CLOSURE_REF: Final = (
    "wait_for_mrb08_closure_or_validation_refs"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF: Final = (
    "blocked_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_BRANCH_STATUS_MISMATCH_REF: Final = (
    "repair_mrb08_branch_status_mismatch"
)

P7_R54_AHR_POST_MRB08_RDB_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_status_ref", "op01_next_required_step", "op01_contract_valid", "op01_ready_for_rdb_op02",
    "op01_waiting_for_mrb08_closure", "op01_repair_required", "op01_bodyfree_leak_promotion_or_autorun_blocked", "op01_manual_hold_unresolved_no_promotion",
    "mrb_op08_contract_valid", "mrb_op08_closed_bodyfree_stopped", "validation_summary_bodyfree_accepted", "result_memo_bodyfree_accepted",
    "mrb_selected_branch_ref", "dhr_op04_result_status_ref", "op06_mrb_selected_branch_ref", "op06_dhr_op04_status_ref", "op06_dhr_op04_result_captured",
    "dhr_op04_manual_call_performed_by_mrb", "actual_source_claim_confirmed_for_downstream_handoff",
    "expected_mrb_selected_branch_ref_for_dhr_status", "expected_dhr_op04_result_status_ref_for_mrb_branch", "branch_status_mapping_refs", "branch_status_mapping_ref_count",
    "rdb_op02_status_ref", "branch_status_consistency_status_ref", "rdb_op02_allowed_status_refs", "rdb_op02_allowed_status_ref_count",
    "branch_status_consistency_checked", "branch_status_consistent", "rdb_op02_ready_for_rdb_op03", "rdb_op02_waiting_for_mrb08_closure", "rdb_op02_repair_required", "rdb_op02_bodyfree_leak_promotion_or_autorun_blocked", "rdb_op02_manual_hold_unresolved_no_promotion",
    "op06_branch_matches_mrb_selected_branch", "op06_dhr_status_matches_dhr_op04_result_status", "dhr_status_maps_to_mrb_selected_branch", "mrb_selected_branch_maps_to_dhr_status",
    "actual_source_claim_confirmed_only_when_dhr_confirmed", "actual_source_claim_confirmed_required_for_confirmed_branch_satisfied", "dhr_op04_manual_call_present_for_called_result_branch", "dhr_op04_result_captured_for_called_result_branch",
    "branch_status_mismatch_refs", "branch_status_mismatch_ref_count", "rdb_op02_reason_refs", "rdb_op02_reason_ref_count", "rdb_op02_blocker_refs", "rdb_op02_blocker_ref_count",
    "op01_input_forbidden_payload_key_path_refs", "op01_input_forbidden_payload_key_path_count", "op01_input_body_like_value_path_refs", "op01_input_body_like_value_path_count", "op01_input_promotion_claim_refs", "op01_input_promotion_claim_ref_count",
    "rdb_op02_does_not_materialize_branch_specific_manual_decision", "rdb_op02_does_not_materialize_next_stage_candidate_envelope", "rdb_op02_does_not_recall_dhr_op04", "rdb_op02_does_not_call_dhr_op05", "rdb_op02_does_not_call_dhr_op06", "rdb_op02_does_not_execute_dmd_r52_or_release", "rdb_op02_does_not_start_p5_p6_p8_p7_or_release", "rdb_op02_does_not_change_api_db_rn_runtime_response_key", "rdb_op02_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MRB08_RDB_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_next_required_step", "op02_contract_valid", "op02_branch_status_consistent", "op02_ready_for_rdb_op03",
    "mrb_selected_branch_ref", "dhr_op04_result_status_ref", "actual_source_claim_confirmed_for_downstream_handoff", "branch_status_mismatch_refs", "branch_status_mismatch_ref_count",
    "rdb_status_ref", "result_manual_decision_lane_status_ref", "rdb_allowed_status_refs", "rdb_allowed_status_ref_count", "rdb_op03_branch_priority_refs", "rdb_op03_branch_priority_ref_count", "rdb_op03_selected_priority_ref",
    "decision_lane_ref", "selected_next_required_step_ref", "exactly_one_rdb_result_branch", "manual_decision_required_without_auto_execution", "manual_decision_lane_resolved", "manual_decision_lane_resolved_bodyfree", "manual_decision_lane_resolver_only_no_materialization",
    "rdb_op03_confirmed_dhr_op05_manual_handoff_candidate", "rdb_op03_not_confirmed_retry_or_start_decision_required", "rdb_op03_waiting_external_claim_required", "rdb_op03_repair_required_after_dhr_op04_result", "rdb_op03_incomplete_unresolved_manual_hold", "rdb_op03_waiting_for_mrb08_result_closure", "rdb_op03_blocked_bodyfree_leak_promotion_or_autorun", "rdb_op03_repair_required_for_mrb08_branch_status_mismatch",
    "selected_next_stage_candidate_not_executed", "dhr_op05_manual_handoff_candidate_present", "retry_or_start_candidate_present", "external_claim_wait_candidate_present", "repair_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "rdb_op03_reason_refs", "rdb_op03_reason_ref_count", "rdb_op03_blocker_refs", "rdb_op03_blocker_ref_count",
    "rdb_op03_does_not_materialize_branch_specific_manual_decision", "rdb_op03_does_not_materialize_next_stage_candidate_envelope", "rdb_op03_does_not_recall_dhr_op04", "rdb_op03_does_not_call_dhr_op05", "rdb_op03_does_not_call_dhr_op06", "rdb_op03_does_not_execute_dmd_r52_or_release", "rdb_op03_does_not_start_p5_p6_p8_p7_or_release", "rdb_op03_does_not_change_api_db_rn_runtime_response_key", "rdb_op03_does_not_materialize_p8_question_spec",
    "p8_question_substitution_allowed", "question_text_materialized", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op01_contract_valid(op01: Mapping[str, Any] | None) -> bool:
    if not isinstance(op01, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract(op01) is True
    except ValueError:
        return False


def _op02_contract_valid(op02: Mapping[str, Any] | None) -> bool:
    if not isinstance(op02, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(op02) is True
    except ValueError:
        return False


def _expected_mrb_branch_for_dhr_status(dhr_status_ref: str) -> str:
    return P7_R54_AHR_POST_MRB08_RDB_DHR_STATUS_TO_MRB_BRANCH_REF_MAP.get(dhr_status_ref, "mrb_selected_branch_unmapped_for_dhr_status")


def _expected_dhr_status_for_mrb_branch(mrb_branch_ref: str) -> str:
    return P7_R54_AHR_POST_MRB08_RDB_MRB_BRANCH_TO_DHR_STATUS_REF_MAP.get(mrb_branch_ref, "dhr_op04_result_status_unmapped_for_mrb_branch")


def _called_result_branch_selected(mrb_branch_ref: str, dhr_status_ref: str) -> bool:
    return (
        mrb_branch_ref in P7_R54_AHR_POST_MRB08_RDB_MRB_BRANCH_TO_DHR_STATUS_REF_MAP
        or dhr_status_ref in P7_R54_AHR_POST_MRB08_RDB_DHR_STATUS_TO_MRB_BRANCH_REF_MAP
    )


def _op02_status_reason_blocker_next(
    *,
    op01_contract_valid: bool,
    op01_ready: bool,
    op01_waiting: bool,
    op01_repair: bool,
    op01_blocked: bool,
    op01_manual_hold: bool,
    branch_status_consistent: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    mismatch_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("rdb_op01_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("rdb_op01_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("rdb_op01_input_promotion_or_autorun_claim_detected")
    if op01_blocked:
        blockers.append("rdb_op01_bodyfree_leak_promotion_or_autorun_blocked")
    if blockers:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["rdb_op02_blocked_before_branch_status_consistency_due_to_bodyfree_or_promotion_boundary"],
            _dedupe_clean_refs(blockers, max_length=300),
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
        )
    if not op01_contract_valid:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF,
            ["rdb_op01_contract_invalid_before_branch_status_consistency_check"],
            ["rdb_op01_contract_invalid"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
        )
    if op01_waiting:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_WAITING_FOR_MRB08_CLOSURE_REF,
            ["rdb_op01_waiting_for_mrb08_closure_before_branch_status_consistency_check"],
            ["rdb_op01_waiting_for_mrb08_closure"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_MRB08_CLOSURE_REF,
        )
    if op01_repair:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF,
            ["rdb_op01_repair_required_before_branch_status_consistency_check"],
            ["rdb_op01_repair_required"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
        )
    if op01_manual_hold or not op01_ready:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
            ["rdb_op01_manual_hold_or_not_ready_before_branch_status_consistency_check"],
            ["rdb_op01_not_ready_for_rdb_op02"],
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
        )
    if not branch_status_consistent:
        return (
            P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF,
            ["mrb_selected_branch_and_dhr_op04_result_status_consistency_repair_required"],
            _dedupe_clean_refs(mismatch_refs, max_length=320),
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
        )
    return (
        P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF,
        ["mrb_selected_branch_and_dhr_op04_result_status_consistent_ready_for_rdb_op03_lane_resolver"],
        [],
        P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF,
    )


def _op03_lane_for_status_ref(status_ref: str) -> tuple[str, str, str, str]:
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_CONFIRMED_DHR_OP05_HANDOFF_CANDIDATE_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
            "priority_5_dhr_op04_confirmed_bodyfree",
            "dhr_op04_confirmed_bodyfree_manual_handoff_candidate_without_dhr_op05_call",
        )
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_RETRY_OR_START_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
            "priority_6_dhr_op04_not_confirmed_retry_or_start_required",
            "dhr_op04_not_confirmed_retry_or_start_decision_without_p8_question",
        )
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_EXTERNAL_CLAIM_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            "priority_7_dhr_op04_waiting_external_bodyfree_claim",
            "dhr_op04_waiting_external_bodyfree_claim_without_raw_evidence",
        )
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_RESULT_OR_MRB08_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            "priority_8_dhr_op04_invalid_repair_required",
            "dhr_op04_invalid_repair_required_without_downstream_promotion",
        )
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_MRB08_CLOSURE_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_MRB08_CLOSURE_REF,
            "priority_3_mrb08_waiting_for_closure_or_validation",
            "mrb08_closure_or_validation_refs_wait_without_downstream_promotion",
        )
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
            "priority_1_bodyfree_leak_promotion_or_autorun_blocked",
            "bodyfree_leak_promotion_or_autorun_blocked_without_raw_value_copy",
        )
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF:
        return (
            P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_BRANCH_STATUS_MISMATCH_REF,
            P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            "priority_4_mrb08_branch_status_mismatch_repair_required",
            "mrb08_branch_status_mismatch_repair_without_dhr_op05_call",
        )
    return (
        P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
        P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
        "fallback_incomplete_unresolved_manual_hold",
        "incomplete_unresolved_manual_hold_without_promotion",
    )


def _op03_status_from_op02(op02: Mapping[str, Any], *, op02_contract_valid: bool) -> str:
    if op02.get("rdb_op02_bodyfree_leak_promotion_or_autorun_blocked") is True:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    if not op02_contract_valid:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF
    if op02.get("rdb_op02_waiting_for_mrb08_closure") is True:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF
    if op02.get("rdb_op02_repair_required") is True and op02.get("branch_status_consistent") is not True:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF
    if op02.get("rdb_op02_manual_hold_unresolved_no_promotion") is True or op02.get("rdb_op02_ready_for_rdb_op03") is not True:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF
    dhr_status_ref = _clean_ref(op02.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=320)
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_INVALID_REPAIR_REQUIRED_REF:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF
    return P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF


def build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
    *,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP02 branch/status consistency material without downstream execution."""

    op01 = (
        mrb_op08_result_memo_closure_intake
        if isinstance(mrb_op08_result_memo_closure_intake, Mapping)
        else build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
            mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
            review_session_id=review_session_id,
        )
    )
    op01_valid = _op01_contract_valid(op01)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op01, path="rdb_op01_intake"), max_length=320)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op01, path="rdb_op01_intake"), max_length=320)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op01, path="rdb_op01_intake"), max_length=320)

    mrb_branch_ref = _clean_ref(op01.get("mrb_selected_branch_ref"), default="mrb_selected_branch_missing", max_length=320)
    dhr_status_ref = _clean_ref(op01.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=320)
    op06_branch_ref = _clean_ref(op01.get("op06_mrb_selected_branch_ref"), default="op06_mrb_selected_branch_missing", max_length=320)
    op06_dhr_status_ref = _clean_ref(op01.get("op06_dhr_op04_status_ref"), default="op06_dhr_op04_status_missing", max_length=320)
    expected_mrb_branch = _expected_mrb_branch_for_dhr_status(dhr_status_ref)
    expected_dhr_status = _expected_dhr_status_for_mrb_branch(mrb_branch_ref)

    called_result_branch = _called_result_branch_selected(mrb_branch_ref, dhr_status_ref)
    op06_branch_matches = bool(op06_branch_ref == mrb_branch_ref and not op06_branch_ref.endswith("missing"))
    op06_dhr_status_matches = bool(op06_dhr_status_ref == dhr_status_ref and not op06_dhr_status_ref.endswith("missing"))
    dhr_status_maps_to_mrb = bool(expected_mrb_branch == mrb_branch_ref)
    mrb_branch_maps_to_dhr = bool(expected_dhr_status == dhr_status_ref)
    actual_confirmed = bool(op01.get("actual_source_claim_confirmed_for_downstream_handoff") is True)
    dhr_confirmed = dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    actual_confirmed_only_when_dhr_confirmed = bool((not actual_confirmed) or dhr_confirmed)
    actual_confirmed_required_for_confirmed_branch_satisfied = bool((not dhr_confirmed) or actual_confirmed)
    dhr_call_present = bool((not called_result_branch) or op01.get("dhr_op04_manual_call_performed_by_mrb") is True)
    dhr_result_captured = bool((not called_result_branch) or op01.get("op06_dhr_op04_result_captured") is True)

    mismatch_refs: list[str] = []
    if not op01_valid:
        mismatch_refs.append("rdb_op01_contract_invalid")
    if not op06_branch_matches:
        mismatch_refs.append("op06_mrb_selected_branch_ref_mismatch_or_missing")
    if not op06_dhr_status_matches:
        mismatch_refs.append("op06_dhr_op04_status_ref_mismatch_or_missing")
    if not dhr_status_maps_to_mrb:
        mismatch_refs.append("dhr_op04_result_status_ref_does_not_map_to_mrb_selected_branch_ref")
    if not mrb_branch_maps_to_dhr:
        mismatch_refs.append("mrb_selected_branch_ref_does_not_map_to_dhr_op04_result_status_ref")
    if not actual_confirmed_only_when_dhr_confirmed:
        mismatch_refs.append("actual_source_claim_confirmed_true_outside_dhr_confirmed_branch")
    if not actual_confirmed_required_for_confirmed_branch_satisfied:
        mismatch_refs.append("actual_source_claim_confirmed_missing_for_dhr_confirmed_branch")
    if not dhr_call_present:
        mismatch_refs.append("dhr_op04_manual_call_performed_by_mrb_false_for_called_result_branch")
    if not dhr_result_captured:
        mismatch_refs.append("op06_dhr_op04_result_captured_false_for_called_result_branch")
    mismatch_refs = _dedupe_clean_refs(mismatch_refs, max_length=320)

    op01_ready = bool(op01.get("rdb_op01_ready_for_rdb_op02") is True)
    branch_status_consistent = bool(
        op01_valid
        and op01_ready
        and not forbidden_paths
        and not body_like_paths
        and not promotion_claims
        and not mismatch_refs
    )
    status_ref, reasons, blockers, next_required_step = _op02_status_reason_blocker_next(
        op01_contract_valid=op01_valid,
        op01_ready=op01_ready,
        op01_waiting=bool(op01.get("rdb_op01_waiting_for_mrb08_closure") is True),
        op01_repair=bool(op01.get("rdb_op01_repair_required") is True),
        op01_blocked=bool(op01.get("rdb_op01_bodyfree_leak_promotion_or_autorun_blocked") is True),
        op01_manual_hold=bool(op01.get("rdb_op01_manual_hold_unresolved_no_promotion") is True),
        branch_status_consistent=branch_status_consistent,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        mismatch_refs=mismatch_refs,
    )
    ready = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF
    waiting = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_WAITING_FOR_MRB08_CLOSURE_REF
    repair = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_REPAIR_REQUIRED_FOR_BRANCH_STATUS_MISMATCH_REF
    blocked = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    manual_hold = status_ref == P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF
    session_id = _safe_review_session_id(review_session_id or op01.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op02_mrb_branch_dhr_status_consistency_check_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01.get("schema_version"), default="rdb_op01_schema_missing", max_length=260),
        "op01_material_ref": _clean_ref(op01.get("material_id"), default="rdb_op01_material_missing", max_length=260),
        "op01_status_ref": _clean_ref(op01.get("rdb_op01_status_ref"), default="rdb_op01_status_missing", max_length=320),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step"), default="rdb_op01_next_step_missing", max_length=320),
        "op01_contract_valid": op01_valid,
        "op01_ready_for_rdb_op02": op01_ready,
        "op01_waiting_for_mrb08_closure": bool(op01.get("rdb_op01_waiting_for_mrb08_closure") is True),
        "op01_repair_required": bool(op01.get("rdb_op01_repair_required") is True),
        "op01_bodyfree_leak_promotion_or_autorun_blocked": bool(op01.get("rdb_op01_bodyfree_leak_promotion_or_autorun_blocked") is True),
        "op01_manual_hold_unresolved_no_promotion": bool(op01.get("rdb_op01_manual_hold_unresolved_no_promotion") is True),
        "mrb_op08_contract_valid": bool(op01.get("mrb_op08_contract_valid") is True),
        "mrb_op08_closed_bodyfree_stopped": bool(op01.get("mrb_op08_closed_bodyfree_stopped") is True),
        "validation_summary_bodyfree_accepted": bool(op01.get("validation_summary_bodyfree_accepted") is True),
        "result_memo_bodyfree_accepted": bool(op01.get("result_memo_bodyfree_accepted") is True),
        "mrb_selected_branch_ref": mrb_branch_ref,
        "dhr_op04_result_status_ref": dhr_status_ref,
        "op06_mrb_selected_branch_ref": op06_branch_ref,
        "op06_dhr_op04_status_ref": op06_dhr_status_ref,
        "op06_dhr_op04_result_captured": bool(op01.get("op06_dhr_op04_result_captured") is True),
        "dhr_op04_manual_call_performed_by_mrb": bool(op01.get("dhr_op04_manual_call_performed_by_mrb") is True),
        "actual_source_claim_confirmed_for_downstream_handoff": actual_confirmed,
        "expected_mrb_selected_branch_ref_for_dhr_status": expected_mrb_branch,
        "expected_dhr_op04_result_status_ref_for_mrb_branch": expected_dhr_status,
        "branch_status_mapping_refs": list(P7_R54_AHR_POST_MRB08_RDB_BRANCH_STATUS_MAPPING_REFS),
        "branch_status_mapping_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_BRANCH_STATUS_MAPPING_REFS),
        "rdb_op02_status_ref": status_ref,
        "branch_status_consistency_status_ref": status_ref,
        "rdb_op02_allowed_status_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP02_ALLOWED_STATUS_REFS),
        "rdb_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP02_ALLOWED_STATUS_REFS),
        "branch_status_consistency_checked": True,
        "branch_status_consistent": branch_status_consistent,
        "rdb_op02_ready_for_rdb_op03": ready,
        "rdb_op02_waiting_for_mrb08_closure": waiting,
        "rdb_op02_repair_required": repair,
        "rdb_op02_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "rdb_op02_manual_hold_unresolved_no_promotion": manual_hold,
        "op06_branch_matches_mrb_selected_branch": op06_branch_matches,
        "op06_dhr_status_matches_dhr_op04_result_status": op06_dhr_status_matches,
        "dhr_status_maps_to_mrb_selected_branch": dhr_status_maps_to_mrb,
        "mrb_selected_branch_maps_to_dhr_status": mrb_branch_maps_to_dhr,
        "actual_source_claim_confirmed_only_when_dhr_confirmed": actual_confirmed_only_when_dhr_confirmed,
        "actual_source_claim_confirmed_required_for_confirmed_branch_satisfied": actual_confirmed_required_for_confirmed_branch_satisfied,
        "dhr_op04_manual_call_present_for_called_result_branch": dhr_call_present,
        "dhr_op04_result_captured_for_called_result_branch": dhr_result_captured,
        "branch_status_mismatch_refs": mismatch_refs,
        "branch_status_mismatch_ref_count": len(mismatch_refs),
        "rdb_op02_reason_refs": reasons,
        "rdb_op02_reason_ref_count": len(reasons),
        "rdb_op02_blocker_refs": blockers,
        "rdb_op02_blocker_ref_count": len(blockers),
        "op01_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op01_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op01_input_body_like_value_path_refs": body_like_paths,
        "op01_input_body_like_value_path_count": len(body_like_paths),
        "op01_input_promotion_claim_refs": promotion_claims,
        "op01_input_promotion_claim_ref_count": len(promotion_claims),
        "rdb_op02_does_not_materialize_branch_specific_manual_decision": True,
        "rdb_op02_does_not_materialize_next_stage_candidate_envelope": True,
        "rdb_op02_does_not_recall_dhr_op04": True,
        "rdb_op02_does_not_call_dhr_op05": True,
        "rdb_op02_does_not_call_dhr_op06": True,
        "rdb_op02_does_not_execute_dmd_r52_or_release": True,
        "rdb_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op02_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RDB-OP02 MRB selected branch / DHR-OP04 result status consistency contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP02")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MRB08_RDB_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP02_STEP_REF,
        source="P7-R54-AHR-PostMRB08-RDB-OP02",
    )
    if data.get("op01_schema_version") != P7_R54_AHR_POST_MRB08_RDB_OP01_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 OP01 schema version changed")
    if data.get("branch_status_consistency_status_ref") != data.get("rdb_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 status alias changed")
    if tuple(data.get("rdb_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 allowed status refs changed")
    if tuple(data.get("branch_status_mapping_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_BRANCH_STATUS_MAPPING_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 mapping refs changed")
    for field, count_field in (
        ("branch_status_mapping_refs", "branch_status_mapping_ref_count"),
        ("branch_status_mismatch_refs", "branch_status_mismatch_ref_count"),
        ("rdb_op02_reason_refs", "rdb_op02_reason_ref_count"),
        ("rdb_op02_blocker_refs", "rdb_op02_blocker_ref_count"),
        ("op01_input_forbidden_payload_key_path_refs", "op01_input_forbidden_payload_key_path_count"),
        ("op01_input_body_like_value_path_refs", "op01_input_body_like_value_path_count"),
        ("op01_input_promotion_claim_refs", "op01_input_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP02 {count_field} changed")
    for key in (
        "branch_status_consistency_checked",
        "rdb_op02_does_not_materialize_branch_specific_manual_decision",
        "rdb_op02_does_not_materialize_next_stage_candidate_envelope",
        "rdb_op02_does_not_recall_dhr_op04",
        "rdb_op02_does_not_call_dhr_op05",
        "rdb_op02_does_not_call_dhr_op06",
        "rdb_op02_does_not_execute_dmd_r52_or_release",
        "rdb_op02_does_not_start_p5_p6_p8_p7_or_release",
        "rdb_op02_does_not_change_api_db_rn_runtime_response_key",
        "rdb_op02_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP02 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 not-yet steps changed")
    flags = [
        data.get("rdb_op02_ready_for_rdb_op03") is True,
        data.get("rdb_op02_waiting_for_mrb08_closure") is True,
        data.get("rdb_op02_repair_required") is True,
        data.get("rdb_op02_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("rdb_op02_manual_hold_unresolved_no_promotion") is True,
    ]
    if data.get("rdb_op02_status_ref") not in P7_R54_AHR_POST_MRB08_RDB_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 exactly one status branch must be selected")
    if data.get("branch_status_consistent") is True:
        if data.get("rdb_op02_status_ref") != P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 consistent branch status changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 consistent next step changed")
        if data.get("branch_status_mismatch_refs") or data.get("rdb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 consistent branch cannot carry mismatch/blockers")
        for key in (
            "op06_branch_matches_mrb_selected_branch",
            "op06_dhr_status_matches_dhr_op04_result_status",
            "dhr_status_maps_to_mrb_selected_branch",
            "mrb_selected_branch_maps_to_dhr_status",
            "actual_source_claim_confirmed_only_when_dhr_confirmed",
            "actual_source_claim_confirmed_required_for_confirmed_branch_satisfied",
            "dhr_op04_manual_call_present_for_called_result_branch",
            "dhr_op04_result_captured_for_called_result_branch",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP02 consistent branch invariant failed: {key}")
    else:
        if data.get("rdb_op02_status_ref") == P7_R54_AHR_POST_MRB08_RDB_OP02_STATUS_CONSISTENT_READY_FOR_OP03_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 inconsistent branch cannot be ready")
        if not data.get("rdb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 non-ready branch must carry blockers")
    if data.get("branch_status_consistent") is True and data.get("actual_source_claim_confirmed_for_downstream_handoff") is True and data.get("dhr_op04_result_status_ref") != dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP02 consistent confirmed claim cannot appear outside DHR confirmed status")
    return True


def build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
    *,
    mrb_branch_dhr_status_consistency_check: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP03 manual decision lane resolver material without materializing OP04."""

    op02 = (
        mrb_branch_dhr_status_consistency_check
        if isinstance(mrb_branch_dhr_status_consistency_check, Mapping)
        else build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
            mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
            mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
            review_session_id=review_session_id,
        )
    )
    op02_valid = _op02_contract_valid(op02)
    status_ref = _op03_status_from_op02(op02, op02_contract_valid=op02_valid)
    lane_ref, selected_next_step, priority_ref, reason_ref = _op03_lane_for_status_ref(status_ref)
    branch_flags = {
        "rdb_op03_confirmed_dhr_op05_manual_handoff_candidate": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
        "rdb_op03_not_confirmed_retry_or_start_decision_required": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
        "rdb_op03_waiting_external_claim_required": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
        "rdb_op03_repair_required_after_dhr_op04_result": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
        "rdb_op03_incomplete_unresolved_manual_hold": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        "rdb_op03_waiting_for_mrb08_result_closure": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
        "rdb_op03_blocked_bodyfree_leak_promotion_or_autorun": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
        "rdb_op03_repair_required_for_mrb08_branch_status_mismatch": status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
    }
    blockers = _dedupe_clean_refs(list(op02.get("rdb_op02_blocker_refs") or []), max_length=320)
    if not op02_valid and "rdb_op02_contract_invalid" not in blockers:
        blockers.append("rdb_op02_contract_invalid")
    if status_ref in (
        P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
    ) and not blockers:
        blockers.append(reason_ref)
    reasons = _dedupe_clean_refs([reason_ref, *list(op02.get("rdb_op02_reason_refs") or [])], max_length=320)
    session_id = _safe_review_session_id(review_session_id or op02.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02.get("schema_version"), default="rdb_op02_schema_missing", max_length=260),
        "op02_material_ref": _clean_ref(op02.get("material_id"), default="rdb_op02_material_missing", max_length=260),
        "op02_status_ref": _clean_ref(op02.get("rdb_op02_status_ref"), default="rdb_op02_status_missing", max_length=320),
        "op02_next_required_step": _clean_ref(op02.get("next_required_step"), default="rdb_op02_next_step_missing", max_length=320),
        "op02_contract_valid": op02_valid,
        "op02_branch_status_consistent": bool(op02.get("branch_status_consistent") is True),
        "op02_ready_for_rdb_op03": bool(op02.get("rdb_op02_ready_for_rdb_op03") is True),
        "mrb_selected_branch_ref": _clean_ref(op02.get("mrb_selected_branch_ref"), default="mrb_selected_branch_missing", max_length=320),
        "dhr_op04_result_status_ref": _clean_ref(op02.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=320),
        "actual_source_claim_confirmed_for_downstream_handoff": bool(op02.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
        "branch_status_mismatch_refs": _dedupe_clean_refs(list(op02.get("branch_status_mismatch_refs") or []), max_length=320),
        "branch_status_mismatch_ref_count": len(_dedupe_clean_refs(list(op02.get("branch_status_mismatch_refs") or []), max_length=320)),
        "rdb_status_ref": status_ref,
        "result_manual_decision_lane_status_ref": status_ref,
        "rdb_allowed_status_refs": list(P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS),
        "rdb_allowed_status_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS),
        "rdb_op03_branch_priority_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP03_BRANCH_PRIORITY_REFS),
        "rdb_op03_branch_priority_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP03_BRANCH_PRIORITY_REFS),
        "rdb_op03_selected_priority_ref": priority_ref,
        "decision_lane_ref": lane_ref,
        "selected_next_required_step_ref": selected_next_step,
        "exactly_one_rdb_result_branch": sum(1 for value in branch_flags.values() if value is True) == 1,
        "manual_decision_required_without_auto_execution": True,
        "manual_decision_lane_resolved": True,
        "manual_decision_lane_resolved_bodyfree": True,
        "manual_decision_lane_resolver_only_no_materialization": True,
        **branch_flags,
        "selected_next_stage_candidate_not_executed": True,
        "dhr_op05_manual_handoff_candidate_present": branch_flags["rdb_op03_confirmed_dhr_op05_manual_handoff_candidate"],
        "retry_or_start_candidate_present": branch_flags["rdb_op03_not_confirmed_retry_or_start_decision_required"],
        "external_claim_wait_candidate_present": branch_flags["rdb_op03_waiting_external_claim_required"],
        "repair_candidate_present": bool(branch_flags["rdb_op03_repair_required_after_dhr_op04_result"] or branch_flags["rdb_op03_repair_required_for_mrb08_branch_status_mismatch"]),
        "unresolved_manual_hold_candidate_present": bool(branch_flags["rdb_op03_incomplete_unresolved_manual_hold"] or branch_flags["rdb_op03_waiting_for_mrb08_result_closure"]),
        "blocked_candidate_present": branch_flags["rdb_op03_blocked_bodyfree_leak_promotion_or_autorun"],
        "rdb_op03_reason_refs": reasons,
        "rdb_op03_reason_ref_count": len(reasons),
        "rdb_op03_blocker_refs": blockers,
        "rdb_op03_blocker_ref_count": len(blockers),
        "rdb_op03_does_not_materialize_branch_specific_manual_decision": True,
        "rdb_op03_does_not_materialize_next_stage_candidate_envelope": True,
        "rdb_op03_does_not_recall_dhr_op04": True,
        "rdb_op03_does_not_call_dhr_op05": True,
        "rdb_op03_does_not_call_dhr_op06": True,
        "rdb_op03_does_not_execute_dmd_r52_or_release": True,
        "rdb_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op03_does_not_materialize_p8_question_spec": True,
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RDB-OP03 DHR-OP04 result manual decision lane resolver contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP03")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MRB08_RDB_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP03_STEP_REF,
        source="P7-R54-AHR-PostMRB08-RDB-OP03",
    )
    if data.get("op02_schema_version") != P7_R54_AHR_POST_MRB08_RDB_OP02_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 OP02 schema version changed")
    if data.get("result_manual_decision_lane_status_ref") != data.get("rdb_status_ref"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 status alias changed")
    if tuple(data.get("rdb_allowed_status_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 allowed status refs changed")
    if tuple(data.get("rdb_op03_branch_priority_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP03_BRANCH_PRIORITY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 priority refs changed")
    for field, count_field in (
        ("rdb_allowed_status_refs", "rdb_allowed_status_ref_count"),
        ("rdb_op03_branch_priority_refs", "rdb_op03_branch_priority_ref_count"),
        ("branch_status_mismatch_refs", "branch_status_mismatch_ref_count"),
        ("rdb_op03_reason_refs", "rdb_op03_reason_ref_count"),
        ("rdb_op03_blocker_refs", "rdb_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP03 {count_field} changed")
    for key in (
        "exactly_one_rdb_result_branch",
        "manual_decision_required_without_auto_execution",
        "manual_decision_lane_resolved",
        "manual_decision_lane_resolved_bodyfree",
        "manual_decision_lane_resolver_only_no_materialization",
        "selected_next_stage_candidate_not_executed",
        "rdb_op03_does_not_materialize_branch_specific_manual_decision",
        "rdb_op03_does_not_materialize_next_stage_candidate_envelope",
        "rdb_op03_does_not_recall_dhr_op04",
        "rdb_op03_does_not_call_dhr_op05",
        "rdb_op03_does_not_call_dhr_op06",
        "rdb_op03_does_not_execute_dmd_r52_or_release",
        "rdb_op03_does_not_start_p5_p6_p8_p7_or_release",
        "rdb_op03_does_not_change_api_db_rn_runtime_response_key",
        "rdb_op03_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP03 required true boundary changed: {key}")
    if data.get("p8_question_substitution_allowed") is not False or data.get("question_text_materialized") is not False:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 P8 question boundary changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 next step changed")
    status_ref = data.get("rdb_status_ref")
    if status_ref not in P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 unknown RDB status")
    branch_flags = [
        data.get("rdb_op03_confirmed_dhr_op05_manual_handoff_candidate") is True,
        data.get("rdb_op03_not_confirmed_retry_or_start_decision_required") is True,
        data.get("rdb_op03_waiting_external_claim_required") is True,
        data.get("rdb_op03_repair_required_after_dhr_op04_result") is True,
        data.get("rdb_op03_incomplete_unresolved_manual_hold") is True,
        data.get("rdb_op03_waiting_for_mrb08_result_closure") is True,
        data.get("rdb_op03_blocked_bodyfree_leak_promotion_or_autorun") is True,
        data.get("rdb_op03_repair_required_for_mrb08_branch_status_mismatch") is True,
    ]
    if sum(branch_flags) != 1:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 exactly one RDB branch must be true")
    expected_lane_ref, expected_next_step, expected_priority_ref, _reason = _op03_lane_for_status_ref(str(status_ref))
    if data.get("decision_lane_ref") != expected_lane_ref:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 decision lane changed")
    if data.get("selected_next_required_step_ref") != expected_next_step:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 selected next required step changed")
    if data.get("rdb_op03_selected_priority_ref") != expected_priority_ref:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 selected priority changed")
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF:
        if data.get("dhr_op05_manual_handoff_candidate_present") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 confirmed lane must present DHR-OP05 candidate")
        if data.get("dhr_op05_called_here") is not False:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 confirmed lane must not call DHR-OP05")
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF:
        if data.get("retry_or_start_candidate_present") is not True or data.get("p8_question_substitution_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 not-confirmed lane must stay retry/start without P8 question")
    if status_ref in (
        P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
    ) and not data.get("rdb_op03_blocker_refs"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP03 hold/repair/blocked lane must carry blockers")
    return True



P7_R54_AHR_POST_MRB08_RDB_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op04_branch_specific_manual_decision_materialization.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op05_next_stage_candidate_envelope_without_execution.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:5]
)
P7_R54_AHR_POST_MRB08_RDB_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[5:]
)
P7_R54_AHR_POST_MRB08_RDB_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:6]
)
P7_R54_AHR_POST_MRB08_RDB_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[6:]
)

P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_CONFIRMED_REF: Final = (
    "rdb_op04_confirmed_dhr_op05_manual_handoff_candidate_material"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_RETRY_OR_START_REF: Final = (
    "rdb_op04_not_confirmed_retry_or_start_decision_material"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_WAIT_EXTERNAL_CLAIM_REF: Final = (
    "rdb_op04_waiting_external_bodyfree_claim_wait_material"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_REPAIR_REF: Final = (
    "rdb_op04_repair_dhr_op04_result_or_mrb08_boundary_material"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_UNRESOLVED_REF: Final = (
    "rdb_op04_manual_hold_unresolved_post_mrb08_material"
)
P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_BLOCKED_REF: Final = (
    "rdb_op04_blocked_bodyfree_leak_promotion_or_autorun_material"
)

P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF: Final = (
    "dhr_op05_manual_handoff_decision_candidate_without_call"
)
P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF: Final = (
    "retry_or_start_decision_candidate_without_p8_question"
)
P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF: Final = (
    "external_bodyfree_actual_source_claim_wait_candidate_without_raw_evidence"
)
P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF: Final = (
    "repair_result_or_mrb08_boundary_candidate_without_downstream_promotion"
)
P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF: Final = (
    "manual_hold_unresolved_post_mrb08_candidate_without_promotion"
)
P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF: Final = (
    "blocked_post_mrb08_bodyfree_leak_promotion_or_autorun_candidate"
)

P7_R54_AHR_POST_MRB08_RDB_REPAIR_DIMENSION_REFS: Final[tuple[str, ...]] = (
    "source_kind_ref",
    "actual_source_claim_origin_ref",
    "actual_source_claim_bodyfree",
    "promotion_claim",
    "dhr_op03_ready_material",
    "mrb_op08_validation_or_result_memo",
)
P7_R54_AHR_POST_MRB08_RDB_BRANCH_STATUS_MISMATCH_REPAIR_DIMENSION_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_MRB08_RDB_REPAIR_DIMENSION_REFS,
    "mrb08_branch_status_mapping_ref",
    "op06_selected_branch_or_dhr_status_ref",
)
P7_R54_AHR_POST_MRB08_RDB_UNRESOLVED_DIMENSION_REFS: Final[tuple[str, ...]] = (
    "mrb_op08_missing_or_not_closed",
    "op06_branch_missing",
    "dhr_op04_result_status_missing",
    "validation_summary_missing",
    "result_memo_missing",
)
P7_R54_AHR_POST_MRB08_RDB_BLOCKED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "bodyfree_leak_detected",
    "forbidden_payload_key_detected",
    "promotion_claim_detected",
    "autorun_or_downstream_execution_claim_detected",
)

P7_R54_AHR_POST_MRB08_RDB_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_decision_lane_ref", "op03_selected_next_required_step_ref", "op03_contract_valid", "op03_manual_decision_lane_resolved", "op03_exactly_one_rdb_result_branch",
    "mrb_selected_branch_ref", "dhr_op04_result_status_ref", "actual_source_claim_confirmed_for_downstream_handoff", "branch_status_mismatch_refs", "branch_status_mismatch_ref_count",
    "rdb_status_ref", "decision_lane_ref", "branch_specific_manual_decision_material_ref", "branch_specific_manual_decision_material_kind_ref",
    "manual_decision_materialized", "manual_decision_materialized_bodyfree", "branch_specific_materialization_complete", "manual_decision_auto_executes_downstream",
    "selected_next_stage_candidate_ref", "selected_next_stage_candidate_kind_ref", "selected_next_stage_operation_candidate_ref", "selected_next_stage_candidate_not_executed",
    "dhr_op05_manual_handoff_candidate_present", "retry_or_start_candidate_present", "external_claim_wait_candidate_present", "repair_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "confirmed_dhr_op05_manual_handoff_material_present", "retry_or_start_decision_material_present", "external_claim_wait_material_present", "repair_decision_material_present", "unresolved_manual_hold_material_present", "blocked_decision_material_present",
    "dhr_op05_candidate_operation_ref", "retry_or_start_candidate_operation_ref", "waiting_external_claim_candidate_operation_ref", "repair_candidate_operation_ref", "unresolved_candidate_operation_ref", "blocked_candidate_operation_ref",
    "repair_dimension_refs", "repair_dimension_ref_count", "unresolved_dimension_refs", "unresolved_dimension_ref_count", "blocked_boundary_refs", "blocked_boundary_ref_count",
    "branch_material_reason_refs", "branch_material_reason_ref_count", "branch_material_blocker_refs", "branch_material_blocker_ref_count",
    "op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count", "op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count", "op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count",
    "p8_question_substitution_allowed", "question_text_materialized", "raw_evidence_request_materialized_here", "body_full_packet_requested_here", "actual_review_operation_started_here", "repair_execution_started_here",
    "rdb_op04_does_not_materialize_next_stage_candidate_envelope", "rdb_op04_does_not_recall_dhr_op04", "rdb_op04_does_not_call_dhr_op05", "rdb_op04_does_not_call_dhr_op06", "rdb_op04_does_not_execute_dmd_r52_or_release", "rdb_op04_does_not_start_p5_p6_p8_p7_or_release", "rdb_op04_does_not_change_api_db_rn_runtime_response_key", "rdb_op04_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MRB08_RDB_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_decision_lane_ref", "op04_branch_specific_manual_decision_material_ref", "op04_selected_next_stage_candidate_ref", "op04_selected_next_stage_candidate_kind_ref", "op04_selected_next_stage_candidate_not_executed", "op04_contract_valid", "op04_manual_decision_materialized",
    "rdb_status_ref", "decision_lane_ref", "candidate_envelope_ref", "candidate_envelope_kind_ref", "selected_next_stage_candidate_ref", "selected_next_stage_candidate_kind_ref", "selected_next_stage_operation_candidate_ref",
    "candidate_envelope_bodyfree", "next_stage_candidate_enveloped_without_execution", "selected_next_stage_candidate_not_executed", "downstream_auto_execution_allowed",
    "dhr_op05_manual_handoff_candidate_present", "retry_or_start_candidate_present", "external_claim_wait_candidate_present", "repair_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "dhr_op05_candidate_but_builder_not_called", "retry_or_start_candidate_but_operation_not_started", "waiting_candidate_but_raw_evidence_not_requested", "repair_candidate_but_repair_not_executed", "p8_question_candidate_created",
    "next_stage_candidate_reason_refs", "next_stage_candidate_reason_ref_count", "next_stage_candidate_blocker_refs", "next_stage_candidate_blocker_ref_count",
    "op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count", "op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count", "op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count",
    "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here",
    "p8_question_design_started_here", "p8_question_implementation_started_here", "release_decision_created_here",
    "rdb_op05_does_not_recall_dhr_op04", "rdb_op05_does_not_call_dhr_op05", "rdb_op05_does_not_call_dhr_op06", "rdb_op05_does_not_execute_dmd_r52_or_release", "rdb_op05_does_not_start_p5_p6_p8_p7_or_release", "rdb_op05_does_not_change_api_db_rn_runtime_response_key", "rdb_op05_does_not_materialize_p8_question_spec",
    "p8_question_substitution_allowed", "question_text_materialized", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op03_contract_valid(op03: Mapping[str, Any] | None) -> bool:
    if not isinstance(op03, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract(op03) is True
    except ValueError:
        return False


def _candidate_info_for_rdb_status(status_ref: str) -> dict[str, Any]:
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF:
        return {
            "material_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_CONFIRMED_REF,
            "material_kind": P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_CONFIRMED_DHR_OP05_HANDOFF_CANDIDATE_REF,
            "candidate_ref": P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
            "candidate_kind": P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF,
            "operation_ref": dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF,
            "reason": "dhr_op04_confirmed_bodyfree_read_only_as_dhr_op05_manual_handoff_candidate",
            "dhr": True,
            "retry": False,
            "waiting": False,
            "repair": False,
            "unresolved": False,
            "blocked": False,
            "repair_dims": (),
            "unresolved_dims": (),
            "blocked_refs": (),
        }
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF:
        return {
            "material_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_RETRY_OR_START_REF,
            "material_kind": P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_RETRY_OR_START_REF,
            "candidate_ref": P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
            "candidate_kind": P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF,
            "operation_ref": "actual_local_only_human_review_operation_retry_or_start_decision",
            "reason": "dhr_op04_not_confirmed_requires_retry_or_start_decision_without_p8_question",
            "dhr": False,
            "retry": True,
            "waiting": False,
            "repair": False,
            "unresolved": False,
            "blocked": False,
            "repair_dims": (),
            "unresolved_dims": (),
            "blocked_refs": (),
        }
    if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF:
        return {
            "material_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_WAIT_EXTERNAL_CLAIM_REF,
            "material_kind": P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_EXTERNAL_CLAIM_REF,
            "candidate_ref": P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            "candidate_kind": P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF,
            "operation_ref": "external_bodyfree_actual_source_claim_wait",
            "reason": "dhr_op04_waiting_external_claim_requires_bodyfree_claim_wait_without_raw_evidence",
            "dhr": False,
            "retry": False,
            "waiting": True,
            "repair": False,
            "unresolved": False,
            "blocked": False,
            "repair_dims": (),
            "unresolved_dims": (),
            "blocked_refs": (),
        }
    if status_ref in (
        P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
    ):
        dims = (
            P7_R54_AHR_POST_MRB08_RDB_BRANCH_STATUS_MISMATCH_REPAIR_DIMENSION_REFS
            if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF
            else P7_R54_AHR_POST_MRB08_RDB_REPAIR_DIMENSION_REFS
        )
        return {
            "material_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_REPAIR_REF,
            "material_kind": (
                P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_BRANCH_STATUS_MISMATCH_REF
                if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF
                else P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_RESULT_OR_MRB08_REF
            ),
            "candidate_ref": P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            "candidate_kind": P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF,
            "operation_ref": "repair_dhr_op04_result_or_mrb08_boundary_decision",
            "reason": "dhr_op04_or_mrb08_boundary_repair_materialized_without_repair_execution",
            "dhr": False,
            "retry": False,
            "waiting": False,
            "repair": True,
            "unresolved": False,
            "blocked": False,
            "repair_dims": dims,
            "unresolved_dims": (),
            "blocked_refs": (),
        }
    if status_ref in (
        P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
    ):
        return {
            "material_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_UNRESOLVED_REF,
            "material_kind": (
                P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_MRB08_CLOSURE_REF
                if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF
                else P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF
            ),
            "candidate_ref": (
                P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_MRB08_CLOSURE_REF
                if status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF
                else P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF
            ),
            "candidate_kind": P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
            "operation_ref": "manual_hold_unresolved_post_mrb08_decision",
            "reason": "mrb08_or_dhr_op04_result_refs_incomplete_manual_hold_without_promotion",
            "dhr": False,
            "retry": False,
            "waiting": False,
            "repair": False,
            "unresolved": True,
            "blocked": False,
            "repair_dims": (),
            "unresolved_dims": P7_R54_AHR_POST_MRB08_RDB_UNRESOLVED_DIMENSION_REFS,
            "blocked_refs": (),
        }
    return {
        "material_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_BLOCKED_REF,
        "material_kind": P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
        "candidate_ref": P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
        "candidate_kind": P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
        "operation_ref": "blocked_post_mrb08_bodyfree_leak_promotion_or_autorun",
        "reason": "bodyfree_leak_promotion_or_autorun_claim_blocks_result_manual_decision",
        "dhr": False,
        "retry": False,
        "waiting": False,
        "repair": False,
        "unresolved": False,
        "blocked": True,
        "repair_dims": (),
        "unresolved_dims": (),
        "blocked_refs": P7_R54_AHR_POST_MRB08_RDB_BLOCKED_BOUNDARY_REFS,
    }


def _op03_to_op04_status(op03: Mapping[str, Any], *, op03_contract_valid: bool) -> str:
    forbidden_paths = _scan_forbidden_payload_key_paths(op03, path="op03")
    body_like_paths = _scan_body_like_value_paths(op03, path="op03")
    promotion_claims = _scan_promotion_claim_refs(op03, path="op03")
    if forbidden_paths or body_like_paths or promotion_claims:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    if not op03_contract_valid:
        return P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF
    status_ref = _clean_ref(op03.get("rdb_status_ref"), default="missing", max_length=320)
    if status_ref in P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS:
        return status_ref
    return P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF


def _op04_contract_valid(op04: Mapping[str, Any] | None) -> bool:
    if not isinstance(op04, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(op04) is True
    except ValueError:
        return False


def build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization(
    *,
    dhr_op04_result_manual_decision_lane_resolver: Mapping[str, Any] | None = None,
    mrb_branch_dhr_status_consistency_check: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP04 branch-specific manual decision material without downstream execution."""

    op03 = (
        dhr_op04_result_manual_decision_lane_resolver
        if isinstance(dhr_op04_result_manual_decision_lane_resolver, Mapping)
        else build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
            mrb_branch_dhr_status_consistency_check=mrb_branch_dhr_status_consistency_check,
            mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
            mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
            review_session_id=review_session_id,
        )
    )
    op03_valid = _op03_contract_valid(op03)
    forbidden_paths = _scan_forbidden_payload_key_paths(op03, path="op03")
    body_like_paths = _scan_body_like_value_paths(op03, path="op03")
    promotion_claims = _scan_promotion_claim_refs(op03, path="op03")
    status_ref = _op03_to_op04_status(op03, op03_contract_valid=op03_valid)
    info = _candidate_info_for_rdb_status(status_ref)
    repair_dims = list(info["repair_dims"])
    unresolved_dims = list(info["unresolved_dims"])
    blocked_refs = list(info["blocked_refs"])
    blockers = _dedupe_clean_refs(
        [*list(op03.get("rdb_op03_blocker_refs") or []), *forbidden_paths, *body_like_paths, *promotion_claims],
        max_length=340,
    )
    if not op03_valid and "rdb_op03_contract_invalid_before_op04_materialization" not in blockers:
        blockers.append("rdb_op03_contract_invalid_before_op04_materialization")
    if info["blocked"] and not blockers:
        blockers.append("bodyfree_leak_promotion_or_autorun_blocked_before_op04")
    if info["repair"] and status_ref == P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF:
        blockers.extend(_dedupe_clean_refs(list(op03.get("branch_status_mismatch_refs") or []), max_length=340))
        blockers = _dedupe_clean_refs(blockers, max_length=340)
    reasons = _dedupe_clean_refs([info["reason"], *list(op03.get("rdb_op03_reason_refs") or [])], max_length=340)
    session_id = _safe_review_session_id(review_session_id or op03.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": _clean_ref(op03.get("schema_version"), default="rdb_op03_schema_missing", max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id"), default="rdb_op03_material_missing", max_length=260),
        "op03_status_ref": _clean_ref(op03.get("rdb_status_ref"), default="rdb_op03_status_missing", max_length=320),
        "op03_decision_lane_ref": _clean_ref(op03.get("decision_lane_ref"), default="rdb_op03_decision_lane_missing", max_length=320),
        "op03_selected_next_required_step_ref": _clean_ref(op03.get("selected_next_required_step_ref"), default="rdb_op03_next_step_missing", max_length=320),
        "op03_contract_valid": op03_valid,
        "op03_manual_decision_lane_resolved": bool(op03.get("manual_decision_lane_resolved") is True),
        "op03_exactly_one_rdb_result_branch": bool(op03.get("exactly_one_rdb_result_branch") is True),
        "mrb_selected_branch_ref": _clean_ref(op03.get("mrb_selected_branch_ref"), default="mrb_selected_branch_missing", max_length=320),
        "dhr_op04_result_status_ref": _clean_ref(op03.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=320),
        "actual_source_claim_confirmed_for_downstream_handoff": bool(op03.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
        "branch_status_mismatch_refs": _dedupe_clean_refs(list(op03.get("branch_status_mismatch_refs") or []), max_length=340),
        "branch_status_mismatch_ref_count": len(_dedupe_clean_refs(list(op03.get("branch_status_mismatch_refs") or []), max_length=340)),
        "rdb_status_ref": status_ref,
        "decision_lane_ref": str(info["material_kind"]),
        "branch_specific_manual_decision_material_ref": str(info["material_ref"]),
        "branch_specific_manual_decision_material_kind_ref": str(info["material_kind"]),
        "manual_decision_materialized": True,
        "manual_decision_materialized_bodyfree": True,
        "branch_specific_materialization_complete": True,
        "manual_decision_auto_executes_downstream": False,
        "selected_next_stage_candidate_ref": str(info["candidate_ref"]),
        "selected_next_stage_candidate_kind_ref": str(info["candidate_kind"]),
        "selected_next_stage_operation_candidate_ref": str(info["operation_ref"]),
        "selected_next_stage_candidate_not_executed": True,
        "dhr_op05_manual_handoff_candidate_present": bool(info["dhr"]),
        "retry_or_start_candidate_present": bool(info["retry"]),
        "external_claim_wait_candidate_present": bool(info["waiting"]),
        "repair_candidate_present": bool(info["repair"]),
        "unresolved_manual_hold_candidate_present": bool(info["unresolved"]),
        "blocked_candidate_present": bool(info["blocked"]),
        "confirmed_dhr_op05_manual_handoff_material_present": bool(info["dhr"]),
        "retry_or_start_decision_material_present": bool(info["retry"]),
        "external_claim_wait_material_present": bool(info["waiting"]),
        "repair_decision_material_present": bool(info["repair"]),
        "unresolved_manual_hold_material_present": bool(info["unresolved"]),
        "blocked_decision_material_present": bool(info["blocked"]),
        "dhr_op05_candidate_operation_ref": dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF if info["dhr"] else "none",
        "retry_or_start_candidate_operation_ref": str(info["operation_ref"]) if info["retry"] else "none",
        "waiting_external_claim_candidate_operation_ref": str(info["operation_ref"]) if info["waiting"] else "none",
        "repair_candidate_operation_ref": str(info["operation_ref"]) if info["repair"] else "none",
        "unresolved_candidate_operation_ref": str(info["operation_ref"]) if info["unresolved"] else "none",
        "blocked_candidate_operation_ref": str(info["operation_ref"]) if info["blocked"] else "none",
        "repair_dimension_refs": repair_dims,
        "repair_dimension_ref_count": len(repair_dims),
        "unresolved_dimension_refs": unresolved_dims,
        "unresolved_dimension_ref_count": len(unresolved_dims),
        "blocked_boundary_refs": blocked_refs,
        "blocked_boundary_ref_count": len(blocked_refs),
        "branch_material_reason_refs": reasons,
        "branch_material_reason_ref_count": len(reasons),
        "branch_material_blocker_refs": blockers,
        "branch_material_blocker_ref_count": len(blockers),
        "op03_input_forbidden_payload_key_path_refs": _dedupe_clean_refs(forbidden_paths, max_length=340),
        "op03_input_forbidden_payload_key_path_count": len(_dedupe_clean_refs(forbidden_paths, max_length=340)),
        "op03_input_body_like_value_path_refs": _dedupe_clean_refs(body_like_paths, max_length=340),
        "op03_input_body_like_value_path_count": len(_dedupe_clean_refs(body_like_paths, max_length=340)),
        "op03_input_promotion_claim_refs": _dedupe_clean_refs(promotion_claims, max_length=340),
        "op03_input_promotion_claim_ref_count": len(_dedupe_clean_refs(promotion_claims, max_length=340)),
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "raw_evidence_request_materialized_here": False,
        "body_full_packet_requested_here": False,
        "actual_review_operation_started_here": False,
        "repair_execution_started_here": False,
        "rdb_op04_does_not_materialize_next_stage_candidate_envelope": True,
        "rdb_op04_does_not_recall_dhr_op04": True,
        "rdb_op04_does_not_call_dhr_op05": True,
        "rdb_op04_does_not_call_dhr_op06": True,
        "rdb_op04_does_not_execute_dmd_r52_or_release": True,
        "rdb_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op04_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RDB-OP04 branch-specific manual decision materialization contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP04")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MRB08_RDB_OP04_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF,
        source="P7-R54-AHR-PostMRB08-RDB-OP04",
    )
    for key in (
        "manual_decision_materialized",
        "manual_decision_materialized_bodyfree",
        "branch_specific_materialization_complete",
        "selected_next_stage_candidate_not_executed",
        "rdb_op04_does_not_materialize_next_stage_candidate_envelope",
        "rdb_op04_does_not_recall_dhr_op04",
        "rdb_op04_does_not_call_dhr_op05",
        "rdb_op04_does_not_call_dhr_op06",
        "rdb_op04_does_not_execute_dmd_r52_or_release",
        "rdb_op04_does_not_start_p5_p6_p8_p7_or_release",
        "rdb_op04_does_not_change_api_db_rn_runtime_response_key",
        "rdb_op04_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP04 required true boundary changed: {key}")
    for key in (
        "manual_decision_auto_executes_downstream",
        "p8_question_substitution_allowed",
        "question_text_materialized",
        "raw_evidence_request_materialized_here",
        "body_full_packet_requested_here",
        "actual_review_operation_started_here",
        "repair_execution_started_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP04 required false execution boundary changed: {key}")
    for field, count_field in (
        ("branch_status_mismatch_refs", "branch_status_mismatch_ref_count"),
        ("repair_dimension_refs", "repair_dimension_ref_count"),
        ("unresolved_dimension_refs", "unresolved_dimension_ref_count"),
        ("blocked_boundary_refs", "blocked_boundary_ref_count"),
        ("branch_material_reason_refs", "branch_material_reason_ref_count"),
        ("branch_material_blocker_refs", "branch_material_blocker_ref_count"),
        ("op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count"),
        ("op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count"),
        ("op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP04 {count_field} changed")
    if data.get("rdb_status_ref") not in P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 status ref is not allowed")
    info = _candidate_info_for_rdb_status(str(data.get("rdb_status_ref")))
    if data.get("branch_specific_manual_decision_material_ref") != info["material_ref"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 material ref changed")
    if data.get("branch_specific_manual_decision_material_kind_ref") != info["material_kind"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 material kind changed")
    if data.get("decision_lane_ref") != info["material_kind"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 decision lane changed")
    if data.get("selected_next_stage_candidate_ref") != info["candidate_ref"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 next-stage candidate ref changed")
    if data.get("selected_next_stage_candidate_kind_ref") != info["candidate_kind"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 candidate kind changed")
    if data.get("selected_next_stage_operation_candidate_ref") != info["operation_ref"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 operation candidate ref changed")
    candidate_flags = [
        data.get("dhr_op05_manual_handoff_candidate_present") is True,
        data.get("retry_or_start_candidate_present") is True,
        data.get("external_claim_wait_candidate_present") is True,
        data.get("repair_candidate_present") is True,
        data.get("unresolved_manual_hold_candidate_present") is True,
        data.get("blocked_candidate_present") is True,
    ]
    if sum(candidate_flags) != 1:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 exactly one candidate branch must be present")
    if data.get("dhr_op05_manual_handoff_candidate_present") is not bool(info["dhr"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 DHR candidate flag changed")
    if data.get("retry_or_start_candidate_present") is not bool(info["retry"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 retry candidate flag changed")
    if data.get("external_claim_wait_candidate_present") is not bool(info["waiting"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 wait candidate flag changed")
    if data.get("repair_candidate_present") is not bool(info["repair"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 repair candidate flag changed")
    if data.get("unresolved_manual_hold_candidate_present") is not bool(info["unresolved"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 unresolved candidate flag changed")
    if data.get("blocked_candidate_present") is not bool(info["blocked"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 blocked candidate flag changed")
    if data.get("confirmed_dhr_op05_manual_handoff_material_present") is not bool(info["dhr"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 confirmed material flag changed")
    if data.get("retry_or_start_decision_material_present") is not bool(info["retry"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 retry material flag changed")
    if data.get("external_claim_wait_material_present") is not bool(info["waiting"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 waiting material flag changed")
    if data.get("repair_decision_material_present") is not bool(info["repair"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 repair material flag changed")
    if data.get("unresolved_manual_hold_material_present") is not bool(info["unresolved"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 unresolved material flag changed")
    if data.get("blocked_decision_material_present") is not bool(info["blocked"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 blocked material flag changed")
    if data.get("dhr_op05_candidate_operation_ref") != (dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF if info["dhr"] else "none"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 DHR-OP05 operation candidate changed")
    if info["dhr"]:
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 confirmed candidate requires confirmed source claim")
        if data.get("dhr_op05_called_here") is not False:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 confirmed candidate must not call DHR-OP05")
    if info["retry"] and data.get("p8_question_substitution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 retry material must not substitute P8 question")
    if info["waiting"]:
        if data.get("raw_evidence_request_materialized_here") is not False or data.get("body_full_packet_requested_here") is not False:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 waiting material must not request raw evidence")
    if info["repair"] and not data.get("repair_dimension_refs"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 repair material requires repair dimensions")
    if info["unresolved"] and not data.get("unresolved_dimension_refs"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 unresolved material requires unresolved dimensions")
    if info["blocked"] and not data.get("branch_material_blocker_refs"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 blocked material requires blockers")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 not-claimed refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP04_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP04 next step changed")
    return True


def build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution(
    *,
    branch_specific_manual_decision_materialization: Mapping[str, Any] | None = None,
    dhr_op04_result_manual_decision_lane_resolver: Mapping[str, Any] | None = None,
    mrb_branch_dhr_status_consistency_check: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP05 next-stage candidate envelope without executing that candidate."""

    op04 = (
        branch_specific_manual_decision_materialization
        if isinstance(branch_specific_manual_decision_materialization, Mapping)
        else build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization(
            dhr_op04_result_manual_decision_lane_resolver=dhr_op04_result_manual_decision_lane_resolver,
            mrb_branch_dhr_status_consistency_check=mrb_branch_dhr_status_consistency_check,
            mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
            mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
            review_session_id=review_session_id,
        )
    )
    op04_valid = _op04_contract_valid(op04)
    forbidden_paths = _scan_forbidden_payload_key_paths(op04, path="op04")
    body_like_paths = _scan_body_like_value_paths(op04, path="op04")
    promotion_claims = _scan_promotion_claim_refs(op04, path="op04")
    status_ref = _clean_ref(op04.get("rdb_status_ref"), default=P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF, max_length=320)
    if forbidden_paths or body_like_paths or promotion_claims:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    elif not op04_valid or status_ref not in P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF
    info = _candidate_info_for_rdb_status(status_ref)
    blockers = _dedupe_clean_refs(
        [*list(op04.get("branch_material_blocker_refs") or []), *forbidden_paths, *body_like_paths, *promotion_claims],
        max_length=340,
    )
    if not op04_valid and "rdb_op04_contract_invalid_before_candidate_envelope" not in blockers:
        blockers.append("rdb_op04_contract_invalid_before_candidate_envelope")
    if info["blocked"] and not blockers:
        blockers.append("bodyfree_leak_promotion_or_autorun_blocked_before_op05")
    reasons = _dedupe_clean_refs([info["reason"], *list(op04.get("branch_material_reason_refs") or [])], max_length=340)
    session_id = _safe_review_session_id(review_session_id or op04.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": _clean_ref(op04.get("schema_version"), default="rdb_op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id"), default="rdb_op04_material_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("rdb_status_ref"), default="rdb_op04_status_missing", max_length=320),
        "op04_decision_lane_ref": _clean_ref(op04.get("decision_lane_ref"), default="rdb_op04_decision_lane_missing", max_length=320),
        "op04_branch_specific_manual_decision_material_ref": _clean_ref(op04.get("branch_specific_manual_decision_material_ref"), default="rdb_op04_material_ref_missing", max_length=320),
        "op04_selected_next_stage_candidate_ref": _clean_ref(op04.get("selected_next_stage_candidate_ref"), default="rdb_op04_candidate_ref_missing", max_length=320),
        "op04_selected_next_stage_candidate_kind_ref": _clean_ref(op04.get("selected_next_stage_candidate_kind_ref"), default="rdb_op04_candidate_kind_missing", max_length=320),
        "op04_selected_next_stage_candidate_not_executed": bool(op04.get("selected_next_stage_candidate_not_executed") is True),
        "op04_contract_valid": op04_valid,
        "op04_manual_decision_materialized": bool(op04.get("manual_decision_materialized") is True),
        "rdb_status_ref": status_ref,
        "decision_lane_ref": str(info["material_kind"]),
        "candidate_envelope_ref": f"rdb_op05_envelope_for_{info['candidate_ref']}",
        "candidate_envelope_kind_ref": "next_stage_candidate_envelope_without_execution",
        "selected_next_stage_candidate_ref": str(info["candidate_ref"]),
        "selected_next_stage_candidate_kind_ref": str(info["candidate_kind"]),
        "selected_next_stage_operation_candidate_ref": str(info["operation_ref"]),
        "candidate_envelope_bodyfree": True,
        "next_stage_candidate_enveloped_without_execution": True,
        "selected_next_stage_candidate_not_executed": True,
        "downstream_auto_execution_allowed": False,
        "dhr_op05_manual_handoff_candidate_present": bool(info["dhr"]),
        "retry_or_start_candidate_present": bool(info["retry"]),
        "external_claim_wait_candidate_present": bool(info["waiting"]),
        "repair_candidate_present": bool(info["repair"]),
        "unresolved_manual_hold_candidate_present": bool(info["unresolved"]),
        "blocked_candidate_present": bool(info["blocked"]),
        "dhr_op05_candidate_but_builder_not_called": bool(info["dhr"]),
        "retry_or_start_candidate_but_operation_not_started": bool(info["retry"]),
        "waiting_candidate_but_raw_evidence_not_requested": bool(info["waiting"]),
        "repair_candidate_but_repair_not_executed": bool(info["repair"]),
        "p8_question_candidate_created": False,
        "next_stage_candidate_reason_refs": reasons,
        "next_stage_candidate_reason_ref_count": len(reasons),
        "next_stage_candidate_blocker_refs": blockers,
        "next_stage_candidate_blocker_ref_count": len(blockers),
        "op04_input_forbidden_payload_key_path_refs": _dedupe_clean_refs(forbidden_paths, max_length=340),
        "op04_input_forbidden_payload_key_path_count": len(_dedupe_clean_refs(forbidden_paths, max_length=340)),
        "op04_input_body_like_value_path_refs": _dedupe_clean_refs(body_like_paths, max_length=340),
        "op04_input_body_like_value_path_count": len(_dedupe_clean_refs(body_like_paths, max_length=340)),
        "op04_input_promotion_claim_refs": _dedupe_clean_refs(promotion_claims, max_length=340),
        "op04_input_promotion_claim_ref_count": len(_dedupe_clean_refs(promotion_claims, max_length=340)),
        "dhr_op05_builder_called_here": False,
        "dhr_op06_builder_called_here": False,
        "dmd_builder_called_here": False,
        "r52_actual_execution_called_here": False,
        "actual_local_human_review_operation_started_here": False,
        "raw_evidence_request_created_here": False,
        "repair_executed_here": False,
        "p8_question_design_started_here": False,
        "p8_question_implementation_started_here": False,
        "release_decision_created_here": False,
        "rdb_op05_does_not_recall_dhr_op04": True,
        "rdb_op05_does_not_call_dhr_op05": True,
        "rdb_op05_does_not_call_dhr_op06": True,
        "rdb_op05_does_not_execute_dmd_r52_or_release": True,
        "rdb_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op05_does_not_materialize_p8_question_spec": True,
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RDB-OP05 next-stage candidate envelope without execution contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP05")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MRB08_RDB_OP05_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF,
        source="P7-R54-AHR-PostMRB08-RDB-OP05",
    )
    for key in (
        "candidate_envelope_bodyfree",
        "next_stage_candidate_enveloped_without_execution",
        "selected_next_stage_candidate_not_executed",
        "rdb_op05_does_not_recall_dhr_op04",
        "rdb_op05_does_not_call_dhr_op05",
        "rdb_op05_does_not_call_dhr_op06",
        "rdb_op05_does_not_execute_dmd_r52_or_release",
        "rdb_op05_does_not_start_p5_p6_p8_p7_or_release",
        "rdb_op05_does_not_change_api_db_rn_runtime_response_key",
        "rdb_op05_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP05 required true boundary changed: {key}")
    for key in (
        "downstream_auto_execution_allowed",
        "p8_question_candidate_created",
        "dhr_op05_builder_called_here",
        "dhr_op06_builder_called_here",
        "dmd_builder_called_here",
        "r52_actual_execution_called_here",
        "actual_local_human_review_operation_started_here",
        "raw_evidence_request_created_here",
        "repair_executed_here",
        "p8_question_design_started_here",
        "p8_question_implementation_started_here",
        "release_decision_created_here",
        "p8_question_substitution_allowed",
        "question_text_materialized",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP05 required false execution boundary changed: {key}")
    for field, count_field in (
        ("next_stage_candidate_reason_refs", "next_stage_candidate_reason_ref_count"),
        ("next_stage_candidate_blocker_refs", "next_stage_candidate_blocker_ref_count"),
        ("op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count"),
        ("op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count"),
        ("op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP05 {count_field} changed")
    status_ref = data.get("rdb_status_ref")
    if status_ref not in P7_R54_AHR_POST_MRB08_RDB_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 status ref is not allowed")
    info = _candidate_info_for_rdb_status(str(status_ref))
    if data.get("decision_lane_ref") != info["material_kind"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 decision lane changed")
    if data.get("selected_next_stage_candidate_ref") != info["candidate_ref"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 candidate ref changed")
    if data.get("selected_next_stage_candidate_kind_ref") != info["candidate_kind"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 candidate kind changed")
    if data.get("selected_next_stage_operation_candidate_ref") != info["operation_ref"]:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 operation candidate ref changed")
    if data.get("candidate_envelope_kind_ref") != "next_stage_candidate_envelope_without_execution":
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 envelope kind changed")
    if not str(data.get("candidate_envelope_ref", "")).startswith("rdb_op05_envelope_for_"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 envelope ref changed")
    candidate_flags = [
        data.get("dhr_op05_manual_handoff_candidate_present") is True,
        data.get("retry_or_start_candidate_present") is True,
        data.get("external_claim_wait_candidate_present") is True,
        data.get("repair_candidate_present") is True,
        data.get("unresolved_manual_hold_candidate_present") is True,
        data.get("blocked_candidate_present") is True,
    ]
    if sum(candidate_flags) != 1:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 exactly one candidate branch must be present")
    if data.get("dhr_op05_manual_handoff_candidate_present") is not bool(info["dhr"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 DHR candidate flag changed")
    if data.get("retry_or_start_candidate_present") is not bool(info["retry"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 retry candidate flag changed")
    if data.get("external_claim_wait_candidate_present") is not bool(info["waiting"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 wait candidate flag changed")
    if data.get("repair_candidate_present") is not bool(info["repair"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 repair candidate flag changed")
    if data.get("unresolved_manual_hold_candidate_present") is not bool(info["unresolved"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 unresolved candidate flag changed")
    if data.get("blocked_candidate_present") is not bool(info["blocked"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 blocked candidate flag changed")
    if data.get("dhr_op05_candidate_but_builder_not_called") is not bool(info["dhr"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 DHR builder-not-called flag changed")
    if data.get("retry_or_start_candidate_but_operation_not_started") is not bool(info["retry"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 retry operation-not-started flag changed")
    if data.get("waiting_candidate_but_raw_evidence_not_requested") is not bool(info["waiting"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 waiting raw-evidence flag changed")
    if data.get("repair_candidate_but_repair_not_executed") is not bool(info["repair"]):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 repair-not-executed flag changed")
    if info["dhr"] and data.get("dhr_op05_called_here") is not False:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 DHR-OP05 candidate must not call DHR-OP05")
    if info["blocked"] and not data.get("next_stage_candidate_blocker_refs"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 blocked candidate requires blockers")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 not-claimed refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP05_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP05 next step changed")
    return True


# Full-title aliases for adjacent R54-AHR tests/helpers.
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08 = (
    build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op01_mrb_op08_result_memo_closure_intake = (
    build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op01_mrb_op08_result_memo_closure_intake_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check = (
    build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op03_dhr_op04_result_manual_decision_lane_resolver = (
    build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract
)

build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_branch_specific_manual_decision_materialization = (
    build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_branch_specific_manual_decision_materialization_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op05_next_stage_candidate_envelope_without_execution = (
    build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op05_next_stage_candidate_envelope_without_execution_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract
)


P7_R54_AHR_POST_MRB08_RDB_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op06_bodyfree_no_touch_no_promotion_guard.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op07_selected_regression_compileall_validation_plan.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:7]
P7_R54_AHR_POST_MRB08_RDB_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[7:]
P7_R54_AHR_POST_MRB08_RDB_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[:8]
P7_R54_AHR_POST_MRB08_RDB_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_MRB08_RDB_STEP_REFS[8:]

P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_PASSED_READY_FOR_OP07_REF: Final = "RDB_OP06_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_PASSED_READY_FOR_OP07"
P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = "RDB_OP06_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_REPAIR_REQUIRED_FOR_OP05_ENVELOPE_REF: Final = "RDB_OP06_REPAIR_REQUIRED_FOR_OP05_CANDIDATE_ENVELOPE"
P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_REF: Final = P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
P7_R54_AHR_POST_MRB08_RDB_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_PASSED_READY_FOR_OP07_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_REPAIR_REQUIRED_FOR_OP05_ENVELOPE_REF,
)
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF: Final = "RDB_OP07_SELECTED_REGRESSION_COMPILEALL_PLAN_READY_FOR_OP08"
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_WAITING_FOR_OP06_GUARD_REF: Final = "RDB_OP07_WAITING_FOR_RDB_OP06_GUARD_PASS"
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = "RDB_OP07_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_CHANGED_FILE_SCOPE_REF: Final = "RDB_OP07_BLOCKED_CHANGED_FILE_SCOPE_OR_P8_TOUCH"
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_PLAN_RECORDED_READY_FOR_OP08_REF: Final = P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_CHANGED_FILE_TOUCH_REF: Final = P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_CHANGED_FILE_SCOPE_REF
P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_REPAIR_OP06_GUARD_REQUIRED_REF: Final = "RDB_OP07_REPAIR_RDB_OP06_GUARD_REQUIRED"
P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_WAITING_FOR_OP06_GUARD_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_CHANGED_FILE_SCOPE_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_REPAIR_OP06_GUARD_REQUIRED_REF,
)

P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_op01_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_op03_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_op05_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_op07_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_result_20260705.py",
)
P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_CHANGED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_op01_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_op03_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_op05_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_op07_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_result_20260705.py",
    "tests/R54_AHR_PostMRB08_DHROP04ResultManualDecision_RDB_OP00_OP08_Result_20260705.md",
    "tests/R54_AHR_PostMRB08_DHROP04ResultManualDecision_RDB_OP00_OP07_Result_20260705.md",
)
P7_R54_AHR_POST_MRB08_RDB_OP07_DEFAULT_CHANGED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_op07_20260705.py",
    "tests/R54_AHR_PostMRB08_DHROP04ResultManualDecision_RDB_OP00_OP07_Result_20260705.md",
)
P7_R54_AHR_POST_MRB08_RDB_OP07_BLOCKED_CHANGED_FILE_TOKEN_REFS: Final[tuple[str, ...]] = (
    "/Cocolon/", "Cocolon/", "/api/", "/db/", "database", "schema.sql", "migration",
    "response_key", "runtime_generation", "runtime_prompt", "question_route", "question_schema",
    "question_trigger", "question_answer_storage", "p8_question",
)

P7_R54_AHR_POST_MRB08_RDB_OP06_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
)
P7_R54_AHR_POST_MRB08_RDB_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_MRB08_RDB_OP06_BASE_FIELD_REFS,
    "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_decision_lane_ref", "op05_candidate_envelope_ref",
    "op05_selected_next_stage_candidate_ref", "op05_selected_next_stage_candidate_kind_ref", "op05_selected_next_stage_candidate_not_executed", "op05_contract_valid",
    "rdb_status_ref", "decision_lane_ref", "selected_next_stage_candidate_ref", "selected_next_stage_candidate_kind_ref", "selected_next_stage_operation_candidate_ref",
    "rdb_op06_status_ref", "bodyfree_no_touch_no_promotion_guard_status_ref", "rdb_op06_allowed_status_refs", "rdb_op06_allowed_status_ref_count",
    "rdb_op06_guard_checked", "body_free_guard_checked", "no_touch_guard_checked", "no_promotion_guard_checked", "no_auto_execution_guard_checked",
    "guard_checked_bodyfree", "guard_checked_no_touch", "guard_checked_no_promotion", "guard_checked_no_auto_execution",
    "op05_public_contract_false", "op05_no_touch_contract_false", "op05_body_free_markers_false", "op05_body_free_true", "op05_selected_next_stage_candidate_not_executed_true", "op05_downstream_auto_execution_false",
    "rdb_bodyfree_guard_passed", "rdb_no_touch_guard_passed", "rdb_no_promotion_guard_passed", "rdb_no_auto_execution_guard_passed", "rdb_public_contract_guard_passed", "rdb_candidate_not_executed_guard_passed", "rdb_op06_ready_for_rdb_op07", "rdb_op06_blocked_bodyfree_leak_promotion_or_autorun", "rdb_op06_repair_required_for_op05_envelope",
    "forbidden_payload_key_path_refs", "forbidden_payload_key_path_count", "body_like_value_path_refs", "body_like_value_path_count", "promotion_claim_refs", "promotion_claim_ref_count",
    "true_public_contract_refs", "true_public_contract_ref_count", "true_no_touch_contract_refs", "true_no_touch_contract_ref_count", "true_body_free_marker_refs", "true_body_free_marker_ref_count", "true_not_claimed_boundary_refs", "true_not_claimed_boundary_ref_count", "required_false_flag_violation_refs", "required_false_flag_violation_ref_count", "execution_flag_violation_refs", "execution_flag_violation_ref_count",
    "op06_guard_reason_refs", "op06_guard_reason_ref_count", "op06_guard_blocker_refs", "op06_guard_blocker_ref_count", "guard_failure_refs", "guard_failure_ref_count",
    "rdb_op06_guard_passed_ready_for_rdb_op07", "selected_next_stage_candidate_not_executed", "downstream_auto_execution_allowed", "manual_decision_auto_executes_downstream", "p8_question_substitution_allowed", "question_text_materialized",
    "rdb_op06_does_not_recall_dhr_op04", "rdb_op06_does_not_call_dhr_op05", "rdb_op06_does_not_call_dhr_op06", "rdb_op06_does_not_execute_dmd_r52_or_release", "rdb_op06_does_not_start_p5_p6_p8_p7_or_release", "rdb_op06_does_not_change_api_db_rn_runtime_response_key", "rdb_op06_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_MRB08_RDB_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_MRB08_RDB_OP06_BASE_FIELD_REFS,
    "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_contract_valid", "op06_ready_for_rdb_op07", "op06_guard_passed_ready_for_rdb_op07", "op06_bodyfree_guard_passed", "op06_no_touch_guard_passed", "op06_no_promotion_guard_passed", "op06_no_auto_execution_guard_passed",
    "rdb_status_ref", "decision_lane_ref", "selected_next_stage_candidate_ref", "selected_next_stage_candidate_kind_ref",
    "rdb_op07_status_ref", "selected_regression_compileall_validation_plan_status_ref", "rdb_op07_allowed_status_refs", "rdb_op07_allowed_status_ref_count",
    "target_test_refs", "target_test_ref_count", "rdb_target_test_refs", "rdb_target_test_ref_count", "selected_regression_refs", "selected_regression_ref_count", "compileall_refs", "compileall_ref_count", "allowed_changed_file_refs", "allowed_changed_file_ref_count", "blocked_changed_file_token_refs", "blocked_changed_file_token_ref_count", "received_changed_file_refs", "received_changed_file_ref_count",
    "selected_regression_refs_recorded", "compileall_refs_recorded", "changed_files_within_allowed_refs", "api_db_rn_runtime_response_key_or_p8_question_touch_blocked", "api_db_rn_runtime_response_key_or_p8_question_touch_detected", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "selected_regression_executed_here", "compileall_executed_here",
    "forbidden_changed_file_token_refs", "forbidden_changed_file_token_ref_count", "disallowed_changed_file_refs", "disallowed_changed_file_ref_count", "changed_file_blocker_refs", "changed_file_blocker_ref_count", "op06_guard_blocker_refs", "op06_guard_blocker_ref_count", "rdb_op07_blocker_refs", "rdb_op07_blocker_ref_count", "op07_validation_reason_refs", "op07_validation_reason_ref_count", "op07_validation_blocker_refs", "op07_validation_blocker_ref_count",
    "rdb_op07_does_not_run_target_tests_here", "rdb_op07_does_not_run_selected_regression_here", "rdb_op07_does_not_run_compileall_here", "rdb_op07_does_not_claim_full_backend_green", "rdb_op07_does_not_claim_rn_contract_green", "rdb_op07_does_not_start_dhr_op05", "rdb_op07_does_not_start_p8", "rdb_op07_does_not_change_api_db_rn_runtime_response_key", "rdb_op07_does_not_materialize_p8_question_spec",
    "p8_question_substitution_allowed", "question_text_materialized", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op05_contract_valid(op05: Mapping[str, Any] | None) -> bool:
    if not isinstance(op05, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(op05) is True
    except ValueError:
        return False


def _op06_contract_valid(op06: Mapping[str, Any] | None) -> bool:
    if not isinstance(op06, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(op06) is True
    except ValueError:
        return False


def _true_mapping_refs(value: Any, *, prefix: str) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{prefix}_missing_or_not_mapping"]
    return _dedupe_clean_refs([f"{prefix}.{key}" for key, child in value.items() if child is True], max_length=340)


def _public_contract_violation_refs(value: Any, *, prefix: str) -> list[str]:
    if not isinstance(value, Mapping):
        return [f"{prefix}_missing_or_not_mapping"]
    expected = public_contract_flags()
    refs = [f"{prefix}.{key}" for key in set(value) | set(expected) if expected.get(key) is not False or value.get(key) is not False]
    return _dedupe_clean_refs(refs, max_length=340)


def _required_false_flag_violation_refs(value: Mapping[str, Any], *, prefix: str) -> list[str]:
    return _dedupe_clean_refs([f"{prefix}.{key}" for key in P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS if value.get(key) is not False], max_length=340)


def _execution_flag_violation_refs(value: Mapping[str, Any], *, prefix: str) -> list[str]:
    refs: list[str] = []
    for key in ("selected_next_stage_candidate_not_executed", "next_stage_candidate_enveloped_without_execution", "candidate_envelope_bodyfree"):
        if value.get(key) is not True:
            refs.append(f"{prefix}.{key}")
    for key in (
        "downstream_auto_execution_allowed", "manual_decision_auto_executes_downstream", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here",
        "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here",
        "repair_executed_here", "p8_question_candidate_created", "p8_question_design_started_here", "p8_question_implementation_started_here", "release_decision_created_here",
    ):
        if value.get(key) is True:
            refs.append(f"{prefix}.{key}")
    return _dedupe_clean_refs(refs, max_length=340)


def _changed_file_scope_refs(changed_file_refs: Sequence[Any]) -> tuple[list[str], list[str], list[str]]:
    clean_changed = _dedupe_clean_refs(changed_file_refs, max_length=360)
    allowed = set(P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_CHANGED_FILE_REFS)
    disallowed = [ref for ref in clean_changed if ref not in allowed]
    forbidden_tokens: list[str] = []
    for ref in clean_changed:
        lower = ref.lower()
        for token in P7_R54_AHR_POST_MRB08_RDB_OP07_BLOCKED_CHANGED_FILE_TOKEN_REFS:
            if token.lower() in lower:
                forbidden_tokens.append(f"{ref}:{token}")
    return clean_changed, _dedupe_clean_refs(disallowed, max_length=360), _dedupe_clean_refs(forbidden_tokens, max_length=360)


def build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
    *,
    candidate_envelope_without_execution: Mapping[str, Any] | None = None,
    next_stage_candidate_envelope_without_execution: Mapping[str, Any] | None = None,
    branch_specific_manual_decision_materialization: Mapping[str, Any] | None = None,
    dhr_op04_result_manual_decision_lane_resolver: Mapping[str, Any] | None = None,
    mrb_branch_dhr_status_consistency_check: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP06 body-free / no-touch / no-promotion guard material."""

    op05 = dict(next_stage_candidate_envelope_without_execution or candidate_envelope_without_execution or build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution(
        branch_specific_manual_decision_materialization=branch_specific_manual_decision_materialization,
        dhr_op04_result_manual_decision_lane_resolver=dhr_op04_result_manual_decision_lane_resolver,
        mrb_branch_dhr_status_consistency_check=mrb_branch_dhr_status_consistency_check,
        mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
        mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
        review_session_id=review_session_id,
    ))
    op05_valid = _op05_contract_valid(op05)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op05, path="op05"), max_length=340)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op05, path="op05"), max_length=340)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op05, path="op05"), max_length=340)
    public_refs = _public_contract_violation_refs(op05.get("public_contract"), prefix="op05.public_contract")
    no_touch_refs = _true_mapping_refs(op05.get("rdb_no_touch_contract"), prefix="op05.rdb_no_touch_contract")
    body_marker_refs = _true_mapping_refs(op05.get("body_free_markers"), prefix="op05.body_free_markers")
    not_claimed_refs = _true_mapping_refs(op05.get("not_claimed_boundary"), prefix="op05.not_claimed_boundary")
    false_flag_refs = _required_false_flag_violation_refs(op05, prefix="op05")
    execution_refs = _execution_flag_violation_refs(op05, prefix="op05")
    promotion_claims = _dedupe_clean_refs([
        *promotion_claims,
        *[ref for ref in execution_refs if ("builder_called_here" in ref or "downstream_auto_execution_allowed" in ref or "manual_decision_auto_executes_downstream" in ref)],
    ], max_length=340)
    bodyfree_passed = bool(op05_valid and not forbidden_paths and not body_like_paths and not body_marker_refs)
    no_touch_passed = bool(op05_valid and not public_refs and not no_touch_refs)
    no_promotion_passed = bool(op05_valid and not promotion_claims and not not_claimed_refs and not false_flag_refs)
    no_auto_passed = bool(op05_valid and not execution_refs and op05.get("selected_next_stage_candidate_not_executed") is True)
    candidate_not_executed_passed = bool(not execution_refs and op05.get("selected_next_stage_candidate_not_executed") is True)
    guard_passed = bool(bodyfree_passed and no_touch_passed and no_promotion_passed and no_auto_passed)
    blockers = _dedupe_clean_refs([*forbidden_paths, *body_like_paths, *promotion_claims, *public_refs, *no_touch_refs, *body_marker_refs, *not_claimed_refs, *false_flag_refs, *execution_refs], max_length=340)
    if not op05_valid:
        blockers = _dedupe_clean_refs(["rdb_op05_candidate_envelope_contract_invalid", *blockers], max_length=340)
    if guard_passed:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_PASSED_READY_FOR_OP07_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF
        reasons = ["rdb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed"]
    elif forbidden_paths or body_like_paths or promotion_claims or execution_refs:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
        reasons = ["rdb_op06_blocked_bodyfree_leak_promotion_or_autorun_before_validation_plan"]
    else:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_REPAIR_REQUIRED_FOR_OP05_ENVELOPE_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF
        reasons = ["rdb_op06_repair_required_for_op05_candidate_envelope_before_validation_plan"]
    session_id = _safe_review_session_id(review_session_id or op05.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": _clean_ref(op05.get("schema_version"), default="rdb_op05_schema_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id"), default="rdb_op05_material_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("rdb_status_ref"), default="rdb_op05_status_missing", max_length=320),
        "op05_decision_lane_ref": _clean_ref(op05.get("decision_lane_ref"), default="rdb_op05_decision_lane_missing", max_length=320),
        "op05_candidate_envelope_ref": _clean_ref(op05.get("candidate_envelope_ref"), default="rdb_op05_candidate_envelope_missing", max_length=320),
        "op05_selected_next_stage_candidate_ref": _clean_ref(op05.get("selected_next_stage_candidate_ref"), default="rdb_op05_candidate_ref_missing", max_length=320),
        "op05_selected_next_stage_candidate_kind_ref": _clean_ref(op05.get("selected_next_stage_candidate_kind_ref"), default="rdb_op05_candidate_kind_missing", max_length=320),
        "op05_selected_next_stage_candidate_not_executed": bool(op05.get("selected_next_stage_candidate_not_executed") is True),
        "op05_contract_valid": op05_valid,
        "rdb_status_ref": _clean_ref(op05.get("rdb_status_ref"), default=P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF, max_length=320),
        "decision_lane_ref": _clean_ref(op05.get("decision_lane_ref"), default="rdb_op05_decision_lane_missing", max_length=320),
        "selected_next_stage_candidate_ref": _clean_ref(op05.get("selected_next_stage_candidate_ref"), default="rdb_op05_candidate_ref_missing", max_length=320),
        "selected_next_stage_candidate_kind_ref": _clean_ref(op05.get("selected_next_stage_candidate_kind_ref"), default="rdb_op05_candidate_kind_missing", max_length=320),
        "selected_next_stage_operation_candidate_ref": _clean_ref(op05.get("selected_next_stage_operation_candidate_ref"), default="rdb_op05_operation_candidate_missing", max_length=320),
        "rdb_op06_status_ref": status_ref,
        "bodyfree_no_touch_no_promotion_guard_status_ref": status_ref,
        "rdb_op06_allowed_status_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP06_ALLOWED_STATUS_REFS),
        "rdb_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP06_ALLOWED_STATUS_REFS),
        "rdb_op06_guard_checked": True,
        "body_free_guard_checked": True,
        "no_touch_guard_checked": True,
        "no_promotion_guard_checked": True,
        "no_auto_execution_guard_checked": True,
        "guard_checked_bodyfree": True,
        "guard_checked_no_touch": True,
        "guard_checked_no_promotion": True,
        "guard_checked_no_auto_execution": True,
        "op05_public_contract_false": bool(not public_refs),
        "op05_no_touch_contract_false": bool(not no_touch_refs),
        "op05_body_free_markers_false": bool(not body_marker_refs),
        "op05_body_free_true": bool(op05.get("body_free") is True),
        "op05_selected_next_stage_candidate_not_executed_true": bool(op05.get("selected_next_stage_candidate_not_executed") is True),
        "op05_downstream_auto_execution_false": bool(op05.get("downstream_auto_execution_allowed") is False),
        "rdb_bodyfree_guard_passed": bodyfree_passed,
        "rdb_no_touch_guard_passed": no_touch_passed,
        "rdb_no_promotion_guard_passed": no_promotion_passed,
        "rdb_no_auto_execution_guard_passed": no_auto_passed,
        "rdb_public_contract_guard_passed": bool(op05_valid and not public_refs),
        "rdb_candidate_not_executed_guard_passed": candidate_not_executed_passed,
        "rdb_op06_ready_for_rdb_op07": guard_passed,
        "rdb_op06_blocked_bodyfree_leak_promotion_or_autorun": status_ref == P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
        "rdb_op06_repair_required_for_op05_envelope": status_ref == P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_REPAIR_REQUIRED_FOR_OP05_ENVELOPE_REF,
        "forbidden_payload_key_path_refs": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "body_like_value_path_refs": body_like_paths,
        "body_like_value_path_count": len(body_like_paths),
        "promotion_claim_refs": promotion_claims,
        "promotion_claim_ref_count": len(promotion_claims),
        "true_public_contract_refs": public_refs,
        "true_public_contract_ref_count": len(public_refs),
        "true_no_touch_contract_refs": no_touch_refs,
        "true_no_touch_contract_ref_count": len(no_touch_refs),
        "true_body_free_marker_refs": body_marker_refs,
        "true_body_free_marker_ref_count": len(body_marker_refs),
        "true_not_claimed_boundary_refs": not_claimed_refs,
        "true_not_claimed_boundary_ref_count": len(not_claimed_refs),
        "required_false_flag_violation_refs": false_flag_refs,
        "required_false_flag_violation_ref_count": len(false_flag_refs),
        "execution_flag_violation_refs": execution_refs,
        "execution_flag_violation_ref_count": len(execution_refs),
        "op06_guard_reason_refs": _dedupe_clean_refs(reasons, max_length=340),
        "op06_guard_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=340)),
        "op06_guard_blocker_refs": blockers,
        "op06_guard_blocker_ref_count": len(blockers),
        "guard_failure_refs": blockers,
        "guard_failure_ref_count": len(blockers),
        "rdb_op06_guard_passed_ready_for_rdb_op07": guard_passed,
        "selected_next_stage_candidate_not_executed": True,
        "downstream_auto_execution_allowed": False,
        "manual_decision_auto_executes_downstream": False,
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "rdb_op06_does_not_recall_dhr_op04": True,
        "rdb_op06_does_not_call_dhr_op05": True,
        "rdb_op06_does_not_call_dhr_op06": True,
        "rdb_op06_does_not_execute_dmd_r52_or_release": True,
        "rdb_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op06_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract(data: Mapping[str, Any]) -> bool:
    """Assert RDB-OP06 body-free / no-touch / no-promotion guard contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP06")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MRB08_RDB_OP06_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF, source="P7-R54-AHR-PostMRB08-RDB-OP06")
    if data.get("rdb_op06_status_ref") not in P7_R54_AHR_POST_MRB08_RDB_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 unknown status")
    if data.get("bodyfree_no_touch_no_promotion_guard_status_ref") != data.get("rdb_op06_status_ref"):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 status alias changed")
    for field, count_field in (
        ("rdb_op06_allowed_status_refs", "rdb_op06_allowed_status_ref_count"), ("forbidden_payload_key_path_refs", "forbidden_payload_key_path_count"), ("body_like_value_path_refs", "body_like_value_path_count"), ("promotion_claim_refs", "promotion_claim_ref_count"), ("true_public_contract_refs", "true_public_contract_ref_count"), ("true_no_touch_contract_refs", "true_no_touch_contract_ref_count"), ("true_body_free_marker_refs", "true_body_free_marker_ref_count"), ("true_not_claimed_boundary_refs", "true_not_claimed_boundary_ref_count"), ("required_false_flag_violation_refs", "required_false_flag_violation_ref_count"), ("execution_flag_violation_refs", "execution_flag_violation_ref_count"), ("op06_guard_reason_refs", "op06_guard_reason_ref_count"), ("op06_guard_blocker_refs", "op06_guard_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP06 {count_field} changed")
    for key in ("rdb_op06_guard_checked", "body_free_guard_checked", "no_touch_guard_checked", "no_promotion_guard_checked", "no_auto_execution_guard_checked", "guard_checked_bodyfree", "guard_checked_no_touch", "guard_checked_no_promotion", "guard_checked_no_auto_execution", "rdb_op06_does_not_recall_dhr_op04", "rdb_op06_does_not_call_dhr_op05", "rdb_op06_does_not_call_dhr_op06", "rdb_op06_does_not_execute_dmd_r52_or_release", "rdb_op06_does_not_start_p5_p6_p8_p7_or_release", "rdb_op06_does_not_change_api_db_rn_runtime_response_key", "rdb_op06_does_not_materialize_p8_question_spec", "selected_next_stage_candidate_not_executed"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP06 required true boundary changed: {key}")
    for key in ("downstream_auto_execution_allowed", "manual_decision_auto_executes_downstream", "p8_question_substitution_allowed", "question_text_materialized"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP06 required false boundary changed: {key}")
    if data.get("rdb_op06_status_ref") == P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_PASSED_READY_FOR_OP07_REF:
        if not all(data.get(key) is True for key in ("rdb_bodyfree_guard_passed", "rdb_no_touch_guard_passed", "rdb_no_promotion_guard_passed", "rdb_no_auto_execution_guard_passed", "rdb_public_contract_guard_passed", "rdb_candidate_not_executed_guard_passed", "rdb_op06_ready_for_rdb_op07", "rdb_op06_guard_passed_ready_for_rdb_op07")):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 passed guard flags changed")
        if data.get("op06_guard_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 passed guard blocker/next changed")
    else:
        if data.get("rdb_op06_ready_for_rdb_op07") is not False or data.get("rdb_op06_guard_passed_ready_for_rdb_op07") is not False or not data.get("op06_guard_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 non-ready guard changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP06_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP06 not-yet steps changed")
    return True


def build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan(
    *,
    bodyfree_no_touch_no_promotion_guard: Mapping[str, Any] | None = None,
    next_stage_candidate_envelope_without_execution: Mapping[str, Any] | None = None,
    branch_specific_manual_decision_materialization: Mapping[str, Any] | None = None,
    dhr_op04_result_manual_decision_lane_resolver: Mapping[str, Any] | None = None,
    mrb_branch_dhr_status_consistency_check: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RDB-OP07 selected regression / compileall validation plan material."""

    op06 = dict(bodyfree_no_touch_no_promotion_guard or build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard(
        next_stage_candidate_envelope_without_execution=next_stage_candidate_envelope_without_execution,
        branch_specific_manual_decision_materialization=branch_specific_manual_decision_materialization,
        dhr_op04_result_manual_decision_lane_resolver=dhr_op04_result_manual_decision_lane_resolver,
        mrb_branch_dhr_status_consistency_check=mrb_branch_dhr_status_consistency_check,
        mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
        mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
        review_session_id=review_session_id,
    ))
    op06_valid = _op06_contract_valid(op06)
    op06_ready = bool(op06_valid and op06.get("rdb_op06_ready_for_rdb_op07") is True)
    clean_changed, disallowed, forbidden_tokens = _changed_file_scope_refs(tuple(changed_file_refs) if changed_file_refs is not None else P7_R54_AHR_POST_MRB08_RDB_OP07_DEFAULT_CHANGED_FILE_REFS)
    changed_ok = bool(not disallowed and not forbidden_tokens)
    op06_blockers = _dedupe_clean_refs(op06.get("op06_guard_blocker_refs") or [], max_length=340)
    blockers = _dedupe_clean_refs([*op06_blockers, *disallowed, *forbidden_tokens], max_length=360)
    if op06.get("rdb_op06_status_ref") == P7_R54_AHR_POST_MRB08_RDB_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
        reasons = ["rdb_op07_waits_because_op06_bodyfree_no_touch_no_promotion_guard_blocked"]
    elif not op06_ready:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_REPAIR_OP06_GUARD_REQUIRED_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF
        reasons = ["rdb_op07_waits_for_op06_guard_pass_before_validation_plan_closure"]
        blockers = _dedupe_clean_refs(["rdb_op06_guard_not_ready_for_validation_plan", *blockers], max_length=360)
        if not op06_valid:
            blockers.append("rdb_op06_contract_invalid_before_validation_plan")
    elif not changed_ok:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_BLOCKED_CHANGED_FILE_SCOPE_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF
        reasons = ["rdb_op07_blocks_disallowed_changed_files_or_p8_api_db_rn_runtime_touch"]
    else:
        status_ref = P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF
        reasons = ["rdb_op07_records_selected_regression_compileall_plan_ready_for_op08_without_running_downstream"]
    session_id = _safe_review_session_id(review_session_id or op06.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": _clean_ref(op06.get("schema_version"), default="rdb_op06_schema_missing", max_length=260),
        "op06_material_ref": _clean_ref(op06.get("material_id"), default="rdb_op06_material_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06.get("rdb_op06_status_ref"), default="rdb_op06_status_missing", max_length=320),
        "op06_contract_valid": op06_valid,
        "op06_ready_for_rdb_op07": op06_ready,
        "op06_guard_passed_ready_for_rdb_op07": bool(op06.get("rdb_op06_guard_passed_ready_for_rdb_op07") is True),
        "op06_bodyfree_guard_passed": bool(op06.get("rdb_bodyfree_guard_passed") is True),
        "op06_no_touch_guard_passed": bool(op06.get("rdb_no_touch_guard_passed") is True),
        "op06_no_promotion_guard_passed": bool(op06.get("rdb_no_promotion_guard_passed") is True),
        "op06_no_auto_execution_guard_passed": bool(op06.get("rdb_no_auto_execution_guard_passed") is True),
        "rdb_status_ref": _clean_ref(op06.get("rdb_status_ref"), default=P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF, max_length=320),
        "decision_lane_ref": _clean_ref(op06.get("decision_lane_ref"), default="rdb_op06_decision_lane_missing", max_length=320),
        "selected_next_stage_candidate_ref": _clean_ref(op06.get("selected_next_stage_candidate_ref"), default="rdb_op06_candidate_missing", max_length=320),
        "selected_next_stage_candidate_kind_ref": _clean_ref(op06.get("selected_next_stage_candidate_kind_ref"), default="rdb_op06_candidate_kind_missing", max_length=320),
        "rdb_op07_status_ref": status_ref,
        "selected_regression_compileall_validation_plan_status_ref": status_ref,
        "rdb_op07_allowed_status_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_STATUS_REFS),
        "rdb_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_STATUS_REFS),
        "target_test_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS),
        "target_test_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS),
        "rdb_target_test_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS),
        "rdb_target_test_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS),
        "selected_regression_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS),
        "selected_regression_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS),
        "compileall_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS),
        "compileall_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS),
        "allowed_changed_file_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_CHANGED_FILE_REFS),
        "allowed_changed_file_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_CHANGED_FILE_REFS),
        "blocked_changed_file_token_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_BLOCKED_CHANGED_FILE_TOKEN_REFS),
        "blocked_changed_file_token_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_BLOCKED_CHANGED_FILE_TOKEN_REFS),
        "received_changed_file_refs": clean_changed,
        "received_changed_file_ref_count": len(clean_changed),
        "selected_regression_refs_recorded": True,
        "compileall_refs_recorded": True,
        "changed_files_within_allowed_refs": changed_ok,
        "api_db_rn_runtime_response_key_or_p8_question_touch_blocked": True,
        "api_db_rn_runtime_response_key_or_p8_question_touch_detected": bool(forbidden_tokens),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "selected_regression_executed_here": False,
        "compileall_executed_here": False,
        "forbidden_changed_file_token_refs": forbidden_tokens,
        "forbidden_changed_file_token_ref_count": len(forbidden_tokens),
        "disallowed_changed_file_refs": disallowed,
        "disallowed_changed_file_ref_count": len(disallowed),
        "changed_file_blocker_refs": _dedupe_clean_refs([*[f"changed_file_not_allowed:{ref}" for ref in disallowed], *[f"changed_file_forbidden_token:{ref}" for ref in forbidden_tokens]], max_length=360),
        "changed_file_blocker_ref_count": len(_dedupe_clean_refs([*[f"changed_file_not_allowed:{ref}" for ref in disallowed], *[f"changed_file_forbidden_token:{ref}" for ref in forbidden_tokens]], max_length=360)),
        "op06_guard_blocker_refs": op06_blockers,
        "op06_guard_blocker_ref_count": len(op06_blockers),
        "rdb_op07_blocker_refs": blockers,
        "rdb_op07_blocker_ref_count": len(blockers),
        "op07_validation_reason_refs": _dedupe_clean_refs(reasons, max_length=340),
        "op07_validation_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=340)),
        "op07_validation_blocker_refs": blockers,
        "op07_validation_blocker_ref_count": len(blockers),
        "rdb_op07_does_not_run_target_tests_here": True,
        "rdb_op07_does_not_run_selected_regression_here": True,
        "rdb_op07_does_not_run_compileall_here": True,
        "rdb_op07_does_not_claim_full_backend_green": True,
        "rdb_op07_does_not_claim_rn_contract_green": True,
        "rdb_op07_does_not_start_dhr_op05": True,
        "rdb_op07_does_not_start_p8": True,
        "rdb_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "rdb_op07_does_not_materialize_p8_question_spec": True,
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(data: Mapping[str, Any]) -> bool:
    """Assert RDB-OP07 selected regression / compileall validation plan contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP07")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MRB08_RDB_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP07_STEP_REF, source="P7-R54-AHR-PostMRB08-RDB-OP07")
    if data.get("rdb_op07_status_ref") not in P7_R54_AHR_POST_MRB08_RDB_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 unknown status")
    for field, count_field in (("target_test_refs", "target_test_ref_count"), ("rdb_target_test_refs", "rdb_target_test_ref_count"), ("selected_regression_refs", "selected_regression_ref_count"), ("compileall_refs", "compileall_ref_count"), ("allowed_changed_file_refs", "allowed_changed_file_ref_count"), ("blocked_changed_file_token_refs", "blocked_changed_file_token_ref_count"), ("received_changed_file_refs", "received_changed_file_ref_count"), ("forbidden_changed_file_token_refs", "forbidden_changed_file_token_ref_count"), ("disallowed_changed_file_refs", "disallowed_changed_file_ref_count"), ("changed_file_blocker_refs", "changed_file_blocker_ref_count"), ("op06_guard_blocker_refs", "op06_guard_blocker_ref_count"), ("rdb_op07_blocker_refs", "rdb_op07_blocker_ref_count"), ("op07_validation_reason_refs", "op07_validation_reason_ref_count"), ("op07_validation_blocker_refs", "op07_validation_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP07 {count_field} changed")
    if tuple(data.get("target_test_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS or tuple(data.get("selected_regression_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS or tuple(data.get("compileall_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 validation refs changed")
    for key in ("selected_regression_refs_recorded", "compileall_refs_recorded", "rdb_op07_does_not_run_target_tests_here", "rdb_op07_does_not_run_selected_regression_here", "rdb_op07_does_not_run_compileall_here", "rdb_op07_does_not_claim_full_backend_green", "rdb_op07_does_not_claim_rn_contract_green", "rdb_op07_does_not_start_dhr_op05", "rdb_op07_does_not_start_p8", "rdb_op07_does_not_change_api_db_rn_runtime_response_key", "rdb_op07_does_not_materialize_p8_question_spec"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP07 required true boundary changed: {key}")
    for key in ("full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "selected_regression_executed_here", "compileall_executed_here", "p8_question_substitution_allowed", "question_text_materialized"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP07 required false boundary changed: {key}")
    if data.get("api_db_rn_runtime_response_key_or_p8_question_touch_blocked") is not True:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 touch block guard changed")
    if data.get("api_db_rn_runtime_response_key_or_p8_question_touch_detected") is not bool(data.get("forbidden_changed_file_token_refs")):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 forbidden token detection flag changed")
    if data.get("changed_files_within_allowed_refs") is not (not data.get("disallowed_changed_file_refs") and not data.get("forbidden_changed_file_token_refs")):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 changed file scope flag changed")
    if data.get("rdb_op07_status_ref") == P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF:
        if data.get("op06_ready_for_rdb_op07") is not True or data.get("changed_files_within_allowed_refs") is not True or data.get("next_required_step") != P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 ready contract changed")
    else:
        if not data.get("op07_validation_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 non-ready status requires blockers")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP07_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP07 not-yet steps changed")
    return True


P7_R54_AHR_POST_MRB08_RDB_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mrb08.rdb."
    "op08_bodyfree_result_manual_decision_memo_closure.bodyfree.v1"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_MRB08_RDB_STEP_REFS
P7_R54_AHR_POST_MRB08_RDB_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF: Final = (
    "RDB_OP08_BODYFREE_RESULT_MANUAL_DECISION_MEMO_CLOSED_STOPPED"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF: Final = (
    "RDB_OP08_WAITING_FOR_OP03_OP04_OP05_OR_VALIDATION_REFS"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_REPAIR_REQUIRED_REF: Final = (
    "RDB_OP08_REPAIR_REQUIRED_FOR_RESULT_MANUAL_DECISION_CLOSURE_INPUTS"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "RDB_OP08_BLOCKED_BODYFREE_RESULT_MEMO_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_WAIT_REF: Final = (
    "wait_for_rdb_op03_op04_op05_op07_validation_or_result_memo_refs_before_closure"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_REPAIR_REF: Final = (
    "repair_rdb_result_manual_decision_closure_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_BLOCKED_REF: Final = (
    "blocked_rdb_op08_bodyfree_result_memo_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_MRB08_RDB_OP08_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "RDB-OP00/OP01 target",
    "RDB-OP02/OP03 target",
    "RDB-OP04/OP05 target",
    "RDB-OP06/OP07 target",
    "RDB-OP08 target",
    "RDB-OP00-OP08 combined target",
    "selected regression",
    "compileall",
)
P7_R54_AHR_POST_MRB08_RDB_OP08_DEFAULT_CHANGED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_result_20260705.py",
    "tests/R54_AHR_PostMRB08_DHROP04ResultManualDecision_RDB_OP00_OP08_Result_20260705.md",
)
P7_R54_AHR_POST_MRB08_RDB_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_material_present", "op04_contract_valid", "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_decision_lane_ref", "op04_branch_specific_manual_decision_material_ref", "op04_manual_decision_materialized",
    "op05_material_present", "op05_contract_valid", "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_decision_lane_ref", "op05_candidate_envelope_ref", "op05_selected_next_stage_candidate_ref", "op05_selected_next_stage_candidate_kind_ref", "op05_selected_next_stage_candidate_not_executed",
    "op07_material_present", "op07_contract_valid", "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_ready_for_op08", "op07_changed_files_within_allowed_refs", "op07_selected_regression_refs_recorded", "op07_compileall_refs_recorded", "op07_full_backend_suite_green_confirmed", "op07_rn_contract_green_confirmed", "op07_rn_real_device_modal_verified_claimed_here",
    "validation_summary_bodyfree_present", "validation_summary_bodyfree_accepted", "validation_summary_bodyfree_ref", "validation_summary_forbidden_payload_key_path_refs", "validation_summary_forbidden_payload_key_path_count", "validation_summary_body_like_value_path_refs", "validation_summary_body_like_value_path_count", "validation_summary_promotion_claim_refs", "validation_summary_promotion_claim_ref_count",
    "result_memo_bodyfree_present", "result_memo_bodyfree_accepted", "result_memo_bodyfree_ref", "result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count", "result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count", "result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count",
    "validation_command_summary_refs", "validation_command_summary_ref_count", "target_test_refs", "target_test_ref_count", "selected_regression_refs", "selected_regression_ref_count", "compileall_refs", "compileall_ref_count",
    "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref", "combined_run_status_ref", "rdb_target_green_confirmed", "selected_regression_green_confirmed", "compileall_green_confirmed", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_green_claim_not_made_here", "rn_green_claim_not_made_here",
    "rdb_op08_status_ref", "bodyfree_result_manual_decision_memo_closure_status_ref", "rdb_op08_allowed_status_refs", "rdb_op08_allowed_status_ref_count",
    "rdb_op08_closed_bodyfree_stopped", "rdb_op08_waiting_for_op03_op04_op05_or_validation_refs", "rdb_op08_repair_required_for_result_manual_decision_closure_inputs", "rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun",
    "rdb_op08_reason_refs", "rdb_op08_reason_ref_count", "rdb_op08_blocker_refs", "rdb_op08_blocker_ref_count",
    "rdb_selected_status_ref", "mrb_selected_branch_ref", "dhr_op04_result_status_ref", "decision_lane_ref", "manual_decision_material_ref", "manual_decision_material_kind_ref", "manual_decision_material_present", "selected_next_stage_candidate_ref", "selected_next_stage_candidate_kind_ref", "selected_next_stage_candidate_not_executed",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started",
    "rdb_op08_does_not_recall_dhr_op04", "rdb_op08_does_not_call_dhr_op05", "rdb_op08_does_not_call_dhr_op06", "rdb_op08_does_not_execute_dmd_r52_or_release", "rdb_op08_does_not_start_p5_p6_p8_p7_or_release", "rdb_op08_does_not_materialize_p8_question_spec", "rdb_op08_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "p8_question_substitution_allowed", "question_text_materialized", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "rdb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op07_contract_valid(op07: Mapping[str, Any] | None) -> bool:
    if not isinstance(op07, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract(op07) is True
    except ValueError:
        return False


def _bodyfree_scan_triplets(value: Mapping[str, Any] | None, *, path: str) -> tuple[list[str], list[str], list[str]]:
    material = value if isinstance(value, Mapping) else {}
    return (
        _scan_forbidden_payload_key_paths(material, path=path),
        _scan_body_like_value_paths(material, path=path),
        _scan_promotion_claim_refs(material, path=path),
    )


def _safe_mapping_copy_when_bodyfree(value: Mapping[str, Any] | None, *, accepted: bool) -> dict[str, Any]:
    if not accepted or not isinstance(value, Mapping):
        return {}
    return dict(value)


def build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure(
    *,
    selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    bodyfree_no_touch_no_promotion_guard: Mapping[str, Any] | None = None,
    next_stage_candidate_envelope_without_execution: Mapping[str, Any] | None = None,
    branch_specific_manual_decision_materialization: Mapping[str, Any] | None = None,
    dhr_op04_result_manual_decision_lane_resolver: Mapping[str, Any] | None = None,
    mrb_branch_dhr_status_consistency_check: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure_intake: Mapping[str, Any] | None = None,
    mrb_op08_result_memo_closure: Mapping[str, Any] | None = None,
    validation_summary_bodyfree: Mapping[str, Any] | None = None,
    result_memo_bodyfree: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Close RDB-OP00〜OP07 as a body-free result manual decision memo and stop."""

    op04 = dict(branch_specific_manual_decision_materialization or build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization(
        dhr_op04_result_manual_decision_lane_resolver=dhr_op04_result_manual_decision_lane_resolver,
        mrb_branch_dhr_status_consistency_check=mrb_branch_dhr_status_consistency_check,
        mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
        mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
        review_session_id=review_session_id,
    ))
    op05 = dict(next_stage_candidate_envelope_without_execution or build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution(
        branch_specific_manual_decision_materialization=op04,
        review_session_id=review_session_id,
    ))
    op07 = dict(selected_regression_compileall_validation_plan or build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan(
        bodyfree_no_touch_no_promotion_guard=bodyfree_no_touch_no_promotion_guard,
        next_stage_candidate_envelope_without_execution=op05,
        branch_specific_manual_decision_materialization=op04,
        dhr_op04_result_manual_decision_lane_resolver=dhr_op04_result_manual_decision_lane_resolver,
        mrb_branch_dhr_status_consistency_check=mrb_branch_dhr_status_consistency_check,
        mrb_op08_result_memo_closure_intake=mrb_op08_result_memo_closure_intake,
        mrb_op08_result_memo_closure=mrb_op08_result_memo_closure,
        changed_file_refs=tuple(changed_file_refs) if changed_file_refs is not None else P7_R54_AHR_POST_MRB08_RDB_OP08_DEFAULT_CHANGED_FILE_REFS,
        review_session_id=review_session_id,
    ))

    op04_valid = _op04_contract_valid(op04)
    op05_valid = _op05_contract_valid(op05)
    op07_valid = _op07_contract_valid(op07)
    op07_ready = bool(op07_valid and op07.get("rdb_op07_status_ref") == P7_R54_AHR_POST_MRB08_RDB_OP07_STATUS_READY_FOR_OP08_REF and op07.get("next_required_step") == P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF)

    validation_present = isinstance(validation_summary_bodyfree, Mapping)
    memo_present = isinstance(result_memo_bodyfree, Mapping)
    validation_forbidden, validation_body_like, validation_promotion = _bodyfree_scan_triplets(validation_summary_bodyfree, path="rdb_op08.validation_summary")
    memo_forbidden, memo_body_like, memo_promotion = _bodyfree_scan_triplets(result_memo_bodyfree, path="rdb_op08.result_memo")
    op07_forbidden, op07_body_like, op07_promotion = _bodyfree_scan_triplets(op07, path="op07")
    validation_accepted = bool(validation_present and not validation_forbidden and not validation_body_like and not validation_promotion)
    memo_accepted = bool(memo_present and not memo_forbidden and not memo_body_like and not memo_promotion)

    reasons: list[str] = []
    blockers: list[str] = []
    if op07_forbidden or op07_body_like or op07_promotion or validation_forbidden or validation_body_like or validation_promotion or memo_forbidden or memo_body_like or memo_promotion:
        status = P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_BLOCKED_REF
        reasons.append("rdb_op08_bodyfree_result_memo_or_upstream_material_scan_blocked")
        if op07_forbidden:
            blockers.append("rdb_op07_forbidden_payload_key_detected_before_result_memo_closure")
        if op07_body_like:
            blockers.append("rdb_op07_body_like_value_detected_before_result_memo_closure")
        if op07_promotion:
            blockers.append("rdb_op07_promotion_or_autorun_claim_detected_before_result_memo_closure")
        if validation_forbidden:
            blockers.append("rdb_op08_validation_summary_forbidden_payload_key_detected")
        if validation_body_like:
            blockers.append("rdb_op08_validation_summary_body_like_value_detected")
        if validation_promotion:
            blockers.append("rdb_op08_validation_summary_promotion_claim_detected")
        if memo_forbidden:
            blockers.append("rdb_op08_result_memo_forbidden_payload_key_detected")
        if memo_body_like:
            blockers.append("rdb_op08_result_memo_body_like_value_detected")
        if memo_promotion:
            blockers.append("rdb_op08_result_memo_promotion_claim_detected")
    elif not isinstance(branch_specific_manual_decision_materialization, Mapping) and not op04_valid:
        status = P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_WAIT_REF
        reasons.append("rdb_op08_waiting_for_op04_manual_decision_material_before_result_memo_closure")
        blockers.append("rdb_op04_manual_decision_material_missing_or_not_ready")
    elif not validation_present or not memo_present:
        status = P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_WAIT_REF
        reasons.append("rdb_op08_waiting_for_bodyfree_validation_summary_or_result_memo_refs")
        if not validation_present:
            blockers.append("validation_summary_bodyfree_missing")
        if not memo_present:
            blockers.append("result_memo_bodyfree_missing")
    elif not op04_valid or not op05_valid or not op07_valid or not op07_ready or op05.get("selected_next_stage_candidate_not_executed") is not True or op04.get("manual_decision_materialized") is not True:
        status = P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_MRB08_RDB_OP08_NEXT_STEP_REPAIR_REF
        reasons.append("rdb_op08_repair_required_for_op04_op05_op07_or_candidate_execution_boundary")
        if not op04_valid:
            blockers.append("rdb_op04_contract_invalid")
        if not op05_valid:
            blockers.append("rdb_op05_contract_invalid")
        if not op07_valid:
            blockers.append("rdb_op07_contract_invalid")
        elif not op07_ready:
            blockers.append("rdb_op07_not_ready_for_op08")
        if op05.get("selected_next_stage_candidate_not_executed") is not True:
            blockers.append("selected_next_stage_candidate_execution_boundary_not_preserved")
        if op04.get("manual_decision_materialized") is not True:
            blockers.append("manual_decision_material_not_materialized")
    else:
        status = P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
        next_step = _clean_ref(op05.get("selected_next_stage_candidate_ref"), default=P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF, max_length=360)
        reasons.append("rdb_op08_bodyfree_result_manual_decision_memo_closed_and_stopped_without_downstream_execution")

    target_status = _clean_ref((validation_summary_bodyfree or {}).get("target_test_result_status_ref"), default="not_run", max_length=120)
    selected_status = _clean_ref((validation_summary_bodyfree or {}).get("selected_regression_result_status_ref"), default="not_run", max_length=120)
    compileall_status = _clean_ref((validation_summary_bodyfree or {}).get("compileall_result_status_ref"), default="not_run", max_length=120)
    combined_status = _clean_ref((validation_summary_bodyfree or {}).get("combined_run_status_ref"), default="not_run", max_length=120)
    status_flags = {
        "rdb_op08_closed_bodyfree_stopped": status == P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF,
        "rdb_op08_waiting_for_op03_op04_op05_or_validation_refs": status == P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
        "rdb_op08_repair_required_for_result_manual_decision_closure_inputs": status == P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_REPAIR_REQUIRED_REF,
        "rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun": status == P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    }
    session_id = _safe_review_session_id(review_session_id or op07.get("review_session_id") or op05.get("review_session_id") or op04.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_MRB08_RDB_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "step": P7_R54_AHR_POST_MRB08_RDB_STEP,
        "scope": P7_R54_AHR_POST_MRB08_RDB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MRB08_RDB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_MRB08_RDB_PHASE,
        "material_id": "p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_material_present": isinstance(branch_specific_manual_decision_materialization, Mapping),
        "op04_contract_valid": op04_valid,
        "op04_schema_version": _clean_ref(op04.get("schema_version"), default="rdb_op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id"), default="rdb_op04_material_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("rdb_status_ref"), default=P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF, max_length=320),
        "op04_decision_lane_ref": _clean_ref(op04.get("decision_lane_ref"), default="rdb_op04_decision_lane_missing", max_length=320),
        "op04_branch_specific_manual_decision_material_ref": _clean_ref(op04.get("branch_specific_manual_decision_material_ref"), default="rdb_op04_manual_decision_material_missing", max_length=320),
        "op04_manual_decision_materialized": bool(op04.get("manual_decision_materialized") is True),
        "op05_material_present": isinstance(next_stage_candidate_envelope_without_execution, Mapping),
        "op05_contract_valid": op05_valid,
        "op05_schema_version": _clean_ref(op05.get("schema_version"), default="rdb_op05_schema_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id"), default="rdb_op05_material_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("rdb_status_ref"), default=P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF, max_length=320),
        "op05_decision_lane_ref": _clean_ref(op05.get("decision_lane_ref"), default="rdb_op05_decision_lane_missing", max_length=320),
        "op05_candidate_envelope_ref": _clean_ref(op05.get("candidate_envelope_ref"), default="rdb_op05_candidate_envelope_missing", max_length=320),
        "op05_selected_next_stage_candidate_ref": _clean_ref(op05.get("selected_next_stage_candidate_ref"), default="rdb_op05_candidate_missing", max_length=360),
        "op05_selected_next_stage_candidate_kind_ref": _clean_ref(op05.get("selected_next_stage_candidate_kind_ref"), default="rdb_op05_candidate_kind_missing", max_length=360),
        "op05_selected_next_stage_candidate_not_executed": bool(op05.get("selected_next_stage_candidate_not_executed") is True),
        "op07_material_present": isinstance(selected_regression_compileall_validation_plan, Mapping),
        "op07_contract_valid": op07_valid,
        "op07_schema_version": _clean_ref(op07.get("schema_version"), default="rdb_op07_schema_missing", max_length=260),
        "op07_material_ref": _clean_ref(op07.get("material_id"), default="rdb_op07_material_missing", max_length=260),
        "op07_status_ref": _clean_ref(op07.get("rdb_op07_status_ref"), default="rdb_op07_status_missing", max_length=320),
        "op07_ready_for_op08": op07_ready,
        "op07_changed_files_within_allowed_refs": bool(op07.get("changed_files_within_allowed_refs") is True),
        "op07_selected_regression_refs_recorded": bool(op07.get("selected_regression_refs_recorded") is True),
        "op07_compileall_refs_recorded": bool(op07.get("compileall_refs_recorded") is True),
        "op07_full_backend_suite_green_confirmed": bool(op07.get("full_backend_suite_green_confirmed") is True),
        "op07_rn_contract_green_confirmed": bool(op07.get("rn_contract_green_confirmed") is True),
        "op07_rn_real_device_modal_verified_claimed_here": bool(op07.get("rn_real_device_modal_verified_claimed_here") is True),
        "validation_summary_bodyfree_present": validation_present,
        "validation_summary_bodyfree_accepted": validation_accepted,
        "validation_summary_bodyfree_ref": _safe_mapping_copy_when_bodyfree(validation_summary_bodyfree, accepted=validation_accepted),
        "validation_summary_forbidden_payload_key_path_refs": validation_forbidden,
        "validation_summary_forbidden_payload_key_path_count": len(validation_forbidden),
        "validation_summary_body_like_value_path_refs": validation_body_like,
        "validation_summary_body_like_value_path_count": len(validation_body_like),
        "validation_summary_promotion_claim_refs": validation_promotion,
        "validation_summary_promotion_claim_ref_count": len(validation_promotion),
        "result_memo_bodyfree_present": memo_present,
        "result_memo_bodyfree_accepted": memo_accepted,
        "result_memo_bodyfree_ref": _safe_mapping_copy_when_bodyfree(result_memo_bodyfree, accepted=memo_accepted),
        "result_memo_forbidden_payload_key_path_refs": memo_forbidden,
        "result_memo_forbidden_payload_key_path_count": len(memo_forbidden),
        "result_memo_body_like_value_path_refs": memo_body_like,
        "result_memo_body_like_value_path_count": len(memo_body_like),
        "result_memo_promotion_claim_refs": memo_promotion,
        "result_memo_promotion_claim_ref_count": len(memo_promotion),
        "op07_input_forbidden_payload_key_path_refs": op07_forbidden,
        "op07_input_forbidden_payload_key_path_count": len(op07_forbidden),
        "op07_input_body_like_value_path_refs": op07_body_like,
        "op07_input_body_like_value_path_count": len(op07_body_like),
        "op07_input_promotion_claim_refs": op07_promotion,
        "op07_input_promotion_claim_ref_count": len(op07_promotion),
        "validation_command_summary_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP08_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP08_VALIDATION_COMMAND_SUMMARY_REFS),
        "target_test_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS),
        "target_test_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS),
        "selected_regression_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS),
        "selected_regression_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS),
        "compileall_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS),
        "compileall_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS),
        "target_test_result_status_ref": target_status,
        "selected_regression_result_status_ref": selected_status,
        "compileall_result_status_ref": compileall_status,
        "combined_run_status_ref": combined_status,
        "rdb_target_green_confirmed": target_status == "passed",
        "selected_regression_green_confirmed": selected_status == "passed",
        "compileall_green_confirmed": compileall_status == "passed",
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "full_backend_green_claim_not_made_here": True,
        "rn_green_claim_not_made_here": True,
        "rdb_op08_status_ref": status,
        "bodyfree_result_manual_decision_memo_closure_status_ref": status,
        "rdb_op08_allowed_status_refs": list(P7_R54_AHR_POST_MRB08_RDB_OP08_ALLOWED_STATUS_REFS),
        "rdb_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_OP08_ALLOWED_STATUS_REFS),
        **status_flags,
        "rdb_op08_reason_refs": _dedupe_clean_refs(reasons, max_length=360),
        "rdb_op08_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=360)),
        "rdb_op08_blocker_refs": _dedupe_clean_refs(blockers, max_length=360),
        "rdb_op08_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=360)),
        "rdb_selected_status_ref": _clean_ref(op04.get("rdb_status_ref"), default=P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF, max_length=320),
        "mrb_selected_branch_ref": _clean_ref(op04.get("mrb_selected_branch_ref"), default="mrb_selected_branch_missing", max_length=320),
        "dhr_op04_result_status_ref": _clean_ref(op04.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=320),
        "decision_lane_ref": _clean_ref(op04.get("decision_lane_ref"), default="rdb_op04_decision_lane_missing", max_length=320),
        "manual_decision_material_ref": _clean_ref(op04.get("branch_specific_manual_decision_material_ref"), default="rdb_op04_manual_decision_material_missing", max_length=320),
        "manual_decision_material_kind_ref": _clean_ref(op04.get("branch_specific_manual_decision_material_kind_ref"), default="rdb_op04_manual_decision_kind_missing", max_length=320),
        "manual_decision_material_present": bool(op04_valid and op04.get("manual_decision_materialized") is True),
        "selected_next_stage_candidate_ref": _clean_ref(op05.get("selected_next_stage_candidate_ref"), default="rdb_op05_candidate_missing", max_length=360),
        "selected_next_stage_candidate_kind_ref": _clean_ref(op05.get("selected_next_stage_candidate_kind_ref"), default="rdb_op05_candidate_kind_missing", max_length=360),
        "selected_next_stage_candidate_not_executed": bool(op05.get("selected_next_stage_candidate_not_executed") is True),
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "rdb_op08_does_not_recall_dhr_op04": True,
        "rdb_op08_does_not_call_dhr_op05": True,
        "rdb_op08_does_not_call_dhr_op06": True,
        "rdb_op08_does_not_execute_dmd_r52_or_release": True,
        "rdb_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "rdb_op08_does_not_materialize_p8_question_spec": True,
        "rdb_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_MRB08_RDB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MRB08_RDB_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "rdb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(data: Mapping[str, Any]) -> bool:
    """Assert RDB-OP08 body-free result manual decision memo closure contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_MRB08_RDB_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMRB08-RDB-OP08")
    if set(data) != set(P7_R54_AHR_POST_MRB08_RDB_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MRB08_RDB_OP08_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MRB08_RDB_OP08_STEP_REF, source="P7-R54-AHR-PostMRB08-RDB-OP08")
    status = data.get("rdb_op08_status_ref")
    flags = [
        data.get("rdb_op08_closed_bodyfree_stopped") is True,
        data.get("rdb_op08_waiting_for_op03_op04_op05_or_validation_refs") is True,
        data.get("rdb_op08_repair_required_for_result_manual_decision_closure_inputs") is True,
        data.get("rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun") is True,
    ]
    if status not in P7_R54_AHR_POST_MRB08_RDB_OP08_ALLOWED_STATUS_REFS or sum(flags) != 1 or data.get("bodyfree_result_manual_decision_memo_closure_status_ref") != status:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 exactly one closure status must be selected")
    for field, count_field in (
        ("validation_summary_forbidden_payload_key_path_refs", "validation_summary_forbidden_payload_key_path_count"),
        ("validation_summary_body_like_value_path_refs", "validation_summary_body_like_value_path_count"),
        ("validation_summary_promotion_claim_refs", "validation_summary_promotion_claim_ref_count"),
        ("result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count"),
        ("result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count"),
        ("result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count"),
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count"),
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("target_test_refs", "target_test_ref_count"),
        ("selected_regression_refs", "selected_regression_ref_count"),
        ("compileall_refs", "compileall_ref_count"),
        ("rdb_op08_allowed_status_refs", "rdb_op08_allowed_status_ref_count"),
        ("rdb_op08_reason_refs", "rdb_op08_reason_ref_count"),
        ("rdb_op08_blocker_refs", "rdb_op08_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP08 {count_field} changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP08_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 validation command refs changed")
    if tuple(data.get("target_test_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP07_TARGET_TEST_REFS or tuple(data.get("selected_regression_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP07_SELECTED_REGRESSION_REFS or tuple(data.get("compileall_refs") or ()) != P7_R54_AHR_POST_MRB08_RDB_OP07_COMPILEALL_REFS:
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 validation refs changed")
    for key in ("dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "rdb_op08_does_not_recall_dhr_op04", "rdb_op08_does_not_call_dhr_op05", "rdb_op08_does_not_call_dhr_op06", "rdb_op08_does_not_execute_dmd_r52_or_release", "rdb_op08_does_not_start_p5_p6_p8_p7_or_release", "rdb_op08_does_not_materialize_p8_question_spec", "rdb_op08_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution", "full_backend_green_claim_not_made_here", "rn_green_claim_not_made_here"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP08 required true boundary changed: {key}")
    for key in ("full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "p8_question_substitution_allowed", "question_text_materialized"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMRB08-RDB-OP08 forbidden green/p8 claim changed: {key}")
    if data.get("not_claimed_boundary") != _not_claimed_boundary():
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 not-claimed boundary changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP08_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_MRB08_RDB_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 implemented/not-yet steps changed")
    if status == P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF:
        if data.get("op04_contract_valid") is not True or data.get("op05_contract_valid") is not True or data.get("op07_contract_valid") is not True or data.get("op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 closed branch requires valid OP04/OP05/OP07")
        if data.get("validation_summary_bodyfree_accepted") is not True or data.get("result_memo_bodyfree_accepted") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 closed branch requires body-free validation/result memo refs")
        if data.get("manual_decision_material_present") is not True or data.get("selected_next_stage_candidate_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 closed branch requires material and non-executed candidate")
        if data.get("rdb_op08_blocker_refs") or data.get("next_required_step") != data.get("selected_next_stage_candidate_ref"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 closed branch blockers/next changed")
    else:
        if not data.get("rdb_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 non-closed branch must carry blockers")
    if status != P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        for field in ("validation_summary_forbidden_payload_key_path_refs", "validation_summary_body_like_value_path_refs", "validation_summary_promotion_claim_refs", "result_memo_forbidden_payload_key_path_refs", "result_memo_body_like_value_path_refs", "result_memo_promotion_claim_refs", "op07_input_forbidden_payload_key_path_refs", "op07_input_body_like_value_path_refs", "op07_input_promotion_claim_refs"):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostMRB08-RDB-OP08 non-blocked branch cannot carry body-free scan blockers")
    return True

# Full-title aliases for adjacent R54-AHR tests/helpers.
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08 = (
    build_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op00_scope_no_touch_no_promotion_refreeze_after_mrb_op08_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op01_mrb_op08_result_memo_closure_intake = (
    build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op01_mrb_op08_result_memo_closure_intake_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check = (
    build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op03_dhr_op04_result_manual_decision_lane_resolver = (
    build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver_contract
)

build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_branch_specific_manual_decision_materialization = (
    build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_branch_specific_manual_decision_materialization_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op05_next_stage_candidate_envelope_without_execution = (
    build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op05_next_stage_candidate_envelope_without_execution_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_bodyfree_no_touch_no_promotion_guard = (
    build_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op06_bodyfree_no_touch_no_promotion_guard_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op07_selected_regression_compileall_validation_plan = (
    build_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op07_selected_regression_compileall_validation_plan_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op07_selected_regression_compileall_validation_plan_contract
)
build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_bodyfree_result_manual_decision_memo_closure = (
    build_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure
)
assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract = (
    assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract
)
