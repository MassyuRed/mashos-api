# -*- coding: utf-8 -*-
"""Post-DMD08 actual local review operation helpers for ALR-OP00/ALR-OP12.

ALR-OP00 through ALR-OP12 intentionally add only a thin, body-free
Post-DMD08 operation-entry layer:

* ALR-OP00 re-freezes the Post-DMD08 scope, no-touch boundary, and
  no-promotion boundary.
* ALR-OP01 intakes the DMD-OP08 body-free result memo / branch material.
* ALR-OP02 inventories existing operation/session/receipt material without
  treating helper green, fixture rows, or historical candidates as actual
  local-only human review evidence.
* ALR-OP03 scans the intake/inventory materials for body-free leaks, invalid
  sources, local path/hash/terminal-body exposure, and downstream promotion
  claims before the later ALR-OP04 action resolver.
* ALR-OP04 resolves exactly one body-free continue/retry/repair/complete action.
* ALR-OP05 materializes the selected action into a guarded operation state.
* ALR-OP06 closes the explicit local-only allow requirement boundary without
  granting allow, generating body-full packets, or running actual review.
* ALR-OP07 materializes only a body-free body-full packet request envelope.
* ALR-OP08 fixes the expected body-free actual operation receipt schema and
  completeness guard without creating an actual receipt.
* ALR-OP09 fixes the selection-only review result / rating / question-need row
  expected schema guard without creating actual rows.
* ALR-OP10 fixes the disposal / purge receipt expected schema guard without
  creating or executing disposal / purge.
* ALR-OP11 finalizes downstream non-promotion / manual decision hold without
  starting P5/P6/P8/R52/P7 or release.
* ALR-OP12 closes the body-free result memo / target-test / selected
  regression / compileall summary without running those commands itself.

These helpers do not generate a body-full packet, do not run actual local-only
human review, do not create actual receipts/rows/disposal evidence, do not
execute PostCR22 re-entry/R52, do not start P5/P6/P8/P7, and do not allow
release. OP04/OP05 decide and materialize a body-free operation-entry state;
OP06/OP07 close the allow requirement and packet-request-envelope boundaries;
OP08/OP09/OP10 close expected evidence-schema boundaries; OP11 closes the
downstream non-promotion hold; OP12 closes only the body-free result memo and
validation summary boundary. They still do not execute the operation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd


P7_R54_AHR_POST_DMD08_ALR_PHASE: Final = "P7"
P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_DMD08_ALR_STEP: Final = (
    "R54-AHR-PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_20260703"
)
P7_R54_AHR_POST_DMD08_ALR_SCOPE: Final = (
    "p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation"
)
P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND: Final = (
    "r54_ahr_post_dmd08_actual_local_review_operation_entry_bodyfree_boundary"
)
P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postdmd08_alr_session_20260703_current_received_265_92_178_v1"
)

P7_R54_AHR_POST_DMD08_ALR_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op01_dmd_op08_result_memo_branch_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op06_explicit_local_only_allow_requirement_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op07_bodyfull_packet_request_bodyfree_envelope.bodyfree.v1"
)

P7_R54_AHR_POST_DMD08_ALR_OP00_STEP_REF: Final = (
    "ALR-OP00_scope_no_touch_no_promotion_re_freeze_after_DMD_OP08"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF: Final = (
    "ALR-OP01_DMD_OP08_result_memo_branch_intake"
)
P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF: Final = (
    "ALR-OP02_existing_operation_material_inventory"
)
P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF: Final = (
    "ALR-OP03_bodyfree_leak_invalid_source_promotion_scan"
)
P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF: Final = (
    "ALR-OP04_continue_retry_repair_complete_action_resolver"
)
P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF: Final = (
    "ALR-OP05_operation_state_machine_materialization"
)
P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF: Final = (
    "ALR-OP06_explicit_local_only_allow_requirement_boundary"
)
P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF: Final = (
    "ALR-OP07_bodyfull_packet_request_bodyfree_envelope"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF: Final = (
    "ALR-OP08_actual_operation_receipt_expected_schema_completeness_guard"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF: Final = (
    "ALR-OP09_selection_only_rows_rating_question_need_expected_schema_guard"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF: Final = (
    "ALR-OP10_disposal_purge_receipt_expected_schema_guard"
)
P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF: Final = (
    "ALR-OP11_downstream_non_promotion_manual_decision_hold_finalizer"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF: Final = (
    "ALR-OP12_result_memo_target_tests_selected_regression_closure"
)
P7_R54_AHR_POST_DMD08_ALR_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP00_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:1]
P7_R54_AHR_POST_DMD08_ALR_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[1:]
P7_R54_AHR_POST_DMD08_ALR_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:2]
P7_R54_AHR_POST_DMD08_ALR_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[2:]
P7_R54_AHR_POST_DMD08_ALR_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:3]
P7_R54_AHR_POST_DMD08_ALR_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[3:]
P7_R54_AHR_POST_DMD08_ALR_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:4]
P7_R54_AHR_POST_DMD08_ALR_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[4:]
P7_R54_AHR_POST_DMD08_ALR_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:5]
P7_R54_AHR_POST_DMD08_ALR_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[5:]
P7_R54_AHR_POST_DMD08_ALR_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:6]
P7_R54_AHR_POST_DMD08_ALR_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[6:]
P7_R54_AHR_POST_DMD08_ALR_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:7]
P7_R54_AHR_POST_DMD08_ALR_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[7:]
P7_R54_AHR_POST_DMD08_ALR_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:8]
P7_R54_AHR_POST_DMD08_ALR_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[8:]

P7_R54_AHR_POST_DMD08_ALR_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-DMD08 Continue/Retry Actual Local-only Human Review Operation before Downstream Decision"
)
P7_R54_AHR_POST_DMD08_ALR_SELECTED_STEP_PREFIX_REF: Final = "ALR-OP"
P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_DMD_BRANCH_REF: Final = (
    dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
)
P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_DMD_NEXT_STEP_REF: Final = (
    dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
)
P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_ACTION_IF_NO_EXTERNAL_RECEIPT_REF: Final = (
    "ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "P8 question design",
    "P8 question implementation",
    "P6 limited human readfeel start",
    "R52 actual execution",
    "P5 finalization",
    "P7 complete",
    "release decision",
)
P7_R54_AHR_POST_DMD08_ALR_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(278).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(92).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(11).zip",
    "rn_zip_ref": "Cocolon(265).zip",
    "backend_zip_ref": "mashos-api(178).zip",
}
P7_R54_AHR_POST_DMD08_ALR_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_PreDesignMemo_20260703.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_DetailedDesign_ImplementationOrder_20260703.md",
    dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_REF,
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703.py",
)

P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF: Final = (
    "ALR_DMD08_INTAKE_ACCEPTED_EVIDENCE_INCOMPLETE"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_REPAIR_REQUIRED_REF: Final = (
    "ALR_DMD08_INTAKE_ACCEPTED_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_COMPLETE_MANUAL_DECISION_REF: Final = (
    "ALR_DMD08_INTAKE_ACCEPTED_COMPLETE_MANUAL_DECISION"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF: Final = (
    "ALR_DMD08_INTAKE_INVALID_OR_MISSING"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_COMPLETE_MANUAL_DECISION_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_CONTINUE_RETRY_RESOLVER_REQUIRED_REF: Final = (
    "ALR_OP01_ROUTE_CONTINUE_RETRY_RESOLVER_REQUIRED_AFTER_EXISTING_OPERATION_INVENTORY"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_REPAIR_STOP_CANDIDATE_REF: Final = (
    "ALR_OP01_ROUTE_REPAIR_STOP_CANDIDATE_AFTER_BODYFREE_SCAN"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_COMPLETE_RECEIPT_MANUAL_DECISION_CANDIDATE_REF: Final = (
    "ALR_OP01_ROUTE_COMPLETE_RECEIPT_MANUAL_DECISION_CANDIDATE_AFTER_BODYFREE_SCAN"
)
P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF: Final = (
    "ALR_OP01_ROUTE_INVALID_OR_MISSING_DMD08_INTAKE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF: Final = (
    "stop_and_repair_bodyfree_evidence_boundary_before_actual_review_operation"
)

P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dmd_op08_result_memo_green_is_not_actual_local_human_review_complete",
    "dmd_op08_target_green_is_not_actual_operation_receipt_creation",
    "dmd_op08_selected_regression_green_is_not_actual_rows_creation",
    "dmd_op08_compileall_green_is_not_body_full_packet_generation",
    "actual_body_full_packet_request_is_not_body_full_packet_generation",
    "actual_operation_receipt_expected_schema_is_not_actual_receipt_creation",
    "question_need_observation_row_schema_is_not_p8_question_design",
    "complete_receipt_candidate_is_not_downstream_auto_execution",
    "p8_question_observation_is_not_p8_question_implementation",
    "release_decision_is_not_allowed_here",
)
P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_local_human_review_execution",
    "actual_operation_receipt_creation",
    "actual_rows_creation",
    "actual_sanitized_review_result_rows_from_real_operation",
    "actual_rating_rows_from_real_operation",
    "actual_question_need_observation_rows_from_real_operation",
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
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "DMD-OP08 result memo green != actual human review complete",
    "DMD-OP08 helper closed != actual body-full packet generated",
    "DMD-OP08 branch intake != continue/retry action resolved",
    "actual evidence incomplete branch != P8 start allowed",
    "repair branch != actual review execution allowed",
    "complete manual decision branch != downstream auto-execution allowed",
    "P5/P6/P8/R52/P7/release remain manual-held here",
)
P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
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
P7_R54_AHR_POST_DMD08_ALR_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_DMD08_ALR_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        *dmd.P7_R54_AHR_POST_DMH18_DMD_FORBIDDEN_PAYLOAD_KEY_REFS,
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
        "stdout",
        "stderr",
        "traceback",
    }
)
P7_R54_AHR_POST_DMD08_ALR_DMD08_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
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

P7_R54_AHR_POST_DMD08_ALR_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_step_prefix_ref", "expected_current_dmd_branch_ref",
    "expected_current_dmd_next_required_step_ref", "expected_current_alr_action_if_no_external_receipt_ref",
    "not_stage_refs", "not_stage_ref_count", "support_material_refs", "support_material_ref_count",
    "local_received_zip_refs", "local_received_zip_ref_count", "body_free", "alr_op00_scope_confirmed",
    "alr_op00_no_touch_boundary_confirmed", "alr_op00_no_promotion_boundary_confirmed",
    "alr_op00_does_not_intake_dmd_op08_result_memo", "alr_op00_does_not_generate_body_full_packet",
    "alr_op00_does_not_run_actual_local_human_review", "alr_op00_does_not_create_receipts_rows_or_disposal",
    "alr_op00_does_not_start_p8_p6_r52_or_release", "alr_op00_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dmd08_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_DMD08_ALR_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op02_existing_operation_material_inventory.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op03_bodyfree_leak_invalid_source_promotion_scan.bodyfree.v1"
)

P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_MISSING_REF: Final = "ALR_OPERATION_MATERIAL_MISSING"
P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_CONTINUABLE_BODYFREE_REF: Final = (
    "ALR_OPERATION_MATERIAL_CONTINUABLE_BODYFREE"
)
P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_INCOMPLETE_RETRY_REQUIRED_REF: Final = (
    "ALR_OPERATION_MATERIAL_INCOMPLETE_RETRY_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_COMPLETE_CANDIDATE_REF: Final = (
    "ALR_OPERATION_MATERIAL_COMPLETE_CANDIDATE"
)
P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF: Final = "ALR_OPERATION_MATERIAL_REPAIR_REQUIRED"
P7_R54_AHR_POST_DMD08_ALR_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_MISSING_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_CONTINUABLE_BODYFREE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_INCOMPLETE_RETRY_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_COMPLETE_CANDIDATE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF,
)

P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_PASSED_REF: Final = "ALR_BODYFREE_SCAN_PASSED"
P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_REPAIR_REQUIRED_REF: Final = (
    "ALR_BODYFREE_SCAN_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_PASSED_REF: Final = "ALR_PROMOTION_SCAN_PASSED"
P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_REPAIR_REQUIRED_REF: Final = (
    "ALR_PROMOTION_SCAN_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP03_ALLOWED_BODYFREE_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_PASSED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP03_ALLOWED_PROMOTION_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_PASSED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_REPAIR_REQUIRED_REF,
)

P7_R54_AHR_POST_DMD08_ALR_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op04_continue_retry_repair_complete_action_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op05_operation_state_machine_materialization.bodyfree.v1"
)

P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF: Final = (
    "ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED"
)
P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF: Final = (
    "ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF: Final = "ALR_ACTION_REPAIR_STOP_REQUIRED"
P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF: Final = (
    "ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_ACTION_RESOLVER_PRIORITY_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_CONTINUE_EXISTING_REVIEW_REF: Final = (
    "continue_existing_actual_local_only_human_review_operation_under_bodyfree_boundary"
)
P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF: Final = (
    "start_or_retry_actual_local_only_human_review_operation_with_explicit_local_only_allow"
)
P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF: Final = (
    "downstream_manual_decision_required_without_auto_execution"
)
P7_R54_AHR_POST_DMD08_ALR_ACTION_NEXT_REQUIRED_STEP_REFS: Final[dict[str, str]] = {
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF: P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_CONTINUE_EXISTING_REVIEW_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
}

P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF: Final = "ALR_STATE_REPAIR_STOP_REQUIRED"
P7_R54_AHR_POST_DMD08_ALR_STATE_RETRY_OR_START_REQUIRED_REF: Final = "ALR_STATE_RETRY_OR_START_REQUIRED"
P7_R54_AHR_POST_DMD08_ALR_STATE_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED_REF: Final = "ALR_STATE_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED"
P7_R54_AHR_POST_DMD08_ALR_STATE_BODYFULL_PACKET_REQUEST_READY_BODYFREE_REF: Final = (
    "ALR_STATE_BODYFULL_PACKET_REQUEST_READY_BODYFREE"
)
P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED_REF: Final = (
    "ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED"
)
P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED_REF: Final = (
    "ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED"
)
P7_R54_AHR_POST_DMD08_ALR_STATE_OPERATION_RECEIPT_WAITING_REF: Final = "ALR_STATE_OPERATION_RECEIPT_WAITING"
P7_R54_AHR_POST_DMD08_ALR_STATE_ROWS_RECEIPT_WAITING_REF: Final = "ALR_STATE_ROWS_RECEIPT_WAITING"
P7_R54_AHR_POST_DMD08_ALR_STATE_DISPOSAL_PURGE_WAITING_REF: Final = "ALR_STATE_DISPOSAL_PURGE_WAITING"
P7_R54_AHR_POST_DMD08_ALR_STATE_EVIDENCE_COMPLETE_CANDIDATE_REF: Final = "ALR_STATE_EVIDENCE_COMPLETE_CANDIDATE"
P7_R54_AHR_POST_DMD08_ALR_STATE_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF: Final = (
    "ALR_STATE_DOWNSTREAM_MANUAL_DECISION_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_STATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_RETRY_OR_START_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_BODYFULL_PACKET_REQUEST_READY_BODYFREE_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_OPERATION_RECEIPT_WAITING_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_ROWS_RECEIPT_WAITING_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_DISPOSAL_PURGE_WAITING_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_EVIDENCE_COMPLETE_CANDIDATE_REF,
    P7_R54_AHR_POST_DMD08_ALR_STATE_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_ACTION_STATE_REFS: Final[dict[str, str]] = {
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_RETRY_OR_START_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_EVIDENCE_COMPLETE_CANDIDATE_REF,
}
P7_R54_AHR_POST_DMD08_ALR_ACTION_NEXT_STATE_REFS: Final[dict[str, str]] = {
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF: P7_R54_AHR_POST_DMD08_ALR_STATE_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
}
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_TRANSITION_REFS_BY_ACTION: Final[dict[str, tuple[str, ...]]] = {
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF: (
        "ALR_TRANSITION_REVIEW_PAUSED_CONTINUE_ALLOWED_TO_REVIEW_IN_PROGRESS_BODYFREE_TRACKED",
        "ALR_TRANSITION_REVIEW_IN_PROGRESS_BODYFREE_TRACKED_TO_OPERATION_RECEIPT_WAITING",
    ),
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF: (
        "ALR_TRANSITION_RETRY_OR_START_REQUIRED_TO_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED",
        "ALR_TRANSITION_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED_TO_BODYFULL_PACKET_REQUEST_READY_BODYFREE",
    ),
    P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF: (
        "ALR_TRANSITION_REPAIR_STOP_REQUIRED_TO_STOP_AND_REPAIR_BODYFREE_EVIDENCE_BOUNDARY",
    ),
    P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF: (
        "ALR_TRANSITION_EVIDENCE_COMPLETE_CANDIDATE_TO_DOWNSTREAM_MANUAL_DECISION_REQUIRED",
    ),
}
P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_TRANSITION_REFS: Final[tuple[str, ...]] = (
    "ALR_FORBIDDEN_DMD08_INTAKE_ACCEPTED_BODYFREE_TO_P8_START",
    "ALR_FORBIDDEN_DMD08_INTAKE_ACCEPTED_BODYFREE_TO_R52_ACTUAL_EXECUTION",
    "ALR_FORBIDDEN_EVIDENCE_COMPLETE_CANDIDATE_TO_P5_FINAL",
    "ALR_FORBIDDEN_EVIDENCE_COMPLETE_CANDIDATE_TO_P6_START",
    "ALR_FORBIDDEN_EVIDENCE_COMPLETE_CANDIDATE_TO_P8_START",
    "ALR_FORBIDDEN_EVIDENCE_COMPLETE_CANDIDATE_TO_P7_COMPLETE",
    "ALR_FORBIDDEN_EVIDENCE_COMPLETE_CANDIDATE_TO_RELEASE_ALLOWED",
    "ALR_FORBIDDEN_REPAIR_STOP_REQUIRED_TO_ACTUAL_REVIEW_EXECUTION",
)

P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF: Final = (
    dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
)
P7_R54_AHR_POST_DMD08_ALR_INVALID_SOURCE_KIND_REFS: Final[tuple[str, ...]] = (
    *dmd.P7_R54_AHR_POST_DMH18_DMD_INVALID_SOURCE_KIND_REFS,
    "helper_fixture",
    "fixture",
    "fixture_only",
    "unit_test",
    "unknown_source",
    "not_actual_local_only_human_review_by_person",
)
P7_R54_AHR_POST_DMD08_ALR_CONTINUABLE_SESSION_STATE_REFS: Final[tuple[str, ...]] = (
    "ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED",
    "ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED",
    "ALR_STATE_OPERATION_RECEIPT_WAITING",
    "ALR_STATE_ROWS_RECEIPT_WAITING",
    "ALR_STATE_DISPOSAL_PURGE_WAITING",
    "review_in_progress_bodyfree_tracked",
    "review_paused_continue_allowed",
    "operation_receipt_waiting",
    "rows_receipt_waiting",
    "disposal_purge_waiting",
    "REVIEW_IN_PROGRESS",
    "PAUSED_LOCAL_ONLY",
    "AWAITING_OPERATION_RECEIPT",
    "AWAITING_ROWS_RECEIPT",
    "AWAITING_DISPOSAL_PURGE",
)
P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DMD08_ALR_DMD08_PROMOTION_CLAIM_FIELD_REFS,
    "actual_local_human_review_complete",
    "actual_local_human_review_executed",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_disposal_purge_executed_here",
    "helper_green_promoted_to_actual_review_complete",
    "target_green_promoted_to_actual_review_complete",
    "result_memo_green_promoted_to_actual_review_complete",
    "p8_start",
    "p8_question_design",
    "p8_question_implementation",
    "r52_actual_execution",
    "p5_finalization",
    "p6_start",
    "p7_complete",
    "release_decision",
)
P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewed_case_count",
    "selection_row_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_need_observation_row_count",
)
P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS: Final[tuple[str, ...]] = (
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

P7_R54_AHR_POST_DMD08_ALR_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed",
    "op00_no_touch_boundary_confirmed", "op00_no_promotion_boundary_confirmed", "dmd_op08_result_memo_present",
    "dmd_op08_contract_valid", "dmd_op08_schema_version", "dmd_op08_material_ref", "dmd_op08_result_memo_ref",
    "dmd_op08_status_ref", "dmd_op08_ready", "dmd_op08_branch_ref", "dmd_op08_next_required_step",
    "dmd_op08_result_memo_bodyfree_closed", "dmd_op08_target_tests_closed", "dmd_op08_selected_regression_closed",
    "dmd_op08_compileall_closed", "dmd_op08_not_executed_boundary_refs", "dmd_op08_not_executed_boundary_ref_count",
    "dmd_op08_not_executed_boundary_preserves_actual_review_unexecuted",
    "dmd_op08_not_executed_boundary_preserves_p8_unstarted",
    "dmd_op08_not_executed_boundary_preserves_release_undecided",
    "dmd_op08_evidence_incomplete_continue_or_retry_required", "dmd_op08_bodyfree_evidence_boundary_repair_required",
    "dmd_op08_downstream_manual_decision_required_without_auto_execution", "dmd_op08_forbidden_payload_key_paths",
    "dmd_op08_forbidden_payload_key_path_count", "dmd_op08_promotion_claim_refs", "dmd_op08_promotion_claim_ref_count",
    "alr_op01_intake_status_ref", "alr_op01_allowed_intake_status_refs", "alr_op01_ready", "alr_op01_route_ref",
    "alr_op01_branch_intake_accepted", "alr_op01_reason_refs", "alr_op01_reason_ref_count", "alr_op01_blocker_refs",
    "alr_op01_blocker_ref_count", "alr_op01_does_not_resolve_continue_retry_final_action",
    "alr_op01_does_not_generate_body_full_packet", "alr_op01_does_not_run_actual_local_human_review",
    "alr_op01_does_not_create_receipts_rows_or_disposal", "alr_op01_does_not_execute_postcr22_ex_reentry_or_r52",
    "alr_op01_does_not_start_p5_p6_p8_p7_or_release", "alr_op01_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dmd08_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_intake_status_ref", "op01_route_ref", "op01_ready",
    "op01_next_required_step", "existing_local_only_review_session_material_present",
    "existing_actual_operation_receipt_present", "existing_bodyfree_evidence_bundle_summary_present",
    "existing_disposal_purge_receipt_present", "session_source_kind_ref", "session_state_ref", "session_body_free",
    "session_disposal_purge_finalized", "session_actual_rows_fixture_only", "review_session_id_consistent",
    "receipt_schema_version", "receipt_source_kind_ref", "receipt_review_session_id_consistent", "operation_receipt_ref",
    "operation_receipt_ref_consistent", "receipt_count_summary", "receipt_count_pass_refs",
    "actual_evidence_receipt_count_complete", "actual_evidence_receipt_guard_complete",
    "actual_evidence_receipt_complete", "operation_material_forbidden_payload_key_paths",
    "operation_material_forbidden_payload_key_path_count", "operation_material_safe_ref_shape_violation_paths",
    "operation_material_safe_ref_shape_violation_path_count", "operation_material_invalid_source_kind_paths",
    "operation_material_invalid_source_kind_path_count", "operation_material_invalid_source_kind_refs",
    "operation_material_invalid_source_kind_ref_count", "operation_material_promotion_claim_paths",
    "operation_material_promotion_claim_path_count", "operation_material_promotion_claim_refs",
    "operation_material_promotion_claim_ref_count", "operation_material_inventory_status_ref",
    "alr_op02_ready", "continue_candidate", "retry_or_start_candidate", "repair_stop_candidate",
    "complete_receipt_manual_decision_candidate", "alr_op02_reason_refs", "alr_op02_reason_ref_count",
    "alr_op02_blocker_refs", "alr_op02_blocker_ref_count", "alr_op02_does_not_resolve_final_action",
    "alr_op02_does_not_generate_body_full_packet", "alr_op02_does_not_run_actual_local_human_review",
    "alr_op02_does_not_create_receipts_rows_or_disposal", "alr_op02_does_not_execute_postcr22_ex_reentry_or_r52",
    "alr_op02_does_not_start_p5_p6_p8_p7_or_release", "alr_op02_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dmd08_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_inventory_status_ref", "op02_next_required_step",
    "op02_ready", "op02_repair_stop_candidate", "bodyfree_scan_status_ref", "promotion_claim_scan_status_ref",
    "forbidden_payload_key_paths", "forbidden_payload_key_path_count", "safe_ref_shape_violation_paths",
    "safe_ref_shape_violation_path_count", "invalid_source_kind_paths", "invalid_source_kind_path_count",
    "invalid_source_kind_refs", "invalid_source_kind_ref_count", "promotion_claim_paths", "promotion_claim_path_count",
    "promotion_claim_refs", "promotion_claim_ref_count", "repair_stop_required", "alr_op03_scan_completed",
    "alr_op03_ready_for_op04", "alr_op03_reason_refs", "alr_op03_reason_ref_count", "alr_op03_blocker_refs",
    "alr_op03_blocker_ref_count", "alr_op03_does_not_resolve_final_action", "alr_op03_does_not_generate_body_full_packet",
    "alr_op03_does_not_run_actual_local_human_review", "alr_op03_does_not_create_receipts_rows_or_disposal",
    "alr_op03_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op03_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op03_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_DMD08_ALR_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_schema_version", "op03_material_ref", "op03_bodyfree_scan_status_ref", "op03_promotion_claim_scan_status_ref",
    "op03_repair_stop_required", "op03_ready_for_op04", "op02_inventory_status_ref",
    "action_resolver_priority_refs", "action_resolver_priority_ref_count", "allowed_action_refs", "allowed_action_ref_count",
    "selected_action_ref", "continue_allowed", "retry_or_start_required", "repair_stop_required",
    "complete_receipt_manual_decision_required", "exactly_one_action_flag_true", "action_reason_refs",
    "action_reason_ref_count", "action_blocker_refs", "action_blocker_ref_count", "operation_plan_required",
    "operation_plan_ref", "selected_action_next_step_ref", "alr_op04_resolver_completed",
    "alr_op04_does_not_materialize_state_machine", "alr_op04_does_not_generate_body_full_packet",
    "alr_op04_does_not_run_actual_local_human_review", "alr_op04_does_not_create_receipts_rows_or_disposal",
    "alr_op04_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op04_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op04_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_schema_version", "op04_material_ref", "op04_selected_action_ref", "op04_next_required_step",
    "op04_ready_for_op05", "selected_action_ref", "continue_allowed", "retry_or_start_required",
    "repair_stop_required", "complete_receipt_manual_decision_required", "operation_state_ref", "next_state_ref",
    "operation_state_materialized", "operation_plan_required", "state_machine_state_refs", "state_machine_state_ref_count",
    "allowed_transition_refs", "allowed_transition_ref_count", "forbidden_transition_refs", "forbidden_transition_ref_count",
    "manual_operation_required", "explicit_local_only_allow_required_next", "downstream_manual_decision_required_next",
    "next_manual_operation_ref", "body_full_packet_generation_allowed_here", "actual_review_execution_allowed_here",
    "state_machine_reason_refs", "state_machine_reason_ref_count", "state_machine_blocker_refs", "state_machine_blocker_ref_count",
    "alr_op05_state_machine_materialized", "alr_op05_does_not_generate_body_full_packet",
    "alr_op05_does_not_run_actual_local_human_review", "alr_op05_does_not_create_receipts_rows_or_disposal",
    "alr_op05_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op05_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op05_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "next_implementation_step", "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT: Final = 24
P7_R54_AHR_POST_DMD08_ALR_OP07_REVIEWER_FORM_KIND_REF: Final = "selection_only_bodyfree_result_form"
P7_R54_AHR_POST_DMD08_ALR_OP07_REVIEW_UNIT_KIND_REF: Final = "actual_local_only_human_review_case_bodyfree_ref"
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_LOCAL_ONLY_REVIEW_ACTION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
    P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF: Final = (
    "ALR_EXPLICIT_LOCAL_ONLY_ALLOW_BOUNDARY_READY_FOR_BODYFREE_PACKET_REQUEST"
)
P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF: Final = (
    "ALR_EXPLICIT_LOCAL_ONLY_ALLOW_NOT_APPLICABLE_REPAIR_STOP"
)
P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF: Final = (
    "ALR_EXPLICIT_LOCAL_ONLY_ALLOW_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION"
)
P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_REPAIR_REQUIRED_REF: Final = (
    "ALR_EXPLICIT_LOCAL_ONLY_ALLOW_BOUNDARY_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF: Final = (
    "ALR_BODYFULL_PACKET_REQUEST_BODYFREE_ENVELOPE_READY"
)
P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF: Final = (
    "ALR_BODYFULL_PACKET_REQUEST_BODYFREE_ENVELOPE_NOT_APPLICABLE_REPAIR_STOP"
)
P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF: Final = (
    "ALR_BODYFULL_PACKET_REQUEST_BODYFREE_ENVELOPE_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION"
)
P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_REPAIR_REQUIRED_REF: Final = (
    "ALR_BODYFULL_PACKET_REQUEST_BODYFREE_ENVELOPE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_EXPORT_DENYLIST_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_export",
    "raw_input_export",
    "comment_text_body_export",
    "reviewer_note_body_export",
    "question_text_export",
    "local_path_export",
    "body_hash_export",
    "terminal_output_body_export",
)
P7_R54_AHR_POST_DMD08_ALR_OP07_FORBIDDEN_PERSISTENCE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_body_persistence_allowed",
    "raw_input_persistence_allowed",
    "comment_text_body_persistence_allowed",
    "reviewer_note_body_persistence_allowed",
    "reviewer_free_text_persistence_allowed",
    "question_text_persistence_allowed",
    "draft_question_text_persistence_allowed",
    "answer_text_persistence_allowed",
    "local_path_persistence_allowed",
    "body_hash_persistence_allowed",
    "terminal_output_body_persistence_allowed",
    "external_export_allowed",
)
P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_BODY_NOT_INCLUDED_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_body_included",
    "raw_input_included",
    "comment_text_body_included",
    "reviewer_note_body_included",
    "question_text_included",
    "draft_question_text_included",
    "answer_text_included",
    "local_path_included",
    "body_hash_included",
    "terminal_output_body_included",
)

P7_R54_AHR_POST_DMD08_ALR_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_schema_version", "op05_material_ref", "op05_selected_action_ref", "op05_operation_state_ref",
    "op05_next_state_ref", "op05_next_required_step", "op05_next_implementation_step", "op05_operation_plan_required",
    "op05_manual_operation_required", "op05_explicit_local_only_allow_required_next", "op05_ready_for_op06",
    "selected_action_ref", "operation_state_ref", "next_state_ref", "local_only_allow_boundary_status_ref",
    "allowed_local_only_review_action_refs", "allowed_local_only_review_action_ref_count",
    "explicit_local_only_allow_required", "operator_explicit_allow_receipt_required_next",
    "operator_explicit_allow_receipt_created_here", "operator_explicit_allow_granted_here",
    "explicit_allow_boundary_closed_bodyfree", "body_full_packet_generation_allowed_before_allow",
    "actual_human_review_execution_allowed_before_allow", "body_full_persistence_allowed", "external_export_allowed",
    "raw_body_persistence_allowed", "reviewer_free_text_allowed", "question_text_persistence_allowed",
    "local_path_persistence_allowed", "hash_persistence_allowed", "terminal_body_persistence_allowed",
    "body_full_packet_export_allowed", "packet_request_bodyfree_envelope_allowed_next",
    "body_full_packet_generation_allowed_after_op06", "actual_review_execution_allowed_after_op06",
    "alr_op06_ready_for_op07", "alr_op06_reason_refs", "alr_op06_reason_ref_count",
    "alr_op06_blocker_refs", "alr_op06_blocker_ref_count", "alr_op06_does_not_generate_body_full_packet",
    "alr_op06_does_not_run_actual_local_human_review", "alr_op06_does_not_create_receipts_rows_or_disposal",
    "alr_op06_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op06_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op06_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "next_implementation_step", "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step",
    "op06_next_implementation_step", "op06_ready_for_op07", "op06_explicit_local_only_allow_required",
    "op06_packet_request_bodyfree_envelope_allowed_next", "selected_action_ref", "packet_request_ref",
    "packet_request_status_ref", "allowed_packet_request_status_refs", "allowed_packet_request_status_ref_count",
    "requested_case_count", "expected_review_unit_count", "review_unit_kind_ref", "reviewer_form_kind_ref",
    "packet_request_bodyfree_envelope_ready", "body_full_packet_request_bodyfree_envelope_ready",
    "packet_generation_allowed_only_after_explicit_local_only_allow", "explicit_local_only_allow_required_before_packet_generation",
    "packet_generation_allowed_here", "body_full_packet_generation_allowed_here", "actual_review_execution_allowed_here",
    "body_full_packet_body_included", "packet_export_allowed", "body_full_packet_export_allowed",
    "raw_body_persistence_allowed", "reviewer_free_text_allowed", "question_text_persistence_allowed",
    "local_path_persistence_allowed", "hash_persistence_allowed", "terminal_body_persistence_allowed",
    "export_denylist_refs", "export_denylist_ref_count", "forbidden_persistence_flags",
    "forbidden_persistence_flag_count", "packet_body_not_included_flags", "packet_body_not_included_flag_count",
    "raw_input_included", "comment_text_body_included", "reviewer_note_body_included", "question_text_included",
    "draft_question_text_included", "answer_text_included", "local_path_included", "body_hash_included",
    "terminal_output_body_included", "packet_request_reason_refs", "packet_request_reason_ref_count",
    "packet_request_blocker_refs", "packet_request_blocker_ref_count", "alr_op07_does_not_generate_body_full_packet",
    "alr_op07_does_not_run_actual_local_human_review", "alr_op07_does_not_create_receipts_rows_or_disposal",
    "alr_op07_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op07_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op07_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "next_implementation_step", "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(
        value,
        default=P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        max_length=220,
    )


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMD08_ALR_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMD08_ALR_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS}


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
            if key_text in P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _dmd08_promotion_claim_refs(dmd08_result_memo: Mapping[str, Any]) -> list[str]:
    return [
        field
        for field in P7_R54_AHR_POST_DMD08_ALR_DMD08_PROMOTION_CLAIM_FIELD_REFS
        if dmd08_result_memo.get(field) is True
    ]


def _dmd08_contract_valid(dmd08_result_memo: Mapping[str, Any] | None) -> bool:
    if not isinstance(dmd08_result_memo, Mapping):
        return False
    try:
        return (
            dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract(
                dmd08_result_memo
            )
            is True
        )
    except ValueError:
        return False


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_DMD08_ALR_PHASE or data.get("current_phase") != P7_R54_AHR_POST_DMD08_ALR_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_DMD08_ALR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_DMD08_ALR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim GitHub connection check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for field in P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS:
        if data.get(field) is not False:
            raise ValueError(f"{source} required false flag changed: {field}")
    if any(value is not False for value in (data.get("public_contract") or {}).values()):
        raise ValueError(f"{source} public contract mutated")
    if any(value is not False for value in (data.get("post_dmd08_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract mutated")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free marker changed")
    if any(key in P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains forbidden top-level payload key")


def build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build ALR-OP00 body-free scope / no-touch / no-promotion re-freeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_DMD08_ALR_SELECTED_STAGE_REF,
        "selected_step_prefix_ref": P7_R54_AHR_POST_DMD08_ALR_SELECTED_STEP_PREFIX_REF,
        "expected_current_dmd_branch_ref": P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_DMD_BRANCH_REF,
        "expected_current_dmd_next_required_step_ref": P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_DMD_NEXT_STEP_REF,
        "expected_current_alr_action_if_no_external_receipt_ref": P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_ACTION_IF_NO_EXTERNAL_RECEIPT_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_DMD08_ALR_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_DMD08_ALR_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "alr_op00_scope_confirmed": True,
        "alr_op00_no_touch_boundary_confirmed": True,
        "alr_op00_no_promotion_boundary_confirmed": True,
        "alr_op00_does_not_intake_dmd_op08_result_memo": True,
        "alr_op00_does_not_generate_body_full_packet": True,
        "alr_op00_does_not_run_actual_local_human_review": True,
        "alr_op00_does_not_create_receipts_rows_or_disposal": True,
        "alr_op00_does_not_start_p8_p6_r52_or_release": True,
        "alr_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert ALR-OP00 scope / no-touch / no-promotion re-freeze contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DMD08_ALR_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDMD08-ALR-OP00",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP00_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP00",
    )
    for key in (
        "alr_op00_scope_confirmed",
        "alr_op00_no_touch_boundary_confirmed",
        "alr_op00_no_promotion_boundary_confirmed",
        "alr_op00_does_not_intake_dmd_op08_result_memo",
        "alr_op00_does_not_generate_body_full_packet",
        "alr_op00_does_not_run_actual_local_human_review",
        "alr_op00_does_not_create_receipts_rows_or_disposal",
        "alr_op00_does_not_start_p8_p6_r52_or_release",
        "alr_op00_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP00 required true boundary changed: {key}")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("local_received_zip_refs", "local_received_zip_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP00 {count_field} changed")
    if tuple(data.get("not_stage_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_STAGE_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 not-stage refs changed")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 support material refs changed")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_DMD08_ALR_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 local received zip refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 fixed non-promotion refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP00 next required step changed")
    return True


def _op01_status_route_and_next_step(
    dmd08_result_memo: Mapping[str, Any] | None, *, dmd08_contract_valid: bool, forbidden_paths: Sequence[str], promotion_claims: Sequence[str]
) -> tuple[str, str, str, list[str], list[str]]:
    if not isinstance(dmd08_result_memo, Mapping):
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op01_dmd_op08_result_memo_missing"],
            ["alr_op01_dmd_op08_result_memo_missing"],
        )
    if not dmd08_contract_valid or forbidden_paths or promotion_claims:
        blockers = []
        if not dmd08_contract_valid:
            blockers.append("alr_op01_dmd_op08_contract_invalid")
        if forbidden_paths:
            blockers.append("alr_op01_dmd_op08_forbidden_payload_key_detected")
        if promotion_claims:
            blockers.append("alr_op01_dmd_op08_promotion_claim_detected")
        blockers = list(dict.fromkeys(blockers))
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op01_dmd_op08_intake_invalid_or_requires_repair"],
            blockers,
        )

    branch_ref = _clean_ref(dmd08_result_memo.get("branch_ref"), max_length=220)
    next_step = _clean_ref(dmd08_result_memo.get("next_required_step"), max_length=260)
    dmd08_status_ref = _clean_ref(dmd08_result_memo.get("dmd_op08_status_ref"), max_length=220)
    if branch_ref == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_REPAIR_STOP_CANDIDATE_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF,
            ["alr_op01_dmd08_repair_branch_accepted_bodyfree_without_operation_execution"],
            [],
        )
    if dmd08_status_ref != dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_STATUS_CLOSED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op01_dmd_op08_result_memo_not_closed"],
            ["alr_op01_dmd_op08_result_memo_not_closed"],
        )
    if branch_ref == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_COMPLETE_MANUAL_DECISION_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_COMPLETE_RECEIPT_MANUAL_DECISION_CANDIDATE_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF,
            ["alr_op01_dmd08_complete_manual_decision_branch_accepted_without_auto_execution"],
            [],
        )
    if (
        branch_ref == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
        and next_step == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    ):
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_CONTINUE_RETRY_RESOLVER_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF,
            ["alr_op01_dmd08_evidence_incomplete_continue_or_retry_branch_accepted_bodyfree"],
            [],
        )
    return (
        P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF,
        P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        ["alr_op01_dmd_op08_unknown_or_mismatched_branch_next_step"],
        ["alr_op01_dmd_op08_branch_next_step_mismatch"],
    )


def build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    dmd_op08_bodyfree_result_memo_target_tests_regression_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP01 body-free DMD-OP08 result memo / branch intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze(
            review_session_id=session_id
        )
    op00_valid = False
    try:
        op00_valid = assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract(op00) is True
    except ValueError:
        op00_valid = False

    dmd08_input = dmd_op08_bodyfree_result_memo_target_tests_regression_closure
    dmd08 = dmd08_input if isinstance(dmd08_input, Mapping) else {}
    dmd08_forbidden_paths = _scan_forbidden_payload_key_paths(dmd08_input, path="dmd_op08") if isinstance(dmd08_input, Mapping) else []
    dmd08_promotion_claims = _dmd08_promotion_claim_refs(dmd08_input) if isinstance(dmd08_input, Mapping) else []
    dmd08_contract_valid = _dmd08_contract_valid(dmd08_input)
    status_ref, route_ref, next_step, reason_refs, blocker_refs = _op01_status_route_and_next_step(
        dmd08_input,
        dmd08_contract_valid=dmd08_contract_valid,
        forbidden_paths=dmd08_forbidden_paths,
        promotion_claims=dmd08_promotion_claims,
    )
    if not op00_valid:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF
        route_ref = P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
        blocker_refs = [*blocker_refs, "alr_op01_op00_scope_no_touch_no_promotion_refreeze_invalid"]
    blocker_refs = list(dict.fromkeys(_clean_ref(ref, max_length=220) for ref in blocker_refs))
    reason_refs = list(dict.fromkeys(_clean_ref(ref, max_length=220) for ref in reason_refs))
    ready = status_ref != P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF

    dmd_not_executed_refs = tuple(dmd08.get("not_executed_boundary_refs") or ()) if isinstance(dmd08, Mapping) else ()
    return {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else None, default="missing_op00_schema_version", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else None, default="missing_op00_material", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else None, default="missing_op00_next_step", max_length=260),
        "op00_scope_confirmed": bool(op00_valid and isinstance(op00, Mapping) and op00.get("alr_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(op00_valid and isinstance(op00, Mapping) and op00.get("alr_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(op00_valid and isinstance(op00, Mapping) and op00.get("alr_op00_no_promotion_boundary_confirmed") is True),
        "dmd_op08_result_memo_present": isinstance(dmd08_input, Mapping),
        "dmd_op08_contract_valid": dmd08_contract_valid,
        "dmd_op08_schema_version": _clean_ref(dmd08.get("schema_version"), default="missing_dmd_op08_schema_version", max_length=260),
        "dmd_op08_material_ref": _clean_ref(dmd08.get("material_id"), default="missing_dmd_op08_material", max_length=260),
        "dmd_op08_result_memo_ref": _clean_ref(dmd08.get("result_memo_ref"), default="missing_dmd_op08_result_memo_ref", max_length=260),
        "dmd_op08_status_ref": _clean_ref(dmd08.get("dmd_op08_status_ref"), default="missing_dmd_op08_status", max_length=220),
        "dmd_op08_ready": dmd08.get("dmd_op08_ready") is True,
        "dmd_op08_branch_ref": _clean_ref(dmd08.get("branch_ref"), default="missing_dmd_op08_branch", max_length=220),
        "dmd_op08_next_required_step": _clean_ref(dmd08.get("next_required_step"), default="missing_dmd_op08_next_step", max_length=260),
        "dmd_op08_result_memo_bodyfree_closed": dmd08.get("result_memo_bodyfree_closed") is True,
        "dmd_op08_target_tests_closed": dmd08.get("target_tests_closed") is True,
        "dmd_op08_selected_regression_closed": dmd08.get("selected_regression_closed") is True,
        "dmd_op08_compileall_closed": dmd08.get("compileall_closed") is True,
        "dmd_op08_not_executed_boundary_refs": list(dmd_not_executed_refs),
        "dmd_op08_not_executed_boundary_ref_count": len(dmd_not_executed_refs),
        "dmd_op08_not_executed_boundary_preserves_actual_review_unexecuted": "actual_local_human_review_execution" in dmd_not_executed_refs,
        "dmd_op08_not_executed_boundary_preserves_p8_unstarted": "p8_start" in dmd_not_executed_refs and "p8_question_design" in dmd_not_executed_refs,
        "dmd_op08_not_executed_boundary_preserves_release_undecided": "release_decision" in dmd_not_executed_refs,
        "dmd_op08_evidence_incomplete_continue_or_retry_required": dmd08.get("evidence_incomplete_continue_or_retry_required") is True,
        "dmd_op08_bodyfree_evidence_boundary_repair_required": dmd08.get("bodyfree_evidence_boundary_repair_required") is True,
        "dmd_op08_downstream_manual_decision_required_without_auto_execution": dmd08.get("downstream_manual_decision_required_without_auto_execution") is True,
        "dmd_op08_forbidden_payload_key_paths": list(dmd08_forbidden_paths),
        "dmd_op08_forbidden_payload_key_path_count": len(dmd08_forbidden_paths),
        "dmd_op08_promotion_claim_refs": list(dmd08_promotion_claims),
        "dmd_op08_promotion_claim_ref_count": len(dmd08_promotion_claims),
        "alr_op01_intake_status_ref": status_ref,
        "alr_op01_allowed_intake_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP01_ALLOWED_STATUS_REFS),
        "alr_op01_ready": ready,
        "alr_op01_route_ref": route_ref,
        "alr_op01_branch_intake_accepted": ready,
        "alr_op01_reason_refs": reason_refs,
        "alr_op01_reason_ref_count": len(reason_refs),
        "alr_op01_blocker_refs": blocker_refs,
        "alr_op01_blocker_ref_count": len(blocker_refs),
        "alr_op01_does_not_resolve_continue_retry_final_action": True,
        "alr_op01_does_not_generate_body_full_packet": True,
        "alr_op01_does_not_run_actual_local_human_review": True,
        "alr_op01_does_not_create_receipts_rows_or_disposal": True,
        "alr_op01_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert ALR-OP01 body-free DMD-OP08 result memo / branch intake contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DMD08_ALR_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDMD08-ALR-OP01",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_DMD08_ALR_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 OP00 next step changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "alr_op01_does_not_resolve_continue_retry_final_action",
        "alr_op01_does_not_generate_body_full_packet",
        "alr_op01_does_not_run_actual_local_human_review",
        "alr_op01_does_not_create_receipts_rows_or_disposal",
        "alr_op01_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op01_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op01_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP01 required true boundary changed: {key}")
    if tuple(data.get("alr_op01_allowed_intake_status_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 allowed status refs changed")
    for field, count_field in (
        ("dmd_op08_not_executed_boundary_refs", "dmd_op08_not_executed_boundary_ref_count"),
        ("dmd_op08_forbidden_payload_key_paths", "dmd_op08_forbidden_payload_key_path_count"),
        ("dmd_op08_promotion_claim_refs", "dmd_op08_promotion_claim_ref_count"),
        ("alr_op01_reason_refs", "alr_op01_reason_ref_count"),
        ("alr_op01_blocker_refs", "alr_op01_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP01 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMD08_ALR_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMD08_ALR_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 not-yet steps changed")

    status_ref = data.get("alr_op01_intake_status_ref")
    branch_ref = data.get("dmd_op08_branch_ref")
    flags = (
        data.get("dmd_op08_evidence_incomplete_continue_or_retry_required"),
        data.get("dmd_op08_bodyfree_evidence_boundary_repair_required"),
        data.get("dmd_op08_downstream_manual_decision_required_without_auto_execution"),
    )
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF:
        if data.get("alr_op01_ready") is not False or data.get("alr_op01_branch_intake_accepted") is not False:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 invalid intake cannot be ready")
        if not data.get("alr_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 invalid intake must carry blockers")
        if data.get("alr_op01_route_ref") != P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 invalid route changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 invalid next step changed")
        return True

    if data.get("alr_op01_ready") is not True or data.get("alr_op01_branch_intake_accepted") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 accepted intake must be ready")
    if data.get("dmd_op08_result_memo_present") is not True or data.get("dmd_op08_contract_valid") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 accepted intake requires valid DMD-OP08 material")
    if data.get("dmd_op08_schema_version") != dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 DMD-OP08 schema version changed")
    if data.get("dmd_op08_result_memo_ref") != dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_RESULT_MEMO_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 DMD-OP08 result memo ref changed")
    if data.get("dmd_op08_forbidden_payload_key_paths") != [] or data.get("dmd_op08_promotion_claim_refs") != []:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 accepted intake cannot carry DMD leak/promotion claims")
    if flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 accepted DMD branch flags must preserve exactly one branch")
    if data.get("dmd_op08_not_executed_boundary_preserves_actual_review_unexecuted") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 must preserve DMD actual review not-executed boundary")
    if data.get("dmd_op08_not_executed_boundary_preserves_p8_unstarted") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 must preserve DMD P8 not-started boundary")
    if data.get("dmd_op08_not_executed_boundary_preserves_release_undecided") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 must preserve DMD release undecided boundary")
    if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 accepted next step must go to OP02 inventory")

    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF:
        if branch_ref != dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 evidence incomplete branch changed")
        if data.get("dmd_op08_next_required_step") != dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 DMD continue/retry next step changed")
        if data.get("alr_op01_route_ref") != P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_CONTINUE_RETRY_RESOLVER_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 evidence incomplete route changed")
    elif status_ref == P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_REPAIR_REQUIRED_REF:
        if branch_ref != dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 repair branch changed")
        if data.get("alr_op01_route_ref") != P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_REPAIR_STOP_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 repair route changed")
    elif status_ref == P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_COMPLETE_MANUAL_DECISION_REF:
        if branch_ref != dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_COMPLETE_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 complete manual decision branch changed")
        if data.get("alr_op01_route_ref") != P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_COMPLETE_RECEIPT_MANUAL_DECISION_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 complete manual decision route changed")
        if data.get("manual_decision_auto_executes_downstream") is not False:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 complete branch cannot auto-execute downstream")
    else:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP01 unknown intake status ref")
    return True



def _material_present(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(value)


def _nested_materials(*values: Any) -> list[Any]:
    return [value for value in values if isinstance(value, (Mapping, list, tuple))]


def _unique_clean_refs(values: Sequence[Any], *, max_length: int = 180) -> list[str]:
    refs: list[str] = []
    for value in values:
        ref = _clean_ref(value, default="", max_length=max_length)
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def _as_path_list(values: Sequence[Any]) -> list[str]:
    paths: list[str] = []
    for value in values:
        path = str(value)
        if path and path not in paths:
            paths.append(path)
    return paths


def _looks_like_local_path_hash_or_terminal_body(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if text.startswith(("/", "./", "../", "~/")) or ":\\" in text or "\\" in text:
        return True
    lower = text.lower()
    if lower.startswith(("sha256:", "md5:", "traceback ")) or "terminal output" in lower:
        return True
    if len(text) in (32, 40, 64) and all(ch in "0123456789abcdefABCDEF" for ch in text):
        return True
    return False


def _scan_safe_ref_shape_violation_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            paths.extend(_scan_safe_ref_shape_violation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_safe_ref_shape_violation_paths(child, path=f"{path}[{index}]"))
    elif isinstance(value, str) and _looks_like_local_path_hash_or_terminal_body(value):
        paths.append(path)
    return paths


def _source_kind_ref(material: Mapping[str, Any] | None, *, default: str = "source_kind_missing") -> str:
    if not isinstance(material, Mapping):
        return default
    for key in (
        "source_kind_ref",
        "session_source_kind_ref",
        "material_source_kind_ref",
        "operation_source_kind_ref",
        "actual_evidence_receipt_source_kind_ref",
        "external_actual_operation_evidence_receipt_source_kind_ref",
    ):
        if key in material:
            return _clean_ref(material.get(key), default=default, max_length=180)
    return default


def _session_state_ref(material: Mapping[str, Any] | None) -> str:
    if not isinstance(material, Mapping):
        return "session_state_missing"
    for key in ("session_state_ref", "operation_state_ref", "state_ref", "review_state_ref"):
        if key in material:
            return _clean_ref(material.get(key), default="session_state_missing", max_length=180)
    return "session_state_missing"


def _material_review_session_id(material: Mapping[str, Any] | None) -> str:
    if not isinstance(material, Mapping):
        return ""
    return _clean_ref(material.get("review_session_id"), default="", max_length=220)


def _scan_invalid_source_kind_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    source_key_markers = ("source_kind", "source_kind_ref", "material_source_kind_ref", "session_source_kind_ref")
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if any(marker in key_text for marker in source_key_markers):
                child_ref = _clean_ref(child, default="unknown", max_length=180)
                if child_ref in P7_R54_AHR_POST_DMD08_ALR_INVALID_SOURCE_KIND_REFS or child_ref == "unknown":
                    paths.append(child_path)
            paths.extend(_scan_invalid_source_kind_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_invalid_source_kind_paths(child, path=f"{path}[{index}]"))
    return paths


def _invalid_source_kind_refs_from_paths_and_materials(paths: Sequence[str], *materials: Any) -> list[str]:
    refs: list[str] = []
    for material in materials:
        if isinstance(material, Mapping):
            source_ref = _source_kind_ref(material, default="")
            if source_ref in P7_R54_AHR_POST_DMD08_ALR_INVALID_SOURCE_KIND_REFS or source_ref == "unknown":
                refs.append(source_ref)
    if paths and not refs:
        refs.append("invalid_source_kind_detected")
    return _unique_clean_refs(refs)


def _promotion_claim_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_FIELD_REFS and child is True:
                paths.append(child_path)
            paths.extend(_promotion_claim_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_promotion_claim_paths(child, path=f"{path}[{index}]"))
    return paths


def _promotion_claim_refs_from_paths(paths: Sequence[str]) -> list[str]:
    refs: list[str] = []
    for path in paths:
        refs.append(path.rsplit(".", 1)[-1])
    return _unique_clean_refs(refs)


def _receipt_count_summary(receipt: Mapping[str, Any] | None) -> dict[str, int | None]:
    summary: dict[str, int | None] = {}
    for field in P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS:
        value = receipt.get(field) if isinstance(receipt, Mapping) else None
        summary[field] = value if isinstance(value, int) else None
    return summary


def _receipt_count_pass_refs(receipt: Mapping[str, Any] | None) -> dict[str, bool]:
    required_count = dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT
    return {field: (receipt.get(field) == required_count if isinstance(receipt, Mapping) else False) for field in P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS}


def _receipt_guard_complete(receipt: Mapping[str, Any] | None) -> bool:
    if not isinstance(receipt, Mapping):
        return False
    return all(receipt.get(field) is True for field in P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS)


def _receipt_schema_version(receipt: Mapping[str, Any] | None) -> str:
    if not isinstance(receipt, Mapping):
        return "actual_operation_receipt_missing"
    return _clean_ref(receipt.get("schema_version"), default="actual_operation_receipt_schema_missing", max_length=220)


def _receipt_complete_candidate(receipt: Mapping[str, Any] | None, *, expected_review_session_id: str) -> bool:
    if not isinstance(receipt, Mapping):
        return False
    return (
        _receipt_schema_version(receipt) == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
        and _source_kind_ref(receipt) == P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF
        and _material_review_session_id(receipt) == expected_review_session_id
        and all(_receipt_count_pass_refs(receipt).values())
        and _receipt_guard_complete(receipt)
    )


def _op01_contract_valid(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    except ValueError:
        return False


def build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
    *,
    dmd_op08_result_memo_branch_intake: Mapping[str, Any] | None = None,
    existing_local_only_review_session_material_bodyfree: Mapping[str, Any] | None = None,
    existing_actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    existing_bodyfree_evidence_bundle_summary: Mapping[str, Any] | None = None,
    existing_disposal_purge_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    alr_op01_dmd_op08_result_memo_branch_intake: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Inventory existing operation material for ALR-OP02 only.

    This function intentionally does not resolve the final ALR action. It only
    records whether existing body-free material is missing, continuable,
    incomplete/retry-needed, complete-candidate, or repair-needed for OP03/OP04.
    """
    op01 = dmd_op08_result_memo_branch_intake or alr_op01_dmd_op08_result_memo_branch_intake
    session = existing_local_only_review_session_material_bodyfree
    receipt = existing_actual_operation_receipt_bodyfree
    bundle = existing_bodyfree_evidence_bundle_summary
    disposal = existing_disposal_purge_receipt_bodyfree

    op01_valid = _op01_contract_valid(op01)
    op01_ready = isinstance(op01, Mapping) and op01.get("alr_op01_ready") is True and op01_valid
    expected_session_id = _safe_review_session_id(
        review_session_id
        or (op01.get("review_session_id") if isinstance(op01, Mapping) else None)
        or _material_review_session_id(session)
        or _material_review_session_id(receipt)
    )

    session_present = _material_present(session)
    receipt_present = _material_present(receipt)
    bundle_present = _material_present(bundle)
    disposal_present = _material_present(disposal)
    any_material_present = session_present or receipt_present or bundle_present or disposal_present

    session_source_kind_ref = _source_kind_ref(session, default="session_source_kind_missing")
    session_state_ref = _session_state_ref(session)
    session_id = _material_review_session_id(session)
    receipt_id = _material_review_session_id(receipt)
    session_id_consistent = (not session_present or session_id == "" or session_id == expected_session_id)
    receipt_id_consistent = (not receipt_present or receipt_id == "" or receipt_id == expected_session_id)
    operation_receipt_ref = _clean_ref(receipt.get("operation_receipt_ref") if isinstance(receipt, Mapping) else None, default="operation_receipt_missing", max_length=220)
    operation_receipt_ref_consistent = operation_receipt_ref != "operation_receipt_missing" if receipt_present else False

    materials_for_scan = _nested_materials(op01, session, receipt, bundle, disposal)
    forbidden_paths = _as_path_list(
        path
        for index, material in enumerate(materials_for_scan)
        for path in _scan_forbidden_payload_key_paths(material, path=f"operation_material[{index}]")
    )
    safe_ref_shape_paths = _as_path_list(
        path
        for index, material in enumerate(materials_for_scan)
        for path in _scan_safe_ref_shape_violation_paths(material, path=f"operation_material[{index}]")
    )
    invalid_source_paths = _as_path_list(
        path
        for index, material in enumerate(materials_for_scan)
        for path in _scan_invalid_source_kind_paths(material, path=f"operation_material[{index}]")
    )
    invalid_source_refs = _invalid_source_kind_refs_from_paths_and_materials(invalid_source_paths, session, receipt, bundle, disposal)
    promotion_paths = _as_path_list(
        path
        for index, material in enumerate(materials_for_scan)
        for path in _promotion_claim_paths(material, path=f"operation_material[{index}]")
    )
    promotion_refs = _promotion_claim_refs_from_paths(promotion_paths)

    session_body_free = session_present and session.get("body_free") is True and not forbidden_paths and not safe_ref_shape_paths
    session_disposal_purge_finalized = isinstance(session, Mapping) and session.get("disposal_purge_finalized") is True
    session_actual_rows_fixture_only = isinstance(session, Mapping) and session.get("actual_rows_fixture_only") is True
    source_kind_valid = session_source_kind_ref == P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF
    session_state_continuable = session_state_ref in P7_R54_AHR_POST_DMD08_ALR_CONTINUABLE_SESSION_STATE_REFS

    count_summary = _receipt_count_summary(receipt)
    count_pass_refs = _receipt_count_pass_refs(receipt)
    receipt_count_complete = receipt_present and all(count_pass_refs.values())
    receipt_guard_complete = _receipt_guard_complete(receipt)
    receipt_complete = _receipt_complete_candidate(receipt, expected_review_session_id=expected_session_id)

    repair_blockers: list[str] = []
    reasons: list[str] = []
    op01_status_ref = op01.get("alr_op01_intake_status_ref") if isinstance(op01, Mapping) else None
    op01_route_ref = op01.get("alr_op01_route_ref") if isinstance(op01, Mapping) else None
    if not op01_valid:
        repair_blockers.append("alr_op02_dmd_op08_branch_intake_missing_or_invalid")
    elif (
        op01_status_ref == P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_REPAIR_REQUIRED_REF
        or op01_route_ref == P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_REPAIR_STOP_CANDIDATE_REF
    ):
        repair_blockers.append("alr_op02_op01_route_repair_stop_candidate")
    if forbidden_paths:
        repair_blockers.append("alr_op02_bodyfull_payload_key_detected_in_existing_material")
    if safe_ref_shape_paths:
        repair_blockers.append("alr_op02_safe_ref_shape_exposes_local_path_hash_or_terminal_body")
    if invalid_source_paths or invalid_source_refs:
        repair_blockers.append("alr_op02_invalid_source_kind_detected")
    if promotion_paths:
        repair_blockers.append("alr_op02_downstream_promotion_claim_detected")
    if session_present and not session_id_consistent:
        repair_blockers.append("alr_op02_review_session_id_inconsistent")
    if receipt_present and not receipt_id_consistent:
        repair_blockers.append("alr_op02_receipt_review_session_id_inconsistent")

    repair = bool(repair_blockers)
    complete_candidate = not repair and receipt_complete
    continuable_candidate = (
        not repair
        and not complete_candidate
        and op01_ready
        and session_present
        and source_kind_valid
        and session_state_continuable
        and session_body_free
        and session_id_consistent
        and not session_disposal_purge_finalized
        and not session_actual_rows_fixture_only
    )
    missing = not repair and op01_ready and not any_material_present
    retry_candidate = not repair and not complete_candidate and not continuable_candidate

    if repair:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF
        reasons.append("alr_op02_existing_operation_material_requires_repair_before_operation")
    elif complete_candidate:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_COMPLETE_CANDIDATE_REF
        reasons.append("alr_op02_actual_operation_receipt_complete_candidate_detected")
    elif continuable_candidate:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_CONTINUABLE_BODYFREE_REF
        reasons.append("alr_op02_existing_local_only_session_continuable_bodyfree")
    elif missing:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_MISSING_REF
        reasons.append("alr_op02_no_existing_operation_material_present")
    else:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_INCOMPLETE_RETRY_REQUIRED_REF
        reasons.append("alr_op02_existing_operation_material_incomplete_or_not_continuable")

    if retry_candidate and not repair:
        repair_blockers.append("alr_op02_actual_operation_material_not_yet_sufficient_for_downstream_decision")

    material_id = "r54_ahr_postdmd08_alr_op02_existing_operation_material_inventory_bodyfree_20260703"
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": "ALR-OP02_existing_operation_material_inventory",
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": material_id,
        "review_session_id": expected_session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": op01.get("schema_version") if isinstance(op01, Mapping) else "op01_material_missing",
        "op01_material_ref": op01.get("material_id") if isinstance(op01, Mapping) else "op01_material_missing",
        "op01_intake_status_ref": op01.get("alr_op01_intake_status_ref") if isinstance(op01, Mapping) else P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_INVALID_OR_MISSING_REF,
        "op01_route_ref": op01.get("alr_op01_route_ref") if isinstance(op01, Mapping) else P7_R54_AHR_POST_DMD08_ALR_OP01_ROUTE_INVALID_INTAKE_REPAIR_REQUIRED_REF,
        "op01_ready": op01_ready,
        "op01_next_required_step": op01.get("next_required_step") if isinstance(op01, Mapping) else P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        "existing_local_only_review_session_material_present": session_present,
        "existing_actual_operation_receipt_present": receipt_present,
        "existing_bodyfree_evidence_bundle_summary_present": bundle_present,
        "existing_disposal_purge_receipt_present": disposal_present,
        "session_source_kind_ref": session_source_kind_ref,
        "session_state_ref": session_state_ref,
        "session_body_free": session_body_free,
        "session_disposal_purge_finalized": session_disposal_purge_finalized,
        "session_actual_rows_fixture_only": session_actual_rows_fixture_only,
        "review_session_id_consistent": session_id_consistent and receipt_id_consistent,
        "receipt_schema_version": _receipt_schema_version(receipt),
        "receipt_source_kind_ref": _source_kind_ref(receipt, default="actual_operation_receipt_source_kind_missing"),
        "receipt_review_session_id_consistent": receipt_id_consistent,
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_ref_consistent": operation_receipt_ref_consistent,
        "receipt_count_summary": count_summary,
        "receipt_count_pass_refs": count_pass_refs,
        "actual_evidence_receipt_count_complete": receipt_count_complete,
        "actual_evidence_receipt_guard_complete": receipt_guard_complete,
        "actual_evidence_receipt_complete": receipt_complete,
        "operation_material_forbidden_payload_key_paths": forbidden_paths,
        "operation_material_forbidden_payload_key_path_count": len(forbidden_paths),
        "operation_material_safe_ref_shape_violation_paths": safe_ref_shape_paths,
        "operation_material_safe_ref_shape_violation_path_count": len(safe_ref_shape_paths),
        "operation_material_invalid_source_kind_paths": invalid_source_paths,
        "operation_material_invalid_source_kind_path_count": len(invalid_source_paths),
        "operation_material_invalid_source_kind_refs": invalid_source_refs,
        "operation_material_invalid_source_kind_ref_count": len(invalid_source_refs),
        "operation_material_promotion_claim_paths": promotion_paths,
        "operation_material_promotion_claim_path_count": len(promotion_paths),
        "operation_material_promotion_claim_refs": promotion_refs,
        "operation_material_promotion_claim_ref_count": len(promotion_refs),
        "operation_material_inventory_status_ref": status_ref,
        "alr_op02_ready": not repair,
        "continue_candidate": continuable_candidate,
        "retry_or_start_candidate": retry_candidate or missing,
        "repair_stop_candidate": repair,
        "complete_receipt_manual_decision_candidate": complete_candidate,
        "alr_op02_reason_refs": _unique_clean_refs(reasons),
        "alr_op02_reason_ref_count": len(_unique_clean_refs(reasons)),
        "alr_op02_blocker_refs": _unique_clean_refs(repair_blockers),
        "alr_op02_blocker_ref_count": len(_unique_clean_refs(repair_blockers)),
        "alr_op02_does_not_resolve_final_action": True,
        "alr_op02_does_not_generate_body_full_packet": True,
        "alr_op02_does_not_run_actual_local_human_review": True,
        "alr_op02_does_not_create_receipts_rows_or_disposal": True,
        "alr_op02_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(data: Mapping[str, Any]) -> bool:
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP02_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP02",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP02")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 unexpected fields changed")
    for key in (
        "alr_op02_does_not_resolve_final_action",
        "alr_op02_does_not_generate_body_full_packet",
        "alr_op02_does_not_run_actual_local_human_review",
        "alr_op02_does_not_create_receipts_rows_or_disposal",
        "alr_op02_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op02_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op02_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP02 required true boundary changed: {key}")
    if data.get("operation_material_inventory_status_ref") not in P7_R54_AHR_POST_DMD08_ALR_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 inventory status changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 next step must remain OP03 scan")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMD08_ALR_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMD08_ALR_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 not-yet steps changed")
    for field, count_field in (
        ("operation_material_forbidden_payload_key_paths", "operation_material_forbidden_payload_key_path_count"),
        ("operation_material_safe_ref_shape_violation_paths", "operation_material_safe_ref_shape_violation_path_count"),
        ("operation_material_invalid_source_kind_paths", "operation_material_invalid_source_kind_path_count"),
        ("operation_material_invalid_source_kind_refs", "operation_material_invalid_source_kind_ref_count"),
        ("operation_material_promotion_claim_paths", "operation_material_promotion_claim_path_count"),
        ("operation_material_promotion_claim_refs", "operation_material_promotion_claim_ref_count"),
        ("alr_op02_reason_refs", "alr_op02_reason_ref_count"),
        ("alr_op02_blocker_refs", "alr_op02_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP02 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 fixed non-promotion refs changed")
    candidate_flags = (
        data.get("continue_candidate"),
        data.get("retry_or_start_candidate"),
        data.get("repair_stop_candidate"),
        data.get("complete_receipt_manual_decision_candidate"),
    )
    if candidate_flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 inventory must expose exactly one candidate path")
    status_ref = data.get("operation_material_inventory_status_ref")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF:
        if data.get("repair_stop_candidate") is not True or data.get("alr_op02_ready") is not False:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 repair status must stop before operation")
        if not data.get("alr_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 repair status requires blockers")
    elif status_ref == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_CONTINUABLE_BODYFREE_REF:
        if data.get("continue_candidate") is not True or data.get("session_source_kind_ref") != P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 continuable status changed")
        if data.get("session_state_ref") not in P7_R54_AHR_POST_DMD08_ALR_CONTINUABLE_SESSION_STATE_REFS:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 continuable state changed")
    elif status_ref == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_COMPLETE_CANDIDATE_REF:
        if data.get("complete_receipt_manual_decision_candidate") is not True or data.get("actual_evidence_receipt_complete") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 complete candidate changed")
    elif status_ref == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_MISSING_REF:
        if data.get("existing_local_only_review_session_material_present") is not False or data.get("retry_or_start_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 missing status changed")
    elif status_ref == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_INCOMPLETE_RETRY_REQUIRED_REF:
        if data.get("retry_or_start_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 incomplete status must require retry/start candidate")
    if "selected_action_ref" in data:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP02 must not resolve selected_action_ref")
    return True


def build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
    *,
    alr_op02_existing_operation_material_inventory: Mapping[str, Any] | None = None,
    existing_local_only_review_session_material_bodyfree: Mapping[str, Any] | None = None,
    existing_actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    existing_bodyfree_evidence_bundle_summary: Mapping[str, Any] | None = None,
    existing_disposal_purge_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Scan OP02 materials for body-free leaks, invalid source, and promotion claims."""
    op02 = alr_op02_existing_operation_material_inventory
    op02_valid = isinstance(op02, Mapping)
    if op02_valid:
        try:
            assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(op02)
        except ValueError:
            op02_valid = False

    expected_session_id = _safe_review_session_id(review_session_id or (op02.get("review_session_id") if isinstance(op02, Mapping) else None))
    # OP02 output contains body-free placeholder refs such as
    # ``session_source_kind_missing`` for absent materials.  OP03 must not
    # reinterpret those placeholders as invalid external source evidence.
    # It therefore reuses OP02's recorded scan lists and scans only optional
    # operation materials supplied alongside OP02.
    scan_materials = _nested_materials(
        existing_local_only_review_session_material_bodyfree,
        existing_actual_operation_receipt_bodyfree,
        existing_bodyfree_evidence_bundle_summary,
        existing_disposal_purge_receipt_bodyfree,
    )

    forbidden_paths = _as_path_list(
        list(op02.get("operation_material_forbidden_payload_key_paths") or []) if isinstance(op02, Mapping) else []
    )
    safe_ref_paths = _as_path_list(
        list(op02.get("operation_material_safe_ref_shape_violation_paths") or []) if isinstance(op02, Mapping) else []
    )
    invalid_paths = _as_path_list(
        list(op02.get("operation_material_invalid_source_kind_paths") or []) if isinstance(op02, Mapping) else []
    )
    invalid_refs = _unique_clean_refs(
        list(op02.get("operation_material_invalid_source_kind_refs") or []) if isinstance(op02, Mapping) else []
    )
    promotion_paths = _as_path_list(
        list(op02.get("operation_material_promotion_claim_paths") or []) if isinstance(op02, Mapping) else []
    )
    promotion_refs = _unique_clean_refs(
        list(op02.get("operation_material_promotion_claim_refs") or []) if isinstance(op02, Mapping) else []
    )

    for index, material in enumerate(scan_materials):
        forbidden_paths = _as_path_list([*forbidden_paths, *_scan_forbidden_payload_key_paths(material, path=f"scan_material[{index}]")])
        safe_ref_paths = _as_path_list([*safe_ref_paths, *_scan_safe_ref_shape_violation_paths(material, path=f"scan_material[{index}]")])
        invalid_paths = _as_path_list([*invalid_paths, *_scan_invalid_source_kind_paths(material, path=f"scan_material[{index}]")])
        promotion_paths = _as_path_list([*promotion_paths, *_promotion_claim_paths(material, path=f"scan_material[{index}]")])
    invalid_refs = _unique_clean_refs([*invalid_refs, *_invalid_source_kind_refs_from_paths_and_materials(invalid_paths, existing_local_only_review_session_material_bodyfree, existing_actual_operation_receipt_bodyfree, existing_bodyfree_evidence_bundle_summary, existing_disposal_purge_receipt_bodyfree)])
    promotion_refs = _unique_clean_refs([*promotion_refs, *_promotion_claim_refs_from_paths(promotion_paths)])

    bodyfree_repair = bool(forbidden_paths or safe_ref_paths or invalid_paths or invalid_refs)
    promotion_repair = bool(promotion_paths or promotion_refs)
    repair_required = bodyfree_repair or promotion_repair or not op02_valid or (isinstance(op02, Mapping) and op02.get("repair_stop_candidate") is True)
    bodyfree_status = P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_REPAIR_REQUIRED_REF if bodyfree_repair or not op02_valid or (isinstance(op02, Mapping) and op02.get("repair_stop_candidate") is True) else P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_PASSED_REF
    promotion_status = P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_REPAIR_REQUIRED_REF if promotion_repair else P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_PASSED_REF

    reasons: list[str] = ["alr_op03_bodyfree_invalid_source_promotion_scan_completed"]
    blockers: list[str] = []
    if not op02_valid:
        blockers.append("alr_op03_op02_inventory_missing_or_invalid")
    if forbidden_paths:
        blockers.append("alr_op03_bodyfull_payload_key_detected")
    if safe_ref_paths:
        blockers.append("alr_op03_local_path_hash_or_terminal_body_shape_detected")
    if invalid_paths or invalid_refs:
        blockers.append("alr_op03_invalid_source_kind_detected")
    if promotion_paths or promotion_refs:
        blockers.append("alr_op03_downstream_promotion_claim_detected")
    if isinstance(op02, Mapping) and op02.get("repair_stop_candidate") is True:
        blockers.append("alr_op03_op02_inventory_repair_stop_candidate")

    material_id = "r54_ahr_postdmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_bodyfree_20260703"
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": "ALR-OP03_bodyfree_leak_invalid_source_promotion_scan",
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": material_id,
        "review_session_id": expected_session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": op02.get("schema_version") if isinstance(op02, Mapping) else "op02_material_missing",
        "op02_material_ref": op02.get("material_id") if isinstance(op02, Mapping) else "op02_material_missing",
        "op02_inventory_status_ref": op02.get("operation_material_inventory_status_ref") if isinstance(op02, Mapping) else P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF,
        "op02_next_required_step": op02.get("next_required_step") if isinstance(op02, Mapping) else P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        "op02_ready": op02.get("alr_op02_ready") if isinstance(op02, Mapping) else False,
        "op02_repair_stop_candidate": op02.get("repair_stop_candidate") if isinstance(op02, Mapping) else True,
        "bodyfree_scan_status_ref": bodyfree_status,
        "promotion_claim_scan_status_ref": promotion_status,
        "forbidden_payload_key_paths": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "safe_ref_shape_violation_paths": safe_ref_paths,
        "safe_ref_shape_violation_path_count": len(safe_ref_paths),
        "invalid_source_kind_paths": invalid_paths,
        "invalid_source_kind_path_count": len(invalid_paths),
        "invalid_source_kind_refs": invalid_refs,
        "invalid_source_kind_ref_count": len(invalid_refs),
        "promotion_claim_paths": promotion_paths,
        "promotion_claim_path_count": len(promotion_paths),
        "promotion_claim_refs": promotion_refs,
        "promotion_claim_ref_count": len(promotion_refs),
        "repair_stop_required": repair_required,
        "alr_op03_scan_completed": True,
        "alr_op03_ready_for_op04": not repair_required,
        "alr_op03_reason_refs": _unique_clean_refs(reasons),
        "alr_op03_reason_ref_count": len(_unique_clean_refs(reasons)),
        "alr_op03_blocker_refs": _unique_clean_refs(blockers),
        "alr_op03_blocker_ref_count": len(_unique_clean_refs(blockers)),
        "alr_op03_does_not_resolve_final_action": True,
        "alr_op03_does_not_generate_body_full_packet": True,
        "alr_op03_does_not_run_actual_local_human_review": True,
        "alr_op03_does_not_create_receipts_rows_or_disposal": True,
        "alr_op03_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF if repair_required else P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(data: Mapping[str, Any]) -> bool:
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP03",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP03")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 unexpected fields changed")
    for key in (
        "alr_op03_scan_completed",
        "alr_op03_does_not_resolve_final_action",
        "alr_op03_does_not_generate_body_full_packet",
        "alr_op03_does_not_run_actual_local_human_review",
        "alr_op03_does_not_create_receipts_rows_or_disposal",
        "alr_op03_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op03_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op03_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP03 required true boundary changed: {key}")
    if data.get("bodyfree_scan_status_ref") not in P7_R54_AHR_POST_DMD08_ALR_OP03_ALLOWED_BODYFREE_SCAN_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 bodyfree scan status changed")
    if data.get("promotion_claim_scan_status_ref") not in P7_R54_AHR_POST_DMD08_ALR_OP03_ALLOWED_PROMOTION_SCAN_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 promotion scan status changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DMD08_ALR_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DMD08_ALR_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 not-yet steps changed")
    for field, count_field in (
        ("forbidden_payload_key_paths", "forbidden_payload_key_path_count"),
        ("safe_ref_shape_violation_paths", "safe_ref_shape_violation_path_count"),
        ("invalid_source_kind_paths", "invalid_source_kind_path_count"),
        ("invalid_source_kind_refs", "invalid_source_kind_ref_count"),
        ("promotion_claim_paths", "promotion_claim_path_count"),
        ("promotion_claim_refs", "promotion_claim_ref_count"),
        ("alr_op03_reason_refs", "alr_op03_reason_ref_count"),
        ("alr_op03_blocker_refs", "alr_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP03 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 fixed non-promotion refs changed")
    bodyfree_should_repair = bool(
        data.get("forbidden_payload_key_paths")
        or data.get("safe_ref_shape_violation_paths")
        or data.get("invalid_source_kind_paths")
        or data.get("invalid_source_kind_refs")
        or data.get("op02_repair_stop_candidate") is True
    )
    promotion_should_repair = bool(data.get("promotion_claim_paths") or data.get("promotion_claim_refs"))
    if bodyfree_should_repair and data.get("bodyfree_scan_status_ref") != P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_REPAIR_REQUIRED_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 bodyfree repair status must be set")
    if not bodyfree_should_repair and data.get("bodyfree_scan_status_ref") != P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_PASSED_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 bodyfree pass status changed")
    if promotion_should_repair and data.get("promotion_claim_scan_status_ref") != P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_REPAIR_REQUIRED_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 promotion repair status must be set")
    if not promotion_should_repair and data.get("promotion_claim_scan_status_ref") != P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_PASSED_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 promotion pass status changed")
    if data.get("repair_stop_required") is not (bodyfree_should_repair or promotion_should_repair):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 repair flag changed")
    if data.get("alr_op03_ready_for_op04") is (data.get("repair_stop_required") is True):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 ready-for-OP04 flag changed")
    expected_next = P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF if data.get("repair_stop_required") is True else P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF
    if data.get("next_required_step") != expected_next:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 next step changed")
    if "selected_action_ref" in data:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP03 must not resolve selected_action_ref")
    return True



def _action_flags_for_selected_action(selected_action_ref: str) -> dict[str, bool]:
    return {
        "continue_allowed": selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
        "retry_or_start_required": selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
        "repair_stop_required": selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
        "complete_receipt_manual_decision_required": selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
    }


def _selected_action_next_step_ref(selected_action_ref: str) -> str:
    return P7_R54_AHR_POST_DMD08_ALR_ACTION_NEXT_REQUIRED_STEP_REFS.get(
        selected_action_ref,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
    )


def _resolve_alr_op04_action(
    alr_op03_bodyfree_leak_invalid_source_promotion_scan: Mapping[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    if not isinstance(alr_op03_bodyfree_leak_invalid_source_promotion_scan, Mapping):
        return (
            P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
            ["alr_op04_op03_material_missing_fail_closed"],
            ["alr_op04_op03_material_missing"],
        )
    op03 = alr_op03_bodyfree_leak_invalid_source_promotion_scan
    op02_status = _clean_ref(op03.get("op02_inventory_status_ref"), max_length=180)
    repair_reasons: list[str] = []
    repair_blockers: list[str] = []
    if op03.get("repair_stop_required") is True:
        repair_reasons.append("alr_op04_op03_repair_stop_required_priority_1")
        repair_blockers.append("alr_op04_op03_repair_stop_required")
    if op03.get("bodyfree_scan_status_ref") == P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_REPAIR_REQUIRED_REF:
        repair_reasons.append("alr_op04_bodyfree_scan_repair_required_priority_1")
        repair_blockers.append("alr_op04_bodyfree_scan_repair_required")
    if op03.get("promotion_claim_scan_status_ref") == P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_REPAIR_REQUIRED_REF:
        repair_reasons.append("alr_op04_promotion_scan_repair_required_priority_1")
        repair_blockers.append("alr_op04_promotion_scan_repair_required")
    if op02_status == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF:
        repair_reasons.append("alr_op04_op02_inventory_repair_required_priority_1")
        repair_blockers.append("alr_op04_op02_inventory_repair_required")
    if repair_reasons:
        return (
            P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
            _unique_clean_refs(repair_reasons),
            _unique_clean_refs(repair_blockers),
        )
    if op03.get("alr_op03_ready_for_op04") is not True:
        return (
            P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
            ["alr_op04_op03_not_ready_fail_closed"],
            ["alr_op04_op03_not_ready_for_op04"],
        )
    if op02_status == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_COMPLETE_CANDIDATE_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
            ["alr_op04_complete_receipt_candidate_priority_2_manual_decision_only"],
            ["alr_downstream_auto_execution_blocked_by_manual_decision_hold"],
        )
    if op02_status == P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_CONTINUABLE_BODYFREE_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
            ["alr_op04_continuable_bodyfree_session_priority_3"],
            [],
        )
    if op02_status in (
        P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_MISSING_REF,
        P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_INCOMPLETE_RETRY_REQUIRED_REF,
    ):
        return (
            P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
            ["alr_op04_no_complete_or_continuable_actual_operation_material_priority_4"],
            ["alr_actual_operation_receipt_missing_or_incomplete"],
        )
    return (
        P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
        ["alr_op04_unknown_inventory_status_fail_closed"],
        ["alr_op04_unknown_inventory_status"],
    )


def build_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver(
    *,
    alr_op03_bodyfree_leak_invalid_source_promotion_scan: Mapping[str, Any] | None = None,
    alr_op02_existing_operation_material_inventory: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Resolve ALR-OP04 selected action without executing the actual review operation."""

    session_id = _safe_review_session_id(review_session_id)
    op03_input = alr_op03_bodyfree_leak_invalid_source_promotion_scan
    if op03_input is None and alr_op02_existing_operation_material_inventory is not None:
        op03_input = build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
            alr_op02_existing_operation_material_inventory=alr_op02_existing_operation_material_inventory,
            review_session_id=session_id,
        )
    if op03_input is None:
        op03_input = build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
            review_session_id=session_id
        )
    op03_valid = False
    try:
        op03_valid = assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(op03_input) is True
    except ValueError:
        op03_valid = False
    selected_action_ref, reason_refs, blocker_refs = _resolve_alr_op04_action(op03_input if op03_valid else None)
    if not op03_valid:
        selected_action_ref = P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
        reason_refs = _unique_clean_refs([*reason_refs, "alr_op04_op03_contract_invalid_fail_closed"])
        blocker_refs = _unique_clean_refs([*blocker_refs, "alr_op04_op03_contract_invalid"])
    action_flags = _action_flags_for_selected_action(selected_action_ref)
    selected_next_step = _selected_action_next_step_ref(selected_action_ref)
    op03 = op03_input if isinstance(op03_input, Mapping) else {}
    operation_plan_required = selected_action_ref in (
        P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
        P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
    )
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op04_continue_retry_repair_complete_action_resolver_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": _clean_ref(op03.get("schema_version"), max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id"), max_length=260),
        "op03_bodyfree_scan_status_ref": _clean_ref(op03.get("bodyfree_scan_status_ref"), max_length=180),
        "op03_promotion_claim_scan_status_ref": _clean_ref(op03.get("promotion_claim_scan_status_ref"), max_length=180),
        "op03_repair_stop_required": op03.get("repair_stop_required") is True,
        "op03_ready_for_op04": op03.get("alr_op03_ready_for_op04") is True,
        "op02_inventory_status_ref": _clean_ref(op03.get("op02_inventory_status_ref"), max_length=180),
        "action_resolver_priority_refs": list(P7_R54_AHR_POST_DMD08_ALR_ACTION_RESOLVER_PRIORITY_REFS),
        "action_resolver_priority_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ACTION_RESOLVER_PRIORITY_REFS),
        "allowed_action_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS),
        "allowed_action_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS),
        "selected_action_ref": selected_action_ref,
        **action_flags,
        "exactly_one_action_flag_true": sum(1 for value in action_flags.values() if value is True) == 1,
        "action_reason_refs": _unique_clean_refs(reason_refs),
        "action_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "action_blocker_refs": _unique_clean_refs(blocker_refs),
        "action_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "operation_plan_required": operation_plan_required,
        "operation_plan_ref": "alr_op04_bodyfree_operation_plan_required_before_actual_operation" if operation_plan_required else "alr_op04_no_operation_plan_execution_here",
        "selected_action_next_step_ref": selected_next_step,
        "alr_op04_resolver_completed": True,
        "alr_op04_does_not_materialize_state_machine": True,
        "alr_op04_does_not_generate_body_full_packet": True,
        "alr_op04_does_not_run_actual_local_human_review": True,
        "alr_op04_does_not_create_receipts_rows_or_disposal": True,
        "alr_op04_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP04_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP04",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP04")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 unexpected fields changed")
    if tuple(data.get("action_resolver_priority_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_ACTION_RESOLVER_PRIORITY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 resolver priority changed")
    if tuple(data.get("allowed_action_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 allowed actions changed")
    for field, count_field in (
        ("action_resolver_priority_refs", "action_resolver_priority_ref_count"),
        ("allowed_action_refs", "allowed_action_ref_count"),
        ("action_reason_refs", "action_reason_ref_count"),
        ("action_blocker_refs", "action_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP04 {count_field} changed")
    selected_action_ref = str(data.get("selected_action_ref"))
    if selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 selected action changed")
    action_flags = {
        "continue_allowed": data.get("continue_allowed") is True,
        "retry_or_start_required": data.get("retry_or_start_required") is True,
        "repair_stop_required": data.get("repair_stop_required") is True,
        "complete_receipt_manual_decision_required": data.get("complete_receipt_manual_decision_required") is True,
    }
    if sum(1 for value in action_flags.values() if value is True) != 1 or data.get("exactly_one_action_flag_true") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 exactly one action flag must be true")
    if action_flags != _action_flags_for_selected_action(selected_action_ref):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 action flags do not match selected action")
    if data.get("selected_action_next_step_ref") != _selected_action_next_step_ref(selected_action_ref):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 action next step changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 next implementation step changed")
    if data.get("operation_plan_required") is not (selected_action_ref in (
        P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
        P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
    )):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 operation-plan requirement changed")
    for key in (
        "alr_op04_resolver_completed",
        "alr_op04_does_not_materialize_state_machine",
        "alr_op04_does_not_generate_body_full_packet",
        "alr_op04_does_not_run_actual_local_human_review",
        "alr_op04_does_not_create_receipts_rows_or_disposal",
        "alr_op04_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op04_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op04_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP04 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 not-claimed refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 fixed non-promotion refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP04_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP04 not-yet steps changed")
    return True


def _state_material_for_action(selected_action_ref: str) -> tuple[str, str, tuple[str, ...], str, str, bool, bool, bool, list[str], list[str]]:
    if selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED_REF,
            P7_R54_AHR_POST_DMD08_ALR_STATE_REVIEW_IN_PROGRESS_BODYFREE_TRACKED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ALLOWED_TRANSITION_REFS_BY_ACTION[selected_action_ref],
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_CONTINUE_EXISTING_REVIEW_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
            True,
            True,
            False,
            ["alr_op05_continue_action_materialized_to_existing_review_operation_state"],
            [],
        )
    if selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_STATE_RETRY_OR_START_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_STATE_EXPLICIT_LOCAL_ONLY_ALLOW_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ALLOWED_TRANSITION_REFS_BY_ACTION[selected_action_ref],
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
            True,
            True,
            False,
            ["alr_op05_retry_or_start_action_materialized_to_explicit_allow_boundary"],
            ["alr_explicit_local_only_allow_required_before_actual_review_operation"],
        )
    if selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_STATE_REPAIR_STOP_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ALLOWED_TRANSITION_REFS_BY_ACTION[selected_action_ref],
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            False,
            False,
            False,
            ["alr_op05_repair_action_materialized_as_repair_stop"],
            ["alr_repair_stop_required_before_actual_review_operation"],
        )
    if selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_STATE_EVIDENCE_COMPLETE_CANDIDATE_REF,
            P7_R54_AHR_POST_DMD08_ALR_STATE_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ALLOWED_TRANSITION_REFS_BY_ACTION[selected_action_ref],
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            False,
            False,
            True,
            ["alr_op05_complete_candidate_materialized_as_downstream_manual_decision_required"],
            ["alr_downstream_auto_execution_blocked_by_manual_decision_hold"],
        )
    return _state_material_for_action(P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF)


