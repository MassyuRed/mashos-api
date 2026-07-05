# -*- coding: utf-8 -*-
"""Post-DRI / DHR-OP04 manual re-intake boundary helpers for MRB-OP00〜OP08.

MRB is intentionally a thin, body-free, backend-internal boundary between the
already-closed Post-RSR16 DRI material line and a later explicit manual DHR-OP04
call.  This module implements MRB-OP00〜MRB-OP08.

* MRB-OP00 refreezes scope / no-touch / no-promotion for the Post-DRI manual
  re-intake boundary.  It does not intake DRI material and does not call DHR.
* MRB-OP01 intakes DRI-OP12 result memo closure plus DRI-OP10 deterministic
  branch material.  It confirms only whether the DRI side is ready to continue
  to MRB-OP02 candidate extraction.
* MRB-OP02 extracts and scans the DRI-OP09 adapter candidate as body-free
  material for later manual DHR-OP04 input.  It does not call DHR-OP04.
* MRB-OP03 intakes DHR-OP03 ready material for later DHR-OP04 input envelope
  assembly.  It does not treat DHR-OP03 receipt shape as actual source claim
  confirmation and does not call DHR-OP04.
* MRB-OP04 assembles an explicit body-free manual request and DHR-OP04 input
  envelope.  It still does not call DHR-OP04.
* MRB-OP05 calls the existing DHR-OP04 builder only when OP04 is ready, captures
  the body-free result, and stops without DHR-OP05/DMD/R52/P8/release promotion.
* MRB-OP06 classifies the captured DHR-OP04 result into an explicit stopped
  boundary.  It records the manual next decision but does not call anything.
* MRB-OP07 guards that the MRB implementation stayed in selected backend helper
  and target-test files without API/DB/RN/runtime/response-key/P8 surface touch.
* MRB-OP08 closes the body-free result memo boundary for OP00〜OP07,
  records validation refs and DHR-OP04 result status, and still stops before
  DHR-OP05/DMD/R52/P8/P7/release promotion.

No MRB step treats DRI closure, DRI candidate readiness, or DHR-OP03 receipt
shape as DHR-OP04 called, DHR actual source claim confirmed, DHR re-intake
executed, DHR-OP05 ready, DMD/R52 execution, P8 start, P7 completion, or release
readiness. MRB-OP05 may explicitly call DHR-OP04 at the manual boundary, but it
still never auto-calls DHR-OP05 or promotes downstream. MRB-OP08 records the
body-free closure and validation summary only; it does not execute downstream
work.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


P7_R54_AHR_POST_DRI_MRB_PHASE: Final = "P7"
P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_DRI_MRB_STEP: Final = (
    "R54-AHR-PostDRI_DHROP04ManualReintake_20260705"
)
P7_R54_AHR_POST_DRI_MRB_SCOPE: Final = (
    "p7_r54_ahr_post_dri_dhr_op04_manual_reintake_boundary"
)
P7_R54_AHR_POST_DRI_MRB_POLICY_KIND: Final = (
    "r54_ahr_post_dri_dhr_op04_manual_reintake_bodyfree_boundary"
)
P7_R54_AHR_POST_DRI_MRB_DEFAULT_REVIEW_SESSION_ID: Final = (
    dri.P7_R54_AHR_POST_RSR16_DRI_DEFAULT_REVIEW_SESSION_ID
)

P7_R54_AHR_POST_DRI_MRB_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op01_dri_result_memo_op10_branch_intake.bodyfree.v1"
)

P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF: Final = (
    "MRB-OP00_scope_no_touch_no_promotion_refreeze"
)
P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF: Final = (
    "MRB-OP01_DRI_result_memo_OP10_branch_intake"
)
P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF: Final = (
    "MRB-OP02_DRI_OP09_adapter_candidate_extraction_and_scan"
)
P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF: Final = (
    "MRB-OP03_DHR_OP03_ready_material_intake"
)
P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF: Final = (
    "MRB-OP04_manual_reintake_request_and_DHR_OP04_input_envelope"
)
P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF: Final = (
    "MRB-OP05_explicit_manual_DHR_OP04_call_and_result_capture"
)
P7_R54_AHR_POST_DRI_MRB_OP06_STEP_REF: Final = (
    "MRB-OP06_DHR_OP04_result_classifier_stop_boundary"
)
P7_R54_AHR_POST_DRI_MRB_OP07_STEP_REF: Final = (
    "MRB-OP07_no_touch_selected_regression_guard"
)
P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF: Final = (
    "MRB-OP08_bodyfree_result_memo_closure"
)
P7_R54_AHR_POST_DRI_MRB_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP06_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP07_STEP_REF,
    P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF,
)
P7_R54_AHR_POST_DRI_MRB_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF,
)
P7_R54_AHR_POST_DRI_MRB_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[1:]
)
P7_R54_AHR_POST_DRI_MRB_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:2]
)
P7_R54_AHR_POST_DRI_MRB_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[2:]
)

P7_R54_AHR_POST_DRI_MRB_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-DRI / DHR-OP04 Manual Re-intake Boundary"
)
P7_R54_AHR_POST_DRI_MRB_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-DRI / DHR-OP04 Manual Re-intake Boundary"
)
P7_R54_AHR_POST_DRI_MRB_BOUNDARY_PREFIX_REF: Final = "MRB"
P7_R54_AHR_POST_DRI_MRB_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "Manual Re-intake Boundary"
)
P7_R54_AHR_POST_DRI_MRB_CURRENT_EXPECTED_DEFAULT_FROM_DRI_REF: Final = (
    "DRI-OP12 result memo closure and DRI-OP10 branch are body-free material only; DHR-OP04 is still not called"
)
P7_R54_AHR_POST_DRI_MRB_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_mrb_op01_dri_result_memo_op10_branch_intake_without_dhr_op04_call"
)

P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF: Final = (
    "wait_for_dri_ready_candidate_or_dhr_op03_ready_material_before_manual_dhr_op04_reintake"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF: Final = (
    "repair_post_dri_to_dhr_op04_manual_reintake_boundary"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_DRI_INTAKE_REF: Final = (
    "blocked_post_dri_to_dhr_op04_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_REF: Final = (
    "manual_hold_after_dri_result_memo_op10_intake_without_downstream_promotion"
)

P7_R54_AHR_POST_DRI_MRB_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(288).zip",
    "implemented_docs": "EmlisAIの実装済み資料(97).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(16).zip",
    "cocolon_app": "Cocolon(270).zip",
    "backend": "mashos-api(183).zip",
}
P7_R54_AHR_POST_DRI_MRB_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/04_forbidden_mixing_design_and_implementation.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/11_cocolon_area_specific_do_not_break.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/14_cocolon_joint_development_and_karen_thought_boundary.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/15_trust_based_joint_development_boundary_2026_06_05.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "EmlisAIの実装済み資料/Cocolon_EmlisAI_P7_R54AHR_PostRSR16_DHRActualSourceClaimReintake_DetailedDesign_ImplementationOrder_20260705.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostDRI_DHR_OP04ManualReintake_DetailedDesign_ImplementationOrder_20260705.md",
)
P7_R54_AHR_POST_DRI_MRB_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "DHR-OP04 automatic call",
    "DHR actual source claim confirmation",
    "DHR re-intake execution",
    "DHR-OP05 automatic call",
    "DHR-OP06 automatic branch resolution",
    "DMD execution",
    "R52 actual execution",
    "actual body-full packet generation",
    "actual local-only human review execution",
    "actual operation receipt creation",
    "actual rows creation",
    "actual question need observation rows creation",
    "actual disposal / purge execution",
    "P5 finalization",
    "P6 start",
    "P8 start",
    "P8 question design",
    "P8 question implementation",
    "P7 completion",
    "release decision",
)
P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "DRI-OP12 closure is only DRI result memo closure",
    "DRI-OP10 ready branch is only material readiness for manual DHR-OP04 input",
    "DRI candidate must not be treated as DHR confirmed result",
    "MRB-OP01 does not extract OP09 candidate body yet",
    "MRB-OP01 does not call DHR-OP04",
    "MRB-OP01 does not run DHR-OP05 or later",
    "MRB-OP01 does not start P8 question design",
)
P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dri_candidate_promoted_to_dhr_confirmed",
    "dhr_op04_called_here",
    "dhr_op04_called_by_mrb",
    "dhr_actual_source_claim_confirmed_here",
    "actual_source_claim_confirmed_for_downstream_handoff",
    "receipt_claimed_as_actual_execution_by_dhr_op03",
    "dhr_actual_source_claim_reintake_executed_here",
    "dhr_op05_called_here",
    "dhr_op06_called_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
)
P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_dhr_op04_auto_call",
    "no_dhr_op05_auto_call",
    "no_dhr_op06_auto_branch_resolve",
    "no_dmd_execution",
    "no_r52_actual_execution",
    "no_p5_finalization",
    "no_p6_start",
    "no_p8_start",
    "no_p8_question_design_or_implementation",
    "no_p7_complete",
    "no_release_allowed",
)
P7_R54_AHR_POST_DRI_MRB_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
)
P7_R54_AHR_POST_DRI_MRB_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
    "local_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_POST_DRI_MRB_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_DRI_MRB_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "dri_candidate_promoted_to_dhr_confirmed",
    "dhr_op04_called_here",
    "dhr_op04_called_by_mrb",
    "dhr_op04_called_by_dri",
    "dhr_op04_called_by_dri_op10",
    "dhr_op04_called_by_dri_op12",
    "dhr_op05_called_here",
    "dhr_op06_called_here",
    "dhr_actual_source_claim_confirmed_here",
    "actual_source_claim_confirmed_for_downstream_handoff",
    "receipt_claimed_as_actual_execution_by_dhr_op03",
    "dhr_actual_source_claim_confirmed_by_dri_op10",
    "dhr_actual_source_claim_confirmed_by_dri_op12",
    "dhr_actual_source_claim_reintake_executed_here",
    "dhr_actual_source_claim_reintake_executed_by_dri_op10",
    "dhr_actual_source_claim_reintake_executed_by_dri_op12",
    "dmd_execution_started_here",
    "dmd_execution_started_by_dri_op10",
    "dmd_execution_started_by_dri_op12",
    "dmd_auto_execution_allowed",
    "manual_decision_auto_executes_downstream",
    "r52_actual_execution_started_here",
    "r52_actual_execution_started_by_dri_op10",
    "r52_actual_execution_started_by_dri_op12",
    "r52_actual_execution_confirmed",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_spec_created",
    "p8_question_design_started_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation_run_here",
    "actual_local_human_review_execution_run_here",
    "actual_local_only_human_review_execution_run_here",
    "actual_operation_receipt_created_by_helper",
    "actual_rows_created_by_helper",
    "actual_question_need_observation_rows_created_by_helper",
    "actual_disposal_purge_execution_run_here",
    "dri_candidate_promoted_to_dhr_confirmed",
    "dhr_op04_called_here",
    "dhr_op04_called_by_mrb",
    "dhr_op04_called_by_dri",
    "dhr_actual_source_claim_confirmed_here",
    "actual_source_claim_confirmed_for_downstream_handoff",
    "receipt_claimed_as_actual_execution_by_dhr_op03",
    "dhr_actual_source_claim_reintake_executed_here",
    "dhr_op05_called_here",
    "dhr_op06_called_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p7_complete",
    "release_allowed",
    "downstream_auto_execution_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)

P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_READY_FOR_OP02_REF: Final = (
    "MRB_OP01_DRI_RESULT_MEMO_OP10_READY_FOR_OP02_NO_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF: Final = (
    "MRB_OP01_WAITING_FOR_DRI_RESULT_MEMO_OR_OP10_READY_BRANCH"
)
P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF: Final = (
    "MRB_OP01_REPAIR_DRI_RESULT_MEMO_OR_OP10_BRANCH"
)
P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "MRB_OP01_BLOCKED_DRI_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF: Final = (
    "MRB_OP01_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_DRI_MRB_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_READY_FOR_OP02_REF,
    P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF,
    P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF,
    P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF,
)

P7_R54_AHR_POST_DRI_MRB_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "boundary_prefix_ref", "boundary_prefix_meaning_ref",
    "expected_from_dri_ref", "expected_next_required_step_ref", "not_stage_refs", "not_stage_ref_count",
    "support_material_refs", "support_material_ref_count", "local_received_zip_refs", "local_received_zip_ref_count",
    "body_free", "mrb_op00_scope_confirmed", "mrb_op00_no_touch_boundary_confirmed", "mrb_op00_no_promotion_boundary_confirmed",
    "source_mode_local_received_zip_only_confirmed", "github_connection_check_not_required_by_mash_instruction", "github_connection_check_performed",
    "mrb_op00_does_not_intake_dri_result_memo", "mrb_op00_does_not_extract_dri_op09_candidate", "mrb_op00_does_not_call_dhr_op04",
    "mrb_op00_does_not_execute_dhr_op05_dmd_r52_or_release", "mrb_op00_does_not_run_actual_local_human_review",
    "mrb_op00_does_not_create_receipts_rows_or_disposal", "mrb_op00_does_not_start_p5_p6_p8_p7_or_release",
    "mrb_op00_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_DRI_MRB_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed", "op00_no_touch_boundary_confirmed", "op00_no_promotion_boundary_confirmed", "op00_contract_valid",
    "dri_op12_result_memo_present", "dri_op12_contract_valid", "dri_op12_schema_version", "dri_op12_operation_step_ref", "dri_op12_material_ref", "dri_op12_status_ref", "dri_op12_result_memo_bodyfree_closed", "dri_op12_next_required_step",
    "dri_op12_selected_dri_branch_ref", "dri_op12_selected_dri_next_required_step", "dri_op12_selected_dri_branch_is_ready_material_only", "dri_op12_target_tests_all_required_green", "dri_op12_selected_regression_all_required_green", "dri_op12_services_ai_inference_compileall_ok",
    "dri_op12_dhr_op04_called", "dri_op12_dhr_actual_source_claim_confirmed", "dri_op12_dhr_reintake_executed", "dri_op12_p8_start_allowed", "dri_op12_release_allowed",
    "dri_op10_branch_present", "dri_op10_contract_valid", "dri_op10_schema_version", "dri_op10_operation_step_ref", "dri_op10_material_ref", "dri_op10_branch_ref", "dri_op10_next_required_step",
    "dri_op10_ready_for_dhr_material", "dri_op10_waiting", "dri_op10_repair_required", "dri_op10_blocked", "dri_op10_manual_hold", "dri_op10_adapter_candidate_materialized", "dri_op10_adapter_candidate_for_manual_dhr_op04_input_only", "dri_op10_adapter_candidate_not_dhr_confirmed", "dri_op10_downstream_auto_execution_allowed",
    "dri_op10_dhr_op04_called", "dri_op10_dhr_actual_source_claim_confirmed", "dri_op10_dhr_reintake_executed", "dri_op10_dmd_execution_started", "dri_op10_r52_actual_execution_started",
    "dri_input_forbidden_payload_key_path_refs", "dri_input_forbidden_payload_key_path_count", "dri_input_body_like_value_path_refs", "dri_input_body_like_value_path_count", "dri_input_promotion_claim_refs", "dri_input_promotion_claim_ref_count",
    "mrb_op01_status_ref", "dri_result_memo_op10_branch_intake_status_ref", "mrb_op01_allowed_status_refs", "mrb_op01_allowed_status_ref_count",
    "mrb_op01_ready_for_mrb_op02", "mrb_op01_waiting_for_dri_ready_material", "mrb_op01_repair_required", "mrb_op01_bodyfree_leak_promotion_or_autorun_blocked", "mrb_op01_manual_hold_unresolved_no_promotion",
    "mrb_op01_reason_refs", "mrb_op01_reason_ref_count", "mrb_op01_blocker_refs", "mrb_op01_blocker_ref_count",
    "dri_result_memo_closure_is_not_actual_review_complete", "dri_result_memo_closure_is_not_dhr_op04_call", "dri_result_memo_closure_is_not_dhr_actual_source_claim_confirmed", "dri_result_memo_closure_is_not_dhr_reintake_execution", "dri_result_memo_closure_is_not_p8_start", "dri_result_memo_closure_is_not_p7_complete", "dri_result_memo_closure_is_not_release_ready",
    "dri_op10_ready_branch_is_material_only", "dri_op10_ready_branch_is_not_downstream_auto_execution", "mrb_op01_does_not_extract_dri_op09_candidate_body", "mrb_op01_does_not_call_dhr_op04", "mrb_op01_does_not_execute_dhr_op05_dmd_r52_or_release", "mrb_op01_does_not_start_p5_p6_p8_p7_or_release", "mrb_op01_does_not_change_api_db_rn_runtime_response_key", "mrb_op01_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_DRI_MRB_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op02_dri_op09_adapter_candidate_extraction_and_scan.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op03_dhr_op03_ready_material_intake.bodyfree.v1"
)

P7_R54_AHR_POST_DRI_MRB_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:3]
)
P7_R54_AHR_POST_DRI_MRB_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[3:]
)
P7_R54_AHR_POST_DRI_MRB_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:4]
)
P7_R54_AHR_POST_DRI_MRB_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[4:]
)

P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_READY_FOR_OP03_REF: Final = (
    "MRB_OP02_DRI_OP09_ADAPTER_CANDIDATE_READY_FOR_OP03_NO_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF: Final = (
    "MRB_OP02_WAITING_FOR_DRI_OP09_ADAPTER_CANDIDATE_OR_OP01_READY"
)
P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF: Final = (
    "MRB_OP02_REPAIR_DRI_OP09_ADAPTER_CANDIDATE_BEFORE_DHR_OP04_INPUT"
)
P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "MRB_OP02_BLOCKED_DRI_OP09_CANDIDATE_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF: Final = (
    "MRB_OP02_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_DRI_MRB_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_READY_FOR_OP03_REF,
    P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF,
    P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF,
    P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF,
)

P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_READY_FOR_OP04_ENVELOPE_REF: Final = (
    "MRB_OP03_DHR_OP03_READY_FOR_OP04_INPUT_ENVELOPE_NO_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF: Final = (
    "MRB_OP03_WAITING_FOR_DHR_OP03_READY_MATERIAL_OR_MRB_OP02_READY"
)
P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF: Final = (
    "MRB_OP03_REPAIR_DHR_OP03_READY_MATERIAL_BEFORE_DHR_OP04_INPUT"
)
P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "MRB_OP03_BLOCKED_DHR_OP03_MATERIAL_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_MANUAL_HOLD_REF: Final = (
    "MRB_OP03_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_DRI_MRB_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_READY_FOR_OP04_ENVELOPE_REF,
    P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF,
    P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF,
    P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_MANUAL_HOLD_REF,
)

P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP02_DRI_OP09_REF: Final = (
    "repair_post_dri_to_dhr_op04_dri_op09_adapter_candidate_before_manual_reintake"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP02_DRI_OP09_REF: Final = (
    "blocked_post_dri_to_dhr_op04_dri_op09_adapter_candidate_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP03_DHR_OP03_REF: Final = (
    "repair_post_dri_to_dhr_op04_dhr_op03_ready_material_before_manual_reintake"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP03_DHR_OP03_REF: Final = (
    "blocked_post_dri_to_dhr_op04_dhr_op03_material_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP02_REF: Final = (
    "manual_hold_after_dri_op09_candidate_extraction_without_downstream_promotion"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP03_REF: Final = (
    "manual_hold_after_dhr_op03_ready_material_intake_without_downstream_promotion"
)

P7_R54_AHR_POST_DRI_MRB_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_next_required_step", "op01_contract_valid", "op01_ready_for_mrb_op02", "op01_status_ref",
    "dri_op09_candidate_material_present", "dri_op09_contract_valid", "dri_op09_schema_version", "dri_op09_operation_step_ref", "dri_op09_material_ref", "dri_op09_status_ref", "dri_op09_next_required_step",
    "dri_op09_adapter_candidate_materialized", "dri_op09_adapter_candidate_materialized_bodyfree", "dri_op09_adapter_candidate_for_manual_dhr_op04_input_only", "dri_op09_adapter_candidate_not_dhr_confirmed",
    "dri_op09_does_not_call_dhr_op04", "dri_op09_does_not_confirm_dhr_actual_source_claim", "dri_op09_does_not_execute_dhr_reintake", "dri_op09_downstream_auto_execution_allowed",
    "external_actual_operation_evidence_claim_bodyfree_optional_present", "external_actual_operation_evidence_claim_bodyfree_optional", "external_actual_operation_evidence_claim_bodyfree_optional_key_refs", "external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count",
    "adapter_candidate_schema_version", "adapter_candidate_material_kind", "adapter_candidate_source_kind_ref", "adapter_candidate_actual_source_claim_source_kind_ref", "adapter_candidate_actual_source_claim_origin_ref",
    "adapter_candidate_actual_source_claim_bodyfree", "adapter_candidate_actual_local_only_human_review_by_person_confirmed", "adapter_candidate_actual_human_review_executed_by_person",
    "adapter_candidate_operation_receipt_bodyfree_ref", "adapter_candidate_disposal_purge_receipt_bodyfree_ref", "adapter_candidate_rsr_op15_branch_ref", "adapter_candidate_rsr_op16_status_ref",
    "adapter_candidate_sanitized_review_result_row_count", "adapter_candidate_rating_row_count", "adapter_candidate_question_need_observation_row_count",
    "adapter_candidate_readable_key_refs", "adapter_candidate_readable_key_ref_count", "adapter_candidate_key_set_valid", "adapter_candidate_source_kind_valid", "adapter_candidate_origin_valid", "adapter_candidate_required_true_flags_valid", "adapter_candidate_required_false_flags_valid", "adapter_candidate_row_counts_valid", "adapter_candidate_bodyfree_scan_clear", "adapter_candidate_promotion_scan_clear",
    "adapter_candidate_forbidden_payload_key_path_refs", "adapter_candidate_forbidden_payload_key_path_count", "adapter_candidate_body_like_value_path_refs", "adapter_candidate_body_like_value_path_count", "adapter_candidate_promotion_claim_refs", "adapter_candidate_promotion_claim_ref_count", "adapter_candidate_contract_or_shape_blocker_refs", "adapter_candidate_contract_or_shape_blocker_ref_count",
    "mrb_op02_status_ref", "dri_op09_adapter_candidate_extraction_status_ref", "mrb_op02_allowed_status_refs", "mrb_op02_allowed_status_ref_count",
    "mrb_op02_ready_for_mrb_op03", "mrb_op02_waiting_for_dri_op09_candidate", "mrb_op02_repair_required", "mrb_op02_bodyfree_leak_promotion_or_autorun_blocked", "mrb_op02_manual_hold_unresolved_no_promotion",
    "mrb_op02_reason_refs", "mrb_op02_reason_ref_count", "mrb_op02_blocker_refs", "mrb_op02_blocker_ref_count",
    "dri_op09_candidate_is_only_dhr_op04_input_material", "dri_op09_candidate_is_not_dhr_op04_call", "dri_op09_candidate_is_not_dhr_actual_source_claim_confirmed", "dri_op09_candidate_is_not_dhr_reintake_execution", "dri_op09_candidate_is_not_dhr_op05_ready", "mrb_op02_does_not_intake_dhr_op03_material", "mrb_op02_does_not_call_dhr_op04", "mrb_op02_does_not_execute_dhr_op05_dmd_r52_or_release", "mrb_op02_does_not_start_p5_p6_p8_p7_or_release", "mrb_op02_does_not_change_api_db_rn_runtime_response_key", "mrb_op02_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DRI_MRB_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_next_required_step", "op02_contract_valid", "op02_ready_for_mrb_op03", "op02_status_ref",
    "dhr_op03_ready_material_present", "dhr_op03_contract_valid", "dhr_op03_schema_version", "dhr_op03_operation_step_ref", "dhr_op03_material_ref", "dhr_op03_status_ref", "dhr_op03_next_required_step",
    "dhr_op03_ready", "dhr_op03_ready_for_actual_source_claim_separation", "dhr_op03_waiting_for_complete_evidence", "dhr_op03_repair_required",
    "dhr_op03_receipt_shape_valid", "dhr_op03_receipt_schema_version_matches_dmd", "dhr_op03_receipt_source_kind_valid", "dhr_op03_receipt_count_fields_are_24", "dhr_op03_receipt_required_true_fields_passed", "dhr_op03_receipt_body_free", "dhr_op03_receipt_claimed_as_actual_execution_by_dhr_op03", "dhr_op03_actual_source_claim_confirmed_for_downstream_handoff",
    "dhr_op03_ready_material_bodyfree", "dhr_op03_ready_material_schema_version", "dhr_op03_ready_material_source_kind_ref", "dhr_op03_ready_material_key_refs", "dhr_op03_ready_material_key_ref_count",
    "dhr_op03_material_forbidden_payload_key_path_refs", "dhr_op03_material_forbidden_payload_key_path_count", "dhr_op03_material_body_like_value_path_refs", "dhr_op03_material_body_like_value_path_count", "dhr_op03_material_promotion_claim_refs", "dhr_op03_material_promotion_claim_ref_count", "dhr_op03_contract_or_shape_blocker_refs", "dhr_op03_contract_or_shape_blocker_ref_count",
    "mrb_op03_status_ref", "dhr_op03_ready_material_intake_status_ref", "mrb_op03_allowed_status_refs", "mrb_op03_allowed_status_ref_count",
    "mrb_op03_ready_for_mrb_op04", "mrb_op03_waiting_for_dhr_op03_ready_material", "mrb_op03_repair_required", "mrb_op03_bodyfree_leak_promotion_or_autorun_blocked", "mrb_op03_manual_hold_unresolved_no_promotion",
    "mrb_op03_reason_refs", "mrb_op03_reason_ref_count", "mrb_op03_blocker_refs", "mrb_op03_blocker_ref_count",
    "dhr_op03_receipt_shape_is_not_actual_source_claim_confirmation", "dhr_op03_ready_material_is_not_dhr_op04_call", "dhr_op03_ready_material_is_not_dhr_actual_source_claim_confirmed", "dhr_op03_ready_material_is_not_dhr_reintake_execution", "dhr_op03_ready_material_is_not_dhr_op05_ready", "mrb_op03_does_not_build_dhr_op04_envelope", "mrb_op03_does_not_call_dhr_op04", "mrb_op03_does_not_execute_dhr_op05_dmd_r52_or_release", "mrb_op03_does_not_start_p5_p6_p8_p7_or_release", "mrb_op03_does_not_change_api_db_rn_runtime_response_key", "mrb_op03_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(value, default=P7_R54_AHR_POST_DRI_MRB_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DRI_MRB_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DRI_MRB_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS}


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
            if key_text in P7_R54_AHR_POST_DRI_MRB_FORBIDDEN_PAYLOAD_KEY_REFS:
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
        "raw_input", "comment_text", "returned_surface", "question_text", "draft_question",
        "answer_text", "reviewer_note", "reviewer_free_text", "body_full_packet", "local_path",
        "file_path", "absolute_path", "relative_path", "input_hash", "body_hash", "sha256",
        "terminal", "stdout", "stderr", "traceback",
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


def _scan_promotion_claim_refs(value: Any, *, path: str = "payload") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_DRI_MRB_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _assert_public_contract_false(data: Mapping[str, Any], *, source: str) -> None:
    if data.get("public_contract") != public_contract_flags():
        raise ValueError(f"{source} public contract changed")


def _assert_false_mapping(data: Mapping[str, Any], *, field: str, source: str) -> None:
    mapping = data.get(field)
    if not isinstance(mapping, Mapping):
        raise ValueError(f"{source} {field} must be a mapping")
    true_keys = [str(key) for key, value in mapping.items() if value is True]
    if true_keys:
        raise ValueError(f"{source} {field} must keep false markers: {true_keys[:6]}")


def _assert_base_bodyfree_boundary(data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_DRI_MRB_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_DRI_MRB_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_DRI_MRB_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_DRI_MRB_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref or data.get("policy_section") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git connection flags changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must stay body-free")
    _assert_public_contract_false(data, source=source)
    _assert_false_mapping(data, field="mrb_no_touch_contract", source=source)
    _assert_false_mapping(data, field="body_free_markers", source=source)
    for key in P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")
    if any(key in P7_R54_AHR_POST_DRI_MRB_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")


def _dri_op12_contract_valid(dri_op12: Mapping[str, Any] | None) -> bool:
    if not isinstance(dri_op12, Mapping):
        return False
    try:
        return dri.assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(dri_op12) is True
    except ValueError:
        return False


def _dri_op10_contract_valid(dri_op10: Mapping[str, Any] | None) -> bool:
    if not isinstance(dri_op10, Mapping):
        return False
    try:
        return dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(dri_op10) is True
    except ValueError:
        return False


def _op01_status_reason_blocker_next(
    *,
    op00_valid: bool,
    op12_present: bool,
    op12_contract_valid: bool,
    op12_status_ref: str,
    op12_closed: bool,
    op12_downstream_claimed: bool,
    op10_present: bool,
    op10_contract_valid: bool,
    op10_branch_ref: str,
    op10_ready: bool,
    op10_waiting: bool,
    op10_repair: bool,
    op10_blocked: bool,
    op10_manual_hold: bool,
    op10_downstream_claimed: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("dri_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("dri_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("dri_input_promotion_or_autorun_claim_detected")
    if op12_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF:
        blockers.append("dri_op12_status_bodyfree_leak_promotion_or_no_touch_blocked")
    if op10_blocked or op10_branch_ref == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF:
        blockers.append("dri_op10_branch_bodyfree_leak_or_promotion_blocked")
    if op12_downstream_claimed:
        blockers.append("dri_op12_downstream_promotion_or_dhr_call_claimed")
    if op10_downstream_claimed:
        blockers.append("dri_op10_downstream_promotion_or_dhr_call_claimed")
    if blockers:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["dri_result_memo_or_op10_branch_failed_bodyfree_no_promotion_boundary_before_mrb_op02"],
            _dedupe_clean_refs(blockers, max_length=300),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_DRI_INTAKE_REF,
        )
    if not op00_valid:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF,
            ["mrb_op00_contract_invalid_before_dri_intake"],
            ["mrb_op00_contract_invalid"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF,
        )
    if not op12_present or not op10_present:
        missing = []
        if not op12_present:
            missing.append("dri_op12_result_memo_missing")
        if not op10_present:
            missing.append("dri_op10_branch_resolver_missing")
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF,
            ["dri_result_memo_or_op10_branch_not_provided_yet"],
            missing,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if not op12_contract_valid or not op10_contract_valid:
        invalid = []
        if not op12_contract_valid:
            invalid.append("dri_op12_result_memo_contract_invalid")
        if not op10_contract_valid:
            invalid.append("dri_op10_branch_resolver_contract_invalid")
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF,
            ["dri_result_memo_or_op10_contract_repair_required_before_mrb_op02"],
            invalid,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF,
        )
    if op12_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF or op10_waiting:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF,
            ["dri_result_memo_or_op10_branch_waiting_before_mrb_op02"],
            ["dri_result_memo_or_op10_branch_waiting"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if op12_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF or op10_repair:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF,
            ["dri_result_memo_or_op10_branch_repair_required_before_mrb_op02"],
            ["dri_result_memo_or_op10_branch_repair_required"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF,
        )
    if op10_manual_hold:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF,
            ["dri_op10_manual_hold_unresolved_no_promotion"],
            ["dri_op10_manual_hold_unresolved"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_REF,
        )
    if op12_closed and op10_ready and op10_branch_ref == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_READY_FOR_OP02_REF,
            ["dri_op12_closed_and_dri_op10_ready_material_only_for_mrb_op02"],
            [],
            P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF,
        ["dri_result_memo_op10_branch_unresolved_without_promotion"],
        ["dri_result_memo_op10_branch_unresolved"],
        P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_REF,
    )


def build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build MRB-OP00 body-free scope / no-touch / no-promotion refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_DRI_MRB_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_DRI_MRB_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_DRI_MRB_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_DRI_MRB_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_dri_ref": P7_R54_AHR_POST_DRI_MRB_CURRENT_EXPECTED_DEFAULT_FROM_DRI_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_DRI_MRB_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_DRI_MRB_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_DRI_MRB_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_DRI_MRB_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_DRI_MRB_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_DRI_MRB_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_DRI_MRB_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "mrb_op00_scope_confirmed": True,
        "mrb_op00_no_touch_boundary_confirmed": True,
        "mrb_op00_no_promotion_boundary_confirmed": True,
        "source_mode_local_received_zip_only_confirmed": True,
        "github_connection_check_not_required_by_mash_instruction": True,
        "github_connection_check_performed": False,
        "mrb_op00_does_not_intake_dri_result_memo": True,
        "mrb_op00_does_not_extract_dri_op09_candidate": True,
        "mrb_op00_does_not_call_dhr_op04": True,
        "mrb_op00_does_not_execute_dhr_op05_dmd_r52_or_release": True,
        "mrb_op00_does_not_run_actual_local_human_review": True,
        "mrb_op00_does_not_create_receipts_rows_or_disposal": True,
        "mrb_op00_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert MRB-OP00 scope / no-touch / no-promotion refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP00_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP00")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DRI_MRB_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DRI_MRB_OP00_STEP_REF,
        source="P7-R54-AHR-PostDRI-MRB-OP00",
    )
    for key in (
        "mrb_op00_scope_confirmed",
        "mrb_op00_no_touch_boundary_confirmed",
        "mrb_op00_no_promotion_boundary_confirmed",
        "source_mode_local_received_zip_only_confirmed",
        "github_connection_check_not_required_by_mash_instruction",
        "mrb_op00_does_not_intake_dri_result_memo",
        "mrb_op00_does_not_extract_dri_op09_candidate",
        "mrb_op00_does_not_call_dhr_op04",
        "mrb_op00_does_not_execute_dhr_op05_dmd_r52_or_release",
        "mrb_op00_does_not_run_actual_local_human_review",
        "mrb_op00_does_not_create_receipts_rows_or_disposal",
        "mrb_op00_does_not_start_p5_p6_p8_p7_or_release",
        "mrb_op00_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP00 required true boundary changed: {key}")
    if data.get("github_connection_check_performed") is not False:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 git check must stay unperformed")
    if data.get("selected_design_target_ref") != P7_R54_AHR_POST_DRI_MRB_SELECTED_DESIGN_TARGET_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 selected design target changed")
    if data.get("boundary_prefix_ref") != P7_R54_AHR_POST_DRI_MRB_BOUNDARY_PREFIX_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 boundary prefix changed")
    if data.get("expected_next_required_step_ref") != P7_R54_AHR_POST_DRI_MRB_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 expected next step changed")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP00 {count_field} changed")
    if data.get("local_received_zip_ref_count") != len(data.get("local_received_zip_refs") or {}):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 local received zip count changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP00 next step changed")
    return True


def build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    dri_op12_result_memo_closure: Mapping[str, Any] | None = None,
    dri_op10_deterministic_branch_resolver: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MRB-OP01 body-free DRI result memo / OP10 branch intake material."""

    op12_map = dri_op12_result_memo_closure if isinstance(dri_op12_result_memo_closure, Mapping) else {}
    op10_map = dri_op10_deterministic_branch_resolver if isinstance(dri_op10_deterministic_branch_resolver, Mapping) else {}
    session_id = _safe_review_session_id(
        review_session_id
        if review_session_id is not None
        else (op12_map.get("review_session_id") or op10_map.get("review_session_id"))
    )
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze(review_session_id=session_id)
    try:
        op00_valid = assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract(op00) is True
    except ValueError:
        op00_valid = False

    op12_present = isinstance(dri_op12_result_memo_closure, Mapping)
    op10_present = isinstance(dri_op10_deterministic_branch_resolver, Mapping)
    op12_contract_valid = _dri_op12_contract_valid(dri_op12_result_memo_closure)
    op10_contract_valid = _dri_op10_contract_valid(dri_op10_deterministic_branch_resolver)
    op12_status_ref = _clean_ref(op12_map.get("dri_op12_status_ref"), default="dri_op12_status_missing", max_length=260)
    op10_branch_ref = _clean_ref(op10_map.get("dri_branch_ref"), default="dri_op10_branch_missing", max_length=260)
    op12_closed = bool(op12_map.get("dri_op12_result_memo_bodyfree_closed") is True)
    op10_ready = bool(op10_map.get("ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution") is True)
    op10_waiting = bool(op10_map.get("waiting_for_supplied_receipts_or_complete_candidate") is True)
    op10_repair = bool(op10_map.get("repair_required_before_dhr_reintake_material") is True)
    op10_blocked = bool(op10_map.get("bodyfree_leak_or_promotion_blocked") is True)
    op10_manual_hold = bool(op10_map.get("manual_hold_unresolved_no_promotion") is True)
    forbidden_paths = _dedupe_clean_refs(
        [
            *_scan_forbidden_payload_key_paths(op12_map, path="dri_op12_result_memo"),
            *_scan_forbidden_payload_key_paths(op10_map, path="dri_op10_branch"),
        ],
        max_length=360,
    )
    body_like_paths = _dedupe_clean_refs(
        [
            *_scan_body_like_value_paths(op12_map, path="dri_op12_result_memo"),
            *_scan_body_like_value_paths(op10_map, path="dri_op10_branch"),
        ],
        max_length=360,
    )
    promotion_claims = _dedupe_clean_refs(
        [
            *_scan_promotion_claim_refs(op12_map, path="dri_op12_result_memo"),
            *_scan_promotion_claim_refs(op10_map, path="dri_op10_branch"),
        ],
        max_length=360,
    )
    op12_downstream_claimed = any(
        op12_map.get(key) is True
        for key in (
            "dhr_op04_called_by_dri_op12",
            "dhr_actual_source_claim_confirmed_by_dri_op12",
            "dhr_actual_source_claim_reintake_executed_by_dri_op12",
            "p8_start_allowed",
            "release_allowed",
        )
    )
    op10_downstream_claimed = any(
        op10_map.get(key) is True
        for key in (
            "dhr_op04_called_by_dri_op10",
            "dhr_actual_source_claim_confirmed_by_dri_op10",
            "dhr_actual_source_claim_reintake_executed_by_dri_op10",
            "dmd_execution_started_by_dri_op10",
            "r52_actual_execution_started_by_dri_op10",
            "downstream_auto_execution_allowed",
            "p8_start_allowed",
            "release_allowed",
        )
    )
    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        op00_valid=op00_valid,
        op12_present=op12_present,
        op12_contract_valid=op12_contract_valid,
        op12_status_ref=op12_status_ref,
        op12_closed=op12_closed,
        op12_downstream_claimed=op12_downstream_claimed,
        op10_present=op10_present,
        op10_contract_valid=op10_contract_valid,
        op10_branch_ref=op10_branch_ref,
        op10_ready=op10_ready,
        op10_waiting=op10_waiting,
        op10_repair=op10_repair,
        op10_blocked=op10_blocked,
        op10_manual_hold=op10_manual_hold,
        op10_downstream_claimed=op10_downstream_claimed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_READY_FOR_OP02_REF
    waiting = status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF
    repair = status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF
    blocked = status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    manual_hold = status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="mrb_op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="mrb_op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="mrb_op00_next_required_step_missing", max_length=260),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("mrb_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("mrb_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("mrb_op00_no_promotion_boundary_confirmed") is True),
        "op00_contract_valid": op00_valid,
        "dri_op12_result_memo_present": op12_present,
        "dri_op12_contract_valid": op12_contract_valid,
        "dri_op12_schema_version": _clean_ref(op12_map.get("schema_version"), default="dri_op12_schema_missing", max_length=260),
        "dri_op12_operation_step_ref": _clean_ref(op12_map.get("operation_step_ref"), default="dri_op12_operation_step_missing", max_length=260),
        "dri_op12_material_ref": _clean_ref(op12_map.get("material_id"), default="dri_op12_material_missing", max_length=260),
        "dri_op12_status_ref": op12_status_ref,
        "dri_op12_result_memo_bodyfree_closed": op12_closed,
        "dri_op12_next_required_step": _clean_ref(op12_map.get("next_required_step"), default="dri_op12_next_required_step_missing", max_length=260),
        "dri_op12_selected_dri_branch_ref": _clean_ref(op12_map.get("selected_dri_branch_ref"), default="dri_op12_selected_branch_missing", max_length=260),
        "dri_op12_selected_dri_next_required_step": _clean_ref(op12_map.get("selected_dri_next_required_step"), default="dri_op12_selected_next_step_missing", max_length=260),
        "dri_op12_selected_dri_branch_is_ready_material_only": bool(op12_map.get("selected_dri_branch_is_ready_material_only") is True),
        "dri_op12_target_tests_all_required_green": bool(op12_map.get("target_tests_all_required_green") is True),
        "dri_op12_selected_regression_all_required_green": bool(op12_map.get("selected_regression_all_required_green") is True),
        "dri_op12_services_ai_inference_compileall_ok": bool(op12_map.get("services_ai_inference_compileall_ok") is True),
        "dri_op12_dhr_op04_called": False,
        "dri_op12_dhr_actual_source_claim_confirmed": False,
        "dri_op12_dhr_reintake_executed": False,
        "dri_op12_p8_start_allowed": False,
        "dri_op12_release_allowed": False,
        "dri_op10_branch_present": op10_present,
        "dri_op10_contract_valid": op10_contract_valid,
        "dri_op10_schema_version": _clean_ref(op10_map.get("schema_version"), default="dri_op10_schema_missing", max_length=260),
        "dri_op10_operation_step_ref": _clean_ref(op10_map.get("operation_step_ref"), default="dri_op10_operation_step_missing", max_length=260),
        "dri_op10_material_ref": _clean_ref(op10_map.get("material_id"), default="dri_op10_material_missing", max_length=260),
        "dri_op10_branch_ref": op10_branch_ref,
        "dri_op10_next_required_step": _clean_ref(op10_map.get("next_required_step"), default="dri_op10_next_required_step_missing", max_length=260),
        "dri_op10_ready_for_dhr_material": op10_ready,
        "dri_op10_waiting": op10_waiting,
        "dri_op10_repair_required": op10_repair,
        "dri_op10_blocked": op10_blocked,
        "dri_op10_manual_hold": op10_manual_hold,
        "dri_op10_adapter_candidate_materialized": bool(op10_map.get("adapter_candidate_materialized") is True),
        "dri_op10_adapter_candidate_for_manual_dhr_op04_input_only": bool(op10_map.get("adapter_candidate_for_manual_dhr_op04_input_only") is True),
        "dri_op10_adapter_candidate_not_dhr_confirmed": bool(op10_map.get("adapter_candidate_not_dhr_confirmed") is True),
        "dri_op10_downstream_auto_execution_allowed": False,
        "dri_op10_dhr_op04_called": False,
        "dri_op10_dhr_actual_source_claim_confirmed": False,
        "dri_op10_dhr_reintake_executed": False,
        "dri_op10_dmd_execution_started": False,
        "dri_op10_r52_actual_execution_started": False,
        "dri_input_forbidden_payload_key_path_refs": forbidden_paths,
        "dri_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "dri_input_body_like_value_path_refs": body_like_paths,
        "dri_input_body_like_value_path_count": len(body_like_paths),
        "dri_input_promotion_claim_refs": promotion_claims,
        "dri_input_promotion_claim_ref_count": len(promotion_claims),
        "mrb_op01_status_ref": status_ref,
        "dri_result_memo_op10_branch_intake_status_ref": status_ref,
        "mrb_op01_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP01_ALLOWED_STATUS_REFS),
        "mrb_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP01_ALLOWED_STATUS_REFS),
        "mrb_op01_ready_for_mrb_op02": ready,
        "mrb_op01_waiting_for_dri_ready_material": waiting,
        "mrb_op01_repair_required": repair,
        "mrb_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "mrb_op01_manual_hold_unresolved_no_promotion": manual_hold,
        "mrb_op01_reason_refs": reasons,
        "mrb_op01_reason_ref_count": len(reasons),
        "mrb_op01_blocker_refs": blockers,
        "mrb_op01_blocker_ref_count": len(blockers),
        "dri_result_memo_closure_is_not_actual_review_complete": True,
        "dri_result_memo_closure_is_not_dhr_op04_call": True,
        "dri_result_memo_closure_is_not_dhr_actual_source_claim_confirmed": True,
        "dri_result_memo_closure_is_not_dhr_reintake_execution": True,
        "dri_result_memo_closure_is_not_p8_start": True,
        "dri_result_memo_closure_is_not_p7_complete": True,
        "dri_result_memo_closure_is_not_release_ready": True,
        "dri_op10_ready_branch_is_material_only": True,
        "dri_op10_ready_branch_is_not_downstream_auto_execution": True,
        "mrb_op01_does_not_extract_dri_op09_candidate_body": True,
        "mrb_op01_does_not_call_dhr_op04": True,
        "mrb_op01_does_not_execute_dhr_op05_dmd_r52_or_release": True,
        "mrb_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "mrb_op01_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert MRB-OP01 DRI result memo / OP10 branch intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP01_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP01")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DRI_MRB_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF,
        source="P7-R54-AHR-PostDRI-MRB-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_DRI_MRB_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 OP00 next step changed")
    if data.get("dri_result_memo_op10_branch_intake_status_ref") != data.get("mrb_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 status alias changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "dri_result_memo_closure_is_not_actual_review_complete",
        "dri_result_memo_closure_is_not_dhr_op04_call",
        "dri_result_memo_closure_is_not_dhr_actual_source_claim_confirmed",
        "dri_result_memo_closure_is_not_dhr_reintake_execution",
        "dri_result_memo_closure_is_not_p8_start",
        "dri_result_memo_closure_is_not_p7_complete",
        "dri_result_memo_closure_is_not_release_ready",
        "dri_op10_ready_branch_is_material_only",
        "dri_op10_ready_branch_is_not_downstream_auto_execution",
        "mrb_op01_does_not_extract_dri_op09_candidate_body",
        "mrb_op01_does_not_call_dhr_op04",
        "mrb_op01_does_not_execute_dhr_op05_dmd_r52_or_release",
        "mrb_op01_does_not_start_p5_p6_p8_p7_or_release",
        "mrb_op01_does_not_change_api_db_rn_runtime_response_key",
        "mrb_op01_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP01 required true boundary changed: {key}")
    for key in (
        "dri_op12_dhr_op04_called",
        "dri_op12_dhr_actual_source_claim_confirmed",
        "dri_op12_dhr_reintake_executed",
        "dri_op12_p8_start_allowed",
        "dri_op12_release_allowed",
        "dri_op10_downstream_auto_execution_allowed",
        "dri_op10_dhr_op04_called",
        "dri_op10_dhr_actual_source_claim_confirmed",
        "dri_op10_dhr_reintake_executed",
        "dri_op10_dmd_execution_started",
        "dri_op10_r52_actual_execution_started",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP01 DRI downstream claim promoted: {key}")
    for field, count_field in (
        ("dri_input_forbidden_payload_key_path_refs", "dri_input_forbidden_payload_key_path_count"),
        ("dri_input_body_like_value_path_refs", "dri_input_body_like_value_path_count"),
        ("dri_input_promotion_claim_refs", "dri_input_promotion_claim_ref_count"),
        ("mrb_op01_reason_refs", "mrb_op01_reason_ref_count"),
        ("mrb_op01_blocker_refs", "mrb_op01_blocker_ref_count"),
        ("mrb_op01_allowed_status_refs", "mrb_op01_allowed_status_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP01 {count_field} changed")
    if tuple(data.get("mrb_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 allowed status refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 not-yet steps changed")
    status_ref = data.get("mrb_op01_status_ref")
    flags = [
        data.get("mrb_op01_ready_for_mrb_op02") is True,
        data.get("mrb_op01_waiting_for_dri_ready_material") is True,
        data.get("mrb_op01_repair_required") is True,
        data.get("mrb_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("mrb_op01_manual_hold_unresolved_no_promotion") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DRI_MRB_OP01_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 exactly one status branch must be selected")
    if status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_READY_FOR_OP02_REF:
        if data.get("op00_contract_valid") is not True or data.get("dri_op12_contract_valid") is not True or data.get("dri_op10_contract_valid") is not True:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 ready branch requires OP00/DRI contracts valid")
        if data.get("dri_op12_result_memo_bodyfree_closed") is not True or data.get("dri_op10_ready_for_dhr_material") is not True:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 ready branch requires DRI OP12 closed and OP10 ready")
        if data.get("dri_input_forbidden_payload_key_path_refs") or data.get("dri_input_body_like_value_path_refs") or data.get("dri_input_promotion_claim_refs") or data.get("mrb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF:
        if data.get("mrb_op01_waiting_for_dri_ready_material") is not True or not data.get("mrb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 waiting branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF:
        if data.get("mrb_op01_repair_required") is not True or not data.get("mrb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if data.get("mrb_op01_bodyfree_leak_promotion_or_autorun_blocked") is not True or not data.get("mrb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_DRI_INTAKE_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 blocked next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF:
        if data.get("mrb_op01_manual_hold_unresolved_no_promotion") is not True or not data.get("mrb_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 manual hold branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP01 manual hold next step changed")
    return True



def _dri_op09_contract_valid(dri_op09: Mapping[str, Any] | None) -> bool:
    if not isinstance(dri_op09, Mapping):
        return False
    try:
        return dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(dri_op09) is True
    except ValueError:
        return False


def _dhr_op03_contract_valid(dhr_op03: Mapping[str, Any] | None) -> bool:
    if not isinstance(dhr_op03, Mapping):
        return False
    try:
        return dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(dhr_op03) is True
    except ValueError:
        return False


def _op02_status_reason_blocker_next(
    *,
    op01_present: bool,
    op01_contract_valid: bool,
    op01_ready: bool,
    op01_status_ref: str,
    op09_present: bool,
    op09_contract_valid: bool,
    op09_status_ref: str,
    op09_candidate_present: bool,
    candidate_key_set_valid: bool,
    candidate_source_kind_valid: bool,
    candidate_origin_valid: bool,
    candidate_required_true_flags_valid: bool,
    candidate_required_false_flags_valid: bool,
    candidate_row_counts_valid: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    contract_or_shape_blockers: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("dri_op09_candidate_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("dri_op09_candidate_body_like_value_detected")
    if promotion_claims:
        blockers.append("dri_op09_candidate_promotion_or_autorun_claim_detected")
    if op01_status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("mrb_op01_blocked_before_op02")
    if op09_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF:
        blockers.append("dri_op09_blocked_before_mrb_op02_candidate_intake")
    if blockers:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["dri_op09_adapter_candidate_failed_bodyfree_no_promotion_boundary_before_mrb_op03"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP02_DRI_OP09_REF,
        )
    if not op01_present or not op09_present:
        missing: list[str] = []
        if not op01_present:
            missing.append("mrb_op01_dri_result_memo_op10_intake_missing")
        if not op09_present:
            missing.append("dri_op09_adapter_candidate_material_missing")
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF,
            ["mrb_op01_or_dri_op09_material_not_provided_yet"],
            missing,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if not op01_contract_valid or not op09_contract_valid:
        invalid: list[str] = []
        if not op01_contract_valid:
            invalid.append("mrb_op01_contract_invalid_before_op02")
        if not op09_contract_valid:
            invalid.append("dri_op09_adapter_candidate_contract_invalid")
        invalid.extend(contract_or_shape_blockers)
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF,
            ["mrb_op01_or_dri_op09_contract_repair_required_before_mrb_op03"],
            _dedupe_clean_refs(invalid, max_length=320),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP02_DRI_OP09_REF,
        )
    if not op01_ready or op01_status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_WAITING_FOR_DRI_READY_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF,
            ["mrb_op01_not_ready_for_dri_op09_candidate_extraction"],
            ["mrb_op01_not_ready_for_op02"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if op01_status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_REPAIR_DRI_INTAKE_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF,
            ["mrb_op01_repair_required_before_dri_op09_candidate_extraction"],
            ["mrb_op01_repair_required_before_op02"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP02_DRI_OP09_REF,
        )
    if op01_status_ref == P7_R54_AHR_POST_DRI_MRB_OP01_STATUS_MANUAL_HOLD_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF,
            ["mrb_op01_manual_hold_unresolved_before_dri_op09_candidate_extraction"],
            ["mrb_op01_manual_hold_unresolved_before_op02"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP02_REF,
        )
    if op09_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF or not op09_candidate_present:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF,
            ["dri_op09_adapter_candidate_waiting_for_final_scan_or_candidate_material"],
            ["dri_op09_adapter_candidate_not_materialized"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if op09_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF or contract_or_shape_blockers:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF,
            ["dri_op09_adapter_candidate_repair_required_before_mrb_op03"],
            _dedupe_clean_refs(contract_or_shape_blockers or ["dri_op09_adapter_candidate_repair_required"], max_length=320),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP02_DRI_OP09_REF,
        )
    if (
        op09_status_ref == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF
        and op01_ready
        and op09_candidate_present
        and candidate_key_set_valid
        and candidate_source_kind_valid
        and candidate_origin_valid
        and candidate_required_true_flags_valid
        and candidate_required_false_flags_valid
        and candidate_row_counts_valid
    ):
        return (
            P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_READY_FOR_OP03_REF,
            ["dri_op09_adapter_candidate_bodyfree_scan_clear_for_mrb_op03"],
            [],
            P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF,
        ["dri_op09_adapter_candidate_unresolved_without_promotion"],
        ["dri_op09_adapter_candidate_unresolved"],
        P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP02_REF,
    )


def _op03_status_reason_blocker_next(
    *,
    op02_present: bool,
    op02_contract_valid: bool,
    op02_ready: bool,
    op02_status_ref: str,
    dhr_op03_present: bool,
    dhr_op03_contract_valid: bool,
    dhr_op03_status_ref: str,
    dhr_op03_ready: bool,
    dhr_op03_ready_for_separation: bool,
    dhr_op03_waiting: bool,
    dhr_op03_repair: bool,
    receipt_shape_valid: bool,
    receipt_source_kind_valid: bool,
    receipt_count_fields_are_24: bool,
    receipt_required_true_fields_passed: bool,
    receipt_body_free: bool,
    actual_source_claim_confirmed: bool,
    receipt_claimed_as_actual_execution: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    contract_or_shape_blockers: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("dhr_op03_material_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("dhr_op03_material_body_like_value_detected")
    if promotion_claims:
        blockers.append("dhr_op03_material_promotion_or_autorun_claim_detected")
    if op02_status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("mrb_op02_blocked_before_op03")
    if blockers:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["dhr_op03_ready_material_failed_bodyfree_no_promotion_boundary_before_mrb_op04"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP03_DHR_OP03_REF,
        )
    if not op02_present or not dhr_op03_present:
        missing: list[str] = []
        if not op02_present:
            missing.append("mrb_op02_dri_op09_candidate_extraction_missing")
        if not dhr_op03_present:
            missing.append("dhr_op03_ready_material_missing")
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF,
            ["mrb_op02_or_dhr_op03_material_not_provided_yet"],
            missing,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if not op02_contract_valid or not dhr_op03_contract_valid:
        invalid: list[str] = []
        if not op02_contract_valid:
            invalid.append("mrb_op02_contract_invalid_before_op03")
        if not dhr_op03_contract_valid:
            invalid.append("dhr_op03_ready_material_contract_invalid")
        invalid.extend(contract_or_shape_blockers)
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF,
            ["mrb_op02_or_dhr_op03_contract_repair_required_before_mrb_op04"],
            _dedupe_clean_refs(invalid, max_length=320),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP03_DHR_OP03_REF,
        )
    if not op02_ready or op02_status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF,
            ["mrb_op02_not_ready_for_dhr_op03_ready_material_intake"],
            ["mrb_op02_not_ready_for_op03"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if op02_status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF,
            ["mrb_op02_repair_required_before_dhr_op03_ready_material_intake"],
            ["mrb_op02_repair_required_before_op03"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP03_DHR_OP03_REF,
        )
    if op02_status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_MANUAL_HOLD_REF,
            ["mrb_op02_manual_hold_unresolved_before_dhr_op03_ready_material_intake"],
            ["mrb_op02_manual_hold_unresolved_before_op03"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP03_REF,
        )
    if dhr_op03_waiting or dhr_op03_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF,
            ["dhr_op03_waiting_for_complete_evidence_before_mrb_op04"],
            ["dhr_op03_ready_material_waiting_for_complete_evidence"],
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
        )
    if dhr_op03_repair or dhr_op03_status_ref in (
        dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_REPAIR_REQUIRED_REF,
        dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_MISSING_OR_INVALID_REF,
    ) or contract_or_shape_blockers:
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF,
            ["dhr_op03_ready_material_repair_required_before_mrb_op04"],
            _dedupe_clean_refs(contract_or_shape_blockers or ["dhr_op03_ready_material_repair_required"], max_length=320),
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP03_DHR_OP03_REF,
        )
    if (
        dhr_op03_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF
        and op02_ready
        and dhr_op03_ready
        and dhr_op03_ready_for_separation
        and receipt_shape_valid
        and receipt_source_kind_valid
        and receipt_count_fields_are_24
        and receipt_required_true_fields_passed
        and receipt_body_free
        and actual_source_claim_confirmed is False
        and receipt_claimed_as_actual_execution is False
    ):
        return (
            P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_READY_FOR_OP04_ENVELOPE_REF,
            ["dhr_op03_ready_material_shape_valid_bodyfree_for_mrb_op04_without_actual_source_confirmation"],
            [],
            P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_MANUAL_HOLD_REF,
        ["dhr_op03_ready_material_unresolved_without_promotion"],
        ["dhr_op03_ready_material_unresolved"],
        P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP03_REF,
    )


def build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
    *,
    mrb_op01_dri_result_memo_op10_branch_intake: Mapping[str, Any] | None = None,
    dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MRB-OP02 DRI-OP09 adapter candidate extraction and body-free scan."""

    session_id = _safe_review_session_id(review_session_id)
    op01 = mrb_op01_dri_result_memo_op10_branch_intake
    op09 = dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate
    op01_present = isinstance(op01, Mapping)
    op09_present = isinstance(op09, Mapping)
    op01_contract_valid = False
    if op01_present:
        try:
            op01_contract_valid = assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(op01) is True
        except ValueError:
            op01_contract_valid = False
    op09_contract_valid = _dri_op09_contract_valid(op09)
    op01_map: Mapping[str, Any] = op01 if isinstance(op01, Mapping) else {}
    op09_map: Mapping[str, Any] = op09 if isinstance(op09, Mapping) else {}
    candidate_any = op09_map.get("external_actual_operation_evidence_claim_bodyfree_optional", {})
    candidate = candidate_any if isinstance(candidate_any, Mapping) else {}
    candidate_present = bool(op09_map.get("external_actual_operation_evidence_claim_bodyfree_optional_present") is True and isinstance(candidate_any, Mapping) and bool(candidate))
    candidate_key_refs = list(candidate.keys()) if isinstance(candidate, Mapping) else []
    readable_key_refs = list(dri.P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS)
    candidate_key_set_valid = tuple(candidate_key_refs) == tuple(readable_key_refs)
    expected_source_kind_ref = "actual_local_only_human_review_by_person"
    candidate_source_kind_valid = (
        candidate.get("source_kind_ref") == expected_source_kind_ref
        and candidate.get("actual_source_claim_source_kind_ref") == expected_source_kind_ref
    )
    candidate_origin_valid = candidate.get("actual_source_claim_origin_ref") == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_ORIGIN_REF
    candidate_required_true_flags_valid = all(
        candidate.get(key) is True
        for key in (
            "actual_source_claim_bodyfree",
            "actual_local_only_human_review_by_person_confirmed",
            "actual_human_review_executed_by_person",
            "body_free",
        )
    )
    candidate_required_false_flags_valid = all(
        candidate.get(key) is False
        for key in (
            "dhr_op04_called_here",
            "dhr_actual_source_claim_reintake_executed_here",
            "dmd_execution_started_here",
            "r52_actual_execution_started_here",
            "p5_final_allowed",
            "p6_start_allowed",
            "p8_start_allowed",
            "p8_question_design_started",
            "p8_question_implementation_started",
            "p7_complete",
            "release_allowed",
        )
    )
    candidate_row_counts_valid = (
        candidate.get("sanitized_review_result_row_count") == 24
        and candidate.get("rating_row_count") == 24
        and candidate.get("question_need_observation_row_count") == 24
    )
    forbidden_paths = _dedupe_clean_refs(
        [
            *_scan_forbidden_payload_key_paths(op09_map, path="dri_op09_material"),
            *_scan_forbidden_payload_key_paths(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"),
        ],
        max_length=360,
    )
    body_like_paths = _dedupe_clean_refs(
        [
            *_scan_body_like_value_paths(op09_map, path="dri_op09_material"),
            *_scan_body_like_value_paths(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"),
        ],
        max_length=360,
    )
    promotion_claims = _dedupe_clean_refs(
        [
            *_scan_promotion_claim_refs(op09_map, path="dri_op09_material"),
            *_scan_promotion_claim_refs(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"),
        ],
        max_length=360,
    )
    contract_or_shape_blockers: list[str] = []
    if op09_present and op09_contract_valid and candidate_present:
        if not candidate_key_set_valid:
            contract_or_shape_blockers.append("dri_op09_candidate_key_set_not_dhr_op04_readable")
        if not candidate_source_kind_valid:
            contract_or_shape_blockers.append("dri_op09_candidate_source_kind_invalid_for_actual_local_only_human_review")
        if not candidate_origin_valid:
            contract_or_shape_blockers.append("dri_op09_candidate_origin_invalid_for_dhr_op04_external_claim")
        if not candidate_required_true_flags_valid:
            contract_or_shape_blockers.append("dri_op09_candidate_required_true_flags_invalid")
        if not candidate_required_false_flags_valid:
            contract_or_shape_blockers.append("dri_op09_candidate_downstream_false_flags_promoted")
        if not candidate_row_counts_valid:
            contract_or_shape_blockers.append("dri_op09_candidate_row_counts_not_24")
    elif op09_present and op09_contract_valid and not candidate_present:
        contract_or_shape_blockers.append("dri_op09_adapter_candidate_absent")
    op01_status_ref = _clean_ref(op01_map.get("mrb_op01_status_ref"), default="mrb_op01_status_missing", max_length=300)
    op09_status_ref = _clean_ref(op09_map.get("dri_op09_status_ref"), default="dri_op09_status_missing", max_length=300)
    op01_ready = bool(op01_map.get("mrb_op01_ready_for_mrb_op02") is True)
    status_ref, reasons, blockers, next_required_step = _op02_status_reason_blocker_next(
        op01_present=op01_present,
        op01_contract_valid=op01_contract_valid,
        op01_ready=op01_ready,
        op01_status_ref=op01_status_ref,
        op09_present=op09_present,
        op09_contract_valid=op09_contract_valid,
        op09_status_ref=op09_status_ref,
        op09_candidate_present=candidate_present,
        candidate_key_set_valid=candidate_key_set_valid,
        candidate_source_kind_valid=candidate_source_kind_valid,
        candidate_origin_valid=candidate_origin_valid,
        candidate_required_true_flags_valid=candidate_required_true_flags_valid,
        candidate_required_false_flags_valid=candidate_required_false_flags_valid,
        candidate_row_counts_valid=candidate_row_counts_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        contract_or_shape_blockers=contract_or_shape_blockers,
    )
    ready = status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_READY_FOR_OP03_REF
    waiting = status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF
    repair = status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF
    blocked = status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    manual_hold = status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF
    safe_candidate = dict(candidate) if ready else {}
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01_map.get("schema_version"), default="mrb_op01_schema_missing", max_length=300),
        "op01_material_ref": _clean_ref(op01_map.get("material_id"), default="mrb_op01_material_missing", max_length=300),
        "op01_next_required_step": _clean_ref(op01_map.get("next_required_step"), default="mrb_op01_next_required_step_missing", max_length=300),
        "op01_contract_valid": op01_contract_valid,
        "op01_ready_for_mrb_op02": op01_ready,
        "op01_status_ref": op01_status_ref,
        "dri_op09_candidate_material_present": op09_present,
        "dri_op09_contract_valid": op09_contract_valid,
        "dri_op09_schema_version": _clean_ref(op09_map.get("schema_version"), default="dri_op09_schema_missing", max_length=300),
        "dri_op09_operation_step_ref": _clean_ref(op09_map.get("operation_step_ref"), default="dri_op09_operation_step_missing", max_length=300),
        "dri_op09_material_ref": _clean_ref(op09_map.get("material_id"), default="dri_op09_material_missing", max_length=300),
        "dri_op09_status_ref": op09_status_ref,
        "dri_op09_next_required_step": _clean_ref(op09_map.get("next_required_step"), default="dri_op09_next_required_step_missing", max_length=300),
        "dri_op09_adapter_candidate_materialized": bool(op09_map.get("adapter_candidate_materialized") is True),
        "dri_op09_adapter_candidate_materialized_bodyfree": bool(op09_map.get("adapter_candidate_materialized_bodyfree") is True),
        "dri_op09_adapter_candidate_for_manual_dhr_op04_input_only": bool(op09_map.get("adapter_candidate_for_manual_dhr_op04_input_only") is True),
        "dri_op09_adapter_candidate_not_dhr_confirmed": bool(op09_map.get("adapter_candidate_not_dhr_confirmed") is True),
        "dri_op09_does_not_call_dhr_op04": bool(op09_map.get("dri_op09_does_not_call_dhr_op04") is True),
        "dri_op09_does_not_confirm_dhr_actual_source_claim": bool(op09_map.get("dri_op09_does_not_confirm_dhr_actual_source_claim") is True),
        "dri_op09_does_not_execute_dhr_reintake": bool(op09_map.get("dri_op09_does_not_execute_dhr_reintake") is True),
        "dri_op09_downstream_auto_execution_allowed": False,
        "external_actual_operation_evidence_claim_bodyfree_optional_present": ready and candidate_present,
        "external_actual_operation_evidence_claim_bodyfree_optional": safe_candidate,
        "external_actual_operation_evidence_claim_bodyfree_optional_key_refs": list(safe_candidate.keys()),
        "external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count": len(safe_candidate.keys()),
        "adapter_candidate_schema_version": _clean_ref(candidate.get("schema_version"), default="adapter_candidate_schema_missing", max_length=300),
        "adapter_candidate_material_kind": _clean_ref(candidate.get("material_kind"), default="adapter_candidate_material_kind_missing", max_length=300),
        "adapter_candidate_source_kind_ref": _clean_ref(candidate.get("source_kind_ref"), default="adapter_candidate_source_kind_missing", max_length=300),
        "adapter_candidate_actual_source_claim_source_kind_ref": _clean_ref(candidate.get("actual_source_claim_source_kind_ref"), default="adapter_candidate_actual_source_claim_source_kind_missing", max_length=300),
        "adapter_candidate_actual_source_claim_origin_ref": _clean_ref(candidate.get("actual_source_claim_origin_ref"), default="adapter_candidate_actual_source_claim_origin_missing", max_length=300),
        "adapter_candidate_actual_source_claim_bodyfree": bool(candidate.get("actual_source_claim_bodyfree") is True),
        "adapter_candidate_actual_local_only_human_review_by_person_confirmed": bool(candidate.get("actual_local_only_human_review_by_person_confirmed") is True),
        "adapter_candidate_actual_human_review_executed_by_person": bool(candidate.get("actual_human_review_executed_by_person") is True),
        "adapter_candidate_operation_receipt_bodyfree_ref": _clean_ref(candidate.get("operation_receipt_bodyfree_ref"), default="operation_receipt_bodyfree_ref_missing", max_length=300),
        "adapter_candidate_disposal_purge_receipt_bodyfree_ref": _clean_ref(candidate.get("disposal_purge_receipt_bodyfree_ref"), default="disposal_purge_receipt_bodyfree_ref_missing", max_length=300),
        "adapter_candidate_rsr_op15_branch_ref": _clean_ref(candidate.get("rsr_op15_branch_ref"), default="rsr_op15_branch_ref_missing", max_length=300),
        "adapter_candidate_rsr_op16_status_ref": _clean_ref(candidate.get("rsr_op16_status_ref"), default="rsr_op16_status_ref_missing", max_length=300),
        "adapter_candidate_sanitized_review_result_row_count": int(candidate.get("sanitized_review_result_row_count") or 0),
        "adapter_candidate_rating_row_count": int(candidate.get("rating_row_count") or 0),
        "adapter_candidate_question_need_observation_row_count": int(candidate.get("question_need_observation_row_count") or 0),
        "adapter_candidate_readable_key_refs": readable_key_refs,
        "adapter_candidate_readable_key_ref_count": len(readable_key_refs),
        "adapter_candidate_key_set_valid": candidate_key_set_valid,
        "adapter_candidate_source_kind_valid": candidate_source_kind_valid,
        "adapter_candidate_origin_valid": candidate_origin_valid,
        "adapter_candidate_required_true_flags_valid": candidate_required_true_flags_valid,
        "adapter_candidate_required_false_flags_valid": candidate_required_false_flags_valid,
        "adapter_candidate_row_counts_valid": candidate_row_counts_valid,
        "adapter_candidate_bodyfree_scan_clear": not forbidden_paths and not body_like_paths,
        "adapter_candidate_promotion_scan_clear": not promotion_claims,
        "adapter_candidate_forbidden_payload_key_path_refs": forbidden_paths,
        "adapter_candidate_forbidden_payload_key_path_count": len(forbidden_paths),
        "adapter_candidate_body_like_value_path_refs": body_like_paths,
        "adapter_candidate_body_like_value_path_count": len(body_like_paths),
        "adapter_candidate_promotion_claim_refs": promotion_claims,
        "adapter_candidate_promotion_claim_ref_count": len(promotion_claims),
        "adapter_candidate_contract_or_shape_blocker_refs": _dedupe_clean_refs(contract_or_shape_blockers, max_length=320),
        "adapter_candidate_contract_or_shape_blocker_ref_count": len(_dedupe_clean_refs(contract_or_shape_blockers, max_length=320)),
        "mrb_op02_status_ref": status_ref,
        "dri_op09_adapter_candidate_extraction_status_ref": status_ref,
        "mrb_op02_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP02_ALLOWED_STATUS_REFS),
        "mrb_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP02_ALLOWED_STATUS_REFS),
        "mrb_op02_ready_for_mrb_op03": ready,
        "mrb_op02_waiting_for_dri_op09_candidate": waiting,
        "mrb_op02_repair_required": repair,
        "mrb_op02_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "mrb_op02_manual_hold_unresolved_no_promotion": manual_hold,
        "mrb_op02_reason_refs": reasons,
        "mrb_op02_reason_ref_count": len(reasons),
        "mrb_op02_blocker_refs": blockers,
        "mrb_op02_blocker_ref_count": len(blockers),
        "dri_op09_candidate_is_only_dhr_op04_input_material": True,
        "dri_op09_candidate_is_not_dhr_op04_call": True,
        "dri_op09_candidate_is_not_dhr_actual_source_claim_confirmed": True,
        "dri_op09_candidate_is_not_dhr_reintake_execution": True,
        "dri_op09_candidate_is_not_dhr_op05_ready": True,
        "mrb_op02_does_not_intake_dhr_op03_material": True,
        "mrb_op02_does_not_call_dhr_op04": True,
        "mrb_op02_does_not_execute_dhr_op05_dmd_r52_or_release": True,
        "mrb_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "mrb_op02_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert MRB-OP02 DRI-OP09 adapter candidate extraction and scan contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP02")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DRI_MRB_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF,
        source="P7-R54-AHR-PostDRI-MRB-OP02",
    )
    if data.get("dri_op09_adapter_candidate_extraction_status_ref") != data.get("mrb_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 status alias changed")
    for key in (
        "dri_op09_candidate_is_only_dhr_op04_input_material",
        "dri_op09_candidate_is_not_dhr_op04_call",
        "dri_op09_candidate_is_not_dhr_actual_source_claim_confirmed",
        "dri_op09_candidate_is_not_dhr_reintake_execution",
        "dri_op09_candidate_is_not_dhr_op05_ready",
        "mrb_op02_does_not_intake_dhr_op03_material",
        "mrb_op02_does_not_call_dhr_op04",
        "mrb_op02_does_not_execute_dhr_op05_dmd_r52_or_release",
        "mrb_op02_does_not_start_p5_p6_p8_p7_or_release",
        "mrb_op02_does_not_change_api_db_rn_runtime_response_key",
        "mrb_op02_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP02 required true boundary changed: {key}")
    for key in (
        "dri_op09_downstream_auto_execution_allowed",
        "dhr_op04_called_here",
        "dhr_actual_source_claim_confirmed_here",
        "dhr_actual_source_claim_reintake_executed_here",
        "dhr_op05_called_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP02 downstream flag promoted: {key}")
    for field, count_field in (
        ("external_actual_operation_evidence_claim_bodyfree_optional_key_refs", "external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count"),
        ("adapter_candidate_readable_key_refs", "adapter_candidate_readable_key_ref_count"),
        ("adapter_candidate_forbidden_payload_key_path_refs", "adapter_candidate_forbidden_payload_key_path_count"),
        ("adapter_candidate_body_like_value_path_refs", "adapter_candidate_body_like_value_path_count"),
        ("adapter_candidate_promotion_claim_refs", "adapter_candidate_promotion_claim_ref_count"),
        ("adapter_candidate_contract_or_shape_blocker_refs", "adapter_candidate_contract_or_shape_blocker_ref_count"),
        ("mrb_op02_allowed_status_refs", "mrb_op02_allowed_status_ref_count"),
        ("mrb_op02_reason_refs", "mrb_op02_reason_ref_count"),
        ("mrb_op02_blocker_refs", "mrb_op02_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP02 {count_field} changed")
    if tuple(data.get("mrb_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 allowed status refs changed")
    if tuple(data.get("adapter_candidate_readable_key_refs") or ()) != dri.P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 readable candidate key refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 not-yet steps changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 not-claimed boundary must stay false")
    status_ref = data.get("mrb_op02_status_ref")
    flags = [
        data.get("mrb_op02_ready_for_mrb_op03") is True,
        data.get("mrb_op02_waiting_for_dri_op09_candidate") is True,
        data.get("mrb_op02_repair_required") is True,
        data.get("mrb_op02_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("mrb_op02_manual_hold_unresolved_no_promotion") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DRI_MRB_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 exactly one status branch must be selected")
    if status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_READY_FOR_OP03_REF:
        for key in (
            "op01_contract_valid", "op01_ready_for_mrb_op02", "dri_op09_contract_valid", "dri_op09_adapter_candidate_materialized",
            "dri_op09_adapter_candidate_materialized_bodyfree", "dri_op09_adapter_candidate_for_manual_dhr_op04_input_only", "dri_op09_adapter_candidate_not_dhr_confirmed",
            "external_actual_operation_evidence_claim_bodyfree_optional_present", "adapter_candidate_key_set_valid", "adapter_candidate_source_kind_valid", "adapter_candidate_origin_valid", "adapter_candidate_required_true_flags_valid", "adapter_candidate_required_false_flags_valid", "adapter_candidate_row_counts_valid", "adapter_candidate_bodyfree_scan_clear", "adapter_candidate_promotion_scan_clear",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP02 ready required true changed: {key}")
        if data.get("external_actual_operation_evidence_claim_bodyfree_optional_key_refs") != list(dri.P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 ready candidate key refs changed")
        if data.get("adapter_candidate_forbidden_payload_key_path_refs") or data.get("adapter_candidate_body_like_value_path_refs") or data.get("adapter_candidate_promotion_claim_refs") or data.get("adapter_candidate_contract_or_shape_blocker_refs") or data.get("mrb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF:
        if data.get("mrb_op02_waiting_for_dri_op09_candidate") is not True or not data.get("mrb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 waiting branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF:
        if data.get("mrb_op02_repair_required") is not True or not data.get("mrb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP02_DRI_OP09_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if data.get("mrb_op02_bodyfree_leak_promotion_or_autorun_blocked") is not True or not data.get("mrb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 blocked branch changed")
        if data.get("external_actual_operation_evidence_claim_bodyfree_optional") != {}:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 blocked branch must not copy candidate")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP02_DRI_OP09_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 blocked next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_MANUAL_HOLD_REF:
        if data.get("mrb_op02_manual_hold_unresolved_no_promotion") is not True or not data.get("mrb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 manual hold branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP02_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP02 manual hold next step changed")
    return True


def build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
    *,
    mrb_op02_dri_op09_adapter_candidate_extraction_and_scan: Mapping[str, Any] | None = None,
    dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MRB-OP03 DHR-OP03 ready material intake without DHR-OP04 call."""

    session_id = _safe_review_session_id(review_session_id)
    op02 = mrb_op02_dri_op09_adapter_candidate_extraction_and_scan
    op03 = dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction
    op02_present = isinstance(op02, Mapping)
    dhr_op03_present = isinstance(op03, Mapping)
    op02_contract_valid = False
    if op02_present:
        try:
            op02_contract_valid = assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(op02) is True
        except ValueError:
            op02_contract_valid = False
    dhr_op03_contract_valid = _dhr_op03_contract_valid(op03)
    op02_map: Mapping[str, Any] = op02 if isinstance(op02, Mapping) else {}
    op03_map: Mapping[str, Any] = op03 if isinstance(op03, Mapping) else {}
    receipt_any = op03_map.get("dmd_compatible_actual_operation_evidence_receipt_bodyfree", {})
    receipt = receipt_any if isinstance(receipt_any, Mapping) else {}
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op03_map, path="dhr_op03_material"), max_length=360)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op03_map, path="dhr_op03_material"), max_length=360)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op03_map, path="dhr_op03_material"), max_length=360)
    receipt_shape_valid = bool(op03_map.get("receipt_shape_valid") is True)
    receipt_source_kind_valid = bool(op03_map.get("receipt_source_kind_valid") is True)
    receipt_count_fields_are_24 = bool(op03_map.get("receipt_count_fields_are_24") is True)
    receipt_required_true_fields_passed = bool(op03_map.get("receipt_required_true_fields_passed") is True)
    receipt_body_free = bool(op03_map.get("receipt_body_free") is True)
    receipt_schema_version_matches_dmd = bool(op03_map.get("receipt_schema_version_matches_dmd") is True)
    receipt_claimed_as_actual_execution = bool(op03_map.get("receipt_claimed_as_actual_execution_by_dhr_op03") is True)
    actual_source_claim_confirmed = bool(op03_map.get("actual_source_claim_confirmed_for_downstream_handoff") is True)
    dhr_op03_status_ref = _clean_ref(op03_map.get("dhr_op03_status_ref"), default="dhr_op03_status_missing", max_length=300)
    contract_or_shape_blockers: list[str] = []
    if dhr_op03_present and dhr_op03_contract_valid:
        if not receipt_shape_valid:
            contract_or_shape_blockers.append("dhr_op03_receipt_shape_not_valid")
        if not receipt_schema_version_matches_dmd:
            contract_or_shape_blockers.append("dhr_op03_receipt_schema_version_not_dmd")
        if not receipt_source_kind_valid:
            contract_or_shape_blockers.append("dhr_op03_receipt_source_kind_invalid")
        if not receipt_count_fields_are_24:
            contract_or_shape_blockers.append("dhr_op03_receipt_counts_not_24")
        if not receipt_required_true_fields_passed:
            contract_or_shape_blockers.append("dhr_op03_receipt_required_true_fields_not_passed")
        if not receipt_body_free:
            contract_or_shape_blockers.append("dhr_op03_receipt_not_body_free")
        if actual_source_claim_confirmed:
            contract_or_shape_blockers.append("dhr_op03_receipt_shape_claimed_as_actual_source_confirmation")
        if receipt_claimed_as_actual_execution:
            contract_or_shape_blockers.append("dhr_op03_receipt_claimed_as_actual_execution")
    op02_status_ref = _clean_ref(op02_map.get("mrb_op02_status_ref"), default="mrb_op02_status_missing", max_length=300)
    op02_ready = bool(op02_map.get("mrb_op02_ready_for_mrb_op03") is True)
    dhr_op03_ready = bool(op03_map.get("dhr_op03_ready") is True)
    dhr_op03_ready_for_separation = bool(op03_map.get("dhr_op03_ready_for_actual_source_claim_separation") is True)
    dhr_op03_waiting = bool(op03_map.get("dhr_op03_waiting_for_complete_evidence") is True)
    dhr_op03_repair = bool(op03_map.get("dhr_op03_repair_required") is True)
    status_ref, reasons, blockers, next_required_step = _op03_status_reason_blocker_next(
        op02_present=op02_present,
        op02_contract_valid=op02_contract_valid,
        op02_ready=op02_ready,
        op02_status_ref=op02_status_ref,
        dhr_op03_present=dhr_op03_present,
        dhr_op03_contract_valid=dhr_op03_contract_valid,
        dhr_op03_status_ref=dhr_op03_status_ref,
        dhr_op03_ready=dhr_op03_ready,
        dhr_op03_ready_for_separation=dhr_op03_ready_for_separation,
        dhr_op03_waiting=dhr_op03_waiting,
        dhr_op03_repair=dhr_op03_repair,
        receipt_shape_valid=receipt_shape_valid,
        receipt_source_kind_valid=receipt_source_kind_valid,
        receipt_count_fields_are_24=receipt_count_fields_are_24,
        receipt_required_true_fields_passed=receipt_required_true_fields_passed,
        receipt_body_free=receipt_body_free,
        actual_source_claim_confirmed=actual_source_claim_confirmed,
        receipt_claimed_as_actual_execution=receipt_claimed_as_actual_execution,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        contract_or_shape_blockers=contract_or_shape_blockers,
    )
    ready = status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_READY_FOR_OP04_ENVELOPE_REF
    waiting = status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF
    repair = status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF
    blocked = status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    manual_hold = status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_MANUAL_HOLD_REF
    safe_op03_material = dict(op03_map) if ready else {}
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02_map.get("schema_version"), default="mrb_op02_schema_missing", max_length=300),
        "op02_material_ref": _clean_ref(op02_map.get("material_id"), default="mrb_op02_material_missing", max_length=300),
        "op02_next_required_step": _clean_ref(op02_map.get("next_required_step"), default="mrb_op02_next_required_step_missing", max_length=300),
        "op02_contract_valid": op02_contract_valid,
        "op02_ready_for_mrb_op03": op02_ready,
        "op02_status_ref": op02_status_ref,
        "dhr_op03_ready_material_present": dhr_op03_present,
        "dhr_op03_contract_valid": dhr_op03_contract_valid,
        "dhr_op03_schema_version": _clean_ref(op03_map.get("schema_version"), default="dhr_op03_schema_missing", max_length=300),
        "dhr_op03_operation_step_ref": _clean_ref(op03_map.get("operation_step_ref"), default="dhr_op03_operation_step_missing", max_length=300),
        "dhr_op03_material_ref": _clean_ref(op03_map.get("material_id"), default="dhr_op03_material_missing", max_length=300),
        "dhr_op03_status_ref": dhr_op03_status_ref,
        "dhr_op03_next_required_step": _clean_ref(op03_map.get("next_required_step"), default="dhr_op03_next_required_step_missing", max_length=300),
        "dhr_op03_ready": dhr_op03_ready,
        "dhr_op03_ready_for_actual_source_claim_separation": dhr_op03_ready_for_separation,
        "dhr_op03_waiting_for_complete_evidence": dhr_op03_waiting,
        "dhr_op03_repair_required": dhr_op03_repair,
        "dhr_op03_receipt_shape_valid": receipt_shape_valid,
        "dhr_op03_receipt_schema_version_matches_dmd": receipt_schema_version_matches_dmd,
        "dhr_op03_receipt_source_kind_valid": receipt_source_kind_valid,
        "dhr_op03_receipt_count_fields_are_24": receipt_count_fields_are_24,
        "dhr_op03_receipt_required_true_fields_passed": receipt_required_true_fields_passed,
        "dhr_op03_receipt_body_free": receipt_body_free,
        "dhr_op03_receipt_claimed_as_actual_execution_by_dhr_op03": False,
        "dhr_op03_actual_source_claim_confirmed_for_downstream_handoff": False,
        "dhr_op03_ready_material_bodyfree": safe_op03_material,
        "dhr_op03_ready_material_schema_version": _clean_ref(receipt.get("schema_version"), default="dhr_op03_receipt_schema_missing", max_length=300),
        "dhr_op03_ready_material_source_kind_ref": _clean_ref(receipt.get("source_kind_ref"), default="dhr_op03_receipt_source_kind_missing", max_length=300),
        "dhr_op03_ready_material_key_refs": list(safe_op03_material.keys()),
        "dhr_op03_ready_material_key_ref_count": len(safe_op03_material.keys()),
        "dhr_op03_material_forbidden_payload_key_path_refs": forbidden_paths,
        "dhr_op03_material_forbidden_payload_key_path_count": len(forbidden_paths),
        "dhr_op03_material_body_like_value_path_refs": body_like_paths,
        "dhr_op03_material_body_like_value_path_count": len(body_like_paths),
        "dhr_op03_material_promotion_claim_refs": promotion_claims,
        "dhr_op03_material_promotion_claim_ref_count": len(promotion_claims),
        "dhr_op03_contract_or_shape_blocker_refs": _dedupe_clean_refs(contract_or_shape_blockers, max_length=320),
        "dhr_op03_contract_or_shape_blocker_ref_count": len(_dedupe_clean_refs(contract_or_shape_blockers, max_length=320)),
        "mrb_op03_status_ref": status_ref,
        "dhr_op03_ready_material_intake_status_ref": status_ref,
        "mrb_op03_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP03_ALLOWED_STATUS_REFS),
        "mrb_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP03_ALLOWED_STATUS_REFS),
        "mrb_op03_ready_for_mrb_op04": ready,
        "mrb_op03_waiting_for_dhr_op03_ready_material": waiting,
        "mrb_op03_repair_required": repair,
        "mrb_op03_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "mrb_op03_manual_hold_unresolved_no_promotion": manual_hold,
        "mrb_op03_reason_refs": reasons,
        "mrb_op03_reason_ref_count": len(reasons),
        "mrb_op03_blocker_refs": blockers,
        "mrb_op03_blocker_ref_count": len(blockers),
        "dhr_op03_receipt_shape_is_not_actual_source_claim_confirmation": True,
        "dhr_op03_ready_material_is_not_dhr_op04_call": True,
        "dhr_op03_ready_material_is_not_dhr_actual_source_claim_confirmed": True,
        "dhr_op03_ready_material_is_not_dhr_reintake_execution": True,
        "dhr_op03_ready_material_is_not_dhr_op05_ready": True,
        "mrb_op03_does_not_build_dhr_op04_envelope": True,
        "mrb_op03_does_not_call_dhr_op04": True,
        "mrb_op03_does_not_execute_dhr_op05_dmd_r52_or_release": True,
        "mrb_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "mrb_op03_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert MRB-OP03 DHR-OP03 ready material intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP03")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DRI_MRB_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF,
        source="P7-R54-AHR-PostDRI-MRB-OP03",
    )
    if data.get("dhr_op03_ready_material_intake_status_ref") != data.get("mrb_op03_status_ref"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 status alias changed")
    for key in (
        "dhr_op03_receipt_shape_is_not_actual_source_claim_confirmation",
        "dhr_op03_ready_material_is_not_dhr_op04_call",
        "dhr_op03_ready_material_is_not_dhr_actual_source_claim_confirmed",
        "dhr_op03_ready_material_is_not_dhr_reintake_execution",
        "dhr_op03_ready_material_is_not_dhr_op05_ready",
        "mrb_op03_does_not_build_dhr_op04_envelope",
        "mrb_op03_does_not_call_dhr_op04",
        "mrb_op03_does_not_execute_dhr_op05_dmd_r52_or_release",
        "mrb_op03_does_not_start_p5_p6_p8_p7_or_release",
        "mrb_op03_does_not_change_api_db_rn_runtime_response_key",
        "mrb_op03_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP03 required true boundary changed: {key}")
    for key in (
        "dhr_op03_receipt_claimed_as_actual_execution_by_dhr_op03",
        "dhr_op03_actual_source_claim_confirmed_for_downstream_handoff",
        "dhr_op04_called_here",
        "dhr_actual_source_claim_confirmed_here",
        "dhr_actual_source_claim_reintake_executed_here",
        "dhr_op05_called_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP03 downstream or actual-source flag promoted: {key}")
    for field, count_field in (
        ("dhr_op03_ready_material_key_refs", "dhr_op03_ready_material_key_ref_count"),
        ("dhr_op03_material_forbidden_payload_key_path_refs", "dhr_op03_material_forbidden_payload_key_path_count"),
        ("dhr_op03_material_body_like_value_path_refs", "dhr_op03_material_body_like_value_path_count"),
        ("dhr_op03_material_promotion_claim_refs", "dhr_op03_material_promotion_claim_ref_count"),
        ("dhr_op03_contract_or_shape_blocker_refs", "dhr_op03_contract_or_shape_blocker_ref_count"),
        ("mrb_op03_allowed_status_refs", "mrb_op03_allowed_status_ref_count"),
        ("mrb_op03_reason_refs", "mrb_op03_reason_ref_count"),
        ("mrb_op03_blocker_refs", "mrb_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP03 {count_field} changed")
    if tuple(data.get("mrb_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 allowed status refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 not-yet steps changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 not-claimed boundary must stay false")
    status_ref = data.get("mrb_op03_status_ref")
    flags = [
        data.get("mrb_op03_ready_for_mrb_op04") is True,
        data.get("mrb_op03_waiting_for_dhr_op03_ready_material") is True,
        data.get("mrb_op03_repair_required") is True,
        data.get("mrb_op03_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("mrb_op03_manual_hold_unresolved_no_promotion") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DRI_MRB_OP03_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 exactly one status branch must be selected")
    if status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_READY_FOR_OP04_ENVELOPE_REF:
        for key in (
            "op02_contract_valid", "op02_ready_for_mrb_op03", "dhr_op03_contract_valid", "dhr_op03_ready", "dhr_op03_ready_for_actual_source_claim_separation",
            "dhr_op03_receipt_shape_valid", "dhr_op03_receipt_schema_version_matches_dmd", "dhr_op03_receipt_source_kind_valid", "dhr_op03_receipt_count_fields_are_24", "dhr_op03_receipt_required_true_fields_passed", "dhr_op03_receipt_body_free",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP03 ready required true changed: {key}")
        if data.get("dhr_op03_receipt_claimed_as_actual_execution_by_dhr_op03") is not False or data.get("dhr_op03_actual_source_claim_confirmed_for_downstream_handoff") is not False:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 ready branch must not confirm actual source claim")
        if data.get("dhr_op03_material_forbidden_payload_key_path_refs") or data.get("dhr_op03_material_body_like_value_path_refs") or data.get("dhr_op03_material_promotion_claim_refs") or data.get("dhr_op03_contract_or_shape_blocker_refs") or data.get("mrb_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF:
        if data.get("mrb_op03_waiting_for_dhr_op03_ready_material") is not True or not data.get("mrb_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 waiting branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF:
        if data.get("mrb_op03_repair_required") is not True or not data.get("mrb_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP03_DHR_OP03_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if data.get("mrb_op03_bodyfree_leak_promotion_or_autorun_blocked") is not True or not data.get("mrb_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 blocked branch changed")
        if data.get("dhr_op03_ready_material_bodyfree") != {}:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 blocked branch must not copy ready material")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP03_DHR_OP03_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 blocked next step changed")
    elif status_ref == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_MANUAL_HOLD_REF:
        if data.get("mrb_op03_manual_hold_unresolved_no_promotion") is not True or not data.get("mrb_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 manual hold branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_OP03_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP03 manual hold next step changed")
    return True



# ---------------------------------------------------------------------------
# MRB-OP04 / MRB-OP05: manual request, DHR-OP04 envelope, explicit call.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb.manual_reintake_request.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_MATERIAL_KIND_REF: Final = (
    "dhr_op04_manual_reintake_request"
)
P7_R54_AHR_POST_DRI_MRB_DHR_OP04_INPUT_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb.dhr_op04_input_envelope.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op04_manual_reintake_request_and_dhr_op04_input_envelope.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op05_explicit_manual_dhr_op04_call_and_result_capture.bodyfree.v1"
)

P7_R54_AHR_POST_DRI_MRB_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:5]
)
P7_R54_AHR_POST_DRI_MRB_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[5:]
)
P7_R54_AHR_POST_DRI_MRB_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:6]
)
P7_R54_AHR_POST_DRI_MRB_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[6:]
)

