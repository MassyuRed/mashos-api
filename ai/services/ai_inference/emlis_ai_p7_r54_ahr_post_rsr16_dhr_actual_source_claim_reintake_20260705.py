# -*- coding: utf-8 -*-
"""Post-RSR16 DHR actual source claim re-intake helpers for DRI-OP00〜OP12.

DRI is intentionally a body-free Post-RSR16 boundary.  It does not run actual
local-only human review, create receipts or rows, execute disposal/purge, call
DHR-OP04, execute DHR re-intake, run DMD/R52, start P5/P6/P8, complete P7, or
allow release.

* DRI-OP00 refreezes the Post-RSR16 scope, no-touch boundary, and no-promotion
  boundary before any RSR result memo intake.
* DRI-OP01 intakes the RSR-OP16 result memo as body-free material.  It treats
  RSR-OP16 closure only as result memo/test/selected-regression closure, never
  as actual review completion, DHR actual source claim confirmation, P8 start,
  P7 completion, or release readiness.
* DRI-OP02 aligns the RSR-OP15 selected branch and next_required_step before any
  DHR re-intake material claim.
* DRI-OP03 inventories complete-candidate prerequisites and supplied body-free
  material refs without treating an OP15 candidate ref alone as actual evidence.
* DRI-OP04 revalidates a supplied RSR-OP10 actual operation receipt as
  body-free actual-local-only-human-review-by-person material.
* DRI-OP05 revalidates supplied RSR-OP11 sanitized review result rows and
  rating rows without creating rows, question text, DHR execution, or promotion.
* DRI-OP06 revalidates supplied RSR-OP12 question-need observation rows only as
  P7/P8 bridge material, never as P8 question text or implementation material.
* DRI-OP07 revalidates supplied RSR-OP13 disposal / purge receipt without
  executing purge, completing evidence, calling DHR, or promoting downstream.
* DRI-OP08 performs the final body-free / no-promotion / source-kind rescan
  before any adapter candidate can be emitted.
* DRI-OP09 materializes only a body-free DHR-OP04 external actual source claim
  adapter candidate. It still does not call DHR-OP04 or confirm downstream.
* DRI-OP10 resolves exactly one deterministic DRI branch without executing DHR,
  DMD/R52, P8, P7 completion, or release.
* DRI-OP11 guards the selected no-touch regression boundary: helper/tests/result
  memo changes only, with no API/DB/RN/runtime/response-key/P8 surface change.
* DRI-OP12 closes the DRI result memo / target tests / selected regression
  record without calling DHR-OP04, executing DHR re-intake, starting P8,
  completing P7, or allowing release.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr


P7_R54_AHR_POST_RSR16_DRI_PHASE: Final = "P7"
P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_RSR16_DRI_STEP: Final = (
    "R54-AHR-PostRSR16_DHRActualSourceClaimReintake_20260705"
)
P7_R54_AHR_POST_RSR16_DRI_SCOPE: Final = (
    "p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake"
)
P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND: Final = (
    "r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_bodyfree_boundary"
)
P7_R54_AHR_POST_RSR16_DRI_DEFAULT_REVIEW_SESSION_ID: Final = (
    rsr.P7_R54_AHR_POST_DHR09_RSR_DEFAULT_REVIEW_SESSION_ID
)

P7_R54_AHR_POST_RSR16_DRI_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op01_rsr_op16_result_memo_intake.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op02_rsr_op15_branch_next_step_alignment.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op03_complete_candidate_prerequisites_supplied_material_inventory.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op04_actual_operation_receipt_revalidation.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op05_sanitized_review_result_rows_rating_rows_revalidation.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op06_question_need_observation_rows_bridge_only_revalidation.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op07_disposal_purge_receipt_revalidation.bodyfree.v1"
)

P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF: Final = (
    "DRI-OP00_scope_no_touch_no_promotion_refreeze_after_RSR_OP16"
)
P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF: Final = (
    "DRI-OP01_RSR_OP16_result_memo_intake"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF: Final = (
    "DRI-OP02_RSR_OP15_branch_next_step_alignment"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF: Final = (
    "DRI-OP03_complete_candidate_prerequisites_supplied_material_inventory"
)
P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF: Final = (
    "DRI-OP04_actual_operation_receipt_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF: Final = (
    "DRI-OP05_sanitized_review_result_rows_rating_rows_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF: Final = (
    "DRI-OP06_question_need_observation_rows_bridge_only_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF: Final = (
    "DRI-OP07_disposal_purge_receipt_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF: Final = (
    "DRI-OP08_final_bodyfree_no_promotion_source_kind_rescan"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF: Final = (
    "DRI-OP09_DHR_OP04_external_actual_source_claim_adapter_candidate"
)
P7_R54_AHR_POST_RSR16_DRI_OP10_STEP_REF: Final = (
    "DRI-OP10_deterministic_branch_resolver"
)
P7_R54_AHR_POST_RSR16_DRI_OP11_STEP_REF: Final = (
    "DRI-OP11_no_touch_selected_regression_guard"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF: Final = (
    "DRI-OP12_result_memo_tests_selected_regression_closure"
)
P7_R54_AHR_POST_RSR16_DRI_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP10_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP11_STEP_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF,
)
P7_R54_AHR_POST_RSR16_DRI_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF,
)
P7_R54_AHR_POST_RSR16_DRI_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[1:]
)
P7_R54_AHR_POST_RSR16_DRI_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:2]
)
P7_R54_AHR_POST_RSR16_DRI_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[2:]
)
P7_R54_AHR_POST_RSR16_DRI_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:3]
)
P7_R54_AHR_POST_RSR16_DRI_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[3:]
)
P7_R54_AHR_POST_RSR16_DRI_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:4]
)
P7_R54_AHR_POST_RSR16_DRI_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[4:]
)
P7_R54_AHR_POST_RSR16_DRI_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:5]
)
P7_R54_AHR_POST_RSR16_DRI_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[5:]
)
P7_R54_AHR_POST_RSR16_DRI_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:6]
)
P7_R54_AHR_POST_RSR16_DRI_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[6:]
)
P7_R54_AHR_POST_RSR16_DRI_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:7]
)
P7_R54_AHR_POST_RSR16_DRI_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[7:]
)
P7_R54_AHR_POST_RSR16_DRI_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:8]
)
P7_R54_AHR_POST_RSR16_DRI_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[8:]
)

P7_R54_AHR_POST_RSR16_DRI_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-RSR16 DHR Actual Source Claim Re-intake Boundary"
)
P7_R54_AHR_POST_RSR16_DRI_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-RSR16 DHR Actual Source Claim Re-intake Boundary"
)
P7_R54_AHR_POST_RSR16_DRI_CURRENT_EXPECTED_DEFAULT_FROM_RSR_REF: Final = (
    "RSR-OP16 closed body-free / OP15 complete candidate may return to DHR actual source claim re-intake material only"
)
P7_R54_AHR_POST_RSR16_DRI_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "provide_dri_bodyfree_actual_source_claim_adapter_material_to_dhr_op04_without_auto_execution_or_wait_repair_block"
)
P7_R54_AHR_POST_RSR16_DRI_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "actual local-only human review execution",
    "actual body-full packet generation",
    "actual operation receipt creation",
    "sanitized review result rows creation",
    "rating rows creation",
    "question need observation rows creation",
    "disposal / purge execution",
    "DHR actual source claim re-intake execution",
    "DHR-OP04 auto call",
    "DMD execution",
    "R52 actual execution",
    "P5 finalization",
    "P6 start",
    "P8 start",
    "P8 question design",
    "P8 question implementation",
    "P7 complete",
    "release decision",
)
P7_R54_AHR_POST_RSR16_DRI_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(286).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(96).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(15).zip",
    "rn_zip_ref": "Cocolon(269).zip",
    "backend_zip_ref": "mashos-api(182).zip",
}
P7_R54_AHR_POST_RSR16_DRI_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostRSR16_DHRActualSourceClaimReintake_PreDesignMemo_20260705.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostRSR16_DHRActualSourceClaimReintake_DetailedDesign_ImplementationOrder_20260705.md",
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704.py",
    "mashos-api/ai/tests/R54_AHR_PostDHR09_ActualLocalReview_RetryStartDecision_RSR_OP00_OP16_Result_20260704.md",
)
P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "rsr_op16_result_memo_closure_is_not_actual_review_execution",
    "rsr_op16_target_green_is_not_actual_review_complete",
    "rsr_op16_selected_regression_green_is_not_actual_source_claim_confirmed",
    "rsr_op15_complete_candidate_is_not_dhr_reintake_execution",
    "dri_op01_intake_is_not_dhr_op04_adapter_materialization",
    "dri_op01_intake_is_not_dhr_actual_source_claim_confirmation",
    "question_need_observation_rows_are_not_p8_question_design",
    "dhr_op04_manual_boundary_remains_required_after_dri_op01",
    "release_decision_is_not_allowed_here",
)
P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_local_only_human_review_execution",
    "actual_operation_receipt_real_creation",
    "sanitized_review_result_rows_real_creation",
    "rating_rows_real_creation",
    "question_need_observation_rows_real_creation",
    "disposal_purge_real_execution",
    "external_actual_operation_evidence_claim_adapter_candidate",
    "actual_source_claim_for_dhr_reintake",
    "dhr_op04_call",
    "dhr_actual_source_claim_reintake_execution",
    "dmd_execution",
    "r52_actual_execution",
    "p5_finalization",
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
P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "RSR-OP16 closure != actual review complete",
    "RSR-OP16 target tests green != actual evidence complete",
    "RSR-OP16 selected regression green != DHR actual source claim confirmed",
    "RSR-OP15 complete candidate != DHR re-intake execution",
    "DRI-OP00〜OP07 helper green != DHR-OP04 adapter candidate materialized",
    "DRI-OP00〜OP07 helper green != DHR actual source confirmed",
    "DRI-OP00〜OP07 helper green != P8 question design start",
    "DHR/DMD/R52/P5/P6/P8/P7/release promotion is outside DRI-OP00〜OP07",
)

P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "actual_body_full_packet_generated_here",
    "body_full_packet_generated_here",
    "body_full_packet_generation_run_here",
    "actual_local_human_review_executed_here",
    "actual_local_only_human_review_executed_here",
    "actual_human_review_run_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_purge_executed_here",
    "actual_review_evidence_complete_here",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "external_actual_operation_evidence_claim_adapter_candidate_materialized_here",
    "actual_source_claim_for_dhr_reintake_materialized_here",
    "dhr_op04_called_here",
    "dhr_op05_called_here",
    "dhr_actual_source_claim_reintake_executed_here",
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
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_RSR16_DRI_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_RSR16_DRI_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_RSR16_DRI_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_RSR16_DRI_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generated_here",
    "body_full_packet_generated_here",
    "body_full_packet_generation_run_here",
    "actual_local_human_review_executed_here",
    "actual_local_only_human_review_executed_here",
    "actual_human_review_run_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_purge_executed_here",
    "actual_review_evidence_complete_here",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "external_actual_operation_evidence_claim_adapter_candidate_materialized_here",
    "actual_source_claim_for_dhr_reintake_materialized_here",
    "dhr_op04_adapter_candidate_materialized_here",
    "dhr_op04_called_here",
    "dhr_op05_called_here",
    "dhr_actual_source_claim_reintake_executed_here",
    "dmd_execution_started_here",
    "dmd_auto_execution_allowed",
    "manual_decision_auto_executes_downstream",
    "r52_actual_execution_started_here",
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

P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF: Final = (
    "DRI_OP01_RSR_OP16_CLOSED_BODYFREE_INTAKE_READY"
)
P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF: Final = (
    "DRI_OP01_WAITING_FOR_RSR_OP16_CLOSURE"
)
P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF: Final = (
    "DRI_OP01_REPAIR_RSR_OP16_RESULT_MEMO"
)
P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF: Final = (
    "DRI_OP01_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION"
)
P7_R54_AHR_POST_RSR16_DRI_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP16_CLOSURE_REF: Final = (
    "wait_for_rsr_op16_bodyfree_result_memo_closure"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF: Final = (
    "repair_rsr_op16_result_memo_before_dri_op02"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF: Final = (
    "blocked_dri_op01_rsr_op16_body_leak_or_promotion"
)

P7_R54_AHR_POST_RSR16_DRI_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "expected_from_rsr_ref", "expected_next_required_step_ref",
    "not_stage_refs", "not_stage_ref_count", "support_material_refs", "support_material_ref_count",
    "local_received_zip_refs", "local_received_zip_ref_count", "body_free",
    "dri_op00_scope_confirmed", "dri_op00_no_touch_boundary_confirmed", "dri_op00_no_promotion_boundary_confirmed",
    "dri_op00_does_not_intake_rsr_op16_result_memo", "dri_op00_does_not_materialize_dhr_op04_adapter_candidate",
    "dri_op00_does_not_call_dhr_op04", "dri_op00_does_not_execute_dhr_reintake_dmd_or_r52",
    "dri_op00_does_not_run_actual_local_human_review", "dri_op00_does_not_create_receipts_rows_or_disposal",
    "dri_op00_does_not_start_p5_p6_p8_p7_or_release", "dri_op00_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_RSR16_DRI_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed", "op00_no_touch_boundary_confirmed",
    "op00_no_promotion_boundary_confirmed", "op00_contract_valid", "rsr_op16_result_memo_present", "rsr_op16_contract_valid",
    "rsr_op16_schema_version", "rsr_op16_operation_step_ref", "rsr_op16_material_ref", "rsr_op16_status_ref",
    "rsr_op16_result_memo_bodyfree_closed", "rsr_op16_selected_branch_ref", "rsr_op16_next_required_step",
    "rsr_op16_selected_next_required_step_after_result_memo", "rsr_op16_op15_contract_valid", "rsr_op16_op15_actual_evidence_complete_candidate",
    "rsr_op16_target_tests_passed_count", "rsr_op16_accumulated_target_passed_count", "rsr_op16_dhr_selected_regression_passed_count",
    "rsr_op16_verification_all_required_summaries_green", "rsr_op16_compileall_ok", "rsr_op16_forbidden_payload_key_path_refs",
    "rsr_op16_forbidden_payload_key_path_count", "rsr_op16_body_like_value_path_refs", "rsr_op16_body_like_value_path_count",
    "rsr_op16_promotion_claim_refs", "rsr_op16_promotion_claim_ref_count", "dri_op01_status_ref", "rsr_op16_intake_status_ref",
    "dri_op01_allowed_status_refs", "dri_op01_allowed_status_ref_count", "dri_op01_ready", "dri_op01_rsr_op16_closed_bodyfree_intake_ready",
    "dri_op01_waiting_for_rsr_op16_closure", "dri_op01_repair_required", "dri_op01_body_leak_or_promotion_blocked",
    "dri_op01_reason_refs", "dri_op01_reason_ref_count", "dri_op01_blocker_refs", "dri_op01_blocker_ref_count",
    "dri_op01_ready_for_rsr_op15_branch_alignment", "actual_review_execution_claimed_by_dri_op01",
    "actual_review_evidence_completed_by_dri_op01", "dhr_actual_source_claim_confirmed_by_dri_op01",
    "dhr_op04_adapter_candidate_materialized_by_dri_op01", "dri_op01_does_not_materialize_dhr_op04_adapter_candidate",
    "dri_op01_does_not_call_dhr_op04", "dri_op01_does_not_execute_dhr_reintake_dmd_or_r52",
    "dri_op01_does_not_run_actual_local_human_review", "dri_op01_does_not_create_receipts_rows_or_disposal",
    "dri_op01_does_not_start_p5_p6_p8_p7_or_release", "dri_op01_does_not_change_api_db_rn_runtime_response_key",
    "dri_op01_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(value, default=P7_R54_AHR_POST_RSR16_DRI_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RSR16_DRI_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RSR16_DRI_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS}


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
            if key_text in P7_R54_AHR_POST_RSR16_DRI_FORBIDDEN_PAYLOAD_KEY_REFS:
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
            if key_text in P7_R54_AHR_POST_RSR16_DRI_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _summary_passed_count(material: Mapping[str, Any], *, field: str) -> int:
    summary = material.get(field)
    if not isinstance(summary, Mapping):
        return 0
    value = summary.get("passed_count")
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _rsr_op16_contract_valid(rsr_op16: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op16, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(rsr_op16) is True
    except ValueError:
        return False


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


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_RSR16_DRI_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_RSR16_DRI_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_RSR16_DRI_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref or data.get("policy_section") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git connection flags changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must stay body-free")
    _assert_public_contract_false(data, source=source)
    _assert_false_mapping(data, field="post_rsr16_no_touch_contract", source=source)
    _assert_false_mapping(data, field="body_free_markers", source=source)
    for key in P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")
    if any(key in P7_R54_AHR_POST_RSR16_DRI_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")


def _op01_status_reason_blocker_next(
    *,
    rsr_op16: Mapping[str, Any] | None,
    rsr_op16_contract_valid: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    op00_valid: bool,
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if not op00_valid:
        blockers.append("dri_op00_contract_invalid")
    if not isinstance(rsr_op16, Mapping):
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF,
            ["rsr_op16_result_memo_missing_or_not_provided"],
            ["rsr_op16_result_memo_missing"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP16_CLOSURE_REF,
        )
    status_ref = _clean_ref(rsr_op16.get("rsr_op16_status_ref"), default="rsr_op16_status_missing", max_length=260)
    if forbidden_paths:
        blockers.append("rsr_op16_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("rsr_op16_body_like_value_detected")
    if promotion_claims:
        blockers.append("rsr_op16_promotion_claim_detected")
    if status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF:
        blockers.append("rsr_op16_status_body_leak_or_promotion_blocked")
    if forbidden_paths or body_like_paths or promotion_claims or status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF,
            ["rsr_op16_bodyfree_or_promotion_boundary_failed_before_dri_op02"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF,
        )
    if not rsr_op16_contract_valid:
        blockers.append("rsr_op16_result_memo_contract_invalid")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF,
            ["rsr_op16_result_memo_boundary_repair_required_before_dri_op02"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF,
        )
    if status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF:
        if rsr_op16.get("result_memo_bodyfree_closed") is not True:
            blockers.append("rsr_op16_closed_status_without_bodyfree_closed_flag")
            return (
                P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF,
                ["rsr_op16_closed_status_requires_bodyfree_closed_flag_repair"],
                _dedupe_clean_refs(blockers),
                P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF,
            )
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF,
            ["rsr_op16_result_memo_closed_bodyfree_intake_ready_for_dri_op02"],
            [],
            P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF,
        )
    if status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF,
            ["rsr_op16_waiting_for_op15_branch_resolution"],
            [],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP16_CLOSURE_REF,
        )
    if status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF,
            ["rsr_op16_result_memo_reported_repair_required"],
            ["rsr_op16_result_memo_repair_required"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF,
        ["rsr_op16_status_is_not_a_dri_op01_intake_target"],
        ["rsr_op16_status_unexpected_for_dri_op01"],
        P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build DRI-OP00 body-free scope / no-touch / no-promotion refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_RSR16_DRI_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_RSR16_DRI_SELECTED_DESIGN_TARGET_REF,
        "expected_from_rsr_ref": P7_R54_AHR_POST_RSR16_DRI_CURRENT_EXPECTED_DEFAULT_FROM_RSR_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_RSR16_DRI_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_RSR16_DRI_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_RSR16_DRI_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "dri_op00_scope_confirmed": True,
        "dri_op00_no_touch_boundary_confirmed": True,
        "dri_op00_no_promotion_boundary_confirmed": True,
        "dri_op00_does_not_intake_rsr_op16_result_memo": True,
        "dri_op00_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op00_does_not_call_dhr_op04": True,
        "dri_op00_does_not_execute_dhr_reintake_dmd_or_r52": True,
        "dri_op00_does_not_run_actual_local_human_review": True,
        "dri_op00_does_not_create_receipts_rows_or_disposal": True,
        "dri_op00_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DRI-OP00 scope / no-touch / no-promotion refreeze contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_RSR16_DRI_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostRSR16-DRI-OP00",
    )
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_RSR16_DRI_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP00_STEP_REF,
        source="P7-R54-AHR-PostRSR16-DRI-OP00",
    )
    for key in (
        "dri_op00_scope_confirmed",
        "dri_op00_no_touch_boundary_confirmed",
        "dri_op00_no_promotion_boundary_confirmed",
        "dri_op00_does_not_intake_rsr_op16_result_memo",
        "dri_op00_does_not_materialize_dhr_op04_adapter_candidate",
        "dri_op00_does_not_call_dhr_op04",
        "dri_op00_does_not_execute_dhr_reintake_dmd_or_r52",
        "dri_op00_does_not_run_actual_local_human_review",
        "dri_op00_does_not_create_receipts_rows_or_disposal",
        "dri_op00_does_not_start_p5_p6_p8_p7_or_release",
        "dri_op00_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP00 required true boundary changed: {key}")
    if data.get("selected_design_target_ref") != P7_R54_AHR_POST_RSR16_DRI_SELECTED_DESIGN_TARGET_REF:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 selected design target changed")
    if data.get("expected_next_required_step_ref") != P7_R54_AHR_POST_RSR16_DRI_CURRENT_EXPECTED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 expected next step changed")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP00 {count_field} changed")
    if data.get("local_received_zip_ref_count") != len(data.get("local_received_zip_refs") or {}):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 local received zip count changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP00 next step changed")
    return True


def build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    rsr_op16_result_memo: Mapping[str, Any] | None = None,
    op16_result_memo: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP01 body-free RSR-OP16 result memo intake material."""

    op16 = rsr_op16_result_memo if rsr_op16_result_memo is not None else op16_result_memo
    session_id = _safe_review_session_id(
        review_session_id if review_session_id is not None else (op16.get("review_session_id") if isinstance(op16, Mapping) else None)
    )
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16(
            review_session_id=session_id
        )
    try:
        op00_valid = assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract(op00) is True
    except ValueError:
        op00_valid = False

    op16_map = op16 if isinstance(op16, Mapping) else {}
    op16_contract_valid = _rsr_op16_contract_valid(op16)
    existing_forbidden_paths = op16_map.get("op16_forbidden_payload_key_path_refs")
    if not isinstance(existing_forbidden_paths, Sequence) or isinstance(existing_forbidden_paths, (str, bytes, bytearray)):
        existing_forbidden_paths = []
    existing_body_like_paths = op16_map.get("op16_body_like_value_path_refs")
    if not isinstance(existing_body_like_paths, Sequence) or isinstance(existing_body_like_paths, (str, bytes, bytearray)):
        existing_body_like_paths = []
    existing_promotion_claims = op16_map.get("op16_promotion_claim_refs")
    if not isinstance(existing_promotion_claims, Sequence) or isinstance(existing_promotion_claims, (str, bytes, bytearray)):
        existing_promotion_claims = []
    forbidden_paths = _dedupe_clean_refs(
        [
            *_scan_forbidden_payload_key_paths(op16_map, path="rsr_op16_result_memo"),
            *existing_forbidden_paths,
        ],
        max_length=300,
    )
    body_like_paths = _dedupe_clean_refs(
        [
            *_scan_body_like_value_paths(op16_map, path="rsr_op16_result_memo"),
            *existing_body_like_paths,
        ],
        max_length=300,
    )
    promotion_claims = _dedupe_clean_refs(
        [
            *_scan_promotion_claim_refs(op16_map, path="rsr_op16_result_memo"),
            *existing_promotion_claims,
        ],
        max_length=300,
    )
    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        rsr_op16=op16,
        rsr_op16_contract_valid=op16_contract_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        op00_valid=op00_valid,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF

    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="op00_next_required_step_missing", max_length=260),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("dri_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("dri_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("dri_op00_no_promotion_boundary_confirmed") is True),
        "op00_contract_valid": op00_valid,
        "rsr_op16_result_memo_present": isinstance(op16, Mapping),
        "rsr_op16_contract_valid": op16_contract_valid,
        "rsr_op16_schema_version": _clean_ref(op16_map.get("schema_version"), default="rsr_op16_schema_missing", max_length=260),
        "rsr_op16_operation_step_ref": _clean_ref(op16_map.get("operation_step_ref"), default="rsr_op16_operation_step_missing", max_length=260),
        "rsr_op16_material_ref": _clean_ref(op16_map.get("material_id"), default="rsr_op16_material_missing", max_length=260),
        "rsr_op16_status_ref": _clean_ref(op16_map.get("rsr_op16_status_ref"), default="rsr_op16_status_missing", max_length=260),
        "rsr_op16_result_memo_bodyfree_closed": bool(op16_map.get("result_memo_bodyfree_closed") is True),
        "rsr_op16_selected_branch_ref": _clean_ref(op16_map.get("selected_branch_ref"), default="rsr_op16_selected_branch_missing", max_length=260),
        "rsr_op16_next_required_step": _clean_ref(op16_map.get("next_required_step"), default="rsr_op16_next_required_step_missing", max_length=260),
        "rsr_op16_selected_next_required_step_after_result_memo": _clean_ref(op16_map.get("selected_next_required_step_after_result_memo"), default="rsr_op16_selected_next_step_missing", max_length=260),
        "rsr_op16_op15_contract_valid": bool(op16_map.get("op15_contract_valid") is True),
        "rsr_op16_op15_actual_evidence_complete_candidate": bool(op16_map.get("op15_actual_evidence_complete_candidate") is True),
        "rsr_op16_target_tests_passed_count": _summary_passed_count(op16_map, field="target_test_summary"),
        "rsr_op16_accumulated_target_passed_count": _summary_passed_count(op16_map, field="rsr_accumulated_target_summary"),
        "rsr_op16_dhr_selected_regression_passed_count": _summary_passed_count(op16_map, field="dhr_selected_regression_summary"),
        "rsr_op16_verification_all_required_summaries_green": bool(op16_map.get("verification_all_required_summaries_green") is True),
        "rsr_op16_compileall_ok": bool(op16_map.get("compileall_ok") is True),
        "rsr_op16_forbidden_payload_key_path_refs": forbidden_paths,
        "rsr_op16_forbidden_payload_key_path_count": len(forbidden_paths),
        "rsr_op16_body_like_value_path_refs": body_like_paths,
        "rsr_op16_body_like_value_path_count": len(body_like_paths),
        "rsr_op16_promotion_claim_refs": promotion_claims,
        "rsr_op16_promotion_claim_ref_count": len(promotion_claims),
        "dri_op01_status_ref": status_ref,
        "rsr_op16_intake_status_ref": status_ref,
        "dri_op01_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP01_ALLOWED_STATUS_REFS),
        "dri_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP01_ALLOWED_STATUS_REFS),
        "dri_op01_ready": ready,
        "dri_op01_rsr_op16_closed_bodyfree_intake_ready": ready,
        "dri_op01_waiting_for_rsr_op16_closure": waiting,
        "dri_op01_repair_required": repair,
        "dri_op01_body_leak_or_promotion_blocked": blocked,
        "dri_op01_reason_refs": reasons,
        "dri_op01_reason_ref_count": len(reasons),
        "dri_op01_blocker_refs": blockers,
        "dri_op01_blocker_ref_count": len(blockers),
        "dri_op01_ready_for_rsr_op15_branch_alignment": ready,
        "actual_review_execution_claimed_by_dri_op01": False,
        "actual_review_evidence_completed_by_dri_op01": False,
        "dhr_actual_source_claim_confirmed_by_dri_op01": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op01": False,
        "dri_op01_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op01_does_not_call_dhr_op04": True,
        "dri_op01_does_not_execute_dhr_reintake_dmd_or_r52": True,
        "dri_op01_does_not_run_actual_local_human_review": True,
        "dri_op01_does_not_create_receipts_rows_or_disposal": True,
        "dri_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op01_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DRI-OP01 body-free RSR-OP16 result memo intake contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_RSR16_DRI_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostRSR16-DRI-OP01",
    )
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_RSR16_DRI_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF,
        source="P7-R54-AHR-PostRSR16-DRI-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_RSR16_DRI_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 OP00 next step changed")
    if data.get("rsr_op16_intake_status_ref") != data.get("dri_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 RSR-OP16 intake status alias changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "dri_op01_does_not_materialize_dhr_op04_adapter_candidate",
        "dri_op01_does_not_call_dhr_op04",
        "dri_op01_does_not_execute_dhr_reintake_dmd_or_r52",
        "dri_op01_does_not_run_actual_local_human_review",
        "dri_op01_does_not_create_receipts_rows_or_disposal",
        "dri_op01_does_not_start_p5_p6_p8_p7_or_release",
        "dri_op01_does_not_change_api_db_rn_runtime_response_key",
        "dri_op01_does_not_materialize_p8_question_spec",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP01 required true boundary changed: {key}")
    for key in (
        "actual_review_execution_claimed_by_dri_op01",
        "actual_review_evidence_completed_by_dri_op01",
        "dhr_actual_source_claim_confirmed_by_dri_op01",
        "dhr_op04_adapter_candidate_materialized_by_dri_op01",
        "actual_body_full_packet_generated_here",
        "actual_local_only_human_review_executed_here",
        "actual_operation_receipt_created_here",
        "actual_rows_created_here",
        "actual_review_evidence_complete_here",
        "external_actual_operation_evidence_claim_adapter_candidate_materialized_here",
        "actual_source_claim_for_dhr_reintake_materialized_here",
        "dhr_op04_called_here",
        "dhr_op05_called_here",
        "dhr_actual_source_claim_reintake_executed_here",
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
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP01 downstream/execution flag promoted: {key}")
    for field, count_field in (
        ("rsr_op16_forbidden_payload_key_path_refs", "rsr_op16_forbidden_payload_key_path_count"),
        ("rsr_op16_body_like_value_path_refs", "rsr_op16_body_like_value_path_count"),
        ("rsr_op16_promotion_claim_refs", "rsr_op16_promotion_claim_ref_count"),
        ("dri_op01_allowed_status_refs", "dri_op01_allowed_status_ref_count"),
        ("dri_op01_reason_refs", "dri_op01_reason_ref_count"),
        ("dri_op01_blocker_refs", "dri_op01_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP01 {count_field} changed")
    if tuple(data.get("dri_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 allowed status refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 not-yet-implemented steps changed")

    status_ref = data.get("dri_op01_status_ref")
    status_flags = [
        data.get("dri_op01_rsr_op16_closed_bodyfree_intake_ready") is True,
        data.get("dri_op01_waiting_for_rsr_op16_closure") is True,
        data.get("dri_op01_repair_required") is True,
        data.get("dri_op01_body_leak_or_promotion_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_CLOSED_BODYFREE_INTAKE_READY_REF:
        if data.get("op00_contract_valid") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 ready requires valid OP00")
        if data.get("rsr_op16_contract_valid") is not True or data.get("rsr_op16_result_memo_bodyfree_closed") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 ready requires valid closed RSR-OP16")
        if data.get("rsr_op16_status_ref") != rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 ready status changed")
        if data.get("dri_op01_ready") is not True or data.get("dri_op01_ready_for_rsr_op15_branch_alignment") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 ready flags changed")
        if data.get("dri_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 ready cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_WAITING_FOR_RSR_OP16_CLOSURE_REF:
        if data.get("dri_op01_ready") is not False or data.get("dri_op01_ready_for_rsr_op15_branch_alignment") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 waiting cannot proceed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP16_CLOSURE_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF:
        if data.get("dri_op01_ready") is not False or data.get("dri_op01_repair_required") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 repair flags changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_RSR_OP16_RESULT_MEMO_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 repair next step changed")
        if not data.get("dri_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 repair must carry blockers")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF:
        if data.get("dri_op01_ready") is not False or data.get("dri_op01_body_leak_or_promotion_blocked") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 blocked flags changed")
        if not (
            data.get("rsr_op16_forbidden_payload_key_path_refs")
            or data.get("rsr_op16_body_like_value_path_refs")
            or data.get("rsr_op16_promotion_claim_refs")
            or data.get("rsr_op16_status_ref") == rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
        ):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 blocked branch requires leak/promotion refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 blocked next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP01 status ref is not allowed")
    return True




# DRI-OP02/OP03 additions: OP15 branch alignment and supplied material inventory.
P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_ALIGNED_REF: Final = (
    "DRI_OP02_RSR_OP15_DHR_REINTAKE_BRANCH_ALIGNED"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF: Final = (
    "DRI_OP02_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF: Final = (
    "DRI_OP02_REPAIR_RSR_OP15_BRANCH_NEXT_STEP_MISMATCH"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_MANUAL_HOLD_UNEXPECTED_BRANCH_REF: Final = (
    "DRI_OP02_MANUAL_HOLD_UNEXPECTED_RSR_OP15_BRANCH"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF: Final = (
    "DRI_OP02_BLOCKED_RSR_OP15_BODYFREE_LEAK_OR_PROMOTION"
)
P7_R54_AHR_POST_RSR16_DRI_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_ALIGNED_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_MANUAL_HOLD_UNEXPECTED_BRANCH_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF,
)
P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_BRANCH_REF: Final = (
    rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF
)
P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS: Final[tuple[str, ...]] = (
    rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF,
    "return_to_dhr_actual_source_claim_reintake_without_auto_execution_or_wait_repair_block_by_supplied_receipts",
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF: Final = (
    "wait_for_rsr_op15_complete_candidate_or_supplied_bodyfree_receipts"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF: Final = (
    "repair_dri_op02_rsr_op15_branch_next_step_before_dri_op03"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP15_ALIGNMENT_REF: Final = (
    "blocked_dri_op02_rsr_op15_bodyfree_leak_or_promotion"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_OP02_REF: Final = (
    "manual_hold_after_dri_op02_without_downstream_promotion"
)

P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_INVENTORY_READY_REF: Final = (
    "DRI_OP03_COMPLETE_CANDIDATE_PREREQUISITES_SUPPLIED_MATERIAL_INVENTORY_READY"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF: Final = (
    "DRI_OP03_WAIT_FOR_COMPLETE_CANDIDATE_PREREQUISITES_OR_SUPPLIED_MATERIALS"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF: Final = (
    "DRI_OP03_REPAIR_COMPLETE_CANDIDATE_PREREQUISITES_OR_SUPPLIED_MATERIALS"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF: Final = (
    "DRI_OP03_BLOCKED_COMPLETE_CANDIDATE_BODYFREE_LEAK_OR_PROMOTION"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_INVENTORY_READY_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF: Final = (
    "repair_dri_reintake_material_before_dhr_op04_adapter"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP03_INVENTORY_REF: Final = (
    "blocked_dri_bodyfree_leak_promotion_or_invalid_source_kind"
)
P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS: Final[tuple[str, ...]] = (
    "rsr_op15_branch_resolver",
    "rsr_op14_final_validation",
    "actual_operation_receipt_bodyfree_ref",
    "sanitized_review_result_rows_bodyfree_ref",
    "rating_rows_bodyfree_ref",
    "question_need_observation_rows_bodyfree_ref",
    "disposal_purge_receipt_bodyfree_ref",
)

P7_R54_AHR_POST_RSR16_DRI_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_next_required_step", "op01_contract_valid", "op01_status_ref", "op01_ready_for_rsr_op15_branch_alignment",
    "rsr_op15_branch_resolver_present", "rsr_op15_contract_valid", "rsr_op15_schema_version", "rsr_op15_operation_step_ref", "rsr_op15_material_ref",
    "rsr_op15_branch_ref", "rsr_op15_next_required_step", "rsr_op15_actual_evidence_complete_candidate", "rsr_op15_actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution",
    "rsr_op15_dhr_actual_source_claim_reintake_required_next", "rsr_op15_manual_decision_required_without_auto_execution", "rsr_op15_downstream_auto_execution_allowed", "rsr_op15_dhr_actual_source_claim_reintake_executed_here",
    "accepted_branch_ref", "accepted_next_required_step_refs", "accepted_next_required_step_ref_count", "rsr_op15_forbidden_payload_key_path_refs", "rsr_op15_forbidden_payload_key_path_count", "rsr_op15_body_like_value_path_refs", "rsr_op15_body_like_value_path_count", "rsr_op15_promotion_claim_refs", "rsr_op15_promotion_claim_ref_count",
    "dri_op02_status_ref", "rsr_op15_alignment_status_ref", "dri_op02_allowed_status_refs", "dri_op02_allowed_status_ref_count", "dri_op02_aligned", "dri_op02_wait_for_rsr_op15_complete_candidate", "dri_op02_repair_required", "dri_op02_manual_hold_unresolved_no_promotion", "dri_op02_bodyfree_leak_or_promotion_blocked", "dri_op02_ready_for_complete_candidate_prerequisite_inventory",
    "dri_op02_reason_refs", "dri_op02_reason_ref_count", "dri_op02_blocker_refs", "dri_op02_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op02", "actual_review_evidence_completed_by_dri_op02", "dhr_actual_source_claim_confirmed_by_dri_op02", "dhr_op04_adapter_candidate_materialized_by_dri_op02", "dhr_op04_called_by_dri_op02", "dhr_actual_source_claim_reintake_executed_by_dri_op02",
    "dri_op02_does_not_execute_dhr_reintake", "dri_op02_does_not_call_dhr_op04", "dri_op02_does_not_materialize_dhr_op04_adapter_candidate", "dri_op02_does_not_execute_dmd_or_r52", "dri_op02_does_not_start_p5_p6_p8_p7_or_release", "dri_op02_does_not_change_api_db_rn_runtime_response_key", "dri_op02_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_RSR16_DRI_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_next_required_step", "op02_contract_valid", "op02_status_ref", "op02_aligned",
    "rsr_op15_branch_resolver_present", "rsr_op15_contract_valid", "rsr_op15_branch_ref", "rsr_op15_next_required_step", "rsr_op15_actual_evidence_complete_candidate", "rsr_op15_candidate_ref", "rsr_op15_candidate_ref_alone_is_not_actual_evidence",
    "rsr_op14_final_validation_present", "rsr_op14_contract_valid", "rsr_op14_status_ref", "rsr_op14_final_validation_passed", "rsr_op14_actual_evidence_complete_candidate_ready_for_op15", "rsr_op14_body_leak_promotion_or_source_kind_blocked",
    "complete_candidate_prerequisite_refs", "complete_candidate_prerequisite_ref_count", "complete_candidate_prerequisite_satisfied_refs", "complete_candidate_prerequisite_satisfied_ref_count", "complete_candidate_prerequisite_missing_refs", "complete_candidate_prerequisite_missing_ref_count",
    "explicit_allow_accepted", "readiness_blocker_count_zero", "reviewer_person_confirmed", "packet_generation_receipt_accepted", "actual_operation_receipt_accepted", "sanitized_review_result_rows_accepted", "rating_rows_accepted", "question_need_observation_rows_accepted", "disposal_purge_receipt_accepted", "final_no_leak_validation_passed",
    "supplied_material_inventory_required_refs", "supplied_material_inventory_required_ref_count", "supplied_material_inventory_refs", "supplied_material_inventory_ref_count", "supplied_material_missing_refs", "supplied_material_missing_ref_count",
    "dri_op03_forbidden_payload_key_path_refs", "dri_op03_forbidden_payload_key_path_count", "dri_op03_body_like_value_path_refs", "dri_op03_body_like_value_path_count", "dri_op03_promotion_claim_refs", "dri_op03_promotion_claim_ref_count",
    "dri_op03_status_ref", "complete_candidate_inventory_status_ref", "dri_op03_allowed_status_refs", "dri_op03_allowed_status_ref_count", "dri_op03_inventory_ready", "dri_op03_wait_for_prerequisites_or_supplied_materials", "dri_op03_repair_required", "dri_op03_bodyfree_leak_or_promotion_blocked", "dri_op03_ready_for_actual_operation_receipt_revalidation",
    "dri_op03_reason_refs", "dri_op03_reason_ref_count", "dri_op03_blocker_refs", "dri_op03_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op03", "actual_review_evidence_completed_by_dri_op03", "dhr_actual_source_claim_confirmed_by_dri_op03", "dhr_op04_adapter_candidate_materialized_by_dri_op03", "dhr_op04_called_by_dri_op03", "dhr_actual_source_claim_reintake_executed_by_dri_op03",
    "dri_op03_does_not_execute_dhr_reintake", "dri_op03_does_not_call_dhr_op04", "dri_op03_does_not_materialize_dhr_op04_adapter_candidate", "dri_op03_does_not_execute_dmd_or_r52", "dri_op03_does_not_start_p5_p6_p8_p7_or_release", "dri_op03_does_not_change_api_db_rn_runtime_response_key", "dri_op03_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _safe_int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _rsr_op15_contract_valid(rsr_op15: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op15, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(rsr_op15) is True
    except ValueError:
        return False


def _rsr_op14_contract_valid(rsr_op14: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op14, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(rsr_op14) is True
    except ValueError:
        return False


def _op02_status_reason_blocker_next(
    *,
    op01_status_ref: str,
    op01_contract_valid: bool,
    op01_ready: bool,
    rsr_op15: Mapping[str, Any] | None,
    rsr_op15_contract_valid: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    reasons: list[str] = []
    if not op01_contract_valid:
        blockers.append("dri_op01_contract_invalid")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
            ["dri_op01_result_memo_intake_must_be_repaired_before_op15_alignment"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF,
        )
    if op01_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF:
        blockers.append("dri_op01_blocked_before_op15_alignment")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF,
            ["dri_op01_bodyfree_or_promotion_block_must_remain_stopped"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP15_ALIGNMENT_REF,
        )
    if op01_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP01_STATUS_REPAIR_RSR_OP16_RESULT_MEMO_REF:
        blockers.append("dri_op01_repair_required_before_op15_alignment")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
            ["repair_rsr_op16_result_memo_before_op15_alignment"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF,
        )
    if not op01_ready:
        blockers.append("dri_op01_not_ready_for_op15_alignment")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF,
            ["wait_for_rsr_op16_closed_bodyfree_before_op15_alignment"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if not isinstance(rsr_op15, Mapping):
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF,
            ["rsr_op15_branch_resolver_missing_wait_for_complete_candidate"],
            ["rsr_op15_branch_resolver_missing"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if forbidden_paths or body_like_paths or promotion_claims:
        blockers.extend("rsr_op15_forbidden_payload_key_detected" for _ in forbidden_paths[:1])
        blockers.extend("rsr_op15_body_like_value_detected" for _ in body_like_paths[:1])
        blockers.extend("rsr_op15_promotion_claim_detected" for _ in promotion_claims[:1])
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF,
            ["rsr_op15_bodyfree_or_promotion_boundary_failed_before_inventory"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP15_ALIGNMENT_REF,
        )
    branch_ref = _clean_ref(rsr_op15.get("rsr_op15_branch_ref"), default="rsr_op15_branch_missing", max_length=260)
    next_step = _clean_ref(rsr_op15.get("next_required_step"), default="rsr_op15_next_required_step_missing", max_length=260)
    if branch_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF,
            ["rsr_op15_selected_bodyfree_leak_or_source_claim_blocked_branch"],
            ["rsr_op15_bodyfree_leak_or_source_claim_blocked"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP15_ALIGNMENT_REF,
        )
    if not rsr_op15_contract_valid:
        blockers.append("rsr_op15_branch_resolver_contract_invalid")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
            ["repair_rsr_op15_branch_resolver_before_inventory"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF,
        )
    if branch_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_BRANCH_REF:
        if next_step in P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS:
            return (
                P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_ALIGNED_REF,
                ["rsr_op15_complete_candidate_branch_and_next_step_aligned_for_inventory"],
                [],
                P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF,
            )
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
            ["rsr_op15_complete_candidate_branch_next_step_mismatch"],
            ["rsr_op15_accepted_branch_next_step_mismatch"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF,
        )
    if branch_ref in (
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY_REF,
        rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF,
    ):
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF,
            ["rsr_op15_selected_branch_is_not_complete_candidate_wait_or_retry_required"],
            [],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if branch_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_STOP_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF,
            ["rsr_op15_environment_or_material_repair_required_before_dri_inventory"],
            ["rsr_op15_environment_or_material_repair_required"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_MANUAL_HOLD_UNEXPECTED_BRANCH_REF,
        ["rsr_op15_manual_hold_or_unexpected_branch_without_downstream_promotion"],
        ["rsr_op15_manual_hold_unresolved_no_promotion"],
        P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_OP02_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
    *,
    rsr_op16_result_memo_intake: Mapping[str, Any] | None = None,
    dri_op01_rsr_op16_result_memo_intake: Mapping[str, Any] | None = None,
    rsr_op15_branch_resolver: Mapping[str, Any] | None = None,
    op15_branch_resolver: Mapping[str, Any] | None = None,
    rsr_op16_result_memo: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP02 body-free OP15 branch / next_required_step alignment material."""

    op01 = rsr_op16_result_memo_intake if rsr_op16_result_memo_intake is not None else dri_op01_rsr_op16_result_memo_intake
    op15 = rsr_op15_branch_resolver if rsr_op15_branch_resolver is not None else op15_branch_resolver
    if op01 is None:
        op01 = build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake(
            rsr_op16_result_memo=rsr_op16_result_memo,
            review_session_id=review_session_id,
        )
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op15.get("review_session_id") if isinstance(op15, Mapping) else (op01.get("review_session_id") if isinstance(op01, Mapping) else None)))
    try:
        op01_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract(op01) is True
    except ValueError:
        op01_contract_valid = False
    op01_map = op01 if isinstance(op01, Mapping) else {}
    op15_map = op15 if isinstance(op15, Mapping) else {}
    op15_contract_valid = _rsr_op15_contract_valid(op15)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op15_map, path="rsr_op15_branch_resolver"), max_length=320)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op15_map, path="rsr_op15_branch_resolver"), max_length=320)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op15_map, path="rsr_op15_branch_resolver"), max_length=320)
    status_ref, reasons, blockers, next_required_step = _op02_status_reason_blocker_next(
        op01_status_ref=_clean_ref(op01_map.get("dri_op01_status_ref"), default="dri_op01_status_missing", max_length=260),
        op01_contract_valid=op01_contract_valid,
        op01_ready=bool(op01_map.get("dri_op01_ready_for_rsr_op15_branch_alignment") is True),
        rsr_op15=op15,
        rsr_op15_contract_valid=op15_contract_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    aligned = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_ALIGNED_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF
    manual_hold = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_MANUAL_HOLD_UNEXPECTED_BRANCH_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01_map.get("schema_version"), default="op01_schema_missing", max_length=260),
        "op01_material_ref": _clean_ref(op01_map.get("material_id"), default="op01_material_missing", max_length=260),
        "op01_next_required_step": _clean_ref(op01_map.get("next_required_step"), default="op01_next_required_step_missing", max_length=260),
        "op01_contract_valid": op01_contract_valid,
        "op01_status_ref": _clean_ref(op01_map.get("dri_op01_status_ref"), default="dri_op01_status_missing", max_length=260),
        "op01_ready_for_rsr_op15_branch_alignment": bool(op01_map.get("dri_op01_ready_for_rsr_op15_branch_alignment") is True),
        "rsr_op15_branch_resolver_present": isinstance(op15, Mapping),
        "rsr_op15_contract_valid": op15_contract_valid,
        "rsr_op15_schema_version": _clean_ref(op15_map.get("schema_version"), default="rsr_op15_schema_missing", max_length=260),
        "rsr_op15_operation_step_ref": _clean_ref(op15_map.get("operation_step_ref"), default="rsr_op15_operation_step_missing", max_length=260),
        "rsr_op15_material_ref": _clean_ref(op15_map.get("material_id"), default="rsr_op15_material_missing", max_length=260),
        "rsr_op15_branch_ref": _clean_ref(op15_map.get("rsr_op15_branch_ref"), default="rsr_op15_branch_missing", max_length=260),
        "rsr_op15_next_required_step": _clean_ref(op15_map.get("next_required_step"), default="rsr_op15_next_required_step_missing", max_length=260),
        "rsr_op15_actual_evidence_complete_candidate": bool(op15_map.get("actual_evidence_complete_candidate") is True),
        "rsr_op15_actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution": bool(op15_map.get("actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution") is True),
        "rsr_op15_dhr_actual_source_claim_reintake_required_next": bool(op15_map.get("dhr_actual_source_claim_reintake_required_next") is True),
        "rsr_op15_manual_decision_required_without_auto_execution": bool(op15_map.get("manual_decision_required_without_auto_execution") is True),
        "rsr_op15_downstream_auto_execution_allowed": bool(op15_map.get("downstream_auto_execution_allowed") is True),
        "rsr_op15_dhr_actual_source_claim_reintake_executed_here": bool(op15_map.get("dhr_actual_source_claim_reintake_executed_here") is True),
        "accepted_branch_ref": P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_BRANCH_REF,
        "accepted_next_required_step_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS),
        "accepted_next_required_step_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS),
        "rsr_op15_forbidden_payload_key_path_refs": forbidden_paths,
        "rsr_op15_forbidden_payload_key_path_count": len(forbidden_paths),
        "rsr_op15_body_like_value_path_refs": body_like_paths,
        "rsr_op15_body_like_value_path_count": len(body_like_paths),
        "rsr_op15_promotion_claim_refs": promotion_claims,
        "rsr_op15_promotion_claim_ref_count": len(promotion_claims),
        "dri_op02_status_ref": status_ref,
        "rsr_op15_alignment_status_ref": status_ref,
        "dri_op02_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP02_ALLOWED_STATUS_REFS),
        "dri_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP02_ALLOWED_STATUS_REFS),
        "dri_op02_aligned": aligned,
        "dri_op02_wait_for_rsr_op15_complete_candidate": waiting,
        "dri_op02_repair_required": repair,
        "dri_op02_manual_hold_unresolved_no_promotion": manual_hold,
        "dri_op02_bodyfree_leak_or_promotion_blocked": blocked,
        "dri_op02_ready_for_complete_candidate_prerequisite_inventory": aligned,
        "dri_op02_reason_refs": _dedupe_clean_refs(reasons),
        "dri_op02_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "dri_op02_blocker_refs": _dedupe_clean_refs(blockers),
        "dri_op02_blocker_ref_count": len(_dedupe_clean_refs(blockers)),
        "actual_review_execution_claimed_by_dri_op02": False,
        "actual_review_evidence_completed_by_dri_op02": False,
        "dhr_actual_source_claim_confirmed_by_dri_op02": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op02": False,
        "dhr_op04_called_by_dri_op02": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op02": False,
        "dri_op02_does_not_execute_dhr_reintake": True,
        "dri_op02_does_not_call_dhr_op04": True,
        "dri_op02_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op02_does_not_execute_dmd_or_r52": True,
        "dri_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op02_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DRI-OP02 body-free OP15 branch / next step alignment contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP02")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP02_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP02_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP02")
    for field, count_field in (
        ("accepted_next_required_step_refs", "accepted_next_required_step_ref_count"),
        ("rsr_op15_forbidden_payload_key_path_refs", "rsr_op15_forbidden_payload_key_path_count"),
        ("rsr_op15_body_like_value_path_refs", "rsr_op15_body_like_value_path_count"),
        ("rsr_op15_promotion_claim_refs", "rsr_op15_promotion_claim_ref_count"),
        ("dri_op02_allowed_status_refs", "dri_op02_allowed_status_ref_count"),
        ("dri_op02_reason_refs", "dri_op02_reason_ref_count"),
        ("dri_op02_blocker_refs", "dri_op02_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP02 {count_field} changed")
    if tuple(data.get("dri_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 allowed status refs changed")
    if tuple(data.get("accepted_next_required_step_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 accepted next step refs changed")
    for key in (
        "dri_op02_does_not_execute_dhr_reintake", "dri_op02_does_not_call_dhr_op04", "dri_op02_does_not_materialize_dhr_op04_adapter_candidate", "dri_op02_does_not_execute_dmd_or_r52", "dri_op02_does_not_start_p5_p6_p8_p7_or_release", "dri_op02_does_not_change_api_db_rn_runtime_response_key", "dri_op02_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP02 required true boundary changed: {key}")
    for key in (
        "actual_review_execution_claimed_by_dri_op02", "actual_review_evidence_completed_by_dri_op02", "dhr_actual_source_claim_confirmed_by_dri_op02", "dhr_op04_adapter_candidate_materialized_by_dri_op02", "dhr_op04_called_by_dri_op02", "dhr_actual_source_claim_reintake_executed_by_dri_op02", "rsr_op15_downstream_auto_execution_allowed", "rsr_op15_dhr_actual_source_claim_reintake_executed_here", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP02 downstream/execution flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP02_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 implemented/not-yet steps changed")
    status_ref = data.get("dri_op02_status_ref")
    if status_ref != data.get("rsr_op15_alignment_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 status alias changed")
    status_flags = [
        data.get("dri_op02_aligned") is True,
        data.get("dri_op02_wait_for_rsr_op15_complete_candidate") is True,
        data.get("dri_op02_repair_required") is True,
        data.get("dri_op02_manual_hold_unresolved_no_promotion") is True,
        data.get("dri_op02_bodyfree_leak_or_promotion_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_ALIGNED_REF:
        if data.get("op01_contract_valid") is not True or data.get("op01_ready_for_rsr_op15_branch_alignment") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 aligned requires ready OP01")
        if data.get("rsr_op15_contract_valid") is not True or data.get("rsr_op15_branch_ref") != P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_BRANCH_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 aligned requires accepted OP15 branch")
        if data.get("rsr_op15_next_required_step") not in P7_R54_AHR_POST_RSR16_DRI_OP02_ACCEPTED_NEXT_REQUIRED_STEP_REFS:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 aligned next step mismatch")
        if data.get("dri_op02_ready_for_complete_candidate_prerequisite_inventory") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 aligned next step changed")
        if data.get("dri_op02_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 aligned branch cannot carry blockers")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_WAIT_FOR_COMPLETE_CANDIDATE_REF:
        if data.get("dri_op02_ready_for_complete_candidate_prerequisite_inventory") is not False or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 wait branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF:
        if data.get("dri_op02_repair_required") is not True or not data.get("dri_op02_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP15_ALIGNMENT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 repair branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_MANUAL_HOLD_UNEXPECTED_BRANCH_REF:
        if data.get("dri_op02_manual_hold_unresolved_no_promotion") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_OP02_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 manual hold branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF:
        if data.get("dri_op02_bodyfree_leak_or_promotion_blocked") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP15_ALIGNMENT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 blocked branch changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP02 status ref is not allowed")
    return True


def _op03_satisfied_material_refs(*, op14: Mapping[str, Any] | None, op15: Mapping[str, Any] | None, op14_valid: bool, op15_valid: bool, supplied_refs: Sequence[Any] | None) -> list[str]:
    satisfied: list[str] = []
    manual_supplied = set(_dedupe_clean_refs(list(supplied_refs or []), max_length=260))
    if op15_valid:
        satisfied.append("rsr_op15_branch_resolver")
    if op14_valid:
        satisfied.append("rsr_op14_final_validation")
    if isinstance(op14, Mapping):
        if op14.get("actual_operation_receipt_accepted") is True:
            satisfied.append("actual_operation_receipt_bodyfree_ref")
        if op14.get("sanitized_review_result_rows_accepted") is True:
            satisfied.append("sanitized_review_result_rows_bodyfree_ref")
        if op14.get("rating_rows_accepted") is True:
            satisfied.append("rating_rows_bodyfree_ref")
        if op14.get("question_need_observation_rows_accepted") is True:
            satisfied.append("question_need_observation_rows_bodyfree_ref")
        if op14.get("disposal_purge_receipt_accepted") is True or op14.get("op13_disposal_purge_receipt_accepted") is True:
            satisfied.append("disposal_purge_receipt_bodyfree_ref")
    satisfied.extend(ref for ref in P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS if ref in manual_supplied)
    return _dedupe_clean_refs(satisfied, max_length=260)


def _op03_status_reason_blocker_next(
    *,
    op02_status_ref: str,
    op02_contract_valid: bool,
    op02_aligned: bool,
    op14_present: bool,
    op14_contract_valid: bool,
    op14_blocked: bool,
    op15_contract_valid: bool,
    op15_complete_candidate: bool,
    prerequisite_missing_refs: Sequence[str],
    supplied_missing_refs: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    reasons: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or op14_blocked or op02_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF:
        if forbidden_paths:
            blockers.append("dri_op03_forbidden_payload_key_detected")
        if body_like_paths:
            blockers.append("dri_op03_body_like_value_detected")
        if promotion_claims:
            blockers.append("dri_op03_promotion_claim_detected")
        if op14_blocked:
            blockers.append("rsr_op14_body_leak_promotion_or_source_kind_blocked")
        if op02_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF:
            blockers.append("dri_op02_blocked_before_inventory")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF,
            ["bodyfree_or_promotion_boundary_failed_before_actual_operation_receipt_revalidation"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP03_INVENTORY_REF,
        )
    if not op02_contract_valid or op02_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP02_STATUS_REPAIR_BRANCH_NEXT_STEP_MISMATCH_REF:
        blockers.append("dri_op02_alignment_repair_required_before_inventory")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF,
            ["repair_op02_alignment_before_complete_candidate_inventory"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF,
        )
    if op14_present and not op14_contract_valid:
        blockers.append("rsr_op14_final_validation_contract_invalid")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF,
            ["repair_rsr_op14_final_validation_before_inventory"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF,
        )
    if not op02_aligned or not op15_contract_valid or not op15_complete_candidate:
        if not op02_aligned:
            blockers.append("dri_op02_not_aligned_for_inventory")
        if not op15_contract_valid:
            blockers.append("rsr_op15_branch_resolver_missing_or_invalid")
        if not op15_complete_candidate:
            blockers.append("rsr_op15_complete_candidate_not_selected")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF,
            ["wait_for_rsr_op15_complete_candidate_before_inventory"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if not op14_present:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF,
            ["candidate_ref_alone_is_not_actual_evidence_wait_for_rsr_op14_or_supplied_materials"],
            ["rsr_op14_final_validation_material_missing"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if prerequisite_missing_refs or supplied_missing_refs:
        blockers.extend(f"missing_prerequisite:{ref}" for ref in prerequisite_missing_refs)
        blockers.extend(f"missing_supplied_material:{ref}" for ref in supplied_missing_refs)
        reasons.append("wait_for_complete_candidate_prerequisites_or_supplied_bodyfree_materials")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF,
            reasons,
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_INVENTORY_READY_REF,
        ["complete_candidate_prerequisites_and_supplied_material_inventory_ready_for_dri_op04"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory(
    *,
    rsr_op15_branch_alignment: Mapping[str, Any] | None = None,
    dri_op02_rsr_op15_branch_next_step_alignment: Mapping[str, Any] | None = None,
    rsr_op15_branch_resolver: Mapping[str, Any] | None = None,
    op15_branch_resolver: Mapping[str, Any] | None = None,
    rsr_op14_final_validation: Mapping[str, Any] | None = None,
    op14_final_no_leak_no_promotion_source_kind_validation: Mapping[str, Any] | None = None,
    supplied_material_inventory_refs: Sequence[Any] | None = None,
    rsr_op16_result_memo: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP03 body-free complete-candidate prerequisite and supplied material inventory."""

    op15 = rsr_op15_branch_resolver if rsr_op15_branch_resolver is not None else op15_branch_resolver
    op14 = rsr_op14_final_validation if rsr_op14_final_validation is not None else op14_final_no_leak_no_promotion_source_kind_validation
    op02 = rsr_op15_branch_alignment if rsr_op15_branch_alignment is not None else dri_op02_rsr_op15_branch_next_step_alignment
    if op02 is None:
        op02 = build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment(
            rsr_op15_branch_resolver=op15,
            rsr_op16_result_memo=rsr_op16_result_memo,
            review_session_id=review_session_id,
        )
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op14.get("review_session_id") if isinstance(op14, Mapping) else (op15.get("review_session_id") if isinstance(op15, Mapping) else (op02.get("review_session_id") if isinstance(op02, Mapping) else None))))
    try:
        op02_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract(op02) is True
    except ValueError:
        op02_contract_valid = False
    op02_map = op02 if isinstance(op02, Mapping) else {}
    op15_map = op15 if isinstance(op15, Mapping) else {}
    op14_map = op14 if isinstance(op14, Mapping) else {}
    op15_contract_valid = _rsr_op15_contract_valid(op15)
    op14_contract_valid = _rsr_op14_contract_valid(op14)
    if isinstance(op14, Mapping):
        prereq_refs = list(op14.get("complete_candidate_prerequisite_refs") or P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS)
        prereq_satisfied = _dedupe_clean_refs(list(op14.get("complete_candidate_prerequisite_satisfied_refs") or []), max_length=260)
        prereq_missing = _dedupe_clean_refs(list(op14.get("complete_candidate_prerequisite_missing_refs") or []), max_length=260)
    elif isinstance(op15, Mapping):
        prereq_refs = list(op15.get("complete_candidate_prerequisite_refs") or P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS)
        prereq_satisfied = _dedupe_clean_refs(list(op15.get("complete_candidate_prerequisite_satisfied_refs") or []), max_length=260)
        prereq_missing = _dedupe_clean_refs(list(op15.get("complete_candidate_prerequisite_missing_refs") or []), max_length=260)
    else:
        prereq_refs = list(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS)
        prereq_satisfied = []
        prereq_missing = list(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS)
    supplied_refs = _op03_satisfied_material_refs(op14=op14, op15=op15, op14_valid=op14_contract_valid, op15_valid=op15_contract_valid, supplied_refs=supplied_material_inventory_refs)
    supplied_missing = [ref for ref in P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS if ref not in supplied_refs]
    scan_targets = {
        "dri_op02_alignment": op02_map,
        "rsr_op15_branch_resolver": op15_map,
        "rsr_op14_final_validation": op14_map,
    }
    forbidden_paths = _dedupe_clean_refs([ref for name, material in scan_targets.items() for ref in _scan_forbidden_payload_key_paths(material, path=name)], max_length=340)
    body_like_paths = _dedupe_clean_refs([ref for name, material in scan_targets.items() for ref in _scan_body_like_value_paths(material, path=name)], max_length=340)
    promotion_claims = _dedupe_clean_refs([ref for name, material in scan_targets.items() for ref in _scan_promotion_claim_refs(material, path=name)], max_length=340)
    status_ref, reasons, blockers, next_required_step = _op03_status_reason_blocker_next(
        op02_status_ref=_clean_ref(op02_map.get("dri_op02_status_ref"), default="dri_op02_status_missing", max_length=260),
        op02_contract_valid=op02_contract_valid,
        op02_aligned=bool(op02_map.get("dri_op02_aligned") is True),
        op14_present=isinstance(op14, Mapping),
        op14_contract_valid=op14_contract_valid,
        op14_blocked=bool(op14_map.get("rsr_op14_body_leak_promotion_or_source_kind_blocked") is True),
        op15_contract_valid=op15_contract_valid,
        op15_complete_candidate=bool(op15_map.get("actual_evidence_complete_candidate") is True),
        prerequisite_missing_refs=prereq_missing,
        supplied_missing_refs=supplied_missing,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_INVENTORY_READY_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02_map.get("schema_version"), default="op02_schema_missing", max_length=260),
        "op02_material_ref": _clean_ref(op02_map.get("material_id"), default="op02_material_missing", max_length=260),
        "op02_next_required_step": _clean_ref(op02_map.get("next_required_step"), default="op02_next_required_step_missing", max_length=260),
        "op02_contract_valid": op02_contract_valid,
        "op02_status_ref": _clean_ref(op02_map.get("dri_op02_status_ref"), default="dri_op02_status_missing", max_length=260),
        "op02_aligned": bool(op02_map.get("dri_op02_aligned") is True),
        "rsr_op15_branch_resolver_present": isinstance(op15, Mapping),
        "rsr_op15_contract_valid": op15_contract_valid,
        "rsr_op15_branch_ref": _clean_ref(op15_map.get("rsr_op15_branch_ref"), default="rsr_op15_branch_missing", max_length=260),
        "rsr_op15_next_required_step": _clean_ref(op15_map.get("next_required_step"), default="rsr_op15_next_required_step_missing", max_length=260),
        "rsr_op15_actual_evidence_complete_candidate": bool(op15_map.get("actual_evidence_complete_candidate") is True),
        "rsr_op15_candidate_ref": _clean_ref(op15_map.get("source_claim_bundle_candidate_ref"), default="rsr_op15_candidate_ref_missing", max_length=260),
        "rsr_op15_candidate_ref_alone_is_not_actual_evidence": True,
        "rsr_op14_final_validation_present": isinstance(op14, Mapping),
        "rsr_op14_contract_valid": op14_contract_valid,
        "rsr_op14_status_ref": _clean_ref(op14_map.get("rsr_op14_status_ref"), default="rsr_op14_status_missing", max_length=260),
        "rsr_op14_final_validation_passed": bool(op14_map.get("rsr_op14_final_validation_passed") is True),
        "rsr_op14_actual_evidence_complete_candidate_ready_for_op15": bool(op14_map.get("actual_evidence_complete_candidate_ready_for_op15") is True),
        "rsr_op14_body_leak_promotion_or_source_kind_blocked": bool(op14_map.get("rsr_op14_body_leak_promotion_or_source_kind_blocked") is True),
        "complete_candidate_prerequisite_refs": _dedupe_clean_refs(prereq_refs, max_length=260),
        "complete_candidate_prerequisite_ref_count": len(_dedupe_clean_refs(prereq_refs, max_length=260)),
        "complete_candidate_prerequisite_satisfied_refs": prereq_satisfied,
        "complete_candidate_prerequisite_satisfied_ref_count": len(prereq_satisfied),
        "complete_candidate_prerequisite_missing_refs": prereq_missing,
        "complete_candidate_prerequisite_missing_ref_count": len(prereq_missing),
        "explicit_allow_accepted": "explicit_allow_accepted" in prereq_satisfied,
        "readiness_blocker_count_zero": "readiness_blocker_count_zero" in prereq_satisfied,
        "reviewer_person_confirmed": "reviewer_person_confirmed" in prereq_satisfied,
        "packet_generation_receipt_accepted": "packet_generation_receipt_accepted" in prereq_satisfied,
        "actual_operation_receipt_accepted": "actual_operation_receipt_accepted" in prereq_satisfied,
        "sanitized_review_result_rows_accepted": "sanitized_review_result_rows_accepted" in prereq_satisfied,
        "rating_rows_accepted": "rating_rows_accepted" in prereq_satisfied,
        "question_need_observation_rows_accepted": "question_need_observation_rows_accepted" in prereq_satisfied,
        "disposal_purge_receipt_accepted": "disposal_purge_receipt_accepted" in prereq_satisfied,
        "final_no_leak_validation_passed": "final_no_leak_validation_passed" in prereq_satisfied,
        "supplied_material_inventory_required_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS),
        "supplied_material_inventory_required_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS),
        "supplied_material_inventory_refs": supplied_refs,
        "supplied_material_inventory_ref_count": len(supplied_refs),
        "supplied_material_missing_refs": supplied_missing,
        "supplied_material_missing_ref_count": len(supplied_missing),
        "dri_op03_forbidden_payload_key_path_refs": forbidden_paths,
        "dri_op03_forbidden_payload_key_path_count": len(forbidden_paths),
        "dri_op03_body_like_value_path_refs": body_like_paths,
        "dri_op03_body_like_value_path_count": len(body_like_paths),
        "dri_op03_promotion_claim_refs": promotion_claims,
        "dri_op03_promotion_claim_ref_count": len(promotion_claims),
        "dri_op03_status_ref": status_ref,
        "complete_candidate_inventory_status_ref": status_ref,
        "dri_op03_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP03_ALLOWED_STATUS_REFS),
        "dri_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP03_ALLOWED_STATUS_REFS),
        "dri_op03_inventory_ready": ready,
        "dri_op03_wait_for_prerequisites_or_supplied_materials": waiting,
        "dri_op03_repair_required": repair,
        "dri_op03_bodyfree_leak_or_promotion_blocked": blocked,
        "dri_op03_ready_for_actual_operation_receipt_revalidation": ready,
        "dri_op03_reason_refs": _dedupe_clean_refs(reasons, max_length=320),
        "dri_op03_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=320)),
        "dri_op03_blocker_refs": _dedupe_clean_refs(blockers, max_length=320),
        "dri_op03_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=320)),
        "actual_review_execution_claimed_by_dri_op03": False,
        "actual_review_evidence_completed_by_dri_op03": False,
        "dhr_actual_source_claim_confirmed_by_dri_op03": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op03": False,
        "dhr_op04_called_by_dri_op03": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op03": False,
        "dri_op03_does_not_execute_dhr_reintake": True,
        "dri_op03_does_not_call_dhr_op04": True,
        "dri_op03_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op03_does_not_execute_dmd_or_r52": True,
        "dri_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op03_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DRI-OP03 body-free complete-candidate prerequisite / inventory contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP03")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP03_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP03_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP03")
    for field, count_field in (
        ("complete_candidate_prerequisite_refs", "complete_candidate_prerequisite_ref_count"),
        ("complete_candidate_prerequisite_satisfied_refs", "complete_candidate_prerequisite_satisfied_ref_count"),
        ("complete_candidate_prerequisite_missing_refs", "complete_candidate_prerequisite_missing_ref_count"),
        ("supplied_material_inventory_required_refs", "supplied_material_inventory_required_ref_count"),
        ("supplied_material_inventory_refs", "supplied_material_inventory_ref_count"),
        ("supplied_material_missing_refs", "supplied_material_missing_ref_count"),
        ("dri_op03_forbidden_payload_key_path_refs", "dri_op03_forbidden_payload_key_path_count"),
        ("dri_op03_body_like_value_path_refs", "dri_op03_body_like_value_path_count"),
        ("dri_op03_promotion_claim_refs", "dri_op03_promotion_claim_ref_count"),
        ("dri_op03_allowed_status_refs", "dri_op03_allowed_status_ref_count"),
        ("dri_op03_reason_refs", "dri_op03_reason_ref_count"),
        ("dri_op03_blocker_refs", "dri_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP03 {count_field} changed")
    if tuple(data.get("dri_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 allowed status refs changed")
    if tuple(data.get("supplied_material_inventory_required_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP03_SUPPLIED_MATERIAL_REQUIRED_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 supplied material required refs changed")
    if tuple(data.get("complete_candidate_prerequisite_refs") or ()) != rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 prerequisite refs changed")
    for key in (
        "rsr_op15_candidate_ref_alone_is_not_actual_evidence", "dri_op03_does_not_execute_dhr_reintake", "dri_op03_does_not_call_dhr_op04", "dri_op03_does_not_materialize_dhr_op04_adapter_candidate", "dri_op03_does_not_execute_dmd_or_r52", "dri_op03_does_not_start_p5_p6_p8_p7_or_release", "dri_op03_does_not_change_api_db_rn_runtime_response_key", "dri_op03_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP03 required true boundary changed: {key}")
    for key in (
        "actual_review_execution_claimed_by_dri_op03", "actual_review_evidence_completed_by_dri_op03", "dhr_actual_source_claim_confirmed_by_dri_op03", "dhr_op04_adapter_candidate_materialized_by_dri_op03", "dhr_op04_called_by_dri_op03", "dhr_actual_source_claim_reintake_executed_by_dri_op03", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP03 downstream/execution flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP03_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 implemented/not-yet steps changed")
    status_ref = data.get("dri_op03_status_ref")
    if status_ref != data.get("complete_candidate_inventory_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 status alias changed")
    status_flags = [
        data.get("dri_op03_inventory_ready") is True,
        data.get("dri_op03_wait_for_prerequisites_or_supplied_materials") is True,
        data.get("dri_op03_repair_required") is True,
        data.get("dri_op03_bodyfree_leak_or_promotion_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_INVENTORY_READY_REF:
        if data.get("op02_contract_valid") is not True or data.get("op02_aligned") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 ready requires OP02 alignment")
        if data.get("rsr_op15_contract_valid") is not True or data.get("rsr_op15_actual_evidence_complete_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 ready requires OP15 complete candidate")
        if data.get("rsr_op14_contract_valid") is not True or data.get("rsr_op14_final_validation_passed") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 ready requires OP14 final validation")
        if data.get("complete_candidate_prerequisite_missing_refs") != [] or data.get("supplied_material_missing_refs") != [] or data.get("dri_op03_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 ready cannot carry missing refs or blockers")
        if data.get("dri_op03_ready_for_actual_operation_receipt_revalidation") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_WAIT_FOR_PREREQUISITES_OR_MATERIALS_REF:
        if data.get("dri_op03_wait_for_prerequisites_or_supplied_materials") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 wait branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF:
        if data.get("dri_op03_repair_required") is not True or not data.get("dri_op03_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 repair branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF:
        if data.get("dri_op03_bodyfree_leak_or_promotion_blocked") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP03_INVENTORY_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 blocked branch changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP03 status ref is not allowed")
    return True



# DRI-OP04/OP05 additions: actual operation receipt and rows/rating rows revalidation.
P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REVALIDATED_BODYFREE_REF: Final = (
    "DRI_OP04_ACTUAL_OPERATION_RECEIPT_REVALIDATED_BODYFREE"
)
P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF: Final = (
    "DRI_OP04_WAIT_FOR_ACTUAL_OPERATION_RECEIPT"
)
P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF: Final = (
    "DRI_OP04_REPAIR_ACTUAL_OPERATION_RECEIPT"
)
P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF: Final = (
    "DRI_OP04_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM"
)
P7_R54_AHR_POST_RSR16_DRI_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REVALIDATED_BODYFREE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_REF: Final = (
    "wait_for_actual_operation_receipt_bodyfree_before_dri_op05"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_REF: Final = (
    "repair_dri_op04_actual_operation_receipt_before_rows_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_REF: Final = (
    "blocked_dri_op04_actual_operation_receipt_body_leak_or_source_claim"
)

P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_ROWS_RATINGS_REVALIDATED_BODYFREE_REF: Final = (
    "DRI_OP05_ROWS_AND_RATINGS_REVALIDATED_BODYFREE"
)
P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF: Final = (
    "DRI_OP05_WAIT_FOR_ROWS_AND_RATINGS"
)
P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF: Final = (
    "DRI_OP05_REPAIR_ROWS_AND_RATINGS"
)
P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF: Final = (
    "DRI_OP05_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM"
)
P7_R54_AHR_POST_RSR16_DRI_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_ROWS_RATINGS_REVALIDATED_BODYFREE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ROWS_AND_RATINGS_REF: Final = (
    "wait_for_sanitized_review_result_rows_and_rating_rows_bodyfree_before_dri_op06"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ROWS_AND_RATINGS_REF: Final = (
    "repair_dri_op05_rows_and_ratings_before_question_need_rows_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ROWS_AND_RATINGS_REF: Final = (
    "blocked_dri_op05_rows_and_ratings_body_leak_or_source_claim"
)

P7_R54_AHR_POST_RSR16_DRI_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_schema_version", "op03_material_ref", "op03_next_required_step", "op03_contract_valid", "op03_status_ref", "op03_inventory_ready", "op03_ready_for_actual_operation_receipt_revalidation",
    "rsr_op10_actual_operation_receipt_intake_present", "rsr_op10_contract_valid", "rsr_op10_schema_version", "rsr_op10_operation_step_ref", "rsr_op10_material_ref", "rsr_op10_status_ref", "rsr_op10_next_required_step",
    "rsr_op10_actual_operation_receipt_accepted", "actual_operation_receipt_accepted_by_rsr_op10", "ready_for_sanitized_review_result_rows_rating_rows_intake",
    "actual_operation_receipt_present", "operation_receipt_ref", "operation_receipt_ref_present", "operation_receipt_review_session_id", "operation_receipt_review_session_id_matches", "operation_receipt_packet_request_ref", "operation_receipt_packet_request_ref_present",
    "source_kind_ref", "source_kind_is_actual_local_only_human_review_by_person", "created_from_real_operation", "actual_human_review_executed_by_person", "reviewer_person_ref", "reviewer_person_ref_present",
    "expected_case_count", "reviewed_case_count", "selection_row_count", "reviewed_case_count_is_24", "selection_row_count_is_24", "local_only_operation_confirmed", "selection_only_form_used", "actual_operation_receipt_body_free",
    "actual_operation_receipt_external_export_performed", "actual_operation_receipt_raw_input_included", "actual_operation_receipt_comment_text_body_included", "actual_operation_receipt_returned_surface_body_included", "actual_operation_receipt_reviewer_free_text_included", "actual_operation_receipt_reviewer_note_body_included", "actual_operation_receipt_question_text_included", "actual_operation_receipt_draft_question_text_included", "actual_operation_receipt_answer_text_included", "actual_operation_receipt_local_path_included", "actual_operation_receipt_body_hash_included", "actual_operation_receipt_terminal_output_body_included",
    "actual_operation_receipt_forbidden_payload_key_path_refs", "actual_operation_receipt_forbidden_payload_key_path_count", "actual_operation_receipt_body_like_value_path_refs", "actual_operation_receipt_body_like_value_path_count", "actual_operation_receipt_promotion_claim_refs", "actual_operation_receipt_promotion_claim_ref_count", "actual_operation_receipt_source_claim_blocker_refs", "actual_operation_receipt_source_claim_blocker_ref_count", "actual_operation_receipt_body_free_marker_violation_refs", "actual_operation_receipt_body_free_marker_violation_ref_count",
    "dri_op04_status_ref", "actual_operation_receipt_revalidation_status_ref", "dri_op04_allowed_status_refs", "dri_op04_allowed_status_ref_count", "dri_op04_revalidated_bodyfree", "dri_op04_wait_for_actual_operation_receipt", "dri_op04_repair_required", "dri_op04_body_leak_or_source_claim_blocked", "dri_op04_ready_for_rows_and_ratings_revalidation",
    "dri_op04_reason_refs", "dri_op04_reason_ref_count", "dri_op04_blocker_refs", "dri_op04_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op04", "actual_review_evidence_completed_by_dri_op04", "dhr_actual_source_claim_confirmed_by_dri_op04", "dhr_op04_adapter_candidate_materialized_by_dri_op04", "dhr_op04_called_by_dri_op04", "dhr_actual_source_claim_reintake_executed_by_dri_op04",
    "dri_op04_does_not_create_actual_operation_receipt", "dri_op04_does_not_run_actual_local_human_review", "dri_op04_does_not_create_rows_question_rows_or_disposal", "dri_op04_does_not_execute_dhr_reintake", "dri_op04_does_not_call_dhr_op04", "dri_op04_does_not_materialize_dhr_op04_adapter_candidate", "dri_op04_does_not_execute_dmd_or_r52", "dri_op04_does_not_start_p5_p6_p8_p7_or_release", "dri_op04_does_not_change_api_db_rn_runtime_response_key", "dri_op04_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RSR16_DRI_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_schema_version", "op04_material_ref", "op04_next_required_step", "op04_contract_valid", "op04_status_ref", "op04_revalidated_bodyfree", "op04_ready_for_rows_and_ratings_revalidation",
    "rsr_op11_rows_rating_rows_intake_present", "rsr_op11_contract_valid", "rsr_op11_schema_version", "rsr_op11_operation_step_ref", "rsr_op11_material_ref", "rsr_op11_status_ref", "rsr_op11_next_required_step",
    "rsr_op11_sanitized_review_result_rows_accepted", "rsr_op11_rating_rows_accepted", "actual_review_rows_and_rating_rows_intaken_bodyfree", "question_need_observation_rows_required_next",
    "operation_receipt_ref", "operation_receipt_ref_matches_op04", "reviewer_person_ref", "review_session_id_matches_op04", "source_kind_ref", "rows_source_kind_is_actual_local_only_human_review_by_person",
    "expected_review_row_count", "sanitized_review_result_row_count", "rating_row_count", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24", "sanitized_review_result_row_refs", "sanitized_review_result_row_ref_count", "rating_row_refs", "rating_row_ref_count", "case_ref_values", "case_ref_count", "case_ref_unique_count", "case_refs_match_between_sanitized_and_rating_rows",
    "sanitized_rows_bodyfree_only", "sanitized_rows_selection_only", "sanitized_rows_have_actual_person_selection_only_provenance", "sanitized_rows_have_required_axis_scores", "sanitized_rows_have_allowed_verdict_refs", "sanitized_rows_have_allowed_question_observation_refs", "sanitized_rows_have_no_body_or_question_or_path_or_hash", "rating_rows_bodyfree_only", "rating_rows_from_sanitized_rows", "rating_rows_have_required_axis_scores", "rating_rows_have_no_body_or_question_or_path_or_hash", "rows_operation_receipt_ref_matches", "rows_reviewer_person_ref_matches",
    "review_rows_forbidden_payload_key_path_refs", "review_rows_forbidden_payload_key_path_count", "review_rows_body_like_value_path_refs", "review_rows_body_like_value_path_count", "review_rows_promotion_claim_refs", "review_rows_promotion_claim_ref_count", "rating_rows_forbidden_payload_key_path_refs", "rating_rows_forbidden_payload_key_path_count", "rating_rows_body_like_value_path_refs", "rating_rows_body_like_value_path_count", "rating_rows_promotion_claim_refs", "rating_rows_promotion_claim_ref_count",
    "question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here",
    "dri_op05_status_ref", "rows_and_ratings_revalidation_status_ref", "dri_op05_allowed_status_refs", "dri_op05_allowed_status_ref_count", "dri_op05_rows_and_ratings_revalidated_bodyfree", "dri_op05_wait_for_rows_and_ratings", "dri_op05_repair_required", "dri_op05_body_leak_or_source_claim_blocked", "dri_op05_ready_for_question_need_rows_bridge_only_revalidation",
    "dri_op05_reason_refs", "dri_op05_reason_ref_count", "dri_op05_blocker_refs", "dri_op05_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op05", "actual_review_evidence_completed_by_dri_op05", "dhr_actual_source_claim_confirmed_by_dri_op05", "dhr_op04_adapter_candidate_materialized_by_dri_op05", "dhr_op04_called_by_dri_op05", "dhr_actual_source_claim_reintake_executed_by_dri_op05",
    "dri_op05_does_not_create_sanitized_rows_or_rating_rows", "dri_op05_does_not_create_question_rows_or_disposal", "dri_op05_does_not_materialize_question_text_or_p8_spec", "dri_op05_does_not_execute_dhr_reintake", "dri_op05_does_not_call_dhr_op04", "dri_op05_does_not_materialize_dhr_op04_adapter_candidate", "dri_op05_does_not_execute_dmd_or_r52", "dri_op05_does_not_start_p5_p6_p8_p7_or_release", "dri_op05_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _rsr_op10_contract_valid(rsr_op10: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op10, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(rsr_op10) is True
    except ValueError:
        return False


def _rsr_op11_contract_valid(rsr_op11: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op11, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(rsr_op11) is True
    except ValueError:
        return False


def _op04_status_reason_blocker_next(
    *,
    op03_status_ref: str,
    op03_contract_valid: bool,
    op03_ready: bool,
    op10_present: bool,
    op10_contract_valid: bool,
    op10_status_ref: str,
    op10_accepted: bool,
    source_kind_actual: bool,
    created_from_real_operation: bool,
    actual_person_review: bool,
    receipt_body_free: bool,
    reviewed_count_ok: bool,
    selection_count_ok: bool,
    marker_violations: Sequence[str],
    source_claim_blockers: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []

    if not op03_contract_valid or op03_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_REPAIR_PREREQUISITES_OR_MATERIALS_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF,
            ["repair_dri_op03_inventory_before_actual_operation_receipt_revalidation"],
            ["dri_op03_inventory_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_REF,
        )
    if op03_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP03_STATUS_BLOCKED_BODYFREE_LEAK_OR_PROMOTION_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF,
            ["blocked_because_dri_op03_inventory_is_already_bodyfree_or_promotion_blocked"],
            ["dri_op03_bodyfree_leak_or_promotion_blocked"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_REF,
        )
    if not op03_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF,
            ["wait_for_dri_op03_inventory_ready_before_actual_operation_receipt_revalidation"],
            ["dri_op03_inventory_not_ready"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_REF,
        )
    if not op10_present or op10_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF,
            ["wait_for_supplied_rsr_op10_actual_operation_receipt_intake"],
            ["actual_operation_receipt_intake_missing_or_waiting"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_REF,
        )

    if forbidden_paths or body_like_paths or promotion_claims or marker_violations or source_claim_blockers or op10_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF or not source_kind_actual:
        if forbidden_paths:
            blockers.append("dri_op04_forbidden_payload_key_detected")
        if body_like_paths:
            blockers.append("dri_op04_body_like_value_detected")
        if promotion_claims:
            blockers.append("dri_op04_promotion_claim_detected")
        if marker_violations:
            blockers.append("dri_op04_body_free_marker_violation_detected")
        if source_claim_blockers:
            blockers.extend(source_claim_blockers)
        if op10_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF:
            blockers.append("rsr_op10_body_leak_or_source_claim_blocked")
        if not source_kind_actual:
            blockers.append("actual_operation_receipt_source_kind_not_actual_local_only_human_review_by_person")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF,
            ["actual_operation_receipt_bodyfree_or_source_claim_boundary_failed_before_rows_revalidation"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_REF,
        )
    if not op10_contract_valid or op10_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF,
            ["repair_rsr_op10_actual_operation_receipt_intake_before_dri_op05"],
            ["rsr_op10_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_REF,
        )
    if not (op10_accepted and created_from_real_operation and actual_person_review and receipt_body_free and reviewed_count_ok and selection_count_ok):
        blockers.extend(
            ref
            for ref, ok in (
                ("actual_operation_receipt_not_accepted_by_rsr_op10", op10_accepted),
                ("actual_operation_receipt_not_created_from_real_operation", created_from_real_operation),
                ("actual_human_review_executed_by_person_not_confirmed", actual_person_review),
                ("actual_operation_receipt_body_free_not_true", receipt_body_free),
                ("reviewed_case_count_not_24", reviewed_count_ok),
                ("selection_row_count_not_24", selection_count_ok),
            )
            if not ok
        )
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF,
            ["repair_actual_operation_receipt_acceptance_or_count_fields_before_dri_op05"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REVALIDATED_BODYFREE_REF,
        ["actual_operation_receipt_revalidated_bodyfree_for_rows_revalidation_without_dhr_execution"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF,
    )

def build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation(
    *,
    dri_op03_complete_candidate_supplied_material_inventory: Mapping[str, Any] | None = None,
    complete_candidate_supplied_material_inventory: Mapping[str, Any] | None = None,
    rsr_op10_actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP04 body-free actual operation receipt revalidation material."""

    op03 = dri_op03_complete_candidate_supplied_material_inventory if dri_op03_complete_candidate_supplied_material_inventory is not None else complete_candidate_supplied_material_inventory
    op10 = rsr_op10_actual_operation_receipt_intake if rsr_op10_actual_operation_receipt_intake is not None else actual_operation_receipt_intake
    op03_map = op03 if isinstance(op03, Mapping) else {}
    op10_map = op10 if isinstance(op10, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op10_map.get("review_session_id") or op03_map.get("review_session_id")))
    try:
        op03_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract(op03_map) is True
    except ValueError:
        op03_contract_valid = False
    op10_contract_valid = _rsr_op10_contract_valid(op10)
    op10_present = isinstance(op10, Mapping)
    op03_status_ref = _clean_ref(op03_map.get("dri_op03_status_ref"), default="dri_op03_status_missing", max_length=260)
    op10_status_ref = _clean_ref(op10_map.get("rsr_op10_status_ref"), default="rsr_op10_status_missing", max_length=260)
    op03_ready = bool(op03_map.get("dri_op03_inventory_ready") is True and op03_map.get("dri_op03_ready_for_actual_operation_receipt_revalidation") is True)
    forbidden_paths = _dedupe_clean_refs(
        list(_scan_forbidden_payload_key_paths(op10, path="rsr_op10_actual_operation_receipt_intake") if op10_present else [])
        + list(op10_map.get("actual_operation_receipt_forbidden_payload_key_path_refs") or []),
        max_length=320,
    )
    body_like_paths = _dedupe_clean_refs(
        list(_scan_body_like_value_paths(op10, path="rsr_op10_actual_operation_receipt_intake") if op10_present else [])
        + list(op10_map.get("actual_operation_receipt_body_like_value_path_refs") or []),
        max_length=320,
    )
    required_false_flag_promotions = [
        f"rsr_op10_actual_operation_receipt_intake.{key}"
        for key in P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS
        if op10_map.get(key) is True
    ]
    promotion_claims = _dedupe_clean_refs(
        list(_scan_promotion_claim_refs(op10, path="rsr_op10_actual_operation_receipt_intake") if op10_present else [])
        + list(op10_map.get("actual_operation_receipt_promotion_claim_refs") or [])
        + required_false_flag_promotions,
        max_length=320,
    )
    marker_violations = _dedupe_clean_refs(list(op10_map.get("actual_operation_receipt_body_free_marker_violation_refs") or []), max_length=320)
    source_claim_blockers = _dedupe_clean_refs(list(op10_map.get("actual_operation_receipt_source_claim_blocker_refs") or []), max_length=320)
    expected_count = getattr(rsr, "P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT", 24)
    reviewed_count = _safe_int_value(op10_map.get("reviewed_case_count"))
    selection_count = _safe_int_value(op10_map.get("selection_row_count"))
    source_kind_ref = _clean_ref(op10_map.get("source_kind_ref"), default="actual_operation_receipt_source_kind_missing", max_length=220)
    source_kind_actual = source_kind_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF and op10_map.get("source_kind_is_actual_local_only_human_review_by_person") is True
    status_ref, reasons, blockers, next_required_step = _op04_status_reason_blocker_next(
        op03_status_ref=op03_status_ref,
        op03_contract_valid=op03_contract_valid,
        op03_ready=op03_ready,
        op10_present=op10_present,
        op10_contract_valid=op10_contract_valid,
        op10_status_ref=op10_status_ref,
        op10_accepted=bool(op10_map.get("rsr_op10_actual_operation_receipt_accepted") is True and op10_map.get("actual_operation_receipt_accepted_by_rsr_op10") is True),
        source_kind_actual=source_kind_actual,
        created_from_real_operation=op10_map.get("created_from_real_operation") is True,
        actual_person_review=op10_map.get("actual_human_review_executed_by_person") is True,
        receipt_body_free=op10_map.get("actual_operation_receipt_body_free") is True,
        reviewed_count_ok=reviewed_count == expected_count,
        selection_count_ok=selection_count == expected_count,
        marker_violations=marker_violations,
        source_claim_blockers=source_claim_blockers,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REVALIDATED_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": op03_map.get("schema_version"),
        "op03_material_ref": _clean_ref(op03_map.get("material_id"), default="dri_op03_material_missing", max_length=260),
        "op03_next_required_step": op03_map.get("next_required_step"),
        "op03_contract_valid": op03_contract_valid,
        "op03_status_ref": op03_status_ref,
        "op03_inventory_ready": op03_map.get("dri_op03_inventory_ready") is True,
        "op03_ready_for_actual_operation_receipt_revalidation": op03_ready,
        "rsr_op10_actual_operation_receipt_intake_present": op10_present,
        "rsr_op10_contract_valid": op10_contract_valid,
        "rsr_op10_schema_version": op10_map.get("schema_version"),
        "rsr_op10_operation_step_ref": op10_map.get("operation_step_ref"),
        "rsr_op10_material_ref": _clean_ref(op10_map.get("material_id"), default="rsr_op10_material_missing", max_length=260),
        "rsr_op10_status_ref": op10_status_ref,
        "rsr_op10_next_required_step": op10_map.get("next_required_step"),
        "rsr_op10_actual_operation_receipt_accepted": op10_map.get("rsr_op10_actual_operation_receipt_accepted") is True,
        "actual_operation_receipt_accepted_by_rsr_op10": op10_map.get("actual_operation_receipt_accepted_by_rsr_op10") is True,
        "ready_for_sanitized_review_result_rows_rating_rows_intake": op10_map.get("ready_for_sanitized_review_result_rows_rating_rows_intake") is True,
        "actual_operation_receipt_present": op10_map.get("actual_operation_receipt_present") is True,
        "operation_receipt_ref": _clean_ref(op10_map.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220),
        "operation_receipt_ref_present": op10_map.get("operation_receipt_ref_present") is True,
        "operation_receipt_review_session_id": _safe_review_session_id(op10_map.get("operation_receipt_review_session_id") or op10_map.get("review_session_id")),
        "operation_receipt_review_session_id_matches": op10_map.get("operation_receipt_review_session_id_matches") is True,
        "operation_receipt_packet_request_ref": _clean_ref(op10_map.get("operation_receipt_packet_request_ref"), default="operation_receipt_packet_request_ref_missing", max_length=220),
        "operation_receipt_packet_request_ref_present": op10_map.get("operation_receipt_packet_request_ref_present") is True,
        "source_kind_ref": source_kind_ref,
        "source_kind_is_actual_local_only_human_review_by_person": source_kind_actual,
        "created_from_real_operation": op10_map.get("created_from_real_operation") is True,
        "actual_human_review_executed_by_person": op10_map.get("actual_human_review_executed_by_person") is True,
        "reviewer_person_ref": _clean_ref(op10_map.get("reviewer_person_ref"), default="reviewer_person_ref_missing", max_length=220),
        "reviewer_person_ref_present": op10_map.get("reviewer_person_ref_present") is True,
        "expected_case_count": expected_count,
        "reviewed_case_count": reviewed_count,
        "selection_row_count": selection_count,
        "reviewed_case_count_is_24": reviewed_count == expected_count,
        "selection_row_count_is_24": selection_count == expected_count,
        "local_only_operation_confirmed": op10_map.get("local_only_operation_confirmed") is True,
        "selection_only_form_used": op10_map.get("selection_only_form_used") is True,
        "actual_operation_receipt_body_free": op10_map.get("actual_operation_receipt_body_free") is True,
        "actual_operation_receipt_external_export_performed": op10_map.get("actual_operation_receipt_external_export_performed") is True,
        "actual_operation_receipt_raw_input_included": op10_map.get("actual_operation_receipt_raw_input_included") is True,
        "actual_operation_receipt_comment_text_body_included": op10_map.get("actual_operation_receipt_comment_text_body_included") is True,
        "actual_operation_receipt_returned_surface_body_included": op10_map.get("actual_operation_receipt_returned_surface_body_included") is True,
        "actual_operation_receipt_reviewer_free_text_included": op10_map.get("actual_operation_receipt_reviewer_free_text_included") is True,
        "actual_operation_receipt_reviewer_note_body_included": op10_map.get("actual_operation_receipt_reviewer_note_body_included") is True,
        "actual_operation_receipt_question_text_included": op10_map.get("actual_operation_receipt_question_text_included") is True,
        "actual_operation_receipt_draft_question_text_included": op10_map.get("actual_operation_receipt_draft_question_text_included") is True,
        "actual_operation_receipt_answer_text_included": op10_map.get("actual_operation_receipt_answer_text_included") is True,
        "actual_operation_receipt_local_path_included": op10_map.get("actual_operation_receipt_local_path_included") is True,
        "actual_operation_receipt_body_hash_included": op10_map.get("actual_operation_receipt_body_hash_included") is True,
        "actual_operation_receipt_terminal_output_body_included": op10_map.get("actual_operation_receipt_terminal_output_body_included") is True,
        "actual_operation_receipt_forbidden_payload_key_path_refs": forbidden_paths,
        "actual_operation_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "actual_operation_receipt_body_like_value_path_refs": body_like_paths,
        "actual_operation_receipt_body_like_value_path_count": len(body_like_paths),
        "actual_operation_receipt_promotion_claim_refs": promotion_claims,
        "actual_operation_receipt_promotion_claim_ref_count": len(promotion_claims),
        "actual_operation_receipt_source_claim_blocker_refs": source_claim_blockers,
        "actual_operation_receipt_source_claim_blocker_ref_count": len(source_claim_blockers),
        "actual_operation_receipt_body_free_marker_violation_refs": marker_violations,
        "actual_operation_receipt_body_free_marker_violation_ref_count": len(marker_violations),
        "dri_op04_status_ref": status_ref,
        "actual_operation_receipt_revalidation_status_ref": status_ref,
        "dri_op04_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP04_ALLOWED_STATUS_REFS),
        "dri_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP04_ALLOWED_STATUS_REFS),
        "dri_op04_revalidated_bodyfree": ready,
        "dri_op04_wait_for_actual_operation_receipt": waiting,
        "dri_op04_repair_required": repair,
        "dri_op04_body_leak_or_source_claim_blocked": blocked,
        "dri_op04_ready_for_rows_and_ratings_revalidation": ready,
        "dri_op04_reason_refs": reasons,
        "dri_op04_reason_ref_count": len(reasons),
        "dri_op04_blocker_refs": blockers,
        "dri_op04_blocker_ref_count": len(blockers),
        "actual_review_execution_claimed_by_dri_op04": False,
        "actual_review_evidence_completed_by_dri_op04": False,
        "dhr_actual_source_claim_confirmed_by_dri_op04": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op04": False,
        "dhr_op04_called_by_dri_op04": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op04": False,
        "dri_op04_does_not_create_actual_operation_receipt": True,
        "dri_op04_does_not_run_actual_local_human_review": True,
        "dri_op04_does_not_create_rows_question_rows_or_disposal": True,
        "dri_op04_does_not_execute_dhr_reintake": True,
        "dri_op04_does_not_call_dhr_op04": True,
        "dri_op04_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op04_does_not_execute_dmd_or_r52": True,
        "dri_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op04_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP04 body-free actual operation receipt revalidation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP04")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP04_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP04_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP04")
    for field, count_field in (("actual_operation_receipt_forbidden_payload_key_path_refs", "actual_operation_receipt_forbidden_payload_key_path_count"), ("actual_operation_receipt_body_like_value_path_refs", "actual_operation_receipt_body_like_value_path_count"), ("actual_operation_receipt_promotion_claim_refs", "actual_operation_receipt_promotion_claim_ref_count"), ("actual_operation_receipt_source_claim_blocker_refs", "actual_operation_receipt_source_claim_blocker_ref_count"), ("actual_operation_receipt_body_free_marker_violation_refs", "actual_operation_receipt_body_free_marker_violation_ref_count"), ("dri_op04_allowed_status_refs", "dri_op04_allowed_status_ref_count"), ("dri_op04_reason_refs", "dri_op04_reason_ref_count"), ("dri_op04_blocker_refs", "dri_op04_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP04 {count_field} changed")
    if tuple(data.get("dri_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 allowed status refs changed")
    for key in ("dri_op04_does_not_create_actual_operation_receipt", "dri_op04_does_not_run_actual_local_human_review", "dri_op04_does_not_create_rows_question_rows_or_disposal", "dri_op04_does_not_execute_dhr_reintake", "dri_op04_does_not_call_dhr_op04", "dri_op04_does_not_materialize_dhr_op04_adapter_candidate", "dri_op04_does_not_execute_dmd_or_r52", "dri_op04_does_not_start_p5_p6_p8_p7_or_release", "dri_op04_does_not_change_api_db_rn_runtime_response_key", "dri_op04_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP04 required true boundary changed: {key}")
    for key in ("actual_review_execution_claimed_by_dri_op04", "actual_review_evidence_completed_by_dri_op04", "dhr_actual_source_claim_confirmed_by_dri_op04", "dhr_op04_adapter_candidate_materialized_by_dri_op04", "dhr_op04_called_by_dri_op04", "dhr_actual_source_claim_reintake_executed_by_dri_op04", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_review_evidence_complete_here", "external_actual_operation_evidence_claim_adapter_candidate_materialized_here", "actual_source_claim_for_dhr_reintake_materialized_here", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP04 downstream/execution flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP04_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 implemented/not-yet steps changed")
    status_ref = data.get("dri_op04_status_ref")
    if status_ref != data.get("actual_operation_receipt_revalidation_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 status alias changed")
    status_flags = [
        data.get("dri_op04_revalidated_bodyfree") is True,
        data.get("dri_op04_wait_for_actual_operation_receipt") is True,
        data.get("dri_op04_repair_required") is True,
        data.get("dri_op04_body_leak_or_source_claim_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REVALIDATED_BODYFREE_REF:
        for key in ("op03_contract_valid", "op03_inventory_ready", "op03_ready_for_actual_operation_receipt_revalidation", "rsr_op10_contract_valid", "rsr_op10_actual_operation_receipt_accepted", "actual_operation_receipt_accepted_by_rsr_op10", "ready_for_sanitized_review_result_rows_rating_rows_intake", "actual_operation_receipt_present", "operation_receipt_ref_present", "operation_receipt_review_session_id_matches", "operation_receipt_packet_request_ref_present", "source_kind_is_actual_local_only_human_review_by_person", "created_from_real_operation", "actual_human_review_executed_by_person", "reviewer_person_ref_present", "reviewed_case_count_is_24", "selection_row_count_is_24", "local_only_operation_confirmed", "selection_only_form_used", "actual_operation_receipt_body_free"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP04 ready branch required true changed: {key}")
        if data.get("dri_op04_blocker_refs") != [] or data.get("actual_operation_receipt_forbidden_payload_key_path_refs") != [] or data.get("actual_operation_receipt_body_like_value_path_refs") != [] or data.get("actual_operation_receipt_promotion_claim_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_WAIT_FOR_RECEIPT_REF:
        if data.get("dri_op04_wait_for_actual_operation_receipt") is not True or data.get("dri_op04_ready_for_rows_and_ratings_revalidation") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 wait branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 wait next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF:
        if data.get("dri_op04_repair_required") is not True or not data.get("dri_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF:
        if data.get("dri_op04_body_leak_or_source_claim_blocked") is not True or not data.get("dri_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 blocked next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP04 status ref is not allowed")
    return True


def _op05_status_reason_blocker_next(
    *,
    op04_status_ref: str,
    op04_contract_valid: bool,
    op04_ready: bool,
    op11_present: bool,
    op11_contract_valid: bool,
    op11_status_ref: str,
    rows_accepted: bool,
    ratings_accepted: bool,
    row_count_ok: bool,
    rating_count_ok: bool,
    session_matches: bool,
    operation_receipt_matches: bool,
    source_kind_actual: bool,
    question_materialized: bool,
    rows_have_no_body: bool,
    ratings_have_no_body: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []

    if not op04_contract_valid or op04_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_REPAIR_RECEIPT_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF,
            ["repair_dri_op04_actual_operation_receipt_before_rows_revalidation"],
            ["dri_op04_receipt_revalidation_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ROWS_AND_RATINGS_REF,
        )
    if op04_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP04_STATUS_BLOCKED_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF,
            ["blocked_because_dri_op04_receipt_revalidation_is_already_blocked"],
            ["dri_op04_receipt_body_leak_or_source_claim_blocked"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ROWS_AND_RATINGS_REF,
        )
    if not op04_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF,
            ["wait_for_dri_op04_receipt_revalidation_before_rows_and_ratings"],
            ["dri_op04_receipt_revalidation_not_ready"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ROWS_AND_RATINGS_REF,
        )
    if not op11_present or op11_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF,
            ["wait_for_supplied_rsr_op11_rows_and_ratings_intake"],
            ["sanitized_review_result_rows_or_rating_rows_missing_or_waiting"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ROWS_AND_RATINGS_REF,
        )

    if forbidden_paths or body_like_paths or promotion_claims or op11_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF or not source_kind_actual or question_materialized:
        if forbidden_paths:
            blockers.append("dri_op05_forbidden_payload_key_detected")
        if body_like_paths:
            blockers.append("dri_op05_body_like_value_detected")
        if promotion_claims:
            blockers.append("dri_op05_promotion_claim_detected")
        if op11_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF:
            blockers.append("rsr_op11_rows_body_leak_or_source_claim_blocked")
        if not source_kind_actual:
            blockers.append("rows_source_kind_not_actual_local_only_human_review_by_person")
        if question_materialized:
            blockers.append("question_text_or_p8_question_materialization_detected")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF,
            ["rows_and_ratings_bodyfree_or_source_claim_boundary_failed_before_question_need_rows"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ROWS_AND_RATINGS_REF,
        )
    if not op11_contract_valid or op11_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF,
            ["repair_rsr_op11_rows_and_ratings_before_dri_op06"],
            ["rsr_op11_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ROWS_AND_RATINGS_REF,
        )
    if not rows_have_no_body or not ratings_have_no_body:
        if not rows_have_no_body:
            blockers.append("sanitized_rows_body_or_question_or_path_or_hash_boundary_failed")
        if not ratings_have_no_body:
            blockers.append("rating_rows_body_or_question_or_path_or_hash_boundary_failed")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF,
            ["rows_and_ratings_bodyfree_boundary_failed_before_question_need_rows"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ROWS_AND_RATINGS_REF,
        )
    if not (rows_accepted and ratings_accepted and row_count_ok and rating_count_ok and session_matches and operation_receipt_matches):
        blockers.extend(
            ref
            for ref, ok in (
                ("sanitized_review_result_rows_not_accepted", rows_accepted),
                ("rating_rows_not_accepted", ratings_accepted),
                ("sanitized_review_result_row_count_not_24", row_count_ok),
                ("rating_row_count_not_24", rating_count_ok),
                ("review_session_id_mismatch_between_op04_and_rows", session_matches),
                ("operation_receipt_ref_mismatch_between_op04_and_rows", operation_receipt_matches),
            )
            if not ok
        )
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF,
            ["repair_rows_and_ratings_acceptance_counts_or_linkage_before_dri_op06"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ROWS_AND_RATINGS_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_ROWS_RATINGS_REVALIDATED_BODYFREE_REF,
        ["sanitized_review_result_rows_and_rating_rows_revalidated_bodyfree_without_question_materialization"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF,
    )

def build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation(
    *,
    dri_op04_actual_operation_receipt_revalidation: Mapping[str, Any] | None = None,
    actual_operation_receipt_revalidation: Mapping[str, Any] | None = None,
    rsr_op11_sanitized_review_result_rows_rating_rows_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_rating_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP05 body-free sanitized review result rows / rating rows revalidation material."""

    op04 = dri_op04_actual_operation_receipt_revalidation if dri_op04_actual_operation_receipt_revalidation is not None else actual_operation_receipt_revalidation
    op11 = rsr_op11_sanitized_review_result_rows_rating_rows_intake if rsr_op11_sanitized_review_result_rows_rating_rows_intake is not None else sanitized_review_result_rows_rating_rows_intake
    op04_map = op04 if isinstance(op04, Mapping) else {}
    op11_map = op11 if isinstance(op11, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op11_map.get("review_session_id") or op04_map.get("review_session_id")))
    try:
        op04_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract(op04_map) is True
    except ValueError:
        op04_contract_valid = False
    op11_contract_valid = _rsr_op11_contract_valid(op11)
    op11_present = isinstance(op11, Mapping)
    op04_status_ref = _clean_ref(op04_map.get("dri_op04_status_ref"), default="dri_op04_status_missing", max_length=260)
    op11_status_ref = _clean_ref(op11_map.get("rsr_op11_status_ref"), default="rsr_op11_status_missing", max_length=260)
    op04_ready = bool(op04_map.get("dri_op04_revalidated_bodyfree") is True and op04_map.get("dri_op04_ready_for_rows_and_ratings_revalidation") is True)
    review_forbidden = _dedupe_clean_refs(
        list(_scan_forbidden_payload_key_paths(op11, path="rsr_op11_rows_rating_rows_intake") if op11_present else [])
        + list(op11_map.get("review_rows_forbidden_payload_key_path_refs") or []),
        max_length=320,
    )
    review_body_like = _dedupe_clean_refs(
        list(_scan_body_like_value_paths(op11, path="rsr_op11_rows_rating_rows_intake") if op11_present else [])
        + list(op11_map.get("review_rows_body_like_value_path_refs") or []),
        max_length=320,
    )
    required_false_flag_promotions = [
        f"rsr_op11_rows_rating_rows_intake.{key}"
        for key in P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS
        if op11_map.get(key) is True
    ]
    question_materialization_promotions = [
        f"rsr_op11_rows_rating_rows_intake.{key}"
        for key in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here")
        if op11_map.get(key) is True
    ]
    review_promotion = _dedupe_clean_refs(
        list(_scan_promotion_claim_refs(op11, path="rsr_op11_rows_rating_rows_intake") if op11_present else [])
        + list(op11_map.get("review_rows_promotion_claim_refs") or [])
        + required_false_flag_promotions
        + question_materialization_promotions,
        max_length=320,
    )
    rating_forbidden = _dedupe_clean_refs(list(op11_map.get("rating_rows_forbidden_payload_key_path_refs") or []), max_length=320)
    rating_body_like = _dedupe_clean_refs(list(op11_map.get("rating_rows_body_like_value_path_refs") or []), max_length=320)
    rating_promotion = _dedupe_clean_refs(list(op11_map.get("rating_rows_promotion_claim_refs") or []), max_length=320)
    expected_count = getattr(rsr, "P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT", 24)
    row_count = _safe_int_value(op11_map.get("sanitized_review_result_row_count"))
    rating_count = _safe_int_value(op11_map.get("rating_row_count"))
    session_matches = _safe_review_session_id(op11_map.get("review_session_id")) == _safe_review_session_id(op04_map.get("review_session_id"))
    operation_receipt_matches = _clean_ref(op11_map.get("operation_receipt_ref"), default="op11_operation_receipt_missing", max_length=220) == _clean_ref(op04_map.get("operation_receipt_ref"), default="op04_operation_receipt_missing", max_length=220)
    source_kind_ref = rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF if op11_map.get("rows_source_kind_is_actual_local_only_human_review_by_person") is True else "rows_source_kind_not_actual_local_only_human_review_by_person"
    question_materialized = bool(op11_map.get("question_text_materialized") is True or op11_map.get("draft_question_text_materialized") is True or op11_map.get("p8_question_spec_created") is True or op11_map.get("p8_question_design_started_here") is True)
    rows_have_no_body = op11_map.get("sanitized_rows_have_no_body_or_question_or_path_or_hash") is True or not op11_present
    ratings_have_no_body = op11_map.get("rating_rows_have_no_body_or_question_or_path_or_hash") is True or not op11_present
    status_ref, reasons, blockers, next_required_step = _op05_status_reason_blocker_next(
        op04_status_ref=op04_status_ref,
        op04_contract_valid=op04_contract_valid,
        op04_ready=op04_ready,
        op11_present=op11_present,
        op11_contract_valid=op11_contract_valid,
        op11_status_ref=op11_status_ref,
        rows_accepted=op11_map.get("rsr_op11_sanitized_review_result_rows_accepted") is True,
        ratings_accepted=op11_map.get("rsr_op11_rating_rows_accepted") is True,
        row_count_ok=row_count == expected_count,
        rating_count_ok=rating_count == expected_count,
        session_matches=session_matches,
        operation_receipt_matches=operation_receipt_matches,
        source_kind_actual=op11_map.get("rows_source_kind_is_actual_local_only_human_review_by_person") is True,
        question_materialized=question_materialized,
        rows_have_no_body=rows_have_no_body,
        ratings_have_no_body=ratings_have_no_body,
        forbidden_paths=review_forbidden + rating_forbidden,
        body_like_paths=review_body_like + rating_body_like,
        promotion_claims=review_promotion + rating_promotion,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_ROWS_RATINGS_REVALIDATED_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": op04_map.get("schema_version"),
        "op04_material_ref": _clean_ref(op04_map.get("material_id"), default="dri_op04_material_missing", max_length=260),
        "op04_next_required_step": op04_map.get("next_required_step"),
        "op04_contract_valid": op04_contract_valid,
        "op04_status_ref": op04_status_ref,
        "op04_revalidated_bodyfree": op04_map.get("dri_op04_revalidated_bodyfree") is True,
        "op04_ready_for_rows_and_ratings_revalidation": op04_ready,
        "rsr_op11_rows_rating_rows_intake_present": op11_present,
        "rsr_op11_contract_valid": op11_contract_valid,
        "rsr_op11_schema_version": op11_map.get("schema_version"),
        "rsr_op11_operation_step_ref": op11_map.get("operation_step_ref"),
        "rsr_op11_material_ref": _clean_ref(op11_map.get("material_id"), default="rsr_op11_material_missing", max_length=260),
        "rsr_op11_status_ref": op11_status_ref,
        "rsr_op11_next_required_step": op11_map.get("next_required_step"),
        "rsr_op11_sanitized_review_result_rows_accepted": op11_map.get("rsr_op11_sanitized_review_result_rows_accepted") is True,
        "rsr_op11_rating_rows_accepted": op11_map.get("rsr_op11_rating_rows_accepted") is True,
        "actual_review_rows_and_rating_rows_intaken_bodyfree": op11_map.get("actual_review_rows_and_rating_rows_intaken_bodyfree") is True,
        "question_need_observation_rows_required_next": op11_map.get("question_need_observation_rows_required_next") is True,
        "operation_receipt_ref": _clean_ref(op11_map.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220),
        "operation_receipt_ref_matches_op04": operation_receipt_matches,
        "reviewer_person_ref": _clean_ref(op11_map.get("reviewer_person_ref"), default="reviewer_person_ref_missing", max_length=220),
        "review_session_id_matches_op04": session_matches,
        "source_kind_ref": source_kind_ref,
        "rows_source_kind_is_actual_local_only_human_review_by_person": op11_map.get("rows_source_kind_is_actual_local_only_human_review_by_person") is True,
        "expected_review_row_count": expected_count,
        "sanitized_review_result_row_count": row_count,
        "rating_row_count": rating_count,
        "sanitized_review_result_row_count_is_24": row_count == expected_count and op11_map.get("sanitized_review_result_row_count_is_24") is True,
        "rating_row_count_is_24": rating_count == expected_count and op11_map.get("rating_row_count_is_24") is True,
        "sanitized_review_result_row_refs": list(op11_map.get("sanitized_review_result_row_refs") or []),
        "sanitized_review_result_row_ref_count": len(op11_map.get("sanitized_review_result_row_refs") or []),
        "rating_row_refs": list(op11_map.get("rating_row_refs") or []),
        "rating_row_ref_count": len(op11_map.get("rating_row_refs") or []),
        "case_ref_values": list(op11_map.get("case_ref_values") or []),
        "case_ref_count": _safe_int_value(op11_map.get("case_ref_count")),
        "case_ref_unique_count": _safe_int_value(op11_map.get("case_ref_unique_count")),
        "case_refs_match_between_sanitized_and_rating_rows": op11_map.get("case_refs_match_between_sanitized_and_rating_rows") is True,
        "sanitized_rows_bodyfree_only": op11_map.get("sanitized_rows_bodyfree_only") is True,
        "sanitized_rows_selection_only": op11_map.get("sanitized_rows_selection_only") is True,
        "sanitized_rows_have_actual_person_selection_only_provenance": op11_map.get("sanitized_rows_have_actual_person_selection_only_provenance") is True,
        "sanitized_rows_have_required_axis_scores": op11_map.get("sanitized_rows_have_required_axis_scores") is True,
        "sanitized_rows_have_allowed_verdict_refs": op11_map.get("sanitized_rows_have_allowed_verdict_refs") is True,
        "sanitized_rows_have_allowed_question_observation_refs": op11_map.get("sanitized_rows_have_allowed_question_observation_refs") is True,
        "sanitized_rows_have_no_body_or_question_or_path_or_hash": op11_map.get("sanitized_rows_have_no_body_or_question_or_path_or_hash") is True,
        "rating_rows_bodyfree_only": op11_map.get("rating_rows_bodyfree_only") is True,
        "rating_rows_from_sanitized_rows": op11_map.get("rating_rows_from_sanitized_rows") is True,
        "rating_rows_have_required_axis_scores": op11_map.get("rating_rows_have_required_axis_scores") is True,
        "rating_rows_have_no_body_or_question_or_path_or_hash": op11_map.get("rating_rows_have_no_body_or_question_or_path_or_hash") is True,
        "rows_operation_receipt_ref_matches": op11_map.get("rows_operation_receipt_ref_matches") is True,
        "rows_reviewer_person_ref_matches": op11_map.get("rows_reviewer_person_ref_matches") is True,
        "review_rows_forbidden_payload_key_path_refs": review_forbidden,
        "review_rows_forbidden_payload_key_path_count": len(review_forbidden),
        "review_rows_body_like_value_path_refs": review_body_like,
        "review_rows_body_like_value_path_count": len(review_body_like),
        "review_rows_promotion_claim_refs": review_promotion,
        "review_rows_promotion_claim_ref_count": len(review_promotion),
        "rating_rows_forbidden_payload_key_path_refs": rating_forbidden,
        "rating_rows_forbidden_payload_key_path_count": len(rating_forbidden),
        "rating_rows_body_like_value_path_refs": rating_body_like,
        "rating_rows_body_like_value_path_count": len(rating_body_like),
        "rating_rows_promotion_claim_refs": rating_promotion,
        "rating_rows_promotion_claim_ref_count": len(rating_promotion),
        "question_text_materialized": False,
        "draft_question_text_materialized": False,
        "p8_question_spec_created": False,
        "p8_question_design_started_here": False,
        "dri_op05_status_ref": status_ref,
        "rows_and_ratings_revalidation_status_ref": status_ref,
        "dri_op05_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP05_ALLOWED_STATUS_REFS),
        "dri_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP05_ALLOWED_STATUS_REFS),
        "dri_op05_rows_and_ratings_revalidated_bodyfree": ready,
        "dri_op05_wait_for_rows_and_ratings": waiting,
        "dri_op05_repair_required": repair,
        "dri_op05_body_leak_or_source_claim_blocked": blocked,
        "dri_op05_ready_for_question_need_rows_bridge_only_revalidation": ready,
        "dri_op05_reason_refs": reasons,
        "dri_op05_reason_ref_count": len(reasons),
        "dri_op05_blocker_refs": blockers,
        "dri_op05_blocker_ref_count": len(blockers),
        "actual_review_execution_claimed_by_dri_op05": False,
        "actual_review_evidence_completed_by_dri_op05": False,
        "dhr_actual_source_claim_confirmed_by_dri_op05": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op05": False,
        "dhr_op04_called_by_dri_op05": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op05": False,
        "dri_op05_does_not_create_sanitized_rows_or_rating_rows": True,
        "dri_op05_does_not_create_question_rows_or_disposal": True,
        "dri_op05_does_not_materialize_question_text_or_p8_spec": True,
        "dri_op05_does_not_execute_dhr_reintake": True,
        "dri_op05_does_not_call_dhr_op04": True,
        "dri_op05_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op05_does_not_execute_dmd_or_r52": True,
        "dri_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP05 body-free rows / ratings revalidation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP05")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP05_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP05_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP05")
    for field, count_field in (("sanitized_review_result_row_refs", "sanitized_review_result_row_ref_count"), ("rating_row_refs", "rating_row_ref_count"), ("review_rows_forbidden_payload_key_path_refs", "review_rows_forbidden_payload_key_path_count"), ("review_rows_body_like_value_path_refs", "review_rows_body_like_value_path_count"), ("review_rows_promotion_claim_refs", "review_rows_promotion_claim_ref_count"), ("rating_rows_forbidden_payload_key_path_refs", "rating_rows_forbidden_payload_key_path_count"), ("rating_rows_body_like_value_path_refs", "rating_rows_body_like_value_path_count"), ("rating_rows_promotion_claim_refs", "rating_rows_promotion_claim_ref_count"), ("dri_op05_allowed_status_refs", "dri_op05_allowed_status_ref_count"), ("dri_op05_reason_refs", "dri_op05_reason_ref_count"), ("dri_op05_blocker_refs", "dri_op05_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP05 {count_field} changed")
    if tuple(data.get("dri_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 allowed status refs changed")
    for key in ("dri_op05_does_not_create_sanitized_rows_or_rating_rows", "dri_op05_does_not_create_question_rows_or_disposal", "dri_op05_does_not_materialize_question_text_or_p8_spec", "dri_op05_does_not_execute_dhr_reintake", "dri_op05_does_not_call_dhr_op04", "dri_op05_does_not_materialize_dhr_op04_adapter_candidate", "dri_op05_does_not_execute_dmd_or_r52", "dri_op05_does_not_start_p5_p6_p8_p7_or_release", "dri_op05_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP05 required true boundary changed: {key}")
    for key in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here", "actual_review_execution_claimed_by_dri_op05", "actual_review_evidence_completed_by_dri_op05", "dhr_actual_source_claim_confirmed_by_dri_op05", "dhr_op04_adapter_candidate_materialized_by_dri_op05", "dhr_op04_called_by_dri_op05", "dhr_actual_source_claim_reintake_executed_by_dri_op05", "actual_sanitized_review_result_rows_materialized_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete_here", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP05 downstream/question flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP05_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 implemented/not-yet steps changed")
    status_ref = data.get("dri_op05_status_ref")
    if status_ref != data.get("rows_and_ratings_revalidation_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 status alias changed")
    status_flags = [
        data.get("dri_op05_rows_and_ratings_revalidated_bodyfree") is True,
        data.get("dri_op05_wait_for_rows_and_ratings") is True,
        data.get("dri_op05_repair_required") is True,
        data.get("dri_op05_body_leak_or_source_claim_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_ROWS_RATINGS_REVALIDATED_BODYFREE_REF:
        for key in ("op04_contract_valid", "op04_revalidated_bodyfree", "op04_ready_for_rows_and_ratings_revalidation", "rsr_op11_contract_valid", "rsr_op11_sanitized_review_result_rows_accepted", "rsr_op11_rating_rows_accepted", "actual_review_rows_and_rating_rows_intaken_bodyfree", "question_need_observation_rows_required_next", "operation_receipt_ref_matches_op04", "review_session_id_matches_op04", "rows_source_kind_is_actual_local_only_human_review_by_person", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24", "case_refs_match_between_sanitized_and_rating_rows", "sanitized_rows_bodyfree_only", "sanitized_rows_selection_only", "sanitized_rows_have_actual_person_selection_only_provenance", "sanitized_rows_have_required_axis_scores", "sanitized_rows_have_allowed_verdict_refs", "sanitized_rows_have_allowed_question_observation_refs", "sanitized_rows_have_no_body_or_question_or_path_or_hash", "rating_rows_bodyfree_only", "rating_rows_from_sanitized_rows", "rating_rows_have_required_axis_scores", "rating_rows_have_no_body_or_question_or_path_or_hash", "rows_operation_receipt_ref_matches", "rows_reviewer_person_ref_matches"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP05 ready branch required true changed: {key}")
        if data.get("sanitized_review_result_row_count") != data.get("expected_review_row_count") or data.get("rating_row_count") != data.get("expected_review_row_count"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 ready row count changed")
        if data.get("dri_op05_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_WAIT_FOR_ROWS_AND_RATINGS_REF:
        if data.get("dri_op05_wait_for_rows_and_ratings") is not True or data.get("dri_op05_ready_for_question_need_rows_bridge_only_revalidation") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 wait branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_ROWS_AND_RATINGS_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 wait next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF:
        if data.get("dri_op05_repair_required") is not True or not data.get("dri_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_ROWS_AND_RATINGS_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF:
        if data.get("dri_op05_body_leak_or_source_claim_blocked") is not True or not data.get("dri_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_ROWS_AND_RATINGS_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 blocked next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP05 status ref is not allowed")
    return True


# DRI-OP06/OP07 additions: question-need bridge rows and disposal/purge receipt revalidation.
P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REVALIDATED_BRIDGE_ONLY_REF: Final = (
    "DRI_OP06_QUESTION_NEED_ROWS_REVALIDATED_BRIDGE_ONLY"
)
P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF: Final = (
    "DRI_OP06_WAIT_FOR_QUESTION_NEED_ROWS"
)
P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF: Final = (
    "DRI_OP06_REPAIR_QUESTION_NEED_ROWS"
)
P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF: Final = (
    "DRI_OP06_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION"
)
P7_R54_AHR_POST_RSR16_DRI_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REVALIDATED_BRIDGE_ONLY_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_QUESTION_NEED_ROWS_REF: Final = (
    "wait_for_question_need_observation_rows_bodyfree_before_dri_op07"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_QUESTION_NEED_ROWS_REF: Final = (
    "repair_dri_op06_question_need_rows_before_disposal_purge_receipt_revalidation"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_QUESTION_NEED_ROWS_REF: Final = (
    "blocked_dri_op06_question_need_rows_question_text_or_p8_materialization"
)

P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REVALIDATED_BODYFREE_REF: Final = (
    "DRI_OP07_DISPOSAL_PURGE_RECEIPT_REVALIDATED_BODYFREE"
)
P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF: Final = (
    "DRI_OP07_WAIT_FOR_DISPOSAL_PURGE_RECEIPT"
)
P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF: Final = (
    "DRI_OP07_REPAIR_DISPOSAL_PURGE_RECEIPT"
)
P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF: Final = (
    "DRI_OP07_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION"
)
P7_R54_AHR_POST_RSR16_DRI_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REVALIDATED_BODYFREE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_PURGE_RECEIPT_REF: Final = (
    "wait_for_disposal_purge_receipt_bodyfree_before_dri_op08"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_PURGE_RECEIPT_REF: Final = (
    "repair_dri_op07_disposal_purge_receipt_before_final_scan"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_PURGE_RECEIPT_REF: Final = (
    "blocked_dri_op07_disposal_purge_receipt_body_leak_or_retention"
)

P7_R54_AHR_POST_RSR16_DRI_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_schema_version", "op05_material_ref", "op05_next_required_step", "op05_contract_valid", "op05_status_ref", "op05_rows_and_ratings_revalidated_bodyfree", "op05_ready_for_question_need_rows_bridge_only_revalidation",
    "rsr_op12_question_need_observation_rows_intake_present", "rsr_op12_contract_valid", "rsr_op12_schema_version", "rsr_op12_operation_step_ref", "rsr_op12_material_ref", "rsr_op12_status_ref", "rsr_op12_next_required_step",
    "rsr_op12_question_need_observation_rows_accepted", "question_need_observation_rows_accepted_by_rsr_op12", "actual_question_need_observation_rows_intaken_bodyfree", "disposal_purge_receipt_required_next",
    "operation_receipt_ref", "operation_receipt_ref_matches_op05", "reviewer_person_ref", "review_session_id_matches_op05", "source_kind_ref", "question_need_rows_source_kind_is_actual_local_only_human_review_by_person",
    "expected_question_need_observation_row_count", "question_need_observation_row_count", "question_need_observation_row_count_is_24", "question_need_observation_row_refs", "question_need_observation_row_ref_count", "source_sanitized_review_result_row_refs", "source_sanitized_review_result_row_ref_count", "source_rating_row_refs", "source_rating_row_ref_count", "case_ref_values", "case_ref_count", "case_ref_unique_count", "question_need_rows_match_op11_case_refs",
    "question_need_observation_rows_bodyfree_only", "question_need_observation_rows_from_review_rows_and_rating_rows", "question_need_observation_rows_have_actual_person_source", "question_need_observation_rows_have_allowed_classes", "question_need_observation_rows_material_only", "question_need_observation_rows_have_no_question_text_or_p8_spec", "p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only",
    "question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here", "p8_question_design_started_by_rows",
    "question_need_rows_forbidden_payload_key_path_refs", "question_need_rows_forbidden_payload_key_path_count", "question_need_rows_body_like_value_path_refs", "question_need_rows_body_like_value_path_count", "question_need_rows_promotion_claim_refs", "question_need_rows_promotion_claim_ref_count", "question_need_rows_source_claim_blocker_refs", "question_need_rows_source_claim_blocker_ref_count",
    "dri_op06_status_ref", "question_need_rows_bridge_only_revalidation_status_ref", "dri_op06_allowed_status_refs", "dri_op06_allowed_status_ref_count", "dri_op06_question_need_rows_revalidated_bridge_only", "dri_op06_wait_for_question_need_rows", "dri_op06_repair_required", "dri_op06_question_text_or_p8_materialization_blocked", "dri_op06_ready_for_disposal_purge_receipt_revalidation",
    "dri_op06_reason_refs", "dri_op06_reason_ref_count", "dri_op06_blocker_refs", "dri_op06_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op06", "actual_review_evidence_completed_by_dri_op06", "dhr_actual_source_claim_confirmed_by_dri_op06", "dhr_op04_adapter_candidate_materialized_by_dri_op06", "dhr_op04_called_by_dri_op06", "dhr_actual_source_claim_reintake_executed_by_dri_op06",
    "dri_op06_does_not_create_question_need_rows", "dri_op06_does_not_materialize_question_text_or_p8_spec", "dri_op06_does_not_execute_disposal_purge", "dri_op06_does_not_execute_dhr_reintake", "dri_op06_does_not_call_dhr_op04", "dri_op06_does_not_materialize_dhr_op04_adapter_candidate", "dri_op06_does_not_execute_dmd_or_r52", "dri_op06_does_not_start_p5_p6_p8_p7_or_release", "dri_op06_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RSR16_DRI_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_next_required_step", "op06_contract_valid", "op06_status_ref", "op06_question_need_rows_revalidated_bridge_only", "op06_ready_for_disposal_purge_receipt_revalidation",
    "rsr_op13_disposal_purge_receipt_intake_present", "rsr_op13_contract_valid", "rsr_op13_schema_version", "rsr_op13_operation_step_ref", "rsr_op13_material_ref", "rsr_op13_status_ref", "rsr_op13_next_required_step",
    "rsr_op13_disposal_purge_receipt_accepted", "disposal_purge_receipt_accepted_by_rsr_op13", "disposal_purge_receipt_accepted_without_purge_execution_by_helper", "final_no_leak_source_kind_validation_required_next",
    "operation_receipt_ref", "operation_receipt_ref_matches_op06", "packet_request_ref", "reviewer_person_ref", "review_session_id_matches_op06", "source_kind_ref", "disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person",
    "disposal_purge_receipt_ref", "disposal_purge_receipt_ref_present", "disposal_purge_receipt_purge_completed", "disposal_purge_receipt_body_free", "body_full_transient_material_reported_purged", "local_temp_material_reported_purged", "reviewer_working_form_body_reported_purged",
    "disposal_purge_receipt_body_full_packet_retained", "disposal_purge_receipt_local_temp_material_retained", "disposal_purge_receipt_reviewer_working_form_body_retained", "disposal_purge_receipt_external_export_performed", "disposal_purge_receipt_raw_input_included", "disposal_purge_receipt_comment_text_body_included", "disposal_purge_receipt_returned_surface_body_included", "disposal_purge_receipt_reviewer_free_text_included", "disposal_purge_receipt_reviewer_note_body_included", "disposal_purge_receipt_question_text_included", "disposal_purge_receipt_draft_question_text_included", "disposal_purge_receipt_answer_text_included", "disposal_purge_receipt_local_path_included", "disposal_purge_receipt_body_hash_included", "disposal_purge_receipt_terminal_output_body_included",
    "disposal_purge_receipt_forbidden_payload_key_path_refs", "disposal_purge_receipt_forbidden_payload_key_path_count", "disposal_purge_receipt_body_like_value_path_refs", "disposal_purge_receipt_body_like_value_path_count", "disposal_purge_receipt_promotion_claim_refs", "disposal_purge_receipt_promotion_claim_ref_count", "disposal_purge_receipt_retention_or_export_blocker_refs", "disposal_purge_receipt_retention_or_export_blocker_ref_count",
    "dri_op07_status_ref", "disposal_purge_receipt_revalidation_status_ref", "dri_op07_allowed_status_refs", "dri_op07_allowed_status_ref_count", "dri_op07_disposal_purge_receipt_revalidated_bodyfree", "dri_op07_wait_for_disposal_purge_receipt", "dri_op07_repair_required", "dri_op07_purge_receipt_body_leak_or_retention_blocked", "dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan",
    "dri_op07_reason_refs", "dri_op07_reason_ref_count", "dri_op07_blocker_refs", "dri_op07_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op07", "actual_review_evidence_completed_by_dri_op07", "dhr_actual_source_claim_confirmed_by_dri_op07", "dhr_op04_adapter_candidate_materialized_by_dri_op07", "dhr_op04_called_by_dri_op07", "dhr_actual_source_claim_reintake_executed_by_dri_op07", "disposal_purge_executed_by_dri_op07",
    "dri_op07_does_not_execute_disposal_purge", "dri_op07_does_not_perform_final_no_leak_validation", "dri_op07_does_not_complete_actual_evidence", "dri_op07_does_not_execute_dhr_reintake", "dri_op07_does_not_call_dhr_op04", "dri_op07_does_not_materialize_dhr_op04_adapter_candidate", "dri_op07_does_not_execute_dmd_or_r52", "dri_op07_does_not_start_p5_p6_p8_p7_or_release", "dri_op07_does_not_change_api_db_rn_runtime_response_key", "dri_op07_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _rsr_op12_contract_valid(rsr_op12: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op12, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(rsr_op12) is True
    except ValueError:
        return False


def _rsr_op13_contract_valid(rsr_op13: Mapping[str, Any] | None) -> bool:
    if not isinstance(rsr_op13, Mapping):
        return False
    try:
        return rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(rsr_op13) is True
    except ValueError:
        return False


def _op06_status_reason_blocker_next(
    *,
    op05_status_ref: str,
    op05_contract_valid: bool,
    op05_ready: bool,
    op12_present: bool,
    op12_contract_valid: bool,
    op12_status_ref: str,
    op12_accepted: bool,
    question_rows_intaken_bodyfree: bool,
    disposal_purge_required_next: bool,
    source_kind_actual: bool,
    row_count_ok: bool,
    case_refs_match: bool,
    bridge_material_only: bool,
    no_question_or_p8: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    source_claim_blockers: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if not op05_contract_valid or op05_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_REPAIR_ROWS_AND_RATINGS_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF,
            ["repair_dri_op05_rows_and_ratings_before_question_need_rows_revalidation"],
            ["dri_op05_rows_and_ratings_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_QUESTION_NEED_ROWS_REF,
        )
    if op05_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP05_STATUS_BLOCKED_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF,
            ["blocked_because_dri_op05_rows_are_already_bodyfree_or_source_claim_blocked"],
            ["dri_op05_bodyfree_leak_or_source_claim_blocked"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_QUESTION_NEED_ROWS_REF,
        )
    if not op05_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF,
            ["wait_for_dri_op05_rows_and_ratings_ready_before_question_need_rows_revalidation"],
            ["dri_op05_rows_and_ratings_not_ready"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_QUESTION_NEED_ROWS_REF,
        )
    if not op12_present or op12_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF,
            ["wait_for_supplied_rsr_op12_question_need_observation_rows_intake"],
            ["question_need_observation_rows_intake_missing_or_waiting"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_QUESTION_NEED_ROWS_REF,
        )
    if (
        forbidden_paths
        or body_like_paths
        or promotion_claims
        or source_claim_blockers
        or op12_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF
        or not source_kind_actual
        or not no_question_or_p8
    ):
        if forbidden_paths:
            blockers.append("dri_op06_forbidden_payload_key_detected")
        if body_like_paths:
            blockers.append("dri_op06_body_like_value_detected")
        if promotion_claims:
            blockers.append("dri_op06_promotion_claim_detected")
        if source_claim_blockers:
            blockers.extend(source_claim_blockers)
        if op12_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF:
            blockers.append("rsr_op12_body_leak_or_question_materialization_blocked")
        if not source_kind_actual:
            blockers.append("question_need_rows_source_kind_not_actual_local_only_human_review_by_person")
        if not no_question_or_p8:
            blockers.append("question_need_rows_question_text_or_p8_materialization_detected")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF,
            ["question_need_rows_bodyfree_or_p8_materialization_boundary_failed_before_purge_receipt_revalidation"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_QUESTION_NEED_ROWS_REF,
        )
    if not op12_contract_valid or op12_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF,
            ["repair_rsr_op12_question_need_observation_rows_before_dri_op07"],
            ["rsr_op12_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_QUESTION_NEED_ROWS_REF,
        )
    if not (op12_accepted and question_rows_intaken_bodyfree and disposal_purge_required_next and row_count_ok and case_refs_match and bridge_material_only):
        blockers.extend(
            ref
            for ref, ok in (
                ("question_need_rows_not_accepted_by_rsr_op12", op12_accepted),
                ("question_need_rows_not_intaken_bodyfree", question_rows_intaken_bodyfree),
                ("disposal_purge_receipt_not_required_next", disposal_purge_required_next),
                ("question_need_observation_row_count_not_24", row_count_ok),
                ("question_need_rows_do_not_match_review_rows_and_rating_rows", case_refs_match),
                ("question_need_rows_not_bridge_material_only", bridge_material_only),
            )
            if not ok
        )
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF,
            ["repair_question_need_rows_acceptance_count_or_bridge_material_flags_before_dri_op07"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_QUESTION_NEED_ROWS_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REVALIDATED_BRIDGE_ONLY_REF,
        ["question_need_rows_revalidated_as_p7_p8_bridge_material_only_without_question_text_or_p8_start"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation(
    *,
    dri_op05_sanitized_rows_rating_rows_revalidation: Mapping[str, Any] | None = None,
    sanitized_rows_rating_rows_revalidation: Mapping[str, Any] | None = None,
    rsr_op12_question_need_observation_rows_intake: Mapping[str, Any] | None = None,
    question_need_observation_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP06 body-free question-need bridge-only rows revalidation material."""

    op05 = dri_op05_sanitized_rows_rating_rows_revalidation if dri_op05_sanitized_rows_rating_rows_revalidation is not None else sanitized_rows_rating_rows_revalidation
    op12 = rsr_op12_question_need_observation_rows_intake if rsr_op12_question_need_observation_rows_intake is not None else question_need_observation_rows_intake
    op05_map = op05 if isinstance(op05, Mapping) else {}
    op12_map = op12 if isinstance(op12, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op12_map.get("review_session_id") or op05_map.get("review_session_id")))
    try:
        op05_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract(op05_map) is True
    except ValueError:
        op05_contract_valid = False
    op12_contract_valid = _rsr_op12_contract_valid(op12)
    op12_present = isinstance(op12, Mapping)
    op05_status_ref = _clean_ref(op05_map.get("dri_op05_status_ref"), default="dri_op05_status_missing", max_length=260)
    op12_status_ref = _clean_ref(op12_map.get("rsr_op12_status_ref"), default="rsr_op12_status_missing", max_length=260)
    op05_ready = bool(op05_map.get("dri_op05_rows_and_ratings_revalidated_bodyfree") is True and op05_map.get("dri_op05_ready_for_question_need_rows_bridge_only_revalidation") is True)
    question_materialization_promotions = [
        f"rsr_op12_question_need_observation_rows_intake.{key}"
        for key in (
            "question_text_materialized",
            "draft_question_text_materialized",
            "p8_question_spec_created",
            "p8_question_design_started_here",
            "p8_question_design_started_by_rows",
        )
        if op12_map.get(key) is True
    ]
    required_false_flag_promotions = [
        f"rsr_op12_question_need_observation_rows_intake.{key}"
        for key in P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS
        if op12_map.get(key) is True
    ]
    forbidden_paths = _dedupe_clean_refs(
        list(_scan_forbidden_payload_key_paths(op12, path="rsr_op12_question_need_observation_rows_intake") if op12_present else [])
        + list(op12_map.get("question_need_observation_rows_forbidden_payload_key_path_refs") or []),
        max_length=320,
    )
    body_like_paths = _dedupe_clean_refs(
        list(_scan_body_like_value_paths(op12, path="rsr_op12_question_need_observation_rows_intake") if op12_present else [])
        + list(op12_map.get("question_need_observation_rows_body_like_value_path_refs") or []),
        max_length=320,
    )
    promotion_claims = _dedupe_clean_refs(
        list(_scan_promotion_claim_refs(op12, path="rsr_op12_question_need_observation_rows_intake") if op12_present else [])
        + list(op12_map.get("question_need_observation_rows_promotion_claim_refs") or [])
        + question_materialization_promotions
        + required_false_flag_promotions,
        max_length=320,
    )
    expected_count = getattr(rsr, "P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT", 24)
    row_count = _safe_int_value(op12_map.get("question_need_observation_row_count"))
    operation_receipt_ref = _clean_ref(op12_map.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220)
    op05_operation_receipt_ref = _clean_ref(op05_map.get("operation_receipt_ref"), default="op05_operation_receipt_ref_missing", max_length=220)
    operation_receipt_matches = bool(operation_receipt_ref and operation_receipt_ref == op05_operation_receipt_ref)
    session_matches = bool(op12_map.get("review_session_id") == op05_map.get("review_session_id") == session_id)
    actual_source = bool(op12_map.get("question_need_observation_rows_have_actual_person_source") is True)
    source_kind_ref = rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF if actual_source else "question_need_rows_source_kind_missing_or_invalid"
    bridge_material_only = bool(
        op12_map.get("p7_p8_bridge_material_only") is True
        and op12_map.get("p8_design_material_candidate_only") is True
        and op12_map.get("question_observation_material_only") is True
        and op12_map.get("question_need_observation_rows_material_only") is True
    )
    no_question_or_p8 = bool(
        op12_map.get("question_text_materialized") is not True
        and op12_map.get("draft_question_text_materialized") is not True
        and op12_map.get("p8_question_spec_created") is not True
        and op12_map.get("p8_question_design_started_here") is not True
        and op12_map.get("p8_question_design_started_by_rows") is not True
        and op12_map.get("question_need_observation_rows_have_no_question_text_or_p8_spec") is True
    )
    source_claim_blockers = _dedupe_clean_refs(
        [ref for ref, ok in (("question_need_rows_source_kind_not_actual_local_only_human_review_by_person", actual_source),) if not ok],
        max_length=320,
    )
    status_ref, reasons, blockers, next_required_step = _op06_status_reason_blocker_next(
        op05_status_ref=op05_status_ref,
        op05_contract_valid=op05_contract_valid,
        op05_ready=op05_ready,
        op12_present=op12_present,
        op12_contract_valid=op12_contract_valid,
        op12_status_ref=op12_status_ref,
        op12_accepted=bool(op12_map.get("rsr_op12_question_need_observation_rows_accepted") is True and op12_map.get("question_need_observation_rows_accepted_by_rsr_op12") is True),
        question_rows_intaken_bodyfree=op12_map.get("actual_question_need_observation_rows_intaken_bodyfree") is True,
        disposal_purge_required_next=op12_map.get("disposal_purge_receipt_required_next") is True,
        source_kind_actual=actual_source,
        row_count_ok=row_count == expected_count and op12_map.get("question_need_observation_row_count_is_24") is True,
        case_refs_match=op12_map.get("question_need_rows_match_op11_case_refs") is True,
        bridge_material_only=bridge_material_only,
        no_question_or_p8=no_question_or_p8,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        source_claim_blockers=source_claim_blockers,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REVALIDATED_BRIDGE_ONLY_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": op05_map.get("schema_version"),
        "op05_material_ref": _clean_ref(op05_map.get("material_id"), default="dri_op05_material_missing", max_length=260),
        "op05_next_required_step": op05_map.get("next_required_step"),
        "op05_contract_valid": op05_contract_valid,
        "op05_status_ref": op05_status_ref,
        "op05_rows_and_ratings_revalidated_bodyfree": op05_map.get("dri_op05_rows_and_ratings_revalidated_bodyfree") is True,
        "op05_ready_for_question_need_rows_bridge_only_revalidation": op05_ready,
        "rsr_op12_question_need_observation_rows_intake_present": op12_present,
        "rsr_op12_contract_valid": op12_contract_valid,
        "rsr_op12_schema_version": op12_map.get("schema_version"),
        "rsr_op12_operation_step_ref": op12_map.get("operation_step_ref"),
        "rsr_op12_material_ref": _clean_ref(op12_map.get("material_id"), default="rsr_op12_material_missing", max_length=260),
        "rsr_op12_status_ref": op12_status_ref,
        "rsr_op12_next_required_step": op12_map.get("next_required_step"),
        "rsr_op12_question_need_observation_rows_accepted": op12_map.get("rsr_op12_question_need_observation_rows_accepted") is True,
        "question_need_observation_rows_accepted_by_rsr_op12": op12_map.get("question_need_observation_rows_accepted_by_rsr_op12") is True,
        "actual_question_need_observation_rows_intaken_bodyfree": op12_map.get("actual_question_need_observation_rows_intaken_bodyfree") is True,
        "disposal_purge_receipt_required_next": op12_map.get("disposal_purge_receipt_required_next") is True,
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_ref_matches_op05": operation_receipt_matches,
        "reviewer_person_ref": _clean_ref(op12_map.get("reviewer_person_ref"), default="reviewer_person_ref_missing", max_length=220),
        "review_session_id_matches_op05": session_matches,
        "source_kind_ref": source_kind_ref,
        "question_need_rows_source_kind_is_actual_local_only_human_review_by_person": actual_source,
        "expected_question_need_observation_row_count": expected_count,
        "question_need_observation_row_count": row_count,
        "question_need_observation_row_count_is_24": row_count == expected_count and op12_map.get("question_need_observation_row_count_is_24") is True,
        "question_need_observation_row_refs": list(op12_map.get("question_need_observation_row_refs") or []),
        "question_need_observation_row_ref_count": len(op12_map.get("question_need_observation_row_refs") or []),
        "source_sanitized_review_result_row_refs": list(op12_map.get("source_sanitized_review_result_row_refs") or []),
        "source_sanitized_review_result_row_ref_count": len(op12_map.get("source_sanitized_review_result_row_refs") or []),
        "source_rating_row_refs": list(op12_map.get("source_rating_row_refs") or []),
        "source_rating_row_ref_count": len(op12_map.get("source_rating_row_refs") or []),
        "case_ref_values": list(op12_map.get("case_ref_values") or []),
        "case_ref_count": _safe_int_value(op12_map.get("case_ref_count")),
        "case_ref_unique_count": _safe_int_value(op12_map.get("case_ref_unique_count")),
        "question_need_rows_match_op11_case_refs": op12_map.get("question_need_rows_match_op11_case_refs") is True,
        "question_need_observation_rows_bodyfree_only": op12_map.get("question_need_observation_rows_bodyfree_only") is True,
        "question_need_observation_rows_from_review_rows_and_rating_rows": op12_map.get("question_need_observation_rows_from_review_rows_and_rating_rows") is True,
        "question_need_observation_rows_have_actual_person_source": actual_source,
        "question_need_observation_rows_have_allowed_classes": op12_map.get("question_need_observation_rows_have_allowed_classes") is True,
        "question_need_observation_rows_material_only": op12_map.get("question_need_observation_rows_material_only") is True,
        "question_need_observation_rows_have_no_question_text_or_p8_spec": op12_map.get("question_need_observation_rows_have_no_question_text_or_p8_spec") is True,
        "p7_p8_bridge_material_only": op12_map.get("p7_p8_bridge_material_only") is True,
        "p8_design_material_candidate_only": op12_map.get("p8_design_material_candidate_only") is True,
        "question_observation_material_only": op12_map.get("question_observation_material_only") is True,
        "question_text_materialized": False,
        "draft_question_text_materialized": False,
        "p8_question_spec_created": False,
        "p8_question_design_started_here": False,
        "p8_question_design_started_by_rows": False,
        "question_need_rows_forbidden_payload_key_path_refs": forbidden_paths,
        "question_need_rows_forbidden_payload_key_path_count": len(forbidden_paths),
        "question_need_rows_body_like_value_path_refs": body_like_paths,
        "question_need_rows_body_like_value_path_count": len(body_like_paths),
        "question_need_rows_promotion_claim_refs": promotion_claims,
        "question_need_rows_promotion_claim_ref_count": len(promotion_claims),
        "question_need_rows_source_claim_blocker_refs": source_claim_blockers,
        "question_need_rows_source_claim_blocker_ref_count": len(source_claim_blockers),
        "dri_op06_status_ref": status_ref,
        "question_need_rows_bridge_only_revalidation_status_ref": status_ref,
        "dri_op06_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP06_ALLOWED_STATUS_REFS),
        "dri_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP06_ALLOWED_STATUS_REFS),
        "dri_op06_question_need_rows_revalidated_bridge_only": ready,
        "dri_op06_wait_for_question_need_rows": waiting,
        "dri_op06_repair_required": repair,
        "dri_op06_question_text_or_p8_materialization_blocked": blocked,
        "dri_op06_ready_for_disposal_purge_receipt_revalidation": ready,
        "dri_op06_reason_refs": reasons,
        "dri_op06_reason_ref_count": len(reasons),
        "dri_op06_blocker_refs": blockers,
        "dri_op06_blocker_ref_count": len(blockers),
        "actual_review_execution_claimed_by_dri_op06": False,
        "actual_review_evidence_completed_by_dri_op06": False,
        "dhr_actual_source_claim_confirmed_by_dri_op06": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op06": False,
        "dhr_op04_called_by_dri_op06": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op06": False,
        "dri_op06_does_not_create_question_need_rows": True,
        "dri_op06_does_not_materialize_question_text_or_p8_spec": True,
        "dri_op06_does_not_execute_disposal_purge": True,
        "dri_op06_does_not_execute_dhr_reintake": True,
        "dri_op06_does_not_call_dhr_op04": True,
        "dri_op06_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op06_does_not_execute_dmd_or_r52": True,
        "dri_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP06 body-free question-need bridge-only rows revalidation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP06")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP06_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP06_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP06")
    for field, count_field in (("question_need_observation_row_refs", "question_need_observation_row_ref_count"), ("source_sanitized_review_result_row_refs", "source_sanitized_review_result_row_ref_count"), ("source_rating_row_refs", "source_rating_row_ref_count"), ("question_need_rows_forbidden_payload_key_path_refs", "question_need_rows_forbidden_payload_key_path_count"), ("question_need_rows_body_like_value_path_refs", "question_need_rows_body_like_value_path_count"), ("question_need_rows_promotion_claim_refs", "question_need_rows_promotion_claim_ref_count"), ("question_need_rows_source_claim_blocker_refs", "question_need_rows_source_claim_blocker_ref_count"), ("dri_op06_allowed_status_refs", "dri_op06_allowed_status_ref_count"), ("dri_op06_reason_refs", "dri_op06_reason_ref_count"), ("dri_op06_blocker_refs", "dri_op06_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP06 {count_field} changed")
    if tuple(data.get("dri_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 allowed status refs changed")
    for key in ("dri_op06_does_not_create_question_need_rows", "dri_op06_does_not_materialize_question_text_or_p8_spec", "dri_op06_does_not_execute_disposal_purge", "dri_op06_does_not_execute_dhr_reintake", "dri_op06_does_not_call_dhr_op04", "dri_op06_does_not_materialize_dhr_op04_adapter_candidate", "dri_op06_does_not_execute_dmd_or_r52", "dri_op06_does_not_start_p5_p6_p8_p7_or_release", "dri_op06_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP06 required true boundary changed: {key}")
    for key in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here", "p8_question_design_started_by_rows", "actual_review_execution_claimed_by_dri_op06", "actual_review_evidence_completed_by_dri_op06", "dhr_actual_source_claim_confirmed_by_dri_op06", "dhr_op04_adapter_candidate_materialized_by_dri_op06", "dhr_op04_called_by_dri_op06", "dhr_actual_source_claim_reintake_executed_by_dri_op06", "actual_question_need_observation_rows_materialized_here", "actual_disposal_purge_executed_here", "actual_review_evidence_complete_here", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP06 downstream/question flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP06_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 implemented/not-yet steps changed")
    status_ref = data.get("dri_op06_status_ref")
    if status_ref != data.get("question_need_rows_bridge_only_revalidation_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 status alias changed")
    status_flags = [
        data.get("dri_op06_question_need_rows_revalidated_bridge_only") is True,
        data.get("dri_op06_wait_for_question_need_rows") is True,
        data.get("dri_op06_repair_required") is True,
        data.get("dri_op06_question_text_or_p8_materialization_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REVALIDATED_BRIDGE_ONLY_REF:
        for key in ("op05_contract_valid", "op05_rows_and_ratings_revalidated_bodyfree", "op05_ready_for_question_need_rows_bridge_only_revalidation", "rsr_op12_contract_valid", "rsr_op12_question_need_observation_rows_accepted", "question_need_observation_rows_accepted_by_rsr_op12", "actual_question_need_observation_rows_intaken_bodyfree", "disposal_purge_receipt_required_next", "operation_receipt_ref_matches_op05", "review_session_id_matches_op05", "question_need_rows_source_kind_is_actual_local_only_human_review_by_person", "question_need_observation_row_count_is_24", "question_need_rows_match_op11_case_refs", "question_need_observation_rows_bodyfree_only", "question_need_observation_rows_from_review_rows_and_rating_rows", "question_need_observation_rows_have_actual_person_source", "question_need_observation_rows_have_allowed_classes", "question_need_observation_rows_material_only", "question_need_observation_rows_have_no_question_text_or_p8_spec", "p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP06 ready branch required true changed: {key}")
        if data.get("question_need_observation_row_count") != data.get("expected_question_need_observation_row_count"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 ready row count changed")
        if data.get("dri_op06_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_WAIT_FOR_QUESTION_NEED_ROWS_REF:
        if data.get("dri_op06_wait_for_question_need_rows") is not True or data.get("dri_op06_ready_for_disposal_purge_receipt_revalidation") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 wait branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_QUESTION_NEED_ROWS_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 wait next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF:
        if data.get("dri_op06_repair_required") is not True or not data.get("dri_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_QUESTION_NEED_ROWS_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF:
        if data.get("dri_op06_question_text_or_p8_materialization_blocked") is not True or not data.get("dri_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_QUESTION_NEED_ROWS_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 blocked next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP06 status ref is not allowed")
    return True


def _op07_status_reason_blocker_next(
    *,
    op06_status_ref: str,
    op06_contract_valid: bool,
    op06_ready: bool,
    op13_present: bool,
    op13_contract_valid: bool,
    op13_status_ref: str,
    op13_accepted: bool,
    purge_completed: bool,
    purge_body_free: bool,
    source_kind_actual: bool,
    receipt_ref_present: bool,
    refs_match: bool,
    no_retention: bool,
    no_helper_purge_execution: bool,
    final_validation_required_next: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    retention_or_export_blockers: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if not op06_contract_valid or op06_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_REPAIR_QUESTION_NEED_ROWS_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF,
            ["repair_dri_op06_question_need_rows_before_purge_receipt_revalidation"],
            ["dri_op06_question_need_rows_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_PURGE_RECEIPT_REF,
        )
    if op06_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP06_STATUS_BLOCKED_QUESTION_TEXT_OR_P8_MATERIALIZATION_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF,
            ["blocked_because_dri_op06_question_need_rows_are_already_blocked"],
            ["dri_op06_question_text_or_p8_materialization_blocked"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_PURGE_RECEIPT_REF,
        )
    if not op06_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF,
            ["wait_for_dri_op06_question_need_rows_ready_before_purge_receipt_revalidation"],
            ["dri_op06_question_need_rows_not_ready"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_PURGE_RECEIPT_REF,
        )
    if not op13_present or op13_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF,
            ["wait_for_supplied_rsr_op13_disposal_purge_receipt_intake"],
            ["disposal_purge_receipt_intake_missing_or_waiting"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_PURGE_RECEIPT_REF,
        )
    if (
        forbidden_paths
        or body_like_paths
        or promotion_claims
        or retention_or_export_blockers
        or op13_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF
        or not source_kind_actual
        or not no_retention
        or not no_helper_purge_execution
    ):
        if forbidden_paths:
            blockers.append("dri_op07_forbidden_payload_key_detected")
        if body_like_paths:
            blockers.append("dri_op07_body_like_value_detected")
        if promotion_claims:
            blockers.append("dri_op07_promotion_claim_detected")
        if retention_or_export_blockers:
            blockers.extend(retention_or_export_blockers)
        if op13_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF:
            blockers.append("rsr_op13_body_leak_or_retention_blocked")
        if not source_kind_actual:
            blockers.append("disposal_purge_receipt_source_kind_not_actual_local_only_human_review_by_person")
        if not no_retention:
            blockers.append("disposal_purge_receipt_retention_or_export_flag_true")
        if not no_helper_purge_execution:
            blockers.append("dri_op07_or_rsr_op13_helper_purge_execution_claim_detected")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF,
            ["disposal_purge_receipt_bodyfree_retention_or_promotion_boundary_failed_before_final_scan"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_PURGE_RECEIPT_REF,
        )
    if not op13_contract_valid or op13_status_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF,
            ["repair_rsr_op13_disposal_purge_receipt_before_dri_op08"],
            ["rsr_op13_contract_or_status_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_PURGE_RECEIPT_REF,
        )
    if not (op13_accepted and receipt_ref_present and refs_match and purge_completed and purge_body_free and final_validation_required_next):
        blockers.extend(
            ref
            for ref, ok in (
                ("disposal_purge_receipt_not_accepted_by_rsr_op13", op13_accepted),
                ("disposal_purge_receipt_ref_missing", receipt_ref_present),
                ("disposal_purge_receipt_refs_do_not_match_op06", refs_match),
                ("disposal_purge_receipt_purge_completed_not_true", purge_completed),
                ("disposal_purge_receipt_body_free_not_true", purge_body_free),
                ("final_no_leak_source_kind_validation_not_required_next", final_validation_required_next),
            )
            if not ok
        )
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF,
            ["repair_disposal_purge_receipt_acceptance_refs_or_purge_completion_flags_before_dri_op08"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_PURGE_RECEIPT_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REVALIDATED_BODYFREE_REF,
        ["disposal_purge_receipt_revalidated_bodyfree_without_helper_purge_execution_or_evidence_completion"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation(
    *,
    dri_op06_question_need_rows_bridge_only_revalidation: Mapping[str, Any] | None = None,
    question_need_rows_bridge_only_revalidation: Mapping[str, Any] | None = None,
    rsr_op13_disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP07 body-free disposal / purge receipt revalidation material."""

    op06 = dri_op06_question_need_rows_bridge_only_revalidation if dri_op06_question_need_rows_bridge_only_revalidation is not None else question_need_rows_bridge_only_revalidation
    op13 = rsr_op13_disposal_purge_receipt_intake if rsr_op13_disposal_purge_receipt_intake is not None else disposal_purge_receipt_intake
    op06_map = op06 if isinstance(op06, Mapping) else {}
    op13_map = op13 if isinstance(op13, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op13_map.get("review_session_id") or op06_map.get("review_session_id")))
    try:
        op06_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract(op06_map) is True
    except ValueError:
        op06_contract_valid = False
    op13_contract_valid = _rsr_op13_contract_valid(op13)
    op13_present = isinstance(op13, Mapping)
    op06_status_ref = _clean_ref(op06_map.get("dri_op06_status_ref"), default="dri_op06_status_missing", max_length=260)
    op13_status_ref = _clean_ref(op13_map.get("rsr_op13_status_ref"), default="rsr_op13_status_missing", max_length=260)
    op06_ready = bool(op06_map.get("dri_op06_question_need_rows_revalidated_bridge_only") is True and op06_map.get("dri_op06_ready_for_disposal_purge_receipt_revalidation") is True)
    retention_true_fields = [
        f"rsr_op13_disposal_purge_receipt_intake.{key}"
        for key in (
            "disposal_purge_receipt_body_full_packet_retained",
            "disposal_purge_receipt_local_temp_material_retained",
            "disposal_purge_receipt_reviewer_working_form_body_retained",
            "disposal_purge_receipt_external_export_performed",
            "disposal_purge_receipt_raw_input_included",
            "disposal_purge_receipt_comment_text_body_included",
            "disposal_purge_receipt_returned_surface_body_included",
            "disposal_purge_receipt_reviewer_free_text_included",
            "disposal_purge_receipt_reviewer_note_body_included",
            "disposal_purge_receipt_question_text_included",
            "disposal_purge_receipt_draft_question_text_included",
            "disposal_purge_receipt_answer_text_included",
            "disposal_purge_receipt_local_path_included",
            "disposal_purge_receipt_body_hash_included",
            "disposal_purge_receipt_terminal_output_body_included",
        )
        if op13_map.get(key) is True
    ]
    required_false_flag_promotions = [
        f"rsr_op13_disposal_purge_receipt_intake.{key}"
        for key in P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS
        if op13_map.get(key) is True
    ]
    forbidden_paths = _dedupe_clean_refs(
        list(_scan_forbidden_payload_key_paths(op13, path="rsr_op13_disposal_purge_receipt_intake") if op13_present else [])
        + list(op13_map.get("disposal_purge_receipt_forbidden_payload_key_path_refs") or []),
        max_length=320,
    )
    body_like_paths = _dedupe_clean_refs(
        list(_scan_body_like_value_paths(op13, path="rsr_op13_disposal_purge_receipt_intake") if op13_present else [])
        + list(op13_map.get("disposal_purge_receipt_body_like_value_path_refs") or []),
        max_length=320,
    )
    promotion_claims = _dedupe_clean_refs(
        list(_scan_promotion_claim_refs(op13, path="rsr_op13_disposal_purge_receipt_intake") if op13_present else [])
        + list(op13_map.get("disposal_purge_receipt_promotion_claim_refs") or [])
        + required_false_flag_promotions,
        max_length=320,
    )
    retention_or_export_blockers = _dedupe_clean_refs(
        list(op13_map.get("disposal_purge_receipt_retention_or_export_blocker_refs") or []) + retention_true_fields,
        max_length=320,
    )
    operation_receipt_ref = _clean_ref(op13_map.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220)
    op06_operation_receipt_ref = _clean_ref(op06_map.get("operation_receipt_ref"), default="op06_operation_receipt_ref_missing", max_length=220)
    operation_receipt_matches = bool(operation_receipt_ref and operation_receipt_ref == op06_operation_receipt_ref)
    session_matches = bool(op13_map.get("review_session_id") == op06_map.get("review_session_id") == session_id)
    source_kind_ref = _clean_ref(op13_map.get("disposal_purge_receipt_source_kind_ref") or op13_map.get("source_kind_ref"), default="disposal_purge_receipt_source_kind_missing", max_length=220)
    source_kind_actual = bool(source_kind_ref == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF and op13_map.get("disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person") is True)
    no_retention = not any(op13_map.get(key) is True for key in (
        "disposal_purge_receipt_body_full_packet_retained",
        "disposal_purge_receipt_local_temp_material_retained",
        "disposal_purge_receipt_reviewer_working_form_body_retained",
        "disposal_purge_receipt_external_export_performed",
        "disposal_purge_receipt_raw_input_included",
        "disposal_purge_receipt_comment_text_body_included",
        "disposal_purge_receipt_returned_surface_body_included",
        "disposal_purge_receipt_reviewer_free_text_included",
        "disposal_purge_receipt_reviewer_note_body_included",
        "disposal_purge_receipt_question_text_included",
        "disposal_purge_receipt_draft_question_text_included",
        "disposal_purge_receipt_answer_text_included",
        "disposal_purge_receipt_local_path_included",
        "disposal_purge_receipt_body_hash_included",
        "disposal_purge_receipt_terminal_output_body_included",
    ))
    no_helper_purge_execution = bool(op13_map.get("helper_executes_disposal_purge") is False and op13_map.get("actual_disposal_purge_executed_here_by_helper") is False)
    refs_match = bool(operation_receipt_matches and session_matches and op13_map.get("disposal_purge_receipt_review_session_id_matches") is True and op13_map.get("disposal_purge_receipt_operation_receipt_ref_matches") is True and op13_map.get("disposal_purge_receipt_packet_request_ref_matches") is True)
    status_ref, reasons, blockers, next_required_step = _op07_status_reason_blocker_next(
        op06_status_ref=op06_status_ref,
        op06_contract_valid=op06_contract_valid,
        op06_ready=op06_ready,
        op13_present=op13_present,
        op13_contract_valid=op13_contract_valid,
        op13_status_ref=op13_status_ref,
        op13_accepted=bool(op13_map.get("rsr_op13_disposal_purge_receipt_accepted") is True and op13_map.get("disposal_purge_receipt_accepted_by_rsr_op13") is True),
        purge_completed=op13_map.get("disposal_purge_receipt_purge_completed") is True,
        purge_body_free=op13_map.get("disposal_purge_receipt_body_free") is True,
        source_kind_actual=source_kind_actual,
        receipt_ref_present=bool(_clean_ref(op13_map.get("disposal_purge_receipt_ref"), default="", max_length=220)),
        refs_match=refs_match,
        no_retention=no_retention,
        no_helper_purge_execution=no_helper_purge_execution,
        final_validation_required_next=op13_map.get("final_no_leak_source_kind_validation_required_next") is True,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        retention_or_export_blockers=retention_or_export_blockers,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REVALIDATED_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": op06_map.get("schema_version"),
        "op06_material_ref": _clean_ref(op06_map.get("material_id"), default="dri_op06_material_missing", max_length=260),
        "op06_next_required_step": op06_map.get("next_required_step"),
        "op06_contract_valid": op06_contract_valid,
        "op06_status_ref": op06_status_ref,
        "op06_question_need_rows_revalidated_bridge_only": op06_map.get("dri_op06_question_need_rows_revalidated_bridge_only") is True,
        "op06_ready_for_disposal_purge_receipt_revalidation": op06_ready,
        "rsr_op13_disposal_purge_receipt_intake_present": op13_present,
        "rsr_op13_contract_valid": op13_contract_valid,
        "rsr_op13_schema_version": op13_map.get("schema_version"),
        "rsr_op13_operation_step_ref": op13_map.get("operation_step_ref"),
        "rsr_op13_material_ref": _clean_ref(op13_map.get("material_id"), default="rsr_op13_material_missing", max_length=260),
        "rsr_op13_status_ref": op13_status_ref,
        "rsr_op13_next_required_step": op13_map.get("next_required_step"),
        "rsr_op13_disposal_purge_receipt_accepted": op13_map.get("rsr_op13_disposal_purge_receipt_accepted") is True,
        "disposal_purge_receipt_accepted_by_rsr_op13": op13_map.get("disposal_purge_receipt_accepted_by_rsr_op13") is True,
        "disposal_purge_receipt_accepted_without_purge_execution_by_helper": op13_map.get("disposal_purge_receipt_accepted_without_purge_execution_by_helper") is True,
        "final_no_leak_source_kind_validation_required_next": op13_map.get("final_no_leak_source_kind_validation_required_next") is True,
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_ref_matches_op06": operation_receipt_matches,
        "packet_request_ref": _clean_ref(op13_map.get("packet_request_ref"), default="packet_request_ref_missing", max_length=220),
        "reviewer_person_ref": _clean_ref(op13_map.get("reviewer_person_ref"), default="reviewer_person_ref_missing", max_length=220),
        "review_session_id_matches_op06": session_matches,
        "source_kind_ref": source_kind_ref,
        "disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person": source_kind_actual,
        "disposal_purge_receipt_ref": _clean_ref(op13_map.get("disposal_purge_receipt_ref"), default="disposal_purge_receipt_ref_missing", max_length=220),
        "disposal_purge_receipt_ref_present": bool(_clean_ref(op13_map.get("disposal_purge_receipt_ref"), default="", max_length=220)),
        "disposal_purge_receipt_purge_completed": op13_map.get("disposal_purge_receipt_purge_completed") is True,
        "disposal_purge_receipt_body_free": op13_map.get("disposal_purge_receipt_body_free") is True,
        "body_full_transient_material_reported_purged": op13_map.get("body_full_transient_material_reported_purged") is True,
        "local_temp_material_reported_purged": op13_map.get("local_temp_material_reported_purged") is True,
        "reviewer_working_form_body_reported_purged": op13_map.get("reviewer_working_form_body_reported_purged") is True,
        "disposal_purge_receipt_body_full_packet_retained": op13_map.get("disposal_purge_receipt_body_full_packet_retained") is True,
        "disposal_purge_receipt_local_temp_material_retained": op13_map.get("disposal_purge_receipt_local_temp_material_retained") is True,
        "disposal_purge_receipt_reviewer_working_form_body_retained": op13_map.get("disposal_purge_receipt_reviewer_working_form_body_retained") is True,
        "disposal_purge_receipt_external_export_performed": op13_map.get("disposal_purge_receipt_external_export_performed") is True,
        "disposal_purge_receipt_raw_input_included": op13_map.get("disposal_purge_receipt_raw_input_included") is True,
        "disposal_purge_receipt_comment_text_body_included": op13_map.get("disposal_purge_receipt_comment_text_body_included") is True,
        "disposal_purge_receipt_returned_surface_body_included": op13_map.get("disposal_purge_receipt_returned_surface_body_included") is True,
        "disposal_purge_receipt_reviewer_free_text_included": op13_map.get("disposal_purge_receipt_reviewer_free_text_included") is True,
        "disposal_purge_receipt_reviewer_note_body_included": op13_map.get("disposal_purge_receipt_reviewer_note_body_included") is True,
        "disposal_purge_receipt_question_text_included": op13_map.get("disposal_purge_receipt_question_text_included") is True,
        "disposal_purge_receipt_draft_question_text_included": op13_map.get("disposal_purge_receipt_draft_question_text_included") is True,
        "disposal_purge_receipt_answer_text_included": op13_map.get("disposal_purge_receipt_answer_text_included") is True,
        "disposal_purge_receipt_local_path_included": op13_map.get("disposal_purge_receipt_local_path_included") is True,
        "disposal_purge_receipt_body_hash_included": op13_map.get("disposal_purge_receipt_body_hash_included") is True,
        "disposal_purge_receipt_terminal_output_body_included": op13_map.get("disposal_purge_receipt_terminal_output_body_included") is True,
        "disposal_purge_receipt_forbidden_payload_key_path_refs": forbidden_paths,
        "disposal_purge_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "disposal_purge_receipt_body_like_value_path_refs": body_like_paths,
        "disposal_purge_receipt_body_like_value_path_count": len(body_like_paths),
        "disposal_purge_receipt_promotion_claim_refs": promotion_claims,
        "disposal_purge_receipt_promotion_claim_ref_count": len(promotion_claims),
        "disposal_purge_receipt_retention_or_export_blocker_refs": retention_or_export_blockers,
        "disposal_purge_receipt_retention_or_export_blocker_ref_count": len(retention_or_export_blockers),
        "dri_op07_status_ref": status_ref,
        "disposal_purge_receipt_revalidation_status_ref": status_ref,
        "dri_op07_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP07_ALLOWED_STATUS_REFS),
        "dri_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP07_ALLOWED_STATUS_REFS),
        "dri_op07_disposal_purge_receipt_revalidated_bodyfree": ready,
        "dri_op07_wait_for_disposal_purge_receipt": waiting,
        "dri_op07_repair_required": repair,
        "dri_op07_purge_receipt_body_leak_or_retention_blocked": blocked,
        "dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan": ready,
        "dri_op07_reason_refs": reasons,
        "dri_op07_reason_ref_count": len(reasons),
        "dri_op07_blocker_refs": blockers,
        "dri_op07_blocker_ref_count": len(blockers),
        "actual_review_execution_claimed_by_dri_op07": False,
        "actual_review_evidence_completed_by_dri_op07": False,
        "dhr_actual_source_claim_confirmed_by_dri_op07": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op07": False,
        "dhr_op04_called_by_dri_op07": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op07": False,
        "disposal_purge_executed_by_dri_op07": False,
        "dri_op07_does_not_execute_disposal_purge": True,
        "dri_op07_does_not_perform_final_no_leak_validation": True,
        "dri_op07_does_not_complete_actual_evidence": True,
        "dri_op07_does_not_execute_dhr_reintake": True,
        "dri_op07_does_not_call_dhr_op04": True,
        "dri_op07_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op07_does_not_execute_dmd_or_r52": True,
        "dri_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op07_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP07 body-free disposal / purge receipt revalidation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP07")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP07_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP07")
    for field, count_field in (("disposal_purge_receipt_forbidden_payload_key_path_refs", "disposal_purge_receipt_forbidden_payload_key_path_count"), ("disposal_purge_receipt_body_like_value_path_refs", "disposal_purge_receipt_body_like_value_path_count"), ("disposal_purge_receipt_promotion_claim_refs", "disposal_purge_receipt_promotion_claim_ref_count"), ("disposal_purge_receipt_retention_or_export_blocker_refs", "disposal_purge_receipt_retention_or_export_blocker_ref_count"), ("dri_op07_allowed_status_refs", "dri_op07_allowed_status_ref_count"), ("dri_op07_reason_refs", "dri_op07_reason_ref_count"), ("dri_op07_blocker_refs", "dri_op07_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP07 {count_field} changed")
    if tuple(data.get("dri_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 allowed status refs changed")
    for key in ("dri_op07_does_not_execute_disposal_purge", "dri_op07_does_not_perform_final_no_leak_validation", "dri_op07_does_not_complete_actual_evidence", "dri_op07_does_not_execute_dhr_reintake", "dri_op07_does_not_call_dhr_op04", "dri_op07_does_not_materialize_dhr_op04_adapter_candidate", "dri_op07_does_not_execute_dmd_or_r52", "dri_op07_does_not_start_p5_p6_p8_p7_or_release", "dri_op07_does_not_change_api_db_rn_runtime_response_key", "dri_op07_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP07 required true boundary changed: {key}")
    for key in ("actual_review_execution_claimed_by_dri_op07", "actual_review_evidence_completed_by_dri_op07", "dhr_actual_source_claim_confirmed_by_dri_op07", "dhr_op04_adapter_candidate_materialized_by_dri_op07", "dhr_op04_called_by_dri_op07", "dhr_actual_source_claim_reintake_executed_by_dri_op07", "disposal_purge_executed_by_dri_op07", "actual_disposal_purge_executed_here", "actual_review_evidence_complete_here", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP07 downstream/purge flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP07_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 implemented/not-yet steps changed")
    status_ref = data.get("dri_op07_status_ref")
    if status_ref != data.get("disposal_purge_receipt_revalidation_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 status alias changed")
    status_flags = [
        data.get("dri_op07_disposal_purge_receipt_revalidated_bodyfree") is True,
        data.get("dri_op07_wait_for_disposal_purge_receipt") is True,
        data.get("dri_op07_repair_required") is True,
        data.get("dri_op07_purge_receipt_body_leak_or_retention_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REVALIDATED_BODYFREE_REF:
        for key in ("op06_contract_valid", "op06_question_need_rows_revalidated_bridge_only", "op06_ready_for_disposal_purge_receipt_revalidation", "rsr_op13_contract_valid", "rsr_op13_disposal_purge_receipt_accepted", "disposal_purge_receipt_accepted_by_rsr_op13", "disposal_purge_receipt_accepted_without_purge_execution_by_helper", "final_no_leak_source_kind_validation_required_next", "operation_receipt_ref_matches_op06", "review_session_id_matches_op06", "disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person", "disposal_purge_receipt_ref_present", "disposal_purge_receipt_purge_completed", "disposal_purge_receipt_body_free", "body_full_transient_material_reported_purged", "local_temp_material_reported_purged", "reviewer_working_form_body_reported_purged"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP07 ready branch required true changed: {key}")
        for key in ("disposal_purge_receipt_body_full_packet_retained", "disposal_purge_receipt_local_temp_material_retained", "disposal_purge_receipt_reviewer_working_form_body_retained", "disposal_purge_receipt_external_export_performed", "disposal_purge_receipt_raw_input_included", "disposal_purge_receipt_comment_text_body_included", "disposal_purge_receipt_returned_surface_body_included", "disposal_purge_receipt_reviewer_free_text_included", "disposal_purge_receipt_reviewer_note_body_included", "disposal_purge_receipt_question_text_included", "disposal_purge_receipt_draft_question_text_included", "disposal_purge_receipt_answer_text_included", "disposal_purge_receipt_local_path_included", "disposal_purge_receipt_body_hash_included", "disposal_purge_receipt_terminal_output_body_included"):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP07 ready branch false retention field changed: {key}")
        if data.get("dri_op07_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF:
        if data.get("dri_op07_wait_for_disposal_purge_receipt") is not True or data.get("dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 wait branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_PURGE_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 wait next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF:
        if data.get("dri_op07_repair_required") is not True or not data.get("dri_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_PURGE_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF:
        if data.get("dri_op07_purge_receipt_body_leak_or_retention_blocked") is not True or not data.get("dri_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_PURGE_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 blocked next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP07 status ref is not allowed")
    return True

# DRI-OP08/OP09 additions: final rescan and DHR-OP04 adapter candidate materialization.
P7_R54_AHR_POST_RSR16_DRI_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op08_final_bodyfree_no_promotion_source_kind_rescan.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op09_dhr_op04_external_actual_source_claim_adapter_candidate.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri.external_actual_operation_evidence_claim.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_MATERIAL_KIND: Final = (
    "dhr_op04_external_actual_operation_evidence_claim_candidate"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_ORIGIN_REF: Final = (
    "external_local_only_human_review_receipt_or_manual_evidence_confirmation"
)
P7_R54_AHR_POST_RSR16_DRI_INVALID_SOURCE_KIND_REFS: Final[tuple[str, ...]] = (
    "unit_test_fixture",
    "helper_green",
    "target_green",
    "result_memo_green",
    "synthetic",
    "historical_reuse_only",
    "unknown",
    "candidate_shape_only",
    "unit_test_fixture_not_actual",
)
P7_R54_AHR_POST_RSR16_DRI_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:9]
)
P7_R54_AHR_POST_RSR16_DRI_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[9:]
)
P7_R54_AHR_POST_RSR16_DRI_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:10]
)
P7_R54_AHR_POST_RSR16_DRI_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[10:]
)

P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_CLEAR_BODYFREE_REF: Final = (
    "DRI_OP08_FINAL_SCAN_CLEAR_BODYFREE"
)
P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF: Final = (
    "DRI_OP08_WAIT_FOR_OP07_READY_BODYFREE_MATERIAL"
)
P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF: Final = (
    "DRI_OP08_FINAL_SCAN_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF: Final = (
    "DRI_OP08_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED"
)
P7_R54_AHR_POST_RSR16_DRI_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_CLEAR_BODYFREE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP07_READY_BEFORE_FINAL_SCAN_REF: Final = (
    "wait_for_dri_op07_ready_before_final_bodyfree_rescan"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP08_FINAL_SCAN_REF: Final = (
    "repair_dri_op08_final_scan_before_dhr_op04_adapter_candidate"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP08_FINAL_SCAN_REF: Final = (
    "blocked_dri_op08_bodyfree_leak_promotion_or_invalid_source_kind"
)

P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF: Final = (
    "DRI_OP09_DHR_OP04_EXTERNAL_ACTUAL_SOURCE_CLAIM_ADAPTER_CANDIDATE_MATERIALIZED_BODYFREE"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF: Final = (
    "DRI_OP09_WAIT_FOR_FINAL_SCAN_CLEAR"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF: Final = (
    "DRI_OP09_REPAIR_FINAL_SCAN_OR_MATERIAL_BEFORE_ADAPTER"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF: Final = (
    "DRI_OP09_BLOCKED_FINAL_SCAN_BODY_LEAK_PROMOTION_OR_INVALID_SOURCE_KIND"
)
P7_R54_AHR_POST_RSR16_DRI_OP09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP08_FINAL_SCAN_REF: Final = (
    "wait_for_dri_op08_final_scan_clear_before_dhr_op04_adapter_candidate"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP09_ADAPTER_REF: Final = (
    "repair_dri_op09_adapter_material_before_manual_dhr_op04_input"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP09_ADAPTER_REF: Final = (
    "blocked_dri_op09_adapter_material_bodyfree_or_promotion_boundary_failed"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF: Final = (
    "provide_dri_bodyfree_actual_source_claim_adapter_material_to_dhr_op04_without_auto_execution"
)

P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "material_kind",
    "review_session_id",
    "source_kind_ref",
    "actual_source_claim_source_kind_ref",
    "actual_source_claim_origin_ref",
    "actual_source_claim_bodyfree",
    "actual_local_only_human_review_by_person_confirmed",
    "actual_human_review_executed_by_person",
    "operation_receipt_bodyfree_ref",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_need_observation_row_count",
    "disposal_purge_receipt_bodyfree_ref",
    "rsr_op15_branch_ref",
    "rsr_op16_status_ref",
    "body_free",
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

P7_R54_AHR_POST_RSR16_DRI_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_contract_valid", "op02_contract_valid", "op03_contract_valid", "op04_contract_valid", "op05_contract_valid", "op06_contract_valid", "op07_contract_valid",
    "op01_status_ref", "op02_status_ref", "op03_status_ref", "op04_status_ref", "op05_status_ref", "op06_status_ref", "op07_status_ref",
    "op07_disposal_purge_receipt_revalidated_bodyfree", "op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan",
    "rsr_op15_branch_ref", "rsr_op16_status_ref", "operation_receipt_bodyfree_ref", "reviewer_person_ref", "actual_human_review_executed_by_person", "actual_local_only_human_review_by_person_confirmed",
    "sanitized_review_result_row_count", "rating_row_count", "question_need_observation_row_count", "disposal_purge_receipt_bodyfree_ref",
    "final_scan_target_material_refs", "final_scan_target_material_ref_count", "final_scan_target_step_refs", "final_scan_target_step_ref_count",
    "final_scan_required_source_kind_ref", "final_scan_source_kind_ref_values", "final_scan_source_kind_ref_value_count", "final_scan_invalid_source_kind_refs", "final_scan_invalid_source_kind_ref_count", "final_scan_invalid_source_kind_allowed_refs", "final_scan_invalid_source_kind_allowed_ref_count",
    "final_scan_forbidden_payload_key_path_refs", "final_scan_forbidden_payload_key_path_count", "final_scan_body_like_value_path_refs", "final_scan_body_like_value_path_count", "final_scan_promotion_claim_refs", "final_scan_promotion_claim_ref_count", "final_scan_contract_or_readiness_blocker_refs", "final_scan_contract_or_readiness_blocker_ref_count",
    "dri_op08_status_ref", "final_bodyfree_no_promotion_source_kind_rescan_status_ref", "dri_op08_allowed_status_refs", "dri_op08_allowed_status_ref_count", "dri_op08_final_scan_clear_bodyfree", "dri_op08_wait_for_op07_ready", "dri_op08_final_scan_repair_required", "dri_op08_final_scan_body_leak_or_promotion_blocked", "dri_op08_ready_for_dhr_op04_adapter_candidate_materialization",
    "dri_op08_reason_refs", "dri_op08_reason_ref_count", "dri_op08_blocker_refs", "dri_op08_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op08", "actual_review_evidence_completed_by_dri_op08", "dhr_actual_source_claim_confirmed_by_dri_op08", "dhr_op04_adapter_candidate_materialized_by_dri_op08", "dhr_op04_called_by_dri_op08", "dhr_actual_source_claim_reintake_executed_by_dri_op08",
    "dri_op08_does_not_materialize_dhr_op04_adapter_candidate", "dri_op08_does_not_call_dhr_op04", "dri_op08_does_not_execute_dhr_reintake", "dri_op08_does_not_execute_dmd_or_r52", "dri_op08_does_not_start_p5_p6_p8_p7_or_release", "dri_op08_does_not_change_api_db_rn_runtime_response_key", "dri_op08_does_not_materialize_p8_question_spec",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RSR16_DRI_OP09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op08_schema_version", "op08_material_ref", "op08_contract_valid", "op08_status_ref", "op08_final_scan_clear_bodyfree", "op08_ready_for_dhr_op04_adapter_candidate_materialization",
    "op04_contract_valid", "op05_contract_valid", "op06_contract_valid", "op07_contract_valid", "op04_status_ref", "op05_status_ref", "op06_status_ref", "op07_status_ref",
    "adapter_candidate_schema_version", "adapter_candidate_material_kind", "adapter_candidate_origin_ref", "adapter_candidate_dhr_op04_readable_key_refs", "adapter_candidate_dhr_op04_readable_key_ref_count",
    "external_actual_operation_evidence_claim_bodyfree_optional_present", "external_actual_operation_evidence_claim_bodyfree_optional", "external_actual_operation_evidence_claim_bodyfree_optional_key_refs", "external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count",
    "operation_receipt_bodyfree_ref", "disposal_purge_receipt_bodyfree_ref", "source_kind_ref", "actual_source_claim_source_kind_ref", "actual_source_claim_origin_ref", "actual_source_claim_bodyfree", "actual_local_only_human_review_by_person_confirmed", "actual_human_review_executed_by_person", "sanitized_review_result_row_count", "rating_row_count", "question_need_observation_row_count", "rsr_op15_branch_ref", "rsr_op16_status_ref",
    "adapter_candidate_materialized", "adapter_candidate_materialized_bodyfree", "adapter_candidate_for_manual_dhr_op04_input_only", "adapter_candidate_not_dhr_confirmed", "adapter_candidate_does_not_call_dhr_op04", "adapter_candidate_does_not_execute_dhr_reintake", "adapter_candidate_downstream_auto_execution_allowed",
    "adapter_candidate_forbidden_payload_key_path_refs", "adapter_candidate_forbidden_payload_key_path_count", "adapter_candidate_body_like_value_path_refs", "adapter_candidate_body_like_value_path_count", "adapter_candidate_promotion_claim_refs", "adapter_candidate_promotion_claim_ref_count", "adapter_candidate_invalid_source_kind_refs", "adapter_candidate_invalid_source_kind_ref_count",
    "dri_op09_status_ref", "dhr_op04_external_actual_source_claim_adapter_candidate_status_ref", "dri_op09_allowed_status_refs", "dri_op09_allowed_status_ref_count", "dri_op09_adapter_candidate_materialized_bodyfree", "dri_op09_wait_for_final_scan_clear", "dri_op09_repair_required", "dri_op09_blocked_before_adapter_candidate", "dri_op09_ready_to_provide_candidate_to_dhr_op04_manually",
    "dri_op09_reason_refs", "dri_op09_reason_ref_count", "dri_op09_blocker_refs", "dri_op09_blocker_ref_count",
    "actual_review_execution_claimed_by_dri_op09", "actual_review_evidence_completed_by_dri_op09", "dhr_actual_source_claim_confirmed_by_dri_op09", "dhr_op04_called_by_dri_op09", "dhr_actual_source_claim_reintake_executed_by_dri_op09", "dmd_execution_started_by_dri_op09", "r52_actual_execution_started_by_dri_op09",
    "dri_op09_does_not_call_dhr_op04", "dri_op09_does_not_execute_dhr_reintake", "dri_op09_does_not_confirm_dhr_actual_source_claim", "dri_op09_does_not_execute_dmd_or_r52", "dri_op09_does_not_start_p5_p6_p8_p7_or_release", "dri_op09_does_not_change_api_db_rn_runtime_response_key", "dri_op09_does_not_materialize_p8_question_spec", "downstream_auto_execution_allowed",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _scan_invalid_source_kind_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.endswith("source_kind_ref") or key_text == "source_kind_ref":
                child_ref = _clean_ref(child, default="", max_length=220)
                if child_ref in P7_R54_AHR_POST_RSR16_DRI_INVALID_SOURCE_KIND_REFS:
                    paths.append(child_path)
            paths.extend(_scan_invalid_source_kind_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_invalid_source_kind_paths(child, path=f"{path}[{index}]"))
    return paths


def _op08_status_reason_blocker_next(
    *,
    op07_status_ref: str,
    op07_ready: bool,
    contract_or_readiness_blockers: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    invalid_source_kind_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or invalid_source_kind_refs or op07_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF:
        if forbidden_paths:
            blockers.append("dri_op08_forbidden_payload_key_detected")
        if body_like_paths:
            blockers.append("dri_op08_body_like_value_detected")
        if promotion_claims:
            blockers.append("dri_op08_promotion_claim_detected")
        if invalid_source_kind_refs:
            blockers.append("dri_op08_invalid_source_kind_detected")
        if op07_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_BLOCKED_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF:
            blockers.append("dri_op07_blocked_before_final_scan")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF,
            ["final_rescan_blocks_before_adapter_candidate_bodyfree_promotion_or_source_kind_boundary_failed"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP08_FINAL_SCAN_REF,
        )
    if op07_status_ref in {"dri_op07_status_missing", P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF} or not op07_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF,
            ["wait_for_dri_op07_ready_before_final_rescan"],
            ["dri_op07_not_ready_for_final_rescan"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP07_READY_BEFORE_FINAL_SCAN_REF,
        )
    if contract_or_readiness_blockers or op07_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF:
        blockers = list(contract_or_readiness_blockers)
        if op07_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_REPAIR_PURGE_RECEIPT_REF:
            blockers.append("dri_op07_repair_required_before_final_scan")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF,
            ["repair_dri_material_contract_or_readiness_before_adapter_candidate"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP08_FINAL_SCAN_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_CLEAR_BODYFREE_REF,
        ["final_bodyfree_no_promotion_source_kind_rescan_clear_before_adapter_candidate"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
    *,
    dri_op01_rsr_op16_result_memo_intake: Mapping[str, Any] | None = None,
    dri_op02_rsr_op15_branch_next_step_alignment: Mapping[str, Any] | None = None,
    dri_op03_complete_candidate_supplied_material_inventory: Mapping[str, Any] | None = None,
    dri_op04_actual_operation_receipt_revalidation: Mapping[str, Any] | None = None,
    dri_op05_sanitized_rows_rating_rows_revalidation: Mapping[str, Any] | None = None,
    dri_op06_question_need_rows_bridge_only_revalidation: Mapping[str, Any] | None = None,
    dri_op07_disposal_purge_receipt_revalidation: Mapping[str, Any] | None = None,
    additional_bodyfree_materials: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP08 final body-free / no-promotion / source-kind rescan material."""

    named_materials: dict[str, Mapping[str, Any]] = {}
    for name, material in (
        ("dri_op01", dri_op01_rsr_op16_result_memo_intake),
        ("dri_op02", dri_op02_rsr_op15_branch_next_step_alignment),
        ("dri_op03", dri_op03_complete_candidate_supplied_material_inventory),
        ("dri_op04", dri_op04_actual_operation_receipt_revalidation),
        ("dri_op05", dri_op05_sanitized_rows_rating_rows_revalidation),
        ("dri_op06", dri_op06_question_need_rows_bridge_only_revalidation),
        ("dri_op07", dri_op07_disposal_purge_receipt_revalidation),
    ):
        if isinstance(material, Mapping):
            named_materials[name] = material
    if isinstance(additional_bodyfree_materials, Mapping):
        for key, value in additional_bodyfree_materials.items():
            if isinstance(value, Mapping):
                named_materials[f"additional.{_clean_ref(key, default='material', max_length=120)}"] = value

    op01 = named_materials.get("dri_op01", {})
    op02 = named_materials.get("dri_op02", {})
    op03 = named_materials.get("dri_op03", {})
    op04 = named_materials.get("dri_op04", {})
    op05 = named_materials.get("dri_op05", {})
    op06 = named_materials.get("dri_op06", {})
    op07 = named_materials.get("dri_op07", {})
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op07.get("review_session_id"))

    validator_specs: tuple[tuple[str, Mapping[str, Any] | None, Any], ...] = (
        ("dri_op01", dri_op01_rsr_op16_result_memo_intake, assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract),
        ("dri_op02", dri_op02_rsr_op15_branch_next_step_alignment, assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract),
        ("dri_op03", dri_op03_complete_candidate_supplied_material_inventory, assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract),
        ("dri_op04", dri_op04_actual_operation_receipt_revalidation, assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract),
        ("dri_op05", dri_op05_sanitized_rows_rating_rows_revalidation, assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract),
        ("dri_op06", dri_op06_question_need_rows_bridge_only_revalidation, assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract),
        ("dri_op07", dri_op07_disposal_purge_receipt_revalidation, assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract),
    )
    contract_valid: dict[str, bool] = {}
    contract_or_readiness_blockers: list[str] = []
    for name, material, validator in validator_specs:
        valid = False
        if isinstance(material, Mapping):
            try:
                valid = validator(material) is True
            except ValueError:
                valid = False
        contract_valid[name] = valid
        if not valid:
            contract_or_readiness_blockers.append(f"{name}_contract_invalid_or_missing")

    readiness_pairs = (
        ("dri_op01_ready_for_rsr_op15_branch_alignment", op01.get("dri_op01_ready_for_rsr_op15_branch_alignment") is True),
        ("dri_op02_ready_for_complete_candidate_prerequisite_inventory", op02.get("dri_op02_ready_for_complete_candidate_prerequisite_inventory") is True),
        ("dri_op03_ready_for_actual_operation_receipt_revalidation", op03.get("dri_op03_ready_for_actual_operation_receipt_revalidation") is True),
        ("dri_op04_ready_for_rows_and_ratings_revalidation", op04.get("dri_op04_ready_for_rows_and_ratings_revalidation") is True),
        ("dri_op05_ready_for_question_need_rows_bridge_only_revalidation", op05.get("dri_op05_ready_for_question_need_rows_bridge_only_revalidation") is True),
        ("dri_op06_ready_for_disposal_purge_receipt_revalidation", op06.get("dri_op06_ready_for_disposal_purge_receipt_revalidation") is True),
        ("dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan", op07.get("dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan") is True),
    )
    contract_or_readiness_blockers.extend(ref for ref, ok in readiness_pairs if not ok)

    forbidden_paths = _dedupe_clean_refs(sum((_scan_forbidden_payload_key_paths(material, path=name) for name, material in named_materials.items()), []), max_length=360)
    body_like_paths = _dedupe_clean_refs(sum((_scan_body_like_value_paths(material, path=name) for name, material in named_materials.items()), []), max_length=360)
    promotion_claims = _dedupe_clean_refs(sum((_scan_promotion_claim_refs(material, path=name) for name, material in named_materials.items()), []), max_length=360)
    invalid_source_kind_refs = _dedupe_clean_refs(sum((_scan_invalid_source_kind_paths(material, path=name) for name, material in named_materials.items()), []), max_length=360)
    source_kind_ref_values = _dedupe_clean_refs([
        op04.get("source_kind_ref"),
        op05.get("source_kind_ref"),
        op06.get("source_kind_ref"),
        op07.get("source_kind_ref"),
    ], max_length=220)
    if any(ref and ref != rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF for ref in source_kind_ref_values):
        invalid_source_kind_refs = _dedupe_clean_refs(list(invalid_source_kind_refs) + ["final_scan_source_kind_ref_not_actual_local_only_human_review_by_person"], max_length=360)

    op07_status_ref = _clean_ref(op07.get("dri_op07_status_ref"), default="dri_op07_status_missing", max_length=260)
    op07_ready = op07.get("dri_op07_disposal_purge_receipt_revalidated_bodyfree") is True and op07.get("dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan") is True
    status_ref, reasons, blockers, next_required_step = _op08_status_reason_blocker_next(
        op07_status_ref=op07_status_ref,
        op07_ready=op07_ready,
        contract_or_readiness_blockers=contract_or_readiness_blockers,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        invalid_source_kind_refs=invalid_source_kind_refs,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_CLEAR_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
    target_refs = _dedupe_clean_refs(list(named_materials.keys()), max_length=220)
    target_steps = _dedupe_clean_refs([material.get("operation_step_ref") for material in named_materials.values()], max_length=260)
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_contract_valid": contract_valid["dri_op01"],
        "op02_contract_valid": contract_valid["dri_op02"],
        "op03_contract_valid": contract_valid["dri_op03"],
        "op04_contract_valid": contract_valid["dri_op04"],
        "op05_contract_valid": contract_valid["dri_op05"],
        "op06_contract_valid": contract_valid["dri_op06"],
        "op07_contract_valid": contract_valid["dri_op07"],
        "op01_status_ref": _clean_ref(op01.get("dri_op01_status_ref"), default="dri_op01_status_missing", max_length=260),
        "op02_status_ref": _clean_ref(op02.get("dri_op02_status_ref"), default="dri_op02_status_missing", max_length=260),
        "op03_status_ref": _clean_ref(op03.get("dri_op03_status_ref"), default="dri_op03_status_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("dri_op04_status_ref"), default="dri_op04_status_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("dri_op05_status_ref"), default="dri_op05_status_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06.get("dri_op06_status_ref"), default="dri_op06_status_missing", max_length=260),
        "op07_status_ref": op07_status_ref,
        "op07_disposal_purge_receipt_revalidated_bodyfree": op07.get("dri_op07_disposal_purge_receipt_revalidated_bodyfree") is True,
        "op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan": op07_ready,
        "rsr_op15_branch_ref": _clean_ref(op02.get("rsr_op15_branch_ref"), default="rsr_op15_branch_ref_missing", max_length=260),
        "rsr_op16_status_ref": _clean_ref(op01.get("rsr_op16_status_ref"), default="rsr_op16_status_ref_missing", max_length=260),
        "operation_receipt_bodyfree_ref": _clean_ref(op04.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220),
        "reviewer_person_ref": _clean_ref(op04.get("reviewer_person_ref") or op07.get("reviewer_person_ref"), default="reviewer_person_ref_missing", max_length=220),
        "actual_human_review_executed_by_person": op04.get("actual_human_review_executed_by_person") is True,
        "actual_local_only_human_review_by_person_confirmed": all(material.get("source_kind_ref") == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF for material in (op04, op05, op06, op07)),
        "sanitized_review_result_row_count": _safe_int_value(op05.get("sanitized_review_result_row_count")),
        "rating_row_count": _safe_int_value(op05.get("rating_row_count")),
        "question_need_observation_row_count": _safe_int_value(op06.get("question_need_observation_row_count")),
        "disposal_purge_receipt_bodyfree_ref": _clean_ref(op07.get("disposal_purge_receipt_ref"), default="disposal_purge_receipt_ref_missing", max_length=220),
        "final_scan_target_material_refs": target_refs,
        "final_scan_target_material_ref_count": len(target_refs),
        "final_scan_target_step_refs": target_steps,
        "final_scan_target_step_ref_count": len(target_steps),
        "final_scan_required_source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "final_scan_source_kind_ref_values": source_kind_ref_values,
        "final_scan_source_kind_ref_value_count": len(source_kind_ref_values),
        "final_scan_invalid_source_kind_refs": invalid_source_kind_refs,
        "final_scan_invalid_source_kind_ref_count": len(invalid_source_kind_refs),
        "final_scan_invalid_source_kind_allowed_refs": list(P7_R54_AHR_POST_RSR16_DRI_INVALID_SOURCE_KIND_REFS),
        "final_scan_invalid_source_kind_allowed_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_INVALID_SOURCE_KIND_REFS),
        "final_scan_forbidden_payload_key_path_refs": forbidden_paths,
        "final_scan_forbidden_payload_key_path_count": len(forbidden_paths),
        "final_scan_body_like_value_path_refs": body_like_paths,
        "final_scan_body_like_value_path_count": len(body_like_paths),
        "final_scan_promotion_claim_refs": promotion_claims,
        "final_scan_promotion_claim_ref_count": len(promotion_claims),
        "final_scan_contract_or_readiness_blocker_refs": _dedupe_clean_refs(contract_or_readiness_blockers, max_length=320),
        "final_scan_contract_or_readiness_blocker_ref_count": len(_dedupe_clean_refs(contract_or_readiness_blockers, max_length=320)),
        "dri_op08_status_ref": status_ref,
        "final_bodyfree_no_promotion_source_kind_rescan_status_ref": status_ref,
        "dri_op08_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP08_ALLOWED_STATUS_REFS),
        "dri_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP08_ALLOWED_STATUS_REFS),
        "dri_op08_final_scan_clear_bodyfree": ready,
        "dri_op08_wait_for_op07_ready": waiting,
        "dri_op08_final_scan_repair_required": repair,
        "dri_op08_final_scan_body_leak_or_promotion_blocked": blocked,
        "dri_op08_ready_for_dhr_op04_adapter_candidate_materialization": ready,
        "dri_op08_reason_refs": reasons,
        "dri_op08_reason_ref_count": len(reasons),
        "dri_op08_blocker_refs": blockers,
        "dri_op08_blocker_ref_count": len(blockers),
        "actual_review_execution_claimed_by_dri_op08": False,
        "actual_review_evidence_completed_by_dri_op08": False,
        "dhr_actual_source_claim_confirmed_by_dri_op08": False,
        "dhr_op04_adapter_candidate_materialized_by_dri_op08": False,
        "dhr_op04_called_by_dri_op08": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op08": False,
        "dri_op08_does_not_materialize_dhr_op04_adapter_candidate": True,
        "dri_op08_does_not_call_dhr_op04": True,
        "dri_op08_does_not_execute_dhr_reintake": True,
        "dri_op08_does_not_execute_dmd_or_r52": True,
        "dri_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op08_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP08 final body-free / no-promotion / source-kind rescan contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP08")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP08_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP08")
    for field, count_field in (("final_scan_target_material_refs", "final_scan_target_material_ref_count"), ("final_scan_target_step_refs", "final_scan_target_step_ref_count"), ("final_scan_source_kind_ref_values", "final_scan_source_kind_ref_value_count"), ("final_scan_invalid_source_kind_refs", "final_scan_invalid_source_kind_ref_count"), ("final_scan_invalid_source_kind_allowed_refs", "final_scan_invalid_source_kind_allowed_ref_count"), ("final_scan_forbidden_payload_key_path_refs", "final_scan_forbidden_payload_key_path_count"), ("final_scan_body_like_value_path_refs", "final_scan_body_like_value_path_count"), ("final_scan_promotion_claim_refs", "final_scan_promotion_claim_ref_count"), ("final_scan_contract_or_readiness_blocker_refs", "final_scan_contract_or_readiness_blocker_ref_count"), ("dri_op08_allowed_status_refs", "dri_op08_allowed_status_ref_count"), ("dri_op08_reason_refs", "dri_op08_reason_ref_count"), ("dri_op08_blocker_refs", "dri_op08_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP08 {count_field} changed")
    if tuple(data.get("dri_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 allowed status refs changed")
    if tuple(data.get("final_scan_invalid_source_kind_allowed_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_INVALID_SOURCE_KIND_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 invalid source kind refs changed")
    for key in ("dri_op08_does_not_materialize_dhr_op04_adapter_candidate", "dri_op08_does_not_call_dhr_op04", "dri_op08_does_not_execute_dhr_reintake", "dri_op08_does_not_execute_dmd_or_r52", "dri_op08_does_not_start_p5_p6_p8_p7_or_release", "dri_op08_does_not_change_api_db_rn_runtime_response_key", "dri_op08_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP08 required true boundary changed: {key}")
    for key in ("actual_review_execution_claimed_by_dri_op08", "actual_review_evidence_completed_by_dri_op08", "dhr_actual_source_claim_confirmed_by_dri_op08", "dhr_op04_adapter_candidate_materialized_by_dri_op08", "dhr_op04_called_by_dri_op08", "dhr_actual_source_claim_reintake_executed_by_dri_op08", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP08 downstream/final scan flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP08_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 implemented/not-yet steps changed")
    status_ref = data.get("dri_op08_status_ref")
    if status_ref != data.get("final_bodyfree_no_promotion_source_kind_rescan_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 status alias changed")
    status_flags = [
        data.get("dri_op08_final_scan_clear_bodyfree") is True,
        data.get("dri_op08_wait_for_op07_ready") is True,
        data.get("dri_op08_final_scan_repair_required") is True,
        data.get("dri_op08_final_scan_body_leak_or_promotion_blocked") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_CLEAR_BODYFREE_REF:
        for key in ("op01_contract_valid", "op02_contract_valid", "op03_contract_valid", "op04_contract_valid", "op05_contract_valid", "op06_contract_valid", "op07_contract_valid", "op07_disposal_purge_receipt_revalidated_bodyfree", "op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan", "actual_human_review_executed_by_person", "actual_local_only_human_review_by_person_confirmed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP08 clear branch required true changed: {key}")
        if data.get("final_scan_forbidden_payload_key_path_refs") != [] or data.get("final_scan_body_like_value_path_refs") != [] or data.get("final_scan_promotion_claim_refs") != [] or data.get("final_scan_invalid_source_kind_refs") != [] or data.get("final_scan_contract_or_readiness_blocker_refs") != [] or data.get("dri_op08_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 clear branch cannot carry scan issues")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 clear next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF:
        if data.get("dri_op08_wait_for_op07_ready") is not True or data.get("dri_op08_ready_for_dhr_op04_adapter_candidate_materialization") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 wait branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF:
        if data.get("dri_op08_final_scan_repair_required") is not True or not data.get("dri_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 repair branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF:
        if data.get("dri_op08_final_scan_body_leak_or_promotion_blocked") is not True or not data.get("dri_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 blocked branch changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP08 status ref is not allowed")
    return True


def _dri_op09_empty_adapter_candidate() -> dict[str, Any]:
    return {}


def _dri_op09_build_adapter_candidate(
    *,
    review_session_id: str,
    op08: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_SCHEMA_VERSION,
        "material_kind": P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_MATERIAL_KIND,
        "review_session_id": review_session_id,
        "source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "actual_source_claim_source_kind_ref": rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "actual_source_claim_origin_ref": P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_ORIGIN_REF,
        "actual_source_claim_bodyfree": True,
        "actual_local_only_human_review_by_person_confirmed": True,
        "actual_human_review_executed_by_person": True,
        "operation_receipt_bodyfree_ref": _clean_ref(op08.get("operation_receipt_bodyfree_ref"), default="operation_receipt_ref_missing", max_length=220),
        "sanitized_review_result_row_count": _safe_int_value(op08.get("sanitized_review_result_row_count")),
        "rating_row_count": _safe_int_value(op08.get("rating_row_count")),
        "question_need_observation_row_count": _safe_int_value(op08.get("question_need_observation_row_count")),
        "disposal_purge_receipt_bodyfree_ref": _clean_ref(op08.get("disposal_purge_receipt_bodyfree_ref"), default="disposal_purge_receipt_ref_missing", max_length=220),
        "rsr_op15_branch_ref": _clean_ref(op08.get("rsr_op15_branch_ref"), default="RSR_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION", max_length=260),
        "rsr_op16_status_ref": _clean_ref(op08.get("rsr_op16_status_ref"), default="RSR_RESULT_MEMO_TESTS_SELECTED_REGRESSION_CLOSED_BODYFREE", max_length=260),
        "body_free": True,
        "dhr_op04_called_here": False,
        "dhr_actual_source_claim_reintake_executed_here": False,
        "dmd_execution_started_here": False,
        "r52_actual_execution_started_here": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "p7_complete": False,
        "release_allowed": False,
    }


def _op09_status_reason_blocker_next(
    *,
    op08_contract_valid: bool,
    op08_status_ref: str,
    op08_ready: bool,
    source_materials_valid: bool,
    candidate_present: bool,
    candidate_issue_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    if op08_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF or candidate_issue_refs:
        blockers = list(candidate_issue_refs)
        if op08_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF:
            blockers.append("dri_op08_final_scan_blocked")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF,
            ["blocked_before_adapter_candidate_manual_handoff"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP09_ADAPTER_REF,
        )
    if not op08_contract_valid or not source_materials_valid or op08_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF,
            ["repair_op08_or_revalidated_source_material_before_adapter_candidate"],
            ["op08_or_source_material_contract_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP09_ADAPTER_REF,
        )
    if not op08_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF,
            ["wait_for_dri_op08_final_scan_clear_before_adapter_candidate"],
            ["dri_op08_final_scan_not_clear"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP08_FINAL_SCAN_REF,
        )
    if not candidate_present:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF,
            ["repair_adapter_candidate_shape_before_manual_dhr_op04_input"],
            ["adapter_candidate_not_materialized_despite_clear_final_scan"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP09_ADAPTER_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF,
        ["adapter_candidate_materialized_bodyfree_for_manual_dhr_op04_input_without_auto_execution"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
    *,
    dri_op08_final_bodyfree_no_promotion_source_kind_rescan: Mapping[str, Any] | None = None,
    final_bodyfree_no_promotion_source_kind_rescan: Mapping[str, Any] | None = None,
    dri_op04_actual_operation_receipt_revalidation: Mapping[str, Any] | None = None,
    dri_op05_sanitized_rows_rating_rows_revalidation: Mapping[str, Any] | None = None,
    dri_op06_question_need_rows_bridge_only_revalidation: Mapping[str, Any] | None = None,
    dri_op07_disposal_purge_receipt_revalidation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP09 body-free DHR-OP04 external actual source claim adapter candidate material."""

    op08_input = dri_op08_final_bodyfree_no_promotion_source_kind_rescan if dri_op08_final_bodyfree_no_promotion_source_kind_rescan is not None else final_bodyfree_no_promotion_source_kind_rescan
    op08 = op08_input if isinstance(op08_input, Mapping) else {}
    op04 = dri_op04_actual_operation_receipt_revalidation if isinstance(dri_op04_actual_operation_receipt_revalidation, Mapping) else {}
    op05 = dri_op05_sanitized_rows_rating_rows_revalidation if isinstance(dri_op05_sanitized_rows_rating_rows_revalidation, Mapping) else {}
    op06 = dri_op06_question_need_rows_bridge_only_revalidation if isinstance(dri_op06_question_need_rows_bridge_only_revalidation, Mapping) else {}
    op07 = dri_op07_disposal_purge_receipt_revalidation if isinstance(dri_op07_disposal_purge_receipt_revalidation, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op08.get("review_session_id"))

    try:
        op08_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(op08) is True
    except ValueError:
        op08_contract_valid = False
    source_validators = (
        (op04, assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract, "dri_op04"),
        (op05, assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract, "dri_op05"),
        (op06, assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract, "dri_op06"),
        (op07, assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract, "dri_op07"),
    )
    source_valid_map: dict[str, bool] = {}
    for material, validator, name in source_validators:
        valid = False
        if isinstance(material, Mapping):
            try:
                valid = validator(material) is True
            except ValueError:
                valid = False
        source_valid_map[name] = valid

    op08_status_ref = _clean_ref(op08.get("dri_op08_status_ref"), default="dri_op08_status_missing", max_length=260)
    op08_ready = op08.get("dri_op08_final_scan_clear_bodyfree") is True and op08.get("dri_op08_ready_for_dhr_op04_adapter_candidate_materialization") is True
    source_materials_ready = bool(
        all(source_valid_map.values())
        and op04.get("dri_op04_revalidated_bodyfree") is True
        and op05.get("dri_op05_rows_and_ratings_revalidated_bodyfree") is True
        and op06.get("dri_op06_question_need_rows_revalidated_bridge_only") is True
        and op07.get("dri_op07_disposal_purge_receipt_revalidated_bodyfree") is True
    )
    candidate = _dri_op09_build_adapter_candidate(review_session_id=session_id, op08=op08) if op08_contract_valid and op08_ready and source_materials_ready else _dri_op09_empty_adapter_candidate()
    candidate_key_refs = _dedupe_clean_refs(list(candidate.keys()), max_length=220)
    candidate_forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"), max_length=360)
    candidate_body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"), max_length=360)
    candidate_promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"), max_length=360)
    candidate_invalid_source_kind_refs = _dedupe_clean_refs(_scan_invalid_source_kind_paths(candidate, path="external_actual_operation_evidence_claim_bodyfree_optional"), max_length=360)
    candidate_issue_refs = _dedupe_clean_refs(list(candidate_forbidden_paths) + list(candidate_body_like_paths) + list(candidate_promotion_claims) + list(candidate_invalid_source_kind_refs), max_length=360)
    status_ref, reasons, blockers, next_required_step = _op09_status_reason_blocker_next(
        op08_contract_valid=op08_contract_valid,
        op08_status_ref=op08_status_ref,
        op08_ready=op08_ready,
        source_materials_valid=source_materials_ready,
        candidate_present=bool(candidate),
        candidate_issue_refs=candidate_issue_refs,
    )
    ready = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP09_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_schema_version": op08.get("schema_version"),
        "op08_material_ref": _clean_ref(op08.get("material_id"), default="dri_op08_material_missing", max_length=260),
        "op08_contract_valid": op08_contract_valid,
        "op08_status_ref": op08_status_ref,
        "op08_final_scan_clear_bodyfree": op08.get("dri_op08_final_scan_clear_bodyfree") is True,
        "op08_ready_for_dhr_op04_adapter_candidate_materialization": op08_ready,
        "op04_contract_valid": source_valid_map["dri_op04"],
        "op05_contract_valid": source_valid_map["dri_op05"],
        "op06_contract_valid": source_valid_map["dri_op06"],
        "op07_contract_valid": source_valid_map["dri_op07"],
        "op04_status_ref": _clean_ref(op04.get("dri_op04_status_ref"), default="dri_op04_status_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("dri_op05_status_ref"), default="dri_op05_status_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06.get("dri_op06_status_ref"), default="dri_op06_status_missing", max_length=260),
        "op07_status_ref": _clean_ref(op07.get("dri_op07_status_ref"), default="dri_op07_status_missing", max_length=260),
        "adapter_candidate_schema_version": P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_SCHEMA_VERSION,
        "adapter_candidate_material_kind": P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_MATERIAL_KIND,
        "adapter_candidate_origin_ref": P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_ORIGIN_REF,
        "adapter_candidate_dhr_op04_readable_key_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS),
        "adapter_candidate_dhr_op04_readable_key_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS),
        "external_actual_operation_evidence_claim_bodyfree_optional_present": bool(candidate),
        "external_actual_operation_evidence_claim_bodyfree_optional": candidate,
        "external_actual_operation_evidence_claim_bodyfree_optional_key_refs": candidate_key_refs,
        "external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count": len(candidate_key_refs),
        "operation_receipt_bodyfree_ref": candidate.get("operation_receipt_bodyfree_ref", ""),
        "disposal_purge_receipt_bodyfree_ref": candidate.get("disposal_purge_receipt_bodyfree_ref", ""),
        "source_kind_ref": candidate.get("source_kind_ref", ""),
        "actual_source_claim_source_kind_ref": candidate.get("actual_source_claim_source_kind_ref", ""),
        "actual_source_claim_origin_ref": candidate.get("actual_source_claim_origin_ref", ""),
        "actual_source_claim_bodyfree": candidate.get("actual_source_claim_bodyfree") is True,
        "actual_local_only_human_review_by_person_confirmed": candidate.get("actual_local_only_human_review_by_person_confirmed") is True,
        "actual_human_review_executed_by_person": candidate.get("actual_human_review_executed_by_person") is True,
        "sanitized_review_result_row_count": _safe_int_value(candidate.get("sanitized_review_result_row_count")),
        "rating_row_count": _safe_int_value(candidate.get("rating_row_count")),
        "question_need_observation_row_count": _safe_int_value(candidate.get("question_need_observation_row_count")),
        "rsr_op15_branch_ref": candidate.get("rsr_op15_branch_ref", ""),
        "rsr_op16_status_ref": candidate.get("rsr_op16_status_ref", ""),
        "adapter_candidate_materialized": ready,
        "adapter_candidate_materialized_bodyfree": ready,
        "adapter_candidate_for_manual_dhr_op04_input_only": ready,
        "adapter_candidate_not_dhr_confirmed": True,
        "adapter_candidate_does_not_call_dhr_op04": True,
        "adapter_candidate_does_not_execute_dhr_reintake": True,
        "adapter_candidate_downstream_auto_execution_allowed": False,
        "adapter_candidate_forbidden_payload_key_path_refs": candidate_forbidden_paths,
        "adapter_candidate_forbidden_payload_key_path_count": len(candidate_forbidden_paths),
        "adapter_candidate_body_like_value_path_refs": candidate_body_like_paths,
        "adapter_candidate_body_like_value_path_count": len(candidate_body_like_paths),
        "adapter_candidate_promotion_claim_refs": candidate_promotion_claims,
        "adapter_candidate_promotion_claim_ref_count": len(candidate_promotion_claims),
        "adapter_candidate_invalid_source_kind_refs": candidate_invalid_source_kind_refs,
        "adapter_candidate_invalid_source_kind_ref_count": len(candidate_invalid_source_kind_refs),
        "dri_op09_status_ref": status_ref,
        "dhr_op04_external_actual_source_claim_adapter_candidate_status_ref": status_ref,
        "dri_op09_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP09_ALLOWED_STATUS_REFS),
        "dri_op09_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP09_ALLOWED_STATUS_REFS),
        "dri_op09_adapter_candidate_materialized_bodyfree": ready,
        "dri_op09_wait_for_final_scan_clear": waiting,
        "dri_op09_repair_required": repair,
        "dri_op09_blocked_before_adapter_candidate": blocked,
        "dri_op09_ready_to_provide_candidate_to_dhr_op04_manually": ready,
        "dri_op09_reason_refs": reasons,
        "dri_op09_reason_ref_count": len(reasons),
        "dri_op09_blocker_refs": blockers,
        "dri_op09_blocker_ref_count": len(blockers),
        "actual_review_execution_claimed_by_dri_op09": False,
        "actual_review_evidence_completed_by_dri_op09": False,
        "dhr_actual_source_claim_confirmed_by_dri_op09": False,
        "dhr_op04_called_by_dri_op09": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op09": False,
        "dmd_execution_started_by_dri_op09": False,
        "r52_actual_execution_started_by_dri_op09": False,
        "dri_op09_does_not_call_dhr_op04": True,
        "dri_op09_does_not_execute_dhr_reintake": True,
        "dri_op09_does_not_confirm_dhr_actual_source_claim": True,
        "dri_op09_does_not_execute_dmd_or_r52": True,
        "dri_op09_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op09_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op09_does_not_materialize_p8_question_spec": True,
        "downstream_auto_execution_allowed": False,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP09 body-free adapter candidate materialization contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP09")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP09_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP09_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP09")
    for field, count_field in (("adapter_candidate_dhr_op04_readable_key_refs", "adapter_candidate_dhr_op04_readable_key_ref_count"), ("external_actual_operation_evidence_claim_bodyfree_optional_key_refs", "external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count"), ("adapter_candidate_forbidden_payload_key_path_refs", "adapter_candidate_forbidden_payload_key_path_count"), ("adapter_candidate_body_like_value_path_refs", "adapter_candidate_body_like_value_path_count"), ("adapter_candidate_promotion_claim_refs", "adapter_candidate_promotion_claim_ref_count"), ("adapter_candidate_invalid_source_kind_refs", "adapter_candidate_invalid_source_kind_ref_count"), ("dri_op09_allowed_status_refs", "dri_op09_allowed_status_ref_count"), ("dri_op09_reason_refs", "dri_op09_reason_ref_count"), ("dri_op09_blocker_refs", "dri_op09_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 {count_field} changed")
    if tuple(data.get("dri_op09_allowed_status_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP09_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 allowed status refs changed")
    if tuple(data.get("adapter_candidate_dhr_op04_readable_key_refs") or ()) != P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 DHR-OP04 readable key refs changed")
    candidate = data.get("external_actual_operation_evidence_claim_bodyfree_optional")
    if data.get("external_actual_operation_evidence_claim_bodyfree_optional_present") is True:
        if not isinstance(candidate, Mapping):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 candidate must be a mapping when present")
        if tuple(candidate.keys()) != P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 candidate key refs changed")
        if candidate.get("schema_version") != P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 candidate schema changed")
        if candidate.get("material_kind") != P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_MATERIAL_KIND:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 candidate material kind changed")
        if candidate.get("source_kind_ref") != rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF or candidate.get("actual_source_claim_source_kind_ref") != rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 candidate source kind changed")
        for key in ("actual_source_claim_bodyfree", "actual_local_only_human_review_by_person_confirmed", "actual_human_review_executed_by_person", "body_free"):
            if candidate.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 candidate required true field changed: {key}")
        for key in ("dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
            if candidate.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 candidate downstream flag promoted: {key}")
        for key in ("operation_receipt_bodyfree_ref", "disposal_purge_receipt_bodyfree_ref", "rsr_op15_branch_ref", "rsr_op16_status_ref"):
            if not candidate.get(key):
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 candidate required ref missing: {key}")
        if candidate.get("sanitized_review_result_row_count") != rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or candidate.get("rating_row_count") != rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or candidate.get("question_need_observation_row_count") != rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 candidate row counts changed")
    elif candidate != {}:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 absent candidate must stay empty")
    for key in ("adapter_candidate_not_dhr_confirmed", "adapter_candidate_does_not_call_dhr_op04", "adapter_candidate_does_not_execute_dhr_reintake", "dri_op09_does_not_call_dhr_op04", "dri_op09_does_not_execute_dhr_reintake", "dri_op09_does_not_confirm_dhr_actual_source_claim", "dri_op09_does_not_execute_dmd_or_r52", "dri_op09_does_not_start_p5_p6_p8_p7_or_release", "dri_op09_does_not_change_api_db_rn_runtime_response_key", "dri_op09_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 required true boundary changed: {key}")
    for key in ("adapter_candidate_downstream_auto_execution_allowed", "downstream_auto_execution_allowed", "actual_review_execution_claimed_by_dri_op09", "actual_review_evidence_completed_by_dri_op09", "dhr_actual_source_claim_confirmed_by_dri_op09", "dhr_op04_called_by_dri_op09", "dhr_actual_source_claim_reintake_executed_by_dri_op09", "dmd_execution_started_by_dri_op09", "r52_actual_execution_started_by_dri_op09", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 downstream flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP09_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP09_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 implemented/not-yet steps changed")
    status_ref = data.get("dri_op09_status_ref")
    if status_ref != data.get("dhr_op04_external_actual_source_claim_adapter_candidate_status_ref"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 status alias changed")
    status_flags = [
        data.get("dri_op09_adapter_candidate_materialized_bodyfree") is True,
        data.get("dri_op09_wait_for_final_scan_clear") is True,
        data.get("dri_op09_repair_required") is True,
        data.get("dri_op09_blocked_before_adapter_candidate") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF:
        for key in ("op08_contract_valid", "op08_final_scan_clear_bodyfree", "op08_ready_for_dhr_op04_adapter_candidate_materialization", "op04_contract_valid", "op05_contract_valid", "op06_contract_valid", "op07_contract_valid", "external_actual_operation_evidence_claim_bodyfree_optional_present", "adapter_candidate_materialized", "adapter_candidate_materialized_bodyfree", "adapter_candidate_for_manual_dhr_op04_input_only", "actual_source_claim_bodyfree", "actual_local_only_human_review_by_person_confirmed", "actual_human_review_executed_by_person"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP09 ready branch required true changed: {key}")
        if data.get("source_kind_ref") != rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF or data.get("actual_source_claim_source_kind_ref") != rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 source kind changed")
        if data.get("sanitized_review_result_row_count") != rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("rating_row_count") != rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("question_need_observation_row_count") != rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 row counts changed")
        if data.get("adapter_candidate_forbidden_payload_key_path_refs") != [] or data.get("adapter_candidate_body_like_value_path_refs") != [] or data.get("adapter_candidate_promotion_claim_refs") != [] or data.get("adapter_candidate_invalid_source_kind_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 ready candidate cannot carry scan issues")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 ready next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF:
        if data.get("dri_op09_wait_for_final_scan_clear") is not True or data.get("external_actual_operation_evidence_claim_bodyfree_optional_present") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 wait branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF:
        if data.get("dri_op09_repair_required") is not True or not data.get("dri_op09_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 repair branch changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF:
        if data.get("dri_op09_blocked_before_adapter_candidate") is not True or not data.get("dri_op09_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 blocked branch changed")
    else:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP09 status ref is not allowed")
    return True




# DRI-OP10/OP11 additions: deterministic branch resolver and no-touch selected regression guard.
P7_R54_AHR_POST_RSR16_DRI_OP10_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op10_deterministic_branch_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP11_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op11_no_touch_selected_regression_guard.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:11]
)
P7_R54_AHR_POST_RSR16_DRI_OP10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[11:]
)
P7_R54_AHR_POST_RSR16_DRI_OP11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[:12]
)
P7_R54_AHR_POST_RSR16_DRI_OP11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS[12:]
)

P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF: Final = (
    "DRI_STATUS_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION"
)
P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF: Final = (
    "DRI_STATUS_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS"
)
P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF: Final = (
    "DRI_STATUS_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL"
)
P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF: Final = (
    "DRI_STATUS_BODYFREE_LEAK_OR_PROMOTION_BLOCKED"
)
P7_R54_AHR_POST_RSR16_DRI_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF: Final = (
    "DRI_STATUS_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_RSR16_DRI_OP10_ALLOWED_BRANCH_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF,
    P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF,
    P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF,
    P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF,
    P7_R54_AHR_POST_RSR16_DRI_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_DRI_REF: Final = (
    "manual_hold_after_dri_without_downstream_promotion"
)

P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_NO_TOUCH_GUARD_CLEAR_REF: Final = (
    "DRI_OP11_NO_TOUCH_SELECTED_REGRESSION_GUARD_CLEAR"
)
P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF: Final = (
    "DRI_OP11_REPAIR_CHANGED_FILE_REFS_OR_OP10_BEFORE_RESULT_MEMO"
)
P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF: Final = (
    "DRI_OP11_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE"
)
P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_NO_TOUCH_GUARD_CLEAR_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP11_NO_TOUCH_GUARD_REF: Final = (
    "repair_dri_op11_changed_file_refs_or_op10_before_result_memo"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP11_NO_TOUCH_GUARD_REF: Final = (
    "blocked_dri_op11_no_touch_or_p8_surface_change"
)

P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_CHANGED_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705.py",
    "mashos-api/ai/tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_op11_20260705.py",
    "mashos-api/ai/tests/R54_AHR_PostRSR16_DHRActualSourceClaimReintake_DRI_OP00_OP11_Result_20260705.md",
    "mashos-api/ai/tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_20260705.py",
    "mashos-api/ai/tests/R54_AHR_PostRSR16_DHRActualSourceClaimReintake_DRI_OP00_OP12_Result_20260705.md",
)
P7_R54_AHR_POST_RSR16_DRI_OP11_SELECTED_REGRESSION_REQUIRED_REFS: Final[tuple[str, ...]] = (
    "dri_op10_op11_target_tests_required",
    "dri_op00_op09_incoming_confirmation_required",
    "rsr_selected_regression_required",
    "dhr_selected_regression_required",
    "services_ai_inference_compileall_required",
    "rn_no_touch_grep_required",
)
P7_R54_AHR_POST_RSR16_DRI_OP11_BLOCKED_CHANGED_FILE_TOKEN_REFS: Final[tuple[str, ...]] = (
    "/Cocolon/",
    "Cocolon/",
    "/app/",
    "/api/",
    "/db/",
    "/database/",
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

P7_R54_AHR_POST_RSR16_DRI_OP10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_schema_version", "op09_material_ref", "op09_contract_valid", "op09_status_ref", "op09_adapter_candidate_materialized_bodyfree", "op09_ready_to_provide_candidate_to_dhr_op04_manually", "op09_external_actual_operation_evidence_claim_bodyfree_optional_present",
    "op09_adapter_candidate_key_refs", "op09_adapter_candidate_key_ref_count", "op09_next_required_step",
    "branch_input_forbidden_payload_key_path_refs", "branch_input_forbidden_payload_key_path_count", "branch_input_body_like_value_path_refs", "branch_input_body_like_value_path_count", "branch_input_promotion_claim_refs", "branch_input_promotion_claim_ref_count", "branch_input_invalid_source_kind_refs", "branch_input_invalid_source_kind_ref_count",
    "dri_branch_ref", "dri_allowed_branch_refs", "dri_allowed_branch_ref_count", "next_required_step", "branch_reason_refs", "branch_reason_ref_count", "branch_blocker_refs", "branch_blocker_ref_count",
    "ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution", "waiting_for_supplied_receipts_or_complete_candidate", "repair_required_before_dhr_reintake_material", "bodyfree_leak_or_promotion_blocked", "manual_hold_unresolved_no_promotion",
    "adapter_candidate_materialized", "adapter_candidate_for_manual_dhr_op04_input_only", "adapter_candidate_not_dhr_confirmed", "downstream_auto_execution_allowed",
    "actual_review_execution_claimed_by_dri_op10", "actual_review_evidence_completed_by_dri_op10", "dhr_actual_source_claim_confirmed_by_dri_op10", "dhr_op04_called_by_dri_op10", "dhr_actual_source_claim_reintake_executed_by_dri_op10", "dmd_execution_started_by_dri_op10", "r52_actual_execution_started_by_dri_op10",
    "dri_op10_selects_exactly_one_branch", "dri_op10_does_not_call_dhr_op04", "dri_op10_does_not_execute_dhr_reintake", "dri_op10_does_not_confirm_dhr_actual_source_claim", "dri_op10_does_not_execute_dmd_or_r52", "dri_op10_does_not_start_p5_p6_p8_p7_or_release", "dri_op10_does_not_change_api_db_rn_runtime_response_key", "dri_op10_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RSR16_DRI_OP11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_schema_version", "op10_material_ref", "op10_contract_valid", "op10_branch_ref", "op10_next_required_step", "op10_ready_for_dhr_material", "op10_waiting", "op10_repair_required", "op10_blocked", "op10_manual_hold",
    "changed_file_refs", "changed_file_ref_count", "allowed_changed_file_refs", "allowed_changed_file_ref_count", "disallowed_changed_file_refs", "disallowed_changed_file_ref_count", "blocked_changed_file_refs", "blocked_changed_file_ref_count",
    "rn_no_touch_grep_match_refs", "rn_no_touch_grep_match_ref_count", "selected_regression_required", "selected_regression_required_refs", "selected_regression_required_ref_count",
    "api_change_detected", "db_change_detected", "rn_change_detected", "runtime_change_detected", "response_key_change_detected", "public_response_top_level_key_added_detected", "p8_question_surface_change_detected",
    "dri_op11_status_ref", "no_touch_selected_regression_guard_status_ref", "dri_op11_allowed_status_refs", "dri_op11_allowed_status_ref_count", "dri_op11_no_touch_guard_clear", "dri_op11_repair_required", "dri_op11_blocked_no_touch_or_p8_surface_change",
    "dri_op11_reason_refs", "dri_op11_reason_ref_count", "dri_op11_blocker_refs", "dri_op11_blocker_ref_count",
    "api_change_allowed_here", "db_change_allowed_here", "rn_change_allowed_here", "runtime_change_allowed_here", "response_key_change_allowed_here", "p8_question_surface_change_allowed_here",
    "changed_file_scope_limited_to_helper_tests_result_memo", "dri_op11_does_not_call_dhr_op04", "dri_op11_does_not_execute_dhr_reintake", "dri_op11_does_not_confirm_dhr_actual_source_claim", "dri_op11_does_not_execute_dmd_or_r52", "dri_op11_does_not_start_p5_p6_p8_p7_or_release", "dri_op11_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution", "downstream_auto_execution_allowed",
    "actual_review_execution_claimed_by_dri_op11", "actual_review_evidence_completed_by_dri_op11", "dhr_actual_source_claim_confirmed_by_dri_op11", "dhr_op04_called_by_dri_op11", "dhr_actual_source_claim_reintake_executed_by_dri_op11", "dmd_execution_started_by_dri_op11", "r52_actual_execution_started_by_dri_op11",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op10_status_reason_blocker_next(
    *,
    op09_present: bool,
    op09_contract_valid: bool,
    op09_status_ref: str,
    op09_candidate_ready: bool,
    scan_issue_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    if scan_issue_refs or op09_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF:
        blockers = ["dri_op09_or_branch_input_bodyfree_promotion_or_source_kind_blocked"] + list(scan_issue_refs)
        return (
            P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF,
            ["dri_op10_blocks_before_dhr_op04_because_bodyfree_promotion_or_source_kind_boundary_failed"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP03_INVENTORY_REF,
        )
    if not op09_present:
        return (
            P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF,
            ["dri_op10_waits_because_dri_op09_adapter_material_is_missing"],
            ["dri_op09_material_missing"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if not op09_contract_valid:
        return (
            P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF,
            ["dri_op10_repairs_because_dri_op09_contract_is_invalid"],
            ["dri_op09_contract_invalid"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF,
        )
    if op09_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF,
            ["dri_op10_waits_because_dri_op09_is_waiting_for_final_scan_or_supplied_material"],
            ["dri_op09_waiting_for_final_scan_clear_or_supplied_material"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF,
        )
    if op09_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF:
        return (
            P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF,
            ["dri_op10_repairs_because_dri_op09_adapter_material_requires_repair"],
            ["dri_op09_repair_required_before_dhr_op04_adapter"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF,
        )
    if op09_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF and op09_candidate_ready:
        return (
            P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF,
            ["dri_op10_ready_branch_selected_with_bodyfree_adapter_candidate_manual_dhr_op04_boundary"],
            [],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
        ["dri_op10_manual_hold_for_unexpected_dri_op09_branch_without_downstream_promotion"],
        ["dri_op09_unexpected_status_or_candidate_readiness_mismatch"],
        P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_DRI_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
    *,
    dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate: Mapping[str, Any] | None = None,
    dhr_op04_external_actual_source_claim_adapter_candidate: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP10 deterministic branch resolver material without downstream execution."""

    op09_input = dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate if dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate is not None else dhr_op04_external_actual_source_claim_adapter_candidate
    op09 = op09_input if isinstance(op09_input, Mapping) else {}
    op09_present = isinstance(op09_input, Mapping)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op09.get("review_session_id"))
    try:
        op09_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(op09) is True
    except ValueError:
        op09_contract_valid = False
    op09_status_ref = _clean_ref(op09.get("dri_op09_status_ref"), default="dri_op09_status_missing", max_length=260)
    candidate = op09.get("external_actual_operation_evidence_claim_bodyfree_optional") if isinstance(op09.get("external_actual_operation_evidence_claim_bodyfree_optional"), Mapping) else {}
    candidate_key_refs = _dedupe_clean_refs(list(candidate.keys()), max_length=220)
    op09_candidate_ready = bool(
        op09.get("dri_op09_adapter_candidate_materialized_bodyfree") is True
        and op09.get("dri_op09_ready_to_provide_candidate_to_dhr_op04_manually") is True
        and op09.get("external_actual_operation_evidence_claim_bodyfree_optional_present") is True
        and candidate
    )
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op09, path="dri_op09"), max_length=360)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op09, path="dri_op09"), max_length=360)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op09, path="dri_op09"), max_length=360)
    invalid_source_kind_refs = _dedupe_clean_refs(_scan_invalid_source_kind_paths(op09, path="dri_op09"), max_length=360)
    scan_issue_refs = _dedupe_clean_refs(list(forbidden_paths) + list(body_like_paths) + list(promotion_claims) + list(invalid_source_kind_refs), max_length=360)
    branch_ref, reasons, blockers, next_required_step = _op10_status_reason_blocker_next(
        op09_present=op09_present,
        op09_contract_valid=op09_contract_valid,
        op09_status_ref=op09_status_ref,
        op09_candidate_ready=op09_candidate_ready,
        scan_issue_refs=scan_issue_refs,
    )
    ready = branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF
    waiting = branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF
    repair = branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF
    blocked = branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF
    manual_hold = branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP10_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP10_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op09_schema_version": op09.get("schema_version"),
        "op09_material_ref": _clean_ref(op09.get("material_id"), default="dri_op09_material_missing", max_length=260),
        "op09_contract_valid": op09_contract_valid,
        "op09_status_ref": op09_status_ref,
        "op09_adapter_candidate_materialized_bodyfree": op09.get("dri_op09_adapter_candidate_materialized_bodyfree") is True,
        "op09_ready_to_provide_candidate_to_dhr_op04_manually": op09.get("dri_op09_ready_to_provide_candidate_to_dhr_op04_manually") is True,
        "op09_external_actual_operation_evidence_claim_bodyfree_optional_present": op09.get("external_actual_operation_evidence_claim_bodyfree_optional_present") is True,
        "op09_adapter_candidate_key_refs": candidate_key_refs,
        "op09_adapter_candidate_key_ref_count": len(candidate_key_refs),
        "op09_next_required_step": _clean_ref(op09.get("next_required_step"), default="dri_op09_next_required_step_missing", max_length=260),
        "branch_input_forbidden_payload_key_path_refs": forbidden_paths,
        "branch_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "branch_input_body_like_value_path_refs": body_like_paths,
        "branch_input_body_like_value_path_count": len(body_like_paths),
        "branch_input_promotion_claim_refs": promotion_claims,
        "branch_input_promotion_claim_ref_count": len(promotion_claims),
        "branch_input_invalid_source_kind_refs": invalid_source_kind_refs,
        "branch_input_invalid_source_kind_ref_count": len(invalid_source_kind_refs),
        "dri_branch_ref": branch_ref,
        "dri_allowed_branch_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP10_ALLOWED_BRANCH_REFS),
        "dri_allowed_branch_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP10_ALLOWED_BRANCH_REFS),
        "next_required_step": next_required_step,
        "branch_reason_refs": reasons,
        "branch_reason_ref_count": len(reasons),
        "branch_blocker_refs": blockers,
        "branch_blocker_ref_count": len(blockers),
        "ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution": ready,
        "waiting_for_supplied_receipts_or_complete_candidate": waiting,
        "repair_required_before_dhr_reintake_material": repair,
        "bodyfree_leak_or_promotion_blocked": blocked,
        "manual_hold_unresolved_no_promotion": manual_hold,
        "adapter_candidate_materialized": ready,
        "adapter_candidate_for_manual_dhr_op04_input_only": ready,
        "adapter_candidate_not_dhr_confirmed": True,
        "downstream_auto_execution_allowed": False,
        "actual_review_execution_claimed_by_dri_op10": False,
        "actual_review_evidence_completed_by_dri_op10": False,
        "dhr_actual_source_claim_confirmed_by_dri_op10": False,
        "dhr_op04_called_by_dri_op10": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op10": False,
        "dmd_execution_started_by_dri_op10": False,
        "r52_actual_execution_started_by_dri_op10": False,
        "dri_op10_selects_exactly_one_branch": True,
        "dri_op10_does_not_call_dhr_op04": True,
        "dri_op10_does_not_execute_dhr_reintake": True,
        "dri_op10_does_not_confirm_dhr_actual_source_claim": True,
        "dri_op10_does_not_execute_dmd_or_r52": True,
        "dri_op10_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op10_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op10_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP10_NOT_YET_IMPLEMENTED_STEPS),
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP10 deterministic branch resolver contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP10")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP10_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP10_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP10_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP10")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP10_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP10_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 implemented/not-yet steps changed")
    for key in ("dri_op10_selects_exactly_one_branch", "dri_op10_does_not_call_dhr_op04", "dri_op10_does_not_execute_dhr_reintake", "dri_op10_does_not_confirm_dhr_actual_source_claim", "dri_op10_does_not_execute_dmd_or_r52", "dri_op10_does_not_start_p5_p6_p8_p7_or_release", "dri_op10_does_not_change_api_db_rn_runtime_response_key", "dri_op10_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP10 required true boundary changed: {key}")
    for key in ("downstream_auto_execution_allowed", "actual_review_execution_claimed_by_dri_op10", "actual_review_evidence_completed_by_dri_op10", "dhr_actual_source_claim_confirmed_by_dri_op10", "dhr_op04_called_by_dri_op10", "dhr_actual_source_claim_reintake_executed_by_dri_op10", "dmd_execution_started_by_dri_op10", "r52_actual_execution_started_by_dri_op10", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP10 downstream flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 not-claimed boundary must stay false")
    if data.get("dri_branch_ref") not in P7_R54_AHR_POST_RSR16_DRI_OP10_ALLOWED_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 branch ref is not allowed")
    flags = [
        data.get("ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution") is True,
        data.get("waiting_for_supplied_receipts_or_complete_candidate") is True,
        data.get("repair_required_before_dhr_reintake_material") is True,
        data.get("bodyfree_leak_or_promotion_blocked") is True,
        data.get("manual_hold_unresolved_no_promotion") is True,
    ]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 exactly one branch flag must be true")
    branch_ref = data.get("dri_branch_ref")
    if branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF:
        for key in ("op09_contract_valid", "op09_adapter_candidate_materialized_bodyfree", "op09_ready_to_provide_candidate_to_dhr_op04_manually", "op09_external_actual_operation_evidence_claim_bodyfree_optional_present", "adapter_candidate_materialized", "adapter_candidate_for_manual_dhr_op04_input_only"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP10 ready branch required true changed: {key}")
        if data.get("branch_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 ready next step changed")
    elif branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF:
        if data.get("waiting_for_supplied_receipts_or_complete_candidate") is not True or data.get("adapter_candidate_materialized") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 wait branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 wait next step changed")
    elif branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF:
        if data.get("repair_required_before_dhr_reintake_material") is not True or not data.get("branch_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 repair next step changed")
    elif branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF:
        if data.get("bodyfree_leak_or_promotion_blocked") is not True or not data.get("branch_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP03_INVENTORY_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 blocked next step changed")
    elif branch_ref == P7_R54_AHR_POST_RSR16_DRI_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF:
        if data.get("manual_hold_unresolved_no_promotion") is not True or data.get("adapter_candidate_materialized") is not False:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 manual hold branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_DRI_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP10 manual hold next step changed")
    return True


def _normalize_changed_file_ref(value: Any) -> str:
    ref = _clean_ref(value, default="", max_length=360)
    return ref.replace("\\", "/")


def _op11_changed_file_partition(changed_file_refs: Sequence[Any]) -> tuple[list[str], list[str], list[str]]:
    changed = _dedupe_clean_refs([_normalize_changed_file_ref(value) for value in changed_file_refs], max_length=360)
    allowed_suffixes = tuple(P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_CHANGED_FILE_REFS)
    disallowed: list[str] = []
    blocked: list[str] = []
    for ref in changed:
        if not any(ref == allowed or ref.endswith(allowed) for allowed in allowed_suffixes):
            disallowed.append(ref)
        ref_lower = ref.lower()
        if any(token.lower() in ref_lower for token in P7_R54_AHR_POST_RSR16_DRI_OP11_BLOCKED_CHANGED_FILE_TOKEN_REFS):
            if not any(ref == allowed or ref.endswith(allowed) for allowed in allowed_suffixes):
                blocked.append(ref)
    return changed, _dedupe_clean_refs(disallowed, max_length=360), _dedupe_clean_refs(blocked, max_length=360)


def _op11_status_reason_blocker_next(
    *,
    op10_contract_valid: bool,
    changed_file_refs: Sequence[str],
    disallowed_changed_file_refs: Sequence[str],
    blocked_changed_file_refs: Sequence[str],
    rn_no_touch_grep_match_refs: Sequence[str],
    no_touch_change_flags: Mapping[str, bool],
) -> tuple[str, list[str], list[str], str]:
    true_no_touch_changes = [key for key, value in no_touch_change_flags.items() if value is True]
    if blocked_changed_file_refs or rn_no_touch_grep_match_refs or true_no_touch_changes:
        blockers = list(blocked_changed_file_refs) + list(rn_no_touch_grep_match_refs) + true_no_touch_changes
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF,
            ["dri_op11_blocks_because_no_touch_or_p8_surface_boundary_changed"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP11_NO_TOUCH_GUARD_REF,
        )
    if not op10_contract_valid or not changed_file_refs or disallowed_changed_file_refs:
        blockers: list[str] = []
        if not op10_contract_valid:
            blockers.append("dri_op10_contract_invalid")
        if not changed_file_refs:
            blockers.append("changed_file_refs_missing_for_no_touch_guard")
        blockers.extend(disallowed_changed_file_refs)
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF,
            ["dri_op11_repairs_changed_file_refs_or_op10_before_result_memo"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP11_NO_TOUCH_GUARD_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_NO_TOUCH_GUARD_CLEAR_REF,
        ["dri_op11_no_touch_guard_clear_for_helper_tests_result_memo_only"],
        [],
        P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard(
    *,
    dri_op10_deterministic_branch_resolver: Mapping[str, Any] | None = None,
    deterministic_branch_resolver: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] | None = None,
    rn_no_touch_grep_match_refs: Sequence[Any] | None = None,
    api_change_detected: bool = False,
    db_change_detected: bool = False,
    rn_change_detected: bool = False,
    runtime_change_detected: bool = False,
    response_key_change_detected: bool = False,
    public_response_top_level_key_added_detected: bool = False,
    p8_question_surface_change_detected: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP11 no-touch selected regression guard material."""

    op10_input = dri_op10_deterministic_branch_resolver if dri_op10_deterministic_branch_resolver is not None else deterministic_branch_resolver
    op10 = op10_input if isinstance(op10_input, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op10.get("review_session_id"))
    try:
        op10_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(op10) is True
    except ValueError:
        op10_contract_valid = False
    changed, disallowed, blocked = _op11_changed_file_partition(changed_file_refs or [])
    rn_grep_refs = _dedupe_clean_refs(list(rn_no_touch_grep_match_refs or []), max_length=360)
    no_touch_change_flags = {
        "api_change_detected": api_change_detected is True,
        "db_change_detected": db_change_detected is True,
        "rn_change_detected": rn_change_detected is True,
        "runtime_change_detected": runtime_change_detected is True,
        "response_key_change_detected": response_key_change_detected is True,
        "public_response_top_level_key_added_detected": public_response_top_level_key_added_detected is True,
        "p8_question_surface_change_detected": p8_question_surface_change_detected is True,
    }
    status_ref, reasons, blockers, next_required_step = _op11_status_reason_blocker_next(
        op10_contract_valid=op10_contract_valid,
        changed_file_refs=changed,
        disallowed_changed_file_refs=disallowed,
        blocked_changed_file_refs=blocked,
        rn_no_touch_grep_match_refs=rn_grep_refs,
        no_touch_change_flags=no_touch_change_flags,
    )
    clear = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_NO_TOUCH_GUARD_CLEAR_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF
    blocked_status = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF
    op10_branch_ref = _clean_ref(op10.get("dri_branch_ref"), default="dri_op10_branch_missing", max_length=260)
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP11_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP11_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op10_schema_version": op10.get("schema_version"),
        "op10_material_ref": _clean_ref(op10.get("material_id"), default="dri_op10_material_missing", max_length=260),
        "op10_contract_valid": op10_contract_valid,
        "op10_branch_ref": op10_branch_ref,
        "op10_next_required_step": _clean_ref(op10.get("next_required_step"), default="dri_op10_next_required_step_missing", max_length=260),
        "op10_ready_for_dhr_material": op10.get("ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution") is True,
        "op10_waiting": op10.get("waiting_for_supplied_receipts_or_complete_candidate") is True,
        "op10_repair_required": op10.get("repair_required_before_dhr_reintake_material") is True,
        "op10_blocked": op10.get("bodyfree_leak_or_promotion_blocked") is True,
        "op10_manual_hold": op10.get("manual_hold_unresolved_no_promotion") is True,
        "changed_file_refs": changed,
        "changed_file_ref_count": len(changed),
        "allowed_changed_file_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_CHANGED_FILE_REFS),
        "allowed_changed_file_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_CHANGED_FILE_REFS),
        "disallowed_changed_file_refs": disallowed,
        "disallowed_changed_file_ref_count": len(disallowed),
        "blocked_changed_file_refs": blocked,
        "blocked_changed_file_ref_count": len(blocked),
        "rn_no_touch_grep_match_refs": rn_grep_refs,
        "rn_no_touch_grep_match_ref_count": len(rn_grep_refs),
        "selected_regression_required": True,
        "selected_regression_required_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP11_SELECTED_REGRESSION_REQUIRED_REFS),
        "selected_regression_required_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP11_SELECTED_REGRESSION_REQUIRED_REFS),
        **no_touch_change_flags,
        "dri_op11_status_ref": status_ref,
        "no_touch_selected_regression_guard_status_ref": status_ref,
        "dri_op11_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_STATUS_REFS),
        "dri_op11_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_STATUS_REFS),
        "dri_op11_no_touch_guard_clear": clear,
        "dri_op11_repair_required": repair,
        "dri_op11_blocked_no_touch_or_p8_surface_change": blocked_status,
        "dri_op11_reason_refs": reasons,
        "dri_op11_reason_ref_count": len(reasons),
        "dri_op11_blocker_refs": blockers,
        "dri_op11_blocker_ref_count": len(blockers),
        "api_change_allowed_here": False,
        "db_change_allowed_here": False,
        "rn_change_allowed_here": False,
        "runtime_change_allowed_here": False,
        "response_key_change_allowed_here": False,
        "p8_question_surface_change_allowed_here": False,
        "changed_file_scope_limited_to_helper_tests_result_memo": clear,
        "dri_op11_does_not_call_dhr_op04": True,
        "dri_op11_does_not_execute_dhr_reintake": True,
        "dri_op11_does_not_confirm_dhr_actual_source_claim": True,
        "dri_op11_does_not_execute_dmd_or_r52": True,
        "dri_op11_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op11_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "downstream_auto_execution_allowed": False,
        "actual_review_execution_claimed_by_dri_op11": False,
        "actual_review_evidence_completed_by_dri_op11": False,
        "dhr_actual_source_claim_confirmed_by_dri_op11": False,
        "dhr_op04_called_by_dri_op11": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op11": False,
        "dmd_execution_started_by_dri_op11": False,
        "r52_actual_execution_started_by_dri_op11": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP11 no-touch selected regression guard contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP11")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP11_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP11_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP11_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP11")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP11_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP11_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 implemented/not-yet steps changed")
    for key in ("api_change_allowed_here", "db_change_allowed_here", "rn_change_allowed_here", "runtime_change_allowed_here", "response_key_change_allowed_here", "p8_question_surface_change_allowed_here", "downstream_auto_execution_allowed", "actual_review_execution_claimed_by_dri_op11", "actual_review_evidence_completed_by_dri_op11", "dhr_actual_source_claim_confirmed_by_dri_op11", "dhr_op04_called_by_dri_op11", "dhr_actual_source_claim_reintake_executed_by_dri_op11", "dmd_execution_started_by_dri_op11", "r52_actual_execution_started_by_dri_op11", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP11 downstream/no-touch flag promoted: {key}")
    for key in ("selected_regression_required", "dri_op11_does_not_call_dhr_op04", "dri_op11_does_not_execute_dhr_reintake", "dri_op11_does_not_confirm_dhr_actual_source_claim", "dri_op11_does_not_execute_dmd_or_r52", "dri_op11_does_not_start_p5_p6_p8_p7_or_release", "dri_op11_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP11 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 not-claimed boundary must stay false")
    status_ref = data.get("dri_op11_status_ref")
    if status_ref != data.get("no_touch_selected_regression_guard_status_ref") or status_ref not in P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 status ref is not allowed")
    flags = [
        data.get("dri_op11_no_touch_guard_clear") is True,
        data.get("dri_op11_repair_required") is True,
        data.get("dri_op11_blocked_no_touch_or_p8_surface_change") is True,
    ]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 exactly one status flag must be true")
    detected_change_flags = ("api_change_detected", "db_change_detected", "rn_change_detected", "runtime_change_detected", "response_key_change_detected", "public_response_top_level_key_added_detected", "p8_question_surface_change_detected")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_NO_TOUCH_GUARD_CLEAR_REF:
        if data.get("op10_contract_valid") is not True or data.get("changed_file_scope_limited_to_helper_tests_result_memo") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 clear branch requires valid op10 and changed file scope")
        if data.get("disallowed_changed_file_refs") != [] or data.get("blocked_changed_file_refs") != [] or data.get("rn_no_touch_grep_match_refs") != [] or data.get("dri_op11_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 clear branch cannot carry blockers")
        for key in detected_change_flags:
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP11 clear branch detected change flag promoted: {key}")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 clear next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF:
        if data.get("dri_op11_repair_required") is not True or not data.get("dri_op11_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP11_NO_TOUCH_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF:
        if data.get("dri_op11_blocked_no_touch_or_p8_surface_change") is not True or not data.get("dri_op11_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP11_NO_TOUCH_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP11 blocked next step changed")
    return True


# DRI-OP12 additions: body-free result memo / target tests / selected regression closure.
P7_R54_AHR_POST_RSR16_DRI_OP12_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rsr16.dri."
    "op12_result_memo_tests_selected_regression_closure.bodyfree.v1"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_STEP_REFS
)
P7_R54_AHR_POST_RSR16_DRI_OP12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF: Final = (
    "DRI_OP12_RESULT_MEMO_TESTS_SELECTED_REGRESSION_CLOSED_BODYFREE"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF: Final = (
    "DRI_OP12_WAIT_FOR_OP11_NO_TOUCH_GUARD_OR_VERIFICATION_SUMMARIES"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF: Final = (
    "DRI_OP12_REPAIR_RESULT_MEMO_TESTS_OR_SELECTED_REGRESSION_SUMMARY"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF: Final = (
    "DRI_OP12_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF,
    P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF,
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP12_VERIFICATION_SUMMARIES_REF: Final = (
    "wait_for_dri_op11_no_touch_guard_or_target_tests_selected_regression_compileall_summaries"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP12_RESULT_MEMO_REF: Final = (
    "repair_dri_op12_result_memo_tests_or_selected_regression_summary"
)
P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP12_RESULT_MEMO_REF: Final = (
    "blocked_dri_op12_bodyfree_leak_promotion_or_no_touch_change"
)
P7_R54_AHR_POST_RSR16_DRI_OP12_UNVERIFIED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green_not_claimed_by_dri_op12",
    "rn_real_device_modal_not_verified_by_dri_op12",
    "actual_local_only_human_review_not_executed_by_dri_op12",
    "dhr_op04_not_called_by_dri_op12",
    "dhr_actual_source_claim_not_confirmed_by_dri_op12",
    "dhr_actual_source_claim_reintake_not_executed_by_dri_op12",
    "dmd_not_executed_by_dri_op12",
    "r52_not_executed_by_dri_op12",
    "p8_question_design_not_started_by_dri_op12",
    "p7_not_completed_by_dri_op12",
    "release_not_allowed_by_dri_op12",
)
P7_R54_AHR_POST_RSR16_DRI_OP12_RESULT_MEMO_OMITTED_BODY_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "raw_input",
    "returned_surface_body",
    "reviewer_free_text",
    "question_text",
    "draft_question_text",
    "local_path",
    "path_hash",
    "body_hash",
    "terminal_output_body",
)
P7_R54_AHR_POST_RSR16_DRI_OP12_SELECTED_REGRESSION_REQUIRED_REFS: Final[tuple[str, ...]] = (
    "dri_op00_op12_target_tests_required",
    "rsr_selected_regression_required",
    "dhr_selected_regression_required",
    "services_ai_inference_compileall_required",
    "rn_no_touch_grep_required",
    "zip_integrity_required",
)

P7_R54_AHR_POST_RSR16_DRI_OP12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_schema_version", "op11_material_ref", "op11_contract_valid", "op11_status_ref", "op11_no_touch_guard_clear", "op11_next_required_step", "op11_changed_file_scope_limited_to_helper_tests_result_memo",
    "op10_branch_ref", "op10_next_required_step", "op10_ready_for_dhr_material", "op10_waiting", "op10_repair_required", "op10_blocked", "op10_manual_hold",
    "selected_dri_branch_ref", "selected_dri_next_required_step", "selected_dri_branch_is_ready_material_only", "selected_dri_branch_is_waiting", "selected_dri_branch_is_repair", "selected_dri_branch_is_blocked", "selected_dri_branch_is_manual_hold",
    "target_tests_summary_present", "target_tests_summary_ref", "target_tests_passed_count", "target_tests_failed_count", "target_tests_error_count", "target_tests_all_required_green", "target_tests_summary_bodyfree",
    "selected_regression_summary_present", "selected_regression_summary_ref", "selected_regression_passed_count", "selected_regression_failed_count", "selected_regression_error_count", "selected_regression_all_required_green", "rsr_selected_regression_passed_count", "dhr_selected_regression_passed_count", "selected_regression_summary_bodyfree",
    "compileall_summary_present", "compileall_summary_ref", "services_ai_inference_compileall_ok", "compileall_summary_bodyfree",
    "changed_file_refs", "changed_file_ref_count", "final_changed_file_refs_bodyfree_scoped", "rn_no_touch_grep_match_refs", "rn_no_touch_grep_match_ref_count",
    "verification_summary_required_refs", "verification_summary_required_ref_count", "unverified_boundary_refs", "unverified_boundary_ref_count", "result_memo_omitted_body_refs", "result_memo_omitted_body_ref_count", "no_promotion_refs", "no_promotion_ref_count",
    "result_memo_input_forbidden_payload_key_path_refs", "result_memo_input_forbidden_payload_key_path_count", "result_memo_input_body_like_value_path_refs", "result_memo_input_body_like_value_path_count", "result_memo_input_promotion_claim_refs", "result_memo_input_promotion_claim_ref_count",
    "dri_op12_status_ref", "result_memo_tests_selected_regression_closure_status_ref", "dri_op12_allowed_status_refs", "dri_op12_allowed_status_ref_count", "dri_op12_result_memo_bodyfree_closed", "dri_op12_waiting_for_op11_or_verification_summaries", "dri_op12_repair_required", "dri_op12_bodyfree_leak_or_promotion_blocked",
    "dri_op12_reason_refs", "dri_op12_reason_ref_count", "dri_op12_blocker_refs", "dri_op12_blocker_ref_count",
    "result_memo_closure_is_not_actual_review_complete", "result_memo_closure_is_not_dhr_actual_source_claim_confirmed", "result_memo_closure_is_not_dhr_op04_call", "result_memo_closure_is_not_dhr_reintake_execution", "result_memo_closure_is_not_p8_start", "result_memo_closure_is_not_p7_complete", "result_memo_closure_is_not_release_ready",
    "dri_op12_does_not_call_dhr_op04", "dri_op12_does_not_execute_dhr_reintake", "dri_op12_does_not_confirm_dhr_actual_source_claim", "dri_op12_does_not_execute_dmd_or_r52", "dri_op12_does_not_start_p5_p6_p8_p7_or_release", "dri_op12_does_not_change_api_db_rn_runtime_response_key", "dri_op12_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution", "downstream_auto_execution_allowed",
    "actual_review_execution_claimed_by_dri_op12", "actual_review_evidence_completed_by_dri_op12", "dhr_actual_source_claim_confirmed_by_dri_op12", "dhr_op04_called_by_dri_op12", "dhr_actual_source_claim_reintake_executed_by_dri_op12", "dmd_execution_started_by_dri_op12", "r52_actual_execution_started_by_dri_op12",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_rsr16_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RSR16_DRI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _summary_int(summary: Mapping[str, Any], *keys: str) -> int:
    for key in keys:
        value = summary.get(key)
        if isinstance(value, bool):
            continue
        try:
            if value is not None:
                return max(0, int(value))
        except (TypeError, ValueError):
            continue
    return 0


def _summary_bool(summary: Mapping[str, Any], *keys: str) -> bool:
    return any(summary.get(key) is True for key in keys)


def _summary_ref(summary: Mapping[str, Any] | None, *, default: str) -> str:
    if not isinstance(summary, Mapping):
        return default
    return _clean_ref(summary.get("summary_ref") or summary.get("material_id") or summary.get("summary_id"), default=default, max_length=260)


def _target_tests_green(summary: Mapping[str, Any] | None) -> bool:
    if not isinstance(summary, Mapping):
        return False
    failed = _summary_int(summary, "failed_count", "target_tests_failed_count")
    errors = _summary_int(summary, "error_count", "target_tests_error_count")
    passed = _summary_int(summary, "passed_count", "target_tests_passed_count", "dri_target_passed_count", "dri_op00_op12_target_passed_count")
    explicit = _summary_bool(summary, "all_required_target_tests_passed", "target_tests_all_required_green", "all_required_green", "green", "passed")
    return failed == 0 and errors == 0 and (explicit or passed > 0)


def _selected_regression_green(summary: Mapping[str, Any] | None) -> bool:
    if not isinstance(summary, Mapping):
        return False
    failed = _summary_int(summary, "failed_count", "selected_regression_failed_count")
    errors = _summary_int(summary, "error_count", "selected_regression_error_count")
    passed = _summary_int(summary, "passed_count", "selected_regression_passed_count", "combined_selected_regression_passed_count")
    rsr_passed = _summary_int(summary, "rsr_selected_regression_passed_count")
    dhr_passed = _summary_int(summary, "dhr_selected_regression_passed_count")
    explicit = _summary_bool(summary, "all_required_selected_regression_passed", "selected_regression_all_required_green", "all_required_green", "green", "passed")
    return failed == 0 and errors == 0 and (explicit or passed > 0 or (rsr_passed > 0 and dhr_passed > 0))


def _compileall_green(summary: Mapping[str, Any] | None) -> bool:
    if not isinstance(summary, Mapping):
        return False
    return _summary_bool(summary, "services_ai_inference_compileall_ok", "compileall_ok", "compileall_passed", "passed", "green", "ok")


def _op12_status_reason_blocker_next(
    *,
    op11_present: bool,
    op11_contract_valid: bool,
    op11_status_ref: str,
    op11_clear: bool,
    op10_next_required_step: str,
    target_present: bool,
    target_green: bool,
    selected_present: bool,
    selected_green: bool,
    compileall_present: bool,
    compileall_ok: bool,
    op10_repair_required: bool,
    op10_blocked: bool,
    leak_or_promotion_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    if leak_or_promotion_refs or op11_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF or op10_blocked:
        blockers = list(leak_or_promotion_refs)
        if op11_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF:
            blockers.append("dri_op11_no_touch_or_p8_surface_change_blocked")
        if op10_blocked:
            blockers.append("dri_op10_selected_branch_blocked_before_result_memo_closure")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF,
            ["dri_op12_blocks_before_result_memo_closure_because_bodyfree_promotion_or_no_touch_boundary_failed"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP12_RESULT_MEMO_REF,
        )
    if not op11_present:
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF,
            ["dri_op12_waits_because_dri_op11_no_touch_guard_is_missing"],
            ["dri_op11_no_touch_selected_regression_guard_missing"],
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP12_VERIFICATION_SUMMARIES_REF,
        )
    if not op11_contract_valid or op11_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF or op10_repair_required:
        blockers: list[str] = []
        if not op11_contract_valid:
            blockers.append("dri_op11_contract_invalid_before_result_memo")
        if op11_status_ref == P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF:
            blockers.append("dri_op11_repair_required_before_result_memo")
        if op10_repair_required:
            blockers.append("dri_op10_selected_branch_repair_required_before_result_memo")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF,
            ["dri_op12_repairs_because_op11_or_op10_summary_is_not_closable"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP12_RESULT_MEMO_REF,
        )
    if not op11_clear or not target_present or not selected_present or not compileall_present:
        blockers = []
        if not op11_clear:
            blockers.append("dri_op11_no_touch_guard_not_clear")
        if not target_present:
            blockers.append("target_tests_summary_missing")
        if not selected_present:
            blockers.append("selected_regression_summary_missing")
        if not compileall_present:
            blockers.append("compileall_summary_missing")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF,
            ["dri_op12_waits_for_op11_clear_target_tests_selected_regression_and_compileall_summaries"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP12_VERIFICATION_SUMMARIES_REF,
        )
    if not target_green or not selected_green or not compileall_ok:
        blockers = []
        if not target_green:
            blockers.append("target_tests_summary_not_green")
        if not selected_green:
            blockers.append("selected_regression_summary_not_green")
        if not compileall_ok:
            blockers.append("services_ai_inference_compileall_not_ok")
        return (
            P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF,
            ["dri_op12_repairs_because_tests_selected_regression_or_compileall_summary_is_not_green"],
            blockers,
            P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP12_RESULT_MEMO_REF,
        )
    return (
        P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF,
        ["dri_op12_closes_bodyfree_result_memo_target_tests_selected_regression_without_promotion"],
        [],
        op10_next_required_step or P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_MANUAL_HOLD_AFTER_DRI_REF,
    )


def build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure(
    *,
    dri_op11_no_touch_selected_regression_guard: Mapping[str, Any] | None = None,
    target_tests_summary: Mapping[str, Any] | None = None,
    selected_regression_summary: Mapping[str, Any] | None = None,
    compileall_summary: Mapping[str, Any] | None = None,
    changed_file_refs: Sequence[Any] = (),
    rn_no_touch_grep_match_refs: Sequence[Any] = (),
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DRI-OP12 body-free result memo / target tests / selected regression closure."""
    op11 = dri_op11_no_touch_selected_regression_guard if isinstance(dri_op11_no_touch_selected_regression_guard, Mapping) else None
    op11_map = op11 or {}
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else op11_map.get("review_session_id"))
    op11_contract_valid = False
    if op11 is not None:
        try:
            op11_contract_valid = assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(op11) is True
        except ValueError:
            op11_contract_valid = False
    target_present = isinstance(target_tests_summary, Mapping)
    selected_present = isinstance(selected_regression_summary, Mapping)
    compileall_present = isinstance(compileall_summary, Mapping)
    target_map = target_tests_summary if isinstance(target_tests_summary, Mapping) else {}
    selected_map = selected_regression_summary if isinstance(selected_regression_summary, Mapping) else {}
    compileall_map = compileall_summary if isinstance(compileall_summary, Mapping) else {}
    target_green = _target_tests_green(target_tests_summary)
    selected_green = _selected_regression_green(selected_regression_summary)
    compileall_ok = _compileall_green(compileall_summary)
    changed = _dedupe_clean_refs(changed_file_refs, max_length=260)
    changed_file_refs_bodyfree_scoped = bool(changed) and all(ref.endswith(P7_R54_AHR_POST_RSR16_DRI_OP11_ALLOWED_CHANGED_FILE_REFS) for ref in changed)
    changed_scope_blocker_refs = [] if changed_file_refs_bodyfree_scoped else (["changed_file_refs_outside_helper_tests_result_memo_scope"] if changed else [])
    rn_grep_refs = _dedupe_clean_refs(rn_no_touch_grep_match_refs, max_length=320)
    scan_inputs = {
        "dri_op11_no_touch_selected_regression_guard": op11_map,
        "target_tests_summary": target_map,
        "selected_regression_summary": selected_map,
        "compileall_summary": compileall_map,
    }
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(scan_inputs, path="dri_op12_inputs"), max_length=360)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(scan_inputs, path="dri_op12_inputs"), max_length=360)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(scan_inputs, path="dri_op12_inputs"), max_length=360)
    if rn_grep_refs:
        promotion_claims = _dedupe_clean_refs([*promotion_claims, "rn_no_touch_grep_match_refs_present_before_result_memo_closure"], max_length=360)
    if changed_scope_blocker_refs:
        promotion_claims = _dedupe_clean_refs([*promotion_claims, *changed_scope_blocker_refs], max_length=360)
    op11_status_ref = _clean_ref(op11_map.get("dri_op11_status_ref"), default="dri_op11_status_missing", max_length=260)
    op10_branch_ref = _clean_ref(op11_map.get("op10_branch_ref"), default="dri_op10_branch_missing", max_length=260)
    op10_next_required_step = _clean_ref(op11_map.get("op10_next_required_step"), default="dri_op10_next_required_step_missing", max_length=260)
    status_ref, reasons, blockers, next_required_step = _op12_status_reason_blocker_next(
        op11_present=op11 is not None,
        op11_contract_valid=op11_contract_valid,
        op11_status_ref=op11_status_ref,
        op11_clear=op11_map.get("dri_op11_no_touch_guard_clear") is True,
        op10_next_required_step=op10_next_required_step,
        target_present=target_present,
        target_green=target_green,
        selected_present=selected_present,
        selected_green=selected_green,
        compileall_present=compileall_present,
        compileall_ok=compileall_ok,
        op10_repair_required=op11_map.get("op10_repair_required") is True,
        op10_blocked=op11_map.get("op10_blocked") is True,
        leak_or_promotion_refs=[*forbidden_paths, *body_like_paths, *promotion_claims],
    )
    closed = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF
    waiting = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF
    repair = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF
    blocked = status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF
    return {
        "schema_version": P7_R54_AHR_POST_RSR16_DRI_OP12_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "step": P7_R54_AHR_POST_RSR16_DRI_STEP,
        "scope": P7_R54_AHR_POST_RSR16_DRI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RSR16_DRI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RSR16_DRI_PHASE,
        "material_id": "p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_20260705",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RSR16_DRI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_schema_version": op11_map.get("schema_version"),
        "op11_material_ref": _clean_ref(op11_map.get("material_id"), default="dri_op11_material_missing", max_length=260),
        "op11_contract_valid": op11_contract_valid,
        "op11_status_ref": op11_status_ref,
        "op11_no_touch_guard_clear": op11_map.get("dri_op11_no_touch_guard_clear") is True,
        "op11_next_required_step": _clean_ref(op11_map.get("next_required_step"), default="dri_op11_next_required_step_missing", max_length=260),
        "op11_changed_file_scope_limited_to_helper_tests_result_memo": op11_map.get("changed_file_scope_limited_to_helper_tests_result_memo") is True,
        "op10_branch_ref": op10_branch_ref,
        "op10_next_required_step": op10_next_required_step,
        "op10_ready_for_dhr_material": op11_map.get("op10_ready_for_dhr_material") is True,
        "op10_waiting": op11_map.get("op10_waiting") is True,
        "op10_repair_required": op11_map.get("op10_repair_required") is True,
        "op10_blocked": op11_map.get("op10_blocked") is True,
        "op10_manual_hold": op11_map.get("op10_manual_hold") is True,
        "selected_dri_branch_ref": op10_branch_ref,
        "selected_dri_next_required_step": op10_next_required_step,
        "selected_dri_branch_is_ready_material_only": op11_map.get("op10_ready_for_dhr_material") is True,
        "selected_dri_branch_is_waiting": op11_map.get("op10_waiting") is True,
        "selected_dri_branch_is_repair": op11_map.get("op10_repair_required") is True,
        "selected_dri_branch_is_blocked": op11_map.get("op10_blocked") is True,
        "selected_dri_branch_is_manual_hold": op11_map.get("op10_manual_hold") is True,
        "target_tests_summary_present": target_present,
        "target_tests_summary_ref": _summary_ref(target_tests_summary, default="target_tests_summary_missing"),
        "target_tests_passed_count": _summary_int(target_map, "passed_count", "target_tests_passed_count", "dri_target_passed_count", "dri_op00_op12_target_passed_count"),
        "target_tests_failed_count": _summary_int(target_map, "failed_count", "target_tests_failed_count"),
        "target_tests_error_count": _summary_int(target_map, "error_count", "target_tests_error_count"),
        "target_tests_all_required_green": target_green,
        "target_tests_summary_bodyfree": bool(target_map.get("body_free") is True or target_map.get("bodyfree") is True or target_green),
        "selected_regression_summary_present": selected_present,
        "selected_regression_summary_ref": _summary_ref(selected_regression_summary, default="selected_regression_summary_missing"),
        "selected_regression_passed_count": _summary_int(selected_map, "passed_count", "selected_regression_passed_count", "combined_selected_regression_passed_count"),
        "selected_regression_failed_count": _summary_int(selected_map, "failed_count", "selected_regression_failed_count"),
        "selected_regression_error_count": _summary_int(selected_map, "error_count", "selected_regression_error_count"),
        "selected_regression_all_required_green": selected_green,
        "rsr_selected_regression_passed_count": _summary_int(selected_map, "rsr_selected_regression_passed_count"),
        "dhr_selected_regression_passed_count": _summary_int(selected_map, "dhr_selected_regression_passed_count"),
        "selected_regression_summary_bodyfree": bool(selected_map.get("body_free") is True or selected_map.get("bodyfree") is True or selected_green),
        "compileall_summary_present": compileall_present,
        "compileall_summary_ref": _summary_ref(compileall_summary, default="compileall_summary_missing"),
        "services_ai_inference_compileall_ok": compileall_ok,
        "compileall_summary_bodyfree": bool(compileall_map.get("body_free") is True or compileall_map.get("bodyfree") is True or compileall_ok),
        "changed_file_refs": changed,
        "changed_file_ref_count": len(changed),
        "final_changed_file_refs_bodyfree_scoped": changed_file_refs_bodyfree_scoped,
        "rn_no_touch_grep_match_refs": rn_grep_refs,
        "rn_no_touch_grep_match_ref_count": len(rn_grep_refs),
        "verification_summary_required_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP12_SELECTED_REGRESSION_REQUIRED_REFS),
        "verification_summary_required_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP12_SELECTED_REGRESSION_REQUIRED_REFS),
        "unverified_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP12_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP12_UNVERIFIED_BOUNDARY_REFS),
        "result_memo_omitted_body_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP12_RESULT_MEMO_OMITTED_BODY_REFS),
        "result_memo_omitted_body_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP12_RESULT_MEMO_OMITTED_BODY_REFS),
        "no_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "no_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "result_memo_input_forbidden_payload_key_path_refs": forbidden_paths,
        "result_memo_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "result_memo_input_body_like_value_path_refs": body_like_paths,
        "result_memo_input_body_like_value_path_count": len(body_like_paths),
        "result_memo_input_promotion_claim_refs": promotion_claims,
        "result_memo_input_promotion_claim_ref_count": len(promotion_claims),
        "dri_op12_status_ref": status_ref,
        "result_memo_tests_selected_regression_closure_status_ref": status_ref,
        "dri_op12_allowed_status_refs": list(P7_R54_AHR_POST_RSR16_DRI_OP12_ALLOWED_STATUS_REFS),
        "dri_op12_allowed_status_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_OP12_ALLOWED_STATUS_REFS),
        "dri_op12_result_memo_bodyfree_closed": closed,
        "dri_op12_waiting_for_op11_or_verification_summaries": waiting,
        "dri_op12_repair_required": repair,
        "dri_op12_bodyfree_leak_or_promotion_blocked": blocked,
        "dri_op12_reason_refs": reasons,
        "dri_op12_reason_ref_count": len(reasons),
        "dri_op12_blocker_refs": blockers,
        "dri_op12_blocker_ref_count": len(blockers),
        "result_memo_closure_is_not_actual_review_complete": True,
        "result_memo_closure_is_not_dhr_actual_source_claim_confirmed": True,
        "result_memo_closure_is_not_dhr_op04_call": True,
        "result_memo_closure_is_not_dhr_reintake_execution": True,
        "result_memo_closure_is_not_p8_start": True,
        "result_memo_closure_is_not_p7_complete": True,
        "result_memo_closure_is_not_release_ready": True,
        "dri_op12_does_not_call_dhr_op04": True,
        "dri_op12_does_not_execute_dhr_reintake": True,
        "dri_op12_does_not_confirm_dhr_actual_source_claim": True,
        "dri_op12_does_not_execute_dmd_or_r52": True,
        "dri_op12_does_not_start_p5_p6_p8_p7_or_release": True,
        "dri_op12_does_not_change_api_db_rn_runtime_response_key": True,
        "dri_op12_does_not_materialize_p8_question_spec": True,
        "manual_decision_required_without_auto_execution": True,
        "downstream_auto_execution_allowed": False,
        "actual_review_execution_claimed_by_dri_op12": False,
        "actual_review_evidence_completed_by_dri_op12": False,
        "dhr_actual_source_claim_confirmed_by_dri_op12": False,
        "dhr_op04_called_by_dri_op12": False,
        "dhr_actual_source_claim_reintake_executed_by_dri_op12": False,
        "dmd_execution_started_by_dri_op12": False,
        "r52_actual_execution_started_by_dri_op12": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RSR16_DRI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RSR16_DRI_OP12_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_rsr16_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract(data: Mapping[str, Any]) -> bool:
    """Assert DRI-OP12 body-free result memo / target tests / selected regression closure contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RSR16_DRI_OP12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRSR16-DRI-OP12")
    if set(data) != set(P7_R54_AHR_POST_RSR16_DRI_OP12_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RSR16_DRI_OP12_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF, source="P7-R54-AHR-PostRSR16-DRI-OP12")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RSR16_DRI_OP12_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != []:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 implemented/not-yet steps changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 not-claimed boundary must stay false")
    for key in ("downstream_auto_execution_allowed", "actual_review_execution_claimed_by_dri_op12", "actual_review_evidence_completed_by_dri_op12", "dhr_actual_source_claim_confirmed_by_dri_op12", "dhr_op04_called_by_dri_op12", "dhr_actual_source_claim_reintake_executed_by_dri_op12", "dmd_execution_started_by_dri_op12", "r52_actual_execution_started_by_dri_op12", "dhr_op04_called_here", "dhr_actual_source_claim_reintake_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP12 downstream/no-promotion flag promoted: {key}")
    for key in ("result_memo_closure_is_not_actual_review_complete", "result_memo_closure_is_not_dhr_actual_source_claim_confirmed", "result_memo_closure_is_not_dhr_op04_call", "result_memo_closure_is_not_dhr_reintake_execution", "result_memo_closure_is_not_p8_start", "result_memo_closure_is_not_p7_complete", "result_memo_closure_is_not_release_ready", "dri_op12_does_not_call_dhr_op04", "dri_op12_does_not_execute_dhr_reintake", "dri_op12_does_not_confirm_dhr_actual_source_claim", "dri_op12_does_not_execute_dmd_or_r52", "dri_op12_does_not_start_p5_p6_p8_p7_or_release", "dri_op12_does_not_change_api_db_rn_runtime_response_key", "dri_op12_does_not_materialize_p8_question_spec", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRSR16-DRI-OP12 required true boundary changed: {key}")
    status_ref = data.get("dri_op12_status_ref")
    if status_ref != data.get("result_memo_tests_selected_regression_closure_status_ref") or status_ref not in P7_R54_AHR_POST_RSR16_DRI_OP12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 status ref is not allowed")
    flags = [
        data.get("dri_op12_result_memo_bodyfree_closed") is True,
        data.get("dri_op12_waiting_for_op11_or_verification_summaries") is True,
        data.get("dri_op12_repair_required") is True,
        data.get("dri_op12_bodyfree_leak_or_promotion_blocked") is True,
    ]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF and data.get("rn_no_touch_grep_match_refs"):
        raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 RN no-touch grep matches cannot be carried as closed material")
    if status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_CLOSED_BODYFREE_REF:
        if data.get("op11_contract_valid") is not True or data.get("op11_no_touch_guard_clear") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 closed branch requires OP11 clear")
        if data.get("target_tests_all_required_green") is not True or data.get("selected_regression_all_required_green") is not True or data.get("services_ai_inference_compileall_ok") is not True:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 closed branch requires target/regression/compileall green")
        if data.get("result_memo_input_forbidden_payload_key_path_refs") != [] or data.get("result_memo_input_body_like_value_path_refs") != [] or data.get("result_memo_input_promotion_claim_refs") != [] or data.get("dri_op12_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 closed branch cannot carry blockers")
        if data.get("op10_next_required_step") != data.get("next_required_step"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 closed next step must stay selected DRI next step")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_WAIT_FOR_OP11_OR_VERIFICATION_SUMMARIES_REF:
        if data.get("dri_op12_waiting_for_op11_or_verification_summaries") is not True or not data.get("dri_op12_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 wait branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP12_VERIFICATION_SUMMARIES_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 wait next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_REPAIR_RESULT_MEMO_TESTS_OR_REGRESSION_SUMMARY_REF:
        if data.get("dri_op12_repair_required") is not True or not data.get("dri_op12_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP12_RESULT_MEMO_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_RSR16_DRI_OP12_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_NO_TOUCH_CHANGE_REF:
        if data.get("dri_op12_bodyfree_leak_or_promotion_blocked") is not True or not data.get("dri_op12_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_BLOCKED_OP12_RESULT_MEMO_REF:
            raise ValueError("P7-R54-AHR-PostRSR16-DRI-OP12 blocked next step changed")
    return True

# Full-title aliases used by adjacent R54-AHR helpers/tests.
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16 = (
    build_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op00_scope_no_touch_no_promotion_refreeze_after_rsr_op16_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op01_rsr_op16_result_memo_intake = (
    build_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op01_rsr_op16_result_memo_intake_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op01_rsr_op16_result_memo_intake_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op02_rsr_op15_branch_next_step_alignment = (
    build_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op02_rsr_op15_branch_next_step_alignment_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op02_rsr_op15_branch_next_step_alignment_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op03_complete_candidate_supplied_material_inventory = (
    build_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op03_complete_candidate_supplied_material_inventory_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op03_complete_candidate_supplied_material_inventory_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_actual_operation_receipt_revalidation = (
    build_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_actual_operation_receipt_revalidation_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op04_actual_operation_receipt_revalidation_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op05_sanitized_rows_rating_rows_revalidation = (
    build_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op05_sanitized_rows_rating_rows_revalidation_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op05_sanitized_rows_rating_rows_revalidation_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op06_question_need_rows_bridge_only_revalidation = (
    build_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op06_question_need_rows_bridge_only_revalidation_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op06_question_need_rows_bridge_only_revalidation_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op07_disposal_purge_receipt_revalidation = (
    build_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op07_disposal_purge_receipt_revalidation_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op07_disposal_purge_receipt_revalidation_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_final_bodyfree_no_promotion_source_kind_rescan = (
    build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate = (
    build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract
)


build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_deterministic_branch_resolver = (
    build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_deterministic_branch_resolver_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op11_no_touch_selected_regression_guard = (
    build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op11_no_touch_selected_regression_guard_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract
)
build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_memo_tests_selected_regression_closure = (
    build_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure
)
assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_memo_tests_selected_regression_closure_contract = (
    assert_p7_r54_ahr_post_rsr16_dri_op12_result_memo_tests_selected_regression_closure_contract
)