def build_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization(
    *,
    alr_op04_continue_retry_repair_complete_action_resolver: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Materialize ALR-OP05 operation state machine from the OP04 selected action."""

    session_id = _safe_review_session_id(review_session_id)
    op04_input = alr_op04_continue_retry_repair_complete_action_resolver
    if op04_input is None:
        op04_input = build_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver(
            review_session_id=session_id
        )
    op04_valid = False
    try:
        op04_valid = assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract(op04_input) is True
    except ValueError:
        op04_valid = False
    op04 = op04_input if isinstance(op04_input, Mapping) else {}
    selected_action_ref = _clean_ref(op04.get("selected_action_ref"), max_length=180)
    if not op04_valid or selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        selected_action_ref = P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    current_state, next_state, allowed_transitions, next_required_step, next_implementation_step, manual_operation_required, explicit_allow_next, downstream_manual_next, reason_refs, blocker_refs = _state_material_for_action(selected_action_ref)
    if not op04_valid:
        reason_refs = _unique_clean_refs([*reason_refs, "alr_op05_op04_contract_invalid_fail_closed"])
        blocker_refs = _unique_clean_refs([*blocker_refs, "alr_op05_op04_contract_invalid"])
    action_flags = _action_flags_for_selected_action(selected_action_ref)
    operation_plan_required = selected_action_ref in (
        P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
        P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
    )
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op05_operation_state_machine_materialization_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": _clean_ref(op04.get("schema_version"), max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id"), max_length=260),
        "op04_selected_action_ref": _clean_ref(op04.get("selected_action_ref"), max_length=180),
        "op04_next_required_step": _clean_ref(op04.get("next_required_step"), max_length=260),
        "op04_ready_for_op05": op04_valid and op04.get("next_required_step") == P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF,
        "selected_action_ref": selected_action_ref,
        **action_flags,
        "operation_state_ref": current_state,
        "next_state_ref": next_state,
        "operation_state_materialized": True,
        "operation_plan_required": operation_plan_required,
        "state_machine_state_refs": list(P7_R54_AHR_POST_DMD08_ALR_STATE_REFS),
        "state_machine_state_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_STATE_REFS),
        "allowed_transition_refs": list(allowed_transitions),
        "allowed_transition_ref_count": len(allowed_transitions),
        "forbidden_transition_refs": list(P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_TRANSITION_REFS),
        "forbidden_transition_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_TRANSITION_REFS),
        "manual_operation_required": manual_operation_required,
        "explicit_local_only_allow_required_next": explicit_allow_next,
        "downstream_manual_decision_required_next": downstream_manual_next,
        "next_manual_operation_ref": next_required_step,
        "body_full_packet_generation_allowed_here": False,
        "actual_review_execution_allowed_here": False,
        "state_machine_reason_refs": _unique_clean_refs(reason_refs),
        "state_machine_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "state_machine_blocker_refs": _unique_clean_refs(blocker_refs),
        "state_machine_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op05_state_machine_materialized": True,
        "alr_op05_does_not_generate_body_full_packet": True,
        "alr_op05_does_not_run_actual_local_human_review": True,
        "alr_op05_does_not_create_receipts_rows_or_disposal": True,
        "alr_op05_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": next_implementation_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP05_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP05_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP05",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP05")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 unexpected fields changed")
    selected_action_ref = str(data.get("selected_action_ref"))
    if selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 selected action changed")
    action_flags = {
        "continue_allowed": data.get("continue_allowed") is True,
        "retry_or_start_required": data.get("retry_or_start_required") is True,
        "repair_stop_required": data.get("repair_stop_required") is True,
        "complete_receipt_manual_decision_required": data.get("complete_receipt_manual_decision_required") is True,
    }
    if sum(1 for value in action_flags.values() if value is True) != 1:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 exactly one action flag must be true")
    if action_flags != _action_flags_for_selected_action(selected_action_ref):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 action flags do not match selected action")
    expected_state, expected_next_state, expected_allowed, expected_next_step, expected_next_implementation_step, expected_manual, expected_allow_next, expected_downstream_next, _, _ = _state_material_for_action(selected_action_ref)
    if data.get("operation_state_ref") != expected_state:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 current operation state changed")
    if data.get("next_state_ref") != expected_next_state:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 next state changed")
    if tuple(data.get("allowed_transition_refs") or ()) != expected_allowed:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 allowed transitions changed")
    if tuple(data.get("forbidden_transition_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FORBIDDEN_TRANSITION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 forbidden transitions changed")
    if data.get("next_required_step") != expected_next_step or data.get("next_implementation_step") != expected_next_implementation_step:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 next step changed")
    if data.get("manual_operation_required") is not expected_manual:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 manual-operation requirement changed")
    if data.get("explicit_local_only_allow_required_next") is not expected_allow_next:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 explicit local-only allow boundary changed")
    if data.get("downstream_manual_decision_required_next") is not expected_downstream_next:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 downstream manual decision boundary changed")
    for key in (
        "operation_state_materialized",
        "alr_op05_state_machine_materialized",
        "alr_op05_does_not_generate_body_full_packet",
        "alr_op05_does_not_run_actual_local_human_review",
        "alr_op05_does_not_create_receipts_rows_or_disposal",
        "alr_op05_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op05_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op05_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP05 required true boundary changed: {key}")
    if data.get("body_full_packet_generation_allowed_here") is not False or data.get("actual_review_execution_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 must not execute review or packet generation")
    for field, count_field in (
        ("state_machine_state_refs", "state_machine_state_ref_count"),
        ("allowed_transition_refs", "allowed_transition_ref_count"),
        ("forbidden_transition_refs", "forbidden_transition_ref_count"),
        ("state_machine_reason_refs", "state_machine_reason_ref_count"),
        ("state_machine_blocker_refs", "state_machine_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP05 {count_field} changed")
    if tuple(data.get("state_machine_state_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_STATE_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 state refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 not-claimed refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 fixed non-promotion refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP05_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP05_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 not-yet steps changed")
    if data.get("operation_plan_required") is not (selected_action_ref in (
        P7_R54_AHR_POST_DMD08_ALR_ACTION_CONTINUE_EXISTING_LOCAL_ONLY_REVIEW_ALLOWED_REF,
        P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
    )):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP05 operation-plan requirement changed")
    return True



def _op05_contract_valid_for_alr_op06(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract(material) is True
    except ValueError:
        return False


def _op06_status_material_for_op05(
    op05: Mapping[str, Any], *, op05_valid: bool
) -> tuple[str, bool, bool, str, str, list[str], list[str]]:
    if not op05_valid:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_REPAIR_REQUIRED_REF,
            False,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op06_op05_contract_invalid_fail_closed"],
            ["alr_op06_op05_contract_invalid"],
        )
    selected_action_ref = _clean_ref(op05.get("selected_action_ref"), max_length=180)
    if selected_action_ref in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_LOCAL_ONLY_REVIEW_ACTION_REFS:
        ready = (
            op05.get("next_implementation_step") == P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF
            and op05.get("explicit_local_only_allow_required_next") is True
            and op05.get("operation_plan_required") is True
        )
        if ready:
            return (
                P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF,
                True,
                True,
                P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF,
                P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF,
                ["alr_op06_explicit_local_only_allow_required_before_packet_or_review"],
                ["alr_body_full_packet_generation_blocked_until_separate_local_only_allow"],
            )
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_REPAIR_REQUIRED_REF,
            False,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op06_local_only_action_without_required_op05_boundary_fail_closed"],
            ["alr_op06_op05_does_not_point_to_explicit_allow_boundary"],
        )
    if selected_action_ref == P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
            False,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            ["alr_op06_complete_receipt_branch_stays_downstream_manual_decision_hold"],
            ["alr_op06_no_packet_request_for_complete_manual_decision_branch"],
        )
    return (
        P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
        False,
        False,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        ["alr_op06_repair_or_unknown_action_keeps_actual_review_operation_closed"],
        ["alr_op06_no_packet_request_for_repair_stop_branch"],
    )


def _op07_forbidden_persistence_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMD08_ALR_OP07_FORBIDDEN_PERSISTENCE_FLAG_REFS}


def _op07_packet_body_not_included_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_BODY_NOT_INCLUDED_FLAG_REFS}


def _bodyfree_packet_request_ref(review_session_id: str) -> str:
    return _clean_ref(
        f"r54_ahr_postdmd08_alr_packet_request_{review_session_id}_24_case_bodyfree_envelope",
        default="r54_ahr_postdmd08_alr_packet_request_bodyfree_envelope",
        max_length=220,
    )


def build_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary(
    *,
    alr_op05_operation_state_machine_materialization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP06 explicit local-only allow requirement boundary material."""

    session_id = _safe_review_session_id(review_session_id)
    op05_input = alr_op05_operation_state_machine_materialization
    if op05_input is None:
        op05_input = build_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization(
            review_session_id=session_id
        )
    op05_valid = _op05_contract_valid_for_alr_op06(op05_input)
    op05 = op05_input if isinstance(op05_input, Mapping) else {}
    selected_action_ref = _clean_ref(op05.get("selected_action_ref"), max_length=180)
    if selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        selected_action_ref = P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
    status_ref, explicit_required, ready_for_op07, next_required_step, next_implementation_step, reason_refs, blocker_refs = _op06_status_material_for_op05(
        op05,
        op05_valid=op05_valid,
    )
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op06_explicit_local_only_allow_requirement_boundary_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": _clean_ref(op05.get("schema_version"), max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id"), max_length=260),
        "op05_selected_action_ref": _clean_ref(op05.get("selected_action_ref"), max_length=180),
        "op05_operation_state_ref": _clean_ref(op05.get("operation_state_ref"), max_length=180),
        "op05_next_state_ref": _clean_ref(op05.get("next_state_ref"), max_length=180),
        "op05_next_required_step": _clean_ref(op05.get("next_required_step"), max_length=260),
        "op05_next_implementation_step": _clean_ref(op05.get("next_implementation_step"), max_length=260),
        "op05_operation_plan_required": op05.get("operation_plan_required") is True,
        "op05_manual_operation_required": op05.get("manual_operation_required") is True,
        "op05_explicit_local_only_allow_required_next": op05.get("explicit_local_only_allow_required_next") is True,
        "op05_ready_for_op06": op05_valid and op05.get("next_implementation_step") == P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
        "selected_action_ref": selected_action_ref,
        "operation_state_ref": _clean_ref(op05.get("operation_state_ref"), max_length=180),
        "next_state_ref": _clean_ref(op05.get("next_state_ref"), max_length=180),
        "local_only_allow_boundary_status_ref": status_ref,
        "allowed_local_only_review_action_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_LOCAL_ONLY_REVIEW_ACTION_REFS),
        "allowed_local_only_review_action_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_LOCAL_ONLY_REVIEW_ACTION_REFS),
        "explicit_local_only_allow_required": explicit_required,
        "operator_explicit_allow_receipt_required_next": explicit_required,
        "operator_explicit_allow_receipt_created_here": False,
        "operator_explicit_allow_granted_here": False,
        "explicit_allow_boundary_closed_bodyfree": explicit_required,
        "body_full_packet_generation_allowed_before_allow": False,
        "actual_human_review_execution_allowed_before_allow": False,
        "body_full_persistence_allowed": False,
        "external_export_allowed": False,
        "raw_body_persistence_allowed": False,
        "reviewer_free_text_allowed": False,
        "question_text_persistence_allowed": False,
        "local_path_persistence_allowed": False,
        "hash_persistence_allowed": False,
        "terminal_body_persistence_allowed": False,
        "body_full_packet_export_allowed": False,
        "packet_request_bodyfree_envelope_allowed_next": ready_for_op07,
        "body_full_packet_generation_allowed_after_op06": False,
        "actual_review_execution_allowed_after_op06": False,
        "alr_op06_ready_for_op07": ready_for_op07,
        "alr_op06_reason_refs": _unique_clean_refs(reason_refs),
        "alr_op06_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "alr_op06_blocker_refs": _unique_clean_refs(blocker_refs),
        "alr_op06_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op06_does_not_generate_body_full_packet": True,
        "alr_op06_does_not_run_actual_local_human_review": True,
        "alr_op06_does_not_create_receipts_rows_or_disposal": True,
        "alr_op06_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": next_implementation_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP06_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP06_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP06",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP06")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 field set changed")
    status_ref = str(data.get("local_only_allow_boundary_status_ref"))
    if status_ref not in P7_R54_AHR_POST_DMD08_ALR_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 invalid status")
    selected_action_ref = str(data.get("selected_action_ref"))
    ready = status_ref == P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF
    if ready:
        if selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_LOCAL_ONLY_REVIEW_ACTION_REFS:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 ready status requires local-only review action")
        for key in (
            "explicit_local_only_allow_required",
            "operator_explicit_allow_receipt_required_next",
            "explicit_allow_boundary_closed_bodyfree",
            "packet_request_bodyfree_envelope_allowed_next",
            "alr_op06_ready_for_op07",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP06 ready flag missing: {key}")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF or data.get("next_implementation_step") != P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 ready next step changed")
    else:
        for key in (
            "explicit_local_only_allow_required",
            "operator_explicit_allow_receipt_required_next",
            "explicit_allow_boundary_closed_bodyfree",
            "packet_request_bodyfree_envelope_allowed_next",
            "alr_op06_ready_for_op07",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP06 non-ready flag opened: {key}")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 downstream manual decision next step changed")
    if status_ref in (
        P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
        P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_REPAIR_REQUIRED_REF,
    ):
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 repair next step changed")
    for key in (
        "operator_explicit_allow_receipt_created_here", "operator_explicit_allow_granted_here",
        "body_full_packet_generation_allowed_before_allow", "actual_human_review_execution_allowed_before_allow",
        "body_full_persistence_allowed", "external_export_allowed", "raw_body_persistence_allowed",
        "reviewer_free_text_allowed", "question_text_persistence_allowed", "local_path_persistence_allowed",
        "hash_persistence_allowed", "terminal_body_persistence_allowed", "body_full_packet_export_allowed",
        "body_full_packet_generation_allowed_after_op06", "actual_review_execution_allowed_after_op06",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP06 forbidden operation flag changed: {key}")
    for key in (
        "alr_op06_does_not_generate_body_full_packet", "alr_op06_does_not_run_actual_local_human_review",
        "alr_op06_does_not_create_receipts_rows_or_disposal", "alr_op06_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op06_does_not_start_p5_p6_p8_p7_or_release", "alr_op06_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP06 required true boundary changed: {key}")
    for field, count_field in (
        ("allowed_local_only_review_action_refs", "allowed_local_only_review_action_ref_count"),
        ("alr_op06_reason_refs", "alr_op06_reason_ref_count"),
        ("alr_op06_blocker_refs", "alr_op06_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP06 {count_field} changed")
    if tuple(data.get("allowed_local_only_review_action_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_ALLOWED_LOCAL_ONLY_REVIEW_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 allowed action refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP06_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP06_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP06 not-yet steps changed")
    return True


def _op07_material_for_op06(
    op06: Mapping[str, Any], *, op06_valid: bool
) -> tuple[str, bool, str, str, list[str], list[str]]:
    if not op06_valid:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_REPAIR_REQUIRED_REF,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op07_op06_contract_invalid_fail_closed"],
            ["alr_op07_op06_contract_invalid"],
        )
    status_ref = _clean_ref(op06.get("local_only_allow_boundary_status_ref"), max_length=220)
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_READY_FOR_PACKET_REQUEST_REF and op06.get("alr_op06_ready_for_op07") is True:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF,
            True,
            P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF,
            ["alr_op07_bodyfree_packet_request_envelope_materialized_without_packet_body"],
            ["alr_packet_generation_requires_separate_explicit_local_only_allow_and_actual_operation"],
        )
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP06_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            ["alr_op07_downstream_manual_decision_branch_has_no_packet_request"],
            ["alr_op07_complete_branch_waits_for_manual_decision"],
        )
    return (
        P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
        False,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
        ["alr_op07_repair_or_non_ready_boundary_has_no_packet_request"],
        ["alr_op07_packet_request_closed_until_repair_is_done"],
    )