P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_READY_FOR_OP05_REF: Final = (
    "MRB_OP04_DHR_OP04_INPUT_ENVELOPE_READY_NO_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF: Final = (
    "MRB_OP04_WAITING_FOR_MANUAL_REQUEST_OR_READY_MATERIAL"
)
P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_REPAIR_INPUT_ENVELOPE_REF: Final = (
    "MRB_OP04_REPAIR_MANUAL_REINTAKE_REQUEST_OR_INPUT_ENVELOPE"
)
P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "MRB_OP04_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_BEFORE_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_MANUAL_HOLD_REF: Final = (
    "MRB_OP04_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_DRI_MRB_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_READY_FOR_OP05_REF,
    P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF,
    P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_REPAIR_INPUT_ENVELOPE_REF,
    P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_MANUAL_HOLD_REF,
)

P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF: Final = (
    "MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF: Final = (
    "MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF: Final = (
    "MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF: Final = (
    "MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED"
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF: Final = (
    "MRB_OP05_WAITING_BEFORE_EXPLICIT_MANUAL_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF: Final = (
    "MRB_OP05_REPAIR_REQUIRED_BEFORE_EXPLICIT_MANUAL_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "MRB_OP05_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_BEFORE_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF,
    P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
    P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_DRI_MRB_OP05_CALLED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
)

P7_R54_AHR_POST_DRI_MRB_REQUESTED_DHR_OP04_OPERATION_STEP_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF
)
P7_R54_AHR_POST_DRI_MRB_REQUESTED_SOURCE_MATERIAL_REF: Final = (
    "DRI-OP09_external_actual_operation_evidence_claim_bodyfree_optional_candidate"
)
P7_R54_AHR_POST_DRI_MRB_REQUESTED_TARGET_HELPER_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704."
    "build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification"
)