def build_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope(
    *,
    alr_op06_explicit_local_only_allow_requirement_boundary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP07 body-full packet request body-free envelope material."""

    session_id = _safe_review_session_id(review_session_id)
    op06_input = alr_op06_explicit_local_only_allow_requirement_boundary
    if op06_input is None:
        op06_input = build_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary(
            review_session_id=session_id
        )
    op06_valid = False
    try:
        op06_valid = assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract(op06_input) is True
    except ValueError:
        op06_valid = False
    op06 = op06_input if isinstance(op06_input, Mapping) else {}
    status_ref, ready, next_required_step, next_implementation_step, reason_refs, blocker_refs = _op07_material_for_op06(
        op06,
        op06_valid=op06_valid,
    )
    requested_count = P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT if ready else 0
    packet_request_ref = _bodyfree_packet_request_ref(session_id) if ready else ""
    packet_not_included = _op07_packet_body_not_included_flags()
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": _clean_ref(op06.get("schema_version"), max_length=260),
        "op06_material_ref": _clean_ref(op06.get("material_id"), max_length=260),
        "op06_status_ref": _clean_ref(op06.get("local_only_allow_boundary_status_ref"), max_length=220),
        "op06_next_required_step": _clean_ref(op06.get("next_required_step"), max_length=260),
        "op06_next_implementation_step": _clean_ref(op06.get("next_implementation_step"), max_length=260),
        "op06_ready_for_op07": op06.get("alr_op06_ready_for_op07") is True,
        "op06_explicit_local_only_allow_required": op06.get("explicit_local_only_allow_required") is True,
        "op06_packet_request_bodyfree_envelope_allowed_next": op06.get("packet_request_bodyfree_envelope_allowed_next") is True,
        "selected_action_ref": _clean_ref(op06.get("selected_action_ref"), default=P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF, max_length=180),
        "packet_request_ref": packet_request_ref,
        "packet_request_status_ref": status_ref,
        "allowed_packet_request_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP07_ALLOWED_STATUS_REFS),
        "allowed_packet_request_status_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP07_ALLOWED_STATUS_REFS),
        "requested_case_count": requested_count,
        "expected_review_unit_count": requested_count,
        "review_unit_kind_ref": P7_R54_AHR_POST_DMD08_ALR_OP07_REVIEW_UNIT_KIND_REF if ready else "",
        "reviewer_form_kind_ref": P7_R54_AHR_POST_DMD08_ALR_OP07_REVIEWER_FORM_KIND_REF if ready else "",
        "packet_request_bodyfree_envelope_ready": ready,
        "body_full_packet_request_bodyfree_envelope_ready": ready,
        "packet_generation_allowed_only_after_explicit_local_only_allow": ready,
        "explicit_local_only_allow_required_before_packet_generation": ready,
        "packet_generation_allowed_here": False,
        "body_full_packet_generation_allowed_here": False,
        "actual_review_execution_allowed_here": False,
        "body_full_packet_body_included": False,
        "packet_export_allowed": False,
        "body_full_packet_export_allowed": False,
        "raw_body_persistence_allowed": False,
        "reviewer_free_text_allowed": False,
        "question_text_persistence_allowed": False,
        "local_path_persistence_allowed": False,
        "hash_persistence_allowed": False,
        "terminal_body_persistence_allowed": False,
        "export_denylist_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_EXPORT_DENYLIST_REFS),
        "forbidden_persistence_flags": _op07_forbidden_persistence_flags(),
        "forbidden_persistence_flag_count": len(P7_R54_AHR_POST_DMD08_ALR_OP07_FORBIDDEN_PERSISTENCE_FLAG_REFS),
        "packet_body_not_included_flags": packet_not_included,
        "packet_body_not_included_flag_count": len(P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_BODY_NOT_INCLUDED_FLAG_REFS),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "reviewer_note_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "answer_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "packet_request_reason_refs": _unique_clean_refs(reason_refs),
        "packet_request_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "packet_request_blocker_refs": _unique_clean_refs(blocker_refs),
        "packet_request_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op07_does_not_generate_body_full_packet": True,
        "alr_op07_does_not_run_actual_local_human_review": True,
        "alr_op07_does_not_create_receipts_rows_or_disposal": True,
        "alr_op07_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": next_implementation_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP07_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP07_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP07",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP07")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 field set changed")
    status_ref = str(data.get("packet_request_status_ref"))
    if status_ref not in P7_R54_AHR_POST_DMD08_ALR_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 invalid packet request status")
    ready = status_ref == P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF
    if ready:
        if data.get("packet_request_ref") == "" or data.get("requested_case_count") != P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 ready packet request shape changed")
        if data.get("expected_review_unit_count") != P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 expected review unit count changed")
        for key in (
            "packet_request_bodyfree_envelope_ready", "body_full_packet_request_bodyfree_envelope_ready",
            "packet_generation_allowed_only_after_explicit_local_only_allow",
            "explicit_local_only_allow_required_before_packet_generation",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP07 ready flag missing: {key}")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 ready next step changed")
    else:
        if data.get("packet_request_ref") != "" or data.get("requested_case_count") != 0 or data.get("expected_review_unit_count") != 0:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 non-ready packet request must stay empty")
        for key in (
            "packet_request_bodyfree_envelope_ready", "body_full_packet_request_bodyfree_envelope_ready",
            "packet_generation_allowed_only_after_explicit_local_only_allow",
            "explicit_local_only_allow_required_before_packet_generation",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP07 non-ready flag opened: {key}")
    for key in (
        "packet_generation_allowed_here", "body_full_packet_generation_allowed_here", "actual_review_execution_allowed_here",
        "body_full_packet_body_included", "packet_export_allowed", "body_full_packet_export_allowed",
        "raw_body_persistence_allowed", "reviewer_free_text_allowed", "question_text_persistence_allowed",
        "local_path_persistence_allowed", "hash_persistence_allowed", "terminal_body_persistence_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP07 forbidden operation flag changed: {key}")
    if any(value is not False for value in (data.get("forbidden_persistence_flags") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 forbidden persistence opened")
    if any(value is not False for value in (data.get("packet_body_not_included_flags") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 packet body marker opened")
    for key in P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_BODY_NOT_INCLUDED_FLAG_REFS:
        if key in data and data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP07 packet body field opened: {key}")
    for key in (
        "alr_op07_does_not_generate_body_full_packet", "alr_op07_does_not_run_actual_local_human_review",
        "alr_op07_does_not_create_receipts_rows_or_disposal", "alr_op07_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op07_does_not_start_p5_p6_p8_p7_or_release", "alr_op07_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP07 required true boundary changed: {key}")
    for field, count_field in (
        ("allowed_packet_request_status_refs", "allowed_packet_request_status_ref_count"),
        ("export_denylist_refs", "export_denylist_ref_count"),
        ("packet_request_reason_refs", "packet_request_reason_ref_count"),
        ("packet_request_blocker_refs", "packet_request_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP07 {count_field} changed")
    if data.get("forbidden_persistence_flag_count") != len(data.get("forbidden_persistence_flags") or {}):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 forbidden persistence count changed")
    if data.get("packet_body_not_included_flag_count") != len(data.get("packet_body_not_included_flags") or {}):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 packet body count changed")
    if tuple(data.get("allowed_packet_request_status_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 status refs changed")
    if tuple(data.get("export_denylist_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP07_PACKET_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 export denylist changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP07_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP07_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 not-yet steps changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP07 not-claimed boundary must stay false")
    return True


# Compatibility aliases with the full operation name used in the design title.
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op00_scope_no_touch_no_promotion_refreeze = (
    build_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op00_scope_no_touch_no_promotion_refreeze_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op00_scope_no_touch_no_promotion_refreeze_contract
)
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op01_dmd_op08_result_memo_branch_intake = (
    build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op01_dmd_op08_result_memo_branch_intake_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract
)

build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_dmd_op08_branch_intake = (
    build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_dmd_op08_branch_intake_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract
)

build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_existing_operation_material_inventory = (
    build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_existing_operation_material_inventory_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract
)
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op03_bodyfree_leak_invalid_source_promotion_scan = (
    build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract
)


build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op04_continue_retry_repair_complete_action_resolver = (
    build_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op04_continue_retry_repair_complete_action_resolver_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver_contract
)
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op05_operation_state_machine_materialization = (
    build_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op05_operation_state_machine_materialization_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization_contract
)
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op06_explicit_local_only_allow_requirement_boundary = (
    build_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op06_explicit_local_only_allow_requirement_boundary_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary_contract
)
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op07_bodyfull_packet_request_bodyfree_envelope = (
    build_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope
)
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract = (
    assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract
)


# ALR-OP08/OP09 extension: expected actual operation receipt and selection-only row schema guards.
P7_R54_AHR_POST_DMD08_ALR_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op08_actual_operation_receipt_expected_schema_completeness_guard.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op09_selection_only_rows_rating_question_need_expected_schema_guard.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.alr.sanitized_review_result_row.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.alr.rating_row.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.alr.question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:9]
P7_R54_AHR_POST_DMD08_ALR_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[9:]
P7_R54_AHR_POST_DMD08_ALR_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:10]
P7_R54_AHR_POST_DMD08_ALR_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[10:]

P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF: Final = (
    "ALR_ACTUAL_OPERATION_RECEIPT_EXPECTED_SCHEMA_READY_RECEIPT_MISSING"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF: Final = (
    "ALR_ACTUAL_OPERATION_RECEIPT_EXPECTED_SCHEMA_READY_RECEIPT_INCOMPLETE"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF: Final = (
    "ALR_ACTUAL_OPERATION_RECEIPT_EXPECTED_SCHEMA_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF: Final = (
    "ALR_ACTUAL_OPERATION_RECEIPT_COMPLETE_CANDIDATE_BODYFREE"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF: Final = (
    "ALR_ACTUAL_OPERATION_RECEIPT_EXPECTED_SCHEMA_NOT_APPLICABLE_REPAIR_STOP"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF: Final = (
    "ALR_ACTUAL_OPERATION_RECEIPT_EXPECTED_SCHEMA_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION"
)
P7_R54_AHR_POST_DMD08_ALR_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP08_EXPECTED_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_receipt_ref",
    "review_session_id",
    "source_kind_ref",
    *P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS[:-1],
    *P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS,
    "body_free",
)

P7_R54_AHR_POST_DMD08_ALR_ALLOWED_VERDICT_REFS: Final[tuple[str, ...]] = (
    "VERDICT_PASS_BODYFREE",
    "VERDICT_PASS_WITH_MINOR_REPAIR_BODYFREE",
    "VERDICT_FAIL_READFEEL_BODYFREE",
    "VERDICT_FAIL_LABEL_CONNECTION_BODYFREE",
    "VERDICT_FAIL_SAFE_DISPLAY_BODYFREE",
    "VERDICT_FAIL_OPERATION_BOUNDARY_BODYFREE",
    "VERDICT_REVIEW_BLOCKED_BODYFREE",
)
P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS: Final[tuple[str, ...]] = (
    "read_as_written_score",
    "label_connection_score",
    "history_line_connection_score",
    "current_input_respect_score",
    "non_template_surface_score",
    "safe_display_boundary_score",
    "next_input_motivation_score",
)
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_RATING_SCORE_REFS: Final[tuple[int, ...]] = (0, 1, 2, 3)
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "QUESTION_NEED_NONE",
    "QUESTION_NEED_LOW_CONTEXT_ONLY",
    "QUESTION_NEED_AMBIGUOUS_TARGET",
    "QUESTION_NEED_TIME_OR_EVENT_CLARIFICATION",
    "QUESTION_NEED_RELATION_OR_ACTOR_CLARIFICATION",
    "QUESTION_NEED_SAFETY_BOUNDARY_CLARIFICATION",
    "QUESTION_NEED_NOT_QUESTION_BUT_CORE_REPAIR_REQUIRED",
)
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_AMBIGUITY_KIND_REFS: Final[tuple[str, ...]] = (
    "AMBIGUITY_NONE",
    "AMBIGUITY_WHO",
    "AMBIGUITY_WHEN",
    "AMBIGUITY_WHAT_EVENT",
    "AMBIGUITY_RELATION",
    "AMBIGUITY_INTENT",
    "AMBIGUITY_HISTORY_LINK",
    "AMBIGUITY_SAFETY_SCOPE",
)
P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "ONE_QUESTION_NOT_NEEDED",
    "ONE_QUESTION_COULD_HELP",
    "ONE_QUESTION_RISKY_OR_TOO_EARLY",
    "ONE_QUESTION_NOT_ENOUGH_CORE_REPAIR_REQUIRED",
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF: Final = (
    "ALR_SELECTION_ONLY_ROWS_EXPECTED_SCHEMA_READY_ROWS_MISSING"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF: Final = (
    "ALR_SELECTION_ONLY_ROWS_EXPECTED_SCHEMA_READY_ROWS_INCOMPLETE"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF: Final = (
    "ALR_SELECTION_ONLY_ROWS_EXPECTED_SCHEMA_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF: Final = (
    "ALR_SELECTION_ONLY_ROWS_COMPLETE_CANDIDATE_BODYFREE"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF: Final = (
    "ALR_SELECTION_ONLY_ROWS_EXPECTED_SCHEMA_NOT_APPLICABLE_REPAIR_STOP"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF: Final = (
    "ALR_SELECTION_ONLY_ROWS_EXPECTED_SCHEMA_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION"
)
P7_R54_AHR_POST_DMD08_ALR_OP09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP09_FORBIDDEN_ROW_TEXT_FLAG_REFS: Final[tuple[str, ...]] = (
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "raw_input_included",
    "comment_text_body_included",
    "returned_surface_body_included",
)
P7_R54_AHR_POST_DMD08_ALR_OP09_SANITIZED_REVIEW_RESULT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "review_session_id", "case_ref", "verdict_ref", "sanitized_reason_ids", "blocker_refs",
    *P7_R54_AHR_POST_DMD08_ALR_OP09_FORBIDDEN_ROW_TEXT_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP09_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "review_session_id", "case_ref", "rating_axis_scores",
    *P7_R54_AHR_POST_DMD08_ALR_OP09_FORBIDDEN_ROW_TEXT_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP09_QUESTION_NEED_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "review_session_id", "case_ref", "question_need_primary_class_ref", "ambiguity_kind_refs",
    "one_question_fit_ref", "repair_required_refs", *P7_R54_AHR_POST_DMD08_ALR_OP09_FORBIDDEN_ROW_TEXT_FLAG_REFS,
    "p8_question_spec_created", "body_free",
)

P7_R54_AHR_POST_DMD08_ALR_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_next_required_step",
    "op07_next_implementation_step", "op07_ready_for_op08", "packet_request_ref", "requested_case_count",
    "actual_operation_receipt_expected_schema_version_ref", "actual_operation_receipt_expected_schema_field_refs",
    "actual_operation_receipt_expected_schema_field_ref_count", "actual_operation_receipt_required_count_field_refs",
    "actual_operation_receipt_required_count_field_ref_count", "actual_operation_receipt_required_true_guard_field_refs",
    "actual_operation_receipt_required_true_guard_field_ref_count", "actual_operation_receipt_repair_guard_field_refs",
    "actual_operation_receipt_repair_guard_field_ref_count", "actual_operation_receipt_guard_status_ref",
    "allowed_actual_operation_receipt_guard_status_refs", "allowed_actual_operation_receipt_guard_status_ref_count",
    "actual_operation_receipt_present", "actual_operation_receipt_schema_version", "actual_operation_receipt_schema_version_valid",
    "operation_receipt_ref", "operation_receipt_ref_consistent", "actual_operation_receipt_source_kind_ref",
    "actual_operation_receipt_source_kind_valid", "created_from_real_operation", "actual_source_guard_passed",
    "actual_human_review_executed_by_person", "reviewed_case_count", "selection_row_count",
    "sanitized_review_result_row_count", "rating_row_count", "question_need_observation_row_count",
    "receipt_count_summary", "receipt_count_pass_refs", "receipt_count_complete", "disposal_purge_receipt_accepted",
    "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed",
    "no_terminal_output_body_validation_passed", "no_touch_validation_passed", "receipt_guard_true_field_pass_refs",
    "receipt_guard_complete", "actual_operation_receipt_forbidden_payload_key_paths",
    "actual_operation_receipt_forbidden_payload_key_path_count", "actual_operation_receipt_safe_ref_shape_violation_paths",
    "actual_operation_receipt_safe_ref_shape_violation_path_count", "actual_operation_receipt_complete_candidate",
    "actual_operation_receipt_missing_or_incomplete", "bodyfree_evidence_boundary_repair_required",
    "actual_operation_receipt_expected_schema_guard_ready", "alr_op08_ready_for_op09", "op08_reason_refs",
    "op08_reason_ref_count", "op08_blocker_refs", "op08_blocker_ref_count",
    "alr_op08_does_not_create_actual_operation_receipt", "alr_op08_does_not_generate_body_full_packet",
    "alr_op08_does_not_run_actual_local_human_review", "alr_op08_does_not_create_rows_or_disposal",
    "alr_op08_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op08_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op08_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "next_implementation_step", "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op08_schema_version", "op08_material_ref", "op08_status_ref", "op08_next_required_step",
    "op08_next_implementation_step", "op08_ready_for_op09", "row_schema_guard_status_ref",
    "allowed_row_schema_guard_status_refs", "allowed_row_schema_guard_status_ref_count",
    "sanitized_review_result_row_schema_version", "rating_row_schema_version", "question_need_observation_row_schema_version",
    "sanitized_review_result_required_field_refs", "sanitized_review_result_required_field_ref_count",
    "rating_row_required_field_refs", "rating_row_required_field_ref_count", "question_need_observation_required_field_refs",
    "question_need_observation_required_field_ref_count", "allowed_verdict_refs", "allowed_verdict_ref_count",
    "rating_axis_refs", "rating_axis_ref_count", "allowed_rating_score_refs", "allowed_rating_score_ref_count",
    "allowed_question_need_primary_class_refs", "allowed_question_need_primary_class_ref_count",
    "allowed_ambiguity_kind_refs", "allowed_ambiguity_kind_ref_count", "allowed_one_question_fit_refs",
    "allowed_one_question_fit_ref_count", "selection_only_rows_expected_case_count", "sanitized_review_result_row_count",
    "rating_row_count", "question_need_observation_row_count", "sanitized_review_result_row_count_is_24",
    "rating_row_count_is_24", "question_need_observation_row_count_is_24", "row_count_complete",
    "sanitized_review_result_rows_bodyfree_valid", "rating_rows_bodyfree_valid", "question_need_observation_rows_bodyfree_valid",
    "row_bodyfree_schema_guard_ready", "rows_complete_candidate", "rows_missing_or_incomplete", "rows_repair_required",
    "question_text_included", "draft_question_text_included", "reviewer_free_text_included", "raw_input_included",
    "comment_text_body_included", "returned_surface_body_included", "p8_question_spec_created", "p8_question_trigger_created",
    "row_forbidden_payload_key_paths", "row_forbidden_payload_key_path_count", "row_safe_ref_shape_violation_paths",
    "row_safe_ref_shape_violation_path_count", "row_schema_violation_refs", "row_schema_violation_ref_count",
    "op09_reason_refs", "op09_reason_ref_count", "op09_blocker_refs", "op09_blocker_ref_count",
    "alr_op09_does_not_create_actual_rows", "alr_op09_does_not_create_question_text_or_p8_spec",
    "alr_op09_does_not_generate_body_full_packet", "alr_op09_does_not_run_actual_local_human_review",
    "alr_op09_does_not_create_disposal_or_purge_receipt", "alr_op09_does_not_execute_postcr22_ex_reentry_or_r52",
    "alr_op09_does_not_start_p5_p6_p8_p7_or_release", "alr_op09_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "next_implementation_step", "public_contract",
    "post_dmd08_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

def _op07_contract_valid_for_alr_op08(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope_contract(material) is True
    except ValueError:
        return False

def _op08_receipt_status_material(
    op07: Mapping[str, Any],
    *,
    op07_valid: bool,
    receipt: Mapping[str, Any] | None,
    review_session_id: str,
) -> tuple[str, bool, bool, str, str, list[str], list[str]]:
    if not op07_valid:
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF, False, True,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                ["alr_op08_op07_contract_invalid_fail_closed"], ["alr_op08_op07_contract_invalid"])
    op07_status_ref = _clean_ref(op07.get("packet_request_status_ref"), max_length=220)
    if op07_status_ref == P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF:
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF, False, True,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                ["alr_op08_repair_stop_branch_has_no_receipt_guard_path"], ["alr_op08_packet_request_not_applicable_repair_stop"])
    if op07_status_ref == P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF:
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF, False, False,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
                P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
                ["alr_op08_complete_branch_stays_downstream_manual_decision_hold"], ["alr_op08_no_receipt_guard_for_downstream_manual_decision_branch"])
    if op07_status_ref != P7_R54_AHR_POST_DMD08_ALR_OP07_STATUS_PACKET_REQUEST_BODYFREE_ENVELOPE_READY_REF:
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF, False, True,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                ["alr_op08_unknown_op07_status_fail_closed"], ["alr_op08_unknown_op07_status"])
    if not isinstance(receipt, Mapping):
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF, False, False,
                P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
                ["alr_op08_expected_receipt_schema_guard_ready_without_actual_receipt"], ["alr_op08_actual_operation_receipt_missing"])
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="actual_operation_receipt_bodyfree")
    safe_ref_paths = _scan_safe_ref_shape_violation_paths(receipt, path="actual_operation_receipt_bodyfree")
    if forbidden_paths or safe_ref_paths or _source_kind_ref(receipt) in P7_R54_AHR_POST_DMD08_ALR_INVALID_SOURCE_KIND_REFS:
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF, False, True,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                ["alr_op08_receipt_boundary_repair_required"], ["alr_op08_receipt_contains_forbidden_or_invalid_material"])
    if any(receipt.get(field) is False for field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REPAIR_GUARD_FIELD_REFS):
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF, False, True,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
                ["alr_op08_receipt_no_leak_guard_false_repair_required"], ["alr_op08_receipt_repair_guard_failed"])
    receipt_count_complete = all(_receipt_count_pass_refs(receipt).values())
    guard_complete = _receipt_guard_complete(receipt)
    schema_valid = _receipt_schema_version(receipt) == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
    source_valid = _source_kind_ref(receipt) == P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF
    session_valid = _material_review_session_id(receipt) == review_session_id
    receipt_ref_valid = _clean_ref(receipt.get("operation_receipt_ref"), default="", max_length=220) != ""
    if receipt_count_complete and guard_complete and schema_valid and source_valid and session_valid and receipt_ref_valid:
        return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF, True, False,
                P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
                ["alr_op08_actual_operation_receipt_complete_candidate_by_schema_counts_and_guards"],
                ["alr_op08_complete_candidate_still_requires_selection_rows_guard_and_downstream_manual_decision"])
    return (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF, False, False,
            P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
            ["alr_op08_actual_operation_receipt_present_but_incomplete"], ["alr_op08_actual_operation_receipt_schema_counts_or_guards_incomplete"])

def build_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard(
    *,
    alr_op07_bodyfull_packet_request_bodyfree_envelope: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP08 expected actual operation receipt schema / completeness guard."""
    session_id = _safe_review_session_id(review_session_id)
    op07_input = alr_op07_bodyfull_packet_request_bodyfree_envelope
    if op07_input is None:
        op07_input = build_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope(review_session_id=session_id)
    op07_valid = _op07_contract_valid_for_alr_op08(op07_input)
    op07 = op07_input if isinstance(op07_input, Mapping) else {}
    receipt = actual_operation_receipt_bodyfree if isinstance(actual_operation_receipt_bodyfree, Mapping) else None
    status_ref, complete_candidate, repair_required, next_required_step, next_implementation_step, reason_refs, blocker_refs = _op08_receipt_status_material(op07, op07_valid=op07_valid, receipt=receipt, review_session_id=session_id)
    count_summary = _receipt_count_summary(receipt)
    count_pass = _receipt_count_pass_refs(receipt)
    guard_pass_refs = {field: (receipt.get(field) is True if isinstance(receipt, Mapping) else False) for field in P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS}
    forbidden_paths = _as_path_list(_scan_forbidden_payload_key_paths(receipt, path="actual_operation_receipt_bodyfree") if isinstance(receipt, Mapping) else [])
    safe_ref_paths = _as_path_list(_scan_safe_ref_shape_violation_paths(receipt, path="actual_operation_receipt_bodyfree") if isinstance(receipt, Mapping) else [])
    receipt_ref = _clean_ref(receipt.get("operation_receipt_ref") if isinstance(receipt, Mapping) else "", default="actual_operation_receipt_ref_missing", max_length=220)
    schema_version = _receipt_schema_version(receipt)
    source_kind = _source_kind_ref(receipt, default="actual_operation_receipt_source_kind_missing")
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op08_actual_operation_receipt_expected_schema_guard_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_schema_version": _clean_ref(op07.get("schema_version"), max_length=260),
        "op07_material_ref": _clean_ref(op07.get("material_id"), max_length=260),
        "op07_status_ref": _clean_ref(op07.get("packet_request_status_ref"), max_length=220),
        "op07_next_required_step": _clean_ref(op07.get("next_required_step"), max_length=260),
        "op07_next_implementation_step": _clean_ref(op07.get("next_implementation_step"), max_length=260),
        "op07_ready_for_op08": op07_valid and op07.get("next_implementation_step") == P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF,
        "packet_request_ref": _clean_ref(op07.get("packet_request_ref"), max_length=220),
        "requested_case_count": op07.get("requested_case_count") if isinstance(op07.get("requested_case_count"), int) else 0,
        "actual_operation_receipt_expected_schema_version_ref": dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION,
        "actual_operation_receipt_expected_schema_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP08_EXPECTED_RECEIPT_FIELD_REFS),
        "actual_operation_receipt_expected_schema_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP08_EXPECTED_RECEIPT_FIELD_REFS),
        "actual_operation_receipt_required_count_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS),
        "actual_operation_receipt_required_count_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS),
        "actual_operation_receipt_required_true_guard_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS),
        "actual_operation_receipt_required_true_guard_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS),
        "actual_operation_receipt_repair_guard_field_refs": list(dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REPAIR_GUARD_FIELD_REFS),
        "actual_operation_receipt_repair_guard_field_ref_count": len(dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_REPAIR_GUARD_FIELD_REFS),
        "actual_operation_receipt_guard_status_ref": status_ref,
        "allowed_actual_operation_receipt_guard_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP08_ALLOWED_STATUS_REFS),
        "allowed_actual_operation_receipt_guard_status_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP08_ALLOWED_STATUS_REFS),
        "actual_operation_receipt_present": isinstance(receipt, Mapping),
        "actual_operation_receipt_schema_version": schema_version,
        "actual_operation_receipt_schema_version_valid": schema_version == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": receipt_ref,
        "operation_receipt_ref_consistent": receipt_ref != "actual_operation_receipt_ref_missing",
        "actual_operation_receipt_source_kind_ref": source_kind,
        "actual_operation_receipt_source_kind_valid": source_kind == P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF,
        "created_from_real_operation": guard_pass_refs["created_from_real_operation"],
        "actual_source_guard_passed": guard_pass_refs["actual_source_guard_passed"],
        "actual_human_review_executed_by_person": guard_pass_refs["actual_human_review_executed_by_person"],
        "reviewed_case_count": count_summary["reviewed_case_count"],
        "selection_row_count": count_summary["selection_row_count"],
        "sanitized_review_result_row_count": count_summary["sanitized_review_result_row_count"],
        "rating_row_count": count_summary["rating_row_count"],
        "question_need_observation_row_count": count_summary["question_need_observation_row_count"],
        "receipt_count_summary": count_summary,
        "receipt_count_pass_refs": count_pass,
        "receipt_count_complete": all(count_pass.values()),
        "disposal_purge_receipt_accepted": guard_pass_refs["disposal_purge_receipt_accepted"],
        "no_body_leak_validation_passed": guard_pass_refs["no_body_leak_validation_passed"],
        "no_question_text_validation_passed": guard_pass_refs["no_question_text_validation_passed"],
        "no_path_hash_validation_passed": guard_pass_refs["no_path_hash_validation_passed"],
        "no_terminal_output_body_validation_passed": guard_pass_refs["no_terminal_output_body_validation_passed"],
        "no_touch_validation_passed": guard_pass_refs["no_touch_validation_passed"],
        "receipt_guard_true_field_pass_refs": guard_pass_refs,
        "receipt_guard_complete": all(guard_pass_refs.values()),
        "actual_operation_receipt_forbidden_payload_key_paths": forbidden_paths,
        "actual_operation_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "actual_operation_receipt_safe_ref_shape_violation_paths": safe_ref_paths,
        "actual_operation_receipt_safe_ref_shape_violation_path_count": len(safe_ref_paths),
        "actual_operation_receipt_complete_candidate": complete_candidate,
        "actual_operation_receipt_missing_or_incomplete": status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF),
        "bodyfree_evidence_boundary_repair_required": repair_required,
        "actual_operation_receipt_expected_schema_guard_ready": status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF, P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF),
        "alr_op08_ready_for_op09": next_implementation_step == P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
        "op08_reason_refs": _unique_clean_refs(reason_refs),
        "op08_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "op08_blocker_refs": _unique_clean_refs(blocker_refs),
        "op08_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op08_does_not_create_actual_operation_receipt": True,
        "alr_op08_does_not_generate_body_full_packet": True,
        "alr_op08_does_not_run_actual_local_human_review": True,
        "alr_op08_does_not_create_rows_or_disposal": True,
        "alr_op08_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": next_implementation_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(data)
    return data

def assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(data: Mapping[str, Any]) -> bool:
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMD08_ALR_OP08_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP08_STEP_REF, source="P7-R54-AHR-PostDMD08-ALR-OP08")
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP08")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 field set changed")
    status_ref = str(data.get("actual_operation_receipt_guard_status_ref"))
    if status_ref not in P7_R54_AHR_POST_DMD08_ALR_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 invalid receipt guard status")
    for field, count_field in (("actual_operation_receipt_expected_schema_field_refs", "actual_operation_receipt_expected_schema_field_ref_count"), ("actual_operation_receipt_required_count_field_refs", "actual_operation_receipt_required_count_field_ref_count"), ("actual_operation_receipt_required_true_guard_field_refs", "actual_operation_receipt_required_true_guard_field_ref_count"), ("actual_operation_receipt_repair_guard_field_refs", "actual_operation_receipt_repair_guard_field_ref_count"), ("allowed_actual_operation_receipt_guard_status_refs", "allowed_actual_operation_receipt_guard_status_ref_count"), ("actual_operation_receipt_forbidden_payload_key_paths", "actual_operation_receipt_forbidden_payload_key_path_count"), ("actual_operation_receipt_safe_ref_shape_violation_paths", "actual_operation_receipt_safe_ref_shape_violation_path_count"), ("op08_reason_refs", "op08_reason_ref_count"), ("op08_blocker_refs", "op08_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP08 {count_field} changed")
    if data.get("actual_operation_receipt_expected_schema_version_ref") != dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 DMD-compatible schema version changed")
    if tuple(data.get("actual_operation_receipt_required_count_field_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 count fields changed")
    if tuple(data.get("actual_operation_receipt_required_true_guard_field_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 true guard fields changed")
    count_summary = data.get("receipt_count_summary") or {}
    count_pass_refs = data.get("receipt_count_pass_refs") or {}
    for field in P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS:
        if data.get(field) != count_summary.get(field):
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 top-level receipt count diverged from count summary")
        expected_count_pass = data.get(field) == dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT
        if count_pass_refs.get(field) is not expected_count_pass:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 receipt count pass refs diverged from top-level counts")
    if data.get("receipt_count_complete") is not all(count_pass_refs.get(field) is True for field in P7_R54_AHR_POST_DMD08_ALR_OP02_COUNT_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 receipt count complete flag diverged from pass refs")
    guard_pass_refs = data.get("receipt_guard_true_field_pass_refs") or {}
    for field in P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS:
        if field == "body_free":
            continue
        if guard_pass_refs.get(field) is not (data.get(field) is True):
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 receipt guard pass refs diverged from top-level receipt guards")
    if data.get("receipt_guard_complete") is not all(guard_pass_refs.get(field) is True for field in P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_TRUE_RECEIPT_GUARD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 receipt guard complete flag diverged from pass refs")
    complete = status_ref == P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF
    if complete:
        if data.get("actual_operation_receipt_complete_candidate") is not True or data.get("receipt_count_complete") is not True or data.get("receipt_guard_complete") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 complete candidate counts/guards changed")
        if data.get("actual_operation_receipt_schema_version_valid") is not True or data.get("actual_operation_receipt_source_kind_valid") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 complete candidate schema/source changed")
    elif data.get("actual_operation_receipt_complete_candidate") is not False:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 non-complete path promoted receipt complete")
    if status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_INCOMPLETE_REF, P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_COMPLETE_CANDIDATE_REF):
        if data.get("actual_operation_receipt_expected_schema_guard_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 expected schema guard or next step changed")
    for key in ("alr_op08_does_not_create_actual_operation_receipt", "alr_op08_does_not_generate_body_full_packet", "alr_op08_does_not_run_actual_local_human_review", "alr_op08_does_not_create_rows_or_disposal", "alr_op08_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op08_does_not_start_p5_p6_p8_p7_or_release", "alr_op08_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP08 required true boundary changed: {key}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP08_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 step list changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP08 not-claimed boundary must stay false")
    return True

def _op08_contract_valid_for_alr_op09(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract(material) is True
    except ValueError:
        return False

def _as_bodyfree_row_sequence(rows: Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if rows is None:
        return []
    return [row for row in rows if isinstance(row, Mapping)]

def _row_bodyfree_base_valid(row: Mapping[str, Any], *, review_session_id: str, expected_schema_version: str) -> bool:
    return (row.get("schema_version") == expected_schema_version and _material_review_session_id(row) == review_session_id and _clean_ref(row.get("case_ref"), default="", max_length=180) != "" and row.get("body_free") is True and all(row.get(flag) is False for flag in P7_R54_AHR_POST_DMD08_ALR_OP09_FORBIDDEN_ROW_TEXT_FLAG_REFS) and not _scan_forbidden_payload_key_paths(row, path="row") and not _scan_safe_ref_shape_violation_paths(row, path="row"))

def _sanitized_review_result_row_valid(row: Mapping[str, Any], *, review_session_id: str) -> bool:
    return (_row_bodyfree_base_valid(row, review_session_id=review_session_id, expected_schema_version=P7_R54_AHR_POST_DMD08_ALR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION) and _clean_ref(row.get("verdict_ref"), default="", max_length=180) in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_VERDICT_REFS and isinstance(row.get("sanitized_reason_ids"), Sequence) and not isinstance(row.get("sanitized_reason_ids"), (str, bytes, bytearray)) and isinstance(row.get("blocker_refs"), Sequence) and not isinstance(row.get("blocker_refs"), (str, bytes, bytearray)))

def _rating_row_valid(row: Mapping[str, Any], *, review_session_id: str) -> bool:
    scores = row.get("rating_axis_scores")
    return isinstance(scores, Mapping) and _row_bodyfree_base_valid(row, review_session_id=review_session_id, expected_schema_version=P7_R54_AHR_POST_DMD08_ALR_RATING_ROW_SCHEMA_VERSION) and set(scores) == set(P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS) and all(score in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_RATING_SCORE_REFS for score in scores.values())

def _question_need_observation_row_valid(row: Mapping[str, Any], *, review_session_id: str) -> bool:
    ambiguity_refs = row.get("ambiguity_kind_refs")
    repair_refs = row.get("repair_required_refs")
    return (_row_bodyfree_base_valid(row, review_session_id=review_session_id, expected_schema_version=P7_R54_AHR_POST_DMD08_ALR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION) and _clean_ref(row.get("question_need_primary_class_ref"), default="", max_length=180) in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_QUESTION_NEED_PRIMARY_CLASS_REFS and isinstance(ambiguity_refs, Sequence) and not isinstance(ambiguity_refs, (str, bytes, bytearray)) and all(_clean_ref(ref, max_length=160) in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_AMBIGUITY_KIND_REFS for ref in ambiguity_refs) and _clean_ref(row.get("one_question_fit_ref"), default="", max_length=180) in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ONE_QUESTION_FIT_REFS and isinstance(repair_refs, Sequence) and not isinstance(repair_refs, (str, bytes, bytearray)) and row.get("p8_question_spec_created") is False)

def _row_forbidden_paths(*row_groups: Sequence[Mapping[str, Any]]) -> list[str]:
    paths: list[str] = []
    for group_index, rows in enumerate(row_groups):
        for row_index, row in enumerate(rows):
            paths.extend(_scan_forbidden_payload_key_paths(row, path=f"row_group[{group_index}][{row_index}]"))
    return _as_path_list(paths)

def _row_safe_ref_paths(*row_groups: Sequence[Mapping[str, Any]]) -> list[str]:
    paths: list[str] = []
    for group_index, rows in enumerate(row_groups):
        for row_index, row in enumerate(rows):
            paths.extend(_scan_safe_ref_shape_violation_paths(row, path=f"row_group[{group_index}][{row_index}]"))
    return _as_path_list(paths)

def _row_status_material(op08: Mapping[str, Any], *, op08_valid: bool, sanitized_rows: Sequence[Mapping[str, Any]], rating_rows: Sequence[Mapping[str, Any]], question_need_rows: Sequence[Mapping[str, Any]], review_session_id: str) -> tuple[str, bool, bool, str, str, list[str], list[str], list[str]]:
    if not op08_valid:
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF, False, True, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, ["alr_op09_op08_contract_invalid_fail_closed"], ["alr_op09_op08_contract_invalid"], ["op08_contract_invalid"])
    op08_status = _clean_ref(op08.get("actual_operation_receipt_guard_status_ref"), max_length=220)
    if op08_status == P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF:
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF, False, True, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, ["alr_op09_repair_stop_branch_has_no_rows_guard_path"], ["alr_op09_rows_not_applicable_repair_stop"], [])
    if op08_status == P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF:
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF, False, False, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF, P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF, ["alr_op09_downstream_manual_decision_branch_has_no_rows_guard_path"], ["alr_op09_rows_not_applicable_downstream_manual_decision"], [])
    if op08_status == P7_R54_AHR_POST_DMD08_ALR_OP08_STATUS_RECEIPT_REPAIR_REQUIRED_REF:
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF, False, True, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, ["alr_op09_op08_receipt_repair_required_fail_closed"], ["alr_op09_op08_receipt_repair_required"], ["op08_receipt_repair_required"])
    forbidden_paths = _row_forbidden_paths(sanitized_rows, rating_rows, question_need_rows)
    safe_ref_paths = _row_safe_ref_paths(sanitized_rows, rating_rows, question_need_rows)
    schema_violations: list[str] = []
    sanitized_valid = all(_sanitized_review_result_row_valid(row, review_session_id=review_session_id) for row in sanitized_rows)
    rating_valid = all(_rating_row_valid(row, review_session_id=review_session_id) for row in rating_rows)
    question_valid = all(_question_need_observation_row_valid(row, review_session_id=review_session_id) for row in question_need_rows)
    if sanitized_rows and not sanitized_valid:
        schema_violations.append("sanitized_review_result_row_schema_invalid")
    if rating_rows and not rating_valid:
        schema_violations.append("rating_row_schema_invalid")
    if question_need_rows and not question_valid:
        schema_violations.append("question_need_observation_row_schema_invalid")
    if forbidden_paths or safe_ref_paths:
        schema_violations.append("row_bodyfree_or_safe_ref_boundary_invalid")
    if schema_violations:
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF, False, True, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, ["alr_op09_rows_bodyfree_schema_repair_required"], ["alr_op09_rows_schema_or_boundary_invalid"], schema_violations)
    counts = (len(sanitized_rows), len(rating_rows), len(question_need_rows))
    if counts == (0, 0, 0):
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF, False, False, P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, ["alr_op09_selection_only_row_expected_schema_guard_ready_without_actual_rows"], ["alr_op09_actual_rows_missing"], [])
    if counts == (P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,) * 3:
        return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF, True, False, P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, ["alr_op09_selection_only_rows_complete_candidate_by_schema_and_counts"], ["alr_op09_rows_complete_candidate_still_requires_disposal_purge_guard_and_manual_decision"], [])
    return (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF, False, False, P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, ["alr_op09_selection_only_rows_present_but_incomplete"], ["alr_op09_selection_only_rows_counts_incomplete"], [])