P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_CALL_DHR_OP04_MANUALLY_REF: Final = (
    "call_dhr_op04_manually_with_dri_bodyfree_actual_source_claim_adapter_and_dhr_op03_ready_material"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP04_ENVELOPE_REF: Final = (
    "repair_post_dri_to_dhr_op04_manual_reintake_request_or_input_envelope"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP04_ENVELOPE_REF: Final = (
    "blocked_post_dri_to_dhr_op04_manual_reintake_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF: Final = (
    "manual_review_dhr_op04_confirmed_bodyfree_result_before_any_dhr_op05"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF: Final = (
    "manual_review_dhr_op04_not_confirmed_result_and_decide_retry_or_start_without_auto_execution"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF: Final = (
    "wait_for_external_bodyfree_actual_source_claim_before_manual_dhr_op04_reintake"
)
P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF: Final = (
    "repair_post_dri_to_dhr_op04_manual_reintake_boundary_after_dhr_op04_result"
)

P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "material_kind", "review_session_id", "manual_reintake_requested",
    "requested_operation_step_ref", "requested_source_material_ref", "requested_target_helper_ref",
    "manual_request_bodyfree", "dhr_op04_only", "dhr_op05_auto_call_allowed",
    "downstream_auto_execution_allowed", "p8_question_design_started", "p8_question_implementation_started",
    "release_allowed", "body_free",
)
P7_R54_AHR_POST_DRI_MRB_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_contract_valid", "op02_ready_for_mrb_op03", "op02_status_ref", "op03_contract_valid", "op03_ready_for_mrb_op04", "op03_status_ref",
    "manual_reintake_request_present", "manual_reintake_request_contract_valid", "manual_reintake_requested", "manual_request_bodyfree",
    "requested_operation_step_ref", "requested_source_material_ref", "requested_target_helper_ref",
    "dri_op09_candidate_present", "dri_op10_ready", "dri_op12_closed_bodyfree", "dhr_op03_ready",
    "external_actual_operation_evidence_claim_bodyfree_optional", "op03_elr_op17_dmd_compatible_receipt_candidate_extraction",
    "dhr_op04_input_envelope_bodyfree", "dhr_op04_input_envelope_ready",
    "mrb_op04_status_ref", "manual_reintake_request_input_envelope_status_ref", "mrb_op04_allowed_status_refs", "mrb_op04_allowed_status_ref_count",
    "mrb_op04_ready_for_mrb_op05", "mrb_op04_waiting_for_manual_request_or_material", "mrb_op04_repair_required",
    "mrb_op04_bodyfree_leak_promotion_or_autorun_blocked", "mrb_op04_manual_hold_unresolved_no_promotion",
    "mrb_op04_reason_refs", "mrb_op04_reason_ref_count", "mrb_op04_blocker_refs", "mrb_op04_blocker_ref_count",
    "mrb_op04_forbidden_payload_key_path_refs", "mrb_op04_forbidden_payload_key_path_count", "mrb_op04_body_like_value_path_refs", "mrb_op04_body_like_value_path_count",
    "mrb_op04_promotion_claim_refs", "mrb_op04_promotion_claim_ref_count", "mrb_op04_does_not_call_dhr_op04",
    "dhr_op04_called_by_manual_reintake_boundary", "dhr_op05_auto_call_allowed", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DRI_MRB_OP05_REQUIRED_FALSE_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    field for field in P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS
    if field not in {"dhr_op04_called_here", "dhr_op04_called_by_mrb", "actual_source_claim_confirmed_for_downstream_handoff"}
)
P7_R54_AHR_POST_DRI_MRB_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_contract_valid", "op04_ready_for_mrb_op05", "op04_status_ref", "dhr_op04_input_envelope_ready",
    "dhr_op04_called_by_manual_reintake_boundary", "dhr_op04_called_by_dri", "dhr_op04_called_by_mrb", "dhr_op04_called_here",
    "dhr_op04_result_captured", "dhr_op04_contract_valid", "dhr_op04_result_bodyfree", "dhr_op04_status_ref", "dhr_op04_result_status_ref", "dhr_op04_next_required_step_ref",
    "actual_source_claim_confirmed_for_downstream_handoff", "actual_source_claim_bodyfree", "actual_source_claim_origin_ref", "actual_local_only_human_review_by_person_confirmed",
    "mrb_op05_status_ref", "dhr_op04_manual_call_result_capture_status_ref", "mrb_op05_allowed_status_refs", "mrb_op05_allowed_status_ref_count",
    "mrb_op05_dhr_op04_confirmed_bodyfree_stopped", "mrb_op05_dhr_op04_not_confirmed_retry_or_start_required_stopped",
    "mrb_op05_dhr_op04_waiting_external_claim_stopped", "mrb_op05_dhr_op04_invalid_repair_required_stopped",
    "mrb_op05_waiting_before_dhr_op04_call", "mrb_op05_repair_required_before_dhr_op04_call", "mrb_op05_bodyfree_leak_promotion_or_autorun_blocked",
    "mrb_op05_reason_refs", "mrb_op05_reason_ref_count", "mrb_op05_blocker_refs", "mrb_op05_blocker_ref_count",
    "mrb_op05_does_not_call_dhr_op05", "mrb_op05_does_not_call_dhr_op06", "mrb_op05_does_not_execute_dmd_r52_or_release", "mrb_op05_does_not_start_p5_p6_p8_p7_or_release",
    "dhr_op05_auto_call_allowed", "dhr_op06_auto_call_allowed", "downstream_auto_execution_allowed", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def build_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree(*, review_session_id: Any = None) -> dict[str, Any]:
    """Build a body-free explicit manual DHR-OP04 re-intake request."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_SCHEMA_VERSION,
        "material_kind": P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_MATERIAL_KIND_REF,
        "review_session_id": session_id,
        "manual_reintake_requested": True,
        "requested_operation_step_ref": P7_R54_AHR_POST_DRI_MRB_REQUESTED_DHR_OP04_OPERATION_STEP_REF,
        "requested_source_material_ref": P7_R54_AHR_POST_DRI_MRB_REQUESTED_SOURCE_MATERIAL_REF,
        "requested_target_helper_ref": P7_R54_AHR_POST_DRI_MRB_REQUESTED_TARGET_HELPER_REF,
        "manual_request_bodyfree": True,
        "dhr_op04_only": True,
        "dhr_op05_auto_call_allowed": False,
        "downstream_auto_execution_allowed": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "release_allowed": False,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-manual-request")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-manual-request field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DRI_MRB_MANUAL_REQUEST_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-manual-request schema changed")
    for key in ("manual_reintake_requested", "manual_request_bodyfree", "dhr_op04_only", "body_free"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-manual-request required true changed: {key}")
    for key in ("dhr_op05_auto_call_allowed", "downstream_auto_execution_allowed", "p8_question_design_started", "p8_question_implementation_started", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-manual-request downstream flag promoted: {key}")
    if data.get("requested_operation_step_ref") != P7_R54_AHR_POST_DRI_MRB_REQUESTED_DHR_OP04_OPERATION_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-manual-request requested step changed")
    if _scan_forbidden_payload_key_paths(data, path="manual_reintake_request"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-manual-request contains forbidden payload keys")
    if _scan_body_like_value_paths(data, path="manual_reintake_request"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-manual-request contains body-like values")
    if _scan_promotion_claim_refs(data, path="manual_reintake_request"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-manual-request contains promotion claims")
    return True


def _manual_reintake_request_valid(manual_request: Mapping[str, Any] | None) -> bool:
    if not isinstance(manual_request, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree_contract(manual_request) is True
    except ValueError:
        return False


def _mrb_op02_contract_valid_for_op04(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(data) is True
    except ValueError:
        return False


def _mrb_op03_contract_valid_for_op04(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(data) is True
    except ValueError:
        return False


def _mrb_op04_contract_valid_for_op05(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(data) is True
    except ValueError:
        return False


def build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
    *,
    mrb_op02_dri_op09_adapter_candidate_extraction_and_scan: Mapping[str, Any] | None = None,
    mrb_op03_dhr_op03_ready_material_intake: Mapping[str, Any] | None = None,
    manual_reintake_request_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Assemble a DHR-OP04 input envelope without calling DHR-OP04."""

    op02 = mrb_op02_dri_op09_adapter_candidate_extraction_and_scan if isinstance(mrb_op02_dri_op09_adapter_candidate_extraction_and_scan, Mapping) else {}
    op03 = mrb_op03_dhr_op03_ready_material_intake if isinstance(mrb_op03_dhr_op03_ready_material_intake, Mapping) else {}
    request = manual_reintake_request_bodyfree if isinstance(manual_reintake_request_bodyfree, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (request.get("review_session_id") or op03.get("review_session_id") or op02.get("review_session_id")))

    op02_valid = _mrb_op02_contract_valid_for_op04(mrb_op02_dri_op09_adapter_candidate_extraction_and_scan)
    op03_valid = _mrb_op03_contract_valid_for_op04(mrb_op03_dhr_op03_ready_material_intake)
    request_present = isinstance(manual_reintake_request_bodyfree, Mapping)
    request_valid = _manual_reintake_request_valid(manual_reintake_request_bodyfree)
    op02_ready = bool(op02_valid and op02.get("mrb_op02_ready_for_mrb_op03") is True)
    op03_ready = bool(op03_valid and op03.get("mrb_op03_ready_for_mrb_op04") is True)
    candidate = op02.get("external_actual_operation_evidence_claim_bodyfree_optional") if isinstance(op02.get("external_actual_operation_evidence_claim_bodyfree_optional"), Mapping) else {}
    dhr_op03_material = op03.get("dhr_op03_ready_material_bodyfree") if isinstance(op03.get("dhr_op03_ready_material_bodyfree"), Mapping) else {}

    forbidden = _dedupe_clean_refs([
        *_scan_forbidden_payload_key_paths(request, path="manual_reintake_request"),
        *_scan_forbidden_payload_key_paths(candidate, path="dri_op09_candidate"),
        *_scan_forbidden_payload_key_paths(dhr_op03_material, path="dhr_op03_ready_material"),
    ], max_length=360)
    body_like = _dedupe_clean_refs([
        *_scan_body_like_value_paths(request, path="manual_reintake_request"),
        *_scan_body_like_value_paths(candidate, path="dri_op09_candidate"),
        *_scan_body_like_value_paths(dhr_op03_material, path="dhr_op03_ready_material"),
    ], max_length=360)
    promotion = _dedupe_clean_refs([
        *_scan_promotion_claim_refs(request, path="manual_reintake_request"),
        *_scan_promotion_claim_refs(candidate, path="dri_op09_candidate"),
        *_scan_promotion_claim_refs(dhr_op03_material, path="dhr_op03_ready_material"),
    ], max_length=360)

    blockers: list[str] = []
    reasons: list[str] = []
    if forbidden:
        blockers.append("mrb_op04_forbidden_payload_key_detected_before_envelope")
    if body_like:
        blockers.append("mrb_op04_body_like_value_detected_before_envelope")
    if promotion:
        blockers.append("mrb_op04_promotion_or_autorun_claim_detected_before_envelope")

    op02_status = _clean_ref(op02.get("mrb_op02_status_ref"), default="mrb_op02_status_missing", max_length=300)
    op03_status = _clean_ref(op03.get("mrb_op03_status_ref"), default="mrb_op03_status_missing", max_length=300)
    if op02_status == P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("mrb_op02_blocked_before_envelope")
    if op03_status == P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("mrb_op03_blocked_before_envelope")

    if blockers:
        status = P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        reasons = ["manual_reintake_input_envelope_blocked_before_dhr_op04_call"]
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP04_ENVELOPE_REF
    elif not request_present:
        status = P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF
        reasons = ["manual_reintake_request_not_provided"]
        blockers = ["manual_reintake_request_missing"]
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
    elif not op02 or not op03:
        status = P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF
        reasons = ["mrb_op02_or_mrb_op03_material_missing_before_dhr_op04_input_envelope"]
        blockers = ["mrb_op02_or_mrb_op03_material_missing"]
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
    elif not request_valid or not op02_valid or not op03_valid:
        status = P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_REPAIR_INPUT_ENVELOPE_REF
        reasons = ["manual_request_or_mrb_material_contract_repair_required_before_dhr_op04_input_envelope"]
        blockers = []
        if not request_valid:
            blockers.append("manual_reintake_request_contract_invalid")
        if not op02_valid:
            blockers.append("mrb_op02_contract_invalid")
        if not op03_valid:
            blockers.append("mrb_op03_contract_invalid")
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP04_ENVELOPE_REF
    elif not (op02_ready and op03_ready and candidate and dhr_op03_material):
        status = P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF
        reasons = ["dri_candidate_or_dhr_op03_ready_material_missing_before_manual_dhr_op04_call"]
        blockers = ["dri_candidate_or_dhr_op03_ready_material_missing"]
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
    else:
        status = P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_READY_FOR_OP05_REF
        reasons = ["manual_reintake_request_and_ready_material_assembled_without_dhr_op04_call"]
        blockers = []
        next_step = P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF

    ready = status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_READY_FOR_OP05_REF
    envelope = {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_DHR_OP04_INPUT_ENVELOPE_SCHEMA_VERSION,
        "material_kind": "dhr_op04_manual_reintake_input_envelope",
        "review_session_id": session_id,
        "manual_reintake_request_present": True,
        "manual_reintake_requested": True,
        "requested_operation_step_ref": P7_R54_AHR_POST_DRI_MRB_REQUESTED_DHR_OP04_OPERATION_STEP_REF,
        "requested_source_material_ref": P7_R54_AHR_POST_DRI_MRB_REQUESTED_SOURCE_MATERIAL_REF,
        "requested_target_helper_ref": P7_R54_AHR_POST_DRI_MRB_REQUESTED_TARGET_HELPER_REF,
        "dri_op10_ready_for_dhr_material": True,
        "dri_op09_candidate_present": True,
        "dhr_op03_ready": True,
        "dhr_op04_input_ready": True,
        "external_actual_operation_evidence_claim_bodyfree_optional": dict(candidate),
        "op03_elr_op17_dmd_compatible_receipt_candidate_extraction": dict(dhr_op03_material),
        "dhr_op04_called_here": False,
        "dhr_op05_auto_call_allowed": False,
        "downstream_auto_execution_allowed": False,
        "body_free": True,
    } if ready else {}

    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_dhr_op04_input_envelope_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_contract_valid": op02_valid,
        "op02_ready_for_mrb_op03": op02_ready,
        "op02_status_ref": op02_status,
        "op03_contract_valid": op03_valid,
        "op03_ready_for_mrb_op04": op03_ready,
        "op03_status_ref": op03_status,
        "manual_reintake_request_present": request_present,
        "manual_reintake_request_contract_valid": request_valid,
        "manual_reintake_requested": bool(request_valid and request.get("manual_reintake_requested") is True),
        "manual_request_bodyfree": bool(request_valid and request.get("manual_request_bodyfree") is True),
        "requested_operation_step_ref": _clean_ref(request.get("requested_operation_step_ref"), default="manual_request_step_missing", max_length=280),
        "requested_source_material_ref": _clean_ref(request.get("requested_source_material_ref"), default="manual_request_source_missing", max_length=280),
        "requested_target_helper_ref": _clean_ref(request.get("requested_target_helper_ref"), default="manual_request_target_missing", max_length=360),
        "dri_op09_candidate_present": bool(candidate),
        "dri_op10_ready": bool(op02_ready and op02.get("op01_ready_for_mrb_op02") is True),
        "dri_op12_closed_bodyfree": bool(op02_ready and op02.get("op01_contract_valid") is True),
        "dhr_op03_ready": op03_ready,
        "external_actual_operation_evidence_claim_bodyfree_optional": dict(candidate) if ready else {},
        "op03_elr_op17_dmd_compatible_receipt_candidate_extraction": dict(dhr_op03_material) if ready else {},
        "dhr_op04_input_envelope_bodyfree": envelope,
        "dhr_op04_input_envelope_ready": ready,
        "mrb_op04_status_ref": status,
        "manual_reintake_request_input_envelope_status_ref": status,
        "mrb_op04_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP04_ALLOWED_STATUS_REFS),
        "mrb_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP04_ALLOWED_STATUS_REFS),
        "mrb_op04_ready_for_mrb_op05": ready,
        "mrb_op04_waiting_for_manual_request_or_material": status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_WAITING_FOR_MANUAL_REQUEST_OR_MATERIAL_REF,
        "mrb_op04_repair_required": status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_REPAIR_INPUT_ENVELOPE_REF,
        "mrb_op04_bodyfree_leak_promotion_or_autorun_blocked": status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
        "mrb_op04_manual_hold_unresolved_no_promotion": status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_MANUAL_HOLD_REF,
        "mrb_op04_reason_refs": reasons,
        "mrb_op04_reason_ref_count": len(reasons),
        "mrb_op04_blocker_refs": _dedupe_clean_refs(blockers, max_length=320),
        "mrb_op04_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=320)),
        "mrb_op04_forbidden_payload_key_path_refs": forbidden,
        "mrb_op04_forbidden_payload_key_path_count": len(forbidden),
        "mrb_op04_body_like_value_path_refs": body_like,
        "mrb_op04_body_like_value_path_count": len(body_like),
        "mrb_op04_promotion_claim_refs": promotion,
        "mrb_op04_promotion_claim_ref_count": len(promotion),
        "mrb_op04_does_not_call_dhr_op04": True,
        "dhr_op04_called_by_manual_reintake_boundary": False,
        "dhr_op05_auto_call_allowed": False,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP04")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DRI_MRB_OP04_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF, source="P7-R54-AHR-PostDRI-MRB-OP04")
    for key in ("mrb_op04_does_not_call_dhr_op04", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP04 required true changed: {key}")
    if data.get("dhr_op04_called_by_manual_reintake_boundary") is not False or data.get("dhr_op05_auto_call_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 call or downstream flag changed")
    status = data.get("mrb_op04_status_ref")
    flags = [
        data.get("mrb_op04_ready_for_mrb_op05") is True,
        data.get("mrb_op04_waiting_for_manual_request_or_material") is True,
        data.get("mrb_op04_repair_required") is True,
        data.get("mrb_op04_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("mrb_op04_manual_hold_unresolved_no_promotion") is True,
    ]
    if status not in P7_R54_AHR_POST_DRI_MRB_OP04_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 exactly one status branch must be selected")
    if status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_READY_FOR_OP05_REF:
        for key in ("op02_contract_valid", "op02_ready_for_mrb_op03", "op03_contract_valid", "op03_ready_for_mrb_op04", "manual_reintake_request_contract_valid", "manual_reintake_requested", "manual_request_bodyfree", "dri_op09_candidate_present", "dhr_op03_ready", "dhr_op04_input_envelope_ready"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP04 ready required true changed: {key}")
        if not data.get("external_actual_operation_evidence_claim_bodyfree_optional") or not data.get("op03_elr_op17_dmd_compatible_receipt_candidate_extraction") or not data.get("dhr_op04_input_envelope_bodyfree"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 ready branch must carry body-free input material")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 ready next step changed")
    else:
        if data.get("external_actual_operation_evidence_claim_bodyfree_optional") != {} or data.get("op03_elr_op17_dmd_compatible_receipt_candidate_extraction") != {} or data.get("dhr_op04_input_envelope_bodyfree") != {} or data.get("dhr_op04_input_envelope_ready") is not False:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 non-ready branch must not carry DHR-OP04 input")
    if status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF and not data.get("mrb_op04_blocker_refs"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 blocked branch requires blocker refs")
    if status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_REPAIR_INPUT_ENVELOPE_REF and data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP04_ENVELOPE_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP04 repair next step changed")
    return True


def _dhr_op04_contract_valid_for_mrb(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract(data) is True
    except ValueError:
        return False


def _mrb_status_and_next_for_dhr_op04(dhr_status_ref: str) -> tuple[str, str]:
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF:
        return (P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF, P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF)
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_REF:
        return (P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF, P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF)
    if dhr_status_ref == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_WAITING_FOR_EXTERNAL_BODYFREE_CLAIM_REF:
        return (P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF, P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF)
    return (P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF, P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF)


def build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture(
    *,
    mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope: Mapping[str, Any] | None = None,
    manual_reintake_input_envelope: Mapping[str, Any] | None = None,
    mrb_op02_dri_op09_adapter_candidate_extraction_and_scan: Mapping[str, Any] | None = None,
    mrb_op03_dhr_op03_ready_material_intake: Mapping[str, Any] | None = None,
    manual_reintake_request_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Call existing DHR-OP04 once only when OP04 envelope is ready, then stop."""

    op04_source = mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope
    if op04_source is None and isinstance(manual_reintake_input_envelope, Mapping) and manual_reintake_input_envelope.get("schema_version") == P7_R54_AHR_POST_DRI_MRB_OP04_SCHEMA_VERSION:
        op04_source = manual_reintake_input_envelope
    if op04_source is None:
        op04_source = build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope(
            mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=mrb_op02_dri_op09_adapter_candidate_extraction_and_scan,
            mrb_op03_dhr_op03_ready_material_intake=mrb_op03_dhr_op03_ready_material_intake,
            manual_reintake_request_bodyfree=manual_reintake_request_bodyfree,
            review_session_id=review_session_id,
        )
    op04 = op04_source if isinstance(op04_source, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op04.get("review_session_id"))
    op04_valid = _mrb_op04_contract_valid_for_op05(op04_source)
    op04_ready = bool(op04_valid and op04.get("mrb_op04_ready_for_mrb_op05") is True and op04.get("dhr_op04_input_envelope_ready") is True)
    op04_status = _clean_ref(op04.get("mrb_op04_status_ref"), default="mrb_op04_status_missing", max_length=320)
    envelope = op04.get("dhr_op04_input_envelope_bodyfree") if isinstance(op04.get("dhr_op04_input_envelope_bodyfree"), Mapping) else {}
    envelope_forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(envelope, path="mrb_op04_input_envelope"), max_length=360)
    envelope_body_like = _dedupe_clean_refs(_scan_body_like_value_paths(envelope, path="mrb_op04_input_envelope"), max_length=360)
    envelope_promotion = _dedupe_clean_refs(_scan_promotion_claim_refs(envelope, path="mrb_op04_input_envelope"), max_length=360)

    blockers: list[str] = []
    reasons: list[str] = []
    called = False
    dhr_result: dict[str, Any] = {}
    dhr_valid = False
    if envelope_forbidden:
        blockers.append("mrb_op04_input_envelope_forbidden_payload_key_detected")
    if envelope_body_like:
        blockers.append("mrb_op04_input_envelope_body_like_value_detected")
    if envelope_promotion:
        blockers.append("mrb_op04_input_envelope_promotion_or_autorun_claim_detected")

    if blockers or op04_status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        status = P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        reasons = ["explicit_manual_dhr_op04_call_blocked_by_bodyfree_no_promotion_scan"]
        if op04_status == P7_R54_AHR_POST_DRI_MRB_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
            blockers.append("mrb_op04_blocked_before_dhr_op04_call")
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP04_ENVELOPE_REF
    elif not op04_valid:
        status = P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF
        reasons = ["mrb_op04_contract_repair_required_before_explicit_dhr_op04_call"]
        blockers = ["mrb_op04_contract_invalid"]
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP04_ENVELOPE_REF
    elif not op04_ready:
        status = P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF
        reasons = ["mrb_op04_not_ready_for_explicit_manual_dhr_op04_call"]
        blockers = ["mrb_op04_not_ready_for_mrb_op05"]
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
    else:
        dhr_result = dhr.build_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification(
            op03_elr_op17_dmd_compatible_receipt_candidate_extraction=envelope.get("op03_elr_op17_dmd_compatible_receipt_candidate_extraction"),
            external_actual_operation_evidence_claim_bodyfree_optional=envelope.get("external_actual_operation_evidence_claim_bodyfree_optional"),
            review_session_id=session_id,
        )
        dhr_valid = _dhr_op04_contract_valid_for_mrb(dhr_result)
        called = True
        dhr_status = _clean_ref(dhr_result.get("dhr_op04_status_ref"), default="dhr_op04_status_missing", max_length=320)
        if not dhr_valid:
            status = P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF
            reasons = ["dhr_op04_result_contract_invalid_after_manual_call"]
            blockers = ["dhr_op04_contract_invalid_after_manual_call"]
            next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF
        else:
            status, next_step = _mrb_status_and_next_for_dhr_op04(dhr_status)
            reasons = ["explicit_manual_dhr_op04_result_captured_and_stopped"]
            blockers = []

    dhr_status_ref = _clean_ref(dhr_result.get("dhr_op04_status_ref") if isinstance(dhr_result, Mapping) else "not_called", default="not_called", max_length=320)
    confirmed = bool(called and dhr_valid and dhr_result.get("actual_source_claim_confirmed_for_downstream_handoff") is True)
    actual_bodyfree = bool(called and dhr_valid and dhr_result.get("actual_source_claim_bodyfree") is True)
    false_flags = _false_flags()
    false_flags.update({
        "dhr_op04_called_here": called,
        "dhr_op04_called_by_mrb": called,
        "actual_source_claim_confirmed_for_downstream_handoff": confirmed,
    })

    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_result_capture_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_contract_valid": op04_valid,
        "op04_ready_for_mrb_op05": op04_ready,
        "op04_status_ref": op04_status,
        "dhr_op04_input_envelope_ready": bool(op04_ready and envelope),
        "dhr_op04_called_by_manual_reintake_boundary": called,
        "dhr_op04_called_by_dri": False,
        "dhr_op04_result_captured": bool(called and dhr_valid),
        "dhr_op04_contract_valid": dhr_valid,
        "dhr_op04_result_bodyfree": dict(dhr_result) if called and dhr_valid else {},
        "dhr_op04_status_ref": dhr_status_ref,
        "dhr_op04_result_status_ref": dhr_status_ref,
        "dhr_op04_next_required_step_ref": _clean_ref(dhr_result.get("next_required_step") if isinstance(dhr_result, Mapping) else "not_called", default="not_called", max_length=320),
        "actual_source_claim_bodyfree": actual_bodyfree,
        "actual_source_claim_origin_ref": _clean_ref(dhr_result.get("actual_source_claim_origin_ref") if isinstance(dhr_result, Mapping) else "not_called", default="not_called", max_length=320),
        "actual_local_only_human_review_by_person_confirmed": bool(called and dhr_valid and dhr_result.get("actual_local_only_human_review_by_person_confirmed") is True),
        "mrb_op05_status_ref": status,
        "dhr_op04_manual_call_result_capture_status_ref": status,
        "mrb_op05_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP05_ALLOWED_STATUS_REFS),
        "mrb_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP05_ALLOWED_STATUS_REFS),
        "mrb_op05_dhr_op04_confirmed_bodyfree_stopped": status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
        "mrb_op05_dhr_op04_not_confirmed_retry_or_start_required_stopped": status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
        "mrb_op05_dhr_op04_waiting_external_claim_stopped": status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
        "mrb_op05_dhr_op04_invalid_repair_required_stopped": status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
        "mrb_op05_waiting_before_dhr_op04_call": status == P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF,
        "mrb_op05_repair_required_before_dhr_op04_call": status == P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
        "mrb_op05_bodyfree_leak_promotion_or_autorun_blocked": status == P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
        "mrb_op05_reason_refs": reasons,
        "mrb_op05_reason_ref_count": len(reasons),
        "mrb_op05_blocker_refs": _dedupe_clean_refs(blockers, max_length=320),
        "mrb_op05_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=320)),
        "mrb_op05_does_not_call_dhr_op05": True,
        "mrb_op05_does_not_call_dhr_op06": True,
        "mrb_op05_does_not_execute_dmd_r52_or_release": True,
        "mrb_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "dhr_op05_auto_call_allowed": False,
        "dhr_op06_auto_call_allowed": False,
        "downstream_auto_execution_allowed": False,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP05")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DRI_MRB_OP05_SCHEMA_VERSION or data.get("operation_step_ref") != P7_R54_AHR_POST_DRI_MRB_OP05_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 identity changed")
    if data.get("phase") != P7_R54_AHR_POST_DRI_MRB_PHASE or data.get("step") != P7_R54_AHR_POST_DRI_MRB_STEP or data.get("scope") != P7_R54_AHR_POST_DRI_MRB_SCOPE:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 base identity changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE or data.get("git_connection_required") is not False or data.get("git_checked") is not False or data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 body-free/source boundary changed")
    _assert_public_contract_false(data, source="P7-R54-AHR-PostDRI-MRB-OP05")
    _assert_false_mapping(data, field="mrb_no_touch_contract", source="P7-R54-AHR-PostDRI-MRB-OP05")
    _assert_false_mapping(data, field="body_free_markers", source="P7-R54-AHR-PostDRI-MRB-OP05")
    for key in P7_R54_AHR_POST_DRI_MRB_OP05_REQUIRED_FALSE_FIELD_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP05 downstream false flag promoted: {key}")
    for key in ("mrb_op05_does_not_call_dhr_op05", "mrb_op05_does_not_call_dhr_op06", "mrb_op05_does_not_execute_dmd_r52_or_release", "mrb_op05_does_not_start_p5_p6_p8_p7_or_release", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP05 required true boundary changed: {key}")
    for key in ("dhr_op05_auto_call_allowed", "dhr_op06_auto_call_allowed", "downstream_auto_execution_allowed", "dhr_op04_called_by_dri"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP05 false call/downstream flag changed: {key}")
    status = data.get("mrb_op05_status_ref")
    flags = [
        data.get("mrb_op05_dhr_op04_confirmed_bodyfree_stopped") is True,
        data.get("mrb_op05_dhr_op04_not_confirmed_retry_or_start_required_stopped") is True,
        data.get("mrb_op05_dhr_op04_waiting_external_claim_stopped") is True,
        data.get("mrb_op05_dhr_op04_invalid_repair_required_stopped") is True,
        data.get("mrb_op05_waiting_before_dhr_op04_call") is True,
        data.get("mrb_op05_repair_required_before_dhr_op04_call") is True,
        data.get("mrb_op05_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status not in P7_R54_AHR_POST_DRI_MRB_OP05_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 exactly one status branch must be selected")
    called = status in P7_R54_AHR_POST_DRI_MRB_OP05_CALLED_STATUS_REFS
    if called:
        for key in ("op04_contract_valid", "op04_ready_for_mrb_op05", "dhr_op04_input_envelope_ready", "dhr_op04_called_by_manual_reintake_boundary", "dhr_op04_called_by_mrb", "dhr_op04_called_here", "dhr_op04_result_captured", "dhr_op04_contract_valid"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP05 called branch required true changed: {key}")
        if not data.get("dhr_op04_result_bodyfree"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 called branch must carry DHR-OP04 body-free result")
    else:
        if data.get("dhr_op04_called_by_manual_reintake_boundary") is not False or data.get("dhr_op04_called_by_mrb") is not False or data.get("dhr_op04_called_here") is not False or data.get("dhr_op04_result_captured") is not False or data.get("dhr_op04_result_bodyfree") != {}:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 pre-call branch must not call DHR-OP04")
    if status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF:
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 confirmed mapping changed")
    elif called:
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not False:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 non-confirmed called branch cannot confirm source claim")
    if status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF and data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 not-confirmed mapping changed")
    if status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF and data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 waiting mapping changed")
    if status == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF and data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP05 invalid mapping changed")
    return True


build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_input_envelope = (
    build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope
)
assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_input_envelope_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract
)


# ---------------------------------------------------------------------------
# MRB-OP06 / MRB-OP07: DHR-OP04 result classifier and no-touch guard.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DRI_MRB_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op06_dhr_op04_result_classifier_stop_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op07_no_touch_selected_regression_guard.bodyfree.v1"
)
P7_R54_AHR_POST_DRI_MRB_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dri.mrb."
    "op08_bodyfree_result_memo_closure.bodyfree.v1"
)

P7_R54_AHR_POST_DRI_MRB_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:7]
)
P7_R54_AHR_POST_DRI_MRB_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[7:]
)
P7_R54_AHR_POST_DRI_MRB_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[:8]
)
P7_R54_AHR_POST_DRI_MRB_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS[8:]
)
P7_R54_AHR_POST_DRI_MRB_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STEP_REFS
)
P7_R54_AHR_POST_DRI_MRB_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_DRI_MRB_STATUS_READY_TO_CALL_DHR_OP04_MANUALLY_NO_DOWNSTREAM_AUTO_EXECUTION_REF: Final = (
    "MRB_STATUS_READY_TO_CALL_DHR_OP04_MANUALLY_NO_DOWNSTREAM_AUTO_EXECUTION"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL_REF: Final = (
    "MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF: Final = (
    "MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "MRB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_DRI_MRB_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF: Final = (
    "MRB_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_DRI_MRB_ALLOWED_BRANCH_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_READY_TO_CALL_DHR_OP04_MANUALLY_NO_DOWNSTREAM_AUTO_EXECUTION_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
)
P7_R54_AHR_POST_DRI_MRB_OP06_ALLOWED_BRANCH_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_ALLOWED_BRANCH_REFS
)
P7_R54_AHR_POST_DRI_MRB_OP06_CALLED_RESULT_BRANCH_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
)

P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_READY_FOR_OP08_REF: Final = (
    "MRB_OP07_NO_TOUCH_SELECTED_REGRESSION_GUARD_READY_FOR_OP08"
)
P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_WAITING_FOR_VALIDATION_REFS_REF: Final = (
    "MRB_OP07_WAITING_FOR_SELECTED_REGRESSION_OR_COMPILEALL_REFS"
)
P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_REPAIR_REQUIRED_REF: Final = (
    "MRB_OP07_REPAIR_REQUIRED_FOR_NO_TOUCH_OR_VALIDATION_REFS"
)
P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_BLOCKED_NO_TOUCH_CHANGE_REF: Final = (
    "MRB_OP07_BLOCKED_API_DB_RN_RUNTIME_RESPONSE_KEY_OR_P8_QUESTION_TOUCH"
)
P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_READY_FOR_OP08_REF,
    P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_WAITING_FOR_VALIDATION_REFS_REF,
    P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_BLOCKED_NO_TOUCH_CHANGE_REF,
)

P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_CHANGED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op00_op01_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_op03_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_op05_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705.py",
    "tests/R54_AHR_PostDRI_DHROP04ManualReintake_MRB_OP00_OP01_Result_20260705.md",
    "tests/R54_AHR_PostDRI_DHROP04ManualReintake_MRB_OP02_OP03_Result_20260705.md",
    "tests/R54_AHR_PostDRI_DHROP04ManualReintake_MRB_OP04_OP05_Result_20260705.md",
    "tests/R54_AHR_PostDRI_DHROP04ManualReintake_MRB_OP06_OP07_Result_20260705.md",
    "tests/R54_AHR_PostDRI_DHROP04ManualReintake_MRB_OP00_OP08_Result_20260705.md",
)
P7_R54_AHR_POST_DRI_MRB_OP07_BLOCKED_CHANGE_TOKEN_REFS: Final[tuple[str, ...]] = (
    "/Cocolon/",
    "Cocolon/",
    "/api/",
    "/db/",
    "database",
    "schema.sql",
    "migration",
    "response_key",
    "runtime_generation",
    "runtime_prompt",
    "question_route",
    "question_schema",
    "question_trigger",
    "p8_question",
)
P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op00_op01_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_op03_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_op05_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py",
)
P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_op09_20260705.py",
    "tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_op11_20260705.py",
    "tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_20260705.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_op03_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
)
P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)

P7_R54_AHR_POST_DRI_MRB_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_material_present", "op05_contract_valid", "op05_schema_version", "op05_operation_step_ref", "op05_material_ref", "op05_status_ref", "op05_next_required_step",
    "op05_dhr_op04_result_captured", "op05_dhr_op04_called_by_manual_reintake_boundary", "op05_dhr_op04_called_by_dri", "op05_dhr_op04_called_by_mrb", "op05_dhr_op04_called_here",
    "dhr_op04_result_captured", "dhr_op04_contract_valid", "dhr_op04_result_bodyfree", "dhr_op04_status_ref", "dhr_op04_result_status_ref", "dhr_op04_next_required_step_ref",
    "actual_source_claim_confirmed_for_downstream_handoff", "actual_source_claim_bodyfree", "actual_source_claim_origin_ref",
    "mrb_op06_status_ref", "dhr_op04_result_classifier_status_ref", "mrb_branch_ref", "mrb_allowed_branch_refs", "mrb_allowed_branch_ref_count",
    "exactly_one_mrb_result_branch", "mrb_op06_dhr_op04_confirmed_bodyfree_stopped", "mrb_op06_dhr_op04_not_confirmed_retry_or_start_required_stopped", "mrb_op06_dhr_op04_waiting_external_claim_stopped", "mrb_op06_dhr_op04_invalid_repair_required_stopped",
    "mrb_op06_waiting_before_dhr_op04_call_stopped", "mrb_op06_repair_required_before_dhr_op04_call_stopped", "mrb_op06_bodyfree_leak_promotion_or_autorun_blocked", "mrb_op06_manual_hold_unresolved_no_promotion",
    "mrb_op06_reason_refs", "mrb_op06_reason_ref_count", "mrb_op06_blocker_refs", "mrb_op06_blocker_ref_count",
    "mrb_op06_result_is_dhr_op04_only", "mrb_op06_does_not_call_dhr_op04_again", "mrb_op06_does_not_call_dhr_op05", "mrb_op06_does_not_call_dhr_op06", "mrb_op06_does_not_execute_dmd_r52_or_release", "mrb_op06_does_not_start_p5_p6_p8_p7_or_release", "mrb_op06_does_not_materialize_p8_question_spec",
    "dhr_op05_auto_call_allowed", "dhr_op06_auto_call_allowed", "downstream_auto_execution_allowed", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "mrb_next_required_step", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "changed_file_refs", "changed_file_ref_count", "allowed_changed_file_refs", "allowed_changed_file_ref_count", "changed_files_within_allowed_refs", "unexpected_changed_file_refs", "unexpected_changed_file_ref_count",
    "blocked_change_token_refs", "blocked_change_token_ref_count", "blocked_no_touch_change_refs", "blocked_no_touch_change_ref_count", "api_db_rn_runtime_response_key_or_p8_question_touch_blocked",
    "target_test_refs", "target_test_ref_count", "required_target_test_refs", "required_target_test_ref_count", "target_tests_recorded", "missing_target_test_refs", "missing_target_test_ref_count",
    "selected_regression_refs", "selected_regression_ref_count", "required_selected_regression_refs", "required_selected_regression_ref_count", "selected_regression_recorded", "missing_selected_regression_refs", "missing_selected_regression_ref_count",
    "compileall_refs", "compileall_ref_count", "required_compileall_refs", "required_compileall_ref_count", "compileall_recorded", "missing_compileall_refs", "missing_compileall_ref_count",
    "mrb_op07_status_ref", "no_touch_selected_regression_guard_status_ref", "mrb_op07_allowed_status_refs", "mrb_op07_allowed_status_ref_count",
    "mrb_op07_ready_for_mrb_op08", "mrb_op07_waiting_for_validation_refs", "mrb_op07_repair_required", "mrb_op07_blocked_no_touch_change", "mrb_op07_reason_refs", "mrb_op07_reason_ref_count", "mrb_op07_blocker_refs", "mrb_op07_blocker_ref_count",
    "mrb_op07_does_not_call_dhr_op04", "mrb_op07_does_not_call_dhr_op05", "mrb_op07_does_not_execute_dmd_r52_or_release", "mrb_op07_does_not_start_p5_p6_p8_p7_or_release", "mrb_op07_does_not_change_api_db_rn_runtime_response_key", "mrb_op07_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF: Final = (
    "MRB_OP08_BODYFREE_RESULT_MEMO_CLOSED_STOPPED"
)
P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_WAITING_FOR_OP06_OP07_OR_VALIDATION_REF: Final = (
    "MRB_OP08_WAITING_FOR_OP06_OP07_OR_VALIDATION_REFS"
)
P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_REPAIR_REQUIRED_REF: Final = (
    "MRB_OP08_REPAIR_REQUIRED_FOR_RESULT_MEMO_CLOSURE_INPUTS"
)
P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "MRB_OP08_BLOCKED_BODYFREE_RESULT_MEMO_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_DRI_MRB_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_WAITING_FOR_OP06_OP07_OR_VALIDATION_REF,
    P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_DRI_MRB_OP08_NEXT_STEP_WAIT_REF: Final = (
    "wait_for_op06_op07_validation_before_mrb_op08_result_memo_closure"
)
P7_R54_AHR_POST_DRI_MRB_OP08_NEXT_STEP_REPAIR_REF: Final = (
    "repair_mrb_op08_result_memo_closure_inputs"
)
P7_R54_AHR_POST_DRI_MRB_OP08_NEXT_STEP_BLOCKED_REF: Final = (
    "blocked_mrb_op08_bodyfree_result_memo_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_DRI_MRB_OP08_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "MRB-OP00/OP01 target",
    "MRB-OP02/OP03 target",
    "MRB-OP04/OP05 target",
    "MRB-OP06/OP07 target",
    "MRB-OP08 target",
    "DRI selected regression",
    "DHR selected regression",
    "compileall",
)
P7_R54_AHR_POST_DRI_MRB_OP08_RESULT_MEMO_REQUIRED_FALSE_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS
    if key != "actual_source_claim_confirmed_for_downstream_handoff"
)
P7_R54_AHR_POST_DRI_MRB_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_material_present", "op01_contract_valid", "op01_dri_op10_branch_ref", "op01_dri_op12_result_memo_closure_intake_status_ref", "op01_dri_op12_result_memo_bodyfree_closed",
    "op02_material_present", "op02_contract_valid", "op02_dri_op09_candidate_input_accepted", "op02_dri_op09_candidate_present", "op02_status_ref", "op02_candidate_not_dhr_confirmed",
    "op03_material_present", "op03_contract_valid", "op03_dhr_op03_ready_material_status_ref", "op03_dhr_op03_ready", "op03_receipt_shape_not_actual_source_confirmation",
    "op04_material_present", "op04_contract_valid", "op04_manual_reintake_request_present", "op04_dhr_op04_input_envelope_ready", "op04_dhr_op04_called_here",
    "op05_material_present", "op05_contract_valid", "op05_dhr_op04_manual_call_performed_by_mrb", "op05_dhr_op04_result_captured", "op05_status_ref",
    "op06_material_present", "op06_contract_valid", "op06_mrb_selected_branch_ref", "op06_mrb_next_required_step", "op06_dhr_op04_result_captured", "op06_dhr_op04_status_ref", "op06_actual_source_claim_confirmed_for_downstream_handoff",
    "op07_material_present", "op07_contract_valid", "op07_status_ref", "op07_ready_for_op08", "op07_no_touch_guard_ready", "op07_selected_regression_recorded", "op07_compileall_recorded",
    "validation_summary_bodyfree_present", "validation_summary_bodyfree_accepted", "validation_summary_bodyfree_ref",
    "validation_summary_forbidden_payload_key_path_refs", "validation_summary_forbidden_payload_key_path_count", "validation_summary_body_like_value_path_refs", "validation_summary_body_like_value_path_count", "validation_summary_promotion_claim_refs", "validation_summary_promotion_claim_ref_count",
    "validation_command_summary_refs", "validation_command_summary_ref_count",
    "result_memo_bodyfree_present", "result_memo_bodyfree_accepted", "result_memo_bodyfree_ref",
    "result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count", "result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count", "result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count",
    "combined_run_status_ref", "full_backend_suite_green_confirmed", "combined_mrb_dri_dhr_green_confirmed", "combined_green_claim_not_made_when_not_passed",
    "mrb_op08_status_ref", "bodyfree_result_memo_closure_status_ref", "mrb_op08_allowed_status_refs", "mrb_op08_allowed_status_ref_count",
    "mrb_op08_closed_bodyfree_stopped", "mrb_op08_waiting_for_op06_op07_or_validation", "mrb_op08_repair_required", "mrb_op08_bodyfree_leak_promotion_or_autorun_blocked",
    "mrb_op08_reason_refs", "mrb_op08_reason_ref_count", "mrb_op08_blocker_refs", "mrb_op08_blocker_ref_count",
    "mrb_selected_branch_ref", "dhr_op04_manual_call_performed_by_mrb", "dhr_op04_result_status_ref", "actual_source_claim_confirmed_for_downstream_handoff",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started",
    "mrb_op08_does_not_call_dhr_op04", "mrb_op08_does_not_call_dhr_op05", "mrb_op08_does_not_call_dhr_op06", "mrb_op08_does_not_execute_dmd_r52_or_release", "mrb_op08_does_not_start_p5_p6_p8_p7_or_release", "mrb_op08_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "mrb_next_required_step", "next_required_step",
    "public_contract", "mrb_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

def _mrb_op05_contract_valid_for_op06(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(data) is True
    except ValueError:
        return False


def _mrb_op06_branch_next_reason_blocker(
    *, op05_present: bool, op05_contract_valid: bool, op05_status_ref: str, dhr_status_ref: str, dhr_op04_result_captured: bool
) -> tuple[str, str, list[str], list[str]]:
    if not op05_present:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
            ["mrb_op05_result_capture_not_provided_yet"],
            ["mrb_op05_result_capture_missing"],
        )
    if not op05_contract_valid:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_DRI_INTAKE_REF,
            ["mrb_op05_result_capture_contract_invalid_before_classification"],
            ["mrb_op05_contract_invalid"],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF,
            ["dhr_op04_confirmed_bodyfree_result_captured_and_stopped"],
            [],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF,
            ["dhr_op04_not_confirmed_retry_or_start_required_result_captured_and_stopped"],
            [],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF,
            ["dhr_op04_waiting_external_bodyfree_claim_result_captured_and_stopped"],
            [],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF,
            ["dhr_op04_invalid_repair_required_result_captured_and_stopped"],
            [],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_WAITING_BEFORE_DHR_OP04_CALL_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF,
            ["manual_dhr_op04_call_waiting_for_ready_material"],
            ["mrb_op05_waiting_before_dhr_op04_call"],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_OP04_ENVELOPE_REF,
            ["manual_dhr_op04_call_repair_required_before_result"],
            ["mrb_op05_repair_required_before_dhr_op04_call"],
        )
    if op05_status_ref == P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_OP04_ENVELOPE_REF,
            ["manual_dhr_op04_call_blocked_by_bodyfree_promotion_or_autorun_guard"],
            ["mrb_op05_bodyfree_leak_promotion_or_autorun_blocked"],
        )
    if dhr_op04_result_captured and dhr_status_ref not in dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_ALLOWED_STATUS_REFS:
        return (
            P7_R54_AHR_POST_DRI_MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
            P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF,
            ["dhr_op04_result_status_ref_unknown_after_capture"],
            ["dhr_op04_status_ref_unknown"],
        )
    return (
        P7_R54_AHR_POST_DRI_MRB_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
        P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_REF,
        ["mrb_op05_result_capture_unresolved_without_downstream_promotion"],
        ["mrb_op05_status_unresolved"],
    )


def build_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary(
    *,
    mrb_op05_explicit_manual_dhr_op04_call_and_result_capture: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Classify the MRB-OP05 DHR-OP04 result and stop without downstream automation."""

    op05 = mrb_op05_explicit_manual_dhr_op04_call_and_result_capture if isinstance(mrb_op05_explicit_manual_dhr_op04_call_and_result_capture, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op05.get("review_session_id"))
    op05_present = isinstance(mrb_op05_explicit_manual_dhr_op04_call_and_result_capture, Mapping)
    op05_valid = _mrb_op05_contract_valid_for_op06(mrb_op05_explicit_manual_dhr_op04_call_and_result_capture)
    op05_status = _clean_ref(op05.get("mrb_op05_status_ref"), default="mrb_op05_status_missing", max_length=260)
    dhr_status = _clean_ref(op05.get("dhr_op04_status_ref"), default="dhr_op04_status_missing", max_length=260)
    dhr_result_captured = bool(op05.get("dhr_op04_result_captured") is True and op05.get("dhr_op04_result_bodyfree"))
    branch, next_step, reasons, blockers = _mrb_op06_branch_next_reason_blocker(
        op05_present=op05_present,
        op05_contract_valid=op05_valid,
        op05_status_ref=op05_status,
        dhr_status_ref=dhr_status,
        dhr_op04_result_captured=dhr_result_captured,
    )
    false_flags = _false_flags()
    false_flags.update({
        "dhr_op04_called_by_mrb": bool(op05.get("dhr_op04_called_by_mrb") is True),
        "dhr_op04_called_here": False,
        "actual_source_claim_confirmed_for_downstream_handoff": bool(branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF and op05.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
    })
    result_bodyfree = op05.get("dhr_op04_result_bodyfree") if dhr_result_captured and isinstance(op05.get("dhr_op04_result_bodyfree"), Mapping) else {}
    branch_flags = {
        "mrb_op06_dhr_op04_confirmed_bodyfree_stopped": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF,
        "mrb_op06_dhr_op04_not_confirmed_retry_or_start_required_stopped": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF,
        "mrb_op06_dhr_op04_waiting_external_claim_stopped": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF,
        "mrb_op06_dhr_op04_invalid_repair_required_stopped": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF,
        "mrb_op06_waiting_before_dhr_op04_call_stopped": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_WAITING_FOR_DRI_OR_DHR_OP03_MATERIAL_REF,
        "mrb_op06_repair_required_before_dhr_op04_call_stopped": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_REPAIR_REQUIRED_BEFORE_DHR_OP04_CALL_REF,
        "mrb_op06_bodyfree_leak_promotion_or_autorun_blocked": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
        "mrb_op06_manual_hold_unresolved_no_promotion": branch == P7_R54_AHR_POST_DRI_MRB_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
    }
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_material_present": op05_present,
        "op05_contract_valid": op05_valid,
        "op05_schema_version": _clean_ref(op05.get("schema_version"), default="op05_schema_missing", max_length=260),
        "op05_operation_step_ref": _clean_ref(op05.get("operation_step_ref"), default="op05_operation_step_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id"), default="op05_material_missing", max_length=260),
        "op05_status_ref": op05_status,
        "op05_next_required_step": _clean_ref(op05.get("next_required_step"), default="op05_next_required_step_missing", max_length=260),
        "op05_dhr_op04_result_captured": bool(op05.get("dhr_op04_result_captured") is True),
        "op05_dhr_op04_called_by_manual_reintake_boundary": bool(op05.get("dhr_op04_called_by_manual_reintake_boundary") is True),
        "op05_dhr_op04_called_by_dri": bool(op05.get("dhr_op04_called_by_dri") is True),
        "op05_dhr_op04_called_by_mrb": bool(op05.get("dhr_op04_called_by_mrb") is True),
        "op05_dhr_op04_called_here": bool(op05.get("dhr_op04_called_here") is True),
        "dhr_op04_result_captured": dhr_result_captured,
        "dhr_op04_contract_valid": bool(op05.get("dhr_op04_contract_valid") is True),
        "dhr_op04_result_bodyfree": result_bodyfree,
        "dhr_op04_status_ref": dhr_status,
        "dhr_op04_result_status_ref": _clean_ref(op05.get("dhr_op04_result_status_ref"), default=dhr_status, max_length=260),
        "dhr_op04_next_required_step_ref": _clean_ref(op05.get("dhr_op04_next_required_step_ref"), default="dhr_op04_next_required_step_missing", max_length=260),
        "actual_source_claim_confirmed_for_downstream_handoff": bool(branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF and op05.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
        "actual_source_claim_bodyfree": bool(branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF and op05.get("actual_source_claim_bodyfree") is True),
        "actual_source_claim_origin_ref": _clean_ref(op05.get("actual_source_claim_origin_ref"), default="actual_source_claim_origin_missing_or_not_confirmed", max_length=260),
        "mrb_op06_status_ref": branch,
        "dhr_op04_result_classifier_status_ref": branch,
        "mrb_branch_ref": branch,
        "mrb_allowed_branch_refs": list(P7_R54_AHR_POST_DRI_MRB_OP06_ALLOWED_BRANCH_REFS),
        "mrb_allowed_branch_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP06_ALLOWED_BRANCH_REFS),
        "exactly_one_mrb_result_branch": sum(1 for value in branch_flags.values() if value is True) == 1,
        **branch_flags,
        "mrb_op06_reason_refs": _dedupe_clean_refs(reasons, max_length=300),
        "mrb_op06_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=300)),
        "mrb_op06_blocker_refs": _dedupe_clean_refs(blockers, max_length=300),
        "mrb_op06_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=300)),
        "mrb_op06_result_is_dhr_op04_only": True,
        "mrb_op06_does_not_call_dhr_op04_again": True,
        "mrb_op06_does_not_call_dhr_op05": True,
        "mrb_op06_does_not_call_dhr_op06": True,
        "mrb_op06_does_not_execute_dmd_r52_or_release": True,
        "mrb_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op06_does_not_materialize_p8_question_spec": True,
        "dhr_op05_auto_call_allowed": False,
        "dhr_op06_auto_call_allowed": False,
        "downstream_auto_execution_allowed": False,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "mrb_next_required_step": next_step,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP06")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DRI_MRB_OP06_SCHEMA_VERSION or data.get("operation_step_ref") != P7_R54_AHR_POST_DRI_MRB_OP06_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 identity changed")
    if data.get("phase") != P7_R54_AHR_POST_DRI_MRB_PHASE or data.get("step") != P7_R54_AHR_POST_DRI_MRB_STEP or data.get("scope") != P7_R54_AHR_POST_DRI_MRB_SCOPE:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 base identity changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE or data.get("git_connection_required") is not False or data.get("git_checked") is not False or data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 source/body-free boundary changed")
    _assert_public_contract_false(data, source="P7-R54-AHR-PostDRI-MRB-OP06")
    _assert_false_mapping(data, field="mrb_no_touch_contract", source="P7-R54-AHR-PostDRI-MRB-OP06")
    _assert_false_mapping(data, field="body_free_markers", source="P7-R54-AHR-PostDRI-MRB-OP06")
    allowed_true_false_flags = {"dhr_op04_called_by_mrb", "actual_source_claim_confirmed_for_downstream_handoff"}
    for key in P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        if key not in allowed_true_false_flags and data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP06 downstream false flag promoted: {key}")
    if data.get("dhr_op04_called_here") is not False:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 must not call DHR-OP04 again")
    for key in ("dhr_op05_auto_call_allowed", "dhr_op06_auto_call_allowed", "downstream_auto_execution_allowed", "op05_dhr_op04_called_by_dri"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP06 false downstream/dri-call flag changed: {key}")
    for key in ("mrb_op06_result_is_dhr_op04_only", "mrb_op06_does_not_call_dhr_op04_again", "mrb_op06_does_not_call_dhr_op05", "mrb_op06_does_not_call_dhr_op06", "mrb_op06_does_not_execute_dmd_r52_or_release", "mrb_op06_does_not_start_p5_p6_p8_p7_or_release", "mrb_op06_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP06 required true boundary changed: {key}")
    if tuple(data.get("mrb_allowed_branch_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP06_ALLOWED_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 allowed branches changed")
    if data.get("mrb_allowed_branch_ref_count") != len(P7_R54_AHR_POST_DRI_MRB_OP06_ALLOWED_BRANCH_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 allowed branch count changed")
    flags = [
        data.get("mrb_op06_dhr_op04_confirmed_bodyfree_stopped") is True,
        data.get("mrb_op06_dhr_op04_not_confirmed_retry_or_start_required_stopped") is True,
        data.get("mrb_op06_dhr_op04_waiting_external_claim_stopped") is True,
        data.get("mrb_op06_dhr_op04_invalid_repair_required_stopped") is True,
        data.get("mrb_op06_waiting_before_dhr_op04_call_stopped") is True,
        data.get("mrb_op06_repair_required_before_dhr_op04_call_stopped") is True,
        data.get("mrb_op06_bodyfree_leak_promotion_or_autorun_blocked") is True,
        data.get("mrb_op06_manual_hold_unresolved_no_promotion") is True,
    ]
    if sum(flags) != 1 or data.get("exactly_one_mrb_result_branch") is not True or data.get("mrb_branch_ref") not in P7_R54_AHR_POST_DRI_MRB_OP06_ALLOWED_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 exactly one branch must be selected")
    if data.get("mrb_op06_status_ref") != data.get("mrb_branch_ref") or data.get("dhr_op04_result_classifier_status_ref") != data.get("mrb_branch_ref"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 branch aliases changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP06_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 implemented/not-yet steps changed")
    for field, count_field in (("mrb_op06_reason_refs", "mrb_op06_reason_ref_count"), ("mrb_op06_blocker_refs", "mrb_op06_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP06 {count_field} changed")
    branch = data.get("mrb_branch_ref")
    if branch in P7_R54_AHR_POST_DRI_MRB_OP06_CALLED_RESULT_BRANCH_REFS:
        if data.get("op05_contract_valid") is not True or data.get("op05_dhr_op04_called_by_manual_reintake_boundary") is not True or data.get("op05_dhr_op04_called_by_dri") is not False or data.get("dhr_op04_result_captured") is not True or not data.get("dhr_op04_result_bodyfree"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 called result branch source changed")
        if data.get("mrb_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 called result branch cannot carry blockers")
    else:
        if data.get("dhr_op04_result_captured") is not False or data.get("dhr_op04_result_bodyfree") != {}:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 pre-call branch must not carry DHR-OP04 result bodyfree")
        if not data.get("mrb_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 pre-call branch must carry blockers")
    if branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF:
        if data.get("dhr_op04_status_ref") != dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF or data.get("actual_source_claim_confirmed_for_downstream_handoff") is not True or data.get("mrb_next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_CONFIRMED_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 confirmed mapping changed")
    elif branch in P7_R54_AHR_POST_DRI_MRB_OP06_CALLED_RESULT_BRANCH_REFS:
        if data.get("actual_source_claim_confirmed_for_downstream_handoff") is not False:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 non-confirmed result branch cannot confirm source claim")
    if branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF and data.get("mrb_next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_REVIEW_DHR_OP04_NOT_CONFIRMED_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 not-confirmed mapping changed")
    if branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF and data.get("mrb_next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_EXTERNAL_CLAIM_AFTER_DHR_OP04_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 waiting mapping changed")
    if branch == P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF and data.get("mrb_next_required_step") != P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_REPAIR_AFTER_DHR_OP04_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 invalid mapping changed")
    if data.get("next_required_step") != data.get("mrb_next_required_step"):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP06 next step alias changed")
    return True


def _normalize_changed_file_ref(value: Any) -> str:
    text = str(value).strip().replace("\\", "/")
    if text.startswith("mashos-api/ai/"):
        text = text[len("mashos-api/ai/"):]
    if text.startswith("./"):
        text = text[2:]
    return _clean_ref(text, default="changed_file_ref_missing", max_length=320)


def _blocked_change_refs(changed_file_refs: Sequence[str]) -> list[str]:
    blocked: list[str] = []
    for ref in changed_file_refs:
        lowered = ref.lower()
        for token in P7_R54_AHR_POST_DRI_MRB_OP07_BLOCKED_CHANGE_TOKEN_REFS:
            token_lower = token.lower()
            if token_lower in lowered:
                blocked.append(f"{ref}::{token}")
                break
    return _dedupe_clean_refs(blocked, max_length=420)


def _missing_required_refs(provided_refs: Sequence[str], required_refs: Sequence[str]) -> list[str]:
    provided = set(provided_refs)
    return [ref for ref in required_refs if ref not in provided]


def build_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard(
    *,
    changed_file_refs: Sequence[Any] | None = None,
    target_test_refs: Sequence[Any] | None = None,
    selected_regression_refs: Sequence[Any] | None = None,
    compileall_refs: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Guard that OP00〜OP07 touched only selected MRB helper/tests and recorded validation refs."""

    session_id = _safe_review_session_id(review_session_id)
    changed = _dedupe_clean_refs([_normalize_changed_file_ref(ref) for ref in (changed_file_refs or [])], max_length=320)
    target_tests = _dedupe_clean_refs([_normalize_changed_file_ref(ref) for ref in (target_test_refs or [])], max_length=320)
    selected_regressions = _dedupe_clean_refs([_normalize_changed_file_ref(ref) for ref in (selected_regression_refs or [])], max_length=320)
    compileall = _dedupe_clean_refs([_normalize_changed_file_ref(ref) for ref in (compileall_refs or [])], max_length=320)
    unexpected = [ref for ref in changed if ref not in P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_CHANGED_FILE_REFS]
    blocked_tokens = _blocked_change_refs(changed)
    missing_targets = _missing_required_refs(target_tests, P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS)
    missing_regressions = _missing_required_refs(selected_regressions, P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS)
    missing_compileall = _missing_required_refs(compileall, P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS)
    blockers: list[str] = []
    reasons: list[str] = []
    if blocked_tokens:
        blockers.append("api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if unexpected:
        blockers.append("changed_file_outside_mrb_allowed_set_detected")
    if missing_targets:
        blockers.append("mrb_target_test_refs_missing")
    if missing_regressions:
        blockers.append("selected_regression_refs_missing")
    if missing_compileall:
        blockers.append("compileall_refs_missing")
    if blocked_tokens or unexpected:
        status = P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_BLOCKED_NO_TOUCH_CHANGE_REF
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_BLOCKED_DRI_INTAKE_REF
        reasons.append("no_touch_guard_blocked_unapproved_surface_or_file_change")
    elif missing_targets or missing_regressions or missing_compileall:
        status = P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_WAITING_FOR_VALIDATION_REFS_REF
        next_step = P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_WAIT_FOR_DRI_READY_MATERIAL_REF
        reasons.append("selected_target_regression_or_compileall_refs_not_fully_recorded")
    else:
        status = P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_READY_FOR_OP08_REF
        next_step = P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF
        reasons.append("no_touch_allowed_files_selected_regression_and_compileall_refs_recorded")
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "changed_file_refs": changed,
        "changed_file_ref_count": len(changed),
        "allowed_changed_file_refs": list(P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_CHANGED_FILE_REFS),
        "allowed_changed_file_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_CHANGED_FILE_REFS),
        "changed_files_within_allowed_refs": not unexpected,
        "unexpected_changed_file_refs": unexpected,
        "unexpected_changed_file_ref_count": len(unexpected),
        "blocked_change_token_refs": list(P7_R54_AHR_POST_DRI_MRB_OP07_BLOCKED_CHANGE_TOKEN_REFS),
        "blocked_change_token_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP07_BLOCKED_CHANGE_TOKEN_REFS),
        "blocked_no_touch_change_refs": blocked_tokens,
        "blocked_no_touch_change_ref_count": len(blocked_tokens),
        "api_db_rn_runtime_response_key_or_p8_question_touch_blocked": bool(blocked_tokens or unexpected),
        "target_test_refs": target_tests,
        "target_test_ref_count": len(target_tests),
        "required_target_test_refs": list(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS),
        "required_target_test_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS),
        "target_tests_recorded": not missing_targets,
        "missing_target_test_refs": missing_targets,
        "missing_target_test_ref_count": len(missing_targets),
        "selected_regression_refs": selected_regressions,
        "selected_regression_ref_count": len(selected_regressions),
        "required_selected_regression_refs": list(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS),
        "required_selected_regression_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS),
        "selected_regression_recorded": not missing_regressions,
        "missing_selected_regression_refs": missing_regressions,
        "missing_selected_regression_ref_count": len(missing_regressions),
        "compileall_refs": compileall,
        "compileall_ref_count": len(compileall),
        "required_compileall_refs": list(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS),
        "required_compileall_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS),
        "compileall_recorded": not missing_compileall,
        "missing_compileall_refs": missing_compileall,
        "missing_compileall_ref_count": len(missing_compileall),
        "mrb_op07_status_ref": status,
        "no_touch_selected_regression_guard_status_ref": status,
        "mrb_op07_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_STATUS_REFS),
        "mrb_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_STATUS_REFS),
        "mrb_op07_ready_for_mrb_op08": status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_READY_FOR_OP08_REF,
        "mrb_op07_waiting_for_validation_refs": status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_WAITING_FOR_VALIDATION_REFS_REF,
        "mrb_op07_repair_required": status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_REPAIR_REQUIRED_REF,
        "mrb_op07_blocked_no_touch_change": status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_BLOCKED_NO_TOUCH_CHANGE_REF,
        "mrb_op07_reason_refs": _dedupe_clean_refs(reasons, max_length=300),
        "mrb_op07_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=300)),
        "mrb_op07_blocker_refs": _dedupe_clean_refs(blockers, max_length=300),
        "mrb_op07_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=300)),
        "mrb_op07_does_not_call_dhr_op04": True,
        "mrb_op07_does_not_call_dhr_op05": True,
        "mrb_op07_does_not_execute_dmd_r52_or_release": True,
        "mrb_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "mrb_op07_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP07")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DRI_MRB_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DRI_MRB_OP07_STEP_REF, source="P7-R54-AHR-PostDRI-MRB-OP07")
    for field, count_field in (
        ("changed_file_refs", "changed_file_ref_count"),
        ("allowed_changed_file_refs", "allowed_changed_file_ref_count"),
        ("unexpected_changed_file_refs", "unexpected_changed_file_ref_count"),
        ("blocked_change_token_refs", "blocked_change_token_ref_count"),
        ("blocked_no_touch_change_refs", "blocked_no_touch_change_ref_count"),
        ("target_test_refs", "target_test_ref_count"),
        ("required_target_test_refs", "required_target_test_ref_count"),
        ("missing_target_test_refs", "missing_target_test_ref_count"),
        ("selected_regression_refs", "selected_regression_ref_count"),
        ("required_selected_regression_refs", "required_selected_regression_ref_count"),
        ("missing_selected_regression_refs", "missing_selected_regression_ref_count"),
        ("compileall_refs", "compileall_ref_count"),
        ("required_compileall_refs", "required_compileall_ref_count"),
        ("missing_compileall_refs", "missing_compileall_ref_count"),
        ("mrb_op07_allowed_status_refs", "mrb_op07_allowed_status_ref_count"),
        ("mrb_op07_reason_refs", "mrb_op07_reason_ref_count"),
        ("mrb_op07_blocker_refs", "mrb_op07_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP07 {count_field} changed")
    if tuple(data.get("allowed_changed_file_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_CHANGED_FILE_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 allowed changed file refs changed")
    if tuple(data.get("required_target_test_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_TARGET_TEST_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 required target refs changed")
    if tuple(data.get("required_selected_regression_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_SELECTED_REGRESSION_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 required selected regression refs changed")
    if tuple(data.get("required_compileall_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP07_REQUIRED_COMPILEALL_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 required compileall refs changed")
    if tuple(data.get("mrb_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 allowed statuses changed")
    status = data.get("mrb_op07_status_ref")
    flags = [
        data.get("mrb_op07_ready_for_mrb_op08") is True,
        data.get("mrb_op07_waiting_for_validation_refs") is True,
        data.get("mrb_op07_repair_required") is True,
        data.get("mrb_op07_blocked_no_touch_change") is True,
    ]
    if status not in P7_R54_AHR_POST_DRI_MRB_OP07_ALLOWED_STATUS_REFS or sum(flags) != 1 or data.get("no_touch_selected_regression_guard_status_ref") != status:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 exactly one status branch must be selected")
    for key in ("mrb_op07_does_not_call_dhr_op04", "mrb_op07_does_not_call_dhr_op05", "mrb_op07_does_not_execute_dmd_r52_or_release", "mrb_op07_does_not_start_p5_p6_p8_p7_or_release", "mrb_op07_does_not_change_api_db_rn_runtime_response_key", "mrb_op07_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP07 required true boundary changed: {key}")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP07_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 implemented/not-yet steps changed")
    if status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_READY_FOR_OP08_REF:
        if data.get("changed_files_within_allowed_refs") is not True or data.get("target_tests_recorded") is not True or data.get("selected_regression_recorded") is not True or data.get("compileall_recorded") is not True:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 ready branch validation refs incomplete")
        if data.get("unexpected_changed_file_refs") or data.get("blocked_no_touch_change_refs") or data.get("missing_target_test_refs") or data.get("missing_selected_regression_refs") or data.get("missing_compileall_refs") or data.get("mrb_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 ready next step changed")
    elif status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_BLOCKED_NO_TOUCH_CHANGE_REF:
        if data.get("api_db_rn_runtime_response_key_or_p8_question_touch_blocked") is not True or not data.get("mrb_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 blocked branch changed")
    elif status == P7_R54_AHR_POST_DRI_MRB_OP07_STATUS_WAITING_FOR_VALIDATION_REFS_REF:
        if data.get("mrb_op07_waiting_for_validation_refs") is not True or not data.get("mrb_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP07 waiting branch changed")
    return True




def _mrb_op01_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(data) is True
    except ValueError:
        return False


def _mrb_op02_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(data) is True
    except ValueError:
        return False


def _mrb_op03_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(data) is True
    except ValueError:
        return False


def _mrb_op04_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract(data) is True
    except ValueError:
        return False


def _mrb_op05_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract(data) is True
    except ValueError:
        return False


def _mrb_op06_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary_contract(data) is True
    except ValueError:
        return False


def _mrb_op07_contract_valid_for_op08(data: Mapping[str, Any] | None) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_contract(data) is True
    except ValueError:
        return False


def _bodyfree_scan_triplets(value: Any, *, path: str) -> tuple[list[str], list[str], list[str]]:
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(value, path=path), max_length=420)
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(value, path=path), max_length=420)
    promotion = _dedupe_clean_refs(_scan_promotion_claim_refs(value, path=path), max_length=420)
    return forbidden, body_like, promotion


def build_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure(
    *,
    mrb_op01_dri_result_memo_op10_branch_intake: Mapping[str, Any] | None = None,
    mrb_op02_dri_op09_adapter_candidate_extraction_and_scan: Mapping[str, Any] | None = None,
    mrb_op03_dhr_op03_ready_material_intake: Mapping[str, Any] | None = None,
    mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope: Mapping[str, Any] | None = None,
    mrb_op05_explicit_manual_dhr_op04_call_and_result_capture: Mapping[str, Any] | None = None,
    mrb_op06_dhr_op04_result_classifier_stop_boundary: Mapping[str, Any] | None = None,
    mrb_op07_no_touch_selected_regression_guard: Mapping[str, Any] | None = None,
    validation_summary_bodyfree: Mapping[str, Any] | None = None,
    result_memo_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Close MRB-OP00〜OP07 as a body-free result memo and stop."""

    op01 = mrb_op01_dri_result_memo_op10_branch_intake if isinstance(mrb_op01_dri_result_memo_op10_branch_intake, Mapping) else {}
    op02 = mrb_op02_dri_op09_adapter_candidate_extraction_and_scan if isinstance(mrb_op02_dri_op09_adapter_candidate_extraction_and_scan, Mapping) else {}
    op03 = mrb_op03_dhr_op03_ready_material_intake if isinstance(mrb_op03_dhr_op03_ready_material_intake, Mapping) else {}
    op04 = mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope if isinstance(mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope, Mapping) else {}
    op05 = mrb_op05_explicit_manual_dhr_op04_call_and_result_capture if isinstance(mrb_op05_explicit_manual_dhr_op04_call_and_result_capture, Mapping) else {}
    op06 = mrb_op06_dhr_op04_result_classifier_stop_boundary if isinstance(mrb_op06_dhr_op04_result_classifier_stop_boundary, Mapping) else {}
    op07 = mrb_op07_no_touch_selected_regression_guard if isinstance(mrb_op07_no_touch_selected_regression_guard, Mapping) else {}
    session_id = _safe_review_session_id(
        review_session_id
        if review_session_id is not None
        else op06.get("review_session_id") or op05.get("review_session_id") or op04.get("review_session_id") or op01.get("review_session_id")
    )

    op01_valid = _mrb_op01_contract_valid_for_op08(mrb_op01_dri_result_memo_op10_branch_intake)
    op02_valid = _mrb_op02_contract_valid_for_op08(mrb_op02_dri_op09_adapter_candidate_extraction_and_scan)
    op03_valid = _mrb_op03_contract_valid_for_op08(mrb_op03_dhr_op03_ready_material_intake)
    op04_valid = _mrb_op04_contract_valid_for_op08(mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope)
    op05_valid = _mrb_op05_contract_valid_for_op08(mrb_op05_explicit_manual_dhr_op04_call_and_result_capture)
    op06_valid = _mrb_op06_contract_valid_for_op08(mrb_op06_dhr_op04_result_classifier_stop_boundary)
    op07_valid = _mrb_op07_contract_valid_for_op08(mrb_op07_no_touch_selected_regression_guard)

    validation_summary_present = isinstance(validation_summary_bodyfree, Mapping)
    result_memo_present = isinstance(result_memo_bodyfree, Mapping)
    validation_forbidden, validation_body_like, validation_promotion = _bodyfree_scan_triplets(validation_summary_bodyfree or {}, path="mrb_op08.validation_summary")
    memo_forbidden, memo_body_like, memo_promotion = _bodyfree_scan_triplets(result_memo_bodyfree or {}, path="mrb_op08.result_memo")
    validation_accepted = bool(validation_summary_present and not validation_forbidden and not validation_body_like and not validation_promotion)
    memo_accepted = bool(result_memo_present and not memo_forbidden and not memo_body_like and not memo_promotion)

    blockers: list[str] = []
    reasons: list[str] = []
    if validation_forbidden or validation_body_like or validation_promotion or memo_forbidden or memo_body_like or memo_promotion:
        status = P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        next_step = P7_R54_AHR_POST_DRI_MRB_OP08_NEXT_STEP_BLOCKED_REF
        reasons.append("mrb_op08_bodyfree_result_memo_or_validation_scan_blocked")
        if validation_forbidden:
            blockers.append("mrb_op08_validation_summary_forbidden_payload_key_detected")
        if validation_body_like:
            blockers.append("mrb_op08_validation_summary_body_like_value_detected")
        if validation_promotion:
            blockers.append("mrb_op08_validation_summary_promotion_claim_detected")
        if memo_forbidden:
            blockers.append("mrb_op08_result_memo_forbidden_payload_key_detected")
        if memo_body_like:
            blockers.append("mrb_op08_result_memo_body_like_value_detected")
        if memo_promotion:
            blockers.append("mrb_op08_result_memo_promotion_claim_detected")
    elif not validation_summary_present or not result_memo_present or not isinstance(mrb_op06_dhr_op04_result_classifier_stop_boundary, Mapping) or not isinstance(mrb_op07_no_touch_selected_regression_guard, Mapping):
        status = P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_WAITING_FOR_OP06_OP07_OR_VALIDATION_REF
        next_step = P7_R54_AHR_POST_DRI_MRB_OP08_NEXT_STEP_WAIT_REF
        reasons.append("mrb_op08_waiting_for_op06_op07_validation_or_result_memo_material")
        if not isinstance(mrb_op06_dhr_op04_result_classifier_stop_boundary, Mapping):
            blockers.append("mrb_op06_result_classifier_missing")
        if not isinstance(mrb_op07_no_touch_selected_regression_guard, Mapping):
            blockers.append("mrb_op07_no_touch_guard_missing")
        if not validation_summary_present:
            blockers.append("validation_summary_bodyfree_missing")
        if not result_memo_present:
            blockers.append("result_memo_bodyfree_missing")
    elif not op06_valid or not op07_valid or not op07.get("mrb_op07_ready_for_mrb_op08"):
        status = P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DRI_MRB_OP08_NEXT_STEP_REPAIR_REF
        reasons.append("mrb_op08_repair_required_for_op06_op07_or_no_touch_guard")
        if not op06_valid:
            blockers.append("mrb_op06_contract_invalid")
        if not op07_valid:
            blockers.append("mrb_op07_contract_invalid")
        elif op07.get("mrb_op07_ready_for_mrb_op08") is not True:
            blockers.append("mrb_op07_not_ready_for_op08")
    else:
        status = P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
        next_step = _clean_ref(op06.get("mrb_next_required_step"), default=P7_R54_AHR_POST_DRI_MRB_NEXT_STEP_MANUAL_HOLD_REF, max_length=320)
        reasons.append("mrb_op08_bodyfree_result_memo_closed_and_stopped_without_downstream_promotion")

    combined_run_status = _clean_ref((validation_summary_bodyfree or {}).get("combined_run_status_ref"), default="not_run", max_length=160)
    combined_confirmed = bool((validation_summary_bodyfree or {}).get("combined_mrb_dri_dhr_green_confirmed") is True and combined_run_status == "passed")
    full_backend_confirmed = bool((validation_summary_bodyfree or {}).get("full_backend_suite_green_confirmed") is True and (validation_summary_bodyfree or {}).get("full_backend_suite_status_ref") == "passed")
    confirmed_for_handoff = bool(op06_valid and op06.get("actual_source_claim_confirmed_for_downstream_handoff") is True)
    false_flags = _false_flags()
    false_flags.update({"actual_source_claim_confirmed_for_downstream_handoff": confirmed_for_handoff})

    status_flags = {
        "mrb_op08_closed_bodyfree_stopped": status == P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF,
        "mrb_op08_waiting_for_op06_op07_or_validation": status == P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_WAITING_FOR_OP06_OP07_OR_VALIDATION_REF,
        "mrb_op08_repair_required": status == P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_REPAIR_REQUIRED_REF,
        "mrb_op08_bodyfree_leak_promotion_or_autorun_blocked": status == P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    }
    return {
        "schema_version": P7_R54_AHR_POST_DRI_MRB_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "step": P7_R54_AHR_POST_DRI_MRB_STEP,
        "scope": P7_R54_AHR_POST_DRI_MRB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DRI_MRB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DRI_MRB_PHASE,
        "material_id": "p7_r54_ahr_post_dri_mrb_op08_bodyfree_result_memo_closure_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_material_present": isinstance(mrb_op01_dri_result_memo_op10_branch_intake, Mapping),
        "op01_contract_valid": op01_valid,
        "op01_dri_op10_branch_ref": _clean_ref(op01.get("dri_op10_branch_ref"), default="op01_dri_op10_branch_missing", max_length=320),
        "op01_dri_op12_result_memo_closure_intake_status_ref": _clean_ref(op01.get("mrb_op01_status_ref"), default="op01_status_missing", max_length=320),
        "op01_dri_op12_result_memo_bodyfree_closed": bool(op01.get("dri_op12_result_memo_bodyfree_closed") is True),
        "op02_material_present": isinstance(mrb_op02_dri_op09_adapter_candidate_extraction_and_scan, Mapping),
        "op02_contract_valid": op02_valid,
        "op02_dri_op09_candidate_input_accepted": bool(op02_valid and op02.get("mrb_op02_ready_for_mrb_op03") is True),
        "op02_dri_op09_candidate_present": bool(op02.get("adapter_candidate_present") is True),
        "op02_status_ref": _clean_ref(op02.get("mrb_op02_status_ref"), default="op02_status_missing", max_length=320),
        "op02_candidate_not_dhr_confirmed": bool(op02.get("dri_op09_candidate_is_not_dhr_actual_source_claim_confirmed") is True),
        "op03_material_present": isinstance(mrb_op03_dhr_op03_ready_material_intake, Mapping),
        "op03_contract_valid": op03_valid,
        "op03_dhr_op03_ready_material_status_ref": _clean_ref(op03.get("mrb_op03_status_ref"), default="op03_status_missing", max_length=320),
        "op03_dhr_op03_ready": bool(op03.get("dhr_op03_ready") is True),
        "op03_receipt_shape_not_actual_source_confirmation": bool(op03.get("dhr_op03_receipt_shape_is_not_actual_source_claim_confirmation") is True),
        "op04_material_present": isinstance(mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope, Mapping),
        "op04_contract_valid": op04_valid,
        "op04_manual_reintake_request_present": bool(op04.get("manual_reintake_request_present") is True),
        "op04_dhr_op04_input_envelope_ready": bool(op04.get("dhr_op04_input_envelope_ready") is True),
        "op04_dhr_op04_called_here": bool(op04.get("dhr_op04_called_here") is True),
        "op05_material_present": isinstance(mrb_op05_explicit_manual_dhr_op04_call_and_result_capture, Mapping),
        "op05_contract_valid": op05_valid,
        "op05_dhr_op04_manual_call_performed_by_mrb": bool(op05.get("dhr_op04_called_by_manual_reintake_boundary") is True),
        "op05_dhr_op04_result_captured": bool(op05.get("dhr_op04_result_captured") is True),
        "op05_status_ref": _clean_ref(op05.get("mrb_op05_status_ref"), default="op05_status_missing", max_length=320),
        "op06_material_present": isinstance(mrb_op06_dhr_op04_result_classifier_stop_boundary, Mapping),
        "op06_contract_valid": op06_valid,
        "op06_mrb_selected_branch_ref": _clean_ref(op06.get("mrb_branch_ref"), default="op06_branch_missing", max_length=320),
        "op06_mrb_next_required_step": _clean_ref(op06.get("mrb_next_required_step"), default="op06_next_required_step_missing", max_length=320),
        "op06_dhr_op04_result_captured": bool(op06.get("dhr_op04_result_captured") is True),
        "op06_dhr_op04_status_ref": _clean_ref(op06.get("dhr_op04_status_ref"), default="op06_dhr_status_missing", max_length=320),
        "op06_actual_source_claim_confirmed_for_downstream_handoff": confirmed_for_handoff,
        "op07_material_present": isinstance(mrb_op07_no_touch_selected_regression_guard, Mapping),
        "op07_contract_valid": op07_valid,
        "op07_status_ref": _clean_ref(op07.get("mrb_op07_status_ref"), default="op07_status_missing", max_length=320),
        "op07_ready_for_op08": bool(op07.get("mrb_op07_ready_for_mrb_op08") is True),
        "op07_no_touch_guard_ready": bool(op07_valid and op07.get("mrb_op07_ready_for_mrb_op08") is True),
        "op07_selected_regression_recorded": bool(op07.get("selected_regression_recorded") is True),
        "op07_compileall_recorded": bool(op07.get("compileall_recorded") is True),
        "validation_summary_bodyfree_present": validation_summary_present,
        "validation_summary_bodyfree_accepted": validation_accepted,
        "validation_summary_bodyfree_ref": dict(validation_summary_bodyfree) if validation_accepted else {},
        "validation_summary_forbidden_payload_key_path_refs": validation_forbidden,
        "validation_summary_forbidden_payload_key_path_count": len(validation_forbidden),
        "validation_summary_body_like_value_path_refs": validation_body_like,
        "validation_summary_body_like_value_path_count": len(validation_body_like),
        "validation_summary_promotion_claim_refs": validation_promotion,
        "validation_summary_promotion_claim_ref_count": len(validation_promotion),
        "validation_command_summary_refs": list(P7_R54_AHR_POST_DRI_MRB_OP08_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP08_VALIDATION_COMMAND_SUMMARY_REFS),
        "result_memo_bodyfree_present": result_memo_present,
        "result_memo_bodyfree_accepted": memo_accepted,
        "result_memo_bodyfree_ref": dict(result_memo_bodyfree) if memo_accepted else {},
        "result_memo_forbidden_payload_key_path_refs": memo_forbidden,
        "result_memo_forbidden_payload_key_path_count": len(memo_forbidden),
        "result_memo_body_like_value_path_refs": memo_body_like,
        "result_memo_body_like_value_path_count": len(memo_body_like),
        "result_memo_promotion_claim_refs": memo_promotion,
        "result_memo_promotion_claim_ref_count": len(memo_promotion),
        "combined_run_status_ref": combined_run_status,
        "full_backend_suite_green_confirmed": full_backend_confirmed,
        "combined_mrb_dri_dhr_green_confirmed": combined_confirmed,
        "combined_green_claim_not_made_when_not_passed": bool(combined_run_status != "passed" and combined_confirmed is False),
        "mrb_op08_status_ref": status,
        "bodyfree_result_memo_closure_status_ref": status,
        "mrb_op08_allowed_status_refs": list(P7_R54_AHR_POST_DRI_MRB_OP08_ALLOWED_STATUS_REFS),
        "mrb_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_DRI_MRB_OP08_ALLOWED_STATUS_REFS),
        **status_flags,
        "mrb_op08_reason_refs": _dedupe_clean_refs(reasons, max_length=320),
        "mrb_op08_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=320)),
        "mrb_op08_blocker_refs": _dedupe_clean_refs(blockers, max_length=320),
        "mrb_op08_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=320)),
        "mrb_selected_branch_ref": _clean_ref(op06.get("mrb_branch_ref"), default="op06_branch_missing", max_length=320),
        "dhr_op04_manual_call_performed_by_mrb": bool(op05.get("dhr_op04_called_by_manual_reintake_boundary") is True or op06.get("op05_dhr_op04_called_by_manual_reintake_boundary") is True),
        "dhr_op04_result_status_ref": _clean_ref(op06.get("dhr_op04_status_ref") if op06.get("dhr_op04_result_captured") is True else "not_called", default="not_called", max_length=320),
        "actual_source_claim_confirmed_for_downstream_handoff": confirmed_for_handoff,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "mrb_op08_does_not_call_dhr_op04": True,
        "mrb_op08_does_not_call_dhr_op05": True,
        "mrb_op08_does_not_call_dhr_op06": True,
        "mrb_op08_does_not_execute_dmd_r52_or_release": True,
        "mrb_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "mrb_op08_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DRI_MRB_CLAIM_BOUNDARY_REFS),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DRI_MRB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DRI_MRB_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "mrb_next_required_step": next_step,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "mrb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DRI_MRB_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDRI-MRB-OP08")
    if set(data) != set(P7_R54_AHR_POST_DRI_MRB_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DRI_MRB_OP08_SCHEMA_VERSION or data.get("operation_step_ref") != P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF or data.get("policy_section") != P7_R54_AHR_POST_DRI_MRB_OP08_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 identity changed")
    if data.get("phase") != P7_R54_AHR_POST_DRI_MRB_PHASE or data.get("step") != P7_R54_AHR_POST_DRI_MRB_STEP or data.get("scope") != P7_R54_AHR_POST_DRI_MRB_SCOPE or data.get("policy_kind") != P7_R54_AHR_POST_DRI_MRB_POLICY_KIND:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 base identity changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE or data.get("git_connection_required") is not False or data.get("git_checked") is not False or data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 source/body-free boundary changed")
    _assert_public_contract_false(data, source="P7-R54-AHR-PostDRI-MRB-OP08")
    _assert_false_mapping(data, field="mrb_no_touch_contract", source="P7-R54-AHR-PostDRI-MRB-OP08")
    _assert_false_mapping(data, field="body_free_markers", source="P7-R54-AHR-PostDRI-MRB-OP08")
    for key in P7_R54_AHR_POST_DRI_MRB_OP08_RESULT_MEMO_REQUIRED_FALSE_FIELD_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP08 downstream false flag promoted: {key}")
    status = data.get("mrb_op08_status_ref")
    flags = [
        data.get("mrb_op08_closed_bodyfree_stopped") is True,
        data.get("mrb_op08_waiting_for_op06_op07_or_validation") is True,
        data.get("mrb_op08_repair_required") is True,
        data.get("mrb_op08_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status not in P7_R54_AHR_POST_DRI_MRB_OP08_ALLOWED_STATUS_REFS or sum(flags) != 1 or data.get("bodyfree_result_memo_closure_status_ref") != status:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 exactly one status branch must be selected")
    for field, count_field in (
        ("validation_summary_forbidden_payload_key_path_refs", "validation_summary_forbidden_payload_key_path_count"),
        ("validation_summary_body_like_value_path_refs", "validation_summary_body_like_value_path_count"),
        ("validation_summary_promotion_claim_refs", "validation_summary_promotion_claim_ref_count"),
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count"),
        ("result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count"),
        ("result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count"),
        ("mrb_op08_allowed_status_refs", "mrb_op08_allowed_status_ref_count"),
        ("mrb_op08_reason_refs", "mrb_op08_reason_ref_count"),
        ("mrb_op08_blocker_refs", "mrb_op08_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP08 {count_field} changed")
    if tuple(data.get("mrb_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 allowed statuses changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_DRI_MRB_OP08_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 validation command refs changed")
    for key in ("dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "mrb_op08_does_not_call_dhr_op04", "mrb_op08_does_not_call_dhr_op05", "mrb_op08_does_not_call_dhr_op06", "mrb_op08_does_not_execute_dmd_r52_or_release", "mrb_op08_does_not_start_p5_p6_p8_p7_or_release", "mrb_op08_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDRI-MRB-OP08 required true boundary changed: {key}")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP08_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DRI_MRB_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 implemented/not-yet steps changed")
    if data.get("combined_run_status_ref") != "passed" and (data.get("combined_mrb_dri_dhr_green_confirmed") is not False or data.get("combined_green_claim_not_made_when_not_passed") is not True):
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 combined green claim boundary changed")
    if data.get("full_backend_suite_green_confirmed") is not False and (data.get("validation_summary_bodyfree_ref") or {}).get("full_backend_suite_status_ref") != "passed":
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 full backend green claim boundary changed")
    if status == P7_R54_AHR_POST_DRI_MRB_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF:
        if data.get("op06_contract_valid") is not True or data.get("op07_contract_valid") is not True or data.get("op07_ready_for_op08") is not True or data.get("validation_summary_bodyfree_accepted") is not True or data.get("result_memo_bodyfree_accepted") is not True:
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 closed branch required inputs missing")
        if data.get("mrb_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 closed branch cannot carry blockers")
        if data.get("next_required_step") != data.get("op06_mrb_next_required_step") or data.get("mrb_next_required_step") != data.get("op06_mrb_next_required_step"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 closed next step changed")
    else:
        if not data.get("mrb_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 non-closed branch must carry blockers")
    if data.get("actual_source_claim_confirmed_for_downstream_handoff") is True and data.get("mrb_selected_branch_ref") != P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 confirmed claim can only mirror confirmed DHR-OP04 branch")
    if data.get("dhr_op04_manual_call_performed_by_mrb") is True and data.get("op05_dhr_op04_manual_call_performed_by_mrb") is not True:
        raise ValueError("P7-R54-AHR-PostDRI-MRB-OP08 manual call source changed")
    return True



# Full-title aliases for adjacent R54-AHR tests/helpers.
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op00_scope_no_touch_no_promotion_refreeze = (
    build_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op00_scope_no_touch_no_promotion_refreeze_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op00_scope_no_touch_no_promotion_refreeze_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op01_dri_result_memo_op10_branch_intake = (
    build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op01_dri_result_memo_op10_branch_intake_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan = (
    build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op03_dhr_op03_ready_material_intake = (
    build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op03_dhr_op03_ready_material_intake_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract
)

build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_bodyfree_request = (
    build_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_bodyfree_request_contract = (
    assert_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_manual_reintake_request_bodyfree = (
    build_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_manual_reintake_request_bodyfree_contract = (
    assert_p7_r54_ahr_post_dri_mrb_manual_reintake_request_bodyfree_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope = (
    build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_manual_reintake_request_and_input_envelope = (
    build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op04_manual_reintake_request_and_input_envelope_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture = (
    build_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op05_explicit_manual_dhr_op04_call_and_result_capture_contract
)


# Compatibility aliases for MRB-OP04/OP05 design spelling used by target tests.
build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_input_envelope = (
    build_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope
)
assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_input_envelope_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op04_manual_reintake_request_and_dhr_op04_input_envelope_contract
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF: Final = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_CONFIRMED_BODYFREE_STOPPED_REF
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF: Final = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_NOT_CONFIRMED_RETRY_OR_START_REQUIRED_STOPPED_REF
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF: Final = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_WAITING_EXTERNAL_CLAIM_STOPPED_REF
)
P7_R54_AHR_POST_DRI_MRB_OP05_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF: Final = (
    P7_R54_AHR_POST_DRI_MRB_STATUS_DHR_OP04_INVALID_REPAIR_REQUIRED_STOPPED_REF
)

# Full-title aliases for MRB-OP06/OP07 design spelling used by target tests.
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_dhr_op04_result_classifier_stop_boundary = (
    build_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_dhr_op04_result_classifier_stop_boundary_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op06_dhr_op04_result_classifier_stop_boundary_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op07_no_touch_selected_regression_guard = (
    build_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op07_no_touch_selected_regression_guard_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op07_no_touch_selected_regression_guard_contract
)
build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_bodyfree_result_memo_closure = (
    build_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure
)
assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_bodyfree_result_memo_closure_contract = (
    assert_p7_r54_ahr_post_dri_mrb_op08_result_memo_tests_selected_regression_closure_contract
)