def build_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard(*, alr_op08_actual_operation_receipt_expected_schema_completeness_guard: Mapping[str, Any] | None = None, sanitized_review_result_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None, rating_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None, question_need_observation_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None, review_session_id: Any = None) -> dict[str, Any]:
    """Build ALR-OP09 selection-only rows / rating / question need expected schema guard."""
    session_id = _safe_review_session_id(review_session_id)
    op08_input = alr_op08_actual_operation_receipt_expected_schema_completeness_guard
    if op08_input is None:
        op08_input = build_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard(review_session_id=session_id)
    op08_valid = _op08_contract_valid_for_alr_op09(op08_input)
    op08 = op08_input if isinstance(op08_input, Mapping) else {}
    sanitized_rows = _as_bodyfree_row_sequence(sanitized_review_result_rows_bodyfree)
    rating_rows = _as_bodyfree_row_sequence(rating_rows_bodyfree)
    question_need_rows = _as_bodyfree_row_sequence(question_need_observation_rows_bodyfree)
    status_ref, complete_candidate, repair_required, next_required_step, next_implementation_step, reason_refs, blocker_refs, schema_violations = _row_status_material(op08, op08_valid=op08_valid, sanitized_rows=sanitized_rows, rating_rows=rating_rows, question_need_rows=question_need_rows, review_session_id=session_id)
    forbidden_paths = _row_forbidden_paths(sanitized_rows, rating_rows, question_need_rows)
    safe_ref_paths = _row_safe_ref_paths(sanitized_rows, rating_rows, question_need_rows)
    row_count_complete = (len(sanitized_rows) == P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT and len(rating_rows) == P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT and len(question_need_rows) == P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT)
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP09_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op09_selection_only_rows_rating_question_need_schema_guard_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_schema_version": _clean_ref(op08.get("schema_version"), max_length=260),
        "op08_material_ref": _clean_ref(op08.get("material_id"), max_length=260),
        "op08_status_ref": _clean_ref(op08.get("actual_operation_receipt_guard_status_ref"), max_length=220),
        "op08_next_required_step": _clean_ref(op08.get("next_required_step"), max_length=260),
        "op08_next_implementation_step": _clean_ref(op08.get("next_implementation_step"), max_length=260),
        "op08_ready_for_op09": op08_valid and op08.get("alr_op08_ready_for_op09") is True,
        "row_schema_guard_status_ref": status_ref,
        "allowed_row_schema_guard_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP09_ALLOWED_STATUS_REFS),
        "allowed_row_schema_guard_status_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP09_ALLOWED_STATUS_REFS),
        "sanitized_review_result_row_schema_version": P7_R54_AHR_POST_DMD08_ALR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
        "rating_row_schema_version": P7_R54_AHR_POST_DMD08_ALR_RATING_ROW_SCHEMA_VERSION,
        "question_need_observation_row_schema_version": P7_R54_AHR_POST_DMD08_ALR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "sanitized_review_result_required_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP09_SANITIZED_REVIEW_RESULT_REQUIRED_FIELD_REFS),
        "sanitized_review_result_required_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP09_SANITIZED_REVIEW_RESULT_REQUIRED_FIELD_REFS),
        "rating_row_required_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP09_RATING_ROW_REQUIRED_FIELD_REFS),
        "rating_row_required_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP09_RATING_ROW_REQUIRED_FIELD_REFS),
        "question_need_observation_required_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP09_QUESTION_NEED_REQUIRED_FIELD_REFS),
        "question_need_observation_required_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP09_QUESTION_NEED_REQUIRED_FIELD_REFS),
        "allowed_verdict_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_VERDICT_REFS),
        "allowed_verdict_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_VERDICT_REFS),
        "rating_axis_refs": list(P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS),
        "rating_axis_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS),
        "allowed_rating_score_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_RATING_SCORE_REFS),
        "allowed_rating_score_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_RATING_SCORE_REFS),
        "allowed_question_need_primary_class_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "allowed_question_need_primary_class_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "allowed_ambiguity_kind_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_AMBIGUITY_KIND_REFS),
        "allowed_ambiguity_kind_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_AMBIGUITY_KIND_REFS),
        "allowed_one_question_fit_refs": list(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ONE_QUESTION_FIT_REFS),
        "allowed_one_question_fit_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ONE_QUESTION_FIT_REFS),
        "selection_only_rows_expected_case_count": P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "sanitized_review_result_row_count": len(sanitized_rows),
        "rating_row_count": len(rating_rows),
        "question_need_observation_row_count": len(question_need_rows),
        "sanitized_review_result_row_count_is_24": len(sanitized_rows) == P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count_is_24": len(rating_rows) == P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "question_need_observation_row_count_is_24": len(question_need_rows) == P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT,
        "row_count_complete": row_count_complete,
        "sanitized_review_result_rows_bodyfree_valid": bool(sanitized_rows) and all(_sanitized_review_result_row_valid(row, review_session_id=session_id) for row in sanitized_rows),
        "rating_rows_bodyfree_valid": bool(rating_rows) and all(_rating_row_valid(row, review_session_id=session_id) for row in rating_rows),
        "question_need_observation_rows_bodyfree_valid": bool(question_need_rows) and all(_question_need_observation_row_valid(row, review_session_id=session_id) for row in question_need_rows),
        "row_bodyfree_schema_guard_ready": status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF),
        "rows_complete_candidate": complete_candidate,
        "rows_missing_or_incomplete": status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF),
        "rows_repair_required": repair_required,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "returned_surface_body_included": False,
        "p8_question_spec_created": False,
        "p8_question_trigger_created": False,
        "row_forbidden_payload_key_paths": forbidden_paths,
        "row_forbidden_payload_key_path_count": len(forbidden_paths),
        "row_safe_ref_shape_violation_paths": safe_ref_paths,
        "row_safe_ref_shape_violation_path_count": len(safe_ref_paths),
        "row_schema_violation_refs": _unique_clean_refs(schema_violations),
        "row_schema_violation_ref_count": len(_unique_clean_refs(schema_violations)),
        "op09_reason_refs": _unique_clean_refs(reason_refs),
        "op09_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "op09_blocker_refs": _unique_clean_refs(blocker_refs),
        "op09_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op09_does_not_create_actual_rows": True,
        "alr_op09_does_not_create_question_text_or_p8_spec": True,
        "alr_op09_does_not_generate_body_full_packet": True,
        "alr_op09_does_not_run_actual_local_human_review": True,
        "alr_op09_does_not_create_disposal_or_purge_receipt": True,
        "alr_op09_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op09_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op09_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": next_implementation_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(data)
    return data

def assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(data: Mapping[str, Any]) -> bool:
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMD08_ALR_OP09_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP09_STEP_REF, source="P7-R54-AHR-PostDMD08-ALR-OP09")
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP09")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP09_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 field set changed")
    status_ref = str(data.get("row_schema_guard_status_ref"))
    if status_ref not in P7_R54_AHR_POST_DMD08_ALR_OP09_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 invalid row schema guard status")
    for field, count_field in (("sanitized_review_result_required_field_refs", "sanitized_review_result_required_field_ref_count"), ("rating_row_required_field_refs", "rating_row_required_field_ref_count"), ("question_need_observation_required_field_refs", "question_need_observation_required_field_ref_count"), ("allowed_verdict_refs", "allowed_verdict_ref_count"), ("rating_axis_refs", "rating_axis_ref_count"), ("allowed_rating_score_refs", "allowed_rating_score_ref_count"), ("allowed_question_need_primary_class_refs", "allowed_question_need_primary_class_ref_count"), ("allowed_ambiguity_kind_refs", "allowed_ambiguity_kind_ref_count"), ("allowed_one_question_fit_refs", "allowed_one_question_fit_ref_count"), ("row_forbidden_payload_key_paths", "row_forbidden_payload_key_path_count"), ("row_safe_ref_shape_violation_paths", "row_safe_ref_shape_violation_path_count"), ("row_schema_violation_refs", "row_schema_violation_ref_count"), ("op09_reason_refs", "op09_reason_ref_count"), ("op09_blocker_refs", "op09_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP09 {count_field} changed")
    if tuple(data.get("allowed_verdict_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_ALLOWED_VERDICT_REFS or tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_RATING_AXIS_REFS or tuple(data.get("allowed_question_need_primary_class_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_ALLOWED_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 allowed enum refs changed")
    if data.get("selection_only_rows_expected_case_count") != P7_R54_AHR_POST_DMD08_ALR_EXPECTED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 expected case count changed")
    for key in P7_R54_AHR_POST_DMD08_ALR_OP09_FORBIDDEN_ROW_TEXT_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP09 forbidden text marker opened: {key}")
    for key in ("p8_question_spec_created", "p8_question_trigger_created"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP09 P8 marker opened: {key}")
    complete = status_ref == P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF
    if complete:
        if data.get("rows_complete_candidate") is not True or data.get("row_count_complete") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 complete candidate flags changed")
        for key in ("sanitized_review_result_rows_bodyfree_valid", "rating_rows_bodyfree_valid", "question_need_observation_rows_bodyfree_valid"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP09 complete candidate valid flag changed: {key}")
    elif data.get("rows_complete_candidate") is not False:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 non-complete path promoted rows complete")
    if status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_INCOMPLETE_REF, P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_COMPLETE_CANDIDATE_REF):
        if data.get("row_bodyfree_schema_guard_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 row schema guard or next step changed")
    for key in ("alr_op09_does_not_create_actual_rows", "alr_op09_does_not_create_question_text_or_p8_spec", "alr_op09_does_not_generate_body_full_packet", "alr_op09_does_not_run_actual_local_human_review", "alr_op09_does_not_create_disposal_or_purge_receipt", "alr_op09_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op09_does_not_start_p5_p6_p8_p7_or_release", "alr_op09_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP09 required true boundary changed: {key}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP09_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP09_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 step list changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP09 not-claimed boundary must stay false")
    return True

build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op08_actual_operation_receipt_expected_schema_completeness_guard = build_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract = assert_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard_contract
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard = build_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract = assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract

# ALR-OP10/OP11 extension: disposal/purge expected schema guard and downstream non-promotion finalizer.
P7_R54_AHR_POST_DMD08_ALR_OP10_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op10_disposal_purge_receipt_expected_schema_guard.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP11_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op11_downstream_non_promotion_manual_decision_hold_finalizer.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.alr.disposal_purge_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:11]
P7_R54_AHR_POST_DMD08_ALR_OP10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[11:]
P7_R54_AHR_POST_DMD08_ALR_OP11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[:12]
P7_R54_AHR_POST_DMD08_ALR_OP11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS[12:]

P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF: Final = (
    "ALR_DISPOSAL_PURGE_RECEIPT_EXPECTED_SCHEMA_READY_RECEIPT_MISSING"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF: Final = (
    "ALR_DISPOSAL_PURGE_RECEIPT_EXPECTED_SCHEMA_READY_RECEIPT_INCOMPLETE"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF: Final = (
    "ALR_DISPOSAL_PURGE_RECEIPT_EXPECTED_SCHEMA_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF: Final = (
    "ALR_DISPOSAL_PURGE_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF: Final = (
    "ALR_DISPOSAL_PURGE_RECEIPT_EXPECTED_SCHEMA_NOT_APPLICABLE_REPAIR_STOP"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF: Final = (
    "ALR_DISPOSAL_PURGE_RECEIPT_EXPECTED_SCHEMA_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION"
)
P7_R54_AHR_POST_DMD08_ALR_OP10_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "disposal_purge_receipt_ref",
    "review_session_id",
    "body_full_packet_retained",
    "raw_input_retained",
    "comment_text_body_retained",
    "reviewer_note_body_retained",
    "question_text_retained",
    "draft_question_text_retained",
    "answer_text_retained",
    "local_path_included",
    "hash_included",
    "terminal_output_body_included",
    "disposal_purge_receipt_accepted",
    "body_free",
)
P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_retained",
    "raw_input_retained",
    "comment_text_body_retained",
    "reviewer_note_body_retained",
    "question_text_retained",
    "draft_question_text_retained",
    "answer_text_retained",
    "local_path_included",
    "hash_included",
    "terminal_output_body_included",
)

P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_INVALID_OP10_REPAIR_REQUIRED_REF: Final = (
    "ALR_DOWNSTREAM_NON_PROMOTION_HOLD_INVALID_OP10_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_REPAIR_STOP_REQUIRED_REF: Final = (
    "ALR_DOWNSTREAM_NON_PROMOTION_HOLD_REPAIR_STOP_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED_REF: Final = (
    "ALR_DOWNSTREAM_NON_PROMOTION_HOLD_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_COMPLETE_RECEIPT_MANUAL_DECISION_REQUIRED_REF: Final = (
    "ALR_DOWNSTREAM_NON_PROMOTION_HOLD_COMPLETE_RECEIPT_MANUAL_DECISION_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_INVALID_OP10_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_REPAIR_STOP_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_COMPLETE_RECEIPT_MANUAL_DECISION_REQUIRED_REF,
)

P7_R54_AHR_POST_DMD08_ALR_OP10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_schema_version", "op09_material_ref", "op09_status_ref", "op09_next_required_step",
    "op09_next_implementation_step", "op09_ready_for_op10", "op09_rows_complete_candidate",
    "op09_rows_missing_or_incomplete", "op09_rows_repair_required", "op09_row_bodyfree_schema_guard_ready",
    "disposal_purge_receipt_expected_schema_version_ref", "disposal_purge_receipt_required_field_refs",
    "disposal_purge_receipt_required_field_ref_count", "disposal_purge_receipt_required_false_flag_refs",
    "disposal_purge_receipt_required_false_flag_ref_count", "disposal_purge_receipt_guard_status_ref",
    "allowed_disposal_purge_receipt_guard_status_refs", "allowed_disposal_purge_receipt_guard_status_ref_count",
    "disposal_purge_receipt_present", "disposal_purge_receipt_schema_version_ref",
    "disposal_purge_receipt_schema_version_valid", "disposal_purge_receipt_ref",
    "disposal_purge_receipt_ref_consistent", "disposal_purge_receipt_review_session_id_consistent",
    "body_full_packet_retained", "raw_input_retained", "comment_text_body_retained",
    "reviewer_note_body_retained", "question_text_retained", "draft_question_text_retained",
    "answer_text_retained", "local_path_included", "hash_included", "terminal_output_body_included",
    "disposal_purge_receipt_accepted", "disposal_purge_retention_false_pass_refs",
    "disposal_purge_retention_false_complete", "disposal_purge_receipt_body_free", "body_free_receipt_guard_passed",
    "disposal_purge_receipt_complete_candidate", "evidence_complete_candidate_after_disposal_guard",
    "disposal_purge_receipt_missing_or_incomplete", "bodyfree_disposal_boundary_repair_required",
    "disposal_purge_receipt_expected_schema_guard_ready", "disposal_purge_receipt_forbidden_payload_key_paths",
    "disposal_purge_receipt_forbidden_payload_key_path_count", "disposal_purge_receipt_safe_ref_shape_violation_paths",
    "disposal_purge_receipt_safe_ref_shape_violation_path_count", "op10_reason_refs", "op10_reason_ref_count",
    "op10_blocker_refs", "op10_blocker_ref_count", "alr_op10_does_not_create_disposal_or_purge_receipt",
    "alr_op10_does_not_execute_disposal_or_purge", "alr_op10_does_not_generate_body_full_packet",
    "alr_op10_does_not_run_actual_local_human_review", "alr_op10_does_not_create_actual_rows",
    "alr_op10_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op10_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op10_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "next_implementation_step", "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DMD08_ALR_OP11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_schema_version", "op10_material_ref", "op10_status_ref", "op10_next_required_step",
    "op10_next_implementation_step", "op10_ready_for_op11", "op10_disposal_purge_receipt_accepted",
    "op10_disposal_purge_receipt_complete_candidate", "op10_evidence_complete_candidate_after_disposal_guard",
    "op10_bodyfree_disposal_boundary_repair_required", "downstream_non_promotion_status_ref",
    "allowed_downstream_non_promotion_status_refs", "allowed_downstream_non_promotion_status_ref_count",
    "selected_action_ref", "continue_allowed", "retry_or_start_required", "repair_stop_required",
    "complete_receipt_manual_decision_required", "exactly_one_final_action_flag_true",
    "manual_decision_hold_finalized", "downstream_non_promotion_finalizer_closed_bodyfree",
    "downstream_manual_decision_required", "actual_local_review_operation_must_continue_or_retry",
    "complete_receipt_branch_requires_manual_decision", "p5_p6_p8_r52_p7_release_auto_promotion_blocked",
    "manual_decision_auto_executes_downstream", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed",
    "r52_actual_execution_started_here", "p7_complete", "release_allowed", "op11_reason_refs", "op11_reason_ref_count",
    "op11_blocker_refs", "op11_blocker_ref_count", "alr_op11_does_not_generate_body_full_packet",
    "alr_op11_does_not_run_actual_local_human_review", "alr_op11_does_not_create_actual_rows",
    "alr_op11_does_not_execute_disposal_or_purge", "alr_op11_does_not_execute_downstream_automatically",
    "alr_op11_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op11_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op11_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "next_implementation_step", "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op09_contract_valid_for_alr_op10(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard_contract(material) is True
    except ValueError:
        return False


def _op10_contract_valid_for_alr_op11(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(material) is True
    except ValueError:
        return False


def _receipt_text_flag_value(receipt: Mapping[str, Any] | None, key: str) -> bool:
    return bool(isinstance(receipt, Mapping) and receipt.get(key) is True)


def _disposal_purge_retention_false_pass_refs(receipt: Mapping[str, Any] | None) -> dict[str, bool]:
    return {
        field: (receipt.get(field) is False if isinstance(receipt, Mapping) else False)
        for field in P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS
    }


def _disposal_purge_receipt_schema_version(receipt: Mapping[str, Any] | None) -> str:
    if not isinstance(receipt, Mapping):
        return "disposal_purge_receipt_missing"
    return _clean_ref(receipt.get("schema_version"), default="disposal_purge_receipt_schema_missing", max_length=220)


def _disposal_purge_receipt_ref(receipt: Mapping[str, Any] | None) -> str:
    if not isinstance(receipt, Mapping):
        return ""
    return _clean_ref(receipt.get("disposal_purge_receipt_ref"), default="", max_length=220)


def _op10_disposal_purge_status_material(
    op09: Mapping[str, Any],
    *,
    op09_valid: bool,
    receipt: Mapping[str, Any] | None,
    review_session_id: str,
) -> tuple[str, bool, bool, bool, str, str, list[str], list[str]]:
    if not op09_valid:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF,
            False,
            False,
            True,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op10_op09_contract_invalid_fail_closed"],
            ["alr_op10_op09_contract_invalid"],
        )
    op09_status_ref = _clean_ref(op09.get("row_schema_guard_status_ref"), max_length=220)
    if op09_status_ref in (
        P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
        P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_ROWS_REPAIR_REQUIRED_REF,
    ):
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
            False,
            False,
            True,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op10_repair_stop_branch_has_no_disposal_guard_path"],
            ["alr_op10_rows_guard_repair_stop"],
        )
    if op09_status_ref == P7_R54_AHR_POST_DMD08_ALR_OP09_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF,
            False,
            False,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            ["alr_op10_downstream_manual_decision_branch_has_no_disposal_guard_path"],
            ["alr_op10_disposal_guard_not_applicable_downstream_manual_decision"],
        )
    if not isinstance(receipt, Mapping):
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF,
            False,
            False,
            False,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            ["alr_op10_disposal_purge_expected_schema_guard_ready_without_receipt"],
            ["alr_op10_disposal_purge_receipt_missing"],
        )
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="disposal_purge_receipt_bodyfree")
    safe_ref_paths = _scan_safe_ref_shape_violation_paths(receipt, path="disposal_purge_receipt_bodyfree")
    retention_pass_refs = _disposal_purge_retention_false_pass_refs(receipt)
    any_retained_body_flag = any(receipt.get(field) is True for field in P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS)
    if forbidden_paths or safe_ref_paths or any_retained_body_flag:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF,
            False,
            False,
            True,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op10_disposal_purge_bodyfree_boundary_repair_required"],
            ["alr_op10_disposal_purge_receipt_body_or_path_boundary_invalid"],
        )
    schema_valid = _disposal_purge_receipt_schema_version(receipt) == P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION
    ref_valid = _disposal_purge_receipt_ref(receipt) != ""
    session_valid = _material_review_session_id(receipt) == review_session_id
    retention_complete = all(retention_pass_refs.values())
    accepted = receipt.get("disposal_purge_receipt_accepted") is True
    bodyfree = receipt.get("body_free") is True
    if schema_valid and ref_valid and session_valid and retention_complete and accepted and bodyfree:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF,
            True,
            bool(op09.get("rows_complete_candidate") is True),
            False,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
            ["alr_op10_disposal_purge_receipt_accepted_bodyfree"],
            ["alr_op10_complete_candidate_still_requires_downstream_non_promotion_finalizer"],
        )
    return (
        P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF,
        False,
        False,
        False,
        P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        ["alr_op10_disposal_purge_receipt_present_but_incomplete"],
        ["alr_op10_disposal_purge_required_schema_or_flags_incomplete"],
    )


def build_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard(
    *,
    alr_op09_selection_only_rows_rating_question_need_expected_schema_guard: Mapping[str, Any] | None = None,
    disposal_purge_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP10 disposal / purge receipt expected schema guard without executing purge."""
    session_id = _safe_review_session_id(review_session_id)
    op09_input = alr_op09_selection_only_rows_rating_question_need_expected_schema_guard
    if op09_input is None:
        op09_input = build_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard(review_session_id=session_id)
    op09_valid = _op09_contract_valid_for_alr_op10(op09_input)
    op09 = op09_input if isinstance(op09_input, Mapping) else {}
    receipt = disposal_purge_receipt_bodyfree if isinstance(disposal_purge_receipt_bodyfree, Mapping) else None
    status_ref, receipt_complete_candidate, evidence_complete_candidate, repair_required, next_required_step, next_implementation_step, reason_refs, blocker_refs = _op10_disposal_purge_status_material(
        op09,
        op09_valid=op09_valid,
        receipt=receipt,
        review_session_id=session_id,
    )
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="disposal_purge_receipt_bodyfree") if isinstance(receipt, Mapping) else []
    safe_ref_paths = _scan_safe_ref_shape_violation_paths(receipt, path="disposal_purge_receipt_bodyfree") if isinstance(receipt, Mapping) else []
    retention_pass_refs = _disposal_purge_retention_false_pass_refs(receipt)
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP10_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op09_schema_version": _clean_ref(op09.get("schema_version"), max_length=260),
        "op09_material_ref": _clean_ref(op09.get("material_id"), max_length=260),
        "op09_status_ref": _clean_ref(op09.get("row_schema_guard_status_ref"), max_length=220),
        "op09_next_required_step": _clean_ref(op09.get("next_required_step"), max_length=260),
        "op09_next_implementation_step": _clean_ref(op09.get("next_implementation_step"), max_length=260),
        "op09_ready_for_op10": op09_valid and op09.get("next_implementation_step") == P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF,
        "op09_rows_complete_candidate": op09.get("rows_complete_candidate") is True,
        "op09_rows_missing_or_incomplete": op09.get("rows_missing_or_incomplete") is True,
        "op09_rows_repair_required": op09.get("rows_repair_required") is True,
        "op09_row_bodyfree_schema_guard_ready": op09.get("row_bodyfree_schema_guard_ready") is True,
        "disposal_purge_receipt_expected_schema_version_ref": P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION,
        "disposal_purge_receipt_required_field_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FIELD_REFS),
        "disposal_purge_receipt_required_field_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FIELD_REFS),
        "disposal_purge_receipt_required_false_flag_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS),
        "disposal_purge_receipt_required_false_flag_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS),
        "disposal_purge_receipt_guard_status_ref": status_ref,
        "allowed_disposal_purge_receipt_guard_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP10_ALLOWED_STATUS_REFS),
        "allowed_disposal_purge_receipt_guard_status_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP10_ALLOWED_STATUS_REFS),
        "disposal_purge_receipt_present": isinstance(receipt, Mapping),
        "disposal_purge_receipt_schema_version_ref": _disposal_purge_receipt_schema_version(receipt),
        "disposal_purge_receipt_schema_version_valid": _disposal_purge_receipt_schema_version(receipt) == P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION,
        "disposal_purge_receipt_ref": _disposal_purge_receipt_ref(receipt),
        "disposal_purge_receipt_ref_consistent": _disposal_purge_receipt_ref(receipt) != "",
        "disposal_purge_receipt_review_session_id_consistent": _material_review_session_id(receipt) == session_id if isinstance(receipt, Mapping) else False,
        # The output material is always body-free.  Retention or path/hash markers
        # observed in an input receipt are represented only through status/blocker refs
        # and per-field pass refs below; they are never carried forward as true flags.
        "body_full_packet_retained": False,
        "raw_input_retained": False,
        "comment_text_body_retained": False,
        "reviewer_note_body_retained": False,
        "question_text_retained": False,
        "draft_question_text_retained": False,
        "answer_text_retained": False,
        "local_path_included": False,
        "hash_included": False,
        "terminal_output_body_included": False,
        "disposal_purge_receipt_accepted": bool(isinstance(receipt, Mapping) and receipt.get("disposal_purge_receipt_accepted") is True),
        "disposal_purge_retention_false_pass_refs": retention_pass_refs,
        "disposal_purge_retention_false_complete": all(retention_pass_refs.values()),
        "disposal_purge_receipt_body_free": bool(isinstance(receipt, Mapping) and receipt.get("body_free") is True),
        "body_free_receipt_guard_passed": bool(isinstance(receipt, Mapping) and receipt.get("body_free") is True),
        "disposal_purge_receipt_complete_candidate": receipt_complete_candidate,
        "evidence_complete_candidate_after_disposal_guard": evidence_complete_candidate,
        "disposal_purge_receipt_missing_or_incomplete": status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF),
        "bodyfree_disposal_boundary_repair_required": repair_required,
        "disposal_purge_receipt_expected_schema_guard_ready": status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF),
        "disposal_purge_receipt_forbidden_payload_key_paths": forbidden_paths,
        "disposal_purge_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "disposal_purge_receipt_safe_ref_shape_violation_paths": safe_ref_paths,
        "disposal_purge_receipt_safe_ref_shape_violation_path_count": len(safe_ref_paths),
        "op10_reason_refs": _unique_clean_refs(reason_refs),
        "op10_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "op10_blocker_refs": _unique_clean_refs(blocker_refs),
        "op10_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op10_does_not_create_disposal_or_purge_receipt": True,
        "alr_op10_does_not_execute_disposal_or_purge": True,
        "alr_op10_does_not_generate_body_full_packet": True,
        "alr_op10_does_not_run_actual_local_human_review": True,
        "alr_op10_does_not_create_actual_rows": True,
        "alr_op10_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op10_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op10_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP10_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": next_implementation_step,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract(data: Mapping[str, Any]) -> bool:
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMD08_ALR_OP10_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP10_STEP_REF, source="P7-R54-AHR-PostDMD08-ALR-OP10")
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP10")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP10_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 field set changed")
    status_ref = str(data.get("disposal_purge_receipt_guard_status_ref"))
    if status_ref not in P7_R54_AHR_POST_DMD08_ALR_OP10_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 invalid disposal/purge guard status")
    for field, count_field in (("disposal_purge_receipt_required_field_refs", "disposal_purge_receipt_required_field_ref_count"), ("disposal_purge_receipt_required_false_flag_refs", "disposal_purge_receipt_required_false_flag_ref_count"), ("allowed_disposal_purge_receipt_guard_status_refs", "allowed_disposal_purge_receipt_guard_status_ref_count"), ("disposal_purge_receipt_forbidden_payload_key_paths", "disposal_purge_receipt_forbidden_payload_key_path_count"), ("disposal_purge_receipt_safe_ref_shape_violation_paths", "disposal_purge_receipt_safe_ref_shape_violation_path_count"), ("op10_reason_refs", "op10_reason_ref_count"), ("op10_blocker_refs", "op10_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP10 {count_field} changed")
    if tuple(data.get("disposal_purge_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 expected receipt field refs changed")
    if tuple(data.get("disposal_purge_receipt_required_false_flag_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 retention false flag refs changed")
    if data.get("disposal_purge_receipt_expected_schema_version_ref") != P7_R54_AHR_POST_DMD08_ALR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 disposal/purge schema version changed")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF:
        for flag in P7_R54_AHR_POST_DMD08_ALR_OP10_RECEIPT_REQUIRED_FALSE_FLAG_REFS:
            if data.get(flag) is not False:
                raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP10 retained/body marker opened: {flag}")
        if data.get("disposal_purge_receipt_complete_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 accepted receipt did not materialize candidate")
        if data.get("disposal_purge_receipt_accepted") is not True or data.get("disposal_purge_retention_false_complete") is not True or data.get("body_free_receipt_guard_passed") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 accepted receipt guard changed")
    else:
        if data.get("disposal_purge_receipt_complete_candidate") is not False:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 non-accepted path promoted disposal/purge receipt complete")
    if data.get("evidence_complete_candidate_after_disposal_guard") is True:
        if status_ref != P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF or data.get("op09_rows_complete_candidate") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 evidence complete candidate opened without rows and purge")
    if status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF):
        if data.get("bodyfree_disposal_boundary_repair_required") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 repair path changed")
    if status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_MISSING_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_INCOMPLETE_REF, P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_ACCEPTED_REF):
        if data.get("disposal_purge_receipt_expected_schema_guard_ready") is not True or data.get("next_implementation_step") != P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 schema guard or next OP11 step changed")
    for key in ("alr_op10_does_not_create_disposal_or_purge_receipt", "alr_op10_does_not_execute_disposal_or_purge", "alr_op10_does_not_generate_body_full_packet", "alr_op10_does_not_run_actual_local_human_review", "alr_op10_does_not_create_actual_rows", "alr_op10_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op10_does_not_start_p5_p6_p8_p7_or_release", "alr_op10_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP10 required true boundary changed: {key}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP10_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP10_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 step list changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP10 not-claimed boundary must stay false")
    return True


def _op11_finalizer_status_material(op10: Mapping[str, Any], *, op10_valid: bool) -> tuple[str, str, bool, bool, bool, bool, str, list[str], list[str]]:
    if not op10_valid:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_INVALID_OP10_REPAIR_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
            False,
            False,
            True,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op11_op10_contract_invalid_fail_closed"],
            ["alr_op11_op10_contract_invalid"],
        )
    op10_status_ref = _clean_ref(op10.get("disposal_purge_receipt_guard_status_ref"), max_length=220)
    if op10_status_ref in (
        P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_RECEIPT_REPAIR_REQUIRED_REF,
        P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_REPAIR_STOP_REF,
    ) or op10.get("bodyfree_disposal_boundary_repair_required") is True:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_REPAIR_STOP_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF,
            False,
            False,
            True,
            False,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            ["alr_op11_repair_stop_preserved_from_op10"],
            ["alr_op11_bodyfree_disposal_or_rows_repair_required"],
        )
    if op10_status_ref == P7_R54_AHR_POST_DMD08_ALR_OP10_STATUS_NOT_APPLICABLE_DOWNSTREAM_MANUAL_DECISION_REF or op10.get("evidence_complete_candidate_after_disposal_guard") is True:
        return (
            P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_COMPLETE_RECEIPT_MANUAL_DECISION_REQUIRED_REF,
            P7_R54_AHR_POST_DMD08_ALR_ACTION_COMPLETE_RECEIPT_DOWNSTREAM_MANUAL_DECISION_REQUIRED_REF,
            False,
            False,
            False,
            True,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
            ["alr_op11_complete_evidence_candidate_held_for_downstream_manual_decision"],
            ["alr_op11_downstream_auto_execution_blocked"],
        )
    return (
        P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED_REF,
        P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF,
        False,
        True,
        False,
        False,
        P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF,
        ["alr_op11_evidence_incomplete_return_to_actual_local_only_review_operation"],
        ["alr_op11_receipt_rows_or_disposal_purge_not_complete_from_real_operation"],
    )


def build_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer(
    *,
    alr_op10_disposal_purge_receipt_expected_schema_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP11 downstream non-promotion / manual decision hold finalizer."""
    session_id = _safe_review_session_id(review_session_id)
    op10_input = alr_op10_disposal_purge_receipt_expected_schema_guard
    if op10_input is None:
        op10_input = build_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard(review_session_id=session_id)
    op10_valid = _op10_contract_valid_for_alr_op11(op10_input)
    op10 = op10_input if isinstance(op10_input, Mapping) else {}
    status_ref, selected_action_ref, continue_allowed, retry_or_start_required, repair_stop_required, complete_receipt_manual_decision_required, next_required_step, reason_refs, blocker_refs = _op11_finalizer_status_material(op10, op10_valid=op10_valid)
    downstream_manual_decision_required = complete_receipt_manual_decision_required is True
    actual_review_continue_retry_required = retry_or_start_required is True or continue_allowed is True
    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP11_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": "r54_ahr_postdmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_bodyfree_20260703",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op10_schema_version": _clean_ref(op10.get("schema_version"), max_length=260),
        "op10_material_ref": _clean_ref(op10.get("material_id"), max_length=260),
        "op10_status_ref": _clean_ref(op10.get("disposal_purge_receipt_guard_status_ref"), max_length=220),
        "op10_next_required_step": _clean_ref(op10.get("next_required_step"), max_length=260),
        "op10_next_implementation_step": _clean_ref(op10.get("next_implementation_step"), max_length=260),
        "op10_ready_for_op11": op10_valid and op10.get("next_implementation_step") == P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF,
        "op10_disposal_purge_receipt_accepted": op10.get("disposal_purge_receipt_accepted") is True,
        "op10_disposal_purge_receipt_complete_candidate": op10.get("disposal_purge_receipt_complete_candidate") is True,
        "op10_evidence_complete_candidate_after_disposal_guard": op10.get("evidence_complete_candidate_after_disposal_guard") is True,
        "op10_bodyfree_disposal_boundary_repair_required": op10.get("bodyfree_disposal_boundary_repair_required") is True,
        "downstream_non_promotion_status_ref": status_ref,
        "allowed_downstream_non_promotion_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP11_ALLOWED_STATUS_REFS),
        "allowed_downstream_non_promotion_status_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP11_ALLOWED_STATUS_REFS),
        "selected_action_ref": selected_action_ref,
        "continue_allowed": continue_allowed,
        "retry_or_start_required": retry_or_start_required,
        "repair_stop_required": repair_stop_required,
        "complete_receipt_manual_decision_required": complete_receipt_manual_decision_required,
        "exactly_one_final_action_flag_true": sum(1 for value in (continue_allowed, retry_or_start_required, repair_stop_required, complete_receipt_manual_decision_required) if value is True) == 1,
        "manual_decision_hold_finalized": True,
        "downstream_non_promotion_finalizer_closed_bodyfree": True,
        "downstream_manual_decision_required": downstream_manual_decision_required,
        "actual_local_review_operation_must_continue_or_retry": actual_review_continue_retry_required,
        "complete_receipt_branch_requires_manual_decision": complete_receipt_manual_decision_required,
        "p5_p6_p8_r52_p7_release_auto_promotion_blocked": True,
        "manual_decision_auto_executes_downstream": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_actual_execution_started_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "op11_reason_refs": _unique_clean_refs(reason_refs),
        "op11_reason_ref_count": len(_unique_clean_refs(reason_refs)),
        "op11_blocker_refs": _unique_clean_refs(blocker_refs),
        "op11_blocker_ref_count": len(_unique_clean_refs(blocker_refs)),
        "alr_op11_does_not_generate_body_full_packet": True,
        "alr_op11_does_not_run_actual_local_human_review": True,
        "alr_op11_does_not_create_actual_rows": True,
        "alr_op11_does_not_execute_disposal_or_purge": True,
        "alr_op11_does_not_execute_downstream_automatically": True,
        "alr_op11_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op11_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op11_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "next_implementation_step": P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "manual_decision_auto_executes_downstream": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_actual_execution_started_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(data: Mapping[str, Any]) -> bool:
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DMD08_ALR_OP11_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP11_STEP_REF, source="P7-R54-AHR-PostDMD08-ALR-OP11")
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP11")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP11_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 field set changed")
    status_ref = str(data.get("downstream_non_promotion_status_ref"))
    if status_ref not in P7_R54_AHR_POST_DMD08_ALR_OP11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 invalid downstream hold status")
    selected_action_ref = str(data.get("selected_action_ref"))
    if selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 invalid selected action")
    if data.get("exactly_one_final_action_flag_true") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 final action flags are not exactly one")
    for field, count_field in (("allowed_downstream_non_promotion_status_refs", "allowed_downstream_non_promotion_status_ref_count"), ("op11_reason_refs", "op11_reason_ref_count"), ("op11_blocker_refs", "op11_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP11 {count_field} changed")
    if tuple(data.get("allowed_downstream_non_promotion_status_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 status refs changed")
    if data.get("manual_decision_hold_finalized") is not True or data.get("downstream_non_promotion_finalizer_closed_bodyfree") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 finalizer did not close body-free hold")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_COMPLETE_RECEIPT_MANUAL_DECISION_REQUIRED_REF:
        if data.get("complete_receipt_manual_decision_required") is not True or data.get("downstream_manual_decision_required") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 complete branch did not require manual decision")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 complete branch next step changed")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_ACTUAL_REVIEW_CONTINUE_OR_RETRY_REQUIRED_REF:
        if data.get("retry_or_start_required") is not True or data.get("actual_local_review_operation_must_continue_or_retry") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 incomplete branch did not return to actual review operation")
        if data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 retry/start next step changed")
    if status_ref in (P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_INVALID_OP10_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_DMD08_ALR_OP11_STATUS_REPAIR_STOP_REQUIRED_REF):
        if data.get("repair_stop_required") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 repair path changed")
    for key in ("manual_decision_auto_executes_downstream", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_actual_execution_started_here", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP11 downstream promotion flag opened: {key}")
    for key in ("alr_op11_does_not_generate_body_full_packet", "alr_op11_does_not_run_actual_local_human_review", "alr_op11_does_not_create_actual_rows", "alr_op11_does_not_execute_disposal_or_purge", "alr_op11_does_not_execute_downstream_automatically", "alr_op11_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op11_does_not_start_p5_p6_p8_p7_or_release", "alr_op11_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP11 required true boundary changed: {key}")
    if data.get("next_implementation_step") != P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 next implementation step changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP11_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 step list changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP11 not-claimed boundary must stay false")
    return True


build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op10_disposal_purge_receipt_expected_schema_guard = build_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op10_disposal_purge_receipt_expected_schema_guard_contract = assert_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard_contract
build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer = build_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract = assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract


# ALR-OP12 extension: body-free result memo / target tests / selected regression closure.
P7_R54_AHR_POST_DMD08_ALR_OP12_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dmd08.actual_local_review."
    "alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure.bodyfree.v1"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DMD08_ALR_STEP_REFS
P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF: Final = (
    "ALR_OP12_BODYFREE_RESULT_MEMO_TARGET_TESTS_SELECTED_REGRESSION_CLOSED"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF: Final = (
    "ALR_OP12_RESULT_MEMO_TARGET_TESTS_SELECTED_REGRESSION_INCOMPLETE_OR_UNVERIFIED"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_REPAIR_REQUIRED_REF: Final = (
    "ALR_OP12_BODYFREE_RESULT_MEMO_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF,
    P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF: Final = "passed_bodyfree_count_only"
P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REFS: Final[frozenset[str]] = frozenset(
    {"passed", P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REF}
)
P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP12_Result_20260703.md"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_NEXT_IMPLEMENTATION_STEP_REF: Final = (
    "ALR_OP12_CLOSED_NO_FURTHER_ALR_HELPER_IMPLEMENTATION_STEP"
)
P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_SECTION_REFS: Final[tuple[str, ...]] = (
    "implementation_scope",
    "changed_files",
    "target_tests",
    "selected_regression",
    "compileall",
    "dmd_op08_branch_intake_status",
    "selected_alr_action_status",
    "downstream_non_promotion_hold_status",
    "next_required_step",
    "not_claimed_boundary",
    "not_executed_boundary",
    "unverified_boundary",
)
P7_R54_AHR_POST_DMD08_ALR_OP12_CHANGED_FILE_REFS: Final[dict[str, tuple[str, ...]]] = {
    "modified": (
        "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703.py",
    ),
    "new": (
        "mashos-api/ai/tests/test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op12_result_20260703.py",
        "mashos-api/ai/tests/R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP12_Result_20260703.md",
    ),
    "deleted": (),
}
P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS: Final[tuple[str, ...]] = (
    "alr_op00_op01_target",
    "alr_op02_op03_target",
    "alr_op04_op05_target",
    "alr_op06_op07_target",
    "alr_op08_op09_target",
    "alr_op10_op11_target",
    "alr_op12_target",
)
P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS: Final[tuple[str, ...]] = (
    "dmd_op00_op08_selected_regression",
    "dmh_pmn_mn_selected_regression",
)
P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_EXECUTED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_local_human_review_execution",
    "actual_operation_receipt_creation",
    "actual_rows_creation",
    "actual_sanitized_review_result_rows_from_real_operation",
    "actual_rating_rows_from_real_operation",
    "actual_question_need_observation_rows_from_real_operation",
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
P7_R54_AHR_POST_DMD08_ALR_OP12_UNVERIFIED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_DMD08_ALR_OP12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_schema_version", "op11_material_ref", "op11_status_ref", "op11_next_required_step",
    "op11_next_implementation_step", "op11_contract_valid", "op11_selected_action_ref",
    "op11_retry_or_start_required", "op11_repair_stop_required", "op11_complete_receipt_manual_decision_required",
    "op11_manual_decision_hold_finalized", "op11_downstream_non_promotion_finalizer_closed_bodyfree",
    "alr_op12_status_ref", "alr_op12_allowed_status_refs", "alr_op12_allowed_status_ref_count", "alr_op12_ready",
    "result_memo_ref", "result_memo_bodyfree_closed", "result_memo_sections_fixed", "result_memo_section_refs",
    "result_memo_section_ref_count", "implementation_scope", "changed_files", "target_tests", "selected_regression",
    "compileall", "dmd_op08_branch_intake_status", "selected_alr_action_status",
    "downstream_non_promotion_hold_status", "next_required_step", "not_executed_boundary_refs",
    "not_executed_boundary_ref_count", "not_executed_boundary", "unverified_boundary_refs", "unverified_boundary_ref_count",
    "unverified_boundary", "target_test_group_refs", "target_test_group_ref_count", "target_test_result_status_refs",
    "target_test_result_status_ref_count", "target_test_result_count_refs", "target_test_result_count_ref_count",
    "target_tests_summary_bodyfree_recorded", "target_tests_closed_by_external_status_summary", "target_tests_closed",
    "selected_regression_group_refs", "selected_regression_group_ref_count", "selected_regression_result_status_refs",
    "selected_regression_result_status_ref_count", "selected_regression_result_count_refs",
    "selected_regression_result_count_ref_count", "selected_regression_summary_bodyfree_recorded",
    "selected_regression_closed_by_external_status_summary", "selected_regression_closed", "compileall_result_status_ref",
    "compileall_result_count_ref", "compileall_summary_bodyfree_recorded", "compileall_closed_by_external_status_summary",
    "compileall_closed", "selected_action_ref", "continue_allowed", "retry_or_start_required", "repair_stop_required",
    "complete_receipt_manual_decision_required", "exactly_one_final_action_flag_true", "manual_decision_hold_finalized",
    "downstream_manual_decision_required", "actual_local_review_operation_must_continue_or_retry",
    "complete_receipt_branch_requires_manual_decision", "p5_p6_p8_r52_p7_release_auto_promotion_blocked",
    "branch_reason_refs", "branch_reason_ref_count", "branch_blocker_refs", "branch_blocker_ref_count",
    "alr_op12_helper_does_not_run_pytest_or_compileall", "alr_op12_does_not_generate_body_full_packet",
    "alr_op12_does_not_run_actual_local_human_review", "alr_op12_does_not_create_receipts_rows_or_disposal",
    "alr_op12_does_not_execute_postcr22_ex_reentry_or_r52", "alr_op12_does_not_start_p5_p6_p8_p7_or_release",
    "alr_op12_does_not_change_api_db_rn_runtime_response_key", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_implementation_step",
    "public_contract", "post_dmd08_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op12_contract_valid_for_result_memo(material: Mapping[str, Any] | None) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer_contract(material) is True
    except ValueError:
        return False


def _op12_clean_status_map(
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


def _op12_clean_count_map(
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


def _op12_all_passed(status_map: Mapping[str, str]) -> bool:
    return bool(status_map) and all(value in P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REFS for value in status_map.values())


def _op12_changed_files_summary() -> dict[str, Any]:
    modified = tuple(P7_R54_AHR_POST_DMD08_ALR_OP12_CHANGED_FILE_REFS["modified"])
    new = tuple(P7_R54_AHR_POST_DMD08_ALR_OP12_CHANGED_FILE_REFS["new"])
    deleted = tuple(P7_R54_AHR_POST_DMD08_ALR_OP12_CHANGED_FILE_REFS["deleted"])
    return {
        "modified_file_refs": list(modified),
        "modified_file_ref_count": len(modified),
        "new_file_refs": list(new),
        "new_file_ref_count": len(new),
        "deleted_file_refs": list(deleted),
        "deleted_file_ref_count": len(deleted),
    }


def _op12_false_boundary(refs: Sequence[str]) -> dict[str, bool]:
    return {ref: False for ref in refs}


def _op12_dmd08_pass_status_refs() -> dict[str, str]:
    return {
        key: dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF
        for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS
    }


def _op12_dmd08_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_TARGET_TEST_GROUP_REFS}


def _op12_dmd08_regression_pass_status_refs() -> dict[str, str]:
    return {
        key: dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF
        for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS
    }


def _op12_dmd08_regression_pass_count_refs() -> dict[str, int]:
    return {key: 1 for key in dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_SELECTED_REGRESSION_GROUP_REFS}


def _op12_build_default_alr_op11_current_retry_path(session_id: str) -> dict[str, Any]:
    dmd08_material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure(
        target_test_result_status_refs=_op12_dmd08_pass_status_refs(),
        target_test_result_count_refs=_op12_dmd08_pass_count_refs(),
        selected_regression_result_status_refs=_op12_dmd08_regression_pass_status_refs(),
        selected_regression_result_count_refs=_op12_dmd08_regression_pass_count_refs(),
        compileall_result_status_ref=dmd.P7_R54_AHR_POST_DMH18_DMD_OP08_PASS_STATUS_REF,
        compileall_result_count_ref="passed",
    )
    op01 = build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=dmd08_material,
        review_session_id=session_id,
    )
    op02 = build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=op01,
        review_session_id=session_id,
    )
    op03 = build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
        review_session_id=session_id,
    )
    op04 = build_p7_r54_ahr_post_dmd08_alr_op04_continue_retry_repair_complete_action_resolver(
        alr_op03_bodyfree_leak_invalid_source_promotion_scan=op03,
        review_session_id=session_id,
    )
    op05 = build_p7_r54_ahr_post_dmd08_alr_op05_operation_state_machine_materialization(
        alr_op04_continue_retry_repair_complete_action_resolver=op04,
        review_session_id=session_id,
    )
    op06 = build_p7_r54_ahr_post_dmd08_alr_op06_explicit_local_only_allow_requirement_boundary(
        alr_op05_operation_state_machine_materialization=op05,
        review_session_id=session_id,
    )
    op07 = build_p7_r54_ahr_post_dmd08_alr_op07_bodyfull_packet_request_bodyfree_envelope(
        alr_op06_explicit_local_only_allow_requirement_boundary=op06,
        review_session_id=session_id,
    )
    op08 = build_p7_r54_ahr_post_dmd08_alr_op08_actual_operation_receipt_expected_schema_completeness_guard(
        alr_op07_bodyfull_packet_request_bodyfree_envelope=op07,
        review_session_id=session_id,
    )
    op09 = build_p7_r54_ahr_post_dmd08_alr_op09_selection_only_rows_rating_question_need_expected_schema_guard(
        alr_op08_actual_operation_receipt_expected_schema_completeness_guard=op08,
        review_session_id=session_id,
    )
    op10 = build_p7_r54_ahr_post_dmd08_alr_op10_disposal_purge_receipt_expected_schema_guard(
        alr_op09_selection_only_rows_rating_question_need_expected_schema_guard=op09,
        review_session_id=session_id,
    )
    return build_p7_r54_ahr_post_dmd08_alr_op11_downstream_non_promotion_manual_decision_hold_finalizer(
        alr_op10_disposal_purge_receipt_expected_schema_guard=op10,
        review_session_id=session_id,
    )


def build_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure(
    *,
    alr_op11_downstream_non_promotion_manual_decision_hold_finalizer: Mapping[str, Any] | None = None,
    target_test_result_status_refs: Mapping[str, Any] | None = None,
    target_test_result_count_refs: Mapping[str, Any] | None = None,
    selected_regression_result_status_refs: Mapping[str, Any] | None = None,
    selected_regression_result_count_refs: Mapping[str, Any] | None = None,
    compileall_result_status_ref: Any = None,
    compileall_result_count_ref: Any = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build ALR-OP12 body-free result memo / target-test / regression closure material."""

    session_id = _safe_review_session_id(review_session_id)
    op11_input = alr_op11_downstream_non_promotion_manual_decision_hold_finalizer
    if op11_input is None:
        op11_input = _op12_build_default_alr_op11_current_retry_path(session_id)
    op11_valid = _op12_contract_valid_for_result_memo(op11_input)
    op11 = op11_input if isinstance(op11_input, Mapping) else {}
    op11_forbidden_paths = _scan_forbidden_payload_key_paths(op11, path="op11_material") if isinstance(op11, Mapping) else []

    target_status_map = _op12_clean_status_map(
        target_test_result_status_refs,
        required_keys=P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS,
    )
    target_count_map = _op12_clean_count_map(
        target_test_result_count_refs,
        required_keys=P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS,
    )
    regression_status_map = _op12_clean_status_map(
        selected_regression_result_status_refs,
        required_keys=P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS,
    )
    regression_count_map = _op12_clean_count_map(
        selected_regression_result_count_refs,
        required_keys=P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS,
    )
    compile_status = _clean_ref(compileall_result_status_ref, default="not_run_by_helper", max_length=180)
    compile_count = _clean_ref(compileall_result_count_ref, default="not_applicable", max_length=180)

    target_closed = _op12_all_passed(target_status_map)
    regression_closed = _op12_all_passed(regression_status_map)
    compile_closed = compile_status in P7_R54_AHR_POST_DMD08_ALR_OP12_PASS_STATUS_REFS
    validation_closed = target_closed and regression_closed and compile_closed
    repair_required = not op11_valid or bool(op11_forbidden_paths)

    if repair_required:
        status_ref = P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_REPAIR_REQUIRED_REF
        ready = False
        result_memo_closed = False
        selected_action_ref = P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF
        continue_allowed = False
        retry_or_start_required = False
        repair_stop_required = True
        complete_receipt_manual_decision_required = False
        next_required_step = P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
        branch_reason_refs = ["alr_op12_requires_valid_bodyfree_op11_material_before_result_memo_closure"]
        branch_blocker_refs = ["alr_op12_op11_downstream_hold_material_missing_or_invalid"]
        if op11_forbidden_paths:
            branch_blocker_refs.append("alr_op12_op11_forbidden_payload_key_detected")
    else:
        status_ref = (
            P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF
            if validation_closed
            else P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF
        )
        ready = validation_closed
        result_memo_closed = validation_closed
        selected_action_ref = _clean_ref(op11.get("selected_action_ref"), default=P7_R54_AHR_POST_DMD08_ALR_ACTION_REPAIR_STOP_REQUIRED_REF, max_length=220)
        continue_allowed = op11.get("continue_allowed") is True
        retry_or_start_required = op11.get("retry_or_start_required") is True
        repair_stop_required = op11.get("repair_stop_required") is True
        complete_receipt_manual_decision_required = op11.get("complete_receipt_manual_decision_required") is True
        next_required_step = _clean_ref(op11.get("next_required_step"), default=P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF, max_length=260)
        branch_reason_refs = list(op11.get("op11_reason_refs") or [])
        if validation_closed:
            branch_reason_refs.append("alr_op12_bodyfree_result_memo_target_tests_selected_regression_closure_recorded")
        else:
            branch_reason_refs.append("alr_op12_waits_for_external_target_tests_selected_regression_compileall_status")
        branch_blocker_refs = list(op11.get("op11_blocker_refs") or [])
        if not validation_closed:
            branch_blocker_refs.append("alr_op12_external_validation_status_not_closed")

    branch_reason_refs = _unique_clean_refs(branch_reason_refs)
    branch_blocker_refs = _unique_clean_refs(branch_blocker_refs)
    exactly_one_action = sum(
        1 for value in (continue_allowed, retry_or_start_required, repair_stop_required, complete_receipt_manual_decision_required) if value is True
    ) == 1
    downstream_manual_decision_required = complete_receipt_manual_decision_required is True
    actual_review_continue_retry_required = continue_allowed is True or retry_or_start_required is True
    complete_receipt_branch_requires_manual_decision = complete_receipt_manual_decision_required is True

    implementation_scope = {
        "implemented_step_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_IMPLEMENTED_STEPS),
        "implemented_step_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_IMPLEMENTED_STEPS),
        "not_yet_implemented_step_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_YET_IMPLEMENTED_STEPS),
        "not_yet_implemented_step_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_YET_IMPLEMENTED_STEPS),
        "actual_operation_execution_included": False,
        "downstream_promotion_included": False,
    }
    target_tests_summary = {
        "target_test_group_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS),
        "target_test_result_status_refs": dict(target_status_map),
        "target_test_result_count_refs": dict(target_count_map),
        "target_tests_closed": target_closed,
    }
    selected_regression_summary = {
        "selected_regression_group_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS),
        "selected_regression_result_status_refs": dict(regression_status_map),
        "selected_regression_result_count_refs": dict(regression_count_map),
        "selected_regression_closed": regression_closed,
    }
    compileall_summary = {
        "compileall_result_status_ref": compile_status,
        "compileall_result_count_ref": compile_count,
        "compileall_closed": compile_closed,
    }
    dmd_op08_branch_intake_status = {
        "expected_current_dmd_branch_ref": P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_DMD_BRANCH_REF,
        "expected_current_dmd_next_required_step_ref": P7_R54_AHR_POST_DMD08_ALR_EXPECTED_CURRENT_DMD_NEXT_STEP_REF,
        "default_dmd08_intake_status_ref": P7_R54_AHR_POST_DMD08_ALR_OP01_STATUS_ACCEPTED_EVIDENCE_INCOMPLETE_REF,
        "dmd_branch_intake_does_not_claim_actual_review_complete": True,
    }
    selected_alr_action_status = {
        "selected_action_ref": selected_action_ref,
        "continue_allowed": continue_allowed,
        "retry_or_start_required": retry_or_start_required,
        "repair_stop_required": repair_stop_required,
        "complete_receipt_manual_decision_required": complete_receipt_manual_decision_required,
        "exactly_one_final_action_flag_true": exactly_one_action,
    }
    downstream_non_promotion_hold_status = {
        "manual_decision_hold_finalized": op11.get("manual_decision_hold_finalized") is True,
        "downstream_non_promotion_finalizer_closed_bodyfree": op11.get("downstream_non_promotion_finalizer_closed_bodyfree") is True,
        "manual_decision_auto_executes_downstream": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_actual_execution_started_here": False,
        "p7_complete": False,
        "release_allowed": False,
    }

    data = {
        "schema_version": P7_R54_AHR_POST_DMD08_ALR_OP12_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "step": P7_R54_AHR_POST_DMD08_ALR_STEP,
        "scope": P7_R54_AHR_POST_DMD08_ALR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DMD08_ALR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DMD08_ALR_PHASE,
        "material_id": f"r54_ahr_postdmd08_alr_op12_result_memo_target_tests_selected_regression_closure_bodyfree_{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DMD08_ALR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_schema_version": _clean_ref(op11.get("schema_version"), max_length=260),
        "op11_material_ref": _clean_ref(op11.get("material_id"), max_length=260),
        "op11_status_ref": _clean_ref(op11.get("downstream_non_promotion_status_ref"), max_length=220),
        "op11_next_required_step": _clean_ref(op11.get("next_required_step"), max_length=260),
        "op11_next_implementation_step": _clean_ref(op11.get("next_implementation_step"), max_length=260),
        "op11_contract_valid": op11_valid,
        "op11_selected_action_ref": _clean_ref(op11.get("selected_action_ref"), max_length=220),
        "op11_retry_or_start_required": op11.get("retry_or_start_required") is True,
        "op11_repair_stop_required": op11.get("repair_stop_required") is True,
        "op11_complete_receipt_manual_decision_required": op11.get("complete_receipt_manual_decision_required") is True,
        "op11_manual_decision_hold_finalized": op11.get("manual_decision_hold_finalized") is True,
        "op11_downstream_non_promotion_finalizer_closed_bodyfree": op11.get("downstream_non_promotion_finalizer_closed_bodyfree") is True,
        "alr_op12_status_ref": status_ref,
        "alr_op12_allowed_status_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_ALLOWED_STATUS_REFS),
        "alr_op12_allowed_status_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_ALLOWED_STATUS_REFS),
        "alr_op12_ready": ready,
        "result_memo_ref": P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_REF,
        "result_memo_bodyfree_closed": result_memo_closed,
        "result_memo_sections_fixed": True,
        "result_memo_section_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_SECTION_REFS),
        "result_memo_section_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_SECTION_REFS),
        "implementation_scope": implementation_scope,
        "changed_files": _op12_changed_files_summary(),
        "target_tests": target_tests_summary,
        "selected_regression": selected_regression_summary,
        "compileall": compileall_summary,
        "dmd_op08_branch_intake_status": dmd_op08_branch_intake_status,
        "selected_alr_action_status": selected_alr_action_status,
        "downstream_non_promotion_hold_status": downstream_non_promotion_hold_status,
        "next_required_step": next_required_step,
        "not_executed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_EXECUTED_BOUNDARY_REFS),
        "not_executed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_EXECUTED_BOUNDARY_REFS),
        "not_executed_boundary": _op12_false_boundary(P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_EXECUTED_BOUNDARY_REFS),
        "unverified_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary": _op12_false_boundary(P7_R54_AHR_POST_DMD08_ALR_OP12_UNVERIFIED_BOUNDARY_REFS),
        "target_test_group_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS),
        "target_test_group_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS),
        "target_test_result_status_refs": dict(target_status_map),
        "target_test_result_status_ref_count": len(target_status_map),
        "target_test_result_count_refs": dict(target_count_map),
        "target_test_result_count_ref_count": len(target_count_map),
        "target_tests_summary_bodyfree_recorded": True,
        "target_tests_closed_by_external_status_summary": target_closed,
        "target_tests_closed": target_closed,
        "selected_regression_group_refs": list(P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS),
        "selected_regression_group_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS),
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
        "selected_action_ref": selected_action_ref,
        "continue_allowed": continue_allowed,
        "retry_or_start_required": retry_or_start_required,
        "repair_stop_required": repair_stop_required,
        "complete_receipt_manual_decision_required": complete_receipt_manual_decision_required,
        "exactly_one_final_action_flag_true": exactly_one_action,
        "manual_decision_hold_finalized": op11.get("manual_decision_hold_finalized") is True,
        "downstream_manual_decision_required": downstream_manual_decision_required,
        "actual_local_review_operation_must_continue_or_retry": actual_review_continue_retry_required,
        "complete_receipt_branch_requires_manual_decision": complete_receipt_branch_requires_manual_decision,
        "p5_p6_p8_r52_p7_release_auto_promotion_blocked": True,
        "branch_reason_refs": branch_reason_refs,
        "branch_reason_ref_count": len(branch_reason_refs),
        "branch_blocker_refs": branch_blocker_refs,
        "branch_blocker_ref_count": len(branch_blocker_refs),
        "alr_op12_helper_does_not_run_pytest_or_compileall": True,
        "alr_op12_does_not_generate_body_full_packet": True,
        "alr_op12_does_not_run_actual_local_human_review": True,
        "alr_op12_does_not_create_receipts_rows_or_disposal": True,
        "alr_op12_does_not_execute_postcr22_ex_reentry_or_r52": True,
        "alr_op12_does_not_start_p5_p6_p8_p7_or_release": True,
        "alr_op12_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_YET_IMPLEMENTED_STEPS),
        "next_implementation_step": P7_R54_AHR_POST_DMD08_ALR_OP12_NEXT_IMPLEMENTATION_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dmd08_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(data)
    return data


def assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert ALR-OP12 body-free result memo / target-test / regression closure contract."""

    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DMD08_ALR_OP12_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DMD08_ALR_OP12_STEP_REF,
        source="P7-R54-AHR-PostDMD08-ALR-OP12",
    )
    _required_fields_present(data, required=P7_R54_AHR_POST_DMD08_ALR_OP12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDMD08-ALR-OP12")
    if set(data) != set(P7_R54_AHR_POST_DMD08_ALR_OP12_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 field set changed")
    if data.get("alr_op12_status_ref") not in P7_R54_AHR_POST_DMD08_ALR_OP12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 status ref changed")
    if tuple(data.get("alr_op12_allowed_status_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 allowed status refs changed")
    if data.get("alr_op12_allowed_status_ref_count") != len(P7_R54_AHR_POST_DMD08_ALR_OP12_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 allowed status count changed")
    for key in (
        "result_memo_sections_fixed",
        "target_tests_summary_bodyfree_recorded",
        "selected_regression_summary_bodyfree_recorded",
        "compileall_summary_bodyfree_recorded",
        "alr_op12_helper_does_not_run_pytest_or_compileall",
        "alr_op12_does_not_generate_body_full_packet",
        "alr_op12_does_not_run_actual_local_human_review",
        "alr_op12_does_not_create_receipts_rows_or_disposal",
        "alr_op12_does_not_execute_postcr22_ex_reentry_or_r52",
        "alr_op12_does_not_start_p5_p6_p8_p7_or_release",
        "alr_op12_does_not_change_api_db_rn_runtime_response_key",
        "p5_p6_p8_r52_p7_release_auto_promotion_blocked",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP12 required true boundary changed: {key}")
    if data.get("result_memo_ref") != P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 result memo ref changed")
    if tuple(data.get("result_memo_section_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_SECTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 result memo section refs changed")
    if data.get("result_memo_section_ref_count") != len(P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_SECTION_REFS):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 result memo section count changed")
    for section_ref in P7_R54_AHR_POST_DMD08_ALR_OP12_RESULT_MEMO_SECTION_REFS:
        if section_ref not in data:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP12 missing result memo section: {section_ref}")
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
        if data.get(count_field) != len(value):
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP12 {count_field} changed")
    if tuple(data.get("target_test_group_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_TARGET_TEST_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 target test group refs changed")
    if tuple(data.get("selected_regression_group_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_SELECTED_REGRESSION_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 selected regression group refs changed")
    if tuple(data.get("not_executed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_EXECUTED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 not-executed refs changed")
    if tuple(data.get("unverified_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_UNVERIFIED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 unverified refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 not-claimed refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DMD08_ALR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 fixed non-promotion refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 not-claimed boundary must stay false")
    if any(value is not False for value in (data.get("not_executed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 not-executed boundary must stay false")
    if any(value is not False for value in (data.get("unverified_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 unverified boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DMD08_ALR_OP12_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 not-yet steps changed")
    if data.get("next_implementation_step") != P7_R54_AHR_POST_DMD08_ALR_OP12_NEXT_IMPLEMENTATION_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 next implementation step changed")
    if data.get("exactly_one_final_action_flag_true") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 must preserve exactly one final action flag")
    selected_action_ref = str(data.get("selected_action_ref"))
    if selected_action_ref not in P7_R54_AHR_POST_DMD08_ALR_ALLOWED_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 invalid selected action ref")
    action_flags = (
        data.get("continue_allowed"),
        data.get("retry_or_start_required"),
        data.get("repair_stop_required"),
        data.get("complete_receipt_manual_decision_required"),
    )
    if action_flags.count(True) != 1:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 final action flags changed")
    if data.get("target_tests_closed") != data.get("target_tests_closed_by_external_status_summary"):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 target test closure alias changed")
    if data.get("selected_regression_closed") != data.get("selected_regression_closed_by_external_status_summary"):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 selected regression closure alias changed")
    if data.get("compileall_closed") != data.get("compileall_closed_by_external_status_summary"):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 compileall closure alias changed")
    status_ref = data.get("alr_op12_status_ref")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_CLOSED_REF:
        if data.get("alr_op12_ready") is not True or data.get("result_memo_bodyfree_closed") is not True:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 closed status must be ready and body-free-closed")
        if not (data.get("target_tests_closed") and data.get("selected_regression_closed") and data.get("compileall_closed")):
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 closed status requires external validation summaries")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_INCOMPLETE_OR_UNVERIFIED_REF:
        if data.get("alr_op12_ready") is not False or data.get("result_memo_bodyfree_closed") is not False:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 incomplete status must stay unclosed")
        if data.get("next_required_step") not in (
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_CONTINUE_EXISTING_REVIEW_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_RETRY_OR_START_REVIEW_WITH_ALLOW_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF,
            P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_DOWNSTREAM_MANUAL_DECISION_NO_AUTO_EXEC_REF,
        ):
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 incomplete next required step changed")
    if status_ref == P7_R54_AHR_POST_DMD08_ALR_OP12_STATUS_REPAIR_REQUIRED_REF:
        if data.get("repair_stop_required") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF:
            raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 repair status must stop and repair")
    if data.get("downstream_manual_decision_required") is True and data.get("complete_receipt_manual_decision_required") is not True:
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 downstream manual decision flag mismatch")
    if data.get("actual_local_review_operation_must_continue_or_retry") is True and not (data.get("continue_allowed") or data.get("retry_or_start_required")):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 continue/retry flag mismatch")
    for key in (
        "manual_decision_auto_executes_downstream",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_actual_execution_started_here",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDMD08-ALR-OP12 promotion or unverified flag opened: {key}")
    if _scan_forbidden_payload_key_paths(data, path="alr_op12"):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 forbidden payload key detected")
    if _scan_safe_ref_shape_violation_paths(data, path="alr_op12"):
        raise ValueError("P7-R54-AHR-PostDMD08-ALR-OP12 unsafe body-free ref shape detected")
    return True


build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op12_result_memo_target_tests_selected_regression_closure = build_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure
assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op12_result_memo_target_tests_selected_regression_closure_contract = assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract
